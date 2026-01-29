from datetime import datetime

def current_time_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_number(num):
    return f"{num:,}"

def get_severity_color(severity):
    """심각도에 따른 색상 코드 반환"""
    colors = {
        "CRITICAL": "#EF4444", # Red
        "HIGH": "#F59E0B",     # Orange
        "MEDIUM": "#3B82F6",   # Blue
        "LOW": "#10B981"       # Green
    }
    return colors.get(severity.upper(), "#9CA3AF")