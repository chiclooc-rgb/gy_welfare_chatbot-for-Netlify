# file_watcher.py
import time
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from typing import Set
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentWatcher(FileSystemEventHandler):
    """문서 폴더 감시 및 자동 인덱싱"""
    
    def __init__(self, data_dir: Path, callback_func):
        self.data_dir = data_dir
        self.callback_func = callback_func
        self.supported_extensions = {'.txt', '.md', '.docx', '.xlsx', '.pdf'}
        self.pending_files: Set[Path] = set()
        self.processing = False
        
    def on_created(self, event):
        """파일 생성 시 호출"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_extensions:
                logger.info(f"📁 새 파일 감지: {file_path.name}")
                self.pending_files.add(file_path)
                self._schedule_processing()
    
    def on_modified(self, event):
        """파일 수정 시 호출"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_extensions:
                logger.info(f"📝 파일 수정 감지: {file_path.name}")
                self.pending_files.add(file_path)
                self._schedule_processing()
    
    def on_moved(self, event):
        """파일 이동/이름변경 시 호출"""
        if not event.is_directory:
            new_path = Path(event.dest_path)
            if new_path.suffix.lower() in self.supported_extensions:
                logger.info(f"📦 파일 이동 감지: {new_path.name}")
                self.pending_files.add(new_path)
                self._schedule_processing()
    
    def _schedule_processing(self):
        """파일 처리 스케줄링 (중복 방지)"""
        if not self.processing:
            self.processing = True
            # 3초 후 처리 (파일 쓰기 완료 대기)
            threading.Timer(3.0, self._process_pending_files).start()
    
    def _process_pending_files(self):
        """대기 중인 파일들 처리"""
        if self.pending_files:
            files_to_process = list(self.pending_files)
            self.pending_files.clear()
            
            # 실제로 존재하는 파일들만 필터링
            existing_files = [f for f in files_to_process if f.exists()]
            
            if existing_files:
                logger.info(f"🔄 {len(existing_files)}개 파일 자동 인덱싱 시작...")
                try:
                    # 비동기 콜백 실행
                    asyncio.create_task(self.callback_func(existing_files))
                except Exception as e:
                    logger.error(f"❌ 자동 인덱싱 오류: {e}")
        
        self.processing = False

class FileWatcherManager:
    """파일 워쳐 관리자"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.observer = None
        self.watcher = None
        self.callback_func = None
        
    def set_callback(self, callback_func):
        """인덱싱 콜백 함수 설정"""
        self.callback_func = callback_func
        
    def start_watching(self):
        """파일 감시 시작"""
        if self.observer is not None:
            logger.warning("⚠️ 파일 워쳐가 이미 실행 중입니다.")
            return
            
        if not self.callback_func:
            logger.error("❌ 콜백 함수가 설정되지 않았습니다.")
            return
            
        # 데이터 폴더 생성
        self.data_dir.mkdir(exist_ok=True)
        
        # 워쳐 및 관찰자 생성
        self.watcher = DocumentWatcher(self.data_dir, self.callback_func)
        self.observer = Observer()
        self.observer.schedule(self.watcher, str(self.data_dir), recursive=False)
        
        # 감시 시작
        self.observer.start()
        logger.info(f"👁️ 파일 워쳐 시작: {self.data_dir}")
        
    def stop_watching(self):
        """파일 감시 중지"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.watcher = None
            logger.info("🛑 파일 워쳐 중지")
            
    def is_watching(self):
        """감시 상태 확인"""
        return self.observer is not None and self.observer.is_alive()

# 전역 파일 워쳐 인스턴스
file_watcher_manager = None

def init_file_watcher(data_dir: Path, callback_func):
    """파일 워쳐 초기화"""
    global file_watcher_manager
    
    file_watcher_manager = FileWatcherManager(data_dir)
    file_watcher_manager.set_callback(callback_func)
    
    return file_watcher_manager

def start_file_watcher():
    """파일 워쳐 시작"""
    if file_watcher_manager:
        file_watcher_manager.start_watching()
        return True
    return False

def stop_file_watcher():
    """파일 워쳐 중지"""
    if file_watcher_manager:
        file_watcher_manager.stop_watching()
        return True
    return False

def get_watcher_status():
    """워쳐 상태 반환"""
    if file_watcher_manager:
        return {
            "active": file_watcher_manager.is_watching(),
            "data_dir": str(file_watcher_manager.data_dir)
        }
    return {"active": False, "data_dir": None}

