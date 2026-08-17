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
