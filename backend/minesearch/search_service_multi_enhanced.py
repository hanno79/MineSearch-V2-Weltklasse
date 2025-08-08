"""
Author: rahn
Datum: 12.07.2025  
Version: 2.0
Beschreibung: Refactored Enhanced Multi-Provider Search Service (CLAUDE.md konform)
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from enhanced_search_operations import EnhancedSearchOperations

logger = logging.getLogger(__name__)


class EnhancedMultiProviderSearchService(EnhancedSearchOperations):
    """
    Enhanced Service für Multi-Provider Mining-Suchen mit zweistufigem Prozess
    
    Erbt alle Funktionen von:
    - EnhancedSearchCore: Basis-Funktionen und Performance-Tracking
    - EnhancedSearchOperations: Such- und Extraktions-Operationen
    """
    
    async def search_comprehensive(self, mine_name: str, country: Optional[str] = None,
                                 commodity: Optional[str] = None, region: Optional[str] = None,
                                 max_source_models: int = 10, max_extraction_models: int = 8) -> Dict[str, Any]:
        """
        Umfassende zweistufige Suche: Erst Quellensammlung, dann Datenextraktion
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            max_source_models: Max. Modelle für Quellensammlung
            max_extraction_models: Max. Modelle für Datenextraktion
            
        Returns:
            Kombinierte und validierte Suchergebnisse
        """
        search_start = datetime.now()
        logger.info(f"[ENHANCED] Starte umfassende Suche für: {mine_name}")
        
        try:
            # PHASE 1: Quellensammlung mit allen verfügbaren Modellen
            logger.info(f"[ENHANCED] Phase 1: Quellensammlung mit {max_source_models} Modellen")
            
            sources = await self.collect_sources_all_models(
                mine_name, country, commodity, region, max_source_models
            )
            
            if not sources:
                logger.warning(f"[ENHANCED] Keine Quellen gefunden - verwende Basis-Suche")
                # Fallback auf einfache Suche mit bestem Modell
                top_models = self._get_top_performing_models(1)
                if top_models:
                    return await self.search_single_model(
                        top_models[0]['model_id'], mine_name, country, commodity, region
                    )
                else:
                    return {
                        "success": False,
                        "error": "Keine Quellen gefunden und keine Modelle verfügbar",
                        "data": {}
                    }
            
            # PHASE 2: Datenextraktion mit gefundenen Quellen
            logger.info(f"[ENHANCED] Phase 2: Datenextraktion mit {max_extraction_models} Modellen aus {len(sources)} Quellen")
            
            extraction_results = await self.extract_data_from_sources(
                sources, mine_name, country, commodity, max_extraction_models
            )
            
            if not extraction_results:
                logger.warning(f"[ENHANCED] Keine Extraktionsergebnisse - verwende nur Quellen")
                return {
                    "success": True,
                    "data": {
                        "structured_data": {},
                        "sources": sources,
                        "raw_data": f"Gefundene Quellen für {mine_name}",
                        "quality_metrics": {"quality_score": 0.1, "sources_found": len(sources)},
                        "search_type": "sources_only",
                        "models_used": 0
                    }
                }
            
            # PHASE 3: Kombination und Validierung der Ergebnisse
            logger.info(f"[ENHANCED] Phase 3: Kombination der Ergebnisse von {len(extraction_results)} Modellen")
            
            combined_result = self._combine_and_validate_results(
                extraction_results, sources, mine_name, country
            )
            
            # Berechne Gesamt-Performance
            total_time = (datetime.now() - search_start).total_seconds()
            combined_result['data']['performance_metrics'] = {
                'total_search_time': total_time,
                'sources_found': len(sources),
                'models_used': len(extraction_results),
                'search_timestamp': search_start.isoformat()
            }
            
            logger.info(f"[ENHANCED] Umfassende Suche abgeschlossen in {total_time:.2f}s: "
                       f"{len(sources)} Quellen, {len(extraction_results)} Modelle")
            
            return combined_result
            
        except Exception as e:
            total_time = (datetime.now() - search_start).total_seconds()
            error_msg = f"Fehler bei umfassender Suche: {str(e)}"
            logger.error(f"[ENHANCED] {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "data": {
                    "performance_metrics": {
                        "total_search_time": total_time,
                        "search_timestamp": search_start.isoformat()
                    }
                }
            }
    
    async def search_with_timeout(self, model_id: str, query: str, 
                                 options: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """
        Führt Suche mit Timeout durch
        
        Args:
            model_id: Modell-ID
            query: Suchanfrage
            options: Such-Optionen
            timeout: Timeout in Sekunden
            
        Returns:
            Suchergebnis oder Timeout-Fehler
        """
        try:
            provider = self.registry.get_provider_for_model(model_id)
            if not provider:
                return {
                    "success": False,
                    "error": f"Provider für {model_id} nicht verfügbar",
                    "data": {}
                }
            
            # Führe Suche mit Timeout durch
            provider_name, model_key = model_id.split(':')
            
            result = await asyncio.wait_for(
                provider.search(query, model_key, options),
                timeout=timeout
            )
            
            return self._convert_to_standard_format(
                result, model_id, options.get('mine_name', ''), options.get('country')
            )
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout ({timeout}s) bei {model_id}"
            logger.warning(f"[ENHANCED] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "data": {}
            }
        except Exception as e:
            error_msg = f"Fehler bei {model_id}: {str(e)}"
            logger.error(f"[ENHANCED] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "data": {}
            }
    
    def _combine_and_validate_results(self, extraction_results: Dict[str, Dict[str, Dict]], 
                                    sources: List[Dict], mine_name: str, 
                                    country: Optional[str]) -> Dict[str, Any]:
        """
        Kombiniert und validiert Extraktionsergebnisse von mehreren Modellen
        
        Args:
            extraction_results: Ergebnisse von verschiedenen Modellen
            sources: Verwendete Quellen
            mine_name: Name der Mine
            country: Land
            
        Returns:
            Kombiniertes und validiertes Ergebnis
        """
        try:
            # Sammle alle strukturierten Daten
            all_structured_data = {}
            successful_extractions = 0
            all_raw_data = []
            field_consensus = {}
            
            # Iteriere durch alle Modell-Ergebnisse
            for model_id, prompt_results in extraction_results.items():
                for prompt_type, result in prompt_results.items():
                    if result.get('success') and result.get('data'):
                        successful_extractions += 1
                        
                        structured_data = result['data'].get('structured_data', {})
                        raw_data = result['data'].get('raw_data', '')
                        
                        if raw_data:
                            all_raw_data.append(f"[{model_id}:{prompt_type}]\n{raw_data}\n")
                        
                        # Sammle Feldwerte für Konsens-Bildung
                        for field, value in structured_data.items():
                            if value and str(value).strip():
                                if field not in field_consensus:
                                    field_consensus[field] = {}
                                
                                value_str = str(value).strip()
                                if value_str not in field_consensus[field]:
                                    field_consensus[field][value_str] = 0
                                field_consensus[field][value_str] += 1
            
            # Bestimme Konsens-Werte (nehme häufigste Werte)
            final_data = {}
            for field, value_counts in field_consensus.items():
                if value_counts:
                    # Sortiere nach Häufigkeit
                    sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
                    best_value = sorted_values[0][0]
                    
                    # Akzeptiere nur Werte mit mindestens 2 Nennungen oder bei nur einem Modell
                    if sorted_values[0][1] >= 2 or len(extraction_results) == 1:
                        final_data[field] = best_value
            
            # Berechne Qualitäts-Metriken
            quality_score = self._calculate_simple_quality(final_data)
            
            # Kombiniere alle Raw-Daten
            combined_raw_data = "\n".join(all_raw_data) if all_raw_data else f"Suchergebnisse für {mine_name}"
            
            quality_metrics = {
                "quality_score": quality_score,
                "filled_fields": len(final_data),
                "successful_extractions": successful_extractions,
                "total_extractions": sum(len(results) for results in extraction_results.values()),
                "consensus_fields": len([f for f, values in field_consensus.items() if max(values.values()) >= 2]),
                "sources_used": len(sources)
            }
            
            return {
                "success": True,
                "data": {
                    "structured_data": final_data,
                    "raw_data": combined_raw_data,
                    "sources": sources,
                    "quality_metrics": quality_metrics,
                    "search_type": "enhanced_comprehensive",
                    "models_used": len(extraction_results),
                    "extraction_breakdown": {
                        model_id: {
                            "prompts_used": len(results),
                            "successful_prompts": len([r for r in results.values() if r.get('success')])
                        } for model_id, results in extraction_results.items()
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"[ENHANCED] Fehler bei Ergebnis-Kombination: {e}")
            return {
                "success": False,
                "error": f"Fehler bei Ergebnis-Kombination: {str(e)}",
                "data": {}
            }


# Globale Service-Instanz
enhanced_search_service = EnhancedMultiProviderSearchService()