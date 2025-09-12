"""
Extraction Processors - Wrapper Module
Stellt Verarbeitungsfunktionen für Mining-Datenextraktion bereit

Author: MineSearch Development Team
Date: 2025-01-11
"""

# Importiere die neue modulare Implementierung
from minesearch.extraction import is_template_or_dummy_value, clean_extracted_value

# Für Rückwärtskompatibilität
__all__ = ["is_template_or_dummy_value", "clean_extracted_value"]
