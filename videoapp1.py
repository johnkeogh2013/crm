"""
Fetch — Video Downloader
Paste a URL → choose format → click Download → save file.
Supports: YouTube, TikTok, Instagram, Facebook, X/Twitter
"""

import streamlit as st
import yt_dlp
import os
import tempfile
import ssl
import certifi
import subprocess
from pathlib import Path

# ── SSL fix ───────────────────────────────────────────────────────────────────
ssl._create_default_https_context = lambda: ssl.create_default_context(
    cafile=certifi.where()
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fetch — Video Downloader",
    page_icon="⬇",
    layout="centered",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=DM+Sans:wght@400;500;600&family=DM+Mono&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #080810; color: #f0f0ff; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 700px; }

.masthead { text-align:center; padding: 2.5rem 0 1.5rem; }
.masthead h1 {
    font-family: 'Playfair Display', serif;
    font-size: 4rem; font-weight: 900;
    color: #fff; margin: 0; letter-spacing: -2px;
}
.masthead .sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem; letter-spacing: 4px;
    color: #5555aa; text-transform: uppercase; margin-top: 0.5rem;
}
.masthead .plats {
    font-size: 0.82rem; color: #6666aa; margin-top: 0.6rem;
}
.bar {
    height: 3px;
    background: linear-gradient(90deg, #6c6ff5, #a855f7, #ec4899);
    border-radius: 2px; margin: 1.5rem 0;
}
.step-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem; letter-spacing: 3px;
    color: #5555aa; text-transform: uppercase;
    margin-bottom: 0.4rem; margin-top: 1.4rem;
}
.success-box {
    background: #061a0f; border: 1px solid #1a4d2a;
    border-left: 3px solid #22dd77; border-radius: 8px;
    padding: 1rem 1.2rem; color: #66ffaa;
    font-size: 0.9rem; margin: 1rem 0;
}
.error-box {
    background: #1a0608; border: 1px solid #4d1a20;
    border-left: 3px solid #ee3355; border-radius: 8px;
    padding: 1rem 1.2rem; color: #ff8899;
    font-size: 0.9rem; margin: 1rem 0;
}
.info-box {
    background: #0a0a1f; border: 1px solid #22225a;
    border-left: 3px solid #6c6ff5; border-radius: 8px;
    padding: 0.8rem 1.1rem; color: #9999dd;
    font-size: 0.82rem; margin: 0.8rem 0;
}
.stTextInput > div > div > input {
    background: #10101e !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
    color: #f0f0ff !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6c6ff5 !important;
    box-shadow: 0 0 0 2px rgba(108,111,245,0.2) !important;
}
.stTextInput > div > div > input::placeholder { color: #444466 !important; }

div.stRadio > div {
    background: #10101e; border: 1px solid #1e1e38;
    border-radius: 10px; padding: 0.8rem 1rem; gap: 0.3rem;
}
div.stRadio label { color: #c0c0e8 !important; font-size: 0.95rem !important; }

.stButton > button {
    background: #6c6ff5 !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 1rem !important;
    padding: 0.7rem 1.8rem !important; width: 100% !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #5558d4 !important;
    box-shadow: 0 4px 20px rgba(108,111,245,0.35) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    color: #ffffff !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
    font-size: 1.05rem !important; padding: 0.8rem 1.8rem !important;
    width: 100% !important; margin-top: 0.5rem !important;
}
.stDownloadButton > button:hover {
    box-shadow: 0 4px 20px rgba(34,197,94,0.3) !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #6c6ff5, #a855f7) !important;
    border-radius: 4px !important;
}
hr { border-color: #1a1a30 !important; margin: 1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def find_output_file(directory: str, base_path: str) -> Path:
    """Find the actual downloaded file — yt-dlp may change the extension."""
    base = Path(base_path)
    # Try exact path first
    if base.exists():
        return base
    # Try common extensions
    for ext in [".mp4", ".mp3", ".mkv", ".webm", ".m4a", ".mov", ".avi"]:
        candidate = base.with_suffix(ext)
        if candidate.exists():
            return candidate
    # Fall back: newest file in directory
    files = sorted(Path(directory).glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
    if files:
        return files[0]
    raise FileNotFoundError(f"No output file found in {directory}")

def download_video(url: str, fmt_key: str, out_dir: str, progress_cb=None) -> Path:
    ffmpeg = has_ffmpeg()

    if fmt_key == "mp3":
        ydl_fmt = "bestaudio/best"
        pp      = ([{"key": "FFmpegExtractAudio",
                     "preferredcodec": "mp3",
                     "preferredquality": "192"}] if ffmpeg else [])
        merge   = None
    elif fmt_key == "best":
        ydl_fmt = "bestvideo+bestaudio/best" if ffmpeg else "best"
        pp      = []
        merge   = "mp4"
    elif fmt_key.startswith("res_"):
        h       = fmt_key.replace("res_", "")
        ydl_fmt = (f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
                   if ffmpeg else f"best[height<={h}]/best")
        pp      = []
        merge   = "mp4"
    else:
        ydl_fmt = "best"
        pp      = []
        merge   = None

    out_tmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
    raw_path = [None]

    def hook(d):
        if d["status"] == "downloading" and progress_cb:
            raw = d.get("_percent_str", "0").replace("%", "").strip()
            try:    progress_cb(min(float(raw) / 100, 0.99))
            except: pass
        elif d["status"] == "finished":
            raw_path[0] = d.get("filename")

    opts = {
        "outtmpl":            out_tmpl,
        "format":             ydl_fmt,
        "noplaylist":         True,
        "progress_hooks":     [hook],
        "quiet":              True,
        "no_warnings":        True,
        "nocheckcertificate": True,
        "postprocessors":     pp,
    }
    if merge:
        opts["merge_output_format"] = merge

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not raw_path[0]:
            raw_path[0] = ydl.prepare_filename(info)

    return find_output_file(out_dir, raw_path[0])

# ── Session state ─────────────────────────────────────────────────────────────

for k, v in {"dl_bytes": None, "dl_filename": None, "error": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="masthead">
    <h1>Fetch</h1>
    <div class="sub">Video Downloader</div>
    <div class="plats">YouTube &nbsp;·&nbsp; TikTok &nbsp;·&nbsp; Instagram &nbsp;·&nbsp; Facebook &nbsp;·&nbsp; X / Twitter</div>
</div>
<div class="bar"></div>
""", unsafe_allow_html=True)

# ── STEP 1: URL ───────────────────────────────────────────────────────────────

st.markdown('<div class="step-label">① Paste your video link</div>', unsafe_allow_html=True)

url = st.text_input(
    label="url",
    placeholder="https://www.youtube.com/watch?v=...  or TikTok / Instagram / Facebook / X link",
    label_visibility="collapsed",
)

# ── STEP 2: Format ────────────────────────────────────────────────────────────

st.markdown('<div class="step-label">② Choose format</div>', unsafe_allow_html=True)

fmt_option = st.radio(
    "Format",
    options=[
        "⭐  Best quality  (Video + Audio)",
        "📺  1080p  (Video + Audio)",
        "📺  720p  (Video + Audio)",
        "🎵  MP3  (Audio only)",
    ],
    label_visibility="collapsed",
)

fmt_map = {
    "⭐  Best quality  (Video + Audio)": "best",
    "📺  1080p  (Video + Audio)":        "res_1080",
    "📺  720p  (Video + Audio)":         "res_720",
    "🎵  MP3  (Audio only)":             "mp3",
}
fmt_key = fmt_map[fmt_option]

if not has_ffmpeg():
    st.markdown(
        '<div class="info-box">ℹ️ FFmpeg not detected — MP3 conversion and HD merging '
        'require FFmpeg. "Best quality" single-stream will be used instead.</div>',
        unsafe_allow_html=True,
    )

# ── STEP 3: Download ──────────────────────────────────────────────────────────

st.markdown('<div class="step-label">③ Download</div>', unsafe_allow_html=True)

if st.button("⬇   Download Video", use_container_width=True):
    if not url or not url.strip():
        st.session_state.error    = "Please paste a video URL first."
        st.session_state.dl_bytes = None
    else:
        st.session_state.error    = None
        st.session_state.dl_bytes = None

        prog  = st.progress(0, text="Starting…")
        msg   = st.empty()
        msg.markdown('<div class="info-box">⬇ Connecting and downloading…</div>',
                     unsafe_allow_html=True)

        try:
            with tempfile.TemporaryDirectory() as tmp:

                def update(frac):
                    pct = int(frac * 100)
                    prog.progress(frac, text=f"Downloading… {pct}%")

                out_path = download_video(url.strip(), fmt_key, tmp, progress_cb=update)

                prog.progress(1.0, text="Processing…")
                msg.markdown('<div class="info-box">⚙️ Processing file…</div>',
                             unsafe_allow_html=True)

                # Read into memory before tempdir is deleted
                st.session_state.dl_bytes    = out_path.read_bytes()
                st.session_state.dl_filename = out_path.name

            prog.empty()
            msg.empty()

        except Exception as e:
            prog.empty()
            msg.empty()
            err = str(e)
            tip = ""
            if "login" in err.lower() or "private" in err.lower():
                tip = (" Instagram/Facebook private posts require login. "
                       "Only public content can be downloaded without cookies.")
            elif "unsupported url" in err.lower():
                tip = " This URL isn't supported. Try a direct link to the video post."
            st.session_state.error = f"{err}{tip}"

# ── Show error ────────────────────────────────────────────────────────────────

if st.session_state.error:
    st.markdown(
        f'<div class="error-box">❌ {st.session_state.error}</div>',
        unsafe_allow_html=True,
    )

# ── Show download button ──────────────────────────────────────────────────────

if st.session_state.dl_bytes and st.session_state.dl_filename:
    fname = st.session_state.dl_filename
    ext   = Path(fname).suffix.lower()
    mime  = "audio/mpeg" if ext == ".mp3" else "video/mp4"

    st.markdown(
        '<div class="success-box">✅ &nbsp;Done! Your file is ready — click below to save it.</div>',
        unsafe_allow_html=True,
    )

    st.download_button(
        label=f"💾  Save  {fname}",
        data=st.session_state.dl_bytes,
        file_name=fname,
        mime=mime,
        use_container_width=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="text-align:center; font-family:'DM Mono',monospace;
            font-size:0.65rem; letter-spacing:2px; color:#2a2a55; padding:0.5rem 0;">
    FETCH · POWERED BY YT-DLP · FOR PERSONAL USE ONLY
</div>
""", unsafe_allow_html=True)
