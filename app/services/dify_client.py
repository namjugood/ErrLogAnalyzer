import requests
import json
import re

class DifyClient:
    def __init__(self, api_config):
        """
        api_config: {
            "url": "...",
            "authorization": "Bearer ...",
            "content_type": "..."
        }
        """
        self.url = api_config.get("url")
        self.headers = {
            "Authorization": api_config.get("authorization"),
            "Content-Type": api_config.get("content_type", "application/json")
        }

    def analyze_issues(self, aggregator_data: dict, user_id="abc-123"):
        """
        1. 정제된 에러로그(aggregator_data)를 문자열로 파싱
        2. inputs.issue_groups에 담아 전송
        3. 응답값(res Array) 파싱 및 반환
        """
        # 1. 에러로그를 정제하여 string으로 파싱 (JSON String)
        issue_groups_str = json.dumps(aggregator_data, ensure_ascii=False, indent=2)

        # 2. Payload 구성
        payload = {
            "inputs": {
                "issue_groups": issue_groups_str
            },
            "response_mode": "blocking",
            "user": user_id
        }

        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            resp_json = response.json()
            
            # 3. 응답값 파싱 (data.outputs.res)
            # Dify workflow 출력이 'res' 변수에 Array 형태로 담겨있다고 가정
            outputs = resp_json.get('data', {}).get('outputs', {})
            res_content = outputs.get('res')

            if res_content is None:
                return []

            # res 타입이 Array인 경우 그대로 반환하거나
            # 문자열(Markdown 코드블럭)로 올 경우 JSON 파싱 시도
            if isinstance(res_content, list):
                return res_content
            
            if isinstance(res_content, str):
                return self._parse_json_from_markdown(res_content)
                
            return res_content

        except Exception as e:
            print(f"Dify API 호출 중 오류: {e}")
            return None

    def _parse_json_from_markdown(self, text):
        """Markdown 코드 블럭(```json ... ```) 제거 및 파싱"""
        try:
            # 코드 블럭 제거 패턴
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, text, re.DOTALL)
            
            if match:
                clean_text = match.group(1)
            else:
                # 코드 블럭이 없으면 그냥 텍스트 전체 시도 (혹은 ```만 제거)
                clean_text = text.strip().strip("`")
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print("JSON 파싱 실패 (Raw text 반환)")
            return text