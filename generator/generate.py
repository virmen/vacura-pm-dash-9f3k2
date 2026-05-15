#!/usr/bin/env python3
"""
Generator für PM-Dashboard-HTMLs v2 (für PM_Gehaltsmodell_v18.xlsx).

Liest v18 Excel + rechnet KPIs selbst aus (keine Excel-Cache-Voraussetzung).
Generiert eine HTML pro PM mit dem 9-Block Roten Faden.

Usage: python3 generate.py
"""
import openpyxl, os, sys, html, json
from datetime import datetime, date

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL = os.environ.get('EXCEL_PATH') or os.path.expanduser('~/Code/Claude/Github/pm-dashboards/PM_Gehaltsmodell_v18.xlsx')
OUT_DIR = os.environ.get('OUT_DIR') or os.path.expanduser('~/Code/Claude/Github/pm-dashboards/v2')

# PKV/SZ-Aufschlag auf GKV-Tarif. Wirkt sich auf IST aus (termin_umsatz) und auf
# den Hebel-Faktor (1 %-Pkt PKV ≈ (PKV_FAKTOR-1)*100 % Umsatz). Schwellen in STUFEN
# sind auf 1,7 kalibriert — bei Änderung müssen die Schwellen rekalibriert oder
# pro Bundle um den Mix-Faktor adjustiert werden.
PKV_FAKTOR = 1.7

# Stufen
STUFEN = [
    {'n': 1, 'name': 'Basis',         'zufr': 5.0, 'zulage': 0.00, 'eur60': 61.17},
    {'n': 2, 'name': 'Gut',           'zufr': 6.0, 'zulage': 0.11, 'eur60': 66.54},
    {'n': 3, 'name': 'Stark',         'zufr': 7.0, 'zulage': 0.22, 'eur60': 72.64},
    {'n': 4, 'name': 'Sehr stark',    'zufr': 8.0, 'zulage': 0.33, 'eur60': 77.28},
    {'n': 5, 'name': 'Exzellent',     'zufr': 8.5, 'zulage': 0.44, 'eur60': 84.11},
    {'n': 6, 'name': 'Herausragend',  'zufr': 8.5, 'zulage': 0.55, 'eur60': 89.48},
]

# KPI-Level für Wege-Block
KPI_LEVELS = {
    'Auslastung': {
        'low':   {'text': 'niedrig',   'range': 'bis 84 %'},
        'mid':   {'text': 'mittel',    'range': '85–92 %'},
        'high':  {'text': 'hoch',      'range': '93–95 %'},
        'vhigh': {'text': 'sehr hoch', 'range': '96 %+'},
    },
    'PKV-Quote': {
        'low':   {'text': 'gering',    'range': 'bis 10 %'},
        'mid':   {'text': 'mittel',    'range': '11–20 %'},
        'high':  {'text': 'hoch',      'range': '21–30 %'},
        'vhigh': {'text': 'sehr hoch', 'range': 'über 30 %'},
    },
    'Krankheit': {
        'low':   {'text': 'wenig',     'range': 'bis 15 Tg./a'},
        'mid':   {'text': 'normal',    'range': '16–20 Tg./a'},
        'high':  {'text': 'höher',     'range': '21–25 Tg./a'},
        'vhigh': {'text': 'sehr viel', 'range': 'über 25 Tg./a'},
    },
}

STUFEN_WEGE = {
    1: {'type': 'text', 'text': 'Standort im Aufbau oder nach Veränderungen — Grundlagen werden gelegt.'},
    2: {'type': 'text', 'text': 'Solide Auslastung, Team läuft stabil.'},
    3: {'type': 'wege', 'wege': [
        [('Auslastung','vhigh'), ('PKV-Quote','low'), ('Krankheit','high')],
        [('Auslastung','high'),  ('PKV-Quote','low'), ('Krankheit','high')],
        [('Auslastung','mid'),   ('PKV-Quote','low'), ('Krankheit','low')],
    ]},
    4: {'type': 'wege', 'wege': [
        [('Auslastung','vhigh'), ('PKV-Quote','mid'),  ('Krankheit','high')],
        [('Auslastung','high'),  ('PKV-Quote','low'),  ('Krankheit','low')],
        [('Auslastung','mid'),   ('PKV-Quote','high'), ('Krankheit','low')],
    ]},
    5: {'type': 'wege', 'wege': [
        [('Auslastung','vhigh'), ('PKV-Quote','high'),  ('Krankheit','high')],
        [('Auslastung','mid'),   ('PKV-Quote','vhigh'), ('Krankheit','low')],
    ]},
    6: {'type': 'text', 'text': 'Konstant Top-Ergebnisse über mehrere Quartale auf Stufe-5-Niveau.'},
}

def render_wege_block(next_stufe_num):
    """Rendert Kombinations-Wege für die Zielstufe."""
    if next_stufe_num not in STUFEN_WEGE:
        return ''
    cfg = STUFEN_WEGE[next_stufe_num]
    if cfg['type'] == 'text':
        return f'<div class="weg-text">{cfg["text"]}</div>'
    weg_labels = ['Weg A','Weg B','Weg C','Weg D']
    wege_html = ''
    for i, kombi in enumerate(cfg['wege']):
        vars_html = ''
        for kpi_name, level in kombi:
            level_info = KPI_LEVELS[kpi_name][level]
            vars_html += (
                '<div class="weg-var">'
                f'<div class="weg-var-label">{kpi_name}</div>'
                '<div class="weg-chip-track">'
                f'<div class="weg-chip weg-chip-{level}">'
                f'<span class="weg-chip-text">{level_info["text"]}</span>'
                f'<span class="weg-chip-range">{level_info["range"]}</span>'
                '</div>'
                '</div>'
                '</div>'
            )
        wege_html += (
            '<div class="weg-card">'
            f'<div class="weg-head"><span class="weg-head-label">{weg_labels[i]}</span><span class="weg-head-tag">Kombination</span></div>'
            f'<div class="weg-vars">{vars_html}</div>'
            '</div>'
        )
    return f'<div class="wege-grid">{wege_html}</div>'


PMS = [
    {'name':'Laura',   'row':5, 'color':'#4CAF50', 'bundle_pms':['Laura','Max'],
     'bundle_standorte':'Spandau, Mitte'},
    {'name':'Marleen', 'row':6, 'color':'#2196F3', 'bundle_pms':['Marleen','Luise'],
     'bundle_standorte':'Friedrichshain, Charlottenburg, Prenzlauer Berg'},
    {'name':'Luise',   'row':7, 'color':'#9C27B0', 'bundle_pms':['Marleen','Luise'],
     'bundle_standorte':'Friedrichshain, Charlottenburg, Prenzlauer Berg'},
    {'name':'Max',     'row':8, 'color':'#FF9800', 'bundle_pms':['Laura','Max'],
     'bundle_standorte':'Spandau, Mitte'},
]

def th_kumuliert(n_th):
    """TH-Zulage kumuliert für n TH-Äquivalente."""
    cum = 0
    for i in range(1, n_th + 1):
        if i <= 4: cum += 250
        elif i <= 9: cum += 400
        else: cum += 700
    return cum

def get_cell_val(ws, r, c):
    v = ws.cell(row=r, column=c).value
    if isinstance(v, str) and v.startswith('='):
        # Formel — versuche zu resolven
        return None
    return v

def resolve_formula(ws, r, c, max_depth=3):
    """Löse einfache =X5-Referenzen auf."""
    v = ws.cell(row=r, column=c).value
    if not isinstance(v, str) or not v.startswith('='):
        return v
    # Einfache Referenz wie =G6
    if max_depth == 0: return None
    import re
    m = re.match(r'^=([A-Z]+)(\d+)$', v.strip())
    if m:
        from openpyxl.utils import column_index_from_string
        col = column_index_from_string(m.group(1))
        row = int(m.group(2))
        return resolve_formula(ws, row, col, max_depth-1)
    return None

def compute_pm(ws_daten, pm):
    r = pm['row']
    # Stammdaten (static)
    wochenstd = ws_daten.cell(row=r, column=3).value
    pm_std_bundle = ws_daten.cell(row=r, column=4).value
    start_stufe = ws_daten.cell(row=r, column=5).value or 1
    mindestgehalt = ws_daten.cell(row=r, column=6).value
    startdatum = ws_daten.cell(row=r, column=1).value
    
    # Q1 2026 Daten (mit Formel-Auflösung für Luise/Max)
    vstd_bundle = resolve_formula(ws_daten, r, 7)
    vstd_ber    = resolve_formula(ws_daten, r, 8)
    abw_ber     = resolve_formula(ws_daten, r, 9)
    ist         = resolve_formula(ws_daten, r, 10)
    ruecken     = resolve_formula(ws_daten, r, 11) or 0
    komm        = resolve_formula(ws_daten, r, 12) or 0
    enps        = resolve_formula(ws_daten, r, 13) or 0
    
    if not all([vstd_bundle, vstd_ber, abw_ber, ist]):
        return None
    
    # Ableitung
    verfueg = vstd_ber - abw_ber
    eur60 = ist / verfueg
    zufr = ruecken*0.2 + komm*0.2 + enps*0.6

    # Rechn. Stufe
    rechn = 0
    for s in reversed(STUFEN):
        if eur60 >= s['eur60'] and zufr >= s['zufr']:
            rechn = s['n']; break
    
    # Tats. Stufe ±1 Deckel
    if rechn == 0:
        tats = max(start_stufe - 1, 1)
    elif rechn > start_stufe + 1:
        tats = start_stufe + 1
    elif rechn < start_stufe - 1:
        tats = max(start_stufe - 1, 1)
    else:
        tats = rechn
    
    # TH
    th_bundle = round(vstd_bundle / 13 / 30)
    th_pm = round(th_bundle * wochenstd / pm_std_bundle)
    
    # Gehalt
    bundle_zulage = th_kumuliert(th_pm)
    basis = 40000 + bundle_zulage
    stufe_zulage_pct = STUFEN[tats - 1]['zulage']
    gehalt_formel = round(basis * (1 + stufe_zulage_pct) * (wochenstd / 40))
    min_gehalt_anteilig = round(mindestgehalt * wochenstd / 40)
    jahr = max(gehalt_formel, min_gehalt_anteilig)
    monat = round(jahr / 12)
    
    return {
        'name': pm['name'],
        'color': pm['color'],
        'wochenstd': wochenstd,
        'pm_std_bundle': pm_std_bundle,
        'start_stufe': start_stufe,
        'mindestgehalt': mindestgehalt,
        'startdatum': startdatum,
        'vstd_bundle': vstd_bundle,
        'vstd_ber': vstd_ber,
        'abw_ber': abw_ber,
        'ist': ist,
        'ruecken': ruecken, 'komm': komm, 'enps': enps,
        'verfueg': verfueg,
        'eur60': eur60,
        'zufr': zufr,
        'rechn_stufe': rechn,
        'tats_stufe': tats,
        'tats_stufe_name': STUFEN[tats-1]['name'],
        'tats_stufe_zulage_pct': stufe_zulage_pct,
        'th_bundle': th_bundle,
        'th_pm': th_pm,
        'bundle_zulage': bundle_zulage,
        'basis_gehalt': basis,
        'gehalt_formel': gehalt_formel,
        'jahresgehalt': jahr,
        'monatsgehalt': monat,
        'mindest_anteilig': min_gehalt_anteilig,
        'bundle_standorte': pm['bundle_standorte'],
        'bundle_pms': pm['bundle_pms'],
    }

def delta_naechste_stufe(pm_data):
    tats = pm_data['tats_stufe']
    if tats >= 6:
        return None
    next_s = STUFEN[tats]
    delta_eur60 = next_s['eur60'] - pm_data['eur60']
    delta_bundle_umsatz_quartal = (next_s['eur60'] - pm_data['eur60']) * pm_data['verfueg']
    delta_bundle_monat = delta_bundle_umsatz_quartal / 3
    # Gehaltsunterschied: next_gehalt - aktuelles_gehalt
    next_zulage = next_s['zulage']
    curr_zulage = pm_data['tats_stufe_zulage_pct']
    next_jahr = round(pm_data['basis_gehalt'] * (1 + next_zulage) * (pm_data['wochenstd'] / 40))
    next_monat = round(next_jahr / 12)
    delta_monat = next_monat - pm_data['monatsgehalt']
    delta_jahr = next_jahr - pm_data['jahresgehalt']
    return {
        'next_stufe': next_s,
        'delta_eur60': delta_eur60,
        'delta_bundle_monat': delta_bundle_monat,
        'delta_gehalt_monat': delta_monat,
        'delta_gehalt_jahr': delta_jahr,
        'next_jahresgehalt': next_jahr,
        'next_monatsgehalt': next_monat,
        # Progress-Percent: wie weit im Gap
        'progress_pct': max(0, min(100, (pm_data['eur60'] - STUFEN[tats-1]['eur60']) /
                                        (next_s['eur60'] - STUFEN[tats-1]['eur60']) * 100)),
    }

def hebel_optionen(pm_data, gap_data, live_kpis):
    """Konkrete Hebel-Werte um die nächste Stufe zu erreichen.

    Faktoren (Standard-Approximation):
      +1 %-Pkt PKV-Quote     ≈ +0,7 % Umsatz
      +1 Termin/Wo (Bundle)  ≈ +0,3 % Umsatz
      −1 %-Pkt Krankenstand  ≈ +0,5 % Umsatz   (1 %-Pkt ≈ 2,3 Tage/TH/Jahr bei 230 Werktagen)
    """
    if not gap_data:
        return None
    delta_pct = gap_data['delta_eur60'] / pm_data['eur60'] * 100
    if delta_pct <= 0:
        return None

    F_PKV, F_TERMIN, F_KRANK = (PKV_FAKTOR - 1), 0.3, 0.5
    d_pkv_pkt   = delta_pct / F_PKV
    d_termin_wo = delta_pct / F_TERMIN
    d_krank_pkt = delta_pct / F_KRANK
    d_krank_tage = d_krank_pkt * 2.3

    pkv_now    = (live_kpis or {}).get('pkv_quote') or 0
    krank_now  = (live_kpis or {}).get('krank_tage_pro_th_jahr') or 0
    auslast_now = (live_kpis or {}).get('auslastung') or 0
    anzahl_th  = (live_kpis or {}).get('auslastung_n_th') or 0
    d_termin_pro_th = (d_termin_wo / anzahl_th) if anzahl_th else None

    # 3-Stufen-Plausibilität: realistic | borderline | impossible
    if d_pkv_pkt <= 15:    pkv_lvl = 'realistic'
    elif d_pkv_pkt <= 25:  pkv_lvl = 'borderline'
    else:                  pkv_lvl = 'impossible'

    # Termine: pro-TH-Wert ist die natürliche Plausibilitäts-Einheit.
    # Auch bei voller Auslastung kann der Hebel ziehen — über PKV-Fokus bei rotierenden Patienten.
    pth = d_termin_pro_th or d_termin_wo
    if pth <= 1:    termin_lvl = 'realistic'
    elif pth <= 2:  termin_lvl = 'borderline'
    else:           termin_lvl = 'impossible'

    if not krank_now or krank_now <= 0:  krank_lvl = 'impossible'
    elif d_krank_tage <= krank_now * 0.5: krank_lvl = 'realistic'
    elif d_krank_tage <= krank_now:      krank_lvl = 'borderline'
    else:                                krank_lvl = 'impossible'

    return {
        'delta_pct': delta_pct,
        'd_pkv_pkt': d_pkv_pkt, 'pkv_now': pkv_now, 'pkv_neu': pkv_now + d_pkv_pkt,
        'd_termin_wo': d_termin_wo, 'd_termin_pro_th': d_termin_pro_th, 'anzahl_th': anzahl_th,
        'd_krank_tage': d_krank_tage, 'krank_now': krank_now, 'krank_neu': max(krank_now - d_krank_tage, 0),
        'pkv_lvl': pkv_lvl, 'termin_lvl': termin_lvl, 'krank_lvl': krank_lvl,
    }

# ==================== HTML TEMPLATE ====================
CSS = """
:root {
  --teal: #0D595A;
  --teal-mid: #1a8a8b;
  --teal-light: #e8f4f4;
  --teal-glow: rgba(13, 89, 90, 0.08);
  --orange: #ED7D31;
  --orange-light: #fef0e5;
  --green: #2e7d32;
  --green-light: #e8f5e9;
  --red: #c62828;
  --red-light: #ffebee;
  --bg: #fafafa;
  --white: #ffffff;
  --ink: #1a1a1a;
  --ink-soft: #4a4a4a;
  --muted: #8e8e8e;
  --line: #e8e8e8;
  --line-strong: #d4d4d4;
  --radius: 20px;
  --radius-sm: 12px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow: 0 4px 24px rgba(0,0,0,0.06);
  --shadow-lg: 0 12px 40px rgba(0,0,0,0.08);
  --font: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
  --mono: 'SF Mono', Menlo, Monaco, monospace;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--ink);
  line-height: 1.55;
  font-feature-settings: 'tnum' 1, 'cv11' 1;
  -webkit-font-smoothing: antialiased;
}

.container { max-width: 760px; margin: 0 auto; padding: 32px 20px 80px; }

/* === TOP BAR === */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
}
.topbar-name {
  font-size: 13px;
  color: var(--muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 600;
}
.topbar-quartal {
  font-size: 13px;
  color: var(--ink);
  font-weight: 500;
  padding: 4px 12px;
  background: var(--teal-light);
  border-radius: 999px;
  color: var(--teal);
}

/* === PAGE TITLE === */
.page-title {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 4px;
  line-height: 1.1;
}
.page-subtitle {
  font-size: 15px;
  color: var(--muted);
  margin-bottom: 40px;
}

/* === BLOCK === */
.block { margin-bottom: 36px; }
.block-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 14px;
}
.block-label::before {
  content: ''; width: 6px; height: 6px; border-radius: 50%;
  background: var(--teal);
}
.block-title {
  font-size: 19px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 16px;
  letter-spacing: -0.01em;
}
.block-intro {
  font-size: 14px;
  color: var(--ink-soft);
  margin-bottom: 18px;
  line-height: 1.6;
}

/* === HERO CARD === */
.hero-card {
  background: linear-gradient(135deg, var(--teal) 0%, var(--teal-mid) 100%);
  color: white;
  border-radius: var(--radius);
  padding: 36px 32px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}
.hero-card::before {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(255,255,255,0.1), transparent 70%);
  border-radius: 50%;
}
.hero-stufe {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  opacity: 0.85;
  padding: 5px 12px;
  background: rgba(255,255,255,0.15);
  border-radius: 999px;
  margin-bottom: 20px;
}
.hero-gehalt {
  font-size: 56px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 4px;
}
.hero-gehalt-unit {
  font-size: 18px;
  font-weight: 500;
  opacity: 0.9;
  margin-bottom: 20px;
}
.hero-meta {
  display: flex; gap: 24px; flex-wrap: wrap;
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,0.15);
  font-size: 13px;
}
.hero-meta-item { opacity: 0.9; }
.hero-meta-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.7;
  display: block;
  margin-bottom: 2px;
}
.hero-meta-value { font-weight: 700; font-size: 15px; }

/* === BREAKDOWN === */
.breakdown-card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--line);
}
.breakdown-formula {
  font-size: 15px;
  color: var(--ink-soft);
  margin-bottom: 18px;
  line-height: 1.7;
}
.breakdown-bar {
  display: flex; height: 40px;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: inset 0 0 0 1px var(--line);
}
.breakdown-seg {
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: white;
  white-space: nowrap;
  padding: 0 10px;
}
.breakdown-seg.sockel { background: var(--teal); }
.breakdown-seg.bundle { background: var(--teal-mid); }
.breakdown-seg.stufe { background: var(--orange); }
.breakdown-seg.rest { background: var(--line); color: var(--muted); }

.breakdown-legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 14px;
}
.breakdown-legend-item {
  display: flex; flex-direction: column; gap: 2px;
  padding-left: 12px;
  border-left: 3px solid var(--teal);
}
.breakdown-legend-item.bundle { border-color: var(--teal-mid); }
.breakdown-legend-item.stufe { border-color: var(--orange); }
.breakdown-legend-label {
  font-size: 11px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.05em;
}
.breakdown-legend-val { font-size: 16px; font-weight: 700; color: var(--ink); }
.breakdown-result {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed var(--line-strong);
  display: flex; align-items: baseline; justify-content: space-between;
  flex-wrap: wrap; gap: 12px;
}
.breakdown-result-label { font-size: 13px; color: var(--muted); }
.breakdown-result-val { font-size: 28px; font-weight: 800; color: var(--teal); }

/* === TWO-KPI GRID === */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.kpi-card {
  background: var(--white);
  border-radius: var(--radius-sm);
  padding: 22px 20px;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}
.kpi-label {
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 34px; font-weight: 800; letter-spacing: -0.02em;
  line-height: 1; margin-bottom: 4px;
}
.kpi-value.good { color: var(--green); }
.kpi-value.ok { color: var(--teal); }
.kpi-value.warn { color: var(--orange); }
.kpi-unit { font-size: 14px; font-weight: 500; color: var(--muted); margin-left: 2px; }
.kpi-schwelle {
  font-size: 12px; color: var(--muted); margin-top: 10px;
  padding-top: 10px; border-top: 1px solid var(--line);
}
.kpi-schwelle strong { color: var(--ink-soft); font-weight: 600; }
.kpi-bar {
  margin-top: 12px;
  height: 6px; background: var(--line); border-radius: 3px; overflow: hidden;
}
.kpi-bar-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--teal), var(--teal-mid));
  transition: width 0.8s ease;
}
.kpi-bar-fill.over { background: linear-gradient(90deg, var(--green), #66bb6a); }
.kpi-bar-fill.under { background: linear-gradient(90deg, var(--orange), #ffab40); }

/* === STUFEN-LEITER === */
.stufen-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 8px 2px 14px;
  scrollbar-width: thin;
  scrollbar-color: var(--line-strong) transparent;
}
.stufen-scroll::-webkit-scrollbar { height: 4px; }
.stufen-scroll::-webkit-scrollbar-thumb { background: var(--line-strong); border-radius: 2px; }

.stufe-chip {
  flex: 0 0 auto;
  background: var(--white);
  border: 2px solid var(--line);
  border-radius: 14px;
  padding: 14px 16px;
  min-width: 120px;
  text-align: center;
  transition: all 0.2s;
}
.stufe-chip-num {
  font-size: 10px; font-weight: 700;
  color: var(--muted); letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 2px;
}
.stufe-chip-name {
  font-size: 14px; font-weight: 700; color: var(--ink);
  margin-bottom: 8px;
}
.stufe-chip-detail {
  font-size: 11px; color: var(--muted); line-height: 1.4;
}
.stufe-chip.current {
  border-color: var(--teal); background: var(--teal-light);
  transform: scale(1.05);
  box-shadow: var(--shadow);
}
.stufe-chip.current .stufe-chip-name { color: var(--teal); }
.stufe-chip.next {
  border-color: var(--orange);
  border-style: dashed;
  background: var(--orange-light);
}
.stufe-chip.next .stufe-chip-name { color: var(--orange); }

/* === GAP BLOCK === */
.gap-card {
  background: linear-gradient(135deg, var(--orange-light) 0%, #fff5e6 100%);
  border-radius: var(--radius);
  padding: 24px 28px;
  border: 1px solid #ffd9b3;
}
.gap-header {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px;
}
.gap-from, .gap-to {
  display: inline-flex; align-items: center;
  padding: 4px 12px; border-radius: 999px;
  font-size: 12px; font-weight: 700;
}
.gap-from { background: var(--teal-light); color: var(--teal); }
.gap-to { background: var(--orange-light); color: var(--orange); border: 1px solid #ffb27a; }
.gap-arrow { color: var(--muted); font-size: 18px; }
.gap-numbers {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.gap-number { }
.gap-number-label {
  font-size: 11px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.08em;
  font-weight: 600;
  margin-bottom: 4px;
}
.gap-number-val { font-size: 22px; font-weight: 800; color: var(--orange); }
.gap-number-val.pos { color: var(--green); }
.gap-bar-wrap {
  background: rgba(255,255,255,0.6);
  border-radius: 8px;
  padding: 10px 14px;
}
.gap-bar-label {
  font-size: 11px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.08em;
  font-weight: 600;
  margin-bottom: 6px;
}
.gap-bar {
  height: 10px; background: white; border-radius: 5px;
  overflow: hidden; margin-bottom: 6px;
  border: 1px solid #ffd9b3;
}
.gap-bar-fill {
  height: 100%; border-radius: 5px;
  background: linear-gradient(90deg, var(--orange), #ffab40);
  transition: width 0.8s ease;
}
.gap-bar-caption { font-size: 11px; color: var(--muted); text-align: right; }

/* === HEBEL === */
.hebel-grid {
  display: grid; gap: 10px;
}
.hebel-item {
  background: var(--white);
  border-radius: var(--radius-sm);
  padding: 16px 18px;
  border: 1px solid var(--line);
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  align-items: center;
}
.hebel-content { }
.hebel-name { font-weight: 700; color: var(--ink); margin-bottom: 4px; }
.hebel-desc { font-size: 13px; color: var(--ink-soft); line-height: 1.5; }
.hebel-effect {
  font-size: 12px; font-weight: 700;
  color: var(--teal);
  background: var(--teal-light);
  padding: 8px 12px;
  border-radius: 8px;
  white-space: nowrap;
  text-align: center;
}
.hebel-effect.borderline { color: var(--orange); background: var(--orange-light); }
.hebel-effect.impossible { color: var(--red); background: var(--red-light); }
.hebel-tag {
  display: inline-block;
  font-size: 11px; font-weight: 600;
  padding: 2px 8px; border-radius: 999px;
  margin-left: 6px;
  letter-spacing: 0.02em;
}
.hebel-tag.realistic  { background: var(--green-light);  color: var(--green); }
.hebel-tag.borderline { background: var(--orange-light); color: var(--orange); }
.hebel-tag.impossible { background: var(--red-light);    color: var(--red); }
.hebel-from-to {
  font-size: 12px; color: var(--ink-soft);
  margin-top: 4px;
}
.hebel-headline {
  font-size: 15px; line-height: 1.55;
  margin-bottom: 14px; color: var(--ink-soft);
}
.hebel-headline strong { color: var(--ink); }
.hebel-note {
  font-size: 12px; color: var(--muted);
  margin-top: 10px; font-style: italic;
}

/* === TIMELINE === */
.timeline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}
.timeline-item {
  background: var(--white);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
}
.timeline-item.current {
  border-color: var(--teal); background: var(--teal-light);
}
.timeline-item.empty {
  background: #f7f7f7; border-style: dashed;
}
.timeline-q {
  font-size: 11px; color: var(--muted); font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 6px;
}
.timeline-stufe { font-size: 14px; font-weight: 700; color: var(--ink); margin-bottom: 2px; }
.timeline-gehalt { font-size: 13px; color: var(--ink-soft); }
.timeline-empty { font-size: 12px; color: var(--muted); font-style: italic; }

/* === LIVE === */
.live-card {
  background: var(--white);
  border: 2px solid var(--teal-mid);
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow);
}
.live-status {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 700;
  color: var(--teal);
  padding: 4px 12px;
  background: var(--teal-light);
  border-radius: 999px;
  margin-bottom: 16px;
}
.live-status::before {
  content: ''; display: inline-block;
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--green); animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
.live-placeholder {
  font-size: 14px; color: var(--muted); line-height: 1.6;
  padding: 16px;
  background: var(--bg);
  border-radius: var(--radius-sm);
}

/* === FOOTER === */
.footer {
  margin-top: 48px; padding-top: 24px;
  border-top: 1px solid var(--line);
  text-align: center;
  font-size: 12px; color: var(--muted);
}
.footer a { color: var(--teal); text-decoration: none; }


.gap-row {
  display: flex;
  gap: 14px;
  padding: 18px 0;
  border-top: 1px solid #ffd9b3;
}
.gap-row:first-child { border-top: none; padding-top: 4px; }
.gap-row:last-child { padding-bottom: 4px; }
.gap-row-icon {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 700; flex-shrink: 0;
}
.gap-row.done .gap-row-icon {
  background: var(--green-light); color: var(--green);
}
.gap-row.gap .gap-row-icon {
  background: var(--orange-light); color: var(--orange);
}
.gap-row-content { flex: 1; min-width: 0; }
.gap-row-title {
  font-weight: 700; font-size: 15px; color: var(--ink);
  margin-bottom: 8px;
}
.gap-row.done .gap-row-title { color: var(--green); }
.gap-row-detail {
  font-size: 13px; color: var(--ink-soft); line-height: 1.5;
}
.gap-row-kpis {
  display: grid; grid-template-columns: auto 1fr; gap: 12px 18px;
  margin-bottom: 10px;
}
.gap-mini-label {
  font-size: 11px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.05em;
  margin-bottom: 2px;
}
.gap-mini-val { font-size: 17px; font-weight: 700; color: var(--orange); }

@media (max-width: 600px) {
  .gap-row-kpis { grid-template-columns: 1fr; }
}

/* === ZUFRIEDENHEITS-BREAKDOWN === */
.zufr-breakdown {
  margin-top: 14px; padding-top: 14px;
  border-top: 1px dashed var(--line);
}
.zufr-breakdown-title {
  font-size: 10px; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: 10px;
}
.zufr-sub {
  display: grid; grid-template-columns: 1fr auto; gap: 4px 10px;
  align-items: center;
  margin-bottom: 8px;
}
.zufr-sub:last-child { margin-bottom: 0; }
.zufr-sub-label {
  font-size: 12px; color: var(--ink-soft);
  grid-column: 1 / 3;
}
.zufr-sub-bar {
  grid-column: 1;
  height: 5px; background: var(--line); border-radius: 3px;
  overflow: hidden;
}
.zufr-sub-fill {
  display: block; height: 100%;
  background: linear-gradient(90deg, var(--teal-mid), var(--teal));
  border-radius: 3px;
}
.zufr-sub-val {
  grid-column: 2; grid-row: 2;
  font-size: 13px; font-weight: 700; color: var(--teal);
  white-space: nowrap;
}
.zufr-sub-val small { font-weight: 500; color: var(--muted); margin-left: 2px; font-size: 11px; }

/* === LIVE KPIs === */
.live-kpi-card {
  background: linear-gradient(135deg, #fff 0%, var(--bg) 100%);
  border: 2px solid var(--teal-light);
  border-radius: var(--radius);
  padding: 20px 22px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-sm);
}
.live-kpi-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px; padding-bottom: 12px;
  border-bottom: 1px dashed var(--line);
}
.live-kpi-title {
  font-size: 14px; font-weight: 800; color: var(--teal);
  text-transform: uppercase; letter-spacing: 0.05em;
}
.live-kpi-date {
  font-size: 11px; color: var(--muted);
  background: var(--teal-light);
  padding: 3px 10px; border-radius: 999px;
  color: var(--teal); font-weight: 600;
}
.live-kpi-row {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 10px 14px;
  align-items: center;
  margin-bottom: 12px;
}
.live-kpi-row:last-child { margin-bottom: 0; }
.live-kpi-label {
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted);
}
.live-kpi-chip-track {
  position: relative;
  background: var(--bg);
  border-radius: 10px;
  height: 36px;
  overflow: hidden;
  border: 1px solid var(--line);
}
.live-kpi-chip {
  position: absolute; inset: 0 auto 0 0;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 12px;
  border-radius: 10px;
  font-size: 13px; font-weight: 700;
  color: white;
  box-shadow: var(--shadow-sm);
  transition: width 0.6s ease;
}
.live-kpi-note {
  grid-column: 2 / 3;
  font-size: 11px; color: var(--muted);
  font-style: italic;
  margin-top: -4px;
}
@media (max-width: 600px) {
  .live-kpi-row { grid-template-columns: 1fr; gap: 4px; }
  .live-kpi-note { grid-column: 1; }
}

/* === WEGE === */
.wege-grid { display: grid; gap: 14px; }
.weg-card {
  background: var(--white);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 20px 22px;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}
.weg-card::before {
  content: ''; position: absolute;
  top: 0; left: 0; width: 4px; height: 100%;
  background: linear-gradient(180deg, var(--teal), var(--teal-mid));
}
.weg-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; padding-bottom: 14px;
  border-bottom: 1px dashed var(--line);
}
.weg-head-label {
  font-size: 17px; font-weight: 800; color: var(--teal);
  letter-spacing: -0.01em;
}
.weg-head-tag {
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--muted);
  background: var(--bg); padding: 4px 10px; border-radius: 999px;
}
.weg-vars { display: grid; gap: 10px; }
.weg-var {
  display: grid; grid-template-columns: 110px 1fr;
  align-items: center; gap: 14px;
}
.weg-var-label {
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted);
}
.weg-chip-track {
  position: relative;
  background: var(--bg);
  border-radius: 10px;
  height: 40px;
  overflow: hidden;
  border: 1px solid var(--line);
}
.weg-chip {
  position: absolute; inset: 0 auto 0 0;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 14px;
  border-radius: 10px;
  font-size: 14px; font-weight: 700;
  color: white;
  box-shadow: var(--shadow-sm);
  transition: width 0.6s ease;
}
.weg-chip-text { font-size: 14px; font-weight: 700; white-space: nowrap; }
.weg-chip-range {
  font-size: 12px; font-weight: 600;
  background: rgba(255,255,255,0.22);
  padding: 2px 8px; border-radius: 999px;
  white-space: nowrap;
}
.weg-chip-low   { width: 32%; background: linear-gradient(135deg, #8bc34a, #7cb342); }
.weg-chip-mid   { width: 55%; background: linear-gradient(135deg, #ffb547, #ff9800); }
.weg-chip-high  { width: 78%; background: linear-gradient(135deg, var(--teal-mid), var(--teal)); }
.weg-chip-vhigh { width: 100%; background: linear-gradient(135deg, #095859, #054546); }

.weg-text {
  background: var(--bg); border-radius: var(--radius-sm);
  padding: 20px 22px; color: var(--ink-soft);
  font-size: 14px; line-height: 1.6;
  border-left: 3px solid var(--teal);
}

.weg-legende {
  margin-top: 18px; padding: 16px 18px;
  background: var(--bg); border-radius: var(--radius-sm);
  font-size: 12px; color: var(--muted);
  border: 1px solid var(--line);
}
.weg-legende-title {
  font-weight: 700; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--ink-soft); margin-bottom: 12px;
}
.weg-legende-row {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; align-items: center;
}
.weg-legende-row:last-child { margin-bottom: 0; }
.weg-legende-kpi {
  font-weight: 700; color: var(--ink-soft); font-size: 12px;
  min-width: 90px;
}
.weg-legende-item {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px; border-radius: 999px;
  color: white; font-size: 11px; font-weight: 700;
}
.weg-legende-item.low   { background: #8bc34a; }
.weg-legende-item.mid   { background: #ff9800; }
.weg-legende-item.high  { background: var(--teal); }
.weg-legende-item.vhigh { background: #095859; }
.weg-legende-item .rg {
  opacity: 0.85; font-weight: 500; font-size: 10px;
}

/* === RESPONSIVE === */
@media (max-width: 600px) {
  .container { padding: 20px 16px 60px; }
  .hero-gehalt { font-size: 44px; }
  .kpi-grid { grid-template-columns: 1fr; }
  .gap-numbers { grid-template-columns: 1fr; }
  .breakdown-legend { grid-template-columns: 1fr 1fr; }
  .hebel-item { grid-template-columns: 1fr; gap: 10px; }
  .hebel-effect { width: 100%; }
}
"""

def fmt_eur(n, decimals=0):
    if n is None: return '—'
    return f"{n:,.{decimals}f}".replace(',', '§').replace('.', ',').replace('§', '.')

def fmt_de(n, decimals=1):
    """Deutsche Dezimal-Formatierung (Komma statt Punkt) für Zahlen ohne €."""
    if n is None: return '—'
    return f"{n:,.{decimals}f}".replace(',', '§').replace('.', ',').replace('§', '.')

def quartal_label(d):
    """'Q2 2026' für ein date-Objekt."""
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"

def vorquartal_label(d):
    """Letztes abgeschlossenes Quartal vor d, z.B. 'Q1 2026' wenn d in Q2 2026."""
    q = (d.month - 1) // 3 + 1
    return f"Q{q - 1} {d.year}" if q > 1 else f"Q4 {d.year - 1}"

def _kpi_bar_render(val, curr_threshold, next_threshold, curr_n, next_n, has_next):
    """Bar mit klar getrennter Caption: '✓ Stufe X erreicht · Y % Richtung Stufe Z'.
    Bar-Füllung = Progress zwischen aktueller und nächster Schwelle (0–100 %)."""
    if not has_next:
        cap = '<span style="color:var(--green);font-weight:700;">✓ Höchste Stufe erreicht</span>'
        return f'<div class="kpi-bar-caption" style="font-size:11px;margin-top:8px;">{cap}</div><div class="kpi-bar"><div class="kpi-bar-fill over" style="width:100%"></div></div>'
    if val >= next_threshold:
        cap = f'<span style="color:var(--green);font-weight:700;">✓ über Schwelle Stufe {next_n}</span>'
        return f'<div class="kpi-bar-caption" style="font-size:11px;margin-top:8px;">{cap}</div><div class="kpi-bar"><div class="kpi-bar-fill over" style="width:100%"></div></div>'
    if val >= curr_threshold:
        denom = next_threshold - curr_threshold
        progress = ((val - curr_threshold) / denom * 100) if denom > 0 else 100
        cap = f'<span style="color:var(--green);font-weight:700;">✓ Stufe {curr_n} erreicht</span> · {progress:.0f} % Richtung Stufe {next_n}'
        return f'<div class="kpi-bar-caption" style="font-size:11px;margin-top:8px;color:var(--ink-soft);">{cap}</div><div class="kpi-bar"><div class="kpi-bar-fill" style="width:{progress:.0f}%"></div></div>'
    cap = f'<span style="color:var(--orange);font-weight:700;">✗ Schwelle Stufe {curr_n} nicht erreicht</span>'
    return f'<div class="kpi-bar-caption" style="font-size:11px;margin-top:8px;">{cap}</div><div class="kpi-bar"><div class="kpi-bar-fill under" style="width:0%"></div></div>'

def _eur_bar_html(pm, curr_s, next_s, d):
    return _kpi_bar_render(pm['eur60'], curr_s['eur60'], next_s['eur60'], curr_s['n'], next_s['n'], bool(d))

def _zufr_bar_html(pm, curr_s, next_s, d):
    return _kpi_bar_render(pm['zufr'], curr_s['zufr'], next_s['zufr'], curr_s['n'], next_s['n'], bool(d))



# ============ LIVE KPIs ============

AUSLASTUNG_4W_TABLE = 'm29vw64nhicfco2'
TH_BY_NAME_CACHE = {}

import subprocess, tempfile, os as _os, time as _time

def _env():
    if _os.environ.get('NOCODB_TOKEN'):
        return {'NOCODB_TOKEN': _os.environ['NOCODB_TOKEN']}
    e = {}
    env_path = _os.path.expanduser('~/.claude/.env')
    if not _os.path.exists(env_path):
        raise RuntimeError('NOCODB_TOKEN not set and ~/.claude/.env not found')
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                e[k] = v.strip('"').strip("'")
    return e

_NOCO_CACHE = {}

def _fetch_all(table_id, where=None):
    cache_key = f'{table_id}|{where}'
    if cache_key in _NOCO_CACHE:
        return _NOCO_CACHE[cache_key]
    env = _env()
    rows = []; offset = 0
    cfg = tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False)
    cfg.write(f'header = "xc-token: {env["NOCODB_TOKEN"]}"\n'); cfg.close(); _os.chmod(cfg.name, 0o600)
    try:
        while True:
            params = [f'limit=200', f'offset={offset}']
            if where: params.append(f'where={where}')
            url = f'https://db.vacura-praxis.de/api/v2/tables/{table_id}/records?' + '&'.join(params)
            # Retry 3x
            data = None
            for attempt in range(3):
                try:
                    r = subprocess.run(['curl','-sS','--max-time','60','-K',cfg.name,url], capture_output=True, text=True, timeout=90)
                    if r.returncode != 0 or not r.stdout.strip():
                        _time.sleep(1); continue
                    data = json.loads(r.stdout)
                    break
                except Exception:
                    _time.sleep(1)
            if not data:
                raise RuntimeError(f'NocoDB fetch failed after retries for {table_id}')
            batch = data.get('list', [])
            rows.extend(batch)
            if len(batch) < 200:
                _NOCO_CACHE[cache_key] = rows
                return rows
            offset += 200
    finally:
        _os.unlink(cfg.name)

def termin_umsatz(t):
    """€-Umsatz eines Termins basierend auf Dauer (aus beginn/ende), Verordnungstyp, Hausbesuch.
    Tarif-Logik aus reference_verguetungswerte.md: GKV-Basis nach Dauer-Stufe, ×PKV_FAKTOR für PKV/SZ, +27,56 € Hausbesuch (× Faktor)."""
    from datetime import datetime as _dt
    import math
    try:
        beginn = _dt.fromisoformat(t['beginn'].replace('Z', '+00:00'))
        ende   = _dt.fromisoformat(t['ende'].replace('Z', '+00:00'))
        dauer  = (ende - beginn).total_seconds() / 60
    except Exception:
        return 0.0
    if dauer <= 0: return 0.0
    if dauer <= 20:   basis = 8.51
    elif dauer <= 30: basis = 56.93
    elif dauer <= 45: basis = 75.91
    elif dauer <= 60: basis = 94.89
    else:             basis = 94.89 + math.ceil((dauer - 60) / 15) * 18.98
    if t.get('is_hausbesuch'):
        basis += 27.56
    if t.get('verordnungstyp') in (2, 3):
        basis *= PKV_FAKTOR
    return basis

def compute_live_quartalsstand(pm, today=None):
    """Live-€/h für laufendes Quartal (Q-bisher) eines PM-Bundles.

    Methode (parallel zu Q1-Bewertung):
    - IST_live: Sum Termin-Umsatz (Status erbracht/erbracht_und_unterschrieben, art=normal,
      deleted_at NULL, !is_blocker, !is_passive_leistung) im Q-bisher
    - VStd_q_bisher: pm['vstd_ber'] / 13 × Wochen-Q-bisher (Bundle-Größe Q1 als Stable-Annahme)
    - Abw_q_bisher: Stunden-Summe von Abwesenheiten (außer krank/krankheit_kind/angefragt — v17-Filter)
    - eur60_live = IST_live / (VStd_q_bisher − Abw_q_bisher)

    Wenn Quartalsanfang (< 1 Woche) oder verfueg_live ≤ 0: return None.
    """
    from datetime import date as _date, timedelta as _td, datetime as _dt
    today = today or _date.today()
    q_month = ((today.month - 1) // 3) * 3 + 1
    q_start = _date(today.year, q_month, 1)
    q_days = (today - q_start).days + 1
    wochen_q_bisher = q_days / 7
    if wochen_q_bisher < 1.0:
        return None

    bundle_standorte = [s.strip().lower().replace(' ', '_') for s in pm['bundle_standorte'].split(',')]

    # 1) IST_live aus Termine im Q-bisher
    ist_live = 0.0
    termine_count = 0
    for st in bundle_standorte:
        termine = _fetch_all('mf2pw17nwfzlkd2', where=f'(filiale,eq,{st})')
        for t in termine:
            if t.get('deleted_at'): continue
            if t.get('art') != 'normal': continue
            if t.get('is_blocker') or t.get('is_passive_leistung'): continue
            if t.get('status') not in ('erbracht', 'erbracht_und_unterschrieben'): continue
            try:
                b = _date.fromisoformat(t['beginn'][:10])
            except Exception: continue
            if b < q_start or b > today: continue
            ist_live += termin_umsatz(t)
            termine_count += 1

    # 2) Bundle-VStd live: aus auslastung_4w (letzter Snapshot pro TH) ÷ 4 = Wochenstunden
    #    × wochen_q_bisher = VStd Q-bisher.
    #    Berücksichtigt Beschäftigungs-Übergänge automatisch (besser als Q1-Extrapolation).
    ma = _fetch_all('mc934lbrlg7w6e1')
    def _aktiv_heute(m):
        bz = m.get('beschaeftigungszeiten') or []
        iso = today.isoformat()
        for e in bz:
            v = e.get('Von'); b = e.get('Bis')
            if (v is None or v <= iso) and (b is None or b >= iso):
                return True
        return False
    bundle_th = [m for m in ma
                 if m.get('is_therapeut')
                 and 'Online' not in f"{m.get('vorname','')} {m.get('nachname','')}"
                 and any(f in bundle_standorte for f in (m.get('filialen') or []))
                 and _aktiv_heute(m)]
    th_ids = {t['id'] for t in bundle_th}
    anzahl_th = max(1, len(bundle_th))

    ausl = _fetch_all('m29vw64nhicfco2')
    latest_per_th = {}
    for r in ausl:
        mid = r.get('mitarbeiter_id')
        if mid not in th_ids: continue
        d = r.get('datum', '')
        if mid not in latest_per_th or d > latest_per_th[mid].get('datum', ''):
            latest_per_th[mid] = r
    bundle_h_pro_woche_live = sum((r.get('arbeitszeit_h', 0) or 0) / 4 for r in latest_per_th.values())
    if bundle_h_pro_woche_live <= 0:
        # Fallback: Q1-Extrapolation
        bundle_h_pro_woche_live = pm['vstd_ber'] / 13
    vstd_q_bisher = bundle_h_pro_woche_live * wochen_q_bisher

    # 3) Abw_q_bisher — Methode A (Hybrid): echte Q-bisher-Abw aus NocoDB,
    # plus Q1-Quote als Diagnose-Wert (nicht für eur60). Live-Wert ist rein
    # informativ — finale Q-Bewertung läuft am Quartalsende aus Excel.
    EXCLUDED_ARTS = {'krank', 'krankheit_kind', 'angefragt'}
    h_pro_werktag_per_th = bundle_h_pro_woche_live / anzahl_th / 5
    abw_records = _fetch_all('mwcnx74etcl1frq')
    abw_h_gemessen = 0.0
    for a in abw_records:
        if a.get('deleted_at'): continue
        if a.get('art') in EXCLUDED_ARTS: continue
        if a.get('mitarbeiter_id') not in th_ids: continue
        try:
            von = _date.fromisoformat(a['von'][:10])
            bis = _date.fromisoformat(a['bis'][:10])
        except Exception: continue
        day = max(von, q_start); end_day = min(bis, today)
        while day <= end_day:
            if day.weekday() < 5:
                abw_h_gemessen += h_pro_werktag_per_th
            day += _td(days=1)
    q1_abw_quote = pm['abw_ber'] / pm['vstd_ber'] if pm['vstd_ber'] > 0 else 0.10
    abw_h_stabilisiert = vstd_q_bisher * q1_abw_quote   # nur Diagnose

    verfueg_live = vstd_q_bisher - abw_h_gemessen
    if verfueg_live <= 0:
        return None
    eur60_live = ist_live / verfueg_live

    # Live-Stufen-Schätzung (gleiche UND-Logik wie Q-Bewertung — Zufriedenheit aus Q1)
    tats_stufe_live = 1
    for s in reversed(STUFEN):
        if eur60_live >= s['eur60'] and pm['zufr'] >= s['zufr']:
            tats_stufe_live = s['n']; break

    return {
        'eur60_live': eur60_live,
        'ist_live': ist_live,
        'verfueg_live': verfueg_live,
        'vstd_q_bisher': vstd_q_bisher,
        'abw_h_stabilisiert': abw_h_stabilisiert,    # via Q1-Abw-Quote (nur Diagnose)
        'abw_h_gemessen': abw_h_gemessen,        # echt aus NocoDB (nur Info)
        'q1_abw_quote': q1_abw_quote,
        'bundle_h_pro_woche': bundle_h_pro_woche_live,
        'wochen_q_bisher': wochen_q_bisher,
        'anzahl_th_aktiv': anzahl_th,
        'q_start': q_start,
        'today': today,
        'tats_stufe_live': tats_stufe_live,
        'termine_count': termine_count,
    }

def compute_live_kpis(bundle_standorte, today=None):
    """Berechnet Auslastung, PKV-Quote, Krank-Tage/TH/Jahr für Bundle."""
    from datetime import date as _date
    today = today or _date.today()
    # Quartalsstart
    q_month = ((today.month - 1) // 3) * 3 + 1
    q_start = _date(today.year, q_month, 1)
    
    # 1) TH im Bundle
    ma = _fetch_all('mc934lbrlg7w6e1')
    bundle_th = [m for m in ma 
                 if m.get('is_therapeut')
                 and 'Online' not in f"{m.get('vorname','')} {m.get('nachname','')}"
                 and any(f in bundle_standorte for f in (m.get('filialen') or []))]
    th_ids = {t['id'] for t in bundle_th}
    
    # 2) AUSLASTUNG: aus Auslastung 4W Tabelle (rolling 30 Tage)
    auslast_records = _fetch_all(AUSLASTUNG_4W_TABLE)
    # Nimm letzten Snapshot pro TH
    latest_per_th = {}
    for r in auslast_records:
        mid = r.get('mitarbeiter_id')
        if mid not in th_ids: continue
        d = r.get('datum','')
        if mid not in latest_per_th or d > latest_per_th[mid].get('datum',''):
            latest_per_th[mid] = r
    # Bundle-Auslastung wie in der App (AdminAuslastung.tsx): SUM(ist_h) / SUM(ziel_h)
    # — gewichtet nach Wochenstunden, nicht avg der Prozent-Werte
    total_ist  = sum(r.get('ist_h', 0) or 0 for r in latest_per_th.values())
    total_ziel = sum(r.get('zielwert_h', 0) or 0 for r in latest_per_th.values())
    auslastung = (total_ist / total_ziel * 100) if total_ziel > 0 else None
    
    # 3) PKV-QUOTE: aus Termine Q-bisher
    pkv_count = 0; total_count = 0
    for st in bundle_standorte:
        termine = _fetch_all('mf2pw17nwfzlkd2', where=f'(filiale,eq,{st})')
        for t in termine:
            if t.get('deleted_at'): continue
            from datetime import date as _dt
            try: 
                b = _dt.fromisoformat(t['beginn'][:10])
            except: continue
            if b < q_start or b > today: continue
            if t.get('status') not in ('erbracht','erbracht_und_unterschrieben'): continue
            if t.get('art') != 'normal': continue
            total_count += 1
            if t.get('verordnungstyp') in (2, 3):
                pkv_count += 1
    pkv_quote = pkv_count / total_count * 100 if total_count else None
    
    # 4) KRANKHEIT: trailing 90 Kalendertage, hochgerechnet aufs Jahr
    # — rolling, damit der Wert beim Quartalswechsel nicht abrupt zurückspringt
    #   und Spitzenmonate (z.B. Februar-Welle) im Mess-Fenster bleiben
    from datetime import timedelta as _td
    from datetime import date as _dt
    krank_start = today - _td(days=90)
    abw = _fetch_all('mwcnx74etcl1frq')
    krank_stunden = 0.0
    for a in abw:
        if a.get('deleted_at'): continue
        if a.get('art') not in ('krank','krankheit_kind'): continue
        if a.get('mitarbeiter_id') not in th_ids: continue
        try:
            von = _dt.fromisoformat(a['von'][:10])
            bis = _dt.fromisoformat(a['bis'][:10])
        except: continue
        day = max(von, krank_start); end_day = min(bis, today)
        while day <= end_day:
            if day.weekday() < 5:
                # Hours für Standard-TH (grob 8h, vereinfacht)
                krank_stunden += 8.0
            day += _td(days=1)
    # Werktage im 90-Tage-Fenster
    werktage_fenster = 0
    d = krank_start
    while d <= today:
        if d.weekday() < 5: werktage_fenster += 1
        d += _td(days=1)
    krank_tage_bundle_jahr = (krank_stunden / 8) * (230 / werktage_fenster) if werktage_fenster else 0
    anzahl_th = len(bundle_th)
    krank_tage_pro_th_jahr = krank_tage_bundle_jahr / anzahl_th if anzahl_th else 0
    
    return {
        'auslastung': auslastung,
        'auslastung_n_th': len(latest_per_th),
        'pkv_quote': pkv_quote,
        'pkv_termine_total': total_count,
        'krank_tage_pro_th_jahr': krank_tage_pro_th_jahr,
        'q_start': q_start,
        'today': today,
        'werktage_fenster': werktage_fenster,
    }

def level_auslastung(val):
    if val is None: return None
    if val < 85: return 'low'
    if val < 93: return 'mid'
    if val < 96: return 'high'
    return 'vhigh'

def level_pkv(val):
    if val is None: return None
    if val <= 10: return 'low'
    if val <= 20: return 'mid'
    if val <= 30: return 'high'
    return 'vhigh'

def level_krank(val):
    """Krank-Tage/TH/Jahr: ≤15=low, 16–20=mid, 21–25=high, >25=vhigh"""
    if val is None: return None
    if val <= 15: return 'low'
    if val <= 20: return 'mid'
    if val <= 25: return 'high'
    return 'vhigh'

def kpi_level_label(kpi, level):
    if kpi == 'Auslastung':
        return {'low':'niedrig','mid':'mittel','high':'hoch','vhigh':'sehr hoch'}.get(level, '—')
    if kpi == 'PKV-Quote':
        return {'low':'gering','mid':'mittel','high':'hoch','vhigh':'sehr hoch'}.get(level, '—')
    if kpi == 'Krankheit':
        return {'low':'wenig','mid':'normal','high':'höher'}.get(level, '—')
    return '—'

def render_html(pm):
    from datetime import date as _date
    today = _date.today()
    q_aktuell = quartal_label(today)        # laufendes Quartal, z.B. 'Q2 2026'
    q_bewertung = vorquartal_label(today)   # zuletzt bewertetes Quartal, z.B. 'Q1 2026'
    q_now_num = (today.month - 1) // 3 + 1  # 1..4 — fürs Timeline-Mapping

    d = delta_naechste_stufe(pm)

    live_kpis = None  # gefüllt nur wenn nicht Stufe 6 (siehe unten)

    # Hero
    hero_stufe_text = f"Stufe {pm['tats_stufe']}"
    
    # Breakdown — Segment-Anteile
    ziel_gehalt = max(pm['gehalt_formel'], pm['mindest_anteilig'])
    total_width = pm['jahresgehalt']
    sockel_pct = (40000 * pm['wochenstd']/40) / total_width * 100
    bundle_pct = (pm['bundle_zulage'] * pm['wochenstd']/40) / total_width * 100
    stufe_pct = max(0, 100 - sockel_pct - bundle_pct)
    
    # Stufen-Leiter
    stufen_chips = []
    for s in STUFEN:
        cls = ''
        if s['n'] == pm['tats_stufe']: cls = 'current'
        elif s['n'] == pm['tats_stufe'] + 1: cls = 'next'
        stufen_chips.append(f'''
        <div class="stufe-chip {cls}">
          <div class="stufe-chip-num">{"★ Deine Stufe" if cls == "current" else ("Nächste Stufe" if cls == "next" else "Stufe")}</div>
          <div class="stufe-chip-name">{s['n']}</div>
          <div class="stufe-chip-detail">€/h ≥ {fmt_eur(s['eur60'], 2)}<br>Zufriedenheit ≥ {fmt_de(s['zufr'])}<br>+{int(s['zulage']*100)} % Zulage</div>
        </div>''')
    
    # €/60min-Block: Schwelle aktuell + progress
    curr_s = STUFEN[pm['tats_stufe']-1]
    next_s = STUFEN[min(pm['tats_stufe'], 5)]
    eur_progress = max(0, min(100, (pm['eur60'] - curr_s['eur60']) / 
                                   (next_s['eur60'] - curr_s['eur60']) * 100 if next_s != curr_s else 100))
    
    # Zufr
    zufr_curr = curr_s['zufr']
    zufr_next = next_s['zufr']
    zufr_progress = 100 if zufr_next == zufr_curr else max(0, min(100, (pm['zufr'] - zufr_curr) / 
                                                                        (zufr_next - zufr_curr) * 100))
    
    # Nächste Stufe - Was bringt / was fehlt
    next_block = ''
    gap_block = ''
    wege_block_html = ''
    hebel_note_condition = ''
    if d:
        next_s_obj = d['next_stufe']
        next_block = f'''
        <div class="block">
          <div class="block-label">Ausblick</div>
          <div class="block-title">Was bringt dir Stufe {next_s_obj['n']}?</div>
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-label">Monatsgehalt bei Stufe {next_s_obj['n']}</div>
              <div class="kpi-value good">{fmt_eur(d['next_monatsgehalt'])} <span class="kpi-unit">€</span></div>
              <div class="kpi-schwelle">Δ zum jetzigen Gehalt: <strong>+{fmt_eur(d['delta_gehalt_monat'])} € / Monat</strong></div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">Jahresgehalt bei Stufe {next_s_obj['n']}</div>
              <div class="kpi-value good">{fmt_eur(d['next_jahresgehalt'])} <span class="kpi-unit">€</span></div>
              <div class="kpi-schwelle">Δ pro Jahr: <strong>+{fmt_eur(d['delta_gehalt_jahr'])} €</strong></div>
            </div>
          </div>
        </div>
        '''
        # Gap: Umsatz + Zufriedenheit separat prüfen
        umsatz_reicht = pm['eur60'] >= next_s_obj['eur60']
        zufr_reicht = pm['zufr'] >= next_s_obj['zufr']
        delta_zufr = next_s_obj['zufr'] - pm['zufr']
        eur_progress = max(0, min(100, (pm['eur60'] - curr_s['eur60']) / 
                                  (next_s_obj['eur60'] - curr_s['eur60']) * 100)) if next_s_obj['eur60'] > curr_s['eur60'] else 100
        zufr_progress = max(0, min(100, (pm['zufr'] - curr_s['zufr']) / 
                                   (next_s_obj['zufr'] - curr_s['zufr']) * 100)) if next_s_obj['zufr'] > curr_s['zufr'] else 100
        
        # Umsatz-Bereich (entweder Gap oder ✓)
        if umsatz_reicht:
            umsatz_html = f'''
            <div class="gap-row done">
              <div class="gap-row-icon">✓</div>
              <div class="gap-row-content">
                <div class="gap-row-title">Umsatz pro Therapie-Stunde — erreicht</div>
                <div class="gap-row-detail">Du hast {fmt_eur(pm['eur60'], 2)} €/h, Schwelle für Stufe {next_s_obj['n']}: {fmt_eur(next_s_obj['eur60'], 2)} €/h</div>
              </div>
            </div>'''
        else:
            umsatz_html = f'''
            <div class="gap-row gap">
              <div class="gap-row-icon">↗</div>
              <div class="gap-row-content">
                <div class="gap-row-title">Mehr Umsatz pro Therapie-Stunde</div>
                <div class="gap-row-kpis">
                  <div class="gap-mini">
                    <div class="gap-mini-label">Fehlt</div>
                    <div class="gap-mini-val">+{fmt_eur(d['delta_eur60'], 2)} €/h</div>
                  </div>
                  <div class="gap-mini">
                    <div class="gap-mini-label">Als Bundle-Umsatz/Monat</div>
                    <div class="gap-mini-val">+{fmt_eur(d['delta_bundle_monat'])} €</div>
                  </div>
                </div>
                <div class="gap-bar"><div class="gap-bar-fill" style="width: {eur_progress:.0f}%"></div></div>
                <div class="gap-bar-caption">{fmt_eur(pm['eur60'], 2)} €/h → {fmt_eur(next_s_obj['eur60'], 2)} €/h</div>
              </div>
            </div>'''
        
        # Zufriedenheits-Bereich
        if zufr_reicht:
            zufr_html = f'''
            <div class="gap-row done">
              <div class="gap-row-icon">✓</div>
              <div class="gap-row-content">
                <div class="gap-row-title">Team-Zufriedenheit — erreicht</div>
                <div class="gap-row-detail">Du hast {fmt_de(pm['zufr'])} / 10, Schwelle für Stufe {next_s_obj['n']}: {fmt_de(next_s_obj['zufr'])}</div>
              </div>
            </div>'''
        else:
            zufr_html = f'''
            <div class="gap-row gap">
              <div class="gap-row-icon">↗</div>
              <div class="gap-row-content">
                <div class="gap-row-title">Höhere Team-Zufriedenheit</div>
                <div class="gap-row-kpis">
                  <div class="gap-mini">
                    <div class="gap-mini-label">Fehlt</div>
                    <div class="gap-mini-val">+{fmt_de(delta_zufr)} Punkte</div>
                  </div>
                  <div class="gap-mini">
                    <div class="gap-mini-label">Ziel</div>
                    <div class="gap-mini-val">{fmt_de(next_s_obj['zufr'])} / 10</div>
                  </div>
                </div>
                <div class="gap-bar"><div class="gap-bar-fill" style="width: {zufr_progress:.0f}%"></div></div>
                <div class="gap-bar-caption">{fmt_de(pm['zufr'])} → {fmt_de(next_s_obj['zufr'])}</div>
              </div>
            </div>'''
        
        # Kombiniere
        alles_erreicht = umsatz_reicht and zufr_reicht
        bundle_umsatz_hint = ''
        if not alles_erreicht:
            # Zeige wie viele Termine oder was auch immer
            pass
        
        gap_block = f'''
        <div class="block">
          <div class="block-label">Weg zur nächsten Stufe</div>
          <div class="block-title">Wie kommst du auf Stufe {next_s_obj['n']}?</div>
          <p class="block-intro">Für Stufe {next_s_obj['n']} müssen <strong>beide</strong> Bedingungen erfüllt sein — Umsatz <strong>und</strong> Team-Zufriedenheit.</p>
          <div class="gap-card">
            {umsatz_html}
            {zufr_html}
          </div>
        </div>
        '''

        # Live-KPIs "Dein aktueller Stand"
        aktueller_stand_html = ''
        live_quartal = None
        try:
            bundle_std_list = [s.strip().lower().replace(' ', '_') for s in pm.get('bundle_standorte','').split(',')]
            # Normalize back mapping
            bundle_std_list = ['prenzlauer_berg' if s == 'prenzlauer_berg' else s for s in bundle_std_list]
            live_kpis = compute_live_kpis(bundle_std_list)
        except Exception as _e:
            print(f'    (Live-KPIs-Fehler {pm["name"]}: {_e})')
        try:
            live_quartal = compute_live_quartalsstand(pm)
        except Exception as _e:
            print(f'    (Live-Quartalsstand-Fehler {pm["name"]}: {_e})')

        if live_kpis:
            from datetime import date as _date
            today_str = live_kpis['today'].strftime('%d.%m.%Y')
            # Aufbauen
            rows_html = ''
            # Auslastung
            a_val = live_kpis['auslastung']
            a_lvl = level_auslastung(a_val) if a_val is not None else None
            a_label = kpi_level_label('Auslastung', a_lvl) if a_lvl else '—'
            a_text = f'{a_val:.0f} %' if a_val is not None else 'keine Daten'
            a_chip_pct = {'low':18,'mid':55,'high':78,'vhigh':100}.get(a_lvl, 50) if a_lvl else 0
            rows_html += f'''
            <div class="live-kpi-row">
              <div class="live-kpi-label">Auslastung</div>
              <div class="live-kpi-chip-track">
                <div class="live-kpi-chip weg-chip-{a_lvl or 'low'}" style="width:{a_chip_pct}%">
                  <span class="weg-chip-text">{a_label}</span>
                  <span class="weg-chip-range">{a_text}</span>
                </div>
              </div>
              <div class="live-kpi-note">letzte 30 Tage (Auslastungs-Workflow)</div>
            </div>'''
            # PKV
            p_val = live_kpis['pkv_quote']
            p_lvl = level_pkv(p_val) if p_val is not None else None
            p_label = kpi_level_label('PKV-Quote', p_lvl) if p_lvl else '—'
            p_text = f'{p_val:.0f} %' if p_val is not None else 'keine Daten'
            p_chip_pct = {'low':32,'mid':55,'high':78,'vhigh':100}.get(p_lvl, 50) if p_lvl else 0
            rows_html += f'''
            <div class="live-kpi-row">
              <div class="live-kpi-label">PKV-Quote</div>
              <div class="live-kpi-chip-track">
                <div class="live-kpi-chip weg-chip-{p_lvl or 'low'}" style="width:{p_chip_pct}%">
                  <span class="weg-chip-text">{p_label}</span>
                  <span class="weg-chip-range">{p_text}</span>
                </div>
              </div>
              <div class="live-kpi-note">{q_aktuell} bisher · Stichprobe: {fmt_eur(live_kpis['pkv_termine_total'])} Termine</div>
            </div>'''
            # Krankheit
            k_val = live_kpis['krank_tage_pro_th_jahr']
            k_lvl = level_krank(k_val) if k_val is not None else None
            k_label = kpi_level_label('Krankheit', k_lvl) if k_lvl else '—'
            k_text = f'{k_val:.0f} Tg./Jahr' if k_val is not None else '—'
            k_chip_pct = {'low':32,'mid':55,'high':78}.get(k_lvl, 50) if k_lvl else 0
            rows_html += f'''
            <div class="live-kpi-row">
              <div class="live-kpi-label">Krank-Tage/TH/Jahr</div>
              <div class="live-kpi-chip-track">
                <div class="live-kpi-chip weg-chip-{k_lvl or 'low'}" style="width:{k_chip_pct}%">
                  <span class="weg-chip-text">{k_label}</span>
                  <span class="weg-chip-range">{k_text}</span>
                </div>
              </div>
              <div class="live-kpi-note">letzte 90 Tage, aufs Jahr hochgerechnet</div>
            </div>'''

            # €/h Live mit Stufen-Tendenz
            if live_quartal:
                _eur_live = live_quartal['eur60_live']
                _stufe_live = live_quartal['tats_stufe_live']
                # Tendenz-Label vs. Q1-Bewertung
                if _stufe_live > pm['tats_stufe']:
                    _tendenz = f'<span style="color:var(--green);font-weight:700;">↑ auf Kurs Richtung Stufe {_stufe_live}</span>'
                    _chip_class = 'high'; _chip_pct = 88
                elif _stufe_live < pm['tats_stufe']:
                    _tendenz = f'<span style="color:var(--orange);font-weight:700;">↓ aktuell unter Q1-Niveau (Tendenz Stufe {_stufe_live})</span>'
                    _chip_class = 'mid'; _chip_pct = 50
                else:
                    _tendenz = f'<span style="color:var(--teal);font-weight:700;">→ Stufe {_stufe_live} bestätigt</span>'
                    _chip_class = 'high'; _chip_pct = 75
                rows_html += f'''
            <div class="live-kpi-row">
              <div class="live-kpi-label">€/h (Trend)</div>
              <div class="live-kpi-chip-track">
                <div class="live-kpi-chip weg-chip-{_chip_class}" style="width:{_chip_pct}%">
                  <span class="weg-chip-text">{_tendenz}</span>
                  <span class="weg-chip-range">{fmt_eur(_eur_live, 2)} €/h</span>
                </div>
              </div>
              <div class="live-kpi-note">Q-bisher ({live_quartal['wochen_q_bisher']:.1f} Wo, {live_quartal['termine_count']} Termine) · finale Bewertung am Q-Ende</div>
            </div>'''

            aktueller_stand_html = f'''
            <div class="block">
              <div class="block-label">Live</div>
              <div class="block-title">Wo stehst du aktuell ({q_aktuell})?</div>
              <p class="block-intro" style="font-size:12px;margin-bottom:14px;">Orientierung für das laufende Quartal — die finale Bewertung erfolgt nach Q-Abschluss aus den endgültigen Daten.</p>
              <div class="live-kpi-card">
                <div class="live-kpi-header">
                  <div class="live-status">Live</div>
                  <div class="live-kpi-date">Stand: {today_str}</div>
                </div>
                {rows_html}
              </div>
            </div>
            '''

        # Konkrete Wege (Kombinationen von Auslastung, PKV, Krankheit)
        wege_content = render_wege_block(next_s_obj['n'])
        wege_legende = '''
        <div class="weg-legende">
          <div class="weg-legende-title">Was bedeuten die Stufen?</div>
          <div class="weg-legende-row">
            <span class="weg-legende-kpi">Auslastung</span>
            <span class="weg-legende-item mid">mittel <span class="rg">85–92 %</span></span>
            <span class="weg-legende-item high">hoch <span class="rg">93–95 %</span></span>
            <span class="weg-legende-item vhigh">sehr hoch <span class="rg">96 %+</span></span>
          </div>
          <div class="weg-legende-row">
            <span class="weg-legende-kpi">PKV-Quote</span>
            <span class="weg-legende-item low">gering <span class="rg">bis 10 %</span></span>
            <span class="weg-legende-item mid">mittel <span class="rg">11–20 %</span></span>
            <span class="weg-legende-item high">hoch <span class="rg">21–30 %</span></span>
            <span class="weg-legende-item vhigh">sehr hoch <span class="rg">über 30 %</span></span>
          </div>
          <div class="weg-legende-row">
            <span class="weg-legende-kpi">Krankheit</span>
            <span class="weg-legende-item low">wenig <span class="rg">10–15 Tg./a</span></span>
            <span class="weg-legende-item mid">normal <span class="rg">16–20 Tg./a</span></span>
            <span class="weg-legende-item high">höher <span class="rg">21–25 Tg./a</span></span>
          </div>
        </div>
        '''
        # Zufriedenheits-Voraussetzung für die Wege (UND-Bedingung neben den 3 Variablen)
        if pm['zufr'] >= next_s_obj['zufr']:
            zufr_voraussetzung = f'<span style="color:var(--green);font-weight:700;">✓ erreicht ({fmt_de(pm["zufr"])} / 10)</span>'
        else:
            _delta_z = next_s_obj['zufr'] - pm['zufr']
            zufr_voraussetzung = f'<span style="color:var(--orange);font-weight:700;">noch +{fmt_de(_delta_z)} Pkt fehlen ({fmt_de(pm["zufr"])} → {fmt_de(next_s_obj["zufr"])})</span>'

        wege_block_html = f'''
        <div class="block">
          <div class="block-label">Konkrete Wege</div>
          <div class="block-title">Optionen um Stufe {next_s_obj['n']} zu erreichen</div>
          <p class="block-intro">Jeder Weg zeigt eine <strong>realistische</strong> Kombination — schon eine davon reicht für Stufe {next_s_obj['n']}. PKV-Quote ist überall „gering" gesetzt, weil das eurem aktuellen Stand entspricht; eine höhere PKV-Quote macht jeden Weg leichter (siehe Hebel oben).</p>
          <p class="block-intro" style="margin-top:-8px;">Voraussetzung in allen Wegen: Team-Zufriedenheit ≥ {fmt_de(next_s_obj['zufr'])} — {zufr_voraussetzung}.</p>
          {wege_content}
          {wege_legende}
        </div>
        '''

    # Block: Aktion „Wie kommst du auf Stufe N?" — Q-Start + Live-Tendenz + Hebel
    hebel_block_html = ''
    h = hebel_optionen(pm, d, live_kpis)
    # Live-Hebel: hebel_optionen mit eur60_live & verfueg_live aufrufen
    h_live = None
    d_live = None
    if h and live_quartal:
        pm_live_dict = dict(pm)
        pm_live_dict['eur60'] = live_quartal['eur60_live']
        pm_live_dict['verfueg'] = live_quartal['verfueg_live']
        d_live = delta_naechste_stufe(pm_live_dict)
        if d_live and d_live.get('delta_eur60', 0) > 0:
            h_live = hebel_optionen(pm_live_dict, d_live, live_kpis)
    if h:
        TAG_LABEL = {'realistic':'realistisch', 'borderline':'ambitioniert', 'impossible':'alleine nicht möglich'}
        def _tag(lvl): return f'<span class="hebel-tag {lvl}">{TAG_LABEL[lvl]}</span>'
        def _eff(lvl): return '' if lvl == 'realistic' else f' {lvl}'

        # Wenn Live-Hebel verfügbar: Werte daraus, plus Q-Start als Vergleich.
        # Sonst: Q1-Werte wie bisher.
        hsrc = h_live if h_live else h

        pkv_from_to = f'von {hsrc["pkv_now"]:.0f} % auf {hsrc["pkv_neu"]:.0f} %' if hsrc["pkv_now"] else f'auf ca. {hsrc["pkv_neu"]:.0f} %'
        if h_live and h["d_pkv_pkt"] != hsrc["d_pkv_pkt"]:
            pkv_from_to += f' <span style="color:var(--muted);font-size:11px;">(Q-Start: +{h["d_pkv_pkt"]:.0f} %-Pkt)</span>'

        if hsrc["d_termin_pro_th"] is not None and hsrc["anzahl_th"]:
            termin_from_to = f'Bundle-weit · ≈ +{fmt_de(hsrc["d_termin_pro_th"])} Termine/Wo pro Therapeut:in (im Bundle: {hsrc["anzahl_th"]} Therapeut:innen)'
        else:
            termin_from_to = 'Bundle-weit, zusätzlich zu heute'
        if h_live and h["d_termin_wo"] != hsrc["d_termin_wo"]:
            termin_from_to += f' <span style="color:var(--muted);font-size:11px;">(Q-Start: +{h["d_termin_wo"]:.0f}/Wo)</span>'

        krank_unmöglich = bool(hsrc["krank_now"] and hsrc["d_krank_tage"] > hsrc["krank_now"])
        if krank_unmöglich:
            krank_from_to = f'Krankenstand bereits niedrig ({hsrc["krank_now"]:.0f} Tg./TH/Jahr) — als alleiniger Hebel nicht ausreichend.'
        elif hsrc["krank_now"]:
            krank_from_to = f'von {hsrc["krank_now"]:.0f} auf {hsrc["krank_neu"]:.0f} Tg./TH/Jahr'
        else:
            krank_from_to = f'auf ca. {hsrc["krank_neu"]:.0f} Tg./TH/Jahr'
        krank_effect_text = 'reicht alleine nicht' if krank_unmöglich else f'−{hsrc["d_krank_tage"]:.0f} Tage/TH/Jahr'

        # Umsatz-Card: Q-Start vs. Live (zwei Spalten)
        if live_quartal:
            _next_eur = next_s_obj['eur60']
            _live_eur = live_quartal['eur60_live']
            _live_stufe = live_quartal['tats_stufe_live']
            _live_delta_zu_ziel = max(0, _next_eur - _live_eur)
            if _live_eur >= _next_eur:
                _live_color = 'var(--green)'
                _live_text = f'✓ über Schwelle Stufe {next_s_obj["n"]} — Live-Tendenz {_live_stufe}'
            elif _live_eur > pm['eur60']:
                _live_color = 'var(--teal)'
                _live_text = f'fehlen noch +{fmt_eur(_live_delta_zu_ziel, 2)} €/h zu Stufe {next_s_obj["n"]}'
            else:
                _live_color = 'var(--orange)'
                _live_text = f'aktuell unter Q1 — Trend Stufe {_live_stufe}'
            umsatz_card = f'''
      <div class="gap-row" style="border-top:none;padding-top:4px;">
        <div class="gap-row-icon" style="background:var(--teal-light);color:var(--teal);">€</div>
        <div class="gap-row-content">
          <div class="gap-row-title">Umsatz pro Therapie-Stunde</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px;">
            <div>
              <div class="gap-mini-label">Bei Q-Start (Q1-Bewertung)</div>
              <div class="gap-mini-val" style="color:var(--teal);">{fmt_eur(pm['eur60'], 2)} €/h</div>
              <div style="font-size:11px;color:var(--muted);margin-top:4px;">fehlten +{fmt_eur(d['delta_eur60'], 2)} €/h zu Stufe {next_s_obj['n']} ({fmt_eur(_next_eur, 2)} €/h)</div>
            </div>
            <div>
              <div class="gap-mini-label">Live (Q-bisher · {live_quartal['wochen_q_bisher']:.1f} Wo)</div>
              <div class="gap-mini-val" style="color:{_live_color};">{fmt_eur(_live_eur, 2)} €/h</div>
              <div style="font-size:11px;color:{_live_color};margin-top:4px;font-weight:600;">{_live_text}</div>
            </div>
          </div>
        </div>
      </div>'''
        else:
            umsatz_card = umsatz_html

        # Zufriedenheit-Card mit Hinweis
        zufr_card = zufr_html.replace(
            '</div>\n            </div>',
            '</div>\n              <div style="font-size:11px;color:var(--muted);font-style:italic;margin-top:6px;">Wert aus Q1-Umfrage · Live-Update zur Zufriedenheit nicht möglich</div>\n            </div>',
            1
        )

        # Hebel-Headline mit Live-Vergleich
        if h_live:
            hebel_headline = f'Drei Hebel zur Umsatz-Lücke — bei Q-Start: <strong>+{fmt_de(h["delta_pct"])} %</strong>, aktuell live: <strong>+{fmt_de(h_live["delta_pct"])} %</strong> Bundle-Umsatz. Jeder Hebel allein würde reichen, eine Kombination ist meist realistischer (siehe Wege unten).'
        elif live_quartal and live_quartal['eur60_live'] >= next_s_obj['eur60']:
            hebel_headline = f'Live-Stand bereits über Schwelle Stufe {next_s_obj["n"]} — wenn das so weitergeht, wäre die nächste Stufe erreicht. Die Hebel unten zeigen den Q-Start-Stand zur Orientierung.'
        else:
            hebel_headline = f'Drei Hebel zur Umsatz-Lücke (<strong>+{fmt_de(h["delta_pct"])} % Bundle-Umsatz</strong>) — jeder einzeln würde reichen, eine Kombination ist meist realistischer (siehe Wege unten).'

        hebel_block_html = f'''
  <!-- BLOCK „Wie kommst du auf Stufe N?" — Vergleich Q-Start vs. Live -->
  <div class="block">
    <div class="block-label">Aktion</div>
    <div class="block-title">Wie kommst du auf Stufe {next_s_obj['n']}?</div>
    <p class="block-intro">Für Stufe {next_s_obj['n']} müssen <strong>beide</strong> Bedingungen erfüllt sein — Umsatz <strong>und</strong> Team-Zufriedenheit. <em style="color:var(--muted);">Live-Werte sind Orientierung; die finale Bewertung erfolgt am Q-Ende.</em></p>
    <div class="gap-card">
      {umsatz_card}
      {zufr_card}
    </div>
    <p class="hebel-headline" style="margin-top:24px">
      {hebel_headline}
    </p>
    <div class="hebel-grid">
      <div class="hebel-item">
        <div class="hebel-content">
          <div class="hebel-name">Höherer PKV-Anteil {_tag(hsrc["pkv_lvl"])}</div>
          <div class="hebel-desc">Privatpatienten aktiv ansprechen. PKV zahlt {fmt_de(PKV_FAKTOR)}× den GKV-Tarif.</div>
          <div class="hebel-from-to">{pkv_from_to}</div>
        </div>
        <div class="hebel-effect{_eff(hsrc["pkv_lvl"])}">+{hsrc["d_pkv_pkt"]:.0f} %-Pkt PKV</div>
      </div>
      <div class="hebel-item">
        <div class="hebel-content">
          <div class="hebel-name">Mehr Termine pro Woche {_tag(hsrc["termin_lvl"])}</div>
          <div class="hebel-desc">Auslastung erhöhen, neue Patienten gewinnen, Slots besser nutzen.</div>
          <div class="hebel-from-to">{termin_from_to}</div>
        </div>
        <div class="hebel-effect{_eff(hsrc["termin_lvl"])}">+{hsrc["d_termin_wo"]:.0f} Termine/Wo</div>
      </div>
      <div class="hebel-item">
        <div class="hebel-content">
          <div class="hebel-name">Krankenstand senken {_tag(hsrc["krank_lvl"])}</div>
          <div class="hebel-desc">Team-Gesundheit, gute Urlaubsplanung, keine Ansteckungsketten.</div>
          <div class="hebel-from-to">{krank_from_to}</div>
        </div>
        <div class="hebel-effect{_eff(hsrc["krank_lvl"])}">{krank_effect_text}</div>
      </div>
    </div>
    <p class="hebel-note">Lineare Näherungen — Live-Werte zeigen den Stand der ersten Q-Wochen und können sich mit kommenden Urlaubsblöcken noch verschieben. Faktoren: +1 %-Pkt PKV ≈ +{fmt_de(PKV_FAKTOR-1)} % Umsatz · +1 Termin/Wo Bundle ≈ +0,3 % · −1 %-Pkt Krank ≈ +0,5 %. PKV-Tarif {fmt_de(PKV_FAKTOR)}× GKV, 230 Werktage/Jahr.</p>
  </div>'''

    # Timeline: nur bewertete Quartale + laufendes (keine leeren Zukunfts-Karten)
    year = today.year
    q_eval = q_now_num - 1 if q_now_num > 1 else None  # None: Bewertung war Vorjahr-Q4 (selten)
    timeline_cards = []
    end_q = q_now_num  # bis und mit dem laufenden Quartal
    for q in range(1, end_q + 1):
        q_label_card = f"Q{q} {year}"
        if q == q_eval:
            timeline_cards.append(f'''<div class="timeline-item current">
        <div class="timeline-q">{q_label_card}</div>
        <div class="timeline-stufe">Stufe {pm['tats_stufe']}</div>
        <div class="timeline-gehalt">{fmt_eur(pm['monatsgehalt'])} € / Monat</div>
      </div>''')
        elif q == q_now_num:
            timeline_cards.append(f'''<div class="timeline-item empty">
        <div class="timeline-q">{q_label_card}</div>
        <div class="timeline-empty">Laufendes Quartal</div>
      </div>''')
        else:
            timeline_cards.append(f'''<div class="timeline-item empty">
        <div class="timeline-q">{q_label_card}</div>
        <div class="timeline-empty">bewertet</div>
      </div>''')
    timeline_html = '\n      '.join(timeline_cards)

    html_str = f'''<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vacura — Dein Gehalt · {pm['name']}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="container">
  
  <div class="topbar">
    <span class="topbar-name">Vacura · Gehalts-Dashboard</span>
    <span class="topbar-quartal">{q_bewertung}</span>
  </div>

  <h1 class="page-title">Hallo {pm['name']}.</h1>
  <p class="page-subtitle">Hier siehst du, wo du stehst und wie du auf die nächste Stufe kommst.</p>
  
  <!-- BLOCK 1: HERO -->
  <div class="block">
    <div class="hero-card">
      <div class="hero-stufe">{hero_stufe_text}</div>
      <div class="hero-gehalt">{fmt_eur(pm['monatsgehalt'])} €</div>
      <div class="hero-gehalt-unit">Monatsgehalt ab {q_aktuell}</div>
      <div class="hero-meta">
        <div class="hero-meta-item">
          <span class="hero-meta-label">Jahresgehalt</span>
          <span class="hero-meta-value">{fmt_eur(pm['jahresgehalt'])} €</span>
        </div>
        <div class="hero-meta-item">
          <span class="hero-meta-label">Bundle</span>
          <span class="hero-meta-value">{pm['bundle_standorte']}</span>
        </div>
        <div class="hero-meta-item">
          <span class="hero-meta-label">Wochenstunden</span>
          <span class="hero-meta-value">{pm['wochenstd']} h</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- BLOCK 2: BREAKDOWN -->
  <div class="block">
    <div class="block-label">Transparenz</div>
    <div class="block-title">Wie setzt sich dein Gehalt zusammen?</div>
    <div class="breakdown-card">
      <div class="breakdown-formula">
        <strong>Sockel</strong> + <strong>Bundle-Zulage</strong> = <strong>Basis-Gehalt</strong>, davon <strong>+{int(pm['tats_stufe_zulage_pct']*100)} %</strong> Stufen-Zulage
      </div>
      <div class="breakdown-bar">
        <div class="breakdown-seg sockel" style="flex: {sockel_pct:.1f}">Sockel</div>
        <div class="breakdown-seg bundle" style="flex: {bundle_pct:.1f}">Bundle</div>
        <div class="breakdown-seg stufe" style="flex: {stufe_pct:.1f}">+ Stufe {pm['tats_stufe']}</div>
      </div>
      <div class="breakdown-legend">
        <div class="breakdown-legend-item">
          <div class="breakdown-legend-label">Sockel (Vollzeit)</div>
          <div class="breakdown-legend-val">{fmt_eur(40000)} €</div>
        </div>
        <div class="breakdown-legend-item bundle">
          <div class="breakdown-legend-label">Bundle-Zulage (für {pm['th_pm']} Anteile<sup>¹</sup>)</div>
          <div class="breakdown-legend-val">+{fmt_eur(pm['bundle_zulage'])} €</div>
        </div>
        <div class="breakdown-legend-item stufe">
          <div class="breakdown-legend-label">Variable Zulage (+{int(pm['tats_stufe_zulage_pct']*100)} %)</div>
          <div class="breakdown-legend-val">× {fmt_de(1 + pm['tats_stufe_zulage_pct'], 2)}</div>
        </div>
      </div>
      <div class="breakdown-result">
        <span class="breakdown-result-label">→ Jahresgehalt (bei {pm['wochenstd']} h/Woche)</span>
        <span class="breakdown-result-val">{fmt_eur(pm['jahresgehalt'])} €</span>
      </div>
      <p style="font-size:11px;color:var(--muted);margin-top:14px;line-height:1.5;">
        <sup>¹</sup> „Anteile" = anteilige Bundle-Größe für deine Zulage — gewichtet auf deine Wochenstunden und deinen Anteil am Bundle-Team.
      </p>
    </div>
  </div>

  <!-- BLOCK 3: WARUM DIESE STUFE -->
  <div class="block">
    <div class="block-label">Einordnung</div>
    <div class="block-title">Woher kommt deine Stufe?</div>
    <p class="block-intro">Beide Werte müssen gleichzeitig die Schwelle erreichen. Umsatz und Team-Stimmung sind UND-verknüpft.</p>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Dein Umsatz pro Therapie-Stunde</div>
        <div class="kpi-value ok">{fmt_eur(pm['eur60'], 2)} <span class="kpi-unit">€/h</span></div>
        <div class="kpi-schwelle">Schwelle Stufe {pm['tats_stufe']}: <strong>{fmt_eur(curr_s['eur60'], 2)} €/h</strong>{' · Stufe ' + str(next_s['n']) + ': ' + fmt_eur(next_s['eur60'], 2) + ' €/h' if d else ''}</div>
        {_eur_bar_html(pm, curr_s, next_s, d)}
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Team-Zufriedenheit</div>
        <div class="kpi-value ok">{fmt_de(pm['zufr'])} <span class="kpi-unit">/ 10</span></div>
        <div class="kpi-schwelle">Schwelle Stufe {pm['tats_stufe']}: <strong>{fmt_de(curr_s['zufr'])}</strong>{' · Stufe ' + str(next_s['n']) + ': ' + fmt_de(next_s['zufr']) if d else ''}</div>
        {_zufr_bar_html(pm, curr_s, next_s, d)}
        <div class="zufr-breakdown">
          <div class="zufr-breakdown-title">Zusammensetzung (gewichtete Summe der drei Dimensionen)</div>
          <div class="zufr-sub">
            <span class="zufr-sub-label">Rücken freihalten</span>
            <span class="zufr-sub-bar"><span class="zufr-sub-fill" style="width:{pm['ruecken']*10:.0f}%"></span></span>
            <span class="zufr-sub-val">{fmt_de(pm['ruecken'])} <small>· Gewicht 20 %</small></span>
          </div>
          <div class="zufr-sub">
            <span class="zufr-sub-label">Kommunikation</span>
            <span class="zufr-sub-bar"><span class="zufr-sub-fill" style="width:{pm['komm']*10:.0f}%"></span></span>
            <span class="zufr-sub-val">{fmt_de(pm['komm'])} <small>· Gewicht 20 %</small></span>
          </div>
          <div class="zufr-sub">
            <span class="zufr-sub-label">Weiterempfehlung (eNPS)</span>
            <span class="zufr-sub-bar"><span class="zufr-sub-fill" style="width:{pm['enps']*10:.0f}%"></span></span>
            <span class="zufr-sub-val">{fmt_de(pm['enps'])} <small>· Gewicht 60 %</small></span>
          </div>
          <div class="zufr-formel" style="font-size:11px;color:var(--muted);margin-top:10px;padding-top:8px;border-top:1px dashed var(--line);">
            Score = 0,2 × {fmt_de(pm['ruecken'])} + 0,2 × {fmt_de(pm['komm'])} + 0,6 × {fmt_de(pm['enps'])} = <strong>{fmt_de(pm['zufr'])}</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- BLOCK 4: STUFEN-LEITER -->
  <div class="block">
    <div class="block-label">Überblick</div>
    <div class="block-title">Die 6 Stufen</div>
    <div class="stufen-scroll">
      {"".join(stufen_chips)}
    </div>
  </div>
  
  {aktueller_stand_html}

  {next_block}

  {hebel_block_html}

  {wege_block_html}

  <!-- BLOCK 8: TIMELINE -->
  <div class="block">
    <div class="block-label">Verlauf</div>
    <div class="block-title">Deine Entwicklung</div>
    <div class="timeline-grid">
      {timeline_html}
    </div>
  </div>

  <div class="footer">
    Vacura · PM-Gehaltsmodell · Stand {q_bewertung}<br>
    <a href="#top">↑ Nach oben</a>
  </div>
  
</div>
</body>
</html>'''
    return html_str

# ==== MAIN ====
print('Lade Excel...')
wb = openpyxl.load_workbook(EXCEL, data_only=False)
ws_d = wb['Daten']

os.makedirs(OUT_DIR, exist_ok=True)

for pm_cfg in PMS:
    print(f'  {pm_cfg["name"]}...')
    pm_data = compute_pm(ws_d, pm_cfg)
    if not pm_data:
        print(f'    übersprungen (keine Daten)')
        continue
    
    html_out = render_html(pm_data)
    TOKENS = {'Laura': '8278b207ba9e80605ae5f1604d696759', 'Marleen': '0093979f8cf4df0f67ec20b6e35e6beb', 'Luise': '52981192518b734a346928ed713bc015', 'Max': '5051837ce5b8f243f109306f60136f17'}
    token = TOKENS.get(pm_cfg["name"], "")
    out_path = os.path.join(OUT_DIR, f'{pm_cfg["name"].lower()}-{token}.html')
    with open(out_path, 'w') as f:
        f.write(html_out)
    print(f'    → {out_path}  (Stufe {pm_data["tats_stufe"]}, {fmt_eur(pm_data["monatsgehalt"])} €/Monat)')

print('\nFertig.')
