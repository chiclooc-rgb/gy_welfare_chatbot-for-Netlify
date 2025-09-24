@echo off
echo FTP 클라이언트 테스트를 시작합니다...
echo.
echo 사용법:
echo   python ftp_client_test.py [옵션]
echo.
echo 옵션:
echo   --host HOST        FTP 서버 호스트 (기본값: 127.0.0.1)
echo   --port PORT        FTP 서버 포트 (기본값: 2121)
echo   --username USER    FTP 사용자명 (기본값: admin)
echo   --password PASS    FTP 비밀번호 (기본값: admin)
echo.
echo 예시:
echo   python ftp_client_test.py --port 21 --username myuser --password mypass
echo.
pause
python ftp_client_test.py


