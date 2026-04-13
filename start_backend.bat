@echo off
cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\czc\miniconda3\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python not found: %PYTHON_EXE%
    pause
    exit /b 1
)

echo ==============================
echo Select profile:
echo 1 - AI
echo 2 - OPS
echo ==============================
set /p GOODJOB_PROFILE_CHOICE=Enter 1 or 2: 

if "%GOODJOB_PROFILE_CHOICE%"=="1" goto profile_ai
if "%GOODJOB_PROFILE_CHOICE%"=="2" goto profile_ops

echo Invalid input. Please enter 1 or 2.
pause
exit /b 1

:profile_ai
set "GOODJOB_PROFILE=ai"
set "GOODJOB_PROFILE_LABEL=AI"
goto start_backend

:profile_ops
set "GOODJOB_PROFILE=ops"
set "GOODJOB_PROFILE_LABEL=OPS"
goto start_backend

:start_backend
echo.
echo Starting goodjob backend... [%GOODJOB_PROFILE_LABEL%]
"%PYTHON_EXE%" main.py

echo.
echo Backend exited.
pause
