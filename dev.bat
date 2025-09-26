@echo off
echo Starting SnapAI Development Server with Hot Reload...
echo.
echo Mobile Client: http://localhost:8080/
echo WebSocket: ws://localhost:8765
echo Hot Reload: Enabled
echo.
echo Press Ctrl+C to stop the server
echo.

python dev_server.py --debug

pause
