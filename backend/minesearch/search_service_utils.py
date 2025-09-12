"""
Search Service Utilities
Hilfsfunktionen für den Search Service

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
from minesearch.database.normalized_manager import NormalizedDatabaseManager
from minesearch.field_value_parser import (
    extract_atomic_value_and_sources,
    normalize_atomic_value,
    find_or_create_source_by_url
)

logger = logging.getLogger(__name__)


class SearchServiceUtils:
    """Hilfsfunktionen für den Search Service"""

    @staticmethod
    async def check_cache(mine_name: str, country: str, model: str, commodity: str = None, region: str = None) -> Optional[Dict[str, Any]]:
        """Prüfe Cache für Suchergebnisse"""
        cache_key = f"{mine_name}_{country}_{model}_{commodity}_{region}"
        cache_service = get_cache_service()
        return await cache_service.get(cache_key)

    @staticmethod
    async def save_to_cache(mine_name: str, country: str, model: str, result: Dict[str, Any], commodity: str = None, region: str = None):
        """Speichere Suchergebnis im Cache"""
        cache_key = f"{mine_name}_{country}_{model}_{commodity}_{region}"
        cache_service = get_cache_service()
        await cache_service.set(cache_key, result)

    @staticmethod
    def generate_search_terms(mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> List[str]:
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

    @staticmethod
    async def execute_search_with_providers(search_terms: List[str], model: str, country_config: Dict[str, Any]) -> List[SearchResult]:
        """Führe Suche mit allen Providern durch"""
        all_results = []
        
        for term in search_terms:
            try:
                # Führe Suche durch
                results = await SearchServiceUtils._search_with_providers(term, model, country_config)
                all_results.extend(results)
                
            except Exception as e:
                logger.warning(f"Fehler bei Suche für '{term}': {e}")
        
        return all_results

    @staticmethod
    async def _search_with_providers(term: str, model: str, country_config: Dict[str, Any]) -> List[SearchResult]:
        """Suche mit allen verfügbaren Providern"""
        results = []
        
        for provider_name, provider in provider_registry.items():
            try:
                # Prüfe Provider-Konfiguration
                if not SearchServiceUtils._is_provider_enabled(provider_name, country_config):
                    continue
                
                # Führe Suche durch
                provider_results = await provider.search(term, model)
                results.extend(provider_results)
                
                # Überwache Kosten
                cost_monitor.record_search(provider_name, len(provider_results))
                
            except Exception as e:
                logger.warning(f"Fehler bei Provider {provider_name}: {e}")
        
        return results

    @staticmethod
    def _is_provider_enabled(provider_name: str, country_config: Dict[str, Any]) -> bool:
        """Prüfe ob Provider für das Land aktiviert ist"""
        if not country_config:
            return True
        
        enabled_providers = country_config.get('enabled_providers', [])
        return provider_name in enabled_providers

    @staticmethod
    async def extract_and_process_data(search_results: List[SearchResult], mine_name: str, model: str) -> Dict[str, Any]:
        """Extrahiere und verarbeite Daten aus Suchergebnissen"""
        try:
            # Kombiniere alle Inhalte
            all_content = []
            for result in search_results:
                if result.content:
                    all_content.append(result.content)
            
            # Extrahiere strukturierte Daten
            data_extractor = DataExtractor()
            extracted_data = await data_extractor.extract_mine_data(
                mine_name, 
                all_content,
                model
            )
            
            # Weise Quellen zu
            data_with_sources = assign_sources_to_data(extracted_data, search_results)
            
            return data_with_sources
            
        except Exception as e:
            logger.error(f"Fehler bei Datenextraktion: {e}")
            return {}

    @staticmethod
    async def save_search_results(mine_name: str, model: str, data: Dict[str, Any], sources: List[SearchResult], country: str = None, region: str = None):
        """Speichere Suchergebnisse in der Datenbank"""
        try:
            db_manager = DatabaseManager()
            normalized_db_manager = NormalizedDatabaseManager()
            
            # Speichere in beiden Datenbanken für Kompatibilität
            await db_manager.save_search_result(mine_name, model, data, sources, country, region)
            await normalized_db_manager.save_search_result(mine_name, model, data, sources, country, region)
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Suchergebnisse: {e}")


__all__ = ["SearchServiceUtils"]
