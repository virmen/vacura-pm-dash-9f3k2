"""Ueberstunden aus der Mitarbeiter-App im Nenner (Valentin 23.09.2026): Deckel auf Behandlung ausserhalb der verfuegbaren Zeit,
Freizeitausgleich nur soweit nicht schon MediFox-Abwesenheit, Stichtag OT_AB."""
import sys, os, json
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate as g


def th(slots):
    return {'id': 'm1', 'arbeitszeit_gruppen': [{'GueltigAb': '2026-01-01', 'Arbeitszeiten': slots}]}


def iv(b, e):
    return (datetime.fromisoformat(b).replace(tzinfo=timezone.utc), datetime.fromisoformat(e).replace(tzinfo=timezone.utc))


FR = 16   # Freitag-Bitmask (2026-09-04 ist ein Freitag)


def test_ot_min_summiert_und_stichtag():
    mp = {'m1_2026-09-04': [{'minutes': 90}, {'minutes': 60}], 'm1_2026-06-30': [{'minutes': 500}]}
    assert g._ot_min(mp, 'm1', '2026-09-04') == 150
    assert g._ot_min(mp, 'm1', '2026-06-30') == 0      # vor dem Stichtag
    assert g._ot_min(mp, 'm2', '2026-09-04') == 0


def test_termin_ganz_in_arbeitszeit_zaehlt_nicht():
    m = th([{'Wochentag': FR, 'Start': '08:00:00', 'Ende': '16:00:00'}])
    # 10:00-11:00 Ortszeit (08:00-09:00 UTC im Sommer)
    assert g._ot_ausserhalb_je_tag(m, [iv('2026-09-04 08:00:00', '2026-09-04 09:00:00')], set(), '2026-09-01', '2026-09-30') == {}


def test_termin_teilweise_ausserhalb_anteilig():
    m = th([{'Wochentag': FR, 'Start': '08:00:00', 'Ende': '16:00:00'}])
    # 15:30-17:00 Ortszeit (13:30-15:00 UTC) -> 60 min ausserhalb
    out = g._ot_ausserhalb_je_tag(m, [iv('2026-09-04 13:30:00', '2026-09-04 15:00:00')], set(), '2026-09-01', '2026-09-30')
    assert out == {'2026-09-04': 60}


def test_abwesenheitstag_zaehlt_ganz_ausserhalb():
    # Stephanie-Fall: Fortbildungstag in MediFox, Behandlung 08:00-10:30 Ortszeit innerhalb der Slots -> 150 min ausserhalb
    m = th([{'Wochentag': FR, 'Start': '08:00:00', 'Ende': '16:00:00'}])
    out = g._ot_ausserhalb_je_tag(m, [iv('2026-09-04 06:00:00', '2026-09-04 08:30:00')], {'2026-09-04'}, '2026-09-01', '2026-09-30')
    assert out == {'2026-09-04': 150}


def test_vor_stichtag_und_ausserhalb_fenster_ignoriert():
    m = th([{'Wochentag': FR, 'Start': '08:00:00', 'Ende': '10:00:00'}])
    assert g._ot_ausserhalb_je_tag(m, [iv('2026-06-26 12:00:00', '2026-06-26 13:00:00')], set(), '2026-06-01', '2026-06-30') == {}
    assert g._ot_ausserhalb_je_tag(m, [iv('2026-09-04 12:00:00', '2026-09-04 13:00:00')], set(), '2026-09-05', '2026-09-30') == {}


def test_overtime_json_wird_geladen(tmp_path, monkeypatch):
    p = tmp_path / 'ot.json'
    p.write_text(json.dumps({'therapie': {'m1_2026-09-04': [{'minutes': 45}]}, 'ausgleich': {'m1_2026-09-17': [{'minutes': 60}]}}))
    monkeypatch.setenv('OVERTIME_JSON', str(p))
    g._OT_CACHE.clear()
    d = g._overtime_data('2026-07-01', '2026-09-30')
    assert g._ot_min(d['therapie'], 'm1', '2026-09-04') == 45
    assert g._ot_min(d['ausgleich'], 'm1', '2026-09-17') == 60
    g._OT_CACHE.clear()
