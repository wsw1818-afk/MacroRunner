@echo off
setlocal
echo ============================================
echo MacroRunner v2.0 빌드
echo ============================================

REM 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Python 실행기 확인
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python을 찾을 수 없습니다.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3.10"
) else (
    set "PYTHON_CMD=python"
)

REM 의존성 설치
echo 의존성 설치 중...
%PYTHON_CMD% -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo.
    echo 의존성 설치 실패.
    pause
    exit /b 1
)

%PYTHON_CMD% -m pip install pyinstaller -q
if errorlevel 1 (
    echo.
    echo PyInstaller 설치 실패.
    pause
    exit /b 1
)

REM 빌드 실행
echo.
echo 빌드 시작...
%PYTHON_CMD% build.py
if errorlevel 1 (
    echo.
    echo 빌드 실패.
    pause
    exit /b 1
)

echo.
echo 빌드가 완료되었습니다.
echo 결과물: 결과물\MacroRunner\MacroRunner.exe
echo.
pause
