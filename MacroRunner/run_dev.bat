@echo off
echo ============================================
echo MacroRunner v2.0 - 개발 모드
echo ============================================

REM 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 앱 실행
python -m src.main

pause
