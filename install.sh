#!/usr/bin/env bash
#
# Vidora - one-command setup and launcher for macOS and Linux.
#
# Author:   Jay Kadam <kadamjay100@gmail.com>
# License:  MIT - see LICENSE
#
# Installs everything Vidora needs into a self-contained virtualenv inside this
# folder, then opens the app. Safe to run again any time: it skips whatever is
# already in place and simply relaunches.
#
#   curl -fsSL https://raw.githubusercontent.com/jay6430/vidora/main/install.sh | bash
#
# Or, once you have the repo:  ./install.sh
#

set -euo pipefail

REPO_URL="https://github.com/jay6430/vidora.git"
TARBALL_URL="https://github.com/jay6430/vidora/archive/refs/heads/main.tar.gz"
REPO_DIR_NAME="vidora"

# ---------------------------------------------------------------- appearance

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    BOLD=$'\033[1m'; DIM=$'\033[2m'; ACC=$'\033[36m'
    OK=$'\033[32m'; WARN=$'\033[33m'; ERR=$'\033[31m'; OFF=$'\033[0m'
else
    BOLD=""; DIM=""; ACC=""; OK=""; WARN=""; ERR=""; OFF=""
fi

step()  { printf "  %s·%s %s\n" "$DIM" "$OFF" "$1"; }
good()  { printf "  %s✓%s %s\n" "$OK" "$OFF" "$1"; }
warn()  { printf "  %s!%s %s\n" "$WARN" "$OFF" "$1"; }
fail()  { printf "\n  %sError%s  %s\n\n" "$ERR" "$OFF" "$1" >&2; exit 1; }

banner() {
    printf "\n"
    printf "  %s╭──────────────────────────────────────────────────────────╮%s\n" "$DIM" "$OFF"
    printf "  %s│%s  %s%sVIDORA%s %s·  HD video downloads, with the sound included%s   %s│%s\n" \
        "$DIM" "$OFF" "$BOLD" "$ACC" "$OFF" "$DIM" "$OFF" "$DIM" "$OFF"
    printf "  %s╰──────────────────────────────────────────────────────────╯%s\n" "$DIM" "$OFF"
    printf "  %s                     © 2026 Jay Kadam   ·   MIT setup%s\n" "$DIM" "$OFF"
    printf "  %s  Thanks to Ishan Mistry, whose idea set Vidora in motion.%s\n\n" "$DIM" "$OFF"
}

# ---------------------------------------------------------------- platform

OS="linux"
[ "$(uname -s)" = "Darwin" ] && OS="macos"

# ---------------------------------------------------------------- locate repo

# When piped from curl there is no script file, so fetch the project first.
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    DIR=""
fi

banner

if [ -z "$DIR" ] || [ ! -f "$DIR/vidora.py" ]; then
    TARGET="$PWD/$REPO_DIR_NAME"

    if [ -f "$TARGET/vidora.py" ]; then
        # Already downloaded before. Update it if this is a git checkout,
        # otherwise just use what is there.
        if [ -d "$TARGET/.git" ] && command -v git >/dev/null 2>&1; then
            step "Updating existing copy in $TARGET"
            git -C "$TARGET" pull --ff-only --quiet 2>/dev/null \
                || warn "could not update, using what is here"
        else
            step "Using existing copy in $TARGET"
        fi
    elif command -v git >/dev/null 2>&1; then
        step "Downloading Vidora into $TARGET"
        git clone --quiet --depth 1 "$REPO_URL" "$TARGET" \
            || fail "Could not download Vidora. Check your internet connection."
    else
        # No git, and no need for it - curl and tar are on every Mac and
        # virtually every Linux, and curl already fetched this script.
        step "Downloading Vidora into $TARGET (no git needed)"

        command -v tar >/dev/null 2>&1 \
            || fail "tar is needed to unpack the download but was not found."
        command -v gzip >/dev/null 2>&1 \
            || fail "gzip is needed to unpack the download but was not found."

        # Download and unpack as separate steps, so a network problem and a
        # broken archive do not produce the same misleading message.
        TMP_TGZ="${TMPDIR:-/tmp}/vidora-main.$$.tar.gz"
        curl -fsSL -o "$TMP_TGZ" "$TARBALL_URL" \
            || fail "Could not download Vidora. Check your internet connection."

        mkdir -p "$TARGET"
        if ! tar -xzf "$TMP_TGZ" -C "$TARGET" --strip-components=1 2>/dev/null; then
            rm -f "$TMP_TGZ"
            fail "The download could not be unpacked. Please try again."
        fi
        rm -f "$TMP_TGZ"

        [ -f "$TARGET/vidora.py" ] \
            || fail "The download did not contain what was expected. Please try again."
    fi

    DIR="$TARGET"
fi

cd "$DIR"
good "Project folder: $DIR"

# ---------------------------------------------------------------- python

PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
            PY="$candidate"; break
        fi
    fi
done

if [ -z "$PY" ]; then
    if [ "$OS" = "macos" ]; then
        fail "Python 3.8 or newer is required.
          Install it with:  brew install python
          If you do not have Homebrew: https://brew.sh"
    else
        fail "Python 3.8 or newer is required.
          Install it with:  sudo apt install python3 python3-venv python3-pip"
    fi
fi
good "Python: $($PY --version 2>&1)"

# ---------------------------------------------------------------- ffmpeg

# ffmpeg does the merging. Prefer a system copy; fall back to the pip-packaged
# build so this never requires sudo or a package manager.
FFMPEG_VIA_PIP="no"

if command -v ffmpeg >/dev/null 2>&1; then
    good "ffmpeg: already installed"
elif [ "$OS" = "macos" ] && command -v brew >/dev/null 2>&1; then
    step "Installing ffmpeg with Homebrew (this can take a minute)…"
    if brew install ffmpeg >/dev/null 2>&1; then
        good "ffmpeg: installed"
    else
        warn "Homebrew install failed, will use the Python build instead"
        FFMPEG_VIA_PIP="yes"
    fi
elif [ "$OS" = "linux" ] && command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" = "0" ]; then
    step "Installing ffmpeg with apt…"
    apt-get install -y ffmpeg >/dev/null 2>&1 && good "ffmpeg: installed" \
        || FFMPEG_VIA_PIP="yes"
else
    step "No system ffmpeg found, using the Python build (no sudo needed)"
    FFMPEG_VIA_PIP="yes"
fi

# ---------------------------------------------------------------- virtualenv

if [ ! -x ".venv/bin/python" ]; then
    step "Creating an isolated environment in .venv"
    "$PY" -m venv .venv 2>/dev/null || fail \
        "Could not create a virtualenv.
          On Debian/Ubuntu this usually means:  sudo apt install python3-venv"
    good "Environment created"
else
    good "Environment: already set up"
fi

VENV_PY=".venv/bin/python"

# ---------------------------------------------------------------- packages

step "Installing packages (yt-dlp, streamlit)…"
"$VENV_PY" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true

if ! "$VENV_PY" -m pip install --quiet --upgrade -r requirements.txt; then
    fail "Could not install the Python packages. Check your internet connection."
fi

if [ "$FFMPEG_VIA_PIP" = "yes" ]; then
    "$VENV_PY" -m pip install --quiet imageio-ffmpeg \
        || fail "Could not install ffmpeg. Try installing it manually."
fi

good "Packages installed"

# ---------------------------------------------------------------- verify

if ! "$VENV_PY" -c "import yt_dlp, streamlit" 2>/dev/null; then
    fail "Something did not install correctly. Try deleting the .venv folder and running this again."
fi

if ! "$VENV_PY" -c "import vidora, sys; sys.exit(0 if vidora.find_ffmpeg() else 1)" 2>/dev/null; then
    fail "ffmpeg could not be found even after setup. Install it manually and re-run."
fi

good "Everything checks out"

# ---------------------------------------------------------------- launch

printf "\n  %sStarting Vidora…%s  %sit will open in your browser at%s %shttp://localhost:8501%s\n" \
    "$BOLD" "$OFF" "$DIM" "$OFF" "$ACC" "$OFF"
printf "  %sPress Ctrl+C in this window to stop it.%s\n\n" "$DIM" "$OFF"

exec "$VENV_PY" -m streamlit run vidora_ui.py \
    --server.headless false \
    --browser.gatherUsageStats false
