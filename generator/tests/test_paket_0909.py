"""Gehaltswelt-Paket 09.09.2026: Zwillinge, Doppelbelegung, Leitungszeit-Staffel, Preise Bericht/Gruppen-Positionsname."""
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate as g


def T(id_, beginn, ende, patient='p1', status='erbracht', deleted=None, bez='Motorisch-funkt. Beh., 2 ZI', mid='m1', **kw):
    t = {'id': id_, 'beginn': beginn, 'ende': ende, 'patient_id': patient, 'status': status, 'deleted_at': deleted,
         'bezeichnung': bez, 'art': 'normal', 'is_blocker': False, 'mitarbeiter': [{'Id': mid}], 'verordnungstyp': 1}
    t.update(kw)
    return t


def test_zwilling_geloescht_zaehlt_nicht():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 10:30:00')
    z = T(2, '2026-08-03 10:00:00', '2026-08-03 10:30:00', deleted='2026-08-04', bez='Sensomotorisch-perz. Beh.')
    assert g._verdraengte_erbrachte([(a, 'm1'), (z, 'm1')]) == {2}


def test_geloeschter_ohne_zwilling_zaehlt():
    z = T(2, '2026-08-03 10:00:00', '2026-08-03 10:30:00', deleted='2026-08-04')
    b = T(3, '2026-08-03 11:00:00', '2026-08-03 11:30:00')
    assert g._verdraengte_erbrachte([(z, 'm1'), (b, 'm1')]) == set()


def test_zwilling_anderer_therapeut_ist_keiner():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 10:30:00', mid='m1')
    z = T(2, '2026-08-03 10:00:00', '2026-08-03 10:30:00', deleted='2026-08-04', mid='m2')
    assert g._verdraengte_erbrachte([(a, 'm1'), (z, 'm2')]) == set()


def test_doppelbelegung_gleicher_patient_spaeterer_entfaellt():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 11:00:00')
    b = T(2, '2026-08-03 10:30:00', '2026-08-03 11:00:00')   # voll im ersten
    assert g._verdraengte_erbrachte([(a, 'm1'), (b, 'm1')]) == {2}


def test_doppelbelegung_gleicher_beginn_kuerzerer_entfaellt():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 10:30:00')
    b = T(2, '2026-08-03 10:00:00', '2026-08-03 11:00:00')
    assert g._verdraengte_erbrachte([(a, 'm1'), (b, 'm1')]) == {1}


def test_doppelbelegung_kleine_ueberlappung_bleibt():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 10:45:00')
    b = T(2, '2026-08-03 10:35:00', '2026-08-03 11:20:00')   # 10 von 45 min
    assert g._verdraengte_erbrachte([(a, 'm1'), (b, 'm1')]) == set()


def test_verschiedene_patienten_parallel_zaehlen():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 10:30:00', patient='p1')
    b = T(2, '2026-08-03 10:00:00', '2026-08-03 10:30:00', patient='p2')
    assert g._verdraengte_erbrachte([(a, 'm1'), (b, 'm1')]) == set()


def test_parallel_position_thermisch_bleibt_und_verdraengt_nicht():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 10:30:00')
    th = T(2, '2026-08-03 10:00:00', '2026-08-03 10:20:00', bez='Thermische Anwendung, Kälte/Wärme')
    assert g._verdraengte_erbrachte([(a, 'm1'), (th, 'm1')]) == set()


def test_geplant_und_geloescht_geplant_unberuehrt():
    a = T(1, '2026-08-03 10:00:00', '2026-08-03 10:30:00', status='geplant')
    b = T(2, '2026-08-03 10:00:00', '2026-08-03 10:30:00', status='geplant', deleted='2026-08-04')
    assert g._verdraengte_erbrachte([(a, 'm1'), (b, 'm1')]) == set()


def test_preis_umfangreicher_bericht_null():
    t = T(1, '2026-08-03 10:00:00', '2026-08-03 10:30:00', bez='Umfangreicher Bericht')
    assert g.termin_umsatz(t) == 0.0


def test_preis_gruppen_positionsname():
    t = T(1, '2026-08-03 10:00:00', '2026-08-03 11:00:00', bez='Bei sensomotorisch-perzeptiven Störungen (bis zu 3 Patienten)')
    assert abs(g.termin_umsatz(t) - 26.57 * 1.0411) < 0.001


def test_lz_staffel():
    assert g._lz_pct(2) == 0.08125 and g._lz_pct(4) == 0.125 and g._lz_pct(6) == 0.16875 and g._lz_pct(8) == 0.20 and g._lz_pct(9) == 0.225


def _ma(id_, rollen=('Therapeut',), start='2026-01-01', filiale='spandau', std=30, aktiv=True, therapeut=True):
    return {'id': id_, 'vorname': 'A', 'nachname': id_, 'rollen': list(rollen), 'filiale': filiale, 'is_active': aktiv, 'is_therapeut': therapeut,
            'beschaeftigungszeiten': [{'Von': start, 'Bis': None}],
            'arbeitszeit_gruppen': [{'GueltigAb': '2026-01-01', 'GueltigBis': None, 'StundenProWoche': std,
                                     'Arbeitszeiten': [{'Wochentag': 1 << i, 'Start': '08:00:00', 'Ende': f'{8 + std // 5:02d}:00:00'} for i in range(5)]}]}


def test_th_count_je_standort_ohne_sl_und_29_tage():
    ma = [_ma('t1'), _ma('t2'), _ma('sl', rollen=('Therapeut', 'Verkauf')), _ma('neu', start='2026-08-20'), _ma('mitte', filiale='mitte'),
          _ma('inaktiv', aktiv=False), _ma('kein_th', therapeut=False)]
    cnt = g._th_count_je_standort(ma, date(2026, 9, 8))
    assert cnt == {'spandau': 2, 'mitte': 1}
    assert g._th_count_je_standort(ma, date(2026, 9, 20)) == {'spandau': 3, 'mitte': 1}


def test_gruppe_wochenstunden_und_sl():
    m = _ma('sl', rollen=('Therapeut', 'Verkauf'), std=40)
    assert g._ist_sl(m) and not g._ist_sl(_ma('x'))
    assert g._th_gruppe_wochenstunden(m, date(2026, 9, 8)) == 40.0
