<div align="center">

# Vidora

**Video and audio, one finished file.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/Platforms-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](#setup)

</div>

> Runs on your own machine. Vidora is not a hosted service and there is no
> public instance — see [Why there is no hosted version](#why-there-is-no-hosted-version).

---

## The problem

Anything above 360p is delivered as two separate streams — video with no sound,
and audio with no picture. That is why the download sites hand you either a
silent 1080p file or a 360p one with audio, and why the usual workaround is to
download both halves and merge them by hand.

Vidora does that last step for you. It reads the resolutions actually on offer,
lets you pick one, downloads both streams and muxes them into a single file.

```
  ╭─────────────────────────────────────────────────╮
  │  VIDORA ·  video and audio, one finished file   │
  ╰─────────────────────────────────────────────────╯
              v1.0.0   ·   © 2026 Jay Kadam   ·   MIT

  · reading available formats ...

   Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film
   Blender Foundation  ·  10:34

      #   RESOLUTION      CODEC         SIZE   FILE
   ───────────────────────────────────────────────────
      1   2160p 60fps     VP9        ~1.3 GB   .mkv
      2   1440p 60fps     VP9      ~480.8 MB   .mkv
      3   1080p 60fps     H.264    ~275.0 MB   .mp4  ← plays anywhere
      4   720p 60fps      H.264    ~172.9 MB   .mp4
      5   480p 30fps      H.264     ~56.2 MB   .mp4
      6   360p 30fps      H.264     ~27.2 MB   .mp4
   ───────────────────────────────────────────────────

   Which one? [1-6, Enter = 1] 3

  · saving to /Users/jay/Movies/Vidora

   video ████████████████░░░░░░░░  67%     8.4 MB/s   eta 0:14
   audio ████████████████████████ 100%    11.2 MB/s   eta 0:00
  · merging video and audio (ffmpeg)

  Done  /Users/jay/Movies/Vidora
```

Sizes include the audio track, so the number shown is roughly what lands on
disk. The `← plays anywhere` marker points at the highest resolution that comes
out as an MP4.

---

## Setup

Three things: Python 3.8+, yt-dlp, ffmpeg.

**macOS**

```bash
brew install python ffmpeg
python3 -m pip install -r requirements.txt
```

**Windows** (PowerShell)

```powershell
winget install Python.Python.3.12
winget install Gyan.FFmpeg
python -m pip install -r requirements.txt
```

Reopen PowerShell afterwards so the new PATH takes effect.

**Linux** (Debian/Ubuntu)

```bash
sudo apt install python3 python3-pip ffmpeg
python3 -m pip install -r requirements.txt
```

**No system install possible?** ffmpeg also ships inside a Python package, and
Vidora will find it there automatically:

```bash
python3 -m pip install imageio-ffmpeg
```

Vidora checks for both dependencies on startup and names whichever is missing,
so nothing fails halfway through a download.

---

## Use

```bash
python3 vidora.py "URL"        # macOS / Linux
python vidora.py "URL"         # Windows
```

Quote the URL. In zsh (the macOS default) an unquoted `?` or `&` is treated as
a glob and you get `zsh: no matches found`.

### Options

| Flag | Effect |
|---|---|
| `--best` | Skip the menu, take the highest resolution |
| `--max 1080` | Skip the menu, best up to that height |
| `-o DIR` | Choose the output folder |
| `--audio-only` | Just the audio, as m4a |
| `--efficient` | Prefer AV1/VP9 — smaller files, less compatible |
| `--container mp4` | Force a container instead of choosing automatically |
| `--subs` | Embed English subtitles when available |
| `--playlist` | Download the whole playlist, not just the one video |
| `--no-banner` | Skip the header, for scripting |
| `-V`, `--version` | Print version and author |

Downloads land in `~/Movies/Vidora` on macOS and `~/Videos/Vidora` elsewhere.
Set `VIDORA_OUT` to change that permanently.

### One-word command

**macOS / Linux** — add to `~/.zshrc` or `~/.bashrc`:

```bash
alias vidora='/full/path/to/YT_Downloader/vidora'
```

**Windows** — put the project folder on your PATH, then `vidora "URL"` works
from anywhere via `vidora.bat`. For PowerShell, add to your `$PROFILE`:

```powershell
Set-Alias vidora "C:\full\path\to\YT_Downloader\vidora.ps1"
```

All three launchers prefer the project's own `.venv` when one exists, so the
command works from any directory without activating anything first.

---

## The web UI

If you would rather click than type, Vidora ships a local interface built on
Streamlit:

```bash
streamlit run vidora_ui.py
```

It opens in your browser at `localhost:8501` with a thumbnail, a resolution
picker, live progress, and the same engine underneath — the CLI and the UI both
call the same functions in `vidora.py`, so they can never disagree about what
they will download.

Nothing leaves your machine. The page is served from your own computer and
files are written straight to the folder you choose.

---

## Why there is no hosted version

Vidora deliberately has no public URL, for two reasons.

**It would not work.** Video sites aggressively block the IP ranges belonging
to AWS, GCP and Azure — which is every free host, since Streamlit Community
Cloud, Hugging Face Spaces, Render and Railway all run on them. A hosted
instance gets "sign in to confirm you're not a bot" on essentially every
request. It would deploy cleanly and then fail on every download.

**It would not be the same thing.** One person downloading their own material
is not the same as a public endpoint anyone can point at any video. Free hosts
prohibit downloaders in their terms for exactly this reason.

So Vidora stays local, where it works and where the responsibility sits with
the person using it. The [project page](https://jay6430.github.io/vidora/)
is a landing page, not an instance.

---

## Why some rows say `.mkv`

MP4 is not a reliable container for VP9 or AV1 video paired with Opus audio,
which is what gets used at 1440p and above. Those go into MKV, which handles
any codec combination. Every modern player — VLC, mpv, IINA, Plex — opens MKV
without complaint.

If you specifically need MP4, for older editing software or a TV, pick a row
marked H.264. Vidora already prefers H.264 at each resolution for this reason;
`--efficient` flips that preference if you would rather have smaller files.

---

## Project layout

```
vidora/
├── vidora.py           the tool
├── vidora_ui.py        local web UI (Streamlit)
├── vidora              launcher — macOS / Linux
├── vidora.bat          launcher — Windows (cmd)
├── vidora.ps1          launcher — Windows (PowerShell)
├── test_vidora.py      offline tests for the selection logic
├── index.html          project landing page (GitHub Pages)
├── requirements.txt    Python dependencies
├── .gitattributes      keeps launcher line endings correct per platform
├── LICENSE             MIT
└── README.md
```

Run the tests with `python3 test_vidora.py`. They cover resolution grouping,
codec preference, size estimates, capping, and format-string construction —
all offline, no network needed.

---

## Notes

- Downloading is against most video sites' Terms of Service regardless of the
  tool used. Sensible for your own uploads, Creative Commons material, or
  content you have permission for.
- Keep yt-dlp current: `python3 -m pip install -U yt-dlp`. Sites change things
  and yt-dlp is patched in response, often within days. If a download suddenly
  breaks, update before assuming anything else is wrong.
- Verified end to end against Big Buck Bunny (Blender Foundation, CC-BY): a
  720p video-only track plus a separate audio track came back as one MP4
  containing H.264 video at 1280×720 and AAC audio.

---

## Thanks

Thanks to **Ishan Mistry**, whose idea set Vidora in motion.

## Author

**Jay Kadam** — [kadamjay100@gmail.com](mailto:kadamjay100@gmail.com)

## License

MIT — see [LICENSE](LICENSE). Copyright © 2026 Jay Kadam.

Vidora builds on [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense) and
[FFmpeg](https://ffmpeg.org/) (LGPL/GPL), which remain under their own licenses.
