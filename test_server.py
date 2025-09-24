from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>테스트 서버</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>🎉 서버가 정상적으로 작동합니다!</h1>
        <p>챗봇 테스트를 위한 기본 서버입니다.</p>
        <div style="background: #f0f0f0; padding: 20px; margin: 20px 0; border-radius: 8px;">
            <h2>✅ 확인 완료</h2>
            <ul>
                <li>FastAPI 서버 실행</li>
                <li>웹 페이지 렌더링</li>
                <li>한글 인코딩</li>
            </ul>
        </div>
        <p>이제 챗봇을 실행할 준비가 되었습니다!</p>
    </body>
    </html>
    """

@app.get("/test")
def test():
    return {"message": "서버가 정상적으로 작동중입니다!", "status": "OK"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 테스트 서버를 시작합니다...")
    print("📱 브라우저에서 http://localhost:8000 에 접속하세요")
    uvicorn.run(app, host="0.0.0.0", port=8000)


