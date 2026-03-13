@echo off
REM Setup script for SnapAI using standard Python venv

echo Setting up SnapAI virtual environment...

REM Prefer Windows Python Launcher (py.exe) to avoid Conda Python.
py -3 -V >nul 2>nul
if errorlevel 1 (
    REM Fallback to python on PATH
    where python >nul 2>nul
    if errorlevel 1 (
        echo Error: python is not installed or not in PATH.
        echo Install Python from python.org recommended, or enable the Windows py launcher.
        pause
        exit /b 1
    )
    echo Warning: py launcher not found; using "python" from PATH.
    python -m venv .venv
) else (
    echo Using Windows py launcher to create .venv...
    py -3 -m venv .venv
)

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
echo 2. Run the application: python main.py  ^(or run_snapai.bat^)
echo
echo Tip: if you have Conda installed, do NOT run from a conda prompt.
echo      Use the included run scripts to force .venv:
echo      - run_snapai.bat  ^(full app: server + overlay^)
echo      - run_server.bat  ^(server only^)
echo ------------------------------------------------
pause
