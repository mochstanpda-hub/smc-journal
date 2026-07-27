# Claude Trade Analyzer — Kontext projektu

## Účel
Tento projekt slouží k analýze trading screenshotů z platformy TradingView.
Uživatel nahraje screenshot, ty provedete analýzu a uložíš výsledek jako JSON soubor,
který uživatel načte do svého obchodního deníku (BACKTESTING.py).

---

## Jak analyzovat screenshot (TradingView)

### KROK 1 — Ceny na pravé cenové ose
Na pravé vertikální ose jsou 3 ceny se zvýrazněným pozadím:
- **MODRÁ** = Entry (vstupní cena)
- **ČERVENÁ** = Stop Loss
- **ZELENÁ** = Take Profit

Přečti přesné číselné hodnoty těchto tří cen.

### KROK 2 — Směr obchodu
Urči směr z logiky cen:
- Stop Loss > Entry > Take Profit → **SHORT**
- Take Profit > Entry > Stop Loss → **LONG**

### KROK 3 — Časy na dolní ose (X osa)
Hledej zvýrazněné časové labely (barevný box na časové ose) — označují otevření a uzavření obchodu.
- Datum jako `Mon 27 Jul 26` převeď na `2026-07-27`
- Výstupní formát: `YYYY-MM-DD HH:MM`

### KROK 4 — Záhlaví grafu (levý horní roh)
- **Symbol**: přesný ticker (XAUUSD, US100, NQ, EURUSD, DAX, ...)
- **Timeframe**: číslo + písmeno (3m, 5m, 15m, 1h, 4h, D)

### KROK 5 — Pojmenované horizontální čáry na grafu
Viditelné labely na levém nebo pravém okraji grafu: ON VAH, ON VAL, ON POC, ON High, ON Low,
RTH High, RTH VAH, RTH POC, RTH VAL, RTH Low, PDH, PDL, VWAP, DAY open, atd.

Urči:
- Která čára je **nejblíže nebo na ní leží Take Profit**? → `tp_level`
- Která čára je **nejblíže nebo na ní leží Stop Loss**? → `sl_level`
- U které čáry/čar leží **Entry** nebo se k nim obchod vztahuje? → `fibo` (max 3)

Pokud TP/SL leží těsně **pod** nebo **nad** zelenou křivkou VWAP, použij: `"pod VWAP"` nebo `"nad VWAP"`.

### KROK 6 — Session
Pravý dolní roh grafu:
- Nápis `RTH` → session = `"RTH"`
- Jinak → session = `"OVERNIGHT"`

---

## Platné hodnoty polí

### `smer`
```
LONG, SHORT
```

### `timeframe_vstup` a `timeframe_graf`
```
1m, 5m, 15m, 30m, 1h, 4h, 1d, 1W, 1M
```

### `session`
```
OVERNIGHT, RTH
```

### `fibo` — setup/úrovně vstupu (max 3 hodnoty jako pole)
```
ON VAH, ON VAL, ON POC, ON High, ON Low,
RTH VAH, RTH VAL, RTH POC, RTH High, RTH Low,
PDH, PDL,
VWAP, VWAP +1σ, VWAP -1σ, VWAP +2σ, VWAP -2σ,
DAY open
```

### `tp_level` a `sl_level` — úrovně kde leží TP/SL (max 3 hodnoty jako pole)
```
ON VAH, ON VAL, ON POC, ON High, ON Low,
RTH VAH, RTH VAL, RTH POC, RTH High, RTH Low,
PDH, PDL,
VWAP, VWAP +1σ, VWAP -1σ, VWAP +2σ, VWAP -2σ,
pod VWAP, nad VWAP,
pod VWAP +1σ, nad VWAP +1σ,
pod VWAP -1σ, nad VWAP -1σ,
DAY open
```

---

## Výstupní JSON schéma

Po analýze screenshotu vytvoř JSON soubor s tímto přesným formátem.
Pokud hodnotu nelze spolehlivě určit, použij `null`.

```json
{
  "symbol": "XAUUSD",
  "smer": "SHORT",
  "vstupni_hodnota": 4088.89,
  "stoploss": 4094.21,
  "takeprofit": 4072.81,
  "cas_otevreni": "2026-07-27 18:41",
  "cas_zavreni": "2026-07-27 19:41",
  "timeframe_vstup": "3m",
  "timeframe_graf": "3m",
  "session": "RTH",
  "fibo": ["VWAP", "ON POC"],
  "tp_level": ["RTH VAL"],
  "sl_level": ["RTH High"],
  "tp_level_note": "",
  "sl_level_note": "",
  "duvod": "",
  "poznamka": ""
}
```

### Popis polí

| Pole | Typ | Popis |
|---|---|---|
| `symbol` | string | Ticker přesně z grafu |
| `smer` | string | LONG nebo SHORT |
| `vstupni_hodnota` | number | Entry cena (modrá na pravé ose) |
| `stoploss` | number | Stop Loss cena (červená na pravé ose) |
| `takeprofit` | number | Take Profit cena (zelená na pravé ose) |
| `cas_otevreni` | string | Datum a čas otevření, formát `YYYY-MM-DD HH:MM` |
| `cas_zavreni` | string | Datum a čas uzavření, formát `YYYY-MM-DD HH:MM` (null pokud není vidět) |
| `timeframe_vstup` | string | Timeframe vstupu (z hlavičky grafu) |
| `timeframe_graf` | string | Timeframe grafu (stejný jako vstup pokud jen jeden) |
| `session` | string | RTH nebo OVERNIGHT |
| `fibo` | array | Úrovně kde leží entry (max 3, z platných hodnot výše) |
| `tp_level` | array | Úrovně kde leží TP (max 3, z platných hodnot výše) |
| `sl_level` | array | Úrovně kde leží SL (max 3, z platných hodnot výše) |
| `tp_level_note` | string | Volitelná poznámka k TP úrovni (ponech prázdné pokud nemáš co dodat) |
| `sl_level_note` | string | Volitelná poznámka k SL úrovni (ponech prázdné pokud nemáš co dodat) |
| `duvod` | string | Důvod vstupu — stručně popiš setup který vidíš na grafu |
| `poznamka` | string | Libovolná poznámka (ponech prázdné) |

---

## Instrukce pro uložení výstupu

1. Proveď analýzu screenshotu
2. Vypiš výsledky do chatu (tabulka nebo seznam) aby je uživatel viděl
3. Vytvoř soubor `trade_analysis.json` s výstupním JSON
4. Uživatel soubor načte do programu BACKTESTING.py tlačítkem **📂 Načíst analýzu (JSON)**

---

## Příklad analýzy (referenční obchod)

**Screenshot**: XAUUSD, 3m graf, RTH session, 2026-07-27

**Co vidím**:
- Pravá osa: modrá = 4 088.89 (entry), červená = 4 094.21 (SL), zelená = 4 072.81 (TP)
- SL (4 094.21) > Entry (4 088.89) > TP (4 072.81) → **SHORT**
- Čas otevření: 2026-07-27 18:41, uzavření: 2026-07-27 19:41
- Entry leží těsně pod VWAP (zelená křivka) a u ON POC čáry
- SL leží na RTH High čáře
- TP leží na RTH VAL čáře
- RRR: 3.02

**Výstup**:
```json
{
  "symbol": "XAUUSD",
  "smer": "SHORT",
  "vstupni_hodnota": 4088.89,
  "stoploss": 4094.21,
  "takeprofit": 4072.81,
  "cas_otevreni": "2026-07-27 18:41",
  "cas_zavreni": "2026-07-27 19:41",
  "timeframe_vstup": "3m",
  "timeframe_graf": "3m",
  "session": "RTH",
  "fibo": ["pod VWAP", "ON POC"],
  "tp_level": ["RTH VAL"],
  "sl_level": ["RTH High"],
  "tp_level_note": "",
  "sl_level_note": "",
  "duvod": "Short od RTH High, entry pod VWAP, mean reversion na RTH VAL",
  "poznamka": ""
}
```
