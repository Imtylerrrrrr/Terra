@echo off
chcp 65001 >nul
REM Terra 발표·점검본 런처 — 레포 루트에서 로컬 서버를 띄우고 폰 프레임(app.html)을 연다.
REM frontend/presentation/ = 원본 frontend/demo/ 의 복사본 + 백엔드 라이브 연동(/compute·/extract·/campus).
REM 원본 demo·start-demo.bat 는 건드리지 않는다. %~dp0 = 이 .bat 폴더(=레포 루트).
cd /d "%~dp0"

set "PORT=8013"
set "URL=http://localhost:%PORT%/frontend/presentation/app.html"

echo ============================================
echo   Terra — 발표/점검본 (백엔드 라이브)
echo   서버 폴더 : %~dp0
echo   주소      : %URL%
echo ============================================
echo.
echo 폰 프레임으로 로그인 화면이 열립니다. (백엔드 라이브 API 호출)
echo 이 창을 닫으면 서버가 종료됩니다.
echo.

REM 서버가 뜰 시간을 잠깐 준 뒤 브라우저를 연다(백그라운드).
start "" cmd /c "timeout /t 2 >nul & start """" ""%URL%"""

REM 파이썬 정적 서버를 포그라운드로 실행(창=서버).
python -m http.server %PORT% 2>nul || py -m http.server %PORT%
