"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Bright Data Web Scraping Agent - Import Wrapper

ÄNDERUNG 22.06.2025: Refaktorierung - Datei in Module aufgeteilt
- Hauptklasse: brightdata/brightdata_agent.py
- Proxy-Management: brightdata/proxy_manager.py
- Datenextraktion: brightdata/extractors.py  
- Scraping: brightdata/scraper.py

Diese Datei dient als Kompatibilitäts-Wrapper für bestehende Imports.
"""

from .brightdata.brightdata_agent import BrightDataAgent

__all__ = ['BrightDataAgent']