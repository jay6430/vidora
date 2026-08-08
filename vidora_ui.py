"""
Vidora UI - an HD video downloader in your browser, running locally.

Paste a link, pick a quality up to 4K, and get one ready-to-play file with the
sound already in it. Runs on your own machine, on your own connection:

    python3 -m streamlit run vidora_ui.py

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
    page_title="Vidora - HD video downloader",
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
    --green: #4ade80;
}

.stApp {
    background:
        radial-gradient(1200px 600px at 15% -10%, rgba(94,234,212,.07), transparent 60%),
        radial-gradient(900px 500px at 85% 0%, rgba(167,139,250,.06), transparent 55%),
        var(--bg);
}

#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 2.8rem; padding-bottom: 4rem; max-width: 720px;}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text);
}

/* ---------- masthead ---------- */
.v-head {text-align: center; margin-bottom: 2.2rem;}
.v-mark {
    font-size: 2.7rem; font-weight: 700; letter-spacing: -.04em;
    background: linear-gradient(100deg, var(--accent) 0%, var(--violet) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: .3rem; line-height: 1;
}
.v-tag {color: var(--text); font-size: 1.01rem; font-weight: 500; letter-spacing: -.01em;}
.v-hint {color: var(--muted); font-size: .86rem; font-weight: 300; margin-top: .25rem;}

/* ---------- inputs ---------- */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 11px !important;
    color: var(--text) !important;
    padding: .9rem 1.05rem !important;
    font-size: .95rem !important;
    transition: border-color .18s ease, box-shadow .18s ease;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent-dim) !important;
    box-shadow: 0 0 0 3px rgba(94,234,212,.10) !important;
}
.stTextInput > div > div > input::placeholder {color: var(--faint) !important;}
.stTextInput label, .stSelectbox label {
    color: var(--muted) !important; font-size: .8rem !important; font-weight: 500 !important;
}

/* ---------- buttons ---------- */
.stButton > button {
    background: var(--surface-2); color: var(--text);
    border: 1px solid var(--line); border-radius: 10px;
    padding: .62rem 1.25rem; font-weight: 500; font-size: .89rem;
    width: 100%; transition: all .18s ease;
}
.stButton > button:hover {
    border-color: var(--accent-dim); color: var(--accent);
    background: var(--surface); transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(100deg, var(--accent) 0%, var(--accent-dim) 100%);
    color: #06231f; border: none; font-weight: 600; font-size: .95rem;
    padding: .75rem 1.25rem;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.08); color: #06231f; transform: translateY(-1px);
    box-shadow: 0 6px 22px rgba(94,234,212,.18);
}

/* ---------- video card ---------- */
.v-card {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 14px; padding: 1.05rem 1.2rem; margin: 1.5rem 0 .6rem;
    display: flex; gap: 1rem; align-items: center;
}
.v-thumb {width: 112px; border-radius: 8px; flex-shrink: 0;}
.v-title {font-weight: 600; font-size: .98rem; line-height: 1.35; margin-bottom: .25rem;}
.v-sub {color: var(--muted); font-size: .81rem;}

/* ---------- section label ---------- */
.v-label {
    color: var(--faint); font-size: .7rem; font-weight: 600;
    letter-spacing: .11em; text-transform: uppercase; margin: 1.6rem 0 .6rem;
}

/* ---------- radio list of qualities ---------- */
div[role="radiogroup"] {gap: .36rem !important;}
div[role="radiogroup"] > label {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: .7rem .95rem; margin: 0 !important;
    transition: all .16s ease; width: 100%;
}
div[role="radiogroup"] > label:hover {
    border-color: #38414f; background: var(--surface-2);
}
div[role="radiogroup"] > label:has(input:checked) {
    border-color: var(--accent-dim);
    background: rgba(94,234,212,.055);
}
div[role="radiogroup"] > label > div:last-child {width: 100%;}
div[role="radiogroup"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .83rem !important; color: var(--text) !important;
    margin: 0 !important; letter-spacing: -.01em;
}

/* ---------- notices ---------- */
.v-note, .v-warn, .v-done {
    border-radius: 10px; padding: .82rem 1rem; color: var(--muted);
    font-size: .82rem; line-height: 1.6; margin: 1rem 0;
}
.v-note {
    background: rgba(94,234,212,.05); border: 1px solid rgba(94,234,212,.16);
    border-left: 2px solid var(--accent-dim);
}
.v-warn {
    background: rgba(251,191,36,.05); border: 1px solid rgba(251,191,36,.16);
    border-left: 2px solid #fbbf24;
}
.v-done {
    background: rgba(74,222,128,.06); border: 1px solid rgba(74,222,128,.2);
    border-left: 2px solid var(--green);
}
.v-note b, .v-warn b, .v-done b {color: var(--text); font-weight: 600;}
.v-done .f {
    font-family: 'JetBrains Mono', monospace; font-size: .8rem;
    color: var(--text); word-break: break-all;
}

/* ---------- progress ---------- */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent-dim), var(--accent)) !important;
}
.stProgress > div > div > div {background: var(--surface-2) !important;}

/* ---------- expander ---------- */
details, .streamlit-expanderHeader {
    background: var(--surface) !important; border: 1px solid var(--line) !important;
    border-radius: 10px !important; color: var(--muted) !important;
    font-size: .84rem !important;
}
details summary {color: var(--muted) !important; font-size: .84rem !important;}

code {
    background: var(--surface-2) !important; color: var(--accent) !important;
    padding: .13em .42em !important; border-radius: 5px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: .85em !important;
}

/* ---------- footer ---------- */
.v-foot {
    text-align: center; color: var(--faint); font-size: .75rem;
    margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--line);
    line-height: 1.9;
}
.v-foot a {color: var(--muted); text-decoration: none; border-bottom: 1px solid var(--line);}
.v-foot a:hover {color: var(--accent);}
.v-thanks {color: var(--violet); opacity: .85;}
</style>
"""

st.markdown(THEME, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def row_label(opt: dict) -> str:
    """
    One fixed-width row per quality. Every option carries audio - Vidora
    merges it - so that is stated on each row rather than left to be assumed.
    """
    res = f"{opt['height']}p" + (f" {opt['fps']:g}" if opt.get("fps") else "")
    codec = vidora.CODEC_LABEL.get(opt["codec"], opt["codec"])
    size = f"~{vidora.human_size(opt['size'])}"
    tail = "  ·  plays anywhere" if opt["container"] == "mp4" else ""
    return (
        f"{res:<11}{codec:<7}+ audio{size:>12}   .{opt['container']}{tail}"
    )


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


def run_download(url: str, selection: dict, outdir: Path):
    """Download and mux, driving a Streamlit progress bar from yt-dlp's hooks."""
    bar = st.progress(0.0)
    status = st.empty()

    def hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            info_dict = d.get("info_dict") or {}
            kind = "Audio" if info_dict.get("vcodec") in (None, "none") else "Video"
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
                "<div class='v-sub'>Combining video and audio …</div>",
                unsafe_allow_html=True,
            )

    class Args:
        audio_only = False
        subs = st.session_state.get("want_subs", False)
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
# masthead
# --------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="v-head">
        <div class="v-mark">Vidora</div>
        <div class="v-tag">Download videos in HD — with the sound included.</div>
        <div class="v-hint">Paste a link, pick your quality, get one
            ready-to-play file.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# dependency checks, before anything can fail confusingly later
# --------------------------------------------------------------------------

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
        "<div class='v-warn'><b>ffmpeg is missing.</b> It is what combines the "
        "video and audio. Install it with <code>brew install ffmpeg</code>, "
        "or without touching your system: <code>pip install imageio-ffmpeg</code>."
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# --------------------------------------------------------------------------
# input
# --------------------------------------------------------------------------

url = st.text_input(
    "Video URL",
    placeholder="Paste a video link here",
    label_visibility="collapsed",
)

# Sensible default that needs no thought; everything adjustable is tucked away.
default_dir = str(vidora.default_outdir())

with st.expander("More options"):
    custom = st.text_input(
        "Save to folder",
        value=st.session_state.get("outdir", default_dir),
        key="outdir",
        help="Defaults to your Downloads folder.",
    )
    st.checkbox(
        "Prefer smaller files (AV1 / VP9)",
        key="efficient",
        help="Off by default, so you get MP4 files that play on anything.",
    )
    st.checkbox(
        "Include English subtitles when available",
        key="want_subs",
    )

outdir_str = st.session_state.get("outdir", default_dir)

if url and not URL_PATTERN.match(url.strip()):
    st.markdown(
        "<div class='v-warn'>That does not look like a link. It should start "
        "with <code>https://</code>.</div>",
        unsafe_allow_html=True,
    )
    url = ""

# --------------------------------------------------------------------------
# quality picker
# --------------------------------------------------------------------------

if url:
    try:
        with st.spinner("Checking available qualities…"):
            meta = fetch_meta(url.strip())
    except Exception as exc:
        first_line = str(exc).splitlines()[0]
        st.markdown(
            f"<div class='v-warn'><b>Could not read that link.</b><br>{first_line}"
            "<br><br>If this used to work, update yt-dlp: "
            "<code>pip install -U yt-dlp</code></div>",
            unsafe_allow_html=True,
        )
        st.stop()

    if meta["is_live"]:
        st.markdown(
            "<div class='v-warn'><b>That is a live stream.</b> Qualities are "
            "not fixed until it ends.</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    options = vidora.collect_options(
        {"formats": meta["formats"]},
        "efficient" if st.session_state.get("efficient") else "compatible",
    )

    if not options:
        st.markdown(
            "<div class='v-warn'>No downloadable video was found at that link.</div>",
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

    st.markdown("<div class='v-label'>Choose your quality</div>", unsafe_allow_html=True)

    # Default to the best quality that produces an MP4, not the highest
    # resolution overall - MP4 plays everywhere, and the top option is
    # usually a large MKV most people would not want by default.
    default_index = vidora.best_compatible_index(options) or 0

    labels = [row_label(o) for o in options]
    picked = st.radio(
        "Quality", labels, index=default_index, label_visibility="collapsed"
    )
    selection = options[labels.index(picked)]

    if selection["container"] == "mkv":
        st.markdown(
            "<div class='v-note'>This quality uses VP9 or AV1, which MP4 cannot "
            "hold reliably, so it will be saved as an <b>.mkv</b> file. VLC, mpv, "
            "IINA and Plex all play it. For an MP4, choose a row marked "
            "<b>plays anywhere</b>.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    go = st.button(f"Download {selection['height']}p with audio", type="primary")

    if go:
        outdir = Path(outdir_str).expanduser()
        try:
            outdir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            st.markdown(
                f"<div class='v-warn'>Cannot save to that folder.<br>{exc}</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        try:
            saved = run_download(url.strip(), selection, outdir)
        except Exception as exc:
            st.markdown(
                f"<div class='v-warn'><b>Download failed.</b><br>"
                f"{str(exc).splitlines()[0]}<br><br>Updating usually fixes this: "
                "<code>pip install -U yt-dlp</code></div>",
                unsafe_allow_html=True,
            )
            st.stop()

        # Survives the rerun that clicking "Open folder" triggers.
        st.session_state["last_file"] = str(saved) if saved else None
        st.session_state["last_dir"] = str(outdir)

# --------------------------------------------------------------------------
# result
# --------------------------------------------------------------------------

if st.session_state.get("last_dir"):
    last_file = st.session_state.get("last_file")
    last_dir = st.session_state["last_dir"]

    if last_file:
        p = Path(last_file)
        size = vidora.human_size(p.stat().st_size) if p.exists() else ""
        st.markdown(
            f"<div class='v-done'><b>Saved</b> &nbsp;{size}<br>"
            f"<span class='f'>{p.name}</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='v-done'><b>Finished.</b> Check <code>{last_dir}</code>."
            "</div>",
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open folder"):
            if not vidora.open_folder(last_dir):
                st.markdown(
                    f"<div class='v-warn'>Could not open the folder "
                    f"automatically. It is at <code>{last_dir}</code></div>",
                    unsafe_allow_html=True,
                )
    with col2:
        if st.button("Download another"):
            for key in ("last_file", "last_dir"):
                st.session_state.pop(key, None)
            st.rerun()

# --------------------------------------------------------------------------
# footer
# --------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="v-foot">
        <b style="color:var(--muted)">Vidora</b> v{vidora.__version__}
        &nbsp;·&nbsp; © {vidora.__year__} {vidora.__author__}
        &nbsp;·&nbsp; {vidora.__license__} licensed<br>
        <span class="v-thanks">{vidora.__thanks__}</span><br>
        Runs entirely on this computer &nbsp;·&nbsp; built on
        <a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a>
        and <a href="https://ffmpeg.org/">FFmpeg</a>
    </div>
    """,
    unsafe_allow_html=True,
)
