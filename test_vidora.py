"""
Offline checks for Vidora's format-selection logic, using a synthetic format
list shaped like the one a video site actually returns.

Author:   Jay Kadam <kadamjay100@gmail.com>
License:  MIT - see LICENSE

Run with:  python3 test_vidora.py
"""

import pathlib

import vidora

# Mirrors a real response: one legacy muxed 360p, the rest video-only DASH,
# with H.264 topping out at 1080p and VP9/AV1 going higher.
INFO = {
    "title": "Sample",
    "formats": [
        # audio-only
        {"format_id": "139", "acodec": "mp4a.40.5", "vcodec": "none", "ext": "m4a", "abr": 48, "filesize": 3_000_000},
        {"format_id": "140", "acodec": "mp4a.40.2", "vcodec": "none", "ext": "m4a", "abr": 128, "filesize": 8_000_000},
        {"format_id": "251", "acodec": "opus", "vcodec": "none", "ext": "webm", "abr": 130, "filesize": 8_500_000},
        # legacy muxed
        {"format_id": "18", "acodec": "mp4a.40.2", "vcodec": "avc1.42001E", "height": 360, "fps": 30, "tbr": 700, "filesize": 30_000_000},
        # video-only DASH
        {"format_id": "136", "acodec": "none", "vcodec": "avc1.4d401f", "height": 720, "fps": 30, "tbr": 2000, "filesize": 60_000_000},
        {"format_id": "247", "acodec": "none", "vcodec": "vp09.00.31.08", "height": 720, "fps": 30, "tbr": 1500, "filesize": 45_000_000},
        {"format_id": "137", "acodec": "none", "vcodec": "avc1.640028", "height": 1080, "fps": 30, "tbr": 4000, "filesize": 120_000_000},
        {"format_id": "248", "acodec": "none", "vcodec": "vp09.00.40.08", "height": 1080, "fps": 30, "tbr": 3000, "filesize": 90_000_000},
        {"format_id": "271", "acodec": "none", "vcodec": "vp09.00.50.08", "height": 1440, "fps": 30, "tbr": 9000, "filesize": 260_000_000},
        {"format_id": "399", "acodec": "none", "vcodec": "av01.0.12M.08", "height": 1080, "fps": 60, "tbr": 2800, "filesize": 85_000_000},
        {"format_id": "313", "acodec": "none", "vcodec": "vp09.00.50.08", "height": 2160, "fps": 30, "tbr": 20000, "filesize": 600_000_000},
    ],
}

failures = []


def check(label, actual, expected):
    ok = actual == expected
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {actual!r}")
    if not ok:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


def section(name):
    print(f"\n{name}")


section("metadata")
check("app name", vidora.__app__, "Vidora")
check("author", vidora.__author__, "Jay Kadam")
check("license", vidora.__license__, "MIT")
check("version is set", bool(vidora.__version__), True)

section("codec_family")
check("avc1.640028", vidora.codec_family("avc1.640028"), "h264")
check("vp09.00.40.08", vidora.codec_family("vp09.00.40.08"), "vp9")
check("av01.0.12M.08", vidora.codec_family("av01.0.12M.08"), "av1")
check("None", vidora.codec_family(None), "other")

section("collect_options (compatible: prefer H.264)")
opts = vidora.collect_options(INFO, "compatible")
check("one entry per height, descending", [o["height"] for o in opts], [2160, 1440, 1080, 720, 360])
check("1080p picks H.264 over the smaller VP9/AV1", opts[2]["format_id"], "137")
check("720p picks H.264", opts[3]["format_id"], "136")
check("H.264 -> mp4", opts[2]["container"], "mp4")
check("VP9-only 2160p -> mkv", opts[0]["container"], "mkv")

section("collect_options (efficient: prefer AV1/VP9)")
eff = vidora.collect_options(INFO, "efficient")
check("1080p picks AV1", eff[2]["format_id"], "399")
check("AV1 -> mkv", eff[2]["container"], "mkv")

section("size estimate includes the audio track")
check("1080p total", opts[2]["size"], 120_000_000 + 8_500_000)
check("muxed 360p not double-counted", opts[4]["size"], 30_000_000)
check("360p flagged as already muxed", opts[4]["muxed"], True)
check("1080p flagged as needing a merge", opts[2]["muxed"], False)

section("best_audio")
check("highest bitrate wins", vidora.best_audio(INFO["formats"])["format_id"], "251")

section("best_compatible_index")
check("first mp4 row is the 1080p H.264", vidora.best_compatible_index(opts), 2)
check("none when every option is mkv",
      vidora.best_compatible_index([{"container": "mkv"}, {"container": "mkv"}]), None)

section("pick_capped")
check("--max 1080", vidora.pick_capped(opts, 1080)["height"], 1080)
check("--max 900 falls to 720", vidora.pick_capped(opts, 900)["height"], 720)
check("--max 4320 gives the top", vidora.pick_capped(opts, 4320)["height"], 2160)
check("--max 144 below everything -> smallest", vidora.pick_capped(opts, 144)["height"], 360)

section("format string built for the chosen track")
args = vidora.build_parser().parse_args([])
built = vidora.build_opts(args, pathlib.Path("/tmp"), opts[2])
check("exact video id + bestaudio, with fallbacks",
      built["format"], "137+bestaudio[ext=m4a]/137+bestaudio/137/best")
check("merge container", built["merge_output_format"], "mp4")

args_mkv = vidora.build_parser().parse_args(["--container", "mkv"])
check("--container overrides the automatic choice",
      vidora.build_opts(args_mkv, pathlib.Path("/tmp"), opts[2])["merge_output_format"], "mkv")

args_audio = vidora.build_parser().parse_args(["--audio-only"])
audio_opts = vidora.build_opts(args_audio, pathlib.Path("/tmp"), None)
check("--audio-only needs no video selection",
      audio_opts["format"], "bestaudio[ext=m4a]/bestaudio/best")

section("human_size / human_time")
check("bytes", vidora.human_size(512), "512 B")
check("megabytes", vidora.human_size(120_000_000), "114.4 MB")
check("unknown", vidora.human_size(None), "?")
check("under an hour", vidora.human_time(634), "10:34")
check("over an hour", vidora.human_time(3725), "1:02:05")

section("menu rendering")
vidora.render_table(opts)

print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("All checks passed.")
