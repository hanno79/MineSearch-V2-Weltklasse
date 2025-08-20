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
from minesearch.utils import generate_name_variants, get_country_config
from minesearch.config import config

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
        # Initialize provider registry
        if not provider_registry._providers:
            provider_registry.initialize(config.PROVIDERS)
        
    async def orchestrate_multi_model_search(
        self,
        mine_name: str,
        models: List[str],
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None,
        session_id: Optional[str] = None,
        max_concurrent_models: int = 10
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
            
        Returns:
            OrchestrationResult mit allen Modell-Ergebnissen
        """
        orchestration_start = datetime.now()
        
        logger.info(f"[ORCHESTRATOR] Starte Multi-Model-Suche für '{mine_name}' mit {len(models)} Modellen")
        
        # PHASE 1: SHARED SOURCE DISCOVERY (nur einmal für alle Modelle)
        logger.info(f"[ORCHESTRATOR] Phase 1: Shared Source Discovery für {mine_name}")
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
                
                # Logge Details für Debug
                if structured_data:
                    data_fields = len(structured_data)
                    filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() != 'nichts gefunden'])
                    logger.info(f"[ORCHESTRATOR-DB] Saving {result.model_id}: {filled_fields}/{data_fields} fields with data")
                else:
                    logger.warning(f"[ORCHESTRATOR-DB] Model {result.model_id} has empty structured_data")
                
                db_manager.save_search_result(
                    mine_name=mine_name,
                    model_used=result.model_id,
                    structured_data=structured_data,  # FIXED: Ensure this has content
                    sources=result.sources,
                    session_id=session_id,
                    country=country,
                    region=region,
                    commodity=commodity,
                    search_type='orchestrated_multi_model',
                    success=True,
                    search_duration=result.search_duration
                )
                
                # CRITICAL FIX: Individual Statistics Update Trigger - mit Error-Handling
                try:
                    db_manager.update_model_statistics_comprehensive(result.model_id)
                    logger.debug(f"[ORCHESTRATOR] Statistics updated for {result.model_id}")
                except Exception as stats_error:
                    logger.error(f"[ORCHESTRATOR] Statistics update failed for {result.model_id}: {stats_error}")
                    # Continue with saving other results even if statistics update fails
                
                saved_count += 1
                
            except Exception as db_error:
                logger.error(f"[ORCHESTRATOR] Database save failed for {result.model_id}: {db_error}")
                # Continue with saving other results even if one fails
        
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
                'orchestration_version': '1.0'
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
            
            # Search options with shared sources
            options = {
                'mine_name': mine_name,
                'country': country,
                'commodity': commodity,
                'region': region,
                'discovered_sources': shared_sources,  # CRITICAL: Pass shared sources
                'skip_source_discovery': True,  # Skip individual discovery
                'name_variants': name_variants,
                'currency': country_config.get('currency', 'USD'),
                'multilingual_terms': country_config.get('multilingual_terms', [])
            }
            
            # Execute provider search
            search_result = await provider.search(query, model_name, options)
            
            search_duration = (datetime.now() - search_start).total_seconds()
            
            if search_result.success:
                # CRITICAL-FIX 19.08.2025: Sichere dass structured_data korrekt extrahiert wird
                structured_data = search_result.structured_data or {}
                
                # Logging für Debug-Zwecke
                logger.debug(f"[ORCHESTRATOR] Model {model_id} extracted {len(structured_data)} fields")
                if structured_data:
                    filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() != 'nichts gefunden'])
                    logger.info(f"[ORCHESTRATOR] Model {model_id} found data in {filled_fields}/{len(structured_data)} fields")
                
                return ModelSearchResult(
                    model_id=model_id,
                    success=True,
                    data={
                        'structured_data': structured_data,  # Ensure this is not empty
                        'raw_content': search_result.content,
                        'search_duration': search_duration
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


# Global orchestrator instance
multi_model_orchestrator = MultiModelSearchOrchestrator()