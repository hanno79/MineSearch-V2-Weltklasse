"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: Perplexity Agent Implementation - Refaktoriert für bessere Modularität
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from urllib.parse import urlparse

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from src.core.cancellation import CancellationException
from .rate_limiter import RateLimiter
from .enhanced_search import get_mining_search_queries, get_mining_domains
from src.core.logger import get_logger, PerformanceLogger
from src.utils.safe_dict_access import safe_get, safe_nested_get, ensure_dict, ensure_list
from src.utils.session_manager import SessionManager
from .perplexity_prompt_builder import PerplexityPromptBuilder
from .perplexity_response_parser import PerplexityResponseParser


class PerplexityAgent(BaseAgent):
    """Perplexity Agent für Web-basierte Recherche"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].perplexity_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-reasoning-pro"  # ÄNDERUNG 24.06.2025: Enhanced reasoning model für bessere Ergebnisse
        # ÄNDERUNG 23.06.2025: Reduziertes Rate Limit
        self._rate_limiter = RateLimiter(rate=5, per=60.0)  # Nur 5 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="perplexity")
        self.perf_logger = PerformanceLogger(self.logger)
        # Request-Cache zur Vermeidung von Duplikaten
        self._request_cache = {}
        self._cache_ttl = 300  # 5 Minuten Cache
        # ÄNDERUNG 27.06.2025: Initialisiere Prompt Builder und Response Parser
        self._prompt_builder = PerplexityPromptBuilder()
        self._response_parser = PerplexityResponseParser(name)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            # ÄNDERUNG 27.06.2025: Robuste Event Loop Prüfung
            try:
                loop_id = id(asyncio.get_running_loop())
                self.logger.debug(f"[PerplexityAgent] Initialisierung im Loop {loop_id}")
            except RuntimeError:
                self.logger.error("Keine laufende Event Loop bei Initialisierung")
                return False
                
            # ÄNDERUNG 27.06.2025: Verwende SessionManager aus Config wenn vorhanden
            if isinstance(self.config, dict) and 'session_manager' in self.config and self.config['session_manager']:
                self._session_manager = self.config['session_manager']
                self.logger.info("Verwende übergebenen SessionManager")
            else:
                self._session_manager = SessionManager()
                self.logger.info("Erstelle neuen SessionManager")
            self._session = await self._session_manager.get_session(f"perplexity_{self.name}")
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
            self.logger.info("Perplexity Agent erfolgreich initialisiert")
            return True
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        # ÄNDERUNG 25.06.2025: Robusteres Cleanup mit besserer Fehlerbehandlung
        try:
            loop_id = id(asyncio.get_running_loop())
            self.logger.debug(f"[PerplexityAgent] Cleanup im Loop {loop_id}")
        except RuntimeError:
            self.logger.debug("[PerplexityAgent] Cleanup ohne aktiven Event Loop")
        
        # Session cleanup
        if hasattr(self, '_session_manager') and self._session_manager:
            try:
                await self._session_manager.close_session(f"perplexity_{self.name}")
                self.logger.debug("Session erfolgreich geschlossen")
            except Exception as e:
                self.logger.warning(f"Fehler beim Session Cleanup: {e}")
        
        # Setze Session auf None
        self._session = None
        self._robust_session = None
        
        # Rufe parent cleanup auf
        try:
            await super().cleanup()
        except Exception as e:
            self.logger.warning(f"Fehler beim parent cleanup: {e}")
        
        self.logger.info("Perplexity Agent beendet")
    
    async def _ensure_session(self):
        """ÄNDERUNG 27.06.2025: Stellt sicher, dass Session verfügbar ist"""
        # Event Loop muss bereits laufen - keine dynamische Erstellung
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
            self.logger.debug(f"[PerplexityAgent] _ensure_session im Loop {loop_id}")
        except RuntimeError as e:
            # Kein laufender Event Loop - das ist ein Fehler
            self.logger.error("[PerplexityAgent] Kein laufender Event Loop - kann keine Session erstellen")
            raise RuntimeError("No running event loop - cannot create session") from e
        
        # ÄNDERUNG 27.06.2025: Vereinfachte Session-Prüfung mit SessionManager
        if not hasattr(self, '_session_manager') or self._session_manager is None:
            self.logger.info(f"[PerplexityAgent] Erstelle neuen SessionManager im Loop {loop_id}")
            # Verwende SessionManager aus Config wenn vorhanden
            if hasattr(self.config, 'session_manager') and self.config.session_manager:
                self._session_manager = self.config.session_manager
            else:
                self._session_manager = SessionManager()
        
        # Verwende RobustSession für erweiterte Kontrolle
        if not hasattr(self, '_robust_session') or self._robust_session is None:
            self.logger.info(f"[PerplexityAgent] Hole RobustSession vom SessionManager")
            self._robust_session = await self._session_manager.get_robust_session(
                f"perplexity_{self.name}", 
                timeout=90
            )
        
        # Hole die aktuelle aiohttp Session
        self._session = await self._robust_session.get_session()
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein Perplexity API-Key konfiguriert")
            return False
            
        try:
            # Stelle sicher, dass Session verfügbar ist
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Einfache Test-Anfrage
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 16  # ÄNDERUNG 24.06.2025: Minimum 16 für API-Kompatibilität
            }
            
            # ÄNDERUNG 27.06.2025: Verwende normalen SessionManager mit async context
            # ÄNDERUNG 27.06.2025: Timeout als Integer (Fix für RuntimeError)
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    self.logger.info("Perplexity API-Key erfolgreich validiert")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Perplexity Validierung fehlgeschlagen ({response.status}): {error_text}")
                    return False
                
        except aiohttp.ClientTimeout:
            self.logger.error("Perplexity Validierung Timeout - API antwortet nicht rechtzeitig")
            return False
        except Exception as e:
            self.logger.error(f"Perplexity Validierung fehlgeschlagen: {type(e).__name__}: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Suche mit Perplexity durch"""
        results = []
        
        self.perf_logger.start_timer(f"perplexity_search_{query.mine_name}")
        
        try:
            # ÄNDERUNG 26.06.2025: Prüfe Cancellation Token zu Beginn
            if self._cancellation_token and self._cancellation_token.is_cancelled():
                self.logger.info("Suche wurde abgebrochen (vor Start)")
                raise CancellationException("Search cancelled")
            # Get enhanced search queries
            search_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # ÄNDERUNG 23.06.2025: Reduzierte Query-Anzahl und Caching
            priority_queries = search_queries[:3]  # Nur Top 3 queries
            
            # Execute searches with different query strategies
            for idx, search_query in enumerate(priority_queries):
                # ÄNDERUNG 26.06.2025: Prüfe Cancellation vor jeder Query
                if self._cancellation_token and self._cancellation_token.is_cancelled():
                    self.logger.info(f"Suche abgebrochen nach {idx} Queries")
                    raise CancellationException("Search cancelled during query execution")
                
                # Check Cache
                cache_key = f"{query.mine_name}_{search_query[:50]}"
                if cache_key in self._request_cache:
                    cached_time, cached_response = self._request_cache[cache_key]
                    if (datetime.now() - cached_time).seconds < self._cache_ttl:
                        self.logger.info(f"Using cached response for query {idx+1}")
                        # ÄNDERUNG 27.06.2025: Verwende ResponseParser für Response-Parsing
                        parsed_results = self._response_parser.parse_response(cached_response, query, f"query_{idx+1}_cached")
                        results.extend(parsed_results)
                        continue
                
                self.logger.info(f"Perplexity-Suche {idx+1}/{len(priority_queries)}: {search_query[:100]}...")
                
                # ÄNDERUNG 27.06.2025: Verwende PromptBuilder für Prompt-Erstellung
                prompt = self._prompt_builder.create_enhanced_prompt(query, search_query, mining_domains[:5])
                
                response = await self._make_api_call(prompt)
                if response:
                    # Cache successful response
                    self._request_cache[cache_key] = (datetime.now(), response)
                    # ÄNDERUNG 27.06.2025: Verwende ResponseParser für Response-Parsing
                    parsed_results = self._response_parser.parse_response(response, query, f"query_{idx+1}")
                    results.extend(parsed_results)
                    
                # Längere Pause zwischen Anfragen
                await asyncio.sleep(3)
            
            # ÄNDERUNG 27.06.2025: Verwende PromptBuilder für spezialisierte Prompts
            prompts = self._prompt_builder.create_prompts(query)
            for search_type, prompt in prompts.items():
                # ÄNDERUNG 26.06.2025: Prüfe Cancellation vor spezialisierten Suchen
                if self._cancellation_token and self._cancellation_token.is_cancelled():
                    self.logger.info(f"Suche abgebrochen vor {search_type} Suche")
                    raise CancellationException("Search cancelled during specialized search")
                self.logger.info(f"Perplexity-Spezialisierte Suche: {search_type}")
                
                response = await self._make_api_call(prompt)
                if response:
                    # ÄNDERUNG 27.06.2025: Verwende ResponseParser für Response-Parsing
                    parsed_results = self._response_parser.parse_response(response, query, search_type)
                    results.extend(parsed_results)
                    
                await asyncio.sleep(1)
            
            self.perf_logger.end_timer(
                f"perplexity_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Update Statistiken
            self.stats['total_requests'] += len(priority_queries) + len(prompts)
            self.stats['successful_requests'] += 1 if results else 0
            self.stats['total_fields_found'] += len(results)
            
        except CancellationException:
            # ÄNDERUNG 26.06.2025: Bei Abbruch keine Fehler loggen
            self.logger.info("Perplexity-Suche wurde abgebrochen")
            self.perf_logger.end_timer(
                f"perplexity_search_{query.mine_name}",
                results_found=len(results),
                status="cancelled"
            )
            raise
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self.stats['failed_requests'] += 1
            
        return results
    
    
    async def _make_api_call(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Macht API-Aufruf zu Perplexity"""
        # ÄNDERUNG 26.06.2025: Prüfe Cancellation vor API Call
        if self._cancellation_token and self._cancellation_token.is_cancelled():
            self.logger.info("API Call abgebrochen (vor Request)")
            raise CancellationException("API call cancelled")
        
        loop_id = id(asyncio.get_running_loop())
        self.logger.debug(f"[PerplexityAgent] _make_api_call im Loop {loop_id}")
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # ÄNDERUNG 27.06.2025: Verwende System-Prompt aus PromptBuilder
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._prompt_builder.get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,  # Sehr niedrig für faktische Genauigkeit
            "max_tokens": 2500,
            "web_search": True,  # Aktiviere Web-Suche
            "return_citations": True  # Gebe Quellen zurück
        }
        
        try:
            # Stelle sicher, dass Session verfügbar ist
            await self._ensure_session()
            
            # ÄNDERUNG 27.06.2025: Verwende normalen SessionManager mit async context
            # ÄNDERUNG 27.06.2025: Timeout als Integer (Fix für RuntimeError)
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    # ÄNDERUNG 20.06.2025: Sicheres JSON-Parsing
                    try:
                        data = await response.json()
                        # Prüfe ob Response ein Dictionary ist
                        if isinstance(data, dict):
                            return data
                        else:
                            self.logger.error(f"Unerwartetes Response-Format: {type(data)}")
                            return None
                    except json.JSONDecodeError as e:
                        text = await response.text()
                        self.logger.error(f"JSON Parse Fehler: {e}, Response: {text[:200]}...")
                        # ÄNDERUNG 23.06.2025: Behandle String-Responses
                        if text:
                            return {"choices": [{"message": {"content": text}}], "type": "text_response"}
                        return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Fehler: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API Anfrage Timeout")
            return None
        except asyncio.CancelledError:
            # Propagiere Cancellation
            self.logger.debug("API Anfrage wurde abgebrochen")
            raise CancellationException("API request cancelled")
        except Exception as e:
            self.logger.error(f"API Anfrage Fehler: {type(e).__name__}: {str(e)}")
            # ÄNDERUNG 27.06.2025: Vereinfachte Fehlerbehandlung
            if "session" in str(e).lower():
                self.logger.warning("Session-Fehler erkannt, markiere Session als ungültig")
                self._session = None
                self._robust_session = None
            return None
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Alias für search_mine - für Kompatibilität mit Source Discovery"""
        return await self.search_mine(query)