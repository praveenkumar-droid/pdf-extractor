@echo off
echo ============================================================
echo PDF EXTRACTION SYSTEM - COMPLETE LOCAL RUNNER
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if pdfplumber is installed
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install pdfplumber
)

REM Check arguments
if "%~1"=="" (
    echo Usage: run_system.bat "path\to\your\file.pdf" [output_path]
    echo.
    echo Examples:
    echo   run_system.bat "input\sample.pdf"
    echo   run_system.bat "input\sample.pdf" "output\result.txt"
    echo   run_system.bat "input\sample.pdf" --llm
    echo.
    pause
    exit /b 1
)

REM Run the extraction
python run_complete_system.py %*

echo.
pause
