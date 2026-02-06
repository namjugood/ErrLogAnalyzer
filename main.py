# main.py

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# SplashScreen은 비교적 가벼우므로 상단에 두어도 되지만, 
# 의존성을 최소화하기 위해 여기서 불러옵니다.
from app.ui.splash_screen import SplashScreen

def main():
    app = QApplication(sys.argv)
    
    # 1. 스플래시 스크린 표시 (가장 먼저 실행)
    splash = SplashScreen()
    splash.show()

    # 화면 중앙 배치
    screen_geometry = app.primaryScreen().geometry()
    x = (screen_geometry.width() - splash.width()) // 2
    y = (screen_geometry.height() - splash.height()) // 2
    splash.move(x, y)
    
    # UI가 즉시 그려지도록 이벤트 처리 강제 실행
    app.processEvents()

    # 2. 로딩 프로세스 및 지연 임포트
    
    # 단계 1: 환경 설정 로드
    splash.update_progress(10, "환경 설정 파일 로드 중...")
    app.processEvents()
    time.sleep(0.3) # 시각적 효과를 위한 지연

    # 단계 2: 리소스 확인 및 핵심 모듈 로드 (여기로 import 이동)
    splash.update_progress(30, "핵심 모듈 로딩 중...")
    app.processEvents()
    
    # [핵심 수정] MainWindow를 스플래시가 뜬 후에 임포트합니다.
    # 이 시점에 무거운 라이브러리들이 메모리에 로드됩니다.
    from app.ui.main_window import MainWindow
    
    time.sleep(0.3)

    # 단계 3: 메인 윈도우 초기화
    splash.update_progress(50, "메인 인터페이스 초기화 중...")
    app.processEvents()
    
    # 실제 MainWindow 객체 생성
    window = MainWindow()
    
    # 단계 4: 모듈 연결
    splash.update_progress(80, "로그 분석 엔진 연결 중...")
    app.processEvents()
    time.sleep(0.3)

    # 단계 5: 완료
    splash.update_progress(100, "실행 준비 완료")
    app.processEvents()
    time.sleep(0.2)

    # 3. 메인 윈도우 표시 및 스플래시 종료
    window.show()
    splash.finish(window) # 메인 윈도우가 뜨면 스플래시 닫기
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()