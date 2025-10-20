@echo off
REM ============================================================
REM Simple Ngrok Starter - Run from Anaconda Prompt
REM ============================================================

echo ========================================
echo Starting Django with Ngrok
echo ========================================
echo.

REM Check if we're in the right environment
python --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    echo Please make sure you're in the Ldjango conda environment
    echo Run: conda activate Ldjango
    pause
    exit /b 1
)

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ngrok not found!
    echo Download from: https://ngrok.com/download
    echo Place ngrok.exe in this folder
    pause
    exit /b 1
)

echo [1/2] Starting Django server...
start "Django Server" cmd /k python manage.py runserver 0.0.0.0:8000

echo [2/2] Waiting 5 seconds for Django to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Copy the Forwarding URL from ngrok!
echo Example: https://abc123.ngrok-free.app
echo ========================================
echo.

ngrok http 8000

REM Cleanup
taskkill /FI "WINDOWTITLE eq Django Server*" /T /F >nul 2>nul
echo.
echo Stopped!

