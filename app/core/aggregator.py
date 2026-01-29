from collections import defaultdict
from datetime import datetime

class LogAggregator:
    def __init__(self):
        # 그룹핑 키 변경: (application, service, operation, error_code, error_msg)
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
        log_entry 예시: {"time": "...", "app": "Biz", "svc": "Service", "op": "getData", "code": "ERR01", "msg": "..."}
        """
        # 1. Grouping Key 생성 (메시지 포함하여 구분)
        key = (log_entry['app'], log_entry['svc'], log_entry['op'], log_entry['code'], log_entry['msg'])
        group = self.groups[key]

        # 2. 통계 업데이트
        group['total_count'] += 1
        group['nodes'].add("Node-01") # 데모용 고정값
        
        # 3. 시간 컨텍스트
        timestamp = log_entry['time']
        if not group['first_seen']:
            group['first_seen'] = timestamp
        group['last_seen'] = timestamp

        # [수정] 시간대별 집계 (메시지 구분을 위해 복합 키 사용)
        try:
            raw_time = timestamp.strip("[]")
            # 초 단위 제거하여 분 단위 버킷 생성
            time_bucket = raw_time[:16] 
            # 차트에서도 메시지별 구분을 위해 (code, msg) 튜플을 임시 키로 사용
            self.time_series[time_bucket][(log_entry['code'], log_entry['msg'])] += 1
        except:
            pass

        # 4. 스냅샷 (Peak Snapshot)
        if len(group['peak_snapshot']) < 5:
            raw_msg = f"[{timestamp}] [{key[0]}] {key[1]}.{key[2]} - {key[3]} (Msg: {log_entry['msg']})"
            group['peak_snapshot'].append(raw_msg)
            
        # 5. 대표 메시지 패턴 저장
        if not group['message_pattern']:
            group['message_pattern'] = log_entry['msg']

    def export_to_dify_format(self):
        """기획서 3. 인터페이스 명세에 맞춘 JSON 생성"""
        issue_groups = []
        
        # 발생 횟수 내림차순 정렬하여 Error ID 부여 (Error01, Error02...)
        sorted_groups = sorted(self.groups.items(), key=lambda x: x[1]['total_count'], reverse=True)
        
        # (code, msg) -> ErrorID 매핑 테이블
        id_mapping = {}

        for idx, (key, data) in enumerate(sorted_groups, 1):
            app, svc, op, code, msg = key
            
            # 구분 ID 생성 (예: Error01)
            error_id = f"Error{idx:02d}"
            id_mapping[(code, msg)] = error_id

            issue_groups.append({
                "error_id": error_id,  # [추가] 구분 컬럼용 ID
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
            
        # [수정] 차트용 시계열 데이터 키 변환 ((code, msg) -> ErrorID)
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
                "monitoring_window": "Realtime"
            },
            "issue_groups": issue_groups,
            "time_series_data": final_time_series
        }