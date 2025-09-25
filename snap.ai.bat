@echo on
setlocal enableextensions
TITLE Snap.AI Launcher

:: Resolve script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"


:: Check if conda environment exists
echo Checking for conda environment 'snap.ai'...
call conda info --envs | findstr /C:"snap.ai" > nul 2>&1
if %errorlevel% neq 0 (
    echo Creating conda environment 'snap.ai'...
    call conda create -n snap.ai python=3.8 -y
    if %errorlevel% neq 0 (
        echo Failed to create conda environment
        pause
        exit /b 1
    )
)

:: Activate environment
echo Activating conda environment...
call conda activate snap.ai
if %errorlevel% neq 0 (
    echo Failed to activate conda environment
    pause
    exit /b 1
)

:: Check if server directory exists
if not exist "%SCRIPT_DIR%server" (
    echo Server directory not found: %SCRIPT_DIR%server
    pause
    exit /b 1
)

:: Check if main.py exists
if not exist "%SCRIPT_DIR%server\main.py" (
    echo main.py not found in server directory
    pause
    exit /b 1
)

:: Start application
echo Starting application...
cd /d "%SCRIPT_DIR%server"
python main.py
set "APP_EXIT=%errorlevel%"

echo Application exited with code: %APP_EXIT%
if not "%APP_EXIT%"=="0" (
    echo Application failed
    pause
    exit /b %APP_EXIT%
)

echo Application completed successfully
pause
