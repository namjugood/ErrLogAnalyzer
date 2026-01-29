@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Git 초기화 중...
git init

echo 원격 저장소 추가 중...
git remote add origin https://github.com/namjugood/ErrLogAnalyzer.git

echo 파일 추가 중...
git add .

echo 커밋 중...
git commit -m "Initial commit: ErrLogAnalyzer 프로젝트"

echo 푸시 중...
git branch -M main
git push -u origin main

echo 완료!
pause
