"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Import-Wrapper für refaktoriertes browser_agent Modul
"""

# ÄNDERUNG 22.06.2025: Modul in kleinere Komponenten aufgeteilt
# Re-exportiere alle Klassen vom refaktorierten Modul
from .browser_agent import (
    BrowserAgent,
    PageAnalyzer,
    BrowserConfig,
    ScrapeResult,
    PortalConfig
)

__all__ = [
    'BrowserAgent',
    'PageAnalyzer',
    'BrowserConfig',
    'ScrapeResult',
    'PortalConfig'
]