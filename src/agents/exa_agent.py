"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: Exa AI Search Agent Implementation
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .rate_limiter import RateLimiter
from ..core.logger import get_logger, PerformanceLogger
from .enhanced_search import get_mining_search_queries, get_mining_domains


class ExaAgent(BaseAgent):
    """Exa AI Agent für semantische Suche"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].exa_key
        self.base_url = "https://api.exa.ai"
        self._rate_limiter = RateLimiter(rate=20, per=60.0)  # 20 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="exa")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Exa Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein Exa API-Key konfiguriert")
            return False
            
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Test-Suche
            payload = {
                "query": "test mining",
                "num_results": 1
            }
            
            async with self._session.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweiterte Mining-spezifische Suche mit Exa durch"""
        results = []
        
        self.perf_logger.start_timer(f"exa_search_{query.mine_name}")
        
        try:
            # Hole erweiterte Mining-Suchanfragen
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Erstelle semantische Suchanfragen
            search_queries = self._create_semantic_queries(query)
            
            # Füge zusätzliche Mining-spezifische Suchen hinzu
            for idx, mining_query in enumerate(mining_queries[:10]):  # Top 10 Queries
                search_queries[f'mining_{idx}'] = {
                    "query": mining_query,
                    "num_results": 10,
                    "use_autoprompt": True,
                    "category": "research paper",
                    "include_domains": mining_domains[:10],  # Top 10 Mining-Domains
                    "start_published_date": "2019-01-01"
                }
            
            total_queries = len(search_queries)
            completed_queries = 0
            
            for search_type, search_params in search_queries.items():
                self.logger.info(f"Exa Mining-Suche ({completed_queries + 1}/{total_queries}): {search_type} für {query.mine_name}")
                
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(f"Exa: Suche {completed_queries + 1}/{total_queries} - {search_type}")
                
                # Nutze Exa's Search API
                search_response = await self._search(search_params)
                
                if search_response and 'results' in search_response:
                    # Hole detaillierte Inhalte für relevante Ergebnisse
                    content_ids = [r['id'] for r in search_response['results'][:10]]  # Mehr Ergebnisse
                    if content_ids:
                        contents = await self._get_contents(content_ids)
                        if contents:
                            parsed_results = self._parse_contents(contents, query, search_type)
                            results.extend(parsed_results)
                
                completed_queries += 1
                await asyncio.sleep(1.0)  # Respektiere Rate Limits
            
            self.perf_logger.end_timer(
                f"exa_search_{query.mine_name}",
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
    
    def _create_semantic_queries(self, query: MineQuery) -> Dict[str, Dict[str, Any]]:
        """Erstellt erweiterte semantische Suchanfragen für Mining-Informationen"""
        queries = {}
        mining_domains = get_mining_domains()
        
        # Allgemeine Mineninformationen mit erweiterten Domains
        queries['general'] = {
            "query": f"Information about {query.mine_name} mine in {query.region}, {query.country}",
            "num_results": 20,
            "use_autoprompt": True,
            "category": "company",
            "include_domains": mining_domains[:15],
            "start_published_date": "2018-01-01"
        }
        
        # Umwelt- und Finanzdaten
        queries['environmental'] = {
            "query": f"{query.mine_name} environmental restoration costs rehabilitation bonds closure financial liability",
            "num_results": 15,
            "use_autoprompt": True,
            "category": "research paper",
            "include_domains": ["gov.ca", "nrcan.gc.ca", "mern.gouv.qc.ca", "sec.gov", "sedar.com"]
        }
        
        # Betreiber und Eigentümer
        queries['operator'] = {
            "query": f"Who operates {query.mine_name} mine owner company {query.region} mining corporation",
            "num_results": 15,
            "use_autoprompt": True,
            "category": "company",
            "include_domains": mining_domains[:10]
        }
        
        # Technische Berichte
        queries['technical'] = {
            "query": f"{query.mine_name} NI 43-101 technical report feasibility study resource estimate",
            "num_results": 10,
            "use_autoprompt": True,
            "category": "research paper",
            "include_domains": ["sedar.com", "sec.gov", "tsx.com", "asx.com.au"]
        }
        
        # Produktion und Reserven
        queries['production'] = {
            "query": f"{query.mine_name} production capacity reserves resources tonnage grade",
            "num_results": 10,
            "use_autoprompt": True,
            "category": "news",
            "include_domains": mining_domains[:10]
        }
        
        # Koordinaten und Standort
        queries['location'] = {
            "query": f"{query.mine_name} mine coordinates GPS location latitude longitude {query.region}",
            "num_results": 10,
            "use_autoprompt": True,
            "include_domains": ["mindat.org", "geonames.org", "openstreetmap.org"]
        }
        
        return queries
    
    async def _search(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Führt Suche mit Exa durch"""
        await self._rate_limiter.acquire()
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/search",
                headers=headers,
                json=params,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"Search API Fehler: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Search API Fehler: {e}")
            return None
    
    async def _get_contents(self, ids: List[str]) -> Optional[Dict[str, Any]]:
        """Holt detaillierte Inhalte für IDs"""
        await self._rate_limiter.acquire()
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "ids": ids,
            "text": {
                "max_characters": 2000,
                "include_html_tags": False
            }
        }
        
        try:
            async with self._session.post(
                f"{self.base_url}/contents",
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    self.logger.error(f"Contents API Fehler: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Contents API Fehler: {e}")
            return None
    
    def _parse_contents(self, contents_response: Dict[str, Any], query: MineQuery, search_type: str) -> List[SearchResult]:
        """Parst Exa Contents und extrahiert strukturierte Daten"""
        results = []
        
        try:
            if 'results' not in contents_response:
                return results
            
            for content in contents_response['results']:
                text = content.get('text', '')
                url = content.get('url', '')
                title = content.get('title', '')
                
                # Kombiniere Title und Text für bessere Extraktion
                full_text = f"{title} {text}"
                
                # Extrahiere verschiedene Felder
                extracted = self._extract_fields(full_text, url, query)
                results.extend(extracted)
                
        except Exception as e:
            self.logger.error(f"Content Parse Fehler: {e}")
            
        return results
    
    def _extract_fields(self, text: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert spezifische Felder aus Text"""
        results = []
        
        # Definiere Extraktionsmuster
        extractions = {
            'betreiber': {
                'patterns': [
                    r'(?:operated by|operator|owned by|owner)[:\s]+([A-Za-z0-9\s&.,()-]+?)(?:\.|,|\s+(?:and|with))',
                    r'([A-Z][A-Za-z0-9\s&.,()-]+?)\s+(?:operates|owns)\s+(?:the\s+)?(?:' + re.escape(query.mine_name) + ')'
                ],
                'confidence': 'high'
            },
            'koordinaten': {
                'patterns': [
                    r'coordinates?[:\s]*([-\d\.]+)[°\s,]+([-\d\.]+)',
                    r'latitude[:\s]*([-\d\.]+).*?longitude[:\s]*([-\d\.]+)',
                    r'located at[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)'
                ],
                'confidence': 'high'
            },
            'sanierungskosten': {
                'patterns': [
                    r'restoration cost[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                    r'rehabilitation[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                    r'closure bond[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                    r'environmental bond[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                    r'reclamation[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                    r'financial assurance[:\s]+\$?([\d,\.]+)\s*(?:million|M)?',
                    r'closure cost[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?'
                ],
                'confidence': 'medium'
            },
            'rohstofftyp': {
                'patterns': [
                    r'(?:produces?|producing|mines?|mining)[:\s]+([A-Za-z0-9\s,&-]+?)(?:\.|,|\s+(?:with|and))',
                    r'(?:commodit(?:y|ies)|mineral[s]?)[:\s]+([A-Za-z0-9\s,&-]+?)(?:\.|,)'
                ],
                'confidence': 'medium'
            },
            'aktivitaetsstatus': {
                'patterns': [
                    r'(?:mine\s+)?(?:is\s+)?(?:currently\s+)?(\w+ing|\w+ed)(?:\s+mine)?',
                    r'status[:\s]+(\w+)',
                    r'(?:mine\s+)?(?:has been\s+)?(\w+)(?:\s+since)?'
                ],
                'confidence': 'medium'
            },
            'jahresproduktion': {
                'patterns': [
                    r'(?:annual production|produces?)[:\s]*([\d,\.]+)\s*(?:tonnes?|tons?|ounces?|oz)',
                    r'([\d,\.]+)\s*(?:tonnes?|tons?|ounces?|oz)\s*(?:per year|annually|/year)'
                ],
                'confidence': 'medium'
            }
        }
        
        for field_name, field_config in extractions.items():
            for pattern in field_config['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Nimm das erste Match
                    match = matches[0]
                    if isinstance(match, tuple):
                        value = ", ".join(match)
                    else:
                        value = match
                    
                    # Bereinige Wert
                    value = value.strip()
                    if field_name == 'sanierungskosten' and 'million' in text.lower():
                        # Konvertiere zu voller Zahl
                        try:
                            num_value = float(value.replace(',', ''))
                            value = f"{num_value * 1000000:,.0f} CAD"
                        except:
                            value = f"{value} million CAD"
                    
                    result = SearchResult(
                        mine_name=query.mine_name,
                        field_name=field_name,
                        value=value,
                        source=f"Exa: {title[:50] if 'title' in locals() else 'Web Source'}",
                        source_url=url,
                        source_date=datetime.now().year,
                        confidence_score=0.9 if field_config['confidence'] == 'high' else 0.7,
                        agent_name=self.name,
                        timestamp=datetime.now(),
                        metadata={}
                    )
                    results.append(result)
                    self.logger.info(f"Gefunden: {field_name} = {value}")
                    break
        
        return results
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Exa Agent beendet")