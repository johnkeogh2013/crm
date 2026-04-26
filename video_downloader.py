"""
Fetch v6.0 — Video Downloader
Supports: YouTube, X/Twitter, Instagram, Facebook, TikTok (no watermark)
Run: python video_downloader.py
"""

import sys, os, subprocess, threading, platform
import tkinter as tk
from tkinter import filedialog, messagebox

# ── Auto-install deps ─────────────────────────────────────────────────────────

def ensure_deps():
    for pkg, pip_name in [("yt_dlp", "yt-dlp"), ("certifi", "certifi")]:
        try:
            __import__(pkg)
        except ImportError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", pip_name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

ensure_deps()
import yt_dlp

import ssl
def fix_ssl():
    try:
        import certifi
        ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ssl._create_default_https_context = ssl._create_unverified_context
fix_ssl()

# ── System helpers ────────────────────────────────────────────────────────────

def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

PLATFORMS = {
    "youtube.com": "YouTube",   "youtu.be":      "YouTube",
    "x.com":       "X/Twitter", "twitter.com":   "X/Twitter",
    "instagram.com":"Instagram", "instagr.am":    "Instagram",
    "facebook.com":"Facebook",  "fb.watch":       "Facebook",
    "fb.com":      "Facebook",
    "tiktok.com":  "TikTok",    "vm.tiktok.com": "TikTok",
}

PLATFORM_COLOURS = {
    "YouTube":   "#ff4040",
    "X/Twitter": "#1d9bf0",
    "Instagram": "#e1306c",
    "Facebook":  "#1877f2",
    "TikTok":    "#ff0050",
}

def detect_platform(url):
    for d, n in PLATFORMS.items():
        if d in url:
            return n
    return None

def open_file(path):
    try:
        s = platform.system()
        if s == "Darwin":    subprocess.Popen(["open", path])
        elif s == "Windows": os.startfile(path)
        else:                subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", str(e))

def open_folder(path):
    try:
        s = platform.system()
        if s == "Darwin":    subprocess.Popen(["open", path])
        elif s == "Windows": subprocess.Popen(["explorer", path])
        else:                subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ── Themes — every colour is explicitly set for full contrast ─────────────────

THEMES = {
    "Dark": {
        "BG":      "#111120",
        "SURF":    "#1e1e35",
        "SURF2":   "#28283f",
        "BORDER":  "#44446a",
        "ACCENT":  "#6c6ff5",
        "ACC_HO":  "#5558d4",
        "ACC_FG":  "#ffffff",   # text ON accent buttons
        "SEC_BG":  "#2e2e55",
        "SEC_FG":  "#ffffff",   # text ON secondary buttons
        "SEC_HO":  "#3a3a66",
        "DANGER":  "#e0304e",
        "DAN_FG":  "#ffffff",
        "SUCCESS": "#22dd77",
        "TEXT":    "#ffffff",
        "T_MED":   "#b8b8e0",
        "T_DIM":   "#666699",
    },
    "Midnight": {
        "BG":      "#071007",
        "SURF":    "#112211",
        "SURF2":   "#1a331a",
        "BORDER":  "#2a5a2a",
        "ACCENT":  "#00dd66",
        "ACC_HO":  "#00bb55",
        "ACC_FG":  "#000000",
        "SEC_BG":  "#1a3a1a",
        "SEC_FG":  "#ccffcc",
        "SEC_HO":  "#224422",
        "DANGER":  "#ff4444",
        "DAN_FG":  "#ffffff",
        "SUCCESS": "#00dd66",
        "TEXT":    "#ffffff",
        "T_MED":   "#99ee99",
        "T_DIM":   "#447744",
    },
    "Slate": {
        "BG":      "#060e1e",
        "SURF":    "#0d2040",
        "SURF2":   "#152c55",
        "BORDER":  "#2a4878",
        "ACCENT":  "#29b6f6",
        "ACC_HO":  "#039be5",
        "ACC_FG":  "#000000",
        "SEC_BG":  "#1a3060",
        "SEC_FG":  "#ffffff",
        "SEC_HO":  "#223870",
        "DANGER":  "#ef5350",
        "DAN_FG":  "#ffffff",
        "SUCCESS": "#26c6da",
        "TEXT":    "#ffffff",
        "T_MED":   "#88ccee",
        "T_DIM":   "#3a6090",
    },
    "Light": {
        "BG":      "#e8eaf6",
        "SURF":    "#ffffff",
        "SURF2":   "#d4d8f0",
        "BORDER":  "#9099cc",
        "ACCENT":  "#3730a3",
        "ACC_HO":  "#2a2480",
        "ACC_FG":  "#ffffff",
        "SEC_BG":  "#c0c5e8",
        "SEC_FG":  "#0a0a40",
        "SEC_HO":  "#b0b5dd",
        "DANGER":  "#c62828",
        "DAN_FG":  "#ffffff",
        "SUCCESS": "#2e7d32",
        "TEXT":    "#0a0a30",
        "T_MED":   "#303080",
        "T_DIM":   "#6060a8",
    },
}

# ── App ───────────────────────────────────────────────────────────────────────

APP_W  = 700   # window width
APP_H  = 820   # starting height — will cap at screen height

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fetch — Video Downloader")
        self.resizable(False, True)

        self._tn   = "Dark"
        self._T    = THEMES["Dark"]
        self._apct = 0.0
        self._tpct = 0.0
        self._ajob = None
        self._last = None
        self._hist = []
        self._wids = []   # (widget, role) for theme recolouring

        self.configure(bg=self._T["BG"])

        # Force window to correct size immediately
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        h  = min(APP_H, sh - 60)
        x  = (sw - APP_W) // 2
        y  = max(30, (sh - h) // 2)
        self.geometry(f"{APP_W}x{h}+{x}+{y}")
        self.update()

        self._build()

    # ── Theming ───────────────────────────────────────────────────────────────

    def _apply_theme(self, name):
        self._tn = name
        T = self._T = THEMES[name]
        self.configure(bg=T["BG"])

        for w, role in self._wids:
            try:
                if   role == "bg":     w.config(bg=T["BG"])
                elif role == "surf":   w.config(bg=T["SURF"])
                elif role == "surf2":  w.config(bg=T["SURF2"])
                elif role == "border": w.config(bg=T["BORDER"])
                elif role == "text":   w.config(fg=T["TEXT"],  bg=T["BG"])
                elif role == "tmed":   w.config(fg=T["T_MED"], bg=T["BG"])
                elif role == "tdim":   w.config(fg=T["T_DIM"], bg=T["BG"])
                elif role == "card":   w.config(bg=T["SURF"],  highlightbackground=T["BORDER"])
                elif role == "entry":  w.config(bg=T["SURF"],  fg=T["TEXT"], insertbackground=T["ACCENT"])
                elif role == "entro":  w.config(bg=T["SURF"],  fg=T["T_MED"], readonlybackground=T["SURF"])
                elif role == "acc":    w.config(bg=T["ACCENT"],  fg=T["ACC_FG"],  activebackground=T["ACC_HO"],  activeforeground=T["ACC_FG"])
                elif role == "sec":    w.config(bg=T["SEC_BG"],  fg=T["SEC_FG"],  activebackground=T["SEC_HO"],  activeforeground=T["SEC_FG"])
                elif role == "dan":    w.config(bg=T["DANGER"],  fg=T["DAN_FG"],  activebackground=T["DANGER"],  activeforeground=T["DAN_FG"])
                elif role == "sbtn":   w.config(bg=T["SURF"],    fg=T["T_MED"],   activebackground=T["SURF"],    activeforeground=T["ACCENT"])
                elif role == "tmed_s": w.config(fg=T["T_MED"],   bg=T["SURF2"])
            except tk.TclError:
                pass

        self._ref_tbtns()
        self._ref_fbtns()
        self._ref_qbtns()
        self.prog_c.config(bg=T["SURF2"])
        self.prog_c.itemconfig(self._pr, fill=T["ACCENT"])
        self._draw_strip(self._strip, APP_W)
        self._ref_hist()

    def _ref_tbtns(self):
        T = self._T
        for b, n in self._tbtns:
            if n == self._tn:
                b.config(bg=T["ACCENT"], fg=T["ACC_FG"],
                         activebackground=T["ACC_HO"], activeforeground=T["ACC_FG"])
            else:
                b.config(bg=T["SEC_BG"], fg=T["SEC_FG"],
                         activebackground=T["SEC_HO"], activeforeground=T["SEC_FG"])

    def _ref_fbtns(self):
        T = self._T; sel = self.fmt_var.get()
        for b, v in self._fbtns:
            if v == sel:
                b.config(bg=T["ACCENT"], fg=T["ACC_FG"],
                         activebackground=T["ACC_HO"], activeforeground=T["ACC_FG"])
            else:
                b.config(bg=T["SEC_BG"], fg=T["SEC_FG"],
                         activebackground=T["SEC_HO"], activeforeground=T["SEC_FG"])

    def _ref_qbtns(self):
        T = self._T; sel = self.qual_var.get(); mp3 = self.fmt_var.get() == "mp3"
        for b, v in self._qbtns:
            if mp3:
                b.config(bg=T["SURF2"], fg=T["T_DIM"], state="disabled",
                         activebackground=T["SURF2"], activeforeground=T["T_DIM"])
            elif v == sel:
                b.config(bg=T["ACCENT"], fg=T["ACC_FG"],
                         activebackground=T["ACC_HO"], activeforeground=T["ACC_FG"], state="normal")
            else:
                b.config(bg=T["SEC_BG"], fg=T["SEC_FG"],
                         activebackground=T["SEC_HO"], activeforeground=T["SEC_FG"], state="normal")

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _r(self, w, role):
        self._wids.append((w, role))
        return w

    def _build(self):
        T  = self._T
        PX = 36   # horizontal padding

        # ── Gradient strip ──
        strip = tk.Canvas(self, height=5, bg=T["BG"], highlightthickness=0, width=APP_W)
        strip.pack(fill="x")
        self._strip = self._r(strip, "bg")
        self._draw_strip(strip, APP_W)

        # ── Scrollable area ───────────────────────────────────────────────────
        wrap = self._r(tk.Frame(self, bg=T["BG"]), "bg")
        wrap.pack(fill="both", expand=True)

        self._cv = tk.Canvas(wrap, bg=T["BG"], highlightthickness=0, bd=0)
        sb = tk.Scrollbar(wrap, orient="vertical", command=self._cv.yview)
        self._cv.configure(yscrollcommand=sb.set)
        self._cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        inner = self._r(tk.Frame(self._cv, bg=T["BG"]), "bg")
        win   = self._cv.create_window((0, 0), window=inner, anchor="nw", width=APP_W)

        inner.bind("<Configure>", lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self.bind_all("<MouseWheel>", lambda e: self._cv.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ── HEADER ───────────────────────────────────────────────────────────
        hdr = self._r(tk.Frame(inner, bg=T["BG"], padx=PX, pady=22), "bg")
        hdr.pack(fill="x")

        self._r(tk.Label(hdr, text="Fetch",
                          font=("Georgia", 38, "bold"),
                          fg=T["TEXT"], bg=T["BG"]),
                "text").pack(side="left", anchor="s")

        sub = self._r(tk.Frame(hdr, bg=T["BG"]), "bg")
        sub.pack(side="left", padx=14, pady=(0, 5), anchor="s")
        self._r(tk.Label(sub, text="VIDEO DOWNLOADER",
                          font=("Helvetica", 10, "bold"),
                          fg=T["T_DIM"], bg=T["BG"]), "tdim").pack(anchor="w")
        self._r(tk.Label(sub, text="YouTube · X · Instagram · Facebook · TikTok",
                          font=("Helvetica", 10),
                          fg=T["T_MED"], bg=T["BG"]), "tmed").pack(anchor="w")

        exit_btn = tk.Button(hdr, text="✕  Exit",
                             font=("Helvetica", 12, "bold"),
                             bg=T["DANGER"], fg=T["DAN_FG"],
                             activebackground=T["DANGER"], activeforeground=T["DAN_FG"],
                             relief="flat", bd=0, padx=20, pady=12,
                             cursor="hand2", command=self.destroy)
        exit_btn.pack(side="right", anchor="n", pady=(4, 0))
        self._r(exit_btn, "dan")

        # ── THEME ─────────────────────────────────────────────────────────────
        self._hdiv(inner, PX)
        trow = self._r(tk.Frame(inner, bg=T["BG"], padx=PX, pady=14), "bg")
        trow.pack(fill="x")
        self._r(tk.Label(trow, text="THEME",
                          font=("Helvetica", 12, "bold"),
                          fg=T["T_MED"], bg=T["BG"]), "tmed").pack(side="left", padx=(0, 16))
        self._tbtns = []
        for name in THEMES:
            b = tk.Button(trow, text=name,
                          font=("Helvetica", 12, "bold"),
                          relief="flat", bd=0, padx=18, pady=9,
                          cursor="hand2",
                          command=lambda n=name: self._apply_theme(n))
            b.pack(side="left", padx=(0, 6))
            self._tbtns.append((b, name))
        self._ref_tbtns()

        # ── VIDEO URL ─────────────────────────────────────────────────────────
        self._hdiv(inner, PX)
        body = self._r(tk.Frame(inner, bg=T["BG"], padx=PX), "bg")
        body.pack(fill="x")

        self._slbl(body, "VIDEO URL", top=18)

        # URL card
        self._ucard = tk.Frame(body, bg=T["SURF"],
                               highlightbackground=T["BORDER"], highlightthickness=2)
        self._ucard.pack(fill="x", pady=(10, 0))
        self._r(self._ucard, "card")

        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self._on_url)

        self.url_e = self._r(
            tk.Entry(self._ucard, textvariable=self.url_var,
                     font=("Helvetica", 14), bg=T["SURF"], fg=T["TEXT"],
                     insertbackground=T["ACCENT"],
                     relief="flat", highlightthickness=0, bd=0),
            "entry")
        self.url_e.pack(side="left", fill="x", expand=True, ipady=17, padx=(18, 0))
        self.url_e.bind("<FocusIn>",
            lambda e: self._ucard.config(highlightbackground=self._T["ACCENT"]))
        self.url_e.bind("<FocusOut>",
            lambda e: self._ucard.config(highlightbackground=self._T["BORDER"]))

        ubf = self._r(tk.Frame(self._ucard, bg=T["SURF"]), "surf")
        ubf.pack(side="right", padx=10)
        self._sbtn(ubf, "PASTE", self._paste).pack(side="left", padx=(0, 4))
        self._sbtn(ubf, "✕",     self._clear, danger=True).pack(side="left")

        # Platform badge
        self.plat_var = tk.StringVar(value="")
        self.plat_lbl = self._r(
            tk.Label(body, textvariable=self.plat_var,
                     font=("Helvetica", 12, "bold"),
                     fg=T["SUCCESS"], bg=T["BG"]), "bg")
        self.plat_lbl.pack(anchor="w", pady=(10, 0))

        # ── FORMAT ────────────────────────────────────────────────────────────
        self._hdiv(inner, PX, top=18)
        self._slbl(body, "FORMAT", top=16)
        frow = self._r(tk.Frame(body, bg=T["BG"]), "bg")
        frow.pack(fill="x", pady=(10, 0))
        self.fmt_var = tk.StringVar(value="mp4")
        self._fbtns = []
        for lbl, val in [("🎬  MP4  (Video)", "mp4"), ("🎵  MP3  (Audio only)", "mp3")]:
            b = tk.Button(frow, text=lbl,
                          font=("Helvetica", 13, "bold"),
                          relief="flat", bd=0, padx=24, pady=13,
                          cursor="hand2",
                          command=lambda v=val: self._set_fmt(v))
            b.pack(side="left", padx=(0, 10))
            self._fbtns.append((b, val))
        self._ref_fbtns()

        # ── QUALITY ───────────────────────────────────────────────────────────
        self._hdiv(inner, PX, top=18)
        self._slbl(body, "QUALITY  (video only)", top=16)
        qrow = self._r(tk.Frame(body, bg=T["BG"]), "bg")
        qrow.pack(fill="x", pady=(10, 0))
        self.qual_var = tk.StringVar(value="best")
        self._qbtns = []
        for lbl, val in [("Best", "best"), ("1080p", "1080"), ("720p", "720"), ("480p", "480")]:
            b = tk.Button(qrow, text=lbl,
                          font=("Helvetica", 12),
                          relief="flat", bd=0, padx=22, pady=11,
                          cursor="hand2",
                          command=lambda v=val: self._set_qual(v))
            b.pack(side="left", padx=(0, 8))
            self._qbtns.append((b, val))
        self._ref_qbtns()

        # TikTok watermark note
        self.tiktok_lbl = self._r(
            tk.Label(body, text="",
                     font=("Helvetica", 10, "italic"),
                     fg=T["T_MED"], bg=T["BG"]), "tmed")
        self.tiktok_lbl.pack(anchor="w", pady=(8, 0))

        # ── SAVE TO ───────────────────────────────────────────────────────────
        self._hdiv(inner, PX, top=18)
        self._slbl(body, "SAVE TO", top=16)
        self._fcard = tk.Frame(body, bg=T["SURF"],
                               highlightbackground=T["BORDER"], highlightthickness=2)
        self._fcard.pack(fill="x", pady=(10, 0))
        self._r(self._fcard, "card")

        self.fold_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self._r(
            tk.Entry(self._fcard, textvariable=self.fold_var,
                     font=("Helvetica", 12), relief="flat",
                     highlightthickness=0, bd=0, state="readonly",
                     readonlybackground=T["SURF"],
                     bg=T["SURF"], fg=T["T_MED"]),
            "entro"
        ).pack(side="left", fill="x", expand=True, ipady=14, padx=(18, 0))

        fbf = self._r(tk.Frame(self._fcard, bg=T["SURF"]), "surf")
        fbf.pack(side="right", padx=10)
        self._sbtn(fbf, "BROWSE", self._browse).pack(side="left", padx=(0, 8))
        self._sbtn(fbf, "OPEN", lambda: open_folder(self.fold_var.get())).pack(side="left")

        # ── ACTION BUTTONS ────────────────────────────────────────────────────
        self._hdiv(inner, PX, top=18)
        arow = self._r(tk.Frame(inner, bg=T["BG"], padx=PX, pady=20), "bg")
        arow.pack(fill="x")

        self.dl_btn = tk.Button(arow, text="⬇   Download",
                                font=("Helvetica", 15, "bold"),
                                bg=T["ACCENT"], fg=T["ACC_FG"],
                                activebackground=T["ACC_HO"], activeforeground=T["ACC_FG"],
                                relief="flat", bd=0, pady=18, cursor="hand2",
                                command=self._start_dl)
        self.dl_btn.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self._r(self.dl_btn, "acc")

        self.play_btn = tk.Button(arow, text="▶   Play Last",
                                  font=("Helvetica", 15, "bold"),
                                  bg=T["SEC_BG"], fg=T["SEC_FG"],
                                  activebackground=T["SEC_HO"], activeforeground=T["SEC_FG"],
                                  relief="flat", bd=0, pady=18, padx=26,
                                  cursor="hand2", command=self._play_last,
                                  state="disabled")
        self.play_btn.pack(side="left")
        self._r(self.play_btn, "sec")

        # ── PROGRESS ──────────────────────────────────────────────────────────
        pbody = self._r(tk.Frame(inner, bg=T["BG"], padx=PX), "bg")
        pbody.pack(fill="x", pady=(0, 4))

        self.prog_c = tk.Canvas(pbody, height=8, bg=T["SURF2"],
                                highlightthickness=0)
        self.prog_c.pack(fill="x")
        self._pr = self.prog_c.create_rectangle(0, 0, 0, 8, fill=T["ACCENT"], outline="")

        srow = self._r(tk.Frame(pbody, bg=T["BG"]), "bg")
        srow.pack(fill="x", pady=(10, 0))

        self.pct_v = tk.StringVar(value="")
        self.spd_v = tk.StringVar(value="")
        self.eta_v = tk.StringVar(value="")

        self._r(tk.Label(srow, textvariable=self.pct_v,
                          font=("Georgia", 30, "bold"),
                          fg=T["TEXT"], bg=T["BG"],
                          width=5, anchor="w"), "text").pack(side="left")

        rs = self._r(tk.Frame(srow, bg=T["BG"]), "bg")
        rs.pack(side="right")
        self._r(tk.Label(rs, textvariable=self.spd_v,
                          font=("Helvetica", 11),
                          fg=T["T_MED"], bg=T["BG"]), "tmed").pack(anchor="e")
        self._r(tk.Label(rs, textvariable=self.eta_v,
                          font=("Helvetica", 11),
                          fg=T["T_DIM"], bg=T["BG"]), "tdim").pack(anchor="e")

        self.stat_v = tk.StringVar(value="Ready  —  paste a URL and hit Download")
        self.stat_l = self._r(
            tk.Label(pbody, textvariable=self.stat_v,
                     font=("Helvetica", 12), fg=T["T_DIM"],
                     bg=T["BG"], wraplength=620, justify="left"),
            "bg")
        self.stat_l.pack(anchor="w", pady=(8, 0))

        # ── HISTORY ───────────────────────────────────────────────────────────
        self._hdiv(inner, PX, top=16)
        hbody = self._r(tk.Frame(inner, bg=T["BG"], padx=PX, pady=14), "bg")
        hbody.pack(fill="x")
        self._slbl(hbody, "RECENT DOWNLOADS")
        self._hframe = self._r(tk.Frame(hbody, bg=T["BG"]), "bg")
        self._hframe.pack(fill="x", pady=(8, 0))
        self._ref_hist()

        # ── FOOTER ────────────────────────────────────────────────────────────
        self._hdiv(inner, PX, top=10)
        ftr = self._r(tk.Frame(inner, bg=T["BG"], padx=PX, pady=12), "bg")
        ftr.pack(fill="x")
        self._r(tk.Label(ftr,
                          text="FFmpeg required for MP3 export and HD merging  •  TikTok: watermark-free via yt-dlp",
                          font=("Helvetica", 10), fg=T["T_DIM"], bg=T["BG"]),
                "tdim").pack(side="left")
        self._r(tk.Label(ftr, text="v6.0",
                          font=("Helvetica", 10), fg=T["T_DIM"], bg=T["BG"]),
                "tdim").pack(side="right")

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _hdiv(self, parent, pad, top=0):
        f = tk.Frame(parent, height=1, bg=self._T["BORDER"])
        f.pack(fill="x", padx=pad, pady=(top, 0))
        self._r(f, "border")

    def _slbl(self, parent, text, top=0):
        self._r(
            tk.Label(parent, text=text,
                     font=("Helvetica", 12, "bold"),
                     fg=self._T["T_MED"], bg=self._T["BG"]),
            "tmed"
        ).pack(anchor="w", pady=(top, 0))

    def _sbtn(self, parent, text, cmd, danger=False):
        T  = self._T
        fg = T["DANGER"] if danger else T["T_MED"]
        ho = T["DANGER"] if danger else T["ACCENT"]
        b  = tk.Button(parent, text=text,
                       font=("Helvetica", 11, "bold"),
                       bg=T["SURF"], fg=fg,
                       activebackground=T["SURF"], activeforeground=ho,
                       relief="flat", bd=0, padx=14, pady=8,
                       cursor="hand2", command=cmd)
        b.bind("<Enter>", lambda e, b=b, c=ho: b.config(fg=c))
        b.bind("<Leave>", lambda e, b=b, c=fg: b.config(fg=c))
        self._r(b, "sbtn")
        return b

    def _draw_strip(self, c, w):
        c.delete("all")
        T = self._T
        def h2r(h):
            h = h.lstrip("#")
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r1, g1, b1 = h2r(T["ACCENT"])
        r2, g2, b2 = h2r(T["ACC_HO"])
        for i in range(max(w, 1)):
            t = i / max(w, 1)
            r = int(r1 + t*(r2-r1))
            g = int(g1 + t*(g2-g1))
            b = int(b1 + t*(b2-b1))
            c.create_line(i, 0, i, 5, fill=f"#{r:02x}{g:02x}{b:02x}")

    # ── Controls ─────────────────────────────────────────────────────────────

    def _set_fmt(self, v):
        self.fmt_var.set(v)
        self._ref_fbtns()
        self._ref_qbtns()

    def _set_qual(self, v):
        self.qual_var.set(v)
        self._ref_qbtns()

    def _paste(self):
        try:
            self.url_var.set(self.clipboard_get().strip())
        except tk.TclError:
            pass

    def _clear(self):
        self.url_var.set("")
        self.plat_var.set("")
        self.pct_v.set("")
        self.spd_v.set("")
        self.eta_v.set("")
        self.tiktok_lbl.config(text="")
        self._sprog(0)
        self.stat_v.set("Ready  —  paste a URL and hit Download")
        self.stat_l.config(fg=self._T["T_DIM"])
        self.url_e.focus()

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.fold_var.get())
        if d:
            self.fold_var.set(d)

    def _on_url(self, *_):
        url = self.url_var.get().strip()
        p   = detect_platform(url)
        col = PLATFORM_COLOURS.get(p, self._T["SUCCESS"])
        if p:
            icons = {
                "YouTube":   "▶  YouTube",
                "X/Twitter": "✦  X / Twitter",
                "Instagram": "◈  Instagram",
                "Facebook":  "f  Facebook",
                "TikTok":    "♪  TikTok  (watermark-free)",
            }
            self.plat_var.set(icons.get(p, p) + "  detected")
            self.plat_lbl.config(fg=col)
            if p == "TikTok":
                self.tiktok_lbl.config(
                    text="ℹ  TikTok videos will be downloaded without watermark via yt-dlp")
            else:
                self.tiktok_lbl.config(text="")
        elif url:
            self.plat_var.set("⚠  Unsupported platform")
            self.plat_lbl.config(fg=self._T["DANGER"])
            self.tiktok_lbl.config(text="")
        else:
            self.plat_var.set("")
            self.tiktok_lbl.config(text="")

    def _sprog(self, pct):
        self.prog_c.update_idletasks()
        W = self.prog_c.winfo_width() or (APP_W - 72)
        self.prog_c.coords(self._pr, 0, 0, int(W * pct / 100), 8)

    def _animate(self):
        diff = self._tpct - self._apct
        if abs(diff) > 0.3:
            self._apct += diff * 0.14
            self._sprog(self._apct)
            self._ajob = self.after(16, self._animate)
        else:
            self._apct = self._tpct
            self._sprog(self._apct)
            self._ajob = None

    def _kanim(self):
        if self._ajob is None:
            self._animate()

    def _play_last(self):
        if self._last and os.path.isfile(self._last):
            open_file(self._last)
        else:
            messagebox.showinfo("No file", "No downloaded file found.")

    def _ref_hist(self):
        T = self._T
        for w in self._hframe.winfo_children():
            w.destroy()
        if not self._hist:
            self._r(
                tk.Label(self._hframe, text="No downloads yet",
                         font=("Helvetica", 11), fg=T["T_DIM"], bg=T["BG"]),
                "tdim"
            ).pack(anchor="w")
            return
        for title, path in self._hist:
            row = self._r(tk.Frame(self._hframe, bg=T["SURF2"]), "surf2")
            row.pack(fill="x", pady=(0, 5))
            short = title[:58] + "…" if len(title) > 58 else title
            ext   = os.path.splitext(path)[1].upper().lstrip(".") if path else ""
            icon  = "🎵" if ext == "MP3" else "🎬"
            self._r(
                tk.Label(row, text=f"   {icon}  {short}",
                         font=("Helvetica", 11), fg=T["T_MED"],
                         bg=T["SURF2"], anchor="w"),
                "tmed_s"
            ).pack(side="left", fill="x", expand=True, ipady=10, padx=(4, 0))

            def mk_p(p=path):
                return lambda: (open_file(p) if os.path.isfile(p)
                                else messagebox.showinfo("Missing", "File not found."))
            def mk_f(p=path):
                return lambda: open_folder(os.path.dirname(p))

            tk.Button(row, text="▶", font=("Helvetica", 11, "bold"),
                      bg=T["ACCENT"], fg=T["ACC_FG"],
                      activebackground=T["ACC_HO"], activeforeground=T["ACC_FG"],
                      relief="flat", bd=0, padx=14, pady=10,
                      cursor="hand2", command=mk_p(path)).pack(side="right", padx=(2, 4))
            tk.Button(row, text="📁", font=("Helvetica", 11),
                      bg=T["SEC_BG"], fg=T["SEC_FG"],
                      activebackground=T["SEC_HO"], activeforeground=T["SEC_FG"],
                      relief="flat", bd=0, padx=12, pady=10,
                      cursor="hand2", command=mk_f(path)).pack(side="right", padx=(0, 2))

    # ── Download ──────────────────────────────────────────────────────────────

    def _start_dl(self):
        T      = self._T
        url    = self.url_var.get().strip()
        folder = self.fold_var.get().strip()

        if not url:
            messagebox.showwarning("No URL", "Please paste a video URL first.")
            return
        plat = detect_platform(url)
        if not plat:
            messagebox.showerror("Unsupported URL",
                                 "Supported: YouTube, X/Twitter, Instagram, Facebook, TikTok")
            return
        if not folder:
            messagebox.showwarning("No folder", "Please choose an output folder.")
            return

        os.makedirs(folder, exist_ok=True)
        self.dl_btn.config(state="disabled", text="Downloading…",
                           bg=T["SURF2"], fg=T["T_DIM"])
        self.play_btn.config(state="disabled")
        self.url_e.config(state="disabled")
        self._apct = 0.0; self._tpct = 0.0; self._sprog(0)
        self.pct_v.set("0%"); self.spd_v.set(""); self.eta_v.set("")
        self.stat_v.set("Connecting…")
        self.stat_l.config(fg=T["T_MED"])
        self.prog_c.itemconfig(self._pr, fill=T["ACCENT"])

        fmt = self.fmt_var.get()
        threading.Thread(target=self._dl_thread,
                         args=(url, folder, plat, fmt), daemon=True).start()

    def _dl_thread(self, url, folder, plat, fmt):
        ffmpeg = has_ffmpeg()
        out    = [None]

        if fmt == "mp3":
            ydl_fmt = "bestaudio/best"
            pp = ([{"key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"}]
                  if ffmpeg else [])
            tmpl  = os.path.join(folder, "%(title)s.%(ext)s")
            merge = None
        else:
            q = self.qual_var.get()
            if plat == "TikTok":
                # yt-dlp's tiktok extractor removes watermark by default
                ydl_fmt = "best"
            elif q == "best":
                ydl_fmt = ("bestvideo+bestaudio/best"
                           if (plat == "YouTube" and ffmpeg) else "best")
            else:
                ydl_fmt = (f"bestvideo[height<={q}]+bestaudio/best[height<={q}]"
                           if ffmpeg else f"best[height<={q}]/best")
            pp    = []
            tmpl  = os.path.join(folder, "%(title)s.%(ext)s")
            merge = "mp4"

        def hook(d):
            if d["status"] == "downloading":
                raw = d.get("_percent_str", "0").strip().replace("%", "")
                try:    pct = float(raw)
                except: pct = 0.0
                spd = d.get("_speed_str", "").strip()
                eta = d.get("_eta_str", "").strip()
                self.after(0, lambda p=pct, s=spd, e=eta: self._tick(p, s, e))
            elif d["status"] == "finished":
                out[0] = d.get("filename")
                self.after(0, lambda: self._tick(100, "", ""))
                self.after(0, lambda: self.stat_v.set("Processing…"))

        opts = {
            "outtmpl":            tmpl,
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

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info  = ydl.extract_info(url, download=True)
                title = info.get("title") or info.get("id", "video")
                if not out[0]:
                    out[0] = ydl.prepare_filename(info)
            self.after(0, lambda t=title, p=out[0]: self._on_ok(t, p))
        except yt_dlp.utils.DownloadError as e:
            self.after(0, lambda msg=str(e): self._on_err(msg))

    def _tick(self, pct, spd, eta):
        self._tpct = pct
        self._kanim()
        self.pct_v.set(f"{pct:.0f}%")
        if spd: self.spd_v.set(f"↓  {spd}")
        if eta: self.eta_v.set(f"ETA  {eta}")
        self.stat_v.set("Downloading…")
        self.stat_l.config(fg=self._T["T_MED"])

    def _on_ok(self, title, path):
        T = self._T
        self._tpct = 100; self._kanim()
        self.pct_v.set("100%"); self.spd_v.set(""); self.eta_v.set("Complete")
        self.stat_v.set(f"✓  {title}")
        self.stat_l.config(fg=T["SUCCESS"])
        self.prog_c.itemconfig(self._pr, fill=T["SUCCESS"])
        self.dl_btn.config(state="normal", text="⬇   Download",
                           bg=T["ACCENT"], fg=T["ACC_FG"])
        self.url_e.config(state="normal")
        self._last = path
        self.play_btn.config(state="normal",
                             bg=T["SEC_BG"], fg=T["SEC_FG"])
        self._hist.insert(0, (title, path))
        self._hist = self._hist[:6]
        self._ref_hist()

    def _on_err(self, err):
        T = self._T
        self._tpct = 0; self._apct = 0; self._sprog(0)
        self.pct_v.set(""); self.spd_v.set(""); self.eta_v.set("")
        tip = ("\n\nTip: For Instagram/Facebook you may need to be logged in.\n"
               "Export cookies from your browser to a cookies.txt file."
               if any(p in err.lower() for p in ["login", "private", "instagram", "facebook"])
               else "")
        self.stat_v.set("Download failed")
        self.stat_l.config(fg=T["DANGER"])
        self.dl_btn.config(state="normal", text="⬇   Download",
                           bg=T["ACCENT"], fg=T["ACC_FG"])
        self.url_e.config(state="normal")
        messagebox.showerror("Download Failed", err + tip)


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
