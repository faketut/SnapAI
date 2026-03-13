@echo off
setlocal

REM Run the SnapAI server using the project-local .venv interpreter.
REM This avoids Conda / global Python package mismatches.

if not exist ".venv\\Scripts\\python.exe" (
  echo Error: .venv not found.
  echo Run: setup_venv.bat
  exit /b 1
)

".venv\\Scripts\\python.exe" main.py --server
