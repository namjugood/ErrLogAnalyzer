from collections import defaultdict
from datetime import datetime

class LogAggregator:
    def __init__(self):
        # 그룹핑 키: (channel, application, service, operation, error_code, error_msg)
        self.groups = defaultdict(lambda: {
            "total_count": 0,
            "nodes": set(),
            "first_seen": None,
            "last_seen": None,
            "peak_snapshot": [], # 최대 5개 스냅샷 저장
            "message_pattern": ""
        })
        # 시간대별 통계 (Key: "YYYY-MM-DD HH:MM", Value: {(code, msg): count})
        # 차트 생성을 위해 내부적으로 (code, msg) 튜플을 키로 사용하고 나중에 ErrorID로 변환
        self.time_series = defaultdict(lambda: defaultdict(int))

    def process_log(self, log_entry: dict):
        """
        단일 로그 라인을 처리하여 그룹에 병합
        log_entry 예시: {"time": "...", "chnl": "MA0", "app": "Biz", "svc": "Service", "op": "getData", "code": "ERR01", "msg": "..."}
        chnl: MA0(모바일앱), MW0(모바일웹), HOM(홈페이지)
        """
        # 1. Grouping Key 생성 (안전한 접근을 위해 .get 사용)
        chnl = log_entry.get('chnl', 'Unknown')
        app = log_entry.get('app', 'Unknown')
        svc = log_entry.get('svc', 'Unknown')
        op = log_entry.get('op', 'Unknown')
        code = log_entry.get('code', 'Unknown')
        msg = log_entry.get('msg', 'Unknown')
        
        key = (chnl, app, svc, op, code, msg)
        group = self.groups[key]

        # 2. 통계 업데이트
        group['total_count'] += 1
        
        # [수정] 데모용 하드코딩("Node-01") 제거
        # 실제 로그에 'node' 필드가 있는 경우에만 수집
        if 'node' in log_entry and log_entry['node']:
            group['nodes'].add(log_entry['node'])

        # 3. 시간 컨텍스트
        timestamp = log_entry.get('time', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not group['first_seen']:
            group['first_seen'] = timestamp
        group['last_seen'] = timestamp

        # 시간대별 집계 (메시지 구분을 위해 복합 키 사용)
        try:
            # 타임스탬프 길이 체크로 안전성 확보
            clean_time = timestamp.strip("[]")
            if len(clean_time) >= 16:
                time_bucket = clean_time[:16] # YYYY-MM-DD HH:MM
                self.time_series[time_bucket][(code, msg)] += 1
        except Exception:
            pass

        # 4. 스냅샷 (Peak Snapshot) — key: (chnl, app, svc, op, code, msg)
        if len(group['peak_snapshot']) < 5:
            # 가독성을 위해 key 인덱스 대신 변수명 사용
            raw_msg = f"[{timestamp}] [{app}] {svc}.{op} - {code} (Msg: {msg})"
            group['peak_snapshot'].append(raw_msg)
            
        # 5. 대표 메시지 패턴 저장
        if not group['message_pattern']:
            group['message_pattern'] = msg

    def export_to_dify_format(self):
        """기획서 3. 인터페이스 명세에 맞춘 JSON 생성"""
        issue_groups = []
        
        # 발생 횟수 내림차순 정렬하여 Error ID 부여 (Error01, Error02...)
        sorted_groups = sorted(self.groups.items(), key=lambda x: x[1]['total_count'], reverse=True)
        
        # (code, msg) -> ErrorID 매핑 테이블
        id_mapping = {}

        for idx, (key, data) in enumerate(sorted_groups, 1):
            # key: (chnl, app, svc, op, code, msg)
            chnl, app, svc, op, code, msg = key

            error_id = f"Error{idx:02d}"
            id_mapping[(code, msg)] = error_id

            issue_groups.append({
                "error_id": error_id,
                "channel": chnl,
                "signature": f"{app} | {svc}.{op} | {code}",
                "target_service": svc,
                "target_operation": op,
                "application": app,
                "error_code": code,
                "message_pattern": data['message_pattern'],
                "total_count": data['total_count'],
                "nodes": list(data['nodes']), # 노드 정보가 없으면 빈 리스트 반환
                "time_context": {
                    "first_seen": data['first_seen'],
                    "last_seen": data['last_seen'],
                    "peak_snapshot": data['peak_snapshot']
                }
            })
            
        # 차트용 시계열 데이터 키 변환 ((code, msg) -> ErrorID)
        final_time_series = defaultdict(lambda: defaultdict(int))
        for time_str, counts in self.time_series.items():
            for (code, msg), count in counts.items():
                if (code, msg) in id_mapping:
                    # 차트 범례에 표시될 키를 'Error01' 형태로 변환
                    mapped_key = id_mapping[(code, msg)]
                    final_time_series[time_str][mapped_key] += count

        return {
            "report_meta": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_logs_processed": sum(g['total_count'] for g in self.groups.values()),
                "monitoring_window": "Period" # [수정] "Realtime" -> "Period" (중립적 표현)
            },
            "issue_groups": issue_groups,
            "time_series_data": final_time_series
        }