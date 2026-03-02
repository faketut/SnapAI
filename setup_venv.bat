@echo off
REM Setup script for SnapAI using standard Python venv

echo Setting up SnapAI virtual environment...

REM Check if python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: python is not installed or not in PATH.
    pause
    exit /b 1
)

REM Create virtual environment
python -m venv .venv

REM Activate virtual environment and install dependencies
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo Warning: requirements.txt not found.
)

echo ------------------------------------------------
echo Setup complete! To start SnapAI:
echo 1. Activate the environment: .venv\Scripts\activate
echo 2. Run the application: python main.py
echo ------------------------------------------------
pause
