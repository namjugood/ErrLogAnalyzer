# app/ui/splash_screen.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(450, 300)
        # 타이틀바 제거 (Frameless) 및 항상 위 설정
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui()

    def init_ui(self):
        # 메인 컨테이너 (둥근 모서리와 배경색 적용을 위함)
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 450, 300)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #0B0E14;
                border: 1px solid #374151;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 1. 로고/타이틀 영역
        title_lbl = QLabel("BXM Error Analyzer")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: white; font-size: 24px; font-weight: bold; border: none;")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("System Monitoring & Analysis Tool")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px; border: none;")
        layout.addWidget(sub_lbl)

        layout.addStretch()

        # 2. 상태 메시지
        self.status_lbl = QLabel("Initializing...")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_lbl.setStyleSheet("color: #60A5FA; font-size: 11px; font-weight: bold; border: none;")
        layout.addWidget(self.status_lbl)

        # 3. 진행바
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(6)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("""
            QProgressBar {
                background-color: #1F2937;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.pbar)

        # 버전 정보
        version_lbl = QLabel("v1.0.0")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_lbl.setStyleSheet("color: #4B5563; font-size: 10px; border: none; margin-top: 5px;")
        layout.addWidget(version_lbl)

    def update_progress(self, value, message):
        """진행률과 메시지를 업데이트하는 메서드"""
        self.pbar.setValue(value)
        self.status_lbl.setText(message)

    # [추가된 부분] 종료 메서드 구현
    def finish(self, window):
        """메인 윈도우가 준비되면 스플래시 스크린을 닫습니다."""
        self.close()