<#
    Vidora - launcher for Windows PowerShell.

    Author:   Jay Kadam <kadamjay100@gmail.com>
    License:  MIT - see LICENSE

    PowerShell will not run scripts by default. Allow local ones once with:
        Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

    Then add a permanent shortcut to your profile ($PROFILE):
        Set-Alias vidora "C:\full\path\to\YT_Downloader\vidora.ps1"
#>

$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $dir ".venv\Scripts\python.exe"

if (Test-Path $venv) {
    $py = $venv
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $py = "python"
} else {
    Write-Error "Vidora: no Python interpreter found on PATH."
    exit 1
}

& $py (Join-Path $dir "vidora.py") @args
exit $LASTEXITCODE
