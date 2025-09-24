# ingest.py
import os, json, re, glob
from pathlib import Path
# from tqdm import tqdm  # tqdm 대신 간단한 진행 표시 사용
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from markdown import markdown
from bs4 import BeautifulSoup  # markdown -> text 정제를 위한 보조
import pandas as pd
import docx

DATA_DIR = Path("data")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(exist_ok=True)

EMB_MODEL_NAME = "jhgan/ko-sroberta-multitask"
CHUNK_SIZE = 1000   # 문자 기준(간단), 필요 시 토큰화 기반으로 개선
CHUNK_OVERLAP = 200

def read_txt(path: Path) -> str:
    """텍스트 파일 읽기"""
    return path.read_text(encoding="utf-8", errors="ignore")

def read_md(path: Path) -> str:
    """마크다운 파일 읽기 및 HTML 변환 후 텍스트 추출"""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # markdown → html → text
    html = markdown(raw)
    text = BeautifulSoup(html, "html.parser").get_text("\n")
    return text

def read_docx(path: Path) -> str:
    """Word 문서 읽기"""
    doc = docx.Document(str(path))
    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paras)

def read_xlsx(path: Path) -> str:
    """Excel 파일 읽기 - 시트별로 표를 간단히 텍스트로 직렬화"""
    xls = pd.ExcelFile(path)
    out = []
    for sheet in xls.sheet_names:
        df = xls.parse(sheet).fillna("")
        out.append(f"[Sheet] {sheet}")
        # 헤더 포함 row 단위 직렬화
        cols = [str(c) for c in df.columns]
        out.append(" | ".join(cols))
        for _, row in df.iterrows():
            out.append(" | ".join(str(x) for x in row.tolist()))
    return "\n".join(out)

def load_and_extract(path: Path) -> str:
    """파일 확장자에 따라 적절한 파서로 텍스트 추출"""
    ext = path.suffix.lower()
    if ext == ".txt":
        return read_txt(path)
    if ext == ".md":
        return read_md(path)
    if ext == ".docx":
        return read_docx(path)
    if ext == ".xlsx":
        return read_xlsx(path)
    return ""  # 비대상 포맷은 스킵

def chunk_text(text: str, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """텍스트를 청크 단위로 분할"""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks

def main():
    """메인 인덱싱 파이프라인"""
    print("문서 수집 및 파싱 시작...")
    
    # 지원하는 파일 형식들 수집
    files = []
    for ext in ("*.txt","*.md","*.docx","*.xlsx"):
        files.extend(glob.glob(str(DATA_DIR / ext)))
    files = [Path(f) for f in files]
    
    if not files:
        print(f"❌ {DATA_DIR} 디렉터리에 지원하는 파일이 없습니다.")
        print("지원 형식: .txt, .md, .docx, .xlsx")
        return

    print(f"📁 발견된 파일: {len(files)}개")
    for f in files:
        print(f"  - {f.name}")

    # 임베딩 모델 로드
    print(f"🤖 임베딩 모델 로딩: {EMB_MODEL_NAME}")
    model = SentenceTransformer(EMB_MODEL_NAME)
    
    vectors = []
    metadatas = []
    corpus_texts = []

    uid = 0
    for i, f in enumerate(files):
        print(f"파싱 중... ({i+1}/{len(files)}) {f.name}")
        text = load_and_extract(f)
        if not text: 
            print(f"⚠️  {f.name}: 텍스트 추출 실패")
            continue
            
        chunks = chunk_text(text)
        print(f"📄 {f.name}: {len(chunks)}개 청크 생성")
        
        for i, ch in enumerate(chunks):
            meta = {
                "uid": uid,
                "source": f.name,
                "chunk_id": i,
                "path": str(f.resolve())
            }
            corpus_texts.append(ch)
            metadatas.append(meta)
            uid += 1

    print(f"✅ 총 청크 수: {len(corpus_texts)}")
    if not corpus_texts:
        print("❌ 청크가 생성되지 않았습니다. ./data에 파일을 넣고 다시 실행하세요.")
        return

    print("🔄 임베딩 생성 중...")
    emb = model.encode(corpus_texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    emb = np.array(emb).astype("float32")

    print("🔍 FAISS 인덱스 구축 중...")
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)  # 코사인 유사도용(정규화했으므로 내적)
    index.add(emb)

    # 인덱스 저장
    faiss.write_index(index, str(INDEX_DIR / "faiss.index"))
    with open(INDEX_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump({"metas": metadatas, "texts": corpus_texts}, f, ensure_ascii=False)

    print("✅ 완료! 인덱스가 ./index에 저장되었습니다.")
    print(f"📊 통계:")
    print(f"  - 총 문서: {len(files)}개")
    print(f"  - 총 청크: {len(corpus_texts)}개")
    print(f"  - 임베딩 차원: {dim}")

if __name__ == "__main__":
    main()