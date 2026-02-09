# app/ui/dashboard.py

import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QPushButton, QTextEdit, QProgressBar,
                             QSpacerItem, QSizePolicy, QTabWidget, QScrollArea, 
                             QApplication, QDateEdit, QComboBox)
from PyQt6.QtCore import Qt, pyqtSlot, QDate, QTime
from PyQt6.QtGui import QColor, QFont, QTextCursor # QTextCursor 필수

from app.workers.monitor_worker import MonitorWorker
from app.ui.styles import DASHBOARD_STYLES

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = os.path.join("settings", "settings.json")
        self.channels = []
        
        self.workers = {}
        self.ui_items = {} 
        
        self.init_ui()
        self.refresh_dashboard()

    def load_channels_from_settings(self):
        if not os.path.exists(self.settings_file):
            return []
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("channels", [])
        except Exception as e:
            print(f"Error loading settings: {e}")
            return []

    def init_ui(self):
        self.setStyleSheet(DASHBOARD_STYLES)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(15)

        # 1. 상단 헤더
        main_layout.addWidget(self.create_header())

        # 2. 조회 기간 설정
        main_layout.addWidget(self.create_date_selector())

        # 3. 메인 컨텐츠
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # [좌측] 채널 리스트
        self.left_layout = QVBoxLayout()
        self.left_layout.setSpacing(10)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        left_widget = QWidget()
        left_widget.setObjectName("ScrollContents")
        left_widget.setLayout(self.left_layout)
        scroll.setWidget(left_widget)
        
        # [우측] 탭
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #374151; border-radius: 8px; background-color: #161B26; }
            QTabBar::tab { background: #1F2937; color: #9CA3AF; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #161B26; color: #60A5FA; font-weight: bold; border-bottom: 2px solid #60A5FA; }
        """)

        content_layout.addWidget(scroll, 4)
        content_layout.addWidget(self.tabs, 6)

        main_layout.addLayout(content_layout)

    def create_date_selector(self):
        container = QFrame()
        container.setObjectName("DateCard")
        container.setFixedHeight(60)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)

        icon_lbl = QLabel("🕒")
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
        title_lbl = QLabel("조회 기간 설정")
        title_lbl.setObjectName("DateLabel")
        
        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)

        now = QDate.currentDate()
        
        self.date_start = QDateEdit(now)
        self.date_start.setDisplayFormat("yyyy-MM-dd")
        self.date_start.setCalendarPopup(True)
        self.time_start = self.create_time_combo("00:00")
        
        self.date_end = QDateEdit(now)
        self.date_end.setDisplayFormat("yyyy-MM-dd")
        self.date_end.setCalendarPopup(True)
        self.time_end = self.create_time_combo("23:59")

        lbl_start = QLabel("Start:")
        lbl_start.setStyleSheet("color: #9CA3AF; font-weight: bold;")
        lbl_end = QLabel("End:")
        lbl_end.setStyleSheet("color: #9CA3AF; font-weight: bold;")
        lbl_tilde = QLabel("~")
        lbl_tilde.setStyleSheet("color: #6B7280; font-size: 16px; font-weight: bold;")

        layout.addStretch()
        layout.addWidget(lbl_start)
        layout.addWidget(self.date_start)
        layout.addWidget(self.time_start)
        layout.addSpacing(10)
        layout.addWidget(lbl_tilde)
        layout.addSpacing(10)
        layout.addWidget(lbl_end)
        layout.addWidget(self.date_end)
        layout.addWidget(self.time_end)

        return container

    def create_header(self):
        frame = QFrame()
        frame.setObjectName("DashHeader")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("멀티 채널 모니터링")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(title)
        layout.addStretch()

        btn_login = QPushButton("로그인")
        btn_login.setObjectName("LoginBtn")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.setFixedWidth(80)
        layout.addWidget(btn_login)

        self.badge = QLabel(" ● 0개 채널 ")
        self.badge.setStyleSheet("""
            background-color: #064E3B; color: #34D399; 
            border-radius: 15px; padding: 5px 10px; font-weight: bold; font-size: 12px;
        """)
        layout.addWidget(self.badge)
        return frame

    def refresh_dashboard(self):
        self.channels = self.load_channels_from_settings()
        self.badge.setText(f" ● {len(self.channels)}개 채널 ")

        while self.left_layout.count():
            child = self.left_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.tabs.clear()
        self.ui_items.clear()

        if not self.channels:
            lbl = QLabel("등록된 채널이 없습니다.\n설정 탭에서 채널을 추가해주세요.")
            lbl.setStyleSheet("color: #9CA3AF; font-size: 14px; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.left_layout.addWidget(lbl)
            return

        for channel in self.channels:
            self.add_channel_ui(channel)

    def add_channel_ui(self, channel_data):
        name = channel_data.get('name', 'Unknown')
        key = channel_data.get('key', name)

        page_widget = QWidget()
        page_layout = QVBoxLayout(page_widget)
        page_layout.setContentsMargins(0,0,0,0)
        page_layout.setSpacing(0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 5, 10, 5)
        toolbar.addStretch()

        btn_copy = QPushButton("📋 Copy")
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.setStyleSheet("background: transparent; color: #9CA3AF; border: none; font-weight: bold;")
        
        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.setStyleSheet("background: transparent; color: #9CA3AF; border: none; font-weight: bold;")
        
        toolbar.addWidget(btn_copy)
        toolbar.addWidget(btn_clear)
        
        console = QTextEdit()
        console.setReadOnly(True)
        console.setStyleSheet("""
            QTextEdit {
                background-color: #0F1218;
                color: #D1D5DB;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 15px;
            }
        """)
        
        btn_clear.clicked.connect(console.clear)
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(console.toPlainText()))

        page_layout.addLayout(toolbar)
        page_layout.addWidget(console)
        
        self.tabs.addTab(page_widget, name)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet("#Card { background-color: #1F2937; border-radius: 12px; border: 1px solid #374151; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        top_row = QHBoxLayout()
        icon = QLabel("❖")
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background-color: #374151; border-radius: 8px; font-size: 20px; color: white;")
        
        title_lbl = QLabel(name)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        
        top_row.addWidget(icon)
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        card_layout.addLayout(top_row)

        desc_lbl = QLabel(f"Key: {key} | URL: {channel_data.get('url', '-')}")
        desc_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        desc_lbl.setWordWrap(True)
        card_layout.addWidget(desc_lbl)

        card_layout.addSpacing(10)
        
        btn = QPushButton("검사 시작")
        btn.setObjectName("PrimaryBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #2563EB; color: white; border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #4B5563; color: #9CA3AF; }
        """)
        btn.clicked.connect(lambda: self.start_check(channel_data))
        card_layout.addWidget(btn)

        status_lbl = QLabel("대기 중")
        status_lbl.setStyleSheet("color: #9CA3AF; font-size: 11px; margin-top: 5px;")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        card_layout.addWidget(status_lbl)

        pbar = QProgressBar()
        pbar.setTextVisible(False)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet("""
            QProgressBar { background-color: #374151; border-radius: 3px; }
            QProgressBar::chunk { background-color: #3B82F6; border-radius: 3px; }
        """)
        pbar.setValue(0)
        card_layout.addWidget(pbar)

        self.left_layout.addWidget(card)

        self.ui_items[key] = {
            'card': card,
            'console': console,
            'btn': btn,
            'status': status_lbl,
            'pbar': pbar,
            'tab_index': self.tabs.count() - 1
        }

    def load_dify_config(self):
        default_config = {
            "url": "https://api.dify.ai/v1/workflows/run",
            "authorization": "Bearer ",
            "content_type": "application/json"
        }
        if not os.path.exists(self.settings_file):
            return default_config
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("dify_config", default_config)
        except:
            return default_config

    def create_time_combo(self, default_text="00:00"):
        combo = QComboBox()
        combo.setEditable(True)
        times = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
        if "23:59" not in times: times.append("23:59")
        combo.addItems(times)
        combo.setCurrentText(default_text)
        combo.lineEdit().setStyleSheet("background: transparent; border: none; color: white;")
        return combo

    def start_check(self, channel_data):
        name = channel_data.get('name')
        key = channel_data.get('key', name)
        
        ui = self.ui_items.get(key)
        if not ui: return

        ui['btn'].setEnabled(False)
        ui['btn'].setText("검사 중...")
        ui['pbar'].setRange(0, 0)
        ui['status'].setText("검사 프로세스 초기화 중...")
        ui['status'].setStyleSheet("color: #60A5FA; font-size: 11px; margin-top: 5px;")
        
        self.tabs.setCurrentIndex(ui['tab_index'])
        ui['console'].clear()
        
        d_start = self.date_start.date().toString("yyyy-MM-dd")
        t_start = self.time_start.currentText()
        if len(t_start) == 5: t_start += ":00"
        
        d_end = self.date_end.date().toString("yyyy-MM-dd")
        t_end = self.time_end.currentText()
        if len(t_end) == 5: t_end += ":59"

        full_start = f"{d_start} {t_start}"
        full_end = f"{d_end} {t_end}"
        
        date_range = {"start": full_start, "end": full_end}

        self.append_log(key, f"[{name}] 검사를 시작합니다... ({full_start} ~ {full_end})", "INFO")

        if key in self.workers and self.workers[key].isRunning():
            return 

        dify_config = self.load_dify_config()
        
        worker = MonitorWorker(channel_data, dify_config, date_range)
        worker.log_signal.connect(lambda msg, lvl: self.append_log(key, msg, lvl))
        worker.finished_signal.connect(self.on_worker_finished)
        
        self.workers[key] = worker
        worker.start()

    @pyqtSlot(str, str)
    def append_log(self, key, message, level="INFO"):
        ui = self.ui_items.get(key)
        if not ui: return
        console = ui['console']

        time_str = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#10B981", "WARN": "#FBBF24", 
            "ERROR": "#EF4444", "DEBUG": "#6B7280", 
            "SCAN": "#3B82F6", "SUCCESS": "#34D399",
            "PROGRESS": "#8B5CF6"
        }
        color = color_map.get(level, "#D1D5DB")
        
        # [수정] 복잡한 커서 조작(덮어쓰기) 로직을 모두 제거하고 단순 추가(append)로 변경
        # 크래시 원인을 원천 차단합니다.
        html = f"""
        <div style="margin-bottom: 2px;">
            <span style="color:#52525B">[{time_str}]</span> 
            <span style="color:{color}; font-weight:bold;">{level:<5}</span> 
            <span style="color:#D1D5DB;">{message}</span>
        </div>
        """
        
        console.append(html)
        
        # 상태 메시지 업데이트
        if level == "SCAN" or level == "PROGRESS":
            ui['status'].setText(message)
        elif level == "ERROR":
            ui['status'].setText("오류 발생")
            ui['status'].setStyleSheet("color: #EF4444; font-size: 11px; margin-top: 5px;")

    @pyqtSlot(str, int)
    def on_worker_finished(self, key, error_count):
        if key in self.workers:
            self.workers[key].deleteLater()
            del self.workers[key]

        ui = self.ui_items.get(key)
        if not ui: return

        ui['btn'].setEnabled(True)
        ui['btn'].setText("검사 시작")
        ui['pbar'].setRange(0, 100)
        
        if error_count == -1:
            ui['pbar'].setValue(0)
            ui['status'].setText("검사 중단됨 (오류)")
            ui['status'].setStyleSheet("color: #EF4444; font-size: 11px; margin-top: 5px;")
            self.append_log(key, "프로세스가 비정상 종료되었습니다.", "ERROR")
        else:
            ui['pbar'].setValue(100)
            ui['status'].setText(f"완료 (에러 {error_count}건)")
            ui['status'].setStyleSheet("color: #34D399; font-size: 11px; margin-top: 5px;")
            self.append_log(key, f"검사가 완료되었습니다. 총 {error_count}건의 에러가 발견되었습니다.", "SUCCESS")