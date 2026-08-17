"""Probezeit-Ende innerhalb des Quartals (Valentin 17.08.2026): das Gehalt wird ab dem
Folgetag des Probezeit-Endes angepasst — Stufe aus dem zuletzt bewerteten Quartal
(±1 ab Stufe 1) plus Bundle-Zulage —, nicht erst ab dem Folgequartal.
Reine Unit-Tests ohne NocoDB/Excel."""
import sys, os
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from generate import probezeit_ende, stufe_nach_probezeit, is_probezeit


def test_probezeit_ende_monatserster():
    assert probezeit_ende('2026-02-01') == date(2026, 7, 31)      # Luise, Max
    assert probezeit_ende(date(2026, 7, 1)) == date(2026, 12, 31)  # Emily

def test_probezeit_ende_mitte_monat_und_monatsende():
    assert probezeit_ende('2026-02-15') == date(2026, 8, 14)
    assert probezeit_ende('2025-08-31') == date(2026, 2, 28)       # 31.08. + 6 M → Feb hat keinen 31.
    assert probezeit_ende(None) is None

def test_is_probezeit_konsistent_zum_ende():
    # Q2-Ende: noch Probezeit; Q3-Ende: nicht mehr
    assert is_probezeit('2026-02-01', date(2026, 6, 30)) is True
    assert is_probezeit('2026-02-01', date(2026, 9, 30)) is False

def test_stufe_nach_probezeit_deckel():
    assert stufe_nach_probezeit(2) == 2      # Luise/Max Q2: rechn 2 → Stufe 2
    assert stufe_nach_probezeit(4) == 2      # max. ein Schritt über Probezeit-Stufe 1
    assert stufe_nach_probezeit(1) == 1
    assert stufe_nach_probezeit(0) == 1      # keine Schwelle erreicht → Stufe 1
    assert stufe_nach_probezeit(None) == 1


def test_gehalt_berechnen_und_vorschau():
    from generate import gehalt_berechnen, probezeit_vorschau
    from datetime import date
    # Max: 30 h, Mindestgehalt 40.000, 6 Anteile (1.800), Stufe 2 → 2.900 €/Mon
    g = gehalt_berechnen(30, 40000, 1800, 2)
    assert g['monatsgehalt'] == 2900 and g['jahresgehalt'] == 34799
    # Stufe 1 mit Bundle-Zulage: 41.800 × 0,75 / 12 = 2.612,50 → kaufmännisch 2.613
    assert gehalt_berechnen(30, 40000, 1800, 1)['monatsgehalt'] == 2613
    # Mindestgehalt greift: Probezeit-Sockel 40 h ohne Zulage
    assert gehalt_berechnen(40, 40000, 0, 1)['monatsgehalt'] == 3333
    v = probezeit_vorschau({'wochenstd': 40, 'mindestgehalt': 40000}, 2, 9, date(2026, 8, 1))
    assert v['tats_stufe'] == 2 and v['bundle_zulage'] == 3000 and v['monatsgehalt'] == 3978
    v4 = probezeit_vorschau({'wochenstd': 40, 'mindestgehalt': 40000}, 4, 9, date(2026, 8, 1))
    assert v4['tats_stufe'] == 2   # Deckel: höchstens eine Stufe über Probezeit-Stufe 1
