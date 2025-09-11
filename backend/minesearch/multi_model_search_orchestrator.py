"""
Author: rahn
Datum: 18.08.2025
Version: 1.0
Beschreibung: Multi-Model Search Orchestrator - EINE Mine-Suche mit ALLEN Modellen parallel
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from minesearch.database.normalized_manager import NormalizedDatabaseManager
from minesearch.utils import generate_name_variants, get_country_config
from minesearch.config import config
from minesearch.source_validation import source_validator

logger = logging.getLogger(__name__)


@dataclass
class ModelSearchResult:
    """Individual result for one model"""
    model_id: str
    success: bool
    data: Dict[str, Any]
    sources: List[Dict[str, Any]]
    error: Optional[str] = None
    search_duration: float = 0.0


@dataclass  
class OrchestrationResult:
    """Combined result from all models"""
    mine_name: str
    country: Optional[str]
    region: Optional[str]
    commodity: Optional[str]
    models_used: List[str]
    successful_models: List[ModelSearchResult]
    failed_models: List[ModelSearchResult]
    shared_sources: List[Dict[str, Any]]
    total_search_duration: float
    orchestration_metadata: Dict[str, Any]


class MultiModelSearchOrchestrator:
    """
    CRITICAL ARCHITECTURE FIX: Orchestriert Suchen mit mehreren Modellen effizient
    
    Statt 55 separate Suchen macht es:
    1. EINE Source Discovery
    2. Parallele Modell-Execution mit shared sources  
    3. Individual database saves
    """
    
    def __init__(self):
        self.source_discovery = EnhancedSourceDiscovery()
        self.normalized_db_manager = NormalizedDatabaseManager()
        # Initialize provider registry (threadsicher/idempotent)
        logger.info(f"[ORCHESTRATOR-INIT] Provider Registry Status: {len(provider_registry._providers)} Provider geladen")
        if not provider_registry._providers:
            logger.info("[ORCHESTRATOR-INIT] Provider Registry wird initialisiert (idempotent)...")
        else:
            logger.info("[ORCHESTRATOR-INIT] Registry bereits gefüllt – führe idempotente Initialisierung aus (wird ggf. übersprungen)")
        provider_registry.initialize(config.PROVIDERS)
    
    def _validate_provider_response(self, search_result, model_id: str) -> Dict[str, Any]:
        """
        PROVIDER-RESPONSE-VALIDIERUNG: Prüft und loggt Provider-Antworten detailliert
        
        Args:
            search_result: Provider search result
            model_id: Model identifier
            
        Returns:
            Validation report with detailed analysis
        """
        validation_report = {
            'model_id': model_id,
            'is_valid': False,
            'has_content': False,
            'has_structured_data': False,
            'field_count': 0,
            'filled_field_count': 0,
            'empty_fields': [],
            'sample_fields': {},
            'content_length': 0,
            'issues': []
        }
        
        try:
            # BASIC RESPONSE VALIDATION
            if not search_result:
                validation_report['issues'].append("Provider returned None/empty result")
                logger.error(f"[VALIDATION-ERROR] {model_id}: Provider returned None/empty result")
                return validation_report
            
            if not hasattr(search_result, 'success'):
                validation_report['issues'].append("Missing 'success' attribute")
                logger.error(f"[VALIDATION-ERROR] {model_id}: Missing 'success' attribute")
                return validation_report
            
            if not search_result.success:
                error_msg = getattr(search_result, 'error', 'Unknown error')
                validation_report['issues'].append(f"Provider search failed: {error_msg}")
                logger.error(f"[VALIDATION-ERROR] {model_id}: Provider search failed: {error_msg}")
                return validation_report
            
            # CONTENT VALIDATION
            content = getattr(search_result, 'content', '')
            validation_report['content_length'] = len(content) if content else 0
            validation_report['has_content'] = validation_report['content_length'] > 0
            
            if not validation_report['has_content']:
                validation_report['issues'].append("No content in response")
                logger.warning(f"[VALIDATION-WARNING] {model_id}: No content in response")
            else:
                logger.info(f"[VALIDATION-CONTENT] {model_id}: Content length {validation_report['content_length']} chars")
            
            # STRUCTURED_DATA VALIDATION
            structured_data = getattr(search_result, 'structured_data', None)
            if structured_data and isinstance(structured_data, dict):
                validation_report['has_structured_data'] = True
                validation_report['field_count'] = len(structured_data)
                
                # Analyze field content
                for field, value in structured_data.items():
                    if value and str(value).strip() and str(value).strip() not in ['nichts gefunden', '', 'None', 'null', '-']:
                        validation_report['filled_field_count'] += 1
                        # Sample first 3 filled fields for logging
                        if len(validation_report['sample_fields']) < 3:
                            validation_report['sample_fields'][field] = str(value)[:100]
                    else:
                        validation_report['empty_fields'].append(field)
                
                logger.info(f"[VALIDATION-STRUCTURED] {model_id}: {validation_report['filled_field_count']}/{validation_report['field_count']} fields with data")
                
                # Log sample fields
                for field, value in validation_report['sample_fields'].items():
                    logger.info(f"[VALIDATION-SAMPLE] {model_id} - {field}: '{value}'")
                
            else:
                validation_report['issues'].append("No structured_data or invalid format")
                logger.error(f"[VALIDATION-ERROR] {model_id}: No structured_data or invalid format")
            
            # OVERALL VALIDATION
            validation_report['is_valid'] = (
                validation_report['has_content'] or 
                validation_report['filled_field_count'] > 0
            )
            
            if validation_report['is_valid']:
                logger.info(f"[VALIDATION-SUCCESS] {model_id}: Response is valid with {validation_report['filled_field_count']} data fields")
            else:
                validation_report['issues'].append("No useful data found")
                logger.error(f"[VALIDATION-FAIL] {model_id}: Response validation failed - no useful data")
            
        except Exception as e:
            validation_report['issues'].append(f"Validation exception: {str(e)}")
            logger.error(f"[VALIDATION-EXCEPTION] {model_id}: {str(e)}")
        
        return validation_report
        
    async def orchestrate_multi_model_search(
        self,
        mine_name: str,
        models: List[str],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None,
        session_id: Optional[str] = None,
        max_concurrent_models: int = 10,
        # 2-PHASEN WORKFLOW PARAMETER (29.08.2025)
        use_all_db_sources: bool = False,
        db_sources: Optional[List[Dict[str, Any]]] = None
    ) -> OrchestrationResult:
        """
        Hauptfunktion: Sucht eine Mine mit allen angegebenen Modellen
        
        Args:
            mine_name: Name der Mine
            models: Liste der zu verwendenden Modell-IDs
            country: Land (optional)
            region: Region (optional) 
            commodity: Rohstoff (optional)
            session_id: Session ID für tracking
            max_concurrent_models: Max parallele Modell-Calls
            use_all_db_sources: True = Nutze alle DB-Quellen (2-Phasen Workflow)
            db_sources: Liste aller DB-Quellen für Phase 2 
            
        Returns:
            OrchestrationResult mit allen Modell-Ergebnissen
        """
        orchestration_start = datetime.now()
        
        # SESSION-ID FIX 04.09.2025: Generiere UUID falls keine session_id übergeben
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"[ORCHESTRATOR] Generierte neue session_id: {session_id} für Mine {mine_name}")
        
        logger.info(f"[ORCHESTRATOR] Starte Multi-Model-Suche für '{mine_name}' mit {len(models)} Modellen (session_id: {session_id})")
        
        # PROVIDER-VERFÜGBARKEITS-CHECK 24.08.2025
        available_models = []
        unavailable_models = []
        
        for model_id in models:
            provider = provider_registry.get_provider_for_model(model_id)
            if provider:
                available_models.append(model_id)
            else:
                unavailable_models.append(model_id)
        
        logger.info(f"[ORCHESTRATOR] 📊 MODEL-VERFÜGBARKEIT:")
        logger.info(f"[ORCHESTRATOR] ✅ Verfügbare Modelle: {len(available_models)}/{len(models)}")
        logger.info(f"[ORCHESTRATOR] ❌ Nicht verfügbare Modelle: {len(unavailable_models)}")
        
        if unavailable_models:
            logger.warning(f"[ORCHESTRATOR] 🚫 Folgende Modelle haben keine Provider/API-Keys:")
            for model in unavailable_models[:10]:  # Erste 10 anzeigen
                logger.warning(f"[ORCHESTRATOR]    • {model}")
            if len(unavailable_models) > 10:
                logger.warning(f"[ORCHESTRATOR]    • ... und {len(unavailable_models) - 10} weitere")
            
            # FALLBACK-FIX 29.08.2025: Verwende nur verfügbare Modelle für Ausführung
            logger.info(f"[ORCHESTRATOR] 🛠️ FALLBACK: Verwende nur {len(available_models)} verfügbare Modelle")
            models = available_models
        
        # PHASE 1: SOURCE DISCOVERY - 2-Phasen Workflow berücksichtigen
        if use_all_db_sources and db_sources:
            # 2-PHASEN WORKFLOW: Nutze vorgesammelte DB-Quellen
            logger.info(f"[ORCHESTRATOR] 🔥 2-PHASEN WORKFLOW: Nutze {len(db_sources)} vorgesammelte DB-Quellen")
            shared_sources = db_sources
            discovery_duration = 0.0  # Bereits in Phase 1 gemacht
            
            logger.info(f"[ORCHESTRATOR] ✅ DB-Quellen-Übersicht:")
            domain_count = {}
            for source in db_sources[:10]:  # Erste 10 für Übersicht
                domain = source.get('domain', 'unknown')
                domain_count[domain] = domain_count.get(domain, 0) + 1
                logger.info(f"[ORCHESTRATOR]   📄 {source.get('title', 'Unknown Title')[:50]}... ({domain})")
                
            logger.info(f"[ORCHESTRATOR] Top Domains: {dict(sorted(domain_count.items(), key=lambda x: x[1], reverse=True)[:5])}")
            
        else:
            # LEGACY WORKFLOW: Individuelle Source Discovery
            logger.info(f"[ORCHESTRATOR] Phase 1: Legacy Source Discovery für {mine_name}")
            discovery_start = datetime.now()
            
            try:
                shared_sources = self.source_discovery.discover_sources_for_mine(
                    mine_name=mine_name,
                    country=country,
                    region=region,
                    commodity=commodity
                )
                discovery_duration = (datetime.now() - discovery_start).total_seconds()
                logger.info(f"[ORCHESTRATOR] Source Discovery completed: {len(shared_sources)} sources in {discovery_duration:.2f}s")
                
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Source Discovery failed: {e}")
                shared_sources = []
                discovery_duration = 0.0
        
        # PHASE 2: PARALLEL MODEL EXECUTION
        logger.info(f"[ORCHESTRATOR] Phase 2: Parallele Modell-Execution")
        
        # Gruppiere Modelle in Batches für Parallelität
        model_batches = [models[i:i+max_concurrent_models] for i in range(0, len(models), max_concurrent_models)]
        
        all_model_results: List[ModelSearchResult] = []
        
        for batch_idx, model_batch in enumerate(model_batches):
            logger.info(f"[ORCHESTRATOR] Processing batch {batch_idx+1}/{len(model_batches)} with {len(model_batch)} models")
            
            # Führe Batch parallel aus
            batch_tasks = [
                self._execute_single_model_search(
                    mine_name=mine_name,
                    model_id=model_id,
                    shared_sources=shared_sources,
                    country=country,
                    region=region,
                    commodity=commodity
                )
                for model_id in model_batch
            ]
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for model_id, result in zip(model_batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"[ORCHESTRATOR] Model {model_id} failed with exception: {result}")
                        all_model_results.append(ModelSearchResult(
                            model_id=model_id,
                            success=False,
                            data={},
                            sources=[],
                            error=str(result)
                        ))
                    else:
                        all_model_results.append(result)
                        
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Batch {batch_idx+1} failed: {e}")
                # Add failed results for this batch
                for model_id in model_batch:
                    all_model_results.append(ModelSearchResult(
                        model_id=model_id,
                        success=False,
                        data={},
                        sources=[],
                        error=f"Batch execution failed: {str(e)}"
                    ))
        
        # PHASE 3: INDIVIDUAL DATABASE SAVES & STATISTICS UPDATES
        logger.info(f"[ORCHESTRATOR] Phase 3: Individual Database Saves")
        
        successful_results = [r for r in all_model_results if r.success]
        failed_results = [r for r in all_model_results if not r.success]
        
        # Save individual results to database
        saved_count = 0
        for result in successful_results:
            try:
                # CRITICAL-FIX 19.08.2025: Validiere structured_data vor Database-Save
                structured_data = result.data.get('structured_data', {})
                
                # ENHANCED DATABASE-SAVE LOGGING
                logger.info(f"[ORCHESTRATOR-DB-START] Starting database save for {result.model_id}")
                
                if structured_data:
                    data_fields = len(structured_data)
                    filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() != 'nichts gefunden'])
                    logger.info(f"[ORCHESTRATOR-DB-FIELDS] Saving {result.model_id}: {filled_fields}/{data_fields} fields with data")
                    
                    # LOG SAMPLE FIELDS vor Database-Save
                    sample_fields = ['Country', 'Region', 'Rohstoff']
                    for field in sample_fields:
                        if field in structured_data:
                            value = structured_data[field]
                            logger.info(f"[ORCHESTRATOR-DB-SAMPLE] {result.model_id} saving {field}: '{value}'")
                else:
                    logger.error(f"[ORCHESTRATOR-DB-ERROR] Model {result.model_id} has EMPTY structured_data - cannot save!")
                
                # ATOMIC SAVE: Beide Saves (Legacy + Normalized) in einer Transaktion
                from minesearch.database import db_manager as legacy_db_manager
                with legacy_db_manager.get_session() as tx_session:
                    try:
                        # Legacy speichern (ohne eigenen Commit)
                        # LEGACY DATABASE REMOVED 03.09.2025: Nur noch normalisierte DB
                        # Speicherung erfolgt automatisch in MineSearchService
                        
                        # Normalized speichern (gleiche Transaktion/Session)
                        normalized_result_id = self.normalized_db_manager.save_search_result_normalized(
                            mine_name=mine_name,
                            model_used=result.model_id,
                            structured_data=structured_data,
                            sources=result.sources,
                            session_id=session_id,
                            country=country,
                            search_duration=result.search_duration,
                            db_session=tx_session
                        )
                        
                        # Expliziter Commit nachdem beide erfolgreich sind
                        tx_session.commit()
                        logger.info(f"[ORCHESTRATOR-DB-SUCCESS] ✅ Atomic save committed for {result.model_id} (normalized_id={normalized_result_id})")
                        logger.info(f"[ORCHESTRATOR-STATS] Statistics auto-updated via save_search_result for {result.model_id}")
                    except Exception as atomic_err:
                        # Rollback bei irgendeinem Fehler
                        try:
                            tx_session.rollback()
                        except Exception:
                            pass
                        logger.error(f"[ORCHESTRATOR-ATOMIC] ❌ Atomic save failed for {result.model_id}: {atomic_err}")
                        raise
                
                saved_count += 1
                logger.info(f"[ORCHESTRATOR-DB-COUNT] Successfully saved {saved_count} results so far")
                
            except Exception as db_error:
                logger.error(f"[ORCHESTRATOR] Database save failed for {result.model_id}: {db_error}")
                # Continue with saving other results even if one fails
        
        # PHASE 3 COMPLETION: Run database consistency verification
        logger.info("[ORCHESTRATOR] Running database consistency verification after Phase 3...")
        consistency_report = self._verify_database_consistency(mine_name, session_id)
        consistency_summary = f"DB entries: {consistency_report['db_entries_found']}, " \
                            f"with data: {consistency_report['models_with_data']}, " \
                            f"empty: {consistency_report['empty_results']}"
        logger.info(f"[ORCHESTRATOR-CONSISTENCY] {consistency_summary}")
        
        if consistency_report['issues']:
            logger.warning(f"[ORCHESTRATOR-CONSISTENCY] Issues found: {', '.join(consistency_report['issues'])}")
        
        total_duration = (datetime.now() - orchestration_start).total_seconds()
        
        # Create orchestration result
        orchestration_result = OrchestrationResult(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            models_used=models,
            successful_models=successful_results,
            failed_models=failed_results,
            shared_sources=shared_sources,
            total_search_duration=total_duration,
            orchestration_metadata={
                'source_discovery_duration': discovery_duration,
                'total_models_processed': len(all_model_results),
                'successful_models': len(successful_results),
                'failed_models': len(failed_results),
                'database_saves': saved_count,
                'sources_discovered': len(shared_sources),
                'batches_processed': len(model_batches),
                'orchestration_version': '1.0',
                'database_consistency': consistency_report
            }
        )
        
        logger.info(f"[ORCHESTRATOR] Orchestration completed: {len(successful_results)}/{len(models)} models successful in {total_duration:.2f}s")
        
        return orchestration_result
    
    async def _execute_single_model_search(
        self,
        mine_name: str,
        model_id: str,
        shared_sources: List[Dict[str, Any]],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None
    ) -> ModelSearchResult:
        """
        Führt Suche für ein einzelnes Modell mit shared sources aus
        """
        search_start = datetime.now()
        
        try:
            logger.debug(f"[ORCHESTRATOR] Executing search for {mine_name} with model {model_id}")
            
            # Get provider for this model
            provider = provider_registry.get_provider_for_model(model_id)
            if not provider:
                raise ValueError(f"No provider found for model {model_id}")
            
            # Extract model name (remove provider prefix)
            model_name = model_id.split(':')[1] if ':' in model_id else model_id
            
            # Build search query
            name_variants = generate_name_variants(mine_name)
            country_config = get_country_config(country) if country else {}
            
            query = self._build_enhanced_query(
                mine_name=mine_name,
                name_variants=name_variants,
                country=country,
                commodity=commodity,
                region=region,
                country_config=country_config
            )
            
            # Search options with shared sources - 2-PHASEN WORKFLOW UNTERSTÜTZUNG
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region,
                'discovered_sources': shared_sources,  # CRITICAL: Pass shared sources
                'skip_source_discovery': True,  # Skip individual discovery
                'use_all_sources': True,  # 2-PHASEN WORKFLOW: Nutze ALLE Quellen ohne Filter
                'name_variants': name_variants,
                'currency': country_config.get('currency', 'USD'),
                'multilingual_terms': country_config.get('multilingual_terms', [])
            }
            
            # Execute provider search with enhanced error handling
            # PROVIDER-ERROR-FIX 29.08.2025: Spezifische Behandlung für API-Limits und 404-Fehler
            search_result = await provider.search(query, model_name, options)
            
            search_duration = (datetime.now() - search_start).total_seconds()
            
            # API-ERROR-CHECK 29.08.2025: Prüfe auf spezifische Provider-Fehler
            if hasattr(search_result, 'error') and search_result.error:
                error_msg = str(search_result.error).lower()
                
                # Kategorisiere Fehler für besseres Logging
                if 'pay-as-you-go limit' in error_msg or 'quota' in error_msg or 'budget' in error_msg:
                    logger.warning(f"[ORCHESTRATOR-API-LIMIT] {model_id}: API-Limit erreicht - {search_result.error}")
                elif '404' in error_msg or 'not found' in error_msg:
                    logger.warning(f"[ORCHESTRATOR-API-404] {model_id}: API-Endpoint nicht erreichbar - {search_result.error}")
                elif 'unauthorized' in error_msg or '401' in error_msg or 'invalid key' in error_msg:
                    logger.warning(f"[ORCHESTRATOR-API-AUTH] {model_id}: Authentifizierung fehlgeschlagen - {search_result.error}")
                else:
                    logger.error(f"[ORCHESTRATOR-API-ERROR] {model_id}: Unbekannter API-Fehler - {search_result.error}")
                
                # Erstelle aussagekräftige Fehlermeldung für Frontend  
                friendly_error = self._create_friendly_error_message(str(search_result.error), model_id)
                
                return ModelSearchResult(
                    model_id=model_id,
                    success=False,
                    data={},
                    sources=[],
                    error=friendly_error,
                    search_duration=search_duration
                )
            
            # PROVIDER-RESPONSE-VALIDIERUNG
            validation_report = self._validate_provider_response(search_result, model_id)
            logger.info(f"[ORCHESTRATOR-VALIDATION] {model_id} validation complete: valid={validation_report['is_valid']}")
            
            if search_result.success:
                # CRITICAL-FIX 19.08.2025: Sichere dass structured_data korrekt extrahiert wird
                structured_data = search_result.structured_data or {}
                
                # ENHANCED DEBUG-LOGGING für vollständige Nachverfolgung
                logger.info(f"[ORCHESTRATOR-SUCCESS] Model {model_id} search successful")
                logger.info(f"[ORCHESTRATOR-DATA] Model {model_id} extracted {len(structured_data)} total fields")
                
                if structured_data:
                    filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() != 'nichts gefunden'])
                    logger.info(f"[ORCHESTRATOR-FILLED] Model {model_id} found data in {filled_fields}/{len(structured_data)} fields")
                    
                    # DETAILED FIELD-BY-FIELD LOGGING für kritische Felder
                    critical_fields = ['Country', 'Region', 'Rohstoff', 'Restaurationskosten', 'Eigentümer']
                    for field in critical_fields:
                        if field in structured_data:
                            value = structured_data[field]
                            logger.info(f"[ORCHESTRATOR-FIELD] Model {model_id} - {field}: '{value}'")
                        else:
                            logger.warning(f"[ORCHESTRATOR-MISSING] Model {model_id} - Field '{field}' not found in structured_data")
                    
                    # LOG RAW CONTENT LENGTH für weitere Analyse
                    raw_content_length = len(search_result.content) if search_result.content else 0
                    logger.info(f"[ORCHESTRATOR-RAW] Model {model_id} raw content length: {raw_content_length} chars")
                else:
                    logger.error(f"[ORCHESTRATOR-EMPTY] Model {model_id} returned EMPTY structured_data!")
                
                # QUELLENVALIDIERUNG: Prüfe ob Provider discovered_sources korrekt verwendet
                provider_name = search_result.metadata.get('provider', 'unknown') if hasattr(search_result, 'metadata') and search_result.metadata else 'unknown'
                
                # Erstelle Options für Validierung
                validation_options = {
                    'mine_name': mine_name,
                    'country': country,
                    'region': region,
                    'commodity': commodity
                }
                
                validation_result = source_validator.validate_search_result(
                    search_result=search_result,
                    provider_name=provider_name,
                    model_id=model_id,
                    discovered_sources=shared_sources,
                    options=validation_options
                )
                
                if not validation_result.valid:
                    logger.warning(f"[SOURCE-VALIDATION] {model_id} hat Quellenprobleme: {validation_result.issues}")
                
                return ModelSearchResult(
                    model_id=model_id,
                    success=True,
                    data={
                        'structured_data': structured_data,  # Ensure this is not empty
                        'raw_content': search_result.content,
                        'search_duration': search_duration,
                        'source_validation': {  # Füge Validierungsergebnisse hinzu
                            'valid': validation_result.valid,
                            'issues': validation_result.issues,
                            'discovered_count': validation_result.discovered_sources_count,
                            'result_count': validation_result.result_sources_count
                        }
                    },
                    sources=shared_sources,  # Use shared sources
                    search_duration=search_duration
                )
            else:
                return ModelSearchResult(
                    model_id=model_id,
                    success=False,
                    data={},
                    sources=[],
                    error=search_result.error or "Unknown search failure",
                    search_duration=search_duration
                )
                
        except Exception as e:
            search_duration = (datetime.now() - search_start).total_seconds()
            logger.error(f"[ORCHESTRATOR] Model {model_id} execution failed: {e}")
            return ModelSearchResult(
                model_id=model_id,
                success=False,
                data={},
                sources=[],
                error=str(e),
                search_duration=search_duration
            )
    
    def _build_enhanced_query(
        self,
        mine_name: str,
        name_variants: List[str],
        country: Optional[str] = None,
        commodity: Optional[str] = None,
        region: Optional[str] = None,
        country_config: Dict[str, Any] = None
    ) -> str:
        """Builds enhanced search query for multi-model context"""
        
        # Base query with mine focus
        query_parts = [
            f"Mining information for: {mine_name}",
        ]
        
        # Add variants
        if name_variants and len(name_variants) > 1:
            query_parts.append(f"Also known as: {', '.join(name_variants[1:3])}")  # Top 2 variants
        
        # Geographic context
        if country:
            query_parts.append(f"Location: {region}, {country}" if region else f"Location: {country}")
        
        # Commodity context
        if commodity:
            query_parts.append(f"Primary commodity: {commodity}")
        
        # Currency context for costs
        currency = country_config.get('currency', 'USD') if country_config else 'USD'
        query_parts.append(f"Please provide all costs in {currency}")
        
        return "\n".join(query_parts)
    
    def _verify_database_consistency(self, mine_name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        DATABASE-KONSISTENZ-PRÜFUNG: Verifiziert dass gespeicherte Daten korrekt in DB stehen
        
        Args:
            mine_name: Name der Mine
            session_id: Session ID für Filterung
            
        Returns:
            Consistency report
        """
        consistency_report = {
            'mine_name': mine_name,
            'session_id': session_id,
            'db_entries_found': 0,
            'models_with_data': 0,
            'empty_results': 0,
            'sample_data': {},
            'issues': []
        }
        
        try:
            from minesearch.database import db_manager
            
            # Hole alle DB-Einträge für diese Mine/Session
            with db_manager.get_session() as db_session:
                from minesearch.database.models import SearchResult
                
                query = db_session.query(SearchResult).filter(SearchResult.mine_name == mine_name)
                if session_id:
                    query = query.filter(SearchResult.session_id == session_id)
                
                db_results = query.all()
                consistency_report['db_entries_found'] = len(db_results)
                
                logger.info(f"[DB-CONSISTENCY] Found {len(db_results)} database entries for {mine_name}")
                
                for db_result in db_results:
                    structured_data = db_result.structured_data or {}
                    
                    if structured_data:
                        filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() != 'nichts gefunden'])
                        if filled_fields > 0:
                            consistency_report['models_with_data'] += 1
                            # Sample first model with data
                            if not consistency_report['sample_data']:
                                consistency_report['sample_data'] = {
                                    'model': db_result.model_used,
                                    'fields': filled_fields,
                                    'sample_fields': {k: v for k, v in list(structured_data.items())[:3]}
                                }
                        else:
                            consistency_report['empty_results'] += 1
                            logger.warning(f"[DB-CONSISTENCY] Model {db_result.model_used} has empty structured_data in DB")
                    else:
                        consistency_report['empty_results'] += 1
                        consistency_report['issues'].append(f"Model {db_result.model_used} has NULL structured_data")
                        logger.error(f"[DB-CONSISTENCY] Model {db_result.model_used} has NULL structured_data in DB")
                
                logger.info(f"[DB-CONSISTENCY] Summary - Data: {consistency_report['models_with_data']}, Empty: {consistency_report['empty_results']}")
                
        except Exception as e:
            consistency_report['issues'].append(f"Database consistency check failed: {str(e)}")
            logger.error(f"[DB-CONSISTENCY-ERROR] {str(e)}")
        
        return consistency_report
    
    def _create_friendly_error_message(self, error: str, model_id: str) -> str:
        """
        ERROR-HANDLING FIX 29.08.2025: Erstelle benutzerfreundliche Fehlermeldungen
        für verschiedene Provider-Fehler-Szenarien
        """
        error_lower = error.lower()
        
        # API-Limit/Quota-Fehler
        if any(phrase in error_lower for phrase in ["pay-as-you-go limit", "quota", "rate limit", "limit exceeded"]):
            return f"💰 {model_id}: Budget-Limit erreicht - Erhöhen Sie Ihr Limit im Provider-Dashboard"
        
        # 404-Fehler (meist ungültige API-Keys oder falsche Endpoints)
        elif "404" in error_lower:
            # Standard 404-Fehlerbehandlung für alle Provider
            return f"❌ {model_id}: Provider nicht erreichbar - möglicherweise fehlt API-Key oder falscher Endpoint"
        
        # Authentifizierungs-Fehler
        elif any(phrase in error_lower for phrase in ["401", "unauthorized", "invalid key", "authentication"]):
            return f"🔑 {model_id}: Authentifizierung fehlgeschlagen - API-Key prüfen"
        
        # Timeout-Fehler
        elif any(phrase in error_lower for phrase in ["timeout", "timed out", "connection timeout"]):
            return f"⏱️ {model_id}: Verbindungs-Timeout - Provider antwortet nicht rechtzeitig"
        
        # JSON-Parsing-Fehler
        elif any(phrase in error_lower for phrase in ["json", "invalid response", "malformed"]):
            return f"📄 {model_id}: Ungültige Antwort - Provider sendet fehlerhaftes Format"
        
        # Generic Fehler
        else:
            return f"❌ {model_id}: {error[:100]}..." if len(error) > 100 else f"❌ {model_id}: {error}"


# Global orchestrator instance
multi_model_orchestrator = MultiModelSearchOrchestrator()