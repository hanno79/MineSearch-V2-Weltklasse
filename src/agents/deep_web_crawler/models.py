"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für Deep Web Crawler
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class CrawlResult:
    """Ergebnis eines Crawl-Vorgangs"""
    url: str
    depth: int
    content_type: str
    relevant_content: Dict[str, List[str]]
    linked_pages: List[str]
    documents_found: List[Dict[str, str]]  # PDFs, Excel, etc.
    data_tables: List[Dict[str, Any]]
    relevance_score: float
