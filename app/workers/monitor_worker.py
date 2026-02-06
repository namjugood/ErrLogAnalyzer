import os
import json
from PyQt6.QtCore import QThread, pyqtSignal
from app.core.aggregator import LogAggregator
from app.services.dify_client import DifyClient
from app.api.bxm_client import BxmApiClient

class MonitorWorker(QThread):
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(str, int) 

    def __init__(self, channel_data, dify_config, date_range):
        super().__init__()
        self.channel_data = channel_data
        self.dify_config = dify_config
        self.date_range = date_range
        self.is_running = True

    def run(self):
        channel_key = self.channel_data.get('key', 'Unknown')
        channel_name = self.channel_data.get('name', 'Unknown')
        
        base_url = self.channel_data.get('url')
        user_id = self.channel_data.get('id')
        password = self.channel_data.get('password')

        def logger_callback(msg, level="INFO"):
            self.log_signal.emit(msg, level)

        bxm_client = BxmApiClient(logger=logger_callback)

        # 1. BXM 로그인
        self.log_signal.emit(f"[{channel_name}] BXM 서버에 로그인 시도 중...", "INFO")
        success, cookies, msg = bxm_client.login(base_url, user_id, password)
        
        if not success:
            self.log_signal.emit(f"로그인 실패: {msg}", "ERROR")
            self.finished_signal.emit(channel_key, -1)
            return

        # 2. 에러 로그 조회
        start_dt = self.date_range.get('start')
        end_dt = self.date_range.get('end')
        self.log_signal.emit(f"로그 데이터 조회 중... ({start_dt} ~ {end_dt})", "SCAN")
        
        aggregator = LogAggregator()
        total_logs = 0
        page = 1
        
        try:
            while self.is_running and page <= 5:
                logs = bxm_client.get_today_error_logs(base_url, cookies, start_dt, end_dt, page_num=page)
                
                if not logs:
                    break
                    
                for log_entry in logs:
                    aggregator.process_log(log_entry)
                
                fetched_count = len(logs)
                total_logs += fetched_count
                self.log_signal.emit(f"데이터 수신 중 (Page {page}): {fetched_count}건", "INFO")
                
                if fetched_count < 100:
                    break
                page += 1

        except Exception as e:
            self.log_signal.emit(f"로그 조회 중 오류: {str(e)}", "ERROR")
            self.finished_signal.emit(channel_key, -1)
            return

        if total_logs == 0:
            self.log_signal.emit("조회된 에러 로그가 없습니다.", "SUCCESS")
            self.finished_signal.emit(channel_key, 0)
            return

        self.log_signal.emit(f"총 {total_logs}건의 로그 데이터 수집 완료", "SUCCESS")

        # 4. 데이터 집계
        json_data = aggregator.export_to_dify_format()
        error_count = sum(g['total_count'] for g in aggregator.groups.values())

        # 5. Dify Streaming 통신
        self.log_signal.emit(f"Dify AI 분석 요청 중... ({error_count}건)", "INFO")
        dify = DifyClient(self.dify_config, logger=logger_callback)
        
        ai_response_data = [] 
        step_count = 0
        
        try:
            # [변경] 스트리밍 데이터를 받아 터미널 진행률처럼 표시
            for status, data in dify.analyze_issues_streaming(json_data, user_id):
                if not self.is_running:
                    break

                if status == 'process':
                    step_count += 1
                    # [핵심] PROGRESS 레벨로 로그 전송 -> 대시보드에서 덮어쓰기 처리됨
                    # Dify에서 주는 메시지: "AI 처리 중: {node_title} ({event})"
                    # 이를 좀 더 진행상황처럼 포맷팅
                    clean_msg = data.replace('AI 처리 중: ', '')
                    display_msg = f"AI 분석 진행 중... [Step {step_count}] {clean_msg}"
                    self.log_signal.emit(display_msg, "PROGRESS")
                
                elif status == 'result':
                    ai_response_data = data
                    # 결과 수신 시 진행 완료 메시지
                    self.log_signal.emit(f"AI 분석 완료 (Total Steps: {step_count})", "SUCCESS")
                    
                elif status == 'error':
                    self.log_signal.emit(f"Dify 오류: {data}", "ERROR")

        except Exception as e:
            self.log_signal.emit(f"AI 분석 중 예외 발생: {e}", "ERROR")
        
        # 6. 리포트 저장 (생략된 경우 기존 로직 유지, 여기선 핵심 흐름만 구현)
        # 만약 ai_response_data가 있으면 PDF 생성 등 후속 작업 진행
        # ... (기존 파일에 있던 PDF 생성 로직 등은 생략됨, 필요시 추가)
        
        self.finished_signal.emit(channel_key, error_count)