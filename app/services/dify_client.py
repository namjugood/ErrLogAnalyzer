# app/services/dify_client.py

import requests
import json
import re

class DifyClient:
    def __init__(self, api_config, logger=None):
        self.url = api_config.get("url")
        self.headers = {
            "Authorization": api_config.get("authorization"),
            "Content-Type": api_config.get("content_type", "application/json")
        }
        self.logger = logger

    def _log(self, message: str, level: str = "INFO"):
        if self.logger:
            self.logger(message, level)

    def analyze_issues_streaming(self, aggregator_data: dict, user_id="abc-123"):
        # [수정 1] JSON 직렬화 실패 방지를 위한 예외 처리
        try:
            issue_groups_str = json.dumps(aggregator_data.get("issue_groups", []), ensure_ascii=False, indent=2)
        except Exception as e:
            yield ('error', f"데이터 준비 중 오류 발생: {e}")
            return

        payload = {
            "inputs": {
                "issue_groups": issue_groups_str
            },
            "query": "입력한 로그를 분석하세요",
            "response_mode": "streaming",
            "conversation_id": "",
            "user": user_id
        }

        self._log(f"[Dify] 스트리밍 요청 시작: {self.url}", "INFO")
        print(f"DEBUG: Request sending to {self.url}") # [디버깅용 콘솔 출력]

        try:
            # [수정] verify=False 옵션 추가 (SSL 인증서 충돌 방지)
            # [수정] timeout 설정 유지
            with requests.post(
                self.url, 
                headers=self.headers, 
                json=payload, 
                stream=True, 
                timeout=(10, 300),
                verify=False  # [중요] SSL 검증 비활성화 (크래시 방지 테스트)
            ) as response:
                print("DEBUG: Response received headers") # [디버깅용]
                response.raise_for_status()

                # [수정] decode_unicode=True 유지
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        # print(f"DEBUG: Line received - {line[:30]}...") # [필요시 주석 해제]
                        if line.startswith("data:"):
                            json_str = line.replace("data: ", "", 1).strip()
                            try:
                                data = json.loads(json_str)
                                event = data.get('event')

                                if event in ['workflow_started', 'node_started']:
                                    node_title = data.get('data', {}).get('title', 'Unknown Node')
                                    yield ('process', f"AI 처리 중: {node_title} ({event})")

                                elif event == 'workflow_finished':
                                    outputs = data.get('data', {}).get('outputs', {})
                                    res_content = outputs.get('res')
                                    final_result = self._parse_result(res_content)
                                    yield ('result', final_result)

                                elif event == 'error':
                                    yield ('error', f"Dify Error: {data.get('message')}")
                                    
                            except json.JSONDecodeError:
                                pass
                            except Exception as e:
                                self._log(f"[Dify] 파싱 오류: {e}", "ERROR")

        except requests.exceptions.SSLError as e:
            print(f"DEBUG: SSL Error {e}")
            self._log(f"[Dify] SSL 인증서 오류: {e}", "ERROR")
            yield ('error', f"SSL Error: {e}")
        except requests.RequestException as e:
            print(f"DEBUG: Request Error {e}")
            self._log(f"[Dify] 통신 오류: {e}", "ERROR")
            yield ('error', str(e))
        except Exception as e:
            print(f"DEBUG: General Error {e}")
            self._log(f"[Dify] 알 수 없는 오류: {e}", "ERROR")
            yield ('error', str(e))

    # ... 나머지 메서드(_parse_result 등)는 기존과 동일 ...
    def _parse_result(self, res_content):
        if res_content is None:
            return []
        if isinstance(res_content, list):
            return res_content
        if isinstance(res_content, str):
            return self._parse_json_from_markdown(res_content)
        return res_content

    def _parse_json_from_markdown(self, text):
        try:
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                clean_text = match.group(1)
            else:
                clean_text = text.strip().strip("`")
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            return json.loads(clean_text)
        except json.JSONDecodeError:
            return text