@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing. Run setup_windows.bat first.
  pause
  exit /b 1
)

start "TaskManager" cmd /k call "%~dp0run_taskmanager_windows.bat"
start "BugPilot" cmd /k call "%~dp0run_bugpilot_windows.bat"

echo TaskManager: http://127.0.0.1:8001/
echo BugPilot:    http://127.0.0.1:8000/
echo.
echo To run integration tests, open a third terminal:
echo cd BugPilot
echo ..\.venv\Scripts\python.exe -m pytest automation -v
pause
