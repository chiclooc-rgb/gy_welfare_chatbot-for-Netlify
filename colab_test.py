# Google Colab에서 실행할 코드
# 1. 새 노트북 생성: https://colab.research.google.com
# 2. 아래 코드를 복사해서 붙여넣기
# 3. 실행하면 바로 테스트 가능!

# 패키지 설치
!pip install fastapi uvicorn sentence-transformers faiss-cpu openai pyngrok

# 챗봇 코드
import json
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import faiss

app = FastAPI()

# 간단한 테스트 데이터
test_docs = [
    "다자녀 가정 지원: 셋째 자녀부터 양육비 월 10만원 지원",
    "임산부 지원: 임신 중 의료비 지원 및 출산 준비금 지급", 
    "육아휴직 지원: 최대 12개월 육아휴직 급여 지원",
    "보육료 지원: 어린이집 이용료 소득별 차등 지원"
]

# 키워드 확장 (개선된 기능!)
keyword_map = {
    "다자녀": ["셋째", "3자녀", "많은자녀"],
    "임산부": ["임신", "예비맘", "산모"],
    "지원": ["혜택", "보조", "급여", "수당"]
}

def expand_query(query):
    for keyword, synonyms in keyword_map.items():
        if keyword in query:
            query += " " + " ".join(synonyms)
    return query

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(req: QuestionRequest):
    # 쿼리 확장 적용!
    expanded_query = expand_query(req.question)
    
    # 간단한 키워드 매칭
    scores = []
    for i, doc in enumerate(test_docs):
        score = 0
        for word in expanded_query.split():
            if word in doc:
                score += 1
        scores.append((i, score, doc))
    
    # 점수순 정렬
    scores.sort(key=lambda x: x[1], reverse=True)
    best_match = scores[0]
    
    if best_match[1] > 0:
        answer = f"관련 정보를 찾았습니다: {best_match[2]}"
        
        # 추가 질문 제안
        suggestions = [
            "더 자세한 신청 방법이 궁금하신가요?",
            "다른 지원 프로그램도 알아보시겠어요?",
            "소득 기준이 궁금하신가요?"
        ]
        answer += f"\n\n💡 추가 질문: {suggestions[best_match[0] % len(suggestions)]}"
    else:
        answer = "죄송합니다. 관련 정보를 찾을 수 없습니다."
    
    return {
        "answer": answer,
        "expanded_query": expanded_query,
        "original_query": req.question
    }

@app.get("/")
def home():
    return {"message": "🎉 챗봇이 정상 작동합니다!", "test_url": "/ask"}

# ngrok으로 외부 접속 가능하게 하기
from pyngrok import ngrok
import uvicorn

# 터널 생성
public_url = ngrok.connect(8000)
print(f"🌐 공개 URL: {public_url}")

# 서버 실행
uvicorn.run(app, host="0.0.0.0", port=8000)


