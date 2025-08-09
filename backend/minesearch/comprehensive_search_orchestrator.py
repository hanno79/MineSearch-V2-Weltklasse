"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Comprehensive Search Orchestrator - Systematische Vollständige Durchsuchung
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

from gestim_connector import gestim_connector
from quebec_registry_connector import quebec_registry_connector
from bilingual_search_strategy import bilingual_search_strategy
from source_discovery import source_discovery
from providers.registry import provider_registry

logger = logging.getLogger(__name__)

@dataclass
class SearchTask:
    """Repräsentiert eine einzelne Suchaufgabe"""
    model_id: str
    search_term: str
    field_type: str
    priority: int
    source_type: str
    completed: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class FieldCompletionStatus:
    """Status der Feldvervollständigung"""
    field_name: str
    attempts: int
    success: bool
    best_value: Optional[str]
    sources_found: List[str]
    models_tried: List[str]

class ComprehensiveSearchOrchestrator:
    """
    Orchestriert vollständige systematische Durchsuchung aller Quellen
    durch alle Modelle für alle Felder ohne Auslassung
    """
    
    def __init__(self):
        self.registry = provider_registry
        
        # Kritische Felder die IMMER vollständig durchsucht werden müssen
        self.critical_fields = [
            'Restaurationskosten',
            'Eigentümer', 
            'Betreiber',
            'x-Koordinate',
            'y-Koordinate',
            'Aktivitätsstatus',
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
            'Minentyp (Untertage/ Open-Pit/ usw.)',
            'Produktionsstart',
            'Produktionsende',
            'Fördermenge/Jahr',
            'Fläche der Mine in qkm'
        ]
        
        # Stopkriterien - wann darf ein Feld als "vollständig durchsucht" gelten
        self.completion_criteria = {
            'min_models_tried': 3,  # Mindestens 3 verschiedene Modelle
            'min_sources_attempted': 5,  # Mindestens 5 verschiedene Quellen
            'success_threshold': 1  # Mindestens 1 erfolgreiche Extraktion
        }
        
        # Source-Discovery Tracker
        self.discovered_sources: Set[str] = set()
        self.source_quality_scores: Dict[str, float] = {}
        
    async def orchestrate_comprehensive_search(self, mine_name: str, country: str = "Canada", 
                                             region: str = "Quebec", commodity: str = None,
                                             available_models: List[str] = None) -> Dict[str, Any]:
        """
        Orchestriert vollständige systematische Durchsuchung
        
        Args:
            mine_name: Name der Mine
            country: Land
            region: Region
            commodity: Rohstoff (optional)
            available_models: Verfügbare Modelle (optional)
            
        Returns:
            Vollständiges Suchergebnis mit Completion-Status
        """
        logger.info(f"[ORCHESTRATOR] Starte comprehensive search für {mine_name}")
        
        start_time = datetime.now()
        
        # 1. QUEBEC-SPEZIFISCHE VORBEREITUNG
        quebec_data = await self._prepare_quebec_sources(mine_name, region)
        
        # 2. BILINGUALE SUCHSTRATEGIE
        search_terms = bilingual_search_strategy.generate_comprehensive_search_terms(
            mine_name, region, self.critical_fields
        )
        
        # 3. MODELL-VERFÜGBARKEIT
        if available_models is None:
            available_models = self._get_available_models()
        
        # 4. SYSTEMATISCHE FELDBEARBEITUNG
        field_status = {}
        all_search_tasks = []
        
        for field_name in self.critical_fields:
            field_status[field_name] = FieldCompletionStatus(
                field_name=field_name,
                attempts=0,
                success=False,
                best_value=None,
                sources_found=[],
                models_tried=[]
            )
            
            # Erstelle Suchaufgaben für dieses Feld
            field_tasks = self._create_field_search_tasks(
                field_name, mine_name, search_terms, available_models
            )
            all_search_tasks.extend(field_tasks)
        
        # 5. PARALLEL SEARCH EXECUTION
        logger.info(f"[ORCHESTRATOR] Führe {len(all_search_tasks)} Suchaufgaben parallel aus")
        
        # Priorisierte Ausführung in Batches
        completed_tasks = await self._execute_search_tasks_prioritized(all_search_tasks)
        
        # 6. ERGEBNIS-AGGREGATION
        aggregated_results = await self._aggregate_search_results(
            completed_tasks, field_status, quebec_data
        )
        
        # 7. COMPLETION-VALIDIERUNG
        completion_report = self._validate_field_completion(field_status)
        
        # 8. QUELLENQUALITÄT BEWERTEN
        source_quality_report = self._evaluate_source_quality()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        final_result = {
            'success': True,
            'mine_name': mine_name,
            'country': country,
            'region': region,
            'search_strategy': 'comprehensive_systematic',
            'duration_seconds': duration,
            'data': aggregated_results,
            'field_completion_status': {
                field: {
                    'attempts': status.attempts,
                    'success': status.success,
                    'models_tried': len(status.models_tried),
                    'sources_found': len(status.sources_found)
                }
                for field, status in field_status.items()
            },
            'completion_report': completion_report,
            'source_quality_report': source_quality_report,
            'total_tasks_executed': len(completed_tasks),
            'quebec_sources_integrated': bool(quebec_data.get('success'))
        }
        
        logger.info(f"[ORCHESTRATOR] Comprehensive search abgeschlossen in {duration:.1f}s")
        return final_result
    
    async def _prepare_quebec_sources(self, mine_name: str, region: str) -> Dict[str, Any]:
        """Bereite Quebec-spezifische Quellen vor"""
        try:
            # GESTIM Integration
            gestim_result = await gestim_connector.search_mine(mine_name)
            
            # Quebec Registry Integration
            registry_result = await quebec_registry_connector.search_comprehensive(
                mine_name, region
            )
            
            combined_sources = {
                'success': gestim_result.get('success') or registry_result.get('success'),
                'gestim_data': gestim_result.get('data', {}),
                'registry_data': registry_result.get('data', {}),
                'quebec_search_terms': gestim_connector.get_quebec_search_terms(mine_name)
            }
            
            # Füge Quellen zur Discovery hinzu
            if gestim_result.get('success'):
                gestim_url = gestim_result['data'].get('gestim_url')
                if gestim_url:
                    self.discovered_sources.add(gestim_url)
                    self.source_quality_scores[gestim_url] = 0.9  # High quality
            
            return combined_sources
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Fehler bei Quebec-Quellen Vorbereitung: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_available_models(self) -> List[str]:
        """Hole alle verfügbaren Modelle"""
        try:
            available = []
            for provider_name in self.registry.get_available_providers():
                provider = self.registry.get_provider(provider_name)
                if provider:
                    models = provider.get_available_models()
                    for model in models:
                        available.append(f"{provider_name}:{model}")
            
            # Priorisiere Premium-Modelle für kritische Felder
            premium_models = [m for m in available if any(p in m for p in ['gpt-4', 'claude-3', 'gemini-pro'])]
            free_models = [m for m in available if m not in premium_models]
            
            # Kombiniere: Premium zuerst, dann kostenlose
            return premium_models + free_models
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Fehler beim Laden verfügbarer Modelle: {e}")
            return ['openrouter:gpt-3.5-turbo']  # Fallback
    
    def _create_field_search_tasks(self, field_name: str, mine_name: str, 
                                 search_terms: Dict[str, List], 
                                 available_models: List[str]) -> List[SearchTask]:
        """Erstelle Suchaufgaben für ein spezifisches Feld"""
        tasks = []
        
        # Feld-spezifische Suchbegriffe
        field_type = self._map_field_to_type(field_name)
        field_terms = search_terms.get(field_type, [])
        
        if not field_terms:
            # Fallback: Allgemeine Begriffe
            field_terms = search_terms.get('general', [])
        
        # Erstelle Tasks für jede Kombination von Modell und Suchbegriff
        for i, model_id in enumerate(available_models[:5]):  # Max 5 Modelle pro Feld
            for j, term in enumerate(field_terms[:3]):  # Max 3 Begriffe pro Modell
                priority = (i + 1) * (j + 1)  # Niedrigere Zahl = höhere Priorität
                
                task = SearchTask(
                    model_id=model_id,
                    search_term=f"{term.french} OR {term.english}",
                    field_type=field_name,
                    priority=priority,
                    source_type='bilingual_systematic'
                )
                tasks.append(task)
        
        return tasks
    
    def _map_field_to_type(self, field_name: str) -> str:
        """Mappe deutschen Feldnamen zu Suchtyp"""
        mapping = {
            'Restaurationskosten': 'restoration_costs',
            'Eigentümer': 'owner',
            'Betreiber': 'operator',
            'x-Koordinate': 'coordinates',
            'y-Koordinate': 'coordinates',
            'Aktivitätsstatus': 'status',
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'commodity',
            'Minentyp (Untertage/ Open-Pit/ usw.)': 'mine_type',
            'Produktionsstart': 'production',
            'Produktionsende': 'production',
            'Fördermenge/Jahr': 'production',
            'Fläche der Mine in qkm': 'area'
        }
        return mapping.get(field_name, 'general')
    
    async def _execute_search_tasks_prioritized(self, tasks: List[SearchTask]) -> List[SearchTask]:
        """Führe Suchaufgaben priorisiert aus"""
        # Sortiere nach Priorität
        tasks.sort(key=lambda t: t.priority)
        
        # Batch-weise Ausführung um Überlastung zu vermeiden
        batch_size = 10
        completed_tasks = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            logger.info(f"[ORCHESTRATOR] Führe Batch {i//batch_size + 1} aus ({len(batch)} Tasks)")
            
            # Führe Batch parallel aus
            batch_results = await asyncio.gather(
                *[self._execute_single_search_task(task) for task in batch],
                return_exceptions=True
            )
            
            # Verarbeite Batch-Ergebnisse
            for task, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    task.error = str(result)
                    task.completed = True
                else:
                    task.result = result
                    task.completed = True
                
                completed_tasks.append(task)
            
            # Kurze Pause zwischen Batches
            await asyncio.sleep(1)
        
        return completed_tasks
    
    async def _execute_single_search_task(self, task: SearchTask) -> Dict[str, Any]:
        """Führe eine einzelne Suchaufgabe aus"""
        try:
            # Hole Provider und Modell
            provider_name, model_key = task.model_id.split(':')
            provider = self.registry.get_provider(provider_name)
            
            if not provider:
                raise ValueError(f"Provider {provider_name} nicht verfügbar")
            
            # Führe Suche aus
            result = await provider.search(
                query=task.search_term,
                model_key=model_key,
                options={
                    'field_focus': task.field_type,
                    'source_type': task.source_type,
                    'priority': task.priority
                }
            )
            
            logger.debug(f"[ORCHESTRATOR] Task {task.model_id}:{task.field_type} erfolgreich")
            return result
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Task {task.model_id}:{task.field_type} fehlgeschlagen: {e}")
            raise e
    
    async def _aggregate_search_results(self, completed_tasks: List[SearchTask], 
                                      field_status: Dict[str, FieldCompletionStatus],
                                      quebec_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregiere Suchergebnisse"""
        aggregated_data = {}
        
        # Gruppiere Tasks nach Feld
        tasks_by_field = defaultdict(list)
        for task in completed_tasks:
            if task.completed and task.result and not task.error:
                tasks_by_field[task.field_type].append(task)
        
        # Verarbeite jedes Feld
        for field_name in self.critical_fields:
            field_tasks = tasks_by_field.get(field_name, [])
            status = field_status[field_name]
            
            # Aktualisiere Status
            status.attempts = len(field_tasks)
            status.models_tried = list(set(t.model_id for t in field_tasks))
            
            # Finde besten Wert
            best_value = None
            best_sources = []
            
            for task in field_tasks:
                if task.result and task.result.get('success'):
                    extracted_value = self._extract_field_value(task.result, field_name)
                    if extracted_value and extracted_value != 'X':
                        best_value = extracted_value
                        status.success = True
                        
                        # Sammle Quellen
                        task_sources = task.result.get('sources', [])
                        best_sources.extend(task_sources)
                        break  # Erste erfolgreiche Extraktion verwenden
            
            # Quebec-Daten als Fallback
            if not best_value and quebec_data.get('success'):
                quebec_value = self._extract_quebec_field_value(quebec_data, field_name)
                if quebec_value:
                    best_value = quebec_value
                    status.success = True
                    best_sources = ['GESTIM_Quebec_Database']
            
            # Markiere als X wenn gesucht aber nicht gefunden
            if not best_value and status.attempts >= self.completion_criteria['min_models_tried']:
                best_value = 'X'  # Systematisch gesucht aber nicht gefunden
            
            status.best_value = best_value
            status.sources_found = list(set(best_sources))
            aggregated_data[field_name] = best_value or ''
        
        return aggregated_data
    
    def _extract_field_value(self, search_result: Dict[str, Any], field_name: str) -> Optional[str]:
        """Extrahiere Feldwert aus Suchergebnis"""
        # Implementierung der Feldextraktion
        data = search_result.get('data', {})
        structured_data = data.get('structured_data', {})
        
        return structured_data.get(field_name)
    
    def _extract_quebec_field_value(self, quebec_data: Dict[str, Any], field_name: str) -> Optional[str]:
        """Extrahiere Feldwert aus Quebec-Daten"""
        gestim_data = quebec_data.get('gestim_data', {})
        registry_data = quebec_data.get('registry_data', {})
        
        # Mapping deutscher Feldnamen zu Quebec-Datenfeldern
        field_mapping = {
            'Eigentümer': 'owner',
            'Betreiber': 'operator',
            'Restaurationskosten': 'restoration_costs',
            'x-Koordinate': lambda d: str(d.get('coordinates', {}).get('latitude', '')),
            'y-Koordinate': lambda d: str(d.get('coordinates', {}).get('longitude', '')),
            'Aktivitätsstatus': 'status',
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'commodity',
            'Minentyp (Untertage/ Open-Pit/ usw.)': 'mine_type',
            'Produktionsstart': 'production_start',
            'Produktionsende': 'production_end',
            'Fördermenge/Jahr': 'annual_production',
            'Fläche der Mine in qkm': 'area'
        }
        
        field_key = field_mapping.get(field_name)
        if not field_key:
            return None
        
        # Funktions-basierte Extraktion
        if callable(field_key):
            return field_key(gestim_data)
        
        # Standard Feldextraktion
        return gestim_data.get(field_key) or registry_data.get(field_key)
    
    def _validate_field_completion(self, field_status: Dict[str, FieldCompletionStatus]) -> Dict[str, Any]:
        """Validiere Vollständigkeit der Feldbearbeitung"""
        completion_report = {
            'total_fields': len(self.critical_fields),
            'completed_fields': 0,
            'successful_fields': 0,
            'incomplete_fields': [],
            'completion_rate': 0.0
        }
        
        for field_name, status in field_status.items():
            is_complete = (
                status.attempts >= self.completion_criteria['min_models_tried'] or
                status.success
            )
            
            if is_complete:
                completion_report['completed_fields'] += 1
            else:
                completion_report['incomplete_fields'].append({
                    'field': field_name,
                    'attempts': status.attempts,
                    'models_tried': len(status.models_tried)
                })
            
            if status.success:
                completion_report['successful_fields'] += 1
        
        completion_report['completion_rate'] = (
            completion_report['completed_fields'] / completion_report['total_fields']
        )
        
        return completion_report
    
    def _evaluate_source_quality(self) -> Dict[str, Any]:
        """Bewerte Qualität der gefundenen Quellen"""
        return {
            'total_sources_discovered': len(self.discovered_sources),
            'high_quality_sources': len([s for s, score in self.source_quality_scores.items() if score > 0.8]),
            'source_discovery_rate': len(self.discovered_sources) / max(1, len(self.critical_fields)),
            'average_source_quality': sum(self.source_quality_scores.values()) / max(1, len(self.source_quality_scores))
        }

# Singleton-Instanz
comprehensive_search_orchestrator = ComprehensiveSearchOrchestrator()