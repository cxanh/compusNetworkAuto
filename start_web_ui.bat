@echo off
cd /d "%~dp0"
python web_app.py
if errorlevel 1 pause
