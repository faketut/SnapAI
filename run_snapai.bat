@echo off
setlocal

REM Run full SnapAI (process manager: server + overlay) using project-local .venv.

if not exist ".venv\Scripts\python.exe" (
  echo Error: .venv not found.
  echo Run: setup_venv.bat
  exit /b 1
)

".venv\Scripts\python.exe" main.py
