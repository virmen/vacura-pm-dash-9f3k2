"""Nicht gewertete Therapeuten (Valentin 25.09.2026): ab `ab` enden Zaehler und Nenner am Tag davor."""
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate as g


def test_theda_ab_q3_ganz_raus():
    # ab 01.07.2026 -> Fensterende 30.06.; ein Q3-Fenster (Start 01.07.) liefert dann eff_start > eff_end
    assert g._ausschluss_ende('67ebee1f-bdd4-4f03-8438-e5ccd15d63d3', date(2026, 9, 25)) == date(2026, 6, 30)


def test_ohne_datum_keine_wirkung(monkeypatch):
    monkeypatch.setitem(g.NICHT_GEWERTET, 'x-ohne-datum', {'name': 'Test', 'ab': None, 'grund': 'offen'})
    assert g._ausschluss_ende('x-ohne-datum', date(2026, 9, 25)) == date(2026, 9, 25)


def test_app_liste_wirkt(monkeypatch):
    monkeypatch.setitem(g._AUSSCHLUSS_APP, 'x-app', {'name': 'App-Fall', 'ab': '2026-09-10', 'grund': 'gekuendigt'})
    assert g._ausschluss_ende('x-app', date(2026, 9, 25)) == date(2026, 9, 9)


def test_unbekannt_und_frueheres_ende_bleiben():
    assert g._ausschluss_ende('gibt-es-nicht', date(2026, 9, 25)) == date(2026, 9, 25)
    assert g._ausschluss_ende('67ebee1f-bdd4-4f03-8438-e5ccd15d63d3', date(2026, 5, 31)) == date(2026, 5, 31)   # Ende vor `ab` unveraendert


def test_schalter(monkeypatch):
    monkeypatch.setattr(g, 'AUSSCHLUSS_AKTIV', False)
    assert g._ausschluss_ende('67ebee1f-bdd4-4f03-8438-e5ccd15d63d3', date(2026, 9, 25)) == date(2026, 9, 25)
