@echo off
setlocal

set "SRC=%~dp0macro_index.json"
set "DST=%LOCALAPPDATA%\MacroRunner\macros"
set "DST_FILE=%DST%\macro_index.json"
set "BACKUP_FILE=%DST%\macro_index.backup.json"

if not exist "%SRC%" (
    echo ERROR: macro_index.json was not found next to this installer.
    echo Put install_macro_update.bat and macro_index.json in the same folder.
    if /I not "%~1"=="/quiet" pause
    exit /b 1
)

if not defined LOCALAPPDATA (
    echo ERROR: LOCALAPPDATA is not defined.
    if /I not "%~1"=="/quiet" pause
    exit /b 1
)

if not exist "%DST%" (
    mkdir "%DST%"
    if errorlevel 1 (
        echo ERROR: Could not create "%DST%".
        if /I not "%~1"=="/quiet" pause
        exit /b 1
    )
)

if exist "%DST_FILE%" (
    copy /Y "%DST_FILE%" "%BACKUP_FILE%" >nul
    if errorlevel 1 (
        echo ERROR: Could not back up existing macro_index.json.
        if /I not "%~1"=="/quiet" pause
        exit /b 1
    )
)

copy /Y "%SRC%" "%DST_FILE%" >nul
if errorlevel 1 (
    echo ERROR: Could not install macro_index.json.
    if /I not "%~1"=="/quiet" pause
    exit /b 1
)

echo MacroRunner macro update installed.
echo Target: "%DST_FILE%"
echo Keep using the existing MacroRunner.exe that is already allowed on this PC.

if /I not "%~1"=="/quiet" pause
exit /b 0
