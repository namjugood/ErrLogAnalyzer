# app/api/bxm_client.py

import requests
import json
import random
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BxmApiClient:
    """
    BXM 시스템 모니터링을 위한 API 클라이언트 (Mock 모드 지원)
    """
    def __init__(self, logger=None):
        self.timeout = 5  # 타임아웃 단축 (빠른 Mock 전환 위해)
        self.logger = logger
        self.session_pool = {}
        self.is_mock_mode = False # Mock 모드 상태 플래그
        
        retry_strategy = Retry(
            total=1,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        self.adapter = HTTPAdapter(max_retries=retry_strategy)

    def _log(self, message, level="INFO"):
        if self.logger:
            self.logger(message, level)

    def _get_session(self, base_url):
        if base_url not in self.session_pool:
            session = requests.Session()
            session.mount("http://", self.adapter)
            session.mount("https://", self.adapter)
            self.session_pool[base_url] = session
        return self.session_pool[base_url]

    def login(self, base_url, user_id, password):
        """
        로그인 시도. 실패 시 Mock 모드로 전환하여 성공 처리.
        """
        api_url = f"{base_url.rstrip('/')}/bxmAdmin/json/login"
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8", 
            "Accept": "application/json"
        }
        
        payload = {
            "header": {
                "application": "bxmAdmin", "langCd": "ko",
                "service": "AuthorityService", "operation": "loginOperation"
            },
            "LoginOMM": {
                "userId": user_id, "userPwd": password, "lang": "ko", "domainId": "OKC"
            }
        }

        try:
            self._log(f"[{base_url}] 로그인 시도 중... ID: {user_id}", "DEBUG")
            session = requests.Session()
            
            # 실제 요청 시도
            response = session.post(api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            self._log(f"[{base_url}] 로그인 성공.", "SUCCESS")
            return True, session.cookies, "Login Success"

        except Exception as e:
            # 실패 시 Mock 모드 활성화
            self._log(f"[{base_url}] API 연결 실패 ({str(e)}). 가상(Mock) 모드로 전환합니다.", "WARN")
            self.is_mock_mode = True
            return True, None, "Mock Login Success"

    def get_today_error_logs(self, base_url, cookies, start_dt=None, end_dt=None, page_num=1):
        """
        에러 로그 조회.
        start_dt, end_dt: "YYYY-MM-DD HH:MM:SS" 형식의 문자열
        """
        # 날짜 기본값 처리 (오늘)
        if not start_dt:
            start_dt = datetime.now().strftime("%Y-%m-%d 00:00:00")
        if not end_dt:
            end_dt = datetime.now().strftime("%Y-%m-%d 23:59:59")

        # Mock 모드 처리 (파라미터 로깅 추가)
        if self.is_mock_mode:
            self._log(f"[Mock] 조회 요청: {start_dt} ~ {end_dt}", "DEBUG")
            return self._generate_mock_logs(page_num)

        # 실제 API 호출 로직
        api_url = f"{base_url.rstrip('/')}/bxmAdmin/json"
        
        self._log(f"[{base_url}] 에러 로그 조회 요청 (Page: {page_num}) - 기간: {start_dt} ~ {end_dt}", "DEBUG")

        payload = {
            "header": {
                "application": "bxmAdmin", "service": "OnlineLogService",
                "operation": "getServiceLogList", "langCd": "ko"
            },
            "OnlineLogSearchConditionOMM": {
                # [수정] 전달받은 날짜 사용
                "opOccurDttmStart": start_dt, 
                "opOccurDttmEnd": end_dt,
                "pageCount": "100", 
                "pageNum": str(page_num),
                "guid": "", "svcNm": "", "opNm": "", "bxmAppId": "", "opErrYn": "Y"
            }
        }

        try:
            session = self._get_session(base_url)
            response = session.post(api_url, headers={}, cookies=cookies, json=payload, timeout=self.timeout)
            response.raise_for_status()
            res_json = response.json()
            
            # 실제 데이터 파싱
            error_logs = []
            if "ServiceLogListOMM" in res_json and "serviceLogList" in res_json["ServiceLogListOMM"]:
                for item in res_json["ServiceLogListOMM"]["serviceLogList"]:
                    error_logs.append({
                        "time": item.get("opOccurDttm"),
                        "app": item.get("bxmAppId", "Unknown"),
                        "svc": item.get("svcNm", "Unknown"),
                        "op": item.get("opNm", "Unknown"),
                        "code": item.get("errCode", "FAIL"),
                        "msg": item.get("msgCont") or item.get("errMsg") or "Error"
                    })
            return error_logs

        except Exception as e:
            self._log(f"API 호출 중 오류 발생: {e}. 가상 데이터로 대체합니다.", "WARN")
            self.is_mock_mode = True
            return self._generate_mock_logs(page_num)

    def _generate_mock_logs(self, page_num):
        """테스트를 위한 가상 에러 로그 생성기"""
        time.sleep(0.5) # API 지연 시뮬레이션
        
        # 3페이지까지만 데이터가 있다고 가정
        if page_num > 3:
            return []

        self._log(f"[Mock] 가상 에러 로그 생성 중... (Page {page_num})", "DEBUG")
        
        mock_data = []
        # 페이지당 10~20개의 랜덤 에러 생성
        count = random.randint(10, 20)
        
        apps = ["Bxm-Core", "Bxm-FEP", "Smart-Banking"]
        services = ["TransferSvc", "AccountSvc", "CustomerSvc", "AuthSvc"]
        operations = ["checkBalance", "transfer", "login", "validateUser"]
        errors = [
            ("DB-001", "Database connection timeout"),
            ("NET-503", "Gateway timeout exception"),
            ("BIZ-102", "Invalid account status"),
            ("SYS-999", "NullPointerException occurred")
        ]

        for _ in range(count):
            err = random.choice(errors)
            mock_data.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "app": random.choice(apps),
                "svc": random.choice(services),
                "op": random.choice(operations),
                "code": err[0],
                "msg": err[1]
            })
            
        return mock_data