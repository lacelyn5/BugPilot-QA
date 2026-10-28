@echo off
cd /d "%~dp0BugPilot"
call "%~dp0.venv\Scripts\activate.bat"
python manage.py migrate --noinput
if errorlevel 1 (pause & exit /b 1)
python manage.py runserver 127.0.0.1:8000
