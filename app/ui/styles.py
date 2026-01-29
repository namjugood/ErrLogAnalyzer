DARK_THEME = """
QMainWindow {
    background-color: #0B0E14;
}
QWidget {
    color: #E5E7EB;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* 사이드바 */
QFrame#Sidebar {
    background-color: #11141C;
    border-right: 1px solid #1F2937;
}
QPushButton#SideBtn {
    background-color: transparent; border: none; text-align: left; 
    padding: 15px; color: #9CA3AF; font-size: 13px;
}
QPushButton#SideBtn:hover { background-color: #374151; color: white; }
QPushButton#SideBtn:checked { color: #60A5FA; font-weight: bold; border-left: 3px solid #60A5FA; }

/* 상단 헤더 */
QFrame#DashHeader {
    background-color: #0B0E14;
    border-bottom: 0px;
    margin-bottom: 10px;
}

/* 카드 스타일 */
QFrame#Card {
    background-color: #161B26;
    border-radius: 12px;
    border: 1px solid #2D3748;
}

/* 버튼 스타일 (공통) */
QPushButton {
    border-radius: 6px;
    padding: 6px 6px;
    font-weight: bold;
}
QPushButton#PrimaryBtn {
    background-color: #3B82F6;
    color: white;
    border: none;
}
QPushButton#PrimaryBtn:hover { background-color: #2563EB; }

QPushButton#SecondaryBtn {
    background-color: #374151;
    color: #D1D5DB;
    border: none;
}
QPushButton#SecondaryBtn:hover { background-color: #4B5563; }

QPushButton#DeleteBtn {
    background-color: #450A0A;
    color: #FCA5A5;
    border: 1px solid #7F1D1D;
}
QPushButton#DeleteBtn:hover { background-color: #7F1D1D; color: white; }

QPushButton#LoginBtn {
    background-color: transparent;
    border: 1px solid #3B82F6;
    color: #3B82F6;
}

/* 테이블 스타일 */
QTableWidget {
    background-color: #161B26;
    border: 1px solid #2D3748;
    border-radius: 8px;
    gridline-color: #2D3748;
    outline: none;
    font-size: 12px;
}
QTableWidget::item {
    padding-left: 0px;
    border-bottom: 1px solid #2D3748;
}
QTableWidget::item:selected {
    background-color: #1F2937;
    color: white;
}
QHeaderView::section {
    background-color: #1F2937;
    color: #9CA3AF;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #2D3748;
    font-weight: bold;
    font-size: 12px;
}
QScrollBar:vertical {
    border: none;
    background: #11141C;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #374151;
    min-height: 20px;
    border-radius: 4px;
}

/* 탭 스타일 */
QTabWidget::pane {
    border: 1px solid #2D3748;
    border-top: none;
    background-color: #161B26;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
}
QTabBar::tab {
    background: #11141C;
    color: #9CA3AF;
    padding: 8px 20px;
    border: 1px solid #2D3748;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    min-width: 60px;
}
QTabBar::tab:selected {
    background: #161B26;
    color: #3B82F6;
    font-weight: bold;
    border-bottom: 1px solid #161B26;
}
QTabBar::tab:hover {
    background: #1F2937;
    color: white;
}

/* [수정] 체크박스 스타일 (체크 표시 보이도록 URL 인코딩 적용) */
QCheckBox { spacing: 0px; }
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 2px solid #6B7280;
    border-radius: 3px;
    background: transparent;
}
QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border-color: #3B82F6;
    /* fill='white' 대신 fill='%23ffffff' 사용 */
    image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ffffff'%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
}
QCheckBox::indicator:hover {
    border-color: #3B82F6;
}

/* [추가] QMessageBox(팝업창) 다크 모드 스타일 */
QMessageBox {
    background-color: #161B26; /* 카드 배경색과 동일하게 */
    color: white;
}
QMessageBox QLabel {
    color: white; /* 텍스트 흰색 강제 */
}
QMessageBox QPushButton {
    background-color: #374151; /* 버튼 배경 어둡게 */
    color: white;
    border: 1px solid #4B5563;
    border-radius: 4px;
    padding: 5px 15px;
    min-width: 60px;
}
QMessageBox QPushButton:hover {
    background-color: #4B5563;
}
/* 입력 필드 스타일 */
QLineEdit {
    background-color: #111827; 
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 10px;
    color: #E5E7EB;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #3B82F6;
}

/* 설정 화면 테이블 스타일 (리포트 뷰와 약간 다름) */
QTableWidget#SettingsTable {
    background-color: transparent;
    border: none;
}
QTableWidget#SettingsTable::item {
    border-bottom: 1px solid #2D3748;
    padding: 0px 5px;
}
QTableWidget#SettingsTable QHeaderView::section {
    background-color: transparent;
    border-bottom: 1px solid #4B5563;
    color: #6B7280;
    font-weight: bold;
    font-size: 11px;
    padding-left: 5px;
}
"""

# [추가] Dashboard 전용 스타일
DARK_THEME = """
QMainWindow {
    background-color: #0B0E14;
}
QWidget {
    color: #E5E7EB;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* 사이드바 */
QFrame#Sidebar {
    background-color: #11141C;
    border-right: 1px solid #1F2937;
}
QPushButton#SideBtn {
    background-color: transparent; border: none; text-align: left; 
    padding: 15px; color: #9CA3AF; font-size: 13px;
}
QPushButton#SideBtn:hover { background-color: #374151; color: white; }
QPushButton#SideBtn:checked { color: #60A5FA; font-weight: bold; border-left: 3px solid #60A5FA; }

/* 상단 헤더 */
QFrame#DashHeader {
    background-color: #0B0E14;
    border-bottom: 0px;
    margin-bottom: 10px;
}

/* 카드 스타일 */
QFrame#Card {
    background-color: #161B26;
    border-radius: 12px;
    border: 1px solid #2D3748;
}

/* 버튼 스타일 (공통) */
QPushButton {
    border-radius: 6px;
    padding: 6px 6px;
    font-weight: bold;
}
QPushButton#PrimaryBtn {
    background-color: #3B82F6;
    color: white;
    border: none;
}
QPushButton#PrimaryBtn:hover { background-color: #2563EB; }

QPushButton#SecondaryBtn {
    background-color: #374151;
    color: #D1D5DB;
    border: none;
}
QPushButton#SecondaryBtn:hover { background-color: #4B5563; }

QPushButton#DeleteBtn {
    background-color: #450A0A;
    color: #FCA5A5;
    border: 1px solid #7F1D1D;
}
QPushButton#DeleteBtn:hover { background-color: #7F1D1D; color: white; }

QPushButton#LoginBtn {
    background-color: transparent;
    border: 1px solid #3B82F6;
    color: #3B82F6;
}

/* 테이블 스타일 */
QTableWidget {
    background-color: #161B26;
    border: 1px solid #2D3748;
    border-radius: 8px;
    gridline-color: #2D3748;
    outline: none;
    font-size: 12px;
}
QTableWidget::item {
    padding-left: 0px;
    border-bottom: 1px solid #2D3748;
}
QTableWidget::item:selected {
    background-color: #1F2937;
    color: white;
}
QHeaderView::section {
    background-color: #1F2937;
    color: #9CA3AF;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #2D3748;
    font-weight: bold;
    font-size: 12px;
    padding-left: 5px;
}
QScrollBar:vertical {
    border: none;
    background: #11141C;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #374151;
    min-height: 20px;
    border-radius: 4px;
}

/* 탭 스타일 */
QTabWidget::pane {
    border: 1px solid #2D3748;
    border-top: none;
    background-color: #161B26;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
}
QTabBar::tab {
    background: #11141C;
    color: #9CA3AF;
    padding: 8px 20px;
    border: 1px solid #2D3748;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    min-width: 60px;
}
QTabBar::tab:selected {
    background: #161B26;
    color: #3B82F6;
    font-weight: bold;
    border-bottom: 1px solid #161B26;
}
QTabBar::tab:hover {
    background: #1F2937;
    color: white;
}

/* [수정] 체크박스 스타일 (체크 표시 보이도록 URL 인코딩 적용) */
QCheckBox { spacing: 0px; }
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 2px solid #6B7280;
    border-radius: 3px;
    background: transparent;
}
QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border-color: #3B82F6;
    /* fill='white' 대신 fill='%23ffffff' 사용 */
    image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ffffff'%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
}
QCheckBox::indicator:hover {
    border-color: #3B82F6;
}

/* [추가] QMessageBox(팝업창) 다크 모드 스타일 */
QMessageBox {
    background-color: #161B26; /* 카드 배경색과 동일하게 */
    color: white;
}
QMessageBox QLabel {
    color: white; /* 텍스트 흰색 강제 */
}
QMessageBox QPushButton {
    background-color: #374151; /* 버튼 배경 어둡게 */
    color: white;
    border: 1px solid #4B5563;
    border-radius: 4px;
    padding: 5px 15px;
    min-width: 60px;
}
QMessageBox QPushButton:hover {
    background-color: #4B5563;
}
/* 입력 필드 스타일 */
QLineEdit {
    background-color: #111827; 
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 10px;
    color: #E5E7EB;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #3B82F6;
}

/* 설정 화면 테이블 스타일 (리포트 뷰와 약간 다름) */
QTableWidget#SettingsTable {
    background-color: transparent;
    border: none;
}
QTableWidget#SettingsTable::item {
    border-bottom: 1px solid #2D3748;
    padding: 0px 5px;
}
QTableWidget#SettingsTable QHeaderView::section {
    background-color: transparent;
    border-bottom: 1px solid #4B5563;
    color: #6B7280;
    font-weight: bold;
    font-size: 11px;
    padding-left: 5px;
}
"""

DARK_THEME = """
QMainWindow {
    background-color: #0B0E14;
}
QWidget {
    color: #E5E7EB;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* 사이드바 */
QFrame#Sidebar {
    background-color: #11141C;
    border-right: 1px solid #1F2937;
}
QPushButton#SideBtn {
    background-color: transparent; border: none; text-align: left; 
    padding: 15px; color: #9CA3AF; font-size: 13px;
}
QPushButton#SideBtn:hover { background-color: #374151; color: white; }
QPushButton#SideBtn:checked { color: #60A5FA; font-weight: bold; border-left: 3px solid #60A5FA; }

/* 상단 헤더 */
QFrame#DashHeader {
    background-color: #0B0E14;
    border-bottom: 0px;
    margin-bottom: 10px;
}

/* 카드 스타일 */
QFrame#Card {
    background-color: #161B26;
    border-radius: 12px;
    border: 1px solid #2D3748;
}

/* 버튼 스타일 (공통) */
QPushButton {
    border-radius: 6px;
    padding: 6px 6px;
    font-weight: bold;
}
QPushButton#PrimaryBtn {
    background-color: #3B82F6;
    color: white;
    border: none;
}
QPushButton#PrimaryBtn:hover { background-color: #2563EB; }

QPushButton#SecondaryBtn {
    background-color: #374151;
    color: #D1D5DB;
    border: none;
}
QPushButton#SecondaryBtn:hover { background-color: #4B5563; }

QPushButton#DeleteBtn {
    background-color: #450A0A;
    color: #FCA5A5;
    border: 1px solid #7F1D1D;
}
QPushButton#DeleteBtn:hover { background-color: #7F1D1D; color: white; }

QPushButton#LoginBtn {
    background-color: transparent;
    border: 1px solid #3B82F6;
    color: #3B82F6;
}

/* 테이블 스타일 */
QTableWidget {
    background-color: #161B26;
    border: 1px solid #2D3748;
    border-radius: 8px;
    gridline-color: #2D3748;
    outline: none;
    font-size: 12px;
}
QTableWidget::item {
    padding-left: 0px;
    border-bottom: 1px solid #2D3748;
}
QTableWidget::item:selected {
    background-color: #1F2937;
    color: white;
}
QHeaderView::section {
    background-color: #1F2937;
    color: #9CA3AF;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #2D3748;
    font-weight: bold;
    font-size: 12px;
    padding-left: 5px;
}
QScrollBar:vertical {
    border: none;
    background: #11141C;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #374151;
    min-height: 20px;
    border-radius: 4px;
}

/* 탭 스타일 */
QTabWidget::pane {
    border: 1px solid #2D3748;
    border-top: none;
    background-color: #161B26;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
}
QTabBar::tab {
    background: #11141C;
    color: #9CA3AF;
    padding: 8px 20px;
    border: 1px solid #2D3748;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    min-width: 60px;
}
QTabBar::tab:selected {
    background: #161B26;
    color: #3B82F6;
    font-weight: bold;
    border-bottom: 1px solid #161B26;
}
QTabBar::tab:hover {
    background: #1F2937;
    color: white;
}

/* [수정] 체크박스 스타일 (체크 표시 보이도록 URL 인코딩 적용) */
QCheckBox { spacing: 0px; }
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 2px solid #6B7280;
    border-radius: 3px;
    background: transparent;
}
QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border-color: #3B82F6;
    /* fill='white' 대신 fill='%23ffffff' 사용 */
    image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ffffff'%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
}
QCheckBox::indicator:hover {
    border-color: #3B82F6;
}

/* [추가] QMessageBox(팝업창) 다크 모드 스타일 */
QMessageBox {
    background-color: #161B26; /* 카드 배경색과 동일하게 */
    color: white;
}
QMessageBox QLabel {
    color: white; /* 텍스트 흰색 강제 */
}
QMessageBox QPushButton {
    background-color: #374151; /* 버튼 배경 어둡게 */
    color: white;
    border: 1px solid #4B5563;
    border-radius: 4px;
    padding: 5px 15px;
    min-width: 60px;
}
QMessageBox QPushButton:hover {
    background-color: #4B5563;
}
/* 입력 필드 스타일 */
QLineEdit {
    background-color: #111827; 
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 10px;
    color: #E5E7EB;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #3B82F6;
}

/* 설정 화면 테이블 스타일 (리포트 뷰와 약간 다름) */
QTableWidget#SettingsTable {
    background-color: transparent;
    border: none;
}
QTableWidget#SettingsTable::item {
    border-bottom: 1px solid #2D3748;
    padding: 0px 5px;
}
QTableWidget#SettingsTable QHeaderView::section {
    background-color: transparent;
    border-bottom: 1px solid #4B5563;
    color: #6B7280;
    font-weight: bold;
    font-size: 11px;
    padding-left: 5px;
}
"""

DASHBOARD_STYLES = """
/* 날짜 선택 카드 컨테이너 */
QFrame#DateCard {
    background-color: #1F2937;
    border-radius: 8px;
    border: 1px solid #374151;
}

/* 라벨 스타일 */
QLabel {
    color: #9CA3AF;
    font-weight: bold;
    font-size: 14px;
}

/* ==============================================
   DateEdit & ComboBox 공통 스타일
   ============================================== */
QDateEdit, QComboBox {
    background-color: #111827;
    color: white;
    border: 1px solid #4B5563;
    border-radius: 4px;
    padding: 4px 10px; /* 패딩을 약간 줄여 내부 텍스트 공간 확보 */
    font-family: 'Consolas', monospace;
    font-size: 13px;
    
    /* [수정] 세로 공간 확보를 위해 최소 높이 명시 */
    min-height: 32px; 
    max-height: 32px;
}

/* [수정] 콤보박스 너비 및 화살표 영역 패딩 설정 */
QComboBox { 
    min-width: 60px;
    /* 기본 화살표가 그려질 공간 확보 (스타일링된 화살표 제거 시 중요하지 않으나 안전장치) */
    padding-right: 10px; 
}

/* [수정] SVG 아이콘 및 drop-down 커스텀 스타일 전체 제거 
   -> Qt 기본 드롭다운 버튼과 화살표가 렌더링되도록 함
*/

/* 마우스 오버 시 테두리 강조 */
QDateEdit:hover, QComboBox:hover {
    border: 1px solid #60A5FA;
}

/* ==============================================
   ComboBox 팝업 리스트 스타일
   ============================================== */
QComboBox QAbstractItemView {
    background-color: #1F2937;
    color: white;
    border: 1px solid #374151;
    selection-background-color: #2563EB;
    selection-color: white;
    outline: none;
    padding: 5px;
}

/* ==============================================
   CalendarWidget (달력 팝업) 스타일
   ============================================== */
QCalendarWidget {
    font-size: 13px;
}

/* 1. 달력 전체 배경 */
QCalendarWidget QWidget {
    background-color: #1F2937;
    color: white;
    alternate-background-color: #1F2937;
}

/* 2. 상단 네비게이션 바 */
QWidget#qt_calendar_navigationbar {
    background-color: #111827;
    border-bottom: 1px solid #374151;
}

/* 3. 좌우 이동 버튼 (기본 아이콘 사용을 위해 url 제거 및 배경 투명화) */
/* [수정] 좌우 이동 버튼: SVG 대신 텍스트(Unicode) 사용 및 흰색 적용 */
QToolButton#qt_calendar_prevmonth {
    qproperty-text: "◀";       /* 유니코드 화살표 문자 사용 */
    qproperty-icon: url("");   /* 기존 아이콘 숨김 */
    color: white;              /* 텍스트 색상 흰색 */
    background-color: transparent;
    border: none;
    width: 25px;
    height: 25px;
    font-size: 14px;
    font-weight: bold;
}

QToolButton#qt_calendar_nextmonth {
    qproperty-text: "▶";       /* 유니코드 화살표 문자 사용 */
    qproperty-icon: url("");   /* 기존 아이콘 숨김 */
    color: white;              /* 텍스트 색상 흰색 */
    background-color: transparent;
    border: none;
    width: 25px;
    height: 25px;
    font-size: 14px;
    font-weight: bold;
}

QToolButton#qt_calendar_prevmonth:hover,
QToolButton#qt_calendar_nextmonth:hover {
    background-color: #374151;
    border-radius: 4px;
}

/* 4. 중앙 월/년 텍스트 버튼 */
QToolButton#qt_calendar_monthbutton,
QToolButton#qt_calendar_yearbutton {
    color: white;
    background-color: transparent;
    font-size: 14px;
    font-weight: bold;
    margin: 0px 5px;
    padding: 2px 8px;
    border: none;
}

QToolButton#qt_calendar_monthbutton::menu-indicator {
    image: none;
}

QToolButton#qt_calendar_monthbutton:hover,
QToolButton#qt_calendar_yearbutton:hover {
    color: #60A5FA;
}

/* 6. 날짜 그리드 */
QCalendarWidget QAbstractItemView:enabled {
    background-color: #1F2937;
    color: white;
    selection-background-color: #2563EB;
    selection-color: white;
    outline: none;
}
QCalendarWidget QAbstractItemView:disabled {
    color: #4B5563;
}

/* 요일 헤더 */
QCalendarWidget QTableView {
    alternate-background-color: #1F2937;
    gridline-color: #1F2937;
}
"""