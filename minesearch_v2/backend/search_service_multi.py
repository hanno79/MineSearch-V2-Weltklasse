"""
Author: rahn
Datum: 02.07.2025  
Version: 1.0
Beschreibung: Multi-Provider Search Service für MineSearch
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from config import config, Config
from providers.registry import provider_registry
from providers.base_provider import SearchResult
from source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config

logger = logging.getLogger(__name__)


class MultiProviderSearchService:
    """Service für Multi-Provider Mining-Suchen"""
    
    def __init__(self):
        # Initialisiere Provider Registry
        provider_registry.initialize(config.PROVIDERS)
        self.registry = provider_registry
        self.enhanced_discovery = EnhancedSourceDiscovery()
    
    async def search_with_model(self, model_id: str, mine_name: str, 
                               country: Optional[str] = None,
                               commodity: Optional[str] = None,
                               region: Optional[str] = None) -> Dict[str, Any]:
        """
        Führe Suche mit einem spezifischen Modell durch
        
        Args:
            model_id: Modell-ID im Format "provider:model"
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Suchergebnis im Standard-Format
        """
        # Validiere Modell
        if not self.registry.is_model_available(model_id):
            return {
                "success": False,
                "error": f"Modell {model_id} nicht verfügbar",
                "data": {}
            }
        
        # Hole Provider und Modell-Config
        provider = self.registry.get_provider_for_model(model_id)
        model_config = self.registry.get_model_config(model_id)
        
        if not provider:
            return {
                "success": False,
                "error": f"Provider für {model_id} nicht gefunden",
                "data": {}
            }
        
        # Starte Source Discovery Session
        session = self.enhanced_discovery.start_session(mine_name, country, region)
        
        # Source Discovery nur für Web-Search-fähige Modelle
        discovered_sources = []
        if model_config.supports_web_search:
            discovered_sources = self.enhanced_discovery.discover_sources_for_mine(
                mine_name, country, region, commodity
            )
            logger.info(f"[MULTI-SEARCH] {len(discovered_sources)} Quellen für {mine_name} entdeckt")
        
        # Erstelle Suchanfrage
        name_variants = generate_name_variants(mine_name)
        multilingual_terms = generate_multilingual_search_terms(mine_name, country)
        
        # Basis-Query
        query = self._build_search_query(
            mine_name, name_variants, multilingual_terms, 
            country, commodity, model_id, discovered_sources
        )
        
        # Provider-spezifische Optionen
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'currency': get_country_config(country).get('currency', 'USD') if country else 'USD',
            'name_variants': name_variants,
            'discovered_sources': discovered_sources
        }
        
        # Führe Suche durch
        try:
            provider_name, model_key = model_id.split(':')
            result = await provider.search(query, model_key, options)
            
            # Konvertiere Provider-Result in Standard-Format
            return self._convert_to_standard_format(result, model_id, mine_name, country)
            
        except Exception as e:
            logger.error(f"[MULTI-SEARCH] Fehler bei {model_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
        finally:
            # Finalisiere Session
            if session:
                self.enhanced_discovery.finalize_session()
    
    async def search_with_multiple_models(self, model_ids: List[str], mine_name: str,
                                        country: Optional[str] = None,
                                        commodity: Optional[str] = None,
                                        region: Optional[str] = None) -> Dict[str, Any]:
        """
        Führe Suche mit mehreren Modellen parallel durch
        
        Args:
            model_ids: Liste von Modell-IDs
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Dict mit Ergebnissen pro Modell
        """
        # Erstelle Tasks für alle Modelle
        tasks = []
        for model_id in model_ids:
            task = self.search_with_model(model_id, mine_name, country, commodity, region)
            tasks.append((model_id, task))
        
        # Führe alle Suchen parallel aus
        results = {}
        for model_id, task in tasks:
            try:
                result = await task
                results[model_id] = result
            except Exception as e:
                logger.error(f"[MULTI-SEARCH] Fehler bei {model_id}: {str(e)}")
                results[model_id] = {
                    "success": False,
                    "error": str(e),
                    "data": {}
                }
        
        return {
            "success": True,
            "mine_name": mine_name,
            "country": country,
            "models_searched": len(model_ids),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _build_search_query(self, mine_name: str, name_variants: List[str],
                           multilingual_terms: List[str], country: Optional[str],
                           commodity: Optional[str], model_id: str,
                           discovered_sources: List[Dict[str, Any]]) -> str:
        """Erstelle Suchanfrage basierend auf Modell-Fähigkeiten"""
        
        model_config = self.registry.get_model_config(model_id)
        
        # Basis-Query
        query = f"Finde Informationen über die Mine: {mine_name}"
        
        if name_variants and len(name_variants) > 1:
            query += f" (auch bekannt als: {', '.join(name_variants[:2])})"
        
        if country:
            query += f" in {country}"
        
        if commodity:
            query += f", die {commodity} abbaut"
        
        # Füge discovered sources hinzu für Web-Search-fähige Modelle
        if model_config.supports_web_search and discovered_sources:
            query += "\n\nPrüfe speziell diese Quellen:\n"
            for source in discovered_sources[:10]:
                query += f"- {source['url']} ({source.get('description', '')})\n"
        
        # Spezielle Anweisungen
        query += "\n\nFokussiere besonders auf:"
        query += "\n- Restaurationskosten / Closure Costs / Environmental Liabilities"
        query += "\n- Betreiber und Eigentümer"
        query += "\n- Produktionsdaten und Status"
        query += "\n- Genaue Koordinaten"
        
        return query
    
    def _convert_to_standard_format(self, provider_result: SearchResult, 
                                   model_id: str, mine_name: str,
                                   country: Optional[str]) -> Dict[str, Any]:
        """Konvertiere Provider-Result in Standard MineSearch Format"""
        
        if not provider_result.success:
            return {
                "success": False,
                "error": provider_result.error,
                "data": {}
            }
        
        # Berechne Datenqualität
        data_quality = self._calculate_data_quality(provider_result.structured_data)
        
        return {
            "success": True,
            "data": {
                "content": provider_result.content,
                "mine_name": mine_name,
                "structured_data": provider_result.structured_data,
                "structured_data_with_sources": provider_result.metadata.get('structured_data_with_sources', {}),
                "source_index": provider_result.metadata.get('source_index', {}),
                "sources": provider_result.sources,
                "source_summary": {
                    "urls": len([s for s in provider_result.sources if s.get('type') == 'url']),
                    "documents": len([s for s in provider_result.sources if s.get('type') == 'document']),
                    "organizations": len([s for s in provider_result.sources if s.get('type') == 'organization']),
                    "total": len(provider_result.sources)
                },
                "data_quality": data_quality,
                "search_metadata": {
                    "model_used": model_id,
                    "provider": provider_result.metadata.get('provider', 'unknown'),
                    "search_timestamp": datetime.now().isoformat(),
                    "search_duration": provider_result.search_duration
                }
            }
        }
    
    def _calculate_data_quality(self, structured_data: Dict[str, str]) -> Dict[str, Any]:
        """Berechne Datenqualitäts-Metriken"""
        from config import CSV_COLUMNS
        
        filled_fields = sum(1 for col in CSV_COLUMNS if structured_data.get(col) and col != 'Name')
        total_fields = len(CSV_COLUMNS) - 1  # Minus Name-Feld
        data_completeness = filled_fields / total_fields if total_fields > 0 else 0
        
        # Bestimme Qualitätsstufe
        if data_completeness >= 0.7:
            quality_level = "Hoch"
        elif data_completeness >= 0.4:
            quality_level = "Mittel"
        else:
            quality_level = "Niedrig"
        
        return {
            "filled_fields": filled_fields,
            "total_fields": total_fields,
            "completeness_percentage": round(data_completeness * 100),
            "quality_level": quality_level,
            "missing_critical_fields": [
                col for col in ['Betreiber', 'Restaurationskosten', 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'] 
                if not structured_data.get(col)
            ]
        }


# Globale Service-Instanz
multi_search_service = MultiProviderSearchService()