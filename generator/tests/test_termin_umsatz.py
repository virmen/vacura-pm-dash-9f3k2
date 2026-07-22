"""Tests für termin_umsatz() — ZI-Systematik (Stand 22.07.2026).

Systematik: (round(Dauer/15) + 1 VNB-ZI) × 18,98 €. Thermische Anwendung/KT/WT
pauschal 8,51 €. PKV ×2,0, Selbstzahler ×1,7, HB-Pauschale +27,56 (nach Faktor).
+4,11 % ab 01.07.2026. Backtest vs. MediFox Q1+Q2 2026: −4,4 bis +1,7 %.
HB-Reihenfolge (×Faktor erst, dann +Pauschale): METHODE.md Abschnitt 3.2.4
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone
from generate import termin_umsatz, PKV_FAKTOR, SZ_FAKTOR, ZI_PREIS


def make_termin(dauer_min, verordnungstyp=1, is_hausbesuch=False,
                bezeichnung='Motorisch-funkt. Beh.', datum=(2026, 4, 1)):
    """Konstruiert einen synthetischen Termin mit gegebener Dauer in Minuten."""
    from datetime import timedelta
    beginn = datetime(*datum, 9, 0, tzinfo=timezone.utc)
    ende = beginn + timedelta(minutes=dauer_min)
    return {
        'beginn': beginn.isoformat(),
        'ende': ende.isoformat(),
        'verordnungstyp': verordnungstyp,
        'is_hausbesuch': is_hausbesuch,
        'bezeichnung': bezeichnung,
    }


# === ZI-Staffel GKV (verordnungstyp=1): Dauer/15 + 1 VNB-ZI ===

def test_dauer_30min_gkv():
    """motorisch 30 min = Regeldauer: 56,93"""
    assert abs(termin_umsatz(make_termin(30)) - 56.93) < 0.01

def test_dauer_45min_gkv():
    """motorisch 45 min: 56,93 × 45/30 = 85,40 (Therapieart-linear, V3-Preisform)"""
    assert abs(termin_umsatz(make_termin(45)) - 56.93 * 45 / 30) < 0.01

def test_dauer_60min_gkv():
    """motorisch 60 min: 56,93 × 60/30 = 113,86"""
    assert abs(termin_umsatz(make_termin(60)) - 56.93 * 2) < 0.01

def test_sensomot_45min_gkv():
    """sensomotorisch 45 min = Regeldauer: 75,91"""
    assert abs(termin_umsatz(make_termin(45, bezeichnung='Sensomot.-perzept. Beh.')) - 75.91) < 0.01

def test_fallback_ohne_art_45min():
    """ohne erkennbare Therapieart: ZI-Staffel 4 × 18,98"""
    assert abs(termin_umsatz(make_termin(45, bezeichnung='')) - 4 * ZI_PREIS) < 0.01

def test_dauer_75min_gkv():
    """motorisch 75 min: 56,93 × 75/30 = 142,33"""
    assert abs(termin_umsatz(make_termin(75)) - 56.93 * 75 / 30) < 0.01

def test_dauer_20min_gkv():
    """motorisch 20 min: 56,93 × 20/30 = 37,95"""
    assert abs(termin_umsatz(make_termin(20)) - 56.93 * 20 / 30) < 0.01


# === Thermische Anwendung: immer 8,51 € ===

def test_thermisch_pauschal():
    t = make_termin(30, bezeichnung='Thermische Anwendung, Kälte/Wärme')
    assert abs(termin_umsatz(t) - 8.51) < 0.01

def test_thermisch_unabhaengig_von_dauer():
    kurz = make_termin(15, bezeichnung='Thermische Anwendung, Kälte/Wärme')
    lang = make_termin(45, bezeichnung='Thermische Anwendung, Kälte/Wärme')
    assert termin_umsatz(kurz) == termin_umsatz(lang)


# === Faktoren: PKV ×2,0 · Selbstzahler ×1,7 · BG wie GKV ===

def test_pkv_30min():
    """motorisch 30 × 2,0 = 113,86"""
    assert abs(termin_umsatz(make_termin(30, verordnungstyp=2)) - 56.93 * 2.0) < 0.01

def test_selbstzahler_45min():
    """SZ (verordnungstyp=3) ×1,7 — NICHT gleich PKV (×2,0)"""
    sz = termin_umsatz(make_termin(45, verordnungstyp=3))
    pkv = termin_umsatz(make_termin(45, verordnungstyp=2))
    assert abs(sz - 56.93 * 45 / 30 * 1.7) < 0.01
    assert pkv > sz

def test_bg_30min():
    """BG (verordnungstyp=4) hat KEINEN Faktor — gleich wie GKV"""
    bg = termin_umsatz(make_termin(30, verordnungstyp=4))
    gkv = termin_umsatz(make_termin(30, verordnungstyp=1))
    assert bg == gkv


# === Hausbesuch-Pauschale (nach Faktor) ===

def test_hb_gkv_45min():
    """85,40 + 27,56 = 112,96"""
    assert abs(termin_umsatz(make_termin(45, is_hausbesuch=True)) - (56.93 * 45 / 30 + 27.56)) < 0.01

def test_hb_pkv_45min():
    """Pauschale NACH Faktor: 85,40 × 2,0 + 27,56"""
    result = termin_umsatz(make_termin(45, verordnungstyp=2, is_hausbesuch=True))
    assert abs(result - (56.93 * 45 / 30 * 2.0 + 27.56)) < 0.01

def test_hb_pkv_NICHT_pauschale_mal_faktor():
    """Sicherstellen, dass NICHT (basis + 27,56) × Faktor gerechnet wird (alter Bug)"""
    falsch = (56.93 * 45 / 30 + 27.56) * 2.0
    richtig = termin_umsatz(make_termin(45, verordnungstyp=2, is_hausbesuch=True))
    assert richtig < falsch


# === GKV-Erhöhung +4,11 % ab 01.07.2026 ===

def test_erhoehung_ab_juli():
    """Behandlung am 01.07.2026: 3 ZI × 18,98 × 1,0411"""
    t = make_termin(30, datum=(2026, 7, 1))
    assert abs(termin_umsatz(t) - 56.93 * 1.0411) < 0.01

def test_keine_erhoehung_vor_juli():
    t = make_termin(30, datum=(2026, 6, 30))
    assert abs(termin_umsatz(t) - 56.93) < 0.01


# === Edge-Cases ===

def test_dauer_0():
    """Dauer 0 → 0 €"""
    t = {'beginn': '2026-04-01T09:00:00Z', 'ende': '2026-04-01T09:00:00Z'}
    assert termin_umsatz(t) == 0.0

def test_fehlende_zeitfelder():
    """Wenn beginn/ende fehlen → 0 €"""
    assert termin_umsatz({}) == 0.0

def test_faktor_konstanten():
    """PKV 2,0 / SZ 1,7 als Modul-Konstanten (Kalibrierung Monatsumsatz-Report V3)"""
    assert PKV_FAKTOR == 2.0
    assert SZ_FAKTOR == 1.7


# === Schwellen-Indexierung (§ 4 Abs. 6 Anpassungsvereinbarung) ===

def test_schwellen_vor_juli_unveraendert():
    from generate import stufen_eff, STUFEN
    assert stufen_eff('2026-04-01') is STUFEN

def test_schwellen_ab_juli_indexiert():
    from generate import stufen_eff
    neu = stufen_eff('2026-07-01')
    assert abs(neu[1]['eur60'] - 69.27) < 0.01   # 66,54 × 1,0411
    assert abs(neu[2]['eur60'] - 75.63) < 0.01   # 72,64 × 1,0411
    assert neu[1]['zufr'] == 6.0                  # Zufr-Schwellen unverändert
    assert neu[1]['zulage'] == 0.11               # Zulage-% unverändert
