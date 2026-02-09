@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo ErrLogAnalyzer 고속 실행 빌드 (Onedir)
echo ========================================
echo.

REM 현재 디렉토리 저장
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 빌드 디렉토리 설정
set BUILD_DIR=dist
set DIST_DIR=dist\ErrLogAnalyzer

REM 날짜/시간 생성
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set mytime=%mytime: =0%
set ARCHIVE_NAME=ErrLogAnalyzer_v%mydate%_%mytime%

echo [1/5] 이전 빌드 파일 정리...
if exist "dist" (
    echo 기존 dist 폴더 삭제 중...
    rmdir /s /q "dist"
)
if exist "build" (
    echo 기존 build 폴더 삭제 중...
    rmdir /s /q "build"
)

echo.
echo [2/5] 환경 확인...
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python을 찾을 수 없습니다.
    pause
    exit /b 1
)

echo.
echo [3/5] PyInstaller 빌드 실행...
python -m PyInstaller --clean ErrLogAnalyzer.spec
if errorlevel 1 (
    echo [오류] 빌드 실패!
    pause
    exit /b 1
)

echo.
echo [4/5] 설정 및 데이터 폴더 구성...

REM [오류 진단 로직 - 괄호 문자 제거 수정됨]
if not exist "%DIST_DIR%" (
    if exist "dist\ErrLogAnalyzer.exe" (
        echo.
        echo [!!! 설정 오류 감지 !!!]
        echo ErrLogAnalyzer.spec 파일이 여전히 '단일 파일 Onefile' 모드입니다.
        echo spec 파일 내용을 위에서 제공된 'COLLECT'가 포함된 코드로 수정해주세요.
    ) else (
        echo [오류] 빌드 결과물 폴더가 생성되지 않았습니다! - 원인 불명
    )
    pause
    exit /b 1
)

REM settings 폴더 및 템플릿 생성
if not exist "%DIST_DIR%\settings" mkdir "%DIST_DIR%\settings"

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

REM data 폴더 구조 생성
if not exist "%DIST_DIR%\data\logs" mkdir "%DIST_DIR%\data\logs"
if not exist "%DIST_DIR%\data\reports" mkdir "%DIST_DIR%\data\reports"

REM README 파일 복사
if exist "README.md" (
    copy /Y "README.md" "%DIST_DIR%\" >nul
    echo README 파일 복사 완료
)

echo.
echo [5/5] 7-Zip으로 압축 (내부 파일만 압축)...

set "SEVEN_ZIP=C:\Program Files\7-Zip\7z.exe"
if not exist "%SEVEN_ZIP%" (
    set "SEVEN_ZIP=C:\Program Files (x86)\7-Zip\7z.exe"
)

if exist "%SEVEN_ZIP%" (
    pushd "%DIST_DIR%"
    "%SEVEN_ZIP%" a -t7z "..\..\%ARCHIVE_NAME%.7z" *
    popd
    if errorlevel 1 (
        echo [오류] 압축 실패!
    ) else (
        echo 압축 완료: %ARCHIVE_NAME%.7z
    )
) else (
    where 7z >nul 2>&1
    if errorlevel 1 (
        echo [경고] 7-Zip을 찾을 수 없습니다. 수동으로 압축해주세요.
        echo 대상 폴더: %DIST_DIR%
    ) else (
        pushd "%DIST_DIR%"
        7z a -t7z "..\..\%ARCHIVE_NAME%.7z" *
        popd
        echo 압축 완료: %ARCHIVE_NAME%.7z
    )
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo 결과물 위치: %DIST_DIR%
echo 압축 파일: %ARCHIVE_NAME%.7z
echo.
pause