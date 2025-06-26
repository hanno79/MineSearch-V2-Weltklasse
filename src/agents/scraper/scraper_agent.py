"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Web Scraper Agent Implementation
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from ..rate_limiter import RateLimiter
from src.core.logger import get_logger, PerformanceLogger
from ..enhanced_search import get_mining_search_queries, get_mining_domains
from src.utils.session_manager import SessionManager

from .extractors import DataExtractor
from .sources import MiningSourceManager
from .registry_scrapers import QuebecRegistryScraper, OntarioRegistryScraper, BCRegistryScraper


class ScraperAgent(BaseAgent):
    """Web Scraping Agent für Mining-Informationen"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.scraping_config = config['scraping_config']
        self._rate_limiter = RateLimiter(rate=60, per=60.0)  # 60 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="scraper")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
        # User-Agents für Rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        self.current_ua_index = 0
        
        # Erweiterte Mining-Informationsquellen
        self.source_manager = MiningSourceManager()
        self.mining_sources = self.source_manager.get_mining_sources()
        
        # Data Extractor
        self.extractor = DataExtractor(self.logger)
        
        # Session Manager für zentrale Session-Verwaltung
        self._session_manager = None
        self._robust_session = None
        
    async def initialize(self) -> bool:
        """Initialisiert den Scraper Agent"""
        try:
            # ÄNDERUNG 25.06.2025: Verwende SessionManager Instanz
            self._session_manager = SessionManager()
            self._robust_session = await self._session_manager.get_robust_session(f"scraper_{self.name}", timeout=self.timeout.total)
            self.logger.info("Scraper Agent mit SessionManager initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Scraper benötigt keine Credentials"""
        return True
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweiterte Mining-spezifisches Web-Scraping durch"""
        results = []
        
        # ÄNDERUNG 21.06.2025: Debug-Logging für Suche
        self.logger.info(f"DEBUG: Scraper startet Suche für Mine: {query.mine_name}")
        self.logger.info(f"DEBUG: Gesuchte Felder: {query.required_fields}")
        
        self.perf_logger.start_timer(f"scraper_search_{query.mine_name}")
        
        try:
            # ÄNDERUNG 20.06.2025: Check für Cancellation vor Beginn
            if self._cancellation_token and self._cancellation_token.is_cancelled():
                self.logger.info("Suche wurde abgebrochen bevor sie begann")
                return []
            
            # Hole erweiterte Mining-Suchanfragen
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            
            # Suche auf verschiedenen Seiten
            search_tasks = []
            
            # Erweiterte Google-Suche mit mehreren Queries
            for idx, mining_query in enumerate(mining_queries[:15]):
                search_tasks.append(self._enhanced_search(query, mining_query, idx))
            
            # Direkte Suche auf Mining-spezifischen Seiten
            search_tasks.append(self._search_mining_sites(query))
            
            # Direkte Suche auf bekannten Mining-Seiten
            if query.country == "Canada":
                search_tasks.append(self._search_canadian_sources(query))
            
            # Government und Regulatory Websites
            search_tasks.append(self._search_government_sources(query))
            
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Scraper: Starte {len(search_tasks)} Mining-Suchen")
            
            # Führe alle Suchen parallel aus
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Verarbeite Ergebnisse
            for result in search_results:
                if isinstance(result, list):
                    results.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Suchfehler: {result}")
            
            # ÄNDERUNG 21.06.2025: Debug-Logging für gefundene Ergebnisse
            self.logger.info(f"DEBUG: Scraper fand {len(results)} Ergebnisse für {query.mine_name}")
            for i, result in enumerate(results[:5]):  # Erste 5 Ergebnisse loggen
                self.logger.info(f"DEBUG: Ergebnis {i+1} für {query.mine_name}: {result.field_name}={result.value[:100]}")
            
            self.perf_logger.end_timer(
                f"scraper_search_{query.mine_name}",
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei Scraper-Suche: {e}")
            return results
    
    async def _enhanced_search(self, query: MineQuery, search_query: str, idx: int) -> List[SearchResult]:
        """Erweiterte Suche mit Mining-spezifischen Queries"""
        results = []
        
        try:
            # Status-Update
            if hasattr(self, 'status_callback') and self.status_callback:
                await self.status_callback(f"Scraper: Mining-Suche {idx + 1} - {search_query[:50]}...")
            
            # ÄNDERUNG 21.06.2025: Keine simulierte Suche - nur Log
            self.logger.info(f"Mining-Suche: {search_query}")
            
            # ÄNDERUNG 22.06.2025: NOT_IMPLEMENTED - Benötigt externe Such-API
            # Implementierung erfordert Google Custom Search API oder Bing Search API
            # Momentan: Keine Mock-Daten zurückgeben
            
            await asyncio.sleep(self.scraping_config.delay_seconds)
            
        except Exception as e:
            self.logger.error(f"Erweiterte Suche fehlgeschlagen: {e}")
        
        return results
    
    async def _search_mining_sites(self, query: MineQuery) -> List[SearchResult]:
        """Durchsucht Mining-spezifische Websites"""
        results = []
        mining_domains = get_mining_domains()
        
        # Stelle sicher, dass Session verfügbar ist
        await self._ensure_session()
        
        # Durchsuche Top Mining-Websites
        for domain in mining_domains[:10]:
            # ÄNDERUNG 20.06.2025: Check für Cancellation in der Schleife
            if self._cancellation_token and self._cancellation_token.is_cancelled():
                self.logger.info("Suche wurde während Mining-Sites Durchsuchung abgebrochen")
                break
                
            try:
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(f"Scraper: Durchsuche {domain}")
                
                # Konstruiere Suchurl für die Domain
                search_url = self.source_manager.get_search_url(domain, query.mine_name)
                
                # Scrape die Seite
                page_results = await self._scrape_page(search_url, query)
                results.extend(page_results)
                
                await asyncio.sleep(self.scraping_config.delay_seconds)
                
            except Exception as e:
                self.logger.error(f"Fehler beim Scraping von {domain}: {e}")
        
        return results
    
    async def _search_government_sources(self, query: MineQuery) -> List[SearchResult]:
        """Durchsucht Regierungs- und Regulatory-Websites"""
        results = []
        
        # Stelle sicher, dass Session verfügbar ist
        await self._ensure_session()
        
        # Government-spezifische URLs
        urls_to_search = self.source_manager.get_government_urls(query.country, query.region)
        
        for url_template in urls_to_search:
            try:
                # Ersetze Platzhalter
                url = url_template.replace('{query}', query.mine_name)
                page_results = await self._scrape_page(url, query)
                results.extend(page_results)
                await asyncio.sleep(self.scraping_config.delay_seconds)
            except Exception as e:
                self.logger.error(f"Government source scraping error: {e}")
        
        return results
    
    async def _search_canadian_sources(self, query: MineQuery) -> List[SearchResult]:
        """Suche auf kanadischen Regierungsseiten"""
        results = []
        
        # Stelle sicher, dass Session verfügbar ist
        await self._ensure_session()
        
        # Quebec Mining Registry
        if query.region.lower() == "quebec":
            scraper = QuebecRegistryScraper(self._session, self.logger)
            results.extend(await scraper.search(query, self.timeout))
        
        # Ontario Mining Lands
        elif query.region.lower() == "ontario":
            scraper = OntarioRegistryScraper(self._session, self.logger)
            results.extend(await scraper.search(query, self.timeout))
        
        # British Columbia
        elif query.region.lower() in ["british columbia", "bc"]:
            scraper = BCRegistryScraper(self._session, self.logger)
            results.extend(await scraper.search(query, self.timeout))
        
        return results
    
    async def _safe_request(self, url: str, max_retries: int = 3) -> Optional[str]:
        """ÄNDERUNG 20.06.2025: Sichere HTTP-Request Methode mit Retry-Logik"""
        await self._ensure_session()
        
        for attempt in range(max_retries):
            try:
                # ÄNDERUNG 25.06.2025: Rotiere User-Agent für jede Request
                self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
                user_agent = self.user_agents[self.current_ua_index]
                
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                async with self._robust_session.request('GET', url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:  # Rate limit
                        wait_time = min(2 ** attempt, 10)  # Exponential backoff
                        self.logger.warning(f"Rate limit erreicht, warte {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        self.logger.warning(f"HTTP {response.status} für {url}")
                        return None
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout bei {url} (Versuch {attempt + 1}/{max_retries})")
            except Exception as e:
                self.logger.error(f"Request-Fehler für {url}: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(1)
        
        return None
    
    async def _ensure_session(self):
        """ÄNDERUNG 25.06.2025: Stellt sicher, dass Session über SessionManager verfügbar ist"""
        # Prüfe ob Session existiert und gültig ist
        if (not hasattr(self, '_robust_session') or self._robust_session is None or 
            not hasattr(self, '_session_manager') or self._session_manager is None):
            self.logger.info("Session wird neu initialisiert")
            if not hasattr(self, '_session_manager') or self._session_manager is None:
                self._session_manager = SessionManager()
            self._robust_session = await self._session_manager.get_robust_session(f"scraper_{self.name}", timeout=self.timeout.total)
        else:
            # Prüfe ob die Session noch gültig ist
            if self._robust_session is not None:
                try:
                    session = await self._robust_session.get_session()
                    if session.closed:
                        self.logger.info("Session war geschlossen, erstelle neue")
                        self._robust_session = await self._session_manager.get_robust_session(f"scraper_{self.name}", timeout=self.timeout.total)
                except Exception as e:
                    self.logger.warning(f"Session-Check fehlgeschlagen: {e}, erstelle neue")
                    self._robust_session = await self._session_manager.get_robust_session(f"scraper_{self.name}", timeout=self.timeout.total)
            else:
                # Session ist None, erstelle neue
                self.logger.info("Session war None, erstelle neue")
                self._robust_session = await self._session_manager.get_robust_session(f"scraper_{self.name}", timeout=self.timeout.total)
    
    async def _scrape_page(self, url: str, query: MineQuery) -> List[SearchResult]:
        """Scraped eine einzelne Seite nach Mining-Informationen"""
        results = []
        
        try:
            # ÄNDERUNG 21.06.2025: Debug-Logging für URL
            self.logger.info(f"DEBUG: Scraping URL: {url}")
            
            # ÄNDERUNG 20.06.2025: Verwende sichere Request-Methode
            html = await self._safe_request(url)
            if not html:
                self.logger.warning(f"Keine HTML-Daten von {url} erhalten")
                return results
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extrahiere verschiedene Informationen
            text = soup.get_text()
            
            # ÄNDERUNG 21.06.2025: Strenge Validierung des HTML-Contents
            self.logger.info(f"DEBUG: HTML Text-Länge von {url}: {len(text)} Zeichen")
            
            # Prüfe auf Fehlerseiten
            error_indicators = ['404', '403', 'not found', 'access denied', 'forbidden', 'error']
            text_lower = text.lower()[:500]  # Erste 500 Zeichen für Fehlerprüfung
            
            if len(text) < 200:  # Erhöht von 100 auf 200
                self.logger.warning(f"Text zu kurz ({len(text)} Zeichen), ignoriere {url}")
                return results
                
            if any(indicator in text_lower for indicator in error_indicators):
                self.logger.warning(f"Mögliche Fehlerseite erkannt auf {url}")
                return results
            
            # Prüfe ob Mining-relevanter Content vorhanden
            mining_keywords = ['mine', 'mining', 'mineral', 'resource', query.mine_name.lower()]
            if not any(keyword in text.lower() for keyword in mining_keywords):
                self.logger.warning(f"Kein Mining-relevanter Content auf {url}")
                return results
            
            # Betreiber/Eigentümer
            operator = self.extractor.extract_operator(text, query.mine_name)
            if operator:
                results.append(SearchResult(
                    mine_name=query.mine_name,
                    field_name='betreiber',
                    value=operator,
                    source=f'Web Scraping: {url}',
                    source_url=url,
                    source_date=datetime.now().year,
                    confidence_score=0.8,
                    agent_name=self.name,
                    timestamp=datetime.now(),
                    metadata={'scraping_method': 'regex'}
                ))
            
            # Koordinaten
            coords = self.extractor.extract_coordinates(soup)
            if coords:
                coord_str = f"{coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')}"
                results.append(SearchResult(
                    mine_name=query.mine_name,
                    field_name='koordinaten',
                    value=coord_str,
                    source=f'Web Scraping: {url}',
                    source_url=url,
                    source_date=datetime.now().year,
                    confidence_score=0.85,
                    agent_name=self.name,
                    timestamp=datetime.now(),
                    metadata={'format': 'lat,lon'}
                ))
            
            # Sanierungskosten
            costs = self.extractor.extract_costs(text)
            if costs and costs.get('value'):
                # ÄNDERUNG 22.06.2025: Entfernung der Mock-Wert-Blacklist - keine aktuelle Quelle gefunden
                cost_value = costs['value']
                
                # Validiere Kostenkontext
                if self.extractor.validate_cost_context(text, cost_value):
                    value = f"{cost_value:,.0f} {costs.get('currency', 'CAD')}"
                    self.logger.info(f"Validierte Kosten gefunden: {value} von {url}")
                    
                    results.append(SearchResult(
                        mine_name=query.mine_name,
                        field_name='sanierungskosten',
                        value=value,
                        source=f'Web Scraping: {url}',
                        source_url=url,
                        source_date=datetime.now().year,
                        confidence_score=0.75,
                        agent_name=self.name,
                        timestamp=datetime.now(),
                        metadata={
                            'currency': costs.get('currency', 'CAD'),
                            'validated': True
                        }
                    ))
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Scraping von {url}: {e}")
        
        return results
    
    async def cleanup(self):
        """ÄNDERUNG 25.06.2025: Cleanup mit SessionManager"""
        # Session cleanup
        if hasattr(self, '_session_manager') and self._session_manager:
            try:
                await self._session_manager.close_session(f"scraper_{self.name}")
                self.logger.debug("Session erfolgreich geschlossen")
            except Exception as e:
                self.logger.warning(f"Fehler beim Session Cleanup: {e}")
        
        # Setze Session auf None
        self._robust_session = None
        
        # Rufe parent cleanup auf
        try:
            await super().cleanup()
        except Exception as e:
            self.logger.warning(f"Fehler beim parent cleanup: {e}")
        
        self.logger.info("Scraper Agent beendet")
