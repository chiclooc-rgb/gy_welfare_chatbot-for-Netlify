#!/usr/bin/env python3
"""
FTP 클라이언트 테스트 스크립트
FTP 서버에 연결하여 파일 업로드/다운로드를 테스트합니다.
"""

import ftplib
import os
import tempfile
from datetime import datetime

def test_ftp_connection(host="127.0.0.1", port=2121, username="admin", password="admin"):
    """
    FTP 서버 연결을 테스트합니다.
    
    Args:
        host (str): FTP 서버 호스트
        port (int): FTP 서버 포트
        username (str): FTP 사용자명
        password (str): FTP 비밀번호
    """
    
    try:
        # FTP 연결
        print(f"FTP 서버에 연결 중... ({host}:{port})")
        ftp = ftplib.FTP()
        ftp.connect(host, port)
        ftp.login(username, password)
        
        print("✓ FTP 서버 연결 성공!")
        
        # 현재 디렉토리 확인
        current_dir = ftp.pwd()
        print(f"현재 디렉토리: {current_dir}")
        
        # 파일 목록 확인
        print("\n파일 목록:")
        files = ftp.nlst()
        for file in files:
            print(f"  - {file}")
        
        # 테스트 파일 업로드
        test_content = f"FTP 테스트 파일\n생성 시간: {datetime.now()}\n"
        test_filename = "ftp_test.txt"
        
        print(f"\n테스트 파일 업로드 중... ({test_filename})")
        ftp.storbinary(f"STOR {test_filename}", test_content.encode())
        print("✓ 파일 업로드 성공!")
        
        # 업로드된 파일 확인
        files_after = ftp.nlst()
        if test_filename in files_after:
            print(f"✓ 업로드된 파일 확인됨: {test_filename}")
        
        # 테스트 파일 다운로드
        print(f"\n테스트 파일 다운로드 중... ({test_filename})")
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            ftp.retrbinary(f"RETR {test_filename}", temp_file.write)
            temp_file_path = temp_file.name
        
        # 다운로드된 파일 내용 확인
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            downloaded_content = f.read()
        
        print("✓ 파일 다운로드 성공!")
        print(f"다운로드된 파일 내용:\n{downloaded_content}")
        
        # 임시 파일 삭제
        os.unlink(temp_file_path)
        
        # 업로드된 테스트 파일 삭제
        ftp.delete(test_filename)
        print(f"✓ 테스트 파일 삭제됨: {test_filename}")
        
        # 연결 종료
        ftp.quit()
        print("\n✓ FTP 연결이 정상적으로 종료되었습니다.")
        
        return True
        
    except ftplib.all_errors as e:
        print(f"✗ FTP 오류 발생: {e}")
        return False
    except Exception as e:
        print(f"✗ 예상치 못한 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FTP 클라이언트 테스트")
    parser.add_argument("--host", default="127.0.0.1", help="FTP 서버 호스트 (기본값: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2121, help="FTP 서버 포트 (기본값: 2121)")
    parser.add_argument("--username", default="admin", help="FTP 사용자명 (기본값: admin)")
    parser.add_argument("--password", default="admin", help="FTP 비밀번호 (기본값: admin)")
    
    args = parser.parse_args()
    
    print("=== FTP 클라이언트 테스트 ===")
    print(f"서버: {args.host}:{args.port}")
    print(f"사용자: {args.username}")
    print("=" * 30)
    
    success = test_ftp_connection(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password
    )
    
    if success:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 테스트 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main()


