# Netlify 배포 가이드

## 🚀 배포 준비사항

### 1. 필수 파일 확인
- ✅ `netlify.toml` - Netlify 설정 파일
- ✅ `requirements.txt` - Python 의존성
- ✅ `runtime.txt` - Python 버전 (3.10.13)
- ✅ `.python-version` - pyenv 호환 버전 파일
- ✅ `build.sh` - 빌드 스크립트
- ✅ `netlify/functions/api.py` - 서버리스 함수

### 2. Netlify 환경변수 설정

Netlify 대시보드에서 다음 환경변수들을 설정하세요:

```
OPENAI_API_KEY=your_actual_openai_api_key
ADMIN_PASSWORD=your_secure_password
NETLIFY=true
PYTHON_VERSION=3.10.13
```

### 3. 배포 순서

1. **GitHub/GitLab에 코드 푸시**
   ```bash
   git add .
   git commit -m "Add Netlify configuration"
   git push origin main
   ```

2. **Netlify에서 사이트 생성**
   - New site from Git 선택
   - 저장소 연결
   - Build settings:
     - Build command: `chmod +x build.sh && ./build.sh`
     - Publish directory: `frontend`
     - Functions directory: `netlify/functions`

3. **환경변수 설정**
   - Site settings > Environment variables
   - 위의 환경변수들 추가

4. **배포 트리거**
   - Deploy site 버튼 클릭 또는 코드 푸시

## 🔧 문제 해결

### Python 버전 오류
만약 Python 3.13 관련 오류가 발생하면:
1. `runtime.txt`에서 `python-3.10.13` 확인
2. `.python-version`에서 `3.10.13` 확인
3. Netlify build logs에서 실제 사용되는 Python 버전 확인

### 의존성 설치 실패
1. `requirements.txt`의 패키지 버전 확인
2. Netlify build logs에서 구체적인 오류 메시지 확인
3. 필요시 패키지 버전 다운그레이드

### 함수 실행 오류
1. Netlify Functions logs 확인
2. `netlify/functions/api.py`의 import 경로 확인
3. 환경변수 설정 확인

## 📋 API 엔드포인트

배포 후 다음 엔드포인트들을 사용할 수 있습니다:

- `GET /` - 메인 페이지
- `POST /api/new-session` - 새 세션 생성
- `POST /api/ask` - 질문하기
- `GET /api/documents` - 문서 목록
- `GET /api/health` - 헬스 체크

## 🔒 보안 사항

1. **API 키 보안**
   - 환경변수로만 설정
   - 코드에 하드코딩하지 말 것

2. **관리자 기능**
   - 서버리스 환경에서는 파일 업로드/삭제 기능 비활성화
   - 읽기 전용 운영 권장

## 📊 모니터링

- Netlify Analytics에서 사용량 모니터링
- Function logs에서 오류 추적
- OpenAI 사용량 별도 모니터링 필요
