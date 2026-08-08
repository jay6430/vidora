<#
    Vidora - setup and launcher for Windows.

    Author:   Jay Kadam <kadamjay100@gmail.com>
    License:  MIT - see LICENSE

    Installs everything Vidora needs - including Python and ffmpeg if they are
    missing - into a self-contained folder, creates a Desktop shortcut, then
    opens the app. Safe to run again: it skips what is already there.

    Normally launched by double-clicking Vidora-Setup.bat. Can also be run as:

      irm https://raw.githubusercontent.com/jay6430/vidora/main/install.ps1 | iex

    Parameters:
      -LaunchOnly   Skip setup and just start the app.
#>

param(
    [switch]$LaunchOnly
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"   # progress bars make downloads crawl

# Bumped on every change to the installer, so you can confirm at a glance that
# the machine actually fetched the newest version rather than a cached one.
$SetupVersion = "1.1.0"

$RepoUrl     = "https://github.com/jay6430/vidora.git"
$ZipUrl      = "https://github.com/jay6430/vidora/archive/refs/heads/main.zip"
$RepoDirName = "vidora"

# Python to fetch when the machine has none. 3.12 is current enough for every
# dependency and old enough to have wheels for everything.
$PyVersion   = "3.12.8"
$PyInstaller = "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-amd64.exe"

# ---------------------------------------------------------------- appearance

function Write-Step { param($m) Write-Host "  . $m" -ForegroundColor DarkGray }
function Write-Good { param($m) Write-Host "  + $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Host "  ! $m" -ForegroundColor Yellow }
function Write-Fail {
    param($m)
    Write-Host ""
    Write-Host "  Error  $m" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Press any key to close..." -ForegroundColor DarkGray
    try { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") } catch { }
    exit 1
}

function Show-Banner {
    Write-Host ""
    Write-Host "  +----------------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host "  |  " -ForegroundColor DarkGray -NoNewline
    Write-Host "VIDORA" -ForegroundColor Cyan -NoNewline
    Write-Host "  -  HD video downloads, with the sound included  |" -ForegroundColor DarkGray
    Write-Host "  +----------------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host "                  Setup v$SetupVersion  -  (c) 2026 Jay Kadam  -  MIT" -ForegroundColor DarkGray
    Write-Host "    Thanks to Ishan Mistry, whose idea set Vidora in motion." -ForegroundColor DarkGray
    Write-Host ""
}

# ---------------------------------------------------------------- helpers

<#
    Run an external program without it stealing the console's input.

    When this script arrives through `irm | iex`, the pipeline's stdin is still
    attached. A native command such as winget or pip inherits that handle and
    blocks waiting on it, which shows up as setup mysteriously stopping until
    you press Enter. Start-Process gives the child its own handles, so it runs
    straight through.
#>
function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$File,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $File
    $psi.UseShellExecute        = $false
    $psi.CreateNoWindow         = $true
    $psi.RedirectStandardInput  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true

    # Set-Location moves PowerShell's location but NOT the process working
    # directory that .NET hands to a child. Without this, "python -m venv
    # .venv" creates the folder wherever the installer was double-clicked -
    # usually Downloads - and setup then cannot find what it just made.
    if (-not $WorkingDirectory) { $WorkingDirectory = (Get-Location).Path }
    $psi.WorkingDirectory = $WorkingDirectory

    # Windows PowerShell 5.1 runs on .NET Framework, which has no ArgumentList,
    # so build one string and quote anything containing a space.
    $psi.Arguments = ($Arguments | ForEach-Object {
        if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
    }) -join ' '

    try {
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        [void]$p.Start()

        # Close stdin immediately. Anything that tries to read it gets EOF
        # instead of waiting on the console - this is what stops setup
        # pausing for a keypress partway through.
        $p.StandardInput.Close()

        # Drain both streams before waiting; a full pipe buffer deadlocks.
        $stdout = $p.StandardOutput.ReadToEnd()
        $stderr = $p.StandardError.ReadToEnd()
        $p.WaitForExit()

        return [pscustomobject]@{
            ExitCode = $p.ExitCode
            Output   = (($stdout, $stderr) -join "`n").Trim()
        }
    } catch {
        return [pscustomobject]@{ ExitCode = 1; Output = $_.Exception.Message }
    }
}

# Shorten a command's output to something readable in an error message.
function Format-Output {
    param([string]$Text, [int]$Lines = 6)
    if (-not $Text) { return "(no output)" }
    $kept = ($Text -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -Last $Lines)
    return ($kept -join "`n          ")
}

# Pick up PATH changes made by an installer we just ran, without needing the
# user to close and reopen the window.
function Update-PathFromRegistry {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user    = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = (($machine, $user) | Where-Object { $_ }) -join ";"
}

function Test-RealPython {
    param([string]$Exe)
    # The Windows Store ships a stub python.exe that opens the Store instead of
    # running anything. Skip it, or setup appears to hang on a shop page.
    if ($Exe -like "*\WindowsApps\*") { return $false }
    try {
        $out = & $Exe -c "import sys; print(sys.version_info[0], sys.version_info[1])" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $out) { return $false }
        $parts = $out.Trim() -split "\s+"
        return ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 8)
    } catch { return $false }
}

function Find-Python {
    foreach ($name in @("python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and (Test-RealPython $cmd.Source)) { return $cmd.Source }
    }
    # Installers do not always update PATH for the running session, so look in
    # the standard locations too.
    $roots = @(
        "$env:LOCALAPPDATA\Programs\Python",
        "$env:ProgramFiles\Python",
        "${env:ProgramFiles(x86)}\Python",
        "C:\Python"
    )
    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        $found = Get-ChildItem $root -Filter "python.exe" -Recurse -Depth 2 -ErrorAction SilentlyContinue |
                 Sort-Object FullName -Descending
        foreach ($f in $found) { if (Test-RealPython $f.FullName) { return $f.FullName } }
    }
    # Fall back to the py launcher.
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            $exe = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($exe -and (Test-RealPython $exe.Trim())) { return $exe.Trim() }
        } catch { }
    }
    return $null
}

function Install-Python {
    Write-Step "Python not found - installing it for you (a few minutes)..."

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Invoke-Native -File "winget" -Arguments @(
            "install", "--id", "Python.Python.3.12", "--silent",
            "--accept-package-agreements", "--accept-source-agreements",
            "--disable-interactivity"
        ) | Out-Null
        Update-PathFromRegistry
        $found = Find-Python
        if ($found) { return $found }
        Write-Warn "winget could not complete, downloading Python directly"
    }

    # Official installer, per-user so no admin prompt is needed.
    $exe = Join-Path $env:TEMP "python-$PyVersion-amd64.exe"
    try {
        Invoke-WebRequest -Uri $PyInstaller -OutFile $exe -UseBasicParsing
    } catch {
        Write-Fail @"
Could not download Python.
          Check your internet connection, or install Python yourself from
          https://www.python.org/downloads/  then run this again.
"@
    }

    Write-Step "Running the Python installer..."
    Invoke-Native -File $exe -Arguments @(
        "/quiet", "InstallAllUsers=0", "PrependPath=1",
        "Include_pip=1", "Include_launcher=1", "Include_test=0"
    ) | Out-Null
    Remove-Item $exe -Force -ErrorAction SilentlyContinue

    Update-PathFromRegistry
    $found = Find-Python
    if (-not $found) {
        Write-Fail @"
Python was installed but could not be found.
          Please close this window, open a new one, and run the installer again.
"@
    }
    return $found
}

function New-Shortcut {
    param([string]$Path, [string]$Target, [string]$WorkDir, [string]$Description)
    try {
        $shell = New-Object -ComObject WScript.Shell
        $sc = $shell.CreateShortcut($Path)
        $sc.TargetPath       = $Target
        $sc.WorkingDirectory = $WorkDir
        $sc.Description      = $Description
        $sc.Save()
        return $true
    } catch { return $false }
}

# ================================================================ start

Show-Banner

# ---------------------------------------------------------------- locate

$dir = $null
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "vidora.py"))) {
    $dir = $PSScriptRoot
}
# Piped through iex, so $PSScriptRoot is null. If the current folder is already
# a Vidora install, use it rather than nesting a fresh copy inside it.
if (-not $dir -and (Test-Path (Join-Path (Get-Location) "vidora.py"))) {
    $dir = (Get-Location).Path
    Write-Step "Already inside a Vidora folder, using it"
}

if (-not $dir) {
    $target = Join-Path $env:LOCALAPPDATA $RepoDirName

    if (Test-Path (Join-Path $target "vidora.py")) {
        Write-Step "Using existing install in $target"
    }
    else {
        Write-Step "Downloading Vidora..."
        $zip = Join-Path $env:TEMP "vidora-main.zip"
        $tmp = Join-Path $env:TEMP "vidora-extract"
        try {
            Remove-Item $zip, $tmp -Recurse -Force -ErrorAction SilentlyContinue
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

        # File by file: Copy-Item -Recurse -Force throws "Container cannot be
        # copied onto existing leaf item" when folders already exist, and this
        # also leaves an existing .venv alone.
        $prefix = $extracted.TrimEnd('\') + '\'
        Get-ChildItem -Path $extracted -Recurse -File | ForEach-Object {
            $destination = Join-Path $target $_.FullName.Substring($prefix.Length)
            $parent = Split-Path $destination -Parent
            if (-not (Test-Path $parent)) {
                New-Item -ItemType Directory -Force -Path $parent | Out-Null
            }
            Copy-Item $_.FullName -Destination $destination -Force
        }

        Remove-Item $zip, $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Write-Good "Downloaded"
    }
    $dir = $target
}

Set-Location $dir
# Keep .NET's idea of the working directory in step with PowerShell's, so any
# child process and any relative path resolve against the project folder.
[Environment]::CurrentDirectory = $dir

$venvPy = Join-Path $dir ".venv\Scripts\python.exe"

# ---------------------------------------------------------------- launch only

if ($LaunchOnly -and (Test-Path $venvPy)) {
    Write-Host ""
    Write-Host "  Starting Vidora..." -NoNewline
    Write-Host "  opening " -ForegroundColor DarkGray -NoNewline
    Write-Host "http://localhost:8501" -ForegroundColor Cyan
    Write-Host "  Close this window to stop it." -ForegroundColor DarkGray
    Write-Host ""
    & $venvPy -m streamlit run vidora_ui.py --server.headless false --browser.gatherUsageStats false
    exit $LASTEXITCODE
}

Write-Good "Project folder: $dir"

# ---------------------------------------------------------------- python

$py = Find-Python
if (-not $py) { $py = Install-Python }
Write-Good "Python: $(& $py --version 2>&1)"

# ---------------------------------------------------------------- ffmpeg

# ffmpeg does the merging. Prefer a system copy; fall back to the pip-packaged
# build, which needs no admin rights and always works.
$ffmpegViaPip = $false

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Good "ffmpeg: already installed"
} elseif (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Step "Installing ffmpeg (this can take a minute)..."
    Invoke-Native -File "winget" -Arguments @(
        "install", "--id", "Gyan.FFmpeg", "--silent",
        "--accept-package-agreements", "--accept-source-agreements",
        "--disable-interactivity"
    ) | Out-Null
    Update-PathFromRegistry
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Good "ffmpeg: installed"
    } else {
        Write-Step "Using the Python build of ffmpeg instead"
        $ffmpegViaPip = $true
    }
} else {
    Write-Step "Using the Python build of ffmpeg (no admin needed)"
    $ffmpegViaPip = $true
}

# ---------------------------------------------------------------- virtualenv

function New-Venv {
    Write-Step "Creating an isolated environment..."
    # Absolute target, so it cannot land anywhere but the project folder.
    $venvPath = Join-Path $dir ".venv"
    $r = Invoke-Native -File $py -Arguments @("-m", "venv", $venvPath) -WorkingDirectory $dir
    if (-not (Test-Path $venvPy)) {
        Write-Fail "Could not create a virtualenv.`n          $(Format-Output $r.Output)"
    }
    Write-Good "Environment created"
}

function Install-Packages {
    Write-Step "Installing packages (this is the slow part, please wait)..."

    Invoke-Native -File $venvPy -WorkingDirectory $dir -Arguments @(
        "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
        "--upgrade", "pip") | Out-Null

    # Absolute path to requirements.txt for the same reason.
    $req = Join-Path $dir "requirements.txt"
    $r = Invoke-Native -File $venvPy -WorkingDirectory $dir -Arguments @(
        "-m", "pip", "install", "--disable-pip-version-check",
        "--upgrade", "-r", $req)
    if ($r.ExitCode -ne 0) {
        Write-Fail "Could not install the Python packages.`n          $(Format-Output $r.Output)"
    }

    if ($ffmpegViaPip) {
        $r = Invoke-Native -File $venvPy -WorkingDirectory $dir -Arguments @(
            "-m", "pip", "install", "--disable-pip-version-check", "imageio-ffmpeg")
        if ($r.ExitCode -ne 0) {
            Write-Fail "Could not install ffmpeg.`n          $(Format-Output $r.Output)"
        }
    }

    Write-Good "Packages installed"
}

if (-not (Test-Path $venvPy)) { New-Venv } else { Write-Good "Environment: already set up" }
Install-Packages

# ---------------------------------------------------------------- verify

# A half-finished earlier run can leave a venv that looks fine but cannot
# import anything. Rather than telling you to delete a folder, rebuild it once
# and try again.
$check = Invoke-Native -File $venvPy -WorkingDirectory $dir -Arguments @("-c", "import yt_dlp, streamlit")

if ($check.ExitCode -ne 0) {
    Write-Warn "The environment looks incomplete - rebuilding it once..."
    Remove-Item (Join-Path $dir ".venv") -Recurse -Force -ErrorAction SilentlyContinue
    New-Venv
    Install-Packages
    $check = Invoke-Native -File $venvPy -Arguments @("-c", "import yt_dlp, streamlit")
}

if ($check.ExitCode -ne 0) {
    Write-Fail "Python packages still will not load.`n          $(Format-Output $check.Output)"
}

# Must run from the project folder - "import vidora" resolves vidora.py from
# the working directory.
$ff = Invoke-Native -File $venvPy -WorkingDirectory $dir -Arguments @(
    "-c", "import vidora, sys; sys.exit(0 if vidora.find_ffmpeg() else 1)")
if ($ff.ExitCode -ne 0) {
    Write-Fail "ffmpeg could not be found even after setup.`n          $(Format-Output $ff.Output)"
}

Write-Good "Everything checks out"

# ---------------------------------------------------------------- shortcuts

$launcher = Join-Path $dir "Start-Vidora.bat"
if (Test-Path $launcher) {
    $desktop   = Join-Path ([Environment]::GetFolderPath("Desktop")) "Vidora.lnk"
    $startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Vidora.lnk"
    $made = New-Shortcut -Path $desktop -Target $launcher -WorkDir $dir `
                         -Description "Vidora - HD video downloader"
    New-Shortcut -Path $startMenu -Target $launcher -WorkDir $dir `
                 -Description "Vidora - HD video downloader" | Out-Null
    if ($made) { Write-Good "Shortcut added to your Desktop" }
}

# ---------------------------------------------------------------- launch

Write-Host ""
Write-Host "  All set." -ForegroundColor Green -NoNewline
Write-Host "  Next time, just double-click the " -ForegroundColor DarkGray -NoNewline
Write-Host "Vidora" -ForegroundColor Cyan -NoNewline
Write-Host " icon on your Desktop." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Starting Vidora..." -NoNewline
Write-Host "  opening " -ForegroundColor DarkGray -NoNewline
Write-Host "http://localhost:8501" -ForegroundColor Cyan
Write-Host "  Close this window to stop it." -ForegroundColor DarkGray
Write-Host ""

& $venvPy -m streamlit run vidora_ui.py --server.headless false --browser.gatherUsageStats false
