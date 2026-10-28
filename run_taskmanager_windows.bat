@echo off
cd /d "%~dp0TaskManager"
call "%~dp0.venv\Scripts\activate.bat"
python manage.py runserver 127.0.0.1:8001
