@echo off
REM ===========================================================================
REM  Vidora - opens the app.  This is what the Desktop shortcut points at.
REM
REM  Author:   Jay Kadam ^<kadamjay100@gmail.com^>
REM  License:  MIT - see LICENSE
REM
REM  Named Start-Vidora rather than Vidora so it cannot collide with
REM  vidora.bat on Windows, where filenames are case-insensitive.
REM ===========================================================================

setlocal
title Vidora
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo   Vidora is not set up yet in this folder.
    echo   Run Vidora-Setup.bat first.
    echo.
    pause
    exit /b 1
)

echo.
echo   Starting Vidora...  it will open at http://localhost:8501
echo   Close this window to stop it.
echo.

".venv\Scripts\python.exe" -m streamlit run vidora_ui.py --server.headless false --browser.gatherUsageStats false

if not "%ERRORLEVEL%"=="0" (
    echo.
    echo   Vidora stopped unexpectedly.
    echo.
    pause
)

endlocal
