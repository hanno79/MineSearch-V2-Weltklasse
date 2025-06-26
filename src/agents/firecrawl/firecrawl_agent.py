"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Firecrawl Web Scraping Agent Implementation
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from ..rate_limiter import RateLimiter
from src.core.logger import get_logger, PerformanceLogger
# ÄNDERUNG 24.06.2025: Nutze Session Manager
from src.utils.session_manager import SessionManager

from .url_builder import FirecrawlURLBuilder
from .extractors import FirecrawlDataExtractor


class FirecrawlAgent(BaseAgent):
    """Firecrawl Agent für intelligentes Web Crawling und Datenextraktion"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].firecrawl_key
        self.base_url = "https://api.firecrawl.dev/v1"
        # ÄNDERUNG 24.06.2025: Reduziertes Rate Limit für Firecrawl (max 10/min laut Logs)
        self._rate_limiter = RateLimiter(rate=8, per=60.0)  # 8 Anfragen pro Minute mit Puffer
        self.logger = get_logger(f"agent.{name}", agent_type="firecrawl")
        self.perf_logger = PerformanceLogger(self.logger)
        
        # Komponenten
        self.url_builder = FirecrawlURLBuilder()
        self.data_extractor = FirecrawlDataExtractor(self.name, self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            # ÄNDERUNG 24.06.2025: Nutze Session Manager statt direkte Session
            session_manager = SessionManager()
            self._session = await session_manager.get_session(f"firecrawl_{self.name}")
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Firecrawl Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key"""
        if not self.api_key:
            self.logger.warning("Kein Firecrawl API-Key konfiguriert")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test mit einfacher URL die schnell antwortet
            payload = {
                "url": "https://httpbin.org/html",
                "formats": ["markdown"]
            }
            
            async with self._session.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 201]:
                    self.logger.info("Firecrawl API-Key erfolgreich validiert")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Firecrawl Validierung fehlgeschlagen ({response.status}): {error_text}")
                    return False
                
        except aiohttp.ClientTimeout:
            self.logger.error("Firecrawl Validierung Timeout - API antwortet nicht rechtzeitig")
            return False
        except Exception as e:
            self.logger.error(f"Firecrawl Validierung fehlgeschlagen: {type(e).__name__}: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt intelligentes Web Crawling für Mine durch"""
        results = []
        
        self.perf_logger.start_timer(f"firecrawl_search_{query.mine_name}")
        
        try:
            # 1. Erstelle Seed-URLs für Crawling
            seed_urls = self.url_builder.create_seed_urls(query)
            
            # 2. Starte Crawl für Mining-Websites
            for seed_url in seed_urls:
                crawl_results = await self._crawl_website(seed_url, query)
                results.extend(crawl_results)
                
                # ÄNDERUNG 24.06.2025: Längere Pause zwischen Crawls
                await asyncio.sleep(8)  # Mindestens 8 Sekunden zwischen Requests
            
            # 3. Gezieltes Scraping auf bekannten URLs
            targeted_results = await self._targeted_scraping(query)
            results.extend(targeted_results)
            
            self.perf_logger.end_timer(
                f"firecrawl_search_{query.mine_name}",
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei Firecrawl-Suche: {e}")
            return results
    
    async def _crawl_website(self, url: str, query: MineQuery) -> List[SearchResult]:
        """Crawlt eine Website nach Mining-Informationen"""
        results = []
        
        # ÄNDERUNG 20.06.2025: Check für Cancellation
        if self._cancellation_token and self._cancellation_token.is_cancelled():
            self.logger.info("Crawl wurde abgebrochen")
            return results
        
        # Starte Crawl
        job_id = await self._start_crawl(url, query)
        if not job_id:
            return results
        
        # Warte auf Completion
        crawl_data = await self._wait_for_crawl(job_id)
        if not crawl_data:
            return results
        
        # Extrahiere aus gecrawlten Seiten
        pages = crawl_data.get('data', [])
        for page in pages[:10]:  # Limitiere auf erste 10 Seiten
            if 'markdown' in page:
                extracted = self.data_extractor.extract_from_content(
                    page['markdown'], 
                    page.get('url', url), 
                    query
                )
                results.extend(extracted)
        
        return results
    
    async def _start_crawl(self, url: str, query: MineQuery) -> Optional[str]:
        """Startet einen Crawl-Job"""
        # ÄNDERUNG 23.06.2025: Retry-Logik für Rate Limiting
        max_retries = 3
        base_delay = 5
        
        for attempt in range(max_retries):
            await self._rate_limiter.acquire()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Crawl-Konfiguration
            payload = self.url_builder.create_crawl_config(query, url)
            
            try:
                async with self._session.post(
                    f"{self.base_url}/crawl",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return data.get('jobId')
                    elif response.status == 429:
                        # Rate limit erreicht
                        retry_after = int(response.headers.get('Retry-After', base_delay * (2 ** attempt)))
                        self.logger.warning(f"Rate limit bei Crawl-Start. Warte {retry_after}s (Versuch {attempt+1}/{max_retries})")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            self.logger.error(f"Crawl-Start fehlgeschlagen nach {max_retries} Versuchen")
                            return None
                    elif response.status == 402:
                        # Insufficient credits
                        self.logger.error("Firecrawl: Unzureichende Credits für Crawl. Agent wird deaktiviert.")
                        self.status = AgentStatus.DISABLED
                        return None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Crawl Start Fehler: {response.status} - {error_text}")
                        return None
                        
            except Exception as e:
                self.logger.error(f"Crawl Start Exception: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                return None
        
        return None
    
    async def _wait_for_crawl(self, job_id: str, max_wait: int = 120) -> Optional[Dict[str, Any]]:
        """Wartet auf Crawl-Completion"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            
            try:
                async with self._session.get(
                    f"{self.base_url}/crawl/status/{job_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status')
                        
                        if status == 'completed':
                            return data
                        elif status in ['failed', 'cancelled']:
                            self.logger.error(f"Crawl fehlgeschlagen: {status}")
                            return None
                            
            except Exception as e:
                self.logger.error(f"Crawl Status Check Fehler: {e}")
        
        return None
    
    async def _targeted_scraping(self, query: MineQuery) -> List[SearchResult]:
        """Führt gezieltes Scraping auf bekannten URLs durch"""
        results = []
        
        # Erstelle gezielte URLs basierend auf Minenname
        target_urls = self.url_builder.create_targeted_urls(query)
        
        # Scrape jede URL
        for url in target_urls:
            try:
                results_from_url = await self._scrape_single_url(url, query)
                results.extend(results_from_url)
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Targeted Scraping Fehler für {url}: {e}")
        
        return results
    
    async def _scrape_single_url(self, url: str, query: MineQuery) -> List[SearchResult]:
        """Scraped eine einzelne URL"""
        # ÄNDERUNG 23.06.2025: Exponential Backoff für Rate Limiting
        max_retries = 3
        base_delay = 5
        
        for attempt in range(max_retries):
            await self._rate_limiter.acquire()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True
            }
            
            try:
                async with self._session.post(
                    f"{self.base_url}/scrape",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        markdown = data.get('data', {}).get('markdown', '')
                        return self.data_extractor.extract_from_content(markdown, url, query)
                    elif response.status == 429:
                        # Rate limit erreicht
                        retry_after = int(response.headers.get('Retry-After', base_delay * (2 ** attempt)))
                        self.logger.warning(f"Rate limit erreicht für {url}. Warte {retry_after}s (Versuch {attempt+1}/{max_retries})")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            self.logger.error(f"Rate limit nach {max_retries} Versuchen für {url}")
                            return []
                    elif response.status == 402:
                        # Insufficient credits
                        self.logger.error("Firecrawl: Unzureichende Credits. Agent wird deaktiviert.")
                        self.status = AgentStatus.DISABLED
                        return []
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Scrape Fehler ({response.status}): {error_text}")
                        return []
                        
            except Exception as e:
                self.logger.error(f"Scrape Single URL Fehler: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                return []
        
        return []
    
    async def cleanup(self):
        """Cleanup der Session"""
        try:
            # ÄNDERUNG 24.06.2025: Nutze Session Manager für Cleanup
            session_manager = SessionManager()
            await session_manager.close_session(f"firecrawl_{self.name}")
            self.logger.debug("Session erfolgreich geschlossen")
        except Exception as e:
            self.logger.warning(f"Fehler beim Schließen der Session: {e}")
        finally:
            self._session = None
            await super().cleanup()
