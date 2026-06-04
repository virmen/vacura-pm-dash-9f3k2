"""Tests für _th_stunden_am_werktag() — TH-Arbeitsstunden an einem Wochentag.

Schema aus NocoDB: arbeitszeit_gruppen[].Arbeitszeiten[] mit Wochentag-Bitmask:
Mo=1, Di=2, Mi=4, Do=8, Fr=16.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date
from generate import _th_stunden_am_werktag


def make_th(slots):
    """Konstruiert synthetischen TH-Datensatz aus Liste von Slots."""
    return {
        'arbeitszeit_gruppen': [{
            'Arbeitszeiten': slots,
            'StundenProWoche': sum(_slot_h(s) for s in slots),
        }]
    }

def _slot_h(s):
    sh, sm = s['Start'].split(':')[:2]
    eh, em = s['Ende'].split(':')[:2]
    return (int(eh) + int(em)/60) - (int(sh) + int(sm)/60)


def test_kein_slot_an_diesem_tag():
    """TH arbeitet Mo+Mi, kein Slot Di → 0 h"""
    th = make_th([
        {'Wochentag': 1, 'Start': '08:00:00', 'Ende': '12:00:00'},  # Mo
        {'Wochentag': 4, 'Start': '09:00:00', 'Ende': '13:00:00'},  # Mi
    ])
    di = date(2026, 4, 7)  # Dienstag
    assert _th_stunden_am_werktag(th, di) == 0.0

def test_ein_slot():
    """1 Slot von 8-12 Uhr Mo → 4 h"""
    th = make_th([{'Wochentag': 1, 'Start': '08:00:00', 'Ende': '12:00:00'}])
    mo = date(2026, 4, 6)  # Montag
    assert _th_stunden_am_werktag(th, mo) == 4.0

def test_zwei_slots_am_tag():
    """Vormittag + Nachmittag = Summe"""
    th = make_th([
        {'Wochentag': 1, 'Start': '08:00:00', 'Ende': '12:00:00'},  # 4h
        {'Wochentag': 1, 'Start': '14:00:00', 'Ende': '18:30:00'},  # 4,5h
    ])
    mo = date(2026, 4, 6)
    assert _th_stunden_am_werktag(th, mo) == 8.5

def test_wochenende():
    """Sa/So immer 0, auch wenn Slot vorhanden"""
    th = make_th([{'Wochentag': 32, 'Start': '10:00:00', 'Ende': '14:00:00'}])
    sa = date(2026, 4, 4)
    so = date(2026, 4, 5)
    assert _th_stunden_am_werktag(th, sa) == 0.0
    assert _th_stunden_am_werktag(th, so) == 0.0

def test_minuten_genau():
    """8:30 - 13:15 = 4,75 h"""
    th = make_th([{'Wochentag': 1, 'Start': '08:30:00', 'Ende': '13:15:00'}])
    mo = date(2026, 4, 6)
    assert _th_stunden_am_werktag(th, mo) == 4.75

def test_gueltigab_zukunft():
    """Slot mit GueltigAb in der Zukunft → wird ignoriert"""
    th = make_th([
        {'Wochentag': 1, 'Start': '08:00:00', 'Ende': '12:00:00', 'GueltigAb': '2026-12-01'}
    ])
    mo = date(2026, 4, 6)  # vor GueltigAb
    assert _th_stunden_am_werktag(th, mo) == 0.0

def test_gruppen_gueltigkeit():
    """Gruppen-GueltigBis vor Datum → Gruppe wird ignoriert"""
    th = {
        'arbeitszeit_gruppen': [{
            'GueltigAb': '2025-01-01',
            'GueltigBis': '2026-03-31',
            'Arbeitszeiten': [{'Wochentag': 1, 'Start': '08:00:00', 'Ende': '12:00:00'}],
        }]
    }
    mo_april = date(2026, 4, 6)  # nach GueltigBis
    assert _th_stunden_am_werktag(th, mo_april) == 0.0

def test_alle_5_werktage():
    """Bitmask: Mo=1, Di=2, Mi=4, Do=8, Fr=16"""
    th = make_th([
        {'Wochentag': 1, 'Start': '08:00:00', 'Ende': '12:00:00'},  # Mo 4h
        {'Wochentag': 2, 'Start': '09:00:00', 'Ende': '14:00:00'},  # Di 5h
        {'Wochentag': 4, 'Start': '10:00:00', 'Ende': '13:00:00'},  # Mi 3h
        {'Wochentag': 8, 'Start': '08:00:00', 'Ende': '14:00:00'},  # Do 6h
        {'Wochentag': 16, 'Start': '10:00:00', 'Ende': '15:00:00'}, # Fr 5h
    ])
    # Mo-Fr eine Woche in April 2026 (KW 14: 30.3-3.4, KW 15: 6-10.4)
    assert _th_stunden_am_werktag(th, date(2026, 4, 6))  == 4   # Mo
    assert _th_stunden_am_werktag(th, date(2026, 4, 7))  == 5   # Di
    assert _th_stunden_am_werktag(th, date(2026, 4, 8))  == 3   # Mi
    assert _th_stunden_am_werktag(th, date(2026, 4, 9))  == 6   # Do
    assert _th_stunden_am_werktag(th, date(2026, 4, 10)) == 5   # Fr
