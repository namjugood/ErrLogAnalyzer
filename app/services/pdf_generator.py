"""
app/services/pdf_generator.py

fpdf2 기반 PDF 생성기.
- 기존 ReportLab 기반 구현을 fpdf2로 교체했습니다.
- 브리핑(요약/상세) 본문은 multi_cell 기반으로 출력하여, 페이지를 넘어가도 내용이 이어지며
  길이가 매우 길어도 오류가 발생하지 않도록 합니다.
"""

import os
import sys
import json
import re
import html
from datetime import datetime
from collections import defaultdict
from typing import Tuple

from fpdf import FPDF
from fpdf.fonts import FontFace
from fpdf.enums import MethodReturnValue

from app.services.chart_generator import ChartGenerator
from app.core.chnl_constants import get_chnl_label, CHNL_LABELS

# 채널 구분 확장: ADM -> 관리자홈
# - 보고서 및 차트 생성 시 ADM 코드가 들어오면 '관리자홈'으로 표시합니다.
CHNL_LABELS.setdefault("ADM", "관리자홈")


def resource_path(relative_path: str) -> str:
    """
    PyInstaller 번들 환경(_MEIPASS)에서도 리소스 경로를 안정적으로 찾기 위한 유틸.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class PDFGenerator:
    """
    에러 로그 분석 리포트를 PDF로 생성합니다.
    - fpdf2의 `table()` 및 `multi_cell()`을 사용해 표/본문을 구성합니다.
    - 브리핑 텍스트는 페이지 경계를 넘어 자연스럽게 이어지도록 `multi_cell()`로 출력합니다.
    """

    def __init__(self, output_dir: str = "data/reports", font_path: str = "app/assets/fonts/NanumGothic.ttf", logger=None):
        self.output_dir = output_dir
        self.font_name = "NanumGothic"
        self.logger = logger
        self.font_path = resource_path(font_path)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        self.chart_gen = ChartGenerator(output_dir=os.path.join(output_dir, "charts"))

    def _log(self, message: str, level: str = "INFO"):
        """
        UI/워커로부터 주입된 로거 콜백이 있으면 로그를 전달합니다.
        """
        if self.logger:
            self.logger(message, level)

    def _ensure_font(self, pdf: FPDF) -> str:
        """
        PDF 폰트를 등록하고 사용할 폰트명을 반환합니다.
        - 폰트 파일이 없거나 등록 실패 시, 내장 폰트(Helvetica)로 폴백합니다.
        """
        try:
            if os.path.exists(self.font_path):
                # uni=True: 유니코드(한글) 출력 지원
                pdf.add_font(self.font_name, "", self.font_path, uni=True)
                return self.font_name
        except Exception as e:
            self._log(f"[PDF] 폰트 등록 실패: {e}", "WARN")
        return "Helvetica"

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        '#RRGGBB' 또는 'RRGGBB' -> (R, G, B)
        """
        s = (hex_color or "").strip().lstrip("#")
        if len(s) != 6:
            return (0, 0, 0)
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

    @staticmethod
    def _clean_text(text) -> str:
        """
        표/본문에 출력 가능한 문자열로 정규화합니다.
        - HTML escape/unescape 혼재 데이터 안전 처리
        - <br/> 계열을 줄바꿈으로 변환
        """
        s = "" if text is None else str(text)
        s = html.unescape(s)
        s = s.replace("<br/>", "\n").replace("<br />", "\n").replace("<br>", "\n")
        return s

    @staticmethod
    def _sanitize_msg_title(text: str) -> str:
        """
        msg_title(에러 메시지/패턴) 출력용 정규화.
        - 요구사항: msg_title에 '\\n'이 포함되면 빈 값으로 치환합니다.
        """
        s = "" if text is None else str(text)
        s = s.strip()
        if "\n" in s:
            return ""
        return s

    @staticmethod
    def _diagnosis_status_border_rgb(status: str) -> Tuple[int, int, int]:
        """
        진단상태(status) 기반 테두리 색상.
        - RED/CRITICAL: 빨강
        - YELLOW/WARNING/MAJOR: 노랑
        - 그 외(INFO 등): 초록(기본)
        """
        st = str(status or "INFO").upper().strip()
        if st in ["CRITICAL", "RED"]:
            return PDFGenerator._hex_to_rgb("#EF4444")
        if st in ["MAJOR", "WARNING", "YELLOW", "HIGH"]:
            return PDFGenerator._hex_to_rgb("#F59E0B")
        # MINOR/GREEN/INFO는 기본(초록)으로 처리
        return PDFGenerator._hex_to_rgb("#10B981")

    @staticmethod
    def _get_image_px_size(image_path: str) -> Tuple[int, int]:
        """
        이미지 픽셀 크기(width_px, height_px)를 반환합니다.
        - Pillow 없이 matplotlib로 읽어 비율을 계산합니다.
        """
        from matplotlib import image as mpimg

        img = mpimg.imread(image_path)
        # shape: (H, W, C) 또는 (H, W)
        height_px = int(img.shape[0])
        width_px = int(img.shape[1])
        return width_px, height_px

    @staticmethod
    def _fit_size_keep_ratio(src_w: float, src_h: float, max_w: float, max_h: float) -> Tuple[float, float]:
        """
        (src_w, src_h)를 (max_w, max_h) 안에 비율 유지로 맞춘 (w, h)를 반환합니다.
        """
        if src_w <= 0 or src_h <= 0:
            return max_w, max_h
        aspect = src_w / src_h
        w = float(max_w)
        h = w / aspect
        if h > max_h:
            h = float(max_h)
            w = h * aspect
        return w, h

    def _place_image_fit_box(
        self,
        pdf: FPDF,
        image_path: str,
        max_w: float,
        max_h: float,
        center: bool = True,
        pad_after: float = 4.0,
        fit_mode: str = "contain",
    ):
        """
        이미지를 지정 박스(max_w, max_h) 내에 비율 유지로 축소하여 삽입합니다.
        - 높이/가로를 임의 왜곡하지 않고, 비율 기반으로만 축소합니다.
        - fit_mode:
          - "contain": (max_w, max_h) 안에 들어오도록 축소(기존 동작)
          - "width": 가로(max_w) 기준으로 비율 고정. (명확한 가독성을 위해 가로 우선)
        """
        w_px, h_px = self._get_image_px_size(image_path)
        aspect = (w_px / h_px) if (w_px and h_px) else 1.0

        if str(fit_mode).lower().strip() == "width":
            # 가로 길이를 기준으로 비율 고정 (요구사항: 세로 기준으로 줄어드는 느낌 방지)
            w_mm = float(max_w)
            h_mm = (w_mm / aspect) if aspect else float(max_h)
        else:
            w_mm, h_mm = self._fit_size_keep_ratio(w_px, h_px, max_w=max_w, max_h=max_h)

        y0 = pdf.get_y()
        # 이미지가 현재 페이지에 들어가지 않으면 페이지를 넘기고 다시 시도 (왜곡 대신 페이지 이동)
        if y0 + h_mm > (pdf.h - pdf.b_margin):
            pdf.add_page()
            y0 = pdf.get_y()

        # "width" 모드라도 페이지에 도저히 안 들어가면(매우 긴 이미지) 페이지 높이 기준으로만 예외 축소
        max_page_h = (pdf.h - pdf.t_margin - pdf.b_margin)
        if h_mm > max_page_h and aspect:
            h_mm = max_page_h
            w_mm = h_mm * aspect

        x0 = pdf.l_margin
        if center:
            epw = pdf.w - pdf.l_margin - pdf.r_margin
            x0 = pdf.l_margin + max(0.0, (epw - w_mm) / 2.0)

        pdf.image(image_path, x=x0, y=y0, w=w_mm)
        pdf.set_y(y0 + h_mm + pad_after)

    @staticmethod
    def _fmt_first_seen(ts) -> str:
        """
        최초 발생 시각을 yyyy-MM-dd HH:mm 형식으로 정규화합니다.
        """
        if not ts or ts == "-":
            return "-"
        s = str(ts).strip()
        if len(s) >= 16:
            return s[:16]
        try:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return s[:16] if len(s) >= 16 else s

    def create_report(self, channel_name, analysis_data, aggregator_data, date_range=None):
        """
        PDF 보고서 생성.
        :param date_range: {"start": "YYYY-MM-DD HH:MM", "end": "..."} 조회 기간 (선택)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{channel_name}_Report_{timestamp}.pdf"
        file_path = os.path.join(self.output_dir, filename)

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(left=10, top=15, right=10)
        pdf.add_page()

        font_name = self._ensure_font(pdf)
        epw = pdf.w - pdf.l_margin - pdf.r_margin

        # 데이터 준비
        issues = (aggregator_data or {}).get("issue_groups", [])
        meta = (aggregator_data or {}).get("report_meta", {})

        channel_stats = defaultdict(int)
        total_errors = 0
        for issue in issues:
            cnt = issue.get("total_count", 0)
            raw_chnl = issue.get("channel", "") or ""
            channel_stats[get_chnl_label(raw_chnl)] += cnt
            total_errors += cnt
        total_logs = meta.get("total_logs_processed", 0)

        # 1) 문서 헤더
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, size=24)
        pdf.cell(0, 12, f"에러 로그 분석 보고서 ({channel_name})", ln=1, align="C")

        pdf.set_font(font_name, size=10)
        if date_range and isinstance(date_range, dict):
            start_str = date_range.get("start", "-")
            end_str = date_range.get("end", "-")
            pdf.cell(0, 6, f"조회 기간: {start_str} ~ {end_str}", ln=1)
        else:
            pdf.cell(0, 6, "조회 기간: -", ln=1)
        pdf.ln(6)

        # 2) 주요 에러 통계
        pdf.set_text_color(*self._hex_to_rgb("#2563EB"))
        pdf.set_font(font_name, size=16)
        pdf.cell(0, 8, "1. 주요 에러 통계 (Top Issues)", ln=1)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, size=10)
        pdf.cell(0, 6, f"총 처리 로그 수: {total_logs}건  |  총 에러 발생 수: {total_errors}건", ln=1)
        pdf.ln(2)

        # 주요 에러 통계 테이블 (구분, 채널, 에러메시지, 발생 횟수, 최초 발생 시각)
        pdf.set_draw_color(*self._hex_to_rgb("#E5E7EB"))
        pdf.set_line_width(0.3)
        pdf.set_font(font_name, size=8)
        # fpdf2 테이블은 기본적으로 headings를 Bold로 렌더링하려고 합니다.
        # TTF 폰트는 Bold 스타일을 별도 add_font()로 등록해야 하므로,
        # 레이아웃 유지를 위해 headings 강조를 비활성화(emphasis="")합니다.
        headings_style = FontFace(emphasis="", fill_color=self._hex_to_rgb("#F3F4F6"))
        with pdf.table(
            width=epw,
            col_widths=(20, 22, 82, 22, 42),
            text_align=("CENTER", "CENTER", "LEFT", "CENTER", "CENTER"),
            headings_style=headings_style,
            repeat_headings=1,
        ) as table:
            table.row(("구분", "채널", "에러메시지", "발생 횟수", "최초 발생 시각"))
            for issue in issues:
                msg_title = self._sanitize_msg_title(issue.get("message_pattern") or "")
                first_seen = self._fmt_first_seen(issue.get("time_context", {}).get("first_seen", "-"))
                table.row(
                    (
                        str(issue.get("error_id", "-") or "-"),
                        str(get_chnl_label(issue.get("channel", "") or "")),
                        self._clean_text(msg_title),
                        f"{issue.get('total_count', 0)}건",
                        first_seen,
                    )
                )
        pdf.ln(6)

        # 3) 채널별 점유율
        if channel_stats:
            pdf.set_text_color(*self._hex_to_rgb("#2563EB"))
            pdf.set_font(font_name, size=16)
            pdf.cell(0, 8, "2. 채널별 에러 점유율 (Channel Stats)", ln=1)

            chart_path = self.chart_gen.generate_channel_share_bar_chart(channel_stats)
            if chart_path and os.path.exists(chart_path):
                # 가로/세로 비율을 유지한 채로 박스에 맞춰 축소해서 출력
                self._place_image_fit_box(pdf, chart_path, max_w=epw, max_h=98, center=True, pad_after=4.0)
            pdf.ln(6)

        # 4) 시간대별 발생 추이
        time_series = (aggregator_data or {}).get("time_series_data", {})
        if time_series:
            pdf.set_text_color(*self._hex_to_rgb("#2563EB"))
            pdf.set_font(font_name, size=16)
            pdf.cell(0, 8, "3. 시간대별 발생 추이 (Trend Analysis)", ln=1)

            all_error_ids = [ig.get("error_id") for ig in issues if ig.get("error_id")]
            chart_path = self.chart_gen.generate_time_series_chart(time_series, all_error_ids=all_error_ids)
            if chart_path and os.path.exists(chart_path):
                # 요구사항: 가로 길이를 기준으로 비율 고정하여 축소 (세로 기준 축소로 보이지 않게)
                self._place_image_fit_box(pdf, chart_path, max_w=epw, max_h=9999, center=False, pad_after=4.0, fit_mode="width")
            pdf.ln(6)

        # 5) AI 상세 분석 결과
        pdf.set_text_color(*self._hex_to_rgb("#2563EB"))
        pdf.set_font(font_name, size=16)
        pdf.cell(0, 8, "4. AI 상세 분석 결과", ln=1)
        pdf.set_text_color(0, 0, 0)

        self._log(f"[DEBUG] PDF 생성 진입 데이터 (analysis_data):\n{analysis_data}", "INFO")
        ai_data = self._normalize_analysis_data(analysis_data)
        self._log(f"[DEBUG] 정규화된 데이터 (ai_data):\n{ai_data}", "INFO")

        if ai_data:
            summary = ai_data.get("summary", {}) or {}
            details = ai_data.get("details", []) or []

            if summary:
                self._draw_ai_summary(pdf, font_name, epw, summary)
                pdf.ln(4)

            if details:
                issue_msg_lookup = {}
                for ig in issues:
                    if ig.get("error_id"):
                        issue_msg_lookup[ig["error_id"]] = (ig.get("message_pattern") or "").strip()

                valid_details = [d for d in details if isinstance(d, dict)]
                details_by_channel = defaultdict(list)
                for item in valid_details:
                    sig = item.get("signature", "")
                    chnl_code = "Unknown"
                    if sig and "|" in sig:
                        chnl_code = sig.split("|")[0].strip()
                    details_by_channel[chnl_code].append(item)

                ordered_keys = [k for k in CHNL_LABELS.keys() if k in details_by_channel]
                other_keys = [k for k in details_by_channel.keys() if k not in CHNL_LABELS]

                pdf.set_font(font_name, size=12)
                pdf.set_text_color(*self._hex_to_rgb("#374151"))
                for ch_idx, chnl_code in enumerate(ordered_keys + other_keys, 1):
                    chnl_name = get_chnl_label(chnl_code)
                    items = details_by_channel[chnl_code]

                    pdf.cell(0, 7, f"{ch_idx}) {chnl_name}", ln=1)
                    pdf.ln(2)

                    for d_idx, item in enumerate(items, 1):
                        self._draw_ai_detail(pdf, font_name, epw, item, ch_idx, d_idx, issue_msg_lookup)
                        # 상세 항목 간 시각적 구분을 위해 한 줄 여백을 둡니다.
                        pdf.ln(6)
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.set_font(font_name, size=10)
                pdf.cell(0, 6, "상세 분석 데이터가 없습니다.", ln=1)
        else:
            pdf.set_font(font_name, size=10)
            fallback_text = str(analysis_data) if analysis_data else "분석 결과가 없습니다."
            pdf.multi_cell(0, 5, self._clean_text(fallback_text))

        pdf.output(file_path)
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
                
                # 브리핑: "구분코드 : 브리핑내용" 형식으로 누적
                br = summ.get("briefing")
                if br:
                    dets = report.get("details", [])
                    code = report.get("error_id") or summ.get("error_id")
                    if not code and isinstance(dets, list) and dets:
                        code = (dets[0] or {}).get("error_id")
                    code = str(code).strip() if code is not None else "-"
                    briefings.append(f"{code} : {br}")
                
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
            # 중복 제거 (순서 유지)
            seen = set()
            briefings_unique = []
            for b in briefings:
                key = (b.strip() if b else "")
                if key and key not in seen:
                    seen.add(key)
                    briefings_unique.append(b)
            # 브리핑 항목 간 구분을 위해 빈 줄(개행 2번)을 삽입합니다.
            merged_summary["briefing"] = "\n\n".join(briefings_unique)

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

    def _draw_ai_summary(self, pdf: FPDF, font_name: str, epw: float, summary: dict):
        """
        AI 요약 영역(진단 상태/주요 이슈/브리핑)을 출력합니다.
        - 브리핑 본문은 multi_cell로 출력하여, 페이지를 넘어가도 자연스럽게 이어집니다.
        """
        status = str(summary.get("status", "INFO") or "INFO").upper()
        # 요구사항: 요약 테이블(진단상태/주요이슈/브리핑) 테두리 색은 진단상태(status) 컬러로 적용
        border_rgb = self._diagnosis_status_border_rgb(status)

        sc = summary.get("critical_count", 0)
        sm = summary.get("major_count", 0)
        sn = summary.get("minor_count", 0)
        briefing = self._clean_text(summary.get("briefing", "-"))

        # 상단 2행은 테이블로 정리
        pdf.set_font(font_name, size=10)
        pdf.set_draw_color(*border_rgb)
        pdf.set_line_width(0.3)
        left_fill = self._hex_to_rgb("#F3F4F6")

        with pdf.table(
            width=epw,
            col_widths=(40, 150),
            text_align=("LEFT", "LEFT"),
            first_row_as_headings=False,
            repeat_headings=0,
        ) as table:
            row = table.row()
            row.cell("진단 상태", style=FontFace(fill_color=left_fill))
            row.cell(status)

            row = table.row()
            row.cell("주요 이슈", style=FontFace(fill_color=left_fill))
            row.cell(f"Critical({sc}), Major({sm}), Minor({sn})")

        # 브리핑: label + 본문(페이지 넘어가며 이어짐)
        label_w = 40
        value_w = epw - label_w
        line_h = 5.5

        pdf.set_font(font_name, size=10)
        pdf.set_draw_color(*border_rgb)

        # 요구사항: 브리핑 본문 높이 변화에 따라 라벨(제목) 높이도 동일하게 맞춤
        # - 브리핑은 "하나의 셀"로 보여야 하므로, 내부 가로 구분선은 그리지 않고
        #   외곽 테두리만 유지하도록 라인 단위로 L/R(및 T/B) 테두리를 분리해 그립니다.
        # - multi_cell의 줄바꿈/워드랩 결과를 dry_run으로 얻어, 라벨/본문을 동일 라인 수로 출력합니다.
        lines = pdf.multi_cell(value_w, line_h, briefing, dry_run=True, output=MethodReturnValue.LINES)
        if not lines:
            lines = [""]

        pdf.set_fill_color(*left_fill)
        i = 0
        while i < len(lines):
            # 남은 공간이 부족하면 다음 페이지에서 계속 (비율/레이아웃 왜곡 없이 페이지 전환)
            remaining_h = (pdf.h - pdf.b_margin) - pdf.get_y()
            max_lines = int(remaining_h // line_h)
            if max_lines <= 0:
                pdf.add_page()
                pdf.set_font(font_name, size=10)
                pdf.set_draw_color(*border_rgb)
                pdf.set_line_width(0.3)
                pdf.set_fill_color(*left_fill)
                remaining_h = (pdf.h - pdf.b_margin) - pdf.get_y()
                max_lines = max(1, int(remaining_h // line_h))

            chunk = lines[i : i + max_lines]
            is_first_chunk = (i == 0)
            is_last_chunk = (i + len(chunk) >= len(lines))

            for j, line in enumerate(chunk):
                is_first_in_chunk = (j == 0)
                is_last_in_chunk = (j == len(chunk) - 1)
                is_last_overall = (i + j == len(lines) - 1)

                # 브리핑 행은 상단 2행 테이블 바로 아래에 이어지므로, 첫 줄은 T를 생략하여 중복 라인을 방지합니다.
                top = (not is_first_chunk) and is_first_in_chunk
                bottom = is_last_overall or (is_last_in_chunk and not is_last_chunk)

                label_border = "LR" + ("T" if top else "") + ("B" if bottom else "")
                value_border = "R" + ("T" if top else "") + ("B" if bottom else "")

                label_text = "브리핑" if (is_first_chunk and is_first_in_chunk) else ""
                pdf.cell(label_w, line_h, label_text, border=label_border, fill=True)

                pdf.set_fill_color(255, 255, 255)
                pdf.cell(value_w, line_h, line, border=value_border, ln=1)
                pdf.set_fill_color(*left_fill)

            i += len(chunk)
            if i < len(lines):
                pdf.add_page()
                pdf.set_font(font_name, size=10)
                pdf.set_draw_color(*border_rgb)
                pdf.set_line_width(0.3)
                pdf.set_fill_color(*left_fill)

    def _draw_ai_detail(self, pdf: FPDF, font_name: str, epw: float, item: dict, ch_idx: int, d_idx: int, issue_msg_lookup: dict):
        """
        AI 상세 분석(개별 에러 항목) 테이블을 출력합니다.
        """
        signature = item.get("signature", "-")
        parsed_sig = self._parse_signature(signature)
        error_code = item.get("error_code") or parsed_sig.get("error_code") or "-"
        error_id = item.get("error_id") or "-"

        # 제목: error_id로 issue_groups의 message_pattern(에러 메시지) 매핑
        raw_title = (issue_msg_lookup.get(item.get("error_id")) or "") if issue_msg_lookup else ""
        msg_title = self._sanitize_msg_title(raw_title)
        # msg_title이 비어 있으면 error_id로 대체하여 구분 가능하도록 함
        display_title = msg_title or str(error_id) or "에러 상세"
        severity = item.get("severity", "INFO")

        pdf.set_font(font_name, size=11)
        pdf.set_text_color(*self._hex_to_rgb("#374151"))
        pdf.multi_cell(0, 6, f"{ch_idx}-{d_idx}) {display_title} ({severity})")

        analysis = item.get("analysis", {})
        if not isinstance(analysis, dict):
            analysis = {}

        impact = analysis.get("impact") or item.get("impact") or "-"
        root_cause = analysis.get("root_cause") or item.get("root_cause") or "-"
        action = analysis.get("action_item") or analysis.get("recommendation") or item.get("action_item") or "-"

        service_info = "-"
        if parsed_sig.get("service") and parsed_sig.get("operation"):
            service_info = f"{parsed_sig['service']}.{parsed_sig['operation']}"

        left_fill = self._hex_to_rgb("#F3F4F6")
        white_fill = (255, 255, 255)
        # 요구사항: 상세(나머지) 테이블의 테두리 색은 "주요 에러 통계" 테이블과 동일하게 적용
        pdf.set_draw_color(*self._hex_to_rgb("#E5E7EB"))
        pdf.set_line_width(0.3)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, size=9)

        with pdf.table(
            width=epw,
            col_widths=(40, 150),
            text_align=("LEFT", "LEFT"),
            first_row_as_headings=False,
            repeat_headings=0,
        ) as table:
            row = table.row()
            row.cell("구분", style=FontFace(fill_color=left_fill))
            row.cell(str(error_id), style=FontFace(fill_color=white_fill))

            row = table.row()
            row.cell("서비스 정보", style=FontFace(fill_color=left_fill))
            row.cell(self._clean_text(service_info), style=FontFace(fill_color=white_fill))

            row = table.row()
            row.cell("에러 코드", style=FontFace(fill_color=left_fill))
            row.cell(self._clean_text(error_code), style=FontFace(fill_color=white_fill))

            row = table.row()
            row.cell("영향도", style=FontFace(fill_color=left_fill))
            row.cell(self._clean_text(impact), style=FontFace(fill_color=white_fill))

            row = table.row()
            row.cell("원인", style=FontFace(fill_color=left_fill))
            row.cell(self._clean_text(root_cause), style=FontFace(fill_color=white_fill))

            row = table.row()
            row.cell("조치 사항", style=FontFace(fill_color=left_fill))
            row.cell(self._clean_text(action), style=FontFace(fill_color=white_fill))

        # 이후 표 렌더링에 영향이 없도록 기본 테두리 스타일로 복원
        pdf.set_draw_color(*self._hex_to_rgb("#E5E7EB"))
        pdf.set_line_width(0.3)

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