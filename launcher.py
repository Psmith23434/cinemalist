import tkinter as tk
from tkinter import font as tkfont
import subprocess
import threading
import os
import sys
import webbrowser
import time

# ── paths ───────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
VENV_PYTHON = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")
VENV_ALEMBIC= os.path.join(BACKEND_DIR, "venv", "Scripts", "alembic.exe")
VENV_UVICORN= os.path.join(BACKEND_DIR, "venv", "Scripts", "uvicorn.exe")

# ── palette (cinema dark theme) ────────────────────────────────────────────
BG          = "#0f0e0d"
SURFACE     = "#1a1917"
SURFACE2    = "#222120"
BORDER      = "#2e2c2a"
TEXT        = "#e8e6e1"
TEXT_MUTED  = "#7a7874"
TEXT_FAINT  = "#4a4845"
ACCENT      = "#e8b84b"        # warm gold — cinema feel
ACCENT_DIM  = "#b8922d"
RED         = "#d16060"
GREEN       = "#6daa55"
BLUE        = "#5591c7"
RADIUS      = 10

# ── state ───────────────────────────────────────────────────────────────────
server_proc   = None
server_thread = None
log_lines     = []

# ─────────────────────────────────────────────────────────────────────────────
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg=ACCENT, fg=BG,
                 width=180, height=42, radius=8, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=SURFACE, highlightthickness=0, bd=0, **kw)
        self._bg = bg; self._fg = fg; self._cmd = command
        self._text = text; self._r = radius
        self._w = width; self._h = height
        self._draw(bg)
        self.bind("<Enter>",      self._on_enter)
        self.bind("<Leave>",      self._on_leave)
        self.bind("<Button-1>",   self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        self.create_arc(x1,y1,x1+2*r,y1+2*r, start=90,  extent=90, style="pieslice",**kw)
        self.create_arc(x2-2*r,y1,x2,y1+2*r, start=0,   extent=90, style="pieslice",**kw)
        self.create_arc(x1,y2-2*r,x1+2*r,y2, start=180, extent=90, style="pieslice",**kw)
        self.create_arc(x2-2*r,y2-2*r,x2,y2, start=270, extent=90, style="pieslice",**kw)
        self.create_rectangle(x1+r,y1,x2-r,y2,**kw)
        self.create_rectangle(x1,y1+r,x2,y2-r,**kw)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(1,1,self._w-1,self._h-1,self._r, fill=color, outline="")
        self.create_text(self._w//2, self._h//2, text=self._text,
                         fill=self._fg, font=("Segoe UI Semibold",10))

    def _on_enter(self,e):  self._draw(self._darken(self._bg, 20))
    def _on_leave(self,e):  self._draw(self._bg)
    def _on_click(self,e):  self._draw(self._darken(self._bg, 40))
    def _on_release(self,e):
        self._draw(self._bg)
        if self._cmd: self._cmd()

    @staticmethod
    def _darken(hex_color, amount):
        hex_color = hex_color.lstrip("#")
        r,g,b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
        r,g,b = max(0,r-amount), max(0,g-amount), max(0,b-amount)
        return f"#{r:02x}{g:02x}{b:02x}"

    def configure_color(self, bg=None, fg=None, text=None):
        if bg:   self._bg = bg
        if fg:   self._fg = fg
        if text: self._text = text
        self._draw(self._bg)


# ─────────────────────────────────────────────────────────────────────────────
class StatusDot(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, width=12, height=12,
                         bg=SURFACE, highlightthickness=0, **kw)
        self._state = "idle"
        self._anim_id = None
        self._phase = 0
        self.set("idle")

    def set(self, state):
        self._state = state
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        colors = {"idle": TEXT_FAINT, "running": GREEN, "stopping": RED, "migrating": ACCENT}
        c = colors.get(state, TEXT_FAINT)
        if state in ("running", "migrating"):
            self._pulse(c)
        else:
            self.delete("all")
            self.create_oval(2,2,10,10, fill=c, outline="")

    def _pulse(self, color):
        self._phase = (self._phase + 1) % 20
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        scale = 0.6 + 0.4 * abs(self._phase - 10) / 10
        r2 = min(255, int(r * scale))
        g2 = min(255, int(g * scale))
        b2 = min(255, int(b * scale))
        c2 = f"#{r2:02x}{g2:02x}{b2:02x}"
        self.delete("all")
        self.create_oval(2,2,10,10, fill=c2, outline="")
        self._anim_id = self.after(80, lambda: self._pulse(color))


# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CinemaList Launcher")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("520x580")
        self._center()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = 520, 580
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # header bar
        header = tk.Frame(self, bg=SURFACE, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        # film-reel logo drawn with canvas
        logo = tk.Canvas(header, width=36, height=36,
                         bg=SURFACE, highlightthickness=0)
        logo.place(x=16, y=14)
        logo.create_oval(2,2,34,34, outline=ACCENT, width=2)
        logo.create_oval(14,14,22,22, fill=ACCENT, outline="")
        for angle, dx, dy in [(0,16,4),(60,26,10),(120,26,22),(180,16,28),(240,6,22),(300,6,10)]:
            logo.create_oval(dx-3,dy-3,dx+3,dy+3, fill=ACCENT, outline="")

        tk.Label(header, text="CinemaList", font=("Segoe UI Semibold",15),
                 fg=TEXT, bg=SURFACE).place(x=60, y=13)
        tk.Label(header, text="Backend Launcher", font=("Segoe UI",9),
                 fg=TEXT_MUTED, bg=SURFACE).place(x=61, y=35)

        # divider
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # status card
        status_frame = tk.Frame(self, bg=SURFACE2, pady=16)
        status_frame.pack(fill="x", padx=16, pady=(14,0))

        row = tk.Frame(status_frame, bg=SURFACE2)
        row.pack(fill="x", padx=16)

        self.dot = StatusDot(row)
        self.dot.pack(side="left", padx=(0,8))

        self.status_label = tk.Label(row, text="Server is stopped",
                                     font=("Segoe UI Semibold",11),
                                     fg=TEXT_MUTED, bg=SURFACE2)
        self.status_label.pack(side="left")

        self.url_label = tk.Label(status_frame,
                                  text="",
                                  font=("Segoe UI",9),
                                  fg=ACCENT, bg=SURFACE2,
                                  cursor="hand2")
        self.url_label.pack(pady=(4,0))
        self.url_label.bind("<Button-1>", lambda e: webbrowser.open("http://localhost:8000/docs"))

        # buttons row 1
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(pady=16)

        self.start_btn = RoundedButton(btn_frame, "\u25b6  Start Server",
                                       command=self._start,
                                       bg=ACCENT, fg=BG, width=200, height=44)
        self.start_btn.pack(side="left", padx=6)

        self.stop_btn = RoundedButton(btn_frame, "\u25a0  Stop Server",
                                      command=self._stop,
                                      bg=SURFACE2, fg=TEXT_MUTED, width=200, height=44)
        self.stop_btn.pack(side="left", padx=6)

        # buttons row 2
        btn_frame2 = tk.Frame(self, bg=BG)
        btn_frame2.pack()

        open_btn2 = RoundedButton(btn_frame2, "\u2295  Open Swagger UI",
                                  command=lambda: webbrowser.open("http://localhost:8000/docs"),
                                  bg=BLUE, fg=TEXT, width=200, height=40)
        open_btn2.pack(side="left", padx=6)

        folder_btn = RoundedButton(btn_frame2, "\u229e  Open Project Folder",
                                   command=lambda: os.startfile(BASE_DIR),
                                   bg=SURFACE2, fg=TEXT, width=200, height=40)
        folder_btn.pack(side="left", padx=6)

        # log area label
        log_header = tk.Frame(self, bg=BG)
        log_header.pack(fill="x", padx=16, pady=(14,4))
        tk.Label(log_header, text="SERVER LOG", font=("Segoe UI",8,"bold"),
                 fg=TEXT_FAINT, bg=BG).pack(side="left")
        self.clear_btn = tk.Label(log_header, text="Clear", font=("Segoe UI",8),
                                  fg=TEXT_FAINT, bg=BG, cursor="hand2")
        self.clear_btn.pack(side="right")
        self.clear_btn.bind("<Button-1>", lambda e: self._clear_log())

        # log box
        log_outer = tk.Frame(self, bg=SURFACE, bd=0, highlightthickness=1,
                             highlightbackground=BORDER)
        log_outer.pack(fill="both", expand=True, padx=16, pady=(0,16))

        self.log_text = tk.Text(log_outer, bg=SURFACE, fg=TEXT_MUTED,
                                font=("Consolas",8), wrap="word",
                                state="disabled", relief="flat",
                                padx=10, pady=8, bd=0,
                                selectbackground=SURFACE2,
                                insertbackground=TEXT)
        self.log_text.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(log_outer, command=self.log_text.yview,
                          bg=SURFACE, troughcolor=SURFACE, width=8,
                          relief="flat", bd=0)
        sb.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=sb.set)

        # colour tags
        self.log_text.tag_config("info",    foreground=TEXT_MUTED)
        self.log_text.tag_config("success", foreground=GREEN)
        self.log_text.tag_config("warn",    foreground=ACCENT)
        self.log_text.tag_config("error",   foreground=RED)
        self.log_text.tag_config("url",     foreground=BLUE)
        self.log_text.tag_config("dim",     foreground=TEXT_FAINT)

        self._log("CinemaList launcher ready.", "dim")
        self._log(f"Backend path: {BACKEND_DIR}", "dim")

    # ── server control ──────────────────────────────────────────────────────────────
    def _start(self):
        global server_proc, server_thread
        if server_proc:
            self._log("Server is already running.", "warn"); return
        if not os.path.exists(VENV_PYTHON):
            self._log("ERROR: venv not found. Run: python -m venv venv && pip install -r requirements.txt", "error"); return

        self._set_status("migrating", "Applying migrations\u2026", "")
        self.start_btn.configure_color(bg=TEXT_FAINT)

        def run():
            self._log("Running alembic upgrade head\u2026", "info")
            r = subprocess.run(
                [VENV_ALEMBIC, "upgrade", "head"],
                cwd=BACKEND_DIR,
                capture_output=True, text=True
            )
            for line in (r.stdout + r.stderr).splitlines():
                tag = "success" if "Running upgrade" in line else "dim"
                self._log(line, tag)

            global server_proc
            self._log("Starting uvicorn\u2026", "info")
            self._set_status("running", "Server is running", "http://localhost:8000/docs")
            server_proc = subprocess.Popen(
                [VENV_UVICORN, "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
                cwd=BACKEND_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.start_btn.configure_color(bg=TEXT_FAINT)
            self.stop_btn.configure_color(bg=RED, fg=TEXT, text="\u25a0  Stop Server")

            for line in server_proc.stdout:
                line = line.rstrip()
                if not line: continue
                tag = "success" if "Application startup" in line or "Uvicorn running" in line \
                      else "error" if "ERROR" in line or "error" in line \
                      else "url"  if "http://" in line \
                      else "warn" if "WARNING" in line \
                      else "dim"
                self._log(line, tag)

            server_proc = None
            self._set_status("idle", "Server is stopped", "")
            self.start_btn.configure_color(bg=ACCENT, fg=BG, text="\u25b6  Start Server")
            self.stop_btn.configure_color(bg=SURFACE2, fg=TEXT_MUTED, text="\u25a0  Stop Server")
            self._log("Server stopped.", "warn")

        server_thread = threading.Thread(target=run, daemon=True)
        server_thread.start()

    def _stop(self):
        global server_proc
        if not server_proc:
            self._log("No server running.", "warn"); return
        self._log("Stopping server\u2026", "warn")
        self._set_status("stopping", "Stopping\u2026", "")
        server_proc.terminate()

    def _on_close(self):
        global server_proc
        if server_proc:
            server_proc.terminate()
        self.destroy()

    # ── helpers ───────────────────────────────────────────────────────────────────
    def _set_status(self, dot_state, label, url):
        self.dot.set(dot_state)
        colors = {"idle": TEXT_MUTED, "running": GREEN, "stopping": RED, "migrating": ACCENT}
        self.status_label.config(text=label, fg=colors.get(dot_state, TEXT_MUTED))
        self.url_label.config(text=url)

    def _log(self, msg, tag="info"):
        def _do():
            self.log_text.config(state="normal")
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{ts}] ", "dim")
            self.log_text.insert("end", msg + "\n", tag)
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.after(0, _do)

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
