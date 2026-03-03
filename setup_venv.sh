#!/bin/bash
# Setup script for SnapAI using standard Python venv

echo "Setting up SnapAI virtual environment..."

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

# Check for python3-venv (common issue on Ubuntu/Debian)
if ! python3 -m venv --help &> /dev/null
then
    echo "Error: python3-venv is not installed."
    echo "Please run: sudo apt update && sudo apt install python3-venv"
    exit 1
fi

# Create virtual environment (remove existing if it's broken)
if [ -d ".venv" ] && [ ! -f ".venv/bin/activate" ]; then
    echo "Existing .venv is broken, recreating..."
    rm -rf .venv
fi
python3 -m venv .venv

# Activate virtual environment and install dependencies
source .venv/bin/activate
pip install --upgrade pip

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found."
fi

echo "------------------------------------------------"
echo "Setup complete! To start SnapAI:"
echo "1. Activate the environment: source .venv/bin/activate"
echo "2. Run the application: python3 main.py"
echo "------------------------------------------------"
