"""
Author: rahn
Datum: 22.06.2025
Version: 1.1
Beschreibung: Import-Wrapper für Apify Agent (Refactoring)

ÄNDERUNG 22.06.2025: Datei in Module aufgeteilt:
- apify/apify_agent.py: Hauptklasse
- apify/actors.py: Actor-Verwaltung
- apify/result_processor.py: Ergebnis-Verarbeitung
"""

from .apify import ApifyAgent

__all__ = ['ApifyAgent']