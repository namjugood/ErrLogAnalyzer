from collections import defaultdict
from datetime import datetime

class LogAggregator:
    def __init__(self):
        # 그룹핑 키: (application, service, operation, error_code)
        self.groups = defaultdict(lambda: {
            "total_count": 0,
            "nodes": set(),
            "first_seen": None,
            "last_seen": None,
            "peak_snapshot": [], # 최대 5개 스냅샷 저장
            "message_pattern": ""
        })

    def process_log(self, log_entry: dict):
        """
        단일 로그 라인을 처리하여 그룹에 병합
        log_entry 예시: {"time": "...", "app": "Biz", "svc": "Service", "op": "getData", "code": "ERR01", "msg": "..."}
        """
        # 1. Grouping Key 생성
        key = (log_entry['app'], log_entry['svc'], log_entry['op'], log_entry['code'])
        group = self.groups[key]

        # 2. 통계 업데이트
        group['total_count'] += 1
        group['nodes'].add("Node-01") # 데모용 고정값
        
        # 3. 시간 컨텍스트
        timestamp = log_entry['time']
        if not group['first_seen']:
            group['first_seen'] = timestamp
        group['last_seen'] = timestamp

        # 4. 스냅샷 (Peak Snapshot) - 기획서 요구사항: Raw Data 첨부
        if len(group['peak_snapshot']) < 5:
            raw_msg = f"[{timestamp}] [{key[0]}] {key[1]}.{key[2]} - {key[3]} (Msg: {log_entry['msg']})"
            group['peak_snapshot'].append(raw_msg)
            
        # 5. 대표 메시지 패턴 저장 (단순화: 첫 번째 메시지 사용)
        if not group['message_pattern']:
            group['message_pattern'] = log_entry['msg']

    def export_to_dify_format(self):
        """기획서 3. 인터페이스 명세에 맞춘 JSON 생성"""
        issue_groups = []
        
        for key, data in self.groups.items():
            app, svc, op, code = key
            
            issue_groups.append({
                "signature": f"{app} | {svc}.{op} | {code}",
                "target_service": svc,
                "target_operation": op,
                "application": app,
                "error_code": code,
                "message_pattern": data['message_pattern'],
                "total_count": data['total_count'],
                "nodes": list(data['nodes']),
                "time_context": {
                    "first_seen": data['first_seen'],
                    "last_seen": data['last_seen'],
                    "peak_snapshot": data['peak_snapshot']
                }
            })
            
        return {
            "report_meta": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_logs_processed": sum(g['total_count'] for g in self.groups.values()),
                "monitoring_window": "Realtime"
            },
            "issue_groups": issue_groups
        }