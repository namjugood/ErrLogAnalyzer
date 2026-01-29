# app/ui/main_window.py

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QStackedWidget, QFrame, QLabel)
from PyQt6.QtCore import Qt
from app.ui.styles import DARK_THEME
from app.ui.dashboard import DashboardView
from app.ui.report_view import ReportView       
from app.ui.settings_view import SettingsView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BXM Error Analyzer - v1.0.0")
        self.resize(1280, 800)
        self.setStyleSheet(DARK_THEME)
        
        # 메인 레이아웃 컨테이너
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 사이드바
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # 2. 메인 컨텐츠 영역
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)

        # 화면 등록
        self.dashboard_view = DashboardView()
        self.report_view = ReportView()
        self.settings_view = SettingsView() 

        self.content_area.addWidget(self.dashboard_view) # Index 0
        self.content_area.addWidget(self.report_view)    # Index 1
        self.content_area.addWidget(self.settings_view)  # Index 2

        # [수정] 설정 저장 시 대시보드 새로고침 연결
        self.settings_view.settings_saved.connect(self.dashboard_view.refresh_dashboard)

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(170)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        
        # 로고 영역
        title_lbl = QLabel("  BXM Error Analyzer")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 20px;")
        layout.addWidget(title_lbl)

        # 메뉴 버튼
        self.btn_dash = self.create_nav_btn("대시보드", 0)
        self.btn_report = self.create_nav_btn("리포트 이력", 1)
        self.btn_settings = self.create_nav_btn("설정", 2)
        
        layout.addWidget(self.btn_dash)
        layout.addWidget(self.btn_report)
        layout.addWidget(self.btn_settings)
        layout.addStretch()
        
        return sidebar

    def create_nav_btn(self, text, index):
        btn = QPushButton(text)
        btn.setObjectName("SideBtn")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        if index == 0: btn.setChecked(True)
        btn.clicked.connect(lambda: self.content_area.setCurrentIndex(index))
        return btn