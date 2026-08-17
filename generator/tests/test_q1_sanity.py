"""Integration-Tests gegen historische Q1-2026-Werte.

Schützt vor Regression beim Code-Refactoring: die Q1-Werte aus dem Excel müssen
nach jeder Code-Änderung weiterhin identisch geladen werden — sonst kippt die
historische Bewertung.

Erwartete Werte sind aus Memory v17 (`project_gehaltsmodell_teamzufriedenheit.md`)
und aus dem aktuellen Excel `Daten`-Tab.

Diese Tests brauchen das Excel — werden übersprungen wenn es fehlt.
"""
import sys, os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

EXCEL_PATH = os.path.expanduser('~/Code/Claude/Projekte/Gehaltsmodelle/Praxismanagement/PM_Gehaltsmodell.xlsx')


@pytest.fixture(scope='module')
def excel_wb():
    if not os.path.exists(EXCEL_PATH):
        pytest.skip(f'Excel-Datei nicht vorhanden: {EXCEL_PATH}')
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=False)
    from generate import load_stufen_aus_excel, load_pms_from_excel
    load_stufen_aus_excel(wb)
    load_pms_from_excel(wb)
    return wb


@pytest.fixture
def pms_config(excel_wb):
    """Abhängig von excel_wb, damit load_pms_from_excel() vorher lief."""
    from generate import PMS
    return {p['name']: p for p in PMS}


# === Q1 IST-Werte (historisch eingefroren im Excel) ===

def test_q1_ist_laura(excel_wb, pms_config):
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Laura'])
    assert pm is not None
    assert pm['ist'] == 291941, f"Lauras Q1-IST muss 291.941 € sein (Memory v17), ist {pm['ist']}"

def test_q1_ist_marleen(excel_wb, pms_config):
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Marleen'])
    assert pm is not None
    assert pm['ist'] == 337924, f"Marleens Q1-IST muss 337.924 € sein (Memory v17), ist {pm['ist']}"


# === Q1 €/h (= IST / verfueg) ===

def test_q1_eur60_laura(excel_wb, pms_config):
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Laura'])
    assert abs(pm['eur60'] - 70.66) < 0.05, f"Laura Q1 €/h 70,66 erwartet, ist {pm['eur60']:.2f}"

def test_q1_eur60_marleen(excel_wb, pms_config):
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Marleen'])
    assert abs(pm['eur60'] - 66.92) < 0.05, f"Marleen Q1 €/h 66,92 erwartet, ist {pm['eur60']:.2f}"


# === Q1 Stufen-Bewertung ===

def test_q1_stufe_laura(excel_wb, pms_config):
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Laura'])
    assert pm['tats_stufe'] == 2, f"Laura Q1 Stufe 2 erwartet, ist {pm['tats_stufe']}"

def test_q1_stufe_marleen(excel_wb, pms_config):
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Marleen'])
    assert pm['tats_stufe'] == 2, f"Marleen Q1 Stufe 2 erwartet, ist {pm['tats_stufe']}"


# === Probezeit-Regel ===

def test_q1_luise_probezeit(excel_wb, pms_config):
    """Luise hat startdatum 2026-02-01 → bei Q1-Ende 31.3. erst 2 Monate beschäftigt → Probezeit."""
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Luise'])
    assert pm['probezeit_aktiv'] is True, "Luise muss in Probezeit sein"
    assert pm['tats_stufe'] == 1, "Stufe muss auf 1 fixiert sein"
    assert pm['bundle_zulage'] == 0, "Bundle-Zulage muss 0 € sein"

def test_q1_max_probezeit(excel_wb, pms_config):
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Max'])
    assert pm['probezeit_aktiv'] is True
    assert pm['tats_stufe'] == 1
    assert pm['bundle_zulage'] == 0


# === Zufriedenheits-Score (Gewichtung Rücken×0.2 + Komm×0.2 + eNPS×0.6) ===

def test_marleen_zufr_score(excel_wb, pms_config):
    """Marleen: Rücken=8.5, Komm=8.7, eNPS=8 → Score = 0.2×8.5 + 0.2×8.7 + 0.6×8 = 8.24"""
    from generate import compute_pm
    pm = compute_pm(excel_wb, pms_config['Marleen'])
    expected = 0.2 * 8.5 + 0.2 * 8.7 + 0.6 * 8
    assert abs(pm['zufr'] - expected) < 0.01


# === Stufen-Schwellen aus Excel geladen ===

def test_stufen_aus_excel_geladen(excel_wb):
    """Stufen-Tab im Excel ist die Quelle der Wahrheit."""
    from generate import STUFEN
    assert len(STUFEN) == 6
    # Schwellen-Spot-Check
    assert STUFEN[0]['eur60'] == 61.17
    assert STUFEN[1]['eur60'] == 66.54
    assert STUFEN[2]['eur60'] == 72.64
    assert STUFEN[5]['eur60'] == 89.48
    assert STUFEN[0]['zufr'] == 5.0
    assert STUFEN[5]['zufr'] == 8.5


# === Probezeit-Ende innerhalb des Quartals (Regel 17.08.2026) ===

def test_q2_luise_max_nach_probezeit_stichtag(excel_wb, pms_config):
    """Q2-Bewertung fiel in die Probezeit (bis 31.07.2026). Stichtag 01.07.: Probezeit,
    Stufe 1, keine Bundle-Zulage. Stichtag 17.08.: reguläres Gehalt ab 01.08. — Stufe 2
    (rechn 2, ±1 ab Stufe 1), Bundle-Zulage > 0 (bzw. Fallback-Pfad ohne NocoDB)."""
    from datetime import date
    from generate import compute_pm
    for name in ('Luise', 'Max'):
        pm_pz = compute_pm(excel_wb, pms_config[name], q_label='Q2 2026', stichtag=date(2026, 7, 1))
        assert pm_pz is not None
        assert pm_pz['probezeit_aktiv'] is True and pm_pz['tats_stufe'] == 1 and pm_pz['bundle_zulage'] == 0
        pm_reg = compute_pm(excel_wb, pms_config[name], q_label='Q2 2026', stichtag=date(2026, 8, 17))
        assert pm_reg['probezeit_aktiv'] is False and pm_reg['nach_probezeit'] is True
        assert pm_reg['probezeit_ende'] == date(2026, 7, 31)
        assert pm_reg['gehalt_ab'] == date(2026, 8, 1)
        assert pm_reg['rechn_stufe'] == 2 and pm_reg['tats_stufe'] == 2
        assert pm_reg['monatsgehalt'] > pm_pz['monatsgehalt']

def test_q2_laura_stichtag_ohne_effekt(excel_wb, pms_config):
    """PMs ohne Probezeit: Stichtag ändert nichts an der Bewertung."""
    from datetime import date
    from generate import compute_pm
    a = compute_pm(excel_wb, pms_config['Laura'], q_label='Q2 2026')
    b = compute_pm(excel_wb, pms_config['Laura'], q_label='Q2 2026', stichtag=date(2026, 8, 17))
    assert a['tats_stufe'] == b['tats_stufe'] == 2 and a['nach_probezeit'] is False and b['nach_probezeit'] is False
