@echo off
echo ============================================
echo MacroRunner v2.0 빌드
echo ============================================

REM 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 의존성 설치
echo 의존성 설치 중...
pip install -r requirements.txt -q
pip install pyinstaller -q

REM 빌드 실행
echo.
echo 빌드 시작...
python build.py

echo.
echo 빌드가 완료되었습니다.
echo 결과물: dist\MacroRunner\MacroRunner.exe
echo.
pause
