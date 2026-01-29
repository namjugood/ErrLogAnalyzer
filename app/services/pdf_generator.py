# app/services/pdf_generator.py

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

class PDFGenerator:
    def __init__(self, output_dir="data/reports", font_path="app/assets/fonts/NanumGothic.ttf"):
        self.output_dir = output_dir
        self.font_name = "NanumGothic"
        self.font_path = font_path
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._register_font()

    def _register_font(self):
        """한글 폰트 등록 (필수)"""
        try:
            if os.path.exists(self.font_path):
                pdfmetrics.registerFont(TTFont(self.font_name, self.font_path))
            else:
                # 폰트 파일이 없을 경우 시스템 폰트 시도 (Windows/Linux 환경에 따라 다름)
                # 여기서는 기본 폰트로 설정하되 한글 깨짐 경고 출력
                self.font_name = "Helvetica" 
                print(f"[Warning] 폰트 파일을 찾을 수 없습니다: {self.font_path}. 한글이 깨질 수 있습니다.")
        except Exception as e:
            print(f"[Error] 폰트 등록 실패: {e}")
            self.font_name = "Helvetica"

    def create_report(self, channel_name, analysis_text, aggregator_data):
        """
        JSON 데이터와 Dify 분석 결과를 결합하여 PDF 생성
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{channel_name}_Report_{timestamp}.pdf"
        file_path = os.path.join(self.output_dir, filename)

        # 문서 템플릿 생성 (여백 설정)
        doc = SimpleDocTemplate(
            file_path, 
            pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm
        )

        elements = []
        
        # 스타일 정의
        styles = getSampleStyleSheet()
        
        # 제목 스타일
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=self.font_name,
            fontSize=24,
            leading=30,
            alignment=1, # Center
            spaceAfter=20
        )
        
        # 본문 스타일
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            leading=16, # 줄간격
            spaceAfter=10
        )

        # 섹션 헤더 스타일
        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName=self.font_name,
            fontSize=16,
            leading=20,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#2563EB") # Blue
        )

        # ---------------------------------------------------------
        # 1. 보고서 제목 및 메타정보
        # ---------------------------------------------------------
        elements.append(Paragraph(f"에러 로그 분석 보고서 ({channel_name})", title_style))
        elements.append(Paragraph(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
        elements.append(Spacer(1, 10))
        
        # 메타데이터 추출 (JSON 구조: new.txt 참고)
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

        # ---------------------------------------------------------
        # 2. 에러 통계 요약 (테이블)
        # ---------------------------------------------------------
        elements.append(Paragraph("1. 주요 에러 통계 (Top Issues)", h1_style))
        
        table_data = [["순위", "서비스", "에러 코드", "발생 횟수", "최초 발생 시각"]]
        
        # issue_groups 데이터 정렬 (건수 기준 내림차순)
        issues = aggregator_data.get('issue_groups', [])
        sorted_issues = sorted(issues, key=lambda x: x.get('total_count', 0), reverse=True)
        
        # 상위 10개만 테이블에 표시
        for idx, issue in enumerate(sorted_issues[:10], 1):
            svc_op = f"{issue.get('target_service', '-')}.{issue.get('target_operation', '-')}"
            row = [
                str(idx),
                svc_op[:30], # 너무 길면 자름
                issue.get('error_code', '-'),
                f"{issue.get('total_count', 0)}건",
                issue.get('time_context', {}).get('first_seen', '-')
            ]
            table_data.append(row)

        # 테이블 스타일링
        t = Table(table_data, colWidths=[15*mm, 60*mm, 30*mm, 25*mm, 40*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")), # 헤더 배경색
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10), # 헤더 폰트 크기
            ('FONTSIZE', (0, 1), (-1, -1), 9),  # 데이터 폰트 크기
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        # ---------------------------------------------------------
        # 3. AI 상세 분석 결과 (Dify Output)
        # ---------------------------------------------------------
        elements.append(Paragraph("2. AI 상세 분석 결과", h1_style))
        
        # Dify 결과물(Markdown 스타일 텍스트)을 PDF용으로 변환
        # (dify 결과물 예시.txt 형식을 고려하여 줄바꿈 및 스타일 적용)
        formatted_analysis = self._format_analysis_text(analysis_text)
        
        for para in formatted_analysis:
            # 제목(###)이나 강조(**) 등을 간단히 처리하여 스타일 적용
            if para.startswith("###") or para.startswith("##"):
                clean_text = para.replace("#", "").strip()
                # 소제목 스타일
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
                # 일반 텍스트 (Markdown bold 처리 -> HTML bold tag)
                # 예: **원인** -> <b>원인</b> (reportlab은 XML 태그 지원)
                processed_text = para.replace("**", "<b>").replace("**", "</b>") 
                # 닫는 태그 처리가 복잡하므로 단순 치환 (쌍이 맞다고 가정하거나 regex 사용 권장)
                # 여기서는 간단히 bold 처리 로직 개선
                import re
                processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
                
                elements.append(Paragraph(processed_text, body_style))

        # PDF 빌드
        doc.build(elements)
        print(f"[PDFGenerator] 리포트 생성 완료: {file_path}")
        return file_path

    def _format_analysis_text(self, text):
        """
        Dify 결과 텍스트를 문단 단위 리스트로 분리
        """
        if not text:
            return ["분석 결과가 없습니다."]
        
        # 줄바꿈 기준으로 분리하되, 빈 줄은 보존
        return text.split('\n')