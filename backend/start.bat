@echo off
REM Quick start script for JDK Compliance Scanner Backend (Windows)
REM Run without Docker - uses local Python and SQLite

echo =========================================
echo JDK Compliance Scanner Backend
echo Starting application (without Docker)...
echo =========================================

REM Check if we're in the backend directory
if not exist "run.py" (
    echo Error: Please run this script from the backend\ directory
    echo Usage: cd backend ^&^& start.bat
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH. Please install Python 3.8 or higher.
    exit /b 1
)

echo Checking Python installation...
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created at .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo Warning: .env file not found. Creating from env.example...
    if exist "env.example" (
        copy env.example .env >nul
        echo Created .env file. Please edit it with your configuration before continuing.
        echo At minimum, set a secure JWT_SECRET_KEY.
        exit /b 1
    ) else (
        echo Error: env.example not found. Cannot create .env file.
        exit /b 1
    )
)

REM Check if dependencies are installed in venv
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Dependencies not installed. Installing into virtual environment...
    pip install -r requirements.txt
)

REM Check if database exists, if not initialize it
if not exist "data\compliance.db" (
    echo Database not found. Initializing database...
    python scripts\init_db.py
) else (
    echo Database found at data\compliance.db
)

echo.
echo Starting server...
echo API will be available at: http://localhost:8000
echo Swagger docs at: http://localhost:8000/docs
echo Press Ctrl+C to stop the server
echo.

REM Run the application
python run.py

