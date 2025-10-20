@echo off
echo ========================================
echo Starting Django Tenant Management App
echo with Ngrok Tunnel
echo ========================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ngrok is not installed or not in PATH!
    echo.
    echo Please download ngrok from: https://ngrok.com/download
    echo After downloading:
    echo 1. Extract ngrok.exe
    echo 2. Place it in this folder OR add it to your PATH
    echo.
    pause
    exit /b 1
)

echo [1/3] Setting up environment...

REM Find conda installation
set "CONDA_PATH="
if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    set "CONDA_PATH=%USERPROFILE%\anaconda3"
) else if exist "%USERPROFILE%\Anaconda3\Scripts\activate.bat" (
    set "CONDA_PATH=%USERPROFILE%\Anaconda3"
) else if exist "C:\ProgramData\anaconda3\Scripts\activate.bat" (
    set "CONDA_PATH=C:\ProgramData\anaconda3"
) else if exist "C:\ProgramData\Anaconda3\Scripts\activate.bat" (
    set "CONDA_PATH=C:\ProgramData\Anaconda3"
)

if "%CONDA_PATH%"=="" (
    echo [ERROR] Could not find Anaconda installation!
    echo Please run this from Anaconda Prompt instead.
    pause
    exit /b 1
)

echo Found Anaconda at: %CONDA_PATH%

echo.
echo [2/3] Starting Django server on port 8000...
start "Django Server" cmd /k "call "%CONDA_PATH%\Scripts\activate.bat" Ldjango && python manage.py runserver 0.0.0.0:8000"

echo.
echo [3/3] Waiting for Django to start...
timeout /t 5 /nobreak >nul

echo.
echo Starting Ngrok tunnel...
echo.
echo ========================================
echo IMPORTANT: Copy the "Forwarding" URL from ngrok!
echo Example: https://abc123.ngrok-free.app
echo ========================================
echo.
ngrok http 8000

REM If ngrok is closed, also close Django
taskkill /FI "WINDOWTITLE eq Django Server*" /T /F >nul 2>nul

