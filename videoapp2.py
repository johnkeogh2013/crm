"""
Fetch — Video Downloader
Paste a URL ? choose format ? click Download ? save file.
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

# SSL Fix
ssl._create_default_https_context = lambda: ssl.create_default_context(
    cafile=certifi.where()
)

# Page config
st.set_page_config(
    page_title="Fetch — Video Downloader",
    page_icon="??",
    layout="centered",
)

# CSS (kept your beautiful styling)
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
.success-box, .error-box, .info-box {
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-size: 0.9rem; margin: 1rem 0;
}
.success-box { background: #061a0f; border: 1px solid #1a4d2a; border-left: 3px solid #22dd77; color: #66ffaa; }
.error-box { background: #1a0608; border: 1px solid #4d1a20; border-left: 3px solid #ee3355; color: #ff8899; }
.info-box { background: #0a0a1f; border: 1px solid #22225a; border-left: 3px solid #6c6ff5; color: #9999dd; }

.stButton > button {
    background: #6c6ff5 !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 1rem !important;
    padding: 0.7rem 1.8rem !important; width: 100% !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    color: #ffffff !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
    padding: 0.8rem 1.8rem !important; width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# Helpers
def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def download_video(url: str, fmt_key: str, out_dir: str, progress_cb=None) -> Path:
    ffmpeg = has_ffmpeg()

    # Format selection
    if fmt_key == "mp3":
        ydl_fmt = "bestaudio/best"
        pp = ([{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}] if ffmpeg else [])
        merge = None
    elif fmt_key == "best":
        ydl_fmt = "bestvideo+bestaudio/best" if ffmpeg else "best"
        pp = []
        merge = "mp4"
    elif fmt_key.startswith("res_"):
        h = fmt_key.replace("res_", "")
        ydl_fmt = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]" if ffmpeg else f"best[height<={h}]/best"
        pp = []
        merge = "mp4"
    else:
        ydl_fmt = "best"
        pp = []
        merge = None

    out_tmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
    raw_path = [None]

    def hook(d):
        if d["status"] == "downloading" and progress_cb:
            try:
                pct = float(d.get("_percent_str", "0").replace("%", "").strip()) / 100
                progress_cb(min(pct, 0.99))
            except:
                pass
        elif d["status"] == "finished":
            raw_path[0] = d.get("filename")

    # === STRONG 403 FIXES ===
    opts = {
        "outtmpl": out_tmpl,
        "format": ydl_fmt,
        "noplaylist": True,
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "postprocessors": pp,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "android", "web", "tv"],   # Most effective combo right now
            }
        },
        "force_ipv4": True,          # Helps bypass many blocks
        "retries": 10,
        "fragment_retries": 10,
    }

    if merge:
        opts["merge_output_format"] = merge

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not raw_path[0]:
            raw_path[0] = ydl.prepare_filename(info)

    # Find the actual file
    base = Path(raw_path[0])
    if base.exists():
        return base
    for ext in [".mp4", ".mkv", ".webm", ".m4a", ".mp3"]:
        candidate = base.with_suffix(ext)
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Downloaded file not found")

# Session state
for k, v in {"dl_bytes": None, "dl_filename": None, "error": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# UI
st.markdown("""
<div class="masthead">
    <h1>Fetch</h1>
    <div class="sub">Video Downloader</div>
    <div class="plats">YouTube · TikTok · Instagram · Facebook · X / Twitter</div>
</div>
<div class="bar"></div>
""", unsafe_allow_html=True)

st.markdown('<div class="step-label">? Paste your video link</div>', unsafe_allow_html=True)
url = st.text_input("url", placeholder="https://www.youtube.com/watch?v=... or TikTok / Instagram link", label_visibility="collapsed")

st.markdown('<div class="step-label">? Choose format</div>', unsafe_allow_html=True)
fmt_option = st.radio(
    "Format",
    options=[
        "? Best quality (Video + Audio)",
        "?? 1080p (Video + Audio)",
        "?? 720p (Video + Audio)",
        "?? MP3 (Audio only)",
    ],
    label_visibility="collapsed",
)

fmt_map = {
    "? Best quality (Video + Audio)": "best",
    "?? 1080p (Video + Audio)": "res_1080",
    "?? 720p (Video + Audio)": "res_720",
    "?? MP3 (Audio only)": "mp3",
}
fmt_key = fmt_map[fmt_option]

if not has_ffmpeg():
    st.markdown('<div class="info-box">?? FFmpeg not detected — some features limited.</div>', unsafe_allow_html=True)

st.markdown('<div class="step-label">? Download</div>', unsafe_allow_html=True)

if st.button("?? Download Video", use_container_width=True):
    if not url or not url.strip():
        st.session_state.error = "Please paste a video URL first."
    else:
        st.session_state.error = None
        st.session_state.dl_bytes = None

        prog = st.progress(0, text="Starting…")
        msg = st.empty()
        msg.markdown('<div class="info-box">?? Connecting and downloading…</div>', unsafe_allow_html=True)

        try:
            with tempfile.TemporaryDirectory() as tmp:
                def update(frac):
                    prog.progress(frac, text=f"Downloading… {int(frac*100)}%")

                out_path = download_video(url.strip(), fmt_key, tmp, progress_cb=update)

                prog.progress(1.0, text="Finalizing…")
                st.session_state.dl_bytes = out_path.read_bytes()
                st.session_state.dl_filename = out_path.name

            prog.empty()
            msg.empty()

        except Exception as e:
            prog.empty()
            msg.empty()
            err = str(e)
            st.session_state.error = f"Error: {err}"

# Show error
if st.session_state.error:
    st.markdown(f'<div class="error-box">? {st.session_state.error}</div>', unsafe_allow_html=True)

# Show download button
if st.session_state.dl_bytes and st.session_state.dl_filename:
    fname = st.session_state.dl_filename
    ext = Path(fname).suffix.lower()
    mime = "audio/mpeg" if ext == ".mp3" else "video/mp4"

    st.markdown('<div class="success-box">? Done! Click below to save it.</div>', unsafe_allow_html=True)

    st.download_button(
        label=f"?? Save {fname}",
        data=st.session_state.dl_bytes,
        file_name=fname,
        mime=mime,
        use_container_width=True,
    )

st.markdown("---")
st.markdown("""
<div style="text-align:center; font-family:'DM Mono',monospace; font-size:0.65rem; color:#2a2a55;">
    FETCH · POWERED BY YT-DLP · PERSONAL USE ONLY
</div>
""", unsafe_allow_html=True)