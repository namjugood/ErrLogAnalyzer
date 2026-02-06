# ErrLogAnalyzer

Python + PyQt6 기반의 데스크톱 애플리케이션으로, BXM 에러 로그 파일을 실시간으로 모니터링하고 AI를 활용하여 분석하는 도구입니다.

## 프로젝트 구조


```

ErrLogAnalyzer/
├── main.py                  # 프로그램 시작점 (Entry Point, 지연 로딩 적용)
├── requirements.txt         # 의존성 패키지 (PyQt6, requests, reportlab 등)
├── .gitignore              # Git 제외 파일 목록
├── config/                 # 설정 모듈
│   └── settings.py         # 설정 관리 모듈
├── settings/               # 설정 파일 (Git 제외)
│   └── settings.json       # 채널 설정, API 키 등
├── app/
│   ├── **init**.py
│   ├── api/                # API 클라이언트
│   │   └── bxm_client.py   # BXM API 통신
│   ├── core/               # 핵심 비즈니스 로직
│   │   ├── log_parser.py   # 로그 파싱 및 전처리 로직
│   │   ├── aggregator.py   # 데이터 그룹핑 및 스냅샷 생성
│   │   └── history_manager.py # 리포트 이력 관리
│   ├── services/           # 외부 시스템 통신
│   │   ├── dify_client.py  # Dify API 호출 및 응답 처리
│   │   ├── pdf_generator.py # PDF 리포트 생성
│   │   └── file_watcher.py # 로그 파일 실시간 감지 (Observer 패턴)
│   ├── ui/                 # 사용자 인터페이스 (PyQt6)
│   │   ├── main_window.py  # 메인 프레임 및 사이드바
│   │   ├── dashboard.py    # 대시보드 화면 (터미널 스타일 콘솔)
│   │   ├── report_view.py  # 리포트 이력 및 상세 보기
│   │   ├── settings_view.py # 설정 화면
│   │   ├── add_channel_dialog.py # 채널 추가 다이얼로그
│   │   └── splash_screen.py # 초기 로딩 화면
│   │   └── styles.py       # QSS 스타일시트 (다크 모드 디자인 적용)
│   ├── workers/            # 백그라운드 작업
│   │   └── monitor_worker.py # 멀티 채널 모니터링 워커
│   └── utils/              # 공통 유틸리티
│       └── helpers.py      # 날짜 포맷팅 등 보조 함수
├── app/assets/             # 리소스 파일
│   └── fonts/              # 폰트 파일
│       └── NanumGothic.ttf # 한글 폰트
└── data/                   # 로컬 데이터 저장소
├── logs/               # 로그 파일 (Git 제외)
└── reports/            # 생성된 PDF 리포트

```

## 설치 방법

1. Python 3.8 이상이 설치되어 있어야 합니다.

2. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt

```

3. `settings/settings.json` 파일을 생성하고 채널 설정 및 API 키를 구성합니다.
* Dify API 키 설정
* BXM 채널 정보 설정
* 로그 경로 및 보관 기간 설정



## 실행 방법

### 개발 모드 실행

```bash
python main.py

```

### 배포용 빌드

Windows 환경에서 실행 파일로 빌드하려면:

1. **필요한 패키지 설치**

```bash
pip install -r requirements.txt

```

2. **빌드 스크립트 실행**

```bash
build.bat

```

빌드 스크립트는 다음 작업을 수행합니다:

* PyInstaller를 사용하여 실행 파일 생성
* 필요한 리소스 파일(폰트 등) 포함
* 배포 폴더 구조 생성 (`dist/ErrLogAnalyzer/`)
* 7-Zip으로 압축 파일 생성 (`ErrLogAnalyzer_vYYYYMMDD_HHMMSS.7z`)

**빌드 결과물:**

* `dist/ErrLogAnalyzer/ErrLogAnalyzer.exe`: 실행 파일
* `dist/ErrLogAnalyzer/settings/`: 설정 파일 폴더 (템플릿 포함)
* `dist/ErrLogAnalyzer/data/`: 데이터 저장 폴더 구조
* `ErrLogAnalyzer_vYYYYMMDD_HHMMSS.7z`: 배포용 압축 파일

**수동 빌드:**

```bash
pyinstaller --clean ErrLogAnalyzer.spec

```

**주의사항:**

* 빌드 전에 `settings/settings.json` 파일이 올바르게 설정되어 있는지 확인하세요.
* 빌드된 실행 파일은 `dist/ErrLogAnalyzer/` 폴더에 생성됩니다.
* 배포 시 `settings/` 폴더의 설정 파일을 함께 배포해야 합니다.

## 주요 기능

### 1. 로그 파일 실시간 모니터링

* `app/services/file_watcher.py`를 통해 로그 파일 변경을 실시간으로 감지합니다.
* Observer 패턴을 사용하여 효율적인 파일 감시를 구현합니다.

### 2. 로그 파싱 및 전처리

* `app/core/log_parser.py`에서 로그 파일을 읽고 구조화된 데이터로 변환합니다.

### 3. 데이터 그룹핑 및 스냅샷 생성

* `app/core/aggregator.py`에서 로그 데이터를 그룹핑하고 스냅샷을 생성합니다.
* 기획서 2.A 항목에 해당하는 기능입니다.

### 4. Dify API 연동

* `app/services/dify_client.py`를 통해 Dify API와 통신하여 AI 분석 결과를 받아옵니다.
* Streaming 응답 처리를 지원하여 분석 과정을 실시간으로 추적합니다.

### 5. 사용자 인터페이스 (UI/UX)

* **대시보드**: 실시간 통계 및 멀티 채널 모니터링 정보 표시
* **터미널 스타일 콘솔**: AI 분석 진행률(Step)을 덮어쓰기(Overwrite) 효과로 시각화하여 가독성 향상
* **스플래시 스크린**: 지연 임포트(Lazy Import) 적용으로 프로그램 실행 즉시 로딩 화면 표시
* **리포트 뷰**: 리포트 이력 및 상세 정보 확인, PDF 다운로드
* **설정 화면**: API 키, 채널 설정 등 관리
* **다크 모드**: QSS 스타일시트를 통한 다크 모드 디자인 지원

### 6. 리포트 이력 관리

* `app/core/history_manager.py`를 통해 생성된 리포트의 메타데이터를 관리합니다.
* 리포트 검색, 필터링, 삭제 기능을 제공합니다.

### 7. PDF 리포트 생성

* `app/services/pdf_generator.py`를 통해 분석 결과를 PDF 형식으로 생성
* 한글 폰트 지원 (NanumGothic)
* 리포트 메타데이터 및 AI 분석 결과 포함

## 개발 환경

* Python 3.8+
* PyQt6 >= 6.6.0
* requests >= 2.31.0
* watchdog >= 3.0.0
* reportlab >= 3.6.0

## 주요 의존성

* **PyQt6**: GUI 프레임워크
* **requests**: HTTP 클라이언트 (API 통신)
* **watchdog**: 파일 시스템 모니터링
* **reportlab**: PDF 생성

## 설정

프로젝트를 실행하기 전에 `settings/settings.json` 파일을 생성하고 다음 형식으로 설정하세요:

```json
{
  "channels": [
    {
      "name": "채널명",
      "key": "채널키",
      "url": "http://서버주소:포트",
      "id": "사용자ID",
      "password": "비밀번호"
    }
  ],
  "log_path": "로그파일경로",
  "retention_days": "30",
  "dify_config": {
    "url": "[https://api.dify.ai/v1/workflows/run](https://api.dify.ai/v1/workflows/run)",
    "authorization": "Bearer YOUR_API_KEY",
    "content_type": "application/json"
  }
}

```

**주의사항:**

* `settings/` 폴더와 `data/logs/` 폴더는 Git에서 제외됩니다.
* 실제 API 키와 비밀번호는 Git에 커밋하지 마세요.
* `.gitignore` 파일에 민감한 정보가 포함된 경로가 설정되어 있습니다.

## 기술 스택

* **Python 3.8+**: 프로그래밍 언어
* **PyQt6**: 데스크톱 GUI 프레임워크
* **watchdog**: 파일 시스템 모니터링 라이브러리
* **reportlab**: PDF 생성 라이브러리
* **requests**: HTTP 클라이언트 라이브러리

## 아키텍처

* **Observer 패턴**: 파일 감시 시스템에 적용
* **MVC 패턴**: UI와 비즈니스 로직 분리
* **워커 스레드**: 백그라운드 작업 처리로 UI 반응성 유지
* **Lazy Import**: 초기 구동 속도 최적화를 위해 무거운 모듈의 로딩 시점 분리
* **Signal/Slot**: UI 업데이트 및 비동기 이벤트 처리에 활용

## 주의사항

* `settings/settings.json` 파일에는 민감한 정보(API 키, 비밀번호 등)가 포함될 수 있으므로 Git에 커밋하지 마세요.
* 로그 파일은 `data/logs/` 디렉토리에 저장되며 Git에서 제외됩니다.
* 생성된 PDF 리포트는 `data/reports/` 디렉토리에 저장됩니다.

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

```