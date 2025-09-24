# app.py
import os, json, asyncio
from pathlib import Path
import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from openai import OpenAI
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from fastapi import UploadFile, File, Header, Depends
import shutil
import tempfile
import subprocess
import os
from file_watcher import init_file_watcher, start_file_watcher, stop_file_watcher, get_watcher_status

# --- 챗봇의 핵심 자원(모델, 인덱스)을 관리하는 lifespan 함수 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 시작될 때 실행되는 부분
    print("🚀 서버 시작! 인덱스와 모델을 비동기적으로 로드합니다...")
    # 무거운 작업을 비동기적으로 처리하여 서버 시작을 방해하지 않음
    await load_resources()
    
    # 파일 워쳐 초기화 및 시작
    print("👁️ 파일 워쳐 초기화 중...")
    init_file_watcher(DATA_DIR, add_documents_to_index)
    start_file_watcher()
    print("✅ 파일 워쳐 시작됨")
    
    yield
    # 서버가 종료될 때 실행되는 부분 (정리 코드)
    print("🛑 파일 워쳐 중지 중...")
    stop_file_watcher()
    print("👋 서버 종료.")

async def load_resources():
    """AI 모델 및 인덱스 파일을 로드하는 함수"""
    global index, metas, texts, emb_model
    try:
        index = faiss.read_index(str(INDEX_DIR / "faiss.index"))
        with open(INDEX_DIR / "meta.json", "r", encoding="utf-8") as f:
            store = json.load(f)
        metas = store["metas"]
        texts = store["texts"]
        emb_model = SentenceTransformer(EMB_MODEL_NAME)
        print("✅ 인덱스와 모델 로드 완료!")
    except Exception as e:
        print(f"❌ 인덱스/모델 로드 실패: {e}")

# .env 파일 로드
load_dotenv()

# API 키 환경변수에서 로드
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY_HERE":
    print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

INDEX_DIR = Path("index")
DATA_DIR = Path("data")
EMB_MODEL_NAME = "jhgan/ko-sroberta-multitask"
TOP_K = 10
SIMILARITY_THRESHOLD = 0.1

# 키워드 확장 맵
KEYWORD_EXPANSION = {
    "다자녀가정": ["다자녀", "셋째아이", "3자녀", "3명 이상", "많은 자녀"], 
    "다자녀": ["다자녀가정", "셋째아이", "3자녀", "3명 이상"],
    "혜택": ["지원", "보조", "급여", "수당", "할인", "감면", "우대"], 
    "지원": ["혜택", "보조", "급여", "수당", "지원금"],
    "임신": ["임산부", "예비맘", "산모", "임신부"], 
    "출산": ["분만", "해산", "신생아", "산후조리"],
    "육아": ["양육", "자녀돌봄", "보육", "육아휴직"], 
    "보육": ["어린이집", "유치원", "놀이방", "육아", "양육"],
    "한부모": ["한부모가정", "미혼모", "편부모", "조손가정"]
}

# === 인덱스 및 모델 변수 초기화 ===
index = None
metas = []
texts = []
emb_model = None

# FastAPI 앱 생성 시 lifespan 연결
app = FastAPI(
    title="지능형 복지 상담 챗봇",
    description="문서 기반의 질문에 답변하는 RAG 챗봇입니다.",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/admin", StaticFiles(directory="admin"), name="admin")

# 관리자 설정
ADMIN_PASSWORD = "admin123"  # 실제 환경에서는 환경변수로 관리

def verify_admin_password(x_admin_password: Optional[str] = Header(None)):
    """관리자 권한 확인"""
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return True

# 세션 관리
class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    sources: Optional[List[Dict]] = None

class ConversationSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[ConversationMessage] = []
        self.created_at = datetime.now()
    
    def add_message(self, role: str, content: str, sources: Optional[List[Dict]] = None):
        self.messages.append(ConversationMessage(
            role=role, 
            content=content, 
            timestamp=datetime.now(), 
            sources=sources
        ))
    
    def get_context(self, max_messages: int = 4) -> str:
        """최근 대화 내용을 컨텍스트로 반환"""
        recent_messages = self.messages[-max_messages:]
        context_parts = []
        for msg in recent_messages:
            if msg.role == "user":
                context_parts.append(f"사용자: {msg.content}")
            else:
                context_parts.append(f"상담사: {msg.content}")
        return "\n".join(context_parts)

sessions: Dict[str, ConversationSession] = {}

# API 모델
class AskReq(BaseModel):
    question: str
    session_id: Optional[str] = None

class NewSessionResponse(BaseModel):
    session_id: str
    message: str

def expand_query(query: str) -> str:
    """질문을 확장하여 더 나은 검색 결과를 얻기"""
    expanded_terms = []
    query_lower = query.lower()
    
    for keyword, synonyms in KEYWORD_EXPANSION.items():
        if keyword in query_lower:
            expanded_terms.extend(synonyms)
        for synonym in synonyms:
            if synonym in query_lower and keyword not in expanded_terms:
                expanded_terms.append(keyword)
                expanded_terms.extend([s for s in synonyms if s != synonym])
    
    if expanded_terms:
        unique_terms = list(set(expanded_terms))
        return f"{query} {' '.join(unique_terms[:5])}"
    return query

def search_similar(query: str, k=TOP_K):
    """유사한 문서를 검색합니다"""
    if not index or not emb_model:
        raise HTTPException(status_code=503, detail="모델/인덱스가 아직 로드되지 않았습니다. 잠시 후 다시 시도해주세요.")
    
    # 질문 확장
    expanded_query = expand_query(query)
    
    # 임베딩 및 검색
    q_emb = emb_model.encode([expanded_query], normalize_embeddings=True).astype("float32")
    D, I = index.search(q_emb, k)
    
    results = []
    for i, score in zip(I[0], D[0]):
        if score >= SIMILARITY_THRESHOLD:  # 유사도 임계값 이상만 포함
            results.append({
                "text": texts[i],
                "source": metas[i]["source"],
                "chunk_id": metas[i]["chunk_id"],
                "score": float(score)
            })
    
    return results

SYSTEM_PROMPT = (
    "당신은 생애복지플랫폼의 전문 복지 상담사입니다. 제공된 '문서 컨텍스트'를 지능적으로 분석하여 답변하십시오.\n\n"
    "## 🔍 정책 분류 및 우선순위 분석 방법:\n"
    "1. **전용 정책**: 특정 대상(다자녀가정, 한부모가정 등)만을 위한 전용 지원 정책\n"
    "2. **우대 정책**: 일반 정책에서 특정 대상에게 우대 혜택을 제공하는 정책\n"
    "3. **관련 정책**: 간접적으로 관련된 정책\n\n"
    "## 📋 답변 구조화 지침:\n"
    "**다자녀가정 지원정책** 질문 시:\n"
    "- 🎯 **다자녀가정 전용 정책** (최우선)\n"
    "- 🔖 **다자녀가정 우대 혜택** (차순위)\n\n"
    "**임신·출산 지원정책** 질문 시:\n"
    "- 🎯 **임신·출산 전용 정책** (최우선)\n"
    "- 🔖 **임신·출산 우대 혜택** (차순위)\n\n"
    "**한부모가정 지원정책** 질문 시:\n"
    "- 🎯 **한부모가정 전용 정책** (최우선)\n"
    "- 🔖 **한부모가정 우대 혜택** (차순위)\n\n"
    "## ✅ 답변 규칙:\n"
    "- 문서 컨텍스트 안에서만 답변하고, 정책을 분류별로 그룹화하여 제시하세요.\n"
    "- 각 정책의 대상, 내용, 신청방법을 명확히 요약하고, 문장마다 [출처: 파일명#청크]를 표기하세요.\n"
    "- 전용 정책을 우선적으로 상세히 설명하고, 우대 조건은 별도로 구분하여 설명하세요.\n"
    "- 컨텍스트에 없는 내용은 '관련 정보를 찾을 수 없습니다'라고 답변하세요.\n"
    "- 마크다운 형식으로 가독성 있게 작성하세요.\n"
    "- 답변 마지막에 추가 질문을 유도하는 친근한 멘트를 포함하세요."
)

def build_prompt(question: str, contexts: list[dict], conversation_history: str = ""):
    """질문과 컨텍스트를 바탕으로 LLM 프롬프트를 구성"""
    ctx_blocks = [f"[{r['source']}#{r['chunk_id']}]\n{r['text']}\n" for r in contexts]
    ctx_text = "\n---\n".join(ctx_blocks)
    
    instruction = (
        "질문에 맞는 정확한 정보를 찾아서, 정책 종류(전용/우대/관련)에 따라 분류하고 "
        "우선순위에 맞게 상세히 설명하세요."
    )
    
    user_parts = []
    if conversation_history.strip():
        user_parts.append(f"[이전 대화]\n{conversation_history}\n")
    
    user_parts.extend([
        f"[현재 질문]\n{question}\n",
        f"[문서 컨텍스트]\n{ctx_text}\n",
        f"[지시사항]\n{instruction}\n"
    ])
    
    return "\n".join(user_parts)

@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

@app.post("/new-session")
def create_new_session():
    """새로운 대화 세션을 생성합니다"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = ConversationSession(session_id)
    return NewSessionResponse(
        session_id=session_id,
        message="새로운 상담 세션이 시작되었습니다. 궁금한 복지 정책에 대해 질문해주세요!"
    )

@app.get("/sessions")
def list_sessions():
    """현재 활성 세션 목록을 반환합니다"""
    return {
        "sessions": [
            {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "message_count": len(session.messages)
            }
            for session in sessions.values()
        ]
    }

@app.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    """특정 세션의 대화 기록을 반환합니다"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "sources": msg.sources
            }
            for msg in session.messages
        ]
    }

@app.get("/documents")
def get_indexed_documents():
    """인덱스된 문서 목록을 반환합니다"""
    if not metas:
        return {"documents": [], "total_documents": 0, "total_chunks": 0}
    
    # 문서별로 그룹화
    doc_info = {}
    for meta in metas:
        source = meta["source"]
        if source not in doc_info:
            doc_info[source] = {
                "filename": source,
                "path": meta.get("path", ""),
                "chunks": 0,
                "first_chunk_text": ""
            }
        doc_info[source]["chunks"] += 1
        
        # 첫 번째 청크의 일부 텍스트를 미리보기로 사용
        if doc_info[source]["chunks"] == 1 and meta["chunk_id"] == 0:
            chunk_index = meta["uid"]
            if chunk_index < len(texts):
                preview_text = texts[chunk_index][:200] + "..." if len(texts[chunk_index]) > 200 else texts[chunk_index]
                doc_info[source]["first_chunk_text"] = preview_text
    
    return {
        "documents": list(doc_info.values()),
        "total_documents": len(doc_info),
        "total_chunks": len(metas)
    }

@app.post("/ask")
def ask(req: AskReq):
    """질문에 대한 답변을 생성합니다"""
    # 세션 관리
    session_id = req.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = ConversationSession(session_id)
    
    session = sessions[session_id]
    
    # 사용자 질문 저장
    session.add_message("user", req.question)
    
    # 유사한 문서 검색
    hits = search_similar(req.question, k=TOP_K)
    
    if not client:
        answer = "⚠️ OpenAI API 키가 설정되지 않았습니다."
    else:
        # LLM 프롬프트 구성
        user_prompt = build_prompt(req.question, hits, session.get_context())
        
        # OpenAI API 호출
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        answer = completion.choices[0].message.content
    
    # 응답 저장
    session.add_message("assistant", answer, hits)
    
    return {
        "answer": answer,
        "sources": hits,
        "session_id": session_id
    }

# === 증분 인덱싱 함수들 ===
async def add_documents_to_index(file_paths: List[Path]):
    """새 문서들을 기존 인덱스에 추가"""
    global index, metas, texts, emb_model
    
    if not emb_model:
        await load_resources()
    
    # 기존 메타데이터에서 최대 uid 찾기
    max_uid = max([meta["uid"] for meta in metas], default=-1)
    
    new_vectors = []
    new_metas = []
    new_texts = []
    
    from ingest import load_and_extract, chunk_text
    
    for file_path in file_paths:
        print(f"📄 처리 중: {file_path.name}")
        
        # 이미 인덱스된 문서인지 확인
        if any(meta["source"] == file_path.name for meta in metas):
            print(f"⚠️ {file_path.name}은 이미 인덱스됨. 건너뜀.")
            continue
        
        try:
            text = load_and_extract(file_path)
            if not text:
                print(f"⚠️ {file_path.name}: 텍스트 추출 실패")
                continue
                
            chunks = chunk_text(text)
            print(f"📄 {file_path.name}: {len(chunks)}개 청크 생성")
            
            for i, chunk in enumerate(chunks):
                max_uid += 1
                meta = {
                    "uid": max_uid,
                    "source": file_path.name,
                    "chunk_id": i,
                    "path": str(file_path.resolve())
                }
                new_metas.append(meta)
                new_texts.append(chunk)
        except Exception as e:
            print(f"❌ {file_path.name} 처리 중 오류: {e}")
            continue
    
    if new_texts:
        # 새 텍스트들 임베딩
        print(f"🔄 {len(new_texts)}개 청크 임베딩 생성 중...")
        new_embeddings = emb_model.encode(new_texts, normalize_embeddings=True)
        new_embeddings = np.array(new_embeddings).astype("float32")
        
        # 기존 인덱스에 추가
        index.add(new_embeddings)
        metas.extend(new_metas)
        texts.extend(new_texts)
        
        # 인덱스 저장
        save_index()
        print(f"✅ {len(new_texts)}개 청크가 인덱스에 추가됨")
        return len(new_texts)
    else:
        print("⚠️ 추가할 새로운 청크가 없습니다")
        return 0

def save_index():
    """인덱스와 메타데이터 저장"""
    INDEX_DIR.mkdir(exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "faiss.index"))
    with open(INDEX_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump({"metas": metas, "texts": texts}, f, ensure_ascii=False)

async def rebuild_full_index():
    """전체 인덱스 재구축"""
    print("🔄 전체 인덱스 재구축 시작...")
    
    # ingest.py 실행
    result = subprocess.run([
        "python", "ingest.py"
    ], capture_output=True, text=True, encoding="utf-8")
    
    if result.returncode == 0:
        # 인덱스 다시 로드
        await load_resources()
        print("✅ 인덱스 재구축 완료")
        return True
    else:
        print(f"❌ 인덱스 재구축 실패: {result.stderr}")
        return False

def remove_document_from_index(filename: str):
    """특정 문서를 인덱스에서 제거"""
    global index, metas, texts
    
    # 해당 문서의 인덱스들 찾기
    indices_to_remove = []
    for i, meta in enumerate(metas):
        if meta["source"] == filename:
            indices_to_remove.append(i)
    
    if not indices_to_remove:
        return False
    
    # 역순으로 제거 (인덱스 변화 방지)
    for i in reversed(indices_to_remove):
        del metas[i]
        del texts[i]
    
    # 전체 인덱스 재구축 필요 (FAISS는 개별 벡터 삭제 미지원)
    return True

# === 관리자 API 엔드포인트들 ===
@app.post("/admin/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    _: bool = Depends(verify_admin_password)
):
    """문서 업로드 및 인덱싱"""
    DATA_DIR.mkdir(exist_ok=True)
    uploaded_files = []
    
    try:
        for file in files:
            # 파일 저장
            file_path = DATA_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file_path)
        
        # 증분 인덱싱
        added_chunks = await add_documents_to_index(uploaded_files)
        
        return {
            "message": f"{len(uploaded_files)}개 파일 업로드 완료. {added_chunks}개 청크가 인덱스에 추가되었습니다.",
            "files": [f.name for f in uploaded_files],
            "added_chunks": added_chunks
        }
    
    except Exception as e:
        # 오류 시 업로드된 파일들 정리
        for file_path in uploaded_files:
            if file_path.exists():
                file_path.unlink()
        raise HTTPException(status_code=500, detail=f"업로드 처리 중 오류: {str(e)}")

@app.delete("/admin/documents/{filename}")
async def delete_document(
    filename: str,
    _: bool = Depends(verify_admin_password)
):
    """문서 삭제"""
    try:
        # 파일 시스템에서 삭제
        file_path = DATA_DIR / filename
        if file_path.exists():
            file_path.unlink()
        
        # 인덱스에서 제거
        removed = remove_document_from_index(filename)
        if removed:
            # 전체 재구축 필요
            await rebuild_full_index()
            return {"message": f"문서 '{filename}'이 삭제되고 인덱스가 재구축되었습니다."}
        else:
            return {"message": f"문서 '{filename}'을 찾을 수 없습니다."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 처리 중 오류: {str(e)}")

@app.post("/admin/rebuild-index")
async def rebuild_index_endpoint(_: bool = Depends(verify_admin_password)):
    """전체 인덱스 재구축"""
    try:
        success = await rebuild_full_index()
        if success:
            return {"message": "인덱스 재구축이 완료되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="인덱스 재구축에 실패했습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"재구축 처리 중 오류: {str(e)}")

@app.post("/admin/clear-index")
async def clear_index_endpoint(_: bool = Depends(verify_admin_password)):
    """인덱스 초기화"""
    global index, metas, texts
    
    try:
        # 데이터 파일들 삭제
        if DATA_DIR.exists():
            for file in DATA_DIR.glob("*"):
                if file.is_file():
                    file.unlink()
        
        # 인덱스 파일들 삭제
        if INDEX_DIR.exists():
            for file in INDEX_DIR.glob("*"):
                if file.is_file():
                    file.unlink()
        
        # 메모리 상의 데이터 초기화
        index = None
        metas = []
        texts = []
        
        return {"message": "모든 인덱스와 문서가 삭제되었습니다."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"초기화 처리 중 오류: {str(e)}")

@app.get("/admin/watcher-status")
async def get_watcher_status_endpoint(_: bool = Depends(verify_admin_password)):
    """파일 워쳐 상태 확인"""
    try:
        status = get_watcher_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 중 오류: {str(e)}")

@app.post("/admin/watcher/start")
async def start_watcher_endpoint(_: bool = Depends(verify_admin_password)):
    """파일 워쳐 시작"""
    try:
        success = start_file_watcher()
        if success:
            return {"message": "파일 워쳐가 시작되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="파일 워쳐 시작에 실패했습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"워쳐 시작 중 오류: {str(e)}")

@app.post("/admin/watcher/stop")
async def stop_watcher_endpoint(_: bool = Depends(verify_admin_password)):
    """파일 워쳐 중지"""
    try:
        success = stop_file_watcher()
        if success:
            return {"message": "파일 워쳐가 중지되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="파일 워쳐 중지에 실패했습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"워쳐 중지 중 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)