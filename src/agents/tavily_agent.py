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
from ..core.logger import get_logger, PerformanceLogger


class TavilyAgent(BaseAgent):
    """Tavily Agent für erweiterte Web-Recherche"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].tavily_key
        self.base_url = "https://api.tavily.com/search"
        self._rate_limiter = RateLimiter(rate=30, per=60.0)  # 30 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="tavily")
        self.search_builder = SearchStrategies()
        self.perf_logger = PerformanceLogger(self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Tavily Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein Tavily API-Key konfiguriert")
            return False
            
        try:
            # Test-Suche
            payload = {
                "api_key": self.api_key,
                "query": "test",
                "max_results": 1
            }
            
            async with self._session.post(
                self.base_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
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
            
            # Execute multiple enhanced queries (increased limit for broader search)
            query_limit = min(30, len(enhanced_queries))  # Increased from 15 to 30
            self.logger.info(f"Tavily executing {query_limit} enhanced queries from {len(enhanced_queries)} total")
            
            for idx, search_query in enumerate(enhanced_queries[:query_limit]):
                self.logger.info(f"Tavily Enhanced Search {idx+1}/{query_limit}: {search_query[:100]}...")
                
                response = await self._make_enhanced_api_call(search_query, query)
                if response:
                    parsed_results = self._parse_response(response, query, f"enhanced_{idx+1}")
                    results.extend(parsed_results)
                    
                await asyncio.sleep(0.3)  # Reduced pause for faster execution
            
            # Also run original specialized queries
            search_queries = self._create_search_queries(query)
            
            for search_type, search_query in search_queries.items():
                self.logger.info(f"Tavily-Spezialisierte Suche: {search_type}")
                
                response = await self._make_enhanced_api_call(search_query, query)
                if response:
                    parsed_results = self._parse_response(response, query, search_type)
                    results.extend(parsed_results)
                    
                await asyncio.sleep(0.5)
            
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
        
        # Gruppiere Queries nach Priorität
        priority_groups = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        for field, field_queries in specialized_queries.items():
            if field_queries:
                # Nimm die erste (höchste Priorität) Query für jedes Feld
                queries[f'{field}_targeted'] = field_queries[0]
                
                # Zusätzliche Queries für wichtige Felder
                if field in ['betreiber', 'koordinaten', 'sanierungskosten']:
                    for i, q in enumerate(field_queries[1:3], 1):  # Nimm bis zu 2 weitere
                        queries[f'{field}_alt{i}'] = q
        
        # Füge generelle Queries hinzu
        queries['comprehensive'] = f'"{query.mine_name}" mine {" ".join(query.required_fields)} {query.region} {query.country}'
        
        # Regierungsspezifische Queries basierend auf Land
        gov_sites = self.search_builder.gov_sites_by_country.get(query.country, [])
        if gov_sites:
            site_filter = " OR ".join([f"site:{site}" for site in gov_sites[:5]])
            queries['government'] = f'"{query.mine_name}" ({site_filter})'
        
        return queries
    
    async def _make_enhanced_api_call(self, query: str, mine_query: MineQuery) -> Optional[Dict[str, Any]]:
        """Enhanced API call with mining-specific domains"""
        await self._rate_limiter.acquire()
        
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
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",  # Tiefere Suche
            "max_results": 15,  # More results for comprehensive search
            "include_answer": True,
            "include_domains": all_domains,  # Feldspezifische + Mining Domains
            "exclude_domains": [
                "wikipedia.org",  # Oft unzuverlässig für aktuelle Daten
                "facebook.com", "twitter.com", "instagram.com",  # Social Media
                "pinterest.com", "tumblr.com"
            ]
        }
        
        try:
            async with self._session.post(
                self.base_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)  # Increased timeout for deeper searches
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Fehler: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API Anfrage Timeout")
            return None
        except Exception as e:
            self.logger.error(f"API Anfrage Fehler: {e}")
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
            async with self._session.post(
                self.base_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Fehler: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error("API Anfrage Timeout")
            return None
        except Exception as e:
            self.logger.error(f"API Anfrage Fehler: {e}")
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
                    title = result.get('title', '')
                    content = result.get('content', '')
                    url = result.get('url', '')
                    
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
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Tavily Agent beendet")