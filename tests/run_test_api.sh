#!/bin/bash
# Script to run API test script with virtual environment
# Ensures all dependencies are available from .venv

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Check if .venv exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating .venv..."
    cd "$BACKEND_DIR" || exit 1
    python3.8 -m venv .venv || python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if requests is installed
if ! python -c "import requests" 2>/dev/null; then
    echo "Installing required dependencies (requests)..."
    pip install requests>=2.31.0
fi

# Run the test script
cd "$PROJECT_ROOT" || exit 1
python tests/test_api.py "$@"

