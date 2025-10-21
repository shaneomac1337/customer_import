@echo off
title Build Bulk Customer Import Executable

echo ============================================================
echo BULK CUSTOMER IMPORT - EXECUTABLE BUILDER
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

echo Installing/upgrading PyInstaller...
pip install --upgrade pyinstaller requests
echo.

echo Starting build process...
python build_exe.py

echo.
echo Build process completed.
pause