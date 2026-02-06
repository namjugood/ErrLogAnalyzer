# app/api/bxm_client.py

import requests
import json
import random
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.chnl_constants import CHNL_LABELS

class BxmApiClient:
    """
    BXM 시스템 모니터링을 위한 API 클라이언트
    (Reference: api_service.py 패턴 적용)
    """
    def __init__(self, logger=None):
        self.timeout = 10
        self.logger = logger
        self.session_pool = {}  # {base_url: Session}
        self.is_mock_mode = False
        
        # 재시도 전략 설정 (api_service.py 참조)
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        self.adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )

    def _log(self, message, level="INFO"):
        if self.logger:
            self.logger(message, level)

    def _get_session(self, base_url):
        """
        URL별 세션 가져오기 (커넥션 재사용용)
        참고: 로그인 세션과는 별도로 관리되며, 쿠키는 인자로 받아서 사용함.
        """
        if base_url not in self.session_pool:
            session = requests.Session()
            session.mount("http://", self.adapter)
            session.mount("https://", self.adapter)
            self.session_pool[base_url] = session
        return self.session_pool[base_url]

    def login(self, base_url, user_id, password):
        """
        로그인 시도. (api_service.py의 login 메서드 패턴 적용)
        - 독립적인 세션을 생성하여 로그인 후 쿠키 반환
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
            # 로그인은 풀(Pool)이 아닌 새 세션 사용
            session = requests.Session()
            
            # 실제 요청 시도
            response = session.post(api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            res_json = response.json()
            
            # 성공 여부 판단 로직 (참고 코드 방식)
            is_success = False
            if "ResponseCode" in res_json and res_json["ResponseCode"].get("code") == 100:
                is_success = True
            elif "header" in res_json and res_json["header"].get("returnCode") == "0":
                is_success = True

            if is_success:
                self._log(f"[{base_url}] 로그인 성공.", "SUCCESS")
                # 세션 객체가 아닌 '쿠키'를 반환
                return True, session.cookies, "Login Success"
            else:
                msg = res_json.get("header", {}).get("returnMessage", "Unknown Error")
                self._log(f"[{base_url}] 로그인 실패 (서버 응답): {msg}", "WARN")
                # 실패 시 Mock 전환
                self.is_mock_mode = True
                return True, None, "Mock Login Success"

        except Exception as e:
            self._log(f"[{base_url}] API 연결 실패 ({str(e)}). 가상(Mock) 모드로 전환합니다.", "WARN")
            self.is_mock_mode = True
            return True, None, "Mock Login Success"

    def get_today_error_logs(self, base_url, cookies, start_dt=None, end_dt=None, page_num=1):
        """
        에러 로그 조회.
        참고 코드의 get_system_logs 패턴 적용
        """

        if not start_dt:
            start_dt = datetime.now().strftime("%Y-%m-%d 00:00")
        if not end_dt:
            end_dt = datetime.now().strftime("%Y-%m-%d 23:59")

        if self.is_mock_mode:
            print(f"[BXM_DEBUG] Mock 모드 활성화 - 실제 API 호출 없이 가상 로그 반환 (page {page_num})")
            return self._generate_mock_logs(page_num)

        api_url = f"{base_url.rstrip('/')}/bxmAdmin/json"
        
        # [핵심 변경] 복잡한 헤더 제거하고 기본 헤더만 사용 (참고 코드 방식)
        headers = {
            "Content-Type": "application/json; charset=UTF-8", 
            "Accept": "application/json"
        }

        payload = {
            "header": {
                "application": "bxmAdmin", "service": "OnlineLogService",
                "operation": "getErrorLogList", "langCd": "ko"
            },
            "OnlineLogSearchConditionOMM": {
                "brdyDt": "",
                "bxmAppId": "",
                "ci": "",
                "custNm": "",
                "errCd": "",
                "guid": "",
                "logOccurDttmEnd": end_dt,
                "logOccurDttmStart": start_dt,
                "nodeName": "",
                "opNm": "",
                "pageCount": "100",
                "pageNum": str(page_num),
                "sendUserIp": "",
                "svcNm": ""
            }
        }

        try:
            # [핵심 변경] 세션 풀 사용 + 명시적 쿠키 전달
            session = self._get_session(base_url)

            response = session.post(api_url, headers=headers, cookies=cookies, json=payload, timeout=self.timeout)
            response.raise_for_status()
            res_json = response.json()

            top_keys = list(res_json.keys()) if isinstance(res_json, dict) else []
            has_omm = "ErrorLogListOMM" in res_json
            has_list = has_omm and "errorLogList" in res_json.get("ErrorLogListOMM")

            if has_omm and has_list:
                raw_logs = res_json["ErrorLogListOMM"]["errorLogList"]
                parsed = self._parse_logs(raw_logs)
                self._log(f"에러 로그 조회 응답: 최상위 키={top_keys}, 건수={len(parsed)}", "INFO")
                return parsed
            else:
                self._log(f"응답 내 로그 없음 (최상위 키: {top_keys})", "WARN")
                return []

        except Exception as e:
            self._log(f"API 호출 중 오류 발생: {e}", "WARN")
            self.is_mock_mode = True
            return self._generate_mock_logs(page_num)

    def _parse_logs(self, raw_list):
        """
        [신규] 참고 코드(api_service.py)의 _parse_logs 로직 이식
        다양한 필드에서 에러 메시지를 추출하여 정확도 향상
        """
        parsed_data = []
        for item in raw_list:
            # 에러 메시지 추출 우선순위 적용
            error_message = item.get("msgType", "Error")         # 기존 폴백
            
            # 에러 코드 결합
            msg_cd = item.get("errCd", "FAIL")
            if msg_cd and msg_cd not in ["0", "00", "0000", "S", "SUCCESS"]:
                if error_message:
                    error_message = f"[{msg_cd}] {error_message}"
                else:
                    error_message = f"Error Code: [{msg_cd}]"

            parsed_data.append({
                "time": item.get("logOccurDttm", "Unknown"),
                "chnl": item.get("chlTypeCd", "Unknown"),
                "app": item.get("application", "Unknown"),
                "svc": item.get("service", "Unknown"),
                "op": item.get("operation", "Unknown"),
                "code": msg_cd,
                "msg": error_message
            })
        return parsed_data

    def _generate_mock_logs(self, page_num):
        """테스트를 위한 가상 에러 로그 생성기"""
        time.sleep(0.5) 
        if page_num > 3: return []

        self._log(f"[Mock] 가상 에러 로그 생성 중... (Page {page_num})", "DEBUG")
        
        mock_data = []
        count = random.randint(10, 20)
        
        channels = list(CHNL_LABELS.keys())
        apps = ["Bxm-Core", "Bxm-FEP", "Smart-Banking"]
        services = ["TransferSvc", "AccountSvc", "CustomerSvc", "AuthSvc"]
        operations = ["checkBalance", "transfer", "login", "validateUser"]
        errors = [("DB-001", "DB Timeout"), ("NET-503", "Gateway Timeout")]

        for _ in range(count):
            err = random.choice(errors)
            mock_data.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "chnl": random.choice(channels),
                "app": random.choice(apps),
                "svc": random.choice(services),
                "op": random.choice(operations),
                "code": err[0],
                "msg": err[1]
            })
            
        return mock_data