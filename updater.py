"""
SMC Journal PRO — Updater
Stáhne nejnovější verzi BACKTESTING.py z GitHubu bez nutnosti spouštět program.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import threading
import os
import re
import shutil
from datetime import datetime

# ── Konfigurace ───────────────────────────────────────────────────────────────
UPDATE_URL   = "https://raw.githubusercontent.com/mochstanpda-hub/smc-journal/main/BACKTESTING.py"
TARGET_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BACKTESTING.py")
BACKUP_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
HEADERS      = {"User-Agent": "SMCJournal-Updater/1.0"}

# ── Barvy ─────────────────────────────────────────────────────────────────────
BG      = "#0f172a"
PANEL   = "#1e293b"
SURF    = "#293548"
TEXT    = "#e2e8f0"
SUB     = "#64748b"
ACCENT  = "#3b82f6"
GREEN   = "#22c55e"
RED     = "#ef4444"
ORANGE  = "#f59e0b"

# ── Pomocné funkce ────────────────────────────────────────────────────────────

def _get_version(content: str) -> str | None:
    m = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    return m.group(1) if m else None

def _version_tuple(v: str):
    try:    return tuple(int(x) for x in v.split("."))
    except: return (0,)

def _local_version() -> str:
    try:
        with open(TARGET_FILE, encoding="utf-8") as f:
            return _get_version(f.read()) or "?"
    except:
        return "soubor nenalezen"

def _make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"BACKTESTING_{ts}.py")
    shutil.copy2(TARGET_FILE, dst)
    return dst

# ── Hlavní okno ───────────────────────────────────────────────────────────────

class UpdaterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMC Journal PRO — Updater")
        self.geometry("520x400")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._center()
        self._remote_content = None
        self._remote_ver     = None
        self._build()
        self.after(200, self._check)

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 520) // 2
        y = (self.winfo_screenheight() - 400) // 2
        self.geometry(f"520x400+{x}+{y}")

    def _build(self):
        # Hlavička
        hdr = tk.Frame(self, bg="#0f3460", height=70)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="SMC Journal PRO", bg="#0f3460", fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=20, pady=16)
        tk.Label(hdr, text="Updater", bg="#0f3460", fg=SUB,
                 font=("Segoe UI", 10)).pack(side="right", padx=20)

        body = tk.Frame(self, bg=BG, padx=30, pady=24)
        body.pack(fill="both", expand=True)

        # Verze řádky
        vf = tk.Frame(body, bg=PANEL, padx=20, pady=16)
        vf.pack(fill="x")

        def _vrow(label, var_ref):
            row = tk.Frame(vf, bg=PANEL)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=PANEL, fg=SUB,
                     font=("Segoe UI", 10), width=18, anchor="w").pack(side="left")
            lbl = tk.Label(row, textvariable=var_ref, bg=PANEL, fg=TEXT,
                           font=("Segoe UI", 10, "bold"))
            lbl.pack(side="left")
            return lbl

        self.local_var  = tk.StringVar(value=_local_version())
        self.remote_var = tk.StringVar(value="Kontroluji…")
        self.status_var = tk.StringVar(value="")

        lbl_local  = _vrow("Tvoje verze:", self.local_var)
        self.remote_lbl = _vrow("GitHub verze:", self.remote_var)

        # Status zpráva
        self.status_lbl = tk.Label(body, textvariable=self.status_var,
                                   bg=BG, fg=SUB, font=("Segoe UI", 9),
                                   wraplength=460, justify="center")
        self.status_lbl.pack(pady=(16, 0))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.pbar = ttk.Progressbar(body, variable=self.progress_var, maximum=100)
        self.pbar.pack(fill="x", pady=(10, 0))
        style = ttk.Style(); style.theme_use("default")
        style.configure("TProgressbar", troughcolor=SURF, background=ACCENT, thickness=6)

        # Tlačítka
        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(pady=(20, 0))

        self.update_btn = tk.Button(
            btn_row, text="⬇  Stáhnout aktualizaci",
            bg=ACCENT, fg="white", relief="flat",
            font=("Segoe UI", 12, "bold"), padx=20, pady=10,
            cursor="hand2", state="disabled",
            command=self._do_update,
        )
        self.update_btn.pack(side="left", padx=(0, 10))

        tk.Button(
            btn_row, text="✕  Zavřít",
            bg=SURF, fg=TEXT, relief="flat",
            font=("Segoe UI", 11), padx=16, pady=10,
            cursor="hand2", command=self.destroy,
        ).pack(side="left")

        tk.Label(self, text=f"Zálohy se ukládají do: {BACKUP_DIR}",
                 bg=BG, fg=SUB, font=("Segoe UI", 8)).pack(
            side="bottom", anchor="e", padx=18, pady=6)

    # ── Kontrola verze ────────────────────────────────────────────────────────

    def _check(self):
        self.status_var.set("Připojuji se na GitHub…")
        threading.Thread(target=self._check_thread, daemon=True).start()

    def _check_thread(self):
        try:
            req  = urllib.request.Request(UPDATE_URL, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")
            ver = _get_version(content)
            self._remote_content = content
            self._remote_ver     = ver
            self.after(0, self._check_done, ver, None)
        except Exception as e:
            self.after(0, self._check_done, None, str(e))

    def _check_done(self, remote_ver, error):
        if error:
            self.remote_var.set("Chyba připojení")
            self.remote_lbl.config(fg=RED)
            self.status_var.set(f"Nepodařilo se připojit:\n{error}")
            self.status_lbl.config(fg=RED)
            return

        self.remote_var.set(remote_ver or "?")
        local_ver = self.local_var.get()

        if remote_ver and _version_tuple(remote_ver) > _version_tuple(local_ver):
            self.remote_lbl.config(fg=GREEN)
            self.status_var.set(f"🎉  Dostupná nová verze {remote_ver}! Klikni na Stáhnout.")
            self.status_lbl.config(fg=GREEN)
            self.update_btn.config(state="normal")
        elif remote_ver and _version_tuple(remote_ver) == _version_tuple(local_ver):
            self.remote_lbl.config(fg=GREEN)
            self.status_var.set("✓  Máš nejnovější verzi. Žádná aktualizace není potřeba.")
            self.status_lbl.config(fg=GREEN)
        else:
            self.remote_lbl.config(fg=ORANGE)
            self.status_var.set("Nepodařilo se zjistit verzi z GitHubu.")
            self.status_lbl.config(fg=ORANGE)

    # ── Stažení aktualizace ───────────────────────────────────────────────────

    def _do_update(self):
        self.update_btn.config(state="disabled", text="⏳  Stahuji…")
        self.status_var.set("Zálohuji aktuální soubor…")
        self.status_lbl.config(fg=SUB)
        threading.Thread(target=self._update_thread, daemon=True).start()

    def _update_thread(self):
        try:
            # 1. Záloha
            if os.path.exists(TARGET_FILE):
                backup = _make_backup()
                self.after(0, self.status_var.set, f"Záloha uložena: {os.path.basename(backup)}")
            self.after(0, self.progress_var.set, 20)

            # 2. Stažení (znovu, aby byl progress správný)
            self.after(0, self.status_var.set, "Stahuji novou verzi…")
            req = urllib.request.Request(UPDATE_URL, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                total   = int(resp.headers.get("Content-Length", 0))
                content = b""
                while True:
                    chunk = resp.read(8192)
                    if not chunk: break
                    content += chunk
                    if total:
                        pct = 20 + len(content) / total * 70
                        self.after(0, self.progress_var.set, pct)

            # 3. Zápis
            self.after(0, self.status_var.set, "Zapisuji soubor…")
            with open(TARGET_FILE, "w", encoding="utf-8") as f:
                f.write(content.decode("utf-8"))
            self.after(0, self.progress_var.set, 100)

            new_ver = _get_version(content.decode("utf-8")) or "?"
            self.after(0, self._update_done, new_ver, None)

        except Exception as e:
            self.after(0, self._update_done, None, str(e))

    def _update_done(self, new_ver, error):
        if error:
            self.status_var.set(f"Chyba při aktualizaci:\n{error}")
            self.status_lbl.config(fg=RED)
            self.update_btn.config(state="normal", text="⬇  Zkusit znovu")
        else:
            self.local_var.set(new_ver)
            self.status_var.set(f"✓  Aktualizace na v{new_ver} dokončena! Spusť program.")
            self.status_lbl.config(fg=GREEN)
            self.update_btn.config(state="disabled", text="✓  Hotovo")
            messagebox.showinfo(
                "Aktualizace dokončena",
                f"Program byl aktualizován na v{new_ver}.\n\nSpusť BACKTESTING.py pro použití nové verze.",
            )


if __name__ == "__main__":
    app = UpdaterApp()
    app.mainloop()
