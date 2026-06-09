// ─── NAVIGATION ───────────────────────────────────────────────────────────────

const visited = new Set(JSON.parse(localStorage.getItem('ict-visited') || '[]'));

function showPage(id, navEl) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById('page-' + id);
  if (page) page.classList.add('active');

  if (navEl) {
    navEl.classList.add('active');
  } else {
    const found = document.querySelector(`.nav-item[data-page="${id}"]`);
    if (found) found.classList.add('active');
  }

  if (id.startsWith('m')) {
    visited.add(id);
    localStorage.setItem('ict-visited', JSON.stringify([...visited]));
    updateProgress();
    markNavCompleted();
  }

  // Render charts lazily
  if (id === 'm2') renderMarketStructureChart();
  if (id === 'm3') renderLiquidityChart();
  if (id === 'm4') renderOrderBlockChart();
  if (id === 'm5') renderFVGChart();
  if (id === 'm6') renderSessionsChart();
  if (id === 'm7') renderOTEChart();
  if (id === 'm8') renderAMDChart();

  window.scrollTo(0, 0);
}

function updateProgress() {
  const total = 10;
  const done = [...visited].filter(v => v.startsWith('m')).length;
  document.getElementById('progress-text').textContent = `${done} / ${total} lekcí`;
  document.getElementById('progress-fill').style.width = (done / total * 100) + '%';
}

function markNavCompleted() {
  visited.forEach(id => {
    const el = document.querySelector(`.nav-item[data-page="${id}"]`);
    if (el && !el.classList.contains('active')) el.classList.add('completed');
  });
}

// ─── QUIZ DATA ────────────────────────────────────────────────────────────────

const QUIZZES = {
  'm1': [
    {
      q: 'Co je hlavním principem ICT strategie?',
      opts: [
        'Obchodování s pomocí indikátorů jako RSI a MACD',
        'Trh je řízen institucemi, které manipulují cenou za účelem získání likvidity',
        'Strategie založená na fundamentální analýze',
        'Obchodování breakoutů z technických vzorů'
      ],
      correct: 1,
      explain: 'ICT je postaveno na myšlence, že trh pohybují velké instituce (banky, hedge fondy), které záměrně manipulují cenou, aby získaly likviditu (stop-lossy retail obchodníků) pro vstup do velkých pozic.'
    },
    {
      q: 'Co je IPDA v ICT terminologii?',
      opts: [
        'Indikátor pro predikci ceny',
        'Interbank Price Delivery Algorithm — algoritmus pohybující cenou na mezibankovním trhu',
        'Typ order bloku',
        'Zkratka pro stop-loss strategii'
      ],
      correct: 1,
      explain: 'IPDA (Interbank Price Delivery Algorithm) je podle ICT metodologie algoritmus, který řídí pohyb ceny — pohybuje ji k likviditě, sbírá ji, vyrovnává nerovnováhy a pak pokračuje v trendu.'
    },
    {
      q: 'Proč retail obchodníci podle ICT neustále prohrávají?',
      opts: [
        'Nemají dost kapitálu',
        'Obchodují v nesprávný čas s nesprávnými nástroji a záměrně je instituce loví',
        'Nepoužívají stop-lossy',
        'Obchodují příliš málo'
      ],
      correct: 1,
      explain: 'Retail obchodníci vstupují na breakoutech, dávají stop-lossy na logická místa (pod support, nad resistance) — přesně tam, kde instituce pohybují cenou, aby je "vylosovaly" a získaly levnější vstup.'
    },
    {
      q: 'Na kterých trzích ICT funguje nejlépe?',
      opts: [
        'Pouze na forexu',
        'Forex, indexové futures (NQ/ES) a Gold (XAUUSD)',
        'Pouze na kryptoměnách',
        'Výhradně na amerických akciích'
      ],
      correct: 1,
      explain: 'ICT původně vzniklo pro forex, ale exceluje také na indexových futures (NQ, ES, MES) a Goldu. Michael Huddleston sám obchoduje hlavně NQ futures.'
    }
  ],
  'm2': [
    {
      q: 'Co znamená CHoCH (Change of Character)?',
      opts: [
        'Pokračování trendu — cena prolomila předchozí swing high',
        'První signal možné změny trendu — prolomení posledního HL (v bullish trendu)',
        'Typ order bloku na vyšším timeframu',
        'Fibonacci úroveň pro vstup'
      ],
      correct: 1,
      explain: 'CHoCH nastává, když cena v bullish trendu prolomí poslední Higher Low dolů — je to PRVNÍ signál, že trend se může obracet. Potvrzení přichází MSS (Market Structure Shift).'
    },
    {
      q: 'Co je bullish trend podle ICT?',
      opts: [
        'Cena je nad 200 MA',
        'Cena tvoří Higher Highs (HH) a Higher Lows (HL)',
        'RSI je nad 50',
        'Cena je v Premium zóně'
      ],
      correct: 1,
      explain: 'Bullish trend = každý vrchol (swing high) je vyšší než předchozí (HH) a každé dno (swing low) je vyšší než předchozí (HL). Toto je základní definice struktury trhu.'
    },
    {
      q: 'Kde je Premium zóna?',
      opts: [
        'Pod 50% hladinou (Equilibrium)',
        'Nad 50% hladinou (Equilibrium)',
        'Na přesné 50% hladině',
        'Záleží na timeframu'
      ],
      correct: 1,
      explain: 'Premium zóna je NAD 50% hladinou (Equilibrium). Cena je tam "drahá" — ideální pro hledání short pozic. Naopak Discount zóna je pod EQ — ideální pro longy.'
    },
    {
      q: 'Co potvrzuje BOS (Break of Structure)?',
      opts: [
        'Možnou změnu trendu',
        'Pokračování trendu',
        'Vstup do obchodu',
        'Konec impulzivního pohybu'
      ],
      correct: 1,
      explain: 'BOS (Break of Structure) nastává, když cena v bullish trendu prolomí předchozí Swing High — potvrzuje, že trend pokračuje nahoru. V bearish trendu prolomení Swing Low = BOS dolů.'
    }
  ],
  'm3': [
    {
      q: 'Co je Buy-side likvidita (BSL)?',
      opts: [
        'Stop-lossy longových obchodníků pod swing lows',
        'Nahromaděné buy objednávky (stop-lossy shortů) nad swing highs a equal highs',
        'Velkoobjemová nákupní zóna na začátku trendu',
        'Fibonacci retracement úroveň 0.618'
      ],
      correct: 1,
      explain: 'Buy-side likvidita (BSL) se nachází NAD swing highs a equal highs — jsou to stop-lossy retail short obchodníků a pending buy objednávky. Instituce pohybují cenou NAHORU, aby tuto likviditu sesbíraly.'
    },
    {
      q: 'Co se typicky stane po Liquidity Sweep?',
      opts: [
        'Trh pokračuje ve stejném směru silným pohybem',
        'Cena se rychle vrátí zpět — reversal v opačném směru',
        'Trh vstoupí do dlouhé konsolidace',
        'Nic zvláštního — sweep je normální'
      ],
      correct: 1,
      explain: 'Po liquidity sweep se cena typicky obrátí (reversal). Instituce sesbírala stop-lossy (likviditu), vstoupila do pozice a nyní pohybuje trhem ve svůj prospěch — opačný směr než sweep.'
    },
    {
      q: 'Co jsou Equal Lows?',
      opts: [
        'Dvě svíčky se stejnou close hodnotou',
        'Dvě nebo více swing low na stejné ceně — silná sell-side likvidita pod nimi',
        'Fibonacci úroveň 1.0',
        'Typ Order Bloku'
      ],
      correct: 1,
      explain: 'Equal Lows jsou dvě nebo více swing low na stejné nebo velmi blízké cenové úrovni. Retail obchodníci dávají stop-lossy těsně pod tuto úroveň — vytváří to velký cluster sell-side likvidity, který instituce zákonitě vezmou.'
    },
    {
      q: 'Jak identifikuješ potenciální liquidity sweep setup?',
      opts: [
        'Čekáš na breakout a vstoupíš s trendem',
        'Identifikuješ equal highs/lows nebo swing highs/lows, čekáš na přiblížení ceny a sweep + rychlý reversal + CHoCH',
        'Používáš RSI divergenci jako potvrzení',
        'Vstoupíš při dotyku Moving Average'
      ],
      correct: 1,
      explain: 'Postup: 1) Najdi equal highs/lows nebo viditelný swing bod s mnoha dotyky. 2) Čekej na přiblížení ceny. 3) Sweep (probití) + rychlý návrat zpět. 4) CHoCH na LTF = vstup v opačném směru.'
    }
  ],
  'm4': [
    {
      q: 'Jak identifikuješ Bullish Order Block?',
      opts: [
        'První zelená svíčka v uptrendu',
        'Poslední bearish (červená) svíčka před silným impulzivním pohybem nahoru',
        'Největší svíčka za posledních 20 period',
        'Svíčka s nejdelším spodním knotem'
      ],
      correct: 1,
      explain: 'Bullish Order Block = poslední BEARISH (červená) svíčka PŘED impulsivním pohybem NAHORU. OB zóna je od low po high této svíčky — sem se cena vrátí a instituce doplňují pozice.'
    },
    {
      q: 'Co je Breaker Block?',
      opts: [
        'Nový typ Order Bloku s větší silou',
        'Order Block, který byl probita — mění polarity (bullish OB se stává bearish resistencí)',
        'Fibonacci úroveň kombinovaná s OB',
        'OB na denním timeframu'
      ],
      correct: 1,
      explain: 'Breaker Block vzniká, když cena probije Order Block (místo aby ho respektovala). Původní Bullish OB se pak stává Bearish Breaker Block — cena se vrátí k Breakeru, tentokrát jako k rezistenci.'
    },
    {
      q: 'Kdy je Order Block neplatný?',
      opts: [
        'Pokud je na 15min timeframu',
        'Pokud byl již "mitigován" — cena se tam vrátila a OB zóna byla již plně vyplněna',
        'Pokud nemá FVG nad sebou',
        'Pokud vznikl v Asian session'
      ],
      correct: 1,
      explain: 'OB je neplatný (mitigovaný), pokud se cena již vrátila do OB zóny a prošla jí. Každý OB funguje pouze jednou — po mitigation ztrácí platnost.'
    },
    {
      q: 'Co zvyšuje pravděpodobnost platnosti Order Bloku?',
      opts: [
        'Velký objem (volume) na dané svíčce',
        'Přítomnost Fair Value Gap (FVG) těsně nad/pod OB a předchozí liquidity sweep',
        'OB na kulatém čísle (1.2000)',
        'Blízkost Moving Average 200'
      ],
      correct: 1,
      explain: 'Kombinace OB + FVG je jedním z nejsilnějších ICT setů. Přidej-li k tomu předchozí liquidity sweep (instituce sesbíraly stop-lossy) a HTF bias ve stejném směru, máš high-probability trade.'
    }
  ],
  'm5': [
    {
      q: 'Co je Fair Value Gap (FVG)?',
      opts: [
        'Mezera mezi dvěma svíčkami ve svíčkovém grafu',
        'Třísvíčkový vzor kde knot svíčky 1 a knot svíčky 3 se nepřekrývají — cenová nerovnováha',
        'Typ Fibonacci úrovně',
        'Zóna konsolidace na nízkém timeframu'
      ],
      correct: 1,
      explain: 'FVG je 3-svíčkový vzor: svíčka 2 je tak velká (impulz), že High svíčky 1 (bullish FVG) je níže než Low svíčky 3 — vzniká mezera, kde nebyla žádná obchodní aktivita. Trh se tam vrátí, aby tuto nerovnováhu "vyrovnal".'
    },
    {
      q: 'Kde ideálně vstupuješ při retrace do Bullish FVG?',
      opts: [
        'Na horní hranici FVG (High svíčky 3)',
        'Na 50% FVG — střed nerovnováhy',
        'Na dolní hranici FVG (High svíčky 1)',
        'Kdekoliv v FVG zóně'
      ],
      correct: 1,
      explain: 'Ideální vstupní bod je 50% FVG (střed zóny). Tady je tzv. "equilibrium" FVG. Stop-loss jde těsně pod celý FVG (pod High svíčky 1), target = předchozí swing high nebo další liquidity pool.'
    },
    {
      q: 'Co je Inverted FVG (IFVG)?',
      opts: [
        'FVG na kratším timeframu než na dlouhém',
        'FVG, který byl probita — mění polarity (podpora se stává rezistencí)',
        'FVG ve směru bearish trendu',
        'FVG kombinovaný s Order Blokem'
      ],
      correct: 1,
      explain: 'Inverted FVG vzniká, když cena projde SKRZ FVG (místo aby se v něm obrátila). Původní Bullish FVG se stává Bearish IFVG — při retrace zpět slouží jako rezistence.'
    },
    {
      q: 'Jaký je vztah FVG a Order Bloku?',
      opts: [
        'Jsou to totéž, jen různé názvy',
        'FVG a OB se vzájemně vylučují — nemůžou být na stejném místě',
        'Kombinace OB + FVG (Unicorn Model) je jednou z nejsilnějších ICT zón',
        'OB je vždy nad FVG'
      ],
      correct: 2,
      explain: 'Unicorn Model je pojmenování pro situaci, kdy OB a FVG se překrývají. Instituce tam mají nevyplněné objednávky (OB) I cenovou nerovnováhu (FVG) — dvojí důvod pro silnou reakci ceny.'
    }
  ],
  'm6': [
    {
      q: 'Co je cílem Asian session v Power of 3 modelu?',
      opts: [
        'Hlavní pohyb dne — distribuce',
        'Falešný breakout (Judas Swing)',
        'Accumulation — konsolidace, instituce tiše budují pozice',
        'Sweep týdenní likvidity'
      ],
      correct: 2,
      explain: 'Asian session = Accumulation fáze. Trh je v úzkém rangi, instituce tiše budují pozice, volatilita je nízká. Definuje se Asian High (AH) a Asian Low (AL) — klíčové referenční body pro London session.'
    },
    {
      q: 'Kdy je London Killzone? (v letním čase SEČ)',
      opts: [
        '08:00 – 12:00',
        '03:00 – 06:00',
        '14:00 – 17:00',
        '21:00 – 00:00'
      ],
      correct: 1,
      explain: 'London Killzone je 02:00 – 05:00 NY čas, což je v letním SEČ (UTC+2) = 08:00 – 11:00 ... Pozor: v zimním SEČ je to 03:00 – 06:00, v letním 04:00 – 07:00. V závislosti na interpretaci zdroje — klíčový čas je NY 2–5 AM = SEČ letní 8–11 AM.'
    },
    {
      q: 'Co je Silver Bullet strategy?',
      opts: [
        'Strategie pro obchodování během Asian session',
        'FVG setup obchodovaný v specifickém 1hodinovém okně (10:00–11:00 NY čas)',
        'Kombinace OB a FVG = Unicorn model',
        'Strategie pro scalping na 1min grafu'
      ],
      correct: 1,
      explain: 'Silver Bullet je specifické 1hodinové okno (primárně 10:00–11:00 NY čas). Hledáš FVG, který vznikl v tomto okně ve směru denního biasu → vstup při retrace do FVG. Jednoduchost a konzistence jsou výhody tohoto modelu.'
    }
  ],
  'm7': [
    {
      q: 'Jaká je OTE zóna v Fibonacci retracement?',
      opts: [
        '38.2% – 50%',
        '50% – 61.8%',
        '61.8% – 78.6% (62% – 79%)',
        '79% – 100%'
      ],
      correct: 2,
      explain: 'OTE (Optimal Trade Entry) zóna = 61.8% – 78.6% (ICT zaokrouhluje na 62–79%). Sweet spot je 70.5% — matematický střed zóny. Zde instituce doplňují pozice s nejmenší expozicí a nejlepším R:R.'
    },
    {
      q: 'Kde se umísťuje Stop Loss při OTE vstupu?',
      opts: [
        'Na 50% Fibonacci úrovni',
        'Na 61.8% Fibonacci úrovni',
        'Těsně za swing low/high — úroveň 1.0 Fibonacci',
        '20 pipů pod vstupem'
      ],
      correct: 2,
      explain: 'SL jde TĚSNĚ za počáteční swing low (bullish setup) nebo swing high (bearish setup) = Fibonacci úroveň 1.0. Tím je SL malý, protože vstupuješ hluboko v retracement — výsledkem je velké R:R.'
    },
    {
      q: 'Co je sweet spot OTE?',
      opts: [
        '50% Fibonacci',
        '61.8% Fibonacci',
        '70.5% Fibonacci — střed OTE zóny',
        '78.6% Fibonacci'
      ],
      correct: 2,
      explain: 'Sweet spot = 70.5% je přesný matematický střed mezi 61.8% a 79%. ICT ho označuje jako nejpravděpodobnější bod reversal v rámci OTE zóny. Mnozí ICT tradeři nastavují limit order přesně na 70.5%.'
    },
    {
      q: 'Jaký je minimální R:R při OTE vstupu?',
      opts: [
        '1:1',
        '1:2',
        '1:3',
        'R:R nezáleží, hlavní je win rate'
      ],
      correct: 2,
      explain: 'ICT doporučuje minimální R:R 1:3. Při OTE vstupu je SL malý (jsi blízko swing low) a target je daleko (swing high a výše), takže 1:5 nebo i 1:10 je běžné. R:R je klíčové — při 1:3 stačí 25% win rate pro profitabilitu.'
    }
  ],
  'm8': [
    {
      q: 'Co je Judas Swing v Power of 3?',
      opts: [
        'Silný pohyb ve směru trendu při NY open',
        'Falešný pohyb v OPAČNÉM směru než je denní záměr institucí — past pro retail tradery',
        'Typ Order Bloku na začátku dne',
        'Silver Bullet setup během London session'
      ],
      correct: 1,
      explain: 'Judas Swing = záměrně falešný pohyb institucí. Pokud je denní bias bullish, Judas Swing jde DOLŮ (pod Asian Low, triggernuje SL long obchodníků). Poté se trh otočí a jde prudce NAHORU — pravý denní směr.'
    },
    {
      q: 'Která fáze AMD odpovídá London session?',
      opts: [
        'Accumulation',
        'Manipulation',
        'Distribution',
        'Žádná — London je mimo AMD'
      ],
      correct: 1,
      explain: 'London session = Manipulation fáze. London dělá falešný pohyb (Judas Swing) — probíhá sweep Asian High nebo Low a pak reversal. Retail obchodníci vstoupí do špatné strany a London jim vezme SL.'
    },
    {
      q: 'Co je denní bias?',
      opts: [
        'Obchodování výhradně jednoho instrumentu celý den',
        'Předpoklad směru trhu na daný den — opřený o HTF strukturu, likviditu a referenční body',
        'Typ Fibonacci úrovně platný pro daný den',
        'Indikátor pro určení silného trendu'
      ],
      correct: 1,
      explain: 'Denní bias = tvůj předpoklad, kam trh půjde daný den (bullish nebo bearish). Vychází z: HTF struktury (denní/4H trend), polohy ceny vůči PDH/PDL, NY Midnight Open, a kde je likvidita. Bias určuje, jaký typ setups hledáš.'
    },
    {
      q: 'Kdy vstupuješ do obchodu v Power of 3 modelu?',
      opts: [
        'Na začátku Asian session při otevření',
        'Při Judas Swing — vstoupíš ve směru falešného pohybu',
        'Po CHoCH, který ukončuje Judas Swing (Manipulation) → vstup ve směru Distribution',
        'Kdykoli v průběhu Distribution fáze'
      ],
      correct: 2,
      explain: 'Správný vstup: ČEKÁŠ na Judas Swing (nenastupuješ do něj!). Po Judas Swing hledáš CHoCH na LTF (5min/1min) → ten signalizuje konec Manipulation a začátek Distribution. Vstupuješ po CHoCH ve směru Distribution.'
    }
  ],
  'm9': [
    {
      q: 'Jaký je Silver Bullet model krok po kroku?',
      opts: [
        'HTF bias → Asian range → London sweep → OTE vstup',
        'Čekej na Silver Bullet okno → identifikuj FVG v okně ve směru biasu → vstup při retrace na 50% FVG',
        'Identifikuj OB → čekej na pullback → vstup na 70.5% Fib',
        'Hledej CHoCH → nakresli OTE Fib → vstup při 62% retrace'
      ],
      correct: 1,
      explain: 'Silver Bullet: 1) Čekej na okno (03–04 / 10–11 / 14–15 NY čas). 2) V okně identifikuj FVG ve směru HTF biasu. 3) Vstup při retrace na 50% FVG. 4) SL pod FVG, TP = swing high/low nebo liquidity pool. Jednoduchý a konzistentní model.'
    },
    {
      q: 'Co je Unicorn Model?',
      opts: [
        'Model pro obchodování kryptoměn',
        'Kombinace OB (Order Block) a FVG na stejném místě — nejsilnější ICT setup',
        'Strategie pro longy i shorty zároveň (hedging)',
        'Model pro obchodování na týdenním timeframu'
      ],
      correct: 1,
      explain: 'Unicorn Model = Order Block + Fair Value Gap se překrývají. Instituce tam mají nevyplněné objednávky (OB) i cenovou nerovnováhu (FVG) — dvojí magnetická přitažlivost. ICT to pojmenoval "Unicorn" protože takový setup je vzácný a velmi silný.'
    },
    {
      q: 'Co musí být splněno PŘED každým vstupem (pre-trade checklist)?',
      opts: [
        'Stačí najít Order Block na 15min grafu',
        'HTF bias + Killzone + Sweep likvidity + CHoCH + vstupní zóna (OB/FVG/OTE) + min. 1:3 R:R',
        'RSI divergence + MACD crossover + svíčkový vzor',
        'Dostatečný volume + trend v souladu s 200 MA'
      ],
      correct: 1,
      explain: 'ICT pre-trade checklist: 1) Jasný HTF bias 2) Jsem v Killzone 3) Proběhl Judas Swing/sweep 4) Vidím CHoCH 5) Vstupní zóna ve směru biasu 6) R:R min. 1:3 7) Definovaný SL a TP 8) Max. 1-2% risk. Všechny body musí být zelené!'
    }
  ],
  'm10': [
    {
      q: 'Kolik % kapitálu maximálně riskuješ na jeden obchod?',
      opts: ['5–10%', '3–5%', '1–2%', 'Záleží na setup quality'],
      correct: 2,
      explain: 'Zlaté pravidlo: max. 1–2% kapitálu na obchod. Při 2% musíš prohrát 50 obchodů za sebou, abys přišel o 64% účtu (složené). Při 1% musíš prohrát 100 za sebou na -63%. Tato pravidla chrání účet i při šňůře ztrát.'
    },
    {
      q: 'Jaký minimální R:R ratio doporučuje ICT?',
      opts: ['1:1', '1:2', '1:3', '1:5'],
      correct: 2,
      explain: 'ICT doporučuje minimálně 1:3. Při 1:3 R:R stačí win rate pouze 25% pro break-even. ICT filozofie: win rate je sekundární, R:R je primární. S 35% win rate a 1:3 R:R jsi výrazně profitabilní.'
    },
    {
      q: 'Co dělat po 2 ztrátách za sebou v jeden den?',
      opts: [
        'Zvýšit velikost pozice (revenge trading) pro rychlé pokrytí ztrát',
        'Přejít na kratší timeframe pro více příležitostí',
        'Zastavit obchodování na daný den a přijít znovu zítra',
        'Počkat na Silver Bullet okno a vstoupit znovu'
      ],
      correct: 2,
      explain: 'Po 2 ztrátách za sebou STOP. Přijít znovu zítra s čistou hlavou. Revenge trading (zvyšování pozic po ztrátách) je nejrychlejší cesta k vyfukování účtu. Disciplína je v ICT stejně důležitá jako technická analýza.'
    },
    {
      q: 'Proč je Trade Journal důležitý?',
      opts: [
        'Pro reportování výsledků brokeru',
        'Pro identifikaci vzorů, chyb a zlepšování edge — bez zápisníku se neučíš',
        'Pouze pro daňové účely',
        'Je důležitý jen pro začátečníky'
      ],
      correct: 1,
      explain: 'Trade Journal je základní nástroj profesionálního tradera. Bez zápisníku opakuješ stejné chyby, protože je nevidíš. S journalem identifikuješ: v jakých hodinách prohráváš, jaké setupy fungují, jaké emoce vedou ke špatným rozhodnutím.'
    }
  ]
};

// ─── QUIZ ENGINE ─────────────────────────────────────────────────────────────

const quizState = {};

function initQuiz(moduleId) {
  const questions = QUIZZES[moduleId];
  if (!questions) return;

  quizState[moduleId] = { current: 0, score: 0, answered: [] };
  renderQuestion(moduleId);
}

function renderQuestion(moduleId) {
  const state = quizState[moduleId];
  const questions = QUIZZES[moduleId];
  const q = questions[state.current];
  const container = document.getElementById('quiz-' + moduleId + '-body');
  const counter = document.getElementById('qcount-' + moduleId);

  if (counter) counter.textContent = `Otázka ${state.current + 1} / ${questions.length}`;

  if (!container || !q) return;

  container.innerHTML = `
    <div class="quiz-question">${q.q}</div>
    <div class="quiz-options">
      ${q.opts.map((opt, i) => `
        <div class="quiz-option" data-idx="${i}" onclick="answerQuiz('${moduleId}', ${i})">
          <span style="color:var(--text3); margin-right:8px;">${['A','B','C','D'][i]}.</span> ${opt}
        </div>
      `).join('')}
    </div>
    <div class="quiz-feedback" id="qfeedback-${moduleId}"></div>
    <div class="quiz-nav">
      <span></span>
      <button class="btn btn-secondary" id="qnext-${moduleId}" style="display:none" onclick="nextQuestion('${moduleId}')">
        ${state.current + 1 < questions.length ? 'Další otázka →' : 'Výsledky'}
      </button>
    </div>
  `;
}

function answerQuiz(moduleId, idx) {
  const state = quizState[moduleId];
  const q = QUIZZES[moduleId][state.current];
  const opts = document.querySelectorAll(`#quiz-${moduleId}-body .quiz-option`);
  const feedback = document.getElementById(`qfeedback-${moduleId}`);
  const nextBtn = document.getElementById(`qnext-${moduleId}`);

  opts.forEach(o => o.classList.add('disabled'));

  const isCorrect = idx === q.correct;
  opts[q.correct].classList.add('correct');
  if (!isCorrect) opts[idx].classList.add('wrong');

  if (isCorrect) state.score++;
  state.answered.push(isCorrect);

  feedback.className = 'quiz-feedback show ' + (isCorrect ? 'correct' : 'wrong');
  feedback.innerHTML = (isCorrect ? '✅ Správně! ' : '❌ Špatně. ') + q.explain;

  nextBtn.style.display = 'inline-block';
}

function nextQuestion(moduleId) {
  const state = quizState[moduleId];
  const questions = QUIZZES[moduleId];
  state.current++;

  if (state.current >= questions.length) {
    showQuizResults(moduleId);
  } else {
    renderQuestion(moduleId);
  }
}

function showQuizResults(moduleId) {
  const state = quizState[moduleId];
  const total = QUIZZES[moduleId].length;
  const pct = Math.round(state.score / total * 100);
  const container = document.getElementById('quiz-' + moduleId + '-body');
  const counter = document.getElementById('qcount-' + moduleId);
  if (counter) counter.textContent = 'Výsledky';

  const color = pct >= 75 ? 'var(--green)' : pct >= 50 ? 'var(--accent)' : 'var(--red)';
  const msg = pct >= 75 ? '🎉 Výborně! Jsi připraven/a na další modul.' :
              pct >= 50 ? '👍 Dobrý výsledek. Zopakuj si látku a zkus znovu.' :
              '📚 Projdi modul znovu — základy jsou klíčové.';

  container.innerHTML = `
    <div style="text-align:center; padding: 20px 0;">
      <div style="font-size:48px; font-weight:800; color:${color}">${pct}%</div>
      <div style="font-size:16px; color:var(--text2); margin:8px 0">${state.score} z ${total} správně</div>
      <div style="font-size:14px; color:var(--text2); margin-bottom:20px">${msg}</div>
      <button class="btn btn-secondary" onclick="initQuiz('${moduleId}')">🔄 Zkusit znovu</button>
    </div>
  `;
}

// ─── GLOSSARY ────────────────────────────────────────────────────────────────

const GLOSSARY = [
  { term: 'Accumulation', def: 'První fáze Power of 3 (AMD). Konsolidace ceny v Asian session, kdy instituce tiše budují pozice v úzkém rangi.' },
  { term: 'AMD', def: 'Accumulation, Manipulation, Distribution — denní vzor pohybu trhu (Power of 3). Tři fáze, které trh prochází každý obchodní den.' },
  { term: 'Asian High / Low (AH/AL)', def: 'Nejvyšší a nejnižší cena během Asian session. Klíčové referenční body — London zpravidla udělá sweep jednoho z nich (Judas Swing).' },
  { term: 'BOS (Break of Structure)', def: 'Prolomení předchozího swing high (bullish) nebo swing low (bearish). Potvrzuje pokračování trendu.' },
  { term: 'Bearish Order Block', def: 'Poslední bullish (zelená) svíčka před silným impulzivním pohybem dolů. Cena se sem vrátí jako k rezistenci.' },
  { term: 'Breaker Block', def: 'Order Block, který byl cena prorazila (nerespektovala). Mění polaritu — původní podpora se stává rezistencí a naopak.' },
  { term: 'BSL (Buy-Side Liquidity)', def: 'Likvidita NAD swing highs a equal highs. Stop-lossy short obchodníků. Instituce pohybují cenou nahoru, aby tuto likviditu sesbíraly.' },
  { term: 'Bullish Order Block', def: 'Poslední bearish (červená) svíčka před silným impulzivním pohybem nahoru. Cena se sem vrátí jako k podpoře.' },
  { term: 'CHoCH (Change of Character)', def: 'Změna charakteru trhu. V bullish trendu = prolomení posledního Higher Low dolů. První signál možné změny trendu.' },
  { term: 'Daily Bias', def: 'Denní předpoklad směru trhu (bullish nebo bearish). Odvozuje se z HTF struktury, PDH/PDL, NY Midnight Open a polohy likvidity.' },
  { term: 'Discount zóna', def: 'Část dealing range POD 50% hladinou (Equilibrium). Ideální zóna pro hledání long pozic — cena je "levná".' },
  { term: 'Displacement', def: 'Silný impulzivní pohyb ceny, typicky doprovázen FVG. Signalizuje vstup institucionálního kapitálu.' },
  { term: 'Distribution', def: 'Třetí fáze AMD. Hlavní pohyb dne — cena jde ve skutečném směru biasu po Manipulation (Judas Swing).' },
  { term: 'EQ (Equilibrium)', def: 'Přesná 50% hladina mezi swing high a swing low. Hranice Premium a Discount zón.' },
  { term: 'ERL (External Range Liquidity)', def: 'Likvidita mimo aktuální range — swing highs a lows přes více period. Silné magnetické úrovně.' },
  { term: 'Equal Highs (EQH)', def: 'Dva nebo více swing high na stejné ceně. Velký cluster buy-side likvidity NAD nimi. Instituce to vezmou.' },
  { term: 'Equal Lows (EQL)', def: 'Dva nebo více swing low na stejné ceně. Velký cluster sell-side likvidity POD nimi. Instituce to vezmou.' },
  { term: 'FVG (Fair Value Gap)', def: '3-svíčkový vzor nerovnováhy. High svíčky 1 nepřekrývá Low svíčky 3 (bullish). Trh se vrátí tuto mezeru "vyplnit".' },
  { term: 'HH (Higher High)', def: 'Vyšší maximum než předchozí — součást bullish struktury trhu.' },
  { term: 'HL (Higher Low)', def: 'Vyšší minimum než předchozí — součást bullish struktury trhu. CHoCH = prolomení HL dolů.' },
  { term: 'HTF (Higher Time Frame)', def: 'Vyšší časový rámec (denní, 4H, 1H). Definuje celkový bias a kontext pro LTF vstup.' },
  { term: 'IFVG (Inverted FVG)', def: 'Fair Value Gap, který byl cena prorazila. Mění polaritu — bullish FVG se stává bearish IFVG (podpora → rezistence).' },
  { term: 'IPDA', def: 'Interbank Price Delivery Algorithm. Podle ICT algoritmus řídící pohyb ceny na mezibankovním trhu — pohybuje cenou k likviditě a vyrovnává nerovnováhy.' },
  { term: 'IRL (Internal Range Liquidity)', def: 'Likvidita uvnitř aktuálního rangi — FVG, Order Blocks. Cena nejdřív vyrovná interní nerovnováhy před dosažením ERL.' },
  { term: 'Judas Swing', def: 'Falešný pohyb v opačném směru než je denní záměr — záměrná past na retail obchodníky. Fáze Manipulation v AMD modelu.' },
  { term: 'Killzone', def: 'Časové okno s vysokou institucionální aktivitou. London (02–05 NY), New York (07–10 NY). ICT modely fungují POUZE v killzones.' },
  { term: 'LH (Lower High)', def: 'Nižší maximum než předchozí — součást bearish struktury trhu.' },
  { term: 'LL (Lower Low)', def: 'Nižší minimum než předchozí — součást bearish struktury trhu.' },
  { term: 'LTF (Lower Time Frame)', def: 'Nižší časový rámec (15min, 5min, 1min). Slouží k přesnému načasování vstupu v rámci HTF biasu.' },
  { term: 'Liquidity Sweep', def: 'Pohyb ceny, který probíjí úroveň likvidity (equal highs/lows, swing bod) a triggernuje stop-lossy, pak se rychle obrátí.' },
  { term: 'Liquidity Void', def: 'Velká cenová mezera (velký FVG přes mnoho svíček). Silný "magnet" — cena se tam téměř vždy vrátí.' },
  { term: 'Macro', def: '20minutové okno s obzvláště vysokou institucioální aktivitou uvnitř killzones. Např. NY Open Macro: 08:50–09:10 NY čas.' },
  { term: 'Manipulation', def: 'Druhá fáze AMD. Falešný pohyb (Judas Swing) v opačném směru pro sesbírání likvidity. Probíhá v London session.' },
  { term: 'Mitigation Block', def: 'Zóna kde institutionálním objednávkám zbyla "nevyplněná část". Cena se vrátí pro mitigaci těchto zbývajících objednávek.' },
  { term: 'MSS (Market Structure Shift)', def: 'Potvrzení změny trendu — CHoCH + nový HH nebo LL v novém směru. Silnější signál než samotný CHoCH.' },
  { term: 'NY Midnight Open', def: 'Půlnoc newyorského čase (06:00 SEČ). Klíčový referenční bod ICT algoritmu. Denní bias závisí na poloze ceny vůči tomuto bodu.' },
  { term: 'OB (Order Block)', def: 'Institucionální zóna vstupu. Bullish OB = poslední bearish svíčka před impulzem nahoru. Bearish OB = poslední bullish svíčka před impulzem dolů.' },
  { term: 'OTE (Optimal Trade Entry)', def: 'Fibonacci retracement zóna 62–79%. Ideální vstupní bod po impulzivním pohybu. Sweet spot = 70.5%.' },
  { term: 'PDH/PDL', def: 'Previous Day High / Previous Day Low. Včerejší maximum a minimum. Klíčové referenční body likvidity pro denní bias.' },
  { term: 'PD Array', def: 'Price Delivery Array — soubor ICT konceptů (OB, FVG, Breaker, Mitigation Block, IFVG), které popisují kde cena reaguje.' },
  { term: 'PO3 (Power of 3)', def: 'Power of Three = AMD model. Denní struktura pohybu: Accumulation → Manipulation → Distribution.' },
  { term: 'Premium zóna', def: 'Část dealing range NAD 50% hladinou (Equilibrium). Ideální zóna pro hledání short pozic — cena je "drahá".' },
  { term: 'R:R (Risk:Reward)', def: 'Poměr rizika k potenciálnímu zisku. ICT minimum = 1:3. Při 1:3 stačí 25% win rate pro profitabilitu.' },
  { term: 'SMC (Smart Money Concepts)', def: 'Obecný název pro metodologii obchodování v souladu s institucemi. ICT je hlavní zakladatel SMC metodologie.' },
  { term: 'SMT (Smart Money Trap)', def: 'Divergence mezi korelovanými páry (např. NQ vs ES nebo EUR/USD vs GBP/USD). Jeden dělá nové high, druhý ne → signál možné obrátky.' },
  { term: 'SSL (Sell-Side Liquidity)', def: 'Likvidita POD swing lows a equal lows. Stop-lossy long obchodníků. Instituce pohybují cenou dolů, aby tuto likviditu sesbíraly.' },
  { term: 'Swing High', def: 'Lokální maximum — svíčka s vyšším high než sousední svíčky. Základ pro analýzu struktury trhu.' },
  { term: 'Swing Low', def: 'Lokální minimum — svíčka s nižším low než sousední svíčky. Základ pro analýzu struktury trhu.' },
  { term: 'Silver Bullet', def: 'ICT vstupní model. FVG setup obchodovaný v 1h okně (10–11 NY čas, nebo 03–04, 14–15). Jednoduchý a konzistentní model.' },
  { term: 'Unicorn Model', def: 'ICT setup kde Order Block a Fair Value Gap se překrývají. Nejsilnější ICT zóna — dvojí institucionální magnetismus.' },
];

function renderGlossary(filter = '') {
  const container = document.getElementById('glossary-list');
  if (!container) return;
  const term = filter.toLowerCase();
  const filtered = GLOSSARY.filter(g =>
    g.term.toLowerCase().includes(term) || g.def.toLowerCase().includes(term)
  ).sort((a, b) => a.term.localeCompare(b.term));

  container.innerHTML = filtered.length ? filtered.map(g => `
    <div class="glossary-item">
      <div class="glossary-term">${g.term}</div>
      <div class="glossary-def">${g.def}</div>
    </div>
  `).join('') : '<p style="color:var(--text3); text-align:center; padding:20px">Žádné výsledky.</p>';
}

function filterGlossary(val) { renderGlossary(val); }

// ─── CHARTS ──────────────────────────────────────────────────────────────────

let chartsRendered = {};

// Pomocná funkce: nastav canvas na správnou výšku a vyrenderuj
function renderChart(canvasId, heightPx, scene) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  canvas.style.height = heightPx + 'px';
  const { candles, anns } = scene;
  new ICTChart(canvasId).load(candles, anns).render();
}

function renderMarketStructureChart() {
  if (chartsRendered['ms']) return;
  chartsRendered['ms'] = true;
  renderChart('chart-ms', 340, makeMarketStructureScene());
}

function renderLiquidityChart() {
  if (chartsRendered['liq']) return;
  chartsRendered['liq'] = true;
  renderChart('chart-liq', 320, makeLiquidityScene());
}

function renderOrderBlockChart() {
  if (chartsRendered['ob']) return;
  chartsRendered['ob'] = true;
  renderChart('chart-ob', 340, makeOrderBlockScene());
}

function renderFVGChart() {
  if (chartsRendered['fvg']) return;
  chartsRendered['fvg'] = true;
  renderChart('chart-fvg', 340, makeFVGScene());
}

function renderOTEChart() {
  if (chartsRendered['ote']) return;
  chartsRendered['ote'] = true;
  renderChart('chart-ote', 340, makeOTEScene());
}

function renderAMDChart() {
  if (chartsRendered['amd']) return;
  chartsRendered['amd'] = true;
  renderChart('chart-amd', 340, makeAMDScene());
}

function renderSessionsChart() {
  if (chartsRendered['sess']) return;
  chartsRendered['sess'] = true;

  const canvas = document.getElementById('chart-sessions');
  if (!canvas) return;
  canvas.style.height = '190px';

  const dpr  = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width) return;
  canvas.width  = rect.width  * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height;

  ctx.fillStyle = '#0d0f14';
  ctx.fillRect(0, 0, W, H);

  // Časová osa: zobrazujeme SEČ letní (UTC+2)
  // NY time + 6h = SEČ letní
  // Asian: NY 18:00–04:00 = SEČ 00:00–10:00
  // London KZ: NY 02:00–05:00 = SEČ 08:00–11:00
  // NY KZ: NY 07:00–10:00 = SEČ 13:00–16:00
  // Silver Bullet: NY 10:00–11:00 = SEČ 16:00–17:00

  const hours = 24;
  const pph   = W / hours;
  const barY  = H * 0.32, barH = H * 0.3;

  // Základní timeline
  ctx.fillStyle = '#1c2030';
  ctx.fillRect(0, barY, W, barH);

  // Session bloky (SEČ letní)
  const blocks = [
    { s: 0,  e: 6,  fill: 'rgba(155,89,182,0.25)', stroke: null },         // Asian část 1
    { s: 8,  e: 11, fill: 'rgba(74,158,255,0.35)',  stroke: '#4a9eff' },    // London KZ
    { s: 13, e: 16, fill: 'rgba(240,185,11,0.35)',  stroke: '#f0b90b' },    // NY KZ
    { s: 16, e: 17, fill: 'rgba(240,185,11,0.55)',  stroke: null },         // Silver Bullet
    { s: 20, e: 24, fill: 'rgba(155,89,182,0.25)', stroke: null },          // Asian část 2
  ];

  blocks.forEach(b => {
    ctx.fillStyle = b.fill;
    ctx.fillRect(b.s * pph, barY, (b.e - b.s) * pph, barH);
    if (b.stroke) {
      ctx.strokeStyle = b.stroke;
      ctx.lineWidth = 1;
      ctx.setLineDash([]);
      ctx.strokeRect(b.s * pph, barY, (b.e - b.s) * pph, barH);
    }
  });

  // Hodiny
  ctx.strokeStyle = 'rgba(42,47,63,0.9)';
  ctx.lineWidth = 0.5;
  ctx.setLineDash([]);
  for (let h = 0; h <= 24; h++) {
    const x = h * pph;
    ctx.beginPath(); ctx.moveTo(x, barY); ctx.lineTo(x, barY + barH); ctx.stroke();
    if (h % 2 === 0) {
      ctx.fillStyle = '#555f72';
      ctx.font = '10px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(h + ':00', x, barY + barH + 14);
    }
  }

  ctx.strokeStyle = '#2a2f3f'; ctx.lineWidth = 1; ctx.setLineDash([]);
  ctx.strokeRect(0, barY, W, barH);

  // Labely uvnitř bloků
  const lbls = [
    { x: 3,    color: '#9b59b6', text: '🌙 Asian' },
    { x: 9.5,  color: '#4a9eff', text: '🇬🇧 London KZ' },
    { x: 14.5, color: '#f0b90b', text: '🗽 NY KZ' },
    { x: 16.5, color: '#f0b90b', text: '⚡SB' },
    { x: 22,   color: '#9b59b6', text: '🌙 Asian' },
  ];
  lbls.forEach(l => {
    ctx.fillStyle = l.color;
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(l.text, l.x * pph, barY + barH / 2 + 4);
  });

  // Popisky nad
  ctx.font = 'bold 11px sans-serif';
  ctx.fillStyle = '#8892a4';
  ctx.textAlign = 'left';
  ctx.fillText('Časy v SEČ letní (UTC+2)', 4, barY - 8);
}

// ─── INIT ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Init quizzes
  Object.keys(QUIZZES).forEach(id => initQuiz(id));

  // Render glossary
  renderGlossary();

  // Restore progress
  updateProgress();
  markNavCompleted();
});
