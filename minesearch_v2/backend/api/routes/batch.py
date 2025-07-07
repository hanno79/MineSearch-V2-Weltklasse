"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Batch-Processing Routes für CSV-Upload
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response, HTMLResponse
import csv
import io
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import CSV_COLUMNS
from batch_service import BatchService
from search_service import MineSearchService
from search_service_multi import MultiProviderSearchService
from providers.registry import provider_registry

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
    model: str = Form("sonar-pro"),
    search_type: str = Form("standard"),
    count: Optional[int] = Form(None),
    search_all: Optional[str] = Form("false"),
    selected_models: Optional[str] = Form(None)
):
    """Batch-Suche für mehrere Minen aus CSV"""
    try:
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
        
        # ÄNDERUNG 04.07.2025: Verwende selected_models wenn vorhanden
        models_to_use = []
        if selected_models:
            # Parse comma-separated model list
            models_to_use = [m.strip() for m in selected_models.split(',') if m.strip()]
            logger.info(f"Verwende ausgewählte Modelle aus Frontend: {models_to_use}")
        else:
            # Fallback auf einzelnes Modell
            models_to_use = [model]
            logger.info(f"Verwende einzelnes Modell: {model}")
        
        # Führe Suchen durch
        results = []
        
        # Multi-Provider Search Service für alle Modelle mit Provider-Präfix
        multi_search_service = MultiProviderSearchService()
        
        for idx, mine in enumerate(mines_to_search):
            mine_name = mine.get("mine_name", "")
            country = mine.get("country", "")
            commodity = mine.get("commodity", "")
            region = mine.get("region", "")
            
            if not mine_name:
                continue
                
            logger.info(f"Suche {idx+1}/{len(mines_to_search)}: {mine_name}")
            
            # Führe Suche mit allen ausgewählten Modellen durch
            if len(models_to_use) > 1:
                # Multi-Model-Suche
                logger.info(f"Multi-Model-Suche für {mine_name} mit {len(models_to_use)} Modellen")
                try:
                    multi_result = await multi_search_service.search_with_multiple_models(
                        model_ids=models_to_use,
                        mine_name=mine_name,
                        country=country,
                        commodity=commodity,
                        region=region
                    )
                    
                    # Aggregiere beste Ergebnisse aus allen Modellen
                    best_data = {}
                    all_sources = []
                    
                    for model_id, model_result in multi_result.get('results', {}).items():
                        if model_result.get('success') and model_result.get('data'):
                            model_data = model_result['data'].get('structured_data', {})
                            # Fülle fehlende Felder mit Daten aus diesem Modell
                            for field, value in model_data.items():
                                if value and not best_data.get(field):
                                    best_data[field] = value
                            
                            # Sammle Quellen
                            if model_result['data'].get('sources'):
                                all_sources.extend(model_result['data']['sources'])
                    
                    results.append({
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": bool(best_data),
                        "data": {
                            "structured_data": best_data,
                            "sources": all_sources[:20]  # Top 20 Quellen
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"Fehler bei Multi-Model-Suche für {mine_name}: {str(e)}")
                    results.append({
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": False,
                        "error": str(e)
                    })
            else:
                # Single-Model-Suche
                model_id = models_to_use[0]
                logger.info(f"Single-Model-Suche für {mine_name} mit {model_id}")
                
                try:
                    # ÄNDERUNG 04.07.2025: Verwende immer MultiProviderSearchService für konsistente Ergebnisse
                    result = await multi_search_service.search_with_model(
                        model_id=model_id,
                        mine_name=mine_name,
                        country=country,
                        commodity=commodity,
                        region=region
                    )
                    
                    results.append({
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": result.get("success", False),
                        "data": result.get("data", {})
                    })
                    
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
        
        # Erstelle HTML-Antwort
        # ÄNDERUNG 04.07.2025: Verwende die existierende create_batch_results_table Funktion
        from html_utils import create_batch_results_table
        html_content = create_batch_results_table(results)
        
        # Speichere Ergebnisse im Cache für Download
        batch_results_cache[session_id] = {
            'results': results,
            'columns': columns,
            'timestamp': datetime.now()
        }
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Fehler bei Batch-Suche: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-batch")
async def process_batch(
    cache_key: str = Form(...),
    model: str = Form("sonar-pro")
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
    
    from html_utils import create_batch_results_table
    
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