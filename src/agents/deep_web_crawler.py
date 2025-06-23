"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Deep Web Crawler - Refactored Import
"""

# ÄNDERUNG 22.06.2025: Import aus modularisierter Struktur
from .deep_web_crawler import DeepWebCrawler, CrawlResult

__all__ = ['DeepWebCrawler', 'CrawlResult']