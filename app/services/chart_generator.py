import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

class ChartGenerator:
    def __init__(self, output_dir="data/temp"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            
        # 한글 폰트 설정 (시스템에 설치된 폰트에 따라 조정 필요)
        # Ubuntu/Linux의 경우 'NanumGothic', Windows의 경우 'Malgun Gothic' 등
        import platform
        sys_os = platform.system()
        if sys_os == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        elif sys_os == 'Darwin': # Mac
            plt.rc('font', family='AppleGothic')
        else:
            # 리눅스 등에서는 폰트 파일 경로 지정 방식 권장 (여기선 기본값)
            plt.rc('font', family='DejaVu Sans') 
            
        plt.rc('axes', unicode_minus=False) # 마이너스 기호 깨짐 방지

    def generate_time_series_chart(self, time_series_data, top_n=5):
        """
        :param time_series_data: { "YYYY-MM-DD HH:MM": {"ERR01": 5, "ERR02": 1}, ... }
        :return: 생성된 이미지 파일 경로
        """
        if not time_series_data:
            return None

        # 1. 데이터 전처리
        # 시간순 정렬
        sorted_times = sorted(time_series_data.keys())
        
        # 상위 N개 에러 코드 추출 (전체 기간 합산 기준)
        error_totals = {}
        for t_data in time_series_data.values():
            for code, count in t_data.items():
                error_totals[code] = error_totals.get(code, 0) + count
        
        top_errors = sorted(error_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
        target_codes = [code for code, count in top_errors]

        # 플롯 데이터 구성
        # x_values: datetime 객체 리스트
        x_values = [datetime.strptime(t, "%Y-%m-%d %H:%M") for t in sorted_times]
        
        y_values_map = {code: [] for code in target_codes}
        
        for t in sorted_times:
            counts = time_series_data[t]
            for code in target_codes:
                y_values_map[code].append(counts.get(code, 0))

        # 2. 차트 그리기
        plt.figure(figsize=(10, 5)) # 가로로 긴 형태
        
        for code, y_vals in y_values_map.items():
            plt.plot(x_values, y_vals, marker='o', markersize=4, label=code)

        plt.title("시간대별 에러 발생 추이 (Top 5)", fontsize=14, pad=20)
        plt.xlabel("시간 (Time)", fontsize=10)
        plt.ylabel("발생 횟수 (Count)", fontsize=10)
        
        # X축 포맷팅 (시간)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gcf().autofmt_xdate() # 라벨 겹침 방지 (회전)
        
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(loc='upper right', fontsize=9)
        plt.tight_layout()

        # 3. 저장
        filename = f"chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=100)
        plt.close()
        
        return filepath