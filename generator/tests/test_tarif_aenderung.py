"""Tests für _check_tarif_aenderungen() — Detection + Skalierungsfaktor.

Cache wird pro Test gesetzt + am Ende auf Fallback zurückgesetzt, damit Reihenfolge
keine Rolle spielt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from datetime import date
import generate


def _reset_cache():
    generate._TARIFE_CACHE = generate._TARIFE_FALLBACK


def test_keine_aenderung_im_fenster():
    """Alle gueltig_ab > 7 Tage alt → None."""
    generate._TARIFE_CACHE = [
        {'schluessel': 'basis_bis_30', 'wert': 56.93, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        {'schluessel': 'basis_bis_45', 'wert': 75.91, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
    ]
    assert generate._check_tarif_aenderungen(date(2026, 6, 5)) is None
    _reset_cache()


def test_initial_import_kein_vorgaenger_kein_change():
    """Nur Initial-Import-Rows (kein Vorgänger) → None (Tarif war vorher nicht im System)."""
    generate._TARIFE_CACHE = [
        {'schluessel': 'basis_bis_30', 'wert': 56.93, 'gueltig_ab': '2026-06-04', 'gueltig_bis': None},
    ]
    assert generate._check_tarif_aenderungen(date(2026, 6, 5)) is None
    _reset_cache()


def test_aenderung_detected_und_skalierung_plausibel():
    """4 neue Sätze gestern aktiviert → Detection + Skalierungsfaktor zwischen 1.04 und 1.07."""
    generate._TARIFE_CACHE = [
        # Alte Sätze (Vorgänger, gueltig_bis = Tag vor neuem Tarif)
        {'schluessel': 'basis_bis_20', 'wert': 8.51,  'gueltig_ab': '2024-01-01', 'gueltig_bis': '2026-06-03'},
        {'schluessel': 'basis_bis_30', 'wert': 56.93, 'gueltig_ab': '2024-01-01', 'gueltig_bis': '2026-06-03'},
        {'schluessel': 'basis_bis_45', 'wert': 75.91, 'gueltig_ab': '2024-01-01', 'gueltig_bis': '2026-06-03'},
        {'schluessel': 'basis_bis_60', 'wert': 94.89, 'gueltig_ab': '2024-01-01', 'gueltig_bis': '2026-06-03'},
        {'schluessel': 'hausbesuch_pauschale',        'wert': 27.56, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        {'schluessel': 'aufschlag_je_15min_ueber_60', 'wert': 18.98, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        # Neue Sätze gestern (gestern = 2026-06-04, im 7-Tage-Fenster bis 2026-06-05)
        {'schluessel': 'basis_bis_20', 'wert': 9.00,   'gueltig_ab': '2026-06-04', 'gueltig_bis': None},
        {'schluessel': 'basis_bis_30', 'wert': 60.00,  'gueltig_ab': '2026-06-04', 'gueltig_bis': None},
        {'schluessel': 'basis_bis_45', 'wert': 80.00,  'gueltig_ab': '2026-06-04', 'gueltig_bis': None},
        {'schluessel': 'basis_bis_60', 'wert': 100.00, 'gueltig_ab': '2026-06-04', 'gueltig_bis': None},
    ]
    # STUFEN-Default muss da sein (Modul-Konstante)
    result = generate._check_tarif_aenderungen(date(2026, 6, 5))
    assert result is not None
    assert len(result['changes']) == 4
    # Mix-gewichteter Faktor: 50%×60/56,93 + 39%×80/75,91 + 10%×100/94,89 + 1%×9/8,51 ≈ +5.3%
    assert 1.04 < result['scale_factor'] < 1.07
    # Empfohlene Schwellen alle höher
    for s in result['empfohlen_schwellen']:
        assert s['neu_eur60'] > s['alt_eur60']
    # Change-Liste hat delta_pct
    for c in result['changes']:
        assert c['delta_pct'] > 0
    _reset_cache()


def test_nur_eine_kategorie_geaendert():
    """Nur basis_bis_30 erhöht (z.B. selektiver Tarif-Anstieg) → Skalierungsfaktor zwischen 1.0 und delta."""
    generate._TARIFE_CACHE = [
        {'schluessel': 'basis_bis_20', 'wert': 8.51,  'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        {'schluessel': 'basis_bis_30', 'wert': 56.93, 'gueltig_ab': '2024-01-01', 'gueltig_bis': '2026-06-03'},
        {'schluessel': 'basis_bis_45', 'wert': 75.91, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        {'schluessel': 'basis_bis_60', 'wert': 94.89, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        {'schluessel': 'hausbesuch_pauschale',        'wert': 27.56, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        {'schluessel': 'aufschlag_je_15min_ueber_60', 'wert': 18.98, 'gueltig_ab': '2024-01-01', 'gueltig_bis': None},
        {'schluessel': 'basis_bis_30', 'wert': 60.00, 'gueltig_ab': '2026-06-04', 'gueltig_bis': None},
    ]
    result = generate._check_tarif_aenderungen(date(2026, 6, 5))
    assert result is not None
    assert len(result['changes']) == 1
    assert result['changes'][0]['schluessel'] == 'basis_bis_30'
    # 50% Mix-Anteil × +5.4% → ~+2.7% Faktor
    assert 1.02 < result['scale_factor'] < 1.04
    _reset_cache()
