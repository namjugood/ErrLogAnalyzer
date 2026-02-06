import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage

from app.services.chart_generator import ChartGenerator

class PDFGenerator:
    def __init__(self, output_dir="data/reports", font_path="app/assets/fonts/NanumGothic.ttf"):
        self.output_dir = output_dir
        self.font_name = "NanumGothic"
        self.font_path = font_path
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._register_font()
        self.chart_gen = ChartGenerator(output_dir=os.path.join(output_dir, "charts"))

    def _register_font(self):
        """한글 폰트 등록 (필수)"""
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

        doc = SimpleDocTemplate(
            file_path, 
            pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm
        )

        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=self.font_name,
            fontSize=24,
            leading=30,
            alignment=1, 
            spaceAfter=20
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            leading=16,
            spaceAfter=10
        )
        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName=self.font_name,
            fontSize=16,
            leading=20,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#2563EB")
        )

        # 1. 헤더
        elements.append(Paragraph(f"에러 로그 분석 보고서 ({channel_name})", title_style))
        elements.append(Paragraph(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
        elements.append(Spacer(1, 10))
        
        meta = aggregator_data.get('report_meta', {})
        total_logs = meta.get('total_logs_processed', 0)
        report_date = meta.get('date', '-')
        
        meta_text = f"""
        <b>분석 일자:</b> {report_date}<br/>
        <b>총 처리 로그 수:</b> {total_logs}건<br/>
        <b>대상 시스템:</b> {channel_name}
        """
        elements.append(Paragraph(meta_text, body_style))
        elements.append(Spacer(1, 20))

        # 2. 에러 통계 (테이블) - [수정] 구분 컬럼 추가
        elements.append(Paragraph("1. 주요 에러 통계 (Top Issues)", h1_style))
        
        # 헤더: 구분, 채널(chnl), 순위, 서비스, 에러 코드, 발생 횟수, 최초 발생 시각
        table_data = [["구분", "채널", "순위", "서비스", "에러 코드", "발생 횟수", "최초 발생 시각"]]
        issues = aggregator_data.get('issue_groups', [])

        for idx, issue in enumerate(issues[:10], 1):
            svc_op = f"{issue.get('target_service', '-')}.{issue.get('target_operation', '-')}"
            row = [
                issue.get('error_id', '-'),
                get_chnl_label(issue.get('channel', '') or ''),
                str(idx),
                svc_op[:28],
                issue.get('error_code', '-'),
                f"{issue.get('total_count', 0)}건",
                issue.get('time_context', {}).get('first_seen', '-')
            ]
            table_data.append(row)

        # 컬럼 너비: 구분 12, 채널 12, 순위 8, 서비스 50, 코드 22, 횟수 22, 시간 42 (총 168mm)
        t = Table(table_data, colWidths=[12*mm, 12*mm, 8*mm, 50*mm, 22*mm, 22*mm, 42*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        # 3. 에러 발생 추이 차트 삽입
        time_series = aggregator_data.get('time_series_data', {})
        if time_series:
            elements.append(Paragraph("2. 시간대별 발생 추이 (Trend Analysis)", h1_style))
            
            # 차트 생성 (time_series의 키가 이미 Error01 등으로 변환되어 있으므로 그대로 사용)
            chart_path = self.chart_gen.generate_time_series_chart(time_series)
            
            if chart_path and os.path.exists(chart_path):
                im = ReportLabImage(chart_path, width=160*mm, height=80*mm)
                elements.append(im)
                elements.append(Spacer(1, 20))

        # 4. AI 분석 결과
        elements.append(Paragraph("3. AI 상세 분석 결과", h1_style))
        
        formatted_analysis = self._format_analysis_text(analysis_text)
        for para in formatted_analysis:
            if para.startswith("###") or para.startswith("##"):
                clean_text = para.replace("#", "").strip()
                sub_header_style = ParagraphStyle(
                    'SubHeader',
                    parent=body_style,
                    fontSize=12,
                    fontName=self.font_name,
                    textColor=colors.HexColor("#374151"),
                    spaceBefore=10,
                    spaceAfter=5,
                    leading=14
                )
                elements.append(Paragraph(f"<b>{clean_text}</b>", sub_header_style))
            elif para.strip() == "":
                elements.append(Spacer(1, 5))
            else:
                import re
                processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
                elements.append(Paragraph(processed_text, body_style))

        doc.build(elements)
        return file_path

    def _format_analysis_text(self, text):
        if not text:
            return ["분석 결과가 없습니다."]
        return text.split('\n')