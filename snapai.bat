@echo off
REM Launcher for SnapAI on Windows

set DIR=%~dp0
cd /d %DIR%

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python main.py
pause
