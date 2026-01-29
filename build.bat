@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo ErrLogAnalyzer 빌드 스크립트
echo ========================================
echo.

REM 현재 디렉토리 저장
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 빌드 디렉토리 설정
set BUILD_DIR=dist
set DIST_DIR=dist\ErrLogAnalyzer

REM 날짜/시간 생성 (호환성 좋은 방법)
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set mytime=%mytime: =0%
set ARCHIVE_NAME=ErrLogAnalyzer_v%mydate%_%mytime%

echo [1/5] 이전 빌드 파일 정리...
if exist "%BUILD_DIR%" (
    echo 기존 빌드 폴더 삭제 중...
    rmdir /s /q "%BUILD_DIR%"
)
if exist "build" (
    echo 기존 build 폴더 삭제 중...
    rmdir /s /q "build"
)

echo.
echo [2/5] Python 설치 확인...
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 없습니다!
    echo Python을 설치하거나 PATH에 추가해주세요.
    pause
    exit /b 1
)
python --version

echo.
echo PyInstaller 설치 확인...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller가 설치되어 있지 않습니다. 설치 중...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [오류] PyInstaller 설치 실패!
        pause
        exit /b 1
    )
) else (
    echo PyInstaller가 이미 설치되어 있습니다.
)

echo.
echo [3/5] PyInstaller로 빌드 실행...
python -m PyInstaller --clean ErrLogAnalyzer.spec
if errorlevel 1 (
    echo [오류] 빌드 실패!
    pause
    exit /b 1
)

echo.
echo [4/5] 배포 파일 준비...
REM dist/ErrLogAnalyzer 폴더 생성
if not exist "%DIST_DIR%" (
    mkdir "%DIST_DIR%"
)

REM 실행 파일 복사
if exist "dist\ErrLogAnalyzer.exe" (
    copy /Y "dist\ErrLogAnalyzer.exe" "%DIST_DIR%\"
    echo 실행 파일 복사 완료
) else (
    echo [오류] 실행 파일을 찾을 수 없습니다!
    pause
    exit /b 1
)

REM settings 폴더 템플릿 생성
if not exist "%DIST_DIR%\settings" (
    mkdir "%DIST_DIR%\settings"
)
REM settings.json 템플릿 파일 생성
(
echo {
echo     "channels": [],
echo     "log_path": "data/logs",
echo     "retention_days": "30",
echo     "dify_config": {
echo         "url": "https://api.dify.ai/v1/workflows/run",
echo         "authorization": "Bearer YOUR_API_KEY",
echo         "content_type": "application/json"
echo     }
echo }
) > "%DIST_DIR%\settings\settings.json"
echo 설정 파일 템플릿 생성 완료

REM data 폴더 구조 생성
if not exist "%DIST_DIR%\data" (
    mkdir "%DIST_DIR%\data"
)
if not exist "%DIST_DIR%\data\logs" (
    mkdir "%DIST_DIR%\data\logs"
)
if not exist "%DIST_DIR%\data\reports" (
    mkdir "%DIST_DIR%\data\reports"
)

REM README 파일 복사 (선택사항)
if exist "README.md" (
    copy /Y "README.md" "%DIST_DIR%\"
    echo README 파일 복사 완료
)

echo.
echo [5/5] 7-Zip으로 압축...
REM 7-Zip 경로 확인
set "SEVEN_ZIP=C:\Program Files\7-Zip\7z.exe"
if not exist "%SEVEN_ZIP%" (
    set "SEVEN_ZIP=C:\Program Files (x86)\7-Zip\7z.exe"
)
if not exist "%SEVEN_ZIP%" (
    REM 7z가 PATH에 있는지 확인
    where 7z >nul 2>&1
    if errorlevel 1 (
        echo [경고] 7-Zip을 찾을 수 없습니다. 수동으로 압축해주세요.
        echo 압축 대상 폴더: %DIST_DIR%
        echo.
        echo 7-Zip이 설치되어 있다면 다음 명령어를 실행하세요:
        echo 7z a -t7z "%ARCHIVE_NAME%.7z" "%DIST_DIR%\*"
    ) else (
        echo 7z 명령어를 사용하여 압축 중...
        7z a -t7z "%ARCHIVE_NAME%.7z" "%DIST_DIR%\*"
        if errorlevel 1 (
            echo [오류] 압축 실패!
        ) else (
            echo 압축 완료: %ARCHIVE_NAME%.7z
        )
    )
) else (
    echo 7-Zip으로 압축 중...
    "%SEVEN_ZIP%" a -t7z "%ARCHIVE_NAME%.7z" "%DIST_DIR%\*"
    if errorlevel 1 (
        echo [오류] 압축 실패!
    ) else (
        echo 압축 완료: %ARCHIVE_NAME%.7z
    )
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo 배포 폴더: %DIST_DIR%
echo 압축 파일: %ARCHIVE_NAME%.7z
echo.
pause
