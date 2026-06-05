"""pytest config for PM-Dashboard tests.

Tarife: Cache wird vor Test-Sammlung auf _TARIFE_FALLBACK gepinnt, damit Tests
keinen NocoDB-Call brauchen und gegen stabile Werte (Stand 2026-06) prüfen.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import generate
generate._TARIFE_CACHE = generate._TARIFE_FALLBACK
