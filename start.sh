#!/bin/bash

# Exit on error
set -e

# --- Configuration ---
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
PYTHON_EXEC="$VENV_DIR/bin/python"
PIP_EXEC="$VENV_DIR/bin/pip"
APP_SCRIPT="run.py"

# --- Functions ---

# Function to print messages
function log {
    echo "--- $1 ---"
}

# Function to check if a command exists
function command_exists {
    command -v "$1" >/dev/null 2>&1
}

# --- Main Script ---

# 1. Check for python3
if ! command_exists python3; then
    log "Error: python3 is not installed or not in your PATH. Please install Python 3.8+."
    exit 1
fi

# 2. Check for virtual environment
if [ ! -d "$VENV_DIR" ]; then
    log "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
    log "Virtual environment created."
fi

# 3. Check for and install/update dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    log "Installing/updating dependencies from $REQUIREMENTS_FILE..."
    "$PIP_EXEC" install -r "$REQUIREMENTS_FILE"
    log "Dependencies are up-to-date."
else
    log "Warning: $REQUIREIMENTS_FILE not found. Skipping dependency installation."
fi

# 4. Run the application
log "Starting the AI Sandbox application..."
"$PYTHON_EXEC" "$APP_SCRIPT"
