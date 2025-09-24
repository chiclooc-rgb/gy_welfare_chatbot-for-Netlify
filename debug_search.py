#!/usr/bin/env python3
# debug_search.py - Search functionality test

import json
from pathlib import Path

def load_documents():
    """문서 로드 테스트"""
    index_dir = Path("index")
    try:
        with open(index_dir / "simple_meta.json", "r", encoding="utf-8") as f:
            store = json.load(f)
        metas = store["metas"]
        texts = store["texts"]
        print(f"✅ 문서 로드 완료: {len(texts)}개 청크")
        
        # 첫 5개 텍스트 샘플 출력
        print("\n📄 첫 5개 텍스트 샘플:")
        for i, text in enumerate(texts[:5]):
            print(f"{i+1}. {text[:100]}...")
            
        # 다자녀 관련 검색 테스트
        print("\n🔍 '다자녀' 검색 테스트:")
        found_count = 0
        for i, text in enumerate(texts):
            if "다자녀" in text.lower():
                print(f"  발견 {i+1}: {text[:200]}...")
                found_count += 1
        print(f"총 {found_count}개 청크에서 '다자녀' 발견")
        
        # 자녀 관련 검색 테스트
        print("\n🔍 '자녀' 검색 테스트:")
        found_count = 0
        for i, text in enumerate(texts):
            if "자녀" in text.lower():
                print(f"  발견 {i+1}: {text[:200]}...")
                found_count += 1
                if found_count >= 3:  # 처음 3개만 출력
                    break
        print(f"총 {found_count}개 청크에서 '자녀' 발견")
        
        return texts, metas
        
    except Exception as e:
        print(f"❌ 문서 로드 실패: {e}")
        return [], []

def expand_query(query):
    """쿼리 확장 테스트"""
    KEYWORD_EXPANSION = {
        "다자녀가정": ["다자녀", "셋째아이", "3자녀", "3명 이상", "많은 자녀", "자녀 3명", "세 자녀"],
        "다자녀": ["다자녀가정", "셋째아이", "3자녀", "3명 이상", "많은 자녀"],
        "혜택": ["지원", "보조", "급여", "수당", "할인", "감면", "우대", "바우처"],
        "지원": ["혜택", "보조", "급여", "수당", "지원금", "보조금"],
    }
    
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
        expanded_query = f"{query} {' '.join(unique_terms[:5])}"
        return expanded_query
    
    return query

def search_documents(query, texts, metas, top_k=5):
    """문서 검색 테스트"""
    expanded_query = expand_query(query)
    print(f"🔍 원본 쿼리: {query}")
    print(f"🔍 확장된 쿼리: {expanded_query}")
    
    scores = []
    keywords = expanded_query.lower().split()
    
    for i, text in enumerate(texts):
        score = 0
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                score += text_lower.count(keyword)
        
        if score > 0:
            scores.append({
                "rank": i + 1,
                "score": score,
                "text": text,
                "source": metas[i]["source"],
                "chunk_id": metas[i]["chunk_id"]
            })
    
    # 점수순 정렬
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]

if __name__ == "__main__":
    print("🚀 Search Debug 시작")
    
    # 문서 로드 테스트
    texts, metas = load_documents()
    
    if not texts:
        print("❌ 문서가 로드되지 않았습니다.")
        exit(1)
    
    # 검색 테스트
    test_queries = [
        "다자녀가정 혜택",
        "자녀 지원",
        "임신 지원",
        "복지 혜택"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"🔍 '{query}' 검색 결과:")
        results = search_documents(query, texts, metas)
        
        if results:
            for i, result in enumerate(results):
                print(f"\n{i+1}. 점수: {result['score']}")
                print(f"   출처: {result['source']}#{result['chunk_id']}")
                print(f"   내용: {result['text'][:200]}...")
        else:
            print("   검색 결과 없음")
    
    print(f"\n🔥 Debug 완료")


