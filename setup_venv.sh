#!/bin/bash
# Setup script for SnapAI using standard Python venv

set -e

echo "Setting up SnapAI virtual environment..."

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found."
fi

echo "------------------------------------------------"
echo "Setup complete! To start SnapAI:"
echo "1. Activate the environment: source .venv/bin/activate"
echo "2. Run the application: python main.py"
echo "------------------------------------------------"
