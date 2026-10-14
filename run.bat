@echo off
cd /d "%~dp0"
title Vortex Media Studio - Local Video & Audio Suite
echo ========================================================
echo   Launching Vortex Media Studio...
echo   Local Video and Audio Trimming, Conversion & Extraction
echo ========================================================
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.9 or newer and add it to PATH.
    pause
    exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo FFmpeg was not found. Install FFmpeg and add it to PATH.
    pause
    exit /b 1
)
where ffprobe >nul 2>nul
if errorlevel 1 (
    echo FFprobe was not found. Install FFmpeg and add it to PATH.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)
if errorlevel 1 (
    echo Could not create the local Python environment.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" app.py
pause
