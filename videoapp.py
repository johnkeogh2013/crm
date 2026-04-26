"""
Fetch — Video Downloader
Streamlit web app powered by yt-dlp
Supports: YouTube, TikTok, Instagram, Facebook, X/Twitter, and more
"""

import streamlit as st
import yt_dlp
import os
import tempfile
import time
import ssl
import certifi
from pathlib import Path

# ── SSL fix (important for macOS / some cloud environments) ──────────────────

ssl._create_default_https_context = lambda: ssl.create_default_context(
    cafile=certifi.where()
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Fetch — Video Downloader",
    page_icon="⬇",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #080810;
    color: #f0f0ff;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 760px;
}

/* ── Masthead ── */
.masthead {
    text-align: center;
    padding: 3rem 0 2rem;
    border-bottom: 1px solid #1e1e35;
    margin-bottom: 2.5rem;
}
.masthead h1 {
    font-family: 'Playfair Display', serif;
    font-size: 4.5rem;
    font-weight: 900;
    letter-spacing: -2px;
    color: #ffffff;
    margin: 0;
    line-height: 1;
}
.masthead .tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 4px;
    color: #5555aa;
    text-transform: uppercase;
    margin-top: 0.6rem;
}
.masthead .platforms {
    font-size: 0.82rem;
    color: #6666aa;
    margin-top: 0.8rem;
    letter-spacing: 0.5px;
}

/* ── Accent strip ── */
.accent-strip {
    height: 3px;
    background: linear-gradient(90deg, #6c6ff5 0%, #a855f7 50%, #ec4899 100%);
    border-radius: 2px;
    margin-bottom: 2.5rem;
}

/* ── Section labels ── */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 3px;
    color: #5555aa;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Info card ── */
.info-card {
    background: #10101e;
    border: 1px solid #1e1e38;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin: 1.2rem 0;
}
.info-card .video-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    color: #ffffff;
    margin-bottom: 0.5rem;
    line-height: 1.3;
}
.info-card .meta-row {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
}
.info-card .meta-item {
    font-size: 0.8rem;
    color: #7777bb;
    font-family: 'DM Mono', monospace;
}
.info-card .meta-item span {
    color: #b0b0e0;
    font-weight: 500;
}

/* ── Platform badge ── */
.platform-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 2px;
    padding: 0.25rem 0.7rem;
    border-radius: 4px;
    margin-bottom: 0.8rem;
    text-transform: uppercase;
}
.badge-youtube   { background: #330a0a; color: #ff6060; border: 1px solid #661111; }
.badge-tiktok    { background: #33001a; color: #ff4488; border: 1px solid #660033; }
.badge-instagram { background: #330022; color: #e879a8; border: 1px solid #660044; }
.badge-facebook  { background: #001433; color: #6699ff; border: 1px solid #002266; }
.badge-twitter   { background: #001a33; color: #4db8ff; border: 1px solid #003366; }
.badge-other     { background: #1a1a33; color: #9999ff; border: 1px solid #333366; }

/* ── Success / Error boxes ── */
.success-box {
    background: #061a0f;
    border: 1px solid #1a4d2a;
    border-left: 3px solid #22dd77;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    color: #66ffaa;
    font-size: 0.9rem;
    margin: 1rem 0;
}
.error-box {
    background: #1a0608;
    border: 1px solid #4d1a20;
    border-left: 3px solid #ee3355;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    color: #ff8899;
    font-size: 0.9rem;
    margin: 1rem 0;
}
.info-box {
    background: #0a0a1f;
    border: 1px solid #22225a;
    border-left: 3px solid #6c6ff5;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    color: #9999dd;
    font-size: 0.85rem;
    margin: 1rem 0;
}

/* ── Streamlit widget overrides ── */
.stTextInput > div > div > input {
    background: #10101e !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
    color: #f0f0ff !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6c6ff5 !important;
    box-shadow: 0 0 0 2px rgba(108,111,245,0.2) !important;
}
.stTextInput > div > div > input::placeholder {
    color: #444466 !important;
}

.stButton > button {
    background: #6c6ff5 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.8rem !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: #5558d4 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(108,111,245,0.35) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* Download button — different colour */
.dl-btn .stButton > button {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
}
.dl-btn .stButton > button:hover {
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    box-shadow: 0 4px 20px rgba(34,197,94,0.3) !important;
}

.stSelectbox > div > div {
    background: #10101e !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
    color: #f0f0ff !important;
}
.stRadio > div {
    background: #10101e;
    border: 1px solid #1e1e38;
    border-radius: 8px;
    padding: 0.8rem 1rem;
}
.stRadio label {
    color: #c0c0e8 !important;
    font-size: 0.9rem !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #6c6ff5, #a855f7) !important;
    border-radius: 4px !important;
}

/* Thumbnail */
.thumb-wrap {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #1e1e38;
    margin-bottom: 1rem;
}

/* Divider */
.my-divider {
    height: 1px;
    background: #1a1a30;
    margin: 2rem 0;
}

/* Format option cards */
.fmt-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.8rem;
    margin: 0.8rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

PLATFORM_MAP = {
    "youtube.com": ("YouTube",   "badge-youtube"),
    "youtu.be":    ("YouTube",   "badge-youtube"),
    "tiktok.com":  ("TikTok",    "badge-tiktok"),
    "vm.tiktok.com":("TikTok",  "badge-tiktok"),
    "instagram.com":("Instagram","badge-instagram"),
    "instagr.am":  ("Instagram", "badge-instagram"),
    "facebook.com":("Facebook",  "badge-facebook"),
    "fb.watch":    ("Facebook",  "badge-facebook"),
    "twitter.com": ("X/Twitter", "badge-twitter"),
    "x.com":       ("X/Twitter", "badge-twitter"),
}

def detect_platform(url: str):
    for domain, (name, badge) in PLATFORM_MAP.items():
        if domain in url:
            return name, badge
    return "Video", "badge-other"

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def format_filesize(bytes_val):
    if not bytes_val:
        return "Unknown size"
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} GB"

def get_ydl_base_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
    }

def fetch_info(url: str) -> dict:
    opts = {**get_ydl_base_opts(), "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info

def build_format_choices(info: dict):
    """Return list of (label, format_id_or_key) tuples."""
    choices = []
    fmts    = info.get("formats", [])

    # Always offer these generic options
    choices.append(("⭐  Best quality  (Video + Audio)", "__best__"))
    choices.append(("🎵  Audio only  (MP3, 192kbps)",   "__mp3__"))

    # Collect notable video resolutions
    seen_heights = set()
    for f in reversed(fmts):
        h = f.get("height")
        if h and h not in seen_heights and f.get("vcodec", "none") != "none":
            seen_heights.add(h)
            ext   = f.get("ext", "mp4")
            fsize = format_filesize(f.get("filesize") or f.get("filesize_approx"))
            choices.append((f"🎬  {h}p  ({ext.upper()})  —  {fsize}", f"__res_{h}__"))
        if len(seen_heights) >= 4:
            break

    return choices

def download_video(url: str, fmt_key: str, out_dir: str, progress_cb=None) -> str:
    """Download and return the output file path."""
    ffmpeg_ok = _has_ffmpeg()

    if fmt_key == "__mp3__":
        ydl_fmt  = "bestaudio/best"
        pp       = ([{"key": "FFmpegExtractAudio",
                      "preferredcodec": "mp3",
                      "preferredquality": "192"}]
                    if ffmpeg_ok else [])
        merge    = None
    elif fmt_key == "__best__":
        ydl_fmt  = "bestvideo+bestaudio/best" if ffmpeg_ok else "best"
        pp       = []
        merge    = "mp4"
    elif fmt_key.startswith("__res_"):
        h        = fmt_key.replace("__res_", "")
        ydl_fmt  = (f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
                    if ffmpeg_ok else f"best[height<={h}]/best")
        pp       = []
        merge    = "mp4"
    else:
        ydl_fmt  = "best"
        pp       = []
        merge    = None

    out_path = [None]

    def hook(d):
        if d["status"] == "downloading" and progress_cb:
            raw = d.get("_percent_str", "0").replace("%", "").strip()
            try:    progress_cb(float(raw) / 100)
            except: pass
        elif d["status"] == "finished":
            out_path[0] = d.get("filename")
            if progress_cb:
                progress_cb(1.0)

    opts = {
        **get_ydl_base_opts(),
        "outtmpl":        os.path.join(out_dir, "%(title)s.%(ext)s"),
        "format":         ydl_fmt,
        "noplaylist":     True,
        "progress_hooks": [hook],
        "postprocessors": pp,
    }
    if merge:
        opts["merge_output_format"] = merge

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not out_path[0]:
            out_path[0] = ydl.prepare_filename(info)

    return out_path[0]

def _has_ffmpeg():
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def read_file_bytes(path: str) -> bytes:
    # Try the exact path first, then common post-processed alternatives
    for candidate in [path,
                      Path(path).with_suffix(".mp4"),
                      Path(path).with_suffix(".mp3"),
                      Path(path).with_suffix(".mkv"),
                      Path(path).with_suffix(".webm")]:
        if Path(candidate).exists():
            return Path(candidate).read_bytes(), str(candidate)
    raise FileNotFoundError(f"Could not find output file near: {path}")


# ── Session state defaults ────────────────────────────────────────────────────

for key, default in {
    "info":         None,
    "fmt_choices":  [],
    "selected_fmt": "__best__",
    "dl_bytes":     None,
    "dl_filename":  None,
    "error":        None,
    "fetching":     False,
    "downloading":  False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── UI ────────────────────────────────────────────────────────────────────────

# Masthead
st.markdown("""
<div class="masthead">
    <h1>Fetch</h1>
    <div class="tagline">Video Downloader</div>
    <div class="platforms">YouTube &nbsp;·&nbsp; TikTok &nbsp;·&nbsp; Instagram &nbsp;·&nbsp; Facebook &nbsp;·&nbsp; X/Twitter &nbsp;·&nbsp; and more</div>
</div>
<div class="accent-strip"></div>
""", unsafe_allow_html=True)

# ── URL Input ─────────────────────────────────────────────────────────────────

st.markdown('<div class="section-label">Video URL</div>', unsafe_allow_html=True)
url = st.text_input(
    label="url",
    placeholder="Paste a YouTube, TikTok, Instagram, Facebook or X link…",
    label_visibility="collapsed",
)

col_fetch, col_clear = st.columns([3, 1])
with col_fetch:
    fetch_clicked = st.button("🔍  Fetch Video Info", use_container_width=True)
with col_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.info        = None
        st.session_state.fmt_choices = []
        st.session_state.dl_bytes    = None
        st.session_state.dl_filename = None
        st.session_state.error       = None
        st.rerun()

# ── Fetch info ────────────────────────────────────────────────────────────────

if fetch_clicked:
    if not url or not url.strip():
        st.session_state.error = "Please paste a video URL first."
    else:
        st.session_state.info        = None
        st.session_state.fmt_choices = []
        st.session_state.dl_bytes    = None
        st.session_state.dl_filename = None
        st.session_state.error       = None

        with st.spinner("Fetching video info…"):
            try:
                info = fetch_info(url.strip())
                st.session_state.info       = info
                st.session_state.fmt_choices = build_format_choices(info)
            except Exception as e:
                err = str(e)
                if "login" in err.lower() or "private" in err.lower():
                    st.session_state.error = (
                        "⚠️  This content is private or requires login. "
                        "Instagram and Facebook private posts require cookie authentication."
                    )
                else:
                    st.session_state.error = f"Could not fetch video info:\n\n{err}"

# ── Show errors ───────────────────────────────────────────────────────────────

if st.session_state.error:
    st.markdown(
        f'<div class="error-box">❌ &nbsp;{st.session_state.error}</div>',
        unsafe_allow_html=True,
    )

# ── Show video info ───────────────────────────────────────────────────────────

if st.session_state.info:
    info   = st.session_state.info
    title  = info.get("title", "Unknown Title")
    dur    = format_duration(info.get("duration"))
    uploader = info.get("uploader") or info.get("channel") or "Unknown"
    views  = info.get("view_count")
    views_str = f"{views:,}" if views else "—"
    thumb  = info.get("thumbnail")
    plat_name, plat_badge = detect_platform(url or "")

    st.markdown('<div class="my-divider"></div>', unsafe_allow_html=True)

    # Platform badge
    st.markdown(
        f'<div class="platform-badge {plat_badge}">{plat_name}</div>',
        unsafe_allow_html=True,
    )

    # Thumbnail + metadata
    if thumb:
        st.image(thumb, use_container_width=True)

    st.markdown(f"""
    <div class="info-card">
        <div class="video-title">{title}</div>
        <div class="meta-row">
            <div class="meta-item">Duration &nbsp;<span>{dur}</span></div>
            <div class="meta-item">Uploader &nbsp;<span>{uploader}</span></div>
            <div class="meta-item">Views &nbsp;<span>{views_str}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Format picker ─────────────────────────────────────────────────────────

    st.markdown('<div class="my-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Format &amp; Quality</div>', unsafe_allow_html=True)

    fmt_labels = [c[0] for c in st.session_state.fmt_choices]
    fmt_keys   = [c[1] for c in st.session_state.fmt_choices]

    chosen_label = st.radio(
        "format",
        options=fmt_labels,
        label_visibility="collapsed",
    )
    chosen_key = fmt_keys[fmt_labels.index(chosen_label)]

    if not _has_ffmpeg():
        st.markdown(
            '<div class="info-box">ℹ️ &nbsp;FFmpeg is not installed on this server. '
            'MP3 conversion and HD merging require FFmpeg. '
            'Best single-file quality will be used instead.</div>',
            unsafe_allow_html=True,
        )

    # ── Download button ───────────────────────────────────────────────────────

    st.markdown('<div class="my-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Download</div>', unsafe_allow_html=True)

    st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
    dl_clicked = st.button("⬇   Download Video", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if dl_clicked:
        st.session_state.dl_bytes    = None
        st.session_state.dl_filename = None
        st.session_state.error       = None

        progress_bar  = st.progress(0, text="Starting download…")
        status_text   = st.empty()

        def update_progress(frac: float):
            pct = min(int(frac * 100), 100)
            progress_bar.progress(frac, text=f"Downloading… {pct}%")

        try:
            with tempfile.TemporaryDirectory() as tmp:
                status_text.markdown(
                    '<div class="info-box">⬇ &nbsp;Downloading…</div>',
                    unsafe_allow_html=True,
                )
                out_path = download_video(
                    url.strip(), chosen_key, tmp, progress_cb=update_progress
                )
                progress_bar.progress(1.0, text="Processing…")

                # Read bytes before tempdir is cleaned up
                file_bytes, real_path = read_file_bytes(out_path)
                st.session_state.dl_bytes    = file_bytes
                st.session_state.dl_filename = Path(real_path).name

            progress_bar.empty()
            status_text.empty()

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            err = str(e)
            tip = ""
            if "login" in err.lower() or "private" in err.lower():
                tip = " This content may be private or require login."
            st.session_state.error = f"Download failed:{tip}\n\n{err}"
            st.rerun()

    # ── Download link ─────────────────────────────────────────────────────────

    if st.session_state.dl_bytes and st.session_state.dl_filename:
        fname = st.session_state.dl_filename
        ext   = Path(fname).suffix.lower()
        mime  = "audio/mpeg" if ext == ".mp3" else "video/mp4"

        st.markdown(
            '<div class="success-box">✅ &nbsp;Ready! Click the button below to save your file.</div>',
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

st.markdown('<div class="my-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; font-family:'DM Mono',monospace;
            font-size:0.68rem; letter-spacing:2px; color:#333366; padding:1rem 0;">
    FETCH v6.0 &nbsp;·&nbsp; POWERED BY YT-DLP &nbsp;·&nbsp;
    FOR PERSONAL USE ONLY — RESPECT CONTENT CREATORS
</div>
""", unsafe_allow_html=True)
