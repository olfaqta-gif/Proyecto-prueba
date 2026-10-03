@echo off
cd /d "%~dp0"
chcp 65001 >nul
where py >nul 2>nul && (py herramientas\instalar_videos.py) || (python herramientas\instalar_videos.py)
echo.
pause
