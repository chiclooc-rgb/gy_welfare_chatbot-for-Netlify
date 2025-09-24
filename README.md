# 🤖 RAG 챗봇 - 생애복지플랫폼

문서 기반 질의응답 시스템으로, txt, md, docx, xlsx 파일을 파싱하여 RAG(Retrieval-Augmented Generation) 방식으로 답변을 제공합니다.

## ✨ 주요 기능

- 📄 **다양한 문서 형식 지원**: txt, md, docx, xlsx 파일 파싱
- 🔍 **지능형 검색**: 벡터 유사도 기반 문서 검색
- 💬 **AI 답변 생성**: OpenAI GPT 모델을 활용한 근거 기반 답변
- 🌐 **웹 인터페이스**: 사용자 친화적인 웹 UI
- 📊 **실시간 통계**: 문서 및 청크 수 표시

## 🏗️ 아키텍처

```
문서 파싱 → 텍스트 청킹 → 임베딩 생성 → 벡터 인덱싱 → 유사도 검색 → LLM 답변 생성
```

- **임베딩 모델**: sentence-transformers/all-MiniLM-L6-v2
- **벡터 DB**: FAISS (로컬 파일 기반)
- **LLM**: OpenAI GPT-4o-mini
- **백엔드**: FastAPI
- **프론트엔드**: HTML + JavaScript

## 📁 프로젝트 구조

```
welfare_chatbot/
├── data/                 # 원본 문서 저장 폴더
├── index/               # 인덱스 및 메타데이터 저장
├── frontend/            # 웹 UI
│   └── index.html
├── ingest.py            # 문서 파싱 및 인덱싱
├── app.py              # FastAPI 서버
├── ftp_server.py       # FTP 서버
├── ftp_client_test.py  # FTP 클라이언트 테스트
├── start_ftp_server.bat # FTP 서버 시작 배치 파일
├── test_ftp_client.bat  # FTP 클라이언트 테스트 배치 파일
├── requirements.txt    # Python 패키지 의존성
├── env.example         # 환경변수 템플릿
└── README.md
```

## 🚀 빠른 시작

### 방법 1: 간단한 버전 (권장 - 패키지 설치 문제 없음)

#### 1. 문서 준비
`data/` 폴더에 질의응답에 사용할 문서들을 넣어주세요:
- `.txt` - 텍스트 파일
- `.md` - 마크다운 파일

#### 2. 인덱싱
```bash
python simple_ingest.py
```

#### 3. 서버 실행
```bash
python simple_app.py
```

#### 4. 웹 접속
브라우저에서 `http://localhost:8000` 접속

### 방법 2: 완전한 버전 (AI 임베딩 + LLM)

#### 1. 환경 설정
```bash
# Python 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp env.example .env
# .env 파일을 열어 OPENAI_API_KEY를 설정하세요
```

#### 2. 문서 준비
`data/` 폴더에 질의응답에 사용할 문서들을 넣어주세요:
- `.txt` - 텍스트 파일
- `.md` - 마크다운 파일  
- `.docx` - Word 문서
- `.xlsx` - Excel 파일

#### 3. 인덱싱
```bash
python ingest.py
```

#### 4. 서버 실행
```bash
python app.py
# 또는
uvicorn app:app --reload
```

#### 5. 웹 접속
브라우저에서 `http://localhost:8000` 접속

## 📁 FTP 서버

프로젝트에 간단한 FTP 서버가 포함되어 있어 파일 공유 및 원격 접근이 가능합니다.

### FTP 서버 시작

#### 방법 1: 배치 파일 사용 (Windows)
```bash
start_ftp_server.bat
```

#### 방법 2: Python 직접 실행
```bash
python ftp_server.py
```

#### 방법 3: 커스텀 설정
```bash
python ftp_server.py --host 0.0.0.0 --port 21 --username myuser --password mypass --directory ./data
```

### FTP 서버 옵션

- `--host`: 서버 호스트 (기본값: 127.0.0.1)
- `--port`: 서버 포트 (기본값: 2121)
- `--username`: FTP 사용자명 (기본값: admin)
- `--password`: FTP 비밀번호 (기본값: admin)
- `--directory`: FTP 루트 디렉토리 (기본값: 현재 디렉토리)

### FTP 클라이언트 테스트

FTP 서버가 정상 작동하는지 테스트하려면:

#### 방법 1: 배치 파일 사용 (Windows)
```bash
test_ftp_client.bat
```

#### 방법 2: Python 직접 실행
```bash
python ftp_client_test.py
```

### FTP 접속 정보

- **호스트**: 127.0.0.1 (또는 설정한 호스트)
- **포트**: 2121 (또는 설정한 포트)
- **사용자명**: admin (또는 설정한 사용자명)
- **비밀번호**: admin (또는 설정한 비밀번호)
- **익명 접속**: 가능 (읽기 전용)

### FTP 클라이언트 프로그램

다음 FTP 클라이언트 프로그램으로 접속할 수 있습니다:
- **FileZilla** (무료, GUI)
- **WinSCP** (Windows, 무료)
- **Cyberduck** (무료, 크로스 플랫폼)
- **Windows 탐색기** (ftp://127.0.0.1:2121)

## 🔧 설정 옵션

### ingest.py 설정

```python
EMB_MODEL_NAME = "all-MiniLM-L6-v2"  # 임베딩 모델
CHUNK_SIZE = 1000                    # 청크 크기 (문자)
CHUNK_OVERLAP = 200                  # 청크 겹침 (문자)
```

### app.py 설정

```python
TOP_K = 5                           # 검색할 상위 K개 문서
EMB_MODEL_NAME = "all-MiniLM-L6-v2" # 임베딩 모델
```

## 📝 사용법

1. **문서 업로드**: `data/` 폴더에 문서 파일들을 넣습니다
2. **인덱싱**: `python ingest.py` 실행하여 문서를 인덱싱합니다
3. **서버 시작**: `python app.py` 실행하여 웹 서버를 시작합니다
4. **질의**: 웹 브라우저에서 질문을 입력하고 답변을 받습니다

## 🔍 API 엔드포인트

- `GET /` - 웹 UI
- `POST /ask` - 질의응답 API
- `GET /health` - 서버 상태 확인
- `GET /stats` - 인덱스 통계

### 질의응답 API 사용 예시

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "복지 혜택은 무엇인가요?"}'
```

## 🛠️ 고급 설정

### 다른 LLM 사용

OpenAI 대신 다른 LLM을 사용하려면 `app.py`의 LLM 호출 부분을 수정하세요:

```python
# Anthropic Claude 예시
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### 벡터 DB 변경

FAISS 대신 다른 벡터 DB를 사용하려면:

- **Supabase (pgvector)**: PostgreSQL 기반
- **Pinecone**: 클라우드 벡터 DB
- **Weaviate**: 오픈소스 벡터 DB

### 청킹 전략 개선

현재는 문자 기반 청킹을 사용합니다. 더 정교한 청킹을 위해:

- 문단/조문 단위 분할
- 표 헤더+행 단위 청킹 (xlsx)
- 토큰 길이 기반 청킹

## 🚨 주의사항

- **API 키 보안**: `.env` 파일을 Git에 커밋하지 마세요
- **문서 접근권한**: 업로드된 문서의 접근 권한을 확인하세요
- **메모리 사용량**: 대용량 문서 처리 시 메모리 사용량을 모니터링하세요

## 🔄 업데이트

문서를 추가하거나 수정한 후:

```bash
python ingest.py  # 인덱스 재생성
```

## 📈 성능 최적화

- **배치 크기 조정**: `ingest.py`의 `batch_size` 파라미터
- **청크 크기 최적화**: 문서 유형에 따라 `CHUNK_SIZE` 조정
- **캐싱**: 임베딩 모델 로딩 시간 단축

## 🐛 문제 해결

### 인덱스 로드 실패
```bash
# 인덱스 재생성
rm -rf index/
python ingest.py
```

### OpenAI API 오류
- API 키가 올바른지 확인
- API 사용량 한도 확인
- 네트워크 연결 상태 확인

### 메모리 부족
- 청크 크기 줄이기
- 배치 크기 줄이기
- 더 작은 임베딩 모델 사용

## 📞 지원

문제가 발생하면 이슈를 등록하거나 개발팀에 문의하세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
