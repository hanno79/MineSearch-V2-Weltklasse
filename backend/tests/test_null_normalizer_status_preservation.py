"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Test-Suite
"""
import sys
import os
import pytest

# Sicherstellen, dass /app/backend im sys.path ist, um 'minesearch' zu importieren
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from minesearch.null_normalizer import NullNormalizer


@pytest.mark.parametrize("value", [
    'noch aktiv', 'Mine geschlossen', 'nur Exploration', 'noch geplant', 'in Entwicklung',
    'still active', 'mine closed', 'only exploration', 'still planned', 'in development'
])
def test_status_values_preserved_in_activity_status(value):
    """test_status_values_preserved_in_activity_status - TODO: Dokumentation hinzufügen"""
    normalizer = NullNormalizer()
    assert normalizer.normalize_value(value, 'Aktivitätsstatus') == value


def test_field_specific_nulls_for_status_markers():
    """test_field_specific_nulls_for_status_markers - TODO: Dokumentation hinzufügen"""
    normalizer = NullNormalizer()
    assert normalizer.normalize_value('noch aktiv', 'Produktionsende') is None
    assert normalizer.normalize_value('Mine geschlossen', 'Fördermenge/Jahr') is None
