<div align="center">

# Vidora

**HD video downloader — with the sound included.**

Paste a YouTube link, pick your quality up to 4K, get one ready-to-play file.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/Platforms-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](#setup)

</div>

> Runs on your own machine. Vidora is not a hosted service and there is no
> public instance — see [Why there is no hosted version](#why-there-is-no-hosted-version).

---

## What it does

Download a video in **4K, 1440p, 1080p or 720p** and actually get the audio
with it. Choose **MP4 or MKV**, grab the **audio on its own**, pull in
**subtitles**, or queue a **whole playlist**.

Most download sites give you a silent file above 360p. That is because anything
higher is delivered as two separate streams — video with no sound, audio with
no picture — and they hand you only the first. Vidora fetches both and merges
them, so every quality on the list comes out ready to play.

Works with YouTube and the many other sites [yt-dlp](https://github.com/yt-dlp/yt-dlp)
supports. Free, open source, no ads, no upload limits, and it runs on your own
computer rather than someone's server.

```
  ╭──────────────────────────────────────────────────────────╮
  │  VIDORA ·  HD video downloads, with the sound included   │
  ╰──────────────────────────────────────────────────────────╯
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

  · saving to /Users/jay/Downloads

   video ████████████████░░░░░░░░  67%     8.4 MB/s   eta 0:14
   audio ████████████████████████ 100%    11.2 MB/s   eta 0:00
  · merging video and audio (ffmpeg)

  Done  /Users/jay/Downloads
```

Sizes include the audio track, so the number shown is roughly what lands on
disk. The `← plays anywhere` marker points at the highest resolution that comes
out as an MP4.

---

## Setup — one line

Copy the line for your system, paste it into a terminal, press Enter. It
installs everything into a self-contained folder and opens Vidora in your
browser.

**macOS** — press `⌘ Space`, type **Terminal**, press Enter, then paste:

```bash
curl -fsSL https://raw.githubusercontent.com/jay6430/vidora/main/install.sh | bash
```

**Windows** — click Start, type **PowerShell**, open it, then paste:

```powershell
irm https://raw.githubusercontent.com/jay6430/vidora/main/install.ps1 | iex
```

If Windows says running scripts is disabled, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

**Linux** — press `Ctrl Alt T`, then paste:

```bash
curl -fsSL https://raw.githubusercontent.com/jay6430/vidora/main/install.sh | bash
```

Run the same line again any time to reopen Vidora. It detects what is already
installed and skips straight to launching.

### What the installer does

Nothing hidden, and nothing outside the project folder:

1. Checks for Python 3.8+ and stops with instructions if it is missing
2. Installs ffmpeg via Homebrew, apt or winget — or falls back to a
   pip-packaged build that needs no admin rights
3. Creates a `.venv` inside the project folder
4. Installs yt-dlp and Streamlit into that venv only
5. Verifies both imports and that ffmpeg is reachable
6. Launches the web UI

It never installs anything system-wide except ffmpeg, and never touches your
global Python packages.

**Prefer to inspect before running?** Reasonable — piping a script from the
internet into your shell is worth being careful about:

```bash
git clone https://github.com/jay6430/vidora.git
cd vidora
less install.sh      # read it
./install.sh
```

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

Downloads land in your **Downloads** folder. Set `VIDORA_OUT` to change that
permanently, or use `-o` for a one-off.

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

The installer opens this automatically. To start it yourself:

```bash
python3 -m streamlit run vidora_ui.py
```

Use `python3 -m` rather than a bare `streamlit` — that guarantees it runs on
the same interpreter as your virtualenv. A bare `streamlit` may resolve to a
global install with no yt-dlp, which produces a confusing failure.

It opens at `localhost:8501` with a thumbnail, a quality picker, live progress
and an **Open folder** button when the download finishes. The highest-quality
MP4 is preselected, since MP4 plays on anything; the larger MKV options are
there if you want them. Everything else — save location, subtitles, smaller
AV1/VP9 files — sits under **More options**.

The CLI and the UI call the same functions in `vidora.py`, so they can never
disagree about what they will download. Nothing leaves your machine.

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
├── install.sh          one-command setup + launcher (macOS / Linux)
├── install.ps1         one-command setup + launcher (Windows)
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
