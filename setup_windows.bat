@echo off
setlocal
cd /d "%~dp0"

echo Checking Python version (3.12 or newer is required)...
py -3 -c "import sys; print('Using Python', sys.version.split()[0]); raise SystemExit(sys.version_info < (3, 12))"
if errorlevel 1 goto :python_version_error

echo [1/5] Creating virtual environment...
py -3 -m venv .venv
if errorlevel 1 goto :fail
call ".venv\Scripts\activate.bat"

".venv\Scripts\python.exe" -c "import sys; print('Virtual environment:', sys.version.split()[0]); raise SystemExit(sys.version_info < (3, 12))"
if errorlevel 1 goto :python_version_error

echo [2/5] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [3/5] Installing Playwright Chromium...
python -m playwright install chromium
if errorlevel 1 goto :fail

echo [4/5] Preparing TaskManager database and test fixtures...
pushd TaskManager
python manage.py migrate --noinput
if errorlevel 1 (popd & goto :fail)
python manage.py seed_qa
if errorlevel 1 (popd & goto :fail)
popd

echo [5/5] Preparing BugPilot database and test cases...
pushd BugPilot
python manage.py migrate --noinput
if errorlevel 1 (popd & goto :fail)
python manage.py seed_demo
if errorlevel 1 (popd & goto :fail)
popd

echo Setup complete. Next, run run_apps_windows.bat.
pause
exit /b 0

:python_version_error
echo Python 3.12 or newer is required because the project uses Django 6.
echo Install Python 3.12 or 3.13, then run setup_windows.bat again.
pause
exit /b 1

:fail
echo Setup failed. Review the error above.
pause
exit /b 1
