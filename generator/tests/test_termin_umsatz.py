"""Tests für termin_umsatz() — Tarif-Berechnung pro Termin.

Quelle der Tarif-Werte: reference_verguetungswerte.md (Memory)
HB-Reihenfolge (×Faktor erst, dann +Pauschale): METHODE.md Abschnitt 3.2.4
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone
from generate import termin_umsatz, PKV_FAKTOR


def make_termin(dauer_min, verordnungstyp=1, is_hausbesuch=False):
    """Konstruiert einen synthetischen Termin mit gegebener Dauer in Minuten."""
    from datetime import timedelta
    beginn = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    ende = beginn + timedelta(minutes=dauer_min)
    return {
        'beginn': beginn.isoformat(),
        'ende': ende.isoformat(),
        'verordnungstyp': verordnungstyp,
        'is_hausbesuch': is_hausbesuch,
    }


# === Dauer-Stufen GKV (verordnungstyp=1) ===

def test_dauer_20min_gkv():
    assert termin_umsatz(make_termin(20)) == 8.51

def test_dauer_30min_gkv():
    assert termin_umsatz(make_termin(30)) == 56.93

def test_dauer_45min_gkv():
    assert termin_umsatz(make_termin(45)) == 75.91

def test_dauer_60min_gkv():
    assert termin_umsatz(make_termin(60)) == 94.89

def test_dauer_75min_gkv():
    """>60min: 94,89 + ceil((75-60)/15) × 18,98 = 94,89 + 18,98 = 113,87"""
    assert termin_umsatz(make_termin(75)) == 113.87


# === PKV-Faktor (verordnungstyp=2) ===

def test_pkv_30min():
    """56,93 × 1,7 = 96,781"""
    assert abs(termin_umsatz(make_termin(30, verordnungstyp=2)) - 96.781) < 0.01

def test_pkv_60min():
    """94,89 × 1,7 = 161,313"""
    assert abs(termin_umsatz(make_termin(60, verordnungstyp=2)) - 161.313) < 0.01

def test_selbstzahler_45min():
    """SZ (verordnungstyp=3) hat gleichen Faktor wie PKV"""
    sz = termin_umsatz(make_termin(45, verordnungstyp=3))
    pkv = termin_umsatz(make_termin(45, verordnungstyp=2))
    assert sz == pkv

def test_bg_30min():
    """BG (verordnungstyp=4) hat KEINEN PKV-Faktor — gleich wie GKV"""
    bg = termin_umsatz(make_termin(30, verordnungstyp=4))
    gkv = termin_umsatz(make_termin(30, verordnungstyp=1))
    assert bg == gkv


# === Hausbesuch-Pauschale (nach Faktor) ===

def test_hb_gkv_45min():
    """75,91 + 27,56 = 103,47"""
    assert abs(termin_umsatz(make_termin(45, is_hausbesuch=True)) - 103.47) < 0.01

def test_hb_pkv_45min():
    """Pauschale NACH Faktor: 75,91 × 1,7 + 27,56 = 129,047 + 27,56 = 156,607"""
    result = termin_umsatz(make_termin(45, verordnungstyp=2, is_hausbesuch=True))
    assert abs(result - 156.607) < 0.01

def test_hb_pkv_NICHT_pauschale_mal_faktor():
    """Sicherstellen, dass NICHT (basis + 27,56) × Faktor gerechnet wird (alter Bug)"""
    falsch = (75.91 + 27.56) * 1.7   # alte falsche Reihenfolge
    richtig = termin_umsatz(make_termin(45, verordnungstyp=2, is_hausbesuch=True))
    assert richtig < falsch   # neue Reihenfolge ergibt niedrigeren Wert (HB nicht mit-multipliziert)


# === Edge-Cases ===

def test_dauer_0():
    """Dauer 0 → 0 €"""
    t = {'beginn': '2026-04-01T09:00:00Z', 'ende': '2026-04-01T09:00:00Z'}
    assert termin_umsatz(t) == 0.0

def test_fehlende_zeitfelder():
    """Wenn beginn/ende fehlen → 0 €"""
    assert termin_umsatz({}) == 0.0

def test_pkv_faktor_konstante():
    """PKV_FAKTOR ist als Modul-Konstante definiert (für zentrale Änderbarkeit)"""
    assert PKV_FAKTOR == 1.7
