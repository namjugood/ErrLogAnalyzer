@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo ErrLogAnalyzer 빌드 스크립트 (간소화 버전)
echo ========================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python을 찾을 수 없습니다!
    echo Python이 설치되어 있고 PATH에 추가되어 있는지 확인하세요.
    pause
    exit /b 1
)

echo Python 버전:
python --version
echo.

REM PyInstaller 설치 확인 및 설치
echo [1/4] PyInstaller 확인 중...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [오류] PyInstaller 설치 실패!
        pause
        exit /b 1
    )
) else (
    echo PyInstaller가 설치되어 있습니다.
)
echo.

REM 이전 빌드 정리
echo [2/4] 이전 빌드 파일 정리 중...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo 정리 완료.
echo.

REM 빌드 실행
echo [3/4] 빌드 실행 중...
python -m PyInstaller --clean ErrLogAnalyzer.spec
if errorlevel 1 (
    echo [오류] 빌드 실패!
    pause
    exit /b 1
)
echo.

REM 배포 폴더 준비
echo [4/4] 배포 파일 준비 중...
set DIST_DIR=dist\ErrLogAnalyzer

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

REM 실행 파일 확인 및 복사
if exist "dist\ErrLogAnalyzer.exe" (
    copy /Y "dist\ErrLogAnalyzer.exe" "%DIST_DIR%\" >nul
    echo 실행 파일 준비 완료
) else (
    echo [경고] 실행 파일을 찾을 수 없습니다. dist 폴더를 확인하세요.
)

REM 폴더 구조 생성
if not exist "%DIST_DIR%\settings" mkdir "%DIST_DIR%\settings"
if not exist "%DIST_DIR%\data" mkdir "%DIST_DIR%\data"
if not exist "%DIST_DIR%\data\logs" mkdir "%DIST_DIR%\data\logs"
if not exist "%DIST_DIR%\data\reports" mkdir "%DIST_DIR%\data\reports"

REM settings.json 템플릿 생성
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

REM README 복사
if exist "README.md" (
    copy /Y "README.md" "%DIST_DIR%\" >nul
)

echo 배포 폴더 준비 완료: %DIST_DIR%
echo.

REM 7-Zip 압축 시도
echo 압축 파일 생성 시도 중...
set "SEVEN_ZIP="
if exist "C:\Program Files\7-Zip\7z.exe" set "SEVEN_ZIP=C:\Program Files\7-Zip\7z.exe"
if exist "C:\Program Files (x86)\7-Zip\7z.exe" set "SEVEN_ZIP=C:\Program Files (x86)\7-Zip\7z.exe"

if defined SEVEN_ZIP (
    set ARCHIVE_NAME=ErrLogAnalyzer_%date:~0,4%%date:~5,2%%date:~8,2%
    "%SEVEN_ZIP%" a -t7z "%ARCHIVE_NAME%.7z" "%DIST_DIR%\*" >nul
    if exist "%ARCHIVE_NAME%.7z" (
        echo 압축 완료: %ARCHIVE_NAME%.7z
    ) else (
        echo [경고] 압축 실패. 수동으로 압축해주세요.
    )
) else (
    where 7z >nul 2>&1
    if not errorlevel 1 (
        set ARCHIVE_NAME=ErrLogAnalyzer_%date:~0,4%%date:~5,2%%date:~8,2%
        7z a -t7z "%ARCHIVE_NAME%.7z" "%DIST_DIR%\*" >nul
        if exist "%ARCHIVE_NAME%.7z" (
            echo 압축 완료: %ARCHIVE_NAME%.7z
        )
    ) else (
        echo [정보] 7-Zip을 찾을 수 없습니다. 수동으로 압축해주세요.
        echo 압축 대상: %DIST_DIR%
    )
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo 배포 폴더: %DIST_DIR%
echo.
pause
