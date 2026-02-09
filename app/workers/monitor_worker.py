# app/workers/monitor_worker.py

import os
import json
import time  # [추가] 시간 제어를 위한 모듈
from PyQt6.QtCore import QThread, pyqtSignal
from app.core.aggregator import LogAggregator
from app.services.dify_client import DifyClient
from app.services.pdf_generator import PDFGenerator
from app.core.history_manager import HistoryManager
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
        self.last_update_time = 0  # [추가] 마지막 UI 업데이트 시간 기록

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

        # 4. 데이터 집계 및 Dify 포맷 변환
        json_data = aggregator.export_to_dify_format()
        error_count = sum(g['total_count'] for g in aggregator.groups.values())

        # 5. Dify Streaming 통신
        self.log_signal.emit(f"Dify AI 분석 요청 중... ({error_count}건)", "INFO")
        dify = DifyClient(self.dify_config, logger=logger_callback)
        
        ai_response_data = [] 
        ai_text = ""
        step_count = 0
        
        try:
            # Generator로부터 데이터 수신 (Blocking 방지)
            for status, data in dify.analyze_issues_streaming(json_data):
                if not self.is_running:
                    break

                if status == 'process':
                    step_count += 1
                    
                    # [핵심 수정] 과도한 UI 업데이트 방지 (0.1초 간격 제한)
                    current_time = time.time()
                    if current_time - self.last_update_time > 0.1:  # 100ms
                        clean_msg = data.replace('AI 처리 중: ', '') if isinstance(data, str) else str(data)
                        display_msg = f"AI 분석 진행 중... [Step {step_count}] {clean_msg}"
                        self.log_signal.emit(display_msg, "PROGRESS")
                        self.last_update_time = current_time
                    
                elif status == 'result':
                    ai_response_data = data
                    # 완료 메시지는 즉시 전송
                    self.log_signal.emit(f"AI 분석 완료 (Total Steps: {step_count})", "SUCCESS")
                    
                elif status == 'error':
                    self.log_signal.emit(f"분석 중 오류 발생: {data}", "ERROR")

            # 결과 데이터 변환
            if not ai_response_data:
                ai_text = "AI 분석 응답이 비어있거나 실패했습니다."
                if self.is_running: 
                    self.log_signal.emit("Dify 분석 응답 없음", "WARN")
            else:
                if isinstance(ai_response_data, str):
                    ai_text = ai_response_data
                else:
                    ai_text = json.dumps(ai_response_data, ensure_ascii=False, indent=2)

        except Exception as e:
            ai_text = f"AI 분석 중 치명적 오류: {str(e)}"
            self.log_signal.emit(f"Dify 통신 오류: {str(e)}", "ERROR")

        # 6. PDF 리포트 제작
        if self.is_running:
            self.log_signal.emit("PDF 리포트 생성 중...", "INFO")
            font_path = os.path.join("app", "assets", "fonts", "NanumGothic.ttf")
            
            # PDFGenerator 인스턴스 생성
            pdf_gen = PDFGenerator(font_path=font_path)
            
            report_path = ""
            try:
                # 리포트 생성
                report_path = pdf_gen.create_report(channel_name, ai_text, json_data)
                self.log_signal.emit(f"리포트 생성 완료: {os.path.basename(report_path)}", "INFO")
            except Exception as e:
                self.log_signal.emit(f"PDF 생성 실패: {str(e)}", "ERROR")

            # 7. 히스토리 저장
            if report_path:
                try:
                    history = HistoryManager()
                    history.add_record(
                        channel_name=channel_name,
                        start_time=start_dt,
                        end_time=end_dt,
                        file_path=report_path,
                        error_count=error_count,
                        status="성공"
                    )
                except Exception as e:
                    self.log_signal.emit(f"히스토리 저장 실패: {e}", "WARN")

            # 모든 작업 완료 후 시그널 전송
            self.finished_signal.emit(channel_key, error_count)

    def stop(self):
        self.is_running = False