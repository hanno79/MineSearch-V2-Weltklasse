"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Sequential Field Orchestrator - Optimaler Workflow für maximale Datenausbeute
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from minesearch.utils import generate_name_variants, get_country_config
from minesearch.config import config

logger = logging.getLogger(__name__)


@dataclass
class SourceDiscoveryPhaseResult:
    """Ergebnis der sequentiellen Quellensuche Phase"""
    total_sources_found: int
    sources_by_model: Dict[str, List[Dict]]
    unique_sources: List[Dict]
    discovery_duration: float
    model_contributions: Dict[str, int]  # Wie viele neue Quellen jedes Modell beigetragen hat


@dataclass
class FieldSearchResult:
    """Ergebnis einer fokussierten Feld-Suche"""
    field_name: str
    model_id: str
    value_found: Optional[str]
    confidence: Optional[float]
    sources_used: List[str]
    sources_that_had_data: List[str]
    search_duration: float
    success: bool
    error: Optional[str] = None


@dataclass
class FieldCompletionReport:
    """Vollständigkeitsbericht für ein Feld"""
    field_name: str
    total_models_tried: int
    total_sources_searched: int
    successful_searches: int
    best_value: Optional[str]
    best_confidence: Optional[float]
    best_model: Optional[str]
    all_values_found: List[FieldSearchResult]
    completion_score: float  # 0.0 bis 1.0


@dataclass
class SequentialSearchResult:
    """Gesamtergebnis des sequentiellen Workflows"""
    mine_name: str
    country: Optional[str]
    region: Optional[str]
    commodity: Optional[str]
    
    # Phase 1: Source Discovery
    source_discovery_result: SourceDiscoveryPhaseResult
    
    # Phase 2: Field-by-Field Search
    field_results: Dict[str, FieldCompletionReport]
    consolidated_data: Dict[str, Any]
    
    # Overall Statistics
    total_duration: float
    models_used: List[str]
    total_api_calls: int
    success: bool
    completion_rate: float  # Prozent der erfolgreich gefüllten Felder


class SequentialFieldOrchestrator:
    """
    Implementiert den optimalen Workflow:
    1. Sequentielle Quellensuche: Jedes Modell fügt neue Quellen zur DB hinzu
    2. Feld-für-Feld Suche: Jedes Modell durchsucht alle Quellen für jedes Feld
    """
    
    def __init__(self):
        self.registry = provider_registry
        self.source_discovery = EnhancedSourceDiscovery()
        
        # Definiere die zu durchsuchenden Felder in Prioritätsreihenfolge
        self.critical_fields = [
            'Country',
            'Region', 
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
            'Eigentümer',
            'Betreiber',
            'Aktivitätsstatus',
            'x-Koordinate',
            'y-Koordinate',
            'Minentyp (Untertage/ Open-Pit/ usw.)',
            'Produktionsstart',
            'Produktionsende',
            'Fördermenge/Jahr',
            'Restaurationskosten',
            'Fläche der Mine in qkm',
            'Jahr der Erstellung des Dokumentes',
            'Dokumentenjahr',
            'Kostenjahr',
            'Minenfläche in qkm'
        ]
        
        # Konfiguration für sequentielle Suche
        self.config = {
            'max_sources_per_model': 50,  # Maximum neue Quellen pro Modell
            'source_quality_threshold': 0.3,  # Mindest-Qualitätsscore für Quellen
            'field_search_timeout': 30,  # Timeout pro Feld-Suche in Sekunden
            'max_concurrent_field_searches': 3,  # Max parallele Feld-Suchen pro Modell
            'enable_source_ranking': True,  # Quellen nach Qualität sortieren
        }
    
    async def orchestrate_sequential_search(
        self,
        mine_name: str,
        models: List[str],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> SequentialSearchResult:
        """
        Hauptfunktion: Führt den optimalen sequentiellen Workflow durch
        
        Args:
            mine_name: Name der Mine
            models: Liste der zu verwendenden Modelle
            country: Land (optional)
            region: Region (optional)
            commodity: Rohstoff (optional)
            session_id: Session ID für Tracking
            
        Returns:
            SequentialSearchResult mit vollständigen Ergebnissen
        """
        orchestration_start = datetime.now()
        
        logger.info(f"[SEQUENTIAL-ORCHESTRATOR] Starte optimalen Workflow für '{mine_name}' mit {len(models)} Modellen")
        
        try:
            # PHASE 1: SEQUENTIELLE QUELLENSUCHE
            logger.info(f"[SEQUENTIAL-ORCHESTRATOR] Phase 1: Sequentielle Quellensuche")
            source_discovery_result = await self._sequential_source_discovery(
                mine_name=mine_name,
                models=models,
                country=country,
                region=region,
                commodity=commodity
            )
            
            logger.info(f"[SEQUENTIAL-ORCHESTRATOR] Phase 1 abgeschlossen: {source_discovery_result.total_sources_found} Quellen gesammelt")
            
            # PHASE 2: FELD-FÜR-FELD DURCHSUCHUNG
            logger.info(f"[SEQUENTIAL-ORCHESTRATOR] Phase 2: Feld-für-Feld Durchsuchung mit {len(source_discovery_result.unique_sources)} Quellen")
            field_results = await self._field_by_field_search(
                mine_name=mine_name,
                models=models,
                sources=source_discovery_result.unique_sources,
                country=country,
                region=region,
                commodity=commodity
            )
            
            # PHASE 3: DATENKONSOLIDIERUNG
            logger.info(f"[SEQUENTIAL-ORCHESTRATOR] Phase 3: Datenkonsolidierung")
            consolidated_data = self._consolidate_field_results(field_results)
            
            # PHASE 4: ERGEBNISSE FINALISIEREN
            total_duration = (datetime.now() - orchestration_start).total_seconds()
            
            # Berechne Statistiken
            total_api_calls = (
                len(models) +  # Source Discovery Calls
                sum(len(field_report.all_values_found) for field_report in field_results.values())  # Field Search Calls
            )
            
            filled_fields = len([v for v in consolidated_data.values() if v and str(v).strip() and str(v) not in ['None', 'null', '']])
            completion_rate = (filled_fields / len(self.critical_fields)) * 100 if self.critical_fields else 0
            
            result = SequentialSearchResult(
                mine_name=mine_name,
                country=country,
                region=region,
                commodity=commodity,
                source_discovery_result=source_discovery_result,
                field_results=field_results,
                consolidated_data=consolidated_data,
                total_duration=total_duration,
                models_used=models,
                total_api_calls=total_api_calls,
                success=filled_fields > 0,
                completion_rate=completion_rate
            )
            
            logger.info(f"[SEQUENTIAL-ORCHESTRATOR] Workflow erfolgreich abgeschlossen: {completion_rate:.1f}% Felder gefüllt in {total_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"[SEQUENTIAL-ORCHESTRATOR] Kritischer Fehler im Workflow: {str(e)}")
            
            # Erstelle Fehler-Result
            error_duration = (datetime.now() - orchestration_start).total_seconds()
            return SequentialSearchResult(
                mine_name=mine_name,
                country=country,
                region=region,
                commodity=commodity,
                source_discovery_result=SourceDiscoveryPhaseResult(
                    total_sources_found=0,
                    sources_by_model={},
                    unique_sources=[],
                    discovery_duration=0,
                    model_contributions={}
                ),
                field_results={},
                consolidated_data={},
                total_duration=error_duration,
                models_used=models,
                total_api_calls=0,
                success=False,
                completion_rate=0.0
            )
    
    async def _sequential_source_discovery(
        self,
        mine_name: str,
        models: List[str],
        country: Optional[str],
        region: Optional[str],
        commodity: Optional[str]
    ) -> SourceDiscoveryPhaseResult:
        """
        Phase 1: Sequentielle Quellensuche - Jedes Modell trägt neue Quellen bei
        """
        discovery_start = datetime.now()
        
        sources_by_model = {}
        all_unique_sources = []
        model_contributions = {}
        
        logger.info(f"[SOURCE-DISCOVERY-PHASE] Starte sequentielle Quellensuche mit {len(models)} Modellen")
        
        for idx, model_id in enumerate(models, 1):
            logger.info(f"[SOURCE-DISCOVERY-PHASE] Schritt {idx}/{len(models)}: {model_id} sucht nach neuen Quellen")
            
            try:
                # Hole Provider für das Modell
                provider = provider_registry.get_provider_for_model(model_id)
                if not provider:
                    logger.warning(f"[SOURCE-DISCOVERY-PHASE] Kein Provider für {model_id} gefunden, überspringe")
                    sources_by_model[model_id] = []
                    model_contributions[model_id] = 0
                    continue
                
                # Führe Enhanced Source Discovery durch
                model_sources = self.source_discovery.discover_sources_for_mine(
                    mine_name=mine_name,
                    country=country,
                    region=region,
                    commodity=commodity,
                    priority_focus=f"model_{idx}_discovery"
                )
                
                # Filtere neue Quellen (die noch nicht in all_unique_sources sind)
                new_sources = []
                existing_urls = {s.get('url') for s in all_unique_sources}
                
                for source in model_sources:
                    source_url = source.get('url')
                    if source_url and source_url not in existing_urls:
                        new_sources.append(source)
                        existing_urls.add(source_url)
                
                sources_by_model[model_id] = new_sources
                model_contributions[model_id] = len(new_sources)
                all_unique_sources.extend(new_sources)
                
                logger.info(f"[SOURCE-DISCOVERY-PHASE] {model_id} fand {len(model_sources)} Quellen, {len(new_sources)} davon neu")
                
                # Aktualisiere Quellendatenbank mit neuen Quellen
                await self._update_source_database(new_sources, model_id, mine_name)
                
            except Exception as e:
                logger.error(f"[SOURCE-DISCOVERY-PHASE] Fehler bei {model_id}: {str(e)}")
                sources_by_model[model_id] = []
                model_contributions[model_id] = 0
        
        discovery_duration = (datetime.now() - discovery_start).total_seconds()
        
        # Zusammenfassung der Source Discovery Phase
        total_sources = len(all_unique_sources)
        logger.info(f"[SOURCE-DISCOVERY-PHASE] Abgeschlossen: {total_sources} einzigartige Quellen in {discovery_duration:.2f}s")
        
        # Logge Beiträge pro Modell
        for model_id, contribution in model_contributions.items():
            logger.info(f"[SOURCE-DISCOVERY-PHASE] {model_id}: +{contribution} neue Quellen")
        
        return SourceDiscoveryPhaseResult(
            total_sources_found=total_sources,
            sources_by_model=sources_by_model,
            unique_sources=all_unique_sources,
            discovery_duration=discovery_duration,
            model_contributions=model_contributions
        )
    
    async def _field_by_field_search(
        self,
        mine_name: str,
        models: List[str],
        sources: List[Dict],
        country: Optional[str],
        region: Optional[str],
        commodity: Optional[str]
    ) -> Dict[str, FieldCompletionReport]:
        """
        Phase 2: Feld-für-Feld Durchsuchung - Jedes Modell durchsucht alle Quellen für jedes Feld
        """
        field_results = {}
        
        logger.info(f"[FIELD-BY-FIELD-PHASE] Durchsuche {len(self.critical_fields)} Felder mit {len(models)} Modellen und {len(sources)} Quellen")
        
        for field_idx, field_name in enumerate(self.critical_fields, 1):
            logger.info(f"[FIELD-BY-FIELD-PHASE] Feld {field_idx}/{len(self.critical_fields)}: {field_name}")
            
            field_search_results = []
            
            # Jedes Modell durchsucht alle Quellen für dieses eine Feld
            for model_idx, model_id in enumerate(models, 1):
                logger.info(f"[FIELD-BY-FIELD-PHASE] Feld '{field_name}' mit {model_id} ({model_idx}/{len(models)})")
                
                try:
                    field_result = await self._search_single_field_with_all_sources(
                        field_name=field_name,
                        model_id=model_id,
                        sources=sources,
                        mine_name=mine_name,
                        country=country,
                        region=region,
                        commodity=commodity
                    )
                    
                    field_search_results.append(field_result)
                    
                    if field_result.success and field_result.value_found:
                        logger.info(f"[FIELD-BY-FIELD-PHASE] ✅ {model_id} fand für '{field_name}': '{field_result.value_found}' (Confidence: {field_result.confidence})")
                    else:
                        logger.info(f"[FIELD-BY-FIELD-PHASE] ❌ {model_id} fand nichts für '{field_name}'")
                
                except Exception as e:
                    logger.error(f"[FIELD-BY-FIELD-PHASE] Fehler bei {model_id} für Feld '{field_name}': {str(e)}")
                    
                    field_search_results.append(FieldSearchResult(
                        field_name=field_name,
                        model_id=model_id,
                        value_found=None,
                        confidence=None,
                        sources_used=[],
                        sources_that_had_data=[],
                        search_duration=0,
                        success=False,
                        error=str(e)
                    ))
            
            # Erstelle Field Completion Report
            field_report = self._create_field_completion_report(field_name, field_search_results, len(sources))
            field_results[field_name] = field_report
            
            logger.info(f"[FIELD-BY-FIELD-PHASE] Feld '{field_name}' abgeschlossen: Score {field_report.completion_score:.2f}, Bester Wert: '{field_report.best_value}'")
        
        return field_results
    
    async def _search_single_field_with_all_sources(
        self,
        field_name: str,
        model_id: str,
        sources: List[Dict],
        mine_name: str,
        country: Optional[str],
        region: Optional[str],
        commodity: Optional[str]
    ) -> FieldSearchResult:
        """
        Durchsucht mit einem Modell alle Quellen nach einem spezifischen Feld
        """
        search_start = datetime.now()
        
        try:
            # Hole Provider
            provider = provider_registry.get_provider_for_model(model_id)
            if not provider:
                raise ValueError(f"Kein Provider für {model_id} gefunden")
            
            # Erstelle fokussierte Query für dieses eine Feld
            focused_query = self._build_field_focused_query(
                field_name=field_name,
                mine_name=mine_name,
                country=country,
                commodity=commodity
            )
            
            # Such-Optionen mit allen Quellen
            options = {
                'mine_name': mine_name,
                'country': country,
                'region': region,
                'commodity': commodity,
                'discovered_sources': sources,
                'focus_field': field_name,  # Neuer Parameter für fokussierte Suche
                'search_mode': 'single_field',  # Kennzeichnet dass nur ein Feld gesucht wird
                'skip_source_discovery': True
            }
            
            # Nutze die neue search_single_field Methode wenn verfügbar
            model_name = model_id.split(':')[1] if ':' in model_id else model_id
            
            if hasattr(provider, 'search_single_field'):
                search_result = await provider.search_single_field(
                    field_name=field_name,
                    mine_name=mine_name,
                    model_id=model_name,
                    sources=sources,
                    options=options
                )
            else:
                # Fallback auf normale search mit fokussierter Query
                search_result = await provider.search(focused_query, model_name, options)
            
            search_duration = (datetime.now() - search_start).total_seconds()
            
            # Extrahiere spezifisch das gesuchte Feld aus dem Ergebnis
            if search_result.success and hasattr(search_result, 'structured_data') and search_result.structured_data:
                field_value = search_result.structured_data.get(field_name)
                
                if field_value and str(field_value).strip() and str(field_value) not in ['None', 'null', '', '-']:
                    return FieldSearchResult(
                        field_name=field_name,
                        model_id=model_id,
                        value_found=str(field_value).strip(),
                        confidence=getattr(search_result, 'confidence', None),
                        sources_used=[s.get('url', '') for s in sources[:10]],  # Sample der genutzten Quellen
                        sources_that_had_data=[],  # Wird vom Provider gefüllt wenn implementiert
                        search_duration=search_duration,
                        success=True
                    )
            
            # Kein Wert gefunden
            return FieldSearchResult(
                field_name=field_name,
                model_id=model_id,
                value_found=None,
                confidence=None,
                sources_used=[s.get('url', '') for s in sources[:10]],
                sources_that_had_data=[],
                search_duration=search_duration,
                success=False
            )
        
        except Exception as e:
            search_duration = (datetime.now() - search_start).total_seconds()
            return FieldSearchResult(
                field_name=field_name,
                model_id=model_id,
                value_found=None,
                confidence=None,
                sources_used=[],
                sources_that_had_data=[],
                search_duration=search_duration,
                success=False,
                error=str(e)
            )
    
    def _build_field_focused_query(
        self,
        field_name: str,
        mine_name: str,
        country: Optional[str],
        commodity: Optional[str]
    ) -> str:
        """
        Erstellt eine fokussierte Query die nur nach einem spezifischen Feld sucht
        """
        base_query = f"Suche spezifisch nach '{field_name}' für die Mine '{mine_name}'"
        
        if country:
            base_query += f" in {country}"
        
        if commodity:
            base_query += f" ({commodity} Mine)"
        
        # Feld-spezifische Query-Verbesserungen
        field_enhancements = {
            'Restaurationskosten': "Suche nach Kosten für Restauration, Sanierung, Mine Closure, Decommissioning, Rehabilitation Costs",
            'Eigentümer': "Suche nach Owner, Eigentümer, Company, Corporation, Besitzer",  
            'Betreiber': "Suche nach Operator, Betreiber, Operating Company, Mine Operator",
            'Koordinaten': "Suche nach Latitude, Longitude, GPS, Coordinates, Koordinaten",
            'Aktivitätsstatus': "Suche nach Status, Active, Inactive, Operational, Closed, Under Development",
            'Rohstoffabbau': "Suche nach Mineral, Commodity, Resource, Material, Gold, Copper, etc.",
            'Fördermenge': "Suche nach Production, Output, Annual Production, Förderung, Menge"
        }
        
        for key, enhancement in field_enhancements.items():
            if key.lower() in field_name.lower():
                base_query += f"\n\n{enhancement}"
                break
        
        base_query += f"\n\nGib nur Informationen zu '{field_name}' zurück. Andere Felder sind nicht relevant für diese Suche."
        
        return base_query
    
    def _create_field_completion_report(
        self,
        field_name: str,
        search_results: List[FieldSearchResult],
        total_sources: int
    ) -> FieldCompletionReport:
        """
        Erstellt einen Vollständigkeitsbericht für ein Feld
        """
        successful_searches = [r for r in search_results if r.success and r.value_found]
        
        # Finde das beste Ergebnis (höchste Confidence oder erstes erfolgreiches)
        best_result = None
        best_confidence = 0.0
        
        for result in successful_searches:
            if result.confidence is not None and result.confidence > best_confidence:
                best_result = result
                best_confidence = result.confidence
            elif best_result is None and result.value_found:
                best_result = result
        
        # Berechne Completion Score
        models_tried = len(search_results)
        successful_count = len(successful_searches)
        
        completion_score = 0.0
        if successful_count > 0:
            completion_score += 0.5  # 50% für gefundenen Wert
            completion_score += (successful_count / models_tried) * 0.3  # 30% für Konsistenz über Modelle
            if best_result and best_result.confidence:
                completion_score += best_result.confidence * 0.2  # 20% für Confidence
        
        completion_score = min(completion_score, 1.0)
        
        return FieldCompletionReport(
            field_name=field_name,
            total_models_tried=models_tried,
            total_sources_searched=total_sources,
            successful_searches=successful_count,
            best_value=best_result.value_found if best_result else None,
            best_confidence=best_result.confidence if best_result else None,
            best_model=best_result.model_id if best_result else None,
            all_values_found=search_results,
            completion_score=completion_score
        )
    
    def _consolidate_field_results(
        self,
        field_results: Dict[str, FieldCompletionReport]
    ) -> Dict[str, Any]:
        """
        Konsolidiert alle Feld-Ergebnisse zu finalen Daten
        """
        consolidated = {}
        
        for field_name, field_report in field_results.items():
            if field_report.best_value:
                consolidated[field_name] = field_report.best_value
            else:
                consolidated[field_name] = None
        
        return consolidated
    
    async def _update_source_database(
        self,
        sources: List[Dict],
        model_id: str,
        mine_name: str
    ) -> None:
        """
        Aktualisiert die Quellendatenbank mit neuen Quellen
        """
        try:
            for source in sources:
                # Füge Metadaten hinzu
                source['discovered_by_model'] = model_id
                source['discovered_for_mine'] = mine_name
                source['discovered_at'] = datetime.now().isoformat()
                
            # Speichere in Datenbank (Enhanced Source Discovery macht das automatisch)
            logger.debug(f"[SOURCE-DB-UPDATE] {len(sources)} Quellen für {model_id} aktualisiert")
            
        except Exception as e:
            logger.error(f"[SOURCE-DB-UPDATE] Fehler beim Aktualisieren der Quellendatenbank: {str(e)}")
    
    def get_workflow_statistics(
        self,
        result: SequentialSearchResult
    ) -> Dict[str, Any]:
        """
        Erstellt detaillierte Statistiken über den Workflow-Durchlauf
        """
        stats = {
            'workflow_type': 'sequential_field_orchestrator',
            'mine_name': result.mine_name,
            'total_duration': result.total_duration,
            'completion_rate': result.completion_rate,
            
            # Source Discovery Stats
            'source_discovery': {
                'total_sources_found': result.source_discovery_result.total_sources_found,
                'discovery_duration': result.source_discovery_result.discovery_duration,
                'model_contributions': result.source_discovery_result.model_contributions
            },
            
            # Field Search Stats
            'field_search': {
                'total_fields': len(self.critical_fields),
                'fields_with_data': len([r for r in result.field_results.values() if r.best_value]),
                'average_completion_score': sum(r.completion_score for r in result.field_results.values()) / len(result.field_results) if result.field_results else 0,
                'total_field_searches': sum(len(r.all_values_found) for r in result.field_results.values()),
                'successful_field_searches': sum(r.successful_searches for r in result.field_results.values())
            },
            
            # Model Performance
            'model_performance': {
                model_id: {
                    'sources_contributed': result.source_discovery_result.model_contributions.get(model_id, 0),
                    'successful_field_searches': sum(
                        1 for field_report in result.field_results.values()
                        for search_result in field_report.all_values_found
                        if search_result.model_id == model_id and search_result.success and search_result.value_found
                    ),
                    'total_field_searches': sum(
                        1 for field_report in result.field_results.values()
                        for search_result in field_report.all_values_found
                        if search_result.model_id == model_id
                    )
                }
                for model_id in result.models_used
            }
        }
        
        return stats