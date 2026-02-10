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

    def _remove_think_tags(self, text: str) -> str:
        """
        텍스트에서 <think>...</think> 태그와 그 내용을 제거.
        Dify 응답에서 나타나는 사고 과정 태그를 정리하기 위함.
        """
        if not isinstance(text, str):
            return text
        # <think>...</think> 태그 제거 (개행 포함, 비탐욕적 매칭)
        pattern = r'<think>[\s\S]*?</think>'
        cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return cleaned.strip()

    def _extract_output_content(self, outputs):
        """
        outputs(dict)에서 결과용 내용 추출. 'res' 외에 text/result/answer 등 다양한 변수명 지원.
        워크플로우/노드별 출력 변수명이 달라도 수집할 수 있도록 함.
        """
        if not outputs or not isinstance(outputs, dict):
            return None
        for key in ('res', 'text', 'result', 'answer', 'output', 'content', 'data'):
            val = outputs.get(key)
            if val is None:
                continue
            if isinstance(val, str) and val.strip():
                return val
            if isinstance(val, (list, dict)):
                return val
        for key, val in outputs.items():
            if val is None:
                continue
            if isinstance(val, str) and val.strip():
                return val
            if isinstance(val, (list, dict)):
                return val
        return None

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

                                elif event == 'node_finished':
                                    node_data = data.get('data', {})
                                    node_title = node_data.get('title', 'Unknown')
                                    outputs = node_data.get('outputs', {}) or node_data.get('output', {})
                                    res_content = self._extract_output_content(outputs)
                                    if res_content is not None:
                                        chunk = self._parse_result(res_content)
                                        if chunk is not None:
                                            chunk_type = type(chunk).__name__
                                            self._log(f"[Dify] 노드 완료: {node_title} - 출력 타입: {chunk_type}", "INFO")
                                            yield ('result_chunk', chunk)

                                elif event == 'workflow_finished':
                                    outputs = data.get('data', {}).get('outputs', {})
                                    res_content = self._extract_output_content(outputs) if outputs else None
                                    if res_content is None and isinstance(data.get('data'), dict):
                                        res_content = data.get('data').get('outputs', {}).get('res')
                                    if res_content is not None:
                                        final_result = self._parse_result(res_content)
                                        if final_result is not None:
                                            result_type = type(final_result).__name__
                                            self._log(f"[Dify] 워크플로우 완료 - 최종 결과 타입: {result_type}", "INFO")
                                            yield ('result_chunk', final_result)

                                elif event in ('message', 'text_chunk', 'agent_message', 'text_delta'):
                                    # 스트리밍 텍스트 이벤트: 텍스트 조각을 문자열 청크로 수집
                                    inner = data.get('data') or data
                                    text = inner.get('text') or inner.get('answer') or inner.get('delta') or data.get('answer')
                                    if text is not None and str(text).strip():
                                        cleaned_text = self._remove_think_tags(str(text).strip())
                                        if cleaned_text:  # 태그 제거 후에도 내용이 있으면 반환
                                            yield ('result_chunk', cleaned_text)

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

    def _parse_result(self, res_content):
        """
        Dify 출력을 일관된 타입으로 반환. str이면 JSON 파싱 시도 후 dict/list 또는 원문 str.
        PDF 등 하류에서는 이 반환값이 dict/list 또는 str 둘 중 하나라고 가정하면 됨.
        """
        if res_content is None:
            return []
        if isinstance(res_content, list):
            return res_content
        if isinstance(res_content, dict):
            return res_content
        if isinstance(res_content, str):
            # <think> 태그 제거 후 파싱
            cleaned_content = self._remove_think_tags(res_content)
            return self._parse_json_from_markdown(cleaned_content)
        return res_content

    def _parse_json_from_markdown(self, text):
        """문자열이면 JSON 파싱 시도(마크다운 제거 후). 성공 시 dict/list, 실패 시 원문 str."""
        if not isinstance(text, str):
            return text
        # <think> 태그 제거
        text = self._remove_think_tags(text)
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
        except (json.JSONDecodeError, TypeError):
            return text