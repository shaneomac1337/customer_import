@echo off
title Bulk Customer Import GUI Launcher

echo ============================================================
echo BULK CUSTOMER IMPORT GUI LAUNCHER
echo ============================================================
echo.

cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.7+ and try again.
    echo.
    pause
    exit /b 1
)

echo Python found!
echo.

echo Launching GUI application...
python launch_gui.py

echo.
echo GUI application closed.
pause