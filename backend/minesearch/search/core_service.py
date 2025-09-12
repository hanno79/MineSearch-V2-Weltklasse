"""
Core Search Service Module
Basis-Suchfunktionalität für MineSearch

Author: MineSearch Development Team
Date: 2025-01-11
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from minesearch.config.base import config, Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from minesearch.utils import (
    normalize_accents,
    generate_name_variants,
    generate_multilingual_search_terms,
    get_country_config,
)
from minesearch.data_extraction import DataExtractor, assign_sources_to_data
from minesearch.source_discovery import extract_sources_from_content
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.providers.registry import provider_registry
from minesearch.providers.base_provider import SearchResult
from minesearch.cache_service import get_cache_service, cached_search
from minesearch.cost_monitor import cost_monitor
from minesearch.database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class CoreSearchService:
    """Kern-Suchservice für MineSearch"""

    def __init__(self):
        """Initialisiere Core Search Service"""
        self.db_manager = DatabaseManager()
        self.cache_service = get_cache_service()
        self.enhanced_source_discovery = EnhancedSourceDiscovery()
        self.data_extractor = DataExtractor()

    async def search_mine(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
        """Hauptsuchmethode für eine Mine"""
        try:
            # Normalisiere Eingaben
            normalized_mine_name = normalize_accents(mine_name)
            country_config = get_country_config(country)
            
            # Generiere Suchbegriffe
            search_terms = self._generate_search_terms(normalized_mine_name, country, region)
            
            # Führe Suche durch
            search_results = await self._execute_search(search_terms, country_config)
            
            # Extrahiere Daten
            extracted_data = await self._extract_data(search_results, normalized_mine_name)
            
            # Weise Quellen zu
            data_with_sources = assign_sources_to_data(extracted_data, search_results)
            
            return {
                'mine_name': normalized_mine_name,
                'country': country,
                'region': region,
                'data': data_with_sources,
                'sources': search_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Suche für {mine_name}: {e}")
            return {
                'mine_name': mine_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _generate_search_terms(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> List[str]:
        """Generiere Suchbegriffe für die Mine"""
        terms = [mine_name]
        
        # Name-Varianten
        name_variants = generate_name_variants(mine_name)
        terms.extend(name_variants)
        
        # Mehrsprachige Begriffe
        if country:
            multilingual_terms = generate_multilingual_search_terms(mine_name, country)
            terms.extend(multilingual_terms)
        
        # Region-spezifische Begriffe
        if region:
            terms.append(f"{mine_name} {region}")
        
        return list(set(terms))  # Entferne Duplikate

    async def _execute_search(self, search_terms: List[str], country_config: Dict[str, Any]) -> List[SearchResult]:
        """Führe Suche mit allen Providern durch"""
        all_results = []
        
        for term in search_terms:
            try:
                # Verwende Cache falls verfügbar
                cached_result = await self.cache_service.get(term)
                if cached_result:
                    all_results.extend(cached_result)
                    continue
                
                # Führe Suche durch
                results = await self._search_with_providers(term, country_config)
                
                # Cache Ergebnisse
                await self.cache_service.set(term, results)
                
                all_results.extend(results)
                
            except Exception as e:
                logger.warning(f"Fehler bei Suche für '{term}': {e}")
        
        return all_results

    async def _search_with_providers(self, term: str, country_config: Dict[str, Any]) -> List[SearchResult]:
        """Suche mit allen verfügbaren Providern"""
        results = []
        
        for provider_name, provider in provider_registry.items():
            try:
                # Prüfe Provider-Konfiguration
                if not self._is_provider_enabled(provider_name, country_config):
                    continue
                
                # Führe Suche durch
                provider_results = await provider.search(term)
                results.extend(provider_results)
                
                # Überwache Kosten
                cost_monitor.record_search(provider_name, len(provider_results))
                
            except Exception as e:
                logger.warning(f"Fehler bei Provider {provider_name}: {e}")
        
        return results

    def _is_provider_enabled(self, provider_name: str, country_config: Dict[str, Any]) -> bool:
        """Prüfe ob Provider für das Land aktiviert ist"""
        if not country_config:
            return True
        
        enabled_providers = country_config.get('enabled_providers', [])
        return provider_name in enabled_providers

    async def _extract_data(self, search_results: List[SearchResult], mine_name: str) -> Dict[str, Any]:
        """Extrahiere Daten aus Suchergebnissen"""
        try:
            # Kombiniere alle Inhalte
            all_content = []
            for result in search_results:
                if result.content:
                    all_content.append(result.content)
            
            # Extrahiere strukturierte Daten
            extracted_data = await self.data_extractor.extract_mine_data(
                mine_name, 
                all_content
            )
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Fehler bei Datenextraktion: {e}")
            return {}


__all__ = ["CoreSearchService"]
