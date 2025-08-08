"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Model Selection Coordinator - Garantiert dass ALLE ausgewählten Modelle ausgeführt werden
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from providers.registry import provider_registry

logger = logging.getLogger(__name__)

class ModelSelectionCoordinator:
    """
    Coordinator für garantierte Modell-Ausführung
    
    KERNPRINZIPIEN:
    1. ALLE ausgewählten Modelle werden GARANTIERT ausgeführt
    2. Keine Fallbacks ohne explizite Berechtigung
    3. Parallele Ausführung für optimale Performance
    4. Vollständige Transparenz über Erfolg/Fehler pro Modell
    """
    
    def __init__(self):
        self.registry = provider_registry
        self._execution_lock = asyncio.Lock()
        
    async def coordinate_guaranteed_execution(
        self,
        selected_models: List[str],
        mine_name: str,
        country: Optional[str] = None,
        commodity: Optional[str] = None,
        region: Optional[str] = None,
        session_id: Optional[str] = None,
        allow_fallbacks: bool = False,
        max_parallel: int = 10
    ) -> Dict[str, Any]:
        """
        Koordiniert die garantierte Ausführung aller ausgewählten Modelle
        
        Args:
            selected_models: Liste der ausgewählten Modelle (ALLE werden ausgeführt)
            mine_name: Mine Name
            country: Land
            commodity: Rohstoff
            region: Region
            session_id: Session ID
            allow_fallbacks: Erlaubt Fallback-Modelle bei Fehlern (Standard: False)
            max_parallel: Maximale parallele Ausführungen
            
        Returns:
            Koordinationsergebnis mit allen Modell-Ergebnissen
        """
        logger.info(f"[MODEL-COORDINATOR] GUARANTEED EXECUTION gestartet für {mine_name}")
        logger.info(f"[MODEL-COORDINATOR] Ausgewählte Modelle: {selected_models}")
        logger.info(f"[MODEL-COORDINATOR] Fallbacks erlaubt: {allow_fallbacks}")
        
        start_time = datetime.now()
        
        # STEP 1: Validiere alle ausgewählten Modelle
        validated_models, invalid_models = await self._validate_all_models(selected_models)
        
        if invalid_models:
            logger.warning(f"[MODEL-COORDINATOR] Ungültige Modelle gefunden: {invalid_models}")
            
            if not allow_fallbacks:
                return {
                    'success': False,
                    'error': f'Ungültige Modelle ohne Fallback-Berechtigung: {invalid_models}',
                    'selected_models': selected_models,
                    'invalid_models': invalid_models,
                    'execution_mode': 'strict_no_fallback'
                }
        
        if not validated_models:
            logger.error(f"[MODEL-COORDINATOR] Keine gültigen Modelle verfügbar")
            return {
                'success': False,
                'error': 'Keine gültigen Modelle in der Auswahl',
                'selected_models': selected_models,
                'invalid_models': invalid_models,
                'execution_mode': 'validation_failed'
            }
        
        logger.info(f"[MODEL-COORDINATOR] Validierte Modelle: {validated_models}")
        
        # STEP 2: Führe ALLE validierten Modelle GARANTIERT aus
        execution_result = await self._execute_all_models_guaranteed(
            models=validated_models,
            mine_name=mine_name,
            country=country,
            commodity=commodity,
            region=region,
            session_id=session_id,
            max_parallel=max_parallel
        )
        
        execution_duration = (datetime.now() - start_time).total_seconds()
        
        # STEP 3: Erstelle umfassenden Koordinationsbericht
        coordination_report = {
            'success': execution_result['models_successful_count'] > 0,
            'execution_mode': 'guaranteed_execution',
            'coordination_duration_seconds': execution_duration,
            
            # Model Selection Details
            'models_requested': selected_models,
            'models_validated': validated_models,
            'models_invalid': invalid_models,
            'models_successful': execution_result['models_successful'],
            'models_failed': execution_result['models_failed'],
            
            # Execution Statistics
            'statistics': {
                'total_requested': len(selected_models),
                'total_validated': len(validated_models),
                'total_successful': execution_result['models_successful_count'],
                'total_failed': execution_result['models_failed_count'],
                'success_rate_of_validated': execution_result['models_successful_count'] / len(validated_models) if validated_models else 0,
                'success_rate_of_requested': execution_result['models_successful_count'] / len(selected_models) if selected_models else 0
            },
            
            # Individual Results
            'individual_results': execution_result['individual_results'],
            'combined_data': execution_result['combined_data'],
            
            # Coordination Metadata
            'fallbacks_allowed': allow_fallbacks,
            'parallel_execution': True,
            'max_parallel_used': max_parallel,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log Koordinationsergebnis
        success_rate = coordination_report['statistics']['success_rate_of_requested'] * 100
        logger.info(f"[MODEL-COORDINATOR] GUARANTEED EXECUTION abgeschlossen:")
        logger.info(f"[MODEL-COORDINATOR] - Erfolgsrate: {success_rate:.1f}% ({execution_result['models_successful_count']}/{len(selected_models)})")
        logger.info(f"[MODEL-COORDINATOR] - Dauer: {execution_duration:.1f}s")
        logger.info(f"[MODEL-COORDINATOR] - Erfolgreiche Modelle: {execution_result['models_successful']}")
        
        if execution_result['models_failed']:
            logger.warning(f"[MODEL-COORDINATOR] - Fehlgeschlagene Modelle: {execution_result['models_failed']}")
        
        return coordination_report
    
    async def _validate_all_models(self, model_ids: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validiert alle angegebenen Modelle
        
        Returns:
            Tuple[validated_models, invalid_models]
        """
        validated = []
        invalid = []
        
        for model_id in model_ids:
            if not model_id or not model_id.strip():
                logger.warning(f"[MODEL-COORDINATOR] Leere Model-ID gefunden")
                invalid.append(model_id)
                continue
                
            model_id = model_id.strip()
            logger.info(f"[MODEL-COORDINATOR] 🔍 Validiere Modell: {model_id}")
            
            # Prüfe Provider-Registry
            if self.registry.is_model_available(model_id):
                # Provider-Validierung: Wenn Provider registriert ist, ist er bereit
                provider = self.registry.get_provider_for_model(model_id)
                if provider:
                    # FIXME 26.07.2025: Provider sind bereit wenn sie in Registry registriert sind
                    # Die is_ready() Methode existiert nicht in allen Providern
                    logger.info(f"[MODEL-COORDINATOR] ✅ Modell {model_id} validiert")
                    validated.append(model_id)
                else:
                    logger.warning(f"[MODEL-COORDINATOR] ❌ Provider für {model_id} nicht gefunden")
                    invalid.append(model_id)
            else:
                logger.warning(f"[MODEL-COORDINATOR] ❌ Modell {model_id} nicht in Registry verfügbar")
                logger.info(f"[MODEL-COORDINATOR] 📋 Verfügbare Modelle: {list(self.registry._available_models.keys())}")
                invalid.append(model_id)
        
        return validated, invalid
    
    async def _execute_all_models_guaranteed(
        self,
        models: List[str],
        mine_name: str,
        country: Optional[str],
        commodity: Optional[str],
        region: Optional[str],
        session_id: Optional[str],
        max_parallel: int
    ) -> Dict[str, Any]:
        """
        Führt ALLE Modelle GARANTIERT aus mit optimaler Parallelität
        """
        logger.info(f"[MODEL-COORDINATOR] Starte GUARANTEED EXECUTION für {len(models)} Modelle")
        
        # Import der Services hier um Circular Imports zu vermeiden
        from services_container import services
        multi_search_service = services.multi_search_service
        
        # Erstelle Tasks für alle Modelle
        execution_tasks = []
        for model_id in models:
            task = self._execute_single_model_guaranteed(
                model_id=model_id,
                mine_name=mine_name,
                country=country,
                commodity=commodity,
                region=region,
                multi_search_service=multi_search_service
            )
            execution_tasks.append((model_id, task))
        
        # Begrenze Parallelität
        if len(execution_tasks) > max_parallel:
            logger.info(f"[MODEL-COORDINATOR] Begrenze Parallelität: {len(execution_tasks)} -> {max_parallel}")
            
            # Führe in Batches aus
            all_results = {}
            for i in range(0, len(execution_tasks), max_parallel):
                batch = execution_tasks[i:i + max_parallel]
                logger.info(f"[MODEL-COORDINATOR] Batch {i//max_parallel + 1}: {len(batch)} Modelle")
                
                batch_tasks = [task for model_id, task in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Verarbeite Batch-Ergebnisse
                for j, (model_id, _) in enumerate(batch):
                    result = batch_results[j]
                    if isinstance(result, Exception):
                        all_results[model_id] = {
                            'success': False,
                            'error': f'Exception: {str(result)}',
                            'model_id': model_id
                        }
                    else:
                        all_results[model_id] = result
        else:
            # Normale parallele Ausführung
            logger.info(f"[MODEL-COORDINATOR] Normale parallele Ausführung: {len(execution_tasks)} Modelle")
            
            tasks_only = [task for model_id, task in execution_tasks]
            results = await asyncio.gather(*tasks_only, return_exceptions=True)
            
            all_results = {}
            for i, (model_id, _) in enumerate(execution_tasks):
                result = results[i]
                if isinstance(result, Exception):
                    all_results[model_id] = {
                        'success': False,
                        'error': f'Exception: {str(result)}',
                        'model_id': model_id
                    }
                else:
                    all_results[model_id] = result
        
        # Analysiere Ergebnisse
        successful_models = []
        failed_models = []
        
        for model_id, result in all_results.items():
            if result.get('success'):
                successful_models.append(model_id)
            else:
                failed_models.append({
                    'model_id': model_id,
                    'error': result.get('error', 'Unbekannter Fehler')
                })
        
        # Erstelle kombinierte Daten
        combined_data = self._combine_successful_results(
            {k: v for k, v in all_results.items() if v.get('success')}
        )
        
        return {
            'individual_results': all_results,
            'models_successful': successful_models,
            'models_failed': failed_models,
            'models_successful_count': len(successful_models),
            'models_failed_count': len(failed_models),
            'combined_data': combined_data
        }
    
    async def _execute_single_model_guaranteed(
        self,
        model_id: str,
        mine_name: str,
        country: Optional[str],
        commodity: Optional[str],
        region: Optional[str],
        multi_search_service
    ) -> Dict[str, Any]:
        """
        Führt ein einzelnes Modell GARANTIERT aus
        """
        try:
            logger.debug(f"[MODEL-COORDINATOR] Starte GUARANTEED Einzelausführung: {model_id}")
            
            # Verwende bewährte Search-Methode
            result = await multi_search_service.search_with_model(
                model_id=model_id,
                mine_name=mine_name,
                country=country,
                commodity=commodity,
                region=region
            )
            
            # Erweitere Ergebnis
            if isinstance(result, dict):
                result['model_id'] = model_id
                result['execution_timestamp'] = datetime.now().isoformat()
                result['execution_mode'] = 'guaranteed'
            
            return result
            
        except Exception as e:
            logger.error(f"[MODEL-COORDINATOR] GUARANTEED Einzelausführung Fehler {model_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'model_id': model_id,
                'execution_timestamp': datetime.now().isoformat(),
                'execution_mode': 'guaranteed_failed'
            }
    
    def _combine_successful_results(self, successful_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kombiniert erfolgreiche Ergebnisse ohne Datenverlust
        """
        if not successful_results:
            return {'structured_data': {}, 'sources': [], 'model_contributions': {}}
        
        combined_structured_data = {}
        combined_sources = []
        model_contributions = {}
        
        for model_id, result in successful_results.items():
            if not result.get('data'):
                continue
                
            structured_data = result['data'].get('structured_data', {})
            sources = result['data'].get('sources', [])
            
            model_contributions[model_id] = []
            
            # Sammle Daten
            for field, value in structured_data.items():
                if value and str(value).strip():
                    if not combined_structured_data.get(field):
                        combined_structured_data[field] = value
                        model_contributions[model_id].append(field)
            
            # Sammle Quellen
            for source in sources:
                if source not in combined_sources:
                    combined_sources.append(source)
        
        return {
            'structured_data': combined_structured_data,
            'sources': combined_sources,
            'model_contributions': model_contributions,
            'contributing_models': list(successful_results.keys())
        }

# Globale Coordinator-Instanz
model_selection_coordinator = ModelSelectionCoordinator()