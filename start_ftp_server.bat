@echo off
echo FTP 서버를 시작합니다...
echo.
echo 사용법:
echo   python ftp_server.py [옵션]
echo.
echo 옵션:
echo   --host HOST        서버 호스트 (기본값: 127.0.0.1)
echo   --port PORT        서버 포트 (기본값: 2121)
echo   --username USER    FTP 사용자명 (기본값: admin)
echo   --password PASS    FTP 비밀번호 (기본값: admin)
echo   --directory DIR    FTP 루트 디렉토리 (기본값: 현재 디렉토리)
echo.
echo 예시:
echo   python ftp_server.py --port 21 --username myuser --password mypass
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.
pause
python ftp_server.py


