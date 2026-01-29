# app/ui/add_channel_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit)
from PyQt6.QtCore import Qt

class AddChannelDialog(QDialog):
    """채널 추가를 위한 모달 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("채널 추가")
        self.setFixedWidth(400)
        # 팝업 스타일
        self.setStyleSheet("""
            QDialog {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 12px;
            }
            QLabel {
                color: #E5E7EB;
                font-weight: bold;
                font-size: 13px;
                margin-bottom: 5px;
            }
            QLineEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 10px;
                color: white;
                font-size: 13px;
                margin-bottom: 15px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            QPushButton#CancelBtn {
                background-color: transparent;
                color: #E5E7EB;
                border: none;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton#SaveBtn {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton#SaveBtn:hover {
                background-color: #1D4ED8;
            }
            QPushButton#HeaderCloseBtn {
                background-color: transparent;
                color: #9CA3AF;
                border: none;
                font-size: 12px;
            }
        """)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(5)

        # 1. 헤더
        header_layout = QHBoxLayout()
        title_lbl = QLabel("채널 추가")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 0px;")
        
        btn_close = QPushButton("close")
        btn_close.setObjectName("HeaderCloseBtn")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.reject)
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(btn_close)
        
        layout.addLayout(header_layout)
        layout.addSpacing(15)

        # 2. 입력 필드
        # 채널명
        layout.addWidget(QLabel("채널명"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("채널 이름을 입력하세요")
        layout.addWidget(self.input_name)

        # [추가됨] 채널 키
        layout.addWidget(QLabel("채널 키"))
        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("고유 식별 키 (예: OCI → AYC)")
        layout.addWidget(self.input_key)

        # URL
        layout.addWidget(QLabel("URL"))
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("http://...")
        layout.addWidget(self.input_url)

        # 아이디 / 비밀번호
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        
        id_group = QVBoxLayout()
        id_group.addWidget(QLabel("아이디"))
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("계정 ID")
        id_group.addWidget(self.input_id)
        
        pw_group = QVBoxLayout()
        pw_group.addWidget(QLabel("비밀번호"))
        self.input_pw = QLineEdit()
        self.input_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pw.setPlaceholderText("••••••••")
        pw_group.addWidget(self.input_pw)

        row_layout.addLayout(id_group)
        row_layout.addLayout(pw_group)
        layout.addLayout(row_layout)

        layout.addSpacing(10)

        # 3. 하단 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("CancelBtn")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("저장")
        btn_save.setObjectName("SaveBtn")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def get_data(self):
        """입력된 데이터 반환 (채널 키 포함)"""
        return (self.input_name.text(),
                self.input_key.text(),  # [추가됨]
                self.input_url.text(), 
                self.input_id.text(), 
                self.input_pw.text())