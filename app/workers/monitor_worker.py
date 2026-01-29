# app/workers/monitor_worker.py

import os
from PyQt6.QtCore import QThread, pyqtSignal
from app.core.log_parser import LogParser
from app.core.aggregator import LogAggregator
from app.services.dify_client import DifyClient
from app.services.pdf_generator import PDFGenerator
from app.core.history_manager import HistoryManager

class MonitorWorker(QThread):
    # 시그널: (메시지, 레벨), (종료시 에러카운트)
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(str, int) 

    def __init__(self, channel_data, dify_config, date_range):
        super().__init__()
        self.channel_data = channel_data
        self.dify_config = dify_config
        self.date_range = date_range # {"start": "...", "end": "..."}
        self.is_running = True

    def run(self):
        channel_key = self.channel_data.get('key', 'Unknown')
        channel_name = self.channel_data.get('name', 'Unknown')
        
        # 1. 파일 경로 확인 (예시: 로컬 경로라고 가정)
        # 실제 환경에서는 SSH나 HTTP로 로그를 가져오는 로직이 필요할 수 있음
        # 여기서는 settings.json의 log_path + 채널명.log 라고 가정
        import json
        settings_path = os.path.join("settings", "settings.json")
        base_path = "/var/log/bxm/current/"
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                s_data = json.load(f)
                base_path = s_data.get("log_path", base_path)
        except:
            pass

        # 테스트용으로 파일이 없으면 생성 (시뮬레이션)
        log_file = os.path.join(base_path, f"{channel_name.lower()}.log")
        if not os.path.exists(log_file):
            self.log_signal.emit(f"로그 파일이 없습니다: {log_file} (테스트 파일 생성)", "WARN")
            # 디렉토리 생성
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'w') as f:
                f.write("[2026-01-28 14:00:00] [Biz] Order.create - ERR001 DB Connection Fail\n")
                f.write("[2026-01-28 14:01:00] [Biz] Order.create - ERR002 Timeout\n")

        # 2. 로그 파싱 및 집계
        self.log_signal.emit("로그 파일을 분석하고 있습니다...", "SCAN")
        aggregator = LogAggregator()
        parser = LogParser()
        line_count = 0
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not self.is_running: break
                    
                    parsed = parser.parse_line(line)
                    if parsed and parser.is_error(parsed):
                        aggregator.process_log(parsed)
                    line_count += 1
            
            self.log_signal.emit(f"총 {line_count} 라인 처리 완료", "INFO")

        except Exception as e:
            self.log_signal.emit(f"파일 읽기 오류: {str(e)}", "ERROR")
            self.finished_signal.emit(channel_key, -1)
            return

        # 3. 집계 데이터 JSON 생성
        json_data = aggregator.export_to_dify_format()
        error_count = sum(g['total_count'] for g in aggregator.groups.values())
        
        if error_count == 0:
            self.log_signal.emit("발견된 에러가 없습니다. 리포트 생성을 건너뜁니다.", "SUCCESS")
            self.finished_signal.emit(channel_key, 0)
            return

        # 4. Dify 전송
        self.log_signal.emit(f"Dify AI로 분석 요청 중... (에러 {error_count}건)", "INFO")
        dify = DifyClient(self.dify_config)
        
        # JSON 데이터를 String으로 파싱하여 전송 (analyze_issues 내부에서 처리됨)
        ai_response = dify.analyze_issues(json_data)
        
        if not ai_response:
            self.log_signal.emit("Dify 분석 실패 (응답 없음)", "ERROR")
            ai_text = "AI 분석에 실패했습니다. 원본 로그를 확인해주세요."
        else:
            # Dify 응답이 String인지 JSON인지 확인
            if isinstance(ai_response, str):
                ai_text = ai_response
            else:
                ai_text = json.dumps(ai_response, ensure_ascii=False, indent=2)
            self.log_signal.emit("AI 분석 완료", "SUCCESS")

        # 5. PDF 생성
        self.log_signal.emit("PDF 리포트 생성 중...", "INFO")
        
        # 폰트 경로 지정 (실제 경로에 맞춰주세요)
        font_path = os.path.join("app", "assets", "fonts", "NanumGothic.ttf")
        pdf_gen = PDFGenerator(font_path=font_path)
        
        try:
            # aggregator_data는 3번 단계에서 생성한 json_data입니다.
            report_path = pdf_gen.create_report(channel_name, ai_text, json_data)
            self.log_signal.emit(f"리포트 저장됨: {os.path.basename(report_path)}", "INFO")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log_signal.emit(f"PDF 생성 실패: {str(e)}", "ERROR")
            report_path = ""

        # 6. 히스토리 저장
        history = HistoryManager()
        history.add_record(
            channel_name=channel_name,
            start_time=self.date_range['start'],
            end_time=self.date_range['end'],
            file_path=report_path,
            error_count=error_count,
            status="성공" if report_path else "실패"
        )

        self.finished_signal.emit(channel_key, error_count)

    def stop(self):
        self.is_running = False