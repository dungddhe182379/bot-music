@echo off
title Discord Music Bot
cd /d "%~dp0"

:: Them FFmpeg vao PATH neu chua co
set "FFMPEG_DIR=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin"
if exist "%FFMPEG_DIR%" (
    set "PATH=%FFMPEG_DIR%;%PATH%"
)

echo ========================================================
echo           DANG KHOI DONG DISCORD MUSIC BOT
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Khong tim thay moi truong ao .venv!
    pause
    exit /b 1
)

.\.venv\Scripts\python.exe main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [THONG BAO] Bot da dung lai.
)
pause
