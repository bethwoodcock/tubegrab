import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os

try:
    from pytubefix import YouTube
    from pytubefix.cli import on_progress
except ImportError:
    messagebox.showerror("Missing dependency", "Please install pytubefix:\n\npip install pytubefix")
    exit()

DOWNLOADS_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")

# ── Colours & fonts ──────────────────────────────────────────────────────────
BG        = "#0f0f0f"
SURFACE   = "#1a1a1a"
BORDER    = "#2a2a2a"
ACCENT    = "#ff4500"          # YouTube-ish red-orange
ACCENT2   = "#ff6a33"
TEXT      = "#f0f0f0"
MUTED     = "#888888"
FONT_TITLE = ("Georgia", 22, "bold")
FONT_BODY  = ("Courier New", 10)
FONT_BTN   = ("Courier New", 11, "bold")
FONT_SMALL = ("Courier New", 9)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("yt-dl")
        self.resizable(False, False)
        self.configure(bg=BG)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG, padx=32, pady=24)
        hdr.pack(fill="x")

        tk.Label(hdr, text="▶  yt-dl", font=FONT_TITLE,
                 bg=BG, fg=ACCENT).pack(anchor="w")
        tk.Label(hdr, text="paste a youtube url and hit download",
                 font=FONT_SMALL, bg=BG, fg=MUTED).pack(anchor="w")

        # ── Divider ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG, padx=32, pady=24)
        body.pack(fill="x")

        # URL entry
        tk.Label(body, text="URL", font=FONT_SMALL,
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 4))

        url_frame = tk.Frame(body, bg=BORDER, bd=0,
                             highlightthickness=1, highlightbackground=BORDER,
                             highlightcolor=ACCENT)
        url_frame.pack(fill="x", pady=(0, 16))

        self.url_var = tk.StringVar()
        self.entry = tk.Entry(url_frame, textvariable=self.url_var,
                              font=FONT_BODY, bg=SURFACE, fg=TEXT,
                              insertbackground=ACCENT, relief="flat",
                              bd=10, width=52)
        self.entry.pack(fill="x")
        self.entry.bind("<FocusIn>",  lambda e: url_frame.config(highlightbackground=ACCENT))
        self.entry.bind("<FocusOut>", lambda e: url_frame.config(highlightbackground=BORDER))

        # Format toggle
        fmt_row = tk.Frame(body, bg=BG)
        fmt_row.pack(fill="x", pady=(0, 20))

        tk.Label(fmt_row, text="format", font=FONT_SMALL,
                 bg=BG, fg=MUTED).pack(side="left", padx=(0, 10))

        self.fmt_var = tk.StringVar(value="audio")
        for label, val in [("audio only (m4a)", "audio"), ("video + audio (mp4)", "video")]:
            rb = tk.Radiobutton(fmt_row, text=label, variable=self.fmt_var, value=val,
                                font=FONT_SMALL, bg=BG, fg=TEXT,
                                selectcolor=BG, activebackground=BG,
                                activeforeground=ACCENT, cursor="hand2",
                                indicatoron=True)
            rb.pack(side="left", padx=(0, 16))

        # Download button
        self.btn = tk.Button(body, text="DOWNLOAD",
                             font=FONT_BTN, bg=ACCENT, fg=BG,
                             activebackground=ACCENT2, activeforeground=BG,
                             relief="flat", bd=0, padx=24, pady=10,
                             cursor="hand2", command=self.start_download)
        self.btn.pack(anchor="w")

        # ── Status area ───────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", pady=(16, 0))

        status_frame = tk.Frame(self, bg=SURFACE, padx=32, pady=16)
        status_frame.pack(fill="x")

        self.status_var = tk.StringVar(value="ready.")
        tk.Label(status_frame, textvariable=self.status_var,
                 font=FONT_SMALL, bg=SURFACE, fg=MUTED,
                 anchor="w", wraplength=420, justify="left").pack(fill="x")

        # Progress bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Red.Horizontal.TProgressbar",
                        troughcolor=BORDER, background=ACCENT,
                        thickness=4)
        self.progress = ttk.Progressbar(status_frame, style="Red.Horizontal.TProgressbar",
                                        mode="determinate", length=420)
        self.progress.pack(fill="x", pady=(8, 0))

        # ── Footer ────────────────────────────────────────────────────────────
        tk.Label(self, text=f"saving to  {DOWNLOADS_FOLDER}",
                 font=FONT_SMALL, bg=BG, fg=BORDER,
                 padx=32, pady=8).pack(anchor="w")

        self.center()

    def center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def set_status(self, msg, color=MUTED):
        self.status_var.set(msg)
        # find the label widget and update colour
        for w in self.winfo_children():
            if isinstance(w, tk.Frame):
                for c in w.winfo_children():
                    if isinstance(c, tk.Label) and c.cget("textvariable") == str(self.status_var):
                        c.config(fg=color)

    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            self.set_status("⚠  please paste a url first.", ACCENT)
            return
        self.btn.config(state="disabled", bg=BORDER)
        self.progress["value"] = 0
        self.set_status("fetching info…", MUTED)
        threading.Thread(target=self.download, args=(url,), daemon=True).start()

    def download(self, url):
        try:
            def progress_cb(stream, chunk, remaining):
                total = stream.filesize
                done  = total - remaining
                pct   = done / total * 100
                self.progress["value"] = pct
                self.set_status(f"downloading… {pct:.0f}%", TEXT)

            yt = YouTube(url, on_progress_callback=progress_cb)
            self.set_status(f"⬇  {yt.title}", TEXT)

            if self.fmt_var.get() == "audio":
                stream = yt.streams.get_audio_only()
            else:
                stream = yt.streams.get_highest_resolution()

            stream.download(output_path=DOWNLOADS_FOLDER)
            self.progress["value"] = 100
            self.set_status(f"✓  done — {yt.title}", "#55ff88")

        except Exception as e:
            self.set_status(f"✗  error: {e}", ACCENT)
        finally:
            self.btn.config(state="normal", bg=ACCENT)

if __name__ == "__main__":
    app = App()
    app.mainloop()
