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
EXCEL = os.environ.get('EXCEL_PATH') or os.path.expanduser('~/Desktop/Claude/Github/pm-dashboards/PM_Gehaltsmodell_v18.xlsx')
OUT_DIR = os.environ.get('OUT_DIR') or os.path.expanduser('~/Desktop/Claude/Github/pm-dashboards/v2')

# Stufen
STUFEN = [
    {'n': 1, 'name': 'Basis',         'li': 75.2,  'zufr': 5.0, 'zulage': 0.00, 'eur60': 61.17},
    {'n': 2, 'name': 'Gut',           'li': 81.8,  'zufr': 6.0, 'zulage': 0.11, 'eur60': 66.54},
    {'n': 3, 'name': 'Stark',         'li': 89.3,  'zufr': 7.0, 'zulage': 0.22, 'eur60': 72.64},
    {'n': 4, 'name': 'Sehr stark',    'li': 95.0,  'zufr': 8.0, 'zulage': 0.33, 'eur60': 77.28},
    {'n': 5, 'name': 'Exzellent',     'li': 103.4, 'zufr': 8.5, 'zulage': 0.44, 'eur60': 84.11},
    {'n': 6, 'name': 'Herausragend',  'li': 110.0, 'zufr': 8.5, 'zulage': 0.55, 'eur60': 89.48},
]

# KPI-Level für Wege-Block
KPI_LEVELS = {
    'Auslastung': {
        'mid':   {'text': 'mittel',    'range': '85–92 %'},
        'high':  {'text': 'hoch',      'range': '93–95 %'},
        'vhigh': {'text': 'sehr hoch', 'range': '96 %+'},
    },
    'PKV-Quote': {
        'low':   {'text': 'gering',    'range': '8–18 %'},
        'mid':   {'text': 'mittel',    'range': '19–29 %'},
        'high':  {'text': 'hoch',      'range': '30–39 %'},
        'vhigh': {'text': 'sehr hoch', 'range': '40 %+'},
    },
    'Krankheit': {
        'low':   {'text': 'wenig',     'range': '10–15 Tg./a'},
        'mid':   {'text': 'normal',    'range': '16–20 Tg./a'},
        'high':  {'text': 'höher',     'range': '21–25 Tg./a'},
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
    ziel = verfueg * 0.825 * 0.9 * 103
    li = ist / ziel * 110 / 1.17
    eur60 = ist / verfueg
    zufr = ruecken*0.2 + komm*0.2 + enps*0.6
    
    # Rechn. Stufe
    rechn = 0
    for s in reversed(STUFEN):
        if li >= s['li'] and zufr >= s['zufr']:
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
        'ziel': ziel,
        'li': li,
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
    if val < 19: return 'low'
    if val < 30: return 'mid'
    if val < 40: return 'high'
    return 'vhigh'

def level_krank(val):
    """Krank-Tage/TH/Jahr: 10-15=low, 16-20=mid, 21-25=high"""
    if val is None: return None
    if val < 16: return 'low'
    if val < 21: return 'mid'
    return 'high'

def kpi_level_label(kpi, level):
    if kpi == 'Auslastung':
        return {'low':'niedrig','mid':'mittel','high':'hoch','vhigh':'sehr hoch'}.get(level, '—')
    if kpi == 'PKV-Quote':
        return {'low':'gering','mid':'mittel','high':'hoch','vhigh':'sehr hoch'}.get(level, '—')
    if kpi == 'Krankheit':
        return {'low':'wenig','mid':'normal','high':'höher'}.get(level, '—')
    return '—'

def render_html(pm):
    d = delta_naechste_stufe(pm)
    
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
          <div class="stufe-chip-detail">€/h ≥ {fmt_eur(s['eur60'], 2)}<br>Zufriedenheit ≥ {s['zufr']:.1f}<br>+{int(s['zulage']*100)}% Zulage</div>
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
                <div class="gap-row-detail">Du hast {pm['zufr']:.1f} / 10, Schwelle für Stufe {next_s_obj['n']}: {next_s_obj['zufr']:.1f}</div>
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
                    <div class="gap-mini-val">+{delta_zufr:.1f} Punkte</div>
                  </div>
                  <div class="gap-mini">
                    <div class="gap-mini-label">Ziel</div>
                    <div class="gap-mini-val">{next_s_obj['zufr']:.1f} / 10</div>
                  </div>
                </div>
                <div class="gap-bar"><div class="gap-bar-fill" style="width: {zufr_progress:.0f}%"></div></div>
                <div class="gap-bar-caption">{pm['zufr']:.1f} → {next_s_obj['zufr']:.1f}</div>
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
        live_kpis = None
        aktueller_stand_html = ''
        try:
            bundle_std_list = [s.strip().lower().replace(' ', '_') for s in pm.get('bundle_standorte','').split(',')]
            # Normalize back mapping
            bundle_std_list = ['prenzlauer_berg' if s == 'prenzlauer_berg' else s for s in bundle_std_list]
            live_kpis = compute_live_kpis(bundle_std_list)
        except Exception as _e:
            print(f'    (Live-KPIs-Fehler {pm["name"]}: {_e})')

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
              <div class="live-kpi-note">Q2 2026 bisher ({live_kpis['pkv_termine_total']} Termine)</div>
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

            aktueller_stand_html = f'''
            <div class="block">
              <div class="block-label">Live</div>
              <div class="block-title">Wo stehst du aktuell (Q2 2026)?</div>
              <div class="live-kpi-card">
                <div class="live-kpi-header">
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
            <span class="weg-legende-item low">gering <span class="rg">8–18 %</span></span>
            <span class="weg-legende-item mid">mittel <span class="rg">19–29 %</span></span>
            <span class="weg-legende-item high">hoch <span class="rg">30–39 %</span></span>
            <span class="weg-legende-item vhigh">sehr hoch <span class="rg">40 %+</span></span>
          </div>
          <div class="weg-legende-row">
            <span class="weg-legende-kpi">Krankheit</span>
            <span class="weg-legende-item low">wenig <span class="rg">10–15 Tg./a</span></span>
            <span class="weg-legende-item mid">normal <span class="rg">16–20 Tg./a</span></span>
            <span class="weg-legende-item high">höher <span class="rg">21–25 Tg./a</span></span>
          </div>
        </div>
        '''
        wege_block_html = f'''
        <div class="block">
          <div class="block-label">Konkrete Wege</div>
          <div class="block-title">Optionen um Stufe {next_s_obj['n']} zu erreichen</div>
          <p class="block-intro">Jeder Weg ist eine mögliche Kombination aus Auslastung, PKV-Quote und Krankenstand. Schon eine dieser Kombinationen reicht.</p>
          {wege_content}
          {wege_legende}
        </div>
        '''

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
    <span class="topbar-quartal">Q1 2026</span>
  </div>
  
  <h1 class="page-title">Hallo {pm['name']}.</h1>
  <p class="page-subtitle">Dein Stand nach Q1 2026 und was das für Q2 bedeutet.</p>
  
  <!-- BLOCK 1: HERO -->
  <div class="block">
    <div class="hero-card">
      <div class="hero-stufe">{hero_stufe_text}</div>
      <div class="hero-gehalt">{fmt_eur(pm['monatsgehalt'])} €</div>
      <div class="hero-gehalt-unit">Monatsgehalt ab Q2 2026</div>
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
        <strong>Sockel</strong> + <strong>Bundle-Zulage</strong> = <strong>Basis-Gehalt</strong>, davon <strong>+{int(pm['tats_stufe_zulage_pct']*100)}%</strong> Stufen-Zulage
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
          <div class="breakdown-legend-label">Bundle-Zulage ({pm['th_pm']} TH-Äqui)</div>
          <div class="breakdown-legend-val">+{fmt_eur(pm['bundle_zulage'])} €</div>
        </div>
        <div class="breakdown-legend-item stufe">
          <div class="breakdown-legend-label">Variable Zulage (+{int(pm['tats_stufe_zulage_pct']*100)}%)</div>
          <div class="breakdown-legend-val">× {1 + pm['tats_stufe_zulage_pct']:.2f}</div>
        </div>
      </div>
      <div class="breakdown-result">
        <span class="breakdown-result-label">→ Jahresgehalt (bei {pm['wochenstd']} h/Woche)</span>
        <span class="breakdown-result-val">{fmt_eur(pm['jahresgehalt'])} €</span>
      </div>
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
        <div class="kpi-bar"><div class="kpi-bar-fill {'over' if pm['eur60'] >= curr_s['eur60'] else 'under'}" style="width: {min(100, pm['eur60']/next_s['eur60']*100):.0f}%"></div></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Team-Zufriedenheit</div>
        <div class="kpi-value ok">{pm['zufr']:.1f} <span class="kpi-unit">/ 10</span></div>
        <div class="kpi-schwelle">Schwelle Stufe {pm['tats_stufe']}: <strong>{curr_s['zufr']:.1f}</strong>{' · Stufe ' + str(next_s['n']) + ': ' + f"{next_s['zufr']:.1f}" if d else ''}</div>
        <div class="kpi-bar"><div class="kpi-bar-fill {'over' if pm['zufr'] >= curr_s['zufr'] else 'under'}" style="width: {min(100, pm['zufr']/max(next_s['zufr'],0.1)*100):.0f}%"></div></div>
        <div class="zufr-breakdown">
          <div class="zufr-breakdown-title">So setzt sich der Score zusammen</div>
          <div class="zufr-sub">
            <span class="zufr-sub-label">Rücken freihalten</span>
            <span class="zufr-sub-bar"><span class="zufr-sub-fill" style="width:{pm['ruecken']*10:.0f}%"></span></span>
            <span class="zufr-sub-val">{pm['ruecken']:.1f} <small>× 20 %</small></span>
          </div>
          <div class="zufr-sub">
            <span class="zufr-sub-label">Kommunikation</span>
            <span class="zufr-sub-bar"><span class="zufr-sub-fill" style="width:{pm['komm']*10:.0f}%"></span></span>
            <span class="zufr-sub-val">{pm['komm']:.1f} <small>× 20 %</small></span>
          </div>
          <div class="zufr-sub">
            <span class="zufr-sub-label">Weiterempfehlung (eNPS)</span>
            <span class="zufr-sub-bar"><span class="zufr-sub-fill" style="width:{pm['enps']*10:.0f}%"></span></span>
            <span class="zufr-sub-val">{pm['enps']:.1f} <small>× 60 %</small></span>
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
  
  {next_block}
  
  {gap_block}

  {aktueller_stand_html}

  {wege_block_html}

  <!-- BLOCK 7: HEBEL -->
  <div class="block">
    <div class="block-label">Aktion</div>
    <div class="block-title">Wie kommst du weiter?</div>
    <div class="hebel-grid">
      <div class="hebel-item">
        <div class="hebel-content">
          <div class="hebel-name">Mehr Termine pro Woche</div>
          <div class="hebel-desc">Auslastung erhöhen, neue Patienten gewinnen, Slots besser nutzen.</div>
        </div>
        <div class="hebel-effect">+10 Termine/Wo<br>≈ +3 % Umsatz</div>
      </div>
      <div class="hebel-item">
        <div class="hebel-content">
          <div class="hebel-name">Höherer PKV-Anteil</div>
          <div class="hebel-desc">Privatpatienten aktiv ansprechen. PKV zahlt 1,7× den GKV-Tarif.</div>
        </div>
        <div class="hebel-effect">+1 %-Pkt PKV<br>≈ +0,7 % Umsatz</div>
      </div>
      <div class="hebel-item">
        <div class="hebel-content">
          <div class="hebel-name">Krankenstand senken</div>
          <div class="hebel-desc">Team-Gesundheit, gute Urlaubsplanung, keine Ansteckungsketten.</div>
        </div>
        <div class="hebel-effect">−1 %-Pkt Krank<br>≈ +0,5 % Umsatz</div>
      </div>
    </div>
    <p class="hebel-note">Orientierungswerte — keine exakten Prognosen.</p>
  </div>
  
  <!-- BLOCK 8: TIMELINE -->
  <div class="block">
    <div class="block-label">Verlauf</div>
    <div class="block-title">Deine Entwicklung</div>
    <div class="timeline-grid">
      <div class="timeline-item current">
        <div class="timeline-q">Q1 2026</div>
        <div class="timeline-stufe">Stufe {pm['tats_stufe']}</div>
        <div class="timeline-gehalt">{fmt_eur(pm['monatsgehalt'])} € / Monat</div>
      </div>
      <div class="timeline-item empty">
        <div class="timeline-q">Q2 2026</div>
        <div class="timeline-empty">Laufendes Quartal</div>
      </div>
      <div class="timeline-item empty">
        <div class="timeline-q">Q3 2026</div>
        <div class="timeline-empty">noch offen</div>
      </div>
      <div class="timeline-item empty">
        <div class="timeline-q">Q4 2026</div>
        <div class="timeline-empty">noch offen</div>
      </div>
    </div>
  </div>
  
  <div class="footer">
    Vacura · PM-Gehaltsmodell · Stand Q1 2026<br>
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
