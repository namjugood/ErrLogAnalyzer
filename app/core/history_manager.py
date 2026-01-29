# app/core/history_manager.py

import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, history_file="data/history.json"):
        self.history_file = history_file
        self.ensure_file()

    def ensure_file(self):
        if not os.path.exists(os.path.dirname(self.history_file)):
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def add_record(self, channel_name, start_time, end_time, file_path, error_count, status="성공"):
        """
        리포트 생성 이력 저장
        """
        record = {
            "id": int(datetime.now().timestamp()),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "channel": channel_name,
            "start_period": start_time,
            "end_period": end_time,
            "report_path": file_path,
            "file_name": os.path.basename(file_path),
            "error_count": str(error_count),
            "status": status
        }

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data.insert(0, record) # 최신순 저장
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save history: {e}")
            return False

    def get_records(self, channel_filter="전체"):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if channel_filter == "전체":
                return data
            
            return [d for d in data if d.get('channel') == channel_filter]
        except:
            return []