@echo off
REM Script to run API test script with virtual environment (Windows)
REM Ensures all dependencies are available from .venv

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set BACKEND_DIR=%PROJECT_ROOT%\backend
set VENV_DIR=%BACKEND_DIR%\.venv

REM Change to project root
cd /d "%PROJECT_ROOT%"
if errorlevel 1 exit /b 1

REM Check if .venv exists, if not create it
if not exist "%VENV_DIR%" (
    echo Virtual environment not found. Creating .venv...
    cd "%BACKEND_DIR%"
    python3.8 -m venv .venv
    if errorlevel 1 python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        exit /b 1
    )
    echo Virtual environment created.
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Check if requests is installed
python -c "import requests" 2>nul
if errorlevel 1 (
    echo Installing required dependencies (requests)...
    pip install requests>=2.31.0
)

REM Run the test script
cd "%PROJECT_ROOT%"
python tests\test_api.py %*

