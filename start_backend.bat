@echo off
cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\czc\miniconda3\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python not found: %PYTHON_EXE%
    pause
    exit /b 1
)

echo Starting goodjob backend...
"%PYTHON_EXE%" main.py

echo.
echo Backend exited.
pause
