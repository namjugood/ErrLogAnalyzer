# app/services/chart_generator.py

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import platform # platform 모듈 필요

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

    def generate_time_series_chart(self, time_series_data, top_n=5):
        # ... (기존 코드 동일) ...
        # (기존 generate_time_series_chart 메서드 내용은 유지해주세요)
        if not time_series_data:
            return None

        # 1. 데이터 전처리
        sorted_times = sorted(time_series_data.keys())
        error_totals = {}
        for t_data in time_series_data.values():
            for code, count in t_data.items():
                error_totals[code] = error_totals.get(code, 0) + count
        
        top_errors = sorted(error_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
        target_codes = [code for code, count in top_errors]

        x_values = [datetime.strptime(t, "%Y-%m-%d %H:%M") for t in sorted_times]
        y_values_map = {code: [] for code in target_codes}
        
        for t in sorted_times:
            counts = time_series_data[t]
            for code in target_codes:
                y_values_map[code].append(counts.get(code, 0))

        plt.figure(figsize=(10, 5))
        for code, y_vals in y_values_map.items():
            plt.plot(x_values, y_vals, marker='o', markersize=4, label=code)

        plt.title("시간대별 에러 발생 추이 (Top 5)", fontsize=14, pad=20)
        plt.xlabel("시간 (Time)", fontsize=10)
        plt.ylabel("발생 횟수 (Count)", fontsize=10)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gcf().autofmt_xdate()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(loc='upper right', fontsize=9)
        plt.tight_layout()

        filename = f"trend_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=100)
        plt.close()
        
        return filepath

    def generate_pie_chart(self, data_dict, title="채널별 에러 점유율"):
        """
        [신규] 원형 차트 생성
        :param data_dict: {'Mobile App': 10, 'Web': 20}
        """
        if not data_dict:
            return None
            
        labels = list(data_dict.keys())
        sizes = list(data_dict.values())
        
        plt.figure(figsize=(6, 4))
        # 파이 차트 그리기
        wedges, texts, autotexts = plt.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%', 
            startangle=140,
            textprops={'fontsize': 9}
        )
        
        plt.title(title, fontsize=12, pad=15)
        plt.axis('equal') # 원형 유지
        plt.tight_layout()

        filename = f"pie_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=100)
        plt.close()
        
        return filepath