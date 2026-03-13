@echo off
echo ============================================
echo MacroRunner v2.0 - 테스트 실행
echo ============================================

REM 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 의존성 설치
pip install pytest pytest-cov -q

REM 테스트 실행
echo.
echo 테스트 실행 중...
python -m pytest tests/ -v --tb=short

echo.
pause
