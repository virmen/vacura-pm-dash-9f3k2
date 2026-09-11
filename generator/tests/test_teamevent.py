"""Teamevent-Bloecke im Nenner (Valentin, Dauerregel seit 11.09.2026): Teil des Blocks innerhalb der Arbeitszeit des Tages."""
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate as g


def th(slots):
    return {'id': 'm1', 'arbeitszeit_gruppen': [{'GueltigAb': '2026-01-01', 'Arbeitszeiten': slots}]}


def blk(beginn, ende, bez='Block Teamevent intern:', mid='m1', deleted=None):
    return {'beginn': beginn, 'ende': ende, 'bezeichnung': bez, 'mitarbeiter': [{'Id': mid}], 'deleted_at': deleted}


DO = 8   # Donnerstag-Bitmask


def test_block_teilweise_in_arbeitszeit():
    # Do 08:00-16:00 Ortszeit; Block 15:45-19:45 Ortszeit (13:45-17:45 UTC im Sommer) -> 15 min
    m = th([{'Wochentag': DO, 'Start': '08:00:00', 'Ende': '16:00:00'}])
    idx = g._team_index([blk('2026-09-03 13:45:00+00:00', '2026-09-03 17:45:00+00:00')])
    assert list(idx['m1'].keys()) == ['2026-09-03']
    assert abs(g._team_stunden_tag(m, date(2026, 9, 3), idx['m1']['2026-09-03']) - 0.25) < 1e-9


def test_block_ganz_in_arbeitszeit():
    m = th([{'Wochentag': DO, 'Start': '08:00:00', 'Ende': '18:30:00'}])
    idx = g._team_index([blk('2026-09-03 14:00:00+00:00', '2026-09-03 17:20:00+00:00')])   # 16:00-19:20 Ortszeit -> 2,5 h
    assert abs(g._team_stunden_tag(m, date(2026, 9, 3), idx['m1']['2026-09-03']) - 2.5) < 1e-9


def test_block_ausserhalb_arbeitszeit():
    m = th([{'Wochentag': DO, 'Start': '08:00:00', 'Ende': '14:00:00'}])
    idx = g._team_index([blk('2026-09-03 14:00:00+00:00', '2026-09-03 17:20:00+00:00')])
    assert g._team_stunden_tag(m, date(2026, 9, 3), idx['m1']['2026-09-03']) == 0


def test_mehrere_bloecke_als_vereinigung():
    m = th([{'Wochentag': DO, 'Start': '08:00:00', 'Ende': '20:00:00'}])
    idx = g._team_index([blk('2026-09-03 14:00:00+00:00', '2026-09-03 16:00:00+00:00'),
                         blk('2026-09-03 15:00:00+00:00', '2026-09-03 17:00:00+00:00')])   # 16-18 und 17-19 -> 3 h
    assert abs(g._team_stunden_tag(m, date(2026, 9, 3), idx['m1']['2026-09-03']) - 3.0) < 1e-9


def test_geloescht_und_fremde_bezeichnung_zaehlen_nicht():
    idx = g._team_index([blk('2026-09-03 14:00:00+00:00', '2026-09-03 16:00:00+00:00', deleted='2026-09-04'),
                         blk('2026-09-03 14:00:00+00:00', '2026-09-03 16:00:00+00:00', bez='Teammeeting intern')])
    assert idx == {}


def test_ortstag_nach_mitternacht_utc():
    # 22:30 UTC = 00:30 Ortszeit des Folgetags -> Ortstag 04.09.
    idx = g._team_index([blk('2026-09-03 22:30:00+00:00', '2026-09-03 23:30:00+00:00')])
    assert list(idx['m1'].keys()) == ['2026-09-04']
