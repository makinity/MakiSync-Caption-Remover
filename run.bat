@echo off
title Caption Remover Studio
cd /d "%~dp0"
echo ========================================================
echo        Starting Caption Remover Studio...
echo ========================================================
call .venv\Scripts\activate
.venv\Scripts\python.exe -m app.web
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error.
    pause
)
