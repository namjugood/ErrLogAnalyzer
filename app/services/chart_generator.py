# app/services/chart_generator.py

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator, FuncFormatter
import numpy as np
from datetime import datetime
from collections import defaultdict
import os
import platform  # platform 모듈 필요

class ChartGenerator:
    def __init__(self, output_dir="data/temp"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            
        # 폰트 설정
        sys_os = platform.system()
        if sys_os == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        elif sys_os == 'Darwin':
            plt.rc('font', family='AppleGothic')
        else:
            plt.rc('font', family='DejaVu Sans') 
            
        plt.rc('axes', unicode_minus=False)

    def generate_time_series_chart(self, time_series_data, top_n=None, all_error_ids=None):
        """
        시간대별 에러 발생 추이를 히트맵으로 생성.
        x축 30분 단위, y축 Error01부터, 에러 범례는 좌측, 컬러바는 자연수만 표기.
        :param time_series_data: { "YYYY-MM-DD HH:MM": { "Error01": count, ... }, ... }
        :param top_n: None이면 모든 에러 포함, 숫자면 상위 N개만 (호환용)
        :param all_error_ids: 전체 에러 ID 목록(issue_groups 순서). 지정 시 Y축에 모두 노출(시계열에 없는 항목은 0으로 표시).
        """
        if not time_series_data:
            return None

        # 1) 시간 구간을 30분 단위로 집계
        def _to_30m_bucket(t_str):
            try:
                dt = datetime.strptime(t_str[:16], "%Y-%m-%d %H:%M")
                m = (dt.minute // 30) * 30
                return dt.replace(minute=m, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")
            except (ValueError, IndexError):
                return t_str[:16] if len(t_str) >= 16 else t_str

        time_series_30m = defaultdict(lambda: defaultdict(int))
        for t_str, counts in time_series_data.items():
            bucket = _to_30m_bucket(t_str)
            for code, cnt in counts.items():
                time_series_30m[bucket][code] += cnt

        sorted_times = sorted(time_series_30m.keys())
        error_totals = {}
        for t_data in time_series_30m.values():
            for code, count in t_data.items():
                error_totals[code] = error_totals.get(code, 0) + count

        # all_error_ids가 있으면 Y축을 해당 순서로 고정(시계열에 없는 Error01, Error02 등도 노출)
        if all_error_ids:
            target_codes = [eid for eid in all_error_ids if eid]
        else:
            if top_n is not None and top_n > 0:
                target_codes = [code for code, _ in sorted(error_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]]
            else:
                target_codes = [code for code, _ in sorted(error_totals.items(), key=lambda x: x[1], reverse=True)]
            # Error01, Error02... 순 정렬
            def _error_id_sort_key(code):
                if isinstance(code, str) and code.startswith("Error"):
                    try:
                        return int(code[5:] or 0)
                    except ValueError:
                        return 9999
                return 9999
            target_codes = sorted(target_codes, key=_error_id_sort_key)

        if not target_codes or not sorted_times:
            return None

        # 행=에러(Error01이 위), 열=시간(30분 단위)
        data = np.zeros((len(target_codes), len(sorted_times)))
        for i, code in enumerate(target_codes):
            for j, t in enumerate(sorted_times):
                data[i, j] = time_series_30m[t].get(code, 0)

        n_errors, n_times = data.shape
        fig_h = max(5.0, n_errors * 0.35)
        fig, ax = plt.subplots(figsize=(11, fig_h))

        im = ax.imshow(data, aspect="auto", cmap="YlOrRd", interpolation="nearest", origin="upper")

        # X축: 30분 단위 눈금 유지, 라벨은 00~23(시) 형식으로 정시에만 표기
        ax.set_xticks(range(len(sorted_times)))
        def _xlabel_00_23(t_str):
            try:
                dt = datetime.strptime(t_str[:16], "%Y-%m-%d %H:%M")
                if dt.minute == 0:
                    return f"{dt.hour:02d}"
                return ""  # 30분 구간은 눈금만, 라벨 없음
            except (ValueError, IndexError):
                return t_str[-5:] if len(t_str) >= 5 else t_str
        time_labels = [_xlabel_00_23(t) for t in sorted_times]
        ax.set_xticklabels(time_labels, fontsize=10)
        ax.set_xlabel("시간 (Time, 00~23)", fontsize=11)

        ax.set_yticks(range(len(target_codes)))
        ax.set_yticklabels(target_codes, fontsize=10)
        ax.tick_params(left=True, labelleft=True, right=False, labelright=False)
        ax.yaxis.set_label_position("left")
        ax.set_ylabel("에러", fontsize=11)

        ax.set_title("시간대별 에러 발생 추이", fontsize=14, pad=14)
        # 발생 건수 컬러바를 차트 왼쪽에 배치
        cbar = plt.colorbar(im, ax=ax, shrink=0.6, label="발생 건수", location="left")
        cbar.ax.tick_params(labelsize=9)
        cbar.ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "%d" % int(round(x))))

        plt.tight_layout()

        filename = f"trend_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=180, bbox_inches="tight")
        plt.close()
        return filepath

    def generate_channel_share_bar_chart(self, data_dict, title="채널별 에러 점유율"):
        """
        채널별 에러 점유율을 100% 누적 가로 막대 차트(막대 1개)로 생성합니다.
        - 첨부 이미지 형태처럼, 하나의 가로 막대에 채널별 비율을 구간(세그먼트)로 표시합니다.
        :param data_dict: {'Mobile App': 10, 'Web': 20}
        """
        if not data_dict:
            return None

        # 우선 노출 순서(있으면 우선 적용): 모바일앱/모바일웹/홈페이지
        preferred_order = ["모바일앱", "모바일웹", "홈페이지", "Mobile App", "Mobile Web", "Homepage", "Home"]

        raw_items = [(str(k), int(v or 0)) for k, v in data_dict.items()]
        raw_items = [(k, v) for k, v in raw_items if k and v >= 0]

        def _order_key(item):
            k, v = item
            if k in preferred_order:
                return (0, preferred_order.index(k), 0)
            # 나머지는 큰 값 우선
            return (1, 999, -v)

        items = sorted(raw_items, key=_order_key)

        labels = [k for k, _ in items]
        counts = [v for _, v in items]
        total = max(1, sum(counts))
        percents = [v * 100.0 / total for v in counts]

        # 100% 누적 막대 (세그먼트)
        fig, ax = plt.subplots(figsize=(11, 3.1))

        # 구분이 명확한 categorical 팔레트 사용 (그라데이션/단일색 지양)
        palette = list(plt.get_cmap("tab20").colors)

        def _is_light(rgb):
            # rgb: 0~1 float tuple
            r, g, b = rgb[0], rgb[1], rgb[2]
            # ITU-R BT.709 luminance
            return (0.2126 * r + 0.7152 * g + 0.0722 * b) > 0.62

        left = 0.0
        bar_y = 0
        bar_h = 0.35
        for i, (label, p, c) in enumerate(zip(labels, percents, counts)):
            if p <= 0:
                continue
            color = palette[i % len(palette)]
            ax.barh([bar_y], [p], left=left, height=bar_h, color=color, edgecolor="white", linewidth=1.0)

            # 세그먼트 중앙: 퍼센트(%) 표시
            mid_x = left + p / 2.0
            txt = f"{p:.0f}%" if p >= 10 else f"{p:.1f}%"
            pct_color = "#111827" if _is_light(color) else "white"
            ax.text(mid_x, bar_y, txt, va="center", ha="center", fontsize=12, color=pct_color, fontweight="bold")

            # 채널명: 타이틀 아래로 배치 (x는 데이터좌표, y는 축 비율좌표)
            ax.text(
                mid_x,
                0.78,
                label,
                transform=ax.get_xaxis_transform(),
                va="bottom",
                ha="center",
                fontsize=12,
                color="#374151",
            )

            left += p

        ax.set_xlim(0, 100)
        ax.set_yticks([])
        ax.set_xticks([])
        for spine in ["top", "right", "left", "bottom"]:
            ax.spines[spine].set_visible(False)

        # 타이틀: 맨 위(suptitle), 채널 구분 라벨은 그 아래에 위치
        fig.suptitle(title, fontsize=16, y=0.98)
        # 상단 여백을 충분히 확보하여 타이틀/라벨이 겹치지 않도록 조정
        fig.subplots_adjust(top=0.80)
        plt.tight_layout(rect=(0, 0, 1, 0.88))

        filename = f"channel_share_bar_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath

    def generate_pie_chart(self, data_dict, title="채널별 에러 점유율"):
        """
        (호환용) 기존 원형 차트 API.
        - 현재 리포트 요구사항에 따라 가로 막대형 차트로 대체합니다.
        """
        return self.generate_channel_share_bar_chart(data_dict, title=title)