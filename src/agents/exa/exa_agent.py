"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für Exa AI Search Agent
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from .api_client import ExaAPIClient
from .query_builder import ExaQueryBuilder
from .result_parser import ExaResultParser
from .geographic_constraints import GeographicConstraintBuilder
from src.core.logger import get_logger, PerformanceLogger

class ExaAgent(BaseAgent):
    """Exa AI Agent für semantische Suche"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].exa_key
        
        # Initialisiere Komponenten
        self._session = None
        self.api_client = None
        self.query_builder = ExaQueryBuilder()
        self.result_parser = ExaResultParser()
        self.geo_constraint_builder = GeographicConstraintBuilder()
        
        self.logger = get_logger(f"agent.{name}", agent_type="exa")
        self.perf_logger = PerformanceLogger(self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            self._session = aiohttp.ClientSession()
            self.api_client = ExaAPIClient(self.api_key, self._session)
            
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
            # Test-Suche
            test_response = await self.api_client.search({
                "query": "test mining",
                "num_results": 1
            })
            
            return test_response is not None
                
        except Exception as e:
            self.logger.error(f"Credential-Validierung fehlgeschlagen: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweiterte Mining-spezifische Suche mit Exa durch"""
        results = []
        
        self.perf_logger.start_timer(f"exa_search_{query.mine_name}")
        
        try:
            # Erstelle semantische Suchanfragen
            search_queries = self._prepare_search_queries(query)
            
            total_queries = len(search_queries)
            completed_queries = 0
            
            for search_type, search_params in search_queries.items():
                self.logger.info(
                    f"Exa Mining-Suche ({completed_queries + 1}/{total_queries}): "
                    f"{search_type} für {query.mine_name}"
                )
                
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(
                        f"Exa: Suche {completed_queries + 1}/{total_queries} - {search_type}"
                    )
                
                # Nutze Exa's Search API
                search_response = await self.api_client.search(search_params)
                
                if search_response and 'results' in search_response:
                    # Parse Ergebnisse
                    parsed_results = self.result_parser.parse_results(
                        search_response, query, search_type
                    )
                    results.extend(parsed_results)
                    
                    # Hole detaillierte Inhalte für relevante Ergebnisse
                    content_ids = [r['id'] for r in search_response['results'][:10]]
                    if content_ids:
                        contents = await self.api_client.get_contents(content_ids)
                        if contents:
                            detailed_results = self._parse_detailed_contents(
                                contents, query, search_type
                            )
                            results.extend(detailed_results)
                
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
    
    def _prepare_search_queries(self, query: MineQuery) -> Dict[str, Dict[str, Any]]:
        """Bereitet alle Suchanfragen vor"""
        # Erstelle semantische Queries
        semantic_queries = self.query_builder.create_semantic_queries(query)
        
        # Füge geografische Constraints hinzu
        geo_constraints = self.geo_constraint_builder.create_geographic_constraints(
            query.region, query.country
        )
        
        # Update alle Queries mit geografischen Einschränkungen
        for query_type, query_config in semantic_queries.items():
            query_config['query'] += f" {geo_constraints}"
            
            # Füge länderspezifische Domains hinzu
            if 'include_domains' not in query_config:
                query_config['include_domains'] = []
            
            query_config['include_domains'].extend(
                self.geo_constraint_builder.get_region_specific_domains(
                    query.country,
                    technical=('technical' in query_type)
                )
            )
            
            # Entferne Duplikate und limitiere
            query_config['include_domains'] = list(set(query_config['include_domains']))[:20]
        
        # Füge Mining-spezifische Queries hinzu
        mining_queries = self.query_builder.create_mining_specific_queries(query)
        for idx, mining_query in enumerate(mining_queries[:5]):  # Limitiere auf 5
            semantic_queries[f'mining_{idx}'] = mining_query
        
        return semantic_queries
    
    def _parse_detailed_contents(self, contents: Dict[str, Any], 
                               query: MineQuery, search_type: str) -> List[SearchResult]:
        """Parst detaillierte Inhalte aus Contents API"""
        # Nutze die existierende parse_results Methode des Parsers
        # aber mit erweiterten Inhalten
        enhanced_response = {
            'results': []
        }
        
        if 'results' in contents:
            for content in contents['results']:
                enhanced_result = {
                    'id': content.get('id', ''),
                    'url': content.get('url', ''),
                    'title': content.get('title', ''),
                    'snippet': content.get('text', '')[:500] if 'text' in content else '',
                    'text': content.get('text', ''),
                    'highlights': content.get('highlights', [])
                }
                enhanced_response['results'].append(enhanced_result)
        
        return self.result_parser.parse_results(enhanced_response, query, f"{search_type}_detailed")
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self.logger.info("Exa Agent beendet")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()