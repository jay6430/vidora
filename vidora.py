#!/usr/bin/env python3
"""
Vidora - download video at full resolution, with the audio already in it.

Anything above 360p is served as separate video-only and audio-only streams,
which is why most download sites hand back a silent file. Vidora lists the
resolutions actually on offer, lets you pick one, and muxes the two streams
into a single finished file in one step.

Author:   Jay Kadam <kadamjay100@gmail.com>
License:  MIT - see LICENSE
Version:  1.0.0

Only download material you have the rights to keep - your own uploads,
Creative Commons content, or anything you have permission for.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

__app__ = "Vidora"
__version__ = "1.0.0"
__author__ = "Jay Kadam"
__email__ = "kadamjay100@gmail.com"
__license__ = "MIT"
__year__ = "2026"
__copyright__ = f"Copyright (c) {__year__} {__author__}"
__tagline__ = "video and audio, one finished file"
__thanks__ = "Thanks to Ishan Mistry, whose idea set Vidora in motion."


# ==========================================================================
# terminal presentation
# ==========================================================================

def _supports_ansi() -> bool:
    """True if we can safely emit colour escapes."""
    if os.environ.get("NO_COLOR"):          # https://no-color.org
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    if not sys.stdout.isatty():             # piped or redirected
        return False
    if sys.platform == "win32":
        # Modern Windows terminals support ANSI once VT processing is on.
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # -11 = STD_OUTPUT_HANDLE, 7 = ENABLE_PROCESSED_OUTPUT
            #   | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            return bool(kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7))
        except Exception:
            return False
    return True


def _supports_unicode() -> bool:
    """True if the console encoding can render box-drawing characters."""
    try:
        "─│╭╮╰╯·←".encode(sys.stdout.encoding or "ascii")
        return True
    except (UnicodeEncodeError, LookupError, TypeError):
        return False


ANSI = _supports_ansi()
UNI = _supports_unicode()


class S:
    """Style helpers. Each returns the text unchanged when colour is off."""

    @staticmethod
    def _wrap(code: str):
        def apply(text: str) -> str:
            return f"\033[{code}m{text}\033[0m" if ANSI else text
        return apply

    bold = _wrap.__func__("1")
    dim = _wrap.__func__("2")
    accent = _wrap.__func__("36")   # cyan
    good = _wrap.__func__("32")     # green
    warn = _wrap.__func__("33")     # yellow
    bad = _wrap.__func__("31")      # red


# Box-drawing characters, with ASCII fallbacks for limited consoles.
G = {
    "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
    "h": "─", "v": "│", "dot": "·", "arrow": "←", "down": "↓",
    "full": "█", "empty": "░", "copy": "©",
} if UNI else {
    "tl": "+", "tr": "+", "bl": "+", "br": "+",
    "h": "-", "v": "|", "dot": "-", "arrow": "<-", "down": "v",
    "full": "#", "empty": ".", "copy": "(c)",
}


def banner():
    title = f" {__app__.upper()} "
    inner = f"{title}{G['dot']}  {__tagline__}  "
    line = G["h"] * (len(inner) + 2)

    # Credit line, right-aligned to the box edge below it.
    credit = (
        f"v{__version__}   {G['dot']}   {G['copy']} {__year__} {__author__}"
        f"   {G['dot']}   {__license__}"
    )
    box_width = len(line) + 2

    print()
    print("  " + S.dim(G["tl"] + line + G["tr"]))
    print("  " + S.dim(G["v"]) + " " + S.bold(S.accent(title))
          + S.dim(f"{G['dot']}  {__tagline__}  ") + " " + S.dim(G["v"]))
    print("  " + S.dim(G["bl"] + line + G["br"]))
    print("  " + S.dim(credit.rjust(box_width)))
    print()


def rule(width: int = 51):
    print("   " + S.dim(G["h"] * width))


def info(msg: str):
    print(f"  {S.dim(G['dot'])} {msg}")


def fail(msg: str, hint: str | None = None):
    print(f"\n  {S.bad('Error')}  {msg}")
    if hint:
        print(f"          {S.dim(hint)}")
    print()
    sys.exit(1)


# ==========================================================================
# dependency checks
# ==========================================================================

FFMPEG_HINT = {
    "darwin": "brew install ffmpeg",
    "win32": "winget install Gyan.FFmpeg    (or: choco install ffmpeg)",
    "linux": "sudo apt install ffmpeg    (or your distro's package manager)",
}


def platform_key() -> str:
    if sys.platform.startswith("win"):
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def find_ffmpeg() -> str | None:
    """
    Locate ffmpeg on PATH, falling back to the copy bundled with the
    imageio-ffmpeg package so Vidora still works where system packages
    cannot be installed.
    """
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def require_deps() -> str:
    """Fail early and usefully rather than halfway through a download."""
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        fail("yt-dlp is not installed - it is what talks to the video site.",
             f"Install it with:  {sys.executable} -m pip install -U yt-dlp")

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        fail("ffmpeg was not found - it is what merges the video and audio.",
             f"Install it with:  {FFMPEG_HINT[platform_key()]}\n"
             f"          Or, with no system install:  "
             f"{sys.executable} -m pip install imageio-ffmpeg")
    return ffmpeg


# ==========================================================================
# format inspection
# ==========================================================================

def codec_family(vcodec: str | None) -> str:
    """Normalise the many spellings a site may use into three buckets."""
    v = (vcodec or "").lower()
    if v.startswith(("avc", "h264", "h.264")):
        return "h264"
    if v.startswith(("vp9", "vp09", "vp8")):
        return "vp9"
    if v.startswith(("av01", "av1")):
        return "av1"
    return "other"


# H.264 plays everywhere, including older TVs and editing software.
# AV1/VP9 are smaller at equivalent quality but less universally supported.
CODEC_RANK = {
    "compatible": {"h264": 0, "vp9": 1, "av1": 2, "other": 3},
    "efficient": {"av1": 0, "vp9": 1, "h264": 2, "other": 3},
}

CODEC_LABEL = {"h264": "H.264", "vp9": "VP9", "av1": "AV1"}


def human_size(n) -> str:
    if not n:
        return "?"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024
    return "?"


def human_time(seconds) -> str:
    if not seconds:
        return ""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def format_size(f) -> int | None:
    return f.get("filesize") or f.get("filesize_approx")


def best_audio(formats) -> dict | None:
    """Highest-bitrate audio-only track, preferring m4a for mp4 compatibility."""
    audio = [
        f for f in formats
        if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")
    ]
    if not audio:
        return None
    return max(audio, key=lambda f: (f.get("abr") or 0, f.get("ext") == "m4a"))


def collect_options(info: dict, prefer: str = "compatible") -> list[dict]:
    """
    One entry per available resolution, each holding the best video track at
    that height. Returned highest-resolution-first.
    """
    rank = CODEC_RANK[prefer]
    formats = info.get("formats") or []
    audio = best_audio(formats)
    audio_size = format_size(audio) if audio else 0

    video = [
        f for f in formats
        if f.get("vcodec") not in (None, "none") and f.get("height")
    ]

    by_height: dict[int, dict] = {}
    for f in video:
        h = f["height"]
        current = by_height.get(h)
        key = (rank[codec_family(f.get("vcodec"))], -(f.get("tbr") or 0))
        if current is None or key < current["_key"]:
            by_height[h] = {"_key": key, "fmt": f}

    options = []
    for h in sorted(by_height, reverse=True):
        f = by_height[h]["fmt"]
        family = codec_family(f.get("vcodec"))
        muxed = f.get("acodec") not in (None, "none")
        vsize = format_size(f) or 0
        options.append({
            "height": h,
            "fps": f.get("fps"),
            "format_id": f["format_id"],
            "codec": family,
            "muxed": muxed,
            # mp4 cannot reliably hold VP9/AV1 + Opus; mkv always can.
            "container": "mp4" if family == "h264" else "mkv",
            "size": vsize + (0 if muxed else (audio_size or 0)),
        })
    return options


def best_compatible_index(options: list[dict]) -> int | None:
    """Index of the highest-resolution option that lands in an MP4."""
    for i, o in enumerate(options):
        if o["container"] == "mp4":
            return i
    return None


# ==========================================================================
# the menu
# ==========================================================================

def render_table(options: list[dict]) -> None:
    highlight = best_compatible_index(options)

    # The leading pad matches the "  {num}   " prefix on each row below,
    # so every column lines up with its heading.
    header = (
        "   #   " + "RESOLUTION".ljust(16) + "CODEC".ljust(8)
        + "SIZE".rjust(10) + "   " + "FILE"
    )
    print("   " + S.dim(header))
    rule()

    for i, o in enumerate(options):
        num = str(i + 1).rjust(2)
        res = f"{o['height']}p" + (f" {o['fps']:g}fps" if o.get("fps") else "")
        codec = CODEC_LABEL.get(o["codec"], o["codec"])
        size = f"~{human_size(o['size'])}"

        row = (
            f"  {S.bold(S.accent(num))}   "
            + S.bold(res.ljust(16))
            + S.dim(codec.ljust(8))
            + size.rjust(10) + "   "
            + S.dim("." + o["container"])
        )
        if i == highlight:
            row += "  " + S.good(f"{G['arrow']} plays anywhere")
        print("   " + row)

    rule()


def choose(options: list[dict]) -> dict:
    render_table(options)
    prompt = (
        f"\n   {S.bold('Which one?')} "
        + S.dim(f"[1-{len(options)}, Enter = 1] ")
    )
    while True:
        raw = input(prompt).strip()
        if not raw:
            return options[0]
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"   {S.warn('Enter a number from the list, or press Enter for the best one.')}")


def pick_capped(options: list[dict], max_height: int) -> dict:
    eligible = [o for o in options if o["height"] <= max_height]
    if not eligible:
        # Everything is above the cap; take the smallest rather than failing.
        return options[-1]
    return eligible[0]


def describe(opt: dict) -> str:
    fps = f" {opt['fps']:g}fps" if opt.get("fps") else ""
    codec = CODEC_LABEL.get(opt["codec"], opt["codec"])
    return f"{opt['height']}p{fps}  {codec}  ~{human_size(opt['size'])}  .{opt['container']}"


# ==========================================================================
# progress
# ==========================================================================

def progress_hook(d: dict) -> None:
    """A single tidy progress line per stream, replacing yt-dlp's default."""
    status = d.get("status")

    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        done = d.get("downloaded_bytes") or 0
        info_dict = d.get("info_dict") or {}
        kind = "audio" if info_dict.get("vcodec") in (None, "none") else "video"

        pct = (done / total) if total else 0
        width = 24
        filled = int(pct * width)
        bar = G["full"] * filled + G["empty"] * (width - filled)

        speed = d.get("speed")
        speed_s = f"{human_size(speed)}/s" if speed else "--"
        eta_s = human_time(d.get("eta")) or "--"

        line = (
            f"   {S.dim(kind.ljust(6))}{S.accent(bar)} "
            f"{str(int(pct * 100)).rjust(3)}%   "
            f"{speed_s.rjust(10)}   {S.dim('eta ' + eta_s)}"
        )
        sys.stdout.write("\r" + line + "  ")
        sys.stdout.flush()

    elif status == "finished":
        sys.stdout.write("\r" + " " * 78 + "\r")
        sys.stdout.flush()


def postprocessor_hook(d: dict) -> None:
    if d.get("status") == "started" and d.get("postprocessor") == "Merger":
        info("merging video and audio " + S.dim("(ffmpeg)"))


# ==========================================================================
# download
# ==========================================================================

def default_outdir() -> Path:
    env = os.environ.get("VIDORA_OUT") or os.environ.get("YTDL_OUT")
    if env:
        return Path(env).expanduser()
    home = Path.home()
    base = home / "Movies" if (home / "Movies").exists() else home / "Videos"
    return base / "Vidora"


def build_opts(args, outdir: Path, selection: dict | None, ffmpeg: str | None = None):
    opts = {
        "outtmpl": str(outdir / "%(title).150B [%(id)s].%(ext)s"),
        "noplaylist": not args.playlist,
        "restrictfilenames": False,
        "windowsfilenames": platform_key() == "win32",
        "concurrent_fragment_downloads": 4,
        "retries": 10,
        "quiet": True,
        "no_warnings": True,
        # Suppress yt-dlp's own progress line so only Vidora's bar is drawn.
        "noprogress": True,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
    }
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg

    if args.audio_only:
        opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        }]
        return opts

    fid = selection["format_id"]
    # Exact video track plus the best audio, with progressive fallbacks so an
    # unusual video degrades rather than failing outright.
    opts["format"] = f"{fid}+bestaudio[ext=m4a]/{fid}+bestaudio/{fid}/best"
    opts["merge_output_format"] = args.container or selection["container"]

    if args.subs:
        opts["writesubtitles"] = True
        opts["subtitleslangs"] = ["en.*", "en"]
        opts["postprocessors"] = [{"key": "FFmpegEmbedSubtitle"}]

    return opts


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vidora",
        description=f"{__app__} - {__tagline__}.",
        epilog=f"{__thanks__}\n{__copyright__}. MIT licensed.",
    )
    p.add_argument("url", nargs="?", help="video URL (quote it in zsh)")
    p.add_argument("-o", "--out", metavar="DIR",
                   help="output folder (default: ~/Movies/Vidora or ~/Videos/Vidora)")
    p.add_argument("--best", action="store_true",
                   help="skip the menu, take the highest resolution")
    p.add_argument("--max", type=int, metavar="HEIGHT",
                   help="skip the menu, best up to this height (e.g. 1080)")
    p.add_argument("--audio-only", action="store_true",
                   help="download the audio track only, as m4a")
    p.add_argument("--efficient", action="store_true",
                   help="prefer AV1/VP9 (smaller files) over H.264")
    p.add_argument("--container", choices=["mp4", "mkv"],
                   help="force the output container")
    p.add_argument("--subs", action="store_true",
                   help="embed English subtitles when available")
    p.add_argument("--playlist", action="store_true",
                   help="download the whole playlist, not just this video")
    p.add_argument("--no-banner", action="store_true", help="skip the header")
    p.add_argument("-V", "--version", action="version",
                   version=f"{__app__} {__version__} - {__author__} <{__email__}> - {__license__}")
    return p


def main():
    args = build_parser().parse_args()

    if not args.no_banner:
        banner()

    ffmpeg = require_deps()
    import yt_dlp

    url = args.url or input(f"   {S.bold('Video URL:')} ").strip()
    if not url:
        fail("No URL given.")

    outdir = Path(args.out).expanduser() if args.out else default_outdir()
    outdir.mkdir(parents=True, exist_ok=True)

    selection = None
    if not args.audio_only:
        info("reading available formats" + S.dim(" ..."))
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                meta = ydl.extract_info(url, download=False)
        except Exception as e:
            fail(f"Could not read that URL.\n          {S.dim(str(e).splitlines()[0])}",
                 "If this used to work, update yt-dlp:  "
                 f"{sys.executable} -m pip install -U yt-dlp")

        # A playlist URL returns entries rather than formats; inspect the first.
        if meta.get("_type") == "playlist":
            entries = [e for e in (meta.get("entries") or []) if e]
            if not entries:
                fail("That playlist appears to be empty.")
            info(f"playlist of {len(entries)} videos "
                 + S.dim("- listing resolutions from the first"))
            meta = entries[0]

        if meta.get("is_live"):
            fail("That is a live stream - resolutions are not fixed.",
                 "Try again once the stream has ended.")

        options = collect_options(meta, "efficient" if args.efficient else "compatible")
        if not options:
            fail("No downloadable video formats were found for that URL.")

        title = meta.get("title", "Unknown title")
        duration = human_time(meta.get("duration"))
        uploader = meta.get("uploader") or ""
        subtitle = f"  {G['dot']}  ".join(x for x in (uploader, duration) if x)

        print()
        print("   " + S.bold(title))
        if subtitle:
            print("   " + S.dim(subtitle))
        print()

        if args.best:
            selection = options[0]
        elif args.max:
            selection = pick_capped(options, args.max)
        else:
            selection = choose(options)

        if args.best or args.max:
            info("selected " + S.bold(describe(selection)))

    print()
    info("saving to " + S.accent(str(outdir)))
    print()

    opts = build_opts(args, outdir, selection, ffmpeg)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            code = ydl.download([url])
    except Exception as e:
        fail(f"Download failed.\n          {S.dim(str(e).splitlines()[0])}",
             f"Updating usually fixes this:  {sys.executable} -m pip install -U yt-dlp")

    if code:
        sys.exit(code)

    print(f"  {S.good('Done')}  {S.dim(str(outdir))}")
    if not args.no_banner:
        print(f"  {S.dim(__thanks__)}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {S.warn('Cancelled.')}\n")
        sys.exit(130)
