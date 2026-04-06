import tkinter as tk
import subprocess
import threading
import os
import sys
import webbrowser
import time
import signal
import shutil

# ── paths ───────────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR   = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR  = os.path.join(BASE_DIR, "frontend")
VENV_PYTHON   = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")
VENV_ALEMBIC  = os.path.join(BACKEND_DIR, "venv", "Scripts", "alembic.exe")
VENV_UVICORN  = os.path.join(BACKEND_DIR, "venv", "Scripts", "uvicorn.exe")

# npm: try known location first, then PATH fallback
NPM_CMD = r"E:\NodeJS\npm.cmd"
if not os.path.exists(NPM_CMD):
    NPM_CMD = shutil.which("npm") or "npm"

# ── palette (cinema dark theme) ───────────────────────────────────────────────────────────────
BG          = "#0f0e0d"
SURFACE     = "#1a1917"
SURFACE2    = "#222120"
BORDER      = "#2e2c2a"
TEXT        = "#e8e6e1"
TEXT_MUTED  = "#7a7874"
TEXT_FAINT  = "#4a4845"
ACCENT      = "#e8b84b"
RED         = "#d16060"
GREEN       = "#6daa55"
BLUE        = "#5591c7"
PURPLE      = "#a86fdf"

# ── state ────────────────────────────────────────────────────────────────────────────
server_proc    = None
server_thread  = None
frontend_proc  = None
frontend_thread = None


def _kill_proc_tree(proc):
    """Kill proc and ALL its children on Windows using taskkill /F /T."""
    if proc is None:
        return
    pid = proc.pid
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    try:
        proc.wait(timeout=3)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────────
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command,
                 bg=ACCENT, fg=BG, btn_width=180, btn_height=42, radius=8):
        super().__init__(parent, bg=SURFACE, highlightthickness=0, bd=0)
        self._bw  = btn_width
        self._bh  = btn_height
        self._bg  = bg
        self._fg  = fg
        self._cmd = command
        self._text = text
        self._r   = radius
        self.config(width=self._bw, height=self._bh)
        self._draw(bg)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)
        self.bind("<Button-1>",        self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        self.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90, style="pieslice", **kw)
        self.create_arc(x2-2*r,  y1,      x2,     y1+2*r, start=0,   extent=90, style="pieslice", **kw)
        self.create_arc(x1,      y2-2*r,  x1+2*r, y2,     start=180, extent=90, style="pieslice", **kw)
        self.create_arc(x2-2*r,  y2-2*r,  x2,     y2,     start=270, extent=90, style="pieslice", **kw)
        self.create_rectangle(x1+r, y1,   x2-r, y2, **kw)
        self.create_rectangle(x1,   y1+r, x2,   y2-r, **kw)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(1, 1, self._bw-1, self._bh-1, self._r, fill=color, outline="")
        self.create_text(self._bw//2, self._bh//2, text=self._text,
                         fill=self._fg, font=("Segoe UI Semibold", 10))

    def _on_enter(self, e):   self._draw(self._darken(self._bg, 20))
    def _on_leave(self, e):   self._draw(self._bg)
    def _on_click(self, e):   self._draw(self._darken(self._bg, 40))
    def _on_release(self, e):
        self._draw(self._bg)
        if self._cmd:
            self._cmd()

    @staticmethod
    def _darken(hex_color, amount):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{max(0,r-amount):02x}{max(0,g-amount):02x}{max(0,b-amount):02x}"

    def configure_color(self, bg=None, fg=None, text=None):
        if bg   is not None: self._bg   = bg
        if fg   is not None: self._fg   = fg
        if text is not None: self._text = text
        self._draw(self._bg)


# ─────────────────────────────────────────────────────────────────────────────────
class StatusDot(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=SURFACE, highlightthickness=0, **kw)
        self.config(width=12, height=12)
        self._state   = "idle"
        self._anim_id = None
        self._phase   = 0
        self.set("idle")

    def set(self, state):
        self._state = state
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        colors = {"idle": TEXT_FAINT, "running": GREEN, "stopping": RED,
                  "migrating": ACCENT, "starting": PURPLE}
        c = colors.get(state, TEXT_FAINT)
        if state in ("running", "migrating", "starting"):
            self._pulse(c)
        else:
            self.delete("all")
            self.create_oval(2, 2, 10, 10, fill=c, outline="")

    def _pulse(self, color):
        self._phase = (self._phase + 1) % 20
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        scale = 0.6 + 0.4 * abs(self._phase - 10) / 10
        r2 = min(255, int(r*scale))
        g2 = min(255, int(g*scale))
        b2 = min(255, int(b*scale))
        self.delete("all")
        self.create_oval(2, 2, 10, 10, fill=f"#{r2:02x}{g2:02x}{b2:02x}", outline="")
        self._anim_id = self.after(80, lambda: self._pulse(color))


# ─────────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CinemaList Launcher")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._center()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 520, 700
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── header ──────────────────────────────────────────────────────
        HEADER_H = 76
        header = tk.Frame(self, bg=SURFACE, height=HEADER_H)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo_y = (HEADER_H - 36) // 2
        logo = tk.Canvas(header, bg=SURFACE, highlightthickness=0)
        logo.config(width=36, height=36)
        logo.place(x=16, y=logo_y)
        logo.create_oval(2, 2, 34, 34, outline=ACCENT, width=2)
        logo.create_oval(14, 14, 22, 22, fill=ACCENT, outline="")
        for dx, dy in [(16,4),(26,10),(26,22),(16,28),(6,22),(6,10)]:
            logo.create_oval(dx-3, dy-3, dx+3, dy+3, fill=ACCENT, outline="")

        text_block_top = (HEADER_H - 40) // 2
        TEXT_X = 62
        tk.Label(header, text="CinemaList",
                 font=("Segoe UI Semibold", 15),
                 fg=TEXT, bg=SURFACE).place(x=TEXT_X, y=text_block_top)
        tk.Label(header, text="Dev Launcher",
                 font=("Segoe UI", 9),
                 fg=TEXT_MUTED, bg=SURFACE).place(x=TEXT_X, y=text_block_top + 26)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── BACKEND status card ──────────────────────────────────────────────
        be_card = tk.Frame(self, bg=SURFACE2, pady=12)
        be_card.pack(fill="x", padx=16, pady=(14, 0))

        tk.Label(be_card, text="BACKEND",
                 font=("Segoe UI", 7, "bold"), fg=TEXT_FAINT,
                 bg=SURFACE2).pack(anchor="w", padx=16)

        be_row = tk.Frame(be_card, bg=SURFACE2)
        be_row.pack(fill="x", padx=16, pady=(4, 0))
        self.be_dot = StatusDot(be_row)
        self.be_dot.pack(side="left", padx=(0, 8))
        self.be_status_label = tk.Label(be_row, text="Stopped",
                                        font=("Segoe UI Semibold", 11),
                                        fg=TEXT_MUTED, bg=SURFACE2)
        self.be_status_label.pack(side="left")

        self.be_url_label = tk.Label(be_card, text="",
                                     font=("Segoe UI", 9), fg=ACCENT,
                                     bg=SURFACE2, cursor="hand2")
        self.be_url_label.pack(pady=(2, 0))
        self.be_url_label.bind("<Button-1>",
                               lambda e: webbrowser.open("http://localhost:8000/docs"))

        # ── FRONTEND status card ──────────────────────────────────────────────
        fe_card = tk.Frame(self, bg=SURFACE2, pady=12)
        fe_card.pack(fill="x", padx=16, pady=(8, 0))

        tk.Label(fe_card, text="FRONTEND",
                 font=("Segoe UI", 7, "bold"), fg=TEXT_FAINT,
                 bg=SURFACE2).pack(anchor="w", padx=16)

        fe_row = tk.Frame(fe_card, bg=SURFACE2)
        fe_row.pack(fill="x", padx=16, pady=(4, 0))
        self.fe_dot = StatusDot(fe_row)
        self.fe_dot.pack(side="left", padx=(0, 8))
        self.fe_status_label = tk.Label(fe_row, text="Stopped",
                                        font=("Segoe UI Semibold", 11),
                                        fg=TEXT_MUTED, bg=SURFACE2)
        self.fe_status_label.pack(side="left")

        self.fe_url_label = tk.Label(fe_card, text="",
                                     font=("Segoe UI", 9), fg=PURPLE,
                                     bg=SURFACE2, cursor="hand2")
        self.fe_url_label.pack(pady=(2, 0))
        self.fe_url_label.bind("<Button-1>",
                               lambda e: webbrowser.open("http://localhost:5173"))

        # ── backend buttons ───────────────────────────────────────────────────
        be_btn_frame = tk.Frame(self, bg=BG)
        be_btn_frame.pack(pady=(14, 0))

        self.start_btn = RoundedButton(
            be_btn_frame, "\u25b6  Start Backend",
            command=self._start_backend,
            bg=ACCENT, fg=BG, btn_width=200, btn_height=44,
        )
        self.start_btn.pack(side="left", padx=6)

        self.stop_btn = RoundedButton(
            be_btn_frame, "\u25a0  Stop Backend",
            command=self._stop_backend,
            bg=SURFACE2, fg=TEXT_MUTED, btn_width=200, btn_height=44,
        )
        self.stop_btn.pack(side="left", padx=6)

        # ── frontend buttons ──────────────────────────────────────────────────
        fe_btn_frame = tk.Frame(self, bg=BG)
        fe_btn_frame.pack(pady=(8, 0))

        self.fe_start_btn = RoundedButton(
            fe_btn_frame, "\u25b6  Start Frontend",
            command=self._start_frontend,
            bg=PURPLE, fg=TEXT, btn_width=200, btn_height=44,
        )
        self.fe_start_btn.pack(side="left", padx=6)

        self.fe_stop_btn = RoundedButton(
            fe_btn_frame, "\u25a0  Stop Frontend",
            command=self._stop_frontend,
            bg=SURFACE2, fg=TEXT_MUTED, btn_width=200, btn_height=44,
        )
        self.fe_stop_btn.pack(side="left", padx=6)

        # ── secondary buttons ───────────────────────────────────────────────────
        btn_frame2 = tk.Frame(self, bg=BG)
        btn_frame2.pack(pady=(8, 0))

        RoundedButton(
            btn_frame2, "\u2295  Swagger UI",
            command=lambda: webbrowser.open("http://localhost:8000/docs"),
            bg=BLUE, fg=TEXT, btn_width=120, btn_height=36,
        ).pack(side="left", padx=4)

        RoundedButton(
            btn_frame2, "\u2295  Open App",
            command=lambda: webbrowser.open("http://localhost:5173"),
            bg=PURPLE, fg=TEXT, btn_width=120, btn_height=36,
        ).pack(side="left", padx=4)

        RoundedButton(
            btn_frame2, "\u229e  Project Folder",
            command=lambda: os.startfile(BASE_DIR),
            bg=SURFACE2, fg=TEXT, btn_width=140, btn_height=36,
        ).pack(side="left", padx=4)

        # ── log header ─────────────────────────────────────────────────────────
        log_header = tk.Frame(self, bg=BG)
        log_header.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(log_header, text="LOG",
                 font=("Segoe UI", 8, "bold"), fg=TEXT_FAINT, bg=BG).pack(side="left")
        clear_lbl = tk.Label(log_header, text="Clear",
                             font=("Segoe UI", 8), fg=TEXT_FAINT, bg=BG, cursor="hand2")
        clear_lbl.pack(side="right")
        clear_lbl.bind("<Button-1>", lambda e: self._clear_log())

        # ── log box ─────────────────────────────────────────────────────────────────
        log_outer = tk.Frame(self, bg=SURFACE, bd=0,
                             highlightthickness=1, highlightbackground=BORDER)
        log_outer.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.log_text = tk.Text(
            log_outer, bg=SURFACE, fg=TEXT_MUTED,
            font=("Consolas", 8), wrap="word",
            state="disabled", relief="flat",
            padx=10, pady=8, bd=0,
            selectbackground=SURFACE2,
            insertbackground=TEXT,
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(log_outer, command=self.log_text.yview,
                          bg=SURFACE, troughcolor=SURFACE,
                          width=8, relief="flat", bd=0)
        sb.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=sb.set)

        self.log_text.tag_config("info",    foreground=TEXT_MUTED)
        self.log_text.tag_config("success", foreground=GREEN)
        self.log_text.tag_config("warn",    foreground=ACCENT)
        self.log_text.tag_config("error",   foreground=RED)
        self.log_text.tag_config("url",     foreground=BLUE)
        self.log_text.tag_config("dim",     foreground=TEXT_FAINT)
        self.log_text.tag_config("fe",      foreground=PURPLE)

        self._log("CinemaList launcher ready.", "dim")
        self._log(f"Backend  : {BACKEND_DIR}", "dim")
        self._log(f"Frontend : {FRONTEND_DIR}", "dim")
        self._log(f"npm      : {NPM_CMD}", "dim")

    # ── BACKEND control ───────────────────────────────────────────────────────────
    def _start_backend(self):
        global server_proc, server_thread
        if server_proc:
            self._log("[BE] Server is already running.", "warn")
            return
        if not os.path.exists(VENV_PYTHON):
            self._log(
                "[BE] ERROR: venv not found. "
                "Run: python -m venv venv && pip install -r requirements.txt",
                "error",
            )
            return

        self._be_set_status("migrating", "Applying migrations\u2026", "")
        self.start_btn.configure_color(bg=TEXT_FAINT)

        def run():
            self._log("[BE] Running alembic upgrade head\u2026", "info")
            r = subprocess.run(
                [VENV_ALEMBIC, "upgrade", "head"],
                cwd=BACKEND_DIR,
                capture_output=True, text=True,
            )
            for line in (r.stdout + r.stderr).splitlines():
                tag = "success" if "Running upgrade" in line else "dim"
                self._log(line, tag)

            global server_proc
            self._log("[BE] Starting uvicorn\u2026", "info")
            server_proc = subprocess.Popen(
                [VENV_UVICORN, "app.main:app", "--reload",
                 "--host", "0.0.0.0", "--port", "8000"],
                cwd=BACKEND_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._be_set_status("running", "Running", "http://localhost:8000/docs")
            self.start_btn.configure_color(bg=TEXT_FAINT)
            self.stop_btn.configure_color(bg=RED, fg=TEXT, text="\u25a0  Stop Backend")

            for line in server_proc.stdout:
                line = line.rstrip()
                if not line:
                    continue
                tag = (
                    "success" if ("Application startup" in line or "Uvicorn running" in line)
                    else "error" if ("ERROR" in line or "error" in line)
                    else "url"  if "http://" in line
                    else "warn" if "WARNING" in line
                    else "dim"
                )
                self._log(f"[BE] {line}", tag)

            server_proc = None
            self._be_reset_idle()

        server_thread = threading.Thread(target=run, daemon=True)
        server_thread.start()

    def _stop_backend(self):
        global server_proc
        if not server_proc:
            self._log("[BE] No server running.", "warn")
            return
        self._log("[BE] Stopping server\u2026", "warn")
        self._be_set_status("stopping", "Stopping\u2026", "")
        self.stop_btn.configure_color(bg=TEXT_FAINT, fg=TEXT_FAINT, text="\u25a0  Stop Backend")
        proc = server_proc
        def do_kill():
            _kill_proc_tree(proc)
            self.after(0, self._be_reset_idle)
            self.after(0, lambda: self._log("[BE] Server stopped.", "warn"))
        threading.Thread(target=do_kill, daemon=True).start()

    def _be_reset_idle(self):
        global server_proc
        server_proc = None
        self._be_set_status("idle", "Stopped", "")
        self.start_btn.configure_color(bg=ACCENT, fg=BG, text="\u25b6  Start Backend")
        self.stop_btn.configure_color(bg=SURFACE2, fg=TEXT_MUTED, text="\u25a0  Stop Backend")

    def _be_set_status(self, dot_state, label, url):
        self.be_dot.set(dot_state)
        colors = {"idle": TEXT_MUTED, "running": GREEN,
                  "stopping": RED, "migrating": ACCENT}
        self.be_status_label.config(text=label, fg=colors.get(dot_state, TEXT_MUTED))
        self.be_url_label.config(text=url)

    # ── FRONTEND control ──────────────────────────────────────────────────────────
    def _start_frontend(self):
        global frontend_proc, frontend_thread
        if frontend_proc:
            self._log("[FE] Frontend is already running.", "warn")
            return
        if not os.path.exists(FRONTEND_DIR):
            self._log(f"[FE] ERROR: frontend/ folder not found at {FRONTEND_DIR}", "error")
            return
        if not os.path.exists(NPM_CMD):
            self._log(f"[FE] ERROR: npm not found at {NPM_CMD}", "error")
            return

        self._fe_set_status("starting", "Starting\u2026", "")
        self.fe_start_btn.configure_color(bg=TEXT_FAINT)

        def run():
            global frontend_proc
            self._log("[FE] Starting Vite dev server\u2026", "fe")
            frontend_proc = subprocess.Popen(
                [NPM_CMD, "run", "dev"],
                cwd=FRONTEND_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            for line in frontend_proc.stdout:
                line = line.rstrip()
                if not line:
                    continue
                # detect when Vite is ready
                if "localhost:5173" in line or "Local:" in line:
                    self._fe_set_status("running", "Running", "http://localhost:5173")
                    self.fe_start_btn.configure_color(bg=TEXT_FAINT)
                    self.fe_stop_btn.configure_color(bg=RED, fg=TEXT, text="\u25a0  Stop Frontend")
                tag = (
                    "error" if "error" in line.lower()
                    else "warn" if "warn" in line.lower()
                    else "fe"
                )
                self._log(f"[FE] {line}", tag)

            frontend_proc = None
            self._fe_reset_idle()

        frontend_thread = threading.Thread(target=run, daemon=True)
        frontend_thread.start()

    def _stop_frontend(self):
        global frontend_proc
        if not frontend_proc:
            self._log("[FE] No frontend running.", "warn")
            return
        self._log("[FE] Stopping frontend\u2026", "warn")
        self._fe_set_status("stopping", "Stopping\u2026", "")
        self.fe_stop_btn.configure_color(bg=TEXT_FAINT, fg=TEXT_FAINT, text="\u25a0  Stop Frontend")
        proc = frontend_proc
        def do_kill():
            _kill_proc_tree(proc)
            self.after(0, self._fe_reset_idle)
            self.after(0, lambda: self._log("[FE] Frontend stopped.", "warn"))
        threading.Thread(target=do_kill, daemon=True).start()

    def _fe_reset_idle(self):
        global frontend_proc
        frontend_proc = None
        self._fe_set_status("idle", "Stopped", "")
        self.fe_start_btn.configure_color(bg=PURPLE, fg=TEXT, text="\u25b6  Start Frontend")
        self.fe_stop_btn.configure_color(bg=SURFACE2, fg=TEXT_MUTED, text="\u25a0  Stop Frontend")

    def _fe_set_status(self, dot_state, label, url):
        self.fe_dot.set(dot_state)
        colors = {"idle": TEXT_MUTED, "running": GREEN,
                  "stopping": RED, "starting": PURPLE}
        self.fe_status_label.config(text=label, fg=colors.get(dot_state, TEXT_MUTED))
        self.fe_url_label.config(text=url)

    # ── close ──────────────────────────────────────────────────────────────────────────
    def _on_close(self):
        global server_proc, frontend_proc
        if server_proc:
            self._log("Closing — killing backend\u2026", "warn")
            _kill_proc_tree(server_proc)
        if frontend_proc:
            self._log("Closing — killing frontend\u2026", "warn")
            _kill_proc_tree(frontend_proc)
        self.destroy()

    # ── helpers ───────────────────────────────────────────────────────────────────────
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
