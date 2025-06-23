"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Bright Data Web Scraping Agent Implementation - Hauptklasse

ÄNDERUNG 22.06.2025: Refaktorierung in Module
- Proxy-Management ausgelagert in proxy_manager.py
- Extraktion ausgelagert in extractors.py
- Scraping ausgelagert in scraper.py
"""

import aiohttp
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from ..rate_limiter import RateLimiter
from src.core.logger import get_logger, PerformanceLogger
from ..enhanced_search import get_mining_search_queries, get_mining_domains

from .proxy_manager import ProxyManager
from .extractors import MiningDataExtractor
from .scraper import BrightDataScraper


class BrightDataAgent(BaseAgent):
    """Bright Data Agent für Enterprise-Level Web Scraping"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].brightdata_key
        self.base_url = "https://api.brightdata.com"
        self._rate_limiter = RateLimiter(rate=100, per=60.0)  # 100 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="brightdata")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
        # Initialisiere Manager
        self.proxy_manager = ProxyManager()
        self.extractor = MiningDataExtractor(self.name, self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            # Initialisiere Scraper nach Session-Erstellung
            self.scraper = BrightDataScraper(
                self.api_key, self.base_url, self._session,
                self._rate_limiter, self.logger, self.timeout
            )
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Bright Data Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key und Proxy-Zugang"""
        if not self.api_key:
            self.logger.warning("Kein Bright Data API-Key konfiguriert")
            return False
            
        try:
            # Test Proxy-Verbindung
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self._session.get(
                f"{self.base_url}/account_info",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweitertes Mining-spezifisches Web Scraping mit Bright Data durch"""
        results = []
        
        self.perf_logger.start_timer(f"brightdata_search_{query.mine_name}")
        
        try:
            # Hole erweiterte Mining-Suchanfragen und Domains
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Bright Data: Starte Enterprise Mining-Suche")
            
            # 1. Erweiterte Web Search Collection
            search_urls = await self.scraper.collect_enhanced_mining_urls(
                query, mining_queries[:20], mining_domains[:20], self.status_callback
            )
            
            # 2. Parallel Deep Scraping mit verschiedenen Proxy-Typen
            if search_urls:
                scraping_tasks = []
                for idx, url in enumerate(search_urls[:30]):  # Mehr URLs für Mining
                    # Status-Update
                    if hasattr(self, 'status_callback') and self.status_callback and idx % 5 == 0:
                        await self.status_callback(f"Bright Data: Scrape {idx+1}/{min(len(search_urls), 30)} URLs")
                    
                    scraping_tasks.append(self._deep_mining_scrape(url, query, mining_queries))
                
                scraped_results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
                
                for result in scraped_results:
                    if isinstance(result, list):
                        results.extend(result)
            
            # 3. Erweiterte spezialisierte Datensammlung
            specialized_results = await self._collect_enhanced_specialized_data(query, mining_domains)
            results.extend(specialized_results)
            
            self.perf_logger.end_timer(
                f"brightdata_search_{query.mine_name}",
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
    
    async def _deep_mining_scrape(self, url: str, query: MineQuery, mining_queries: List[str]) -> List[SearchResult]:
        """Führt Deep Mining Scrape mit Bright Data Enterprise Features durch"""
        results = []
        
        try:
            # Hole Scraping-Parameter von Proxy Manager
            scrape_params = self.proxy_manager.get_scrape_params(
                url, 
                self._get_country_code(query.country),
                query.languages
            )
            
            # Führe Scraping durch
            content = await self.scraper.execute_scraping(scrape_params)
            
            if content:
                # Extrahiere strukturierte Daten
                extracted = self.extractor.extract_mining_data(content, url, query)
                results.extend(extracted)
                
                # ÄNDERUNG 17.06.2025: Dynamische Regierungsseiten-Erkennung
                # Government-Seiten werden durch generische Muster erkannt
                if self.proxy_manager._is_government_site(url):
                    gov_data = self.extractor.extract_government_data(content, url, query)
                    results.extend(gov_data)
        
        except Exception as e:
            self.logger.error(f"Proxy Scraping Fehler für {url}: {e}")
        
        return results
    
    async def _collect_enhanced_specialized_data(self, query: MineQuery, mining_domains: List[str]) -> List[SearchResult]:
        """Sammelt erweiterte spezialisierte Mining-Daten über Bright Data Datasets"""
        results = []
        
        # Erweiterte Mining-spezifische Datasets
        dataset_types = [
            'mining_companies',
            'environmental_compliance',
            'government_permits',
            'financial_filings',
            'technical_reports'
        ]
        
        # ÄNDERUNG 17.06.2025: Entfernt hardcodierte Länder-spezifische Datasets
        # Datasets werden dynamisch basierend auf verfügbaren Datenquellen ausgewählt
        
        for dataset_type in dataset_types:
            try:
                dataset_params = {
                    "dataset": dataset_type,
                    "filters": {
                        "company_name": {"contains": query.mine_name},
                        "industry": {"in": ["mining", "minerals", "extraction"]},
                        "country": query.country
                    },
                    "fields": ["all"]
                }
                
                dataset_results = await self.scraper.query_dataset(dataset_params)
                
                if dataset_results:
                    # Parse Dataset-spezifische Felder
                    for record in dataset_results:
                        parsed = self.extractor.parse_dataset_record(record, dataset_type, query)
                        results.extend(parsed)
                
            except Exception as e:
                self.logger.error(f"Dataset Query Fehler: {e}")
        
        return results
    
    def _get_country_code(self, country: str) -> str:
        """
        Konvertiert Ländernamen zu ISO-Code
        
        ÄNDERUNG 17.06.2025: Entfernt hardcodiertes Country-Mapping
        Dynamische Lösung: Nutze Landesname direkt oder hole Code über Agent
        """
        return country.lower()[:2] if country else "int"  # "int" für international
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Bright Data Agent beendet")