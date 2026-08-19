"""Tests für den Aktionsblock (seit 18.08.2026): Intervall-Logik, Absagen ohne Nachbesetzung
(synthetische NocoDB-Daten, kein Netz) und ein Render-Smoke-Test."""
import sys, os
from datetime import date, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import generate as g


def _dt(h, m=0, d=date(2026, 8, 3)):
    return datetime(d.year, d.month, d.day, h, m)


def test_iv_union_und_minus():
    a = [(_dt(9), _dt(10)), (_dt(9, 30), _dt(11)), (_dt(13), _dt(14))]
    assert abs(g._iv_union_len(a) - 3.0) < 1e-9          # 9–11 (2 h) + 13–14 (1 h)
    rest = g._iv_minus([(_dt(9), _dt(11))], [(_dt(9, 30), _dt(10))])
    assert abs(g._iv_union_len(rest) - 1.5) < 1e-9       # 9–9:30 + 10–11
    assert g._iv_minus([(_dt(9), _dt(10))], [(_dt(8), _dt(11))]) == []


def test_absagen_ohne_nachbesetzung(monkeypatch):
    """Zwei TH-Tage: (a) Absage 9–10 mit parallel erbrachtem Termin 9–10 → nachbesetzt;
    (b) Absage 13–14 ohne Überdeckung → frei; (c) Absage an einem Krank-Tag zählt gar nicht."""
    th = 'th-1'
    termine = [
        {'id': 1, 'art': 'normal', 'status': 'abgesagt_durch_therapeut', 'beginn': '2026-08-03T09:00:00', 'ende': '2026-08-03T10:00:00',
         'mitarbeiter': [{'Id': th}], 'filiale': 'mitte', 'patient_vorname': 'A', 'patient_nachname': 'B'},
        {'id': 2, 'art': 'normal', 'status': 'erbracht_und_unterschrieben', 'beginn': '2026-08-03T09:00:00', 'ende': '2026-08-03T10:00:00',
         'mitarbeiter': [{'Id': th}], 'filiale': 'mitte', 'patient_vorname': 'C', 'patient_nachname': 'D'},
        {'id': 3, 'art': 'normal', 'status': 'abgesagt_durch_therapeut', 'beginn': '2026-08-03T13:00:00', 'ende': '2026-08-03T14:00:00',
         'mitarbeiter': [{'Id': th}], 'filiale': 'mitte', 'patient_vorname': 'E', 'patient_nachname': 'F'},
        {'id': 4, 'art': 'normal', 'status': 'abgesagt_durch_therapeut', 'beginn': '2026-08-04T09:00:00', 'ende': '2026-08-04T10:00:00',
         'mitarbeiter': [{'Id': th}], 'filiale': 'mitte', 'patient_vorname': 'G', 'patient_nachname': 'H'},
    ]
    abw = [{'id': 9, 'mitarbeiter_id': th, 'art': 'krank', 'von': '2026-08-04', 'bis': '2026-08-04', 'deleted_at': None}]

    def fake_fetch(table_id, where=None):
        if table_id == 'mf2pw17nwfzlkd2': return termine
        if table_id == 'mwcnx74etcl1frq': return abw
        return []
    monkeypatch.setattr(g, '_fetch_all', fake_fetch)
    r = g.absagen_ohne_nachbesetzung(['mitte'], {th: (date(2026, 8, 1), date(2026, 8, 31))}, date(2026, 8, 1), date(2026, 8, 31))
    assert r['n_abg'] == 2                     # Termin 4 (Krank-Tag) zählt nicht
    assert abs(r['h_abg'] - 2.0) < 1e-9
    assert r['n_frei'] == 1                    # nur Termin 3 blieb frei
    assert abs(r['h_frei'] - 1.0) < 1e-9


def _fake_ab():
    live = {'q_start': date(2026, 7, 1), 'q_end': date(2026, 9, 30), 'eff_end': date(2026, 8, 18), 'wochen': 7.0, 'nth': 16,
            'verfueg': 2100.0, 'ist': 154000.0, 'eur60': 73.3, 'termine': 1880, 'geplant': 120,
            'behandlung': 1330.0, 'beh_anteil': 1330.0 / 2100.0, 'eur_beh': 154000.0 / 1330.0, 'pkv': 0.11,
            'dauer_termin': 0.71, '_plausibel': True, 'n_abg': 560, 'h_abg': 355.0, 'n_frei': 205, 'h_frei': 143.0}
    ref = dict(live, q_start=date(2026, 4, 1), q_end=date(2026, 6, 30), eff_end=date(2026, 6, 30), wochen=13.0,
               verfueg=3900.0, ist=293000.0, eur60=75.1, behandlung=2700.0, beh_anteil=2700.0 / 3900.0, eur_beh=293000.0 / 2700.0)
    hist = [{'monat': date(2026, 3, 1), 'beh': 70.9, 't_wo': 363, 'frei_wo': 16.3, 'nachbesetzt': 0.65, 'aus': 92.5, 'nth': 14, 'teilmonat': False, '_plausibel': True},
            {'monat': date(2026, 5, 1), 'beh': 77.4, 't_wo': 241, 'frei_wo': 21.8, 'nachbesetzt': 0.48, 'aus': 95.1, 'nth': 14, 'teilmonat': False, '_plausibel': False},
            {'monat': date(2026, 6, 1), 'beh': 68.2, 't_wo': 333, 'frei_wo': 18.8, 'nachbesetzt': 0.58, 'aus': 91.7, 'nth': 14, 'teilmonat': False, '_plausibel': True},
            {'monat': date(2026, 7, 1), 'beh': 63.8, 't_wo': 265, 'frei_wo': 16.3, 'nachbesetzt': 0.64, 'aus': 87.7, 'nth': 16, 'teilmonat': False, '_plausibel': True},
            {'monat': date(2026, 8, 1), 'beh': 62.6, 't_wo': 272, 'frei_wo': 27.9, 'nachbesetzt': 0.53, 'aus': 84.0, 'nth': 16, 'teilmonat': True, '_plausibel': True}]
    return {'live': live, 'ref': ref, 'ziel': g.stufen_eff('2026-07-01')[2], 'thr_live': g.stufen_eff('2026-07-01')[2]['eur60'],
            'thr_q': g.STUFEN[2]['eur60'], 'rest_need': 78.1, 'rest_ref': 78.5,
            'hist_aus': {'Q4 2025': 86.0, 'Q1 2026': 88.5, 'Q2 2026': 92.6}, 'live_aus': 84.0,
            'historie': hist, 'standorte': [{'name': 'Spandau', 'nth': 7, 'verf_wo': 139.0, 'frei_wo': 9.3, 'frei_n_wo': 13, 'nachbesetzt': 0.60},
                                            {'name': 'Mitte', 'nth': 9, 'verf_wo': 162.0, 'frei_wo': 11.2, 'frei_n_wo': 16, 'nachbesetzt': 0.59}],
            'q_label_live': 'Q3 2026', 'q_label_ref': 'Q2 2026', 'today': date(2026, 8, 18)}


def test_render_aktionsblock_smoke():
    pm = {'name': 'Test', 'eur60': 70.69, 'tats_stufe': 2, 'zufr': 8.5, 'stufen_eff': g.STUFEN, 'probezeit_aktiv': False}
    html = g.render_aktionsblock(pm, _fake_ab())
    assert 'Wie kommst du auf Stufe 3?' in html
    assert '75,63' in html                                    # indexierte Q3-Schwelle, nicht 72,64 als Live-Ziel
    assert 'Abgesagte Slots nachbesetzen' in html
    assert 'Was bei euch schon gut lief' in html
    assert 'März 2026' in html and 'Juni 2026' in html
    assert 'Mai 2026' not in html                             # unplausibler Monat (Feiertage) bleibt außen vor
    assert 'Krank' not in html and 'krank' not in html        # Krankheit ist kein Bestandteil mehr
    assert '—' not in html                                    # keine Gedankenstriche im neuen Block


def test_render_aktionsblock_ueber_schwelle():
    """Live über der Schwelle: Halten-Variante ohne „fehlen"-Box und ohne „0,0 h von"."""
    ab = _fake_ab()
    ab['live'] = dict(ab['live'], eur60=80.0, ist=80.0 * 2100.0, eur_beh=80.0 * 2100.0 / 1330.0)
    pm = {'name': 'Test', 'eur60': 70.69, 'tats_stufe': 2, 'zufr': 8.5, 'stufen_eff': g.STUFEN}
    html = g.render_aktionsblock(pm, ab)
    assert 'Der Live-Stand reicht für Stufe 3' in html
    assert '0,0 h von' not in html
