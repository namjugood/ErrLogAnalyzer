# app/services/pdf_generator.py

import os
import sys
import json
import re
from datetime import datetime
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage

from app.services.chart_generator import ChartGenerator
from app.core.chnl_constants import get_chnl_label, CHNL_LABELS

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class PDFGenerator:
    def __init__(self, output_dir="data/reports", font_path="app/assets/fonts/NanumGothic.ttf", logger=None):
        self.output_dir = output_dir
        self.font_name = "NanumGothic"
        self.logger = logger
        self.font_path = resource_path(font_path)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self._register_font()
        self.chart_gen = ChartGenerator(output_dir=os.path.join(output_dir, "charts"))

    def _log(self, message: str, level: str = "INFO"):
        if self.logger:
            self.logger(message, level)

    def _register_font(self):
        try:
            if os.path.exists(self.font_path):
                pdfmetrics.registerFont(TTFont(self.font_name, self.font_path))
            else:
                self.font_name = "Helvetica" 
                print(f"[Warning] 폰트 파일을 찾을 수 없습니다: {self.font_path}")
        except Exception as e:
            print(f"[Error] 폰트 등록 실패: {e}")
            self.font_name = "Helvetica"

    def create_report(self, channel_name, analysis_data, aggregator_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{channel_name}_Report_{timestamp}.pdf"
        file_path = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            file_path, 
            pagesize=A4,
            rightMargin=10*mm, leftMargin=10*mm,
            topMargin=15*mm, bottomMargin=15*mm
        )

        elements = []
        styles = getSampleStyleSheet()
        
        # 스타일 정의
        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontName=self.font_name, fontSize=24, leading=30, alignment=1, spaceAfter=20)
        body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontName=self.font_name, fontSize=10, leading=16, spaceAfter=5)
        h1_style = ParagraphStyle('CustomH1', parent=styles['Heading1'], fontName=self.font_name, fontSize=16, leading=20, spaceBefore=20, spaceAfter=10, textColor=colors.HexColor("#2563EB"))
        h2_style = ParagraphStyle('CustomH2', parent=styles['Heading2'], fontName=self.font_name, fontSize=12, leading=15, spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#374151"))
        label_style = ParagraphStyle('LabelStyle', parent=body_style, fontName=self.font_name, fontSize=10, textColor=colors.HexColor("#1F2937"))

        # 데이터 준비
        issues = aggregator_data.get('issue_groups', [])
        channel_stats = defaultdict(int)
        total_errors = 0
        for issue in issues:
            cnt = issue.get('total_count', 0)
            raw_chnl = issue.get('channel', '') or ''
            channel_stats[get_chnl_label(raw_chnl)] += cnt
            total_errors += cnt

        # 1. 문서 헤더
        elements.append(Paragraph(f"에러 로그 분석 보고서 ({channel_name})", title_style))
        elements.append(Paragraph(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
        elements.append(Spacer(1, 10))
        
        meta = aggregator_data.get('report_meta', {})
        meta_text = f"""
        <b>분석 일자:</b> {meta.get('date', '-')}<br/>
        <b>총 처리 로그 수:</b> {meta.get('total_logs_processed', 0)}건<br/>
        <b>총 에러 발생 수:</b> {total_errors}건<br/>
        <b>대상 시스템:</b> {channel_name}
        """
        elements.append(Paragraph(meta_text, body_style))
        elements.append(Spacer(1, 20))

        # 2. 주요 에러 통계
        elements.append(Paragraph("1. 주요 에러 통계 (Top Issues)", h1_style))
        table_data = [["구분", "채널", "순위", "서비스", "에러 코드", "발생 횟수", "최초 발생"]]
        for idx, issue in enumerate(issues[:10], 1):
            svc_op = f"{issue.get('target_service', '-')}.{issue.get('target_operation', '-')}"
            row = [
                issue.get('error_id', '-'),
                get_chnl_label(issue.get('channel', '') or ''),
                str(idx),
                svc_op[:35], 
                issue.get('error_code', '-'),
                f"{issue.get('total_count', 0)}건",
                issue.get('time_context', {}).get('first_seen', '-')
            ]
            table_data.append(row)

        t = Table(table_data, colWidths=[15*mm, 15*mm, 10*mm, 60*mm, 30*mm, 20*mm, 40*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        # 3. 채널별 점유율 및 추이
        if channel_stats:
            elements.append(Paragraph("2. 채널별 에러 점유율 (Channel Stats)", h1_style))
            pie_chart_path = self.chart_gen.generate_pie_chart(channel_stats)
            if pie_chart_path and os.path.exists(pie_chart_path):
                elements.append(ReportLabImage(pie_chart_path, width=100*mm, height=70*mm))
                elements.append(Spacer(1, 10))

            stat_table_data = [["채널명", "에러 수", "점유율(%)"]]
            sorted_stats = sorted(channel_stats.items(), key=lambda x: x[1], reverse=True)
            for ch_name, count in sorted_stats:
                percent = (count / total_errors) * 100 if total_errors > 0 else 0
                stat_table_data.append([ch_name, f"{count}건", f"{percent:.1f}%"])
            
            t2 = Table(stat_table_data, colWidths=[60*mm, 30*mm, 30*mm], hAlign='LEFT')
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(t2)
            elements.append(Spacer(1, 20))

        time_series = aggregator_data.get('time_series_data', {})
        if time_series:
            elements.append(Paragraph("3. 시간대별 발생 추이 (Trend Analysis)", h1_style))
            chart_path = self.chart_gen.generate_time_series_chart(time_series)
            if chart_path and os.path.exists(chart_path):
                elements.append(ReportLabImage(chart_path, width=190*mm, height=95*mm))
                elements.append(Spacer(1, 20))

        # 4. AI 상세 분석 결과 (핵심 수정 부분)
        elements.append(Paragraph("4. AI 상세 분석 결과", h1_style))
        
        # ==========================================================
        # [DEBUG 추가 2] AI 상세 분석 결과 작성 전의 데이터 출력
        # ==========================================================
        self._log(f"[DEBUG] PDF 생성 진입 데이터 (analysis_data):\n{analysis_data}", "INFO")

        # 데이터를 정규화하여 단일 구조({summary:..., details:[...]})로 통합
        ai_data = self._normalize_analysis_data(analysis_data)
        
        # [DEBUG 추가 3] 정규화(Normalize) 후 데이터 구조 확인
        self._log(f"[DEBUG] 정규화된 데이터 (ai_data):\n{ai_data}", "INFO")

        # 데이터를 정규화하여 단일 구조({summary:..., details:[...]})로 통합
        ai_data = self._normalize_analysis_data(analysis_data)
        
        if ai_data:
            summary = ai_data.get("summary", {})
            details = ai_data.get("details", [])
            
            # Summary 표시
            if summary:
                self._append_summary_table(elements, summary, label_style, body_style, colors)
                elements.append(Spacer(1, 15))
            
            # Details 표시 (채널별 그룹화)
            if details:
                # details가 dict 리스트가 맞는지 확인
                valid_details = [d for d in details if isinstance(d, dict)]
                
                details_by_channel = defaultdict(list)
                for item in valid_details:
                    sig = item.get("signature", "")
                    # signature 형식: "Channel|..." 또는 "..."
                    chnl_code = "Unknown"
                    if sig and "|" in sig:
                        chnl_code = sig.split("|")[0].strip()
                    details_by_channel[chnl_code].append(item)

                # 순서 정렬 (CHNL_LABELS 순서 우선)
                ordered_keys = [k for k in CHNL_LABELS.keys() if k in details_by_channel]
                other_keys = [k for k in details_by_channel.keys() if k not in CHNL_LABELS]
                
                # 채널별 출력
                for ch_idx, chnl_code in enumerate(ordered_keys + other_keys, 1):
                    chnl_name = get_chnl_label(chnl_code)
                    items = details_by_channel[chnl_code]
                    
                    elements.append(Paragraph(f"{ch_idx}) {chnl_name}", h2_style))
                    elements.append(Spacer(1, 5))
                    
                    for d_idx, item in enumerate(items, 1):
                        self._append_detail_table(elements, item, ch_idx, d_idx, label_style, body_style, h2_style)
                        elements.append(Spacer(1, 10))
            else:
                elements.append(Paragraph("상세 분석 데이터가 없습니다.", body_style))
        else:
            # 파싱 실패 시 원본 텍스트 출력 (Fallback)
            fallback_text = str(analysis_data) if analysis_data else "분석 결과가 없습니다."
            for line in fallback_text.split('\n'):
                if line.strip():
                    elements.append(Paragraph(line, body_style))

        doc.build(elements)
        return file_path

    def _normalize_analysis_data(self, analysis_data):
        """
        입력 데이터(Dict, List[Dict], String)를 표준 포맷 {summary: {}, details: []}으로 변환.
        다중 JSON 객체가 포함된 경우 모두 병합합니다.
        """
        parsed_list = []

        # 1. 입력 타입에 따른 초기 리스트 변환
        if isinstance(analysis_data, dict):
            parsed_list = [analysis_data]
        elif isinstance(analysis_data, list):
            parsed_list = analysis_data
        elif isinstance(analysis_data, str):
            # 문자열인 경우 파싱 시도 (단일 또는 다중 JSON)
            parsed_list = self._parse_ai_response_string(analysis_data)
        
        if not parsed_list:
            return None

        # 2. 병합 (Merge) 로직
        merged_summary = {
            "status": "INFO", 
            "total_logs": 0, "critical_count": 0, "major_count": 0, "minor_count": 0, 
            "briefing": ""
        }
        merged_details = []
        briefings = []
        
        # 상태 우선순위
        status_priority = {"CRITICAL": 5, "RED": 4, "MAJOR": 3, "YELLOW": 2, "WARNING": 2, "INFO": 1}
        max_prio = 0

        for report in parsed_list:
            if not isinstance(report, dict):
                continue
            
            # Summary 병합
            summ = report.get("summary", {})
            if summ:
                merged_summary["total_logs"] += int(summ.get("total_logs", 0))
                merged_summary["critical_count"] += int(summ.get("critical_count", 0))
                merged_summary["major_count"] += int(summ.get("major_count", 0))
                merged_summary["minor_count"] += int(summ.get("minor_count", 0))
                
                br = summ.get("briefing")
                if br: briefings.append(br)
                
                st = str(summ.get("status", "INFO")).upper()
                p = status_priority.get(st, 0)
                if p > max_prio:
                    max_prio = p
                    merged_summary["status"] = st

            # Details 병합
            dets = report.get("details", [])
            if isinstance(dets, list):
                merged_details.extend(dets)
            elif isinstance(dets, dict): # 혹시 details가 dict라면
                merged_details.append(dets)

        if briefings:
            merged_summary["briefing"] = "\n\n".join(briefings)

        # 내용이 전혀 없으면 None 반환 (Fallback 유도)
        if not merged_details and not briefings and merged_summary["total_logs"] == 0:
            return None

        return {"summary": merged_summary, "details": merged_details}

    def _parse_ai_response_string(self, text):
        """
        문자열에서 JSON 객체들을 추출. 
        단일 JSON 뿐만 아니라 '{...}{...}' 형태의 연속된 다중 JSON도 처리.
        """
        if not text:
            return []
        
        # 0. <think> 태그 제거
        text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE).strip()
        
        # 1. 마크다운 제거
        clean_text = text
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            clean_text = match.group(1)
        else:
            clean_text = text.strip().strip("`")
            if clean_text.startswith("json"):
                clean_text = clean_text[4:].strip()

        results = []
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(clean_text):
            # 공백 스킵
            while pos < len(clean_text) and clean_text[pos].isspace():
                pos += 1
            if pos >= len(clean_text):
                break
            
            try:
                # raw_decode는 (객체, 파싱된_문자수)를 반환
                obj, idx = decoder.raw_decode(clean_text[pos:])
                results.append(obj)
                pos += idx
            except json.JSONDecodeError:
                # 파싱 실패하면 루프 종료 (남은 부분은 무시)
                # 필요하다면 로깅 추가 가능
                break
        
        return results

    def _append_summary_table(self, elements, summary, label_style, body_style, colors):
        status = summary.get("status", "INFO")
        status_color = "#10B981" # Green
        if status in ["RED", "CRITICAL"]:
            status_color = "#EF4444"
        elif status in ["YELLOW", "WARNING", "MAJOR"]:
            status_color = "#F59E0B"
            
        sc = summary.get("critical_count", 0)
        sm = summary.get("major_count", 0)
        br = str(summary.get("briefing", "-")).replace("\n", "<br/>")

        rows = [
            [Paragraph("<b>진단 상태</b>", label_style), Paragraph(f"<font color='{status_color}'><b>{status}</b></font>", body_style)],
            [Paragraph("<b>주요 이슈</b>", label_style), Paragraph(f"Critical({sc}), Major({sm})", body_style)],
            [Paragraph("<b>브리핑</b>", label_style), Paragraph(br, body_style)],
        ]
        t = Table(rows, colWidths=[40*mm, 150*mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(status_color)),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)

    def _append_detail_table(self, elements, item, ch_idx, d_idx, label_style, body_style, h2_style):
        signature = item.get("signature", "-")
        # 제목 생성 (메시지 패턴이 없으면 시그니처 사용)
        msg_title = item.get("message_pattern")
        if not msg_title:
             # signature에서 메시지 유추 시도 (예: 마지막 부분)
             parts = signature.split("|")
             msg_title = parts[-1] if parts else signature
        
        severity = item.get("severity", "INFO")
        elements.append(Paragraph(f"{ch_idx}-{d_idx}) {msg_title} ({severity})", h2_style))
        
        # 분석 정보 추출
        analysis = item.get("analysis", {})
        if not isinstance(analysis, dict): analysis = {} # 방어 코드

        impact = analysis.get("impact") or item.get("impact") or "-"
        root_cause = analysis.get("root_cause") or item.get("root_cause") or "-"
        action = analysis.get("action_item") or analysis.get("recommendation") or item.get("action_item") or "-"
        
        parsed_sig = self._parse_signature(signature)
        error_code = item.get("error_code") or parsed_sig["error_code"]

        def _fmt(txt):
            return str(txt).replace("\n", "<br/>")

        rows = [
            [Paragraph("<b>Signature</b>", label_style), Paragraph(signature, body_style)],
            [Paragraph("<b>Service Info</b>", label_style), Paragraph(f"{parsed_sig['application']} / {parsed_sig['service']} / {parsed_sig['operation']}", body_style)],
            [Paragraph("<b>Error Code</b>", label_style), Paragraph(_fmt(error_code), body_style)],
            [Paragraph("<b>Impact</b>", label_style), Paragraph(_fmt(impact), body_style)],
            [Paragraph("<b>Root Cause</b>", label_style), Paragraph(_fmt(root_cause), body_style)],
            [Paragraph("<b>Action Item</b>", label_style), Paragraph(_fmt(action), body_style)],
        ]
        t = Table(rows, colWidths=[40*mm, 150*mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)

    def _parse_signature(self, signature: str):
        # 기본값
        res = {"channel": "-", "application": "-", "service": "-", "operation": "-", "error_code": "-"}
        if not signature: return res
        
        parts = [p.strip() for p in signature.split("|")]
        if len(parts) >= 3:
            # 예상: Channel | App | Service.Op | Code  혹은  App | Service.Op | Code
            # 여기서는 뒤에서부터 매핑하는 것이 안전
            res["error_code"] = parts[-1]
            if "." in parts[-2]:
                svc_parts = parts[-2].split(".", 1)
                res["service"] = svc_parts[0]
                res["operation"] = svc_parts[1]
            else:
                res["service"] = parts[-2]
            
            res["application"] = parts[-3]
            if len(parts) >= 4:
                res["channel"] = parts[-4]
        return res