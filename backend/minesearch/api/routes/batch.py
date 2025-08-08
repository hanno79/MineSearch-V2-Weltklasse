"""
Author: rahn
Datum: 19.07.2025
Version: 1.1
Beschreibung: Batch-Processing Routes für CSV-Upload (FIXED 500 Error)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response, HTMLResponse
import csv
import io
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from minesearch.config import CSV_COLUMNS
from minesearch_v2.backend.batch_service import BatchService  # transitional
from minesearch.search_service import MineSearchService
from minesearch.search_service_multi import MultiProviderSearchService
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from extraction_validators import is_placeholder_value

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test")
async def test_batch_endpoint():
    """Test-Endpoint um zu prüfen ob die Route funktioniert"""
    return {"status": "ok", "message": "Batch endpoints are working"}

# Temporärer Speicher für CSV-Daten (in Production würde man Redis/DB nutzen)
uploaded_mines_cache = {}
batch_results_cache = {}

# Batch Service
batch_service = BatchService(uploaded_mines_cache, batch_results_cache)

@router.post("/upload-csv")
async def upload_csv(csv_file: UploadFile = File(...)):
    """CSV Datei hochladen und analysieren"""
    # ÄNDERUNG 04.07.2025: Parameter-Name von 'file' zu 'csv_file' geändert für Frontend-Kompatibilität
    try:
        logger.info(f"CSV Upload empfangen: {csv_file.filename}, Size: {csv_file.size if hasattr(csv_file, 'size') else 'unknown'}")
        return await batch_service.process_csv_upload(csv_file)
    except Exception as e:
        logger.error(f"Fehler beim CSV Upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch-search")
async def batch_search(
    session_id: str = Form(...),
    model: Optional[str] = Form(None, description="Einzelnes Modell (Legacy)"),
    search_type: str = Form("standard"),
    count: Optional[int] = Form(None),
    search_all: Optional[str] = Form("false"),
    selected_models: Optional[str] = Form(None, description="Komma-getrennte Modell-Liste"),
    # ÄNDERUNG 07.07.2025: Option für Mehrfach-Durchlauf
    consistency_check: Optional[str] = Form("false"),
    consistency_runs: Optional[int] = Form(3),
    # PHASE 2.3: COMPREHENSIVE SEARCH Option
    comprehensive_search: Optional[str] = Form("false")
):
    """
    Batch-Suche für mehrere Minen aus CSV
    FIXED 19.07.2025: 500 Error consensus Variable behoben
    """
    try:
        logger.info(f"[BATCH API] Received request: session_id='{session_id}', model='{model}', selected_models='{selected_models}'")
        # Hole Minen-Daten aus dem Cache
        if session_id not in uploaded_mines_cache:
            raise ValueError("Session abgelaufen. Bitte CSV erneut hochladen.")
        
        session_data = uploaded_mines_cache[session_id]
        mines = session_data['mines']
        columns = session_data['columns']
        logger.info(f"Batch-Suche für Session {session_id} mit {len(mines)} Minen")
        
        # Bestimme wie viele Minen gesucht werden
        if search_all == "true":
            mines_to_search = mines
        else:
            mines_to_search = mines[:count] if count else mines[:5]
        logger.info(f"Anzahl zu durchsuchender Minen: {len(mines_to_search)}")
        
        # IMPROVED 19.07.2025: Vereinfachte und robuste Model-Auswahl
        models_to_use = []
        
        # 1. Priorität: selected_models (Frontend Liste)
        if selected_models and selected_models.strip():
            models_to_use = [m.strip() for m in selected_models.split(',') if m.strip()]
            logger.info(f"[BATCH-MODELS] Frontend selection: {models_to_use}")
        
        # 2. Fallback: einzelnes model Parameter (Legacy)
        elif model and model.strip():
            models_to_use = [model.strip()]
            logger.info(f"[BATCH-MODELS] Legacy single model: {models_to_use}")
        
        # 3. Default: Kimi K2 (beste Performance)
        else:
            models_to_use = ["openrouter:kimi-k2"]
            logger.warning(f"[BATCH-MODELS] No models specified, using default: {models_to_use[0]}")
        
        # Final validation
        if not models_to_use or not any(m.strip() for m in models_to_use):
            raise HTTPException(
                status_code=400, 
                detail="Mindestens ein gültiges Modell muss ausgewählt werden. Frontend-Parameter: selected_models, model"
            )
        
        # Führe Suchen durch
        results = []
        
        # Shared Service Container
        from minesearch.services_container import services
        
        # PHASE 2.3: COMPREHENSIVE SEARCH ORCHESTRATOR Integration
        from minesearch_v2.backend.comprehensive_search_orchestrator import comprehensive_search_orchestrator
        
        for idx, mine in enumerate(mines_to_search):
            mine_name = mine.get("mine_name", "")
            country = mine.get("country", "")
            commodity = mine.get("commodity", "")
            region = mine.get("region", "")
            
            if not mine_name:
                continue
                
            logger.info(f"Suche {idx+1}/{len(mines_to_search)}: {mine_name}")
            
            try:
                # PHASE 2.3: COMPREHENSIVE SEARCH Option
                if comprehensive_search == "true":
                    logger.info(f"[COMPREHENSIVE] Starte systematische Vollsuche für {mine_name}")
                    try:
                        comprehensive_result = await comprehensive_search_orchestrator.orchestrate_comprehensive_search(
                            mine_name=mine_name,
                            country=country or "Canada",
                            region=region or "Quebec", 
                            commodity=commodity,
                            available_models=models_to_use
                        )
                        
                        if comprehensive_result.get('success'):
                            # Formatiere für Batch-Ergebnisse
                            result_data = {
                                "mine_name": mine_name,
                                "country": country,
                                "commodity": commodity,
                                "region": region,
                                "success": True,
                                "data": {
                                    "structured_data": comprehensive_result['data'],
                                    "field_completion_status": comprehensive_result['field_completion_status'],
                                    "completion_report": comprehensive_result['completion_report'],
                                    "source_quality_report": comprehensive_result['source_quality_report'],
                                    "search_strategy": "comprehensive_systematic"
                                }
                            }
                            results.append(result_data)
                            
                            # Speichere in Datenbank
                            try:
                                db_manager.save_search_result(
                                    mine_name=mine_name,
                                    model_used='comprehensive_systematic',
                                    structured_data=comprehensive_result['data'],
                                    sources=[],
                                    session_id=session_id,
                                    country=country,
                                    region=region,
                                    commodity=commodity,
                                    search_type='batch_comprehensive',
                                    search_duration=comprehensive_result.get('duration_seconds'),
                                    data_quality=comprehensive_result['completion_report'],
                                    success=True
                                )
                                logger.info(f"[COMPREHENSIVE-DB] Ergebnis für {mine_name} gespeichert")
                            except Exception as db_error:
                                logger.error(f"[COMPREHENSIVE-DB] Fehler beim Speichern: {str(db_error)}")
                        else:
                            # Fallback auf Standard-Suche
                            logger.warning(f"[COMPREHENSIVE] Comprehensive search für {mine_name} fehlgeschlagen, verwende Standard-Suche")
                            comprehensive_search = "false"  # Fallback für diese Mine
                    
                    except Exception as e:
                        logger.error(f"[COMPREHENSIVE] Fehler bei comprehensive search für {mine_name}: {str(e)}")
                        # Fallback auf Standard-Suche
                        comprehensive_search = "false"
                
                # Standard-Suche nur wenn nicht comprehensive
                if comprehensive_search != "true":
                    # Führe Standard-Suche durch
                    if len(models_to_use) > 1:
                        # Multi-Model-Suche
                        result = await services.multi_search_service.search_with_multiple_models(
                            model_ids=models_to_use,
                            mine_name=mine_name,
                            country=country,
                            commodity=commodity,
                            region=region
                        )
                    else:
                        # Single-Model-Suche
                        result = await services.multi_search_service.search_with_model(
                            model_id=models_to_use[0],
                            mine_name=mine_name,
                            country=country,
                            commodity=commodity,
                            region=region
                        )
                    
                    # Erstelle Ergebnis
                    result_data = {
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": result.get('success', False),
                        "data": result.get('data', {}),
                        "model_info": {
                            "models_used": models_to_use,
                            "search_strategy": "standard"
                        }
                    }
                    results.append(result_data)
                    
                    # Speichere in Datenbank wenn erfolgreich
                    if result_data["success"] and result_data.get("data"):
                        try:
                            structured_data = result.get('data', {}).get('structured_data', {})
                            if structured_data:
                                db_manager.save_search_result(
                                    mine_name=mine_name,
                                    model_used='_'.join(models_to_use) if len(models_to_use) > 1 else models_to_use[0],
                                    structured_data=structured_data,
                                    sources=result.get('data', {}).get('sources', []),
                                    session_id=session_id,
                                    country=country,
                                    region=region,
                                    commodity=commodity,
                                    search_type='batch_standard',
                                    success=True
                                )
                                logger.info(f"[BATCH-DB] Ergebnis für {mine_name} gespeichert")
                        except Exception as db_error:
                            logger.error(f"[BATCH-DB] Fehler beim Speichern: {str(db_error)}")
                
            except Exception as e:
                logger.error(f"Fehler bei Suche für {mine_name}: {str(e)}")
                results.append({
                    "mine_name": mine_name,
                    "country": country,
                    "commodity": commodity,
                    "region": region,
                    "success": False,
                    "error": str(e)
                })
        
        # Debug: Log die Struktur der Ergebnisse
        logger.info(f"[BATCH-DEBUG] Anzahl Ergebnisse: {len(results)}")
        if results:
            first_result = results[0]
            logger.info(f"[BATCH-DEBUG] Erstes Ergebnis - Keys: {list(first_result.keys())}")
            if 'data' in first_result and first_result['data']:
                logger.info(f"[BATCH-DEBUG] Data Keys: {list(first_result['data'].keys())}")
        
        # Erstelle HTML-Antwort
        from minesearch.html_utils import create_batch_results_table
        html_content = create_batch_results_table(results)
        
        # Speichere Ergebnisse im Cache für Download
        batch_results_cache[session_id] = {
            'results': results,
            'columns': columns,
            'timestamp': datetime.now()
        }
        
        # Debug: Log einen Teil des generierten HTML
        logger.info(f"[BATCH-DEBUG] HTML-Länge: {len(html_content)}")
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Fehler bei Batch-Suche: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-batch")
async def process_batch(
    cache_key: str = Form(...),
    model: str = Form(..., description="Modell-ID (z.B. 'openrouter:deepseek-free')")
):
    """Batch-Verarbeitung der hochgeladenen Minen"""
    try:
        return await batch_service.process_batch(cache_key, model)
    except Exception as e:
        logger.error(f"Fehler bei Batch-Verarbeitung: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch-results/{cache_key}")
async def get_batch_results(cache_key: str):
    """Batch-Ergebnisse abrufen"""
    if cache_key not in batch_results_cache:
        raise HTTPException(status_code=404, detail="Keine Ergebnisse gefunden")
    
    from minesearch.html_utils import create_batch_results_table
    
    results = batch_results_cache[cache_key]
    html = create_batch_results_table(results)
    
    return {"html": html, "results": results}

@router.get("/batch-results/{cache_key}/download")
async def download_batch_results(cache_key: str):
    """Batch-Ergebnisse als CSV herunterladen"""
    if cache_key not in batch_results_cache:
        raise HTTPException(status_code=404, detail="Keine Ergebnisse gefunden")
    
    results = batch_results_cache[cache_key]
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    
    for result in results:
        if result["success"]:
            row = {
                "Mine Name": result["mine_name"],
                "Country": result.get("country", ""),
                "Commodity": result.get("commodity", ""),
                "Region": result.get("region", "")
            }
            
            # Strukturierte Daten hinzufügen
            structured_data = result["data"].get("structured_data", {})
            for key in CSV_COLUMNS[4:]:  # Skip die ersten 4 (Mine Name, Country, etc.)
                row[key] = structured_data.get(key, "k.A.")
            
            writer.writerow(row)
    
    content = output.getvalue()
    
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=mine_search_results_{cache_key}.csv"
        }
    )