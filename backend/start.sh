#!/bin/bash
# Quick start script for JDK Compliance Scanner Backend
# Run without Docker - uses local Python and SQLite

set -e

echo "========================================="
echo "JDK Compliance Scanner Backend"
echo "Starting application (without Docker)..."
echo "========================================="

# Check if we're in the backend directory
if [ ! -f "run.py" ]; then
    echo "Error: Please run this script from the backend/ directory"
    echo "Usage: cd backend && ./start.sh"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created at .venv"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from env.example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "Created .env file. Please edit it with your configuration before continuing."
        echo "At minimum, set a secure JWT_SECRET_KEY."
        exit 1
    else
        echo "Error: env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Check if dependencies are installed in venv
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Dependencies not installed. Installing into virtual environment..."
    pip install -r requirements.txt
fi

# Check if database exists, if not initialize it
if [ ! -f "data/compliance.db" ]; then
    echo "Database not found. Initializing database..."
    python scripts/init_db.py
else
    echo "Database found at data/compliance.db"
fi

echo ""
echo "Starting server..."
echo "API will be available at: http://localhost:8000"
echo "Swagger docs at: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
python run.py

