@echo off
chcp 65001 >nul
REM Terra 데모 런처 — 레포 루트에서 로컬 서버를 띄우고 로그인 화면을 연다.
REM %~dp0 = 이 .bat 이 있는 폴더(=레포 루트). 한글 경로도 안전하게 처리됨.
cd /d "%~dp0"

set "PORT=8012"
REM app.html = 폰 프레임 셸(데모를 모바일 화면처럼 감쌈). 데모 본체는 그 안 iframe.
set "URL=http://localhost:%PORT%/frontend/demo/app.html"

echo ============================================
echo   Terra Demo
echo   서버 폴더 : %~dp0
echo   주소      : %URL%
echo ============================================
echo.
echo 브라우저가 로그인 화면으로 열립니다.
echo 이 창을 닫으면 서버가 종료됩니다.
echo.

REM 서버가 뜰 시간을 잠깐 준 뒤 브라우저를 연다(백그라운드).
start "" cmd /c "timeout /t 2 >nul & start """" ""%URL%"""

REM 파이썬 정적 서버를 포그라운드로 실행(창=서버).
python -m http.server %PORT% 2>nul || py -m http.server %PORT%
