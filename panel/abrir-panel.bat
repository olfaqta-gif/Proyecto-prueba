@echo off
cd /d "%~dp0\.."
where py >nul 2>nul && (py panel\servidor.py) || (python panel\servidor.py)
pause
