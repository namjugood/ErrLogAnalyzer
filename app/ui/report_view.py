# app/ui/report_view.py

import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QDialog, QTextBrowser, QFrame, 
                             QCheckBox, QAbstractItemView, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import subprocess 
import sys

from app.core.history_manager import HistoryManager

class ReportView(QWidget):
    def __init__(self):
        super().__init__()
        # 전체 데이터 보관용
        self.history_manager = HistoryManager() # 매니저 인스턴스
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(15)

        # 1. 헤더
        layout.addWidget(self.create_header())

        # 2. 통계 카드
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        stats_layout.addWidget(self.create_stat_card("전체 에러 개수", "1,284", "이번 달 +12%", "#3B82F6", "📊"))
        stats_layout.addWidget(self.create_stat_card("심각한 에러", "42", "조치 필요", "#EF4444", "🚨"))
        stats_layout.addWidget(self.create_stat_card("사용자 에러", "315", "패스워드/입력 오류", "#F59E0B", "👤"))
        layout.addLayout(stats_layout)

        # 3. 리스트 섹션 헤더
        list_header_layout = QHBoxLayout()
        lbl_recent = QLabel("최근 분석 리포트")
        lbl_recent.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        
        btn_delete = QPushButton(" 선택 삭제 ")
        btn_delete.setObjectName("DeleteBtn")
        btn_delete.clicked.connect(self.delete_selected_rows)

        # btn_download = QPushButton(" 다운로드 ")
        # btn_download.setObjectName("SecondaryBtn")

        list_header_layout.addWidget(lbl_recent)
        list_header_layout.addStretch()
        list_header_layout.addWidget(btn_delete)
        # list_header_layout.addWidget(btn_download)
        
        layout.addLayout(list_header_layout)

        # 4. 탭 및 테이블 영역
        self.tabs = QTabWidget()
        self.setup_tabs() 
        layout.addWidget(self.tabs)
        
        # 초기 데이터 로드
        self.init_sample_data()
        self.load_data_to_table("전체")

    def create_header(self):
        frame = QFrame()
        frame.setObjectName("DashHeader")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("리포트 이력")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        lbl_search = QLabel("🔍 로그 파일 검색...")
        lbl_search.setStyleSheet("color: #6B7280; background-color: #1F2937; padding: 6px 12px; border-radius: 6px; border: 1px solid #374151; font-size: 12px;")
        layout.addWidget(lbl_search)

        return frame

    def create_stat_card(self, title, value, sub_text, color_code, icon):
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(f"#Card {{ border-left: 4px solid {color_code}; }}")
        
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(15, 15, 15, 15)
        
        hbox_top = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 16px;")
        
        hbox_top.addWidget(lbl_title)
        hbox_top.addStretch()
        hbox_top.addWidget(lbl_icon)
        vbox.addLayout(hbox_top)
        
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-top: 5px;")
        vbox.addWidget(lbl_val)
        
        lbl_sub = QLabel(sub_text)
        lbl_sub.setStyleSheet(f"color: {color_code}; font-size: 11px; font-weight: bold;")
        vbox.addWidget(lbl_sub)
        
        return card

    def load_channels(self):
        """settings.json에서 채널명 리스트 로드"""
        settings_path = os.path.join("settings", "settings.json")
        channels = []
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get("channels", []):
                        channels.append(item.get("name"))
            except Exception as e:
                print(f"Failed to load channels: {e}")
        return channels

    def setup_tabs(self):
        """[수정 요청 3-1] 동적 탭 생성 (settings.json 기반)"""
        # "전체"는 기본 탭으로 고정
        channel_names = ["전체"]
        
        # 파일에서 로드한 채널명 추가
        loaded = self.load_channels()
        if loaded:
            channel_names.extend(loaded)
        else:
            # 설정 파일이 없거나 비어있을 경우 기본값 (예시)
            channel_names.extend(["금융투자", "은행", "카드", "생명", "저축은행"])

        for name in channel_names:
            if name == "전체":
                page = QWidget()
                layout = QVBoxLayout(page)
                layout.setContentsMargins(0, 0, 0, 0)
                self.setup_table() # 테이블 생성
                layout.addWidget(self.table)
                page.setLayout(layout)
                self.tabs.addTab(page, name)
            else:
                self.tabs.addTab(QWidget(), name)
        
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def setup_table(self):
        self.table = QTableWidget()
        
        # [수정] 컬럼 구성 변경: 계열사 삭제 / 일시 분리
        columns = ["", "조회시작", "조회종료", "파일명", "에러 수", "수집 상태"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        header = self.table.horizontalHeader()
        
        # [수정] 컬럼 너비 조정
        # 0. 체크박스
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        
        # 1. 조회시작 (YYYY-MM-DD HH:MM 에 맞는 너비)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # self.table.setColumnWidth(1, 200)
        
        # 2. 조회종료
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # self.table.setColumnWidth(2, 200)
        
        # 3. 파일명 (가장 중요하므로 Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        # self.table.setColumnWidth(3, 300)
        
        # 4. 에러 수
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        # self.table.setColumnWidth(4, 200)
        
        # 5. 수집 상태
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        # self.table.setColumnWidth(5, 200)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False) 
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(42)
        
        self.table.cellClicked.connect(self.on_table_clicked)

    def init_sample_data(self):
        """샘플 데이터 초기화 (계열사 필드는 탭 필터링을 위해 내부적으로 유지)"""
        # [참고] 실제 구현시에는 DB나 로그 파일에서 읽어온 'aff' 값이 
        # settings.json의 채널명과 일치해야 탭 필터링이 정상 동작합니다.
        self.all_data = [
            {"start": "2026-01-23 14:30", "end": "2026-01-23 14:35", "fname": "auth-service.log", "aff": "금융투자", "err": "42", "sev": "High", "stat": "성공"},
            {"start": "2026-01-23 10:15", "end": "2026-01-23 10:20", "fname": "gateway-api.log", "aff": "은행", "err": "0", "sev": "None", "stat": "성공"},
            {"start": "2026-01-22 18:00", "end": "2026-01-22 18:05", "fname": "db-proxy.log", "aff": "카드", "err": "-", "sev": "Fail", "stat": "실패"},
            {"start": "2026-01-22 15:45", "end": "2026-01-22 16:00", "fname": "payment-v3.log", "aff": "생명", "err": "12", "sev": "Medium", "stat": "성공"},
            {"start": "2026-01-21 09:20", "end": "2026-01-21 09:30", "fname": "user-batch.log", "aff": "저축은행", "err": "5", "sev": "Low", "stat": "성공"},
            {"start": "2026-01-20 11:00", "end": "2026-01-20 11:10", "fname": "core-banking.log", "aff": "은행", "err": "8", "sev": "Low", "stat": "성공"},
            {"start": "2026-01-19 13:22", "end": "2026-01-19 13:45", "fname": "stock-trade.log", "aff": "금융투자", "err": "156", "sev": "High", "stat": "성공"},
            # 동적으로 추가된 채널 테스트용 데이터 (예: OKC)
            {"start": "2026-01-23 16:00", "end": "2026-01-23 16:10", "fname": "okc-test.log", "aff": "OKC", "err": "3", "sev": "Low", "stat": "성공"},
        ]

    def on_tab_changed(self, index):
        """탭 변경 시 테이블 데이터 필터링"""
        tab_text = self.tabs.tabText(index)
        
        current_page = self.tabs.widget(index)
        if current_page.layout() is None:
            layout = QVBoxLayout(current_page)
            layout.setContentsMargins(0,0,0,0)
            current_page.setLayout(layout)
        
        self.table.setParent(current_page)
        current_page.layout().addWidget(self.table)
        
        self.load_data_to_table(tab_text)

    def load_data_to_table(self, affiliate_filter="전체"):
        self.table.setRowCount(0) 
        
        # [수정] 파일에서 실제 데이터 로드
        records = self.history_manager.get_records(affiliate_filter)
        
        self.table.setRowCount(len(records))
        
        for row, data in enumerate(records):
            # 0. 체크박스
            chk_widget = QWidget()
            chk = QCheckBox()
            chk.setCursor(Qt.CursorShape.PointingHandCursor)
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0,0,0,0)
            self.table.setCellWidget(row, 0, chk_widget)

            # 1. 조회시작 (YYYY-MM-DD HH:MM)
            start_item = QTableWidgetItem(data.get("start_period", "-"))
            start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, start_item)
            
            # 2. 조회종료
            end_item = QTableWidgetItem(data.get("end_period", "-"))
            end_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, end_item)

            # 3. 파일명 (파일명만 표시, 전체 경로는 숨겨진 데이터로 저장)
            fname_item = QTableWidgetItem(data.get("file_name", "-"))
            fname_item.setData(Qt.ItemDataRole.UserRole, data.get("report_path")) # 경로 저장
            fname_item.setForeground(QColor("#60A5FA"))
            fname_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            fname_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, fname_item)

            # 4. 에러 수
            err_widget = self.create_badge(data.get("error_count", "0"), "High") # Severity 로직은 추후 고도화
            self.table.setCellWidget(row, 4, err_widget)
            
            # 5. 상태
            status_text = data.get("status", "성공")
            status_item = QTableWidgetItem("● " + status_text)
            status_item.setForeground(QColor("#10B981") if status_text == "성공" else QColor("#EF4444"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, status_item)

    def create_badge(self, text, severity):
        """[수정] 에러 수에 따라 50단위로 색상 구분"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        
        lbl = QLabel(f" {text} 에러 ")
        lbl.setFixedHeight(18)
        
        # 기본값 (숫자가 아닐 경우)
        bg_color = "#374151"
        text_color = "#9CA3AF"
        
        # 숫자 파싱 및 색상 결정
        try:
            count = int(text)
            if count == 0:
                bg_color = "#064E3B" # Green (0)
                text_color = "#34D399"
            elif count < 50:
                bg_color = "#172554" # Blue (1~49)
                text_color = "#BFDBFE"
            elif count < 100:
                bg_color = "#451A03" # Orange (50~99)
                text_color = "#FDBA74"
            else:
                bg_color = "#450A0A" # Red (100+)
                text_color = "#FCA5A5"
        except ValueError:
            # "-" 등의 문자인 경우 기본값 유지
            pass
            
        lbl.setStyleSheet(f"""
            background-color: {bg_color}; 
            color: {text_color}; 
            border-radius: 9px; 
            padding: 0px 6px;
            font-size: 10px; 
            font-weight: bold;
        """)
        
        layout.addWidget(lbl)
        return widget

    def delete_selected_rows(self):
        """체크된 행 일괄 삭제"""
        rows_to_delete = []
        
        # 역순 탐색
        for row in range(self.table.rowCount() - 1, -1, -1):
            widget = self.table.cellWidget(row, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    rows_to_delete.append(row)
        
        if not rows_to_delete:
            QMessageBox.information(self, "알림", "삭제할 항목을 선택해주세요.")
            return

        confirm = QMessageBox.question(self, "삭제 확인", f"선택한 {len(rows_to_delete)}개 리포트를 삭제하시겠습니까?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            deleted_files = []
            for row in rows_to_delete:
                # [수정] 파일명 컬럼 인덱스가 2 -> 3으로 변경됨
                fname = self.table.item(row, 3).text()
                deleted_files.append(fname)
                self.table.removeRow(row)
            
            self.all_data = [d for d in self.all_data if d["fname"] not in deleted_files]

    def on_table_clicked(self, row, col):
        if col == 3:
            item = self.table.item(row, 3)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                self.open_file(file_path)
            else:
                QMessageBox.warning(self, "오류", "파일을 찾을 수 없습니다.")

    def open_report_detail(self, fname):
        dialog = ReportDetailDialog(fname, self)
        dialog.exec()

    def open_file(self, path):
        """OS 기본 뷰어로 PDF 열기"""
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.call(['open', path])
        else:
            subprocess.call(['xdg-open', path])

class ReportDetailDialog(QDialog):
    def __init__(self, fname, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Log Analysis Report - {fname}")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #111827; color: white;")
        
        layout = QVBoxLayout(self)
        
        viewer = QTextBrowser()
        viewer.setStyleSheet("background-color: white; color: black; padding: 20px; border-radius: 8px;")
        
        sample_html = f"""
        <h3>Log Analysis Report</h3>
        <p style='color:gray; font-size:12px;'>File: <b>{fname}</b> | Analyzed: 2026-01-23 14:35</p>
        <hr>
        <h4>Executive Summary</h4>
        <p style='font-size:13px;'>Analysis Result for {fname}</p>
        """
        viewer.setHtml(sample_html)
        layout.addWidget(viewer)
        
        btn_close = QPushButton("닫기")
        btn_close.setObjectName("PrimaryBtn")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)