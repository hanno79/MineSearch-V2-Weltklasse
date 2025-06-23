"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: ScrapingBee Agent Wrapper - importiert refaktorierte Module
"""

# ÄNDERUNG 22.06.2025: Datei in Module aufgeteilt zur besseren Wartbarkeit
# Die Funktionalität bleibt identisch, nur die Struktur wurde verbessert

from .scrapingbee import ScrapingBeeAgent

__all__ = ['ScrapingBeeAgent']