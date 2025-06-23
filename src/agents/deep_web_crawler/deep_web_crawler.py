"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für Multi-Layer Web Crawler
"""

from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
import asyncio

from .crawler_engine import CrawlerEngine
from .link_analyzer import LinkAnalyzer


@dataclass
class CrawlResult:
    """Ergebnis eines Crawl-Vorgangs"""
    url: str
    depth: int
    content_type: str
    relevant_content: Dict[str, List[str]]
    linked_pages: List[str]
    documents_found: List[Dict[str, str]]
    data_tables: List[Dict[str, Any]]
    relevance_score: float


class DeepWebCrawler:
    """Crawlt Websites in mehreren Ebenen für Mining-Informationen"""
    
    def __init__(self, name: str, config: Dict[str, Any], scraper_agents=None):
        self.name = name
        self.config = config
        self.visited_urls = set()
        self.queued_urls = set()
        self.results = []
        self.scraper_agents = scraper_agents or {}
        self.active_scraper = None
        
        # ÄNDERUNG 22.06.2025: Logger und DB-Manager hinzufügen
        from src.core.logger import get_logger
        self.logger = get_logger(f"agent.{name}", agent_type="deep_crawler")
        try:
            from src.core.database import get_db_manager
            self.db_manager = get_db_manager()
        except:
            self.db_manager = None
            
        # Initialisiere Sub-Module
        self.crawler_engine = CrawlerEngine(self)
        self.link_analyzer = LinkAnalyzer(self)
        
    def set_scraper_agents(self, agents: Dict[str, Any]):
        """Setzt verfügbare Scraper-Agenten"""
        # ÄNDERUNG 17.06.2025: Methode zur Agent-Integration
        self.scraper_agents = {
            name: agent for name, agent in agents.items() 
            if name in ['scraper', 'brightdata', 'scrapingbee', 'apify', 'firecrawl']
        }
        
    async def deep_crawl(self, start_url: str, max_depth: int, 
                        mine_name: str, target_fields: List[str]) -> List[CrawlResult]:
        """
        Führt einen tiefen Crawl einer Website durch
        
        Args:
            start_url: Ausgangs-URL
            max_depth: Maximale Crawl-Tiefe
            mine_name: Name der Mine für Relevanz-Filterung
            target_fields: Gesuchte Datenfelder
        """
        self.mine_name = mine_name.lower()
        self.target_fields = target_fields
        
        # Nutze CrawlerEngine für den eigentlichen Crawl-Prozess
        return await self.crawler_engine.deep_crawl(start_url, max_depth, mine_name, target_fields)