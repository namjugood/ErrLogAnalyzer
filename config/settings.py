import os

# 전역 설정 관리
class AppConfig:
    APP_NAME = "BXM Analyzer"
    VERSION = "v1.0.4"
    
    # Dify 설정
    DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
    DIFY_API_KEY = "YOUR_API_KEY_HERE"
    
    # UI 색상 테마 (이미지 참고)
    COLOR_BG = "#111827"       # 다크 네이비 배경
    COLOR_ACCENT = "#2563EB"   # 파란색 버튼
    COLOR_TEXT = "#FFFFFF"
    
    # [수정 요청 1] 기본 로그 경로: 프로그램 설치 경로/logs
    # 현재 실행 위치(os.getcwd()) 기준 logs 폴더
    BASE_DIR = os.getcwd()
    DEFAULT_LOG_PATH = os.path.join(BASE_DIR, "logs")