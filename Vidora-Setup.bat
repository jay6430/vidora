@echo off
REM ===========================================================================
REM  Vidora - Windows installer.  Just double-click this file.
REM
REM  Author:   Jay Kadam ^<kadamjay100@gmail.com^>
REM  License:  MIT - see LICENSE
REM
REM  Downloads the installer to a real file and runs it with -File rather than
REM  piping it in. Piped scripts share the console's input handle, which makes
REM  tools like winget and pip stop and wait for a keypress halfway through.
REM ===========================================================================

setlocal
title Vidora Setup

set "PS1=%TEMP%\vidora-install.ps1"
set "URL=https://raw.githubusercontent.com/jay6430/vidora/main/install.ps1"

echo.
echo   Getting the Vidora installer...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri '%URL%' -OutFile '%PS1%' -UseBasicParsing } catch { exit 1 }"

if not exist "%PS1%" (
    echo.
    echo   Could not download the installer.
    echo   Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

REM -File gives the script its own stdin, so nothing pauses for a keypress.
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"

set "CODE=%ERRORLEVEL%"
del "%PS1%" >nul 2>&1

if not "%CODE%"=="0" (
    echo.
    echo   Setup did not finish. See the message above.
    echo.
    pause
)

endlocal
exit /b %CODE%
