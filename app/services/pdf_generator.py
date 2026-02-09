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
from app.core.chnl_constants import get_chnl_label

def resource_path(relative_path):
    """PyInstaller 빌드 환경과 개발 환경 모두에서 리소스 경로를 찾습니다."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class PDFGenerator:
    def __init__(self, output_dir="data/reports", font_path="app/assets/fonts/NanumGothic.ttf"):
        self.output_dir = output_dir
        self.font_name = "NanumGothic"
        
        # 폰트 경로 설정
        self.font_path = resource_path(font_path)
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._register_font()
        self.chart_gen = ChartGenerator(output_dir=os.path.join(output_dir, "charts"))

    def _register_font(self):
        """한글 폰트 등록"""
        try:
            if os.path.exists(self.font_path):
                pdfmetrics.registerFont(TTFont(self.font_name, self.font_path))
            else:
                self.font_name = "Helvetica" 
                print(f"[Warning] 폰트 파일을 찾을 수 없습니다: {self.font_path}. 한글이 깨질 수 있습니다.")
        except Exception as e:
            print(f"[Error] 폰트 등록 실패: {e}")
            self.font_name = "Helvetica"

    def create_report(self, channel_name, analysis_text, aggregator_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{channel_name}_Report_{timestamp}.pdf"
        file_path = os.path.join(self.output_dir, filename)

        # 여백 조정 (10mm)
        doc = SimpleDocTemplate(
            file_path, 
            pagesize=A4,
            rightMargin=10*mm, leftMargin=10*mm,
            topMargin=15*mm, bottomMargin=15*mm
        )

        elements = []
        styles = getSampleStyleSheet()
        
        # --- 스타일 정의 ---
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Title'], fontName=self.font_name, 
            fontSize=24, leading=30, alignment=1, spaceAfter=20
        )
        body_style = ParagraphStyle(
            'CustomBody', parent=styles['Normal'], fontName=self.font_name, 
            fontSize=10, leading=16, spaceAfter=5
        )
        h1_style = ParagraphStyle(
            'CustomH1', parent=styles['Heading1'], fontName=self.font_name, 
            fontSize=16, leading=20, spaceBefore=20, spaceAfter=10, textColor=colors.HexColor("#2563EB")
        )
        h2_style = ParagraphStyle(
            'CustomH2', parent=styles['Heading2'], fontName=self.font_name, 
            fontSize=12, leading=15, spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#374151")
        )
        label_style = ParagraphStyle(
            'LabelStyle', parent=body_style, fontName=self.font_name, fontSize=10, textColor=colors.HexColor("#1F2937")
        )

        # --- 데이터 준비: 채널별 통계 ---
        issues = aggregator_data.get('issue_groups', [])
        channel_stats = defaultdict(int)
        total_errors = 0
        for issue in issues:
            cnt = issue.get('total_count', 0)
            raw_chnl = issue.get('channel', '') or ''
            chnl_label = get_chnl_label(raw_chnl)
            channel_stats[chnl_label] += cnt
            total_errors += cnt

        # 1. 문서 헤더
        elements.append(Paragraph(f"에러 로그 분석 보고서 ({channel_name})", title_style))
        elements.append(Paragraph(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
        elements.append(Spacer(1, 10))
        
        meta = aggregator_data.get('report_meta', {})
        total_logs = meta.get('total_logs_processed', 0)
        report_date = meta.get('date', '-')
        
        meta_text = f"""
        <b>분석 일자:</b> {report_date}<br/>
        <b>총 처리 로그 수:</b> {total_logs}건<br/>
        <b>총 에러 발생 수:</b> {total_errors}건<br/>
        <b>대상 시스템:</b> {channel_name}
        """
        elements.append(Paragraph(meta_text, body_style))
        elements.append(Spacer(1, 20))

        # 2. 주요 에러 통계 (Top Issues)
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

        # 3. 채널별 에러 점유율 (Channel Stats)
        if channel_stats:
            elements.append(Paragraph("2. 채널별 에러 점유율 (Channel Stats)", h1_style))
            
            pie_chart_path = self.chart_gen.generate_pie_chart(channel_stats)
            if pie_chart_path and os.path.exists(pie_chart_path):
                im = ReportLabImage(pie_chart_path, width=100*mm, height=70*mm)
                elements.append(im)
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

        # 4. 시간대별 발생 추이
        time_series = aggregator_data.get('time_series_data', {})
        if time_series:
            elements.append(Paragraph("3. 시간대별 발생 추이 (Trend Analysis)", h1_style))
            chart_path = self.chart_gen.generate_time_series_chart(time_series)
            if chart_path and os.path.exists(chart_path):
                im = ReportLabImage(chart_path, width=190*mm, height=95*mm)
                elements.append(im)
                elements.append(Spacer(1, 20))

        # =========================================================================
        # 5. AI 상세 분석 결과 (수정된 로직 적용)
        # =========================================================================
        elements.append(Paragraph("4. AI 상세 분석 결과", h1_style))
        
        # [핵심 수정] 리스트 언래핑 및 재파싱 로직 사용
        ai_data = self._parse_ai_response(analysis_text)
        
        if isinstance(ai_data, dict):
            # 1) Summary 섹션
            summary = ai_data.get("summary", {})
            if summary:
                elements.append(Paragraph("■ 종합 분석 요약", h2_style))
                
                status = summary.get("status", "INFO")
                status_color = "#10B981" # Green
                if status in ["RED", "CRITICAL"]: status_color = "#EF4444"
                elif status in ["YELLOW", "WARNING"]: status_color = "#F59E0B"
                
                summary_text = f"""
                <b>진단 상태:</b> <font color='{status_color}'><b>{status}</b></font><br/>
                <b>주요 이슈:</b> Critical({summary.get('critical_count',0)}), Major({summary.get('major_count',0)})<br/>
                <b>브리핑:</b> {summary.get('briefing', '-')}
                """
                
                t_summary = Table([[Paragraph(summary_text, body_style)]], colWidths=[190*mm])
                t_summary.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(status_color)),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ]))
                elements.append(t_summary)
                elements.append(Spacer(1, 15))

            # 2) Details 섹션
            details = ai_data.get("details", [])
            if details:
                elements.append(Paragraph("■ 상세 에러 분석", h2_style))
                
                for idx, item in enumerate(details, 1):
                    code = item.get("error_code", "Unknown")
                    severity = item.get("severity", "INFO")
                    signature = item.get("signature", "-")
                    
                    elements.append(Paragraph(f"{idx}. {code} ({severity})", h2_style))
                    elements.append(Paragraph(f"Signature: {signature}", body_style))
                    
                    analysis = item.get("analysis", {})
                    
                    detail_content = [
                        [Paragraph("<b>예상 영향 (Impact)</b>", label_style), Paragraph(analysis.get("impact", "-"), body_style)],
                        [Paragraph("<b>원인 분석 (Root Cause)</b>", label_style), Paragraph(analysis.get("root_cause", "-"), body_style)],
                        [Paragraph("<b>조치 방안 (Action Item)</b>", label_style), Paragraph(analysis.get("action_item", "-"), body_style)]
                    ]
                    
                    t_detail = Table(detail_content, colWidths=[40*mm, 150*mm])
                    t_detail.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    elements.append(t_detail)
                    elements.append(Spacer(1, 10))

        else:
            # 파싱 실패 시 원문 출력
            formatted_text = self._format_analysis_text_fallback(analysis_text)
            for para in formatted_text:
                if para.strip():
                    elements.append(Paragraph(para, body_style))

        doc.build(elements)
        return file_path

    def _parse_ai_response(self, text):
        """
        AI 응답 처리:
        1. 1차 파싱: ["..."] 형태의 리스트 언래핑
        2. 마크다운 제거: ```json ... ``` 패턴 제거
        3. 2차 파싱: 최종 딕셔너리 변환
        """
        if not text:
            return {}
        
        # 1차 파싱: 리스트나 JSON 문자열 파싱 시도
        try:
            parsed = json.loads(text)
            
            # 리스트인 경우 (예: ["```json..."]) -> 첫 번째 요소 추출
            if isinstance(parsed, list) and len(parsed) > 0:
                text = parsed[0]
            # 딕셔너리인 경우 (이미 완료)
            elif isinstance(parsed, dict):
                return parsed
        except Exception:
            # JSON 포맷이 아니거나 파싱 에러인 경우, 원본 텍스트로 계속 진행
            pass

        # 여기까지 오면 text는 "문자열" 상태임 (마크다운 포함 가능성 높음)
        
        # 2. 마크다운 코드블럭 패턴 제거
        try:
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                clean_text = match.group(1)
            else:
                # 패턴이 없으면 앞뒤 특수문자만 제거 후 시도
                clean_text = text.strip().strip("`")
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:].strip()
            
            # 3. 2차 파싱
            return json.loads(clean_text)
            
        except (json.JSONDecodeError, AttributeError):
            # 최종 실패 시 원문 텍스트 반환 (호출부에서 isinstance로 체크하여 Fallback)
            return text

    def _format_analysis_text_fallback(self, text):
        if not text:
            return ["분석 결과가 없습니다."]
        return text.split('\n')