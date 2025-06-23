"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Apify Web Scraping Agent Hauptklasse
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from ..rate_limiter import RateLimiter
from src.core.logger import get_logger, PerformanceLogger
from ..enhanced_search import get_mining_search_queries, get_mining_domains

from .actors import ApifyActorManager
from .result_processor import ApifyResultProcessor


class ApifyAgent(BaseAgent):
    """Apify Agent für strukturiertes Web Scraping"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].apify_key
        self.base_url = "https://api.apify.com/v2"
        self._rate_limiter = RateLimiter(rate=30, per=60.0)  # 30 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="apify")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            # Initialisiere Manager-Komponenten
            self.actor_manager = ApifyActorManager(
                self.api_key, 
                self.base_url, 
                self._session
            )
            self.result_processor = ApifyResultProcessor(self.name)
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Apify Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein Apify API-Key konfiguriert")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Test API-Zugriff
            async with self._session.get(
                f"{self.base_url}/acts",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweiterte Mining-spezifisches Web Scraping mit Apify durch"""
        results = []
        
        self.perf_logger.start_timer(f"apify_search_{query.mine_name}")
        
        try:
            # Hole erweiterte Mining-Suchanfragen
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Apify: Starte erweiterte Mining-Suche")
            
            # 1. Erweiterte Google-Suche mit Mining-Queries
            urls = await self._enhanced_google_search(query, mining_queries[:15])
            
            # 2. Scrape Mining-spezifische Websites
            if urls:
                scraped_data = await self._scrape_mining_sites(urls, query)
                results.extend(scraped_data)
            
            # 3. Spezielle Regierungsseiten-Scraping für Kanada
            if query.country.lower() == 'canada':
                gov_results = await self._scrape_government_sites(query)
                results.extend(gov_results)
            
            self.perf_logger.end_timer(
                f"apify_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Update Statistiken
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1 if results else 0
            self.stats['total_fields_found'] += len(results)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self.stats['failed_requests'] += 1
            
        return results
    
    async def _enhanced_google_search(self, query: MineQuery, mining_queries: List[str]) -> List[str]:
        """Sucht relevante URLs via Google"""
        urls = []
        
        # Verwende die erweiterten Mining-Queries
        completed = 0
        
        for search_query in mining_queries:
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Apify: Google-Suche {completed + 1}/{len(mining_queries)}")
            
            completed += 1
            try:
                await self._rate_limiter.acquire()
                
                actor_input = self.actor_manager.get_google_search_input(search_query)
                
                # Starte Actor Run
                run_id = await self.actor_manager.start_actor_run(
                    self.actor_manager.actors['google_search'],
                    actor_input
                )
                
                if run_id:
                    # Warte auf Ergebnisse
                    results = await self.actor_manager.get_actor_results(run_id)
                    if results:
                        extracted_urls = self.result_processor.extract_urls_from_google_results(results, query)
                        urls.extend(extracted_urls)
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Google-Suche Fehler: {e}")
        
        return list(set(urls))  # Deduplizieren
    
    async def _scrape_mining_sites(self, urls: List[str], query: MineQuery) -> List[SearchResult]:
        """Scraped Websites für Mining-Informationen"""
        results = []
        
        for url in urls[:10]:  # Max 10 URLs
            try:
                await self._rate_limiter.acquire()
                
                actor_input = self.actor_manager.get_cheerio_scraper_input(url)
                
                # Starte Scraping
                run_id = await self.actor_manager.start_actor_run(
                    self.actor_manager.actors['cheerio_scraper'],
                    actor_input
                )
                
                if run_id:
                    # Hole Ergebnisse
                    scraped_data = await self.actor_manager.get_actor_results(run_id)
                    if scraped_data:
                        for item in scraped_data:
                            # Extrahiere Daten
                            extracted = self.result_processor.extract_from_scraped_data(
                                item,
                                url,
                                query
                            )
                            results.extend(extracted)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Website Scraping Fehler für {url}: {e}")
        
        return results
    
    async def _scrape_government_sites(self, query: MineQuery) -> List[SearchResult]:
        """Spezielles Scraping für Regierungsseiten"""
        results = []
        
        # Quebec GESTIM
        if query.region.lower() in ['quebec', 'québec']:
            gestim_url = f"https://gestim.mines.gouv.qc.ca/MRN_GestimP_Presentation/ODM02301_menu_base.aspx"
            
            try:
                await self._rate_limiter.acquire()
                
                actor_input = self.actor_manager.get_web_scraper_input(gestim_url, query.mine_name)
                
                run_id = await self.actor_manager.start_actor_run(
                    self.actor_manager.actors['web_scraper'],
                    actor_input
                )
                
                if run_id:
                    scraped_data = await self.actor_manager.get_actor_results(run_id)
                    if scraped_data:
                        for item in scraped_data:
                            if item and 'content' in item:
                                # Parse GESTIM-spezifische Felder
                                extracted = self.result_processor.parse_gestim_data(item, query)
                                results.extend(extracted)
                
            except Exception as e:
                self.logger.error(f"GESTIM Scraping Fehler: {e}")
        
        return results
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Apify Agent beendet")