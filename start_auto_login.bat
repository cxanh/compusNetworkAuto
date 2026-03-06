@echo off
cd /d "%~dp0"
python auto_login_csxy.py
if errorlevel 1 pause
