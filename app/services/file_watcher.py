import os
import time
from PyQt6.QtCore import QThread, pyqtSignal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogEventHandler(FileSystemEventHandler):
    """
    Watchdog 이벤트 핸들러
    파일 변경(modified) 이벤트가 발생했을 때만 새로운 로그를 읽어옵니다.
    """
    def __init__(self, file_path, callback):
        self.file_path = os.path.abspath(file_path)
        self.callback = callback
        self._file = None
        self._open_file()

    def _open_file(self):
        """파일을 열고 포인터를 끝으로 이동"""
        try:
            if self._file:
                self._file.close()
            
            if os.path.exists(self.file_path):
                self._file = open(self.file_path, 'r', encoding='utf-8')
                self._file.seek(0, os.SEEK_END)  # 파일 끝으로 이동 (Tail -f)
        except Exception as e:
            print(f"File Open Error: {e}")

    def on_modified(self, event):
        """파일 수정 이벤트 발생 시 호출"""
        if os.path.abspath(event.src_path) == self.file_path:
            self._read_new_lines()

    def on_created(self, event):
        """파일이 생성/재생성(로테이션) 되었을 때 호출"""
        if os.path.abspath(event.src_path) == self.file_path:
            self._open_file()

    def _read_new_lines(self):
        """새로 추가된 라인을 읽어서 콜백으로 전달"""
        if not self._file:
            return

        while True:
            line = self._file.readline()
            if not line:
                break
            self.callback(line.strip())

    def close(self):
        if self._file:
            self._file.close()

class LogFileWatcher(QThread):
    # 새로운 로그 라인이 발견되면 시그널 발생
    log_received = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._is_running = True
        self.observer = None
        self.event_handler = None

    def run(self):
        """Watchdog Observer 시작"""
        # 파일이 없으면 빈 파일 생성 (기존 로직 유지)
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                f.write("")

        # 감시할 디렉토리 경로 설정
        dir_path = os.path.dirname(os.path.abspath(self.file_path))

        # 핸들러 및 옵저버 초기화
        self.event_handler = LogEventHandler(self.file_path, self._on_log_received)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, dir_path, recursive=False)
        self.observer.start()

        # 스레드 유지 (Observer는 별도 스레드에서 돌지만, QThread가 종료되지 않도록 유지)
        try:
            while self._is_running:
                time.sleep(1)
        except Exception as e:
            print(f"Watcher Error: {e}")
        finally:
            self._cleanup()

    def _on_log_received(self, line):
        """핸들러로부터 받은 로그를 Qt 시그널로 전송"""
        if line:
            self.log_received.emit(line)

    def _cleanup(self):
        """자원 정리"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        if self.event_handler:
            self.event_handler.close()

    def stop(self):
        """감시 종료 요청"""
        self._is_running = False
        # sleep 중인 루프가 1초 뒤에 깨어나면서 종료됨