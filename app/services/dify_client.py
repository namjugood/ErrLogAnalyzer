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
        """
        [변경] Streaming(SSE) 방식으로 Dify API 호출
        Generator를 반환하며, (status_type, data) 튜플을 yield 합니다.
        
        status_type: 
          - 'process': 진행 상황 메시지
          - 'result': 최종 분석 결과 (JSON 객체)
          - 'error': 에러 메시지
        """
        issue_groups_str = json.dumps(aggregator_data.get("issue_groups", []), ensure_ascii=False, indent=2)
        
        payload = {
            "inputs": {
                "issue_groups": issue_groups_str
            },
            "query": "입력한 로그를 분석하세요",
            "response_mode": "streaming",  # [핵심] streaming 모드로 설정
            "conversation_id": "",
            "user": user_id
        }

        self._log(f"[Dify] 스트리밍 요청 시작: {self.url}", "INFO")

        try:
            # stream=True 옵션 사용
            # timeout=(connect_timeout, read_timeout) 
            # 스트리밍이므로 read_timeout을 넉넉하게 주거나 None으로 설정
            with requests.post(self.url, headers=self.headers, json=payload, stream=True, timeout=(10, 300)) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        
                        # SSE 포맷은 "data: "로 시작
                        if decoded_line.startswith("data:"):
                            json_str = decoded_line.replace("data: ", "", 1).strip()
                            
                            try:
                                data = json.loads(json_str)
                                event = data.get('event')

                                # 1. 진행 상황 (노드 실행 등)
                                if event in ['workflow_started', 'node_started']:
                                    node_title = data.get('data', {}).get('title', 'Unknown Node')
                                    yield ('process', f"AI 처리 중: {node_title} ({event})")

                                # 2. 최종 완료 (여기에 결과가 담김)
                                elif event == 'workflow_finished':
                                    outputs = data.get('data', {}).get('outputs', {})
                                    res_content = outputs.get('res')
                                    
                                    # 결과 파싱
                                    final_result = self._parse_result(res_content)
                                    yield ('result', final_result)

                                # 3. 에러 발생 시
                                elif event == 'error':
                                    yield ('error', f"Dify Error: {data.get('message')}")

                            except json.JSONDecodeError:
                                pass
                            except Exception as e:
                                self._log(f"[Dify] 스트림 파싱 에러: {e}", "ERROR")

        except requests.RequestException as e:
            self._log(f"[Dify] 통신 오류: {e}", "ERROR")
            yield ('error', str(e))

    def _parse_result(self, res_content):
        """결과 데이터 파싱 (JSON or String)"""
        if res_content is None:
            return []
        
        if isinstance(res_content, list):
            return res_content

        if isinstance(res_content, str):
            return self._parse_json_from_markdown(res_content)
            
        return res_content

    def _parse_json_from_markdown(self, text):
        """기존 코드 유지"""
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