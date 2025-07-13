"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Such-Endpoints für MineSearch API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import logging
from datetime import datetime

from ..models import MineSearchRequest, MineSearchResponse, MultiSearchRequest, SmartSearchRequest
from search_service import MineSearchService
from search_service_multi import multi_search_service
from search_service_multi_enhanced import EnhancedMultiProviderSearchService
from providers.registry import provider_registry
from model_benchmark_service import ModelBenchmarkService
from search_utils import count_filled_fields
from config import CSV_COLUMNS

logger = logging.getLogger(__name__)
router = APIRouter()

# Service-Instanzen
mine_search_service = MineSearchService()
enhanced_search_service = EnhancedMultiProviderSearchService()
benchmark_service = ModelBenchmarkService()

@router.post("/search", response_model=MineSearchResponse)
async def search_mine(request: MineSearchRequest, model: str):
    """
    Sucht nach Mining-Informationen über Multi-Provider System.
    ÄNDERUNG 12.07.2025: Erweitert um model_statistics und field_statistics Tracking
    """
    search_start_time = datetime.now()
    
    try:
        # ÄNDERUNG 11.07.2025: Nutze Enhanced Service für alle Provider-Modelle
        logger.info(f"[SEARCH API] Request mit model='{model}', mine='{request.mine_name}'")
        if ":" in model:  # Provider:Model Format (z.B. anthropic:claude-3.7-sonnet)
            logger.info(f"[SEARCH API] Verwende Enhanced Service für {model}")
            # Nutze Enhanced Service für Provider-basierte Suche
            result = await enhanced_search_service.search_single_model(
                model_id=model,
                mine_name=request.mine_name,
                country=request.country,
                commodity=request.commodity,
                region=request.region
            )
        else:
            logger.info(f"[SEARCH API] Verwende Legacy Service für {model}")
            # Legacy Support für Perplexity-Modelle
            result = await mine_search_service.search_mine(
                mine_name=request.mine_name,
                country=request.country,
                commodity=request.commodity,
                model=model,
                region=request.region
            )
        
        # Berechne Response-Zeit
        response_time_ms = (datetime.now() - search_start_time).total_seconds() * 1000
        
        # ÄNDERUNG 12.07.2025: Erweiterte Datenbank-Speicherung
        if result.get('success') and result.get('data'):
            try:
                from database import db_manager
                search_duration = result.get('data', {}).get('search_duration')
                structured_data = result['data'].get('structured_data', {})
                
                # Zähle gefüllte Felder korrekt
                filled_fields = count_filled_fields(structured_data)
                sources_count = len(result['data'].get('sources', []))
                
                # 1. Speichere search_result (bestehend)
                db_manager.save_search_result(
                    mine_name=request.mine_name,
                    model_used=model,
                    structured_data=structured_data,
                    sources=result['data'].get('sources', []),
                    country=request.country,
                    region=request.region,
                    commodity=request.commodity,
                    search_type='standard',
                    search_duration=search_duration,
                    structured_data_with_sources=result['data'].get('structured_data_with_sources'),
                    source_index=result['data'].get('source_index'),
                    data_quality=result['data'].get('data_quality'),
                    source_discovery_session=result['data'].get('source_discovery_session'),
                    success=True
                )
                
                # 2. NEUE model_statistics Speicherung
                await benchmark_service.save_model_statistics(
                    model_id=model,
                    mine_name=request.mine_name,
                    country=request.country,
                    region=request.region,
                    commodity=request.commodity,
                    run_number=1,  # API-Calls sind immer Run 1
                    success=True,
                    response_time_ms=response_time_ms,
                    fields_found=filled_fields,
                    sources_count=sources_count,
                    raw_result=result,
                    structured_data=structured_data
                )
                
                # 3. NEUE field_statistics Update
                await benchmark_service.update_field_statistics(
                    model_id=model,
                    structured_data=structured_data
                )
                
                logger.info(f"[SEARCH API] Statistiken gespeichert: {model}, {filled_fields} Felder, {response_time_ms:.0f}ms")
                
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Statistiken: {str(e)}")
        else:
            # Auch fehlgeschlagene Suchen tracken
            try:
                error_message = result.get('error', 'Unbekannter Fehler')
                await benchmark_service.save_model_statistics(
                    model_id=model,
                    mine_name=request.mine_name,
                    country=request.country,
                    region=request.region,
                    commodity=request.commodity,
                    run_number=1,
                    success=False,
                    response_time_ms=response_time_ms,
                    fields_found=0,
                    sources_count=0,
                    error_message=error_message
                )
                logger.info(f"[SEARCH API] Fehler-Statistik gespeichert: {model}, {error_message}")
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Fehler-Statistik: {str(e)}")
        
        return MineSearchResponse(**result)
    except ValueError as e:
        logger.error(f"Fehler bei der Suche: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler")

@router.post("/search/two-phase")
async def search_two_phase(request: MineSearchRequest):
    """
    ÄNDERUNG 04.07.2025: Optimierte Zwei-Phasen-Suche
    Phase 1: Schnelle Quellensuche
    Phase 2: Detaillierte Datenextraktion mit Premium-Modellen
    """
    try:
        result = await multi_search_service.search_two_phase(
            mine_name=request.mine_name,
            country=request.country,
            commodity=request.commodity,
            region=request.region
        )
        
        # Speichere Ergebnis
        if result.get('success') and result.get('data'):
            try:
                from database import db_manager
                db_manager.save_search_result(
                    mine_name=request.mine_name,
                    model_used='two_phase',
                    structured_data=result.get('data', {}),
                    sources=result.get('sources', []),
                    country=request.country,
                    region=request.region,
                    commodity=request.commodity,
                    search_type='two_phase',
                    search_duration=result.get('search_duration'),
                    confidence_scores=result.get('confidence_scores'),
                    phase1_sources=result.get('phase1_sources'),
                    phase2_models=result.get('phase2_models'),
                    success=True
                )
            except Exception as e:
                logger.error(f"Fehler beim Speichern des Zwei-Phasen-Ergebnisses: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Fehler bei Zwei-Phasen-Suche: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/multi")
async def search_multiple_models(request: MultiSearchRequest):
    """Suche mit mehreren Modellen gleichzeitig"""
    try:
        result = await multi_search_service.search_with_multiple_models(
            model_ids=request.model_ids,
            mine_name=request.mine_name,
            country=request.country,
            commodity=request.commodity,
            region=request.region
        )
        
        # Speichere alle erfolgreichen Ergebnisse
        if result.get('success') and result.get('results'):
            from database import db_manager
            for model_id, model_result in result['results'].items():
                if model_result.get('success') and model_result.get('data'):
                    try:
                        db_manager.save_search_result(
                            mine_name=request.mine_name,
                            model_used=model_id,
                            structured_data=model_result['data'].get('structured_data', {}),
                            sources=model_result['data'].get('sources', []),
                            country=request.country,
                            region=request.region,
                            commodity=request.commodity,
                            search_type='multi_model',
                            search_duration=model_result.get('search_duration'),
                            structured_data_with_sources=model_result['data'].get('structured_data_with_sources'),
                            source_index=model_result['data'].get('source_index'),
                            data_quality=model_result['data'].get('data_quality'),
                            success=True
                        )
                    except Exception as e:
                        logger.error(f"Fehler beim Speichern für Modell {model_id}: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Fehler bei Multi-Model-Suche: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/smart")
async def smart_search(request: SmartSearchRequest):
    """Intelligente Suche mit automatischer Modell-Auswahl"""
    try:
        result = await multi_search_service.smart_search(
            mine_name=request.mine_name,
            country=request.country,
            commodity=request.commodity,
            region=request.region
        )
        
        # Speichere Ergebnis
        if result.get('success') and result.get('data'):
            from database import db_manager
            try:
                models_used = ", ".join(result.get('models_used', []))
                db_manager.save_search_result(
                    mine_name=request.mine_name,
                    model_used=models_used,
                    structured_data=result['data'].get('structured_data', {}),
                    sources=result['data'].get('sources', []),
                    country=request.country,
                    region=request.region,
                    commodity=request.commodity,
                    search_type='smart_search',
                    search_duration=result.get('total_duration'),
                    structured_data_with_sources=result['data'].get('structured_data_with_sources'),
                    source_index=result['data'].get('source_index'),
                    data_quality=result['data'].get('data_quality'),
                    success=True
                )
            except Exception as e:
                logger.error(f"Fehler beim Speichern des Smart-Search-Ergebnisses: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Fehler bei Smart Search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/enhanced")
async def enhanced_search(
    mine_name: str = Query(...),
    country: str = Query(None),
    commodity: str = Query(None),
    region: str = Query(None),
    model: str = Query(..., description="Modell-ID (z.B. 'openrouter:deepseek-free')")
):
    """Erweiterte Suche mit Source Discovery"""
    try:
        result = await mine_search_service.enhanced_search(
            mine_name=mine_name,
            country=country,
            commodity=commodity,
            region=region,
            model=model
        )
        
        # Speichere Ergebnis
        if result.get('success') and result.get('data'):
            from database import db_manager
            try:
                db_manager.save_search_result(
                    mine_name=mine_name,
                    model_used=model,
                    structured_data=result['data'].get('structured_data', {}),
                    sources=result['data'].get('sources', []),
                    country=country,
                    region=region,
                    commodity=commodity,
                    search_type='enhanced',
                    search_duration=result['data'].get('search_duration'),
                    structured_data_with_sources=result['data'].get('structured_data_with_sources'),
                    source_index=result['data'].get('source_index'),
                    data_quality=result['data'].get('data_quality'),
                    source_discovery_session=result['data'].get('source_discovery_session'),
                    success=True
                )
            except Exception as e:
                logger.error(f"Fehler beim Speichern des Enhanced-Search-Ergebnisses: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Fehler bei Enhanced Search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/comprehensive")
async def comprehensive_search(request: MineSearchRequest):
    """
    Umfassende Suche mit Enhanced Service (10/10 System)
    - Phase 1: Alle Modelle sammeln Quellen
    - Phase 2: Alle Modelle analysieren alle Quellen
    """
    try:
        result = await enhanced_search_service.search_comprehensive(
            mine_name=request.mine_name,
            country=request.country,
            commodity=request.commodity,
            region=request.region
        )
        
        # Speichere Ergebnis
        if result.get('success') and result.get('data'):
            try:
                from database import db_manager
                db_manager.save_search_result(
                    mine_name=request.mine_name,
                    model_used='comprehensive_enhanced',
                    structured_data=result.get('data', {}),
                    sources=result.get('sources', []),
                    country=request.country,
                    region=request.region,
                    commodity=request.commodity,
                    search_type='comprehensive',
                    search_duration=result.get('search_duration'),
                    confidence_scores=result.get('confidence_scores'),
                    phase1_sources=result.get('phase1_sources'),
                    phase2_models=result.get('phase2_models'),
                    success=True
                )
            except Exception as e:
                logger.error(f"Fehler beim Speichern des Comprehensive-Ergebnisses: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Fehler bei Comprehensive Search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/html")
async def search_mine_html(request: MineSearchRequest, model: str):
    """Sucht nach Mining-Informationen und gibt HTML zurück"""
    try:
        from html_utils import create_result_card, create_error_card
        
        result = await mine_search_service.search_mine(
            mine_name=request.mine_name,
            country=request.country,
            commodity=request.commodity,
            model=model,
            region=request.region
        )
        
        if result["success"]:
            return {"html": create_result_card(result["data"])}
        else:
            return {"html": create_error_card(result.get("error", "Unbekannter Fehler"))}
    except Exception as e:
        logger.error(f"Fehler bei HTML-Suche: {str(e)}")
        return {"html": create_error_card(str(e))}