"""
IBT Journal — Instalátor
Stáhne nejnovější BACKTESTING.py z GitHubu, nainstaluje program a vytvoří zástupce.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import urllib.request
import urllib.error
import os
import sys
import shutil
import subprocess
import re

# ── Konfigurace ───────────────────────────────────────────────────────────────
APP_NAME     = "IBT Journal"
EXE_NAME     = "IBT_Journal.exe"
GITHUB_RAW   = "https://raw.githubusercontent.com/mochstanpda-hub/smc-journal/main/BACKTESTING.py"
HEADERS      = {"User-Agent": "IBTJournal-Installer/1.0"}
DEFAULT_DIR  = r"C:\IBT Journal"

# ── Barvy ─────────────────────────────────────────────────────────────────────
BG     = "#0f172a"
PANEL  = "#1e293b"
SURF   = "#293548"
TEXT   = "#e2e8f0"
SUB    = "#64748b"
ACCENT = "#3b82f6"
GREEN  = "#22c55e"
RED    = "#ef4444"
ORANGE = "#f59e0b"

# ── Pomocné funkce ────────────────────────────────────────────────────────────

def _get_version(content: str) -> str:
    m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    return m.group(1) if m else "?"

def _create_shortcut(target: str, link_path: str, description: str = ""):
    """Vytvoří zástupce přes VBScript (bez externích knihoven)."""
    vbs = (
        'Set sh = WScript.CreateObject("WScript.Shell")\n'
        f'Set lnk = sh.CreateShortcut("{link_path}")\n'
        f'lnk.TargetPath = "{target}"\n'
        f'lnk.Description = "{description}"\n'
        f'lnk.WorkingDirectory = "{os.path.dirname(target)}"\n'
        "lnk.Save\n"
    )
    tmp = os.path.join(os.environ.get("TEMP", os.getcwd()), "_ibt_setup.vbs")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(vbs)
        subprocess.run(["cscript", "//nologo", tmp],
                       capture_output=True, timeout=10)
    finally:
        try: os.remove(tmp)
        except: pass

# ── Hlavní okno ───────────────────────────────────────────────────────────────

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Instalátor")
        self.geometry("580x520")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._center()

        self._remote_ver   = None
        self._remote_bytes = None
        self._install_dir  = tk.StringVar(value=DEFAULT_DIR)

        self._build()
        self.after(300, self._check_version)

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"580x520+{(sw-580)//2}+{(sh-520)//2}")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        # Hlavička
        hdr = tk.Frame(self, bg="#0f3460", height=80)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=APP_NAME, bg="#0f3460", fg=TEXT,
                 font=("Segoe UI", 22, "bold")).pack(side="left", padx=24, pady=18)
        tk.Label(hdr, text="Instalátor", bg="#0f3460", fg=SUB,
                 font=("Segoe UI", 11)).pack(side="right", padx=24)

        body = tk.Frame(self, bg=BG, padx=32, pady=24)
        body.pack(fill="both", expand=True)

        # ── Verze z GitHubu ──
        vbox = tk.Frame(body, bg=PANEL, padx=20, pady=16)
        vbox.pack(fill="x")

        self.ver_var = tk.StringVar(value="Připojuji se na GitHub…")
        ver_row = tk.Frame(vbox, bg=PANEL); ver_row.pack(fill="x")
        tk.Label(ver_row, text="Nejnovější verze:", bg=PANEL, fg=SUB,
                 font=("Segoe UI", 10), width=20, anchor="w").pack(side="left")
        self.ver_lbl = tk.Label(ver_row, textvariable=self.ver_var,
                                bg=PANEL, fg=ORANGE,
                                font=("Segoe UI", 10, "bold"))
        self.ver_lbl.pack(side="left")

        # ── Složka instalace ──
        tk.Label(body, text="Složka instalace:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(20, 4))

        dir_row = tk.Frame(body, bg=BG); dir_row.pack(fill="x")
        self.dir_entry = tk.Entry(dir_row, textvariable=self._install_dir,
                                  font=("Segoe UI", 10), bg=SURF, fg=TEXT,
                                  insertbackground=TEXT, relief="flat",
                                  highlightthickness=1, highlightbackground=ACCENT)
        self.dir_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        tk.Button(dir_row, text="📁", bg=SURF, fg=TEXT, relief="flat",
                  font=("Segoe UI", 11), padx=8, cursor="hand2",
                  command=self._browse).pack(side="left")

        # ── Zástupce ──
        self.shortcut_var = tk.BooleanVar(value=True)
        tk.Checkbutton(body, text="Vytvořit zástupce na Ploše",
                       variable=self.shortcut_var,
                       bg=BG, fg=TEXT, selectcolor=SURF,
                       activebackground=BG, activeforeground=TEXT,
                       font=("Segoe UI", 10)).pack(anchor="w", pady=(14, 0))

        # ── Status + progress ──
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(body, textvariable=self.status_var,
                                   bg=BG, fg=SUB, font=("Segoe UI", 9),
                                   wraplength=500, justify="center")
        self.status_lbl.pack(pady=(18, 4))

        self.progress_var = tk.DoubleVar()
        style = ttk.Style(); style.theme_use("default")
        style.configure("I.TProgressbar",
                         troughcolor=SURF, background=ACCENT, thickness=8)
        self.pbar = ttk.Progressbar(body, variable=self.progress_var,
                                     maximum=100, style="I.TProgressbar")
        self.pbar.pack(fill="x", pady=(0, 4))

        # ── Tlačítka ──
        btn_row = tk.Frame(body, bg=BG); btn_row.pack(pady=(16, 0))

        self.install_btn = tk.Button(
            btn_row, text="⬇  Stáhnout a nainstalovat",
            bg=ACCENT, fg="white", relief="flat",
            font=("Segoe UI", 12, "bold"), padx=22, pady=10,
            cursor="hand2", state="disabled",
            command=self._do_install,
        )
        self.install_btn.pack(side="left", padx=(0, 12))

        tk.Button(btn_row, text="✕  Zrušit", bg=SURF, fg=TEXT,
                  relief="flat", font=("Segoe UI", 11), padx=16, pady=10,
                  cursor="hand2", command=self.destroy).pack(side="left")

        # Patička
        tk.Label(self, text="github.com/mochstanpda-hub/smc-journal",
                 bg=BG, fg=SUB, font=("Segoe UI", 8)).pack(
            side="bottom", anchor="e", padx=16, pady=6)

    # ── Akce ──────────────────────────────────────────────────────────────────

    def _browse(self):
        d = filedialog.askdirectory(title="Vyber složku pro instalaci",
                                    initialdir=self._install_dir.get())
        if d: self._install_dir.set(d)

    def _set_status(self, msg, color=None):
        self.status_var.set(msg)
        if color: self.status_lbl.config(fg=color)

    # ── Kontrola verze ────────────────────────────────────────────────────────

    def _check_version(self):
        self._set_status("Připojuji se na GitHub…")
        threading.Thread(target=self._check_thread, daemon=True).start()

    def _check_thread(self):
        try:
            req = urllib.request.Request(GITHUB_RAW, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            ver = _get_version(data.decode("utf-8"))
            self._remote_ver   = ver
            self._remote_bytes = data
            self.after(0, self._check_done, ver, None)
        except Exception as e:
            self.after(0, self._check_done, None, str(e))

    def _check_done(self, ver, err):
        if err:
            self.ver_var.set("Chyba připojení")
            self.ver_lbl.config(fg=RED)
            self._set_status(f"Nepodařilo se připojit na GitHub:\n{err}", RED)
            return
        self.ver_var.set(f"v{ver}")
        self.ver_lbl.config(fg=GREEN)
        self._set_status(f"Verze v{ver} je připravena ke stažení.", GREEN)
        self.install_btn.config(state="normal")

    # ── Instalace ─────────────────────────────────────────────────────────────

    def _do_install(self):
        d = self._install_dir.get().strip()
        if not d:
            messagebox.showwarning("Instalátor", "Vyber složku pro instalaci."); return
        self.install_btn.config(state="disabled", text="⏳  Instaluji…")
        self.dir_entry.config(state="disabled")
        threading.Thread(target=self._install_thread,
                         args=(d,), daemon=True).start()

    def _install_thread(self, install_dir: str):
        try:
            # 1. Vytvoř složku
            self.after(0, self._set_status, "Vytvářím instalační složku…")
            os.makedirs(install_dir, exist_ok=True)
            self.after(0, self.progress_var.set, 15)

            # 2. Stáhni BACKTESTING.py (nebo použij již stažený)
            self.after(0, self._set_status, "Stahuji nejnovější BACKTESTING.py z GitHubu…")
            if self._remote_bytes:
                content = self._remote_bytes
            else:
                req = urllib.request.Request(GITHUB_RAW, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    total   = int(resp.headers.get("Content-Length", 0))
                    content = b""
                    while True:
                        chunk = resp.read(8192)
                        if not chunk: break
                        content += chunk
                        if total:
                            self.after(0, self.progress_var.set,
                                       15 + len(content) / total * 45)
            bt_dst = os.path.join(install_dir, "BACKTESTING.py")
            with open(bt_dst, "w", encoding="utf-8") as f:
                f.write(content.decode("utf-8"))
            self.after(0, self.progress_var.set, 65)

            # 3. Zkopíruj launcher (tento .exe) do cílové složky
            self.after(0, self._set_status, "Kopíruji spouštěcí soubor…")
            exe_src = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
            exe_dst = os.path.join(install_dir, EXE_NAME)
            if os.path.abspath(exe_src) != os.path.abspath(exe_dst):
                shutil.copy2(exe_src, exe_dst)
            self.after(0, self.progress_var.set, 85)

            # 4. Zástupce na ploše
            if self.shortcut_var.get():
                self.after(0, self._set_status, "Vytvářím zástupce na Ploše…")
                desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
                lnk     = os.path.join(desktop, f"{APP_NAME}.lnk")
                _create_shortcut(exe_dst, lnk, APP_NAME)
            self.after(0, self.progress_var.set, 100)

            ver = _get_version(content.decode("utf-8"))
            self.after(0, self._install_done, install_dir, exe_dst, ver, None)

        except Exception as e:
            import traceback
            self.after(0, self._install_done, install_dir, None, None,
                       f"{e}\n\n{traceback.format_exc()}")

    def _install_done(self, install_dir, exe_dst, ver, err):
        if err:
            self._set_status(f"Chyba při instalaci:\n{err}", RED)
            self.install_btn.config(state="normal", text="⬇  Zkusit znovu")
            return

        self._set_status(
            f"✓  Instalace v{ver} dokončena!\n"
            f"Program je v: {install_dir}", GREEN)
        self.install_btn.config(text="✓  Nainstalováno")

        if messagebox.askyesno(
            "Instalace dokončena",
            f"{APP_NAME} v{ver} byl úspěšně nainstalován.\n\n"
            f"Složka: {install_dir}\n\n"
            "Chceš program spustit teď?",
        ):
            try:
                subprocess.Popen([exe_dst], cwd=install_dir)
            except Exception as e:
                messagebox.showerror("Chyba", f"Nelze spustit program:\n{e}")
        self.destroy()


if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
