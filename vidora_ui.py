"""
Vidora UI - an HD video downloader in your browser, running locally.

Paste a link, pick a quality up to 4K, and get one ready-to-play file with the
sound already in it. Runs on your own machine, on your own connection:

    streamlit run vidora_ui.py

Author:   Jay Kadam <kadamjay100@gmail.com>
License:  MIT - see LICENSE
Version:  1.0.0

Only download material you have the rights to keep - your own uploads,
Creative Commons content, or anything you have permission for.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import streamlit as st

import vidora

# --------------------------------------------------------------------------
# page chrome
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Vidora",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

THEME = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0c0d10;
    --surface: #14161b;
    --surface-2: #1b1e25;
    --line: #262a33;
    --text: #e8eaed;
    --muted: #8b919d;
    --faint: #5a606c;
    --accent: #5eead4;
    --accent-dim: #2dd4bf;
    --violet: #a78bfa;
}

.stApp {
    background:
        radial-gradient(1200px 600px at 15% -10%, rgba(94,234,212,.07), transparent 60%),
        radial-gradient(900px 500px at 85% 0%, rgba(167,139,250,.06), transparent 55%),
        var(--bg);
}

#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 3.2rem; padding-bottom: 4rem; max-width: 760px;}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text);
}

/* ---------- masthead ---------- */
.v-head {text-align: center; margin-bottom: 2.6rem;}
.v-mark {
    font-size: 2.9rem; font-weight: 700; letter-spacing: -.04em;
    background: linear-gradient(100deg, var(--accent) 0%, var(--violet) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: .35rem; line-height: 1;
}
.v-tag {color: var(--text); font-size: 1.02rem; font-weight: 500; letter-spacing: -.01em;}
.v-hint {color: var(--muted); font-size: .87rem; font-weight: 300; margin-top: .3rem;}
.v-meta {
    color: var(--faint); font-size: .74rem; margin-top: .9rem;
    font-family: 'JetBrains Mono', monospace; letter-spacing: .02em;
}

/* ---------- inputs ---------- */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 11px !important;
    color: var(--text) !important;
    padding: .85rem 1.05rem !important;
    font-size: .94rem !important;
    transition: border-color .18s ease, box-shadow .18s ease;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent-dim) !important;
    box-shadow: 0 0 0 3px rgba(94,234,212,.10) !important;
}
.stTextInput > div > div > input::placeholder {color: var(--faint) !important;}
.stTextInput label {color: var(--muted) !important; font-size: .82rem !important; font-weight: 500 !important;}

/* ---------- buttons ---------- */
.stButton > button {
    background: var(--surface-2); color: var(--text);
    border: 1px solid var(--line); border-radius: 10px;
    padding: .62rem 1.25rem; font-weight: 500; font-size: .9rem;
    width: 100%; transition: all .18s ease;
}
.stButton > button:hover {
    border-color: var(--accent-dim); color: var(--accent);
    background: var(--surface); transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(100deg, var(--accent) 0%, var(--accent-dim) 100%);
    color: #06231f; border: none; font-weight: 600;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.08); color: #06231f; transform: translateY(-1px);
    box-shadow: 0 6px 22px rgba(94,234,212,.18);
}

/* ---------- video card ---------- */
.v-card {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 14px; padding: 1.15rem 1.3rem; margin: 1.6rem 0 1.1rem;
    display: flex; gap: 1.05rem; align-items: center;
}
.v-thumb {width: 116px; border-radius: 8px; flex-shrink: 0;}
.v-title {font-weight: 600; font-size: 1rem; line-height: 1.35; margin-bottom: .3rem;}
.v-sub {color: var(--muted); font-size: .82rem;}

/* ---------- section label ---------- */
.v-label {
    color: var(--faint); font-size: .7rem; font-weight: 600;
    letter-spacing: .11em; text-transform: uppercase; margin: 1.9rem 0 .7rem;
}

/* ---------- radio list of resolutions ---------- */
div[role="radiogroup"] {gap: .38rem !important;}
div[role="radiogroup"] > label {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: .72rem .95rem; margin: 0 !important;
    transition: all .16s ease; width: 100%;
}
div[role="radiogroup"] > label:hover {
    border-color: #38414f; background: var(--surface-2);
}
div[role="radiogroup"] > label > div:last-child {width: 100%;}
div[role="radiogroup"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .845rem !important; color: var(--text) !important;
    margin: 0 !important; letter-spacing: -.01em;
}

/* ---------- notices ---------- */
.v-note {
    background: rgba(94,234,212,.05); border: 1px solid rgba(94,234,212,.16);
    border-left: 2px solid var(--accent-dim);
    border-radius: 9px; padding: .8rem 1rem; color: var(--muted);
    font-size: .82rem; line-height: 1.55; margin: 1.1rem 0;
}
.v-warn {
    background: rgba(251,191,36,.05); border: 1px solid rgba(251,191,36,.16);
    border-left: 2px solid #fbbf24;
    border-radius: 9px; padding: .8rem 1rem; color: var(--muted);
    font-size: .82rem; line-height: 1.55; margin: 1.1rem 0;
}
.v-note b, .v-warn b {color: var(--text); font-weight: 600;}

/* ---------- progress ---------- */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent-dim), var(--accent)) !important;
}
.stProgress > div > div > div {background: var(--surface-2) !important;}

/* ---------- footer ---------- */
.v-foot {
    text-align: center; color: var(--faint); font-size: .76rem;
    margin-top: 3.4rem; padding-top: 1.6rem; border-top: 1px solid var(--line);
    line-height: 1.9;
}
.v-foot a {color: var(--muted); text-decoration: none; border-bottom: 1px solid var(--line);}
.v-foot a:hover {color: var(--accent);}
.v-thanks {color: var(--violet); opacity: .85;}

/* ---------- expander ---------- */
.streamlit-expanderHeader, details summary {
    background: var(--surface) !important; border: 1px solid var(--line) !important;
    border-radius: 10px !important; color: var(--muted) !important;
    font-size: .84rem !important;
}
code {
    background: var(--surface-2) !important; color: var(--accent) !important;
    padding: .13em .42em !important; border-radius: 5px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: .85em !important;
}
</style>
"""

st.markdown(THEME, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def row_label(opt: dict) -> str:
    """A fixed-width row so the list reads like a table in the mono font."""
    res = f"{opt['height']}p" + (f" {opt['fps']:g}" if opt.get("fps") else "")
    codec = vidora.CODEC_LABEL.get(opt["codec"], opt["codec"])
    size = f"~{vidora.human_size(opt['size'])}"
    tail = "  ·  plays anywhere" if opt["container"] == "mp4" else ""
    return f"{res:<12}{codec:<8}{size:>11}   .{opt['container']}{tail}"


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_meta(url: str) -> dict:
    """Read metadata without downloading. Cached so re-runs stay instant."""
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        meta = ydl.extract_info(url, download=False)

    if meta.get("_type") == "playlist":
        entries = [e for e in (meta.get("entries") or []) if e]
        if not entries:
            raise ValueError("That playlist appears to be empty.")
        meta = entries[0]

    return {
        "title": meta.get("title", "Untitled"),
        "uploader": meta.get("uploader") or "",
        "duration": meta.get("duration"),
        "thumbnail": meta.get("thumbnail"),
        "is_live": bool(meta.get("is_live")),
        "formats": meta.get("formats") or [],
    }


def run_download(url: str, selection: dict, outdir: Path, efficient: bool):
    """Download and mux, driving a Streamlit progress bar from yt-dlp's hooks."""
    bar = st.progress(0.0)
    status = st.empty()

    def hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            info_dict = d.get("info_dict") or {}
            kind = "audio" if info_dict.get("vcodec") in (None, "none") else "video"
            pct = min(done / total, 1.0) if total else 0.0
            speed = d.get("speed")
            speed_s = f"{vidora.human_size(speed)}/s" if speed else ""
            eta = vidora.human_time(d.get("eta"))
            bar.progress(pct)
            status.markdown(
                f"<div class='v-sub'>{kind} &nbsp;·&nbsp; {int(pct * 100)}%"
                + (f" &nbsp;·&nbsp; {speed_s}" if speed_s else "")
                + (f" &nbsp;·&nbsp; {eta} left" if eta else "")
                + "</div>",
                unsafe_allow_html=True,
            )
        elif d.get("status") == "finished":
            bar.progress(1.0)
            status.markdown(
                "<div class='v-sub'>merging video and audio …</div>",
                unsafe_allow_html=True,
            )

    class Args:
        audio_only = False
        subs = False
        playlist = False
        container = None

    opts = vidora.build_opts(Args(), outdir, selection, vidora.find_ffmpeg())
    opts["progress_hooks"] = [hook]
    opts["postprocessor_hooks"] = []

    before = set(outdir.iterdir()) if outdir.exists() else set()
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    after = set(outdir.iterdir())

    bar.empty()
    status.empty()

    new_files = [p for p in (after - before) if p.is_file()]
    return max(new_files, key=lambda p: p.stat().st_mtime) if new_files else None


# --------------------------------------------------------------------------
# page
# --------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="v-head">
        <div class="v-mark">Vidora</div>
        <div class="v-tag">Download YouTube videos in HD — with the sound included.</div>
        <div class="v-hint">Paste a link, pick your quality, get one
            ready-to-play file.</div>
        <div class="v-meta">v{vidora.__version__} &nbsp;·&nbsp; © {vidora.__year__}
            {vidora.__author__} &nbsp;·&nbsp; {vidora.__license__}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Dependency checks up front, so nothing fails halfway through - and so a
# missing package is never reported as a bad URL.
try:
    import yt_dlp  # noqa: F401
except ImportError:
    st.markdown(
        "<div class='v-warn'><b>yt-dlp is not installed in this Python.</b><br><br>"
        f"Streamlit is running on <code>{sys.executable}</code>, and that "
        "interpreter does not have yt-dlp. This almost always means Streamlit "
        "was launched from a different environment than your virtualenv — the "
        "command line tool can work perfectly while this page fails."
        "<br><br><b>Launch it through the same Python:</b><br>"
        "<code>python3 -m streamlit run vidora_ui.py</code>"
        "<br><br><b>Or install yt-dlp into this one:</b><br>"
        f"<code>{sys.executable} -m pip install -U yt-dlp</code></div>",
        unsafe_allow_html=True,
    )
    st.stop()

if not vidora.find_ffmpeg():
    st.markdown(
        "<div class='v-warn'><b>ffmpeg is missing.</b> It is what merges the "
        "video and audio streams. Install it with <code>brew install ffmpeg</code>, "
        "or without touching your system: <code>pip install imageio-ffmpeg</code>."
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

url = st.text_input(
    "Video URL",
    placeholder="https://…",
    label_visibility="collapsed",
)

outdir_str = st.text_input(
    "Save to",
    value=str(vidora.default_outdir()),
    help="The folder finished files are written to.",
)

if url and not URL_PATTERN.match(url.strip()):
    st.markdown(
        "<div class='v-warn'>That does not look like a URL. It should start "
        "with <code>https://</code>.</div>",
        unsafe_allow_html=True,
    )
    url = ""

if url:
    try:
        with st.spinner("Reading available formats…"):
            meta = fetch_meta(url.strip())
    except Exception as exc:
        first_line = str(exc).splitlines()[0]
        st.markdown(
            f"<div class='v-warn'><b>Could not read that URL.</b><br>{first_line}"
            "<br><br>If this used to work, update yt-dlp: "
            "<code>pip install -U yt-dlp</code></div>",
            unsafe_allow_html=True,
        )
        st.stop()

    if meta["is_live"]:
        st.markdown(
            "<div class='v-warn'><b>That is a live stream.</b> Resolutions are "
            "not fixed until it ends.</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    efficient = st.session_state.get("efficient", False)
    options = vidora.collect_options(
        {"formats": meta["formats"]}, "efficient" if efficient else "compatible"
    )

    if not options:
        st.markdown(
            "<div class='v-warn'>No downloadable video formats were found.</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    duration = vidora.human_time(meta["duration"])
    subtitle = "  ·  ".join(x for x in (meta["uploader"], duration) if x)
    thumb = (
        f"<img src='{meta['thumbnail']}' class='v-thumb'>" if meta["thumbnail"] else ""
    )
    st.markdown(
        f"""
        <div class="v-card">
            {thumb}
            <div>
                <div class="v-title">{meta['title']}</div>
                <div class="v-sub">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='v-label'>Choose your quality</div>", unsafe_allow_html=True
    )

    labels = [row_label(o) for o in options]
    picked = st.radio(
        "Resolution", labels, index=0, label_visibility="collapsed"
    )
    selection = options[labels.index(picked)]

    if selection["container"] == "mkv":
        st.markdown(
            "<div class='v-note'>This resolution uses VP9 or AV1, which MP4 "
            "cannot hold reliably alongside Opus audio, so it will be saved as "
            "<b>.mkv</b>. VLC, mpv, IINA and Plex all play it. For MP4, pick a "
            "row marked <b>plays anywhere</b>.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    go = st.button(f"Download {selection['height']}p", type="primary")

    if go:
        outdir = Path(outdir_str).expanduser()
        try:
            outdir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            st.markdown(
                f"<div class='v-warn'>Cannot write to that folder.<br>{exc}</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        try:
            saved = run_download(url.strip(), selection, outdir, efficient)
        except Exception as exc:
            st.markdown(
                f"<div class='v-warn'><b>Download failed.</b><br>"
                f"{str(exc).splitlines()[0]}<br><br>Updating usually fixes this: "
                "<code>pip install -U yt-dlp</code></div>",
                unsafe_allow_html=True,
            )
            st.stop()

        if saved:
            size = vidora.human_size(saved.stat().st_size)
            st.markdown(
                f"<div class='v-note'><b>Done.</b> {saved.name}<br>"
                f"{size} &nbsp;·&nbsp; saved to <code>{outdir}</code></div>",
                unsafe_allow_html=True,
            )
            st.balloons()
        else:
            st.markdown(
                f"<div class='v-note'><b>Finished.</b> Check <code>{outdir}</code>."
                "</div>",
                unsafe_allow_html=True,
            )

with st.expander("Options and notes"):
    st.checkbox(
        "Prefer AV1 / VP9 — smaller files, less compatible",
        key="efficient",
        help="Off by default: H.264 is preferred so you get MP4 wherever possible.",
    )
    st.markdown(
        "Vidora runs entirely on this machine — nothing is uploaded anywhere, "
        "and files are written straight to the folder above.\n\n"
        "Keep yt-dlp current with `pip install -U yt-dlp`. Sites change things "
        "often and yt-dlp is patched in response.\n\n"
        "Please only download material you have the rights to keep — your own "
        "uploads, Creative Commons content, or anything you have permission for."
    )

st.markdown(
    f"""
    <div class="v-foot">
        <b style="color:var(--muted)">Vidora</b> v{vidora.__version__}
        &nbsp;·&nbsp; © {vidora.__year__} {vidora.__author__}
        &nbsp;·&nbsp; {vidora.__license__} licensed<br>
        <span class="v-thanks">{vidora.__thanks__}</span><br>
        Built on <a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a>
        and <a href="https://ffmpeg.org/">FFmpeg</a>
    </div>
    """,
    unsafe_allow_html=True,
)
