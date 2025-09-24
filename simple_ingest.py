#!/usr/bin/env python3
# simple_ingest.py - 간단한 버전의 인덱싱 스크립트

import os
import json
import re
import glob
from pathlib import Path

DATA_DIR = Path("data")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def read_txt(path: Path) -> str:
    """텍스트 파일 읽기"""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"텍스트 파일 읽기 실패 {path}: {e}")
        return ""

def read_md(path: Path) -> str:
    """마크다운 파일 읽기"""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        # 간단한 마크다운 처리 (BeautifulSoup 없이)
        text = re.sub(r'#+ ', '', raw)  # 헤더 제거
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 볼드 제거
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # 이탤릭 제거
        text = re.sub(r'`(.*?)`', r'\1', text)  # 코드 제거
        return text
    except Exception as e:
        print(f"마크다운 파일 읽기 실패 {path}: {e}")
        return ""

def load_and_extract(path: Path) -> str:
    """파일 확장자에 따라 적절한 파서로 텍스트 추출"""
    ext = path.suffix.lower()
    if ext == ".txt":
        return read_txt(path)
    elif ext == ".md":
        return read_md(path)
    else:
        print(f"지원하지 않는 파일 형식: {ext}")
        return ""

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
    """메인 인덱싱 파이프라인 (간단한 버전)"""
    print("=== 간단한 문서 인덱싱 시작 ===")
    
    # 지원하는 파일 형식들 수집
    files = []
    for ext in ("*.txt", "*.md"):
        files.extend(glob.glob(str(DATA_DIR / ext)))
    files = [Path(f) for f in files]
    
    if not files:
        print(f"❌ {DATA_DIR} 디렉터리에 지원하는 파일이 없습니다.")
        print("지원 형식: .txt, .md")
        return

    print(f"📁 발견된 파일: {len(files)}개")
    for f in files:
        print(f"  - {f.name}")

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
        
        for j, ch in enumerate(chunks):
            meta = {
                "uid": uid,
                "source": f.name,
                "chunk_id": j,
                "path": str(f.resolve())
            }
            corpus_texts.append(ch)
            metadatas.append(meta)
            uid += 1

    print(f"✅ 총 청크 수: {len(corpus_texts)}")
    if not corpus_texts:
        print("❌ 청크가 생성되지 않았습니다.")
        return

    # 간단한 메타데이터만 저장 (임베딩 없이)
    with open(INDEX_DIR / "simple_meta.json", "w", encoding="utf-8") as f:
        json.dump({"metas": metadatas, "texts": corpus_texts}, f, ensure_ascii=False)

    print("✅ 완료! 간단한 메타데이터가 ./index/simple_meta.json에 저장되었습니다.")
    print(f"📊 통계:")
    print(f"  - 총 문서: {len(files)}개")
    print(f"  - 총 청크: {len(corpus_texts)}개")

if __name__ == "__main__":
    main()

