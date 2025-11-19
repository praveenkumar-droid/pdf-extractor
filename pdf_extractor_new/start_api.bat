@echo off
title PDF Extractor API Server

echo.
echo ========================================
echo   PDF Extractor API Server
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from python.org
    pause
    exit /b 1
)
python --version

echo.
echo [2/3] Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo [3/3] Starting API server...
echo.
echo ========================================
echo   Server will start in a few seconds
echo ========================================
echo.
echo Once you see "Uvicorn running on...", the server is ready!
echo.
echo Then you can:
echo   1. Open web_ui.html in your browser
echo   2. Go to http://localhost:8000/docs for API docs
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

python start_api.py

pause
