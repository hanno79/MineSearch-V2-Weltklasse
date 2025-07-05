"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Async Utility-Funktionen für Multi-Provider Suchen
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AsyncSearchUtils:
    """Utility-Funktionen für asynchrone Suchen"""
    
    @staticmethod
    async def search_with_enhanced_query(registry, convert_func, model_id: str, mine_name: str,
                                       country: str, commodity: str, region: str,
                                       specialized_query: str, 
                                       discovered_sources: List[Dict]) -> Dict[str, Any]:
        """Führe Suche mit erweiterter Query und vorhandenen Quellen durch"""
        
        provider = registry.get_provider_for_model(model_id)
        if not provider:
            return {"success": False, "error": f"Provider für {model_id} nicht gefunden"}
        
        # Erweiterte Optionen mit discovered sources
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'temperature': 0.2,
            'pre_discovered_sources': discovered_sources  # Übergebe Quellen aus Phase 1
        }
        
        try:
            provider_name, model_key = model_id.split(':')
            result = await provider.search(specialized_query, model_key, options)
            return convert_func(result, model_id, mine_name, country)
        except Exception as e:
            logger.error(f"[TWO-PHASE] Fehler in Phase 2 mit {model_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def search_with_timeout(search_func, model_id: str, mine_name: str,
                                country: str, commodity: str, region: str,
                                timeout: int) -> Dict[str, Any]:
        """Führe Suche mit Timeout durch"""
        try:
            return await asyncio.wait_for(
                search_func(model_id, mine_name, country, commodity, region),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"[SOURCE-SHARING] Timeout für {model_id} nach {timeout}s")
            return {
                "success": False,
                "error": f"Timeout nach {timeout} Sekunden",
                "data": {}
            }
    
    @staticmethod
    async def execute_phase2_with_sources(sources: List[Dict], model_ids: List[str],
                                        mine_name: str, country: str, commodity: str, 
                                        region: str, start_time: datetime,
                                        search_service, phase_manager,
                                        source_sharing_config: Dict) -> Dict[str, Any]:
        """Führe Phase 2 mit vorhandenen Quellen aus"""
        
        # Erstelle erweiterte Query
        enhanced_query = phase_manager.build_source_sharing_query(
            mine_name, country, region, commodity, sources
        )
        
        # Phase 2 mit allen Modellen
        phase2_tasks = []
        for model_id in model_ids:
            if search_service.registry.is_model_available(model_id):
                task = search_service._analyze_with_shared_sources(
                    model_id, mine_name, country, commodity, region,
                    enhanced_query, sources
                )
                phase2_tasks.append(task)
        
        # Führe mit Timeout aus
        phase2_timeout = source_sharing_config.get('phase2_timeout', 60)
        phase2_results = []
        
        for task in phase2_tasks:
            try:
                result = await asyncio.wait_for(task, timeout=phase2_timeout)
                phase2_results.append(result)
            except asyncio.TimeoutError:
                phase2_results.append({"success": False, "error": "Phase 2 Timeout"})
        
        # Importiere hier um zirkuläre Imports zu vermeiden
        from search_result_combiner import SearchResultCombiner
        combiner = SearchResultCombiner()
        
        # Kombiniere Ergebnisse
        return combiner.combine_source_sharing_results(
            [], model_ids, phase2_results, start_time, sources
        )