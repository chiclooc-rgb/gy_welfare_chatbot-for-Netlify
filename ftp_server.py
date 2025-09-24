#!/usr/bin/env python3
"""
간단한 FTP 서버
pyftpdlib을 사용하여 로컬 FTP 서버를 실행합니다.
"""

import os
import sys
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_ftp_server(host="127.0.0.1", port=2121, username="admin", password="admin", directory="."):
    """
    FTP 서버를 생성하고 실행합니다.
    
    Args:
        host (str): 서버 호스트 (기본값: 127.0.0.1)
        port (int): 서버 포트 (기본값: 2121)
        username (str): FTP 사용자명 (기본값: admin)
        password (str): FTP 비밀번호 (기본값: admin)
        directory (str): FTP 루트 디렉토리 (기본값: 현재 디렉토리)
    """
    
    # 현재 디렉토리를 절대 경로로 변환
    ftp_directory = os.path.abspath(directory)
    
    # FTP 디렉토리가 존재하는지 확인
    if not os.path.exists(ftp_directory):
        logger.error(f"FTP 디렉토리가 존재하지 않습니다: {ftp_directory}")
        return False
    
    # 인증자 생성
    authorizer = DummyAuthorizer()
    
    # 사용자 추가 (읽기/쓰기 권한)
    authorizer.add_user(username, password, ftp_directory, perm="elradfmwMT")
    
    # 익명 사용자 추가 (읽기 전용)
    authorizer.add_anonymous(ftp_directory, perm="elr")
    
    # FTP 핸들러 생성
    handler = FTPHandler
    handler.authorizer = authorizer
    
    # 서버 생성
    server = FTPServer((host, port), handler)
    
    # 서버 설정
    server.max_cons = 256
    server.max_cons_per_ip = 5
    
    logger.info(f"FTP 서버가 시작되었습니다.")
    logger.info(f"호스트: {host}")
    logger.info(f"포트: {port}")
    logger.info(f"사용자명: {username}")
    logger.info(f"비밀번호: {password}")
    logger.info(f"FTP 루트 디렉토리: {ftp_directory}")
    logger.info(f"익명 접속 가능: 예")
    logger.info("서버를 중지하려면 Ctrl+C를 누르세요.")
    
    try:
        # 서버 시작
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("FTP 서버를 중지합니다...")
        server.close_all()
        return True
    except Exception as e:
        logger.error(f"FTP 서버 실행 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="간단한 FTP 서버")
    parser.add_argument("--host", default="127.0.0.1", help="서버 호스트 (기본값: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2121, help="서버 포트 (기본값: 2121)")
    parser.add_argument("--username", default="admin", help="FTP 사용자명 (기본값: admin)")
    parser.add_argument("--password", default="admin", help="FTP 비밀번호 (기본값: admin)")
    parser.add_argument("--directory", default=".", help="FTP 루트 디렉토리 (기본값: 현재 디렉토리)")
    
    args = parser.parse_args()
    
    # FTP 서버 시작
    success = create_ftp_server(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        directory=args.directory
    )
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()


