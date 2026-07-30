"""
Záložka 🔁 REPLAY — analýza TradingView Replay Trading exportů.
Více XLSX souborů se sčítá do jednoho konzistentního přehledu.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, json, math, uuid
from datetime import datetime

# ── Optional deps ─────────────────────────────────────────────────────────────
try:
    import openpyxl
    _HAS_XL = True
except ImportError:
    _HAS_XL = False

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.patches as mpatches
    import matplotlib.ticker as mticker
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

# ── Colours ───────────────────────────────────────────────────────────────────
BG      = '#0f172a'
PANEL   = '#1e293b'
SURF    = '#293548'
SURF2   = '#1a2438'
TEXT    = '#e2e8f0'
SUB     = '#64748b'
ACCENT  = '#3b82f6'
GREEN   = '#22c55e'
RED     = '#ef4444'
ORANGE  = '#f59e0b'
BORDER  = '#334155'
MFIG    = '#1e293b'
MAXES   = '#233044'
MGRID   = '#2d3f55'
MTEXT   = '#e2e8f0'

FN   = ('Segoe UI', 10)
FNB  = ('Segoe UI', 10, 'bold')
FNS  = ('Segoe UI', 9)
FNXL = ('Segoe UI', 18, 'bold')
FNLG = ('Segoe UI', 12, 'bold')

# ── Global state ──────────────────────────────────────────────────────────────
_APP_DIR = None


def _data_path():
    d = _APP_DIR or os.getcwd()
    return os.path.join(d, 'replay_data.json')


def _load():
    p = _data_path()
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'sessions': []}


def _save(data):
    with open(_data_path(), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── XLSX parser ───────────────────────────────────────────────────────────────

def _parse_xlsx(path):
    """Parse TradingView Replay XLSX. Returns {initial_capital, trades[]}."""
    wb = openpyxl.load_workbook(path, data_only=True)

    cap = 1000.0
    if 'Performance' in wb.sheetnames:
        for row in wb['Performance'].iter_rows(values_only=True):
            if row[0] == 'Initial capital' and row[1] is not None:
                try:
                    cap = float(row[1])
                except Exception:
                    pass
                break

    if 'Trades' not in wb.sheetnames:
        raise ValueError("Soubor neobsahuje list 'Trades'")

    rows = list(wb['Trades'].iter_rows(values_only=True))
    if len(rows) < 2:
        raise ValueError("Žádné obchody v souboru")

    td = {}
    for row in rows[1:]:
        if not row or row[0] is None:
            continue
        try:
            num  = int(row[0])
            typ  = str(row[1] or '')
            dt   = row[2]
            dt_s = dt.strftime('%Y-%m-%d %H:%M') if isinstance(dt, datetime) else str(dt or '')
            sig  = str(row[3] or '')
            price = float(row[4] or 0)
            pnl   = float(row[7] or 0)
            ppct  = float(row[8] or 0)
            fav   = float(row[10] or 0)
            adv   = float(row[12] or 0)
            bars  = int(row[16]) if row[16] is not None else 0

            if num not in td:
                td[num] = {}
            if 'entry' in typ.lower():
                td[num].update({
                    'entry_time': dt_s,
                    'entry_price': price,
                    'type': 'long' if 'long' in typ.lower() else 'short',
                })
            else:
                td[num].update({
                    'exit_time': dt_s,
                    'exit_price': price,
                    'pnl': pnl,
                    'pnl_pct': ppct,
                    'fav_excursion': fav,
                    'adv_excursion': adv,
                    'bars': bars,
                    'signal': sig,
                })
        except Exception:
            continue

    trades = []
    for num in sorted(td.keys()):
        t = {
            'trade_num': num, 'type': 'short',
            'entry_time': '', 'exit_time': '',
            'entry_price': 0.0, 'exit_price': 0.0,
            'pnl': 0.0, 'pnl_pct': 0.0,
            'fav_excursion': 0.0, 'adv_excursion': 0.0,
            'bars': 0, 'signal': '',
        }
        t.update(td[num])
        trades.append(t)

    return {'initial_capital': cap, 'trades': trades}


# ── Statistics ────────────────────────────────────────────────────────────────

def _active_trades(data):
    trades = []
    for s in data.get('sessions', []):
        if not s.get('enabled', True):
            continue
        for t in s.get('trades', []):
            t2 = dict(t)
            t2['_sid']   = s['id']
            t2['_sym']   = s.get('symbol', '')
            trades.append(t2)
    trades.sort(key=lambda t: t.get('exit_time', '') or '')
    return trades


def _compute(trades):
    if not trades:
        return None

    pnls = [t['pnl'] for t in trades]
    winners = [p for p in pnls if p > 0]
    losers  = [p for p in pnls if p < 0]
    bes     = [p for p in pnls if p == 0]
    total   = len(pnls)
    tot_pnl = sum(pnls)
    gross_p = sum(winners)
    gross_l = abs(sum(losers))

    # Equity curve
    equity = [0.0]
    for p in pnls:
        equity.append(equity[-1] + p)

    # Max drawdown
    peak   = 0.0
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        max_dd = max(max_dd, peak - v)

    pf = gross_p / gross_l if gross_l > 0 else (float('inf') if gross_p > 0 else 0.0)

    if len(pnls) > 1:
        mean = tot_pnl / total
        var  = sum((p - mean) ** 2 for p in pnls) / (total - 1)
        std  = math.sqrt(var) if var > 0 else 1e-9
        sharpe = (mean / std) * math.sqrt(total)
    else:
        sharpe = 0.0

    pcts = [t.get('pnl_pct', 0) for t in trades]

    return {
        'total': total,
        'tot_pnl': tot_pnl,
        'gross_p': gross_p,
        'gross_l': gross_l,
        'winners': len(winners),
        'losers': len(losers),
        'bes': len(bes),
        'win_rate': len(winners) / total * 100,
        'pf': pf,
        'epayoff': tot_pnl / total,
        'avg_w': gross_p / len(winners) if winners else 0,
        'avg_l': gross_l / len(losers) if losers else 0,
        'largest_w': max(pnls),
        'largest_l': min(pnls),
        'avg_bars': sum(t.get('bars', 0) for t in trades) / total,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'equity': equity,
        'pnls': pnls,
        'pcts': pcts,
    }


# ── Main UI class ─────────────────────────────────────────────────────────────

class ReplayUI:
    def __init__(self, parent):
        self._data    = _load()
        self._fig     = None
        self._canvas  = None
        self._sv      = {}   # session enable BooleanVars  {sid: BooleanVar}
        self._kpis    = {}   # kpi label StringVars
        self._build(parent)
        self._refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self, parent):
        parent.configure(bg=BG)

        # ── Toolbar ──────────────────────────────────────────────────────────
        tb = tk.Frame(parent, bg=SURF2, height=44)
        tb.pack(fill='x', side='top')
        tb.pack_propagate(False)

        tk.Label(tb, text='🔁  REPLAY TRADING', bg=SURF2, fg=TEXT,
                 font=FNB).pack(side='left', padx=16, pady=10)

        tk.Button(tb, text='📂  Načíst XLSX', bg=ACCENT, fg='white',
                  relief='flat', font=FNB, padx=14, pady=4,
                  cursor='hand2', activebackground='#2563eb',
                  command=self._add_session).pack(side='right', padx=10, pady=6)

        # ── Main split ───────────────────────────────────────────────────────
        split = tk.Frame(parent, bg=BG)
        split.pack(fill='both', expand=True)

        # LEFT — session list
        left = tk.Frame(split, bg=PANEL, width=230)
        left.pack(side='left', fill='y')
        left.pack_propagate(False)
        self._left = left
        self._build_sessions_panel()

        # RIGHT — charts + KPIs
        right = tk.Frame(split, bg=BG)
        right.pack(side='left', fill='both', expand=True)
        self._build_right(right)

    def _build_sessions_panel(self):
        hdr = tk.Frame(self._left, bg=SURF2, height=36)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text='Relace', bg=SURF2, fg=SUB, font=FNS
                 ).pack(side='left', padx=12, pady=8)

        # Scrollable list
        self._sess_canvas = tk.Canvas(self._left, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(self._left, orient='vertical',
                          command=self._sess_canvas.yview)
        self._sess_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self._sess_canvas.pack(fill='both', expand=True)

        self._sess_frame = tk.Frame(self._sess_canvas, bg=PANEL)
        self._sess_win   = self._sess_canvas.create_window(
            (0, 0), window=self._sess_frame, anchor='nw')
        self._sess_frame.bind('<Configure>', self._on_sess_configure)
        self._sess_canvas.bind('<Configure>',
            lambda e: self._sess_canvas.itemconfig(self._sess_win, width=e.width))

    def _on_sess_configure(self, _evt):
        self._sess_canvas.configure(
            scrollregion=self._sess_canvas.bbox('all'))

    def _rebuild_sessions_list(self):
        for w in self._sess_frame.winfo_children():
            w.destroy()

        sessions = self._data.get('sessions', [])
        if not sessions:
            tk.Label(self._sess_frame,
                     text='Žádné relace.\nNačti XLSX soubor.',
                     bg=PANEL, fg=SUB, font=FNS,
                     wraplength=200, justify='center').pack(pady=24)
            return

        for s in sessions:
            sid  = s['id']
            sym  = s.get('symbol', '?')
            dt   = s.get('uploaded', '')[:10]
            cnt  = len(s.get('trades', []))
            pnl  = sum(t['pnl'] for t in s.get('trades', []))
            col  = GREEN if pnl >= 0 else RED
            sign = '+' if pnl >= 0 else ''

            card = tk.Frame(self._sess_frame, bg=SURF, pady=8, padx=10)
            card.pack(fill='x', padx=6, pady=4)

            top = tk.Frame(card, bg=SURF); top.pack(fill='x')

            if sid not in self._sv:
                self._sv[sid] = tk.BooleanVar(value=s.get('enabled', True))

            tk.Checkbutton(
                top, variable=self._sv[sid], bg=SURF,
                activebackground=SURF, selectcolor=ACCENT,
                command=lambda s2=s, v=self._sv[sid]: self._toggle(s2, v),
            ).pack(side='left')
            tk.Label(top, text=f'{sym}', bg=SURF, fg=TEXT,
                     font=FNB).pack(side='left')

            # Delete button
            tk.Button(top, text='✕', bg=SURF, fg=SUB, relief='flat',
                      font=('Segoe UI', 8), padx=4, cursor='hand2',
                      activebackground=RED, activeforeground='white',
                      command=lambda s2=s: self._delete(s2)
                      ).pack(side='right')

            row2 = tk.Frame(card, bg=SURF); row2.pack(fill='x', pady=(2, 0))
            tk.Label(row2, text=dt, bg=SURF, fg=SUB, font=FNS
                     ).pack(side='left')
            tk.Label(row2, text=f'{sign}${pnl:.2f}',
                     bg=SURF, fg=col, font=FNS).pack(side='right')

            row3 = tk.Frame(card, bg=SURF); row3.pack(fill='x')
            tk.Label(row3, text=f'{cnt} obchodů', bg=SURF, fg=SUB,
                     font=FNS).pack(side='left')
            fname = s.get('filename', '')
            if len(fname) > 22:
                fname = '…' + fname[-20:]
            tk.Label(row3, text=fname, bg=SURF, fg=SURF2, font=FNS
                     ).pack(side='right')

    def _build_right(self, parent):
        # ── KPI row ──────────────────────────────────────────────────────────
        kpi_row = tk.Frame(parent, bg=PANEL, height=80)
        kpi_row.pack(fill='x', padx=0, pady=0)
        kpi_row.pack_propagate(False)

        self._kpi_frame = kpi_row
        self._kpi_vars  = {}

        kpi_defs = [
            ('tot_pnl',  'Total PnL',        '$0.00'),
            ('max_dd',   'Max Drawdown',      '$0.00'),
            ('win_rate', 'Profitable trades', '0 %'),
            ('pf',       'Profit factor',     '0.000'),
            ('sharpe',   'Sharpe ratio',      '0.000'),
            ('epayoff',  'Expected payoff',   '$0.00'),
        ]
        for i, (key, lbl, default) in enumerate(kpi_defs):
            sep_col = BORDER if i > 0 else PANEL
            tk.Frame(kpi_row, bg=sep_col, width=1).pack(side='left', fill='y', padx=0)
            cell = tk.Frame(kpi_row, bg=PANEL, padx=18)
            cell.pack(side='left', fill='y')
            tk.Label(cell, text=lbl, bg=PANEL, fg=SUB, font=FNS).pack(pady=(12, 0))
            var = tk.StringVar(value=default)
            self._kpi_vars[key] = var
            tk.Label(cell, textvariable=var, bg=PANEL, fg=TEXT,
                     font=FNLG).pack()

        # ── Chart canvas ─────────────────────────────────────────────────────
        chart_frame = tk.Frame(parent, bg=BG)
        chart_frame.pack(fill='both', expand=True, padx=6, pady=6)
        self._chart_frame = chart_frame

        if _HAS_MPL:
            self._fig = Figure(facecolor=MFIG)
            self._canvas = FigureCanvasTkAgg(self._fig, master=chart_frame)
            self._canvas.get_tk_widget().pack(fill='both', expand=True)
        else:
            tk.Label(chart_frame,
                     text='Chybí matplotlib. pip install matplotlib',
                     bg=BG, fg=RED, font=FN).pack(expand=True)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_session(self):
        if not _HAS_XL:
            messagebox.showerror('Chybí openpyxl',
                                 'Nainstaluj: pip install openpyxl')
            return
        paths = filedialog.askopenfilenames(
            title='Vyber TradingView Replay XLSX',
            filetypes=[('Excel', '*.xlsx'), ('Všechny', '*.*')],
        )
        if not paths:
            return
        added = 0
        for path in paths:
            try:
                parsed = _parse_xlsx(path)
                fname  = os.path.basename(path)
                # Detect symbol from filename (e.g. Replay_Trading_SKILLING_US100_...)
                sym = 'N/A'
                parts = fname.replace('.xlsx', '').split('_')
                # Try to find a capitalised ticker-like token
                for p in reversed(parts):
                    if p.isupper() and 2 <= len(p) <= 8 and p not in ('TRADING', 'REPLAY', 'SKILLING'):
                        sym = p
                        break

                session = {
                    'id':       str(uuid.uuid4()),
                    'filename': fname,
                    'symbol':   sym,
                    'uploaded': datetime.now().strftime('%Y-%m-%d'),
                    'enabled':  True,
                    'initial_capital': parsed['initial_capital'],
                    'trades':   parsed['trades'],
                }
                self._data.setdefault('sessions', []).append(session)
                added += 1
            except Exception as e:
                messagebox.showerror('Chyba', f'{os.path.basename(path)}:\n{e}')

        if added:
            _save(self._data)
            self._refresh()

    def _delete(self, session):
        if not messagebox.askyesno('Smazat relaci',
                                   f'Smazat relaci "{session.get("filename","")}"?\n'
                                   'Všechna data relace budou odstraněna.'):
            return
        sid = session['id']
        self._data['sessions'] = [
            s for s in self._data['sessions'] if s['id'] != sid
        ]
        self._sv.pop(sid, None)
        _save(self._data)
        self._refresh()

    def _toggle(self, session, var):
        session['enabled'] = var.get()
        _save(self._data)
        self._refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        self._rebuild_sessions_list()
        trades = _active_trades(self._data)
        stats  = _compute(trades)
        self._update_kpis(stats)
        if _HAS_MPL and self._fig is not None:
            self._draw_charts(stats, trades)

    def _update_kpis(self, st):
        if st is None:
            for k, v in self._kpi_vars.items():
                v.set('—')
            return
        pnl_sign = '+' if st['tot_pnl'] >= 0 else ''
        self._kpi_vars['tot_pnl'].set(f"{pnl_sign}${st['tot_pnl']:.2f}")
        self._kpi_vars['max_dd'].set(f"${st['max_dd']:.2f}")
        self._kpi_vars['win_rate'].set(
            f"{st['win_rate']:.1f}%  {st['winners']}/{st['total']}")
        pf_val = st['pf']
        self._kpi_vars['pf'].set('∞' if math.isinf(pf_val) else f"{pf_val:.3f}")
        self._kpi_vars['sharpe'].set(f"{st['sharpe']:.3f}")
        ep_sign = '+' if st['epayoff'] >= 0 else ''
        self._kpi_vars['epayoff'].set(f"{ep_sign}${st['epayoff']:.2f}")

        # Colour total PnL label
        for w in self._kpi_frame.winfo_children():
            if isinstance(w, tk.Frame):
                for c in w.winfo_children():
                    if isinstance(c, tk.Label) and c.cget('textvariable'):
                        tv = str(self._kpi_frame.tk.call(
                            c.cget('textvariable'), 'get'))
                        if tv == self._kpi_vars['tot_pnl'].get():
                            col = GREEN if st['tot_pnl'] >= 0 else RED
                            c.config(fg=col)

    # ── Charts ────────────────────────────────────────────────────────────────

    def _ax_style(self, ax, title='', xlabel='', ylabel=''):
        ax.set_facecolor(MAXES)
        ax.tick_params(colors=MTEXT, labelsize=8)
        ax.spines[:].set_color(MGRID)
        ax.yaxis.label.set_color(MTEXT)
        ax.xaxis.label.set_color(MTEXT)
        ax.grid(color=MGRID, linewidth=0.5, linestyle='--', alpha=0.6)
        if title:
            ax.set_title(title, color=MTEXT, fontsize=9, pad=6)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=8)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=8)

    def _draw_charts(self, st, trades):
        self._fig.clf()

        if st is None:
            ax = self._fig.add_subplot(111)
            ax.set_facecolor(MAXES)
            self._fig.patch.set_facecolor(MFIG)
            ax.text(0.5, 0.5, 'Načti XLSX soubor pro zobrazení analýzy',
                    transform=ax.transAxes, ha='center', va='center',
                    color=SUB, fontsize=12)
            ax.set_xticks([]); ax.set_yticks([])
            ax.spines[:].set_color(MGRID)
            self._canvas.draw()
            return

        # Grid: top row = equity curve (full width)
        #        bottom row = 3 panels
        import matplotlib.gridspec as gs
        grid = gs.GridSpec(2, 3,
                           figure=self._fig,
                           height_ratios=[2, 1],
                           hspace=0.45, wspace=0.35,
                           left=0.06, right=0.97,
                           top=0.94, bottom=0.08)

        ax_eq  = self._fig.add_subplot(grid[0, :])   # full width
        ax_prs = self._fig.add_subplot(grid[1, 0])   # profit structure
        ax_dn  = self._fig.add_subplot(grid[1, 1])   # donut
        ax_his = self._fig.add_subplot(grid[1, 2])   # histogram

        self._draw_equity(ax_eq, st, trades)
        self._draw_profit_structure(ax_prs, st)
        self._draw_donut(ax_dn, st)
        self._draw_histogram(ax_his, st)

        self._canvas.draw()

    def _draw_equity(self, ax, st, trades):
        self._ax_style(ax, title='Equity křivka — kumulativní P&L')
        pnls   = st['pnls']
        equity = st['equity']
        n      = len(pnls)
        xs     = list(range(1, n + 1))

        colors = [GREEN if p >= 0 else RED for p in pnls]
        ax.bar(xs, pnls, color=colors, alpha=0.6, width=0.7, zorder=2)

        ax.plot(xs, equity[1:], color='#38bdf8', linewidth=2,
                zorder=3, marker='o', markersize=3.5, markerfacecolor='#38bdf8')

        # Zero line
        ax.axhline(0, color=MGRID, linewidth=0.8, linestyle='-')

        # Annotate final value
        final = equity[-1]
        col   = GREEN if final >= 0 else RED
        ax.annotate(f'${final:.2f}',
                    xy=(n, final), xytext=(n + 0.5, final),
                    color=col, fontsize=8, va='center',
                    arrowprops=dict(arrowstyle='-', color=col, lw=0.5))

        # X-axis labels: use exit time for context
        step = max(1, n // 10)
        ticks = list(range(0, n, step)) + [n - 1]
        ticks = sorted(set(ticks))
        labels = []
        for i in ticks:
            t = trades[i] if i < len(trades) else None
            labels.append(t.get('exit_time', '')[:10] if t else '')
        ax.set_xticks([i + 1 for i in ticks])
        ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=7)
        ax.set_xlim(0, n + 2)
        ax.set_ylabel('P&L (USD)', fontsize=8)

        # Legend
        pw = mpatches.Patch(color=GREEN, alpha=0.7, label='WIN')
        lw = mpatches.Patch(color=RED,   alpha=0.7, label='LOSS')
        el = ax.lines[0] if ax.lines else None
        handles = [pw, lw]
        if el:
            from matplotlib.lines import Line2D
            handles.append(Line2D([0], [0], color='#38bdf8', lw=2, label='Kumulativní P&L'))
        ax.legend(handles=handles, loc='upper left', fontsize=7,
                  facecolor=MFIG, edgecolor=MGRID, labelcolor=MTEXT)

    def _draw_profit_structure(self, ax, st):
        self._ax_style(ax, title='Profit struktura')
        labels = ['Gross\nProfit', 'Gross\nLoss', 'Net\nPnL']
        values = [st['gross_p'], -st['gross_l'], st['tot_pnl']]
        colors = [GREEN, RED, GREEN if st['tot_pnl'] >= 0 else RED]
        bars = ax.bar(labels, values, color=colors, alpha=0.8, width=0.5)
        ax.axhline(0, color=MGRID, linewidth=0.8)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    val + (abs(val) * 0.03 if val >= 0 else -abs(val) * 0.05),
                    f'${val:.1f}', ha='center', va='bottom' if val >= 0 else 'top',
                    color=MTEXT, fontsize=8)
        ax.set_ylabel('USD', fontsize=8)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f'${x:.0f}'))

    def _draw_donut(self, ax, st):
        ax.set_facecolor(MAXES)
        ax.set_title('Distribuce obchodů', color=MTEXT, fontsize=9, pad=6)

        w  = st['winners']
        l  = st['losers']
        be = st['bes']
        sizes  = [x for x in [w, l, be] if x > 0]
        labels = [x for x, v in [('Winners', w), ('Losers', l), ('Breakevens', be)] if v > 0]
        colors = [x for x, v in [(GREEN, w), (RED, l), (ORANGE, be)] if v > 0]

        if not sizes:
            ax.text(0.5, 0.5, 'Žádná data', transform=ax.transAxes,
                    ha='center', va='center', color=SUB)
            return

        wedges, _ = ax.pie(
            sizes, labels=None, colors=colors,
            wedgeprops={'width': 0.55, 'edgecolor': MFIG, 'linewidth': 1.5},
            startangle=90,
        )
        ax.text(0, 0, f'{st["total"]}\nobchodů',
                ha='center', va='center', color=MTEXT,
                fontsize=9, fontweight='bold', linespacing=1.5)

        legend_labels = [
            f'{lbl}  {v}  ({v/st["total"]*100:.1f}%)'
            for lbl, v in zip(['Winners', 'Losers', 'BEs'], [w, l, be])
            if v > 0
        ]
        patches = [mpatches.Patch(color=c, label=lb)
                   for c, lb in zip(colors, legend_labels)]
        ax.legend(handles=patches, loc='lower center',
                  bbox_to_anchor=(0.5, -0.28),
                  fontsize=7, facecolor=MFIG,
                  edgecolor=MGRID, labelcolor=MTEXT, ncol=1)

    def _draw_histogram(self, ax, st):
        self._ax_style(ax, title='Distribuce výnosů (%)')
        pcts = st['pcts']
        if not pcts:
            return

        wins_pct  = [p for p in pcts if p > 0]
        loses_pct = [p for p in pcts if p < 0]

        bins = 20
        if loses_pct:
            ax.hist(loses_pct, bins=bins, color=RED,   alpha=0.75, label='Losers')
        if wins_pct:
            ax.hist(wins_pct,  bins=bins, color=GREEN, alpha=0.75, label='Winners')

        # Average lines
        if wins_pct:
            avg_w = sum(wins_pct) / len(wins_pct)
            ax.axvline(avg_w, color=GREEN, linestyle='--', linewidth=1.2,
                       label=f'Avg W {avg_w:.2f}%')
        if loses_pct:
            avg_l = sum(loses_pct) / len(loses_pct)
            ax.axvline(avg_l, color=RED, linestyle='--', linewidth=1.2,
                       label=f'Avg L {avg_l:.2f}%')

        ax.axvline(0, color=MTEXT, linewidth=0.6)
        ax.set_xlabel('%', fontsize=8)
        ax.set_ylabel('Počet', fontsize=8)
        ax.legend(fontsize=7, facecolor=MFIG, edgecolor=MGRID,
                  labelcolor=MTEXT, loc='upper right')


# ── Public entry point ────────────────────────────────────────────────────────

def setup_replay_tab(parent, app_dir):
    """Inicializuje záložku Replay. Volat z BACKTESTING.py."""
    global _APP_DIR
    _APP_DIR = app_dir

    missing = []
    if not _HAS_XL:
        missing.append('openpyxl')
    if not _HAS_MPL:
        missing.append('matplotlib')

    if missing:
        frame = tk.Frame(parent, bg=BG)
        frame.pack(expand=True)
        tk.Label(frame,
                 text=f'❌ Chybí knihovny: {", ".join(missing)}\n\n'
                      f'Nainstaluj: pip install {" ".join(missing)}',
                 bg=BG, fg=RED, font=('Segoe UI', 12), justify='center'
                 ).pack(expand=True)
        return

    ReplayUI(parent)
