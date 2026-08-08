@echo off
REM
REM Vidora - command line launcher for Windows.
REM
REM Author:   Jay Kadam ^<kadamjay100@gmail.com^>
REM License:  MIT - see LICENSE
REM
REM Prefers the project's own virtualenv when one exists. Put this folder on
REM your PATH and the command becomes:  vidora "URL"
REM
REM For the app with the visual picker, use Start-Vidora.bat instead.
REM
setlocal

set "DIR=%~dp0"

if exist "%DIR%.venv\Scripts\python.exe" (
    set "PY=%DIR%.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

"%PY%" "%DIR%vidora.py" %*
exit /b %errorlevel%
