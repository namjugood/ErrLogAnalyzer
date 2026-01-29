import re
from datetime import datetime

class LogParser:
    """
    다양한 형태의 시스템 로그를 파싱하여 표준 포맷으로 변환
    표준 포맷: {time, app, svc, op, code, msg}
    """
    
    # 예시 로그 포맷: [2025-01-23 14:00:00] [Biz] Service.getData - AON001 Message...
    LOG_PATTERN = re.compile(
        r"\[(?P<time>.*?)\]\s+"       # Timestamp
        r"\[(?P<app>.*?)\]\s+"       # Application Name
        r"(?P<svc>\w+)\.(?P<op>\w+)\s+-\s+" # Service.Operation
        r"(?P<code>\w+)\s+"          # Error Code
        r"(?P<msg>.*)"               # Message Body
    )

    @staticmethod
    def parse_line(line: str) -> dict:
        match = LogParser.LOG_PATTERN.search(line)
        if match:
            return match.groupdict()
        
        # 매칭되지 않는 경우 (단순 정보성 로그 등) -> None 반환하거나 기본값 처리
        # 여기서는 None을 반환하여 Aggregator가 무시하도록 함
        return None

    @staticmethod
    def is_error(log_dict: dict) -> bool:
        """단순 필터링 로직 (필요시 사용)"""
        if not log_dict: return False
        # 에러 코드에 'ERR'이나 'FAIL'이 포함되어 있으면 True
        return "ERR" in log_dict['code'].upper() or "FAIL" in log_dict['code'].upper()