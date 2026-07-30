# launcher.py — startovací soubor pro SMC Journal PRO
# Tento soubor se NIKDY neaktualizuje.
# Obsahuje Python + všechny knihovny. Spouští BACKTESTING.py ze stejného adresáře.

# === Vynucené importy pro PyInstaller — musí vědět co zabalit ===
import tkinter, tkinter.ttk, tkinter.filedialog, tkinter.messagebox
import tkinter.simpledialog, tkinter.font
import csv, os, sys, json, re, shutil, math, random, calendar
import webbrowser, zipfile, traceback, threading, locale
import urllib.request, urllib.error
from datetime import datetime, date
from collections import defaultdict

try: from PIL import Image, ImageTk, ImageDraw
except ImportError: pass
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    import matplotlib.figure, matplotlib.patches, matplotlib.ticker
    import matplotlib.gridspec
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.colors import TwoSlopeNorm
except ImportError: pass
try: import openpyxl
except ImportError: pass
try: import cv2
except ImportError: pass
try: import numpy as np
except ImportError: pass
try: import pytesseract
except ImportError: pass
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError: pass

# === Najdi a spusť BACKTESTING.py ===
if getattr(sys, 'frozen', False):
    _app_dir = os.path.dirname(sys.executable)
else:
    _app_dir = os.path.dirname(os.path.abspath(__file__))

_script = os.path.join(_app_dir, 'BACKTESTING.py')

if not os.path.exists(_script):
    import tkinter as _tk
    from tkinter import messagebox as _mb
    _r = _tk.Tk(); _r.withdraw()
    _mb.showerror("Chyba spuštění",
        f"Soubor BACKTESTING.py nebyl nalezen v:\n{_app_dir}\n\n"
        f"Ujisti se, že jsou oba soubory ve stejné složce.")
    sys.exit(1)

with open(_script, 'r', encoding='utf-8') as _f:
    _code = compile(_f.read(), _script, 'exec')

exec(_code, {
    '__file__':  _script,
    '__name__':  '__main__',
    '__spec__':  None,
    '__loader__': None,
    '__builtins__': __builtins__,
})
