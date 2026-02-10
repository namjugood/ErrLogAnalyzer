# app/workers/monitor_worker.py

import os
import json
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal
from app.core.aggregator import LogAggregator
from app.services.dify_client import DifyClient
from app.services.pdf_generator import PDFGenerator
from app.core.history_manager import HistoryManager
from app.api.bxm_client import BxmApiClient


def _is_input_data(item):
    """
    항목이 Dify 투입 데이터(issue_groups)인지 확인.
    투입 데이터 특징: error_id, channel, target_service, message_pattern 등이 있고,
    summary, details, analysis 같은 필드가 없음.
    """
    if not isinstance(item, dict):
        return False
    # 투입 데이터 특징: error_id, channel, target_service 등이 있음
    has_input_fields = any(key in item for key in ['error_id', 'target_service', 'target_operation', 'message_pattern', 'total_count'])
    # 결과 데이터 특징: summary, details, analysis 등이 있음
    has_result_fields = any(key in item for key in ['summary', 'details', 'analysis'])
    # 투입 데이터 필드는 있지만 결과 데이터 필드는 없으면 투입 데이터로 판단
    return has_input_fields and not has_result_fields


def _merge_ai_chunks(chunks, logger_callback=None):
    """
    Dify 스트리밍 청크들을 병합하여 구조화된 데이터 리스트로 반환.
    - 문자열 청크(delta)는 모두 이어붙인 뒤 JSON 파싱 시도.
    - 딕셔너리/리스트 청크는 수집하되, 이중 리스트는 평탄화.
    - 투입 데이터(issue_groups)는 필터링하여 제외.
    - 결과적으로 List[dict] 또는 dict 또는 str(파싱 실패 시) 반환.
    """
    def _log(msg, level="INFO"):
        if logger_callback:
            logger_callback(msg, level)
    
    if not chunks:
        _log("[병합] 수집된 청크가 없습니다.", "WARN")
        return None

    text_buffer = []
    structured_data = []
    input_data_count = 0
    result_data_count = 0

    for idx, c in enumerate(chunks):
        if c is None:
            continue
        
        if isinstance(c, str):
            text_buffer.append(c)
        elif isinstance(c, dict):
            # 투입 데이터 필터링
            if _is_input_data(c):
                input_data_count += 1
                _log(f"[병합] 청크 {idx+1}: 투입 데이터 감지 및 제외 (error_id: {c.get('error_id', 'N/A')})", "INFO")
                continue
            structured_data.append(c)
            result_data_count += 1
        elif isinstance(c, list):
            # 이중 리스트 평탄화 및 투입 데이터 필터링
            flattened = []
            for item in c:
                if isinstance(item, list):
                    # 삼중 리스트도 평탄화
                    flattened.extend(item)
                else:
                    flattened.append(item)
            
            # 평탄화된 리스트에서 투입 데이터 필터링
            for item in flattened:
                if isinstance(item, dict) and _is_input_data(item):
                    input_data_count += 1
                    _log(f"[병합] 청크 {idx+1}: 평탄화된 리스트에서 투입 데이터 감지 및 제외 (error_id: {item.get('error_id', 'N/A')})", "INFO")
                    continue
                elif isinstance(item, dict):
                    structured_data.append(item)
                    result_data_count += 1
                elif item is not None:
                    structured_data.append(item)
                    result_data_count += 1

    # 1. 텍스트 버퍼 처리 (이어붙여서 파싱 시도)
    if text_buffer:
        full_text = "".join(text_buffer).strip()
        # <think> 태그 제거
        full_text = re.sub(r'<think>[\s\S]*?</think>', '', full_text, flags=re.IGNORECASE).strip()
        if full_text:
            _log(f"[병합] 텍스트 버퍼 처리 중... (길이: {len(full_text)}자)", "INFO")
            _log(f"병합 텍스트 데이터 : {full_text[:800]}...", "INFO")
            try:
                parsed = json.loads(full_text)
                if isinstance(parsed, list):
                    _log(f"[병합] 텍스트에서 리스트 파싱 성공 (항목 수: {len(parsed)})", "INFO")
                    # 리스트 내부 항목도 필터링
                    filtered = [item for item in parsed if not (isinstance(item, dict) and _is_input_data(item))]
                    filtered_count = len(parsed) - len(filtered)
                    if filtered_count > 0:
                        _log(f"[병합] 텍스트 파싱 결과에서 투입 데이터 {filtered_count}개 제외", "INFO")
                    structured_data.extend(filtered)
                    result_data_count += len(filtered)
                elif isinstance(parsed, dict):
                    if _is_input_data(parsed):
                        _log("[병합] 텍스트에서 파싱된 딕셔너리가 투입 데이터로 판단되어 제외", "INFO")
                        input_data_count += 1
                    else:
                        _log("[병합] 텍스트에서 딕셔너리 파싱 성공", "INFO")
                        structured_data.append(parsed)
                        result_data_count += 1
            except json.JSONDecodeError:
                _log("[병합] 텍스트 버퍼 JSON 파싱 실패 (연속된 JSON 또는 불완전한 JSON일 수 있음)", "WARN")
                if not structured_data:
                    _log("[병합] 구조화된 데이터가 없어 텍스트를 그대로 반환", "INFO")
                    return full_text

    # 병합 결과 요약 로그
    _log(f"[병합] 완료 - 결과 데이터: {result_data_count}개, 제외된 투입 데이터: {input_data_count}개", "INFO")
    
    if not structured_data:
        _log("[병합] 최종 구조화된 데이터가 없습니다.", "WARN")
        return None

    _log(f"[병합] 최종 병합된 데이터 타입: {type(structured_data).__name__}, 항목 수: {len(structured_data) if isinstance(structured_data, list) else 1}", "INFO")
    return structured_data


class MonitorWorker(QThread):
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(str, int) 

    def __init__(self, channel_data, dify_config, date_range):
        super().__init__()
        self.channel_data = channel_data
        self.dify_config = dify_config
        self.date_range = date_range
        self.is_running = True
        self.last_update_time = 0

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

        # 4. 데이터 집계 및 Dify 포맷 변환 (투입 데이터)
        input_data = aggregator.export_to_dify_format()
        error_count = sum(g['total_count'] for g in aggregator.groups.values())
        issue_count = len(input_data.get("issue_groups", []))
        
        self.log_signal.emit(f"[투입 데이터] 준비 완료 - 에러 그룹: {issue_count}개, 총 에러 수: {error_count}건", "INFO")
        self.log_signal.emit(f"[투입 데이터] 채널별 분포: {', '.join(set(ig.get('channel', 'Unknown') for ig in input_data.get('issue_groups', [])))}", "INFO")

        # 5. Dify Streaming 통신
        self.log_signal.emit(f"Dify AI 분석 요청 중... ({error_count}건)", "INFO")
        dify = DifyClient(self.dify_config, logger=logger_callback)
        
        # Dify 결과 데이터 수집용 별도 변수
        dify_result_chunks = [] 
        step_count = 0
        
        try:
            for status, data in dify.analyze_issues_streaming(input_data):
                if not self.is_running:
                    break

                if status == 'process':
                    step_count += 1
                    current_time = time.time()
                    if current_time - self.last_update_time > 0.1:
                        clean_msg = data.replace('AI 처리 중: ', '') if isinstance(data, str) else str(data)
                        self.log_signal.emit(f"AI 분석 진행 중... [Step {step_count}] {clean_msg}", "PROGRESS")
                        self.last_update_time = current_time
                    
                elif status == 'result_chunk':
                    dify_result_chunks.append(data)
                    chunk_type = type(data).__name__
                    self.log_signal.emit(f"[결과 데이터] 청크 수신 ({len(dify_result_chunks)}건) - 타입: {chunk_type}", "PROGRESS")
                    
                elif status == 'error':
                    self.log_signal.emit(f"분석 중 오류 발생: {data}", "ERROR")

            # Dify 결과 데이터 수집 완료 로그
            self.log_signal.emit(f"[결과 데이터] 수집 완료 - 총 청크 수: {len(dify_result_chunks)}개", "INFO")
            
            # 수집된 청크 타입 분석
            chunk_types = {}
            for chunk in dify_result_chunks:
                chunk_type = type(chunk).__name__
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            type_summary = ", ".join([f"{k}: {v}개" for k, v in chunk_types.items()])
            self.log_signal.emit(f"[결과 데이터] 청크 타입 분포: {type_summary}", "INFO")

            # 결과 데이터 병합 (투입 데이터 필터링 포함)
            self.log_signal.emit("[결과 데이터] 병합 시작...", "INFO")
            merged_result_data = _merge_ai_chunks(dify_result_chunks, logger_callback)
            
            if merged_result_data is None:
                analysis_data = "AI 분석 응답이 비어있거나 실패했습니다."
                if self.is_running:
                    self.log_signal.emit("[결과 데이터] 병합 실패 - 응답이 비어있거나 모든 데이터가 투입 데이터로 필터링됨", "WARN")
            else:
                analysis_data = merged_result_data
                result_type = type(merged_result_data).__name__
                if isinstance(merged_result_data, list):
                    result_summary = f"리스트 (항목 수: {len(merged_result_data)})"
                    # 첫 번째 항목 구조 확인
                    if merged_result_data and isinstance(merged_result_data[0], dict):
                        has_summary = "summary" in merged_result_data[0]
                        has_details = "details" in merged_result_data[0]
                        result_summary += f" - 구조: summary={has_summary}, details={has_details}"
                else:
                    result_summary = result_type
                self.log_signal.emit(f"[결과 데이터] 병합 성공 - 타입: {result_summary}", "SUCCESS")

        except Exception as e:
            analysis_data = f"AI 분석 중 치명적 오류: {str(e)}"
            self.log_signal.emit(f"Dify 통신 오류: {str(e)}", "ERROR")

        # 6. PDF 리포트 제작
        if self.is_running:
            self.log_signal.emit("PDF 리포트 생성 중...", "INFO")
            font_path = os.path.join("app", "assets", "fonts", "NanumGothic.ttf")
            
            pdf_gen = PDFGenerator(font_path=font_path, logger=logger_callback)
            
            report_path = ""
            try:
                # PDF 생성 시 투입 데이터(input_data)와 결과 데이터(analysis_data)를 명확히 분리하여 전달
                self.log_signal.emit(f"[PDF 생성] 투입 데이터: {len(input_data.get('issue_groups', []))}개 그룹, 결과 데이터 타입: {type(analysis_data).__name__}", "INFO")
                report_path = pdf_gen.create_report(channel_name, analysis_data, input_data)
                self.log_signal.emit(f"리포트 생성 완료: {os.path.basename(report_path)}", "INFO")
            except Exception as e:
                self.log_signal.emit(f"PDF 생성 실패: {str(e)}", "ERROR")
                # import traceback
                # traceback.print_exc() 

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

            self.finished_signal.emit(channel_key, error_count)

    def stop(self):
        self.is_running = False