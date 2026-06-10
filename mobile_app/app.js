// ─── DATA ──────────────────────────────────────────────────────────────────

const SYMBOLS  = ['EURUSD','GBPUSD','USDJPY','XAUUSD','USDCAD','AUDUSD',
                   'NZDUSD','EURGBP','EURJPY','GBPJPY','US30','NAS100','SPX500'];
const SESSIONS = ['London','New York','Asian','Pacific','Overlap'];
const SETUPS   = ['Golden Zone','OTE','Discount','Premium','FVG','Order Block',
                   'Breaker Block','Mitigation','CISD','BOS','CHoCH'];
const RESULTS  = ['win','loss','be'];

function loadTrades()  { try { return JSON.parse(localStorage.getItem('smc-trades') || '[]'); } catch { return []; } }
function saveTrades(t) { localStorage.setItem('smc-trades', JSON.stringify(t)); }

let trades = loadTrades();

// Draft pro rozpracovaný obchod
let draft = newDraft();

function newDraft() {
  const now = new Date();
  const fmt = d => d.toISOString().slice(0,16);
  return {
    id: null,
    symbol: 'EURUSD',
    smer: '',
    vstupni_hodnota: '',
    stoploss: '',
    takeprofit: '',
    rrr: '',
    pips: '',
    cas_otevreni: fmt(now),
    cas_zavreni: '',
    session: '',
    fibo_setup: '',
    vysledek: '',
    poznamka: '',
    duvod: '',
    tags: '',
    synced: false,
    created_at: now.toISOString()
  };
}

// ─── ROUTER ────────────────────────────────────────────────────────────────

let currentScreen = 'home';
let editingId     = null;
let listFilter    = 'all';

function navigate(screen, opts = {}) {
  currentScreen = screen;
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

  const el = document.getElementById('screen-' + screen);
  if (el) el.classList.add('active');

  const navBtn = document.querySelector(`.nav-btn[data-screen="${screen}"]`);
  if (navBtn) navBtn.classList.add('active');

  if (screen === 'home')  renderHome();
  if (screen === 'new')   renderNewTrade(opts.editId || null);
  if (screen === 'list')  renderList();

  // Scroll to top
  if (el) el.scrollTop = 0;
}

// ─── CALCULATIONS ──────────────────────────────────────────────────────────

function calcRRR(entry, sl, tp) {
  const e = parseFloat(entry), s = parseFloat(sl), t = parseFloat(tp);
  if (!e || !s || !t || e === s) return null;
  const risk   = Math.abs(e - s);
  const reward = Math.abs(t - e);
  return (reward / risk).toFixed(2);
}

function calcPips(entry, sl) {
  const e = parseFloat(entry), s = parseFloat(sl);
  if (!e || !s) return null;
  const diff = Math.abs(e - s);
  // XAUUSD → pips = diff*10, Forex → diff*10000
  const sym = draft.symbol || '';
  if (sym.includes('JPY')) return (diff * 100).toFixed(1);
  if (sym === 'XAUUSD') return (diff * 10).toFixed(1);
  return (diff * 10000).toFixed(1);
}

function updateRRRDisplay() {
  const e = draft.vstupni_hodnota, sl = draft.stoploss, tp = draft.takeprofit;
  const rrr  = calcRRR(e, sl, tp);
  const pips = calcPips(e, sl);
  draft.rrr  = rrr || '';
  draft.pips = pips || '';
  const el = document.getElementById('rrr-display');
  if (!el) return;
  if (rrr) {
    el.textContent = `RRR  1:${rrr}${pips ? `   |   SL = ${pips} pips` : ''}`;
    el.style.display = 'block';
  } else {
    el.style.display = 'none';
  }
}

// ─── HOME SCREEN ───────────────────────────────────────────────────────────

function renderHome() {
  const today = new Date().toDateString();
  const todayTrades = trades.filter(t => new Date(t.created_at).toDateString() === today);
  const wins   = todayTrades.filter(t => t.vysledek === 'win').length;
  const losses = todayTrades.filter(t => t.vysledek === 'loss').length;
  const total  = todayTrades.length;

  document.getElementById('home-stats').innerHTML = `
    <div class="stat">
      <div class="stat-val blue">${total}</div>
      <div class="stat-lbl">Dnes</div>
    </div>
    <div class="stat">
      <div class="stat-val green">${wins}</div>
      <div class="stat-lbl">Win</div>
    </div>
    <div class="stat">
      <div class="stat-val red">${losses}</div>
      <div class="stat-lbl">Loss</div>
    </div>
  `;

  // Posledních 5 obchodů
  const recent = [...trades].reverse().slice(0, 5);
  const listEl = document.getElementById('recent-list');
  if (recent.length === 0) {
    listEl.innerHTML = `<div style="color:var(--sub);font-size:13px;text-align:center;padding:16px 0;">Zatím žádné obchody. Přidej první! 👆</div>`;
  } else {
    listEl.innerHTML = recent.map(tradeCardHTML).join('');
  }

  // Update header date
  const opts = { weekday:'long', day:'numeric', month:'long' };
  document.getElementById('home-date').textContent =
    new Date().toLocaleDateString('cs-CZ', opts);
}

// ─── NEW TRADE SCREEN ──────────────────────────────────────────────────────

function renderNewTrade(editId = null) {
  editingId = editId;
  if (editId) {
    const t = trades.find(t => t.id === editId);
    if (t) draft = { ...t };
  } else {
    draft = newDraft();
  }

  const isEdit = !!editId;
  document.getElementById('new-header-title').textContent = isEdit ? 'Upravit obchod' : 'Nový obchod';
  document.getElementById('new-back').style.display = 'flex';

  const screen = document.getElementById('screen-new');
  screen.innerHTML = buildFormHTML();
  bindFormEvents();
  updateRRRDisplay();
}

function buildFormHTML() {
  const d = draft;

  // Symbol chips (scrollable)
  const symChips = SYMBOLS.map(s =>
    `<div class="chip${d.symbol === s ? ' active' : ''}" onclick="setField('symbol','${s}');refreshChips('symbol',this.parentNode,'${s}')">${s}</div>`
  ).join('');

  // Session chips
  const sesChips = SESSIONS.map(s =>
    `<div class="chip${d.session === s ? ' active' : ''}" onclick="setField('session','${s}');refreshChips('session',this.parentNode,'${s}')">${s}</div>`
  ).join('');

  // Setup chips
  const setupChips = SETUPS.map(s =>
    `<div class="chip${d.fibo_setup === s ? ' active' : ''}" onclick="setField('fibo_setup','${s}');refreshChips('fibo_setup',this.parentNode,'${s}')">${s}</div>`
  ).join('');

  // Result chips
  const resChips = [
    ['win','WIN ✅','win-chip'],
    ['loss','LOSS ❌','loss-chip'],
    ['be','BE ↔','be-chip']
  ].map(([v,label,cls]) =>
    `<div class="chip ${cls}${d.vysledek === v ? ' active' : ''}" onclick="setField('vysledek','${v}');refreshChips('vysledek',this.parentNode,'${v}')">${label}</div>`
  ).join('');

  const isEdit = !!editingId;

  return `
    <!-- Symbol -->
    <div class="form-section">
      <div class="form-section-title">Symbol</div>
      <div class="chips" id="chips-symbol">${symChips}</div>
      <div class="field">
        <label>nebo zadej ručně</label>
        <input type="text" value="${d.symbol}" placeholder="např. EURUSD"
               oninput="setField('symbol',this.value)" style="text-transform:uppercase">
      </div>
    </div>

    <!-- Směr -->
    <div class="form-section">
      <div class="form-section-title">Směr</div>
      <div class="dir-toggle">
        <div class="dir-btn buy${d.smer==='Buy'?' active':''}" onclick="setDir('Buy')">▲ BUY</div>
        <div class="dir-btn sell${d.smer==='Sell'?' active':''}" onclick="setDir('Sell')">▼ SELL</div>
      </div>
    </div>

    <!-- Ceny -->
    <div class="form-section">
      <div class="form-section-title">Ceny</div>
      <div class="field-row3">
        <div class="field">
          <label>Entry</label>
          <input type="number" step="any" value="${d.vstupni_hodnota}" placeholder="0.00000"
                 oninput="setField('vstupni_hodnota',this.value);updateRRRDisplay()">
        </div>
        <div class="field">
          <label>Stop Loss</label>
          <input type="number" step="any" value="${d.stoploss}" placeholder="0.00000"
                 oninput="setField('stoploss',this.value);updateRRRDisplay()">
        </div>
        <div class="field">
          <label>Take Profit</label>
          <input type="number" step="any" value="${d.takeprofit}" placeholder="0.00000"
                 oninput="setField('takeprofit',this.value);updateRRRDisplay()">
        </div>
      </div>
      <div class="rrr-badge" id="rrr-display" style="display:none"></div>
    </div>

    <!-- Čas -->
    <div class="form-section">
      <div class="form-section-title">Datum & čas</div>
      <div class="field-row">
        <div class="field">
          <label>Otevření</label>
          <input type="datetime-local" value="${d.cas_otevreni}"
                 oninput="setField('cas_otevreni',this.value)">
        </div>
        <div class="field">
          <label>Zavření</label>
          <input type="datetime-local" value="${d.cas_zavreni}"
                 oninput="setField('cas_zavreni',this.value)">
        </div>
      </div>
    </div>

    <!-- Session -->
    <div class="form-section">
      <div class="form-section-title">Seance</div>
      <div class="chips" id="chips-session">${sesChips}</div>
    </div>

    <!-- Setup -->
    <div class="form-section">
      <div class="form-section-title">Setup</div>
      <div class="chips" id="chips-fibo_setup">${setupChips}</div>
    </div>

    <!-- Výsledek -->
    <div class="form-section">
      <div class="form-section-title">Výsledek</div>
      <div class="chips" id="chips-vysledek">${resChips}</div>
    </div>

    <!-- Poznámky -->
    <div class="form-section">
      <div class="form-section-title">Poznámky</div>
      <div class="field">
        <label>Důvod vstupu</label>
        <textarea placeholder="Proč jsem vstoupil..." oninput="setField('duvod',this.value)">${d.duvod}</textarea>
      </div>
      <div class="field">
        <label>Poznámka</label>
        <textarea placeholder="Co jsem si všiml..." oninput="setField('poznamka',this.value)">${d.poznamka}</textarea>
      </div>
      <div class="field">
        <label>Štítky (Tags)</label>
        <input type="text" value="${d.tags}" placeholder="např. fomo, reversal, liquidity"
               oninput="setField('tags',this.value)">
      </div>
    </div>

    <!-- Uložit -->
    <button class="save-btn" onclick="saveTrade()">
      ${isEdit ? '💾  Uložit změny' : '✅  Uložit obchod'}
    </button>
    ${isEdit ? `<button class="del-btn" onclick="deleteTrade('${editingId}')">🗑  Smazat obchod</button>` : ''}
    <div style="height:8px"></div>
  `;
}

function bindFormEvents() {
  // Nothing extra needed — all handlers are inline
}

function setField(key, val) {
  draft[key] = val;
}

function setDir(dir) {
  draft.smer = dir;
  document.querySelectorAll('.dir-btn').forEach(b => {
    b.classList.toggle('active', b.classList.contains(dir.toLowerCase()));
  });
}

function refreshChips(field, container, val) {
  // Toggle active on sibling chips (single select)
  container.querySelectorAll('.chip').forEach(c => {
    const isMatch = c.textContent.trim().replace(' ✅','').replace(' ❌','').replace(' ↔','') === val ||
                    c.getAttribute('onclick')?.includes(`'${val}'`);
    c.classList.toggle('active', isMatch);
  });
}

// ─── SAVE / DELETE ─────────────────────────────────────────────────────────

function saveTrade() {
  if (!draft.symbol) { showToast('Vyber symbol'); return; }
  if (!draft.smer)   { showToast('Vyber směr (Buy/Sell)'); return; }

  if (editingId) {
    const idx = trades.findIndex(t => t.id === editingId);
    if (idx !== -1) {
      trades[idx] = { ...draft, synced: false };
    }
    showToast('Obchod upraven ✏️');
  } else {
    draft.id = Date.now();
    draft.created_at = new Date().toISOString();
    draft.synced = false;
    trades.push({ ...draft });
    showToast('Obchod uložen ✅');
  }

  saveTrades(trades);
  setTimeout(() => navigate('home'), 600);
}

function deleteTrade(id) {
  if (!confirm('Smazat tento obchod?')) return;
  trades = trades.filter(t => String(t.id) !== String(id));
  saveTrades(trades);
  showToast('Smazáno 🗑');
  setTimeout(() => navigate('list'), 400);
}

// ─── LIST SCREEN ───────────────────────────────────────────────────────────

function renderList() {
  const filterBtns = ['all','win','loss','be'].map(f =>
    `<div class="chip${listFilter === f ? ' active' : ''}" onclick="setFilter('${f}')">${
      f === 'all' ? 'Vše' : f.toUpperCase()
    }</div>`
  ).join('');

  document.getElementById('list-filters').innerHTML = filterBtns;

  const filtered = listFilter === 'all'
    ? [...trades].reverse()
    : [...trades].filter(t => t.vysledek === listFilter).reverse();

  const listEl = document.getElementById('trade-list');
  if (filtered.length === 0) {
    listEl.innerHTML = `<div class="empty"><div class="eicon">📭</div><p>Žádné obchody</p></div>`;
  } else {
    listEl.innerHTML = filtered.map(tradeCardHTML).join('');
  }
}

function setFilter(f) {
  listFilter = f;
  renderList();
}

function tradeCardHTML(t) {
  const res = t.vysledek || 'pending';
  const resLabel = { win:'WIN', loss:'LOSS', be:'BE', pending:'...' }[res] || res.toUpperCase();
  const dt = t.cas_otevreni ? t.cas_otevreni.replace('T',' ').slice(0,16) : '';
  const rrr = t.rrr ? `1:${t.rrr}` : '';
  const sync = t.synced
    ? '<span class="sync-badge synced">✓ sync</span>'
    : '<span class="sync-badge">⏳ local</span>';

  return `
    <div class="trade-card ${res}" onclick="navigate('new',{editId:${t.id}})">
      <div class="tc-left">
        <div class="tc-symbol">${t.symbol} <span style="font-size:13px;color:var(--sub);font-weight:400">${t.smer || ''}</span></div>
        <div class="tc-meta">${dt}${t.session ? ' · '+t.session : ''}${t.fibo_setup ? ' · '+t.fibo_setup : ''}</div>
      </div>
      <div class="tc-right">
        <div class="tc-result ${res}">${resLabel}</div>
        <div class="tc-rrr">${rrr}${sync}</div>
      </div>
    </div>
  `;
}

// ─── TOAST ─────────────────────────────────────────────────────────────────

let toastTimer = null;
function showToast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2200);
}

// ─── EXPORT ────────────────────────────────────────────────────────────────

function exportTrades() {
  const data = JSON.stringify(trades, null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url;
  a.download = `smc_trades_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Export uložen 📁');
}

// ─── INIT ──────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }

  navigate('home');
});
