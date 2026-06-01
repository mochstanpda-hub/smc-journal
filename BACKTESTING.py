import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import csv
import os
import shutil
import json
from datetime import datetime, date
import locale
from collections import defaultdict
import sys
import traceback
import calendar
import webbrowser
import zipfile 
import random 
import math

# === KONTROLA KNIHOVEN ===
try:
    from PIL import Image, ImageTk
    import matplotlib
    matplotlib.use('TkAgg') 
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.colors import TwoSlopeNorm 
except ImportError as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Chybějící knihovna", f"Chybí nutné knihovny!\n\nChyba: {e}\n\nNainstalujte je příkazem:\npip install pillow matplotlib")
    sys.exit()

# --- IMPORTY PRO PDF (VOLITELNÉ) ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    pass

# --- IMPORTY PRO TRADINGVIEW (VOLITELNÉ) ---
try:
    import tkwebview2.tkwebview2 as tk_web
except ImportError:
    # Knihovna je volitelná. Pokud není nalezena, nastavíme proměnnou na None
    # a chyba se odchytí později při pokusu o vytvoření grafu.
    tk_web = None

# ==============================================================================
# 1. KONFIGURACE A CESTY
# ==============================================================================

try:
    locale.setlocale(locale.LC_TIME, 'cs_CZ.UTF-8')
except:
    pass

# ==============================================================================
# VERZE A AUTO-UPDATE
# ==============================================================================
VERSION = "1.5.67"

# CHANGELOG — co je nového v každé verzi (parsováno při aktualizaci)
# Formát: verze | Změna 1; Změna 2; Změna 3
CHANGELOG = """\
1.5.50 | OCR čas zavření — fallback skenuje spodních 20 % obrazu i celý obrázek i když byl otevírací čas nalezen; parse_all_dt přidán formát ISO + unicode apostrofy + formát 2
1.5.49 | OCR — kritická oprava _parse_price: dec[:2] → dec[:5]; forex ceny (1.18225) se správně parsují na 5 desetinných míst místo zkrácení na 2 (1.18)
1.5.48 | OCR — detekce žlutého labelu (aktuální tržní cena EURUSD 1.17926) jako samostatná třída 'yellow'; žlutý band se přeskakuje a nevstupuje do přiřazení Entry/SL/TP; opraveny 3-band a 2-band případy pro Buy i Sell
1.5.47 | OCR analýza screenshotu — opravena logika přiřazení Entry/SL/TP: 3 pásma bez červené (Buy) dostávala prohozené SL↔TP; 2 pásma bez červené předpokládala Sell; rozšířen scan strip (5/6 %); post-processing auto-prohodí SL↔TP pokud jsou hodnoty nekonzistentní
1.5.46 | Firebase — oprava KeyError 'level': get_rank_info() nemá klíč level, správně je rank_idx+1
1.5.45 | Firebase Sync — tlačítko Sync moje XP nyní ukazuje výsledek a chybový messagebox (dříve selhávalo tiše); HTTP 403 vede na návod k opravě Rules
1.5.44 | Firebase — přechod z requests na urllib (standardní knihovna, funguje v .exe bez instalace); odstraněna závislost na externím balíčku
1.5.43 | Firebase — auto-instalace requests: appka použije sys.executable (správný Python) a nabídne automatickou instalaci přes pip přímo z UI
1.5.42 | Firebase test připojení — opraveno: messagebox místo tichého selhání; detekce chybějící knihovny requests s návodem pip install; auto-detekce EU vs US URL (zkusí europe-west1 pokud primární URL selže); jasné chybové hlášky pro 401/403
1.5.41 | Firebase žebříček — online srovnání XP s kamarády; tlačítko 🏆 Žebříček v toolbaru; tab 🔥 Firebase v Nastavení (URL, secret, jméno, test připojení, ruční sync); auto-sync XP po každém uložení obchodu v background threadu
1.5.40 | P&L % — opravený výpočet: primárně zisk_mena / kapitál účtu (REAL mód), fallback z cenových úrovní vstup/SL/TP × směr × výsledek (BACKTEST i REAL bez zisk_mena)
1.5.39 | Trade ID — každý obchod dostane unikátní #ID (automaticky přiřazeno při uložení, zpětně doplněno i starým); Řazení sloupců — klik na záhlaví řadí vzestupně, druhý klik sestupně, šipka ↑↓ indikuje aktivní řazení (číselné sloupce jako číslo, kvalita A+>A>B, checklist jako %); Galerie — každá karta zobrazuje #ID a tlačítko → přejít na obchod (přepne ZÁPIS tab, resetuje filtr, vybere řádek)
1.5.38 | BACKTEST mód — odstraněny pole Účet a Zisk/Ztráta z formuláře; skryto tlačítko ÚČTY z toolbaru; REAL mód beze změny
1.5.37 | XP — 24 nových odznaků (trades_250/1000, wins_25/50/100, streak_7, big_rrr, comeback, all_results, symbols_5/10, photos/notes/tags, checklist_50, first_be, bt_1h/5h/10h/20h, journal_100, xp_10000); Backtesting stopky — tlačítko ⏱ START v toolbaru, po každé hodině zahraje melodický zvuk, vyskočí popup s XP a odznaky, pravý klik = menu (pauza/reset/celkový čas)
1.5.36 | Periody — filtr účtu: dropdown "Účet" v hlavičce záložky filtruje všechna data (KPI karty, oba grafy, obě tabulky); výchozí "Všechny účty"; název účtu se zobrazuje v nadpisech sekcí a grafů
1.5.35 | XP Bodovací systém — rank žebříček (Nováček → Elite); XP za backtest/reálný obchod, WIN bonus, disciplína (LOSS+SL), foto, poznámka, checklist 100%, zápis do deníku; 8 konfigurovatelných pravidel (denní/týdenní limit, bez revenge, min. RRR, série výher…); 16 odznaků/achievements; XP badge v toolbaru; přehledové okno s progress barem a historií; záložka ⭐ XP Systém v Nastavení
1.5.34 | Oprava výpočtu Aktuální kapitál a P&L% — strip() na názvu účtu zabraňuje nespárování s obchody; výpočet Aktuální = Počáteční + Σ(zisky/ztráty připojených obchodů), P&L% = Σ P&L / Počáteční × 100
1.5.33 | Oprava výpočtu Aktuální kapitál a P&L% — robustní parser čísel zvládne všechny formáty: 252285, 252285,42, 252 285,42, 252.285,42, 252,285.42; Aktuální vždy zobrazuje alespoň počáteční kapitál
1.5.32 | Správce účtů — tabulka přepsána na ttk.Treeview: perfektní zarovnání sloupců, resize tažením, výběr řádku aktivuje toolbar (📋 Detail / ✏ Upravit / 🗑 Smazat), dvojklik otevře detail; barevné řádky dle statusu (Aktivní/Funded/Propadlý…)
1.5.31 | Kritická oprava — accounts_combo chyběl v global deklaraci show_main_screen(), takže přiřazený účet se při ukládání obchodu vždy ztratil (widget byl lokální proměnná, pridat_obchod() viděl None)
1.5.30 | Správce účtů — kliknutí na účet nebo tlačítko 📋 otevře detail s kompletním seznamem připojených obchodů (datum, symbol, směr, výsledek, P&L, P&L%); KPI souhrn v detailu: Obchodů, W/L/BE, Winrate, Celk. P&L, Aktuální kapitál, P&L%; Robustnější parsování P&L hodnot (1000, -1000, +500, 1 000, 1000,50)
1.5.29 | Záložka Analýza — kompletní redesign: KPI karty (Winrate, Profit Factor, Expectancy, Max DD, Streak…) + barevné tabulky v kartách místo monospace textu; Správce účtů — nové sloupce Aktuální kapitál a P&L% automaticky počítané z obchodů; Nové sloupce v seznamu obchodů: Zisk/Ztráta a P&L% (přidat přes konfiguraci sloupců)
1.5.28 | Kompletní přepis OCR detekce cen ze screenshotu — úzký band strip (4.5%) vyhne se šumu z grafu; Entry/TP rozhodnutí podle Y-polohy (prostřední box = Entry) místo záměnné barvy; SL = červená (spolehlivé); BINARY+INVERT threshold jako první pokus pro bílé bg; lepší parsování cen (3 378,64)
1.5.27 | Oprava kritické chyby — ACCOUNTS_FILE chyběl v global deklaraci ve všech 4 funkcích otevření projektu; účty se nyní správně ukládají v otevřeném projektu
1.5.26 | Oprava ukládání účtů — účty se nyní správně uloží a zobrazí v seznamu; Pole Zisk/Ztráta v záznamu obchodu — ručně zadáš částku v domácí měně; Tlačítko 💱 kalkulačka měn — přepočet z USD/EUR na CZK a jiné; Nastavení domácí měny v Obecném nastavení (CZK, EUR, USD, GBP…); Sloupec P&L v správci účtů — součet zaznamenaných obchodů per-účet; Robustnější správce účtů — chybová hláška při pokusu uložit bez projektu
1.5.25 | Okno Co je nového — zobrazí se automaticky po aktualizaci s přehledem všech změn od předchozí verze; Funguje i při přeskočení více verzí najednou; Zobrazí se jen jednou při prvním spuštění nové verze; Verze se ukládá do last_version.txt
1.5.24 | Redesign tmavého motivu — harmonická slate paleta bez křiklavých barev; Toolbar sjednocen (jedno tlačítko = jeden styl); TAKE PROFIT a STOP LOSS labely reagují na motiv; Intro karty projektů mají jednotnou barvu hlavičky; Vylepšené WIN/LOSS/BE odstíny
1.5.23 | Intro obrazovka plně přizpůsobena motivu — karty projektů, pozadí a texty reagují na zvolený motiv; Tmavý a Tmavý modrý motiv dostupný přímo z intro obrazovky; Přepínač motivů na intro obrazovce obsahuje všechny 5 motivů
1.5.22 | Nový tmavý motiv — stejný design jako okno Správce účtů; Motiv Tmavý modrý; Klasický motiv zachován; Výchozí motiv změněn na Tmavý; Vylepšený ttk styling pro tmavé motivy
1.5.21 | Pole Začátek a Konec účtu v správci účtů; Zobrazení datumu v seznamu účtů
1.5.20 | Správce účtů — FTMO Challenge/Verifikace/Funded; Pole Účet ve formuláři; Tlačítko 🏦 ÚČTY v toolbaru; Per-účet statistiky v Analýze
1.5.19 | Zvýšení verze pro testování update notifikace
1.5.18 | Changelog v update dialogu — co je nového při každé aktualizaci; Startup automatická kontrola s dialogem jen při nové verzi; Scrollovatelný changelog s přehledem změn
1.5.17 | Nová záložka 📅 PERIODY — týdenní a měsíční přehled výkonnosti; Bar charty posledních 10 týdnů / 13 měsíců; KPI karty (Win Rate, Celkem R, Profit Factor); Detailní tabulka s historií
1.5.16 | Vylepšená OCR pro tmavé TradingView téma (Tomáš); Ukládání debug PNG z Tesseractu; Oprava _is_plausible pro EURUSD; Rozšíření OCR pruhu na 5 %
1.5.15 | Oprava detekce časů v dark-bg screenshotech (Feb'25 bez mezery); Rozšíření Entry HSV rozsahu pro teal barvu; Zúžení OCR pruhu pro tmavé téma
1.5.14 | Podpora tmavého motivu TradingView ve screenshotu; Automatická detekce dark bg; HSV contour fallback pro ceny
1.5.13 | Záložka MOJE PRAVIDLA; Editor obchodních pravidel s kategoriemi
1.5.12 | Monte Carlo simulace; A/B test strategie; Výběr N obchodů ze vzorku
"""

UPDATE_URL = "https://raw.githubusercontent.com/mochstanpda-hub/smc-journal/main/BACKTESTING.py"

def _show_update_dialog(connected, remote_ver=None, error_msg=None, on_update=None,
                        changelog_entries=None):
    """
    Dialog aktualizace s changelog sekcí.
    changelog_entries = list of (verze, [změna1, změna2, ...]) pro verze novější než aktuální.
    """
    has_update   = bool(on_update)
    has_changelog = bool(changelog_entries)

    # Výška: závisí na počtu položek changelogu
    base_h = 340
    if has_changelog:
        n_items = sum(len(ch) for _, ch in changelog_entries)
        base_h  = min(600, base_h + n_items * 20 + len(changelog_entries) * 28)
    elif not connected:
        base_h = 260

    win = tk.Toplevel(root)
    win.title("Aktualizace")
    win.resizable(False, True)
    win.configure(bg=DT_BG)
    win.geometry(f"520x{base_h}")
    win.minsize(520, 240)
    win.lift()
    win.focus_set()

    # ── Hlavička ───────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg='#0f172a', pady=11)
    hdr.pack(fill='x')
    tk.Label(hdr, text="🔄  Aktualizace programu", bg='#0f172a', fg='white',
             font=('Segoe UI', 12, 'bold')).pack(side='left', padx=16)
    dot_text  = '●  GitHub: připojeno' if connected else '●  GitHub: offline'
    dot_color = '#22c55e' if connected else '#ef4444'
    tk.Label(hdr, text=dot_text, bg='#0f172a', fg=dot_color,
             font=('Segoe UI', 9)).pack(side='right', padx=16)

    # ── Tlačítka (pack first = always visible at bottom) ───────────────────
    bf = tk.Frame(win, bg=DT_BG, padx=20, pady=10)
    bf.pack(fill='x', side='bottom')
    if has_update:
        def _do():
            win.destroy(); on_update()
        tk.Button(bf, text="⬇  STÁHNOUT A NAINSTALOVAT", bg='#16a34a', fg='white',
                  font=('Segoe UI', 10, 'bold'), padx=14, pady=8, relief='flat',
                  cursor='hand2', activebackground='#15803d',
                  command=_do).pack(side='left')
        tk.Button(bf, text="Později", bg=DT_BTN, fg=DT_TEXT,
                  font=('Segoe UI', 9), padx=10, pady=8, relief='flat',
                  cursor='hand2', command=win.destroy).pack(side='left', padx=(10, 0))
    else:
        def _recheck():
            win.destroy()
            root.after(100, lambda: check_for_updates(silent=False, startup=False))
        tk.Button(bf, text="🔍  Vyhledat aktualizace", bg='#1e3a5f', fg='#60a5fa',
                  font=('Segoe UI', 10, 'bold'), padx=14, pady=8, relief='flat',
                  cursor='hand2', activebackground='#1e40af',
                  command=_recheck).pack(side='left')
        tk.Button(bf, text="Zavřít", bg=DT_BTN, fg=DT_TEXT,
                  font=('Segoe UI', 10), padx=18, pady=8, relief='flat',
                  cursor='hand2', command=win.destroy).pack(side='right')

    # ── Scrollovatelné tělo ────────────────────────────────────────────────
    body_outer = tk.Frame(win, bg=DT_BG)
    body_outer.pack(fill='both', expand=True)
    body_canv = tk.Canvas(body_outer, bg=DT_BG, highlightthickness=0)
    body_scb  = ttk.Scrollbar(body_outer, orient='vertical', command=body_canv.yview)
    body_canv.configure(yscrollcommand=body_scb.set)
    body_canv.pack(side='left', fill='both', expand=True)
    body_scb.pack(side='right', fill='y')
    body = tk.Frame(body_canv, bg=DT_BG, padx=20, pady=14)
    body_canv.create_window((0, 0), window=body, anchor='nw')
    body.bind("<Configure>", lambda e: body_canv.configure(scrollregion=body_canv.bbox("all")))
    body_canv.bind("<MouseWheel>", lambda e: body_canv.yview_scroll(int(-1*(e.delta/120)), "units"))

    if not connected:
        tk.Label(body, text="⚠️  Nepodařilo se připojit k GitHubu.", bg=DT_BG,
                 fg='#ef4444', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        if error_msg:
            tk.Label(body, text=str(error_msg), bg=DT_BG, fg=DT_SUBTEXT,
                     font=('Segoe UI', 9), wraplength=460, justify='left').pack(anchor='w', pady=(6, 0))
        return

    # ── Verze info ─────────────────────────────────────────────────────────
    vf = tk.Frame(body, bg=DT_SURFACE, padx=16, pady=10)
    vf.pack(fill='x', pady=(0, 12))

    def _vrow(parent, label, value, val_color):
        r = tk.Frame(parent, bg=DT_SURFACE); r.pack(fill='x', pady=2)
        tk.Label(r, text=label, bg=DT_SURFACE, fg=DT_SUBTEXT,
                 font=('Segoe UI', 10), width=15, anchor='w').pack(side='left')
        tk.Label(r, text=value, bg=DT_SURFACE, fg=val_color,
                 font=('Segoe UI', 10, 'bold')).pack(side='left')

    _vrow(vf, "Tvoje verze:", VERSION, DT_TEXT)
    gh_color = '#22c55e' if has_update else DT_TEXT
    _vrow(vf, "GitHub verze:", remote_ver or '—', gh_color)

    if has_update:
        status_f = tk.Frame(body, bg='#14532d', padx=12, pady=7)
        status_f.pack(fill='x', pady=(0, 12))
        tk.Label(status_f, text="🚀  Nová verze je k dispozici!",
                 bg='#14532d', fg='#86efac',
                 font=('Segoe UI', 11, 'bold')).pack(side='left')
        tk.Label(status_f, text=f"  {VERSION}  →  {remote_ver}",
                 bg='#14532d', fg='#4ade80',
                 font=('Segoe UI', 10)).pack(side='left', padx=(8, 0))
    else:
        tk.Label(body, text="✓  Máš nejnovější verzi.", bg=DT_BG,
                 fg='#22c55e', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 8))

    # ── Changelog sekce ────────────────────────────────────────────────────
    if has_changelog:
        tk.Label(body, text="📋  Co je nového", bg=DT_BG, fg=DT_TEXT,
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 6))

        for ver, items in changelog_entries:
            # Záhlaví verze
            vh = tk.Frame(body, bg='#1e3a5f', pady=5, padx=10)
            vh.pack(fill='x', pady=(0, 2))
            tk.Label(vh, text=f"Verze {ver}", bg='#1e3a5f', fg='#93c5fd',
                     font=('Segoe UI', 9, 'bold')).pack(side='left')

            # Položky changelogu
            for item in items:
                if not item.strip(): continue
                irow = tk.Frame(body, bg=DT_BG, padx=14)
                irow.pack(fill='x', pady=1)
                tk.Label(irow, text="•", bg=DT_BG, fg='#60a5fa',
                         font=('Segoe UI', 9)).pack(side='left', padx=(0, 6))
                tk.Label(irow, text=item.strip(), bg=DT_BG, fg=DT_TEXT,
                         font=('Segoe UI', 9), wraplength=440,
                         justify='left', anchor='w').pack(side='left', fill='x', expand=True)



def _parse_remote_changelog(text, current_ver):
    """
    Parsuje CHANGELOG blok z textu vzdáleného souboru.
    Vrátí list of (verze, [položky]) pro verze NOVĚJŠÍ než current_ver.
    """
    import re
    def vt(v):
        try: return tuple(int(x) for x in str(v).strip().split('.'))
        except: return (0,)

    # Najdi CHANGELOG = """...""" blok
    m = re.search(r'CHANGELOG\s*=\s*"""(.*?)"""', text, re.DOTALL)
    if not m:
        return []

    entries = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line:
            continue
        # Formát: "1.5.17 | Změna 1; Změna 2"
        mm = re.match(r'^(\d+\.\d+\.\d+)\s*\|\s*(.+)$', line)
        if not mm:
            continue
        ver, changes_raw = mm.group(1), mm.group(2)
        if vt(ver) > vt(current_ver):
            items = [c.strip() for c in changes_raw.split(';') if c.strip()]
            entries.append((ver, items))

    # Seřadit od nejnovější
    entries.sort(key=lambda x: vt(x[0]), reverse=True)
    return entries


def check_for_updates(silent=False, startup=False):
    """
    Zkontroluje GitHub pro novou verzi programu.
    silent=True  → žádný dialog vůbec (jen rozsviť UPDATE tlačítko)
    startup=True → dialog JEN pokud je nová verze (ne "jsi aktuální")
    """
    if "TVUJ_USERNAME" in UPDATE_URL:
        return
    if silent:
        # Tichý režim — žádné dialogy, žádná okna
        try:
            import re, urllib.request
            req = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'SMCJournal-Updater/1.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                header_bytes = response.read(4096).decode('utf-8', errors='ignore')
            m = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', header_bytes, re.MULTILINE)
            if m:
                remote_ver = m.group(1).strip()
                def _vt(v):
                    try: return tuple(int(x) for x in str(v).strip().split('.'))
                    except: return (0,)
                if _vt(remote_ver) > _vt(VERSION):
                    # Je dostupná nová verze — rozsvítíme UPDATE tlačítko (pokud existuje)
                    try:
                        for w in root.winfo_children():
                            for ww in (w.winfo_children() if hasattr(w, 'winfo_children') else []):
                                if hasattr(ww, 'cget') and 'UPDATE' in str(ww.cget('text') if ww.winfo_class() == 'Button' else ''):
                                    ww.configure(bg='#e74c3c', text=f"🔴 UPDATE  {remote_ver}")
                    except Exception:
                        pass
        except Exception:
            pass
        return

    def ver_tuple(v):
        try: return tuple(int(x) for x in str(v).strip().split('.'))
        except: return (0,)

    try:
        import re, urllib.request
        req = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'SMCJournal-Updater/1.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            # Čteme víc bajtů aby se vešel CHANGELOG blok
            header_bytes = response.read(20480).decode('utf-8', errors='ignore')

        m = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', header_bytes, re.MULTILINE)
        if not m:
            if not startup:
                _show_update_dialog(connected=True, remote_ver='???',
                    error_msg="Nelze přečíst verzi ze souboru na GitHubu.\nZkontroluj formát: VERSION = \"x.y.z\"")
            return

        remote_ver = m.group(1).strip()
        is_new     = ver_tuple(remote_ver) > ver_tuple(VERSION)

        # Parsuj changelog pro verze novější než aktuální
        changelog_entries = _parse_remote_changelog(header_bytes, VERSION) if is_new else []

        # Žádná nová verze
        if not is_new:
            if not startup:
                # Manuální kliknutí → ukáž "jsi aktuální"
                try: _show_update_dialog(connected=True, remote_ver=remote_ver)
                except Exception: messagebox.showinfo("Aktualizace", f"Tvoje verze: {VERSION}\nGitHub: {remote_ver}\nMáš nejnovější verzi.")
            return

        # ── Nová verze dostupná — rozsviť tlačítko ───────────────────────────
        try:
            for w in root.winfo_children():
                for ww in (w.winfo_children() if hasattr(w, 'winfo_children') else []):
                    if hasattr(ww, 'cget') and ww.winfo_class() == 'Button':
                        try:
                            if 'UPDATE' in str(ww.cget('text')):
                                ww.configure(bg='#dc2626', text=f"🔴 UPDATE  {remote_ver}")
                        except Exception: pass
        except Exception: pass

        def do_download():
            if getattr(sys, 'frozen', False):
                py_path  = os.path.join(os.path.dirname(sys.executable), 'BACKTESTING.py')
                tmp_path = py_path + '.new'
                try:
                    messagebox.showinfo("Stahování", f"Stahuji verzi {remote_ver}...\nPočkej prosím.")
                    req2 = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'SMCJournal-Updater/1.0'})
                    with urllib.request.urlopen(req2, timeout=60) as r:
                        new_content = r.read().decode('utf-8')
                except Exception as dl_err:
                    messagebox.showerror("Chyba stahování", f"Nepodařilo se stáhnout:\n{dl_err}")
                    return
                if len(new_content.encode('utf-8')) < 150_000:
                    messagebox.showerror("Chyba aktualizace",
                        f"Stažený soubor je příliš malý ({len(new_content)//1024} KB).\nAktualizace zrušena.")
                    return
                try: compile(new_content, 'BACKTESTING.py', 'exec')
                except SyntaxError as se:
                    messagebox.showerror("Chyba aktualizace",
                        f"Stažený soubor je poškozený (SyntaxError řádek {se.lineno}).\nAktualizace zrušena.")
                    return
                if os.path.exists(py_path): shutil.copy2(py_path, py_path + f'.backup_{VERSION}')
                with open(tmp_path, 'w', encoding='utf-8') as f: f.write(new_content)
                if os.path.exists(py_path): os.remove(py_path)
                os.rename(tmp_path, py_path)
                messagebox.showinfo("✅ Hotovo", f"Aktualizováno na verzi {remote_ver}.\nSpusť program znovu.")
            else:
                req2 = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'SMCJournal-Updater/1.0'})
                with urllib.request.urlopen(req2, timeout=30) as r:
                    new_content = r.read().decode('utf-8')
                if len(new_content.encode('utf-8')) < 150_000:
                    messagebox.showerror("Chyba aktualizace",
                        f"Stažený soubor je příliš malý ({len(new_content)//1024} KB).\nAktualizace zrušena.")
                    return
                try: compile(new_content, 'BACKTESTING.py', 'exec')
                except SyntaxError as se:
                    messagebox.showerror("Chyba aktualizace",
                        f"Stažený soubor je poškozený (SyntaxError řádek {se.lineno}).\nAktualizace zrušena.")
                    return
                current_path = os.path.abspath(__file__)
                shutil.copy2(current_path, current_path + f'.backup_{VERSION}')
                with open(current_path, 'w', encoding='utf-8') as f: f.write(new_content)
                messagebox.showinfo("✅ Hotovo", f"Aktualizováno na verzi {remote_ver}.\nSpusť program znovu.")
            try: root.destroy()
            except: pass
            sys.exit(0)

        try:
            _show_update_dialog(connected=True, remote_ver=remote_ver,
                                on_update=do_download,
                                changelog_entries=changelog_entries)
        except Exception:
            if messagebox.askyesno("🔄 Aktualizace",
                    f"Nová verze {remote_ver} (tvoje: {VERSION}). Stáhnout?"):
                do_download()

    except Exception as e:
        if not startup:
            try: _show_update_dialog(connected=False, error_msg=str(e))
            except Exception: messagebox.showerror("Chyba aktualizace", f"Nepodařilo se připojit k GitHubu:\n{e}")

# ==============================================================================
# MOTIVY (THEMES)
# ==============================================================================
THEMES = {
    # ── Tmavé motivy ──────────────────────────────────────────────────────────
    "Tmavý": {
        # Tailwind slate — profesionální tmavý motiv
        "BG":"#0f172a","PANEL":"#1e293b","SURFACE":"#293548",
        "TEXT":"#e2e8f0","SUBTEXT":"#64748b","ACCENT":"#3b82f6",
        "WIN_BG":"#0d2e1a","WIN_FG":"#4ade80",
        "LOSS_BG":"#2d0e0e","LOSS_FG":"#f87171",
        "BE_BG":"#2a1a07","BE_FG":"#fbbf24",
        "BTN":"#253348","ENTRY":"#1a2540","BORDER":"#334155",
        "SELECT_COLOR":"#253348","ttk":"clam",
    },
    "Tmavý modrý": {
        # Hlubší navy varianta
        "BG":"#080d1a","PANEL":"#0f1729","SURFACE":"#172033",
        "TEXT":"#e2e8f0","SUBTEXT":"#64748b","ACCENT":"#6366f1",
        "WIN_BG":"#0a2414","WIN_FG":"#34d399",
        "LOSS_BG":"#250a0a","LOSS_FG":"#fb7185",
        "BE_BG":"#21180a","BE_FG":"#fbbf24",
        "BTN":"#1a2440","ENTRY":"#0f1729","BORDER":"#1e2d50",
        "SELECT_COLOR":"#1a2440","ttk":"clam",
    },
    # ── Světlé motivy ─────────────────────────────────────────────────────────
    "Klasický": {
        "BG":"#f0f0f0","PANEL":"#f0f0f0","SURFACE":"#e0e0e0",
        "TEXT":"#1a1a1a","SUBTEXT":"#555555","ACCENT":"#0078d4",
        "WIN_BG":"#d4edda","WIN_FG":"#155724",
        "LOSS_BG":"#f8d7da","LOSS_FG":"#721c24",
        "BE_BG":"#fff3cd","BE_FG":"#856404",
        "BTN":"#e0e0e0","ENTRY":"#ffffff","BORDER":"#aaaaaa",
        "SELECT_COLOR":"#ffffff","ttk":"vista",
    },
    "Šedý profesionál": {
        "BG":"#eaecee","PANEL":"#dde1e4","SURFACE":"#cfd4d8",
        "TEXT":"#1c2833","SUBTEXT":"#566573","ACCENT":"#2e86c1",
        "WIN_BG":"#d5f5e3","WIN_FG":"#1e8449",
        "LOSS_BG":"#fadbd8","LOSS_FG":"#922b21",
        "BE_BG":"#fef9e7","BE_FG":"#9a7d0a",
        "BTN":"#cfd4d8","ENTRY":"#f4f6f6","BORDER":"#aab7b8",
        "SELECT_COLOR":"#f4f6f6","ttk":"vista",
    },
    "Světlý elegantní": {
        "BG":"#ffffff","PANEL":"#f8f9fa","SURFACE":"#e9ecef",
        "TEXT":"#212529","SUBTEXT":"#6c757d","ACCENT":"#0d6efd",
        "WIN_BG":"#d1e7dd","WIN_FG":"#0a3622",
        "LOSS_BG":"#f8d7da","LOSS_FG":"#58151c",
        "BE_BG":"#fff3cd","BE_FG":"#664d03",
        "BTN":"#e9ecef","ENTRY":"#ffffff","BORDER":"#ced4da",
        "SELECT_COLOR":"#ffffff","ttk":"vista",
    },
}
_SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)) if not getattr(sys,'frozen',False) else os.path.dirname(sys.executable), 'projects')
THEME_FILE        = os.path.join(_SETTINGS_DIR, 'theme.txt')
LAST_VERSION_FILE = os.path.join(_SETTINGS_DIR, 'last_version.txt')

def load_theme_name():
    try:
        if os.path.exists(THEME_FILE):
            t = open(THEME_FILE, encoding='utf-8').read().strip()
            if t in THEMES: return t
    except: pass
    return "Tmavý"  # výchozí motiv

def save_theme_name(name):
    try:
        os.makedirs('projects', exist_ok=True)
        open(THEME_FILE, 'w', encoding='utf-8').write(name)
    except: pass

def apply_theme(name):
    """Aplikuje motiv — aktualizuje globální DT_ proměnné."""
    global DT_BG, DT_PANEL, DT_SURFACE, DT_TEXT, DT_SUBTEXT, DT_ACCENT
    global DT_WIN_BG, DT_WIN_FG, DT_LOSS_BG, DT_LOSS_FG, DT_BE_BG, DT_BE_FG
    global DT_BTN, DT_ENTRY, DT_BORDER
    t = THEMES.get(name, THEMES["Klasický"])
    DT_BG=t["BG"]; DT_PANEL=t["PANEL"]; DT_SURFACE=t["SURFACE"]
    DT_TEXT=t["TEXT"]; DT_SUBTEXT=t["SUBTEXT"]; DT_ACCENT=t["ACCENT"]
    DT_WIN_BG=t["WIN_BG"]; DT_WIN_FG=t["WIN_FG"]
    DT_LOSS_BG=t["LOSS_BG"]; DT_LOSS_FG=t["LOSS_FG"]
    DT_BE_BG=t["BE_BG"]; DT_BE_FG=t["BE_FG"]
    DT_BTN=t["BTN"]; DT_ENTRY=t["ENTRY"]; DT_BORDER=t["BORDER"]
    save_theme_name(name)

# Načti motiv při startu — výchozí je "Tmavý" pokud ještě nebyl vybrán jiný
apply_theme(load_theme_name())

# ==============================================================================
# CO JE NOVÉHO — zobrazit po aktualizaci
# ==============================================================================

def load_last_version():
    """Vrátí verzi z minulého spuštění (nebo '' pokud soubor neexistuje)."""
    try:
        if os.path.exists(LAST_VERSION_FILE):
            return open(LAST_VERSION_FILE, encoding='utf-8').read().strip()
    except: pass
    return ''

def save_last_version(ver):
    """Uloží aktuální verzi jako 'naposledy spuštěnou'."""
    try:
        os.makedirs(_SETTINGS_DIR, exist_ok=True)
        open(LAST_VERSION_FILE, 'w', encoding='utf-8').write(ver)
    except: pass

def _parse_local_changelog_since(old_ver):
    """
    Parsuje lokální CHANGELOG string a vrátí položky pro všechny verze
    NOVĚJŠÍ než old_ver (ale nejvýše VERSION).
    Vrátí list of (verze_str, [položky]) seřazený od nejnovější.
    """
    import re
    def vt(v):
        try: return tuple(int(x) for x in str(v).strip().split('.'))
        except: return (0,)
    old_t = vt(old_ver)
    entries = []
    for line in CHANGELOG.splitlines():
        line = line.strip()
        if not line: continue
        m = re.match(r'^(\d+\.\d+\.\d+)\s*\|\s*(.+)$', line)
        if not m: continue
        ver, changes_raw = m.group(1), m.group(2)
        if vt(ver) > old_t:
            items = [c.strip() for c in changes_raw.split(';') if c.strip()]
            entries.append((ver, items))
    entries.sort(key=lambda x: vt(x[0]), reverse=True)
    return entries

def show_whats_new(old_ver, entries):
    """
    Zobrazí okno 'Co je nového' se všemi změnami od old_ver do VERSION.
    Volat po zobrazení hlavního okna.
    """
    n_items = sum(len(ch) for _, ch in entries)
    n_vers  = len(entries)
    win_h   = min(680, 180 + n_vers * 34 + n_items * 22)

    win = tk.Toplevel(root)
    win.title("Co je nového")
    win.configure(bg=DT_BG)
    win.geometry(f"560x{win_h}")
    win.minsize(560, 300)
    win.resizable(False, True)
    win.lift(); win.focus_set()
    # Vystřed na rodiče
    root.update_idletasks()
    rx, ry = root.winfo_x(), root.winfo_y()
    rw, rh = root.winfo_width(), root.winfo_height()
    wx, wy = rx + (rw - 560) // 2, ry + (rh - win_h) // 2
    win.geometry(f"560x{win_h}+{wx}+{wy}")

    # ── Hlavička ──────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg=DT_ACCENT, pady=14)
    hdr.pack(fill='x')
    tk.Label(hdr, text="🎉  Co je nového", bg=DT_ACCENT, fg='#ffffff',
             font=('Segoe UI', 13, 'bold')).pack(side='left', padx=18)
    tk.Label(hdr, text=f"v{old_ver}  →  v{VERSION}", bg=DT_ACCENT,
             fg='#dbeafe', font=('Segoe UI', 10)).pack(side='right', padx=18)

    # ── Scrollovatelný obsah ─────────────────────────────────────────────────
    outer = tk.Frame(win, bg=DT_BG)
    outer.pack(fill='both', expand=True)
    canv = tk.Canvas(outer, bg=DT_BG, highlightthickness=0)
    scb  = ttk.Scrollbar(outer, orient='vertical', command=canv.yview)
    canv.configure(yscrollcommand=scb.set)
    canv.pack(side='left', fill='both', expand=True)
    scb.pack(side='right', fill='y')
    body = tk.Frame(canv, bg=DT_BG, padx=20, pady=16)
    canv.create_window((0, 0), window=body, anchor='nw')
    body.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
    canv.bind("<MouseWheel>", lambda e: canv.yview_scroll(int(-1*(e.delta/120)), "units"))

    for ver, items in entries:
        # Verze záhlaví
        vh = tk.Frame(body, bg=DT_SURFACE, pady=6, padx=12)
        vh.pack(fill='x', pady=(0, 3))
        tk.Label(vh, text=f"  Verze {ver}", bg=DT_SURFACE, fg=DT_ACCENT,
                 font=('Segoe UI', 9, 'bold')).pack(side='left')
        # Položky
        for item in items:
            if not item.strip(): continue
            row = tk.Frame(body, bg=DT_BG, padx=12)
            row.pack(fill='x', pady=1)
            tk.Label(row, text="·", bg=DT_BG, fg=DT_SUBTEXT,
                     font=('Segoe UI', 10)).pack(side='left', padx=(0, 8))
            tk.Label(row, text=item.strip(), bg=DT_BG, fg=DT_TEXT,
                     font=('Segoe UI', 9), wraplength=470,
                     justify='left', anchor='w').pack(side='left', fill='x', expand=True)
        # Oddělovač
        tk.Frame(body, bg=DT_BORDER, height=1).pack(fill='x', pady=(4, 6))

    # ── Zavřít ────────────────────────────────────────────────────────────────
    bf = tk.Frame(win, bg=DT_BG, padx=20, pady=10)
    bf.pack(fill='x', side='bottom')
    tk.Button(bf, text="✓  Super, zavřít", command=win.destroy,
              bg=DT_ACCENT, fg='#ffffff',
              font=('Segoe UI', 10, 'bold'), padx=18, pady=8,
              relief='flat', cursor='hand2').pack(side='right')

_whats_new_shown = False   # Zobrazit jen jednou za celé spuštění

def check_whats_new():
    """
    Porovná aktuální VERSION s poslední spuštěnou verzí.
    Pokud se liší → zobrazí okno s novinkama a uloží aktuální verzi.
    Volat po zobrazení hlavního okna (show_intro_screen).
    Zobrazí se max. jednou za celé spuštění programu.
    """
    global _whats_new_shown
    if _whats_new_shown:
        return
    last = load_last_version()
    def vt(v):
        try: return tuple(int(x) for x in str(v).strip().split('.'))
        except: return (0,)

    if not last:
        # První spuštění — jen ulož verzi, nic nezobrazuj
        save_last_version(VERSION)
        _whats_new_shown = True
        return

    if vt(VERSION) > vt(last):
        entries = _parse_local_changelog_since(last)
        save_last_version(VERSION)
        _whats_new_shown = True
        if entries:
            root.after(400, lambda: show_whats_new(last, entries))
    else:
        _whats_new_shown = True

def apply_dark_theme(root):
    t = THEMES.get(load_theme_name(), THEMES["Tmavý"])
    style = ttk.Style(root)
    ttk_theme = t.get("ttk", "clam")
    try: style.theme_use(ttk_theme)
    except:
        try: style.theme_use('clam')
        except:
            try: style.theme_use('default')
            except: pass

    # ── Treeview ──────────────────────────────────────────────────────────────
    style.configure('Treeview', rowheight=24, font=('Segoe UI', 9),
                    background=DT_ENTRY, foreground=DT_TEXT,
                    fieldbackground=DT_ENTRY, borderwidth=0)
    style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'),
                    background=DT_SURFACE, foreground=DT_TEXT,
                    relief='flat', borderwidth=0)
    style.map('Treeview',
              background=[('selected', DT_ACCENT)],
              foreground=[('selected', '#ffffff')])
    style.map('Treeview.Heading',
              background=[('active', DT_SURFACE)])

    # ── Notebook (záložky) ────────────────────────────────────────────────────
    style.configure('TNotebook', background=DT_BG, borderwidth=0)
    style.configure('TNotebook.Tab',
                    background=DT_SURFACE, foreground=DT_SUBTEXT,
                    padding=[12, 6], font=('Segoe UI', 9))
    style.map('TNotebook.Tab',
              background=[('selected', DT_PANEL)],
              foreground=[('selected', DT_ACCENT)])

    # ── Combobox ──────────────────────────────────────────────────────────────
    style.configure('TCombobox',
                    fieldbackground=DT_ENTRY, background=DT_SURFACE,
                    foreground=DT_TEXT, selectbackground=DT_ACCENT,
                    selectforeground='#ffffff', insertcolor=DT_TEXT,
                    borderwidth=1, relief='flat')
    style.map('TCombobox',
              fieldbackground=[('readonly', DT_ENTRY)],
              foreground=[('readonly', DT_TEXT)],
              selectbackground=[('readonly', DT_ACCENT)])

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    style.configure('Vertical.TScrollbar',
                    background=DT_SURFACE, troughcolor=DT_BG,
                    borderwidth=0, arrowcolor=DT_SUBTEXT)
    style.configure('Horizontal.TScrollbar',
                    background=DT_SURFACE, troughcolor=DT_BG,
                    borderwidth=0, arrowcolor=DT_SUBTEXT)

    # ── PanedWindow sash ──────────────────────────────────────────────────────
    style.configure('TPanedwindow', background=DT_BORDER)

    # ── Globální widget defaults ──────────────────────────────────────────────
    root.configure(bg=DT_BG)
    root.option_add('*Font', 'Segoe\\ UI 9')
    root.option_add('*Background',          DT_BG)
    root.option_add('*Foreground',          DT_TEXT)
    root.option_add('*Label.Background',    DT_BG)
    root.option_add('*Label.Foreground',    DT_TEXT)
    root.option_add('*Frame.Background',    DT_BG)
    root.option_add('*LabelFrame.Background', DT_PANEL)
    root.option_add('*LabelFrame.Foreground', DT_TEXT)
    root.option_add('*Entry.Background',    DT_ENTRY)
    root.option_add('*Entry.Foreground',    DT_TEXT)
    root.option_add('*Entry.InsertBackground', DT_TEXT)
    root.option_add('*Entry.Relief',        'flat')
    root.option_add('*Entry.BorderWidth',   1)
    root.option_add('*Text.Background',     DT_ENTRY)
    root.option_add('*Text.Foreground',     DT_TEXT)
    root.option_add('*Text.InsertBackground', DT_TEXT)
    root.option_add('*Text.Relief',         'flat')
    root.option_add('*Button.Relief',       'flat')
    root.option_add('*Button.BorderWidth',  0)
    root.option_add('*Button.Cursor',       'hand2')
    root.option_add('*Button.Background',   DT_BTN)
    root.option_add('*Button.Foreground',   DT_TEXT)
    root.option_add('*Button.activeBackground', DT_SURFACE)
    root.option_add('*Button.activeForeground', DT_TEXT)
    root.option_add('*Listbox.Background',  DT_ENTRY)
    root.option_add('*Listbox.Foreground',  DT_TEXT)
    root.option_add('*Listbox.SelectBackground', DT_ACCENT)
    root.option_add('*Listbox.SelectForeground', '#ffffff')
    root.option_add('*Listbox.BorderWidth', 0)
    root.option_add('*Radiobutton.Background',       DT_BG)
    root.option_add('*Radiobutton.Foreground',       DT_TEXT)
    root.option_add('*Radiobutton.activeBackground', DT_BG)
    root.option_add('*Radiobutton.activeForeground', DT_TEXT)
    root.option_add('*Radiobutton.selectColor',      t["SELECT_COLOR"])
    root.option_add('*Checkbutton.Background',       DT_PANEL)
    root.option_add('*Checkbutton.Foreground',       DT_TEXT)
    root.option_add('*Checkbutton.activeBackground', DT_PANEL)
    root.option_add('*Checkbutton.activeForeground', DT_TEXT)
    root.option_add('*Checkbutton.selectColor',      t["SELECT_COLOR"])
    root.option_add('*Menu.Background',        DT_PANEL)
    root.option_add('*Menu.Foreground',        DT_TEXT)
    root.option_add('*Menu.ActiveBackground',  DT_SURFACE)
    root.option_add('*Menu.ActiveForeground',  DT_ACCENT)
    root.option_add('*Menu.Relief',            'flat')
    root.option_add('*Canvas.HighlightThickness', 0)
    root.option_add('*Entry.Background', DT_ENTRY)
    root.option_add('*Entry.Foreground', DT_TEXT)
    root.option_add('*Label.Background', DT_BG)
    root.option_add('*Label.Foreground', DT_TEXT)
    root.option_add('*Frame.Background', DT_BG)
    root.option_add('*Listbox.Background', DT_ENTRY)
    root.option_add('*Listbox.Foreground', DT_TEXT)

# ── Kořenový adresář aplikace ───────────────────────────────────────────
# .py skript → adresář kde leží skript
# .exe (PyInstaller) → adresář kde leží EXE
if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    try:    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
    except: _APP_DIR = os.getcwd()

# Hlavní složky (absolutní cesty — funguje jak ze skriptu, tak z EXE/instalátoru)
BASE_DIR    = os.path.join(_APP_DIR, 'projects')
DIR_BACKTEST = os.path.join(BASE_DIR, 'BACKTEST')
DIR_REAL     = os.path.join(BASE_DIR, 'REAL')
DIR_JOURNAL  = os.path.join(BASE_DIR, 'JOURNAL')
DIR_BACKUPS  = os.path.join(_APP_DIR, 'backups')

# Soubory a proměnné
DATA_FILE = ''
PROP_CONFIG_FILE = ''
CHECKLIST_FILE = '' 
SCORING_FILE = '' 
PAIRS_FILE = '' # NOVÉ: Soubor pro seznam párů
TIMEFRAMES_FILE = '' # NOVÉ: Soubor pro seznam timeframe
RULES_FILE = '' # NOVÉ: Soubor pro pravidla
FILTERS_FILE = '' # Soubor pro uložené filtry
ACCOUNTS_FILE = '' # Správce účtů (FTMO Challenge, Verifikace, Funded...)

# XP Systém — bodovací žebříček (globální, napříč projekty)
XP_FILE             = os.path.join(_APP_DIR, 'xp_data.json')
XP_CONFIG_FILE      = os.path.join(_APP_DIR, 'xp_config.json')
FIREBASE_CONFIG_FILE = os.path.join(_APP_DIR, 'firebase_config.json')

# Soubor s vlastními cestami projektů (globální, mimo projekt)
PROJECT_PATHS_FILE = os.path.join(_APP_DIR, 'project_paths.json')

# ── DEBUG LOG ────────────────────────────────────────────────────────────────
# Centrální debug soubor — vždy v adresáři programu (C:\SMC\debug_log.txt)
# Max velikost: 2 MB → pak se automaticky otočí (přejmenuje na debug_log.bak)
DEBUG_LOG_FILE    = os.path.join(_APP_DIR, 'debug_log.txt')
DEBUG_LOG_MAX_MB  = 2
_DEBUG_ENABLED    = True   # nastavit na False pro vypnutí bez nutnosti restartu

def _dbg_log(section: str, message: str, level: str = 'INFO'):
    """
    Připíše jeden záznam do C:\\SMC\\debug_log.txt.
    section  … krátký tag oblasti (např. 'OCR', 'XP', 'FIREBASE', 'TRADE', 'STARTUP')
    message  … libovolný text (může být víceřádkový)
    level    … 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
    """
    if not _DEBUG_ENABLED:
        return
    try:
        # Rotace pokud soubor překročí limit
        if os.path.exists(DEBUG_LOG_FILE):
            if os.path.getsize(DEBUG_LOG_FILE) > DEBUG_LOG_MAX_MB * 1024 * 1024:
                bak = DEBUG_LOG_FILE.replace('.txt', '.bak')
                try:
                    if os.path.exists(bak): os.remove(bak)
                    os.rename(DEBUG_LOG_FILE, bak)
                except Exception:
                    pass
        ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[{ts}] [{level:<5}] [{section}] {message}\n"
        with open(DEBUG_LOG_FILE, 'a', encoding='utf-8') as _lf:
            _lf.write(line)
    except Exception:
        pass   # debug log nikdy nesmí shodit program
# ─────────────────────────────────────────────────────────────────────────────

def load_project_paths():
    try:
        if os.path.exists(PROJECT_PATHS_FILE):
            with open(PROJECT_PATHS_FILE, 'r', encoding='utf-8') as _f:
                return json.load(_f)
    except Exception:
        pass
    return {}

def save_project_paths(data):
    try:
        with open(PROJECT_PATHS_FILE, 'w', encoding='utf-8') as _f:
            json.dump(data, _f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Chyba", f"Nepodařilo se uložit cesty projektů: {e}")

def _resolve_project_path(mode, name):
    """Vrátí cestu projektu — vlastní pokud nastavena a existuje, jinak výchozí."""
    key = f"{mode}/{name}"
    custom = load_project_paths().get(key)
    if custom and os.path.isdir(custom):
        return custom
    base = DIR_BACKTEST if mode == "BACKTEST" else DIR_REAL
    return os.path.join(base, name)

# Globální nastavení aplikace (prohlížeč, atd.)
GLOBAL_SETTINGS_FILE = os.path.join(_APP_DIR, 'global_settings.json')

def load_global_settings():
    try:
        if os.path.exists(GLOBAL_SETTINGS_FILE):
            with open(GLOBAL_SETTINGS_FILE, 'r', encoding='utf-8') as _f:
                return json.load(_f)
    except Exception:
        pass
    return {}

def save_global_settings(data):
    try:
        with open(GLOBAL_SETTINGS_FILE, 'w', encoding='utf-8') as _f:
            json.dump(data, _f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Chyba", f"Nepodařilo se uložit nastavení: {e}")

def get_app_currency():
    """Vrátí zvolenou domácí měnu (výchozí CZK). Ukládá se v global_settings.json."""
    return load_global_settings().get('app_currency', 'CZK')

def set_app_currency(cur):
    cfg = load_global_settings()
    cfg['app_currency'] = cur
    save_global_settings(cfg)

def get_browser_exe():
    """Vrátí cestu k prohlížeči z nastavení nebo auto-detekuje Edge/Chrome/Firefox."""
    cfg = load_global_settings()
    custom = cfg.get('browser_exe', '')
    if custom and os.path.exists(custom):
        return custom
    # Auto-detect
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "msedge.exe"  # fallback
IMAGES_DIR = ''
JOURNAL_FILE = os.path.join(DIR_JOURNAL, 'journal_entries.json')

# Globální stav
current_mode = "" 
current_project_name = ""
stats_canvases = [] # Pro equity curve
pie_canvases = []   # Pro kruhový graf
heatmap_canvases = [] # Pro heatmapu
_sort_col    = None   # aktuálně řazený sloupec v trades_tree
_sort_rev    = False  # True = sestupně
main_notebook = None  # hlavní ttk.Notebook (pro přepnutí tab z galerie)

periods_canvases    = []    # Pro charty v záložce PERIODY
periods_frames      = {}    # Odkazy na widgety v záložce PERIODY
periods_account_var = None  # StringVar — filtr účtu v záložce PERIODY

# Globální proměnné UI
trades_tree = None 
paned = None        
v_paned = None      
root = None         
save_btn = None     
filter_col_var = None
filter_val_var = None
editing_trade_index = None 
best_performers_frame = None

# Globální proměnná pro filtr statistik
stats_symbol_var = None
stats_symbol_combo = None

# Pokročilé filtry
filter_symbol_var = None
filter_result_var = None
filter_session_var = None
filter_date_from_var = None
filter_date_to_var = None
filter_tag_var = None
filter_rrr_min_var = None
filter_rrr_max_var = None

# Grafy – bar charts
bar_chart_frame = None
bar_chart_canvases = []

# Monte Carlo UI
mc_canvas_frame = None
mc_stats_text_widget = None 
mc_sim_count_var = None
mc_trade_count_var = None
mc_risk_var = None

# UI Analýza
stats_text = None
pie_graph_frame = None
stats_graph_frame = None
heatmap_graph_frame = None
kpi_frame = None
xp_badge_btn = None   # tlačítko v toolbaru zobrazující aktuální XP

# Backtesting stopky
bt_sw_running   = False   # je stopwatch aktivní?
bt_sw_start     = None    # datetime startu aktuálního sezení
bt_sw_elapsed   = 0       # sekundy z předchozích zastavení
bt_sw_btn       = None    # tk.Button v toolbaru
bt_sw_after_id  = None    # handle pro root.after()
bt_sw_xp_marks  = set()   # hodiny za které bylo uděleno XP v tomto sezení
tables_frame = None

# UI prvky formuláře
cas_otevreni_entry = None; cas_zavreni_entry = None; symbol_combo = None; smer_var = None
accounts_combo = None  # Dropdown pro výběr účtu ve formuláři
vstupni_hodnota_entry = None; stoploss_entry = None; takeprofit_entry = None; rrr_entry = None
pips_entry = None; session_combo = None; htf_combo = None; ltf_combo = None; fibo_combo = None
duvod_entry = None; poznamka_entry = None; vysledek_combo = None; den_tydne_entry = None
delka_obchodu_entry = None; slippage_entry = None; obrazky_list = None; score_label = None
news_var = None; news_event_entry = None
tags_entry = None # NOVÉ: Štítky
zisk_mena_entry = None  # Ručně zadaná částka zisku/ztráty v domácí měně
details_text = None; image_frame = None; gallery_inner = None
checklist_display_label = None

# UI Prop Firm Dashboard
prop_balance_label = None
prop_equity_label = None

# Globální proměnné UI (Journal)
cal_frame = None
journal_text = None
journal_trades_frame = None 
current_cal_date = datetime.now()
selected_journal_date = None

# Vytvoření složek
for d in [DIR_BACKTEST, DIR_REAL, DIR_JOURNAL, DIR_BACKUPS]:
    if not os.path.exists(d):
        os.makedirs(d)

COL_TRANSLATION = {
    "trade_id":       "#ID",
    "cas_otevreni": "Čas otevření", "cas_zavreni": "Čas zavření", "symbol": "Symbol",
    "smer": "Směr", "vstupni_hodnota": "Vstup", "stoploss": "Stop Loss",
    "takeprofit": "Take Profit", "rrr": "RRR", "pips": "Pips", "session": "Seance",
    "timeframe_graf": "HTF Graf", "timeframe_vstup": "LTF Vstup", "fibo": "Setup/Fibo",
    "duvod": "Důvod", "poznamka": "Poznámka", "vysledek": "Výsledek",
    "den_tydne": "Den", "delka_obchodu": "Délka", "slippage": "Slippage", "kvalita": "Kvalita",
    "news": "News (Impact)", "news_event": "Fundament (Zpráva)", "checklist_ratio": "✅ Pravidla",
    "tags": "Štítky (Tags)",
    "ucet": "Účet",
    "zisk_mena": "Zisk/Ztráta",
    "pnl_pct": "P&L %",
}

DEFAULT_SCORING = {
    "setups": {"Golden Zone (50-61.8)": 4, "Discount (>61.8)": 3, "Premium (<50)": 2, "Order Block": 1},
    "sessions": {"London": 3, "NY AM": 2, "NY PM": 2, "Asia": 1, "Close": 1},
    "days": {"Úterý": 2, "Středa": 2, "Čtvrtek": 2, "Pondělí": 1, "Pátek": 1},
    "rrr": {"1:1": 0, "1:2": 1, "1:3": 2, "1:4": 3, "1:5+": 4},
    "pips": {"5-10": 2, "10-15": 1, "15-20": 0, "20+": -1},
    "thresholds": {"A+": 13, "A": 9, "B": 5},
    "columns": ["cas_otevreni", "symbol", "smer", "rrr", "checklist_ratio", "vysledek"],
    "layout": {} 
}

# Výchozí páry, pokud není načten config
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "GBPAUD", "AUDUSD", "USDCAD", "EURJPY", "EURGBP", "US30", "NAS100", "DAX"]
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1W", "1M"]
FIBO_OPTIONS = ["DISCOUNT", "GOLDEN ZONE", "PREMIUM", "ORDER BLOCK", "BREAKER", "FVG ONLY"]
SESSIONS_LIST = ["Asia", "London", "NY AM", "NY PM", "Close"]

def load_scoring_config():
    if SCORING_FILE and os.path.exists(SCORING_FILE):
        try:
            with open(SCORING_FILE, 'r') as f:
                cfg = json.load(f)
                if "columns" not in cfg: cfg["columns"] = DEFAULT_SCORING["columns"]
                if "layout" not in cfg: cfg["layout"] = {}
                for key in ["setups", "sessions", "days", "rrr", "pips", "thresholds"]:
                    if key not in cfg: cfg[key] = DEFAULT_SCORING[key]
                return cfg
        except: return DEFAULT_SCORING
    return DEFAULT_SCORING

def save_scoring_config(config):
    if SCORING_FILE:
        with open(SCORING_FILE, 'w') as f: json.dump(config, f, indent=4)

def load_pairs_config():
    global PAIRS
    if PAIRS_FILE and os.path.exists(PAIRS_FILE):
        try:
            with open(PAIRS_FILE, 'r') as f:
                loaded_pairs = json.load(f)
                if isinstance(loaded_pairs, list) and len(loaded_pairs) > 0:
                    PAIRS = loaded_pairs
        except: pass

def save_pairs_config():
    if PAIRS_FILE:
        try:
            with open(PAIRS_FILE, 'w') as f: json.dump(PAIRS, f)
        except Exception as e: messagebox.showerror("Chyba", f"Nepodařilo se uložit páry: {e}")

def load_timeframes_config():
    global TIMEFRAMES
    if TIMEFRAMES_FILE and os.path.exists(TIMEFRAMES_FILE):
        try:
            with open(TIMEFRAMES_FILE, 'r') as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and len(loaded) > 0:
                    TIMEFRAMES = loaded
        except: pass

def save_timeframes_config():
    if TIMEFRAMES_FILE:
        try:
            with open(TIMEFRAMES_FILE, 'w') as f: json.dump(TIMEFRAMES, f)
        except Exception as e: messagebox.showerror("Chyba", f"Nepodařilo se uložit TF: {e}")

def load_rules_text():
    if RULES_FILE and os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r', encoding='utf-8') as f: return f.read()
        except: return ""
    return "Zde si napište svá obchodní pravidla (např. Risk management, Vstupní signály...)"

def save_rules_text(text):
    if RULES_FILE:
        try:
            with open(RULES_FILE, 'w', encoding='utf-8') as f: f.write(text)
            messagebox.showinfo("Uloženo", "Pravidla byla uložena.")
        except Exception as e: messagebox.showerror("Chyba", f"Nepodařilo se uložit pravidla: {e}")

# ==============================================================================
# 2. CHECKLIST & DATA LOADING
# ==============================================================================

def load_checklist_rules():
    if CHECKLIST_FILE and os.path.exists(CHECKLIST_FILE):
        try:
            with open(CHECKLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []
    return ["Trend (HTF Structure)", "Liquidity Sweep", "FVG / IMB", "Risk/Reward min 1:2"]

def save_checklist_rules(rules):
    if CHECKLIST_FILE:
        with open(CHECKLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=4)

def open_checklist_editor():
    editor = tk.Toplevel(root)
    editor.title("Editor pravidel strategie")
    editor.geometry("400x500")
    
    lbl = tk.Label(editor, text="PRAVIDLA VSTUPU (Checklist)", font=("Arial", 12, "bold"))
    lbl.pack(pady=10)
    
    listbox = tk.Listbox(editor, selectmode=tk.SINGLE, font=("Arial", 10))
    listbox.pack(fill="both", expand=True, padx=10, pady=5)
    
    current_rules = load_checklist_rules()
    for r in current_rules: listbox.insert(tk.END, r)
    
    entry = tk.Entry(editor, font=("Arial", 10))
    entry.pack(fill="x", padx=10, pady=5)
    
    def add_rule():
        val = entry.get().strip()
        if val:
            listbox.insert(tk.END, val)
            entry.delete(0, tk.END)
            
    def remove_rule():
        sel = listbox.curselection()
        if sel: listbox.delete(sel[0])
        
    def save_and_close():
        new_rules = list(listbox.get(0, tk.END))
        save_checklist_rules(new_rules)
        messagebox.showinfo("Uloženo", "Pravidla byla aktualizována.")
        editor.destroy()
        
    btn_frame = tk.Frame(editor)
    btn_frame.pack(fill="x", pady=10)
    
    tk.Button(btn_frame, text="Přidat", command=add_rule, bg="#3498db", fg="white").pack(side="left", padx=10)
    tk.Button(btn_frame, text="Odebrat", command=remove_rule, bg="#e74c3c", fg="white").pack(side="left", padx=10)
    tk.Button(editor, text="ULOŽIT ZMĚNY", command=save_and_close, bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x", padx=10, pady=10)

def show_checklist_popup():
    rules = load_checklist_rules()
    if not rules: return "N/A"
    
    popup = tk.Toplevel(root)
    popup.title("Kontrola pravidel")
    popup.geometry("350x500")
    popup.transient(root)
    popup.grab_set()
    
    tk.Label(popup, text="SPLŇUJE OBCHOD PRAVIDLA?", font=("Arial", 12, "bold"), fg="#e67e22").pack(pady=15)
    
    vars = []
    for rule in rules:
        var = tk.IntVar()
        cb = tk.Checkbutton(popup, text=rule, variable=var, font=("Arial", 10))
        cb.pack(anchor="w", padx=20, pady=2)
        vars.append(var)
        
    result_container = {"value": None}
    
    def confirm():
        checked_count = sum([v.get() for v in vars])
        total_count = len(rules)
        res_str = f"{checked_count}/{total_count}"
        
        if checked_count < total_count:
            ans = messagebox.askyesno("Porušení pravidel", f"Pozor! Splněno pouze {checked_count} z {total_count} pravidel.\nChceš obchod přesto uložit?", parent=popup)
            if not ans: return
            
        result_container["value"] = res_str
        popup.destroy()

    tk.Button(popup, text="POTVRDIT", command=confirm, bg="#2ecc71", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", padx=20, pady=20)
    
    root.wait_window(popup)
    return result_container["value"]

def backup_project():
    if current_project_name and DATA_FILE:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{current_project_name}_backup_{timestamp}.zip"
            backup_path = os.path.join(DIR_BACKUPS, backup_name)
            project_dir = os.path.dirname(DATA_FILE)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root_dir, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root_dir, file)
                        arcname = os.path.relpath(file_path, project_dir)
                        zipf.write(file_path, arcname)
            
            if os.path.exists(JOURNAL_FILE):
                 with zipfile.ZipFile(backup_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
                     zipf.write(JOURNAL_FILE, "journal_entries.json")
                     
            print(f"Záloha vytvořena: {backup_name}")
        except Exception as e:
            print(f"Chyba zálohování: {e}")

# ==============================================================================
# 3. JOURNAL & UTILS
# ==============================================================================

def load_journal_data():
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_journal_data(data):
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_current_journal_entry():
    if not selected_journal_date: return
    text = journal_text.get("1.0", tk.END).strip()
    data = load_journal_data()
    date_str = selected_journal_date.strftime("%Y-%m-%d")
    is_new_entry = (text and date_str not in data)
    if text: data[date_str] = text
    else:
        if date_str in data: del data[date_str]
    save_journal_data(data)
    messagebox.showinfo("Uloženo", "Zápis byl uložen.")
    render_calendar()
    # XP za nový zápis do deníku (jen pokud to je nový záznam — ne přepisování)
    if is_new_entry:
        try:
            award_xp('xp_journal_entry', note=date_str)
            _show_xp_toast(root, f"⭐ +{get_xp_config().get('xp_journal_entry', 8)} XP  ·  Zápis do deníku")
        except Exception:
            pass

def open_trade_from_journal(trade_index):
    show_main_screen(current_project_name)
    def select_row():
        try:
            reset_filter() 
            children = trades_tree.get_children()
            if trade_index < len(children):
                item_id = children[trade_index]
                trades_tree.selection_set(item_id)
                trades_tree.focus(item_id)
                trades_tree.see(item_id)
                show_trade_details(None)
        except Exception as e: print(f"Chyba: {e}")
    root.after(100, select_row)

def on_day_click(day, month, year):
    global selected_journal_date
    selected_journal_date = datetime(year, month, day)
    journal_lbl_date.config(text=f"ZÁPIS: {selected_journal_date.strftime('%d. %m. %Y')}")
    data = load_journal_data()
    date_str = selected_journal_date.strftime("%Y-%m-%d")
    journal_text.delete("1.0", tk.END)
    if date_str in data: journal_text.insert("1.0", data[date_str])

    for w in journal_trades_frame.winfo_children(): w.destroy()
    
    # ZMĚNA: Načítat obchody pouze pokud jsme v REAL režimu
    if current_project_name and DATA_FILE and os.path.exists(DATA_FILE) and current_mode == "REAL":
        all_trades = load_data()
        found_any = False
        tk.Label(journal_trades_frame, text=f"OBCHODY V PROJEKTU: {current_project_name}", font=("Arial", 8, "bold"), fg="gray", bg="white").pack(anchor="w")
        for i, t in enumerate(all_trades):
            t_date = t.get('cas_otevreni', '')
            if t_date.startswith(date_str):
                found_any = True
                res = t.get('vysledek', '??')
                col = "#27ae60" if res.lower() == "win" else "#c0392b" if res.lower() == "loss" else "black"
                chk = t.get('checklist_ratio', '')
                chk_str = f" [Pravidla: {chk}]" if chk else ""
                txt = f"↗ {t.get('symbol')} | {t.get('smer')} | {res}{chk_str}"
                lbl = tk.Label(journal_trades_frame, text=txt, fg=col, bg="#f0f0f0", padx=5, pady=3, font=("Consolas", 9, "bold"), cursor="hand2")
                lbl.pack(fill="x", pady=1, padx=2)
                lbl.bind("<Button-1>", lambda e, idx=i: open_trade_from_journal(idx))
                lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg="#d5dbdb"))
                lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg="#f0f0f0"))
        if not found_any: tk.Label(journal_trades_frame, text="Žádné obchody v tento den.", fg="gray", bg="white").pack(anchor="w")
    elif current_mode == "BACKTEST":
        tk.Label(journal_trades_frame, text="Backtest data se v deníku nezobrazují.", fg="gray", bg="white", font=("Arial", 9, "italic")).pack(anchor="w", pady=10)
    else: tk.Label(journal_trades_frame, text="Otevřete REAL projekt pro zobrazení obchodů.", fg="gray", bg="white").pack(anchor="w")

def change_month(delta):
    global current_cal_date
    m = current_cal_date.month + delta
    y = current_cal_date.year
    if m < 1: m = 12; y -= 1
    elif m > 12: m = 1; y += 1
    current_cal_date = datetime(y, m, 1)
    render_calendar()

def render_calendar():
    for w in cal_frame.winfo_children(): w.destroy()
    data = load_journal_data()
    header = tk.Frame(cal_frame, bg="#2c3e50"); header.pack(fill="x", pady=5)
    tk.Button(header, text="<", command=lambda: change_month(-1), bg="#34495e", fg="white", width=3).pack(side="left")
    tk.Label(header, text=current_cal_date.strftime("%B %Y").upper(), font=("Arial", 12, "bold"), bg="#2c3e50", fg="white", width=20).pack(side="left")
    tk.Button(header, text=">", command=lambda: change_month(1), bg="#34495e", fg="white", width=3).pack(side="left")
    days_header = tk.Frame(cal_frame); days_header.pack()
    for d in ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]: tk.Label(days_header, text=d, width=4, font=("Arial", 9, "bold")).pack(side="left")
    grid_frame = tk.Frame(cal_frame); grid_frame.pack(pady=5)
    trade_dates = set()
    
    # ZMĚNA: Zvýrazňovat dny s obchody pouze pro REAL
    if DATA_FILE and os.path.exists(DATA_FILE) and current_mode == "REAL":
        tr = load_data()
        for t in tr:
            try: trade_dates.add(t.get('cas_otevreni', '')[:10])
            except: pass
            
    cal = calendar.monthcalendar(current_cal_date.year, current_cal_date.month)
    for r, week in enumerate(cal):
        for c, day in enumerate(week):
            if day == 0: tk.Label(grid_frame, text="", width=4).grid(row=r, column=c, padx=1, pady=1)
            else:
                dt_str = datetime(current_cal_date.year, current_cal_date.month, day).strftime("%Y-%m-%d")
                bg_col = "#ecf0f1"; fg_col = "black"
                has_journal = dt_str in data; has_trade = dt_str in trade_dates
                if has_journal and has_trade: bg_col = "#8e44ad"; fg_col = "white"
                elif has_journal: bg_col = "#2ecc71"; fg_col = "white"
                elif has_trade: bg_col = "#f39c12"; fg_col = "white"
                if selected_journal_date and dt_str == selected_journal_date.strftime("%Y-%m-%d"): bg_col = "#3498db"; fg_col = "white"
                tk.Button(grid_frame, text=str(day), width=4, bg=bg_col, fg=fg_col, command=lambda d=day: on_day_click(d, current_cal_date.month, current_cal_date.year)).grid(row=r, column=c, padx=1, pady=1)

def show_journal_screen_target_date(target_date=None):
    show_journal_screen()
    if target_date:
        global current_cal_date
        current_cal_date = datetime(target_date.year, target_date.month, 1)
        render_calendar()
        on_day_click(target_date.day, target_date.month, target_date.year)

def show_journal_screen():
    global cal_frame, journal_text, journal_lbl_date, selected_journal_date, journal_trades_frame
    for w in root.winfo_children(): w.destroy()
    h = tk.Frame(root, bg='#8e44ad', height=40); h.pack(fill='x')
    tk.Label(h, text="TRADING DENÍK | MYŠLENKY & EMOCE", fg='white', bg='#8e44ad', font=('Arial', 10, 'bold')).pack(side='left', padx=20)
    if current_project_name: tk.Button(h, text=f"ZPĚT DO PROJEKTU: {current_project_name}", command=lambda: show_main_screen(current_project_name), bg='#2980b9', fg='white').pack(side='right', padx=20, pady=5)
    else: tk.Button(h, text="ZPĚT NA MENU", command=show_intro_screen, bg='#c0392b', fg='white').pack(side='right', padx=20, pady=5)
    main = tk.Frame(root, padx=20, pady=20); main.pack(fill="both", expand=True)
    left_panel = tk.Frame(main, width=400); left_panel.pack(side="left", fill="y", padx=(0, 20))
    tk.Label(left_panel, text="KALENDÁŘ", font=("Arial", 14, "bold"), fg="#2c3e50").pack(pady=(0, 10))
    cal_frame = tk.Frame(left_panel); cal_frame.pack()
    right_panel = tk.Frame(main); right_panel.pack(side="right", fill="both", expand=True)
    journal_lbl_date = tk.Label(right_panel, text="VYBER DEN V KALENDÁŘI", font=("Arial", 16, "bold"), fg="#2c3e50"); journal_lbl_date.pack(anchor="w", pady=(0, 10))
    toolbar = tk.Frame(right_panel); toolbar.pack(fill="x", pady=5)
    tk.Button(toolbar, text="💾 ULOŽIT ZÁPIS", command=save_current_journal_entry, bg="#27ae60", fg="white", font=("Arial", 10, "bold"), height=2).pack(side="left")
    journal_text = tk.Text(right_panel, font=("Consolas", 11), bg="#fdfefe", wrap="word", padx=10, pady=10, height=15); journal_text.pack(fill="x", expand=False)
    tk.Label(right_panel, text="OBCHODY V TENTO DEN (Klikni pro detail):", font=("Arial", 11, "bold"), fg="#2c3e50").pack(anchor="w", pady=(20, 5))
    journal_trades_frame = tk.Frame(right_panel, bg="white", relief="sunken", borderwidth=1); journal_trades_frame.pack(fill="both", expand=True)
    render_calendar(); now = datetime.now(); on_day_click(now.day, now.month, now.year)

# ==============================================================================
# 4. MONTE CARLO SIMULATION
# ==============================================================================

def copy_mc_results():
    if mc_stats_text_widget:
        text = mc_stats_text_widget.get("1.0", tk.END)
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("Kopírování", "Výsledek zkopírován do schránky.")

def run_monte_carlo_simulation():
    # 1. Získání dat (R-násobky obchodů)
    trades = load_data()
    r_multiples = []
    
    for t in trades:
        res = t.get('vysledek', '').lower()
        if not res: continue
        
        try:
            rrr = float(str(t.get('rrr', 0)).replace(',', '.'))
        except:
            rrr = 0.0
            
        if res == 'win':
            r_multiples.append(rrr)
        elif res == 'loss':
            r_multiples.append(-1.0)
        elif res == 'be':
            r_multiples.append(0.0)

    if not r_multiples:
        messagebox.showwarning("Nedostatek dat", "Pro simulaci potřebujete alespoň nějaké uzavřené obchody (Win/Loss).")
        return
        
    if len(r_multiples) < 30:
        messagebox.showwarning("Malý vzorek dat", f"Máte pouze {len(r_multiples)} obchodů.\n\nSimulace bude velmi zkreslená (pravděpodobně příliš optimistická).\nPro spolehlivé Monte Carlo je potřeba alespoň 50+ obchodů.")

    # 2. Nastavení simulace
    try:
        start_capital = float(load_prop_config().get("balance", 100000))
        risk_pct = float(mc_risk_var.get())
        sim_count = int(mc_sim_count_var.get())
        trades_per_sim = int(mc_trade_count_var.get())
    except:
        messagebox.showerror("Chyba", "Zkontrolujte zadané parametry (čísla).")
        return

    # 3. Výpočet (Monte Carlo - Resampling with Replacement)
    final_equities = []
    max_drawdowns = []
    
    # Pro graf - uložíme prvních 50 křivek
    curves_to_plot = []
    
    for i in range(sim_count):
        current_equity = start_capital
        equity_curve = [start_capital]
        peak = start_capital
        max_dd = 0.0
        
        sim_trades = random.choices(r_multiples, k=trades_per_sim)
        
        for r in sim_trades:
            risk_amount = start_capital * (risk_pct / 100.0) 
            
            pnl = risk_amount * r
            current_equity += pnl
            equity_curve.append(current_equity)
            
            # DD calculation
            if current_equity > peak:
                peak = current_equity
            dd = (peak - current_equity) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
        
        final_equities.append(current_equity)
        max_drawdowns.append(max_dd)
        
        if i < 50: 
            curves_to_plot.append(equity_curve)

    # 4. Statistiky
    avg_final = sum(final_equities) / len(final_equities)
    median_final = sorted(final_equities)[len(final_equities)//2]
    worst_case_dd = sorted(max_drawdowns)[int(len(max_drawdowns)*0.95)] # 95. percentil
    prob_ruin = sum(1 for x in final_equities if x < start_capital) / sim_count * 100 # Risk of Loss
    prob_real_ruin = sum(1 for x in final_equities if x <= 0) / sim_count * 100 # Risk of blowing account
    
    profit_probability = sum(1 for x in final_equities if x > start_capital) / sim_count * 100

    # 5. Vykreslení
    for w in mc_canvas_frame.winfo_children(): w.destroy()
    
    fig = plt.Figure(figsize=(8, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    for curve in curves_to_plot:
        ax.plot(curve, color='#2ecc71', alpha=0.15, linewidth=1)
        
    ax.axhline(start_capital, color='#64748b', linestyle='--', alpha=0.6)
    ax.set_title(f"Monte Carlo: {sim_count} simulací (Bootstrapping)", color=DT_TEXT)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')
    ax.tick_params(colors=DT_TEXT)
    ax.grid(True, alpha=0.4, color='#e2e8f0')
    for spine in ax.spines.values(): spine.set_color('#cbd5e1')
    
    canvas = FigureCanvasTkAgg(fig, master=mc_canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    
    # 6. Update Text Widget
    res_text = f"--- VÝSLEDKY SIMULACE ({trades_per_sim} budoucích obchodů) ---\n"
    res_text += f"Pravděpodobnost zisku: {profit_probability:.1f} %\n"
    res_text += f"Mediánový výsledek: {median_final:,.0f} (Zisk: {median_final-start_capital:,.0f})\n"
    res_text += f"Riziko ztráty kapitálu: {prob_ruin:.1f} %\n"
    res_text += f"Riziko bankrotu (<=0): {prob_real_ruin:.1f} %\n"
    res_text += f"Očekávaný Max Drawdown (95% jistota): {worst_case_dd:.2f} %\n"
    
    mc_stats_text_widget.config(state='normal')
    mc_stats_text_widget.delete("1.0", tk.END)
    mc_stats_text_widget.insert(tk.END, res_text)
    mc_stats_text_widget.config(state='disabled')


def setup_monte_carlo_ui(parent):
    global mc_canvas_frame, mc_stats_text_widget, mc_sim_count_var, mc_trade_count_var, mc_risk_var
    
    main = tk.Frame(parent, bg="#ecf0f1")
    main.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Controls
    ctrl_frame = tk.Frame(main, bg="#bdc3c7", pady=10, padx=10, relief="raised")
    ctrl_frame.pack(fill="x")
    
    tk.Label(ctrl_frame, text="Počet simulací:", bg="#bdc3c7").pack(side="left")
    mc_sim_count_var = tk.StringVar(value="1000")
    tk.Entry(ctrl_frame, textvariable=mc_sim_count_var, width=8).pack(side="left", padx=5)
    
    tk.Label(ctrl_frame, text="Obchodů na simulaci:", bg="#bdc3c7").pack(side="left", padx=(10,0))
    mc_trade_count_var = tk.StringVar(value="100")
    tk.Entry(ctrl_frame, textvariable=mc_trade_count_var, width=5).pack(side="left", padx=5)
    
    tk.Label(ctrl_frame, text="Risk na obchod (%):", bg="#bdc3c7").pack(side="left", padx=(10,0))
    mc_risk_var = tk.StringVar(value="1.0")
    tk.Entry(ctrl_frame, textvariable=mc_risk_var, width=5).pack(side="left", padx=5)
    
    tk.Button(ctrl_frame, text="▶ SPUSTIT SIMULACI", command=run_monte_carlo_simulation, bg="#8e44ad", fg="white", font=("Arial", 10, "bold")).pack(side="right", padx=10)
    
    # Layout
    content = tk.Frame(main)
    content.pack(fill="both", expand=True, pady=10)
    
    # Graph Area
    mc_canvas_frame = tk.Frame(content, bg=DT_SURFACE, relief="sunken", bd=1)
    mc_canvas_frame.pack(side="left", fill="both", expand=True)
    
    # Stats Area
    stats_panel = tk.Frame(content, bg="white", width=300, relief="sunken", bd=2)
    stats_panel.pack(side="right", fill="y", padx=(10,0))
    stats_panel.pack_propagate(False)
    
    tk.Label(stats_panel, text="STATISTIKA", font=("Arial", 12, "bold"), bg="white", fg="#2c3e50").pack(pady=10)
    
    # Použití Text widgetu místo Label pro možnost kopírování
    mc_stats_text_widget = tk.Text(stats_panel, font=("Consolas", 10), bg="white", height=10, padx=5, pady=5, relief="flat")
    mc_stats_text_widget.insert(tk.END, "Spusťte simulaci...")
    mc_stats_text_widget.config(state='disabled') # Read-only
    mc_stats_text_widget.pack(fill="x", padx=10)
    
    # Tlačítko pro kopírování
    tk.Button(stats_panel, text="[KOPÍROVAT VÝSLEDEK]", command=copy_mc_results, bg="#bdc3c7", font=("Arial", 8)).pack(pady=5)

    # Tip
    tk.Label(stats_panel, text="\nTip:\nPokud máte 100% pravděpodobnost zisku, znamená to, že vaše historická data jsou velmi silná (nebo je jich málo).", font=("Arial", 9, "italic"), fg="gray", bg="white", justify="center", wraplength=280).pack(side="bottom", pady=20)


# ==============================================================================
# 5. MAIN UI & HELPERS
# ==============================================================================

class ImageZoomViewer(tk.Toplevel):
    def __init__(self, parent, gallery_items, start_index):
        super().__init__(parent); self.gallery_items = gallery_items; self.current_index = start_index; self.title("Detail Snímku")
        try: self.state('zoomed')
        except: self.geometry("1000x800")
        self.configure(bg="#1a1a1a")
        ctrl = tk.Frame(self, bg="#2c3e50", pady=10); ctrl.pack(side="top", fill="x")
        tk.Button(ctrl, text="◀ Předchozí", command=self.prev_img, bg="#34495e", fg="white", font=('Arial', 10, 'bold')).pack(side="left", padx=20)
        self.lbl = tk.Label(ctrl, text="", bg="#2c3e50", fg="#ecf0f1", font=('Arial', 14, 'bold')); self.lbl.pack(side="left", expand=True)
        tk.Button(ctrl, text="Další ▶", command=self.next_img, bg="#34495e", fg="white", font=('Arial', 10, 'bold')).pack(side="right", padx=20)
        self.canvas = tk.Canvas(self, bg="#1a1a1a", highlightthickness=0); self.canvas.pack(fill="both", expand=True)
        self.load_image()
    def load_image(self):
        if not self.gallery_items: return
        item = self.gallery_items[self.current_index]; path = item['path']; info_text = item.get('info', os.path.basename(path))
        self.lbl.config(text=f"{info_text}   [{self.current_index + 1} z {len(self.gallery_items)}]")
        self.img_orig = Image.open(path); self.show_image()
    def show_image(self):
        self.canvas.update(); cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10 or ch < 10: return
        w, h = self.img_orig.size; ratio = min(cw/w, ch/h); new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
        img_res = self.img_orig.resize(new_size, Image.Resampling.LANCZOS); self.photo = ImageTk.PhotoImage(img_res)
        self.canvas.delete("all"); self.canvas.create_image(cw//2, ch//2, image=self.photo)
    def prev_img(self): 
        if not self.gallery_items: return
        self.current_index = (self.current_index - 1) % len(self.gallery_items); self.load_image()
    def next_img(self): 
        if not self.gallery_items: return
        self.current_index = (self.current_index + 1) % len(self.gallery_items); self.load_image()

class ColumnConfigurator(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent); self.callback = callback; self.title("Správa sloupců tabulky"); self.geometry("500x400"); self.configure(bg="#f0f0f0")
        cfg = load_scoring_config(); current_cols = cfg.get("columns", DEFAULT_SCORING["columns"]); all_keys = list(COL_TRANSLATION.keys()); available_cols = [k for k in all_keys if k not in current_cols]
        main_f = tk.Frame(self, padx=10, pady=10); main_f.pack(fill="both", expand=True)
        lf = tk.LabelFrame(main_f, text="Dostupné sloupce"); lf.pack(side="left", fill="both", expand=True, padx=5)
        self.lb_avail = tk.Listbox(lf, selectmode=tk.SINGLE); self.lb_avail.pack(fill="both", expand=True)
        for k in available_cols: self.lb_avail.insert(tk.END, COL_TRANSLATION[k])
        cf = tk.Frame(main_f); cf.pack(side="left", padx=5)
        tk.Button(cf, text="Přidat ->", command=self.add_col).pack(fill="x", pady=5)
        tk.Button(cf, text="<- Odebrat", command=self.rem_col).pack(fill="x", pady=5)
        tk.Frame(cf, height=20).pack()
        tk.Button(cf, text="Nahoru", command=self.move_up).pack(fill="x", pady=5)
        tk.Button(cf, text="Dolů", command=self.move_down).pack(fill="x", pady=5)
        rf = tk.LabelFrame(main_f, text="Zobrazené sloupce"); rf.pack(side="left", fill="both", expand=True, padx=5)
        self.lb_sel = tk.Listbox(rf, selectmode=tk.SINGLE); self.lb_sel.pack(fill="both", expand=True)
        for k in current_cols: self.lb_sel.insert(tk.END, COL_TRANSLATION.get(k, k))
        tk.Button(self, text="ULOŽIT NASTAVENÍ", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), command=self.save).pack(pady=10)
        self.rev_map = {v: k for k, v in COL_TRANSLATION.items()}
    def add_col(self):
        sel = self.lb_avail.curselection()
        if not sel: return
        txt = self.lb_avail.get(sel[0]); self.lb_sel.insert(tk.END, txt); self.lb_avail.delete(sel[0])
    def rem_col(self):
        sel = self.lb_sel.curselection()
        if not sel: return
        txt = self.lb_sel.get(sel[0]); self.lb_avail.insert(tk.END, txt); self.lb_sel.delete(sel[0])
    def move_up(self):
        sel = self.lb_sel.curselection(); 
        if not sel or sel[0] == 0: return
        idx = sel[0]; txt = self.lb_sel.get(idx); self.lb_sel.delete(idx); self.lb_sel.insert(idx-1, txt); self.lb_sel.selection_set(idx-1)
    def move_down(self):
        sel = self.lb_sel.curselection()
        if not sel or sel[0] == self.lb_sel.size()-1: return
        idx = sel[0]; txt = self.lb_sel.get(idx); self.lb_sel.delete(idx); self.lb_sel.insert(idx+1, txt); self.lb_sel.selection_set(idx+1)
    def save(self):
        new_cols = []
        for i in range(self.lb_sel.size()): txt = self.lb_sel.get(i); key = self.rev_map.get(txt, txt.lower()); new_cols.append(key)
        cfg = load_scoring_config(); cfg["columns"] = new_cols; save_scoring_config(cfg); self.callback(); self.destroy()

def load_data():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f: 
        data = []; reader = csv.DictReader(f)
        for row in reader: lower_row = {k.lower(): v for k, v in row.items() if k is not None}; data.append(lower_row)
        return data

def load_prop_config():
    if PROP_CONFIG_FILE and os.path.exists(PROP_CONFIG_FILE):
        try:
            with open(PROP_CONFIG_FILE, 'r') as f: return json.load(f)
        except: pass
    return {"balance": 100000, "currency": "USD", "risk_per_trade_percent": 1.0}

def save_prop_config(cfg):
    if PROP_CONFIG_FILE:
        with open(PROP_CONFIG_FILE, 'w') as f: json.dump(cfg, f)

def open_prop_settings():
    cfg = load_prop_config()
    res = simpledialog.askfloat("Nastavení účtu", f"Zadejte počáteční kapitál ({cfg.get('currency','USD')}):", initialvalue=cfg.get("balance", 100000))
    if res is not None:
        cfg["balance"] = res
        save_prop_config(cfg)
        update_statistics()

def prepocitat_historii():
    if not os.path.exists(DATA_FILE): return
    trades = load_data(); cfg = load_scoring_config(); updated_count = 0
    for t in trades:
        if not t.get('delka_obchodu') and t.get('cas_otevreni') and t.get('cas_zavreni'):
            try:
                dt_start = datetime.strptime(t.get('cas_otevreni'), "%Y-%m-%d %H:%M")
                dt_end = datetime.strptime(t.get('cas_zavreni'), "%Y-%m-%d %H:%M")
                diff = dt_end - dt_start; total_seconds = int(diff.total_seconds()); hours, remainder = divmod(total_seconds, 3600); minutes, _ = divmod(remainder, 60); t['delka_obchodu'] = f"{hours}h {minutes}m"
            except: pass
        total = 0; total += cfg["setups"].get(t.get('fibo', ''), 0); total += cfg["sessions"].get(t.get('session', ''), 0); total += cfg["days"].get(t.get('den_tydne', ''), 0)
        try:
            r = float(str(t.get('rrr', 0)).replace(',', '.')); rrr_pts = cfg["rrr"]
            if r >= 5.0: total += rrr_pts.get("1:5+", 0)
            elif r >= 4.0: total += rrr_pts.get("1:4", 0)
            elif r >= 3.0: total += rrr_pts.get("1:3", 0)
            elif r >= 2.0: total += rrr_pts.get("1:2", 0)
            else: total += rrr_pts.get("1:1", 0)
        except: pass
        try:
            p = float(str(t.get('pips', 0)).replace(',', '.')); pips_pts = cfg["pips"]
            if p >= 20: total += pips_pts.get("20+", 0)
            elif 15 <= p < 20: total += pips_pts.get("15-20", 0)
            elif 10 <= p < 15: total += pips_pts.get("10-15", 0)
            elif 5 <= p < 10: total += pips_pts.get("5-10", 0)
        except: pass
        thr = cfg["thresholds"]; res = "C"
        if total >= thr["A+"]: res = "A+"
        elif total >= thr["A"]: res = "A"
        elif total >= thr["B"]: res = "B"
        t['kvalita'] = res; updated_count += 1
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        if trades: w = csv.DictWriter(f, fieldnames=list(trades[0].keys())); w.writeheader(); w.writerows(trades)
    update_listbox(); update_statistics(); messagebox.showinfo("Hotovo", f"Aktualizováno {updated_count} obchodů.")

def export_trade_to_pdf():
    try: from reportlab.lib.pagesizes import A4
    except ImportError: messagebox.showerror("Chyba", "Chybí knihovna 'reportlab'."); return
    if trades_tree is None: return
    sel = trades_tree.selection()
    if not sel: messagebox.showwarning("Upozornění", "Vyber obchod pro export."); return
    idx = int(sel[0]); trades = load_data()
    if idx >= len(trades): return
    t = trades[idx]
    filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")], title="Uložit Playbook PDF", initialfile=f"Trade_{t.get('symbol','unk')}_{t.get('cas_otevreni','').split(' ')[0]}.pdf")
    if not filename: return
    try:
        try: pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf')); font_name = 'Arial'
        except: font_name = 'Helvetica'
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40); story = []; styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TradeTitle', parent=styles['Heading1'], fontName=font_name, fontSize=18, spaceAfter=20, textColor=colors.HexColor("#2c3e50"))
        normal_style = ParagraphStyle('TradeNormal', parent=styles['Normal'], fontName=font_name, fontSize=10)
        label_style = ParagraphStyle('TradeLabel', parent=styles['Normal'], fontName=font_name, fontSize=10, textColor=colors.gray)
        header_text = f"{t.get('symbol')} | {t.get('smer')} | {t.get('vysledek')}"; story.append(Paragraph(header_text, title_style)); story.append(Spacer(1, 10))
        data_grid = [["Čas otevření:", t.get('cas_otevreni'), "Výsledek:", t.get('vysledek')], ["Symbol:", t.get('symbol'), "RRR:", t.get('rrr')], ["Směr:", t.get('smer'), "Setup:", t.get('fibo')], ["Vstup:", t.get('vstupni_hodnota'), "Seance:", t.get('session')], ["Stop Loss:", t.get('stoploss'), "Kvalita:", t.get('kvalita')], ["Take Profit:", t.get('takeprofit'), "Délka:", t.get('delka_obchodu')], ["Pravidla:", t.get('checklist_ratio', 'N/A'), "News Impact:", t.get('news', 'Ne')], ["Fundament:", t.get('news_event', '-'), "Štítky:", t.get('tags', '-')]]
        table = Table(data_grid, colWidths=[80, 140, 80, 140]); table.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), font_name), ('FONTSIZE', (0,0), (-1,-1), 10), ('TEXTCOLOR', (0,0), (0,-1), colors.gray), ('TEXTCOLOR', (2,0), (2,-1), colors.gray), ('TEXTCOLOR', (1,0), (1,-1), colors.black), ('TEXTCOLOR', (3,0), (3,-1), colors.black), ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke), ('PADDING', (0,0), (-1,-1), 8)])); story.append(table); story.append(Spacer(1, 20))
        if t.get('duvod'): story.append(Paragraph("<b>Důvod vstupu:</b>", normal_style)); story.append(Paragraph(t.get('duvod'), normal_style)); story.append(Spacer(1, 10))
        if t.get('poznamka'): story.append(Paragraph("<b>Poznámka:</b>", normal_style)); story.append(Paragraph(t.get('poznamka'), normal_style)); story.append(Spacer(1, 20))
        img_names = [n for n in t.get('obrazky','').split(';') if n]
        for name in img_names:
            full_path = os.path.join(IMAGES_DIR, name)
            if os.path.exists(full_path):
                try:
                    pil_img = Image.open(full_path); w, h = pil_img.size; aspect = h / w; display_w = 480; display_h = display_w * aspect
                    if display_h > 600: display_h = 600; display_w = display_h / aspect
                    img_obj = PDFImage(full_path, width=display_w, height=display_h); story.append(img_obj); story.append(Spacer(1, 10)); story.append(Paragraph(f"<i>{name}</i>", label_style)); story.append(Spacer(1, 20))
                except: pass
        doc.build(story); messagebox.showinfo("Export hotov", f"PDF uloženo do:\n{filename}")
    except Exception as e: messagebox.showerror("Chyba exportu", f"Nepodařilo se vytvořit PDF.\nChyba: {e}")

# NOVÉ: Funkce pro A/B Simulaci
def run_ab_simulation():
    trades = load_data()
    if not trades:
        messagebox.showwarning("Chyba", "Nejsou k dispozici žádná data.")
        return

    # Dotaz na Fixed R
    fixed_r = simpledialog.askfloat("A/B Simulace", "Zadejte fixní RRR (Target) pro simulaci:\n\n(Např. '2.0' znamená, že každý ziskový obchod bude mít zisk 2R, bez ohledu na realitu.)", initialvalue=2.0)
    
    if fixed_r is None: return

    equity_orig = [0.0]
    equity_sim = [0.0]
    
    current_orig = 0.0
    current_sim = 0.0
    
    for t in trades:
        res = t.get('vysledek', '').lower()
        if not res: continue
        
        try: real_rrr = float(str(t.get('rrr', 0)).replace(',', '.'))
        except: real_rrr = 0.0
        
        # Originál
        val_orig = 0.0
        if res == 'win': val_orig = real_rrr
        elif res == 'loss': val_orig = -1.0
        
        # Simulace
        # Předpokládáme, že LOSS zůstává LOSS (protože nevíme, kam trh šel)
        # WIN se stává Fixed R
        val_sim = 0.0
        if res == 'win': val_sim = fixed_r
        elif res == 'loss': val_sim = -1.0
        
        current_orig += val_orig
        current_sim += val_sim
        
        equity_orig.append(current_orig)
        equity_sim.append(current_sim)
        
    # Vykreslení Popup Grafu
    popup = tk.Toplevel(root)
    popup.title(f"A/B TEST: Realita vs. Fixní {fixed_r}R")
    popup.geometry("800x500")
    
    fig = plt.Figure(figsize=(8, 5), dpi=100)
    ax = fig.add_subplot(111)
    
    ax.plot(equity_orig, label="REALITA (Vaše strategie)", color='#2ecc71', linewidth=2)
    ax.plot(equity_sim, label=f"SIMULACE (Fixní {fixed_r}R)", color='#3498db', linestyle='--', linewidth=2)
    
    ax.legend()
    ax.set_title("Porovnání výkonnosti")
    ax.grid(True, alpha=0.3)
    
    canvas = FigureCanvasTkAgg(fig, master=popup)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)

def update_statistics():
    global best_performers_frame, stats_symbol_combo, prop_equity_label, prop_balance_label, bar_chart_canvases, kpi_frame, tables_frame
    if not stats_graph_frame: return
    trades = load_data()
    prop_cfg = load_prop_config()
    start_balance = prop_cfg.get("balance", 100000)
    risk_pct = prop_cfg.get("risk_per_trade_percent", 1.0) 
    all_symbols = sorted(list(set(t.get('symbol', '') for t in trades if t.get('symbol'))))
    
    if stats_symbol_combo:
        current_selection = stats_symbol_var.get()
        stats_symbol_combo['values'] = ["VŠE"] + all_symbols
        if current_selection != "VŠE" and current_selection not in all_symbols: stats_symbol_combo.set("VŠE")
        
    selected_symbol_filter = stats_symbol_var.get() if stats_symbol_var else "VŠE"
    
    for c in stats_canvases: c.get_tk_widget().destroy()
    stats_canvases.clear()
    for c in pie_canvases: c.get_tk_widget().destroy()
    pie_canvases.clear()
    for c in heatmap_canvases: c.get_tk_widget().destroy()
    heatmap_canvases.clear()
    for c in bar_chart_canvases: c.get_tk_widget().destroy()
    bar_chart_canvases.clear()
    if kpi_frame:
        for w in kpi_frame.winfo_children(): w.destroy()
    if tables_frame:
        for w in tables_frame.winfo_children(): w.destroy()
    if best_performers_frame:
        for w in best_performers_frame.winfo_children(): w.destroy()

    if not trades:
        if tables_frame:
            tk.Label(tables_frame, text="Žádná data k zobrazení.",
                     bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 11)).pack(pady=40)
        return
    
    # --- STATISTICS VARIABLES ---
    stats = {
        'total': 0, 'wins': 0, 'profit_r': 0.0, 'gross_profit': 0.0, 'gross_loss': 0.0,
        'total_rrr_potential': 0.0, 
        'days': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0, 'rrr_sum': 0.0}),
        'sessions': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0, 'rrr_sum': 0.0}),
        'setups': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0, 'rrr_sum': 0.0}),
        'directions': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0}),
        'tags': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0, 'rrr_sum': 0.0}),
        'timeframes': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0}),
        'monthly': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0}),
        'combinations': defaultdict(lambda: {'wins': 0, 'count': 0, 'r': 0.0}),
        'rolling': [],
        'duration': {'all': [], 'win': [], 'loss': []}
    }
    
    heatmap_data = [[0.0 for _ in range(5)] for _ in range(24)]
    days_map = {"Pondělí":0, "Úterý":1, "Středa":2, "Čtvrtek":3, "Pátek":4}
    
    cnt_win = 0
    cnt_loss = 0
    cnt_be = 0
    
    current_money_equity = start_balance; equity_curve = [start_balance]
    
    for t in trades:
        # 1. FILTR SYMBOLU
        if selected_symbol_filter != "VŠE" and t.get('symbol') != selected_symbol_filter: continue
        
        # 2. FILTR VÍKENDŮ
        raw_day = t.get('den_tydne', 'Neznámý').capitalize()
        if raw_day in ["Sobota", "Neděle"]: continue
        
        res = t.get('vysledek', '').lower()
        if not res: continue

        # Hodnoty
        try: rrr_val = float(str(t.get('rrr', 0)).replace(',', '.'))
        except: rrr_val = 0.0
        
        session = t.get('session', 'Neznámý')
        setup = t.get('fibo', 'Neznámý').upper() 
        
        if "GOLDEN" in setup: setup = "GOLDEN"
        elif "DISCOUNT" in setup: setup = "DISCOUNT"
        elif "PREMIUM" in setup: setup = "PREMIUM"
        elif "ORDER" in setup: setup = "ORDER BLOCK"
        
        direction = t.get('smer', 'Neznámý')
        tags_str = t.get('tags', '') # NOVÉ
        tf_vstup = t.get('timeframe_vstup', 'N/A')
        if not tf_vstup: tf_vstup = "N/A"
        
        # Čas a Heatmap Logic
        dur_mins = 0
        raw_dur = t.get('delka_obchodu', '')
        open_time_str = t.get('cas_otevreni', '')
        
        if open_time_str:
            try:
                dt_open = datetime.strptime(open_time_str, "%Y-%m-%d %H:%M")
                h_idx = dt_open.hour
                day_name = t.get('den_tydne', '').capitalize()
                d_idx = days_map.get(day_name, -1)
            except:
                d_idx = -1; h_idx = -1
        else:
            d_idx = -1; h_idx = -1
            
        if raw_dur:
            try:
                parts = raw_dur.split(' ')
                h = int(parts[0].replace('h', ''))
                m = int(parts[1].replace('m', ''))
                dur_mins = h * 60 + m
            except: pass

        # === CORE LOGIC ===
        stats['total'] += 1
        stats['total_rrr_potential'] += rrr_val
        realized_r = 0.0
        
        is_win = False
        if res == 'win':
            is_win = True
            realized_r = rrr_val
            stats['wins'] += 1
            stats['gross_profit'] += rrr_val
            stats['duration']['win'].append(dur_mins)
            cnt_win += 1
            if current_mode == "REAL":
                risk_amount = start_balance * (risk_pct / 100.0)
                current_money_equity += (risk_amount * rrr_val)
        elif res == 'loss':
            realized_r = -1.0
            stats['gross_loss'] += 1.0
            stats['duration']['loss'].append(dur_mins)
            cnt_loss += 1
            if current_mode == "REAL":
                risk_amount = start_balance * (risk_pct / 100.0)
                current_money_equity -= risk_amount
        else: # BE
            cnt_be += 1

        stats['profit_r'] += realized_r
        stats['duration']['all'].append(dur_mins)

        if current_mode == "REAL": equity_curve.append(current_money_equity)
        else: equity_curve.append(equity_curve[-1] + realized_r)
            
        if d_idx != -1 and h_idx != -1: heatmap_data[h_idx][d_idx] += realized_r

        # Agregace
        stats['days'][raw_day]['count'] += 1
        stats['days'][raw_day]['r'] += realized_r
        stats['days'][raw_day]['rrr_sum'] += rrr_val
        if is_win: stats['days'][raw_day]['wins'] += 1
        
        stats['sessions'][session]['count'] += 1
        stats['sessions'][session]['r'] += realized_r
        stats['sessions'][session]['rrr_sum'] += rrr_val
        if is_win: stats['sessions'][session]['wins'] += 1
        
        stats['setups'][setup]['count'] += 1
        stats['setups'][setup]['r'] += realized_r
        stats['setups'][setup]['rrr_sum'] += rrr_val
        if is_win: stats['setups'][setup]['wins'] += 1
        
        stats['directions'][direction]['count'] += 1
        stats['directions'][direction]['r'] += realized_r
        if is_win: stats['directions'][direction]['wins'] += 1
        
        stats['timeframes'][tf_vstup]['count'] += 1
        stats['timeframes'][tf_vstup]['r'] += realized_r
        if is_win: stats['timeframes'][tf_vstup]['wins'] += 1
        month_key = open_time_str[:7] if open_time_str else 'N/A'
        stats['monthly'][month_key]['count'] += 1
        stats['monthly'][month_key]['r'] += realized_r
        if is_win: stats['monthly'][month_key]['wins'] += 1
        combo_key = f"{session} | {t.get('symbol','?')} | {setup}"
        stats['combinations'][combo_key]['count'] += 1
        stats['combinations'][combo_key]['r'] += realized_r
        if is_win: stats['combinations'][combo_key]['wins'] += 1
        stats['rolling'].append((res, realized_r))
        
        # NOVÉ: Zpracování TAGŮ
        if tags_str:
            # Rozdělení podle mezer nebo čárek
            tag_list = tags_str.replace(',', ' ').split()
            for tag in tag_list:
                clean_tag = tag.strip()
                if clean_tag:
                    stats['tags'][clean_tag]['count'] += 1
                    stats['tags'][clean_tag]['r'] += realized_r
                    stats['tags'][clean_tag]['rrr_sum'] += rrr_val
                    if is_win: stats['tags'][clean_tag]['wins'] += 1

    # === VÝPOČTY METRIK ===
    winrate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
    avg_target_rrr = (stats['total_rrr_potential'] / stats['total']) if stats['total'] > 0 else 0
    profit_factor = (stats['gross_profit'] / stats['gross_loss']) if stats['gross_loss'] > 0 else stats['gross_profit']

    def avg_time_str(dur_list):
        if not dur_list: return "0h 0m"
        avg_min = sum(dur_list) / len(dur_list)
        h, m = divmod(int(avg_min), 60)
        return f"{h}h {m}m"

    # === STREAK TRACKER ===
    streak_cur = 0; streak_type = None
    best_win_streak = 0; best_loss_streak = 0
    temp_streak = 0; temp_type = None
    for t in trades:
        r = t.get('vysledek', '').lower()
        if r not in ('win', 'loss'): continue
        if r == temp_type: temp_streak += 1
        else: temp_streak = 1; temp_type = r
        if temp_type == 'win' and temp_streak > best_win_streak: best_win_streak = temp_streak
        if temp_type == 'loss' and temp_streak > best_loss_streak: best_loss_streak = temp_streak
    streak_cur = temp_streak; streak_type = temp_type

    # --- KLÍČOVÉ METRIKY ---
    avg_win_r  = stats['gross_profit'] / stats['wins'] if stats['wins'] > 0 else 0
    avg_loss_r = stats['gross_loss'] / max(stats['total'] - stats['wins'] - cnt_be, 1)
    expectancy = (winrate/100 * avg_win_r) - ((1 - winrate/100) * avg_loss_r)
    min_rrr_be = (1 - winrate/100) / (winrate/100) if winrate > 0 else float('inf')

    # --- DRAWDOWN (předpočet pro KPI + graf) ---
    dd_curve = []; peak_eq = equity_curve[0]
    for val in equity_curve:
        if val > peak_eq: peak_eq = val
        dd = ((peak_eq - val) / abs(peak_eq) * 100) if peak_eq != 0 else 0
        dd_curve.append(-dd)
    max_dd_pct = abs(min(dd_curve)) if dd_curve else 0

    # --- PER ÚČET ---
    acct_stats = defaultdict(lambda: {'count':0,'wins':0,'losses':0,'be':0,'r':0.0,'gross_p':0.0,'gross_l':0.0})
    for t in load_data():
        if t.get('den_tydne','').capitalize() in ('Sobota','Neděle'): continue
        res2 = t.get('vysledek','').lower()
        if not res2: continue
        if selected_symbol_filter != "VŠE" and t.get('symbol') != selected_symbol_filter: continue
        ucet2 = t.get('ucet','').strip() or '— (bez účtu) —'
        try: rrr_v = float(str(t.get('rrr',1)).replace(',','.'))
        except: rrr_v = 1.0
        acct_stats[ucet2]['count'] += 1
        if res2 == 'win':
            acct_stats[ucet2]['wins'] += 1; acct_stats[ucet2]['r'] += rrr_v; acct_stats[ucet2]['gross_p'] += rrr_v
        elif res2 == 'loss':
            acct_stats[ucet2]['losses'] += 1; acct_stats[ucet2]['r'] -= 1.0; acct_stats[ucet2]['gross_l'] += 1.0
        else: acct_stats[ucet2]['be'] += 1

    # ═══════════════════════════════════════════════════════════════════════════
    # KPI KARTY
    # ═══════════════════════════════════════════════════════════════════════════
    if kpi_frame:
        _kpi_items = [
            ("OBCHODŮ",       str(stats['total']),              DT_TEXT),
            ("W / L / BE",    f"{stats['wins']} / {cnt_loss} / {cnt_be}", DT_SUBTEXT),
            ("WINRATE",       f"{winrate:.1f}%",                '#4ade80' if winrate >= 50 else '#f87171'),
            ("PROFIT",        f"{stats['profit_r']:+.2f} R",   '#4ade80' if stats['profit_r'] >= 0 else '#f87171'),
            ("PROFIT FACTOR", f"{profit_factor:.2f}",           '#4ade80' if profit_factor >= 1.5 else '#fbbf24' if profit_factor >= 1 else '#f87171'),
            ("EXPECTANCY",    f"{expectancy:+.3f} R",           '#4ade80' if expectancy > 0 else '#f87171'),
            ("MAX DRAWDOWN",  f"{max_dd_pct:.1f}%",            '#f87171' if max_dd_pct > 10 else '#fbbf24' if max_dd_pct > 5 else '#4ade80'),
            ("AVG RRR CÍL",   f"{avg_target_rrr:.2f}",         DT_TEXT),
            ("WIN SÉRIE",     f"{best_win_streak}×",            '#4ade80'),
            ("LOSS SÉRIE",    f"{best_loss_streak}×",           '#f87171'),
        ]
        for label, value, color in _kpi_items:
            c = tk.Frame(kpi_frame, bg=DT_SURFACE, padx=12, pady=8)
            c.pack(side='left', padx=3, pady=2)
            tk.Label(c, text=value, font=('Segoe UI', 13, 'bold'),
                     bg=DT_SURFACE, fg=color).pack()
            tk.Label(c, text=label, font=('Segoe UI', 7),
                     bg=DT_SURFACE, fg=DT_SUBTEXT).pack()

    # ═══════════════════════════════════════════════════════════════════════════
    # TABULKY STATISTIK — styled cards
    # ═══════════════════════════════════════════════════════════════════════════
    days_order = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek"]

    def _wr_fg(wr): return '#4ade80' if wr >= 55 else '#fbbf24' if wr >= 45 else '#f87171'
    def _r_fg(r):   return '#4ade80' if r > 0 else '#f87171' if r < 0 else DT_SUBTEXT

    def _stat_card(parent, title, headers, rows, accent=None):
        """Render a styled statistics card."""
        accent_c = accent or DT_ACCENT
        card = tk.Frame(parent, bg=DT_SURFACE)
        card.pack(fill='x', pady=(0, 6))
        hf = tk.Frame(card, bg=accent_c)
        hf.pack(fill='x')
        tk.Label(hf, text=f"  {title}", font=('Segoe UI', 9, 'bold'),
                 bg=accent_c, fg='white', pady=4, anchor='w').pack(fill='x')
        hrow = tk.Frame(card, bg=DT_PANEL)
        hrow.pack(fill='x')
        for h in headers:
            tk.Label(hrow, text=h, font=('Segoe UI', 7, 'bold'), bg=DT_PANEL,
                     fg=DT_SUBTEXT, padx=8, pady=2, anchor='center').pack(side='left', expand=True, fill='x')
        for ri, row_vals in enumerate(rows):
            rbg = DT_SURFACE if ri % 2 == 0 else DT_BG
            rf  = tk.Frame(card, bg=rbg); rf.pack(fill='x')
            for (val, fg_c) in row_vals:
                tk.Label(rf, text=val, font=('Segoe UI', 9), bg=rbg,
                         fg=fg_c or DT_TEXT, padx=8, pady=3, anchor='center').pack(side='left', expand=True, fill='x')

    if tables_frame:
        # ── 2-sloupcový layout ─────────────────────────────────────────────────
        _col_l = tk.Frame(tables_frame, bg=DT_BG)
        _col_r = tk.Frame(tables_frame, bg=DT_BG)
        _col_l.pack(side='left', fill='both', expand=True, padx=(0, 4))
        _col_r.pack(side='right', fill='both', expand=True, padx=(4, 0))

        # ── LEVÝ SLOUPEC ──────────────────────────────────────────────────────
        # Klíčové metriky
        _stat_card(_col_l, "KLÍČOVÉ METRIKY", ["Metrika", "Hodnota"], [
            [("Expectancy / obchod", DT_SUBTEXT), (f"{expectancy:+.3f} R", _r_fg(expectancy))],
            [("Avg RRR výhry",       DT_SUBTEXT), (f"{avg_win_r:.2f} R", '#4ade80')],
            [("Min RRR pro breakeven",DT_SUBTEXT),(f"{min_rrr_be:.2f} R (WR {winrate:.1f}%)", DT_TEXT)],
            [("Délka obchodu (vše)", DT_SUBTEXT), (avg_time_str(stats['duration']['all']), DT_TEXT)],
            [("Délka obchodu (WIN)", DT_SUBTEXT), (avg_time_str(stats['duration']['win']), '#4ade80')],
            [("Délka obchodu (LOSS)",DT_SUBTEXT), (avg_time_str(stats['duration']['loss']), '#f87171')],
        ], accent='#1e40af')

        # DNY
        _days_rows = []
        for dk in days_order:
            v = stats['days'].get(dk)
            if not v or v['count'] == 0: continue
            wr2 = v['wins']/v['count']*100
            _days_rows.append([
                (dk, DT_TEXT),
                (f"{wr2:.1f}%", _wr_fg(wr2)),
                (f"{v['r']:+.2f}", _r_fg(v['r'])),
                (f"{v['rrr_sum']/v['count']:.2f}", DT_TEXT),
                (str(v['count']), DT_SUBTEXT),
            ])
        if _days_rows:
            _stat_card(_col_l, "DNY OBCHODOVÁNÍ", ["Den", "WR%", "R celkem", "Avg RRR", "Počet"], _days_rows)

        # SESSION
        _sess_rows = []
        for sk in sorted(stats['sessions'].keys()):
            v = stats['sessions'][sk]
            if v['count'] == 0: continue
            wr2 = v['wins']/v['count']*100
            _sess_rows.append([
                (sk, DT_TEXT),
                (f"{wr2:.1f}%", _wr_fg(wr2)),
                (f"{v['r']:+.2f}", _r_fg(v['r'])),
                (f"{v['rrr_sum']/v['count']:.2f}", DT_TEXT),
                (str(v['count']), DT_SUBTEXT),
            ])
        if _sess_rows:
            _stat_card(_col_l, "SESSION", ["Seance", "WR%", "R celkem", "Avg RRR", "Počet"], _sess_rows)

        # TIMEFRAME
        if stats['timeframes']:
            _tf_rows = []
            for tf in sorted(stats['timeframes'].keys()):
                v = stats['timeframes'][tf]
                if v['count'] == 0: continue
                wr2 = v['wins']/v['count']*100
                _tf_rows.append([
                    (tf, DT_TEXT),
                    (f"{wr2:.1f}%", _wr_fg(wr2)),
                    (f"{v['r']:+.2f}", _r_fg(v['r'])),
                    (str(v['count']), DT_SUBTEXT),
                ])
            if _tf_rows:
                _stat_card(_col_l, "TIMEFRAME VSTUPU", ["Timeframe", "WR%", "R celkem", "Počet"], _tf_rows)

        # TAGS
        if stats['tags']:
            _tag_rows = []
            for tg in sorted(stats['tags'].keys()):
                v = stats['tags'][tg]
                if v['count'] == 0: continue
                wr2 = v['wins']/v['count']*100
                _tag_rows.append([
                    (tg, DT_TEXT),
                    (f"{wr2:.1f}%", _wr_fg(wr2)),
                    (f"{v['r']:+.2f}", _r_fg(v['r'])),
                    (str(v['count']), DT_SUBTEXT),
                ])
            if _tag_rows:
                _stat_card(_col_l, "ŠTÍTKY (TAGS)", ["Tag", "WR%", "R celkem", "Počet"], _tag_rows)

        # ── PRAVÝ SLOUPEC ─────────────────────────────────────────────────────
        # Streak & Rolling
        streak_emoji = "🔥" if streak_type == 'win' else "❄️" if streak_type == 'loss' else ""
        rolling = stats['rolling']
        _rolling_rows = []
        for n in [10, 20, 50]:
            last_n = [(r, rv) for r, rv in rolling[-n:] if r in ('win','loss','be')]
            if len(last_n) >= min(n, 3):
                wr_n = sum(1 for r,_ in last_n if r == 'win') / len(last_n) * 100
                r_n  = sum(rv for _,rv in last_n)
                _rolling_rows.append([
                    (f"Posl. {n} obchodů", DT_SUBTEXT),
                    (f"{wr_n:.1f}%", _wr_fg(wr_n)),
                    (f"{r_n:+.2f} R", _r_fg(r_n)),
                ])
        _stat_card(_col_r, "STREAK & ROLLING WINRATE", ["", "WR%", "R"], [
            [("Aktuální série", DT_SUBTEXT), (f"{streak_emoji} {streak_cur}× {streak_type.upper() if streak_type else 'N/A'}", '#4ade80' if streak_type == 'win' else '#f87171')],
            [("Nejlepší WIN série", DT_SUBTEXT), (f"{best_win_streak}×", '#4ade80')],
            [("Nejhorší LOSS série", DT_SUBTEXT), (f"{best_loss_streak}×", '#f87171')],
        ] + _rolling_rows, accent='#065f46')

        # SETUP / FIBO
        _setup_rows = []
        for sk in sorted(stats['setups'].keys()):
            v = stats['setups'][sk]
            if v['count'] == 0: continue
            wr2 = v['wins']/v['count']*100
            _setup_rows.append([
                (sk, DT_TEXT),
                (f"{wr2:.1f}%", _wr_fg(wr2)),
                (f"{v['r']:+.2f}", _r_fg(v['r'])),
                (f"{v['rrr_sum']/v['count']:.2f}", DT_TEXT),
                (str(v['count']), DT_SUBTEXT),
            ])
        if _setup_rows:
            _stat_card(_col_r, "SETUP / FIBO", ["Setup", "WR%", "R celkem", "Avg RRR", "Počet"], _setup_rows)

        # SMĚR
        _dir_rows = []
        for d2 in ["Buy", "Sell"]:
            v = stats['directions'].get(d2, {'wins':0,'count':0,'r':0.0})
            wr2 = v['wins']/v['count']*100 if v['count'] > 0 else 0
            _dir_rows.append([
                (d2, '#4ade80' if d2 == 'Buy' else '#f87171'),
                (f"{wr2:.1f}%", _wr_fg(wr2)),
                (f"{v['r']:+.2f}", _r_fg(v['r'])),
                (str(v['count']), DT_SUBTEXT),
            ])
        _stat_card(_col_r, "SMĚR OBCHODU", ["Směr", "WR%", "R celkem", "Počet"], _dir_rows)

        # MĚSÍČNÍ PŘEHLED (full width)
        if stats['monthly']:
            _mo_rows = []
            for month in sorted(stats['monthly'].keys()):
                v = stats['monthly'][month]
                if v['count'] == 0: continue
                wr2 = v['wins']/v['count']*100
                _mo_rows.append([
                    (month, DT_TEXT),
                    (f"{wr2:.1f}%", _wr_fg(wr2)),
                    (f"{v['r']:+.2f}", _r_fg(v['r'])),
                    (f"{v['wins']}/{v['count']-v['wins']}", DT_SUBTEXT),
                    (str(v['count']), DT_SUBTEXT),
                ])
            _stat_card(_col_r, "MĚSÍČNÍ PŘEHLED", ["Měsíc", "WR%", "R", "W/L", "Obc"], _mo_rows, accent='#7c3aed')

        # TOP KOMBINACE (full-width pod sloupci)
        _combo_section = tk.Frame(tables_frame, bg=DT_BG)
        _combo_section.pack(fill='x', pady=(4, 0))
        combos = [(k, v) for k, v in stats['combinations'].items() if v['count'] >= 3]
        combos.sort(key=lambda x: x[1]['wins']/x[1]['count'], reverse=True)
        _combo_rows = []
        for k, v in combos[:10]:
            wr2 = v['wins']/v['count']*100
            _combo_rows.append([
                (k, DT_TEXT),
                (f"{wr2:.1f}%", _wr_fg(wr2)),
                (f"{v['r']:+.2f}", _r_fg(v['r'])),
                (str(v['count']), DT_SUBTEXT),
            ])
        if not _combo_rows:
            _combo_rows = [[("Potřeba min. 3 obchody na jednu kombinaci", DT_SUBTEXT), ("—",DT_SUBTEXT),("—",DT_SUBTEXT),("—",DT_SUBTEXT)]]
        _stat_card(_combo_section, "TOP KOMBINACE  (Session | Symbol | Setup)  — min. 3 obchody",
                   ["Kombinace", "WR%", "R celkem", "Počet"], _combo_rows, accent='#92400e')

        # PER ÚČET
        _acc_section = tk.Frame(tables_frame, bg=DT_BG)
        _acc_section.pack(fill='x', pady=(4, 0))
        if len(acct_stats) > 1 or (len(acct_stats)==1 and list(acct_stats.keys())[0]!='— (bez účtu) —'):
            _acc_rows = []
            for acname, s in sorted(acct_stats.items(), key=lambda x: -x[1]['r']):
                d3  = s['wins'] + s['losses']
                wr3 = s['wins'] / d3 * 100 if d3 > 0 else 0.0
                pf3 = f"{s['gross_p']/s['gross_l']:.2f}" if s['gross_l'] > 0 else ('∞' if s['gross_p'] > 0 else '—')
                nm  = (acname[:30]+'…') if len(acname) > 31 else acname
                _acc_rows.append([
                    (nm, DT_TEXT),
                    (str(s['count']), DT_SUBTEXT),
                    (f"{wr3:.1f}%", _wr_fg(wr3)),
                    (f"{s['r']:+.2f} R", _r_fg(s['r'])),
                    (pf3, DT_TEXT),
                ])
            _stat_card(_acc_section, "🏦  PŘEHLED PER ÚČET",
                       ["Účet", "Obc", "WR%", "R celkem", "P. Factor"], _acc_rows, accent='#1e3a5f')

    # Pie Charts (Winrate & Timeframes)
    if stats['total'] > 0:
        fig_pie = plt.Figure(figsize=(6, 3), dpi=80)
        ax_pie = fig_pie.add_subplot(121)
        labels = ['WIN', 'LOSS', 'BE']
        sizes = [cnt_win, cnt_loss, cnt_be]
        colors_pie = ['#2ecc71', '#e74c3c', '#95a5a6']
        final_sizes = []; final_labels = []; final_colors = []
        for s, l, c in zip(sizes, labels, colors_pie):
            if s > 0:
                final_sizes.append(s); final_labels.append(l); final_colors.append(c)
        if final_sizes:
            ax_pie.pie(final_sizes, labels=final_labels, colors=final_colors, autopct='%1.0f%%', startangle=140, pctdistance=0.75, textprops={'color':DT_TEXT, 'weight':'bold', 'fontsize': 9})
            centre_circle = plt.Circle((0,0),0.60,fc='#ffffff')
            ax_pie.add_artist(centre_circle)
            ax_pie.set_title("WINRATE", color=DT_TEXT, fontsize=10, pad=10)

        ax_tf = fig_pie.add_subplot(122)
        tf_items = sorted(stats['timeframes'].items(), key=lambda x: x[1]['count'], reverse=True)
        if tf_items:
            ax_tf.pie([x[1]['count'] for x in tf_items], labels=[x[0] for x in tf_items], autopct='%1.0f%%', startangle=90, pctdistance=0.75, textprops={'color':DT_TEXT, 'fontsize': 8})
            ax_tf.add_artist(plt.Circle((0,0),0.60,fc='#ffffff'))
            ax_tf.set_title("TIMEFRAMES", color=DT_TEXT, fontsize=10, pad=10)

        fig_pie.patch.set_facecolor('#ffffff')
        canvas_pie = FigureCanvasTkAgg(fig_pie, master=pie_graph_frame)
        canvas_pie.draw()
        canvas_pie.get_tk_widget().pack(fill='both', expand=True)
        pie_canvases.append(canvas_pie)

    # === EQUITY + DRAWDOWN (2 subploty) — dd_curve/max_dd_pct computed above ===
    fig = plt.Figure(figsize=(9, 5), dpi=100)
    fig.patch.set_facecolor('#ffffff')

    ax1 = fig.add_subplot(211)
    ax1.plot(equity_curve, color='#6366f1', linewidth=2)
    ax1.fill_between(range(len(equity_curve)), equity_curve, equity_curve[0], alpha=0.12, color='#6366f1')
    baseline = start_balance if current_mode == "REAL" else 0
    ax1.axhline(baseline, color='#94a3b8', alpha=0.6, linestyle='--')
    title_txt = f"Equity Curve ({prop_cfg.get('currency','USD')})" if current_mode == "REAL" else "Vývoj konta (R násobky)"
    ax1.set_title(title_txt, color=DT_TEXT, fontsize=10, pad=6)
    ax1.set_facecolor('#f8fafc'); ax1.tick_params(colors=DT_TEXT, labelsize=8)
    ax1.grid(True, alpha=0.5, color='#e2e8f0')
    for sp in ax1.spines.values(): sp.set_color('#cbd5e1')

    ax2 = fig.add_subplot(212, sharex=ax1)
    ax2.fill_between(range(len(dd_curve)), dd_curve, 0, color='#dc2626', alpha=0.25)
    ax2.plot(dd_curve, color='#dc2626', linewidth=1.2)
    ax2.set_title(f"Drawdown (max {max_dd_pct:.1f}%)", color='#dc2626', fontsize=9, pad=4)
    ax2.set_facecolor('#f8fafc'); ax2.tick_params(colors=DT_TEXT, labelsize=8)
    ax2.grid(True, alpha=0.5, color='#e2e8f0')
    for sp in ax2.spines.values(): sp.set_color('#cbd5e1')

    fig.tight_layout(pad=1.5)
    canvas = FigureCanvasTkAgg(fig, master=stats_graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    stats_canvases.append(canvas)

    # Heatmap
    if stats['total'] > 0:
        fig_hm = plt.Figure(figsize=(8, 4), dpi=100)
        ax_hm = fig_hm.add_subplot(111)
        flat_data = [item for sublist in heatmap_data for item in sublist]
        max_val = max(flat_data) if flat_data else 1
        min_val = min(flat_data) if flat_data else -1
        limit = max(abs(max_val), abs(min_val))
        if limit == 0: limit = 1
        im = ax_hm.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', interpolation='nearest', vmin=-limit, vmax=limit)
        ax_hm.set_xticks(range(5))
        ax_hm.set_xticklabels(['Po', 'Út', 'St', 'Čt', 'Pá'])
        ax_hm.set_yticks(range(0, 24, 2))
        ax_hm.set_yticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])
        ax_hm.set_title("HEATMAPA ZISKOVOSTI (Čas vs Den)", color=DT_TEXT, fontsize=10)
        cbar = fig_hm.colorbar(im, ax=ax_hm, pad=0.02)
        cbar.ax.yaxis.set_tick_params(color=DT_TEXT)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=DT_TEXT)
        fig_hm.patch.set_facecolor('#ffffff')
        ax_hm.set_facecolor('#f8fafc')
        ax_hm.tick_params(colors=DT_TEXT)
        for spine in ax_hm.spines.values(): spine.set_color('#cbd5e1')
        canvas_hm = FigureCanvasTkAgg(fig_hm, master=heatmap_graph_frame)
        canvas_hm.draw()
        canvas_hm.get_tk_widget().pack(fill='both', expand=True)
        heatmap_canvases.append(canvas_hm)

    # === BAR CHARTS: WR po dnech, seancích, symbolech + RRR po setupu ===
    if stats['total'] > 0 and bar_chart_frame:
        fig_b = plt.Figure(figsize=(10, 7), dpi=100)
        fig_b.patch.set_facecolor('#ffffff')
        bar_kw = dict(edgecolor='none', zorder=3)

        def _bar_wr(ax, data_dict, keys, title, clr_good='#4ade80', clr_bad='#f87171'):
            labels_b, wr_vals, cnt_vals = [], [], []
            for k in keys:
                v = data_dict.get(k)
                if not v or v['count'] == 0: continue
                labels_b.append(k[:8])
                wr_vals.append(v['wins'] / v['count'] * 100)
                cnt_vals.append(v['count'])
            if not labels_b: ax.text(0.5,0.5,'Žádná data',ha='center',va='center',color='gray',transform=ax.transAxes); return
            colors_b = [clr_good if w >= 50 else clr_bad for w in wr_vals]
            bars = ax.bar(labels_b, wr_vals, color=colors_b, **bar_kw)
            ax.axhline(50, color='#94a3b8', linewidth=0.8, linestyle='--', alpha=0.7)
            for bar, cnt in zip(bars, cnt_vals):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f'{bar.get_height():.0f}%\n(n={cnt})', ha='center', va='bottom', color=DT_TEXT, fontsize=7)
            ax.set_ylim(0, min(115, max(wr_vals)+20) if wr_vals else 100)
            ax.set_title(title, color=DT_ACCENT, fontsize=9, pad=6)
            ax.set_facecolor('#f8fafc'); ax.tick_params(colors=DT_TEXT, labelsize=7.5)
            ax.grid(axis='y', alpha=0.5, color='#e2e8f0')
            for sp in ax.spines.values(): sp.set_color('#cbd5e1')

        def _bar_rrr(ax, data_dict, keys, title):
            labels_b, rrr_vals, cnt_vals = [], [], []
            for k in keys:
                v = data_dict.get(k)
                if not v or v['count'] == 0: continue
                labels_b.append(k[:10])
                rrr_vals.append(v['rrr_sum'] / v['count'])
                cnt_vals.append(v['count'])
            if not labels_b: ax.text(0.5,0.5,'Žádná data',ha='center',va='center',color='gray',transform=ax.transAxes); return
            colors_b = ['#00d4aa' if r >= 2 else '#fbbf24' for r in rrr_vals]
            bars = ax.bar(labels_b, rrr_vals, color=colors_b, **bar_kw)
            for bar, cnt in zip(bars, cnt_vals):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.02, f'{bar.get_height():.2f}R\n(n={cnt})', ha='center', va='bottom', color=DT_TEXT, fontsize=7)
            ax.set_title(title, color=DT_ACCENT, fontsize=9, pad=6)
            ax.set_facecolor('#f8fafc'); ax.tick_params(colors=DT_TEXT, labelsize=7.5)
            ax.grid(axis='y', alpha=0.5, color='#e2e8f0')
            for sp in ax.spines.values(): sp.set_color('#cbd5e1')

        days_order = ["Pondělí","Úterý","Středa","Čtvrtek","Pátek"]
        sym_order  = sorted(stats.get('symbols', stats['sessions']).keys()) if False else \
                     sorted([k for k in set(t.get('symbol','') for t in trades if t.get('symbol'))],
                            key=lambda s: -stats['sessions'].get(s,{}).get('count',0))[:12]

        # Sestavíme symbol stats samostatně (sessions dict je seance, ne symboly)
        sym_stats = defaultdict(lambda: {'wins':0,'count':0,'r':0.0,'rrr_sum':0.0})
        for t in trades:
            if selected_symbol_filter != "VŠE" and t.get('symbol') != selected_symbol_filter: continue
            r2 = t.get('vysledek','').lower()
            if not r2: continue
            sym = t.get('symbol','?')
            try: rv = float(str(t.get('rrr',0)).replace(',','.'))
            except: rv = 0.0
            sym_stats[sym]['count'] += 1
            sym_stats[sym]['rrr_sum'] += rv
            if r2 == 'win': sym_stats[sym]['wins'] += 1
        sym_order2 = sorted(sym_stats.keys(), key=lambda s: -sym_stats[s]['count'])[:10]

        ax_b1 = fig_b.add_subplot(221)
        _bar_wr(ax_b1, stats['days'], days_order, "WR podle dne")
        ax_b2 = fig_b.add_subplot(222)
        _bar_wr(ax_b2, stats['sessions'], sorted(stats['sessions'].keys()), "WR podle seance")
        ax_b3 = fig_b.add_subplot(223)
        _bar_wr(ax_b3, sym_stats, sym_order2, "WR podle symbolu")
        ax_b4 = fig_b.add_subplot(224)
        _bar_rrr(ax_b4, stats['setups'], sorted(stats['setups'].keys()), "Prům. RRR podle setupu")

        fig_b.tight_layout(pad=2.0)
        canvas_b = FigureCanvasTkAgg(fig_b, master=bar_chart_frame)
        canvas_b.draw()
        canvas_b.get_tk_widget().pack(fill='both', expand=True)
        bar_chart_canvases.append(canvas_b)

def update_calculated_fields():
    t_start = cas_otevreni_entry.get().strip(); t_end = cas_zavreni_entry.get().strip()
    if t_start:
        try:
            dt_start = datetime.strptime(t_start, "%Y-%m-%d %H:%M")
            _cz = ["Pondělí","Úterý","Středa","Čtvrtek","Pátek","Sobota","Neděle"]
            den = _cz[dt_start.weekday()]; den_tydne_entry.config(state='normal'); den_tydne_entry.delete(0, tk.END); den_tydne_entry.insert(0, den); den_tydne_entry.config(state='readonly'); h = dt_start.hour
            if 8 <= h < 13: session_combo.set("London")
            elif 13 <= h < 17: session_combo.set("NY AM")
            elif 17 <= h < 21: session_combo.set("NY PM")
            else: session_combo.set("Asia")
            if t_end:
                dt_end = datetime.strptime(t_end, "%Y-%m-%d %H:%M"); diff = dt_end - dt_start; total_seconds = int(diff.total_seconds()); hours, remainder = divmod(total_seconds, 3600); minutes, _ = divmod(remainder, 60); duration_str = f"{hours}h {minutes}m"
                delka_obchodu_entry.config(state='normal'); delka_obchodu_entry.delete(0, tk.END); delka_obchodu_entry.insert(0, duration_str); delka_obchodu_entry.config(state='readonly')
        except: pass
    try:
        sym = symbol_combo.get().upper(); v = float(vstupni_hodnota_entry.get().replace(',','.')); sl = float(stoploss_entry.get().replace(',','.')); tp = float(takeprofit_entry.get().replace(',','.')); risk_dist = abs(v - sl); reward_dist = abs(tp - v); multiplier = 100 if ("JPY" in sym) else 10000 
        if "XAU" in sym or "US30" in sym or "DAX" in sym: multiplier = 10
        pips = round(risk_dist * multiplier, 1); pips_entry.config(state='normal'); pips_entry.delete(0, tk.END); pips_entry.insert(0, str(pips)); pips_entry.config(state='readonly')
        if risk_dist > 0: rrr = reward_dist / risk_dist; rrr_entry.delete(0, tk.END); rrr_entry.insert(0, f"{rrr:.2f}")
    except: pass

def calculate_auto_rrr(event=None):
    try:
        entry = float(vstupni_hodnota_entry.get().replace(',', '.'))
        sl    = float(stoploss_entry.get().replace(',', '.'))
        tp    = float(takeprofit_entry.get().replace(',', '.'))
        risk   = abs(entry - sl)
        reward = abs(tp - entry)
        if risk <= 0: return
        rrr = reward / risk
        rrr_entry.delete(0, tk.END); rrr_entry.insert(0, f"{rrr:.2f}")
        sym = symbol_combo.get() if symbol_combo else ''
        if sym in ('XAUUSD', 'XAGUSD'): mult = 10
        elif sym in ('NAS100', 'US30', 'SP500', 'GER40', 'UK100'): mult = 1
        elif 'JPY' in sym: mult = 100
        else: mult = 10000
        pips_entry.config(state='normal')
        pips_entry.delete(0, tk.END); pips_entry.insert(0, f"{risk * mult:.1f}")
        pips_entry.config(state='readonly')
        calculate_auto_score()
    except (ValueError, TypeError): pass

def calculate_auto_score():
    config = load_scoring_config(); total = 0
    total += config["setups"].get(fibo_combo.get(), 0); total += config["sessions"].get(session_combo.get(), 0); total += config["days"].get(den_tydne_entry.get(), 0)
    try:
        r = float(rrr_entry.get().replace(',', '.')); rrr_pts = config["rrr"]
        if r >= 5.0: total += rrr_pts.get("1:5+", 0)
        elif r >= 4.0: total += rrr_pts.get("1:4", 0)
        elif r >= 3.0: total += rrr_pts.get("1:3", 0)
        elif r >= 2.0: total += rrr_pts.get("1:2", 0)
        else: total += rrr_pts.get("1:1", 0)
    except: pass
    try:
        p = float(pips_entry.get().replace(',', '.')); pips_pts = config["pips"]
        if p >= 20: total += pips_pts.get("20+", 0)
        elif 15 <= p < 20: total += pips_pts.get("15-20", 0)
        elif 10 <= p < 15: total += pips_pts.get("10-15", 0)
        elif 5 <= p < 10: total += pips_pts.get("5-10", 0)
    except: pass
    thr = config["thresholds"]; res = "C"
    if total >= thr["A+"]: res = "A+"
    elif total >= thr["A"]: res = "A"
    elif total >= thr["B"]: res = "B"
    score_label.config(text=f"BODOVÁNÍ: {total} b. | SKÓRE: {res}", fg="#2ecc71" if res=="A+" else "#f1c40f" if res=="A" else "#e67e22")
    return res

def setup_settings_ui(parent):
    cfg = load_scoring_config(); entries = {}
    main_frame = tk.Frame(parent); main_frame.pack(fill='both', expand=True)
    canvas = tk.Canvas(main_frame); scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview); scrollable_frame = tk.Frame(canvas, padx=20, pady=20)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
    cats = ["thresholds", "setups", "sessions", "days", "rrr", "pips"]
    for cat in cats:
        tk.Label(scrollable_frame, text=cat.upper(), font=('Arial', 10, 'bold'), fg="#2c3e50").pack(pady=(15,5), anchor='center'); entries[cat] = {}; cf = tk.Frame(scrollable_frame); cf.pack(anchor='center'); col = 0; keys = list(cfg[cat].keys())
        if cat == "thresholds": order = ["A+", "A", "B"]; keys = [k for k in order if k in keys]
        for k in keys:
            v = cfg[cat][k]; f_item = tk.Frame(cf); f_item.grid(row=0, column=col, padx=5); tk.Label(f_item, text=k, font=('Arial', 8)).pack(anchor='w'); e = tk.Entry(f_item, width=5); e.insert(0, str(v)); e.pack(); entries[cat][k] = e; col += 1
    def save():
        for c in entries:
            for k in entries[c]: cfg[c][k] = int(entries[c][k].get())
        save_scoring_config(cfg); messagebox.showinfo("OK", "Uloženo!")
    tk.Button(scrollable_frame, text="ULOŽIT BODY", bg='green', fg='white', command=save, width=20, height=2).pack(pady=20, anchor='center')
    tk.Button(scrollable_frame, text="PŘEPOČÍTAT VŠECHNY OBCHODY", bg='#f39c12', fg='white', font=('Arial', 9, 'bold'), command=prepocitat_historii, width=30).pack(pady=(0, 20), anchor='center')
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(1, width=e.width))

def setup_lists_manager_ui(parent):
    main = tk.Frame(parent, padx=20, pady=20)
    main.pack(fill="both", expand=True)

    tk.Label(main, text="NASTAVENÍ SEZNAMŮ (PÁRY & TIMEFRAMES)", font=("Arial", 14, "bold"), fg="#2c3e50").pack(pady=(0, 20))

    content = tk.Frame(main)
    content.pack(fill="both", expand=True)

    # --- SEKCE PÁRY ---
    frame_pairs = tk.LabelFrame(content, text="Měnové páry (Symboly)", padx=10, pady=10)
    frame_pairs.pack(side="left", fill="both", expand=True, padx=(0, 10))

    lb_pairs = tk.Listbox(frame_pairs, font=("Arial", 10), selectmode=tk.SINGLE)
    lb_pairs.pack(side="left", fill="both", expand=True)
    sb_pairs = tk.Scrollbar(frame_pairs, orient="vertical", command=lb_pairs.yview)
    sb_pairs.pack(side="right", fill="y")
    lb_pairs.config(yscrollcommand=sb_pairs.set)
    for p in PAIRS: lb_pairs.insert(tk.END, p)

    ctrl_pairs = tk.Frame(frame_pairs, pady=10)
    ctrl_pairs.pack(side="bottom", fill="x")
    entry_pair = tk.Entry(ctrl_pairs, font=("Arial", 10))
    entry_pair.pack(fill="x", pady=5)
    
    def add_pair():
        val = entry_pair.get().strip().upper()
        if val and val not in PAIRS:
            PAIRS.append(val); PAIRS.sort()
            save_pairs_config(); lb_pairs.delete(0, tk.END)
            for p in PAIRS: lb_pairs.insert(tk.END, p)
            entry_pair.delete(0, tk.END)
            if symbol_combo: symbol_combo['values'] = PAIRS # Aktualizace dropdownu v hlavním okně
    
    def remove_pair():
        sel = lb_pairs.curselection()
        if sel:
            val = lb_pairs.get(sel[0])
            if messagebox.askyesno("Smazat", f"Opravdu odebrat {val}?"):
                if val in PAIRS: PAIRS.remove(val)
                save_pairs_config(); lb_pairs.delete(sel[0])
                if symbol_combo: symbol_combo['values'] = PAIRS

    tk.Button(ctrl_pairs, text="PŘIDAT PÁR", command=add_pair, bg="#2ecc71", fg="white", font=("Arial", 9, "bold")).pack(fill="x", pady=2)
    tk.Button(ctrl_pairs, text="ODEBRAT VYBRANÝ", command=remove_pair, bg="#e74c3c", fg="white", font=("Arial", 9)).pack(fill="x", pady=2)

    # --- SEKCE TIMEFRAMES ---
    frame_tf = tk.LabelFrame(content, text="Timeframes (HTF/LTF)", padx=10, pady=10)
    frame_tf.pack(side="right", fill="both", expand=True, padx=(10, 0))

    lb_tf = tk.Listbox(frame_tf, font=("Arial", 10), selectmode=tk.SINGLE)
    lb_tf.pack(side="left", fill="both", expand=True)
    sb_tf = tk.Scrollbar(frame_tf, orient="vertical", command=lb_tf.yview)
    sb_tf.pack(side="right", fill="y")
    lb_tf.config(yscrollcommand=sb_tf.set)
    for t in TIMEFRAMES: lb_tf.insert(tk.END, t)

    ctrl_tf = tk.Frame(frame_tf, pady=10)
    ctrl_tf.pack(side="bottom", fill="x")
    entry_tf = tk.Entry(ctrl_tf, font=("Arial", 10))
    entry_tf.pack(fill="x", pady=5)

    def add_tf():
        val = entry_tf.get().strip()
        if val and val not in TIMEFRAMES:
            TIMEFRAMES.append(val) # Nesortujeme, aby si uživatel mohl určit pořadí přidáním
            save_timeframes_config(); lb_tf.insert(tk.END, val)
            entry_tf.delete(0, tk.END)
            if htf_combo: htf_combo['values'] = TIMEFRAMES
            if ltf_combo: ltf_combo['values'] = TIMEFRAMES

    def remove_tf():
        sel = lb_tf.curselection()
        if sel:
            val = lb_tf.get(sel[0])
            if messagebox.askyesno("Smazat", f"Opravdu odebrat {val}?"):
                if val in TIMEFRAMES: TIMEFRAMES.remove(val)
                save_timeframes_config(); lb_tf.delete(sel[0])
                if htf_combo: htf_combo['values'] = TIMEFRAMES
                if ltf_combo: ltf_combo['values'] = TIMEFRAMES

    tk.Button(ctrl_tf, text="PŘIDAT TF", command=add_tf, bg="#2ecc71", fg="white", font=("Arial", 9, "bold")).pack(fill="x", pady=2)
    tk.Button(ctrl_tf, text="ODEBRAT VYBRANÝ", command=remove_tf, bg="#e74c3c", fg="white", font=("Arial", 9)).pack(fill="x", pady=2)

def setup_rules_ui(parent):
    frame = tk.Frame(parent, padx=20, pady=20)
    frame.pack(fill="both", expand=True)
    
    tk.Label(frame, text="MOJE OBCHODNÍ PRAVIDLA", font=("Arial", 14, "bold"), fg="#2c3e50").pack(anchor="w", pady=(0, 10))
    tk.Label(frame, text="Zde si udržujte aktuální seznam pravidel, která musíte dodržovat.", fg="gray").pack(anchor="w", pady=(0, 5))
    
    current_font_size = tk.IntVar(value=12)
    
    text_area = tk.Text(frame, font=("Consolas", current_font_size.get()), undo=True, wrap="word", padx=10, pady=10, bg="#fdfefe")
    text_area.pack(fill="both", expand=True)
    
    # Load content
    content = load_rules_text()
    text_area.insert("1.0", content)
    
    btn_frame = tk.Frame(frame, pady=10)
    btn_frame.pack(fill="x")
    
    tk.Button(btn_frame, text="💾 ULOŽIT PRAVIDLA", command=lambda: save_rules_text(text_area.get("1.0", tk.END)), 
              bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), height=2, width=20).pack(side="left")

    # Font controls
    font_ctrl = tk.Frame(btn_frame)
    font_ctrl.pack(side="right")
    
    tk.Label(font_ctrl, text="Velikost písma:").pack(side="left", padx=5)
    
    def update_font(delta):
        new_size = current_font_size.get() + delta
        if 8 <= new_size <= 32:
            current_font_size.set(new_size)
            text_area.configure(font=("Consolas", new_size))
            
    tk.Button(font_ctrl, text="-", command=lambda: update_font(-1), width=3).pack(side="left")
    tk.Label(font_ctrl, textvariable=current_font_size, width=4, font=("Arial", 10, "bold")).pack(side="left")
    tk.Button(font_ctrl, text="+", command=lambda: update_font(1), width=3).pack(side="left")

# Globální slovník pro filtry galerie (vyplňuje se při stavbě záložky)
_GAL_FILTERS = {}

def update_gallery():
    if gallery_inner is None: return
    for w in gallery_inner.winfo_children(): w.destroy()

    f_sym  = _GAL_FILTERS.get('sym_var',  tk.StringVar(value='VŠE')).get()
    f_res  = _GAL_FILTERS.get('res_var',  tk.StringVar(value='VŠE')).get()
    f_ses  = _GAL_FILTERS.get('ses_var',  tk.StringVar(value='VŠE')).get()
    f_tag  = _GAL_FILTERS.get('tag_var',  tk.StringVar()).get().strip().lower()
    f_sort = _GAL_FILTERS.get('sort_var', tk.StringVar(value='Datum ↓')).get()
    f_size = _GAL_FILTERS.get('size_var', tk.IntVar(value=200)).get()
    f_cols = _GAL_FILTERS.get('cols_var', tk.IntVar(value=5)).get()
    count_var = _GAL_FILTERS.get('count_var', None)

    trades = load_data()
    gallery_items = []
    if not os.path.exists(IMAGES_DIR):
        if count_var: count_var.set("Složka obrázků neexistuje.")
        return

    for orig_idx, t in enumerate(trades):
        if f_sym and f_sym != 'VŠE' and t.get('symbol', '') != f_sym: continue
        res_raw = t.get('vysledek', '').strip()
        if f_res and f_res != 'VŠE' and res_raw.lower() != f_res.lower(): continue
        if f_ses and f_ses != 'VŠE' and t.get('session', '') != f_ses: continue
        if f_tag and f_tag not in t.get('tags', '').lower(): continue

        for img_name in t.get('obrazky', '').split(';'):
            if not img_name: continue
            full_path = os.path.join(IMAGES_DIR, img_name)
            if os.path.exists(full_path):
                gallery_items.append({
                    'path': full_path, 'result': res_raw,
                    'symbol': t.get('symbol', ''), 'datum': t.get('cas_otevreni', '')[:10],
                    'session': t.get('session', ''), 'smer': t.get('smer', ''),
                    'rrr': t.get('rrr', ''), 'tags': t.get('tags', ''),
                    'trade_id': t.get('trade_id', ''),
                    'orig_idx': orig_idx,
                })

    sort_key = {'Datum ↓': lambda x: x['datum'], 'Datum ↑': lambda x: x['datum'],
                'Symbol': lambda x: x['symbol'],
                'Výsledek': lambda x: {'win':0,'loss':1,'be':2}.get(x['result'].lower(), 3)}
    rev = f_sort == 'Datum ↓'
    gallery_items.sort(key=sort_key.get(f_sort, lambda x: x['datum']), reverse=rev)

    if count_var: count_var.set(f"{len(gallery_items)} obrázků")

    RES_COLORS = {'win': ('#d5f5e3','#1e8449'), 'loss': ('#fadbd8','#922b21'), 'be': ('#fef9e7','#9a7d0a')}
    thumb_w = max(100, min(int(f_size), 340))
    thumb_h = int(thumb_w * 0.75)
    cols = max(1, int(f_cols))

    row, col = 0, 0
    for idx, item in enumerate(gallery_items):
        try:
            img = Image.open(item['path']); img.thumbnail((thumb_w, thumb_h))
            ph = ImageTk.PhotoImage(img)
            res_lower = item['result'].lower()
            bg_c, fg_c = RES_COLORS.get(res_lower, ('#f5f5f5', '#333'))

            frame = tk.Frame(gallery_inner, bg=bg_c, highlightbackground='#ccc', highlightthickness=1)
            frame.grid(row=row, column=col, padx=6, pady=6, sticky='n')

            lbl = tk.Label(frame, image=ph, cursor='hand2', bg=bg_c)
            lbl.image = ph; lbl.pack(padx=2, pady=(4, 2))
            lbl.bind('<Button-1>', lambda e, i=idx: ImageZoomViewer(root, gallery_items, i))

            # ── ID + sym + výsledek ───────────────────────────────────────────
            info = tk.Frame(frame, bg=bg_c); info.pack(fill='x', padx=4, pady=(0, 1))
            tid = item.get('trade_id', '')
            if tid:
                tk.Label(info, text=f"#{tid}", bg=bg_c, fg='#888',
                         font=('Segoe UI', 7, 'bold')).pack(side='left')
            sym_txt = item['symbol'] or '—'
            if item['smer']: sym_txt += f" {item['smer']}"
            tk.Label(info, text=sym_txt, bg=bg_c, fg=fg_c,
                     font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(4, 0))
            tk.Label(info, text=item['result'].upper() or '—', bg=bg_c, fg=fg_c,
                     font=('Segoe UI', 8, 'bold')).pack(side='right')

            # ── Datum + RRR + session ─────────────────────────────────────────
            meta = tk.Frame(frame, bg=bg_c); meta.pack(fill='x', padx=4, pady=(0, 2))
            tk.Label(meta, text=item['datum'], bg=bg_c, fg='#666',
                     font=('Segoe UI', 7)).pack(side='left')
            if item['rrr']:
                tk.Label(meta, text=f"R:{item['rrr']}", bg=bg_c, fg='#555',
                         font=('Segoe UI', 7)).pack(side='right')
            if item['session']:
                tk.Label(meta, text=item['session'], bg=bg_c, fg='#888',
                         font=('Segoe UI', 7)).pack(side='right', padx=(0, 4))

            # ── Proklik → obchod ─────────────────────────────────────────────
            def _go_to_trade(orig=item['orig_idx']):
                try:
                    reset_filter()
                    if main_notebook:
                        main_notebook.select(0)  # přepni na ZÁPIS tab
                    def _select():
                        try:
                            trades_tree.selection_set(str(orig))
                            trades_tree.focus(str(orig))
                            trades_tree.see(str(orig))
                            show_trade_details(None)
                        except Exception: pass
                    root.after(80, _select)
                except Exception: pass

            nav_row = tk.Frame(frame, bg=bg_c); nav_row.pack(fill='x', padx=4, pady=(0, 4))
            nav_btn = tk.Label(nav_row, text="→ přejít na obchod", bg=bg_c, fg='#4a90d9',
                               font=('Segoe UI', 7, 'underline'), cursor='hand2')
            nav_btn.pack(side='left')
            nav_btn.bind('<Button-1>', lambda e, fn=_go_to_trade: fn())

            col += 1
            if col >= cols: col = 0; row += 1
        except Exception: pass

def _save_trades_file(trades, reference_trade=None):
    """
    Uloží všechny obchody do CSV s jednotnými sloupci.
    Sjednotí klíče ze všech obchodů + reference_trade (nový/editovaný).
    Vyplní chybějící hodnoty prázdným stringem.
    Tím se zabrání posunutí sloupců při přidání nového pole.
    """
    if not trades and not reference_trade:
        return

    # ── Přiřaď trade_id obchodům, které ho nemají ────────────────────────────
    _max_id = 0
    for t in trades:
        _tid = t.get('trade_id', '')
        if str(_tid).isdigit():
            _max_id = max(_max_id, int(_tid))
    for t in trades:
        if not t.get('trade_id'):
            _max_id += 1
            t['trade_id'] = str(_max_id)

    # Sestav pořadí sloupců: reference_trade má nejaktuálnější klíče
    ref_keys = list(reference_trade.keys()) if reference_trade else []
    # Přidej klíče ze starých obchodů pokud nejsou v ref
    extra_keys = []
    for t in trades:
        for k in t.keys():
            if k not in ref_keys and k not in extra_keys:
                extra_keys.append(k)
    all_keys = ref_keys + extra_keys
    # Vyplň chybějící klíče v každém obchodu
    for t in trades:
        for k in all_keys:
            if k not in t:
                t[k] = ''
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=all_keys, extrasaction='ignore')
        w.writeheader()
        w.writerows(trades)

def pridat_obchod():
    global editing_trade_index
    if not DATA_FILE: messagebox.showerror("Chyba", "Není vybrán žádný projekt!"); return

    try:
        update_calculated_fields(); qual = calculate_auto_score()
        checklist_res = show_checklist_popup()
        if checklist_res is None: return 
        
        # Výběr účtu — ulož jen čistý název (bez [FTMO 100k] části)
        _raw_ucet = accounts_combo.get() if accounts_combo else ''
        _ucet_map = get_account_short_names()
        _ucet_val = _ucet_map.get(_raw_ucet, _raw_ucet)
        if _ucet_val.startswith('—'): _ucet_val = ''

        d = {
            'ucet': _ucet_val,
            'cas_otevreni': cas_otevreni_entry.get(), 'cas_zavreni': cas_zavreni_entry.get(),
            'symbol': symbol_combo.get(), 'smer': smer_var.get(), 'vstupni_hodnota': vstupni_hodnota_entry.get(),
            'stoploss': stoploss_entry.get(), 'takeprofit': takeprofit_entry.get(), 'rrr': rrr_entry.get(),
            'pips': pips_entry.get(), 'session': session_combo.get(), 'timeframe_graf': htf_combo.get(),
            'timeframe_vstup': ltf_combo.get(), 'fibo': fibo_combo.get(), 'duvod': duvod_entry.get(),
            'poznamka': poznamka_entry.get(), 'vysledek': vysledek_combo.get(), 'den_tydne': den_tydne_entry.get(),
            'delka_obchodu': delka_obchodu_entry.get(), 'slippage': slippage_entry.get(),
            'kvalita': qual, 'obrazky': obrazky_list.get(), 'news': news_var.get(),
            'news_event': news_event_entry.get(),
            'checklist_ratio': checklist_res,
            'tags': tags_entry.get(),
            'zisk_mena': zisk_mena_entry.get() if zisk_mena_entry else '',
        }
        trades = load_data()
        if editing_trade_index is not None:
            if editing_trade_index < len(trades):
                trades[editing_trade_index] = d
                _save_trades_file(trades, d)
                _dbg_log('TRADE', f"EDIT #{editing_trade_index}: {d.get('symbol')} {d.get('smer')} výsledek={d.get('vysledek')} zisk={d.get('zisk_mena')} projekt={os.path.basename(DATA_FILE)}")
                messagebox.showinfo("OK", "Obchod aktualizován."); editing_trade_index = None; save_btn.config(text="ULOŽIT OBCHOD", bg='#2ecc71')
                try: award_xp_for_trade(d, is_edit=True, parent_win=root)
                except Exception: pass
        else:
            trades.append(d)
            _save_trades_file(trades, d)
            _dbg_log('TRADE', f"NOVÝ: {d.get('symbol')} {d.get('smer')} výsledek={d.get('vysledek')} zisk={d.get('zisk_mena')} projekt={os.path.basename(DATA_FILE)}")
            messagebox.showinfo("OK", "Obchod uložen.")
            try: award_xp_for_trade(d, is_edit=False, parent_win=root)
            except Exception: pass
        update_listbox(); reset_form(); update_statistics()
    except Exception as e:
        messagebox.showerror("Chyba ukládání", f"Nastala chyba:\n{e}\n\n{traceback.format_exc()}")

def delete_specific_image(trade_idx, img_name):
    trades = load_data()
    if trade_idx >= len(trades): return
    t = trades[trade_idx]; current_imgs = [n for n in t.get('obrazky','').split(';') if n]
    if img_name in current_imgs:
        current_imgs.remove(img_name); t['obrazky'] = ";".join(current_imgs)
        _save_trades_file(trades)
        class MockEvent: pass
        show_trade_details(MockEvent()); messagebox.showinfo("Smazáno", "Obrázek odstraněn.")

def go_to_journal_for_trade(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M"); show_journal_screen_target_date(dt)
    except:
        try: dt = datetime.strptime(date_str, "%Y-%m-%d"); show_journal_screen_target_date(dt)
        except: messagebox.showerror("Chyba", "Nelze přečíst datum obchodu.")

def open_ff_calendar_for_date(date_str_input):
    try:
        if " " in date_str_input: dt = datetime.strptime(date_str_input, "%Y-%m-%d %H:%M")
        else: dt = datetime.strptime(date_str_input, "%Y-%m-%d")
        months_map = {1:"jan",2:"feb",3:"mar",4:"apr",5:"may",6:"jun",7:"jul",8:"aug",9:"sep",10:"oct",11:"nov",12:"dec"}
        m_str = months_map[dt.month]; day_str = dt.day; year_str = dt.year
        url = f"https://www.forexfactory.com/calendar?day={m_str}{day_str}.{year_str}"
        webbrowser.open(url)
    except Exception as e: messagebox.showerror("Chyba", f"Nepodařilo se otevřít kalendář.\n{e}")

def show_trade_details(event):
    global checklist_display_label
    if trades_tree is None: return
    sel = trades_tree.selection()
    if not sel: return
    idx = int(sel[0]); trades = load_data()
    if idx >= len(trades): return
    t = trades[idx]; details_text.delete(1.0, tk.END)
    for k, v in t.items():
        if k != 'obrazky': details_text.insert(tk.END, f"{k.capitalize():15}: {v}\n")
    
    if checklist_display_label:
        val = t.get('checklist_ratio', 'N/A')
        if val != 'N/A' and '/' in val:
            try:
                parts = val.split('/'); ok = int(parts[0]); total = int(parts[1]); ratio = ok / total if total > 0 else 0
                txt = f"✅ CHECKLIST: {val} ({int(ratio*100)}%)" if ratio == 1.0 else f"⚠️ CHECKLIST: {val} ({int(ratio*100)}%)"
                fg_col = "#27ae60" if ratio == 1.0 else "#e67e22" 
                if ratio < 0.5: fg_col = "#c0392b"
                checklist_display_label.config(text=txt, fg=fg_col)
            except: checklist_display_label.config(text=f"Checklist: {val}", fg="gray")
        else: checklist_display_label.config(text="Checklist: N/A", fg="gray")
            
    for w in image_frame.winfo_children(): w.destroy()
    img_names = [n for n in t.get('obrazky','').split(';') if n]
    trade_gallery_items = []
    info_parts = []; 
    if t.get('symbol'): info_parts.append(t['symbol'])
    if t.get('smer'): info_parts.append(t['smer'])
    if t.get('vysledek'): info_parts.append(t['vysledek'])
    label_text = " | ".join(info_parts)
    for name in img_names:
        full_path = os.path.join(IMAGES_DIR, name)
        if os.path.exists(full_path): trade_gallery_items.append({'path': full_path, 'info': label_text})
    for i, item in enumerate(trade_gallery_items):
        img_name = os.path.basename(item['path']); img = Image.open(item['path']); img.thumbnail((120, 80)); ph = ImageTk.PhotoImage(img)
        lbl = tk.Label(image_frame, image=ph, cursor="hand2"); lbl.image = ph; lbl.pack(side='left', padx=2)
        lbl.bind("<Button-1>", lambda e, idx=i, items=trade_gallery_items: ImageZoomViewer(root, items, idx))
        menu = tk.Menu(root, tearoff=0); menu.add_command(label="Odstranit obrázek", command=lambda ti=idx, iname=img_name: delete_specific_image(ti, iname))
        def do_popup(event, m=menu):
            try: m.tk_popup(event.x_root, event.y_root)
            finally: m.grab_release()
        lbl.bind("<Button-3>", do_popup)

def pridat_obrazky():
    paths = filedialog.askopenfilenames()
    for p in paths:
        fname = os.path.basename(p); shutil.copy(p, os.path.join(IMAGES_DIR, fname))
        obrazky_list.set((obrazky_list.get() + ";" + fname).strip(';'))

def reset_form():
    global editing_trade_index
    _clear = [e for e in [vstupni_hodnota_entry, stoploss_entry, takeprofit_entry, rrr_entry,
                           poznamka_entry, duvod_entry, news_event_entry, tags_entry, zisk_mena_entry]
              if e is not None]
    for e in _clear: e.delete(0, tk.END)
    cas_otevreni_entry.delete(0, tk.END); cas_otevreni_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
    obrazky_list.set(""); editing_trade_index = None; news_var.set("Ne"); save_btn.config(text="ULOŽIT OBCHOD", bg='#2ecc71')
    if accounts_combo:
        vals = get_account_dropdown_values()
        accounts_combo['values'] = vals
        accounts_combo.set(vals[0] if vals else '')

def smazat_obchod():
    if trades_tree is None: return
    sel = trades_tree.selection()
    if sel:
        idx = int(sel[0]); tr = load_data()
        if idx < len(tr):
            del tr[idx]
            _save_trades_file(tr)
            update_listbox(); update_statistics(); reset_form()

def _tree_sort(col):
    """Kliknutí na záhlaví sloupce — přepne řazení a znovu sestaví seznam."""
    global _sort_col, _sort_rev
    if _sort_col == col:
        _sort_rev = not _sort_rev
    else:
        _sort_col = col
        _sort_rev = False
    update_listbox()


def _sort_val(raw, col):
    """Klíč pro řazení — numerické sloupce jako číslo, ostatní jako string."""
    s = str(raw).strip()
    # Kvalita: A+ > A > B > C
    if col == 'kvalita':
        _q = {'A+': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
        return _q.get(s.upper(), 0)
    # checklist_ratio "3/4" → 0.75
    if col == 'checklist_ratio' and '/' in s:
        try:
            a, b = s.split('/')
            return float(a) / float(b) if float(b) else 0.0
        except: return 0.0
    # Procenta "+2.5%" → 2.5
    s_num = s.replace('%', '').replace('+', '').replace(',', '.').replace(' ', '')
    try:
        return float(s_num)
    except (ValueError, TypeError):
        return s.lower()


def update_listbox():
    global _sort_col, _sort_rev
    if trades_tree is None: return
    for item in trades_tree.get_children(): trades_tree.delete(item)
    # Barevné řádky – tagy
    trades_tree.tag_configure('win',  background=DT_WIN_BG,  foreground=DT_WIN_FG)
    trades_tree.tag_configure('loss', background=DT_LOSS_BG, foreground=DT_LOSS_FG)
    trades_tree.tag_configure('be',   background=DT_BE_BG,   foreground=DT_BE_FG)
    trades_tree.tag_configure('other', background=DT_PANEL,  foreground=DT_TEXT)

    cfg = load_scoring_config(); current_cols = cfg.get("columns", DEFAULT_SCORING["columns"]); trades = load_data()

    # P&L% lookup: mapa název_účtu → počáteční kapitál
    _acct_cap_lookup = {}
    if ACCOUNTS_FILE and os.path.exists(ACCOUNTS_FILE):
        try:
            for _a in load_accounts():
                _n = _a.get('nazev', '').strip()
                _v = _a.get('velikost', '')
                if _n and _v:
                    try: _acct_cap_lookup[_n] = float(str(_v).replace(',', '.').replace(' ', ''))
                    except: pass
        except: pass

    # Hodnoty filtrů
    f_symbol  = filter_symbol_var.get()    if filter_symbol_var  else "VŠE"
    f_result  = filter_result_var.get()    if filter_result_var  else "VŠE"
    f_session = filter_session_var.get()   if filter_session_var else "VŠE"
    f_from    = filter_date_from_var.get() if filter_date_from_var else ""
    f_to      = filter_date_to_var.get()   if filter_date_to_var else ""
    _f_tag_raw = filter_tag_var.get().strip().lower() if filter_tag_var else ""
    f_tag     = "" if _f_tag_raw in ("vše", "vse", "") else _f_tag_raw
    f_rrr_min = filter_rrr_min_var.get().strip() if filter_rrr_min_var else ""
    f_rrr_max = filter_rrr_max_var.get().strip() if filter_rrr_max_var else ""

    # ── Sbírání a filtrování ──────────────────────────────────────────────────
    filtered = []   # (orig_idx, t, _t_display, tag_str)
    for i, t in enumerate(trades):
        res = t.get('vysledek', '').lower()
        trade_date = t.get('cas_otevreni', '')[:10]
        if f_symbol != "VŠE" and t.get('symbol', '') != f_symbol: continue
        if f_result != "VŠE" and res != f_result.lower(): continue
        if f_session != "VŠE" and t.get('session', '') != f_session: continue
        if f_from and trade_date < f_from: continue
        if f_to and trade_date > f_to: continue
        if f_tag and f_tag not in t.get('tags', '').lower(): continue
        if f_rrr_min:
            try:
                if float(str(t.get('rrr', '0')).replace(',', '.')) < float(f_rrr_min): continue
            except: pass
        if f_rrr_max:
            try:
                if float(str(t.get('rrr', '0')).replace(',', '.')) > float(f_rrr_max): continue
            except: pass

        _t_display = dict(t)
        if 'pnl_pct' in current_cols:
            _ucet = t.get('ucet', '').strip()
            _zm   = t.get('zisk_mena', '').strip().replace(',', '.').replace(' ', '')
            _cap  = _acct_cap_lookup.get(_ucet, 0)
            _pnl_pct_val = ''
            # 1) REAL mód s účtem: zisk_mena / počáteční kapitál
            if _zm and _cap > 0:
                try: _pnl_pct_val = f"{float(_zm) / _cap * 100:+.2f}%"
                except: pass
            # 2) Fallback — výpočet z cenových úrovní (BACKTEST nebo chybějící zisk_mena)
            if not _pnl_pct_val:
                try:
                    def _pf(v): return float(str(v).replace(',', '.').replace(' ', ''))
                    _entry = _pf(t.get('vstupni_hodnota', ''))
                    _sl    = _pf(t.get('stoploss', ''))
                    _tp    = _pf(t.get('takeprofit', ''))
                    _vysl  = t.get('vysledek', '').lower().strip()
                    _smer  = t.get('smer', '').lower().strip()
                    if _entry > 0 and _vysl in ('win', 'loss', 'be'):
                        if _vysl == 'be':
                            _pnl_pct_val = '0.00%'
                        elif _smer in ('buy', 'long'):
                            if _vysl == 'win':
                                _pnl_pct_val = f"{(_tp - _entry) / _entry * 100:+.2f}%"
                            else:
                                _pnl_pct_val = f"{(_sl - _entry) / _entry * 100:+.2f}%"
                        elif _smer in ('sell', 'short'):
                            if _vysl == 'win':
                                _pnl_pct_val = f"{(_entry - _tp) / _entry * 100:+.2f}%"
                            else:
                                _pnl_pct_val = f"{(_entry - _sl) / _entry * 100:+.2f}%"
                except: pass
            _t_display['pnl_pct'] = _pnl_pct_val

        tag = 'win' if res == 'win' else 'loss' if res == 'loss' else 'be' if res == 'be' else 'other'
        filtered.append((i, t, _t_display, tag))

    # ── Řazení ───────────────────────────────────────────────────────────────
    if _sort_col and _sort_col in current_cols:
        try:
            filtered.sort(
                key=lambda x: _sort_val(x[2].get(_sort_col, x[1].get(_sort_col, '')), _sort_col),
                reverse=_sort_rev
            )
        except TypeError:
            # Smíšené typy — fallback na string
            filtered.sort(
                key=lambda x: str(x[2].get(_sort_col, x[1].get(_sort_col, ''))).lower(),
                reverse=_sort_rev
            )

    # ── Záhlaví — ukaž šipku u aktivního sloupce ─────────────────────────────
    for col in current_cols:
        base = COL_TRANSLATION.get(col, col)
        if col == _sort_col:
            arrow = " ↓" if _sort_rev else " ↑"
            trades_tree.heading(col, text=base + arrow)
        else:
            trades_tree.heading(col, text=base)

    # ── Vkládání ─────────────────────────────────────────────────────────────
    for orig_idx, t, _t_display, tag in filtered:
        vals = [_t_display.get(c, "") for c in current_cols]
        trades_tree.insert("", "end", iid=orig_idx, values=vals, tags=(tag,))

def on_close():
    try:
        backup_project()
        cfg = load_scoring_config()
        if trades_tree and trades_tree.winfo_exists():
            col_widths = {}
            for col in trades_tree['columns']:
                try: col_widths[col] = trades_tree.column(col, "width")
                except: pass
            cfg["layout"]["col_widths"] = col_widths
        if paned and paned.winfo_exists():
            try: cfg["layout"]["sash_horizontal"] = paned.sash_coord(0)[0]
            except: pass
        if v_paned and v_paned.winfo_exists():
            try: cfg["layout"]["sash_vertical"] = v_paned.sash_coord(0)[1]
            except: pass
        save_scoring_config(cfg)
    except Exception as e: print(f"Chyba pri ukladani configu: {e}")
    try: root.destroy()
    except: pass
    sys.exit()

def apply_saved_layout():
    root.update_idletasks(); cfg = load_scoring_config(); layout = cfg.get("layout", {}); col_widths = layout.get("col_widths", {})
    if trades_tree and col_widths:
        for col, width in col_widths.items():
            if int(width) > 0:
                try: trades_tree.column(col, width=int(width))
                except: pass
    if paned and "sash_horizontal" in layout:
        try: paned.sash_place(0, int(layout["sash_horizontal"]), 0)
        except: pass
    if v_paned and "sash_vertical" in layout:
        try: v_paned.sash_place(0, 0, int(layout["sash_vertical"]))
        except: pass

def open_column_config(): ColumnConfigurator(root, lambda: show_main_screen(current_project_name))
def load_saved_filters():
    if FILTERS_FILE and os.path.exists(FILTERS_FILE):
        try:
            with open(FILTERS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {}

def save_saved_filters(data):
    if FILTERS_FILE:
        try:
            with open(FILTERS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e: print(f"Chyba uložení filtrů: {e}")

def save_current_filter(saved_combo=None):
    name = simpledialog.askstring("Uložit filtr", "Název filtru:")
    if not name: return
    data = load_saved_filters()
    data[name] = {
        'symbol': filter_symbol_var.get() if filter_symbol_var else 'VŠE',
        'result': filter_result_var.get() if filter_result_var else 'VŠE',
        'session': filter_session_var.get() if filter_session_var else 'VŠE',
        'date_from': filter_date_from_var.get() if filter_date_from_var else '',
        'date_to': filter_date_to_var.get() if filter_date_to_var else '',
        'tag': filter_tag_var.get() if filter_tag_var else '',
    }
    save_saved_filters(data)
    if saved_combo:
        saved_combo['values'] = list(data.keys())
    messagebox.showinfo("Filtr uložen", f"Filtr '{name}' byl uložen.")

def apply_saved_filter_by_name(name, saved_combo=None):
    data = load_saved_filters()
    if name not in data: return
    f = data[name]
    if filter_symbol_var: filter_symbol_var.set(f.get('symbol', 'VŠE'))
    if filter_result_var: filter_result_var.set(f.get('result', 'VŠE'))
    if filter_session_var: filter_session_var.set(f.get('session', 'VŠE'))
    if filter_date_from_var: filter_date_from_var.set(f.get('date_from', ''))
    if filter_date_to_var: filter_date_to_var.set(f.get('date_to', ''))
    if filter_tag_var: filter_tag_var.set(f.get('tag', ''))
    update_listbox()

def apply_filter(): update_listbox()
def reset_filter():
    if filter_val_var: filter_val_var.set("")
    if filter_symbol_var: filter_symbol_var.set("VŠE")
    if filter_result_var: filter_result_var.set("VŠE")
    if filter_session_var: filter_session_var.set("VŠE")
    if filter_date_from_var: filter_date_from_var.set("")
    if filter_date_to_var: filter_date_to_var.set("")
    if filter_tag_var: filter_tag_var.set("")
    if filter_rrr_min_var: filter_rrr_min_var.set("")
    if filter_rrr_max_var: filter_rrr_max_var.set("")
    update_listbox()
def open_external_calendar(): webbrowser.open("https://www.forexfactory.com/calendar")

def duplikovat_obchod():
    if trades_tree is None: return
    sel = trades_tree.selection()
    if not sel: messagebox.showwarning("Upozornění", "Vyber obchod k duplikaci."); return
    idx = int(sel[0]); trades = load_data()
    if idx >= len(trades): return
    t = trades[idx]
    symbol_combo.set(t.get('symbol', '')); smer_var.set(t.get('smer', 'Buy'))
    vstupni_hodnota_entry.delete(0, tk.END); vstupni_hodnota_entry.insert(0, t.get('vstupni_hodnota', ''))
    takeprofit_entry.delete(0, tk.END); takeprofit_entry.insert(0, t.get('takeprofit', ''))
    stoploss_entry.delete(0, tk.END); stoploss_entry.insert(0, t.get('stoploss', ''))
    rrr_entry.delete(0, tk.END); rrr_entry.insert(0, t.get('rrr', ''))
    htf_combo.set(t.get('timeframe_graf', '')); ltf_combo.set(t.get('timeframe_vstup', ''))
    fibo_combo.set(t.get('fibo', '')); session_combo.set(t.get('session', ''))
    duvod_entry.delete(0, tk.END); duvod_entry.insert(0, t.get('duvod', ''))
    tags_entry.delete(0, tk.END); tags_entry.insert(0, t.get('tags', ''))
    news_var.set(t.get('news', 'Ne')); news_event_entry.delete(0, tk.END); news_event_entry.insert(0, t.get('news_event', ''))
    cas_otevreni_entry.delete(0, tk.END); cas_otevreni_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
    cas_zavreni_entry.delete(0, tk.END); vysledek_combo.set(''); obrazky_list.set('')
    messagebox.showinfo("Duplikát", "Parametry zkopírovány. Uprav čas a výsledek, pak ulož."); update_calculated_fields(); calculate_auto_score()

def naci_obchod_pro_upravu():
    global editing_trade_index
    if trades_tree is None: return
    sel = trades_tree.selection()
    if not sel: messagebox.showwarning("Upozornění", "Vyber obchod k úpravě."); return
    idx = int(sel[0]); editing_trade_index = idx; trades = load_data()
    if idx >= len(trades): return
    t = trades[idx]
    cas_otevreni_entry.delete(0, tk.END); cas_otevreni_entry.insert(0, t.get('cas_otevreni',''))
    cas_zavreni_entry.delete(0, tk.END); cas_zavreni_entry.insert(0, t.get('cas_zavreni',''))
    symbol_combo.set(t.get('symbol','')); smer_var.set(t.get('smer','Buy'))
    vstupni_hodnota_entry.delete(0, tk.END); vstupni_hodnota_entry.insert(0, t.get('vstupni_hodnota',''))
    takeprofit_entry.delete(0, tk.END); takeprofit_entry.insert(0, t.get('takeprofit',''))
    stoploss_entry.delete(0, tk.END); stoploss_entry.insert(0, t.get('stoploss',''))
    rrr_entry.delete(0, tk.END); rrr_entry.insert(0, t.get('rrr',''))
    htf_combo.set(t.get('timeframe_graf','')); ltf_combo.set(t.get('timeframe_vstup',''))
    fibo_combo.set(t.get('fibo','')); session_combo.set(t.get('session',''))
    duvod_entry.delete(0, tk.END); duvod_entry.insert(0, t.get('duvod',''))
    poznamka_entry.delete(0, tk.END); poznamka_entry.insert(0, t.get('poznamka',''))
    vysledek_combo.set(t.get('vysledek','')); obrazky_list.set(t.get('obrazky',''))
    slippage_entry.delete(0, tk.END); slippage_entry.insert(0, t.get('slippage','0'))
    news_var.set(t.get('news', 'Ne'))
    news_event_entry.delete(0, tk.END); news_event_entry.insert(0, t.get('news_event', ''))
    tags_entry.delete(0, tk.END); tags_entry.insert(0, t.get('tags', ''))
    if zisk_mena_entry: zisk_mena_entry.delete(0, tk.END); zisk_mena_entry.insert(0, t.get('zisk_mena', ''))
    update_calculated_fields(); calculate_auto_score(); save_btn.config(text="AKTUALIZOVAT OBCHOD", bg="#e67e22")

# ==============================================================================
# SCREENSHOT ANALYZER
# ==============================================================================

def analyze_screenshot(image_path):
    """
    Analyzuje TradingView screenshot pomocí řádkové BGR analýzy + HSV contour fallback.
    Funguje pro světlé i tmavé motivy TradingView.
    """
    import cv2, pytesseract, re
    import numpy as np

    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Nelze načíst obrázek.")

    h, w = img.shape[:2]
    result = {}
    debug_lines = []

    # ── 1. Detekce světlého/tmavého pozadí ───────────────────────────────────
    _bg_sample  = img[70:130, max(0, w - 60):]
    _is_dark_bg = float(np.mean(_bg_sample)) < 80
    debug_lines.append(f"[DEBUG] img={w}x{h}  dark_bg={_is_dark_bg}")

    # ── 2. Scan úzkého pruhu vpravo — jen price scale oblast ─────────────────
    # Záměrně úzký aby se vyhnul barevným zónám v grafu
    # Dark BG: 5 % (cca 96px na 1920px); Light BG: 6 %
    label_pct   = 0.05 if _is_dark_bg else 0.06
    label_w     = max(70, int(w * label_pct))
    label_strip = img[:, max(0, w - label_w):]
    debug_lines.append(f"  label_w={label_w}")

    raw_bands = []   # (y_start, y_end, color_class)  color_class = 'red' | 'other'
    cur_cls   = None
    cur_start = None

    for y in range(h):
        row   = label_strip[y].astype(np.float32)
        b_arr = row[:, 0]; g_arr = row[:, 1]; r_arr = row[:, 2]
        mx    = np.maximum(np.maximum(b_arr, g_arr), r_arr)
        mn    = np.minimum(np.minimum(b_arr, g_arr), r_arr)
        sat_m = (mx - mn) > 35
        if not np.any(sat_m):
            cls = None
        else:
            b = float(np.mean(b_arr[sat_m]))
            g = float(np.mean(g_arr[sat_m]))
            r = float(np.mean(r_arr[sat_m]))
            sat = max(b, g, r) - min(b, g, r)
            if sat < 25:
                cls = None
            elif r > b * 1.2 and r > g * 1.2:
                cls = 'red'     # RED → SL (TradingView červená)
            elif r > 140 and g > 120 and b < 80 and r > b * 2.0 and g > b * 1.5:
                cls = 'yellow'  # YELLOW/GOLD → aktuální tržní cena (přeskočit!)
            elif (b > r * 1.4 or g > r * 1.4):
                cls = 'other'   # Modrá / zelená = Entry nebo TP
            else:
                cls = None

        if cls != cur_cls:
            if cur_cls and cur_start is not None and (y - cur_start) >= 3:
                raw_bands.append((cur_start, y, cur_cls))
            cur_cls   = cls
            cur_start = y if cls else None

    # Merge sousedních stejnobarevných pásů
    def _merge(bl, gap=10):
        if not bl: return []
        bl = sorted(bl)
        out = [list(bl[0])]
        for b in bl[1:]:
            p = out[-1]
            if b[2] == p[2] and b[0] - p[1] <= gap:
                p[1] = b[1]
            else:
                out.append(list(b))
        return [tuple(x) for x in out]

    merged = _merge(raw_bands)
    # Price label box: max ~50 px tall. Zóny Kill Zone / Session = stovky px → vyhodíme
    bands = [b for b in merged if (b[1] - b[0]) <= 55]
    debug_lines.append(f"  raw_bands={raw_bands[:10]}  bands={bands}")

    # ── 3. OCR ceny z každého pásu ───────────────────────────────────────────
    # Širší pruh pro OCR (samotný text může být trochu dál od okraje)
    ocr_w     = max(90, int(w * (0.06 if _is_dark_bg else 0.11)))
    ocr_strip = img[:, max(0, w - ocr_w):]
    debug_lines.append(f"  ocr_w={ocr_w}")

    def _parse_price(text):
        """Parsuje string s cenou — podporuje forex (1.18225), gold (2378.64), indexy (43500.25)."""
        text = text.strip().replace(' ', '')
        nums = re.findall(r'\d+', text)
        if len(nums) >= 2:
            try:
                # Forex má až 5 desetinných míst (1.18225), gold/indexy 2 (2378.64)
                dec = nums[-1][:5]   # max 5 decimal digits
                v   = float(''.join(nums[:-1]) + '.' + dec)
                if v > 0.01: return v
            except: pass
        # Fallback: hledej číslo s tečkou nebo čárkou
        for n in re.findall(r'\d+[.,]\d+', text.replace(',', '.')):
            try:
                v = float(n)
                if v > 0.01: return v
            except: pass
        # Fallback 2: celé číslo >= 4 cifry (indexy, BTC)
        for n in re.findall(r'\d{4,}', text):
            try:
                v = float(n)
                if v > 0.01: return v
            except: pass
        return None

    def ocr_price_band(y_s, y_e, tag=''):
        pad = 8
        roi = ocr_strip[max(0, y_s - pad):min(h, y_e + pad), :]
        if roi.size == 0: return None
        roi_big = cv2.resize(roi, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        gray    = cv2.cvtColor(roi_big, cv2.COLOR_BGR2GRAY)

        # Pro SVĚTLÉ BG: cena je bílý text na barevném boxu
        #   → BINARY(160) dá bílý text / černé pozadí → INVERT → černý text na bílém → Tesseract
        # Pro TMAVÉ BG: cena je bílý text na tmavém bg
        #   → stejný postup ale threshold nižší
        if _is_dark_bg:
            attempts = [(130, True), (100, True), (160, False)]
        else:
            attempts = [(160, True), (120, True), (80, True), (160, False)]

        best_val = None
        for thr_val, do_inv in attempts:
            _, thr = cv2.threshold(gray, thr_val, 255, cv2.THRESH_BINARY)
            if do_inv: thr = cv2.bitwise_not(thr)
            txt = pytesseract.image_to_string(
                thr, config='--psm 7 -c tessedit_char_whitelist=0123456789.,'
            )
            debug_lines.append(f"    ocr[{tag}] thr={thr_val} inv={do_inv}: '{txt.strip()}'")
            v = _parse_price(txt)
            if v:
                best_val = v
                break
        try:
            cv2.imwrite(f'C:\\obd\\debug_band_{tag}.png', roi_big)
        except: pass
        return best_val

    # Sbírej (y_mid, color_class, price) pro každý band
    detected = []   # list of dict {y_mid, cls, price}
    for y_s, y_e, cls in bands:
        if cls == 'yellow':
            # Žlutý label = aktuální tržní cena (EURUSD 1.17926) → přeskočit
            debug_lines.append(f"  band yellow[{y_s}-{y_e}] → SKIP (aktuální cena)")
            continue
        tag   = f"{cls}_{y_s}"
        price = ocr_price_band(y_s, y_e, tag=tag)
        y_mid = (y_s + y_e) / 2
        debug_lines.append(f"  band {cls}[{y_s}-{y_e}] y_mid={y_mid:.0f} → price={price}")
        if price and price > 0.1:
            detected.append({'y_mid': y_mid, 'cls': cls, 'price': price})

    # ── 4. Přiřazení SL / Entry / TP podle pozice a barvy ───────────────────
    # Pravidla:
    #   • RED band → vždy SL (TradingView červená = stop loss)
    #   • YELLOW band → aktuální tržní cena → ignorovat
    #   • Ze 3 bandů: prostřední (mediánové Y) = Entry, krajní = TP
    #   • Ze 2 bandů bez červené: menší Y (výše na obrazovce) = Entry nebo TP

    red_bands   = [d for d in detected if d['cls'] == 'red']
    other_bands = [d for d in detected if d['cls'] == 'other']

    # SL z červeného bandu
    if red_bands:
        # Vezmi nejpravější / nejčistší červený band (největší Y rozsah)
        best_sl = sorted(red_bands, key=lambda d: d['price'])[0]
        result['stoploss'] = f"{best_sl['price']:.6g}"
        debug_lines.append(f"  → SL(red)={best_sl['price']}")

    # Zbývající bary seřaď podle Y polohy (nahoře = malé Y = vyšší cena)
    all_non_sl = sorted(other_bands, key=lambda d: d['y_mid'])

    if len(all_non_sl) == 1:
        result['vstupni_hodnota'] = f"{all_non_sl[0]['price']:.6g}"
        debug_lines.append(f"  → Entry(only)={all_non_sl[0]['price']}")

    elif len(all_non_sl) >= 2:
        if red_bands:
            sl_y   = red_bands[0]['y_mid']
            # Entry = non-SL band nejblíže k SL (na ose Y — Entry leží mezi SL a TP)
            by_dist = sorted(all_non_sl, key=lambda d: abs(d['y_mid'] - sl_y))
            entry   = by_dist[0]
            tp      = by_dist[1]
        else:
            # Bez červené: hledáme Entry + TP podle Y polohy
            if len(all_non_sl) >= 3:
                # Prostřední pásmo (Y) = Entry — platí pro Buy i Sell
                mid   = len(all_non_sl) // 2
                entry = all_non_sl[mid]
                remaining = [d for i, d in enumerate(all_non_sl) if i != mid]
                # SL je blíže Entry cenou (menší R/R vzdálenost), TP dál
                # → takto funguje pro Buy i Sell
                remaining.sort(key=lambda d: abs(d['price'] - entry['price']))
                sl_band = remaining[0]   # blíže Entry = SL
                tp      = remaining[-1]  # dál od Entry = TP
                result['stoploss'] = f"{sl_band['price']:.6g}"
                debug_lines.append(f"  3-band-no-red: SL(closest)={sl_band['price']}  TP(farthest)={tp['price']}")
            else:
                # 2 pásma bez červené: Entry = prostřední ze dvou → nem možné určit přesně
                # Použij Y polohu: vyšší na obrazovce (menší Y) = výše = u Buy = TP, u Sell = SL
                # Nechme to na post-processingu — přiřaď tentativně podle Y
                by_y = sorted(all_non_sl, key=lambda d: d['y_mid'])  # seřaď: top→bottom
                # Pro Buy: TP nahoře, Entry dole (SL chybí)
                # Pro Sell: SL nahoře, Entry dole (chybí TP)
                # Bezpečnější: vyšší cena = TP (častěji správné pro oba směry)
                by_price = sorted(all_non_sl, key=lambda d: d['price'], reverse=True)
                # Pokud Y a cena souhlasí (top = higher price), jsme v normálu
                if by_y[0]['price'] > by_y[1]['price']:
                    # Horní pásmo má vyšší cenu → Buy (TP nahoře) nebo Sell (SL nahoře)
                    # Přiřaď horní jako TP tentativně — post-proc opraví pokud je to SL
                    entry = by_y[1]   # spodní = Entry
                    tp    = by_y[0]   # horní = TP (nebo SL — opraví post-proc)
                else:
                    entry = by_y[0]
                    tp    = by_y[1]
                debug_lines.append(f"  2-band-no-red: tentative Entry={entry['price']}  TP={tp['price']}")

        result['vstupni_hodnota'] = f"{entry['price']:.6g}"
        result['takeprofit']      = f"{tp['price']:.6g}"
        debug_lines.append(f"  → Entry={entry['price']}  TP={tp['price']}")

    # ── 5. HSV fallback — pokud chybí některá hodnota ────────────────────────
    def _is_plausible(s):
        try: return float(s) > 0.1
        except: return False

    if not all(_is_plausible(result.get(k)) for k in ('vstupni_hodnota', 'stoploss', 'takeprofit')):
        search_w    = max(200, int(w * 0.18))
        right_panel = img[:, max(0, w - search_w):]
        hsv_rp      = cv2.cvtColor(right_panel, cv2.COLOR_BGR2HSV)

        hsv_ranges = {
            'stoploss':       [(np.array([0,  120, 80]), np.array([10,  255, 255])),
                               (np.array([165,120, 80]), np.array([179, 255, 255]))],
            'vstupni_hodnota':[(np.array([85, 60,  60]), np.array([145, 255, 255]))],
            'takeprofit':     [(np.array([55, 60,  60]), np.array([100, 255, 255])),
                               (np.array([140,60,  60]), np.array([179, 255, 255]))],
        }

        for key, ranges in hsv_ranges.items():
            if _is_plausible(result.get(key)):
                debug_lines.append(f"  hsv_{key}: skip (already={result.get(key)})")
                continue
            mask_h = np.zeros(right_panel.shape[:2], np.uint8)
            for lo, hi in ranges:
                mask_h |= cv2.inRange(hsv_rp, lo, hi)
            mask_h = cv2.morphologyEx(mask_h, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            cnts, _ = cv2.findContours(mask_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best_c = None
            for cnt in cnts:
                x, y, cw, ch = cv2.boundingRect(cnt)
                if 6 < ch < 60 and cw > 15 and cv2.contourArea(cnt) > 100:
                    score = x + cw
                    if best_c is None or score > best_c[0]:
                        best_c = (score, x, y, cw, ch)
            debug_lines.append(f"  hsv_{key}: best={best_c}")
            if not best_c: continue
            _, bx, by, bw2, bh2 = best_c
            roi_h = right_panel[max(0, by-3):min(right_panel.shape[0], by+bh2+3),
                                max(0, bx-3):min(right_panel.shape[1], bx+bw2+3)]
            if roi_h.size == 0: continue
            try: cv2.imwrite(f'C:\\obd\\debug_hsv_{key}.png', roi_h)
            except: pass
            roi_h_big = cv2.resize(roi_h, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
            gray_h    = cv2.cvtColor(roi_h_big, cv2.COLOR_BGR2GRAY)
            for thr_val, do_inv in [(160, True), (160, False)]:
                _, thr_h = cv2.threshold(gray_h, thr_val, 255, cv2.THRESH_BINARY)
                if do_inv: thr_h = cv2.bitwise_not(thr_h)
                txt_h = pytesseract.image_to_string(thr_h, config='--psm 7 -c tessedit_char_whitelist=0123456789.,').strip()
                debug_lines.append(f"  hsv_{key} ocr thr={thr_val} inv={do_inv}: '{txt_h}'")
                v_h = _parse_price(txt_h)
                if v_h:
                    result[key] = f"{v_h:.6g}"
                    break

    # ── 4. Symbol ─────────────────────────────────────────────────────────────
    title_h = max(65, int(h * 0.045))
    top      = img[0:title_h, :]
    top_gray = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
    top_big  = cv2.resize(top_gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, top_thr = cv2.threshold(top_big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    top_txt  = pytesseract.image_to_string(top_thr, config='--psm 6').upper()

    SYM_PATTERNS = [
        (r'\bXAUUSD\b', 'XAUUSD'), (r'\bGOLDSPOT\b', 'XAUUSD'), (r'\bGOLD\b', 'XAUUSD'),
        (r'\bEURUSD\b', 'EURUSD'), (r'\bGBPUSD\b',  'GBPUSD'),  (r'\bUSDJPY\b', 'USDJPY'),
        (r'\bGBPJPY\b', 'GBPJPY'), (r'\bUSDCAD\b',  'USDCAD'),  (r'\bAUDUSD\b', 'AUDUSD'),
        (r'\bNAS\s*100\b', 'NAS100'), (r'\bNASDAQ\b', 'NAS100'),
        (r'\bUS30\b', 'US30'),     (r'\bDOW\b', 'US30'),
        (r'\bSP500\b', 'US500'),   (r'\bUS\s*500\b', 'US500'),
        (r'\bBTCUSD\b', 'BTCUSD'), (r'\bBITCOIN\b', 'BTCUSD'), (r'\bDAX\b', 'DAX'),
    ]
    for pat, sym in SYM_PATTERNS:
        if re.search(pat, top_txt):
            result['symbol'] = sym; break

    if not result.get('symbol'):
        ref = None
        for k in ('vstupni_hodnota', 'stoploss', 'takeprofit'):
            try: ref = float(result[k]); break
            except: pass
        if ref:
            if   1400 < ref < 5500:   result['symbol'] = 'XAUUSD'
            elif 0.50 < ref < 2.00:   result['symbol'] = 'EURUSD'
            elif 100  < ref < 200:    result['symbol'] = 'USDJPY'
            elif 1.00 < ref < 2.50:   result['symbol'] = 'GBPUSD'
            elif 14000< ref < 25000:  result['symbol'] = 'NAS100'
            elif 30000< ref < 50000:  result['symbol'] = 'US30'

    # ── 5. Časy otevření / uzavření ───────────────────────────────────────────
    month_map = {'jan':'01','feb':'02','mar':'03','apr':'04','may':'05','jun':'06',
                 'jul':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'}

    def parse_all_dt(txt):
        # Normalizuj — odstraň unicode apostrofy, uvozovky, nahraď _ mezerou
        txt = txt.replace('’', '').replace('‘', '').replace('“', '').replace('”', '')
        txt = txt.encode('ascii', 'ignore').decode('ascii')
        txt = re.sub(r"['\"`]", '', txt)
        txt = txt.replace('_', ' ')
        found = []
        # Formát 1: "Wed 04 Feb 26 10:00" nebo "04 Feb 2026 10:00"
        for m in re.finditer(
                r'(?:\w{3,9}\s+)?(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\s*[,\s\']*(\d{2,4})[,\s]+(\d{1,2}:\d{2})', txt):
            day, mon, yr, tim = m.groups()
            mo = month_map.get(mon.lower())
            if mo:
                yr4 = yr if len(yr) == 4 else '20' + yr
                dt  = f"{yr4}-{mo}-{day.zfill(2)} {tim}"
                if dt not in found: found.append(dt)
        # Formát 2: "Feb 04, 2026, 10:00" nebo "Feb 04 2026 10:00"
        if not found:
            for m2 in re.finditer(
                    r'([A-Za-z]{3})[A-Za-z]*\s+(\d{1,2})[,\s]+(\d{4})[,\s]+(\d{1,2}:\d{2})', txt):
                mon, day, yr, tim = m2.groups()
                mo = month_map.get(mon.lower())
                if mo:
                    dt = f"{yr}-{mo}-{day.zfill(2)} {tim}"
                    if dt not in found: found.append(dt)
        # Formát 3: "2026-02-04 10:00" (ISO)
        for m3 in re.finditer(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}:\d{2})', txt):
            yr, mo, day, tim = m3.groups()
            dt = f"{yr}-{mo}-{day} {tim}"
            if dt not in found: found.append(dt)
        return found

    debug_lines.append(f"  prices_before_postproc={result}")
    open_time = close_time = None

    y_axis_start = int(h * 0.60)
    axis_strip   = img[y_axis_start:, :]
    hsv_strip    = cv2.cvtColor(axis_strip, cv2.COLOR_BGR2HSV)
    blue_ranges  = [
        (np.array([85,  60,  80]), np.array([145, 255, 255])),
        (np.array([85,  30, 100]), np.array([145, 255, 255])),
    ]
    blue_mask = np.zeros(hsv_strip.shape[:2], np.uint8)
    for lo, hi in blue_ranges:
        blue_mask |= cv2.inRange(hsv_strip, lo, hi)
    blue_mask = cv2.morphologyEx(blue_mask,
                                 cv2.MORPH_CLOSE,
                                 cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5)))
    contours2, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    time_boxes = []
    for cnt in contours2:
        bx, by, bw2, bh2 = cv2.boundingRect(cnt)
        if bw2 < 50 or bh2 < 8: continue
        abs_y = by + y_axis_start
        roi   = img[abs_y:abs_y+bh2, bx:bx+bw2]
        if roi.size == 0: continue
        roi_big  = cv2.resize(roi, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        roi_gray = cv2.cvtColor(roi_big, cv2.COLOR_BGR2GRAY)
        roi_inv  = cv2.bitwise_not(roi_gray)
        _, roi_thr = cv2.threshold(roi_inv, 80, 255, cv2.THRESH_BINARY)
        txt = pytesseract.image_to_string(roi_thr, config='--psm 7 --oem 3')
        debug_lines.append(f"  blue box ({bx},{abs_y},{bw2},{bh2}): '{txt.strip()}'")
        for dt in parse_all_dt(txt):
            time_boxes.append((bx, dt))
            debug_lines.append(f"    -> {dt}")

    time_boxes.sort(key=lambda t: t[1])
    seen_dt = []
    for _, dt in time_boxes:
        if dt not in seen_dt: seen_dt.append(dt)
    if len(seen_dt) >= 1: open_time  = seen_dt[0]
    if len(seen_dt) >= 2: close_time = seen_dt[-1]

    # Fallback — skenuj spodní část obrazovky textem (hledáme oba časy)
    if not open_time or not close_time:
        # Skenuj celý spodek obrázku (posledních 20 % výšky) — tam jsou replay časy
        bottom_y  = int(h * 0.80)
        bottom    = img[bottom_y:, :]
        gray_bot  = cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)
        big_bot   = cv2.resize(gray_bot, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        all_times = list(seen_dt)  # začni s tím co už máme z blue boxů

        for thr_val, do_inv in [(160, True), (100, False), (80, False), (200, True)]:
            _, thr_img = cv2.threshold(big_bot, thr_val, 255, cv2.THRESH_BINARY)
            if do_inv: thr_img = cv2.bitwise_not(thr_img)
            full_txt = pytesseract.image_to_string(thr_img, config='--psm 6 --oem 3')
            debug_lines.append(f"  fallback_bottom thr={thr_val} inv={do_inv}: '{full_txt[:120].strip()}'")
            for line in full_txt.splitlines():
                for dt in parse_all_dt(line):
                    if dt not in all_times:
                        all_times.append(dt)

        # Pokud spodek nestačil, zkus celý obrázek
        if len(all_times) < 2:
            gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            big_full  = cv2.resize(gray_full, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            for thr_val in [160, 100, 80]:
                _, thr_img = cv2.threshold(big_full, thr_val, 255, cv2.THRESH_BINARY)
                full_txt   = pytesseract.image_to_string(thr_img, config='--psm 6 --oem 3')
                for line in full_txt.splitlines():
                    for dt in parse_all_dt(line):
                        if dt not in all_times:
                            all_times.append(dt)

        try:
            all_times.sort(key=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M"))
        except Exception:
            pass

        if not open_time and all_times:
            open_time = all_times[0]
        if not close_time and len(all_times) >= 2:
            close_time = all_times[-1]

    debug_lines.append(f"\nFINAL_TIMES: open={open_time}  close={close_time}")

    if open_time:  result['cas_otevreni'] = open_time
    if close_time: result['cas_zavreni']  = close_time

    # ── 6. Post-processing: zahoď hodnoty mimo rozsah symbolu ────────────────
    _price_ranges = {
        'XAUUSD': (1400, 5500),   'EURUSD': (0.5,  2.5),
        'GBPUSD': (1.0,  2.5),   'USDJPY': (80,   200),
        'GBPJPY': (100,  280),   'USDCAD': (1.0,  2.0),
        'AUDUSD': (0.5,  1.2),   'NAS100': (8000, 25000),
        'US30':  (20000, 50000), 'US500':  (2000,  7000),
        'BTCUSD':(5000, 120000), 'DAX':   (8000,  22000),
    }
    _sym = result.get('symbol')
    if _sym in _price_ranges:
        _lo, _hi = _price_ranges[_sym]
        for _k in ('vstupni_hodnota', 'stoploss', 'takeprofit'):
            try:
                if result.get(_k) and not (_lo <= float(result[_k]) <= _hi):
                    debug_lines.append(f"  postproc: removed {_k}={result[_k]} (out of range {_lo}-{_hi} for {_sym})")
                    result.pop(_k, None)
            except (ValueError, TypeError): pass

    # ── 7. Směr z poměru cen + auto-oprava prohozených hodnot ───────────────
    try:
        entry = float(result.get('vstupni_hodnota', 0))
        sl    = float(result.get('stoploss', 0))
        tp    = float(result.get('takeprofit', 0))
        if entry and sl and tp:
            if tp > entry > sl:
                result['smer'] = 'Buy'
            elif sl > entry > tp:
                result['smer'] = 'Sell'
            else:
                # Hodnoty nedávají smysl — zkus prohozené SL↔TP
                if sl > tp > entry or entry > tp > sl:
                    # Prohoď TP a SL
                    result['stoploss'], result['takeprofit'] = result.get('takeprofit',''), result.get('stoploss','')
                    sl, tp = tp, sl
                    debug_lines.append(f"  postproc: prohodil SL↔TP → SL={sl} TP={tp}")
                    if tp > entry > sl:   result['smer'] = 'Buy'
                    elif sl > entry > tp: result['smer'] = 'Sell'
        elif entry and tp and not sl:
            # Máme jen Entry + TP (chybí SL) — Entry by mělo být MEZI SL a TP
            # Alespoň nastav smer tentativně podle polohy TP vůči Entry
            if tp > entry: result['smer'] = 'Buy'
            else:          result['smer'] = 'Sell'
    except (ValueError, TypeError): pass

    debug_lines.append(f"FINAL_RESULT: {result}")
    _detail = '\n'.join(debug_lines)
    try:
        with open(r'C:\obd\time_debug.txt', 'w', encoding='utf-8') as dbf:
            dbf.write(_detail)
    except: pass
    _dbg_log('OCR-PATRIK', f"file={os.path.basename(image_path)}\n{_detail}", level='DEBUG')

    return result


def analyze_screenshot_tomas(image_path):
    """
    Analyzuje TradingView screenshot ve stylu Tomáše:
      • PINK / salmon label  → aktuální tržní cena (přeskočit, jako žlutá u Patrika)
      • CYAN / teal label    → obchodní hladina (Entry / TP)
      • YELLOW label         → obchodní hladina (Entry / TP) — u Tomáše NENÍ skip!
      • RED label            → SL (stejně jako u Patrika)
    Zbytek logiky (OCR, band assignment, post-processing) identický s Patrikovým profilem.
    """
    import cv2, pytesseract, re
    import numpy as np

    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Nelze načíst obrázek.")

    def _fmt_p(p):
        """Formátuj cenu s vhodným počtem desetinných míst (bez ztráty trailing zeros)."""
        if p < 10:      return f"{p:.5f}"   # GBPUSD, EURUSD → 1.25300
        elif p < 200:   return f"{p:.3f}"   # USDJPY         → 145.500
        elif p < 10000: return f"{p:.2f}"   # XAUUSD, DAX    → 2378.64
        else:           return f"{p:.0f}"   # BTC, indices   → 98500

    h, w = img.shape[:2]
    result = {}
    debug_lines = []

    # ── 1. Detekce světlého/tmavého pozadí ───────────────────────────────────
    _bg_sample  = img[70:130, max(0, w - 60):]
    _is_dark_bg = float(np.mean(_bg_sample)) < 80
    debug_lines.append(f"[TOMAS DEBUG] img={w}x{h}  dark_bg={_is_dark_bg}")

    # ── 2. Scan pruhu vpravo — detekce barevných pásů ────────────────────────
    label_pct   = 0.05 if _is_dark_bg else 0.06
    label_w     = max(70, int(w * label_pct))
    label_strip = img[:, max(0, w - label_w):]
    debug_lines.append(f"  label_w={label_w}")

    raw_bands = []
    cur_cls   = None
    cur_start = None

    for y in range(h):
        row   = label_strip[y].astype(np.float32)
        b_arr = row[:, 0]; g_arr = row[:, 1]; r_arr = row[:, 2]
        mx    = np.maximum(np.maximum(b_arr, g_arr), r_arr)
        mn    = np.minimum(np.minimum(b_arr, g_arr), r_arr)
        sat_m = (mx - mn) > 35
        if not np.any(sat_m):
            cls = None
        else:
            b = float(np.mean(b_arr[sat_m]))
            g = float(np.mean(g_arr[sat_m]))
            r = float(np.mean(r_arr[sat_m]))
            sat = max(b, g, r) - min(b, g, r)
            if sat < 25:
                cls = None
            elif r > b * 1.2 and r > g * 1.2:
                # Červená — SL (stejné jako u Patrika)
                # POZOR: musí být PŘED pink testem, protože pure red by prošlo pink podmínkou
                # Čistě červená: r >> g a r >> b (g a b relativně malé)
                if g < r * 0.75 and b < r * 0.75:
                    cls = 'red'
                # Pink/salmon: r dominantní, ale g a b jsou výrazné (pastelová)
                elif r > 160 and g > 90 and b > 80 and r > g * 1.15 and r > b * 1.15 and (g - b) < 70:
                    cls = 'pink'   # aktuální tržní cena → přeskočit
                else:
                    cls = 'red'    # ostatní červeno-přídech → SL
            elif b > r * 1.4 and (g > r * 1.2 or b > 150):
                cls = 'other'   # CYAN / teal → obchodní hladina
            elif r > 140 and g > 120 and b < 80 and r > b * 2.0 and g > b * 1.5:
                cls = 'other'   # YELLOW → obchodní hladina (u Tomáše NENÍ skip!)
            elif (b > r * 1.4 or g > r * 1.4):
                cls = 'other'   # modrá / zelená obecně
            else:
                cls = None

        if cls != cur_cls:
            if cur_cls and cur_start is not None and (y - cur_start) >= 3:
                raw_bands.append((cur_start, y, cur_cls))
            cur_cls   = cls
            cur_start = y if cls else None

    def _merge(bl, gap=10):
        if not bl: return []
        bl = sorted(bl)
        out = [list(bl[0])]
        for b in bl[1:]:
            p = out[-1]
            if b[2] == p[2] and b[0] - p[1] <= gap:
                p[1] = b[1]
            else:
                out.append(list(b))
        return [tuple(x) for x in out]

    merged = _merge(raw_bands)

    # Tomáš používá velké barevné ZÓNY: CYAN (TP) + ŠEDÁ (přechod) + ŽLUTÁ/ČERVENá (Entry) + ČERVENÁ (SL).
    # Pravidlo: skenuj jen PRVNÍ a POSLEDNÍ velkou 'other' zónu + OBOU jejich hran.
    # Střední (přechodové) šedé zóny dávají falešné hodnoty → přeskočit.
    # Malé pásy (≤55px): skenuj normálně (jsou to konkrétní labely).
    EDGE_PX = 26   # výška okrajového plátku (px)

    # Seřaď velké 'other' zóny podle Y — potřebujeme vědět které jsou krajní
    _large_other = [(ys, ye, cl) for ys, ye, cl in merged
                    if cl not in ('red', 'pink') and (ye - ys) > 55]

    bands = []
    for y_s, y_e, cls in merged:
        h_band = y_e - y_s
        if cls in ('red',):
            # Červené: vždy skenuj celý malý pás
            if h_band <= 55:
                bands.append((y_s, y_e, cls))
        elif cls == 'pink':
            bands.append((y_s, y_e, cls))   # přeskočeno později v sbírání
        else:
            # 'other' — buď malé nebo velké
            if h_band <= 55:
                bands.append((y_s, y_e, cls))
            elif h_band <= 1500 and (y_s, y_e, cls) in _large_other:
                # Velká 'other' zóna: skenuj jen pokud je PRVNÍ nebo POSLEDNÍ
                is_first = (y_s, y_e, cls) == _large_other[0]
                is_last  = (y_s, y_e, cls) == _large_other[-1]
                if is_first or is_last or len(_large_other) <= 2:
                    # Horní hrana — vždy
                    bands.append((y_s, min(y_s + EDGE_PX, y_e), cls))
                    # Dolní hrana — vždy (TradingView zóna může mít label na obou hranách)
                    if (y_e - EDGE_PX) > (y_s + EDGE_PX):
                        bands.append((max(y_e - EDGE_PX, y_s), y_e, cls))
                else:
                    debug_lines.append(f"  skip middle zone [{y_s}-{y_e}] (přechodová šedá)")
    debug_lines.append(f"  raw_bands={raw_bands[:10]}  bands={bands}")

    # ── 3. OCR ceny z každého pásu ───────────────────────────────────────────
    # Šíře OCR pruhu: musí zachytit celý price label "1.23573" včetně "1." prefixu.
    # 200px ≈ 5.2 % → pokrývá celý TradingView price scale (pravý okraj).
    # Anotace v grafu ("Target: 0.01467...") jsou v levém chart body → bezpečné.
    ocr_w     = max(150, int(w * 0.052))   # ~200px pro 3840px
    ocr_strip = img[:, max(0, w - ocr_w):]
    debug_lines.append(f"  ocr_w={ocr_w}")

    def _parse_price(text):
        text = text.strip().replace(' ', '')
        nums = re.findall(r'\d+', text)
        if len(nums) >= 2:
            try:
                dec = nums[-1][:5]
                v   = float(''.join(nums[:-1]) + '.' + dec)
                if v > 0.01: return v
            except: pass
        for n in re.findall(r'\d+[.,]\d+', text.replace(',', '.')):
            try:
                v = float(n)
                if v > 0.01: return v
            except: pass
        # Speciální případ: 6místné číslo bez oddělovačů = XAUUSD/index cena
        # kde OCR slil čárku tisíců + desetinnou tečku dohromady.
        # Příklad: "350400" → OCR z "3,504.00" → interpretuj jako 3504.00
        # Příklad: "344547" → OCR z "3,445.47" → interpretuj jako 3445.47
        for n in re.findall(r'(?<!\d)\d{6}(?!\d)', text):
            try:
                v = float(n[:-2] + '.' + n[-2:])
                if 200 <= v <= 9999: return v   # rozsah XAUUSD a podobných komodit
            except: pass
        for n in re.findall(r'\d{4,}', text):
            try:
                v = float(n)
                if v > 0.01: return v
            except: pass
        return None

    def ocr_price_band(y_s, y_e, tag='', color_cls='other'):
        pad = 10
        roi = ocr_strip[max(0, y_s - pad):min(h, y_e + pad), :]
        if roi.size == 0: return None
        roi_big = cv2.resize(roi, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        gray    = cv2.cvtColor(roi_big, cv2.COLOR_BGR2GRAY)

        # ── Metoda 1: HSV white-text maska ───────────────────────────────────
        # Bílý text (S≈0, V≈255) na jakémkoliv barevném pozadí (S>>0).
        # Maska zachytí POUZE bílé/šedé pixely → černý text na bílém pozadí.
        # Funguje pro cyan, žlutou, červenou i jakékoliv jiné barevné pozadí.
        try:
            hsv_roi = cv2.cvtColor(roi_big, cv2.COLOR_BGR2HSV)
            # Bílý text = nízká saturace (S<60) + vysoká hodnota (V>170)
            white_mask = (hsv_roi[:, :, 1] < 60) & (hsv_roi[:, :, 2] > 170)
            hsv_img = np.where(white_mask[:, :, np.newaxis], [0, 0, 0], [255, 255, 255]).astype(np.uint8)
            hsv_gray = cv2.cvtColor(hsv_img, cv2.COLOR_BGR2GRAY)
            txt_hsv = pytesseract.image_to_string(
                hsv_gray, config='--psm 7 -c tessedit_char_whitelist=0123456789.,'
            )
            debug_lines.append(f"    ocr_t[{tag}] HSV-white: '{txt_hsv.strip()}'")
            v = _parse_price(txt_hsv)
            if v:
                try: cv2.imwrite(f'C:\\obd\\debug_tomas_band_{tag}.png', roi_big)
                except: pass
                return v
        except Exception as _hsv_e:
            debug_lines.append(f"    ocr_t[{tag}] HSV chyba: {_hsv_e}")

        # ── Metoda 2: Klasické threshold pokusy ───────────────────────────────
        if _is_dark_bg:
            if color_cls == 'red':
                attempts = [(80,  True), (130, True), (100, True), (160, False)]
            else:  # other (cyan / yellow / obecně)
                attempts = [(165, True), (180, True), (200, True), (215, True),
                            (230, True), (130, True), (150, True), (100, True), (160, False)]
        else:
            attempts = [(160, True), (120, True), (80, True), (160, False)]

        best_val = None
        for thr_val, do_inv in attempts:
            _, thr = cv2.threshold(gray, thr_val, 255, cv2.THRESH_BINARY)
            if do_inv: thr = cv2.bitwise_not(thr)
            txt = pytesseract.image_to_string(
                thr, config='--psm 7 -c tessedit_char_whitelist=0123456789.,'
            )
            debug_lines.append(f"    ocr_t[{tag}] thr={thr_val} inv={do_inv}: '{txt.strip()}'")
            v = _parse_price(txt)
            if v:
                best_val = v
                break
        try:
            cv2.imwrite(f'C:\\obd\\debug_tomas_band_{tag}.png', roi_big)
        except: pass
        return best_val

    # Rychlý symbol lookup pro price-range filtr (symbol zatím neznáme → zkus z názvu)
    _early_sym = None
    _fname_up  = os.path.basename(image_path).upper()
    for _s in ['XAUUSD','EURUSD','GBPUSD','USDJPY','GBPJPY','USDCAD',
               'AUDUSD','NAS100','US30','US500','BTCUSD','DAX','NZDUSD','USDCHF','EURJPY','EURGBP']:
        if _s in _fname_up:
            _early_sym = _s
            break
    _pr_ranges = {
        'XAUUSD': (1400, 5500), 'EURUSD': (0.5, 2.5), 'GBPUSD': (1.0, 2.5),
        'USDJPY': (80, 200),   'GBPJPY': (100, 280),  'USDCAD': (1.0, 2.0),
        'AUDUSD': (0.5, 1.2),  'NAS100': (8000, 25000),'US30':  (20000, 50000),
        'US500':  (2000, 7000),'BTCUSD': (5000,120000),'DAX':   (8000, 22000),
    }
    _pr_lo, _pr_hi = _pr_ranges.get(_early_sym, (0.001, 999999))

    # Sbírej (y_mid, color_class, price) — přeskoč pink (= aktuální cena)
    # Pro každou (zaokrouhlenou) cenu a třídu uchovej jen jeden zástupce (nejčistší Y-střed)
    _seen_price_cls = {}   # (round_price, cls) → {'y_mid', 'price'}
    raw_detected    = []
    for y_s, y_e, cls in bands:
        if cls == 'pink':
            debug_lines.append(f"  band pink[{y_s}-{y_e}] → SKIP (aktuální cena Tomáš)")
            continue
        tag   = f"{cls}_{y_s}"
        price = ocr_price_band(y_s, y_e, tag=tag, color_cls=cls)
        y_mid = (y_s + y_e) / 2
        debug_lines.append(f"  band {cls}[{y_s}-{y_e}] y_mid={y_mid:.0f} → price={price}")
        if price and _pr_lo <= price <= _pr_hi:
            raw_detected.append({'y_mid': y_mid, 'cls': cls, 'price': price})

    # De-duplikuj: stejná cena (±0.0005) + stejná třída → ponech jen první výskyt (nejmenší y_mid)
    detected = []
    for d in sorted(raw_detected, key=lambda x: x['y_mid']):
        rk = (round(d['price'], 3), d['cls'])
        if rk not in _seen_price_cls:
            _seen_price_cls[rk] = True
            detected.append(d)

    # ── 4. Přiřazení SL / Entry / TP ─────────────────────────────────────────
    red_bands   = [d for d in detected if d['cls'] == 'red']
    other_bands = [d for d in detected if d['cls'] == 'other']
    best_sl     = None   # bude nastaven níže

    if red_bands:
        # Filtr: odstraň false-positive červené na úplném vrcholu obrazu (UI lišta)
        _no_top = [d for d in red_bands if d['y_mid'] > 200]
        if _no_top:
            red_bands = _no_top

        # Seřaď červené podle Y (nahoru→dolů)
        _red_sorted = sorted(red_bands, key=lambda d: d['y_mid'])

        # Nejspodnější červený band = SL
        best_sl = _red_sorted[-1]
        result['stoploss'] = _fmt_p(best_sl['price'])
        debug_lines.append(f"  → SL(red)={best_sl['price']}  (z {len(red_bands)} red bandů)")

        # Předposlední červený band = Entry (Tomáš označuje Entry ČERVENĚ, nad SL)
        # Platí jen pokud je cena blízko SL (v rozsahu 0.01–5 % od SL)
        if len(_red_sorted) >= 2:
            _entry_red = _red_sorted[-2]
            _sl_p_r    = best_sl['price']
            _diff_pct  = abs(_entry_red['price'] - _sl_p_r) / _sl_p_r
            if 0.0001 <= _diff_pct <= 0.08:   # 0.01 % – 8 % od SL = platný Entry
                other_bands.append(_entry_red)
                debug_lines.append(f"  → Entry candidate from red: y={_entry_red['y_mid']:.0f} price={_entry_red['price']}")

    # Filtr 'other' cen: zahoď ceny vzdálené >5× od SL — to jsou OCR garbage hodnoty
    # (např. 1800 pro GBPUSD kde SL=1.236 → 1800/1.236≈1456 → zjevně špatně)
    if result.get('stoploss'):
        try:
            _sl_p = float(result['stoploss'])
            _before = len(other_bands)
            other_bands = [d for d in other_bands
                           if _sl_p / 5.0 <= d['price'] <= _sl_p * 5.0]
            if len(other_bands) < _before:
                debug_lines.append(f"  SL-proximity filter: {_before} → {len(other_bands)} 'other' bandů")
        except Exception: pass

    # Filtr: ceny na OBOU stranách SL → Buy nebo Sell setup → zahoď menšinovou stranu
    # Příklad: SL=3289, nad=[3348,3309], pod=[3260] → Buy → zahoď 3260 (je to šum, ne entry)
    if result.get('stoploss') and len(other_bands) >= 2:
        try:
            _sl_p  = float(result['stoploss'])
            _above = [d for d in other_bands if d['price'] > _sl_p]
            _below = [d for d in other_bands if d['price'] < _sl_p]
            if _above and _below:
                if len(_above) >= len(_below):
                    other_bands = _above
                    debug_lines.append(f"  SL-side filter (Buy): ponecháno {len(_above)} nad SL, zahozeno {len(_below)} pod SL")
                else:
                    other_bands = _below
                    debug_lines.append(f"  SL-side filter (Sell): ponecháno {len(_below)} pod SL, zahozeno {len(_above)} nad SL")
        except Exception: pass

    all_non_sl = sorted(other_bands, key=lambda d: d['y_mid'])

    if len(all_non_sl) == 1:
        result['vstupni_hodnota'] = _fmt_p(all_non_sl[0]['price'])
        debug_lines.append(f"  → Entry(only)={all_non_sl[0]['price']}")
    elif len(all_non_sl) >= 2:
        if best_sl is not None:
            sl_y    = best_sl['y_mid']
            by_dist = sorted(all_non_sl, key=lambda d: abs(d['y_mid'] - sl_y))
            entry   = by_dist[0]
            tp      = by_dist[1]
        else:
            if len(all_non_sl) >= 3:
                mid   = len(all_non_sl) // 2
                entry = all_non_sl[mid]
                remaining = [d for i, d in enumerate(all_non_sl) if i != mid]
                remaining.sort(key=lambda d: abs(d['price'] - entry['price']))
                sl_band = remaining[0]
                tp      = remaining[-1]
                result['stoploss'] = _fmt_p(sl_band['price'])
                debug_lines.append(f"  3-band-no-red: SL(closest)={sl_band['price']}  TP(farthest)={tp['price']}")
            else:
                by_y = sorted(all_non_sl, key=lambda d: d['y_mid'])
                if by_y[0]['price'] > by_y[1]['price']:
                    entry = by_y[1]
                    tp    = by_y[0]
                else:
                    entry = by_y[0]
                    tp    = by_y[1]
                debug_lines.append(f"  2-band-no-red: tentative Entry={entry['price']}  TP={tp['price']}")
        result['vstupni_hodnota'] = _fmt_p(entry['price'])
        result['takeprofit']      = _fmt_p(tp['price'])
        debug_lines.append(f"  → Entry={entry['price']}  TP={tp['price']}")

    # ── 5. Symbol z názvu souboru / hlavičky ─────────────────────────────────
    _KNOWN_SYMS = ['XAUUSD','EURUSD','GBPUSD','USDJPY','GBPJPY','USDCAD',
                   'AUDUSD','NAS100','US30','US500','BTCUSD','DAX',
                   'NZDUSD','USDCHF','EURJPY','EURGBP']
    fname = os.path.basename(image_path).upper()
    for _s in _KNOWN_SYMS:
        if _s in fname:
            result['symbol'] = _s
            break
    if not result.get('symbol'):
        top_strip = img[:60, :]
        gray_top  = cv2.cvtColor(top_strip, cv2.COLOR_BGR2GRAY)
        big_top   = cv2.resize(gray_top, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, thr_top = cv2.threshold(big_top, 140, 255, cv2.THRESH_BINARY)
        thr_top    = cv2.bitwise_not(thr_top)
        top_txt    = pytesseract.image_to_string(thr_top, config='--psm 6 --oem 3').upper()
        for _s in _KNOWN_SYMS:
            if _s in top_txt:
                result['symbol'] = _s
                debug_lines.append(f"  symbol from header: {_s}")
                break

    # ── 6. Post-processing: rozsah cen ───────────────────────────────────────
    _price_ranges = {
        'XAUUSD': (1400, 5500),   'EURUSD': (0.5,  2.5),
        'GBPUSD': (1.0,  2.5),   'USDJPY': (80,   200),
        'GBPJPY': (100,  280),   'USDCAD': (1.0,  2.0),
        'AUDUSD': (0.5,  1.2),   'NAS100': (8000, 25000),
        'US30':  (20000, 50000), 'US500':  (2000,  7000),
        'BTCUSD':(5000, 120000), 'DAX':   (8000,  22000),
    }
    _sym = result.get('symbol')
    if _sym in _price_ranges:
        _lo, _hi = _price_ranges[_sym]
        for _k in ('vstupni_hodnota', 'stoploss', 'takeprofit'):
            try:
                if result.get(_k) and not (_lo <= float(result[_k]) <= _hi):
                    debug_lines.append(f"  postproc: removed {_k}={result[_k]} (out of range {_lo}-{_hi} for {_sym})")
                    result.pop(_k, None)
            except (ValueError, TypeError): pass

    # ── 7. Směr z poměru cen ─────────────────────────────────────────────────
    # Pravidlo: Buy = TP > Entry > SL  |  Sell = SL > Entry > TP
    # Záloha:   Buy = TP > SL          |  Sell = TP < SL  (stačí 2 ceny)
    try:
        entry = float(result.get('vstupni_hodnota', 0))
        sl    = float(result.get('stoploss', 0))
        tp    = float(result.get('takeprofit', 0))
        if entry and sl and tp:
            if tp > entry > sl:
                result['smer'] = 'Buy'
            elif sl > entry > tp:
                result['smer'] = 'Sell'
            else:
                # SL a TP možná proházené → zkus prohodit
                if sl > tp > entry or entry > tp > sl:
                    result['stoploss'], result['takeprofit'] = result.get('takeprofit',''), result.get('stoploss','')
                    sl, tp = tp, sl
                    debug_lines.append(f"  postproc: prohodil SL↔TP → SL={sl} TP={tp}")
                if tp > entry > sl:   result['smer'] = 'Buy'
                elif sl > entry > tp: result['smer'] = 'Sell'
                # Záloha: aspoň TP vs SL
                elif not result.get('smer') and sl and tp:
                    result['smer'] = 'Buy' if tp > sl else 'Sell'
        elif sl and tp:
            # Nemáme Entry — stačí porovnat TP vs SL
            result['smer'] = 'Buy' if tp > sl else 'Sell'
            debug_lines.append(f"  smer (TP vs SL): {'Buy' if tp > sl else 'Sell'}")
        elif entry and tp:
            result['smer'] = 'Buy' if tp > entry else 'Sell'
        elif entry and sl:
            result['smer'] = 'Buy' if entry > sl else 'Sell'
    except (ValueError, TypeError): pass

    debug_lines.append(f"FINAL_RESULT_TOMAS: {result}")
    _detail = '\n'.join(debug_lines)
    try:
        with open(r'C:\obd\time_debug_tomas.txt', 'w', encoding='utf-8') as dbf:
            dbf.write(_detail)
    except: pass
    _dbg_log('OCR-TOMAS', f"file={os.path.basename(image_path)}\n{_detail}", level='DEBUG')

    return result


def _analyze_screenshot_dispatch(image_path):
    """
    Automaticky vybere správný profil (Patrik / Tomáš) podle toho, kolik
    platných cen se podaří rozpoznat.
    • Zkusí Patrikův profil (analyze_screenshot) — spočítá nalezené ceny.
    • Pokud najde < 2 platné ceny, zkusí Tomášův profil (analyze_screenshot_tomas).
    • Vrátí výsledek profilu s více nalezenými cenami (nebo Tomášův jako zálohu).
    """
    def _count_prices(r):
        keys = ('vstupni_hodnota', 'stoploss', 'takeprofit')
        return sum(1 for k in keys if r.get(k))

    try:
        result_patrik = analyze_screenshot(image_path)
        cnt_p = _count_prices(result_patrik)
    except Exception:
        result_patrik = {}
        cnt_p = 0

    if cnt_p >= 3:
        # Patrikův profil našel všechny 3 ceny — použij ho ihned, není co řešit
        return result_patrik

    # Patrikův profil nenašel kompletní sadu — zkus také Tomáše
    try:
        result_tomas = analyze_screenshot_tomas(image_path)
        cnt_t = _count_prices(result_tomas)
    except Exception:
        result_tomas = {}
        cnt_t = 0

    # Vyber profil s VÍCE nalezenými cenami (Tomáš vyhraje při stejném počtu)
    if cnt_t >= cnt_p:
        # Tomáš vyhrál na cenách — doplň časy z Patrika (blue-box analýza)
        for _tk in ('cas_otevreni', 'cas_zavreni', 'symbol'):
            if result_patrik.get(_tk) and not result_tomas.get(_tk):
                result_tomas[_tk] = result_patrik[_tk]
        return result_tomas
    return result_patrik


# ==============================================================================
# SPRÁVCE ÚČTŮ — FTMO Challenge / Verifikace / Funded / Osobní
# ==============================================================================

ACCOUNT_TYPES   = ['Challenge', 'Verifikace', 'Funded', 'Osobní', 'Jiný']
ACCOUNT_FIRMS   = ['FTMO', 'MyForexFunds', 'FundedNext', 'The5ers', 'Topstep', 'Jiná']
ACCOUNT_STATUSES = ['Aktivní', 'Splněn', 'Propadlý', 'Archivovaný']
ACCOUNT_STATUS_COLORS = {
    'Aktivní':     ('#166534', '#86efac'),   # tmavě zelená, světle zelená text
    'Splněn':      ('#1e40af', '#93c5fd'),   # modrá
    'Propadlý':    ('#7f1d1d', '#fca5a5'),   # červená
    'Archivovaný': ('#374151', '#9ca3af'),   # šedá
}


def load_accounts():
    """Načte seznam účtů ze souboru projektu."""
    if not ACCOUNTS_FILE or not os.path.exists(ACCOUNTS_FILE):
        return []
    try:
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_accounts(accounts):
    """Uloží seznam účtů do souboru projektu."""
    if not ACCOUNTS_FILE:
        return
    try:
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Chyba", f"Nelze uložit účty:\n{e}")


# ==============================================================================
# XP SYSTÉM — bodovací engine, ranky, pravidla
# ==============================================================================

# Prahové hodnoty: (min_xp, emoji, název ranku, xp_pro_další_level)
_XP_RANKS = [
    (0,     "🌱", "Nováček",          100),
    (100,   "📊", "Začátečník",       300),
    (300,   "💼", "Junior Trader",    600),
    (600,   "⚡", "Trader",          1000),
    (1000,  "🎯", "Zkušený Trader",  2000),
    (2000,  "🏆", "Expert",          4000),
    (4000,  "💎", "Profesionál",     8000),
    (8000,  "👑", "Master Trader",  15000),
    (15000, "🔥", "Elite",          99999),
]

_XP_ACHIEVEMENTS = [
    # ── Obchody — počet ──────────────────────────────────────────────────────
    ("first_trade",   "🐣", "První krok",           "Přidal/a jsi první obchod."),
    ("trades_10",     "📈", "Začátečník",            "10 obchodů celkem."),
    ("trades_50",     "📊", "Půl stovky",            "50 obchodů celkem."),
    ("trades_100",    "💯", "Stovka",                "100 obchodů celkem."),
    ("trades_250",    "🏔️","Čtvrt tisíce",           "250 obchodů celkem."),
    ("trades_500",    "🚀", "Výzva přijata",          "500 obchodů celkem."),
    ("trades_1000",   "🌌", "Tisícovka",              "1000 obchodů celkem."),
    # ── Výhry ────────────────────────────────────────────────────────────────
    ("first_win",     "✅", "První výhra",            "První WIN obchod."),
    ("wins_10",       "🏅", "10 výher",               "10 WIN obchodů celkem."),
    ("wins_25",       "🥈", "25 výher",               "25 WIN obchodů celkem."),
    ("wins_50",       "🥇", "Padesát výher",          "50 WIN obchodů celkem."),
    ("wins_100",      "💎", "Sto výher",              "100 WIN obchodů celkem."),
    # ── Win série ────────────────────────────────────────────────────────────
    ("streak_3",      "🔥", "Série 3",                "3 výhry v řadě."),
    ("streak_5",      "⚡", "Série 5",                "5 výher v řadě."),
    ("streak_7",      "🌪️","Tornádo",                "7 výher v řadě."),
    ("streak_10",     "👑", "Neporazitelný",           "10 výher v řadě."),
    # ── Disciplína & kvalita ─────────────────────────────────────────────────
    ("big_rrr",       "🎯", "Ostrostřelec",           "Jeden obchod s RRR ≥ 5."),
    ("all_results",   "🎭", "Kompletní set",           "Máš WIN, LOSS i BE výsledek."),
    ("photos_10",     "📷", "Fotograf",               "10 obchodů se screenshotem."),
    ("notes_20",      "✍️", "Kronikář",               "20 obchodů s poznámkou."),
    ("tags_20",       "🏷️","Organizátor",             "20 obchodů s vyplněnými tagy."),
    ("symbols_5",     "🌍", "Globalista",             "Obchodoval/a jsi 5 různých symbolů."),
    ("symbols_10",    "🌐", "Světový obchodník",       "Obchodoval/a jsi 10 různých symbolů."),
    ("checklist_10",  "✔️", "Perfekcionista",          "10× kompletní checklist (100%)."),
    ("checklist_50",  "📋", "Metodický",              "50× kompletní checklist."),
    ("first_be",      "⚖️", "Nula není ztráta",       "První BE obchod."),
    ("loss_comeback", "💪", "Comeback",               "WIN obchod ihned po 3 ztrátách v řadě."),
    # ── Deník ────────────────────────────────────────────────────────────────
    ("journal_7",     "📔", "Týden zápisků",          "7 různých dní zápisu v deníku."),
    ("journal_30",    "📚", "Měsíc zápisků",          "30 různých dní zápisu v deníku."),
    ("journal_100",   "📖", "Spisovatel",             "100 různých dní zápisu v deníku."),
    # ── Backtesting stopky ────────────────────────────────────────────────────
    ("bt_1h",         "⏱️", "První seance",           "1 hodina backtestování v jednom sezení."),
    ("bt_5h",         "⏰", "Poctivec",               "5 hodin backtestování celkem."),
    ("bt_10h",        "🕰️","Drilování",              "10 hodin backtestování celkem."),
    ("bt_20h",        "🧠", "Mozková příprava",        "20 hodin backtestování celkem."),
    # ── XP milníky ───────────────────────────────────────────────────────────
    ("xp_500",        "⭐", "500 XP",                 "Nasbíral/a jsi 500 XP."),
    ("xp_2000",       "🌟", "2000 XP",                "Nasbíral/a jsi 2000 XP."),
    ("xp_5000",       "💫", "5000 XP",                "Nasbíral/a jsi 5000 XP."),
    ("xp_10000",      "🌠", "10 000 XP",              "Nasbíral/a jsi 10 000 XP."),
]

_XP_DEFAULT_CONFIG = {
    # ── Základní XP za akci ──────────────────────────────────────────────────
    "xp_backtest_trade":   10,   # přidání backtest obchodu
    "xp_real_trade":       15,   # přidání reálného obchodu
    "xp_edit_trade":        3,   # úprava existujícího obchodu
    "xp_journal_entry":     8,   # uložení záznamu v deníku
    # ── Bonusy za kvalitu obchodu ────────────────────────────────────────────
    "xp_win_bonus":        20,   # WIN výsledek
    "xp_be_bonus":          5,   # BE výsledek
    "xp_loss_with_sl":      8,   # LOSS, ale SL byl nastaven (disciplína)
    "xp_with_photo":        5,   # obchod má screenshot/foto
    "xp_with_note":         5,   # obchod má vyplněnou poznámku
    "xp_checklist_full":   12,   # checklist splněn na 100%
    "xp_bt_hour":          40,   # XP za každou dokončenou hodinu backtestování
    # ── Pravidla (bonus za dodržení) ─────────────────────────────────────────
    "rules": {
        "daily_limit": {
            "enabled": True,
            "name":    "Denní limit obchodů",
            "desc":    "Bonus za den kdy počet obchodů nepřekročí limit.",
            "xp":      25,
            "value":   3,        # max. počet obchodů za den
        },
        "weekly_limit": {
            "enabled": True,
            "name":    "Týdenní limit obchodů",
            "desc":    "Bonus za týden kdy počet obchodů nepřekročí limit.",
            "xp":      50,
            "value":   15,
        },
        "no_revenge": {
            "enabled": True,
            "name":    "Bez revenge tradingu",
            "desc":    "Bonus za obchod kdy nemáš X a více ztrát za sebou.",
            "xp":      15,
            "value":   2,        # max. po sobě jdoucí ztráty
        },
        "rrr_min": {
            "enabled": True,
            "name":    "Minimální RRR",
            "desc":    "Bonus za obchod s RRR ≥ nastavenou hodnotou.",
            "xp":      10,
            "value":   1.5,
        },
        "always_sl": {
            "enabled": True,
            "name":    "Vždy Stop Loss",
            "desc":    "Bonus za obchod kde je vyplněn Stop Loss.",
            "xp":       5,
            "value":    0,
        },
        "win_streak_3": {
            "enabled": True,
            "name":    "Série 3 výher",
            "desc":    "Bonus za dosažení série 3 výher v řadě.",
            "xp":      40,
            "value":    3,
        },
        "win_streak_5": {
            "enabled": True,
            "name":    "Série 5 výher",
            "desc":    "Bonus za dosažení série 5 výher v řadě.",
            "xp":      80,
            "value":    5,
        },
        "with_tags": {
            "enabled": True,
            "name":    "Vyplněné tagy",
            "desc":    "Bonus za obchod kde jsou vyplněny tagy.",
            "xp":       3,
            "value":    0,
        },
    }
}


def load_xp_data():
    """Načte XP data (globální napříč projekty)."""
    try:
        if os.path.exists(XP_FILE):
            with open(XP_FILE, 'r', encoding='utf-8') as _f:
                return json.load(_f)
    except Exception:
        pass
    return {"total_xp": 0, "history": [], "achievements": []}


def save_xp_data(data):
    try:
        with open(XP_FILE, 'w', encoding='utf-8') as _f:
            json.dump(data, _f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    _dbg_log('XP', f"XP uloženo: total_xp={data.get('total_xp',0)}  achievements={len(data.get('achievements',[]))}")
    # Auto-sync na Firebase po každém uložení XP
    try:
        firebase_sync_xp()
    except Exception:
        pass


# ── Firebase — online žebříček ────────────────────────────────────────────────

def load_firebase_config():
    """Načte Firebase konfiguraci (globální, mimo projekt)."""
    try:
        if os.path.exists(FIREBASE_CONFIG_FILE):
            with open(FIREBASE_CONFIG_FILE, 'r', encoding='utf-8') as _f:
                return json.load(_f)
    except Exception:
        pass
    return {"url": "https://obd1-26456-default-rtdb.firebaseio.com", "secret": "", "username": "patrik"}


def save_firebase_config(cfg):
    """Uloží Firebase konfiguraci."""
    try:
        with open(FIREBASE_CONFIG_FILE, 'w', encoding='utf-8') as _f:
            json.dump(cfg, _f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _fb_get(url, secret='', timeout=8):
    """HTTP GET na Firebase (urllib — bez externích závislostí)."""
    import urllib.request, urllib.parse
    if secret:
        url = url + ('&' if '?' in url else '?') + urllib.parse.urlencode({'auth': secret})
    with urllib.request.urlopen(url, timeout=timeout) as _r:
        return _r.status, _r.read().decode('utf-8')


def _fb_put(url, data, secret='', timeout=8):
    """HTTP PUT na Firebase (urllib — bez externích závislostí)."""
    import urllib.request, urllib.parse
    if secret:
        url = url + ('&' if '?' in url else '?') + urllib.parse.urlencode({'auth': secret})
    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    req  = urllib.request.Request(url, data=body, method='PUT')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    with urllib.request.urlopen(req, timeout=timeout) as _r:
        return _r.status


def firebase_sync_xp():
    """Odešle aktuální XP snapshot na Firebase v background threadu."""
    import threading
    def _sync():
        try:
            cfg = load_firebase_config()
            url      = cfg.get('url', '').rstrip('/')
            secret   = cfg.get('secret', '').strip()
            username = cfg.get('username', '').strip()
            if not url or not username:
                _dbg_log('FIREBASE', 'Sync přeskočen — url nebo username není nastaven', level='WARN')
                return
            xp_data = load_xp_data()
            trades  = load_data() if DATA_FILE else []
            wins    = sum(1 for t in trades if t.get('vysledek', '').lower() == 'win')
            total   = len(trades)
            winrate = round(wins / total * 100, 1) if total > 0 else 0.0
            ri = get_rank_info(xp_data.get('total_xp', 0))
            payload = {
                "xp":           xp_data.get('total_xp', 0),
                "rank":         ri['name'],
                "rank_emoji":   ri['emoji'],
                "level":        ri['rank_idx'] + 1,
                "achievements": len(xp_data.get('achievements', [])),
                "total_trades": total,
                "winrate":      winrate,
                "bt_hours":     round(xp_data.get('bt_total_minutes', 0) / 60, 1),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            _fb_put(f"{url}/users/{username}.json", payload, secret=secret)
            _dbg_log('FIREBASE', f"Sync OK → user={username} xp={payload['xp']} rank={payload['rank']} trades={total} wr={winrate}%")
        except Exception as _e:
            _dbg_log('FIREBASE', f"Sync CHYBA: {_e}", level='ERROR')
            print(f"[Firebase] sync chyba: {_e}")
    threading.Thread(target=_sync, daemon=True).start()


def open_leaderboard():
    """Otevře okno s online žebříčkem (čte data z Firebase)."""
    import threading

    win = tk.Toplevel(root)
    win.title("🏆 Online Žebříček")
    win.geometry("760x460")
    win.configure(bg=DT_PANEL)
    win.resizable(True, True)

    # Hlavička
    hdr = tk.Frame(win, bg='#0f172a', pady=12)
    hdr.pack(fill='x')
    tk.Label(hdr, text="🏆  Online Žebříček", font=('Segoe UI', 15, 'bold'),
             bg='#0f172a', fg='#fbbf24').pack(side='left', padx=20)

    # Status řádek
    status_lbl = tk.Label(win, text="Načítám data z Firebase…",
                          font=('Segoe UI', 9), bg=DT_PANEL, fg=DT_SUBTEXT)
    status_lbl.pack(anchor='w', padx=16, pady=(8, 0))

    # Treeview
    _cols = ('pos', 'username', 'xp', 'rank', 'achievements', 'trades', 'winrate', 'bt_hours', 'updated')
    _hdrs = ('#', 'Hráč', 'XP', 'Rank', '🏅 Odznaky', 'Obchodů', 'Winrate', '⏱ BT hodin', 'Aktualizace')
    _ws   = (35,  130,   80,  130,   70,            70,        75,       80,           130)

    tf = tk.Frame(win, bg=DT_PANEL)
    tf.pack(fill='both', expand=True, padx=10, pady=6)

    _sty = ttk.Style()
    _sty.configure('LB.Treeview', background='#1e293b', foreground='#e2e8f0',
                   fieldbackground='#1e293b', rowheight=28, font=('Segoe UI', 10))
    _sty.configure('LB.Treeview.Heading', background='#0f172a', foreground='#94a3b8',
                   font=('Segoe UI', 9, 'bold'))
    _sty.map('LB.Treeview', background=[('selected', '#2563eb')], foreground=[('selected', '#fff')])

    tree = ttk.Treeview(tf, columns=_cols, show='headings', style='LB.Treeview', selectmode='browse')
    vsb  = ttk.Scrollbar(tf, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    for col, hdr_text, w in zip(_cols, _hdrs, _ws):
        tree.heading(col, text=hdr_text, anchor='center')
        tree.column(col, width=w, minwidth=30, anchor='center', stretch=(col == 'rank'))
    tree.pack(side='left', fill='both', expand=True)
    vsb.pack(side='right', fill='y')

    tree.tag_configure('me',    background='#1e3a5f', foreground='#93c5fd')
    tree.tag_configure('gold',  background='#451a03', foreground='#fbbf24')
    tree.tag_configure('even',  background='#1e293b', foreground='#e2e8f0')
    tree.tag_configure('odd',   background='#0f172a', foreground='#e2e8f0')

    # Tlačítka
    bf = tk.Frame(win, bg=DT_PANEL)
    bf.pack(fill='x', padx=10, pady=(0, 10))

    cfg_lbl = tk.Label(bf, text="", font=('Segoe UI', 8), bg=DT_PANEL, fg=DT_SUBTEXT)
    cfg_lbl.pack(side='right', padx=8)

    def _load_cfg_label():
        cfg = load_firebase_config()
        u = cfg.get('username', '?')
        url_short = cfg.get('url', '').replace('https://', '').split('.')[0]
        cfg_lbl.config(text=f"db: {url_short}  ·  hráč: {u}")

    def refresh():
        status_lbl.config(text="Načítám data z Firebase…")
        for item in tree.get_children():
            tree.delete(item)
        _load_cfg_label()

        def _fetch():
            try:
                cfg    = load_firebase_config()
                url    = cfg.get('url', '').rstrip('/')
                secret = cfg.get('secret', '').strip()
                my_name = cfg.get('username', '').strip()
                if not url:
                    win.after(0, lambda: status_lbl.config(
                        text="⚠  Firebase URL není nastavena. Jdi do Nastavení → 🔥 Firebase."))
                    return
                _status, _body = _fb_get(f"{url}/users.json", secret=secret, timeout=7)
                data = json.loads(_body) if _body and _body != 'null' else None
                if not isinstance(data, dict) or not data:
                    win.after(0, lambda: status_lbl.config(
                        text="Žebříček je zatím prázdný. XP se odešle automaticky při příštím uložení obchodu."))
                    return
                users = sorted(
                    [(n, v) for n, v in data.items() if isinstance(v, dict)],
                    key=lambda x: x[1].get('xp', 0), reverse=True
                )
                def _update():
                    for item in tree.get_children():
                        tree.delete(item)
                    for pos, (name, info) in enumerate(users, 1):
                        if name == my_name:
                            tag = 'me'
                        elif pos == 1:
                            tag = 'gold'
                        else:
                            tag = 'even' if pos % 2 == 0 else 'odd'
                        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, str(pos))
                        tree.insert('', 'end', values=(
                            medal,
                            name,
                            f"{info.get('xp', 0):,}",
                            f"{info.get('rank_emoji', '')} {info.get('rank', '?')}",
                            info.get('achievements', 0),
                            info.get('total_trades', 0),
                            f"{info.get('winrate', 0):.1f}%",
                            f"{info.get('bt_hours', 0):.1f}h",
                            info.get('last_updated', '?'),
                        ), tags=(tag,))
                    status_lbl.config(text=f"✅ {len(users)} hráčů  ·  poslední aktualizace: {datetime.now().strftime('%H:%M:%S')}")
                win.after(0, _update)
            except Exception as _err:
                win.after(0, lambda: status_lbl.config(text=f"❌ Chyba připojení: {_err}"))

        threading.Thread(target=_fetch, daemon=True).start()

    def _manual_sync():
        status_lbl.config(text="Odesílám vlastní XP…")
        win.update_idletasks()
        # Sync synchronně aby jsme viděli výsledek
        try:
            cfg = load_firebase_config()
            url      = cfg.get('url', '').rstrip('/')
            secret   = cfg.get('secret', '').strip()
            username = cfg.get('username', '').strip()
            if not url or not username:
                status_lbl.config(text="⚠  Nastav Firebase URL a jméno v Nastavení → 🔥 Firebase.")
                return
            xp_data = load_xp_data()
            trades  = load_data() if DATA_FILE else []
            wins    = sum(1 for t in trades if t.get('vysledek', '').lower() == 'win')
            total   = len(trades)
            winrate = round(wins / total * 100, 1) if total > 0 else 0.0
            ri      = get_rank_info(xp_data.get('total_xp', 0))
            payload = {
                "xp":           xp_data.get('total_xp', 0),
                "rank":         ri['name'],
                "rank_emoji":   ri['emoji'],
                "level":        ri['rank_idx'] + 1,
                "achievements": len(xp_data.get('achievements', [])),
                "total_trades": total,
                "winrate":      winrate,
                "bt_hours":     round(xp_data.get('bt_total_minutes', 0) / 60, 1),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            stat = _fb_put(f"{url}/users/{username}.json", payload, secret=secret, timeout=8)
            if stat == 200:
                status_lbl.config(text=f"✅ XP odesláno!  ({username}: {payload['xp']} XP, {ri['name']})")
                win.after(800, refresh)
            else:
                status_lbl.config(text=f"❌ Firebase vrátil HTTP {stat} — zkontroluj Rules (musí být .write: true)")
                messagebox.showerror("Sync selhal",
                    f"Firebase vrátil HTTP {stat}.\n\n"
                    "Jdi do Firebase konzole → Realtime Database → Rules\n"
                    "a nastav:\n\n"
                    '{\n  "rules": {\n    ".read": true,\n    ".write": true\n  }\n}\n\n'
                    "Klikni Publish a zkus znovu.", parent=win)
        except Exception as _e:
            status_lbl.config(text=f"❌ Chyba: {_e}")
            messagebox.showerror("Chyba při odesílání",
                f"Nepodařilo se odeslat XP na Firebase:\n\n{_e}\n\n"
                "Zkontroluj URL a internetové připojení.", parent=win)

    tk.Button(bf, text="🔄  Obnovit", command=refresh,
              bg='#1d4ed8', fg='white', font=('Segoe UI', 9, 'bold'),
              relief='flat', padx=12, pady=5, cursor='hand2').pack(side='left', padx=(0, 6))
    tk.Button(bf, text="📤  Sync moje XP", command=_manual_sync,
              bg='#15803d', fg='white', font=('Segoe UI', 9),
              relief='flat', padx=12, pady=5, cursor='hand2').pack(side='left', padx=(0, 6))

    refresh()


def get_xp_config():
    """Načte konfiguraci XP systému; doplní chybějící klíče z výchozí konfigurace."""
    cfg = {}
    try:
        if os.path.exists(XP_CONFIG_FILE):
            with open(XP_CONFIG_FILE, 'r', encoding='utf-8') as _f:
                cfg = json.load(_f)
    except Exception:
        pass
    # Doplň chybějící top-level klíče
    for k, v in _XP_DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
    # Doplň chybějící pravidla
    for rk, rv in _XP_DEFAULT_CONFIG['rules'].items():
        cfg['rules'].setdefault(rk, rv)
    return cfg


def save_xp_config(cfg):
    try:
        with open(XP_CONFIG_FILE, 'w', encoding='utf-8') as _f:
            json.dump(cfg, _f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_rank_info(total_xp):
    """Vrátí dict s info o aktuálním ranku pro dané XP."""
    rank_idx = 0
    for i, (thr, _em, _nm, _nx) in enumerate(_XP_RANKS):
        if total_xp >= thr:
            rank_idx = i
    thr, emoji, name, next_thr = _XP_RANKS[rank_idx]
    is_max = (rank_idx == len(_XP_RANKS) - 1)
    progress = (total_xp - thr) / (next_thr - thr) if (next_thr > thr and not is_max) else 1.0
    return {
        'emoji':        emoji,
        'name':         name,
        'threshold':    thr,
        'next_threshold': next_thr,
        'progress':     min(max(progress, 0.0), 1.0),
        'xp_to_next':   max(0, next_thr - total_xp),
        'is_max':       is_max,
        'rank_idx':     rank_idx,
    }


def _refresh_xp_badge():
    """Aktualizuje XP badge tlačítko v toolbaru."""
    global xp_badge_btn
    if xp_badge_btn is None:
        return
    try:
        if not xp_badge_btn.winfo_exists():
            return
        data = load_xp_data()
        xp   = data.get('total_xp', 0)
        ri   = get_rank_info(xp)
        xp_badge_btn.config(text=f"{ri['emoji']} {xp} XP")
    except Exception:
        pass


def _check_xp_achievements(data, trades=None):
    """
    Zkontroluje a udělí odznaky. Vrátí seznam ID nových odznaků.
    trades — volitelný seznam obchodů pro trade-based achievementy;
             pokud None, pokusí se načíst ze souboru.
    """
    earned      = set(data.get('achievements', []))
    history     = data.get('history', [])
    total_xp    = data.get('total_xp', 0)
    bt_minutes  = data.get('bt_total_minutes', 0)
    new_badges  = []

    # ── Počítadla z XP historie ──────────────────────────────────────────────
    trade_adds      = [h for h in history if h.get('source') in ('xp_backtest_trade', 'xp_real_trade')]
    wins_hist       = [h for h in history if h.get('source') == 'xp_win_bonus']
    be_hist         = [h for h in history if h.get('source') == 'xp_be_bonus']
    journal_days    = set(h['date'][:10] for h in history if h.get('source') == 'xp_journal_entry')
    chk_fulls       = [h for h in history if h.get('source') == 'xp_checklist_full']
    photos_hist     = [h for h in history if h.get('source') == 'xp_with_photo']
    notes_hist      = [h for h in history if h.get('source') == 'xp_with_note']
    tags_hist       = [h for h in history if h.get('source') == 'rule_with_tags']

    streak_3  = any(h.get('source') == 'rule_win_streak_3' for h in history)
    streak_5  = any(h.get('source') == 'rule_win_streak_5' for h in history)
    bt_1h_done = any(h.get('source') == 'bt_hour' for h in history)

    # ── Trade-based achievementy — sáhni na soubor jen pokud nemáme data ─────
    if trades is None and DATA_FILE:
        try:
            trades = load_data()
        except Exception:
            trades = []
    trades = trades or []

    results_set     = set(t.get('vysledek', '').lower() for t in trades if t.get('vysledek'))
    all_results_ok  = {'win', 'loss', 'be'}.issubset(results_set)
    symbols_set     = set(t.get('symbol', '').strip() for t in trades if t.get('symbol', '').strip())
    big_rrr_ok      = any(
        _safe_float(t.get('rrr', 0)) >= 5.0 for t in trades
    )
    # Comeback: WIN ihned po 3+ po sobě jdoucích ztrátách
    comeback_ok = False
    consec_loss = 0
    for t in trades:
        res = t.get('vysledek', '').lower()
        if res == 'loss':
            consec_loss += 1
        elif res == 'win':
            if consec_loss >= 3:
                comeback_ok = True; break
            consec_loss = 0
        else:
            consec_loss = 0

    # Série 7 / 10 výher — projdi výsledky
    streak_7_ok = streak_10_ok = False
    cur_streak   = 0
    max_streak   = 0
    for t in trades:
        if t.get('vysledek', '').lower() == 'win':
            cur_streak += 1; max_streak = max(max_streak, cur_streak)
        elif t.get('vysledek', '').lower() in ('loss', 'be'):
            cur_streak = 0
    if max_streak >= 7:  streak_7_ok  = True
    if max_streak >= 10: streak_10_ok = True

    # ── Sestavení checků ─────────────────────────────────────────────────────
    checks = [
        # Počty obchodů
        ("first_trade",   len(trade_adds) >= 1),
        ("trades_10",     len(trade_adds) >= 10),
        ("trades_50",     len(trade_adds) >= 50),
        ("trades_100",    len(trade_adds) >= 100),
        ("trades_250",    len(trade_adds) >= 250),
        ("trades_500",    len(trade_adds) >= 500),
        ("trades_1000",   len(trade_adds) >= 1000),
        # Výhry
        ("first_win",     len(wins_hist) >= 1),
        ("wins_10",       len(wins_hist) >= 10),
        ("wins_25",       len(wins_hist) >= 25),
        ("wins_50",       len(wins_hist) >= 50),
        ("wins_100",      len(wins_hist) >= 100),
        # Série
        ("streak_3",      streak_3),
        ("streak_5",      streak_5),
        ("streak_7",      streak_7_ok),
        ("streak_10",     streak_10_ok),
        # Disciplína & kvalita
        ("big_rrr",       big_rrr_ok),
        ("all_results",   all_results_ok),
        ("photos_10",     len(photos_hist) >= 10),
        ("notes_20",      len(notes_hist) >= 20),
        ("tags_20",       len(tags_hist)  >= 20),
        ("symbols_5",     len(symbols_set) >= 5),
        ("symbols_10",    len(symbols_set) >= 10),
        ("checklist_10",  len(chk_fulls) >= 10),
        ("checklist_50",  len(chk_fulls) >= 50),
        ("first_be",      len(be_hist) >= 1),
        ("loss_comeback", comeback_ok),
        # Deník
        ("journal_7",     len(journal_days) >= 7),
        ("journal_30",    len(journal_days) >= 30),
        ("journal_100",   len(journal_days) >= 100),
        # Backtesting čas
        ("bt_1h",         bt_1h_done),
        ("bt_5h",         bt_minutes >= 300),
        ("bt_10h",        bt_minutes >= 600),
        ("bt_20h",        bt_minutes >= 1200),
        # XP milníky
        ("xp_500",        total_xp >= 500),
        ("xp_2000",       total_xp >= 2000),
        ("xp_5000",       total_xp >= 5000),
        ("xp_10000",      total_xp >= 10000),
    ]

    for aid, condition in checks:
        if condition and aid not in earned:
            earned.add(aid)
            new_badges.append(aid)

    data['achievements'] = list(earned)
    return new_badges


def _safe_float(val, default=0.0):
    """Bezpečný převod na float."""
    try:
        return float(str(val).replace(',', '.'))
    except (ValueError, TypeError):
        return default


def _award_xp_internal(source, amount, note, project):
    """Interní přidání XP — vrátí (nové_total_xp, [nové odznaky])."""
    data = load_xp_data()
    data['total_xp'] = data.get('total_xp', 0) + amount
    data.setdefault('history', []).append({
        'date':    datetime.now().strftime('%Y-%m-%d %H:%M'),
        'source':  source,
        'xp':      amount,
        'note':    note,
        'project': project,
    })
    if len(data['history']) > 2000:
        data['history'] = data['history'][-2000:]
    new_badges = _check_xp_achievements(data)
    save_xp_data(data)
    return data['total_xp'], new_badges


def award_xp(source, note='', amount=None):
    """
    Přidá XP body a zaktualizuje badge.
    source  — klíč z konfigurace (např. 'xp_real_trade') nebo interní ('rule_daily_limit')
    note    — volitelný popis (symbol, datum…)
    amount  — pokud None, načte se z konfigurace
    """
    cfg = get_xp_config()
    if amount is None:
        # Zkus top-level klíč, pak pravidla
        amount = cfg.get(source, 0)
        if amount == 0 and source.startswith('rule_'):
            rule_id = source[5:]
            amount  = cfg.get('rules', {}).get(rule_id, {}).get('xp', 0)
    if amount <= 0:
        return 0, []
    total, new_badges = _award_xp_internal(source, amount, note, current_project_name or '')
    _refresh_xp_badge()
    return total, new_badges


def _show_xp_toast(parent, text, color='#854d0e'):
    """Krátká toast notifikace v rohu okna."""
    try:
        t = tk.Toplevel(parent)
        t.overrideredirect(True)
        t.attributes('-topmost', True)
        t.configure(bg=color)
        lbl = tk.Label(t, text=text, bg=color, fg='#fef3c7',
                       font=('Segoe UI', 10, 'bold'), padx=14, pady=8)
        lbl.pack()
        # Umístění — pravý dolní roh parent okna
        parent.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  - 240
        py = parent.winfo_rooty() + parent.winfo_height() - 60
        t.geometry(f"+{max(0, px)}+{max(0, py)}")
        t.after(2500, t.destroy)
    except Exception:
        pass


def award_xp_for_trade(trade_dict, is_edit=False, parent_win=None):
    """
    Udělí XP za přidání / úpravu obchodu a zkontroluje pravidla.
    Vrátí celkový počet přidaných XP a zobrazí toast.
    """
    if not DATA_FILE:
        return
    cfg     = get_xp_config()
    mode    = current_mode or ''
    symbol  = trade_dict.get('symbol', '')
    vysl    = trade_dict.get('vysledek', '').lower()
    sl_val  = trade_dict.get('stoploss', '').strip()
    rrr_val = trade_dict.get('rrr', '').strip()
    note_val= trade_dict.get('poznamka', '').strip()
    foto_val= trade_dict.get('obrazky', '').strip()
    tags_val= trade_dict.get('tags', '').strip()
    chk_val = trade_dict.get('checklist_ratio', '')   # např. "3/4"
    date_val= trade_dict.get('cas_otevreni', '')[:10]

    earned_now = 0
    msgs = []

    if is_edit:
        amt = cfg.get('xp_edit_trade', 3)
        award_xp('xp_edit_trade', note=symbol, amount=amt)
        earned_now += amt
    else:
        # Základ za typ projektu
        if 'REAL' in mode.upper():
            base = cfg.get('xp_real_trade', 15)
            award_xp('xp_real_trade', note=symbol, amount=base)
        else:
            base = cfg.get('xp_backtest_trade', 10)
            award_xp('xp_backtest_trade', note=symbol, amount=base)
        earned_now += base
        msgs.append(f"+{base} XP za obchod")

        # Bonus: výsledek
        if vysl == 'win':
            b = cfg.get('xp_win_bonus', 20)
            award_xp('xp_win_bonus', note=symbol, amount=b)
            earned_now += b; msgs.append(f"+{b} WIN bonus")
        elif vysl == 'be':
            b = cfg.get('xp_be_bonus', 5)
            award_xp('xp_be_bonus', note=symbol, amount=b)
            earned_now += b
        elif vysl == 'loss' and sl_val:
            b = cfg.get('xp_loss_with_sl', 8)
            award_xp('xp_loss_with_sl', note=symbol, amount=b)
            earned_now += b; msgs.append(f"+{b} disciplína")

        # Bonus: foto
        if foto_val:
            b = cfg.get('xp_with_photo', 5)
            award_xp('xp_with_photo', note=symbol, amount=b)
            earned_now += b

        # Bonus: poznámka
        if note_val:
            b = cfg.get('xp_with_note', 5)
            award_xp('xp_with_note', note=symbol, amount=b)
            earned_now += b

        # Bonus: checklist 100%
        try:
            parts = chk_val.split('/') if '/' in chk_val else []
            if len(parts) == 2 and int(parts[0]) == int(parts[1]) and int(parts[1]) > 0:
                b = cfg.get('xp_checklist_full', 12)
                award_xp('xp_checklist_full', note=symbol, amount=b)
                earned_now += b; msgs.append(f"+{b} checklist 100%")
        except Exception:
            pass

        # ── Pravidla ─────────────────────────────────────────────────────────
        rules = cfg.get('rules', {})
        all_trades = []
        try:
            all_trades = load_data()
        except Exception:
            pass

        # Pravidlo: always_sl
        r_sl = rules.get('always_sl', {})
        if r_sl.get('enabled') and sl_val:
            b = r_sl.get('xp', 5)
            award_xp('rule_always_sl', note='SL nastaven', amount=b)
            earned_now += b

        # Pravidlo: rrr_min
        r_rrr = rules.get('rrr_min', {})
        if r_rrr.get('enabled'):
            try:
                rrr_f = float(rrr_val.replace(',', '.'))
                if rrr_f >= float(r_rrr.get('value', 1.5)):
                    b = r_rrr.get('xp', 10)
                    award_xp('rule_rrr_min', note=f"RRR {rrr_f:.1f}", amount=b)
                    earned_now += b; msgs.append(f"+{b} RRR≥{r_rrr['value']}")
            except Exception:
                pass

        # Pravidlo: with_tags
        r_tags = rules.get('with_tags', {})
        if r_tags.get('enabled') and tags_val:
            b = r_tags.get('xp', 3)
            award_xp('rule_with_tags', note='tagy', amount=b)
            earned_now += b

        # Pravidlo: no_revenge — počítej ztráty za sebou z historických obchodů
        r_nrv = rules.get('no_revenge', {})
        if r_nrv.get('enabled') and all_trades:
            max_consec = int(r_nrv.get('value', 2))
            recent_results = [t.get('vysledek', '').lower() for t in all_trades[-max_consec:]]
            if vysl != 'loss' or recent_results.count('loss') < max_consec:
                b = r_nrv.get('xp', 15)
                award_xp('rule_no_revenge', note='bez revenge', amount=b)
                earned_now += b

        # Pravidlo: win_streak_3 / win_streak_5 — zkontroluj sérii
        if vysl == 'win' and all_trades:
            recent_vysl = [t.get('vysledek', '').lower() for t in all_trades[-9:]] + ['win']
            # Spočítej aktuální win streak
            streak = 0
            for res in reversed(recent_vysl):
                if res == 'win': streak += 1
                else: break
            for streak_key, streak_min in [('win_streak_5', 5), ('win_streak_3', 3)]:
                r_str = rules.get(streak_key, {})
                if r_str.get('enabled') and streak == int(r_str.get('value', streak_min)):
                    b = r_str.get('xp', 40)
                    award_xp(f'rule_{streak_key}', note=f"série {streak}×", amount=b)
                    earned_now += b; msgs.append(f"+{b} série {streak}× 🔥")

        # Pravidlo: daily_limit — zkontroluj kolik obchodů bylo dnes
        r_dl = rules.get('daily_limit', {})
        if r_dl.get('enabled') and date_val and all_trades:
            count_today = sum(1 for t in all_trades
                              if t.get('cas_otevreni', '')[:10] == date_val)
            if count_today <= int(r_dl.get('value', 3)):
                b = r_dl.get('xp', 25)
                award_xp('rule_daily_limit', note=f"denní limit OK ({count_today})", amount=b)
                earned_now += b; msgs.append(f"+{b} denní limit ✓")

    # Zobraz toast
    if earned_now > 0 and parent_win:
        summary = f"⭐ +{earned_now} XP"
        if msgs:
            summary += "  ·  " + msgs[0]
        _show_xp_toast(parent_win, summary)


def open_xp_overview():
    """Otevře přehledové okno XP — rank, progress bar, historie, odznaky."""
    data  = load_xp_data()
    total = data.get('total_xp', 0)
    ri    = get_rank_info(total)
    hist  = list(reversed(data.get('history', [])))
    earned_ids = set(data.get('achievements', []))

    win = tk.Toplevel(root)
    win.title("⭐  XP Žebříček")
    win.geometry("680x600")
    win.configure(bg='#0f172a')
    win.resizable(True, True)
    win.lift(); win.focus_set()

    # ── Hlavička — rank banner ─────────────────────────────────────────────
    hdr = tk.Frame(win, bg='#1c1400', pady=18, padx=24)
    hdr.pack(fill='x')

    left = tk.Frame(hdr, bg='#1c1400')
    left.pack(side='left')
    tk.Label(left, text=ri['emoji'], font=('Segoe UI', 36), bg='#1c1400', fg='#fbbf24').pack(anchor='w')
    tk.Label(left, text=ri['name'],  font=('Segoe UI', 16, 'bold'), bg='#1c1400', fg='#fef3c7').pack(anchor='w')

    right = tk.Frame(hdr, bg='#1c1400')
    right.pack(side='left', padx=32, fill='x', expand=True)

    tk.Label(right, text=f"{total:,} XP celkem", font=('Segoe UI', 20, 'bold'),
             bg='#1c1400', fg='#fbbf24').pack(anchor='w')
    if not ri['is_max']:
        tk.Label(right, text=f"Do dalšího ranku: {ri['xp_to_next']:,} XP",
                 font=('Segoe UI', 9), bg='#1c1400', fg='#a16207').pack(anchor='w', pady=(2, 6))
        # Progress bar (canvas)
        bar_w = 340
        bar_c = tk.Canvas(right, width=bar_w, height=14, bg='#292524', highlightthickness=0, bd=0)
        bar_c.pack(anchor='w')
        fill_w = int(bar_w * ri['progress'])
        if fill_w > 0:
            bar_c.create_rectangle(0, 0, fill_w, 14, fill='#f59e0b', outline='')
        bar_c.create_text(bar_w//2, 7, text=f"{ri['progress']*100:.0f}%",
                          font=('Segoe UI', 7, 'bold'), fill='#1c1400')
    else:
        tk.Label(right, text="Maximální rank dosažen! 🔥",
                 font=('Segoe UI', 10, 'bold'), bg='#1c1400', fg='#4ade80').pack(anchor='w')

    # ── Tabs: Odznaky | Historie ────────────────────────────────────────────
    nb = ttk.Notebook(win); nb.pack(fill='both', expand=True, padx=8, pady=8)

    # Tab: Odznaky
    t_ach = ttk.Frame(nb); nb.add(t_ach, text='  🏅 Odznaky  ')
    ach_canvas = tk.Canvas(t_ach, bg='#0f172a', highlightthickness=0)
    ach_sb = ttk.Scrollbar(t_ach, command=ach_canvas.yview)
    ach_canvas.configure(yscrollcommand=ach_sb.set)
    ach_sb.pack(side='right', fill='y')
    ach_canvas.pack(fill='both', expand=True)
    ach_inner = tk.Frame(ach_canvas, bg='#0f172a')
    ach_canvas.create_window((0, 0), window=ach_inner, anchor='nw')
    ach_inner.bind('<Configure>', lambda e: ach_canvas.configure(scrollregion=ach_canvas.bbox('all')))

    ach_by_id = {a[0]: a for a in _XP_ACHIEVEMENTS}
    row_i = 0
    for aid, aemoji, aname, adesc in _XP_ACHIEVEMENTS:
        got   = aid in earned_ids
        bg    = '#1a2e1a' if got else '#1e293b'
        fg    = '#4ade80' if got else '#475569'
        ef    = '#86efac' if got else '#334155'
        row_f = tk.Frame(ach_inner, bg=bg, pady=6, padx=12)
        row_f.pack(fill='x', padx=10, pady=3)
        tk.Label(row_f, text=aemoji if got else '🔒',
                 font=('Segoe UI', 18), bg=bg, fg=ef).pack(side='left', padx=(0, 10))
        txt_f = tk.Frame(row_f, bg=bg); txt_f.pack(side='left')
        tk.Label(txt_f, text=aname, font=('Segoe UI', 10, 'bold'), bg=bg, fg=fg).pack(anchor='w')
        tk.Label(txt_f, text=adesc, font=('Segoe UI', 8),           bg=bg, fg='#64748b').pack(anchor='w')
        if got:
            tk.Label(row_f, text="✔ SPLNĚNO", font=('Segoe UI', 8, 'bold'),
                     bg=bg, fg='#4ade80').pack(side='right', padx=8)

    # Tab: Historie XP
    t_hist = ttk.Frame(nb); nb.add(t_hist, text='  📜 Historie  ')
    hist_canvas = tk.Canvas(t_hist, bg='#0f172a', highlightthickness=0)
    hist_sb = ttk.Scrollbar(t_hist, command=hist_canvas.yview)
    hist_canvas.configure(yscrollcommand=hist_sb.set)
    hist_sb.pack(side='right', fill='y')
    hist_canvas.pack(fill='both', expand=True)
    hist_inner = tk.Frame(hist_canvas, bg='#0f172a')
    hist_canvas.create_window((0, 0), window=hist_inner, anchor='nw')
    hist_inner.bind('<Configure>', lambda e: hist_canvas.configure(scrollregion=hist_canvas.bbox('all')))

    _SOURCE_LABELS = {
        'xp_backtest_trade': 'Backtest obchod',
        'xp_real_trade':     'Reálný obchod',
        'xp_edit_trade':     'Úprava obchodu',
        'xp_journal_entry':  'Zápis do deníku',
        'xp_win_bonus':      'WIN bonus',
        'xp_be_bonus':       'BE bonus',
        'xp_loss_with_sl':   'Disciplína (loss+SL)',
        'xp_with_photo':     'Screenshot',
        'xp_with_note':      'Poznámka',
        'xp_checklist_full': 'Checklist 100%',
        'rule_always_sl':    '✓ Pravidlo: SL nastaven',
        'rule_rrr_min':      '✓ Pravidlo: min. RRR',
        'rule_no_revenge':   '✓ Pravidlo: bez revenge',
        'rule_with_tags':    '✓ Pravidlo: tagy',
        'rule_daily_limit':  '✓ Pravidlo: denní limit',
        'rule_weekly_limit': '✓ Pravidlo: týdenní limit',
        'rule_win_streak_3': '🔥 Série 3 výher',
        'rule_win_streak_5': '🔥 Série 5 výher',
    }
    for i, h in enumerate(hist[:200]):
        row_bg = '#1e293b' if i % 2 == 0 else '#0f172a'
        row_f  = tk.Frame(hist_inner, bg=row_bg, pady=4, padx=10)
        row_f.pack(fill='x')
        src_lbl = _SOURCE_LABELS.get(h.get('source', ''), h.get('source', ''))
        tk.Label(row_f, text=h.get('date', '')[:16],
                 font=('Segoe UI', 8), bg=row_bg, fg='#64748b', width=14, anchor='w').pack(side='left')
        tk.Label(row_f, text=src_lbl,
                 font=('Segoe UI', 9), bg=row_bg, fg='#94a3b8', anchor='w').pack(side='left', padx=8)
        if h.get('note'):
            tk.Label(row_f, text=h['note'],
                     font=('Segoe UI', 8), bg=row_bg, fg='#475569', anchor='w').pack(side='left')
        tk.Label(row_f, text=f"+{h.get('xp', 0)} XP",
                 font=('Segoe UI', 9, 'bold'), bg=row_bg, fg='#fbbf24').pack(side='right', padx=4)
        if h.get('project'):
            tk.Label(row_f, text=h['project'],
                     font=('Segoe UI', 7), bg=row_bg, fg='#334155').pack(side='right', padx=4)


# ==============================================================================
# BACKTESTING STOPKY
# ==============================================================================

def _bt_sw_total_seconds():
    """Vrátí celkový počet sekund (elapsed + aktuální sezení)."""
    total = bt_sw_elapsed
    if bt_sw_running and bt_sw_start:
        total += int((datetime.now() - bt_sw_start).total_seconds())
    return total


def _bt_sw_play_sound():
    """Přehraje melodický zvuk v pozadí (neblokuje UI)."""
    import threading
    def _beep():
        try:
            import winsound
            # Vzestupná triáda C-E-G + fanfára
            for freq, dur in [(523, 120), (659, 120), (784, 180),
                              (784, 80),  (880, 80),  (988, 350)]:
                winsound.Beep(freq, dur)
        except Exception:
            pass
    threading.Thread(target=_beep, daemon=True).start()


def _bt_sw_show_milestone(hour_n, xp_awarded, new_badges):
    """Zobrazí nesmazatelný popup při dosažení hodiny."""
    try:
        popup = tk.Toplevel(root)
        popup.title("⏱  Backtesting milestone!")
        popup.geometry("400x220")
        popup.configure(bg='#1c0a3e')
        popup.attributes('-topmost', True)
        popup.resizable(False, False)
        popup.lift()

        tk.Label(popup, text="⏱", font=('Segoe UI', 44), bg='#1c0a3e', fg='#c084fc').pack(pady=(12, 0))
        tk.Label(popup,
                 text=f"Dokončil/a jsi hodinu č. {hour_n}!" if hour_n == 1
                      else f"Dokončil/a jsi {hour_n} hodiny backtestování!",
                 font=('Segoe UI', 13, 'bold'), bg='#1c0a3e', fg='#e9d5ff').pack()
        tk.Label(popup, text=f"+{xp_awarded} XP přidáno  ·  Čas na krátkou přestávku! 🧠",
                 font=('Segoe UI', 9), bg='#1c0a3e', fg='#a78bfa').pack(pady=4)

        if new_badges:
            badge_names = []
            badge_dict  = {a[0]: a for a in _XP_ACHIEVEMENTS}
            for bid in new_badges:
                if bid in badge_dict:
                    badge_names.append(f"{badge_dict[bid][1]} {badge_dict[bid][2]}")
            if badge_names:
                tk.Label(popup, text="Nový odznak: " + "  ·  ".join(badge_names),
                         font=('Segoe UI', 9, 'bold'), bg='#1c0a3e', fg='#4ade80').pack(pady=2)

        # Celkový čas dnes
        data = load_xp_data()
        total_min = data.get('bt_total_minutes', 0)
        tk.Label(popup, text=f"Celkový čas backtestování: {total_min // 60}h {total_min % 60}m",
                 font=('Segoe UI', 8), bg='#1c0a3e', fg='#6d28d9').pack()

        tk.Button(popup, text="  Pokračovat  ", command=popup.destroy,
                  bg='#7c3aed', fg='white', font=('Segoe UI', 10, 'bold'),
                  padx=20, pady=7, relief='flat', cursor='hand2').pack(pady=12)

        # Auto-zavření po 30 sekundách
        popup.after(30000, lambda: popup.destroy() if popup.winfo_exists() else None)
    except Exception:
        pass


def _bt_sw_tick():
    """Tickuje každou sekundu — aktualizuje label a kontroluje hodiny."""
    global bt_sw_after_id, bt_sw_xp_marks

    if not bt_sw_running:
        return

    total_sec = _bt_sw_total_seconds()
    h  = total_sec // 3600
    m  = (total_sec % 3600) // 60
    s  = total_sec % 60

    # Aktualizuj tlačítko
    if bt_sw_btn:
        try:
            if bt_sw_btn.winfo_exists():
                bt_sw_btn.config(text=f"⏱  {h:02d}:{m:02d}:{s:02d}",
                                 fg='#c084fc' if h > 0 else '#fbbf24')
        except Exception:
            pass

    # Zkontroluj hodinu — každá nová dokončená hodina = XP + zvuk + popup
    completed_hours = total_sec // 3600
    for hour_n in range(1, completed_hours + 1):
        if hour_n not in bt_sw_xp_marks:
            bt_sw_xp_marks.add(hour_n)
            try:
                cfg = get_xp_config()
                xp_amt = cfg.get('xp_bt_hour', 40)

                # Zapiš čas do XP dat
                xp_data = load_xp_data()
                xp_data['bt_total_minutes'] = xp_data.get('bt_total_minutes', 0) + 60
                save_xp_data(xp_data)

                # Udělí XP (a znovu načte data, tak je bt_total_minutes aktuální)
                _total, new_badges = award_xp('bt_hour',
                                              note=f"Sezení {hour_n}h",
                                              amount=xp_amt)
                _bt_sw_play_sound()
                root.after(200, lambda h=hour_n, x=xp_amt, b=new_badges:
                           _bt_sw_show_milestone(h, x, b))
            except Exception:
                pass

    bt_sw_after_id = root.after(1000, _bt_sw_tick)


def _bt_sw_toggle():
    """Start / Stop stopek."""
    global bt_sw_running, bt_sw_start, bt_sw_elapsed, bt_sw_after_id, bt_sw_xp_marks

    if bt_sw_running:
        # ── STOP ─────────────────────────────────────────────────────────────
        bt_sw_elapsed += int((datetime.now() - bt_sw_start).total_seconds())
        bt_sw_running  = False
        bt_sw_start    = None
        if bt_sw_after_id:
            try: root.after_cancel(bt_sw_after_id)
            except Exception: pass
            bt_sw_after_id = None

        total_sec = bt_sw_elapsed
        h = total_sec // 3600; m = (total_sec % 3600) // 60
        if bt_sw_btn:
            try:
                bt_sw_btn.config(
                    text=f"⏱  {h:02d}:{m:02d}  ▶",
                    fg='#94a3b8', bg='#1e293b')
            except Exception: pass
    else:
        # ── START ─────────────────────────────────────────────────────────────
        bt_sw_running = True
        bt_sw_start   = datetime.now()
        bt_sw_xp_marks = set(range(1, bt_sw_elapsed // 3600 + 1))  # skip hours already counted
        if bt_sw_btn:
            try:
                bt_sw_btn.config(bg='#3b0764', fg='#fbbf24')
            except Exception: pass
        _bt_sw_tick()


def _bt_sw_reset():
    """Resetuje stopky na nulu (ptá se na potvrzení)."""
    global bt_sw_running, bt_sw_start, bt_sw_elapsed, bt_sw_after_id, bt_sw_xp_marks
    if bt_sw_running or bt_sw_elapsed > 0:
        from tkinter import messagebox as _mb
        if not _mb.askyesno("Reset stopek", "Opravdu resetovat stopky na 00:00:00?"):
            return
    if bt_sw_running:
        bt_sw_running = False
        if bt_sw_after_id:
            try: root.after_cancel(bt_sw_after_id)
            except Exception: pass
            bt_sw_after_id = None
    bt_sw_elapsed = 0; bt_sw_start = None; bt_sw_xp_marks = set()
    if bt_sw_btn:
        try:
            bt_sw_btn.config(text="⏱  START", fg='#fbbf24', bg='#451a03')
        except Exception: pass


def _bt_sw_right_click(event):
    """Pravý klik na stopky → kontextové menu."""
    m = tk.Menu(root, tearoff=0, bg='#1e293b', fg='#e2e8f0',
                activebackground='#334155', activeforeground='white')
    m.add_command(label="▶  Start / ⏸ Pauza", command=_bt_sw_toggle)
    m.add_command(label="↺  Reset stopek",     command=_bt_sw_reset)
    m.add_separator()
    data = load_xp_data()
    bm   = data.get('bt_total_minutes', 0)
    m.add_command(label=f"Celkem backtestováno: {bm//60}h {bm%60}m", state='disabled')
    try: m.tk_popup(event.x_root, event.y_root)
    finally: m.grab_release()


def _fmt_vel(vel):
    """Bezpečně zformátuje číslo velikosti účtu; při chybě vrátí původní string."""
    try:
        return f"{int(float(vel)):,}" if vel else ''
    except (ValueError, TypeError):
        return str(vel)

def get_account_dropdown_values():
    """Vrátí seznam pro dropdown ve formuláři (jen aktivní + prázdná volba)."""
    accounts = load_accounts()
    result = ['— (bez účtu) —']
    for a in accounts:
        if a.get('status', 'Aktivní') == 'Aktivní':
            firma = a.get('firma', '')
            vel   = a.get('velikost', '')
            label = a.get('nazev', '?')
            if firma or vel:
                vel_fmt = _fmt_vel(vel)
                parts = []
                if firma: parts.append(firma)
                if vel_fmt: parts.append(f"{vel_fmt} {a.get('mena','USD')}")
                label += f"  [{' · '.join(parts)}]"
            result.append(label)
    return result


def get_account_short_names():
    """Vrátí {zobrazovaný_label: nazev} pro reverse lookup."""
    accounts = load_accounts()
    mapping = {}
    for a in accounts:
        firma = a.get('firma', '')
        vel   = a.get('velikost', '')
        label = a.get('nazev', '?')
        if firma or vel:
            vel_fmt = _fmt_vel(vel)
            parts = []
            if firma: parts.append(firma)
            if vel_fmt: parts.append(f"{vel_fmt} {a.get('mena','USD')}")
            label_full = label + f"  [{' · '.join(parts)}]"
        else:
            label_full = label
        mapping[label_full] = a.get('nazev', label)
    return mapping


def refresh_accounts_combo():
    """Aktualizuje hodnoty v dropdown formuláře (zavolat po změně účtů)."""
    global accounts_combo
    if accounts_combo:
        vals = get_account_dropdown_values()
        accounts_combo['values'] = vals
        if accounts_combo.get() not in vals:
            accounts_combo.set(vals[0] if vals else '')


def open_accounts_manager():
    """Otevře okno správce účtů."""
    win = tk.Toplevel(root)
    win.title("🏦 Správce účtů")
    win.geometry("1200x580")
    win.configure(bg='#0f172a')
    win.resizable(True, True)
    win.grab_set()

    # ── Hlavička ─────────────────────────────────────────────────────────────
    hdr = tk.Frame(win, bg='#0f172a', pady=12)
    hdr.pack(fill='x', padx=0)
    tk.Label(hdr, text="🏦  Správce účtů — Challenge / Verifikace / Funded",
             font=('Segoe UI', 12, 'bold'), bg='#0f172a', fg='white').pack(side='left', padx=18)
    tk.Button(hdr, text="＋  Nový účet", bg='#16a34a', fg='white',
              font=('Segoe UI', 9, 'bold'), relief='flat', padx=12, pady=5,
              cursor='hand2', command=lambda: _open_edit_dialog(None)).pack(side='right', padx=14)

    # ── Treeview tabulka ─────────────────────────────────────────────────────
    _tree_outer = tk.Frame(win, bg='#0f172a')
    _tree_outer.pack(fill='both', expand=True, padx=14, pady=(4, 0))

    # Styl Treeview — tmavý
    _sty = ttk.Style()
    _sty.theme_use('clam')
    _sty.configure('Acc.Treeview',
        background='#1e293b', fieldbackground='#1e293b',
        foreground='#e2e8f0', font=('Segoe UI', 9), rowheight=30,
        borderwidth=0)
    _sty.configure('Acc.Treeview.Heading',
        background='#0f172a', foreground='#94a3b8',
        font=('Segoe UI', 8, 'bold'), relief='flat', padding=(6, 4))
    _sty.map('Acc.Treeview',
        background=[('selected', '#334155')],
        foreground=[('selected', '#ffffff')])
    _sty.map('Acc.Treeview.Heading',
        background=[('active', '#1e293b'), ('pressed', '#1e293b')])

    _COLS = ('nazev', 'typ', 'firma', 'pocatecni', 'mena', 'status',
             'datum', 'aktualni', 'pnl_pct', 'pnl', 'poznamka')

    tree = ttk.Treeview(_tree_outer, columns=_COLS, show='headings',
                        selectmode='browse', style='Acc.Treeview')
    _vsb = ttk.Scrollbar(_tree_outer, orient='vertical',   command=tree.yview)
    _hsb = ttk.Scrollbar(_tree_outer, orient='horizontal', command=tree.xview)
    tree.configure(yscrollcommand=_vsb.set, xscrollcommand=_hsb.set)
    tree.grid(row=0, column=0, sticky='nsew')
    _vsb.grid(row=0, column=1, sticky='ns')
    _hsb.grid(row=1, column=0, sticky='ew')
    _tree_outer.grid_rowconfigure(0, weight=1)
    _tree_outer.grid_columnconfigure(0, weight=1)

    # Definice sloupců: (id, nadpis, šířka, anchor, stretch)
    _col_cfg = [
        ('nazev',     'Název účtu',      180, 'w',      True),
        ('typ',       'Typ',              90, 'center', False),
        ('firma',     'Firma',           100, 'center', False),
        ('pocatecni', 'Počáteční',        95, 'e',      False),
        ('mena',      'Měna',             55, 'center', False),
        ('status',    'Status',           90, 'center', False),
        ('datum',     'Začátek → Konec', 155, 'center', False),
        ('aktualni',  'Aktuální',         95, 'e',      False),
        ('pnl_pct',   'P&L %',            75, 'e',      False),
        ('pnl',       'P&L',             115, 'e',      False),
        ('poznamka',  'Poznámka',        130, 'w',      True),
    ]
    for cid, heading, width, anchor, stretch in _col_cfg:
        tree.heading(cid, text=heading, anchor='center')
        tree.column(cid, width=width, minwidth=40, anchor=anchor, stretch=stretch)

    # Barevné tagy dle statusu + P&L
    tree.tag_configure('aktivni',  background='#0f1e0f', foreground='#86efac')
    tree.tag_configure('funded',   background='#0a1628', foreground='#93c5fd')
    tree.tag_configure('splnen',   background='#0f1628', foreground='#7dd3fc')
    tree.tag_configure('propadly', background='#1c0a0a', foreground='#fca5a5')
    tree.tag_configure('archiv',   background='#1e293b', foreground='#64748b')
    tree.tag_configure('normal',   background='#1e293b', foreground='#e2e8f0')
    tree.tag_configure('normal2',  background='#0f172a', foreground='#e2e8f0')

    # Akční toolbar pod tabulkou
    _act_bar = tk.Frame(win, bg='#1e293b', pady=6, padx=10)
    _act_bar.pack(fill='x', padx=14, pady=(2, 0))
    _lbl_sel = tk.Label(_act_bar, text="Vyber účet v tabulce →",
                        font=('Segoe UI', 8), bg='#1e293b', fg='#475569')
    _lbl_sel.pack(side='left', padx=6)
    _btn_detail = tk.Button(_act_bar, text="📋  Detail", bg='#0f4c75', fg='white',
                            font=('Segoe UI', 8, 'bold'), relief='flat', padx=10, pady=4,
                            cursor='hand2', state='disabled')
    _btn_detail.pack(side='left', padx=3)
    _btn_edit = tk.Button(_act_bar, text="✏  Upravit", bg='#1e40af', fg='white',
                          font=('Segoe UI', 8, 'bold'), relief='flat', padx=10, pady=4,
                          cursor='hand2', state='disabled')
    _btn_edit.pack(side='left', padx=3)
    _btn_del = tk.Button(_act_bar, text="🗑  Smazat", bg='#7f1d1d', fg='white',
                         font=('Segoe UI', 8, 'bold'), relief='flat', padx=10, pady=4,
                         cursor='hand2', state='disabled')
    _btn_del.pack(side='left', padx=3)

    # ── Statistiky (summary bar) ──────────────────────────────────────────────
    stats_bar = tk.Frame(win, bg='#1e293b', pady=8, padx=14)
    stats_bar.pack(fill='x', padx=14, pady=(4, 14))

    # Sdílený seznam účtů pro akce
    _accounts_ref = []

    def _get_selected_acc():
        sel = tree.selection()
        if not sel: return None
        idx = tree.index(sel[0])
        return _accounts_ref[idx] if idx < len(_accounts_ref) else None

    def _on_tree_select(event=None):
        acc = _get_selected_acc()
        state = 'normal' if acc else 'disabled'
        _btn_detail.config(state=state)
        _btn_edit.config(state=state)
        _btn_del.config(state=state)
        if acc:
            _lbl_sel.config(text=f"Vybrán:  {acc.get('nazev','')}", fg='#94a3b8')
        else:
            _lbl_sel.config(text="Vyber účet v tabulce →", fg='#475569')

    tree.bind('<<TreeviewSelect>>', _on_tree_select)
    tree.bind('<Double-1>', lambda e: (_get_selected_acc() and _show_account_detail(_get_selected_acc())))

    _btn_detail.config(command=lambda: (_get_selected_acc() and _show_account_detail(_get_selected_acc())))
    _btn_edit.config(command=lambda: (_get_selected_acc() and _open_edit_dialog(_get_selected_acc())))
    _btn_del.config(command=lambda: (_get_selected_acc() and _delete_account(_get_selected_acc())))

    def _parse_amount(raw):
        """Robustní parsování čísla — zvládne všechny formáty:
        252285 | 252285.42 | 252285,42 | 252 285,42 | 252.285,42 | -1000 | +500"""
        import re as _re
        if raw is None: return None
        s = str(raw).strip()
        if not s: return None
        # Zachyť znaménko
        sign = -1 if s.startswith('-') else 1
        # Odstraň vše kromě číslic, tečky a čárky
        s = _re.sub(r'[^\d.,]', '', s)
        if not s: return None
        # Urči desetinný oddělovač
        last_dot   = s.rfind('.')
        last_comma = s.rfind(',')
        if last_dot > 0 and last_comma > 0:
            # Oba přítomné → poslední je desetinný
            if last_dot > last_comma:
                s = s.replace(',', '')                        # čárka=tisíce
            else:
                s = s.replace('.', '').replace(',', '.')      # tečka=tisíce
        elif last_comma > 0:
            # Jen čárka → pokud za ní jsou ≤ 2 číslice = desetinná
            if len(s) - last_comma - 1 <= 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        # Jen tečka nebo žádný oddělovač → necháme jak je
        try:
            return sign * float(s)
        except (ValueError, TypeError):
            return None

    _parse_pnl_val = _parse_amount  # alias pro zpětnou kompatibilitu

    def _rebuild_list():
        # Zapamatuj vybraný účet
        _prev_sel_id = tree.selection()[0] if tree.selection() else None
        _prev_name   = None
        if _prev_sel_id:
            try: _prev_name = _accounts_ref[tree.index(_prev_sel_id)].get('nazev')
            except: pass

        for iid in tree.get_children(): tree.delete(iid)
        _accounts_ref.clear()
        accounts = load_accounts()

        # P&L per-account
        _acc_pnl = {}
        if DATA_FILE and os.path.exists(DATA_FILE):
            try:
                for _t in load_data():
                    _aname = _t.get('ucet', '').strip()
                    _v = _parse_pnl_val(_t.get('zisk_mena', ''))
                    if _aname and _v is not None:
                        _acc_pnl[_aname] = _acc_pnl.get(_aname, 0.0) + _v
            except Exception: pass

        cur_sym = get_app_currency()
        restore_iid = None

        for i, acc in enumerate(accounts):
            _accounts_ref.append(acc)
            st       = acc.get('status', 'Aktivní')
            acc_name = acc.get('nazev', '').strip()

            vel_str  = _fmt_vel(acc.get('velikost', ''))
            ds       = acc.get('datum_start', '')
            dk       = acc.get('datum_konec', '')
            datum_str = f"{ds}  →  {dk or '…'}" if (ds or dk) else ''

            _pnl_val = _acc_pnl.get(acc_name, None)
            # Parsuj velikost — zkus surovou hodnotu, pak fallback na vel_str
            _vel_num = _parse_amount(acc.get('velikost', '')) or _parse_amount(vel_str)

            # Aktuální kapitál
            if _vel_num is not None and _pnl_val is not None:
                _akt_str = f"{_vel_num + _pnl_val:,.0f} {acc.get('mena','')}"
            elif _vel_num is not None:
                _akt_str = f"{vel_str} {acc.get('mena','')}".strip()
            else:
                _akt_str = vel_str or '—'

            # P&L %
            if _vel_num and _vel_num != 0 and _pnl_val is not None:
                _pct_str = f"{_pnl_val / _vel_num * 100:+.2f}%"
            elif _pnl_val is not None:
                _pct_str = '?'   # P&L máme, ale chybí velikost pro výpočet %
            else:
                _pct_str = '—'

            # P&L absolutní
            _pnl_str = f"{_pnl_val:+,.0f} {cur_sym}" if _pnl_val is not None else '—'

            pozn = acc.get('poznamka', '')

            values = (
                acc_name,
                acc.get('typ', ''),
                acc.get('firma', ''),
                vel_str,
                acc.get('mena', 'USD'),
                st,
                datum_str,
                _akt_str,
                _pct_str,
                _pnl_str,
                pozn,
            )

            # Tag dle statusu
            st_tag = {'Aktivní': 'aktivni', 'Funded': 'funded', 'Splněn': 'splnen',
                      'Propadlý': 'propadly', 'Archiv': 'archiv'}.get(st, 'normal' if i%2==0 else 'normal2')

            iid = tree.insert('', 'end', values=values, tags=(st_tag,))
            if _prev_name and acc_name == _prev_name:
                restore_iid = iid

        # Obnov výběr
        if restore_iid:
            tree.selection_set(restore_iid)
            tree.see(restore_iid)
        _on_tree_select()

        # Statistiky
        for w in stats_bar.winfo_children(): w.destroy()
        total    = len(accounts)
        aktivni  = sum(1 for a in accounts if a.get('status') == 'Aktivní')
        splneny  = sum(1 for a in accounts if a.get('status') == 'Splněn')
        propadly = sum(1 for a in accounts if a.get('status') == 'Propadlý')

        def _stat(lbl, val, bg, fg):
            f = tk.Frame(stats_bar, bg=bg, padx=10, pady=5)
            f.pack(side='left', padx=4)
            tk.Label(f, text=str(val), font=('Segoe UI', 13, 'bold'), bg=bg, fg=fg).pack()
            tk.Label(f, text=lbl,     font=('Segoe UI', 7),           bg=bg, fg=fg).pack()

        _stat('Celkem',    total,    '#334155', '#e2e8f0')
        _stat('Aktivní',   aktivni,  '#14532d', '#86efac')
        _stat('Splněno',   splneny,  '#1e3a5f', '#93c5fd')
        _stat('Propadlých',propadly, '#7f1d1d', '#fca5a5')

    def _open_edit_dialog(acc_or_none):
        """Dialog pro přidání nebo editaci účtu."""
        is_new = acc_or_none is None
        dlg = tk.Toplevel(win)
        dlg.title("Nový účet" if is_new else f"Upravit: {acc_or_none.get('nazev','')}")
        dlg.geometry("440x580")
        dlg.configure(bg='#0f172a')
        dlg.grab_set()

        tk.Label(dlg, text="Nový účet" if is_new else "Upravit účet",
                 font=('Segoe UI', 11, 'bold'), bg='#0f172a', fg='white').pack(pady=(14,10))

        form = tk.Frame(dlg, bg='#1e293b', padx=20, pady=16)
        form.pack(fill='x', padx=14)

        fields = {}

        def _row(label, key, widget_fn, default=''):
            r = tk.Frame(form, bg='#1e293b')
            r.pack(fill='x', pady=4)
            tk.Label(r, text=label, font=('Segoe UI', 9), bg='#1e293b', fg='#94a3b8',
                     width=14, anchor='w').pack(side='left')
            val = (acc_or_none or {}).get(key, default)
            w = widget_fn(r, val)
            w.pack(side='left', fill='x', expand=True)
            fields[key] = w

        def _entry(parent, val):
            e = tk.Entry(parent, bg='#334155', fg='white', insertbackground='white',
                         font=('Segoe UI', 10), relief='flat', bd=0)
            e.insert(0, str(val))
            return e

        def _combo(vals):
            def _make(parent, val):
                c = ttk.Combobox(parent, values=vals, state='readonly', font=('Segoe UI', 10))
                c.set(val if val in vals else vals[0])
                return c
            return _make

        _row("Název účtu:", 'nazev',       _entry,                  'Můj FTMO Challenge')
        _row("Typ:",        'typ',         _combo(ACCOUNT_TYPES),   'Challenge')
        _row("Prop firma:", 'firma',       _combo(ACCOUNT_FIRMS),   'FTMO')
        _row("Velikost ($):",'velikost',  _entry,                  '100000')
        _row("Měna:",       'mena',        _combo(['USD','EUR','GBP','CZK']), 'USD')
        _row("Status:",     'status',      _combo(ACCOUNT_STATUSES),'Aktivní')

        # Oddělovač
        tk.Frame(form, bg='#334155', height=1).pack(fill='x', pady=6)
        tk.Label(form, text="Datum začátku a konce účtu (YYYY-MM-DD):",
                 font=('Segoe UI', 8), bg='#1e293b', fg='#64748b').pack(anchor='w', pady=(0,4))

        _row("Začátek účtu:", 'datum_start', _entry, '')
        _row("Konec účtu:",   'datum_konec', _entry, '')
        tk.Label(form, text="Formát: 2025-01-15  (nebo nechej prázdné)",
                 font=('Segoe UI', 7), bg='#1e293b', fg='#475569').pack(anchor='w', pady=(0,4))

        tk.Frame(form, bg='#334155', height=1).pack(fill='x', pady=6)
        _row("Poznámka:",   'poznamka', _entry, '')

        def _save():
            data = {}
            for key, widget in fields.items():
                data[key] = widget.get()
            if not data.get('nazev', '').strip():
                messagebox.showwarning("Chyba", "Název účtu nesmí být prázdný.", parent=dlg)
                return
            if not ACCOUNTS_FILE:
                messagebox.showwarning("Žádný projekt",
                    "Nejprve otevři nebo vytvoř projekt — účty jsou vázané na projekt.",
                    parent=dlg)
                return
            os.makedirs(os.path.dirname(ACCOUNTS_FILE), exist_ok=True)
            accounts = load_accounts()
            if is_new:
                data['id'] = f"acc_{int(__import__('time').time())}"
                accounts.append(data)
            else:
                data['id'] = acc_or_none.get('id', data['nazev'])
                for i, a in enumerate(accounts):
                    if a.get('id') == data['id']:
                        accounts[i] = data; break
                else:
                    accounts.append(data)
            save_accounts(accounts)
            try: refresh_accounts_combo()
            except Exception: pass
            dlg.destroy()
            _rebuild_list()

        tk.Button(dlg, text="💾  Uložit", bg='#16a34a', fg='white',
                  font=('Segoe UI', 10, 'bold'), relief='flat', padx=18, pady=8,
                  cursor='hand2', command=_save).pack(pady=14)
        tk.Button(dlg, text="Zrušit", bg='#334155', fg='#94a3b8',
                  font=('Segoe UI', 9), relief='flat', padx=12, pady=6,
                  cursor='hand2', command=dlg.destroy).pack()

    def _show_account_detail(acc):
        """Zobrazí detail účtu — seznam připojených obchodů."""
        acc_name = acc.get('nazev', '').strip()
        cur_sym  = get_app_currency()

        dlg = tk.Toplevel(win)
        dlg.title(f"📋  Obchody — {acc_name}")
        dlg.geometry("960x640")
        dlg.configure(bg='#0f172a')

        # ── Hlavička ──────────────────────────────────────────────────────────
        hdr = tk.Frame(dlg, bg='#1e293b', padx=16, pady=12)
        hdr.pack(fill='x')
        tk.Label(hdr, text=f"🏦  {acc_name}", font=('Segoe UI', 12, 'bold'),
                 bg='#1e293b', fg='white').pack(side='left')
        st_h = acc.get('status', '')
        st_bg_h, st_fg_h = ACCOUNT_STATUS_COLORS.get(st_h, ('#374151', '#9ca3af'))
        sf_h = tk.Frame(hdr, bg=st_bg_h, padx=8, pady=3)
        sf_h.pack(side='left', padx=10)
        tk.Label(sf_h, text=st_h, font=('Segoe UI', 8, 'bold'), bg=st_bg_h, fg=st_fg_h).pack()
        info_ln = f"{acc.get('typ','')}  ·  {acc.get('firma','')}  ·  {_fmt_vel(acc.get('velikost',''))} {acc.get('mena','')}"
        tk.Label(hdr, text=info_ln, font=('Segoe UI', 9), bg='#1e293b', fg='#94a3b8').pack(side='left', padx=8)

        # ── Načtení obchodů ───────────────────────────────────────────────────
        acc_trades = []
        if DATA_FILE and os.path.exists(DATA_FILE):
            try:
                for t in load_data():
                    if t.get('ucet', '').strip() == acc_name:
                        acc_trades.append(t)
            except Exception: pass

        # Pomocná funkce pro parsování P&L hodnoty
        # Sdílí _parse_amount z vnějšího scope open_accounts_manager
        _parse_pnl = _parse_amount

        vel_num = _parse_amount(acc.get('velikost', '')) or _parse_amount(_fmt_vel(acc.get('velikost', '')))
        total_pnl = sum(v for t in acc_trades if (v := _parse_amount(t.get('zisk_mena', ''))) is not None)

        # ── KPI souhrn ────────────────────────────────────────────────────────
        sumf = tk.Frame(dlg, bg='#0f172a', pady=8, padx=10)
        sumf.pack(fill='x')

        wins_c   = sum(1 for t in acc_trades if t.get('vysledek','').lower()=='win')
        losses_c = sum(1 for t in acc_trades if t.get('vysledek','').lower()=='loss')
        bes_c    = sum(1 for t in acc_trades if t.get('vysledek','').lower()=='be')
        wr_c     = wins_c / len(acc_trades) * 100 if acc_trades else 0

        def _kpi(lbl, val, clr):
            c = tk.Frame(sumf, bg='#1e293b', padx=14, pady=8); c.pack(side='left', padx=3)
            tk.Label(c, text=val, font=('Segoe UI', 13, 'bold'), bg='#1e293b', fg=clr).pack()
            tk.Label(c, text=lbl, font=('Segoe UI', 7),          bg='#1e293b', fg='#64748b').pack()

        _kpi("OBCHODŮ",          str(len(acc_trades)),  '#e2e8f0')
        _kpi("W / L / BE",       f"{wins_c} / {losses_c} / {bes_c}", '#94a3b8')
        _kpi("WINRATE",          f"{wr_c:.1f}%",        '#4ade80' if wr_c >= 50 else '#f87171')
        pnl_clr = '#4ade80' if total_pnl >= 0 else '#f87171'
        _kpi(f"CELK. P&L ({cur_sym})", f"{total_pnl:+,.0f}", pnl_clr)
        if vel_num and vel_num != 0:
            akt = vel_num + total_pnl
            pct = total_pnl / vel_num * 100
            _kpi("AKTUÁLNÍ KAPITÁL",
                 f"{akt:,.0f} {acc.get('mena','')}",
                 '#4ade80' if akt >= vel_num else '#f87171')
            _kpi("P&L %", f"{pct:+.2f}%", '#4ade80' if pct >= 0 else '#f87171')

        # ── Záhlaví tabulky ───────────────────────────────────────────────────
        col_spec = [
            ("Datum / čas",     130), ("Symbol", 75), ("Směr", 55),
            ("Výsledek",         80), ("RRR",    50),
            (f"Zisk/Ztráta ({cur_sym})", 115), ("P&L %", 72), ("Délka", 70),
        ]
        thdr = tk.Frame(dlg, bg='#1e293b', pady=4, padx=8)
        thdr.pack(fill='x', padx=14)
        for h, w in col_spec:
            tk.Label(thdr, text=h, font=('Segoe UI', 8, 'bold'),
                     bg='#1e293b', fg='#94a3b8',
                     width=w//7, anchor='center').pack(side='left')

        # ── Scrollovatelný seznam ──────────────────────────────────────────────
        lf     = tk.Frame(dlg, bg='#0f172a'); lf.pack(fill='both', expand=True, padx=14, pady=(0, 6))
        lcanv  = tk.Canvas(lf, bg='#0f172a', highlightthickness=0)
        lscb   = ttk.Scrollbar(lf, command=lcanv.yview)
        lcanv.pack(side='left', fill='both', expand=True); lscb.pack(side='right', fill='y')
        linner = tk.Frame(lcanv, bg='#0f172a')
        lcanv.create_window((0, 0), window=linner, anchor='nw')
        linner.bind("<Configure>", lambda e: lcanv.configure(scrollregion=lcanv.bbox("all")))
        lcanv.configure(yscrollcommand=lscb.set)
        lcanv.bind("<MouseWheel>", lambda e: lcanv.yview_scroll(int(-1*(e.delta/120)), "units"))

        if not acc_trades:
            tk.Label(linner,
                     text=f"Žádné obchody přiřazené k účtu '{acc_name}'.\n\n"
                          "Při zadávání obchodu vyber tento účet v poli 'Účet'.",
                     bg='#0f172a', fg='#64748b',
                     font=('Segoe UI', 10), justify='center').pack(pady=50)
        else:
            for i, t in enumerate(reversed(acc_trades)):  # nejnovější nahoře
                res = t.get('vysledek', '').lower()
                if   res == 'win':  row_bg2 = '#0d2e1a'; res_fg = '#4ade80'; res_txt = '✔  WIN'
                elif res == 'loss': row_bg2 = '#2d0e0e'; res_fg = '#f87171'; res_txt = '✘  LOSS'
                elif res == 'be':   row_bg2 = '#2a1a07'; res_fg = '#fbbf24'; res_txt = '—  BE'
                else:               row_bg2 = '#0f172a'; res_fg = '#94a3b8'; res_txt = res or '?'

                if i % 2 == 0:
                    bg_r = row_bg2
                else:
                    # Slightly lighter shade for alternating
                    bg_r = '#1e293b' if res not in ('win','loss','be') else row_bg2

                row_w = tk.Frame(linner, bg=bg_r, pady=5); row_w.pack(fill='x')

                zm_num  = _parse_pnl(t.get('zisk_mena', ''))
                zm_str  = f"{zm_num:+,.0f}" if zm_num is not None else (t.get('zisk_mena','') or '—')
                zm_clr  = ('#4ade80' if (zm_num or 0) >= 0 else '#f87171') if zm_num is not None else '#64748b'
                pct_str = f"{zm_num/vel_num*100:+.2f}%" if (zm_num is not None and vel_num and vel_num != 0) else '—'
                pct_clr = zm_clr if zm_num is not None else '#64748b'

                cols_v = [
                    (t.get('cas_otevreni','')[:16], '#94a3b8', 130),
                    (t.get('symbol','—'),            '#e2e8f0', 75),
                    (t.get('smer','—'),              '#60a5fa', 55),
                    (res_txt,                         res_fg,   80),
                    (t.get('rrr','—'),               '#e2e8f0', 50),
                    (zm_str,                          zm_clr,  115),
                    (pct_str,                         pct_clr,  72),
                    (t.get('delka_obchodu','—'),      '#94a3b8', 70),
                ]
                for val, fg, cw in cols_v:
                    tk.Label(row_w, text=val, font=('Segoe UI', 9),
                             bg=bg_r, fg=fg,
                             width=cw//7, anchor='center').pack(side='left')

        # ── Zavřít ────────────────────────────────────────────────────────────
        tk.Button(dlg, text="Zavřít", bg='#334155', fg='#94a3b8',
                  font=('Segoe UI', 9), relief='flat', padx=16, pady=6,
                  cursor='hand2', command=dlg.destroy).pack(pady=8)

    def _delete_account(acc):
        if not messagebox.askyesno("Smazat účet",
                f"Opravdu smazat účet '{acc.get('nazev')}'?\n"
                "Obchody přiřazené k tomuto účtu zůstanou, jen bez přiřazení.",
                parent=win):
            return
        accounts = load_accounts()
        accounts = [a for a in accounts if a.get('id') != acc.get('id')]
        save_accounts(accounts)
        refresh_accounts_combo()
        _rebuild_list()

    _rebuild_list()


# ==============================================================================
# ZÁLOŽKA PERIODY — týdenní a měsíční přehled výkonnosti
# ==============================================================================

def setup_periods_tab(parent):
    """Vytvoří záložku PERIODY s týdenním a měsíčním přehledem."""
    global periods_frames, periods_account_var
    periods_frames = {}

    canv = tk.Canvas(parent, bg=DT_BG, highlightthickness=0)
    scb  = ttk.Scrollbar(parent, command=canv.yview)
    canv.pack(side='left', fill='both', expand=True)
    scb.pack(side='right', fill='y')
    sf = tk.Frame(canv, bg=DT_BG)
    canv.create_window((0, 0), window=sf, anchor='nw')
    sf.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
    canv.configure(yscrollcommand=scb.set)
    canv.bind_all("<MouseWheel>", lambda e: canv.yview_scroll(int(-1*(e.delta/120)), "units"))

    # ── Hlavička ─────────────────────────────────────────────────────────────
    hdr = tk.Frame(sf, bg='#0f172a', pady=10)
    hdr.pack(fill='x')
    tk.Label(hdr, text="📅  PŘEHLED VÝKONNOSTI — TÝDEN & MĚSÍC",
             font=('Segoe UI', 13, 'bold'), bg='#0f172a', fg='white').pack(side='left', padx=18)
    tk.Button(hdr, text="🔄  Aktualizovat", command=lambda: update_periods_analysis(),
              bg='#0ea5e9', fg='white', font=('Segoe UI', 9, 'bold'),
              relief='flat', pady=4, padx=14, cursor='hand2',
              activebackground='#0284c7').pack(side='right', padx=14)

    # ── Filtr účtu ────────────────────────────────────────────────────────────
    filter_bar = tk.Frame(sf, bg='#1e293b', pady=7, padx=14)
    filter_bar.pack(fill='x')

    tk.Label(filter_bar, text="Účet:", font=('Segoe UI', 9, 'bold'),
             bg='#1e293b', fg='#94a3b8').pack(side='left')

    periods_account_var = tk.StringVar(value='— Všechny účty —')

    def _get_acc_choices():
        choices = ['— Všechny účty —']
        try:
            accs = load_accounts()
            choices += [a.get('nazev', '').strip() for a in accs if a.get('nazev', '').strip()]
        except Exception:
            pass
        return choices

    _acc_combo = ttk.Combobox(filter_bar, textvariable=periods_account_var,
                              state='readonly', font=('Segoe UI', 9), width=28)
    _acc_combo['values'] = _get_acc_choices()
    _acc_combo.pack(side='left', padx=(6, 16))

    def _on_acc_change(event=None):
        # Obnoví seznam účtů (mohl přibýt nový) a spustí přepočet
        _acc_combo['values'] = _get_acc_choices()
        update_periods_analysis()

    _acc_combo.bind('<<ComboboxSelected>>', _on_acc_change)

    tk.Label(filter_bar, text="— filtruje data v grafech i tabulkách níže",
             font=('Segoe UI', 8), bg='#1e293b', fg='#475569').pack(side='left')

    # ── KPI row (tento týden | tento měsíc) ──────────────────────────────────
    kpi_row = tk.Frame(sf, bg=DT_BG)
    kpi_row.pack(fill='x', padx=14, pady=(12, 6))
    periods_frames['kpi_week']  = tk.Frame(kpi_row, bg='#1e293b')
    periods_frames['kpi_week'].pack(side='left', fill='both', expand=True, padx=(0, 7))
    periods_frames['kpi_month'] = tk.Frame(kpi_row, bg='#1e293b')
    periods_frames['kpi_month'].pack(side='left', fill='both', expand=True, padx=(7, 0))

    # ── Chart areas ───────────────────────────────────────────────────────────
    periods_frames['chart_week']  = tk.Frame(sf, bg='#0f172a')
    periods_frames['chart_week'].pack(fill='x', padx=14, pady=(6, 4))
    periods_frames['chart_month'] = tk.Frame(sf, bg='#0f172a')
    periods_frames['chart_month'].pack(fill='x', padx=14, pady=(4, 8))

    # ── Table areas ───────────────────────────────────────────────────────────
    periods_frames['table_week']  = tk.Frame(sf, bg='#0f172a')
    periods_frames['table_week'].pack(fill='x', padx=14, pady=(0, 6))
    periods_frames['table_month'] = tk.Frame(sf, bg='#0f172a')
    periods_frames['table_month'].pack(fill='x', padx=14, pady=(0, 20))

    update_periods_analysis()


def update_periods_analysis():
    """Načte data a překreslí celou záložku PERIODY."""
    global periods_canvases, periods_frames

    if not periods_frames:
        return

    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from collections import defaultdict

    # Uklid starých grafů
    for c in periods_canvases:
        try: c.get_tk_widget().destroy()
        except: pass
    periods_canvases.clear()

    all_trades = load_data()
    now        = datetime.now()

    # ── Filtr účtu ────────────────────────────────────────────────────────────
    _sel_acc = ''
    try:
        if periods_account_var:
            _sel_acc = periods_account_var.get().strip()
    except Exception:
        pass
    _filter_active = _sel_acc and not _sel_acc.startswith('—')
    if _filter_active:
        trades = [t for t in all_trades if t.get('ucet', '').strip() == _sel_acc]
    else:
        trades = all_trades

    # ── Parsování obchodů ────────────────────────────────────────────────────
    parsed = []
    for t in trades:
        raw_day = t.get('den_tydne', '').capitalize()
        if raw_day in ('Sobota', 'Neděle'):
            continue
        res = t.get('vysledek', '').lower()
        if not res:
            continue
        try:
            dt = datetime.strptime(t['cas_otevreni'], "%Y-%m-%d %H:%M")
        except:
            continue
        try:
            rrr = float(str(t.get('rrr', 1)).replace(',', '.'))
        except:
            rrr = 1.0
        r_val = rrr if res == 'win' else (-1.0 if res == 'loss' else 0.0)
        iso = dt.isocalendar()
        parsed.append({
            'dt': dt, 'res': res, 'rrr': rrr, 'r': r_val,
            'week':  f"{iso[0]}-W{iso[1]:02d}",
            'month': f"{dt.year}-{dt.month:02d}",
        })

    # Aktuální periody
    iso_now    = now.isocalendar()
    cur_week   = f"{iso_now[0]}-W{iso_now[1]:02d}"
    cur_month  = f"{now.year}-{now.month:02d}"

    # Agregace
    def agg_by(key):
        d = defaultdict(lambda: {'count':0,'wins':0,'losses':0,'be':0,'r':0.0,'gross_p':0.0,'gross_l':0.0})
        for p in parsed:
            k = p[key]
            d[k]['count']  += 1
            d[k]['r']      += p['r']
            if p['res'] == 'win':
                d[k]['wins']    += 1
                d[k]['gross_p'] += p['rrr']
            elif p['res'] == 'loss':
                d[k]['losses']  += 1
                d[k]['gross_l'] += 1.0
            else:
                d[k]['be'] += 1
        return d

    week_data  = agg_by('week')
    month_data = agg_by('month')

    def wr_pct(s):
        d = s['wins'] + s['losses']
        return s['wins'] / d * 100 if d > 0 else 0.0

    def pf_str(s):
        if s['gross_l'] == 0:
            return '∞' if s['gross_p'] > 0 else '—'
        return f"{s['gross_p']/s['gross_l']:.2f}"

    # Posledních N period (+ ujistit se že aktuální je vždy přítomná)
    def last_n(data_dict, cur_key, n):
        keys = sorted(data_dict.keys())
        if cur_key not in keys:
            keys.append(cur_key)
            data_dict[cur_key]  # touch → create default
        # keep last n, always include cur
        if cur_key in keys[-n:]:
            return keys[-n:]
        return keys[-(n-1):] + [cur_key]

    weeks_keys  = last_n(week_data,  cur_week,  10)
    months_keys = last_n(month_data, cur_month, 13)

    # ── Popisky period ────────────────────────────────────────────────────────
    MESICE = ['','Led','Úno','Bře','Dub','Kvě','Čvn','Čvc','Srp','Zář','Říj','Lis','Pro']

    def week_lbl(k):
        try:
            y, w = k.split('-W')
            mon = datetime.strptime(f"{y}-W{w}-1", "%G-W%V-%u")
            fri = mon + __import__('datetime').timedelta(days=4)
            return f"{mon.day}.{mon.month}–{fri.day}.{fri.month}"
        except:
            return k

    def week_lbl_full(k):
        try:
            y, w = k.split('-W')
            mon = datetime.strptime(f"{y}-W{w}-1", "%G-W%V-%u")
            fri = mon + __import__('datetime').timedelta(days=4)
            return f"{mon.day}.{mon.month} – {fri.day}.{fri.month}.{fri.year}"
        except:
            return k

    def month_lbl(k):
        try:
            y, m = k.split('-')
            return f"{MESICE[int(m)]} {y}"
        except:
            return k

    # ── KPI karty ────────────────────────────────────────────────────────────
    def build_kpi(frame, title, subtitle, s):
        for w in frame.winfo_children(): w.destroy()

        wr  = wr_pct(s)
        r   = s['r']
        pf  = pf_str(s)
        r_color  = '#22c55e' if r > 0 else ('#ef4444' if r < 0 else '#94a3b8')
        wr_bg    = '#14532d' if wr >= 55 else ('#1e40af' if wr >= 45 else '#7f1d1d')

        # Nadpis sekce
        th = tk.Frame(frame, bg='#1e293b', pady=7)
        th.pack(fill='x')
        tk.Label(th, text=title,    font=('Segoe UI', 10, 'bold'), bg='#1e293b', fg='white').pack(side='left', padx=12)
        tk.Label(th, text=subtitle, font=('Segoe UI', 8),          bg='#1e293b', fg='#64748b').pack(side='right', padx=12)

        # Row karet
        row = tk.Frame(frame, bg='#1e293b', padx=10, pady=10)
        row.pack(fill='x')

        card_data = [
            ("Obchodů",  str(s['count']),        '#334155',  '#e2e8f0'),
            ("Win Rate", f"{wr:.0f}%",            wr_bg,      '#ffffff'),
            ("Celkem R", f"{r:+.2f}R",            '#1c3d2e' if r > 0 else '#3d1c1c', r_color),
            ("✓ Win",    str(s['wins']),           '#14532d',  '#86efac'),
            ("✗ Loss",   str(s['losses']),         '#7f1d1d',  '#fca5a5'),
            ("PF",       pf,                       '#1e3a5f',  '#93c5fd'),
        ]
        for label, val, bg, fg in card_data:
            c = tk.Frame(row, bg=bg, padx=12, pady=8)
            c.pack(side='left', expand=True, fill='both', padx=3)
            tk.Label(c, text=val,   font=('Segoe UI', 16, 'bold'), bg=bg, fg=fg).pack()
            tk.Label(c, text=label, font=('Segoe UI', 7),           bg=bg, fg='#94a3b8').pack()

    wk_s = week_data.get(cur_week,  {'count':0,'wins':0,'losses':0,'be':0,'r':0.0,'gross_p':0.0,'gross_l':0.0})
    mo_s = month_data.get(cur_month,{'count':0,'wins':0,'losses':0,'be':0,'r':0.0,'gross_p':0.0,'gross_l':0.0})

    _acc_suffix = f"  ·  {_sel_acc}" if _filter_active else "  ·  všechny účty"
    build_kpi(periods_frames['kpi_week'],  "📆  TENTO TÝDEN",  week_lbl_full(cur_week) + _acc_suffix, wk_s)
    build_kpi(periods_frames['kpi_month'], "🗓️  TENTO MĚSÍC", month_lbl(cur_month)    + _acc_suffix, mo_s)

    # ── Bar chart helper ──────────────────────────────────────────────────────
    def build_chart(fkey, title, keys, data_dict, lbl_fn, cur_key):
        frame = periods_frames[fkey]
        for w in frame.winfo_children(): w.destroy()

        r_vals  = [data_dict[k]['r']     for k in keys]
        wr_vals = [wr_pct(data_dict[k])  for k in keys]
        labels  = [lbl_fn(k)             for k in keys]
        colors  = []
        for k, v in zip(keys, r_vals):
            if k == cur_key:   colors.append('#60a5fa')   # modrá = aktuální týden/měsíc
            elif v > 0:        colors.append('#22c55e')   # zelená = zisk
            elif v < 0:        colors.append('#ef4444')   # červená = ztráta
            else:              colors.append('#475569')   # šedá = nula

        fig = Figure(figsize=(11, 2.8), dpi=90)
        fig.patch.set_facecolor('#0f172a')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f172a')

        bars = ax.bar(range(len(keys)), r_vals, color=colors, width=0.55, zorder=3)
        # Hodnoty nad/pod sloupci
        y_range = max(r_vals) - min(r_vals) if r_vals else 1
        offset  = max(0.08, y_range * 0.03)
        for bar, v in zip(bars, r_vals):
            if v == 0: continue
            ax.text(bar.get_x() + bar.get_width()/2.,
                    v + (offset if v > 0 else -offset),
                    f'{v:+.1f}R', ha='center',
                    va='bottom' if v > 0 else 'top',
                    fontsize=7, color='white', fontweight='bold')

        ax.axhline(0, color='#334155', linewidth=0.9, zorder=2)
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(labels, rotation=25, ha='right', fontsize=7.5, color='#94a3b8')
        ax.tick_params(axis='y', colors='#64748b', labelsize=7.5)
        for spine in ax.spines.values(): spine.set_color('#1e293b')
        ax.set_ylabel('R', color='#64748b', fontsize=8)
        ax.grid(axis='y', color='#1e293b', linewidth=0.8, zorder=1)
        ax.set_title(title, color='#94a3b8', fontsize=9, fontweight='bold', pad=7)
        fig.tight_layout(pad=1.0)

        fc = FigureCanvasTkAgg(fig, master=frame)
        fc.draw()
        fc.get_tk_widget().pack(fill='x', padx=0, pady=0)
        periods_canvases.append(fc)

    _chart_acc_tag = f"  [{_sel_acc}]" if _filter_active else ""
    build_chart('chart_week',  f'Výkonnost po TÝDNECH{_chart_acc_tag}  (modrá = aktuální)',
                weeks_keys,  week_data,  week_lbl,  cur_week)
    build_chart('chart_month', f'Výkonnost po MĚSÍCÍCH{_chart_acc_tag}  (modrá = aktuální)',
                months_keys, month_data, month_lbl, cur_month)

    # ── Tabulka helper ────────────────────────────────────────────────────────
    def build_table(fkey, title, keys, data_dict, lbl_fn, cur_key):
        frame = periods_frames[fkey]
        for w in frame.winfo_children(): w.destroy()

        # Nadpis
        th = tk.Frame(frame, bg='#1e293b', pady=7)
        th.pack(fill='x')
        tk.Label(th, text=title, font=('Segoe UI', 10, 'bold'),
                 bg='#1e293b', fg='white').pack(side='left', padx=12)

        # Záhlaví sloupců
        COL = [('Období',14),('Obchody',7),('Win',5),('Loss',5),
               ('BE',4),('Win %',7),('Celkem R',9),('PF',6)]
        hrow = tk.Frame(frame, bg='#334155', pady=5)
        hrow.pack(fill='x', padx=0)
        for cname, cw in COL:
            tk.Label(hrow, text=cname, font=('Segoe UI', 8, 'bold'),
                     bg='#334155', fg='#94a3b8', width=cw, anchor='center').pack(side='left')

        # Řádky dat (nejnovější nahoře)
        for i, k in enumerate(reversed(keys)):
            s   = data_dict[k]
            cur = (k == cur_key)
            row_bg = '#1e3a5f' if cur else ('#1e293b' if i%2==0 else '#0f172a')
            row = tk.Frame(frame, bg=row_bg, pady=4)
            row.pack(fill='x')

            wr   = wr_pct(s)
            r    = s['r']
            pf   = pf_str(s)
            r_fg = '#22c55e' if r > 0 else ('#ef4444' if r < 0 else '#94a3b8')
            wr_fg= '#86efac' if wr >= 55 else ('#93c5fd' if wr >= 45 else '#fca5a5')

            cells = [
                (lbl_fn(k) + (' ◀' if cur else ''), '#60a5fa' if cur else '#e2e8f0', 14),
                (str(s['count']),    '#e2e8f0', 7),
                (str(s['wins']),     '#86efac', 5),
                (str(s['losses']),   '#fca5a5', 5),
                (str(s['be']),       '#94a3b8', 4),
                (f"{wr:.0f}%",       wr_fg,     7),
                (f"{r:+.2f}R",       r_fg,      9),
                (pf,                 '#93c5fd', 6),
            ]
            for val, fg, cw in cells:
                tk.Label(row, text=val, font=('Segoe UI', 9),
                         bg=row_bg, fg=fg, width=cw, anchor='center').pack(side='left')

    build_table('table_week',  '🗒️  DETAILNÍ PŘEHLED PO TÝDNECH',
                weeks_keys,  week_data,  week_lbl_full, cur_week)
    build_table('table_month', '🗒️  DETAILNÍ PŘEHLED PO MĚSÍCÍCH',
                months_keys, month_data, month_lbl,     cur_month)


def show_screenshot_dialog(prefill_callback):
    """Otevře dialog pro výběr screenshotu, analyzuje ho a zavolá callback s výsledky."""
    path = filedialog.askopenfilename(
        title="Vyber TradingView screenshot",
        filetypes=[("Obrázky", "*.png *.jpg *.jpeg *.bmp *.webp"), ("Vše", "*.*")]
    )
    if not path:
        return

    try:
        result = _analyze_screenshot_dispatch(path)
    except Exception as e:
        messagebox.showerror("Chyba analýzy", f"Nepodařilo se zpracovat screenshot:\n{e}")
        return

    if not result:
        messagebox.showwarning("Nic nenalezeno",
            "Na screenshotu nebyly nalezeny žádné cenové labely.\n"
            "Ujisti se, že screenshot je z TradingView s viditelnými SL/TP linkami.")
        return

    # Potvrzovací dialog
    win = tk.Toplevel()
    win.title("Detekované hodnoty ze screenshotu")
    win.geometry("460x460")
    win.configure(bg=DT_PANEL)
    win.grab_set()
    win.resizable(False, False)

    tk.Label(win, text="📊 Nalezené hodnoty", font=('Segoe UI',13,'bold'),
             bg=DT_PANEL, fg=DT_TEXT).pack(pady=(18,4))
    tk.Label(win, text="Zkontroluj a uprav, pak klikni POUŽÍT",
             font=('Segoe UI',9), bg=DT_PANEL, fg=DT_SUBTEXT).pack(pady=(0,14))

    fields = [
        ('symbol',         'Symbol:',          '#1e293b'),
        ('vstupni_hodnota','Entry cena:',       '#1d4ed8'),
        ('stoploss',       'Stop Loss:',        '#b91c1c'),
        ('takeprofit',     'Take Profit:',      '#15803d'),
        ('cas_otevreni',   'Čas otevření:',     '#1e293b'),
        ('cas_zavreni',    'Čas uzavření:',     '#1e293b'),
        ('timeframe_vstup','Timeframe:',        '#1e293b'),
    ]
    vars_ = {}
    for key, label, color in fields:
        row = tk.Frame(win, bg=DT_PANEL); row.pack(fill='x', padx=24, pady=2)
        tk.Label(row, text=label, width=15, anchor='w',
                 font=('Segoe UI',9,'bold'), bg=DT_PANEL, fg=color).pack(side='left')
        v = tk.StringVar(value=result.get(key, ''))
        tk.Entry(row, textvariable=v, font=('Segoe UI',10),
                 bg=DT_ENTRY, fg=DT_TEXT, relief='solid', bd=1,
                 insertbackground=DT_ACCENT).pack(side='left', fill='x', expand=True)
        vars_[key] = v

    def apply():
        out = {k: v.get().strip() for k, v in vars_.items()}
        win.destroy()
        prefill_callback(out)

    tk.Button(win, text="✅  POUŽÍT — VYPLNIT FORMULÁŘ", bg='#27ae60', fg='white',
              font=('Segoe UI',11,'bold'), pady=10, relief='flat', cursor='hand2',
              activebackground='#219a52', activeforeground='white',
              command=apply).pack(fill='x', padx=24, pady=(14,4))
    tk.Button(win, text="Zrušit", bg=DT_SURFACE, fg=DT_SUBTEXT,
              font=('Segoe UI',9), relief='flat',
              command=win.destroy).pack()


# ==============================================================================
# ==============================================================================
# TRADINGVIEW TAB
# ==============================================================================

def setup_tradingview_tab(parent):
    """Záložka s TradingView embedded přes Edge app-mode + Win32 SetParent + rychlý zápis."""
    import subprocess, threading, ctypes, ctypes.wintypes as wt
    import win32gui, win32process, win32con

    edge_exe = get_browser_exe()

    edge_proc = [None]   # subprocess handle
    edge_hwnd = [None]   # HWND embedded okna

    main = tk.Frame(parent, bg=DT_BG)
    main.pack(fill='both', expand=True)

    # ── Pravý panel – Quick Save (pevná šířka) ───────────────────────────────
    qs_outer = tk.Frame(main, width=270, bg=DT_PANEL, relief='flat')
    qs_outer.pack(side='right', fill='y')
    qs_outer.pack_propagate(False)

    # ── Levá část – embedded Edge ────────────────────────────────────────────
    left = tk.Frame(main, bg='#000000')
    left.pack(side='left', fill='both', expand=True)

    tv_sym_var = tk.StringVar(value="EURUSD")
    current_tf  = tk.StringVar(value="15")

    # Ovládací lišta
    ctrl = tk.Frame(left, bg=DT_SURFACE, pady=5, padx=10)
    ctrl.pack(fill='x')

    tk.Label(ctrl, text="Symbol:", bg=DT_SURFACE, fg=DT_TEXT,
             font=('Segoe UI',9)).pack(side='left')
    sym_cb = ttk.Combobox(ctrl, textvariable=tv_sym_var, values=PAIRS, width=11)
    sym_cb.pack(side='left', padx=(4,10))

    status_lbl = tk.Label(ctrl, text="● Nenačteno", bg=DT_SURFACE, fg='#94a3b8',
                          font=('Segoe UI',8))
    status_lbl.pack(side='right', padx=8)

    def set_status(txt, color='#94a3b8'):
        try: status_lbl.config(text=txt, fg=color)
        except: pass

    def get_url(tf=None):
        sym = tv_sym_var.get().strip() or 'EURUSD'
        t   = tf or current_tf.get() or '15'
        current_tf.set(t)
        return f"https://www.tradingview.com/chart/?symbol={sym}&interval={t}&theme=light"

    def resize_edge(*_):
        if not edge_hwnd[0]: return
        try:
            w = left.winfo_width()
            h = left.winfo_height() - ctrl.winfo_height()
            if w > 10 and h > 10:
                ctypes.windll.user32.MoveWindow(edge_hwnd[0], 0, 0, w, h, True)
        except: pass

    def embed_edge(url):
        """Spustí Edge v app-mode a vloží okno do left frame."""
        # Zavři předchozí instanci
        if edge_proc[0]:
            try: edge_proc[0].terminate()
            except: pass
            edge_hwnd[0] = None

        left.after(0, lambda: set_status("● Spouštím Edge...", '#f59e0b'))

        frame_hwnd = left.winfo_id()
        w = max(left.winfo_width(),  800)
        h = max(left.winfo_height() - ctrl.winfo_height(), 600)

        proc = subprocess.Popen([
            edge_exe,
            f'--app={url}',
            f'--window-size={w},{h}',
            '--no-first-run',
            '--disable-features=TranslateUI',
        ])
        edge_proc[0] = proc

        # Počkej až Edge vytvoří okno (max 8s)
        hwnd = None
        for _ in range(40):
            threading.Event().wait(0.2)
            found = []

            def cb(h, _):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(h)
                    if pid == proc.pid and win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h):
                        found.append(h)
                except: pass
                return True

            win32gui.EnumWindows(cb, None)
            if found:
                hwnd = found[0]; break

        if not hwnd:
            left.after(0, lambda: set_status("● Edge nenalezen", '#ef4444'))
            return

        edge_hwnd[0] = hwnd

        # Odeber title bar a border
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                   win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_SYSMENU)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        # Vlož do tkinter frame
        ctypes.windll.user32.SetParent(hwnd, frame_hwnd)
        ctypes.windll.user32.MoveWindow(hwnd, 0, ctrl.winfo_height(), w, h, True)

        left.after(0, lambda: [set_status("● TradingView", '#22c55e'), resize_edge()])

    def load_chart(tf=None):
        url = get_url(tf)
        qs_sym_var.set(tv_sym_var.get().strip() or 'EURUSD')
        threading.Thread(target=embed_edge, args=(url,), daemon=True).start()

    # TF tlačítka
    tk.Label(ctrl, text="TF:", bg=DT_SURFACE, fg=DT_SUBTEXT,
             font=('Segoe UI',8)).pack(side='left')
    for lbl_txt, tf_val in [("1m","1"),("5m","5"),("15m","15"),("1h","60"),("4h","240"),("1D","D")]:
        tk.Button(ctrl, text=lbl_txt, bg=DT_BTN, fg='white',
                  font=('Segoe UI',8,'bold'), padx=7, pady=3,
                  command=lambda t=tf_val: load_chart(t)).pack(side='left', padx=1)

    sym_cb.bind('<<ComboboxSelected>>', lambda e: load_chart())
    sym_cb.bind('<Return>',             lambda e: load_chart())

    # Resize listener
    left.bind('<Configure>', resize_edge)

    # Plocha pro Edge
    web_area = tk.Frame(left, bg='#1a1a2e')
    web_area.pack(fill='both', expand=True)

    # Počáteční načtení
    left.after(400, lambda: load_chart())

    # Cleanup při zavření okna
    def on_close():
        if edge_proc[0]:
            try: edge_proc[0].terminate()
            except: pass
    parent.winfo_toplevel().bind('<Destroy>', lambda e: on_close(), add='+')

    # ── Quick Save Panel ─────────────────────────────────────────────────────
    # Header
    tk.Label(qs_outer, text="⚡  RYCHLÝ ZÁPIS", bg=DT_BTN, fg='white',
             font=('Segoe UI',11,'bold'), pady=10).pack(fill='x')

    form = tk.Frame(qs_outer, bg=DT_PANEL, padx=14, pady=8)
    form.pack(fill='both', expand=True)

    def lbl(txt, pady=(6,1)):
        tk.Label(form, text=txt, bg=DT_PANEL, fg=DT_SUBTEXT,
                 font=('Segoe UI',8), anchor='w').pack(fill='x', pady=pady)

    # Symbol
    qs_sym_var = tk.StringVar(value="EURUSD")
    lbl("Symbol:")
    ttk.Combobox(form, textvariable=qs_sym_var, values=PAIRS, width=24).pack(fill='x')

    # Směr
    lbl("Směr:", (10,2))
    dir_f = tk.Frame(form, bg=DT_PANEL); dir_f.pack(fill='x')
    qs_dir_var = tk.StringVar(value="Buy")
    buy_btn  = tk.Button(dir_f, text="▲  BUY",  bg='#16a34a', fg='white', font=('Segoe UI',10,'bold'), pady=7)
    sell_btn = tk.Button(dir_f, text="▼  SELL", bg=DT_SURFACE, fg=DT_TEXT, font=('Segoe UI',10,'bold'), pady=7)

    def set_dir(v):
        qs_dir_var.set(v)
        buy_btn.config( bg='#16a34a' if v=='Buy'  else DT_SURFACE, fg='white' if v=='Buy'  else DT_TEXT)
        sell_btn.config(bg='#dc2626' if v=='Sell' else DT_SURFACE, fg='white' if v=='Sell' else DT_TEXT)

    buy_btn.config(command=lambda: set_dir('Buy'));   buy_btn.pack(side='left', expand=True, fill='x', padx=(0,2))
    sell_btn.config(command=lambda: set_dir('Sell')); sell_btn.pack(side='left', expand=True, fill='x')

    # Výsledek
    lbl("Výsledek:", (10,2))
    res_f = tk.Frame(form, bg=DT_PANEL); res_f.pack(fill='x')
    qs_res_var = tk.StringVar(value="")
    res_btns = {}

    def set_res(v):
        qs_res_var.set(v)
        cfg = {'Win':('#16a34a','white'), 'Loss':('#dc2626','white'), 'BE':('#ca8a04','white')}
        for rv, btn in res_btns.items():
            bg, fg = cfg[rv] if rv == v else (DT_SURFACE, DT_TEXT)
            btn.config(bg=bg, fg=fg)

    for rv, txt in [('Win','✓ WIN'), ('Loss','✗ LOSS'), ('BE','= BE')]:
        b = tk.Button(res_f, text=txt, bg=DT_SURFACE, fg=DT_TEXT,
                      font=('Segoe UI',9,'bold'), pady=6, command=lambda r=rv: set_res(r))
        b.pack(side='left', expand=True, fill='x', padx=1)
        res_btns[rv] = b

    # Čas vstupu
    qs_open_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
    lbl("Čas vstupu:")
    open_row = tk.Frame(form, bg=DT_PANEL); open_row.pack(fill='x')
    tk.Entry(open_row, textvariable=qs_open_var, bg=DT_ENTRY, fg=DT_TEXT,
             relief='solid', bd=1, insertbackground=DT_ACCENT).pack(side='left', fill='x', expand=True)
    tk.Button(open_row, text="⏱", bg=DT_SURFACE, fg=DT_TEXT, font=('Segoe UI',9), padx=4,
              command=lambda: qs_open_var.set(datetime.now().strftime("%Y-%m-%d %H:%M"))).pack(side='left', padx=(3,0))

    # Čas výstupu
    qs_close_var = tk.StringVar(value="")
    lbl("Čas výstupu:")
    close_row = tk.Frame(form, bg=DT_PANEL); close_row.pack(fill='x')
    tk.Entry(close_row, textvariable=qs_close_var, bg=DT_ENTRY, fg=DT_TEXT,
             relief='solid', bd=1, insertbackground=DT_ACCENT).pack(side='left', fill='x', expand=True)
    tk.Button(close_row, text="⏱", bg=DT_SURFACE, fg=DT_TEXT, font=('Segoe UI',9), padx=4,
              command=lambda: qs_close_var.set(datetime.now().strftime("%Y-%m-%d %H:%M"))).pack(side='left', padx=(3,0))

    # RRR
    qs_rrr_var = tk.StringVar()
    lbl("RRR (např. 2.5):")
    tk.Entry(form, textvariable=qs_rrr_var, bg=DT_ENTRY, fg=DT_TEXT,
             relief='solid', bd=1, insertbackground=DT_ACCENT).pack(fill='x')

    # Setup
    qs_setup_var = tk.StringVar()
    lbl("Setup:")
    ttk.Combobox(form, textvariable=qs_setup_var, values=FIBO_OPTIONS, width=24).pack(fill='x')

    # Session
    qs_session_var = tk.StringVar()
    lbl("Seance:")
    ttk.Combobox(form, textvariable=qs_session_var, values=SESSIONS_LIST, width=24).pack(fill='x')

    # Poznámka
    qs_note_var = tk.StringVar()
    lbl("Poznámka:")
    tk.Entry(form, textvariable=qs_note_var, bg=DT_ENTRY, fg=DT_TEXT,
             relief='solid', bd=1, insertbackground=DT_ACCENT).pack(fill='x')

    # ── Save logic ────────────────────────────────────────────────────────────
    def quick_save():
        if not DATA_FILE:
            messagebox.showerror("Chyba", "Nejdřív otevři projekt!"); return
        if not qs_res_var.get():
            messagebox.showwarning("Chyba", "Vyber výsledek (Win / Loss / BE)!"); return

        open_t  = qs_open_var.get().strip()
        close_t = qs_close_var.get().strip()

        # Den v týdnu
        den = ""
        try:
            dt_o = datetime.strptime(open_t, "%Y-%m-%d %H:%M")
            _cz2 = ["Pondělí","Úterý","Středa","Čtvrtek","Pátek","Sobota","Neděle"]
            den  = _cz2[dt_o.weekday()]
            # Auto-session
            if not qs_session_var.get():
                h = dt_o.hour
                qs_session_var.set("London" if 8<=h<13 else "NY AM" if 13<=h<17 else "NY PM" if 17<=h<21 else "Asia")
        except: pass

        # Délka obchodu
        delka = ""
        try:
            dt_o = datetime.strptime(open_t,  "%Y-%m-%d %H:%M")
            dt_c = datetime.strptime(close_t, "%Y-%m-%d %H:%M")
            diff = dt_c - dt_o; h, r = divmod(int(diff.total_seconds()), 3600)
            delka = f"{h}h {r//60}m"
        except: pass

        d = {
            'cas_otevreni': open_t, 'cas_zavreni': close_t,
            'symbol': qs_sym_var.get(), 'smer': qs_dir_var.get(),
            'vstupni_hodnota':'', 'stoploss':'', 'takeprofit':'',
            'rrr': qs_rrr_var.get(), 'pips':'',
            'session': qs_session_var.get(), 'timeframe_graf':'', 'timeframe_vstup':'',
            'fibo': qs_setup_var.get(), 'duvod':'',
            'poznamka': qs_note_var.get(), 'vysledek': qs_res_var.get(),
            'den_tydne': den, 'delka_obchodu': delka, 'slippage':'0',
            'kvalita':'', 'obrazky':'', 'news':'Ne', 'news_event':'',
            'checklist_ratio':'', 'tags':''
        }

        try:
            ex = os.path.exists(DATA_FILE)
            with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=list(d.keys()))
                if not ex: w.writeheader()
                w.writerow(d)

            # Reset formuláře
            qs_open_var.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
            qs_close_var.set(""); qs_rrr_var.set(""); qs_note_var.set("")
            qs_res_var.set(""); qs_session_var.set("")
            for btn in res_btns.values(): btn.config(bg=DT_SURFACE, fg=DT_TEXT)

            update_listbox(); update_statistics()

            save_qs_btn.config(text="✅  ULOŽENO!", bg='#16a34a')
            qs_outer.after(2000, lambda: save_qs_btn.config(text="💾  ULOŽIT OBCHOD", bg=DT_BTN))
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se uložit:\n{e}")

    def reset_qs():
        qs_open_var.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        qs_close_var.set(""); qs_rrr_var.set(""); qs_note_var.set("")
        qs_res_var.set(""); qs_session_var.set("")
        qs_dir_var.set("Buy"); set_dir("Buy")
        for btn in res_btns.values(): btn.config(bg=DT_SURFACE, fg=DT_TEXT)

    tk.Frame(form, bg=DT_PANEL, height=8).pack()
    save_qs_btn = tk.Button(form, text="💾  ULOŽIT OBCHOD", command=quick_save,
                            bg=DT_BTN, fg='white', font=('Segoe UI',11,'bold'), pady=11)
    save_qs_btn.pack(fill='x', pady=(0,4))
    tk.Button(form, text="🗑  Resetovat", command=reset_qs,
              bg=DT_SURFACE, fg=DT_SUBTEXT, font=('Segoe UI',8), pady=4).pack(fill='x')


# HLAVNÍ OBRAZOVKA (TRADING)
# ==============================================================================




def _build_gallery_tab(parent):
    """Záložka galerie s filtry, hezčím vizuálem a nastavitelnou velikostí."""
    global gallery_inner

    # ── Lišta filtrů ─────────────────────────────────────────────────────────
    flt_outer = tk.Frame(parent, bg=DT_PANEL)
    flt_outer.pack(fill='x')

    # Záhlaví filtru
    flt_hdr = tk.Frame(flt_outer, bg='#2c3e50', pady=4)
    flt_hdr.pack(fill='x')
    tk.Label(flt_hdr, text="  🔍 FILTR GALERIE", bg='#2c3e50', fg='white',
             font=('Segoe UI', 8, 'bold')).pack(side='left')
    count_var = tk.StringVar(value="")
    tk.Label(flt_hdr, textvariable=count_var, bg='#2c3e50', fg='#7f8c8d',
             font=('Segoe UI', 8)).pack(side='right', padx=12)

    flt_row = tk.Frame(flt_outer, bg=DT_PANEL, padx=8, pady=6)
    flt_row.pack(fill='x')

    sym_var  = tk.StringVar(value='VŠE')
    res_var  = tk.StringVar(value='VŠE')
    ses_var  = tk.StringVar(value='VŠE')
    tag_var  = tk.StringVar(value='')
    sort_var = tk.StringVar(value='Datum ↓')
    size_var = tk.IntVar(value=200)
    cols_var = tk.IntVar(value=5)

    # Ulož do globálního slovníku
    _GAL_FILTERS.update({
        'sym_var': sym_var, 'res_var': res_var, 'ses_var': ses_var,
        'tag_var': tag_var, 'sort_var': sort_var,
        'size_var': size_var, 'cols_var': cols_var,
        'count_var': count_var,
    })

    def _chip(parent, label, widget_fn):
        f = tk.Frame(parent, bg=DT_PANEL); f.pack(side='left', padx=4)
        tk.Label(f, text=label, bg=DT_PANEL, fg=DT_SUBTEXT,
                 font=('Segoe UI', 7, 'bold')).pack(anchor='w')
        widget_fn(f)

    _chip(flt_row, "Symbol",
          lambda f: ttk.Combobox(f, textvariable=sym_var,
                                 values=['VŠE']+PAIRS, width=10,
                                 state='readonly').pack())
    _chip(flt_row, "Výsledek",
          lambda f: ttk.Combobox(f, textvariable=res_var,
                                 values=['VŠE','Win','Loss','BE'], width=7,
                                 state='readonly').pack())
    _chip(flt_row, "Seance",
          lambda f: ttk.Combobox(f, textvariable=ses_var,
                                 values=['VŠE']+SESSIONS_LIST, width=9,
                                 state='readonly').pack())
    _chip(flt_row, "Tag (obsahuje)",
          lambda f: tk.Entry(f, textvariable=tag_var, width=12,
                             bg='white', relief='solid', bd=1,
                             font=('Segoe UI', 9)).pack())
    _chip(flt_row, "Seřadit",
          lambda f: ttk.Combobox(f, textvariable=sort_var,
                                 values=['Datum ↓','Datum ↑','Symbol','Výsledek'],
                                 width=10, state='readonly').pack())

    sep = tk.Frame(flt_row, bg=DT_PANEL, width=1); sep.pack(side='left', fill='y', padx=8)

    # Velikost & sloupce
    size_frame = tk.Frame(flt_row, bg=DT_PANEL); size_frame.pack(side='left', padx=4)
    tk.Label(size_frame, text="Velikost", bg=DT_PANEL, fg=DT_SUBTEXT,
             font=('Segoe UI', 7, 'bold')).pack(anchor='w')
    size_lbl = tk.Label(size_frame, textvariable=tk.StringVar(),
                        bg=DT_PANEL, fg=DT_TEXT, font=('Segoe UI', 7))
    size_lbl.pack(anchor='w')
    def _update_size_lbl(*_):
        size_lbl.config(text=f"{size_var.get()} px")
    size_var.trace_add('write', _update_size_lbl)
    _update_size_lbl()
    ttk.Scale(size_frame, from_=120, to=340, variable=size_var,
              orient='horizontal', length=90,
              command=lambda _: update_gallery()).pack()

    cols_frame = tk.Frame(flt_row, bg=DT_PANEL); cols_frame.pack(side='left', padx=4)
    tk.Label(cols_frame, text="Sloupce", bg=DT_PANEL, fg=DT_SUBTEXT,
             font=('Segoe UI', 7, 'bold')).pack(anchor='w')
    cols_spin = tk.Spinbox(cols_frame, from_=2, to=8, textvariable=cols_var,
                           width=3, font=('Segoe UI', 9),
                           command=update_gallery)
    cols_spin.pack()

    # Tlačítka vpravo
    btn_f = tk.Frame(flt_row, bg=DT_PANEL); btn_f.pack(side='right', padx=6)
    tk.Button(btn_f, text="Použít", command=update_gallery,
              bg='#27ae60', fg='white', font=('Segoe UI', 8, 'bold'),
              padx=10, pady=4, relief='flat', cursor='hand2').pack(side='top', pady=(0, 3))
    def _reset_gal():
        sym_var.set('VŠE'); res_var.set('VŠE'); ses_var.set('VŠE')
        tag_var.set(''); sort_var.set('Datum ↓')
        size_var.set(200); cols_var.set(5)
        update_gallery()
    tk.Button(btn_f, text="Reset", command=_reset_gal,
              bg='#e74c3c', fg='white', font=('Segoe UI', 8),
              padx=10, pady=4, relief='flat', cursor='hand2').pack(side='top')

    # Bind combos → auto-apply
    for child in flt_row.winfo_children():
        for sub in (child.winfo_children() if hasattr(child, 'winfo_children') else []):
            if isinstance(sub, ttk.Combobox):
                sub.bind('<<ComboboxSelected>>', lambda e: update_gallery())
    tag_var.trace_add('write', lambda *_: None)  # Enter ruční

    # ── Scrollovatelná plocha pro obrázky ────────────────────────────────────
    gal_wrap = tk.Frame(parent, bg=DT_BG); gal_wrap.pack(fill='both', expand=True)
    gal_canv = tk.Canvas(gal_wrap, bg=DT_BG, highlightthickness=0)
    gal_scb  = ttk.Scrollbar(gal_wrap, command=gal_canv.yview)
    gal_canv.pack(side='left', fill='both', expand=True)
    gal_scb.pack(side='right', fill='y')
    gallery_inner = tk.Frame(gal_canv, bg=DT_BG)
    gal_canv.create_window((0, 0), window=gallery_inner, anchor='nw')
    gallery_inner.bind('<Configure>',
                       lambda e: gal_canv.configure(scrollregion=gal_canv.bbox('all')))
    gal_canv.configure(yscrollcommand=gal_scb.set)
    gal_canv.bind('<MouseWheel>',
                  lambda e: gal_canv.yview_scroll(int(-1*(e.delta/120)), 'units'))

def _make_tabs_draggable(notebook):
    """Drag & drop přeřazení záložek v ttk.Notebook."""
    _d = {'src': None}

    def _press(e):
        try: _d['src'] = notebook.index(f'@{e.x},{e.y}')
        except tk.TclError: _d['src'] = None

    def _release(e):
        if _d['src'] is None: return
        try: dst = notebook.index(f'@{e.x},{e.y}')
        except tk.TclError: dst = notebook.index('end') - 1
        if dst != _d['src']:
            notebook.insert(dst, _d['src'])
        _d['src'] = None

    def _motion(e):
        if _d['src'] is None: return
        try:
            dst = notebook.index(f'@{e.x},{e.y}')
            notebook.configure(cursor='fleur' if dst != _d['src'] else '')
        except tk.TclError:
            notebook.configure(cursor='')

    notebook.bind('<ButtonPress-1>', _press, add=True)
    notebook.bind('<ButtonRelease-1>', _release, add=True)
    notebook.bind('<B1-Motion>', _motion, add=True)

def open_settings_window(initial_tab=0):
    """Centrální nastavení — motiv, aktualizace, páry, scoring, sloupce, složka projektu."""
    sw = tk.Toplevel(root)
    sw.title("Nastavení")
    sw.geometry("720x560")
    sw.configure(bg=DT_BG)
    sw.resizable(True, True)
    sw.minsize(600, 480)
    sw.lift(); sw.focus_set()

    # Hlavička
    hdr = tk.Frame(sw, bg='#2c3e50', pady=8)
    hdr.pack(fill='x')
    tk.Label(hdr, text="⚙  Nastavení", bg='#2c3e50', fg='white',
             font=('Segoe UI', 13, 'bold')).pack(side='left', padx=18)

    nb = ttk.Notebook(sw)
    nb.pack(fill='both', expand=True, padx=8, pady=8)

    # ── Tab: Motiv ────────────────────────────────────────────────────────────
    t_theme = ttk.Frame(nb); nb.add(t_theme, text='  🎨 Motiv  ')
    _th_frame = tk.Frame(t_theme, bg=DT_BG, padx=28, pady=24)
    _th_frame.pack(fill='both', expand=True)
    tk.Label(_th_frame, text="Barevný motiv aplikace", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 16))
    _ALL_THEMES_BTN = [
        # (název,             btn_bg,    btn_fg,    popis)
        ("Tmavý",            "#1e293b", "#60a5fa", "Tmavé pozadí — slate paleta"),
        ("Tmavý modrý",      "#111827", "#3b82f6", "Hlubší tmavá — noční varianta"),
        ("Klasický",         "#e0e0e0", "#1a1a1a", "Světlý klasický Windows styl"),
        ("Šedý profesionál", "#cfd4d8", "#1c2833", "Světlý šedý profesionální"),
        ("Světlý elegantní", "#ffffff", "#0d6efd", "Čistě bílý elegantní"),
    ]
    cur_theme = load_theme_name()

    # Oddělovač tmavé / světlé
    tk.Label(_th_frame, text="— TMAVÉ MOTIVY —", bg=DT_BG, fg=DT_SUBTEXT,
             font=('Segoe UI', 8)).pack(anchor='w', pady=(0, 4))

    def _sw_switch_theme(name):
        apply_theme(name)
        apply_dark_theme(root)
        sw.destroy()
        show_intro_screen() if not current_project_name else show_main_screen(current_project_name)

    for i, (tname, tbg, tfg, tdesc) in enumerate(_ALL_THEMES_BTN):
        if i == 2:  # před prvním světlým
            tk.Frame(_th_frame, bg=DT_BORDER, height=1).pack(fill='x', pady=8)
            tk.Label(_th_frame, text="— SVĚTLÉ MOTIVY —", bg=DT_BG, fg=DT_SUBTEXT,
                     font=('Segoe UI', 8)).pack(anchor='w', pady=(0, 4))
        is_active = (tname == cur_theme)
        row = tk.Frame(_th_frame, bg=DT_BG)
        row.pack(anchor='w', pady=3)
        tk.Button(row,
                  text=("✔  " if is_active else "     ") + tname,
                  bg=tbg, fg=tfg,
                  font=('Segoe UI', 11, 'bold' if is_active else 'normal'),
                  relief='solid' if is_active else 'flat',
                  bd=2 if is_active else 0,
                  padx=24, pady=10, cursor='hand2', width=22,
                  command=lambda n=tname: _sw_switch_theme(n)).pack(side='left')
        tk.Label(row, text=tdesc, bg=DT_BG, fg=DT_SUBTEXT,
                 font=('Segoe UI', 9)).pack(side='left', padx=12)

    # ── Tab: Obecné (měna, jazyk) ─────────────────────────────────────────────
    t_gen = ttk.Frame(nb); nb.add(t_gen, text='  ⚙ Obecné  ')
    _gen_frame = tk.Frame(t_gen, bg=DT_BG, padx=28, pady=24)
    _gen_frame.pack(fill='both', expand=True)
    tk.Label(_gen_frame, text="Obecné nastavení", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 20))

    # Měna
    _cur_box = tk.Frame(_gen_frame, bg=DT_SURFACE, padx=18, pady=14)
    _cur_box.pack(fill='x', pady=(0, 14))
    tk.Label(_cur_box, text="🪙  Domácí měna", bg=DT_SURFACE, fg=DT_TEXT,
             font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 6))
    tk.Label(_cur_box, text="Měna, ve které sleduješ zisk/ztrátu svých obchodů (zobrazuje se v poli Zisk/Ztráta ve formuláři).",
             bg=DT_SURFACE, fg=DT_SUBTEXT, font=('Segoe UI', 9), wraplength=580, justify='left').pack(anchor='w', pady=(0, 10))
    _cur_row = tk.Frame(_cur_box, bg=DT_SURFACE); _cur_row.pack(anchor='w')
    tk.Label(_cur_row, text="Měna:", bg=DT_SURFACE, fg=DT_SUBTEXT,
             font=('Segoe UI', 10), width=10, anchor='w').pack(side='left')
    _CURRENCIES = ['CZK', 'EUR', 'USD', 'GBP', 'PLN', 'HUF', 'CHF']
    _cur_var = tk.StringVar(value=get_app_currency())
    _cur_combo = ttk.Combobox(_cur_row, values=_CURRENCIES, textvariable=_cur_var,
                               state='readonly', width=10, font=('Segoe UI', 10))
    _cur_combo.pack(side='left')

    def _save_currency():
        set_app_currency(_cur_var.get())
        messagebox.showinfo("✓ Uloženo", f"Domácí měna nastavena na: {_cur_var.get()}\n\nZměna se projeví při příštím otevření formuláře.", parent=sw)

    tk.Button(_cur_row, text="Uložit", command=_save_currency,
              bg=DT_ACCENT, fg='#ffffff', font=('Segoe UI', 9, 'bold'),
              padx=12, pady=4, relief='flat', cursor='hand2').pack(side='left', padx=10)

    # ── Tab: Aktualizace ─────────────────────────────────────────────────────
    t_upd = ttk.Frame(nb); nb.add(t_upd, text='  🔄 Aktualizace  ')
    _upd_frame = tk.Frame(t_upd, bg=DT_BG, padx=28, pady=24)
    _upd_frame.pack(fill='both', expand=True)
    tk.Label(_upd_frame, text="Aktualizace programu", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 16))
    _ver_box = tk.Frame(_upd_frame, bg=DT_SURFACE, padx=18, pady=14)
    _ver_box.pack(fill='x', pady=(0, 16))
    def _vrow2(lbl, val, vc=None):
        r = tk.Frame(_ver_box, bg=DT_SURFACE); r.pack(fill='x', pady=3)
        tk.Label(r, text=lbl, bg=DT_SURFACE, fg=DT_SUBTEXT,
                 font=('Segoe UI', 10), width=18, anchor='w').pack(side='left')
        tk.Label(r, text=val, bg=DT_SURFACE, fg=vc or DT_TEXT,
                 font=('Segoe UI', 10, 'bold')).pack(side='left')
    _vrow2("Aktuální verze:", VERSION, DT_ACCENT)
    _vrow2("GitHub URL:", UPDATE_URL[:48] + "...", DT_SUBTEXT)
    tk.Button(_upd_frame, text="🔄  Zkontrolovat aktualizace", command=lambda: [sw.destroy(), check_for_updates(silent=False)],
              bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
              padx=16, pady=8, relief='flat', cursor='hand2').pack(anchor='w')

    # ── Tab: Páry & Timeframes ────────────────────────────────────────────────
    t_lists = ttk.Frame(nb); nb.add(t_lists, text='  📊 Páry & TF  ')
    setup_lists_manager_ui(t_lists)

    # ── Tab: Scoring ──────────────────────────────────────────────────────────
    t_score = ttk.Frame(nb); nb.add(t_score, text='  🏆 Scoring  ')
    setup_settings_ui(t_score)

    # ── Tab: Sloupce tabulky ─────────────────────────────────────────────────
    t_cols = ttk.Frame(nb); nb.add(t_cols, text='  ⚙ Sloupce  ')
    _cols_frame = tk.Frame(t_cols, bg=DT_BG, padx=28, pady=24)
    _cols_frame.pack(fill='both', expand=True)
    tk.Label(_cols_frame, text="Sloupce tabulky obchodů", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 12))
    tk.Label(_cols_frame, text="Přidej nebo odeber sloupce v tabulce obchodů. Změny se projeví po zavření nastavení.",
             bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 16))
    def _open_col_cfg():
        sw.destroy()
        ColumnConfigurator(root, lambda: show_main_screen(current_project_name))
    tk.Button(_cols_frame, text="⚙  Otevřít konfiguraci sloupců",
              command=_open_col_cfg,
              bg=DT_BTN, fg=DT_TEXT, font=('Segoe UI', 10),
              padx=16, pady=8, relief='flat', cursor='hand2').pack(anchor='w')

    # ── Tab: Složka projektu ──────────────────────────────────────────────────
    t_folder = ttk.Frame(nb); nb.add(t_folder, text='  📁 Složka projektu  ')
    _fld_frame = tk.Frame(t_folder, bg=DT_BG, padx=28, pady=24)
    _fld_frame.pack(fill='both', expand=True)
    tk.Label(_fld_frame, text="Vlastní složka projektu", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 6))
    tk.Label(_fld_frame,
             text="Každý projekt může mít data v libovolné složce na disku. Hodí se pro synchronizaci přes cloud (OneDrive, Dropbox, ...).",
             bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 10),
             wraplength=580, justify='left').pack(anchor='w', pady=(0, 20))

    if not current_project_name:
        tk.Label(_fld_frame, text="⚠  Žádný projekt není otevřen.", bg=DT_BG, fg='#e74c3c',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
    else:
        proj_key = f"{current_mode}/{current_project_name}"
        paths_data = load_project_paths()
        cur_custom = paths_data.get(proj_key, "")
        cur_default = _resolve_project_path(current_mode, current_project_name)

        info_box = tk.Frame(_fld_frame, bg=DT_SURFACE, padx=16, pady=12)
        info_box.pack(fill='x', pady=(0, 16))
        def _irow(lbl, val):
            r = tk.Frame(info_box, bg=DT_SURFACE); r.pack(fill='x', pady=2)
            tk.Label(r, text=lbl, bg=DT_SURFACE, fg=DT_SUBTEXT,
                     font=('Segoe UI', 9), width=16, anchor='w').pack(side='left')
            tk.Label(r, text=val, bg=DT_SURFACE, fg=DT_TEXT,
                     font=('Segoe UI', 9, 'bold'), wraplength=450, anchor='w').pack(side='left', fill='x', expand=True)
        _irow("Projekt:", f"{current_project_name}  ({current_mode})")
        _irow("Aktuální složka:", cur_custom if cur_custom else cur_default)
        if cur_custom:
            _irow("Typ:", "✔  Vlastní složka")
        else:
            _irow("Typ:", "Výchozí (automatická)")

        path_var = tk.StringVar(value=cur_custom or cur_default)
        path_entry = tk.Entry(_fld_frame, textvariable=path_var, width=60,
                              bg=DT_ENTRY if hasattr(globals(), 'DT_ENTRY') else 'white',
                              fg=DT_TEXT, relief='solid', bd=1,
                              font=('Segoe UI', 9))
        path_entry.pack(fill='x', pady=(0, 8))

        btn_row = tk.Frame(_fld_frame, bg=DT_BG)
        btn_row.pack(anchor='w')

        def _browse():
            d = filedialog.askdirectory(title="Vyber složku projektu",
                                        initialdir=path_var.get() or _APP_DIR)
            if d:
                path_var.set(d.replace('/', os.sep))

        def _save_path():
            new_path = path_var.get().strip()
            if not new_path:
                messagebox.showwarning("Prázdná cesta", "Zadej cestu ke složce.")
                return
            if not os.path.isdir(new_path):
                if messagebox.askyesno("Složka neexistuje",
                                       f"Složka neexistuje:\n{new_path}\n\nChceš ji vytvořit?"):
                    try:
                        os.makedirs(os.path.join(new_path, 'images'), exist_ok=True)
                    except Exception as ex:
                        messagebox.showerror("Chyba", f"Nelze vytvořit: {ex}"); return
                else:
                    return
            paths_data[proj_key] = new_path
            save_project_paths(paths_data)
            # Okamžitě přepnout globální proměnné
            global DATA_FILE, IMAGES_DIR, PROP_CONFIG_FILE, CHECKLIST_FILE
            global SCORING_FILE, PAIRS_FILE, TIMEFRAMES_FILE, RULES_FILE, FILTERS_FILE, ACCOUNTS_FILE
            p = new_path
            DATA_FILE = os.path.join(p, 'trades.csv')
            PROP_CONFIG_FILE = os.path.join(p, 'prop_config.json')
            IMAGES_DIR = os.path.join(p, 'images')
            CHECKLIST_FILE = os.path.join(p, 'checklist.json')
            SCORING_FILE = os.path.join(p, 'scoring_config.json')
            PAIRS_FILE = os.path.join(p, 'pairs_config.json')
            TIMEFRAMES_FILE = os.path.join(p, 'timeframes_config.json')
            RULES_FILE = os.path.join(p, 'rules.txt')
            FILTERS_FILE = os.path.join(p, 'filters_config.json'); ACCOUNTS_FILE = os.path.join(p, 'accounts.json')
            messagebox.showinfo("Uloženo", f"Složka projektu uložena:\n{new_path}")
            sw.destroy()
            show_main_screen(current_project_name)

        def _reset_path():
            if messagebox.askyesno("Reset", "Vrátit projekt do výchozí složky?"):
                paths_data.pop(proj_key, None)
                save_project_paths(paths_data)
                sw.destroy()
                open_project_by_name(current_mode, current_project_name)

        tk.Button(btn_row, text="📂  Procházet...", command=_browse,
                  bg=DT_BTN, fg=DT_TEXT, font=('Segoe UI', 9),
                  padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left', padx=(0, 8))
        tk.Button(btn_row, text="💾  Uložit", command=_save_path,
                  bg='#27ae60', fg='white', font=('Segoe UI', 9, 'bold'),
                  padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left', padx=(0, 8))
        tk.Button(btn_row, text="↺  Reset na výchozí", command=_reset_path,
                  bg='#e74c3c', fg='white', font=('Segoe UI', 9),
                  padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left')

    # ── Tab: Prohlížeč ────────────────────────────────────────────────────────
    t_browser = ttk.Frame(nb); nb.add(t_browser, text='  🌐 Prohlížeč  ')
    _br_frame = tk.Frame(t_browser, bg=DT_BG, padx=28, pady=24)
    _br_frame.pack(fill='both', expand=True)
    tk.Label(_br_frame, text="Prohlížeč pro TradingView", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 6))
    tk.Label(_br_frame, text="TradingView se otevírá ve vestavěném okně prohlížeče. Vyber prohlížeč nebo zadej vlastní cestu.",
             bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 10), wraplength=580, justify='left').pack(anchor='w', pady=(0, 16))

    # Detekuj dostupné prohlížeče
    _browsers = [
        ("Microsoft Edge",  r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ("Microsoft Edge",  r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ("Google Chrome",   r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("Google Chrome",   r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ("Mozilla Firefox", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
    ]
    _available = [(name, path) for name, path in _browsers if os.path.exists(path)]

    cur_gs = load_global_settings()
    _br_var = tk.StringVar(value=cur_gs.get('browser_exe', ''))

    if _available:
        tk.Label(_br_frame, text="Nalezené prohlížeče:", bg=DT_BG, fg=DT_SUBTEXT,
                 font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(0, 4))
        for _bname, _bpath in _available:
            tk.Radiobutton(_br_frame, text=f"{_bname}  ({_bpath})",
                           variable=_br_var, value=_bpath,
                           bg=DT_BG, fg=DT_TEXT, selectcolor=DT_SURFACE,
                           activebackground=DT_BG, font=('Segoe UI', 9),
                           cursor='hand2').pack(anchor='w', pady=2)
        tk.Radiobutton(_br_frame, text="Vlastní cesta (viz níže):",
                       variable=_br_var, value='__custom__',
                       bg=DT_BG, fg=DT_TEXT, selectcolor=DT_SURFACE,
                       activebackground=DT_BG, font=('Segoe UI', 9),
                       cursor='hand2').pack(anchor='w', pady=(8, 2))

    _custom_var = tk.StringVar(value=cur_gs.get('browser_exe', '') if cur_gs.get('browser_exe', '') not in [p for _, p in _available] else '')
    _custom_entry = tk.Entry(_br_frame, textvariable=_custom_var, width=54,
                             font=('Segoe UI', 9), relief='solid', bd=1)
    _custom_entry.pack(fill='x', pady=(0, 4))

    def _browse_browser():
        p = filedialog.askopenfilename(title="Vyber spustitelný soubor prohlížeče",
                                       filetypes=[("Spustitelné soubory", "*.exe"), ("Vše", "*.*")])
        if p:
            _custom_var.set(p)
            _br_var.set('__custom__')

    def _save_browser():
        chosen = _br_var.get()
        if chosen == '__custom__':
            chosen = _custom_var.get().strip()
        if not chosen:
            messagebox.showwarning("Prázdná hodnota", "Vyber nebo zadej cestu k prohlížeči.", parent=sw)
            return
        if not os.path.exists(chosen):
            messagebox.showwarning("Soubor nenalezen", f"Soubor neexistuje:\n{chosen}", parent=sw)
            return
        gs = load_global_settings()
        gs['browser_exe'] = chosen
        save_global_settings(gs)
        messagebox.showinfo("Uloženo", f"Prohlížeč nastaven:\n{chosen}", parent=sw)

    _br_btn_row = tk.Frame(_br_frame, bg=DT_BG)
    _br_btn_row.pack(anchor='w', pady=(4, 0))
    tk.Button(_br_btn_row, text="📂  Procházet...", command=_browse_browser,
              bg=DT_BTN, fg=DT_TEXT, font=('Segoe UI', 9),
              padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left', padx=(0, 8))
    tk.Button(_br_btn_row, text="💾  Uložit", command=_save_browser,
              bg='#27ae60', fg='white', font=('Segoe UI', 9, 'bold'),
              padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left')

    # ── Tab: Firebase ─────────────────────────────────────────────────────────
    t_fb = ttk.Frame(nb); nb.add(t_fb, text='  🔥 Firebase  ')
    _fb_frame = tk.Frame(t_fb, bg=DT_BG, padx=28, pady=24)
    _fb_frame.pack(fill='both', expand=True)

    tk.Label(_fb_frame, text="🔥  Online žebříček — Firebase", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 4))
    tk.Label(_fb_frame, text="Nastavení sdíleného žebříčku XP s kamarády. Data se ukládají na Firebase Realtime Database.",
             bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 9), wraplength=580, justify='left').pack(anchor='w', pady=(0, 18))

    _fb_cfg = load_firebase_config()

    def _fb_row(parent, label, default, show=''):
        row = tk.Frame(parent, bg=DT_BG); row.pack(fill='x', pady=4)
        tk.Label(row, text=label, bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 9),
                 width=18, anchor='w').pack(side='left')
        var = tk.StringVar(value=default)
        e = tk.Entry(row, textvariable=var, font=('Segoe UI', 10), width=52,
                     bg='#1e293b', fg='#e2e8f0', insertbackground='white',
                     relief='solid', bd=1, show=show)
        e.pack(side='left', fill='x', expand=True)
        return var

    _fb_url_var  = _fb_row(_fb_frame, "URL databáze:",   _fb_cfg.get('url',      'https://obd1-26456-default-rtdb.firebaseio.com'))
    _fb_sec_var  = _fb_row(_fb_frame, "Database secret:", _fb_cfg.get('secret',   ''), show='●')
    _fb_name_var = _fb_row(_fb_frame, "Tvoje jméno:",     _fb_cfg.get('username', 'patrik'))

    tk.Label(_fb_frame,
             text="💡  URL najdeš v Firebase konzoli: Realtime Database → Data (horní lišta).\n"
                  "    Secret: Project Settings → Service Accounts → Database secrets → Show.",
             bg=DT_BG, fg='#64748b', font=('Segoe UI', 8),
             justify='left').pack(anchor='w', pady=(10, 16))

    _fb_status = tk.Label(_fb_frame, text="", bg=DT_BG, fg='#4ade80', font=('Segoe UI', 9, 'bold'))
    _fb_status.pack(anchor='w', pady=(0, 8))

    def _save_fb():
        cfg = {
            'url':      _fb_url_var.get().strip().rstrip('/'),
            'secret':   _fb_sec_var.get().strip(),
            'username': _fb_name_var.get().strip(),
        }
        if not cfg['url'] or not cfg['username']:
            _fb_status.config(text="⚠  URL a Jméno jsou povinné.", fg='#f87171')
            return
        save_firebase_config(cfg)
        _fb_status.config(text="✅  Uloženo! XP se odešle při příštím uložení obchodu.", fg='#4ade80')

    def _test_fb():
        # urllib je součást Pythonu — žádná instalace není potřeba
        _fb_status.config(text="Testuju připojení…", fg='#fbbf24')
        sw.update_idletasks()
        import threading
        def _t():
            try:
                import urllib.error
                url    = _fb_url_var.get().strip().rstrip('/')
                secret = _fb_sec_var.get().strip()
                if not url:
                    sw.after(0, lambda: _fb_status.config(text="⚠  Zadej URL databáze.", fg='#f87171'))
                    return

                # Zkus primární URL, při chybě zkus EU variantu
                _used_url = url
                try:
                    status, body = _fb_get(f"{url}/users.json", secret=secret, timeout=8)
                except Exception as conn_err:
                    proj_id = url.split('//')[1].split('.')[0]
                    alt_url = f"https://{proj_id}.europe-west1.firebasedatabase.app"
                    try:
                        status, body = _fb_get(f"{alt_url}/users.json", secret=secret, timeout=8)
                        _used_url = alt_url
                        sw.after(0, lambda u=alt_url: _fb_url_var.set(u))
                    except Exception as conn_err2:
                        sw.after(0, lambda e=str(conn_err): (
                            _fb_status.config(text=f"❌  Nelze se připojit: {e}", fg='#f87171'),
                            messagebox.showerror("Chyba připojení",
                                f"Nepodařilo se připojit k Firebase.\n\nChyba: {e}\n\n"
                                "Zkontroluj URL v Firebase konzoli:\nRealtime Database → Data → horní lišta",
                                parent=sw)
                        ))
                        return

                if status == 200:
                    try:   data_fb = json.loads(body)
                    except: data_fb = None
                    count = len(data_fb) if isinstance(data_fb, dict) else 0
                    sw.after(0, lambda u=_used_url, c=count: (
                        _fb_status.config(text=f"✅  Připojeno!  V databázi je {c} hráčů.", fg='#4ade80'),
                        messagebox.showinfo("Připojeno!", f"Firebase funguje! ✅\n\nURL: {u}\nHráčů v databázi: {c}", parent=sw)
                    ))
                elif status in (401, 403):
                    sw.after(0, lambda s=status: (
                        _fb_status.config(text=f"❌  HTTP {s} — zkontroluj Firebase Rules.", fg='#f87171'),
                        messagebox.showerror("Přístup odmítnut",
                            f"Firebase vrátil HTTP {s}.\n\n"
                            "Jdi do Firebase konzole → Realtime Database → Rules\n"
                            "a nastav na (dočasně pro test):\n\n"
                            '{\n  "rules": {\n    ".read": true,\n    ".write": true\n  }\n}\n\n'
                            "Pak klikni Publish a zkus znovu.", parent=sw)
                    ))
                else:
                    sw.after(0, lambda s=status: _fb_status.config(text=f"❌  HTTP {s}", fg='#f87171'))
            except Exception as _e:
                sw.after(0, lambda e=str(_e): _fb_status.config(text=f"❌  {e}", fg='#f87171'))
        threading.Thread(target=_t, daemon=True).start()

    def _sync_now():
        _save_fb()
        firebase_sync_xp()
        _fb_status.config(text="📤  XP odesláno na Firebase!", fg='#4ade80')

    _fb_btn_row = tk.Frame(_fb_frame, bg=DT_BG)
    _fb_btn_row.pack(anchor='w')
    tk.Button(_fb_btn_row, text="💾  Uložit", command=_save_fb,
              bg='#15803d', fg='white', font=('Segoe UI', 9, 'bold'),
              padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left', padx=(0, 8))
    tk.Button(_fb_btn_row, text="🔌  Test připojení", command=_test_fb,
              bg='#1d4ed8', fg='white', font=('Segoe UI', 9),
              padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left', padx=(0, 8))
    tk.Button(_fb_btn_row, text="📤  Odeslat moje XP teď", command=_sync_now,
              bg='#b45309', fg='white', font=('Segoe UI', 9),
              padx=12, pady=6, relief='flat', cursor='hand2').pack(side='left')

    # ── Tab: XP Systém ────────────────────────────────────────────────────────
    t_xp = ttk.Frame(nb); nb.add(t_xp, text='  ⭐ XP Systém  ')
    xp_outer = tk.Frame(t_xp, bg=DT_BG)
    xp_outer.pack(fill='both', expand=True)

    xp_canvas = tk.Canvas(xp_outer, bg=DT_BG, highlightthickness=0)
    xp_sb_v   = ttk.Scrollbar(xp_outer, command=xp_canvas.yview)
    xp_canvas.configure(yscrollcommand=xp_sb_v.set)
    xp_sb_v.pack(side='right', fill='y')
    xp_canvas.pack(fill='both', expand=True)
    xp_inner = tk.Frame(xp_canvas, bg=DT_BG, padx=20, pady=14)
    xp_canvas.create_window((0, 0), window=xp_inner, anchor='nw')
    xp_inner.bind('<Configure>', lambda e: xp_canvas.configure(scrollregion=xp_canvas.bbox('all')))

    _xp_cfg = get_xp_config()

    tk.Label(xp_inner, text="⭐  XP Bodovací systém", bg=DT_BG, fg=DT_TEXT,
             font=('Segoe UI', 13, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 4))
    tk.Label(xp_inner, text="Nastav kolik XP získáš za jednotlivé akce a pravidla.",
             bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 9)).grid(row=1, column=0, columnspan=3, sticky='w', pady=(0, 14))

    # ── Základní XP ──────────────────────────────────────────────────────────
    tk.Label(xp_inner, text="ZÁKLADNÍ XP ZA AKCI", bg=DT_BG, fg=DT_SUBTEXT,
             font=('Segoe UI', 8, 'bold')).grid(row=2, column=0, columnspan=3, sticky='w', pady=(0, 4))

    _basic_fields = [
        ("xp_backtest_trade",  "Backtest obchod (+XP za přidání)"),
        ("xp_real_trade",      "Reálný obchod (+XP za přidání)"),
        ("xp_edit_trade",      "Úprava existujícího obchodu"),
        ("xp_journal_entry",   "Zápis do deníku (nový záznam)"),
        ("xp_win_bonus",       "WIN výsledek — bonus"),
        ("xp_be_bonus",        "BE výsledek — bonus"),
        ("xp_loss_with_sl",    "LOSS + SL nastaven — disciplína"),
        ("xp_with_photo",      "Obchod se screenshotem"),
        ("xp_with_note",       "Obchod s poznámkou"),
        ("xp_checklist_full",  "Checklist splněn na 100%"),
        ("xp_bt_hour",         "⏱ Každá hodina backtestování"),
    ]
    _xp_vars = {}
    for ri2, (key, label) in enumerate(_basic_fields, start=3):
        tk.Label(xp_inner, text=label, bg=DT_BG, fg=DT_TEXT,
                 font=('Segoe UI', 9)).grid(row=ri2, column=0, sticky='w', padx=(12, 6), pady=2)
        _v = tk.StringVar(value=str(_xp_cfg.get(key, 0)))
        _xp_vars[key] = _v
        tk.Entry(xp_inner, textvariable=_v, width=6, font=('Segoe UI', 9),
                 bg=DT_SURFACE, fg=DT_TEXT, insertbackground=DT_TEXT,
                 relief='flat').grid(row=ri2, column=1, sticky='w', padx=4, pady=2)
        tk.Label(xp_inner, text="XP", bg=DT_BG, fg=DT_SUBTEXT,
                 font=('Segoe UI', 8)).grid(row=ri2, column=2, sticky='w')

    # ── Pravidla ─────────────────────────────────────────────────────────────
    rule_start_row = 3 + len(_basic_fields) + 1
    tk.Frame(xp_inner, bg=DT_BORDER, height=1).grid(
        row=rule_start_row-1, column=0, columnspan=3, sticky='ew', pady=(10, 6))
    tk.Label(xp_inner, text="PRAVIDLA — bonus XP za dodržení", bg=DT_BG, fg=DT_SUBTEXT,
             font=('Segoe UI', 8, 'bold')).grid(row=rule_start_row, column=0, columnspan=3, sticky='w', pady=(0, 6))

    _rules_cfg = _xp_cfg.get('rules', {})
    _rule_enabled_vars = {}
    _rule_xp_vars      = {}
    _rule_val_vars     = {}

    _rule_meta = {
        "daily_limit":  ("Denní limit obchodů",    "Max. obchodů/den:", True),
        "weekly_limit": ("Týdenní limit obchodů",  "Max. obchodů/týden:", True),
        "no_revenge":   ("Bez revenge tradingu",   "Max. ztrát za sebou:", True),
        "rrr_min":      ("Minimální RRR",           "Min. RRR:", True),
        "always_sl":    ("Vždy Stop Loss",          None, False),
        "win_streak_3": ("Série 3 výher v řadě",   None, False),
        "win_streak_5": ("Série 5 výher v řadě",   None, False),
        "with_tags":    ("Vyplněné tagy",           None, False),
    }

    for ri2, (rule_id, (rname, rval_label, has_val)) in enumerate(_rule_meta.items(), start=rule_start_row+1):
        rcfg = _rules_cfg.get(rule_id, {})
        # Enabled checkbox
        _ev = tk.BooleanVar(value=rcfg.get('enabled', True))
        _rule_enabled_vars[rule_id] = _ev
        tk.Checkbutton(xp_inner, variable=_ev, bg=DT_BG,
                       activebackground=DT_BG, selectcolor=DT_SURFACE).grid(row=ri2, column=0, sticky='w', padx=(12, 0))
        tk.Label(xp_inner, text=rname, bg=DT_BG, fg=DT_TEXT,
                 font=('Segoe UI', 9)).grid(row=ri2, column=0, sticky='w', padx=(36, 6))
        # XP za pravidlo
        _xv = tk.StringVar(value=str(rcfg.get('xp', 10)))
        _rule_xp_vars[rule_id] = _xv
        tk.Entry(xp_inner, textvariable=_xv, width=6, font=('Segoe UI', 9),
                 bg=DT_SURFACE, fg=DT_TEXT, insertbackground=DT_TEXT,
                 relief='flat').grid(row=ri2, column=1, sticky='w', padx=4)
        tk.Label(xp_inner, text="XP", bg=DT_BG, fg=DT_SUBTEXT,
                 font=('Segoe UI', 8)).grid(row=ri2, column=2, sticky='w')
        # Hodnota pravidla (volitelná)
        if has_val and rval_label:
            tk.Label(xp_inner, text=rval_label, bg=DT_BG, fg=DT_SUBTEXT,
                     font=('Segoe UI', 8)).grid(row=ri2, column=3, sticky='w', padx=(12, 4))
            _vv = tk.StringVar(value=str(rcfg.get('value', '')))
            _rule_val_vars[rule_id] = _vv
            tk.Entry(xp_inner, textvariable=_vv, width=7, font=('Segoe UI', 9),
                     bg=DT_SURFACE, fg=DT_TEXT, insertbackground=DT_TEXT,
                     relief='flat').grid(row=ri2, column=4, sticky='w')

    # ── Tlačítko Uložit ───────────────────────────────────────────────────────
    save_row = rule_start_row + 2 + len(_rule_meta)
    tk.Frame(xp_inner, bg=DT_BORDER, height=1).grid(
        row=save_row-1, column=0, columnspan=5, sticky='ew', pady=(10, 6))

    def _save_xp_config():
        cfg2 = get_xp_config()
        for key, var in _xp_vars.items():
            try: cfg2[key] = int(var.get())
            except ValueError: pass
        for rule_id in _rule_meta:
            cfg2['rules'][rule_id]['enabled'] = _rule_enabled_vars[rule_id].get()
            try: cfg2['rules'][rule_id]['xp']  = int(_rule_xp_vars[rule_id].get())
            except ValueError: pass
            if rule_id in _rule_val_vars:
                raw_val = _rule_val_vars[rule_id].get().replace(',', '.')
                try:
                    cfg2['rules'][rule_id]['value'] = float(raw_val) if '.' in raw_val else int(raw_val)
                except ValueError:
                    pass
        save_xp_config(cfg2)
        messagebox.showinfo("Uloženo", "Nastavení XP systému uloženo.", parent=sw)

    btn_row_f = tk.Frame(xp_inner, bg=DT_BG)
    btn_row_f.grid(row=save_row, column=0, columnspan=5, sticky='w', pady=6)
    tk.Button(btn_row_f, text="💾  Uložit XP nastavení", command=_save_xp_config,
              bg='#ca8a04', fg='#1c1400', font=('Segoe UI', 10, 'bold'),
              padx=18, pady=8, relief='flat', cursor='hand2').pack(side='left')
    tk.Button(btn_row_f, text="⭐  Zobrazit XP přehled", command=open_xp_overview,
              bg=DT_BTN, fg=DT_TEXT, font=('Segoe UI', 9),
              padx=14, pady=8, relief='flat', cursor='hand2').pack(side='left', padx=10)

    nb.select(initial_tab)


def open_project_by_name(mode, name):
    """Otevře projekt podle jména bez Listbox (používá se po reset složky)."""
    p = _resolve_project_path(mode, name)
    global DATA_FILE, IMAGES_DIR, PROP_CONFIG_FILE, CHECKLIST_FILE, SCORING_FILE, PAIRS_FILE, TIMEFRAMES_FILE, RULES_FILE, current_mode, FILTERS_FILE, ACCOUNTS_FILE
    DATA_FILE = os.path.join(p, 'trades.csv'); PROP_CONFIG_FILE = os.path.join(p, 'prop_config.json')
    IMAGES_DIR = os.path.join(p, 'images'); CHECKLIST_FILE = os.path.join(p, 'checklist.json')
    SCORING_FILE = os.path.join(p, 'scoring_config.json'); PAIRS_FILE = os.path.join(p, 'pairs_config.json')
    TIMEFRAMES_FILE = os.path.join(p, 'timeframes_config.json'); RULES_FILE = os.path.join(p, 'rules.txt')
    FILTERS_FILE = os.path.join(p, 'filters_config.json'); ACCOUNTS_FILE = os.path.join(p, 'accounts.json')
    current_mode = mode
    show_main_screen(name)

def show_main_screen(p_name):
    global current_project_name, trades_tree, filter_col_var, filter_val_var, paned, v_paned, save_btn
    global cas_otevreni_entry, cas_zavreni_entry, symbol_combo, smer_var, vstupni_hodnota_entry, stoploss_entry, takeprofit_entry
    global rrr_entry, pips_entry, duvod_entry, session_combo, fibo_combo, den_tydne_entry, delka_obchodu_entry, htf_combo, ltf_combo
    global obrazky_list, poznamka_entry, vysledek_combo, slippage_entry, score_label, details_text, image_frame, stats_text, stats_graph_frame, gallery_inner, best_performers_frame, zisk_mena_entry, accounts_combo
    global stats_symbol_var, stats_symbol_combo, news_var, checklist_display_label, pie_graph_frame, news_event_entry
    global heatmap_graph_frame, tags_entry, bar_chart_frame, bar_chart_canvases, kpi_frame, tables_frame, xp_badge_btn, periods_account_var, bt_sw_btn, main_notebook, _sort_col, _sort_rev
    _sort_col = None; _sort_rev = False   # reset řazení při přepnutí projektu
    global filter_symbol_var, filter_result_var, filter_session_var, filter_date_from_var, filter_date_to_var, filter_tag_var, filter_rrr_min_var, filter_rrr_max_var

    current_project_name = p_name
    if filter_col_var is None: filter_col_var = tk.StringVar(value="Symbol")
    if filter_val_var is None: filter_val_var = tk.StringVar(value="")
    bar_chart_canvases = []
    # Inicializace filtrů
    filter_symbol_var   = tk.StringVar(value="VŠE")
    filter_result_var   = tk.StringVar(value="VŠE")
    filter_session_var  = tk.StringVar(value="VŠE")
    filter_date_from_var = tk.StringVar(value="")
    filter_date_to_var   = tk.StringVar(value="")
    filter_tag_var       = tk.StringVar(value="")
    filter_rrr_min_var   = tk.StringVar(value="")
    filter_rrr_max_var   = tk.StringVar(value="")

    # Načtení párů pro tento projekt
    load_pairs_config()
    load_timeframes_config()

    for w in root.winfo_children(): w.destroy()

    mode_color = '#00d4aa' if current_mode == "REAL" else '#0f3460'
    mode_text  = "REAL TRADING (FTMO)" if current_mode == "REAL" else "BACKTEST"

    h = tk.Frame(root, bg=DT_PANEL, height=52); h.pack(fill='x')
    h.pack_propagate(False)
    # Levá část – název
    left_h = tk.Frame(h, bg=DT_PANEL); left_h.pack(side='left', fill='y')
    mode_badge = tk.Label(left_h, text=f" {mode_text} ", bg=mode_color, fg=DT_BG, font=('Segoe UI', 8, 'bold'), padx=6, pady=3)
    mode_badge.pack(side='left', padx=(15,8), pady=14)
    _pname_var = tk.StringVar(value=p_name.upper())
    _pname_lbl = tk.Label(left_h, textvariable=_pname_var, fg=DT_ACCENT, bg=DT_PANEL,
                          font=('Segoe UI', 12, 'bold'), cursor='hand2')
    _pname_lbl.pack(side='left', pady=14)
    tk.Label(left_h, text=" ✏️", bg=DT_PANEL, fg=DT_SUBTEXT, font=('Segoe UI', 9),
             cursor='hand2').pack(side='left', pady=14)
    def _rename_project(e=None):
        new_name = simpledialog.askstring("Přejmenovat projekt",
            "Nový název projektu:", initialvalue=_pname_var.get(), parent=root)
        if not new_name or not new_name.strip(): return
        new_name = new_name.strip()
        old_path = os.path.join(BASE_DIR, p_name)
        new_path = os.path.join(BASE_DIR, new_name)
        if os.path.exists(new_path):
            messagebox.showerror("Chyba", f"Projekt '{new_name}' už existuje."); return
        try:
            os.rename(old_path, new_path)
            _pname_var.set(new_name.upper())
            # Aktualizuj p_name pro zbytek session
            import ctypes; ctypes.py_object
        except Exception as ex:
            messagebox.showerror("Chyba přejmenování", str(ex))
    _pname_lbl.bind('<Button-1>', _rename_project)
    # Pravá část – tlačítka
    hb = tk.Frame(h, bg=DT_PANEL); hb.pack(side='right', fill='y', padx=12)
    tk.Button(hb, text="✕  MENU", command=show_intro_screen,
              bg=DT_LOSS_BG, fg=DT_LOSS_FG,
              font=('Segoe UI', 9, 'bold'), padx=12, pady=6).pack(side='right', padx=4, pady=10)
    tk.Button(hb, text="⚙  NASTAVENÍ", command=open_settings_window,
              bg=DT_BTN, fg=DT_SUBTEXT,
              font=('Segoe UI', 9), padx=10, pady=6).pack(side='right', padx=4, pady=10)
    tk.Button(hb, text="🔄  UPDATE", command=lambda: check_for_updates(silent=False),
              bg=DT_BTN, fg=DT_SUBTEXT,
              font=('Segoe UI', 9), padx=10, pady=6).pack(side='right', padx=4, pady=10)
    if current_mode != "BACKTEST":
        tk.Button(hb, text="🏦  ÚČTY", command=open_accounts_manager,
                  bg=DT_BTN, fg=DT_TEXT,
                  font=('Segoe UI', 9), padx=10, pady=6).pack(side='right', padx=4, pady=10)
    # ── Backtesting stopky ────────────────────────────────────────────────────
    _bt_init_sec = _bt_sw_total_seconds()
    _bt_h = _bt_init_sec // 3600; _bt_m = (_bt_init_sec % 3600) // 60
    _bt_label = f"⏱  {_bt_h:02d}:{_bt_m:02d}  ▶" if _bt_init_sec > 0 else "⏱  START"
    bt_sw_btn = tk.Button(hb,
              text=_bt_label,
              command=_bt_sw_toggle,
              bg='#3b0764' if bt_sw_running else '#451a03',
              fg='#c084fc' if bt_sw_running else '#fbbf24',
              font=('Segoe UI', 9, 'bold'), padx=10, pady=6,
              relief='flat', cursor='hand2')
    bt_sw_btn.pack(side='right', padx=4, pady=10)
    bt_sw_btn.bind('<Button-3>', _bt_sw_right_click)
    # Pokud stopky běžely a uživatel znovu otevřel show_main_screen, obnov tick
    if bt_sw_running and bt_sw_after_id is None:
        _bt_sw_tick()

    # XP badge — zobrazí aktuální rank a XP
    _xp_data_init = load_xp_data()
    _xp_total_init = _xp_data_init.get('total_xp', 0)
    _xp_ri_init    = get_rank_info(_xp_total_init)
    xp_badge_btn = tk.Button(hb,
              text=f"{_xp_ri_init['emoji']} {_xp_total_init} XP",
              command=open_xp_overview,
              bg='#451a03', fg='#fbbf24',
              font=('Segoe UI', 9, 'bold'), padx=10, pady=6, relief='flat', cursor='hand2')
    xp_badge_btn.pack(side='right', padx=4, pady=10)
    tk.Button(hb, text="🏆  Žebříček", command=open_leaderboard,
              bg='#1e3a5f', fg='#60a5fa',
              font=('Segoe UI', 9, 'bold'), padx=10, pady=6, relief='flat', cursor='hand2').pack(side='right', padx=4, pady=10)
    tk.Button(hb, text="📖  DENÍK", command=show_journal_screen,
              bg=DT_BTN, fg=DT_TEXT,
              font=('Segoe UI', 9), padx=10, pady=6).pack(side='right', padx=4, pady=10)
    tk.Button(hb, text="📝  PRAVIDLA", command=open_checklist_editor,
              bg=DT_BTN, fg=DT_TEXT,
              font=('Segoe UI', 9), padx=10, pady=6).pack(side='right', padx=4, pady=10)

    nb = ttk.Notebook(root); nb.pack(fill='both', expand=True, padx=5, pady=5)
    main_notebook = nb
    _make_tabs_draggable(nb)
    
    # TAB 1
    tab1 = ttk.Frame(nb); nb.add(tab1, text='  ZÁPIS  ')
    paned = tk.PanedWindow(tab1, orient='horizontal', sashwidth=4, sashrelief='raised'); paned.pack(fill='both', expand=True)
    f_side = tk.Frame(paned); paned.add(f_side, minsize=480)
    canv = tk.Canvas(f_side); scb = ttk.Scrollbar(f_side, command=canv.yview); canv.pack(side='left', fill='both', expand=True); scb.pack(side='right', fill='y')
    f = tk.LabelFrame(canv, text="PARAMETRY OBCHODU", font=('Arial', 10, 'bold'), padx=20, pady=20); canv.create_window((0,0), window=f, anchor='nw'); f.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all"))); canv.configure(yscrollcommand=scb.set)

    r = 0
    def check_news_for_current_date():
        d = cas_otevreni_entry.get().strip()
        if d: open_ff_calendar_for_date(d)
        else: messagebox.showwarning("Chyba", "Zadejte nejprve Datum otevření.")

    tk.Button(f, text="🌍 OTEVŘÍT KALENDÁŘ (FOREX FACTORY)", command=open_external_calendar, bg="#95a5a6", fg="white", font=("Arial", 8)).grid(row=r, column=0, columnspan=2, pady=5); r+=1

    def screenshot_prefill(data):
        """Vyplní formulář hodnotami detekovanými ze screenshotu."""
        def set_entry(widget, val):
            widget.config(state='normal')
            widget.delete(0, 'end')
            widget.insert(0, val)
        if data.get('symbol'):
            symbol_combo.set(data['symbol'])
        if data.get('vstupni_hodnota'):
            set_entry(vstupni_hodnota_entry, data['vstupni_hodnota'])
        if data.get('stoploss'):
            set_entry(stoploss_entry, data['stoploss'])
        if data.get('takeprofit'):
            set_entry(takeprofit_entry, data['takeprofit'])
        if data.get('cas_otevreni'):
            set_entry(cas_otevreni_entry, data['cas_otevreni'])
        if data.get('cas_zavreni'):
            set_entry(cas_zavreni_entry, data['cas_zavreni'])
        if data.get('timeframe_vstup'):
            ltf_combo.set(data['timeframe_vstup'])
        if data.get('smer'):
            smer_var.set(data['smer'])
        update_calculated_fields()
        calculate_auto_rrr()
        calculate_auto_score()

    tk.Button(f, text="📎 ANALYZOVAT SCREENSHOT (auto-fill)",
              command=lambda: show_screenshot_dialog(screenshot_prefill),
              bg="#6366f1", fg="white", font=("Arial", 8, "bold")).grid(row=r, column=0, columnspan=2, pady=(0,8)); r+=1
    
    tk.Label(f, text="Čas otevření:").grid(row=r, column=0, sticky='w'); cas_otevreni_entry = tk.Entry(f, width=35); cas_otevreni_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="Čas uzavření:").grid(row=r, column=0, sticky='w'); cas_zavreni_entry = tk.Entry(f, width=35); cas_zavreni_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="Délka / Den:").grid(row=r, column=0, sticky='w'); fd = tk.Frame(f); fd.grid(row=r, column=1, sticky='w'); delka_obchodu_entry = tk.Entry(fd, width=15, state='readonly'); delka_obchodu_entry.pack(side='left'); den_tydne_entry = tk.Entry(fd, width=15, state='readonly', font=('Segoe UI', 9)); den_tydne_entry.pack(side='left', padx=5); r+=1
    # ── Výběr účtu — jen v REAL módu ─────────────────────────────────────────
    if current_mode != "BACKTEST":
        ucet_row = tk.Frame(f); ucet_row.grid(row=r, column=0, columnspan=2, sticky='we', pady=(6,2)); r+=1
        ucet_lbl = tk.Frame(ucet_row, bg='#1e293b', padx=8, pady=4); ucet_lbl.pack(fill='x')
        tk.Label(ucet_lbl, text="🏦  Účet:", font=('Segoe UI', 9, 'bold'),
                 bg='#1e293b', fg='#93c5fd').pack(side='left')
        accounts_combo = ttk.Combobox(ucet_lbl, values=get_account_dropdown_values(),
                                      state='readonly', width=42, font=('Segoe UI', 9))
        acvals = get_account_dropdown_values()
        accounts_combo.set(acvals[0] if acvals else '')
        accounts_combo.pack(side='left', padx=8)
        tk.Button(ucet_lbl, text="⚙ Spravovat", bg='#1e3a5f', fg='#93c5fd',
                  font=('Segoe UI', 8), relief='flat', padx=6, cursor='hand2',
                  command=open_accounts_manager).pack(side='left')
    else:
        accounts_combo = None  # BACKTEST — účet se neeviduje

    tk.Label(f, text="Symbol:").grid(row=r, column=0, sticky='w'); symbol_combo = ttk.Combobox(f, values=PAIRS, width=33); symbol_combo.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="Směr:").grid(row=r, column=0, sticky='w'); smer_var = tk.StringVar(value="Buy"); sf = tk.Frame(f); sf.grid(row=r, column=1, sticky='w'); tk.Radiobutton(sf, text="BUY", variable=smer_var, value="Buy", fg=DT_WIN_FG, font=('Arial', 9, 'bold')).pack(side='left'); tk.Radiobutton(sf, text="SELL", variable=smer_var, value="Sell", fg=DT_LOSS_FG, font=('Arial', 9, 'bold')).pack(side='left'); r+=1
    tk.Label(f, text="ENTRY PRICE:", font=('Arial', 9, 'bold')).grid(row=r, column=0, sticky='w'); vstupni_hodnota_entry = tk.Entry(f, width=35); vstupni_hodnota_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="TAKE PROFIT:", fg=DT_WIN_FG, font=('Arial', 9, 'bold')).grid(row=r, column=0, sticky='w'); takeprofit_entry = tk.Entry(f, width=35); takeprofit_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="STOP LOSS:", fg=DT_LOSS_FG, font=('Arial', 9, 'bold')).grid(row=r, column=0, sticky='w'); stoploss_entry = tk.Entry(f, width=35); stoploss_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="Vypočtené RRR:").grid(row=r, column=0, sticky='w'); rrr_entry = tk.Entry(f, width=35); rrr_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="SL v Pipsech:").grid(row=r, column=0, sticky='w'); pips_entry = tk.Entry(f, width=35, state='readonly', fg='blue'); pips_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="HTF Graf / LTF Vstup:").grid(row=r, column=0, sticky='w'); ft = tk.Frame(f); ft.grid(row=r, column=1, sticky='w'); htf_combo = ttk.Combobox(ft, values=TIMEFRAMES, width=14); htf_combo.pack(side='left'); ltf_combo = ttk.Combobox(ft, values=TIMEFRAMES, width=14); ltf_combo.pack(side='left', padx=5); r+=1
    tk.Label(f, text="Setup / Seance:").grid(row=r, column=0, sticky='w'); fs = tk.Frame(f); fs.grid(row=r, column=1, sticky='w'); fibo_combo = ttk.Combobox(fs, values=FIBO_OPTIONS, width=15); fibo_combo.pack(side='left'); session_combo = ttk.Combobox(fs, values=SESSIONS_LIST, width=15); session_combo.pack(side='left', padx=5); r+=1
    
    # NOVÉ NEWS UI
    tk.Label(f, text="High Impact News?:").grid(row=r, column=0, sticky='w'); 
    news_f = tk.Frame(f); news_f.grid(row=r, column=1, sticky='w')
    news_var = tk.StringVar(value="Ne"); news_cb = ttk.Combobox(news_f, textvariable=news_var, values=["Ano", "Ne"], width=10); news_cb.pack(side='left')
    tk.Button(news_f, text="🌍 ZJISTIT (FF)", command=check_news_for_current_date, bg="#e67e22", fg="white", font=("Arial", 7, "bold")).pack(side='left', padx=5)
    r+=1
    
    tk.Label(f, text="Zprávy (Fundament):").grid(row=r, column=0, sticky='w'); news_event_entry = tk.Entry(f, width=35); news_event_entry.grid(row=r, column=1, pady=3); r+=1

    # NOVÉ: Štítky
    tk.Label(f, text="Štítky (Tags):").grid(row=r, column=0, sticky='w')
    tags_entry = tk.Entry(f, width=35); tags_entry.grid(row=r, column=1, pady=3)
    tk.Label(f, text="(např: #trend #agresivni)", font=("Arial", 7), fg="gray").grid(row=r+1, column=1, sticky='n'); r+=2
    
    tk.Label(f, text="Důvod vstupu:").grid(row=r, column=0, sticky='w'); duvod_entry = tk.Entry(f, width=35); duvod_entry.grid(row=r, column=1, pady=3); r+=1
    tk.Label(f, text="Poznámka:").grid(row=r, column=0, sticky='w'); poznamka_entry = tk.Entry(f, width=35); poznamka_entry.grid(row=r, column=1, pady=3); r+=1

    # ── Zisk / Ztráta — jen v REAL módu ──────────────────────────────────────
    if current_mode != "BACKTEST":
        _cur = get_app_currency()
        tk.Label(f, text=f"Zisk/Ztráta ({_cur}):").grid(row=r, column=0, sticky='w')
        _pnl_frame = tk.Frame(f)
        _pnl_frame.grid(row=r, column=1, sticky='w', pady=4)
        zisk_mena_entry = tk.Entry(_pnl_frame, width=16, font=('Arial', 10))
        zisk_mena_entry.pack(side='left')
        tk.Label(_pnl_frame, text=f" {_cur}", fg=DT_SUBTEXT, font=('Arial', 9)).pack(side='left')

        def _open_currency_calc():
            """Mini kalkulačka měn — přepočet částky na domácí měnu."""
            cc = tk.Toplevel(root)
            cc.title("💱 Kalkulačka měn")
            cc.configure(bg=DT_BG)
            cc.geometry("320x230")
            cc.resizable(False, False)
            cc.grab_set()
            tk.Label(cc, text="💱  Kalkulačka měn", bg=DT_BG, fg=DT_TEXT,
                     font=('Segoe UI', 11, 'bold')).pack(pady=(14, 10))
            frm = tk.Frame(cc, bg=DT_BG, padx=20)
            frm.pack(fill='x')
            def _lbl(text): return tk.Label(frm, text=text, bg=DT_BG, fg=DT_SUBTEXT, font=('Segoe UI', 9), anchor='w', width=16)
            def _ent(default=''): e = tk.Entry(frm, bg=DT_SURFACE, fg=DT_TEXT, insertbackground=DT_TEXT, font=('Segoe UI', 10), relief='flat', bd=4); e.insert(0, str(default)); return e

            r2 = tk.Frame(frm, bg=DT_BG); r2.pack(fill='x', pady=3)
            _lbl("Částka:").pack(in_=r2, side='left')
            _from_e = _ent(zisk_mena_entry.get() or '0'); _from_e.pack(in_=r2, side='left', fill='x', expand=True)

            r3 = tk.Frame(frm, bg=DT_BG); r3.pack(fill='x', pady=3)
            _lbl("Kurz (1 → CZK):").pack(in_=r3, side='left')
            _rate_e = _ent('23.5'); _rate_e.pack(in_=r3, side='left', fill='x', expand=True)

            res_var = tk.StringVar(value='—')
            res_lbl = tk.Label(cc, textvariable=res_var, bg=DT_SURFACE, fg=DT_ACCENT,
                               font=('Segoe UI', 13, 'bold'), pady=8)
            res_lbl.pack(fill='x', padx=20, pady=(8, 4))

            def _calc():
                try:
                    amt  = float(_from_e.get().replace(',', '.').replace(' ', ''))
                    rate = float(_rate_e.get().replace(',', '.'))
                    result = amt * rate
                    res_var.set(f"{result:+,.2f} {_cur}")
                except ValueError:
                    res_var.set("Neplatné číslo")

            def _use():
                try:
                    amt  = float(_from_e.get().replace(',', '.').replace(' ', ''))
                    rate = float(_rate_e.get().replace(',', '.'))
                    result = amt * rate
                    zisk_mena_entry.delete(0, tk.END)
                    zisk_mena_entry.insert(0, f"{result:.2f}")
                except ValueError: pass
                cc.destroy()

            bf = tk.Frame(cc, bg=DT_BG); bf.pack(pady=6)
            tk.Button(bf, text="Vypočítat", command=_calc, bg=DT_BTN, fg=DT_TEXT,
                      font=('Segoe UI', 9), padx=10, pady=5, relief='flat').pack(side='left', padx=4)
            tk.Button(bf, text="✓ Použít výsledek", command=_use, bg=DT_ACCENT, fg='#fff',
                      font=('Segoe UI', 9, 'bold'), padx=10, pady=5, relief='flat').pack(side='left', padx=4)

        tk.Button(_pnl_frame, text="💱", command=_open_currency_calc,
                  bg=DT_SURFACE, fg=DT_ACCENT, font=('Segoe UI', 10),
                  relief='flat', padx=6, pady=1, cursor='hand2').pack(side='left', padx=(6, 0))
        r += 1
    else:
        zisk_mena_entry = None  # BACKTEST — zisk se neeviduje

    tk.Label(f, text="VÝSLEDEK:").grid(row=r, column=0, sticky='w'); vysledek_combo = ttk.Combobox(f, values=["Win", "Loss", "BE"], width=33); vysledek_combo.grid(row=r, column=1, pady=10); r+=1
    obrazky_list = tk.StringVar(); tk.Button(f, text="+ SCREENSHOTY", command=pridat_obrazky, bg='#3498db', fg='white', width=30).grid(row=r, column=1, sticky='w'); r+=1
    score_label = tk.Label(f, text="BODOVÁNÍ: 0 | SKÓRE: C", font=('Arial', 11, 'bold'), pady=10); score_label.grid(row=r, column=0, columnspan=2); r+=1
    save_btn = tk.Button(f, text="ULOŽIT OBCHOD", font=('Arial', 10, 'bold'), bg='#2ecc71', fg='white', height=2, command=pridat_obchod); save_btn.grid(row=r, column=0, columnspan=2, sticky='we', pady=5); r+=1
    slippage_entry = tk.Entry(f); slippage_entry.insert(0, "0")

    h_side = tk.Frame(paned, padx=0, pady=0); paned.add(h_side)
    v_paned = tk.PanedWindow(h_side, orient='vertical', sashwidth=4, bg='#bdc3c7', sashrelief='raised'); v_paned.pack(fill='both', expand=True)

    top_pane = tk.Frame(v_paned, padx=10, pady=10); v_paned.add(top_pane, minsize=200, height=450)
    rh = tk.Frame(top_pane); rh.pack(fill='x')
    tk.Label(rh, text="HISTORIE OBCHODŮ", font=('Arial', 9, 'bold')).pack(side='left')
    hb_right = tk.Frame(rh); hb_right.pack(side='right')
    tk.Button(hb_right, text="📄 EXPORT PDF", command=export_trade_to_pdf, font=('Arial', 8), bg="#9b59b6", fg="white").pack(side='left', padx=5)
    tk.Button(hb_right, text="⚙ SLOUPCE", command=open_column_config, font=('Arial', 8), bg="#34495e", fg="white").pack(side='left')

    # === MULTI-FILTR PANEL ===
    # ── FILTER BAR ──────────────────────────────────────────────────────────
    filter_outer = tk.Frame(top_pane, bg='#2c3e50')
    filter_outer.pack(fill='x', pady=(4, 0))

    # Skrývací tělo
    flt_body = tk.Frame(top_pane, bg='#eaecee', pady=4, padx=6)
    flt_body.pack(fill='x')

    _flt_vis = [True]
    def _toggle_flt():
        if _flt_vis[0]:
            flt_body.pack_forget(); _toggle_flt_btn.config(text="▼")
        else:
            flt_body.pack(fill='x', before=_flt_anchor); _toggle_flt_btn.config(text="▲")
        _flt_vis[0] = not _flt_vis[0]

    tk.Label(filter_outer, text="  🔍 FILTRY", bg='#2c3e50', fg='white',
             font=('Segoe UI', 8, 'bold')).pack(side='left', pady=3)
    _toggle_flt_btn = tk.Button(filter_outer, text="▲", command=_toggle_flt,
                                bg='#34495e', fg='white', font=('Segoe UI', 8),
                                bd=0, padx=8, cursor='hand2')
    _toggle_flt_btn.pack(side='right', padx=4, pady=2)

    def _open_filter_config():
        """Dialog pro výběr viditelných filtrů."""
        cfg_win = tk.Toplevel(root)
        cfg_win.title("Konfigurace filtrů")
        cfg_win.resizable(False, False)
        cfg_win.configure(bg=DT_BG)
        cfg_win.geometry("260x320")
        cfg_win.lift(); cfg_win.focus_set()
        tk.Label(cfg_win, text="⚙  Zobrazené filtry", bg='#2c3e50', fg='white',
                 font=('Segoe UI', 11, 'bold'), pady=10).pack(fill='x')
        body_cfg = tk.Frame(cfg_win, bg=DT_BG, padx=18, pady=10)
        body_cfg.pack(fill='both', expand=True)
        _all_chips = ['Symbol', 'Výsledek', 'Seance', 'Štítky', 'Od', 'Do', 'RRR', 'Uložené']
        cur_vis = load_saved_filters().get('chip_visibility', {})
        _vars = {}
        for name in _all_chips:
            v = tk.BooleanVar(value=cur_vis.get(name, True))
            _vars[name] = v
            tk.Checkbutton(body_cfg, text=name, variable=v, bg=DT_BG, fg=DT_TEXT,
                           activebackground=DT_BG, selectcolor=DT_SURFACE,
                           font=('Segoe UI', 10)).pack(anchor='w', pady=2)
        bf_cfg = tk.Frame(cfg_win, bg=DT_BG, padx=18, pady=10)
        bf_cfg.pack(fill='x', side='bottom')
        def _apply_cfg():
            new_vis = {n: _vars[n].get() for n in _all_chips}
            data = load_saved_filters()
            data['chip_visibility'] = new_vis
            save_saved_filters(data)
            for name, frame in _chip_frames.items():
                try:
                    if new_vis.get(name, True):
                        frame.pack(side='left', padx=3, pady=1, ipady=2)
                    else:
                        frame.pack_forget()
                except Exception:
                    pass
            row_a.update_idletasks()
            flt_canvas.configure(scrollregion=flt_canvas.bbox('all'))
            cfg_win.destroy()
        tk.Button(bf_cfg, text="Použít", command=_apply_cfg,
                  bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
                  padx=14, pady=6, relief='flat', cursor='hand2').pack(side='left')
        tk.Button(bf_cfg, text="Zrušit", command=cfg_win.destroy,
                  bg=DT_BTN, fg=DT_TEXT, font=('Segoe UI', 9),
                  padx=10, pady=6, relief='flat', cursor='hand2').pack(side='left', padx=(8, 0))

    tk.Button(filter_outer, text="⚙", command=_open_filter_config,
              bg='#2c3e50', fg='#7f8c8d', font=('Segoe UI', 9),
              bd=0, padx=8, cursor='hand2').pack(side='right', padx=0, pady=2)
    tk.Button(filter_outer, text="Uložit", command=lambda: save_current_filter(saved_combo_flt),
              bg='#8e44ad', fg='white', font=('Segoe UI', 8), bd=0, padx=8, cursor='hand2'
              ).pack(side='right', padx=2, pady=2)
    tk.Button(filter_outer, text="Reset", command=reset_filter,
              bg='#e74c3c', fg='white', font=('Segoe UI', 8), bd=0, padx=8, cursor='hand2'
              ).pack(side='right', padx=2, pady=2)
    tk.Button(filter_outer, text="Použít", command=apply_filter,
              bg='#27ae60', fg='white', font=('Segoe UI', 8, 'bold'), bd=0, padx=10, cursor='hand2'
              ).pack(side='right', padx=2, pady=2)

    # Řádek s filtry — scrollovatelný canvas (pevná výška, žádné expand)
    flt_canvas = tk.Canvas(flt_body, bg='#eaecee', height=36, highlightthickness=0)
    flt_xsb = ttk.Scrollbar(flt_body, orient='horizontal', command=flt_canvas.xview)
    flt_canvas.configure(xscrollcommand=flt_xsb.set)
    flt_xsb.pack(fill='x', side='bottom')
    flt_canvas.pack(fill='x', pady=(2, 0))
    row_a = tk.Frame(flt_canvas, bg='#eaecee')
    _flt_win = flt_canvas.create_window((0, 0), window=row_a, anchor='nw')
    def _flt_configure(e=None):
        flt_canvas.configure(scrollregion=flt_canvas.bbox('all'))
    row_a.bind('<Configure>', _flt_configure)
    flt_canvas.bind('<MouseWheel>', lambda e: flt_canvas.xview_scroll(int(-1*(e.delta/120)), 'units'))

    def chip(parent, lbl, widget):
        """Bílý rámeček s popiskem + widgetem. Vrací frame pro show/hide."""
        f = tk.Frame(parent, bg='white', relief='solid', bd=1)
        f.pack(side='left', padx=3, pady=1, ipady=2)
        tk.Label(f, text=lbl, bg='white', fg='#555', font=('Segoe UI', 7, 'bold'), padx=5).pack(side='left')
        widget(f).pack(side='left', padx=(0, 5))
        return f

    _chip_frames = {}
    def chip_t(parent, lbl, widget):
        """chip() s ukládáním reference pro konfiguraci viditelnosti."""
        f = chip(parent, lbl, widget)
        _chip_frames[lbl] = f
        # Skryj pokud uložená konfig říká skrýt
        _vis = load_saved_filters().get('chip_visibility', {})
        if not _vis.get(lbl, True):
            f.pack_forget()
        return f

    chip_t(row_a, "Symbol",    lambda f: ttk.Combobox(f, textvariable=filter_symbol_var, values=["VŠE"]+PAIRS, width=10, state='readonly'))
    chip_t(row_a, "Výsledek",  lambda f: ttk.Combobox(f, textvariable=filter_result_var, values=["VŠE","Win","Loss","BE"], width=7, state='readonly'))
    chip_t(row_a, "Seance",    lambda f: ttk.Combobox(f, textvariable=filter_session_var, values=["VŠE"]+SESSIONS_LIST, width=9, state='readonly'))

    # Tag filter — dynamický seznam hashtagů z obchodů
    def _load_project_tags():
        tags = set()
        try:
            import glob as _glob
            p_dir = os.path.join(BASE_DIR, current_project_name)
            for csv_f in _glob.glob(os.path.join(p_dir, '*.csv')):
                with open(csv_f, 'r', encoding='utf-8') as _f:
                    for row in csv.DictReader(_f):
                        for t in row.get('tags','').replace(',',' ').split():
                            if t.startswith('#'): tags.add(t)
        except Exception: pass
        return ["VŠE"] + sorted(tags)

    _tag_combo_ref = [None]
    def _make_tag_combo(f):
        cb = ttk.Combobox(f, textvariable=filter_tag_var, values=_load_project_tags(), width=12)
        cb.bind('<Button-1>', lambda e: cb.configure(values=_load_project_tags()))
        _tag_combo_ref[0] = cb
        return cb
    chip_t(row_a, "Štítky", _make_tag_combo)
    chip_t(row_a, "Od",        lambda f: tk.Entry(f, textvariable=filter_date_from_var, width=11, bg='white', relief='flat'))
    chip_t(row_a, "Do",        lambda f: tk.Entry(f, textvariable=filter_date_to_var, width=11, bg='white', relief='flat'))

    # RRR chip
    rrr_f = tk.Frame(row_a, bg='white', relief='solid', bd=1)
    rrr_f.pack(side='left', padx=3, pady=1, ipady=2)
    _chip_frames['RRR'] = rrr_f
    if not load_saved_filters().get('chip_visibility', {}).get('RRR', True): rrr_f.pack_forget()
    tk.Label(rrr_f, text="RRR", bg='white', fg='#555', font=('Segoe UI', 7, 'bold'), padx=5).pack(side='left')
    rrr_min_e = tk.Entry(rrr_f, textvariable=filter_rrr_min_var, width=4, bg='white', relief='flat'); rrr_min_e.pack(side='left')
    tk.Label(rrr_f, text="–", bg='white', fg='#888').pack(side='left')
    rrr_max_e = tk.Entry(rrr_f, textvariable=filter_rrr_max_var, width=4, bg='white', relief='flat'); rrr_max_e.pack(side='left', padx=(0, 4))

    # Uložené filtry chip
    saved_flt_var = tk.StringVar()
    sf = tk.Frame(row_a, bg='white', relief='solid', bd=1)
    sf.pack(side='left', padx=3, pady=1, ipady=2)
    _chip_frames['Uložené'] = sf
    if not load_saved_filters().get('chip_visibility', {}).get('Uložené', True): sf.pack_forget()
    tk.Label(sf, text="💾 Uložené", bg='white', fg='#555', font=('Segoe UI', 7, 'bold'), padx=5).pack(side='left')
    saved_combo_flt = ttk.Combobox(sf, textvariable=saved_flt_var, width=12, state='readonly')
    saved_flt_data = load_saved_filters()
    saved_combo_flt['values'] = list(saved_flt_data.keys())
    saved_combo_flt.pack(side='left', padx=(0, 4))

    # Bind events
    for w in row_a.winfo_children():
        for child in w.winfo_children():
            if isinstance(child, ttk.Combobox): child.bind('<<ComboboxSelected>>', lambda e: apply_filter())
            if isinstance(child, tk.Entry): child.bind('<Return>', lambda e: apply_filter())
    rrr_min_e.bind('<Return>', lambda e: apply_filter())
    rrr_max_e.bind('<Return>', lambda e: apply_filter())
    saved_combo_flt.bind('<<ComboboxSelected>>', lambda e: apply_saved_filter_by_name(saved_flt_var.get(), saved_combo_flt) or None)

    # Inicializace scrollregion — filtry viditelné hned od startu
    row_a.update_idletasks()
    flt_canvas.configure(scrollregion=flt_canvas.bbox('all'))

    # Anchor pro toggle (musí být za flt_body)
    _flt_anchor = tk.Frame(top_pane, height=0, bg=DT_PANEL); _flt_anchor.pack(fill='x')

    tree_frame = tk.Frame(top_pane); tree_frame.pack(fill='both', expand=True, pady=5)
    cfg = load_scoring_config(); current_cols = cfg.get("columns", DEFAULT_SCORING["columns"])
    trades_tree = ttk.Treeview(tree_frame, columns=current_cols, show='headings', selectmode='browse')
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=trades_tree.yview); hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=trades_tree.xview)
    trades_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set); trades_tree.grid(column=0, row=0, sticky='nsew'); vsb.grid(column=1, row=0, sticky='ns'); hsb.grid(column=0, row=1, sticky='ew')
    tree_frame.grid_columnconfigure(0, weight=1); tree_frame.grid_rowconfigure(0, weight=1)
    for col in current_cols:
        trades_tree.heading(col, text=COL_TRANSLATION.get(col, col), anchor='center',
                            command=lambda c=col: _tree_sort(c))
        trades_tree.column(col, width=100, minwidth=50, anchor='center', stretch=False)
    trades_tree.bind('<<TreeviewSelect>>', show_trade_details)
    
    btn_box = tk.Frame(top_pane); btn_box.pack(anchor='e', pady=2)
    tk.Button(btn_box, text="UPRAVIT VYBRANÝ", command=naci_obchod_pro_upravu, bg='#f39c12', fg='white', font=('Arial', 8, 'bold')).pack(side='left', padx=5)
    tk.Button(btn_box, text="📋 DUPLIKOVAT", command=duplikovat_obchod, bg='#8e44ad', fg='white', font=('Arial', 8, 'bold')).pack(side='left', padx=5)
    tk.Button(btn_box, text="Smazat vybraný", command=smazat_obchod, bg='#e74c3c', fg='white', font=('Arial', 8)).pack(side='left')

    bottom_pane = tk.Frame(v_paned, padx=10, pady=10); v_paned.add(bottom_pane, minsize=150)
    bp_header = tk.Frame(bottom_pane); bp_header.pack(fill='x')
    tk.Label(bp_header, text="DETAIL OBCHODU", font=('Arial', 9, 'bold')).pack(side='left')
    
    def jump_to_journal():
        if trades_tree:
            sel = trades_tree.selection()
            if sel:
                idx = int(sel[0]); trades = load_data(); t = trades[idx]
                if t.get('cas_otevreni'): go_to_journal_for_trade(t['cas_otevreni'][:10])

    def jump_to_ff_details():
        if trades_tree:
            sel = trades_tree.selection()
            if sel:
                idx = int(sel[0]); trades = load_data(); t = trades[idx]
                d = t.get('cas_otevreni', '').strip()
                if d: open_ff_calendar_for_date(d)
    
    if current_mode == "REAL":
        tk.Button(bp_header, text="📖 ZOBRAZIT ZÁPIS Z DENÍKU", command=jump_to_journal, bg="#8e44ad", fg="white", font=("Arial", 8, "bold")).pack(side='right', padx=5)
    
    tk.Button(bp_header, text="🌍 OTEVŘÍT ZPRÁVY (FF) PRO TENTO DEN", command=jump_to_ff_details, bg="#e67e22", fg="white", font=("Arial", 8, "bold")).pack(side='right')

    checklist_display_label = tk.Label(bp_header, text="", font=("Arial", 10, "bold"), padx=10)
    checklist_display_label.pack(side="right", padx=10)

    details_text = tk.Text(bottom_pane, height=10, font=('Consolas', 9), bg='#f8f9fa'); details_text.pack(fill='both', expand=True, pady=5)
    img_scroll = tk.Canvas(bottom_pane, height=120); img_scroll.pack(fill='x', pady=(5,0)); image_frame = tk.Frame(img_scroll); img_scroll.create_window((0,0), window=image_frame, anchor='nw')

    # TAB 2 — ANALÝZA (redesigned)
    tab2 = ttk.Frame(nb); nb.add(tab2, text='  ANALÝZA  ')
    st_canv = tk.Canvas(tab2, bg=DT_BG, highlightthickness=0)
    st_scb  = ttk.Scrollbar(tab2, command=st_canv.yview)
    st_canv.pack(side='left', fill='both', expand=True)
    st_scb.pack(side='right', fill='y')
    st_f = tk.Frame(st_canv, bg=DT_BG)
    st_canv.create_window((0, 0), window=st_f, anchor='nw')
    st_f.bind("<Configure>", lambda e: st_canv.configure(scrollregion=st_canv.bbox("all")))
    st_canv.configure(yscrollcommand=st_scb.set)

    # Mousewheel scroll
    def _an_scroll(event):
        try: st_canv.yview_scroll(int(-1*(event.delta/120)), "units")
        except: pass
    st_canv.bind_all("<MouseWheel>", _an_scroll)

    if current_mode == "REAL":
        prop_header = tk.Frame(st_f, bg=DT_PANEL, pady=6, padx=12)
        prop_header.pack(fill='x', padx=10, pady=(8, 0))
        tk.Label(prop_header, text="⚙  NASTAVENÍ ÚČTU (KAPITÁL)", bg=DT_PANEL,
                 fg=DT_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(prop_header, text="ZMĚNIT BALANCE", command=open_prop_settings,
                  bg=DT_BTN, fg=DT_TEXT, relief='flat', padx=10).pack(side="right")

    # Filter bar
    stats_ctrl_frame = tk.Frame(st_f, bg=DT_PANEL, pady=8, padx=14)
    stats_ctrl_frame.pack(fill='x', padx=10, pady=(8, 4))
    tk.Label(stats_ctrl_frame, text="SYMBOL:", bg=DT_PANEL,
             fg=DT_SUBTEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
    stats_symbol_var = tk.StringVar(value="VŠE")
    stats_symbol_combo = ttk.Combobox(stats_ctrl_frame, textvariable=stats_symbol_var,
                                      state="readonly", width=14)
    stats_symbol_combo.pack(side="left", padx=8)
    stats_symbol_combo.bind("<<ComboboxSelected>>", lambda e: update_statistics())
    tk.Button(stats_ctrl_frame, text="🧪  A/B SIMULACE", command=run_ab_simulation,
              bg=DT_BTN, fg=DT_SUBTEXT, font=("Segoe UI", 9, "bold"),
              relief='flat', padx=12, pady=4).pack(side="right", padx=4)

    # ── KPI karty ──────────────────────────────────────────────────────────────
    kpi_frame = tk.Frame(st_f, bg=DT_BG)
    kpi_frame.pack(fill='x', padx=10, pady=(6, 2))

    # ── Řada grafů: equity vlevo, koláče vpravo ────────────────────────────────
    _charts_row = tk.Frame(st_f, bg=DT_BG)
    _charts_row.pack(fill='x', padx=10, pady=(4, 0))
    stats_graph_frame = tk.Frame(_charts_row, bg=DT_BG)
    stats_graph_frame.pack(side='left', fill='both', expand=True)
    pie_graph_frame = tk.Frame(_charts_row, bg=DT_BG)
    pie_graph_frame.pack(side='right', fill='y')

    # ── Top výkon (best performers) ────────────────────────────────────────────
    _bp_hdr = tk.Frame(st_f, bg=DT_PANEL, padx=12, pady=5)
    _bp_hdr.pack(fill='x', padx=10, pady=(6, 0))
    tk.Label(_bp_hdr, text="🏆  TOP VÝKON — BEST CONDITIONS", bg=DT_PANEL,
             fg=DT_TEXT, font=("Segoe UI", 9, "bold")).pack(side='left')
    best_performers_frame = tk.Frame(st_f, bg=DT_BG)
    best_performers_frame.pack(fill='x', padx=10, pady=(2, 4))

    # ── Bar charts ─────────────────────────────────────────────────────────────
    bar_chart_frame = tk.Frame(st_f, bg=DT_BG)
    bar_chart_frame.pack(fill='both', expand=True, padx=10, pady=(4, 0))

    # ── Heatmapa ───────────────────────────────────────────────────────────────
    heatmap_graph_frame = tk.Frame(st_f, bg=DT_BG)
    heatmap_graph_frame.pack(fill='both', expand=True, padx=10, pady=(4, 0))

    # ── Tabulky statistik (nahrazuje stats_text) ───────────────────────────────
    tables_frame = tk.Frame(st_f, bg=DT_BG)
    tables_frame.pack(fill='both', expand=True, padx=10, pady=(4, 14))

    # TAB 3, 4
    tab3 = ttk.Frame(nb); nb.add(tab3, text='  GALERIE  '); _build_gallery_tab(tab3)
    
    # TAB PRAVIDLA
    tab_rules = ttk.Frame(nb); nb.add(tab_rules, text='  MOJE PRAVIDLA  ')
    setup_rules_ui(tab_rules)

    # TAB 5 (MONTE CARLO)
    tab5 = ttk.Frame(nb); nb.add(tab5, text='  MONTE CARLO  ')
    setup_monte_carlo_ui(tab5)

    # TAB PERIODY (týden / měsíc)
    tab_periods = ttk.Frame(nb); nb.add(tab_periods, text='  📅 PERIODY  ')

    # TAB TRADINGVIEW
    tab_tv = ttk.Frame(nb)
    nb.add(tab_tv, text='  TRADINGVIEW GRAF  ')

    for w in [cas_otevreni_entry, cas_zavreni_entry, vstupni_hodnota_entry, stoploss_entry, takeprofit_entry, fibo_combo, session_combo, symbol_combo]:
        w.bind('<KeyRelease>', lambda e: [update_calculated_fields(), calculate_auto_score()])
        if isinstance(w, ttk.Combobox): w.bind('<<ComboboxSelected>>', lambda e: [update_calculated_fields(), calculate_auto_score()])
    for w in [vstupni_hodnota_entry, stoploss_entry, takeprofit_entry]:
        w.bind('<KeyRelease>', calculate_auto_rrr)
    symbol_combo.bind('<<ComboboxSelected>>', lambda e: calculate_auto_rrr())

    def _wl_shortcut(event):
        focused = root.focus_get()
        if isinstance(focused, (tk.Entry, tk.Text)): return
        key = event.char.lower()
        if key == 'w': vysledek_combo.set('Win'); calculate_auto_score()
        elif key == 'l': vysledek_combo.set('Loss'); calculate_auto_score()
        elif key == 'b': vysledek_combo.set('BE'); calculate_auto_score()
    root.bind('<Key>', _wl_shortcut)

    def on_tab_changed(event):
        try:
            sel = nb.index("current")
            if sel == 1:
                update_statistics()
            elif sel == 2:
                update_gallery()
            elif sel == nb.index(tab_periods):
                if not tab_periods.winfo_children():
                    setup_periods_tab(tab_periods)
                else:
                    update_periods_analysis()
            elif sel == nb.index(tab_tv):
                if not tab_tv.winfo_children():
                    setup_tradingview_tab(tab_tv)
        except tk.TclError:
            pass

    nb.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    update_listbox(); reset_form(); update_statistics(); root.after(100, apply_saved_layout)

def show_global_rules_screen():
    global RULES_FILE
    RULES_FILE = os.path.join(BASE_DIR, 'strategy_rules.txt')
    
    for w in root.winfo_children(): w.destroy()
    h = tk.Frame(root, bg='#d35400', height=40); h.pack(fill='x')
    tk.Label(h, text="STRATEGIE & PRAVIDLA (GLOBÁLNÍ)", fg='white', bg='#d35400', font=('Arial', 10, 'bold')).pack(side='left', padx=20)
    tk.Button(h, text="ZPĚT NA MENU", command=show_intro_screen, bg='#c0392b', fg='white').pack(side='right', padx=20, pady=5)
    
    main = tk.Frame(root, padx=20, pady=20); main.pack(fill="both", expand=True)
    setup_rules_ui(main)

APP_TITLE_FILE = os.path.join(_APP_DIR, 'projects', 'app_title.txt')

def load_app_title():
    try:
        if os.path.exists(APP_TITLE_FILE):
            t = open(APP_TITLE_FILE, encoding='utf-8').read().strip()
            if t: return t
    except: pass
    return "Trade Tracker"

def save_app_title(title):
    try:
        os.makedirs('projects', exist_ok=True)
        open(APP_TITLE_FILE, 'w', encoding='utf-8').write(title)
    except: pass


def show_splash(callback):
    """Animovaný splash screen při startu, ~2.5 s."""
    splash = tk.Toplevel()
    splash.overrideredirect(True)
    w, h = 440, 270
    sw = splash.winfo_screenwidth(); sh = splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    splash.configure(bg='#0d1117')
    splash.lift(); splash.attributes('-topmost', True)

    tk.Label(splash, text="Trade Tracker", bg='#0d1117', fg='#ffffff',
             font=('Segoe UI', 30, 'bold')).pack(pady=(44, 4))
    tk.Label(splash, text="Profesionální obchodní deník", bg='#0d1117', fg='#586069',
             font=('Segoe UI', 11)).pack()

    pb_bg = tk.Canvas(splash, bg='#21262d', width=300, height=6,
                      highlightthickness=0, bd=0)
    pb_bg.pack(pady=(28, 6))
    bar = pb_bg.create_rectangle(0, 0, 0, 6, fill='#58a6ff', outline='')

    tk.Label(splash, text=f"v{VERSION}", bg='#0d1117', fg='#30363d',
             font=('Segoe UI', 9)).pack(side='bottom', anchor='e', padx=18, pady=10)

    _step = [0]
    def _anim():
        if _step[0] <= 100:
            pb_bg.coords(bar, 0, 0, _step[0] * 3, 6)
            _step[0] += 2
            splash.after(38, _anim)
        else:
            try: splash.destroy()
            except: pass
            callback()
    splash.after(80, _anim)


def import_project_from_folder():
    """Importuje projekt z libovolné složky — zkopíruje data do projektového adresáře."""
    folder = filedialog.askdirectory(title="Vyber složku projektu k importu", parent=root)
    if not folder:
        return

    # Detekuj typ projektu
    has_trades = os.path.exists(os.path.join(folder, 'trades.csv'))
    has_prop   = os.path.exists(os.path.join(folder, 'prop_config.json'))
    suggested_name = os.path.basename(folder.rstrip('/\\'))

    # Dialog pro název a typ
    dlg = tk.Toplevel(root)
    dlg.title("Import projektu")
    dlg.geometry("380x230")
    dlg.configure(bg='#ecf0f1')
    dlg.resizable(False, False)
    dlg.grab_set()

    tk.Label(dlg, text="Import projektu ze složky", font=('Segoe UI', 12, 'bold'),
             bg='#ecf0f1', fg='#2c3e50').pack(pady=(18, 4))
    tk.Label(dlg, text=f"Složka: ...{os.sep}{suggested_name}", font=('Segoe UI', 9),
             bg='#ecf0f1', fg='#555').pack()

    form = tk.Frame(dlg, bg='#ecf0f1', padx=24, pady=10)
    form.pack(fill='x')

    tk.Label(form, text="Název projektu:", bg='#ecf0f1', font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', pady=4)
    name_var = tk.StringVar(value=suggested_name)
    tk.Entry(form, textvariable=name_var, width=26).grid(row=0, column=1, padx=8)

    tk.Label(form, text="Typ:", bg='#ecf0f1', font=('Segoe UI', 9)).grid(row=1, column=0, sticky='w', pady=4)
    mode_var = tk.StringVar(value="REAL" if has_prop else "BACKTEST")
    ttk.Combobox(form, textvariable=mode_var, values=["BACKTEST", "REAL"],
                 state='readonly', width=14).grid(row=1, column=1, padx=8, sticky='w')

    result = [None]

    def _do_import():
        name = name_var.get().strip().replace(' ', '_')
        mode = mode_var.get()
        if not name:
            messagebox.showwarning("Chyba", "Zadej název projektu.", parent=dlg)
            return
        base = DIR_BACKTEST if mode == "BACKTEST" else DIR_REAL
        dest = os.path.join(base, name)
        if os.path.exists(dest):
            if not messagebox.askyesno("Přepsat?",
                    f"Projekt '{name}' již existuje. Přepsat?", parent=dlg):
                return
        try:
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(folder, dest)
            result[0] = (mode, name)
            dlg.destroy()
        except Exception as ex:
            messagebox.showerror("Chyba importu", str(ex), parent=dlg)

    bf = tk.Frame(dlg, bg='#ecf0f1')
    bf.pack(pady=(0, 14))
    tk.Button(bf, text="Importovat", command=_do_import,
              bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
              padx=16, pady=6, relief='flat').pack(side='left', padx=6)
    tk.Button(bf, text="Zrušit", command=dlg.destroy,
              bg='#e74c3c', fg='white', font=('Segoe UI', 9),
              padx=12, pady=6, relief='flat').pack(side='left')

    dlg.wait_window()
    if result[0]:
        mode, name = result[0]
        messagebox.showinfo("Hotovo", f"Projekt '{name}' importován jako {mode}.")
        show_intro_screen()

def show_intro_screen():
    global root
    for w in root.winfo_children(): w.destroy()
    main_container = tk.Frame(root, bg=DT_BG); main_container.pack(fill="both", expand=True)

    # Název — kliknutím na ✏️ se dá přepsat
    title_frame = tk.Frame(main_container, bg=DT_BG); title_frame.pack(pady=(35, 5))
    title_var = tk.StringVar(value=load_app_title())
    title_lbl = tk.Label(title_frame, textvariable=title_var, bg=DT_BG,
                         font=('Arial', 24, 'bold'), fg=DT_TEXT)
    title_lbl.pack(side='left')

    def edit_title():
        new = simpledialog.askstring("Změnit název", "Zadej nový název aplikace:",
                                     initialvalue=title_var.get(), parent=root)
        if new and new.strip():
            title_var.set(new.strip())
            save_app_title(new.strip())
            root.title(new.strip())

    tk.Button(title_frame, text="✏️", command=edit_title, bg=DT_BG, fg=DT_SUBTEXT,
              relief='flat', font=('Arial', 14), cursor='hand2',
              activebackground=DT_BG).pack(side='left', padx=(8, 0))
    tk.Label(main_container, text=f"v{VERSION}", bg=DT_BG, fg=DT_SUBTEXT,
             font=('Segoe UI', 9)).pack(side='bottom', anchor='e', padx=18, pady=6)
    grid_frame = tk.Frame(main_container, bg=DT_BG); grid_frame.pack(expand=True)

    f1 = tk.Frame(grid_frame, bg=DT_PANEL, relief="flat", borderwidth=0, width=300, height=400); f1.grid(row=0, column=0, padx=20, pady=20); f1.pack_propagate(False)
    tk.Label(f1, text="⛏ BACKTEST", font=('Arial', 16, 'bold'), bg=DT_ACCENT, fg="#ffffff", pady=10).pack(fill="x")
    tk.Label(f1, text="Analýza historických dat.", bg=DT_PANEL, fg=DT_SUBTEXT, pady=10).pack()
    lb1 = tk.Listbox(f1, height=8, width=30, borderwidth=0, bg=DT_SURFACE, fg=DT_TEXT,
                     selectbackground=DT_ACCENT, selectforeground="#ffffff"); lb1.pack(pady=10, padx=10)
    if os.path.exists(DIR_BACKTEST):
        for p in sorted(os.listdir(DIR_BACKTEST)): lb1.insert(tk.END, p)
    tk.Button(f1, text="+ NOVÝ BACKTEST", command=lambda: create_new_project("BACKTEST"), bg="#2ecc71", fg="white").pack(fill="x", padx=20, pady=5)
    tk.Button(f1, text="OTEVŘÍT", command=lambda: open_project(lb1, "BACKTEST"), bg="#34495e", fg="white").pack(fill="x", padx=20, pady=(0, 5))
    tk.Button(f1, text="🗑 SMAZAT PROJEKT", command=lambda: delete_project(lb1, "BACKTEST"), bg="#e74c3c", fg="white").pack(fill="x", padx=20, pady=(0, 15))

    f2 = tk.Frame(grid_frame, bg=DT_PANEL, relief="flat", borderwidth=0, width=300, height=400); f2.grid(row=0, column=1, padx=20, pady=20); f2.pack_propagate(False)
    tk.Label(f2, text="📈 REAL TRADING", font=('Arial', 16, 'bold'), bg=DT_ACCENT, fg="#ffffff", pady=10).pack(fill="x")
    tk.Label(f2, text="FTMO / Prop Firm management.", bg=DT_PANEL, fg=DT_SUBTEXT, pady=10).pack()
    lb2 = tk.Listbox(f2, height=8, width=30, borderwidth=0, bg=DT_SURFACE, fg=DT_TEXT,
                     selectbackground=DT_ACCENT, selectforeground="#ffffff"); lb2.pack(pady=10, padx=10)
    if os.path.exists(DIR_REAL):
        for p in sorted(os.listdir(DIR_REAL)): lb2.insert(tk.END, p)
    tk.Button(f2, text="+ NOVÝ PROJEKT", command=lambda: create_new_project("REAL"), bg="#2ecc71", fg="white").pack(fill="x", padx=20, pady=5)
    tk.Button(f2, text="OTEVŘÍT", command=lambda: open_project(lb2, "REAL"), bg="#2980b9", fg="white").pack(fill="x", padx=20, pady=(0, 5))
    tk.Button(f2, text="🗑 SMAZAT PROJEKT", command=lambda: delete_project(lb2, "REAL"), bg="#e74c3c", fg="white").pack(fill="x", padx=20, pady=(0, 15))

    f3 = tk.Frame(grid_frame, bg=DT_PANEL, relief="flat", borderwidth=0, width=300, height=400); f3.grid(row=0, column=2, padx=20, pady=20); f3.pack_propagate(False)
    tk.Label(f3, text="🧠 DENÍK", font=('Arial', 16, 'bold'), bg=DT_ACCENT, fg="#ffffff", pady=10).pack(fill="x")
    tk.Label(f3, text="Psychologie a emoce.", bg=DT_PANEL, fg=DT_SUBTEXT, pady=10).pack()
    tk.Label(f3, text="📅", font=('Arial', 50), bg=DT_PANEL, fg=DT_TEXT).pack(pady=30)
    tk.Button(f3, text="OTEVŘÍT DENÍK", command=show_journal_screen, bg="#8e44ad", fg="white", font=('Arial', 12, 'bold'), height=2).pack(fill="x", padx=20, pady=40)
    # ── Přepínač motivů ─────────────────────────────────────────────────────
    # Import projektu tlačítko (vedle motivů)
    bottom_bar = tk.Frame(main_container, bg=DT_BG)
    bottom_bar.pack(side="bottom", pady=12)

    tk.Button(bottom_bar, text="📂  Importovat projekt ze složky",
              command=import_project_from_folder,
              bg=DT_ACCENT, fg="#ffffff", font=('Segoe UI', 9, 'bold'),
              padx=14, pady=6, relief='flat', cursor='hand2').pack(side='left', padx=(0, 20))

    theme_bar = tk.Frame(bottom_bar, bg=DT_BG)
    theme_bar.pack(side='left')
    tk.Label(theme_bar, text="🎨 MOTIV:", bg=DT_BG, fg=DT_SUBTEXT,
             font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 8))

    # (name, preview_bg, preview_fg, description) — všechny motivy
    _ALL_THEMES_BTN = [
        ("Tmavý",            "#1e293b", "#60a5fa", "Tmavé pozadí — slate paleta"),
        ("Tmavý modrý",      "#111827", "#3b82f6", "Hlubší tmavá — noční varianta"),
        ("Klasický",         "#e0e0e0", "#1a1a1a", "Světlý klasický Windows styl"),
        ("Šedý profesionál", "#cfd4d8", "#1c2833", "Světlý šedý profesionální"),
        ("Světlý elegantní", "#ffffff", "#0d6efd", "Čistě bílý elegantní"),
    ]
    current_theme = load_theme_name()

    def _switch_theme(name):
        apply_theme(name)
        apply_dark_theme(root)
        show_intro_screen()

    for tname, tbg, tfg, _tdesc in _ALL_THEMES_BTN:
        is_active = (tname == current_theme)
        btn = tk.Button(
            theme_bar, text=("✔  " if is_active else "  ") + tname,
            bg=tbg, fg=tfg,
            font=('Segoe UI', 9, 'bold' if is_active else 'normal'),
            relief='solid' if is_active else 'flat',
            bd=2 if is_active else 0,
            padx=14, pady=5, cursor='hand2',
            command=lambda n=tname: _switch_theme(n)
        )
        btn.pack(side='left', padx=4)

    f4 = tk.Frame(grid_frame, bg=DT_PANEL, relief="flat", borderwidth=0, width=300, height=400); f4.grid(row=0, column=3, padx=20, pady=20); f4.pack_propagate(False)
    tk.Label(f4, text="📋 STRATEGIE", font=('Arial', 16, 'bold'), bg=DT_ACCENT, fg="#ffffff", pady=10).pack(fill="x")
    tk.Label(f4, text="Pravidla a poznámky.", bg=DT_PANEL, fg=DT_SUBTEXT, pady=10).pack()
    tk.Label(f4, text="✍️", font=('Arial', 50), bg=DT_PANEL, fg=DT_TEXT).pack(pady=30)
    tk.Button(f4, text="OTEVŘÍT PRAVIDLA", command=show_global_rules_screen, bg="#e67e22", fg="white", font=('Arial', 12, 'bold'), height=2).pack(fill="x", padx=20, pady=40)

    # Zkontrolovat novinky po aktualizaci (jen jednou po updatu, 600ms po vykreslení)
    root.after(600, check_whats_new)

def create_new_project(mode):
    n = simpledialog.askstring(f"Nový {mode}", "Název projektu:")
    if n:
        base = DIR_BACKTEST if mode == "BACKTEST" else DIR_REAL
        p = os.path.join(base, n.replace(" ","_"))
        os.makedirs(os.path.join(p, 'images'), exist_ok=True)
        global DATA_FILE, IMAGES_DIR, PROP_CONFIG_FILE, CHECKLIST_FILE, SCORING_FILE, PAIRS_FILE, TIMEFRAMES_FILE, RULES_FILE, current_mode, FILTERS_FILE, ACCOUNTS_FILE
        DATA_FILE = os.path.join(p, 'trades.csv'); PROP_CONFIG_FILE = os.path.join(p, 'prop_config.json'); IMAGES_DIR = os.path.join(p, 'images'); CHECKLIST_FILE = os.path.join(p, 'checklist.json')
        SCORING_FILE = os.path.join(p, 'scoring_config.json'); PAIRS_FILE = os.path.join(p, 'pairs_config.json'); TIMEFRAMES_FILE = os.path.join(p, 'timeframes_config.json'); RULES_FILE = os.path.join(p, 'rules.txt')
        FILTERS_FILE = os.path.join(p, 'filters_config.json'); ACCOUNTS_FILE = os.path.join(p, 'accounts.json')
        current_mode = mode
        if mode == "REAL": save_prop_config({"balance": 100000, "currency": "USD", "risk_per_trade_percent": 1.0})
        show_main_screen(n)

def delete_project(lb, mode):
    if not lb.curselection():
        messagebox.showwarning("Nic nevybráno", "Nejdřív vyber projekt ze seznamu.")
        return
    n = lb.get(lb.curselection()[0])
    base = DIR_BACKTEST if mode == "BACKTEST" else DIR_REAL
    p = os.path.join(base, n)
    if not messagebox.askyesno("Smazat projekt",
            f"Opravdu smazat projekt '{n}'?\n\nVšechna data (obchody, screenshoty) budou nenávratně smazána!",
            icon='warning'):
        return
    try:
        import shutil
        shutil.rmtree(p)
        show_intro_screen()
    except Exception as e:
        messagebox.showerror("Chyba", f"Nelze smazat projekt:\n{e}")

def open_project(lb, mode):
    if lb.curselection():
        n = lb.get(lb.curselection()[0])
        p = _resolve_project_path(mode, n)
        global DATA_FILE, IMAGES_DIR, PROP_CONFIG_FILE, CHECKLIST_FILE, SCORING_FILE, PAIRS_FILE, TIMEFRAMES_FILE, RULES_FILE, current_mode, FILTERS_FILE, ACCOUNTS_FILE
        DATA_FILE = os.path.join(p, 'trades.csv'); PROP_CONFIG_FILE = os.path.join(p, 'prop_config.json'); IMAGES_DIR = os.path.join(p, 'images'); CHECKLIST_FILE = os.path.join(p, 'checklist.json')
        SCORING_FILE = os.path.join(p, 'scoring_config.json'); PAIRS_FILE = os.path.join(p, 'pairs_config.json'); TIMEFRAMES_FILE = os.path.join(p, 'timeframes_config.json'); RULES_FILE = os.path.join(p, 'rules.txt')
        FILTERS_FILE = os.path.join(p, 'filters_config.json'); ACCOUNTS_FILE = os.path.join(p, 'accounts.json')
        current_mode = mode
        show_main_screen(n)

if __name__ == "__main__":
    _dbg_log('STARTUP', f"═══ SMC Journal PRO v{VERSION} spuštěn ═══  APP_DIR={_APP_DIR}  frozen={getattr(sys,'frozen',False)}")
    try:
        root = tk.Tk(); root.title(load_app_title()); root.geometry("1400x900")
        root.tk.call('encoding', 'system', 'utf-8')
        root.minsize(1100, 700)
        apply_dark_theme(root)
        root.protocol("WM_DELETE_WINDOW", on_close)
        root.withdraw()  # Skryj main window dokud splash neskončí
        root.after(100, lambda: show_splash(lambda: [root.deiconify(), show_intro_screen()]))
        # Tiše zkontroluj aktualizace 4 sekundy po startu — na hlavním threadu (ne v background threadu!)
        root.after(4000, lambda: check_for_updates(startup=True))
        root.mainloop()
    except Exception as e:
        _dbg_log('STARTUP', f"FATÁLNÍ CHYBA: {e}", level='ERROR')
        if 'root' in locals(): messagebox.showerror("Fatální chyba", str(e))
        else: print(f"CRITICAL ERROR: {e}")