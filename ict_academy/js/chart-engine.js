// ICT Chart Engine v2 — deterministické scény, přesné anotace

// ─── CHART ENGINE ────────────────────────────────────────────────────────────

class ICTChart {
  constructor(canvasId, opts = {}) {
    this.canvasId = canvasId;
    this.canvas = document.getElementById(canvasId);
    this.options = Object.assign({
      pad: { top: 28, right: 56, bottom: 32, left: 8 },
      bullColor:  '#00c896',
      bearColor:  '#e84040',
      bg:         '#0d0f14',
      grid:       'rgba(42,47,63,0.55)',
      textColor:  '#8892a4',
    }, opts);
    this.candles = [];
    this.anns    = [];
  }

  load(candles, anns = []) {
    this.candles = candles;
    this.anns    = anns;
    return this;
  }

  // ─── internals ─────────────────────────────────────────────────────────────

  _setup() {
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) return false;
    const dpr  = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    if (!rect.width) return false;
    this.canvas.width  = rect.width  * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx = this.canvas.getContext('2d');
    this.ctx.scale(dpr, dpr);
    this.W = rect.width;
    this.H = rect.height;
    return true;
  }

  _range() {
    let lo = Infinity, hi = -Infinity;
    this.candles.forEach(c => { lo = Math.min(lo, c.low); hi = Math.max(hi, c.high); });
    this.anns.forEach(a => {
      if (a.price  !== undefined) { lo = Math.min(lo, a.price);  hi = Math.max(hi, a.price);  }
      if (a.top    !== undefined) { hi = Math.max(hi, a.top);    }
      if (a.bottom !== undefined) { lo = Math.min(lo, a.bottom); }
    });
    const pad = (hi - lo) * 0.13;
    return { lo: lo - pad, hi: hi + pad };
  }

  _y(price, lo, hi) {
    const { top, bottom } = this.options.pad;
    return top + (this.H - top - bottom) * (1 - (price - lo) / (hi - lo));
  }

  _x(i) {
    const { left, right } = this.options.pad;
    const slotW = (this.W - left - right) / this.candles.length;
    return left + i * slotW + slotW * 0.5;
  }

  _cw() {
    const { left, right } = this.options.pad;
    return Math.max(3, (this.W - left - right) / this.candles.length * 0.6);
  }

  // ─── render ────────────────────────────────────────────────────────────────

  render() {
    if (!this._setup()) return this;
    const { lo, hi } = this._range();
    const ctx = this.ctx;
    const P   = this.options.pad;

    ctx.clearRect(0, 0, this.W, this.H);
    ctx.fillStyle = this.options.bg;
    ctx.fillRect(0, 0, this.W, this.H);

    // Grid
    for (let i = 0; i <= 5; i++) {
      const p = lo + (hi - lo) * (i / 5);
      const y = this._y(p, lo, hi);
      ctx.strokeStyle = this.options.grid;
      ctx.lineWidth   = 0.5;
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(P.left, y); ctx.lineTo(this.W - P.right, y); ctx.stroke();
      ctx.fillStyle   = this.options.textColor;
      ctx.font        = '10px monospace';
      ctx.textAlign   = 'right';
      ctx.fillText(p.toFixed(0), this.W - 2, y + 3);
    }

    // Background annotations
    this._drawAnns(ctx, lo, hi, 'bg');

    // Candles
    const cw = this._cw();
    this.candles.forEach((c, i) => {
      const x   = this._x(i);
      const yO  = this._y(c.open,  lo, hi);
      const yC  = this._y(c.close, lo, hi);
      const yH  = this._y(c.high,  lo, hi);
      const yL  = this._y(c.low,   lo, hi);
      const bull = c.close >= c.open;
      const col  = bull ? this.options.bullColor : this.options.bearColor;

      ctx.strokeStyle = col; ctx.lineWidth = 1; ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(x, yH); ctx.lineTo(x, yL); ctx.stroke();

      ctx.fillStyle = col;
      const bT = Math.min(yO, yC);
      const bH = Math.max(1.5, Math.abs(yO - yC));
      ctx.fillRect(x - cw / 2, bT, cw, bH);
    });

    // Foreground annotations
    this._drawAnns(ctx, lo, hi, 'fg');
    return this;
  }

  // ─── annotation drawing ────────────────────────────────────────────────────

  _drawAnns(ctx, lo, hi, layer) {
    const P = this.options.pad;
    this.anns.forEach(a => {
      if ((a.layer || 'bg') !== layer) return;
      ctx.setLineDash([]); ctx.globalAlpha = 1;

      // ── zone (shaded box) ──────────────────────────────────────────────────
      if (a.type === 'zone') {
        const y1 = this._y(a.top, lo, hi);
        const y2 = this._y(a.bottom, lo, hi);
        const x1 = a.fromCandle !== undefined ? this._x(a.fromCandle) : P.left;
        const x2 = a.toCandle   !== undefined ? this._x(a.toCandle)   : this.W - P.right;
        ctx.fillStyle = a.fill || 'rgba(240,185,11,0.12)';
        ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
        if (a.border) {
          ctx.strokeStyle = a.border; ctx.lineWidth = 1;
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        }
        if (a.label) {
          ctx.fillStyle  = a.labelColor || a.border || '#f0b90b';
          ctx.font       = 'bold 10px sans-serif';
          ctx.textAlign  = 'left';
          ctx.fillText(a.label, x1 + 5, y1 + 13);
        }
      }

      // ── hline (full-width horizontal line) ────────────────────────────────
      if (a.type === 'hline') {
        const y = this._y(a.price, lo, hi);
        ctx.strokeStyle = a.color || '#f0b90b';
        ctx.lineWidth   = a.width || 1;
        if (a.dash) ctx.setLineDash(a.dash);
        const xFrom = a.fromCandle !== undefined ? this._x(a.fromCandle) : P.left;
        ctx.beginPath(); ctx.moveTo(xFrom, y); ctx.lineTo(this.W - P.right, y); ctx.stroke();
        ctx.setLineDash([]);
        if (a.label) {
          ctx.fillStyle = a.color || '#f0b90b';
          ctx.font      = 'bold 10px sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(a.label, this.W - P.right - 2, y - 3);
        }
      }

      // ── bosline (dashed BOS/CHoCH line + badge on right) ──────────────────
      if (a.type === 'bosline' || a.type === 'chochline') {
        const y     = this._y(a.price, lo, hi);
        const color = a.color || (a.type === 'bosline' ? '#4a9eff' : '#f0b90b');
        const xFrom = a.fromCandle !== undefined ? this._x(a.fromCandle) : P.left;
        ctx.strokeStyle = color; ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 3]);
        ctx.beginPath();
        ctx.moveTo(xFrom, y);
        ctx.lineTo(this.W - P.right - 36, y);
        ctx.stroke();
        ctx.setLineDash([]);
        this._badge(ctx, a.label || (a.type === 'bosline' ? 'BOS' : 'CHoCH'),
                    this.W - P.right - 34, y, color, '#fff');
      }

      // ── swingpoint (HH / HL / LH / LL label at exact candle high/low) ──────
      if (a.type === 'swingpoint') {
        const x     = this._x(a.candle);
        const y     = this._y(a.price, lo, hi);
        const above = a.side === 'above';
        ctx.fillStyle = a.color || '#8892a4';
        ctx.font      = 'bold 10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(a.label, x, above ? y - 7 : y + 15);
        // small tick line from candle extreme
        ctx.strokeStyle = a.color || '#8892a4';
        ctx.lineWidth   = 1;
        ctx.beginPath();
        ctx.moveTo(x, above ? y - 1 : y + 1);
        ctx.lineTo(x, above ? y - 5 : y + 5);
        ctx.stroke();
      }

      // ── arrow (entry/direction indicator) ────────────────────────────────
      if (a.type === 'arrow') {
        const x   = this._x(a.candle);
        const y   = this._y(a.price, lo, hi);
        const up  = (a.dir || 'up') === 'up';
        ctx.fillStyle = a.color || '#00c896';
        ctx.beginPath();
        if (up) {
          ctx.moveTo(x, y - 5); ctx.lineTo(x - 6, y + 7); ctx.lineTo(x + 6, y + 7);
        } else {
          ctx.moveTo(x, y + 5); ctx.lineTo(x - 6, y - 7); ctx.lineTo(x + 6, y - 7);
        }
        ctx.closePath(); ctx.fill();
        if (a.label) {
          ctx.font      = 'bold 10px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(a.label, x, up ? y - 9 : y + 19);
        }
      }

      // ── entryline (SL / TP / Entry thin horizontal line) ─────────────────
      if (a.type === 'entryline') {
        const y = this._y(a.price, lo, hi);
        ctx.strokeStyle = a.color || '#00c896';
        ctx.lineWidth   = a.width || 1;
        if (a.dash) ctx.setLineDash(a.dash);
        ctx.beginPath(); ctx.moveTo(P.left, y); ctx.lineTo(this.W - P.right, y); ctx.stroke();
        ctx.setLineDash([]);
        if (a.label) {
          ctx.fillStyle = a.color || '#00c896';
          ctx.font      = '10px sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(a.label, this.W - P.right - 2, y - 3);
        }
      }

      ctx.setLineDash([]); ctx.globalAlpha = 1;
    });
  }

  _badge(ctx, text, x, y, bg, fg = '#fff') {
    ctx.font = 'bold 10px sans-serif';
    const tw = ctx.measureText(text).width;
    const w  = tw + 8, h = 15;
    ctx.fillStyle = bg;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y - h / 2, w, h, 3);
    else ctx.rect(x, y - h / 2, w, h);
    ctx.fill();
    ctx.fillStyle = fg;
    ctx.textAlign = 'left';
    ctx.fillText(text, x + 4, y + 4);
  }
}

// ─── LEG BUILDER — DETERMINISTICKÝ (žádný Math.random) ───────────────────────
// Vytváří hladké svíčky od `from` do `to`.
// wickFactor: jak velké jsou knoty jako % pohybu jedné svíčky

function makeLeg(from, to, n, wickFactor = 0.28) {
  const candles = [];
  const step    = (to - from) / n;
  const wick    = Math.abs(step) * wickFactor;
  for (let i = 0; i < n; i++) {
    const o = from + step * i;
    const c = from + step * (i + 1);
    const h = Math.max(o, c) + wick;
    const l = Math.min(o, c) - wick;
    candles.push({ open: o, high: h, low: l, close: c });
  }
  return candles;
}

// Explicit OHLC svíčka
function C(o, h, l, c) { return { open: o, high: h, low: l, close: c }; }

// Konkatenace polí svíček
function join(...legs) { return [].concat(...legs); }

// Swing high/low z posledního prvku nohy
function swHigh(leg) { return leg[leg.length - 1].high; }
function swLow(leg)  { return leg[leg.length - 1].low; }

// ─── SCENE GENERATORS ────────────────────────────────────────────────────────

// ── 1. Market Structure (BOS + CHoCH) ────────────────────────────────────────
function makeMarketStructureScene() {
  /*
    Bullish trend: HH1 → HL1 → HH2 (BOS) → HL2 → HH3 (BOS)
    CHoCH: big drop → breaks HL2 → Change of Character
    Bearish start: LH1 + BOS down breaks HL1
  */
  const leg1 = makeLeg(1960, 1976, 5);   // up impulse 1
  const leg2 = makeLeg(1976, 1967, 3);   // pullback → HL1
  const leg3 = makeLeg(1967, 1991, 5);   // up impulse 2 → HH2, BOS above HH1
  const leg4 = makeLeg(1991, 1979, 3);   // pullback → HL2
  const leg5 = makeLeg(1979, 2004, 4);   // up impulse 3 → HH3, BOS above HH2
  const leg6 = makeLeg(2004, 1969, 7);   // big drop → CHoCH (breaks HL2 = 1979)
  const leg7 = makeLeg(1969, 1983, 3);   // bounce → LH1
  const leg8 = makeLeg(1983, 1955, 5);   // drop → BOS down

  const candles = join(leg1, leg2, leg3, leg4, leg5, leg6, leg7, leg8);

  // Candle indices of swing points (last candle of each leg)
  let i = 0;
  function end(leg) { i += leg.length; return i - 1; }

  const iHH1 = end(leg1);   // last candle of leg1
  const iHL1 = end(leg2);
  const iHH2 = end(leg3);   // BOS above HH1
  const iHL2 = end(leg4);
  const iHH3 = end(leg5);   // BOS above HH2
  const iCH  = end(leg6);   // CHoCH bottom
  const iLH1 = end(leg7);
  const iLL1 = end(leg8);

  // Exact swing prices from actual candle data
  const pHH1 = swHigh(leg1);
  const pHL1 = swLow(leg2);
  const pHH2 = swHigh(leg3);
  const pHL2 = swLow(leg4);
  const pHH3 = swHigh(leg5);
  const pCH  = swLow(leg6);
  const pLH1 = swHigh(leg7);
  const pLL1 = swLow(leg8);

  // BOS lines start from the FIRST candle of the leg that breaks the level
  const bos1From    = leg1.length + leg2.length;                                          // start of leg3 = idx 8
  const bos2From    = leg1.length + leg2.length + leg3.length + leg4.length;              // start of leg5 = idx 16
  const bosDownFrom = leg1.length + leg2.length + leg3.length + leg4.length + leg5.length + leg6.length + leg7.length; // start of leg8 = idx 30

  // CHoCH fires ~midway through leg6 when it crosses pHL2 (≈4th candle of leg6)
  const chochFrom   = leg1.length + leg2.length + leg3.length + leg4.length + leg5.length + 4; // idx 24

  const anns = [
    // ── Bullish swing labels ──
    { type: 'swingpoint', candle: iHH1, price: pHH1, label: 'HH', side: 'above', color: '#00c896', layer: 'fg' },
    { type: 'swingpoint', candle: iHL1, price: pHL1, label: 'HL', side: 'below', color: '#00c896', layer: 'fg' },
    { type: 'swingpoint', candle: iHH2, price: pHH2, label: 'HH', side: 'above', color: '#00c896', layer: 'fg' },
    { type: 'swingpoint', candle: iHL2, price: pHL2, label: 'HL', side: 'below', color: '#00c896', layer: 'fg' },
    { type: 'swingpoint', candle: iHH3, price: pHH3, label: 'HH', side: 'above', color: '#00c896', layer: 'fg' },
    // ── BOS lines (bullish) — dashed at exact swing high price ──
    { type: 'bosline', price: pHH1, fromCandle: bos1From, color: '#4a9eff', label: 'BOS ↑', layer: 'fg' },
    { type: 'bosline', price: pHH2, fromCandle: bos2From, color: '#4a9eff', label: 'BOS ↑', layer: 'fg' },
    // ── CHoCH line at HL2 price — breaks here ──
    { type: 'chochline', price: pHL2, fromCandle: chochFrom, color: '#f0b90b', label: 'CHoCH', layer: 'fg' },
    // ── Bearish swing labels ──
    { type: 'swingpoint', candle: iLH1, price: pLH1, label: 'LH', side: 'above', color: '#e84040', layer: 'fg' },
    { type: 'swingpoint', candle: iLL1, price: pLL1, label: 'LL', side: 'below', color: '#e84040', layer: 'fg' },
    // ── BOS down line at HL1 price ──
    { type: 'bosline', price: pHL1, fromCandle: bosDownFrom, color: '#e84040', label: 'BOS ↓', layer: 'fg' },
  ];

  return { candles, anns };
}

// ── 2. Liquidity Sweep (Equal Highs → Sweep → Reversal) ──────────────────────
function makeLiquidityScene() {
  /*
    - Range/slight uptrend with several candles touching the SAME high (= Equal Highs)
    - Liquidity sweep: one candle spikes ABOVE equal highs and closes back below
    - Sharp reversal down (Sell-side Distribution)
  */
  const EQL_HIGH = 2018;  // exact equal highs level
  const EQL_LOW  = 2002;  // approximate range low

  // Create 12 ranging candles; force candles 2, 6, 10 to have high = EQL_HIGH
  const rangeCandles = [];
  const prices = [2008, 2011, 2007, 2009, 2013, 2010, 2008, 2012, 2009, 2011, 2007, 2010];
  prices.forEach((close, i) => {
    const open  = i === 0 ? 2008 : prices[i - 1];
    const forceH = (i === 1 || i === 5 || i === 9);  // equal highs at these
    const h = forceH ? EQL_HIGH : Math.min(EQL_HIGH - 1, Math.max(open, close) + 3);
    const l = Math.max(EQL_LOW, Math.min(open, close) - 3);
    rangeCandles.push({ open, high: h, low: l, close });
  });

  // Sweep candle: opens inside range, high goes above EQL_HIGH, closes back below
  const sweepC = C(2012, EQL_HIGH + 8, 2007, 2008);   // high = 2026, close back in range

  // Reversal: 6 bearish candles dropping sharply
  const revLeg  = makeLeg(2008, 1982, 6, 0.2);

  const candles = join(rangeCandles, [sweepC], revLeg);

  const sweepIdx = 12;  // index of sweep candle

  const anns = [
    // Equal Highs zone (thin shaded area + line)
    { type: 'zone', top: EQL_HIGH + 1, bottom: EQL_HIGH - 1,
      fill: 'rgba(240,185,11,0.18)', border: '#f0b90b',
      label: 'Equal Highs — Buy-side Liquidity', labelColor: '#f0b90b', layer: 'bg' },
    // Dashed horizontal line at equal highs
    { type: 'hline', price: EQL_HIGH, color: 'rgba(240,185,11,0.5)', dash: [4, 3],
      width: 1, layer: 'bg' },
    // Arrow pointing DOWN at the sweep candle high (sweep direction)
    { type: 'arrow', candle: sweepIdx, price: sweepC.high + 2, dir: 'down',
      color: '#e84040', label: 'SWEEP', layer: 'fg' },
    // Arrow pointing DOWN showing the reversal (first candle of revLeg)
    { type: 'arrow', candle: sweepIdx + 2, price: candles[sweepIdx + 2].low - 2, dir: 'down',
      color: '#e84040', label: '', layer: 'fg' },
    // SSL label below range
    { type: 'hline', price: EQL_LOW - 1, color: 'rgba(0,200,150,0.35)', dash: [3, 3],
      width: 1, label: 'Sell-side Liq.', layer: 'bg' },
  ];

  return { candles, anns };
}

// ── 3. Order Block (Bullish OB) ───────────────────────────────────────────────
function makeOrderBlockScene() {
  /*
    Downtrend → last bearish candle (OB) → BIG impulse up (+ FVG) →
    pullback INTO OB zone → bounce up from OB
  */
  // Downtrend: 7 candles 1875 → 1848
  const dnLeg  = makeLeg(1875, 1850, 7, 0.22);

  // OB candle: last bearish before impulse (index 7)
  // Use explicit OHLC so we know exact values
  const obOpen  = 1850, obClose = 1841, obHigh = 1852, obLow = 1839;
  const obC     = C(obOpen, obHigh, obLow, obClose);

  // Impulse up (3 candles): 1841 → 1882 — creates FVG between obHigh(1852) and candle3.low
  const impC1   = C(1841, 1847, 1840, 1846);   // FVG c1 — high = 1847
  const impC2   = C(1846, 1885, 1845, 1882);   // BIG impulse
  const impC3   = C(1882, 1888, 1862, 1886);   // FVG c3 — low = 1862

  // FVG zone = impC1.high(1847) to impC3.low(1862)
  const fvgTop = impC3.low;    // 1862
  const fvgBot = impC1.high;   // 1847

  // Continue up (3 candles): 1886 → 1905
  const upLeg2 = makeLeg(1886, 1905, 3, 0.2);

  // Pullback into OB zone (5 candles): 1905 → 1843
  // OB zone = obLow(1839) to obHigh(1852)  → pullback enters zone at ~1845
  const pbLeg  = makeLeg(1905, 1843, 5, 0.2);

  // Bounce from OB (4 candles): 1843 → 1878
  const bnLeg  = makeLeg(1843, 1878, 4, 0.2);

  const candles = join(dnLeg, [obC, impC1, impC2, impC3], upLeg2, pbLeg, bnLeg);

  // Index of OB candle
  const iOB    = dnLeg.length;         // 7
  const iFVGc1 = iOB + 1;              // 8
  const iFVGc3 = iOB + 3;              // 10
  const iPBend = dnLeg.length + 4 + upLeg2.length + pbLeg.length - 1;  // last of pullback
  const iEntry = iPBend;               // arrow at bottom of pullback (inside OB)

  const anns = [
    // OB zone (full range of OB candle: obLow to obHigh)
    { type: 'zone', top: obHigh, bottom: obLow,
      fill: 'rgba(0,200,150,0.15)', border: '#00c896',
      label: 'Bullish Order Block', labelColor: '#00c896', layer: 'bg' },

    // FVG zone (between c1.high and c3.low)
    { type: 'zone', top: fvgTop, bottom: fvgBot,
      fill: 'rgba(74,158,255,0.12)', border: '#4a9eff',
      label: 'FVG', labelColor: '#4a9eff', layer: 'bg' },

    // Entry arrow at bottom of pullback (inside OB)
    { type: 'arrow', candle: iEntry, price: candles[iEntry].low - 3,
      dir: 'up', color: '#00c896', label: 'Vstup', layer: 'fg' },
  ];

  return { candles, anns };
}

// ── 4. FVG (Fair Value Gap) ────────────────────────────────────────────────────
function makeFVGScene() {
  /*
    Pre-impulse candles → FVG 3-svíčkový vzor → continuation up →
    pullback INTO FVG (hits 50%) → bounce
  */
  // Background: 8 candles up 1900 → 1912
  const preLeg  = makeLeg(1900, 1912, 8, 0.2);

  // FVG setup (3 explicit candles):
  const fvgC1 = C(1912, 1916, 1910, 1914);   // small bull — high = 1916
  const fvgC2 = C(1914, 1954, 1913, 1951);   // BIG impulse (gap creator)
  const fvgC3 = C(1951, 1957, 1932, 1955);   // small — low = 1932
  // FVG = fvgC1.high(1916) to fvgC3.low(1932)  ← gap between these two

  const fvgTop  = fvgC3.low;   // 1932
  const fvgBot  = fvgC1.high;  // 1916
  const fvgMid  = (fvgTop + fvgBot) / 2;   // 1924

  // Continue up (4 candles): 1955 → 1970
  const upLeg2  = makeLeg(1955, 1970, 4, 0.2);

  // Retrace: goes to fvgMid ≈ 1924 (well into FVG zone [1916-1932])
  const pbLeg   = makeLeg(1970, 1925, 6, 0.18);

  // Bounce up (4 candles): 1925 → 1960
  const bnLeg   = makeLeg(1925, 1960, 4, 0.2);

  const candles = join(preLeg, [fvgC1, fvgC2, fvgC3], upLeg2, pbLeg, bnLeg);

  // Indices
  const iFVG1  = preLeg.length;                    // 8
  const iFVG2  = iFVG1 + 1;                        // 9
  const iFVG3  = iFVG1 + 2;                        // 10
  const iPBend = preLeg.length + 3 + upLeg2.length + pbLeg.length - 1;

  const anns = [
    // FVG zone (from c1.high to c3.low)
    { type: 'zone', top: fvgTop, bottom: fvgBot,
      fill: 'rgba(0,200,150,0.15)', border: '#00c896',
      label: 'Bullish FVG', labelColor: '#00c896', layer: 'bg' },

    // 50% FVG line (midpoint)
    { type: 'hline', price: fvgMid, color: '#f0b90b', dash: [5, 3], width: 1,
      label: '50% FVG', layer: 'bg' },

    // Labels at FVG candle extremes
    { type: 'swingpoint', candle: iFVG1, price: fvgBot, label: 'c1.high', side: 'above',
      color: '#00c896', layer: 'fg' },
    { type: 'swingpoint', candle: iFVG3, price: fvgTop, label: 'c3.low', side: 'below',
      color: '#00c896', layer: 'fg' },

    // Entry arrow at bottom of retrace (inside FVG, near 50%)
    { type: 'arrow', candle: iPBend, price: candles[iPBend].low - 3,
      dir: 'up', color: '#00c896', label: 'Vstup', layer: 'fg' },
  ];

  return { candles, anns, fvgTop, fvgBot, fvgMid };
}

// ── 5. OTE (Optimal Trade Entry — Fibonacci) ──────────────────────────────────
function makeOTEScene() {
  /*
    Pre-range → sweep low → impulse up (swing low → swing high) →
    retrace into OTE zone (62-79%) → bounce from OTE to new high
  */
  // Pre-range: 4 candles flat around 2048
  const preLeg = makeLeg(2052, 2048, 4, 0.15);

  // Sweep of swing low (1 candle): spike down then reverse
  const sweepC = C(2048, 2049, 2040, 2047);  // spike below, close above low

  // Impulse UP (swing low to swing high):
  // Swing Low = sweepC.low = 2040  (that's the measured point)
  // Target Swing High = 2040 + 55 = 2095
  const swingLow  = sweepC.low;   // 2040
  const swingHigh = 2095;

  const impLeg = makeLeg(2047, swingHigh, 6, 0.18);

  // OTE levels (from swingLow to swingHigh, range = 55)
  const range  = swingHigh - swingLow;
  const ote62  = swingHigh - range * 0.62;    // 2095 - 34.1 = 2060.9
  const ote705 = swingHigh - range * 0.705;   // 2095 - 38.775 = 2056.2
  const ote79  = swingHigh - range * 0.79;    // 2095 - 43.45 = 2051.6
  const eq50   = swingHigh - range * 0.50;    // 2095 - 27.5 = 2067.5

  // Retrace: goes to ote705 ≈ 2056 (inside OTE zone [2051.6 - 2060.9])
  const pbLeg  = makeLeg(swingHigh, ote705, 7, 0.18);

  // Bounce up past swing high (new TP)
  const bnLeg  = makeLeg(ote705, swingHigh + 18, 6, 0.18);

  const candles = join(preLeg, [sweepC], impLeg, pbLeg, bnLeg);

  const iPBend = preLeg.length + 1 + impLeg.length + pbLeg.length - 1;
  const iImpEnd = preLeg.length + 1 + impLeg.length - 1;

  const anns = [
    // Swing Low and High reference lines
    { type: 'hline', price: swingLow, color: 'rgba(232,64,64,0.5)', dash: [3, 3], width: 1,
      label: 'Swing Low (0%)', layer: 'bg' },
    { type: 'hline', price: swingHigh, color: 'rgba(0,200,150,0.5)', dash: [3, 3], width: 1,
      label: 'Swing High (100%)', layer: 'bg' },

    // 50% Equilibrium line
    { type: 'hline', price: eq50, color: 'rgba(74,158,255,0.45)', dash: [4, 3], width: 1,
      label: '50% EQ', layer: 'bg' },

    // OTE zone (62–79%)
    { type: 'zone', top: ote62, bottom: ote79,
      fill: 'rgba(0,200,150,0.13)', border: '#00c896',
      label: 'OTE zóna 62–79%', labelColor: '#00c896', layer: 'bg' },

    // 70.5% Sweet Spot line
    { type: 'hline', price: ote705, color: '#f0b90b', dash: [5, 2], width: 1.5,
      label: '70.5% Sweet Spot ⭐', layer: 'bg' },

    // OTE boundary labels
    { type: 'swingpoint', candle: iPBend, price: ote62,  label: '62%', side: 'above',
      color: '#8892a4', layer: 'fg' },
    { type: 'swingpoint', candle: iPBend, price: ote79,  label: '79%', side: 'below',
      color: '#8892a4', layer: 'fg' },

    // Entry arrow at bottom of retrace (inside OTE zone)
    { type: 'arrow', candle: iPBend, price: candles[iPBend].low - 2,
      dir: 'up', color: '#00c896', label: 'Vstup', layer: 'fg' },

    // SL line (just below swing low)
    { type: 'entryline', price: swingLow - 2, color: '#e84040', dash: [3, 3],
      width: 1, label: 'SL', layer: 'bg' },
  ];

  return { candles, anns, swingLow, swingHigh, ote62, ote705, ote79 };
}

// ── 6. AMD — Power of 3 ───────────────────────────────────────────────────────
function makeAMDScene() {
  /*
    BULLISH AMD day:
    Accumulation: tight Asian range 1975–1985
    Manipulation: Judas Swing DOWN below Asian Low (= false bearish breakout)
    Distribution: strong move UP through Asian High and beyond
  */
  const ASIAN_HIGH = 1986;
  const ASIAN_LOW  = 1974;

  // Accumulation: 10 tight candles staying in [1974, 1986]
  const accCandles = [];
  const accPrices  = [1979, 1981, 1978, 1983, 1980, 1977, 1982, 1979, 1984, 1981];
  accPrices.forEach((cl, i) => {
    const op = i === 0 ? 1979 : accPrices[i - 1];
    const h  = Math.min(ASIAN_HIGH, Math.max(op, cl) + 3);
    const l  = Math.max(ASIAN_LOW,  Math.min(op, cl) - 3);
    accCandles.push({ open: op, high: h, low: l, close: cl });
  });

  // Judas Swing (Manipulation): 2 candles spiking below Asian Low
  const judas1 = C(1981, 1983, 1963, 1965);   // spike to 1963 (below Asian Low 1974!)
  const judas2 = C(1965, 1968, 1961, 1963);   // continuation down (to 1961)

  // CHoCH / reversal: 1 strong bullish candle back above Asian Low
  const reversal = C(1963, 1978, 1962, 1977);

  // Distribution: 8 strong bullish candles 1977 → 2025
  const distLeg = makeLeg(1977, 2025, 8, 0.15);

  const candles = join(accCandles, [judas1, judas2, reversal], distLeg);

  const iJudas1  = accCandles.length;       // 10
  const iJudas2  = iJudas1 + 1;             // 11
  const iRev     = iJudas2 + 1;             // 12
  const iDistEnd = candles.length - 1;

  const anns = [
    // Asian High/Low zone
    { type: 'zone', top: ASIAN_HIGH, bottom: ASIAN_LOW,
      fill: 'rgba(155,89,182,0.1)', border: 'rgba(155,89,182,0.6)',
      label: 'Asian Range (Accumulation)', labelColor: '#9b59b6', layer: 'bg' },

    // Asian High / Low dashed lines
    { type: 'hline', price: ASIAN_HIGH, color: 'rgba(155,89,182,0.7)', dash: [5, 3],
      width: 1, label: 'Asian High', layer: 'bg' },
    { type: 'hline', price: ASIAN_LOW, color: 'rgba(155,89,182,0.7)', dash: [5, 3],
      width: 1, label: 'Asian Low', layer: 'bg' },

    // Judas Swing arrow (DOWN) — at the spike low
    { type: 'arrow', candle: iJudas2, price: judas2.low - 3,
      dir: 'down', color: '#e84040', label: 'Judas Swing', layer: 'fg' },

    // Annotation: sweep of Asian Low
    { type: 'hline', price: judas2.low, color: 'rgba(232,64,64,0.4)', dash: [3, 2],
      width: 1, label: 'Sweep pod Asian Low', layer: 'bg', fromCandle: iJudas1 },

    // Reversal / Distribution arrow (UP)
    { type: 'arrow', candle: iRev + 1, price: candles[iRev + 1].low - 2,
      dir: 'up', color: '#00c896', label: 'Distribution ↑', layer: 'fg' },
  ];

  return { candles, anns, ASIAN_HIGH, ASIAN_LOW };
}
