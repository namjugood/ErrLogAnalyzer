import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QAbstractItemView, QDialog, 
                             QMessageBox, QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.ui.add_channel_dialog import AddChannelDialog

class SettingsView(QWidget):
    # 설정 저장 완료 시그널 정의
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings_dir = "settings"
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        # [스타일] 대시보드 테마를 참고한 설정 화면 전용 스타일 정의
        SETTINGS_THEME = """
            /* 스크롤 영역 투명화 */
            QScrollArea { background-color: transparent; border: none; }
            QWidget#ContentWidget { background-color: transparent; }

            /* 카드(섹션) 스타일 */
            QFrame#Card {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 12px;
            }

            /* 라벨 스타일 */
            QLabel {
                color: #E5E7EB;
                font-weight: bold;
            }

            /* 입력 필드: 카드 배경보다 어둡게 하여 구분감 줌 */
            QLineEdit {
                background-color: #111827; 
                border: 1px solid #4B5563;
                border-radius: 6px;
                padding: 10px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }

            /* 테이블: 카드 배경보다 어둡게 처리 */
            QTableWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
            }
            QTableWidget::item {
                border-bottom: 1px solid #2D3748;
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #374151;
                color: #D1D5DB;
                border: none;
                padding: 6px;
                font-weight: bold;
                font-size: 12px;
            }
        """
        self.setStyleSheet(SETTINGS_THEME)

        # 전체 화면 스크롤 적용
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_widget.setObjectName("ContentWidget")
        
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # UI 컴포넌트 추가
        main_layout.addWidget(self.create_header())
        main_layout.addWidget(self.create_channel_section())
        main_layout.addWidget(self.create_path_section())
        main_layout.addWidget(self.create_dify_section()) # [복구] Dify 섹션 추가
        main_layout.addStretch()
        main_layout.addWidget(self.create_footer())
        
        scroll_area.setWidget(content_widget)
        
        # 메인 레이아웃에 스크롤 영역 추가
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(scroll_area)

    def create_header(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        text_layout = QVBoxLayout()
        title = QLabel("시스템 설정")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        desc = QLabel("모니터링 채널 구성 및 로그 분석 시스템의 전반적인 환경을 설정합니다.")
        desc.setStyleSheet("font-size: 13px; color: #9CA3AF; margin-top: 5px;")
        
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        
        layout.addLayout(text_layout)
        layout.addStretch()

        btn_reset = QPushButton("설정 다시 불러오기")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet("""
            background-color: transparent; 
            color: #9CA3AF; 
            font-weight: bold; 
            border: none;
            margin-right: 15px;
        """)
        btn_reset.clicked.connect(self.load_settings)

        btn_save = QPushButton("💾 변경사항 저장")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setObjectName("PrimaryBtn")
        btn_save.setFixedSize(140, 40)
        btn_save.clicked.connect(self.save_settings)

        layout.addWidget(btn_reset)
        layout.addWidget(btn_save)

        return container

    def create_channel_section(self):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # 카드 헤더
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("(•)")
        icon_lbl.setStyleSheet("color: #3B82F6; font-weight: bold; font-size: 16px;")
        
        title_lbl = QLabel("모니터링 채널 관리")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-left: 5px;")
        
        btn_add = QPushButton("+ 채널 추가")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            background-color: #111827; 
            color: #3B82F6; 
            border: 1px solid #374151; 
            border-radius: 4px;
            padding: 5px 12px;
            font-weight: bold;
            font-size: 12px;
        """)
        btn_add.clicked.connect(self.show_add_channel_popup)

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(btn_add)
        
        layout.addLayout(header_layout)

        # 테이블 설정
        self.channel_table = QTableWidget()
        self.channel_table.setColumnCount(6)
        self.channel_table.setHorizontalHeaderLabels(["채널명", "채널 키", "URL", "아이디", "수정", "삭제"])
        
        header = self.channel_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.channel_table.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.channel_table.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.channel_table.setColumnWidth(3, 120)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.channel_table.setColumnWidth(4, 70) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.channel_table.setColumnWidth(5, 70)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        self.channel_table.verticalHeader().setVisible(False)
        self.channel_table.setShowGrid(False)
        self.channel_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.channel_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.channel_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.channel_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.channel_table.setFixedHeight(200)
        self.channel_table.verticalHeader().setDefaultSectionSize(42)
        layout.addWidget(self.channel_table)

        return card

    def show_add_channel_popup(self):
        dialog = AddChannelDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, key, url, user_id, password = dialog.get_data()
            if name.strip() and url.strip():
                self.add_channel_row(name, key, url, user_id, password)

    def add_channel_row(self, name, key, url, uid, password=""):
        row = self.channel_table.rowCount()
        self.channel_table.insertRow(row)
        self.channel_table.setRowHeight(row, 42)

        def create_item(text, color="white"):
            item = QTableWidgetItem(text)
            item.setForeground(QColor(color))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            return item

        item_name = create_item(name, "white")
        item_name.setData(Qt.ItemDataRole.UserRole, password)
        self.channel_table.setItem(row, 0, item_name)
        self.channel_table.setItem(row, 1, create_item(key, "#9CA3AF"))
        self.channel_table.setItem(row, 2, create_item(url, "#9CA3AF"))
        self.channel_table.setItem(row, 3, create_item(uid, "#9CA3AF"))

        # 수정 버튼
        btn_edit = QPushButton("수정")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setFixedHeight(34)
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #60A5FA; 
                font-size: 12px;
            }
            QPushButton:hover { background-color: #374151; }
        """)
        btn_edit.clicked.connect(self.handle_edit_clicked)
        
        container_edit = QWidget()
        layout_edit = QHBoxLayout(container_edit)
        layout_edit.setContentsMargins(5, 0, 5, 0)
        layout_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_edit.addWidget(btn_edit)
        self.channel_table.setCellWidget(row, 4, container_edit)

        # 삭제 버튼
        btn_del = QPushButton("삭제")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setFixedHeight(34)
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FCA5A5; 
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #450A0A; color: white; }
        """)
        btn_del.clicked.connect(self.handle_delete_clicked)
        
        container_del = QWidget()
        layout_del = QHBoxLayout(container_del)
        layout_del.setContentsMargins(5, 0, 5, 0)
        layout_del.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_del.addWidget(btn_del)
        self.channel_table.setCellWidget(row, 5, container_del)

    def handle_edit_clicked(self):
        button = self.sender()
        if not button: return

        index = self.channel_table.indexAt(button.parent().pos())
        if not index.isValid(): return
        row = index.row()

        item_name = self.channel_table.item(row, 0)
        current_name = item_name.text()
        current_pw = item_name.data(Qt.ItemDataRole.UserRole)
        current_key = self.channel_table.item(row, 1).text()
        current_url = self.channel_table.item(row, 2).text()
        current_id = self.channel_table.item(row, 3).text()

        dialog = AddChannelDialog(self)
        dialog.setWindowTitle("채널 수정")
        dialog.input_name.setText(current_name)
        dialog.input_key.setText(current_key)
        dialog.input_url.setText(current_url)
        dialog.input_id.setText(current_id)
        dialog.input_pw.setText(current_pw if current_pw else "")

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, new_key, new_url, new_uid, new_pw = dialog.get_data()
            
            self.channel_table.item(row, 0).setText(new_name)
            self.channel_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, new_pw)
            self.channel_table.item(row, 1).setText(new_key)
            self.channel_table.item(row, 2).setText(new_url)
            self.channel_table.item(row, 3).setText(new_uid)

    def handle_delete_clicked(self):
        button = self.sender()
        if button:
            index = self.channel_table.indexAt(button.parent().pos())
            if index.isValid():
                confirm = QMessageBox.question(
                    self, "삭제 확인", "정말 이 채널을 삭제하시겠습니까?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if confirm == QMessageBox.StandardButton.Yes:
                    self.channel_table.removeRow(index.row())

    def create_path_section(self):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        icon_lbl = QLabel("📂")
        icon_lbl.setStyleSheet("color: #3B82F6; font-size: 16px;")
        title_lbl = QLabel("파일 경로 설정")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-left: 5px;")
        
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(20)

        path_group = QVBoxLayout()
        lbl_path = QLabel("기본 로그 디렉토리 경로")
        lbl_path.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
        
        path_input_box = QHBoxLayout()
        self.input_path = QLineEdit("/var/log/bxm/current/")
        self.input_path.setReadOnly(False) 
        
        btn_folder = QPushButton("📁")
        btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_folder.setFixedSize(40, 38)
        btn_folder.setStyleSheet("background-color: #374151; border: 1px solid #4B5563; border-radius: 6px; color: #9CA3AF;")
        btn_folder.clicked.connect(self.select_log_directory)
        
        path_input_box.addWidget(btn_folder)
        path_input_box.addWidget(self.input_path)
        
        path_group.addWidget(lbl_path)
        path_group.addLayout(path_input_box)

        period_group = QVBoxLayout()
        lbl_period = QLabel("로그 보관 기간 (일)")
        lbl_period.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
        
        self.input_period = QLineEdit("30")
        
        period_group.addWidget(lbl_period)
        period_group.addWidget(self.input_period)

        form_layout.addLayout(path_group, 7)
        form_layout.addLayout(period_group, 3)
        
        layout.addLayout(form_layout)

        return card

    def select_log_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "로그 디렉토리 선택", self.input_path.text())
        if dir_path:
            self.input_path.setText(dir_path)

    # [복구] Dify 설정 섹션 추가
    def create_dify_section(self):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # 헤더
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("🤖")
        icon_lbl.setStyleSheet("font-size: 16px;")
        title_lbl = QLabel("Dify API 설정")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-left: 5px;")
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 입력 폼
        # 1. URL
        layout.addWidget(self._create_label("Workflow API URL"))
        self.dify_url = QLineEdit()
        self.dify_url.setPlaceholderText("https://api.dify.ai/v1/workflows/run")
        layout.addWidget(self.dify_url)

        # 2. Authorization
        layout.addWidget(self._create_label("Authorization (API Key)"))
        self.dify_auth = QLineEdit()
        self.dify_auth.setText("Bearer ")
        self.dify_auth.textChanged.connect(self._ensure_bearer_prefix) # 접두사 고정 로직
        layout.addWidget(self.dify_auth)

        # 3. Content-Type
        layout.addWidget(self._create_label("Content-Type"))
        self.dify_content_type = QLineEdit("application/json")
        layout.addWidget(self.dify_content_type)

        return card

    def _create_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
        return lbl

    def _ensure_bearer_prefix(self, text):
        """Authorization 입력 시 'Bearer ' 접두사를 강제하는 슬롯"""
        prefix = "Bearer "
        if not text.startswith(prefix):
            cursor_pos = self.dify_auth.cursorPosition()
            self.dify_auth.blockSignals(True) 
            self.dify_auth.setText(prefix + text.replace(prefix, "", 1))
            self.dify_auth.blockSignals(False)
            
            if cursor_pos < len(prefix):
                self.dify_auth.setCursorPosition(len(prefix))

    def create_footer(self):
        footer = QWidget()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 20, 0, 0)

        copyright_lbl = QLabel("© 2024 BXM Enterprise Systems. All rights reserved.")
        copyright_lbl.setStyleSheet("color: #6B7280; font-size: 12px;")

        links_lbl = QLabel("도움말 문서    릴리즈 노트")
        links_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        links_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px;")

        layout.addWidget(copyright_lbl)
        layout.addStretch()
        layout.addWidget(links_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #1F2937; height: 1px; border: none;")
        
        container_layout = QVBoxLayout()
        container_layout.addWidget(line)
        container_layout.addWidget(footer)
        
        container = QWidget()
        container.setLayout(container_layout)
        return container

    def save_settings(self):
        channels = []
        for row in range(self.channel_table.rowCount()):
            item_name = self.channel_table.item(row, 0)
            item_key = self.channel_table.item(row, 1)
            item_url = self.channel_table.item(row, 2)
            item_uid = self.channel_table.item(row, 3)
            
            password = item_name.data(Qt.ItemDataRole.UserRole)
            
            channels.append({
                "name": item_name.text(),
                "key": item_key.text(),
                "url": item_url.text(),
                "id": item_uid.text(),
                "password": password if password else "" 
            })

        settings_data = {
            "channels": channels,
            "log_path": self.input_path.text(),
            "retention_days": self.input_period.text(),
            # [복구] Dify 설정 저장
            "dify_config": {
                "url": self.dify_url.text(),
                "authorization": self.dify_auth.text(),
                "content_type": self.dify_content_type.text()
            }
        }

        try:
            if not os.path.exists(self.settings_dir):
                os.makedirs(self.settings_dir)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
            
            QMessageBox.information(self, "저장 완료", "설정이 성공적으로 저장되었습니다.")
            self.settings_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"설정 파일을 저장하는 중 오류가 발생했습니다.\n{str(e)}")

    def load_settings(self):
        self.channel_table.setRowCount(0)

        if not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

            channels = settings_data.get("channels", [])
            for ch in channels:
                self.add_channel_row(
                    ch.get("name", ""),
                    ch.get("key", ""),
                    ch.get("url", ""),
                    ch.get("id", ""),
                    ch.get("password", "")
                )

            self.input_path.setText(settings_data.get("log_path", "/var/log/bxm/current/"))
            self.input_period.setText(settings_data.get("retention_days", "30"))

            # [복구] Dify 설정 로드
            dify_conf = settings_data.get("dify_config", {})
            self.dify_url.setText(dify_conf.get("url", "https://api.dify.ai/v1/workflows/run"))
            
            auth_val = dify_conf.get("authorization", "Bearer ")
            if not auth_val.startswith("Bearer "):
                auth_val = "Bearer " + auth_val
            self.dify_auth.setText(auth_val)
            
            self.dify_content_type.setText(dify_conf.get("content_type", "application/json"))

        except Exception as e:
            print(f"설정 로드 실패: {e}")