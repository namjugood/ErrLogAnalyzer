import time
import os
from PyQt6.QtCore import QThread, pyqtSignal

class LogFileWatcher(QThread):
    # 새로운 로그 라인이 발견되면 시그널 발생
    log_received = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._is_running = True

    def run(self):
        """파일의 끝을 계속 감시 (Tail -f 구현)"""
        if not os.path.exists(self.file_path):
            # 파일이 없으면 생성해둠 (테스트용)
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                f.write("")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            # 파일 끝으로 이동
            f.seek(0, os.SEEK_END)
            
            while self._is_running:
                line = f.readline()
                if not line:
                    time.sleep(0.1) # 데이터가 없으면 잠시 대기
                    continue
                
                # 라인이 있으면 시그널 전송
                self.log_received.emit(line.strip())

    def stop(self):
        self._is_running = False
        self.wait()