"""
Author: rahn
Datum: 21.06.2025
Version: 1.0
Beschreibung: Deep Web Crawler als vollwertiger Agent
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .deep_web_crawler import DeepWebCrawler, CrawlResult
from src.core.logger import get_logger


class DeepWebCrawlerAgent(BaseAgent):
    """Deep Web Crawler Agent für tiefgreifende Website-Analyse"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.crawler = DeepWebCrawler(name, config)
        self.logger = get_logger(f"agent.{name}", agent_type="deep_crawler")
        self.max_depth = config.get('crawler_config', {}).get('max_depth', 3)
        self.max_pages = config.get('crawler_config', {}).get('max_pages', 100)
        
    async def initialize(self) -> bool:
        """Initialisiert den Crawler Agent"""
        try:
            self.status = AgentStatus.READY
            self.logger.info("Deep Web Crawler Agent initialisiert")
            return True
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def validate_credentials(self) -> bool:
        """Deep Web Crawler benötigt keine Credentials"""
        return True
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Deep Web Crawl für Mine durch"""
        results = []
        
        # ÄNDERUNG 21.06.2025: Nutze discovered_sources wenn verfügbar
        discovered_sources = getattr(query, 'discovered_sources', None)
        if discovered_sources:
            self.logger.info(f"Nutze {len(discovered_sources)} entdeckte Quellen")
            start_urls = [source.url for source in discovered_sources[:10]]  # Top 10 Quellen
        else:
            # Fallback: Suche nach Start-URLs
            start_urls = await self._find_start_urls(query)
        
        if not start_urls:
            self.logger.warning(f"Keine Start-URLs für {query.mine_name} gefunden")
            return results
        
        # Crawle jede Start-URL
        all_crawl_results = []
        for url in start_urls[:5]:  # Maximal 5 URLs pro Suche
            self.logger.info(f"Starte Deep Crawl für {url}")
            
            try:
                crawl_results = await self.crawler.deep_crawl(
                    start_url=url,
                    max_depth=self.max_depth,
                    mine_name=query.mine_name,
                    target_fields=query.required_fields
                )
                all_crawl_results.extend(crawl_results)
            except Exception as e:
                self.logger.error(f"Fehler beim Crawlen von {url}: {e}")
        
        # Konvertiere CrawlResults zu SearchResults
        for crawl_result in all_crawl_results:
            # Extrahiere relevante Daten aus gecrawlten Seiten
            for field, values in crawl_result.relevant_content.items():
                if field in query.required_fields:
                    for value in values[:3]:  # Max 3 Werte pro Feld
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field,
                            value=value,
                            source=f"Deep Crawl: {crawl_result.url}",
                            source_url=crawl_result.url,
                            source_date=datetime.now().year,
                            confidence_score=crawl_result.relevance_score,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={
                                'depth': crawl_result.depth,
                                'content_type': crawl_result.content_type,
                                'documents_found': len(crawl_result.documents_found),
                                'tables_found': len(crawl_result.data_tables)
                            }
                        )
                        results.append(result)
            
            # Speichere gefundene Dokumente als separate Ergebnisse
            if crawl_result.documents_found:
                for doc in crawl_result.documents_found[:5]:  # Max 5 Dokumente
                    result = SearchResult(
                        mine_name=query.mine_name,
                        field_name='document',
                        value=f"{doc['type']}: {doc['title']}",
                        source=f"Document found on: {crawl_result.url}",
                        source_url=doc['url'],
                        source_date=datetime.now().year,
                        confidence_score=0.8,
                        agent_name=self.name,
                        timestamp=datetime.now(),
                        metadata={
                            'document_type': doc['type'],
                            'extension': doc['extension']
                        }
                    )
                    results.append(result)
        
        # Update Statistiken
        self.stats['total_requests'] += len(start_urls)
        self.stats['successful_requests'] += len([r for r in all_crawl_results if r.relevance_score > 0])
        self.stats['total_fields_found'] += len(results)
        
        self.logger.info(f"Deep Crawl abgeschlossen: {len(results)} Ergebnisse gefunden")
        return results
    
    async def _find_start_urls(self, query: MineQuery) -> List[str]:
        """Findet Start-URLs für Deep Crawl"""
        start_urls = []
        
        # Basis-Suchmaschinen URLs
        search_patterns = [
            f"https://www.google.com/search?q={query.mine_name}+mine+{query.country}",
            f"https://www.bing.com/search?q={query.mine_name}+mining+{query.region}"
        ]
        
        # Länderspezifische Mining-Portale
        if query.country.lower() == 'canada':
            start_urls.extend([
                "https://www.nrcan.gc.ca/mining-materials/mining/canadian-minerals-yearbook/8426",
                "https://www.mining.ca/",
                f"https://www.mern.gouv.qc.ca/en/mines/quebec-mines/search/?q={query.mine_name}"
            ])
        elif query.country.lower() == 'australia':
            start_urls.extend([
                "https://www.ga.gov.au/",
                "https://www.industry.gov.au/data-and-publications/australias-identified-mineral-resources"
            ])
        
        return start_urls
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        self.crawler.visited_urls.clear()
        self.crawler.queued_urls.clear()
        self.crawler.results.clear()
        self.logger.info("Deep Web Crawler Agent beendet")