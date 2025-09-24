#!/usr/bin/env python3
# simple_app.py - 간단한 버전의 FastAPI 서버

import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="RAG Chatbot (Simple MVP)", description="문서 기반 질의응답 챗봇 - 간단한 버전")

# 정적 파일 서빙 (프론트엔드)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

INDEX_DIR = Path("index")

# === 인덱스 로드 ===
try:
    with open(INDEX_DIR / "simple_meta.json", "r", encoding="utf-8") as f:
        store = json.load(f)
    metas = store["metas"]
    texts = store["texts"]
    print("✅ 간단한 인덱스 로드 완료")
    print(f"📊 로드된 청크: {len(texts)}개")
except Exception as e:
    print(f"❌ 인덱스 로드 실패: {e}")
    print("   먼저 python simple_ingest.py를 실행하여 인덱스를 생성하세요.")
    metas = []
    texts = []

class AskReq(BaseModel):
    question: str

def simple_search(query: str, k=5):
    """간단한 키워드 기반 검색"""
    if not texts:
        return []
    
    query_lower = query.lower()
    results = []
    
    for i, text in enumerate(texts):
        text_lower = text.lower()
        # 간단한 키워드 매칭 점수 계산
        score = 0
        query_words = query_lower.split()
        for word in query_words:
            if word in text_lower:
                score += text_lower.count(word)
        
        if score > 0:
            results.append({
                "rank": len(results) + 1,
                "score": score,
                "text": text,
                "source": metas[i]["source"],
                "chunk_id": metas[i]["chunk_id"]
            })
    
    # 점수순으로 정렬하고 상위 k개 반환
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:k]

@app.get("/")
async def read_root():
    """루트 경로 - 프론트엔드 서빙"""
    return FileResponse("frontend/index.html")

@app.post("/ask")
def ask(req: AskReq):
    """질의응답 API (간단한 버전)"""
    try:
        # 간단한 검색
        hits = simple_search(req.question, k=5)
        
        if not hits:
            answer = "죄송합니다. 관련 정보를 찾을 수 없습니다."
        else:
            # 간단한 답변 생성 (첫 번째 검색 결과 기반)
            best_hit = hits[0]
            answer = f"검색된 정보:\n\n{best_hit['text'][:500]}..."
            if len(best_hit['text']) > 500:
                answer += "\n\n(전체 내용은 참고 문서를 확인하세요)"
        
        return {"answer": answer, "sources": hits}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")

@app.get("/health")
def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "index_loaded": len(texts) > 0,
        "total_chunks": len(texts)
    }

@app.get("/stats")
def get_stats():
    """통계 정보"""
    if not texts:
        return {"error": "인덱스가 로드되지 않았습니다."}
    
    return {
        "total_chunks": len(texts),
        "total_documents": len(set(meta["source"] for meta in metas)),
        "search_type": "simple_keyword_search"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 간단한 RAG 챗봇 서버 시작...")
    print("📱 웹 브라우저에서 http://localhost:8000 접속하세요")
    uvicorn.run(app, host="0.0.0.0", port=8000)
