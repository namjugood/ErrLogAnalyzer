# 빌드 가이드

## 빌드 전 준비사항

1. **Python 3.8 이상 설치 확인**
   ```bash
   python --version
   ```

2. **필요한 패키지 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **7-Zip 설치 (선택사항)**
   - 7-Zip이 설치되어 있으면 자동으로 압축 파일을 생성합니다.
   - 설치되지 않은 경우, 빌드 후 수동으로 압축할 수 있습니다.
   - 다운로드: https://www.7-zip.org/

## 빌드 방법

### 자동 빌드 (권장)

Windows에서 `build.bat` 파일을 더블클릭하거나 명령 프롬프트에서 실행:

```bash
build.bat
```

빌드 스크립트는 다음을 수행합니다:
1. 이전 빌드 파일 정리
2. PyInstaller 설치 확인 및 설치
3. PyInstaller로 실행 파일 빌드
4. 배포 폴더 구조 생성 및 파일 복사
5. 7-Zip으로 압축 파일 생성

### 수동 빌드

1. **PyInstaller 설치**
   ```bash
   pip install pyinstaller
   ```

2. **빌드 실행**
   ```bash
   pyinstaller --clean ErrLogAnalyzer.spec
   ```

3. **배포 폴더 준비**
   - `dist/ErrLogAnalyzer/` 폴더에 실행 파일이 생성됩니다.
   - `settings/` 폴더와 `data/` 폴더 구조를 수동으로 생성해야 합니다.

4. **압축 (선택사항)**
   ```bash
   7z a -t7z ErrLogAnalyzer_v1.0.7z dist\ErrLogAnalyzer\*
   ```

## 빌드 결과물

빌드가 완료되면 다음 구조가 생성됩니다:

```
dist/
└── ErrLogAnalyzer/
    ├── ErrLogAnalyzer.exe      # 실행 파일
    ├── settings/                # 설정 폴더
    │   └── settings.json        # 설정 파일 템플릿
    ├── data/                    # 데이터 폴더
    │   ├── logs/                # 로그 파일 저장소
    │   └── reports/             # 리포트 저장소
    └── README.md                # README 파일 (선택사항)
```

## 배포

1. **압축 파일 배포**
   - `ErrLogAnalyzer_vYYYYMMDD_HHMMSS.7z` 파일을 배포합니다.
   - 사용자는 7-Zip 또는 다른 압축 해제 도구로 압축을 풀 수 있습니다.

2. **설정 파일 구성**
   - 사용자가 `settings/settings.json` 파일을 자신의 환경에 맞게 수정해야 합니다.
   - 설정 파일 형식은 README.md를 참조하세요.

3. **실행**
   - `ErrLogAnalyzer.exe`를 더블클릭하여 실행합니다.

## 문제 해결

### 빌드 오류

- **ModuleNotFoundError**: 필요한 패키지가 설치되지 않았을 수 있습니다. `pip install -r requirements.txt` 실행
- **Font not found**: `app/assets/fonts/NanumGothic.ttf` 파일이 존재하는지 확인
- **ImportError**: spec 파일의 `hiddenimports`에 누락된 모듈이 있는지 확인

### 실행 오류

- **폰트 관련 오류**: 실행 파일과 같은 위치에 `app/assets/fonts/` 폴더가 있는지 확인
- **설정 파일 오류**: `settings/settings.json` 파일이 올바르게 구성되었는지 확인
- **경로 오류**: 상대 경로를 사용하는 경우, 실행 파일 위치를 기준으로 경로가 올바른지 확인

## 빌드 최적화

### 파일 크기 줄이기

- UPX 압축 사용 (spec 파일에서 `upx=True`로 설정됨)
- 불필요한 모듈 제외 (`excludes` 리스트에 추가)

### 실행 속도 향상

- `noarchive=False`로 설정하여 단일 실행 파일 생성
- 디버그 모드 비활성화 (`debug=False`)

## 추가 참고사항

- 빌드된 실행 파일은 Windows Defender나 다른 안티바이러스에서 경고를 표시할 수 있습니다. 이는 PyInstaller로 빌드된 파일의 일반적인 현상입니다.
- 코드 서명을 원하는 경우, spec 파일의 `codesign_identity`를 설정하세요.
- 아이콘을 추가하려면 `.ico` 파일을 생성하고 spec 파일의 `icon` 경로를 지정하세요.
