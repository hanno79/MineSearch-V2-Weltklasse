"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Browser Agent Module
"""

from .browser_agent import BrowserAgent
from .page_analyzer import PageAnalyzer
from .models import BrowserConfig, ScrapeResult, PortalConfig

__all__ = [
    'BrowserAgent',
    'PageAnalyzer',
    'BrowserConfig',
    'ScrapeResult',
    'PortalConfig'
]