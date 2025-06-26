"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: Tavily Search Agent Implementation
"""

import aiohttp
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from .enhanced_search import get_mining_search_queries, get_mining_domains
from .search_strategies import SearchStrategies
from src.core.logger import get_logger, PerformanceLogger
from src.utils.safe_dict_access import safe_get, safe_nested_get, ensure_dict, ensure_list
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
        self.search_builder = SearchStrategies()
        self.perf_logger = PerformanceLogger(self.logger)
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
    
    def _optimize_query_length(self, query: str, max_length: int = 395) -> str:
        """
        ÄNDERUNG 24.06.2025: Zentrale Query-Optimierung für Tavily 400-Zeichen-Limit
        Intelligente Kürzung ohne Informationsverlust
        """
        # Bereinige Query zuerst
        query = self._clean_query(query)
        
        if len(query) <= max_length:
            return query
        
        # Strategie 1: Entferne Duplikate und Redundanzen
        query = self._remove_redundancies(query)
        if len(query) <= max_length:
            return query
        
        # Strategie 2: Priorisiere wichtige Komponenten
        components = self._extract_query_components(query)
        optimized = self._rebuild_query(components, max_length)
        
        # Sicherstellen dass Query nicht zu kurz wird
        if len(optimized) < 20:
            # Fallback: Harte Kürzung mit Ellipsis
            return query[:max_length-3] + "..."
        
        return optimized
    
    def _clean_query(self, query: str) -> str:
        """Bereinigt Query von überflüssigen Zeichen und Leerzeichen"""
        # Entferne mehrfache Leerzeichen
        query = ' '.join(query.split())
        # Entferne überflüssige Anführungszeichen
        query = re.sub(r'""', '"', query)
        # Entferne leere Klammern
        query = re.sub(r'\(\s*\)', '', query)
        query = re.sub(r'\[\s*\]', '', query)
        return query.strip()
    
    def _remove_redundancies(self, query: str) -> str:
        """Entfernt redundante Begriffe aus Query"""
        # Extrahiere alle Wörter in Anführungszeichen
        quoted_terms = re.findall(r'"([^"]+)"', query)
        
        # Finde und entferne Duplikate (case-insensitive)
        seen = set()
        for term in quoted_terms:
            normalized = term.lower().strip()
            if normalized in seen:
                # Entferne das Duplikat
                query = query.replace(f'"{term}"', '', 1)
            else:
                seen.add(normalized)
        
        # Entferne doppelte Wörter außerhalb von Anführungszeichen
        words = []
        seen_words = set()
        in_quotes = False
        current_word = ""
        
        for char in query + " ":
            if char == '"':
                in_quotes = not in_quotes
                current_word += char
            elif char == ' ' and not in_quotes:
                if current_word:
                    word_lower = current_word.lower()
                    if word_lower not in seen_words or current_word.startswith('"'):
                        words.append(current_word)
                        if not current_word.startswith('"'):
                            seen_words.add(word_lower)
                    current_word = ""
            else:
                current_word += char
        
        return ' '.join(words)
    
    def _extract_query_components(self, query: str) -> dict:
        """Extrahiert und priorisiert Query-Komponenten"""
        components = {
            'mine_name': '',
            'location': '',
            'country': '',
            'primary_terms': [],
            'secondary_terms': [],
            'site_restrictions': [],
            'operators': []
        }
        
        # Extrahiere Mine-Name (höchste Priorität)
        mine_match = re.search(r'"([^"]+)"\s*(?:mine)?', query)
        if mine_match:
            components['mine_name'] = mine_match.group(0)
            query = query.replace(mine_match.group(0), '')
        
        # Extrahiere Site-Restriktionen
        site_matches = re.findall(r'site:\S+', query)
        components['site_restrictions'] = site_matches[:2]  # Max 2 Sites
        for site in site_matches:
            query = query.replace(site, '')
        
        # Extrahiere OR-Operatoren
        or_matches = re.findall(r'\bOR\b', query)
        components['operators'] = or_matches[:2]  # Max 2 OR
        
        # Extrahiere Länder und Regionen
        location_keywords = ['Canada', 'Quebec', 'Ontario', 'Australia', 'USA', 'Chile']
        for loc in location_keywords:
            if loc in query:
                components['location'] = loc
                components['country'] = loc if loc in ['Canada', 'Australia', 'USA', 'Chile'] else 'Canada'
                break
        
        # Kategorisiere verbleibende Begriffe
        remaining_words = query.split()
        priority_keywords = ['operator', 'coordinates', 'GPS', 'production', 'closure', 'costs', 
                           'environmental', 'report', 'assessment', 'NI 43-101', 'annual']
        
        for word in remaining_words:
            if word.lower() in [k.lower() for k in priority_keywords]:
                components['primary_terms'].append(word)
            elif len(word) > 3 and word not in components['operators']:
                components['secondary_terms'].append(word)
        
        return components
    
    def _rebuild_query(self, components: dict, max_length: int) -> str:
        """Baut optimierte Query aus Komponenten"""
        # Beginne mit Mine-Name (essential)
        parts = []
        if components['mine_name']:
            parts.append(components['mine_name'])
        
        # Füge Location hinzu wenn Platz
        current_length = len(' '.join(parts))
        if components['location'] and current_length + len(components['location']) + 1 < max_length - 50:
            parts.append(components['location'])
        
        # Füge primäre Begriffe hinzu
        current_length = len(' '.join(parts))
        for term in components['primary_terms'][:5]:  # Max 5 primäre Begriffe
            if current_length + len(term) + 1 < max_length - 20:
                parts.append(term)
                current_length += len(term) + 1
        
        # Füge Site-Restriktionen hinzu wenn Platz
        current_length = len(' '.join(parts))
        for site in components['site_restrictions'][:1]:  # Max 1 Site
            if current_length + len(site) + 1 < max_length:
                # Füge auch OR hinzu wenn vorhanden
                if components['operators'] and 'OR' in components['operators']:
                    parts.append(site)
                    parts.append('OR')
                    current_length += len(site) + 4
                else:
                    parts.append(site)
                    current_length += len(site) + 1
        
        # Füge weitere Site-Restriktionen hinzu wenn OR vorhanden
        if len(components['site_restrictions']) > 1 and 'OR' in components.get('operators', []):
            for site in components['site_restrictions'][1:2]:  # Noch eine Site
                if current_length + len(site) + 1 < max_length:
                    parts.append(site)
                    current_length += len(site) + 1
        
        # Füge sekundäre Begriffe hinzu wenn noch Platz
        current_length = len(' '.join(parts))
        for term in components['secondary_terms'][:3]:  # Max 3 sekundäre Begriffe
            if current_length + len(term) + 1 < max_length:
                parts.append(term)
                current_length += len(term) + 1
            else:
                break
        
        return ' '.join(parts)
    
    def _create_query_hash(self, query: str) -> str:
        """Erstellt einen Hash für Query-Caching"""
        import hashlib
        return hashlib.md5(query.encode()).hexdigest()[:10]

    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Suche mit Tavily durch"""
        results = []
        
        self.perf_logger.start_timer(f"tavily_search_{query.mine_name}")
        
        try:
            # Get enhanced search queries from enhanced_search module with required fields
            enhanced_queries = get_mining_search_queries(
                query.mine_name, 
                query.region, 
                query.country,
                query.required_fields
            )
            
            # ÄNDERUNG 23.06.2025: Reduzierte Query-Anzahl zur Vermeidung von API-Limits
            query_limit = min(5, len(enhanced_queries))  # Reduziert auf max. 5 Queries
            self.logger.info(f"Tavily executing {query_limit} enhanced queries from {len(enhanced_queries)} total")
            
            for idx, original_query in enumerate(enhanced_queries[:query_limit]):
                # ÄNDERUNG 24.06.2025: Prüfe Query-Länge VOR Verarbeitung
                if len(original_query) > 380:
                    self.logger.warning(f"Query {idx+1} zu lang ({len(original_query)} Zeichen): {original_query[:100]}...")
                    # Kürze Query auf sicheres Maximum
                    original_query = original_query[:377] + "..."
                
                # ÄNDERUNG 24.06.2025: Optimiere Query-Länge
                search_query = self._optimize_query_length(original_query)
                
                # Nur eine optimierte Query pro enhanced query
                for part_idx, search_query in enumerate([search_query]):
                    # Check Cache
                    cache_key = f"{query.mine_name}_{search_query[:50]}_{part_idx}"
                    if cache_key in self._request_cache:
                        cached_time, cached_response = self._request_cache[cache_key]
                        if (datetime.now() - cached_time).seconds < self._cache_ttl:
                            self.logger.info(f"Using cached response for query {idx+1} part {part_idx+1}")
                            parsed_results = self._parse_response(cached_response, query, f"enhanced_{idx+1}_p{part_idx+1}_cached")
                            results.extend(parsed_results)
                            continue
                    
                    self.logger.info(f"Tavily Enhanced Search {idx+1}/{query_limit} Part {part_idx+1}/1: {search_query[:100]}...")
                    
                    response = await self._make_enhanced_api_call(search_query, query)
                    if response:
                        # Cache successful response
                        self._request_cache[cache_key] = (datetime.now(), response)
                        parsed_results = self._parse_response(response, query, f"enhanced_{idx+1}_p{part_idx+1}")
                        results.extend(parsed_results)
                    
                    await asyncio.sleep(1.5)  # Pause zwischen Query-Teilen
                    
                await asyncio.sleep(2.0)  # Erhöhte Pause zwischen Haupt-Requests
            
            # ÄNDERUNG 23.06.2025: Begrenzte spezialisierte Queries
            search_queries = self._create_search_queries(query)
            
            # Nur die wichtigsten 2 spezialisierten Queries ausführen
            priority_queries = ['comprehensive', 'government']
            executed_specialized = 0
            
            for search_type, search_query in search_queries.items():
                if executed_specialized >= 2 or search_type not in priority_queries:
                    continue
                
                # ÄNDERUNG 24.06.2025: Prüfe Query-Länge für spezialisierte Queries
                if len(search_query) > 380:
                    self.logger.warning(f"Spezialisierte Query '{search_type}' zu lang ({len(search_query)} Zeichen)")
                    search_query = search_query[:377] + "..."
                    
                # Check Cache für spezialisierte Queries
                cache_key = f"{query.mine_name}_{search_type}"
                if cache_key in self._request_cache:
                    cached_time, cached_response = self._request_cache[cache_key]
                    if (datetime.now() - cached_time).seconds < self._cache_ttl:
                        self.logger.info(f"Using cached response for {search_type}")
                        parsed_results = self._parse_response(cached_response, query, f"{search_type}_cached")
                        results.extend(parsed_results)
                        executed_specialized += 1
                        continue
                
                self.logger.info(f"Tavily-Spezialisierte Suche: {search_type}")
                
                response = await self._make_enhanced_api_call(search_query, query)
                if response:
                    # Cache successful response
                    self._request_cache[cache_key] = (datetime.now(), response)
                    parsed_results = self._parse_response(response, query, search_type)
                    results.extend(parsed_results)
                    executed_specialized += 1
                    
                await asyncio.sleep(3.0)  # Längere Pause für API-Schonung
            
            self.perf_logger.end_timer(
                f"tavily_search_{query.mine_name}",
                results_found=len(results)
            )
            
            # Update Statistiken
            self.stats['total_requests'] += len(enhanced_queries[:15]) + len(search_queries)
            self.stats['successful_requests'] += 1 if results else 0
            self.stats['total_fields_found'] += len(results)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self.stats['failed_requests'] += 1
            
        return results
    
    def _create_search_queries(self, query: MineQuery) -> Dict[str, str]:
        """Erstellt optimierte Suchanfragen für Tavily mit intelligenten Strategien"""
        # Nutze IntelligentSearchBuilder für feldspezifische Queries
        specialized_queries = self.search_builder.get_specialized_queries(
            mine_name=query.mine_name,
            fields=query.required_fields,
            region=query.region,
            country=query.country,
            languages=query.languages
        )
        
        # Konvertiere zu Tavily-Format
        queries = {}
        
        # ÄNDERUNG 21.06.2025: Robustere Behandlung von specialized_queries
        if specialized_queries is None:
            self.logger.warning("specialized_queries ist None, verwende leere Liste")
            specialized_queries = []
            
        if isinstance(specialized_queries, list):
            # Konvertiere Liste von Queries zu Dict
            for idx, query_item in enumerate(specialized_queries):
                if isinstance(query_item, dict):
                    field = safe_get(query_item, 'field', f'query_{idx}')
                    query_text = safe_get(query_item, 'query', '')
                    priority = safe_get(query_item, 'priority', 'medium')
                    
                    if query_text:
                        queries[f'{field}_{priority}'] = query_text
        elif isinstance(specialized_queries, dict):
            # Altes Format (Dict von Listen)
            try:
                for field, field_queries in specialized_queries.items():
                    if field_queries:
                        # Nimm die erste (höchste Priorität) Query für jedes Feld
                        queries[f'{field}_targeted'] = field_queries[0]
                        
                        # Zusätzliche Queries für wichtige Felder
                        if field in ['betreiber', 'koordinaten', 'sanierungskosten']:
                            for i, q in enumerate(field_queries[1:3], 1):  # Nimm bis zu 2 weitere
                                queries[f'{field}_alt{i}'] = q
            except AttributeError as e:
                self.logger.error(f"AttributeError bei specialized_queries: {e}, Type: {type(specialized_queries)}")
        else:
            self.logger.error(f"Unerwarteter Typ für specialized_queries: {type(specialized_queries)}")
            # Fallback zu leerer Query-Liste
        
        # ÄNDERUNG 24.06.2025: Optimierte Query-Erstellung für Tavily (max 380 chars)
        # Basis-Query (kompakt)
        base_query = f'"{query.mine_name}" mine {query.region} {query.country}'
        
        # Optimiere alle Queries mit zentraler Funktion
        optimized_queries = {}
        for key, q in queries.items():
            optimized_queries[key] = self._optimize_query_length(q, max_length=395)
        
        # Basis-Query (immer dabei)
        if len(base_query) < 350 and query.required_fields:
            optimized_queries['comprehensive'] = self._optimize_query_length(
                f'{base_query} {query.required_fields[0]}', max_length=395
            )
        else:
            optimized_queries['comprehensive'] = self._optimize_query_length(base_query, max_length=395)
        
        # Government Query (nur wenn sinnvoll)
        if query.country.lower() == 'canada' and len(base_query) < 250:
            gov_query = f'{base_query} site:gc.ca OR site:gouv.qc.ca'
            optimized_queries['government'] = self._optimize_query_length(gov_query, max_length=395)
        
        return optimized_queries
    
    async def _make_enhanced_api_call(self, query: str, mine_query: MineQuery) -> Optional[Dict[str, Any]]:
        """Enhanced API call with mining-specific domains"""
        await self._rate_limiter.acquire()
        import asyncio
        start_time = asyncio.get_event_loop().time()  # ÄNDERUNG 23.06.2025: Timing für Monitoring
        
        # ÄNDERUNG 24.06.2025: Nutze zentrale Query-Optimierung
        original_length = len(query)
        query = self._optimize_query_length(query, max_length=395)
        
        if original_length > 395:
            self.logger.info(f"Query optimiert: {original_length} -> {len(query)} Zeichen")
        
        # Extrahiere Feldtyp aus Query-Name für Site-Empfehlungen
        field_type = None
        for field in mine_query.required_fields:
            if field in query.lower():
                field_type = field
                break
        
        # Hole feldspezifische Site-Empfehlungen
        recommended_sites = []
        if field_type:
            recommended_sites = self.search_builder.get_site_recommendations(field_type)
        
        # Kombiniere mit generellen Mining-Domains
        mining_domains = get_mining_domains()
        all_domains = list(set(recommended_sites + mining_domains))[:25]
        
        # ÄNDERUNG 23.06.2025: Geografische Filter aus Query extrahieren
        exclude_domains = [
            "wikipedia.org",  # Oft unzuverlässig für aktuelle Daten
            "facebook.com", "twitter.com", "instagram.com",  # Social Media
            "pinterest.com", "tumblr.com"
        ]
        
        # Füge geografische Exclusions hinzu basierend auf Land
        if mine_query and mine_query.country:
            if mine_query.country.lower() in ["canada", "kanada"]:
                exclude_domains.extend([
                    "miningreview.com",
                    "africanminingmarket.com",
                    "mining-africa.com"
                ])
            elif mine_query.country.lower() in ["australia", "australien"]:
                exclude_domains.extend([
                    "africanminingmarket.com",
                    "mining-africa.com"
                ])
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",  # Tiefere Suche
            "max_results": 15,  # More results for comprehensive search
            "include_answer": True,
            "include_domains": all_domains,  # Feldspezifische + Mining Domains
            "exclude_domains": exclude_domains
        }
        
        try:
            # Stelle sicher, dass Session verfügbar ist
            await self._ensure_session()
            
            async with self._robust_session.request(
                'POST',
                self.base_url,
                json=payload,
                timeout=60  # Increased timeout for deeper searches
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Fehler: {response.status} - {error_text}")
                    
                    # ÄNDERUNG 23.06.2025: Spezielle Behandlung für Rate Limit Fehler
                    if response.status == 433:
                        self.logger.warning("Tavily API Rate Limit erreicht - Agent wird temporär deaktiviert")
                        self.status = AgentStatus.RATE_LIMITED
                        # Setze längere Wartezeit
                        self._rate_limiter = RateLimiter(rate=1, per=120.0)  # Nur 1 Request alle 2 Minuten
                    
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API Anfrage Timeout")
            return None
        except Exception as e:
            # ÄNDERUNG 23.06.2025: Erweiterte Fehlerdiagnose
            import traceback
            self.logger.error(f"API Anfrage Fehler: {e}")
            self.logger.error(f"Fehler-Typ: {type(e).__name__}")
            self.logger.error(f"Stack Trace:\n{traceback.format_exc()}")
            
            # Prüfe Event Loop Status
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                self.logger.error(f"Event Loop läuft: {loop.is_running()}")
                self.logger.error(f"Event Loop geschlossen: {loop.is_closed()}")
            except:
                self.logger.error("Konnte Event Loop Status nicht prüfen")
                
            return None
    
    async def _make_api_call(self, query: str) -> Optional[Dict[str, Any]]:
        """Macht API-Aufruf zu Tavily"""
        await self._rate_limiter.acquire()
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",  # Tiefere Suche
            "max_results": 10,
            "include_answer": True,
            "include_domains": [
                "*.gov.ca", "*.gc.ca", "*.gouv.qc.ca",  # Kanadische Regierung
                "mining.com", "mining-technology.com",  # Mining Portale
                "*.edu", "*.org"  # Akademische/NGO Quellen
            ],
            "exclude_domains": [
                "wikipedia.org",  # Oft unzuverlässig für aktuelle Daten
                "facebook.com", "twitter.com"  # Social Media
            ]
        }
        
        try:
            # Stelle sicher, dass Session verfügbar ist
            await self._ensure_session()
            
            async with self._robust_session.request(
                'POST',
                self.base_url,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Fehler: {response.status} - {error_text}")
                    
                    # ÄNDERUNG 23.06.2025: Spezielle Behandlung für Rate Limit Fehler
                    if response.status == 433:
                        self.logger.warning("Tavily API Rate Limit erreicht - Agent wird temporär deaktiviert")
                        self.status = AgentStatus.RATE_LIMITED
                        # Setze längere Wartezeit
                        self._rate_limiter = RateLimiter(rate=1, per=120.0)  # Nur 1 Request alle 2 Minuten
                    
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API Anfrage Timeout")
            return None
        except Exception as e:
            # ÄNDERUNG 23.06.2025: Erweiterte Fehlerdiagnose
            import traceback
            self.logger.error(f"API Anfrage Fehler: {e}")
            self.logger.error(f"Fehler-Typ: {type(e).__name__}")
            self.logger.error(f"Stack Trace:\n{traceback.format_exc()}")
            
            # Prüfe Event Loop Status
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                self.logger.error(f"Event Loop läuft: {loop.is_running()}")
                self.logger.error(f"Event Loop geschlossen: {loop.is_closed()}")
            except:
                self.logger.error("Konnte Event Loop Status nicht prüfen")
                
            return None
    
    def _parse_response(self, response: Dict[str, Any], query: MineQuery, search_type: str) -> List[SearchResult]:
        """Parst Tavily-Antwort und extrahiert strukturierte Daten"""
        results = []
        
        try:
            # Tavily liefert strukturierte Antworten
            if 'answer' in response and response['answer']:
                # Extrahiere Daten aus der zusammengefassten Antwort
                extracted = self._extract_from_answer(response['answer'], query)
                results.extend(extracted)
            
            # Zusätzlich aus einzelnen Suchergebnissen
            if 'results' in response:
                for result in response['results'][:5]:  # Top 5 Ergebnisse
                    title = safe_get(result, 'title', '')
                    content = safe_get(result, 'content', '')
                    url = safe_get(result, 'url', '')
                    
                    # Extrahiere spezifische Felder
                    extracted = self._extract_from_content(
                        title + ' ' + content,
                        url,
                        query
                    )
                    results.extend(extracted)
            
        except Exception as e:
            self.logger.error(f"Response Parse Fehler: {e}")
            
        return results
    
    def _extract_from_answer(self, answer: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus Tavily's zusammengefasster Antwort mit kontextbasierter Extraktion"""
        results = []
        
        # Nutze kontextbasierte Extraktion für alle erforderlichen Felder
        for field in query.required_fields:
            extracted_values = self._extract_with_context(answer, field)
            
            if extracted_values:
                # Nimm den Wert mit höchster Konfidenz
                best_value, confidence = extracted_values[0]
                
                # Erstelle SearchResult nur wenn Konfidenz hoch genug
                if confidence >= 0.5:
                    result = SearchResult(
                        mine_name=query.mine_name,
                        field_name=field,
                        value=best_value,
                        source="Tavily Search Summary",
                        source_url="",
                        source_date=datetime.now().year,
                        confidence_score=confidence,
                        agent_name=self.name,
                        timestamp=datetime.now(),
                        metadata={
                            "extraction_method": "contextual",
                            "alternative_values": [
                                {"value": val, "confidence": conf} 
                                for val, conf in extracted_values[1:3]
                            ] if len(extracted_values) > 1 else []
                        }
                    )
                    results.append(result)
                    self.logger.info(f"Gefunden: {field} = {best_value} (Konfidenz: {confidence:.2f})")
        
        return results
    
    def _extract_from_content(self, content: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Daten aus einzelnem Suchergebnis mit kontextbasierter Extraktion"""
        results = []
        
        # Nutze kontextbasierte Extraktion für alle erforderlichen Felder
        for field in query.required_fields:
            extracted_values = self._extract_with_context(content, field)
            
            if extracted_values:
                # Nimm den Wert mit höchster Konfidenz
                best_value, confidence = extracted_values[0]
                
                # Erstelle SearchResult nur wenn Konfidenz hoch genug
                if confidence >= 0.4:  # Etwas niedrigerer Schwellwert für Content
                    result = SearchResult(
                        mine_name=query.mine_name,
                        field_name=field,
                        value=best_value,
                        source=f"Tavily: {urlparse(url).netloc}",
                        source_url=url,
                        source_date=self._extract_year_from_text(content),
                        confidence_score=confidence * 0.8,  # Reduziere Konfidenz für Content
                        agent_name=self.name,
                        timestamp=datetime.now(),
                        metadata={
                            "extraction_method": "contextual",
                            "content_snippet": content[:200]
                        }
                    )
                    results.append(result)
        
        return results
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Alias für search_mine - für Kompatibilität mit Source Discovery"""
        return await self.search_mine(query)
    
