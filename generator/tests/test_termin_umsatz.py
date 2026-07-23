"""Tests für termin_umsatz() — finale ZI-Systematik (Entscheidung 22.07.2026 abends).

Behandlung = (round(Dauer/15) + 1 VNB-ZI) × 18,98 € — für alle Therapiearten.
Festpreis-Ausnahmen: thermisch/KT/WT 8,51 €, Gruppen, Analyse, Bericht.
PKV ×2,0, Selbstzahler ×1,7, HB-Pauschale +27,56 (nach Faktor), +4,11 % ab 01.07.2026.
HB-Reihenfolge (×Faktor erst, dann +Pauschale): METHODE.md Abschnitt 3.2.4
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone
from generate import termin_umsatz, PKV_FAKTOR, SZ_FAKTOR, ZI_PREIS


def make_termin(dauer_min, verordnungstyp=1, is_hausbesuch=False,
                bezeichnung='Motorisch-funkt. Beh.', datum=(2026, 4, 1)):
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


# === ZI-Systematik: Dauer/15 + 1 VNB-ZI, therapieart-unabhängig ===

def test_dauer_30min():
    """2 + 1 = 3 ZI = 56,94"""
    assert abs(termin_umsatz(make_termin(30)) - 3 * ZI_PREIS) < 0.01

def test_dauer_45min():
    """3 + 1 = 4 ZI = 75,92 — NICHT therapieartlinear 85,40"""
    assert abs(termin_umsatz(make_termin(45)) - 4 * ZI_PREIS) < 0.01

def test_dauer_60min():
    """4 + 1 = 5 ZI = 94,90"""
    assert abs(termin_umsatz(make_termin(60)) - 5 * ZI_PREIS) < 0.01

def test_dauer_120min():
    """8 + 1 = 9 ZI = 170,82 (Valentins Referenzbeispiel)"""
    assert abs(termin_umsatz(make_termin(120)) - 9 * ZI_PREIS) < 0.01

def test_sensomot_gleich_motorisch():
    """Therapieart ändert den Behandlungspreis nicht — nur die Dauer zählt"""
    a = termin_umsatz(make_termin(45, bezeichnung='Sensomot.-perzept. Beh.'))
    b = termin_umsatz(make_termin(45, bezeichnung='Motorisch-funkt. Beh.'))
    assert a == b


# === Festpreis-Ausnahmen ===

def test_thermisch_pauschal():
    t = make_termin(30, bezeichnung='Thermische Anwendung, Kälte/Wärme')
    assert abs(termin_umsatz(t) - 8.51) < 0.01

def test_gruppe_festpreis():
    t = make_termin(60, bezeichnung='Gruppenbehandlung sensomotorisch')
    assert abs(termin_umsatz(t) - 26.57) < 0.01

def test_bericht_festpreis():
    t = make_termin(10, bezeichnung='Übermittlung Bericht an Arzt')
    assert abs(termin_umsatz(t) - 1.20) < 0.01


# === Faktoren ===

def test_pkv_30min():
    """3 ZI × 2,0"""
    assert abs(termin_umsatz(make_termin(30, verordnungstyp=2)) - 3 * ZI_PREIS * 2.0) < 0.01

def test_selbstzahler_45min():
    sz = termin_umsatz(make_termin(45, verordnungstyp=3))
    pkv = termin_umsatz(make_termin(45, verordnungstyp=2))
    assert abs(sz - 4 * ZI_PREIS * 1.7) < 0.01
    assert pkv > sz

def test_bg_wie_gkv():
    assert termin_umsatz(make_termin(30, verordnungstyp=4)) == termin_umsatz(make_termin(30, verordnungstyp=1))


# === Hausbesuch (Pauschale nach Faktor) ===

def test_hb_gkv_45min():
    assert abs(termin_umsatz(make_termin(45, is_hausbesuch=True)) - (4 * ZI_PREIS + 27.56)) < 0.01

def test_hb_pkv_45min():
    result = termin_umsatz(make_termin(45, verordnungstyp=2, is_hausbesuch=True))
    assert abs(result - (4 * ZI_PREIS * 2.0 + 27.56)) < 0.01

def test_hb_pkv_NICHT_pauschale_mal_faktor():
    falsch = (4 * ZI_PREIS + 27.56) * 2.0
    assert termin_umsatz(make_termin(45, verordnungstyp=2, is_hausbesuch=True)) < falsch


# === +4,11 % ab 01.07.2026 ===

def test_erhoehung_ab_juli():
    t = make_termin(30, datum=(2026, 7, 1))
    assert abs(termin_umsatz(t) - 3 * ZI_PREIS * 1.0411) < 0.01

def test_keine_erhoehung_vor_juli():
    t = make_termin(30, datum=(2026, 6, 30))
    assert abs(termin_umsatz(t) - 3 * ZI_PREIS) < 0.01


# === Edge-Cases ===

def test_dauer_0():
    t = {'beginn': '2026-04-01T09:00:00Z', 'ende': '2026-04-01T09:00:00Z'}
    assert termin_umsatz(t) == 0.0

def test_fehlende_zeitfelder():
    assert termin_umsatz({}) == 0.0

def test_faktor_konstanten():
    assert PKV_FAKTOR == 2.0
    assert SZ_FAKTOR == 1.7


# === Schwellen-Indexierung (§ 4 Abs. 6 Anpassungsvereinbarung) ===

def test_schwellen_vor_juli_unveraendert():
    from generate import stufen_eff, STUFEN
    assert stufen_eff('2026-04-01') is STUFEN

def test_schwellen_ab_juli_indexiert():
    from generate import stufen_eff
    neu = stufen_eff('2026-07-01')
    assert abs(neu[1]['eur60'] - 69.27) < 0.01
    assert abs(neu[2]['eur60'] - 75.63) < 0.01
    assert neu[1]['zufr'] == 6.0
    assert neu[1]['zulage'] == 0.11


# === Pauschal-Leistungen: Integration 152,32 / Schiene 390 (Valentin 23.07.2026) ===

def test_einzelbehandlung_bei_integrationsberatung_festpreis():
    """Auch „…Einzelbehandlung bei Beratung zur Integration…" = 152,32-Festpreis, NICHT ZI"""
    t = make_termin(45, bezeichnung='Motorisch-funktionelle Behandlung: Einzelbehandlung bei Beratung zur Integration in das soziale Umfeld')
    assert abs(termin_umsatz(t) - 152.32) < 0.01

def test_reine_integrationsberatung_festpreis():
    t = make_termin(60, bezeichnung='Integrationsberatung')
    assert abs(termin_umsatz(t) - 152.32) < 0.01

def test_schiene_pauschale():
    from generate import SCHIENEN_PAUSCHALE
    t = make_termin(30, bezeichnung='Ergo. Schiene')
    assert abs(termin_umsatz(t) - SCHIENEN_PAUSCHALE) < 0.01
    t2 = make_termin(45, bezeichnung='Ergotherapeutische temporäre Schiene- ohne Anpassung')
    assert abs(termin_umsatz(t2) - SCHIENEN_PAUSCHALE) < 0.01

def test_nicht_erschienen_ist_keine_schiene():
    """'nicht erschienen' enthält den Substring 'schiene' — darf NICHT 390 € bekommen"""
    t = make_termin(45, bezeichnung='Ergotherapie: nicht erschienen (AR)')
    assert abs(termin_umsatz(t) - 4 * ZI_PREIS) < 0.01


# === Kaufmännische Rundung (Vertrag), nicht Banker's Rounding ===

def test_kround_kaufmaennisch():
    from generate import kround
    assert kround(2.5) == 3      # Python round(2.5) wäre 2 (Banker's)
    assert kround(0.5) == 1
    assert kround(1.5) == 2
    assert kround(0.125, 2) == 0.13   # round(0.125, 2) wäre 0.12

def test_zi_anzahl_kaufmaennisch_gerundet():
    """37,5 min / 15 = 2,5 → kaufmännisch 3 (+1 VNB = 4 ZI); Banker's ergäbe 3 ZI"""
    t = make_termin(37.5)
    assert abs(termin_umsatz(t) - 4 * ZI_PREIS) < 0.01


# === Thermisch: PKV UND Selbstzahler ×2,0 (Valentin 23.07.2026) ===

def test_thermisch_sz_zweifach():
    t = make_termin(30, verordnungstyp=3, bezeichnung='Thermische Anwendung, Kälte/Wärme')
    assert abs(termin_umsatz(t) - 8.51 * 2.0) < 0.01

def test_thermisch_pkv_zweifach():
    t = make_termin(30, verordnungstyp=2, bezeichnung='Thermische Anwendung, Kälte/Wärme')
    assert abs(termin_umsatz(t) - 8.51 * 2.0) < 0.01

def test_sz_faktor_sonst_unveraendert():
    assert abs(termin_umsatz(make_termin(45, verordnungstyp=3)) - 4 * ZI_PREIS * 1.7) < 0.01


# === Testkonten-Erkennung (MediFox-Testdaten) ===

def test_testkonten_erkannt():
    from generate import _ist_testkonto
    assert _ist_testkonto('Testbär', 'Testerei')
    assert _ist_testkonto('Testuser', 'Pberg')
    assert _ist_testkonto('Test', 'User')
    assert _ist_testkonto('Ben', 'Test')
    assert _ist_testkonto('Jakob', 'Wense Test')
    assert _ist_testkonto(None, 'Fritzen Test')
    assert _ist_testkonto('test', 'test')

def test_echte_namen_kein_testkonto():
    from generate import _ist_testkonto
    assert not _ist_testkonto('Nicolo', 'Testa')
    assert not _ist_testkonto('Bärbel', 'Lehrheuer')
    assert not _ist_testkonto('Bärbel', 'Sauermann')

def test_test_termin_via_mitarbeiter():
    from generate import _ist_test_termin
    t = {'patient_vorname': 'Lea', 'patient_nachname': 'Wirtz',
         'mitarbeiter': [{'Id': '3d746938-0f1a-4fae-b008-0173ccf373c6', 'Vorname': 'Testbär', 'Nachname': 'Testerei'}]}
    assert _ist_test_termin(t)
    t2 = {'patient_vorname': 'Lea', 'patient_nachname': 'Wirtz',
          'mitarbeiter': [{'Id': 'x', 'Vorname': 'Sophia', 'Nachname': 'von Winkler'}]}
    assert not _ist_test_termin(t2)
