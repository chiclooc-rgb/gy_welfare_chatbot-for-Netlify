#!/bin/bash

# Netlify 빌드 스크립트
echo "🚀 Netlify 빌드 시작..."

# Python 버전 확인
echo "📍 Python 버전 확인..."
python --version
python -c "import sys; print(f'Python 경로: {sys.executable}')"

# 환경 변수 설정
export PYTHONPATH="${PWD}:${PYTHONPATH}"
export NETLIFY=true

echo "📦 Python 의존성 설치 중..."
pip install -r requirements.txt

echo "🔍 설치된 패키지 확인..."
pip list | grep -E "(fastapi|mangum|sentence-transformers|faiss)"

# 인덱스 및 데이터 파일 확인
echo "📄 필요한 파일들 확인..."
if [ -d "index" ]; then
    echo "✅ index 디렉토리 존재"
    ls -la index/
else
    echo "⚠️ index 디렉토리가 없습니다. 인덱스를 생성합니다..."
    mkdir -p index
    
    # 기본 인덱스 생성 (빈 인덱스)
    python -c "
import faiss
import json
import numpy as np
from pathlib import Path

# 빈 FAISS 인덱스 생성
dimension = 768  # ko-sroberta-multitask 모델의 차원
index = faiss.IndexFlatIP(dimension)
faiss.write_index(index, 'index/faiss.index')

# 빈 메타데이터 생성
meta_data = {'metas': [], 'texts': []}
with open('index/meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta_data, f, ensure_ascii=False)

print('✅ 기본 인덱스 파일이 생성되었습니다.')
"
fi

if [ -d "data" ]; then
    echo "✅ data 디렉토리 존재"
    ls -la data/
else
    echo "⚠️ data 디렉토리가 없습니다. 생성합니다..."
    mkdir -p data
fi

# 정적 파일 준비
echo "🌐 정적 파일 준비..."
if [ ! -d "frontend" ]; then
    echo "⚠️ frontend 디렉토리가 없습니다. 기본 인덱스 파일을 생성합니다..."
    mkdir -p frontend
    
    cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>복지 상담 챗봇</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        .api-info {
            background: #f0f8ff;
            border: 1px solid #2196f3;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 복지 상담 챗봇</h1>
        
        <div class="status">
            <h3>✅ 서비스 상태</h3>
            <p>서버리스 환경에서 실행 중입니다.</p>
            <p>API 엔드포인트를 통해 챗봇 서비스를 이용하실 수 있습니다.</p>
        </div>
        
        <div class="api-info">
            <h3>📋 API 사용법</h3>
            <p><strong>새 세션 생성:</strong></p>
            <p><code>POST /api/new-session</code></p>
            
            <p><strong>질문하기:</strong></p>
            <p><code>POST /api/ask</code></p>
            <pre>{
  "question": "다자녀가정 지원 정책이 무엇인가요?",
  "session_id": "session-id"
}</pre>
            
            <p><strong>문서 목록 확인:</strong></p>
            <p><code>GET /api/documents</code></p>
            
            <p><strong>헬스 체크:</strong></p>
            <p><code>GET /api/health</code></p>
        </div>
    </div>
</body>
</html>
EOF
fi

echo "✅ 빌드 완료!"
echo "📍 생성된 파일들:"
find . -name "*.py" -o -name "*.toml" -o -name "*.txt" -o -name "*.html" | head -20

