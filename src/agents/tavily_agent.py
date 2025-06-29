"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: Tavily Search Agent Implementation - Refaktoriert
# ÄNDERUNG 27.06.2025: Refaktoriert um unter 500 Zeilen zu bleiben
# Query-Building und Response-Parsing in separate Module extrahiert
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from .tavily_query_builder import TavilyQueryBuilder
from .tavily_response_parser import TavilyResponseParser
from src.core.logger import get_logger, PerformanceLogger
from src.utils.safe_dict_access import safe_get
from src.utils.retry_utils import async_retry
from src.core.monitoring import record_api_call
from src.utils.session_manager import SessionManager


class TavilyAgent(BaseAgent):
    """Tavily Agent für erweiterte Web-Recherche"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].tavily_key
        self.base_url = "https://api.tavily.com/search"
        # ÄNDERUNG 23.06.2025: Reduzierte Rate Limits zur Vermeidung von API-Limit Fehlern
        self._rate_limiter = RateLimiter(rate=5, per=60.0)  # Nur 5 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="tavily")
        self.perf_logger = PerformanceLogger(self.logger)
        
        # ÄNDERUNG 27.06.2025: Verwende extrahierte Module
        self.query_builder = TavilyQueryBuilder()
        self.response_parser = TavilyResponseParser(self.name)
        
        # Request-Cache zur Vermeidung von Duplikaten
        self._request_cache = {}
        self._cache_ttl = 300  # 5 Minuten Cache
        
    async def _ensure_session(self):
        """ÄNDERUNG 25.06.2025: Nutzt robustes Session Management"""
        if not hasattr(self, '_robust_session') or not hasattr(self, '_session_manager'):
            if not hasattr(self, '_session_manager'):
                self._session_manager = SessionManager()
            self._robust_session = await self._session_manager.get_robust_session(f"tavily_{self.name}", timeout=60)
    
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            # ÄNDERUNG 25.06.2025: Nutze robustes Session Management mit SessionManager Instanz
            self._session_manager = SessionManager()
            self._robust_session = await self._session_manager.get_robust_session(f"tavily_{self.name}", timeout=60)
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Tavily Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        # ÄNDERUNG 25.06.2025: Nutze SessionManager für Cleanup
        if hasattr(self, '_session_manager'):
            await self._session_manager.close_session(f"tavily_{self.name}")
        self.logger.info("Tavily Agent beendet")
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein Tavily API-Key konfiguriert")
            return False
            
        try:
            # Stelle sicher, dass Session verfügbar ist
            await self._ensure_session()
            
            # Test-Suche
            payload = {
                "api_key": self.api_key,
                "query": "test",
                "max_results": 1
            }
            
            async with self._robust_session.request(
                'POST',
                self.base_url,
                json=payload,
                timeout=10
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Alias für search_mine - für Kompatibilität mit Source Discovery"""
        return await self.search_mine(query)
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Suche mit Tavily durch"""
        results = []
        self.perf_logger.start_timer(f"tavily_search_{query.mine_name}")
        
        try:
            # ÄNDERUNG 27.06.2025: Verwende Query Builder
            search_queries = self.query_builder.create_search_queries(query)
            
            # Execute searches with different strategies
            for search_type, search_query in search_queries.items():
                # Check Cache
                cache_key = self.query_builder.create_query_hash(search_query)
                if cache_key in self._request_cache:
                    cached_time, cached_results = self._request_cache[cache_key]
                    if (datetime.now() - cached_time).seconds < self._cache_ttl:
                        self.logger.info(f"Using cached results for {search_type}")
                        results.extend(cached_results)
                        continue
                
                self.logger.info(f"Executing {search_type} search: {search_query[:100]}...")
                
                # Make API call
                response = await self._make_api_call(search_query, search_type)
                if response:
                    # ÄNDERUNG 27.06.2025: Verwende Response Parser
                    parsed_results = self.response_parser.parse_response(response, query, search_type)
                    
                    # Cache results
                    self._request_cache[cache_key] = (datetime.now(), parsed_results)
                    results.extend(parsed_results)
                    
                    # Log findings
                    for result in parsed_results:
                        self.logger.info(f"Found: {result.field_name} = {result.value}")
                
                # Respect rate limit
                await asyncio.sleep(1)
            
            self.perf_logger.end_timer(
                f"tavily_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Update statistics
            self.stats['total_requests'] += len(search_queries)
            self.stats['successful_requests'] += 1 if results else 0
            self.stats['total_fields_found'] += len(results)
            
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            self.stats['failed_requests'] += 1
            
        return results
    
    @async_retry(max_attempts=3, delay=2.0)
    async def _make_api_call(self, query: str, search_type: str) -> Optional[Dict[str, Any]]:
        """Macht API-Aufruf zu Tavily mit Retry-Logik"""
        # Ensure session
        await self._ensure_session()
        
        # Rate limiting
        await self._rate_limiter.acquire()
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": False,
            "max_results": 10,
            "include_domains": self._get_include_domains(search_type),
            "exclude_domains": ["wikipedia.org", "wikidata.org"]
        }
        
        # Add topic if government search
        if search_type == "government":
            payload["topic"] = "general"
            payload["days"] = 365  # Last year
        
        # Monitor API call
        start_time = datetime.now()
        success = False
        
        try:
            async with self._robust_session.request(
                'POST',
                self.base_url,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = True
                    return data
                elif response.status == 429:
                    self.logger.warning("Rate limit reached, waiting...")
                    await asyncio.sleep(60)  # Wait 1 minute
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"API error {response.status}: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout for query: {query[:50]}...")
            return None
        except Exception as e:
            self.logger.error(f"API call error: {type(e).__name__}: {e}")
            return None
        finally:
            # Record monitoring data
            duration = (datetime.now() - start_time).total_seconds()
            record_api_call("tavily", success, duration, {"search_type": search_type})
    
    def _get_include_domains(self, search_type: str) -> List[str]:
        """Gibt relevante Domains für Suchtyp zurück"""
        domain_map = {
            "operator": [
                "miningintelligence.com",
                "globaldata.com", 
                "mining.com",
                "minedocs.com",
                "northernminer.com"
            ],
            "coordinates": [
                "mindat.org",
                "mrdata.usgs.gov",
                "nrcan.gc.ca",
                "mern.gouv.qc.ca"
            ],
            "production": [
                "kitco.com",
                "mining-journal.com",
                "infomine.com",
                "resourceworld.com"
            ],
            "environmental": [
                "mining.ca",
                "miningwatch.ca",
                "ec.gc.ca",
                "canada.ca"
            ],
            "government": [
                "nrcan.gc.ca",
                "mern.gouv.qc.ca",
                "ontario.ca",
                "gov.bc.ca",
                "canada.ca"
            ],
            "status": [
                "mining.com",
                "northernminer.com",
                "miningnewsnorth.com"
            ],
            "news": [
                "mining.com",
                "northernminer.com", 
                "canadianminingjournal.com",
                "miningreview.com"
            ]
        }
        
        return domain_map.get(search_type, [])