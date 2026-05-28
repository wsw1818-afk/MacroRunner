@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo Building MacroRunner security-PC variants...
py -3.10 build_security_pc.py
if errorlevel 1 goto :error

echo.
echo Build complete.
echo Outputs:
echo   D:\OneDrive\코드작업\결과물\MacroRunner\MacroRunner.exe
echo   D:\OneDrive\코드작업\결과물\MacroRunner\MacroRunner_security_unsigned.exe
echo   D:\OneDrive\코드작업\결과물\MacroRunner\MacroRunner_security_folder
exit /b 0

:error
echo.
echo Build failed.
exit /b 1
