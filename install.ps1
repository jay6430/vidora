<#
    Vidora - one-command setup and launcher for Windows.

    Author:   Jay Kadam <kadamjay100@gmail.com>
    License:  MIT - see LICENSE

    Installs everything Vidora needs into a self-contained virtualenv inside
    this folder, then opens the app. Safe to run again any time: it skips
    whatever is already in place and simply relaunches.

    Run this one line in PowerShell:

      irm https://raw.githubusercontent.com/jay6430/vidora/main/install.ps1 | iex

    Or, once you have the repo:  .\install.ps1
#>

$ErrorActionPreference = "Stop"

$RepoUrl     = "https://github.com/jay6430/vidora.git"
$ZipUrl      = "https://github.com/jay6430/vidora/archive/refs/heads/main.zip"
$RepoDirName = "vidora"

# ---------------------------------------------------------------- appearance

function Write-Step { param($m) Write-Host "  . $m" -ForegroundColor DarkGray }
function Write-Good { param($m) Write-Host "  + $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Host "  ! $m" -ForegroundColor Yellow }
function Write-Fail {
    param($m)
    Write-Host ""
    Write-Host "  Error  $m" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Show-Banner {
    Write-Host ""
    Write-Host "  +----------------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host "  |  " -ForegroundColor DarkGray -NoNewline
    Write-Host "VIDORA" -ForegroundColor Cyan -NoNewline
    Write-Host "  -  HD video downloads, with the sound included  |" -ForegroundColor DarkGray
    Write-Host "  +----------------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host "                        (c) 2026 Jay Kadam  -  MIT setup" -ForegroundColor DarkGray
    Write-Host "    Thanks to Ishan Mistry, whose idea set Vidora in motion." -ForegroundColor DarkGray
    Write-Host ""
}

Show-Banner

# ---------------------------------------------------------------- locate repo

$dir = $null
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "vidora.py"))) {
    $dir = $PSScriptRoot
}

if (-not $dir) {
    $target = Join-Path (Get-Location) $RepoDirName

    if (Test-Path (Join-Path $target "vidora.py")) {
        # Already downloaded before. Update it if git is available, otherwise
        # just use what is there.
        if ((Test-Path (Join-Path $target ".git")) -and
            (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Step "Updating existing copy in $target"
            git -C $target pull --ff-only --quiet 2>$null
        } else {
            Write-Step "Using existing copy in $target"
        }
    }
    elseif (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Step "Downloading Vidora into $target"
        git clone --quiet --depth 1 $RepoUrl $target 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Fail "Could not download Vidora from $RepoUrl" }
    }
    else {
        # No git, and no need for it - fetch the ZIP that GitHub publishes.
        # Windows has had Expand-Archive built in since PowerShell 5.
        Write-Step "Downloading Vidora (no git needed)..."
        $zip = Join-Path $env:TEMP "vidora-main.zip"
        $tmp = Join-Path $env:TEMP "vidora-extract"

        try {
            Remove-Item $zip, $tmp -Recurse -Force -ErrorAction SilentlyContinue
            $ProgressPreference = "SilentlyContinue"   # the bar slows this hugely
            Invoke-WebRequest -Uri $ZipUrl -OutFile $zip -UseBasicParsing
            Expand-Archive -Path $zip -DestinationPath $tmp -Force
        } catch {
            Write-Fail "Could not download Vidora.`n          Check your internet connection, then try again.`n          $($_.Exception.Message)"
        }

        $extracted = Join-Path $tmp "vidora-main"
        if (-not (Test-Path (Join-Path $extracted "vidora.py"))) {
            Write-Fail "The download did not contain what was expected. Please try again."
        }

        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Copy-Item -Path (Join-Path $extracted "*") -Destination $target -Recurse -Force
        Remove-Item $zip, $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Write-Good "Downloaded"
    }

    $dir = $target
}

Set-Location $dir
Write-Good "Project folder: $dir"

# ---------------------------------------------------------------- python

$py = $null
foreach ($candidate in @("python", "python3", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $ok = & $candidate -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $candidate; break }
    }
}

if (-not $py) {
    Write-Fail @"
Python 3.8 or newer is required.
          Install it with:  winget install Python.Python.3.12
          Then close this window, open a new PowerShell, and run this again.
"@
}
Write-Good "Python: $(& $py --version 2>&1)"

# ---------------------------------------------------------------- ffmpeg

# ffmpeg does the merging. Prefer a system copy; fall back to the pip-packaged
# build so this never needs admin rights.
$ffmpegViaPip = $false

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Good "ffmpeg: already installed"
} elseif (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Step "Installing ffmpeg with winget (this can take a minute)..."
    winget install --id Gyan.FFmpeg --silent --accept-package-agreements `
        --accept-source-agreements 2>$null | Out-Null
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Good "ffmpeg: installed"
    } else {
        Write-Warn "winget could not add ffmpeg to this session, using the Python build"
        $ffmpegViaPip = $true
    }
} else {
    Write-Step "No system ffmpeg found, using the Python build (no admin needed)"
    $ffmpegViaPip = $true
}

# ---------------------------------------------------------------- virtualenv

$venvPy = Join-Path $dir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Step "Creating an isolated environment in .venv"
    & $py -m venv .venv
    if (-not (Test-Path $venvPy)) { Write-Fail "Could not create a virtualenv." }
    Write-Good "Environment created"
} else {
    Write-Good "Environment: already set up"
}

# ---------------------------------------------------------------- packages

Write-Step "Installing packages (yt-dlp, streamlit)..."
& $venvPy -m pip install --quiet --upgrade pip 2>$null | Out-Null
& $venvPy -m pip install --quiet --upgrade -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Could not install the Python packages. Check your internet connection."
}

if ($ffmpegViaPip) {
    & $venvPy -m pip install --quiet imageio-ffmpeg
    if ($LASTEXITCODE -ne 0) { Write-Fail "Could not install ffmpeg." }
}

Write-Good "Packages installed"

# ---------------------------------------------------------------- verify

& $venvPy -c "import yt_dlp, streamlit" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Something did not install correctly. Delete the .venv folder and run this again."
}

& $venvPy -c "import vidora, sys; sys.exit(0 if vidora.find_ffmpeg() else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "ffmpeg could not be found even after setup. Install it manually and re-run."
}

Write-Good "Everything checks out"

# ---------------------------------------------------------------- launch

Write-Host ""
Write-Host "  Starting Vidora..." -NoNewline
Write-Host "  it will open in your browser at " -ForegroundColor DarkGray -NoNewline
Write-Host "http://localhost:8501" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C in this window to stop it." -ForegroundColor DarkGray
Write-Host ""

& $venvPy -m streamlit run vidora_ui.py `
    --server.headless false `
    --browser.gatherUsageStats false
