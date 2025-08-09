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
from minesearch.batch_service import BatchService  # Adapter
from minesearch.search_service import MineSearchService
# CONSOLIDATION 09.08.2025: MultiProviderSearchService entfernt - verwende MineSearchService direkt
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from minesearch.extraction_validators import is_placeholder_value

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
        
        # Verarbeite CSV direkt hier statt batch_service zu nutzen
        contents = await csv_file.read()
        csv_content = contents.decode('utf-8-sig')  # FIX: UTF-8-SIG entfernt BOM automatisch
        
        # FIX: Auto-detect CSV-Delimiter (Semikolon vs Komma)
        delimiter = ';' if ';' in csv_content.split('\n')[0] else ','
        logger.info(f"[CSV-PARSER] Detected delimiter: '{delimiter}'")
        
        # Parse CSV mit korrektem Delimiter
        csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        mines = []
        columns = []
        
        for i, row in enumerate(csv_reader):
            if i == 0:
                columns = list(row.keys())
            mines.append(row)
            
            # Limit für Demo
            if i >= 100:
                break
        
        # Erstelle Session
        import uuid
        session_id = str(uuid.uuid4())
        
        # Speichere in Cache
        from datetime import datetime
        uploaded_mines_cache[session_id] = {
            'mines': mines,
            'columns': columns,
            'timestamp': datetime.now()
        }
        
        mine_count = len(mines)
        logger.info(f"CSV processed: {mine_count} mines, session: {session_id}")
        
        # Erstelle HTML-Interface für Batch-Suche
        session_id = session_id
        mine_count = mine_count
        columns = columns
        
        # HTML für Batch-Search-Interface generieren
        html_content = f"""
        <div class="csv-upload-success">
            <div class="alert alert-success">
                <h3>✅ CSV erfolgreich hochgeladen!</h3>
                <p><strong>{mine_count} Minen</strong> wurden erkannt mit <strong>{len(columns)} Spalten</strong></p>
                <p><em>Session ID: {session_id}</em></p>
            </div>
            
            <div class="batch-search-interface" style="margin-top: 20px;">
                <h3>🔍 Batch-Suche konfigurieren</h3>
                
                <form id="batch-form" 
                      hx-post="/api/batch-search"
                      hx-target="#batch-results"
                      hx-indicator="#loading">
                    
                    <input type="hidden" name="session_id" value="{session_id}">
                    <input type="hidden" name="selected_models" value="">
                    
                    <div class="form-group">
                        <label><strong>Anzahl zu durchsuchender Minen:</strong></label>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="search_all" value="false" checked> Nur erste 5 Minen (schnell)</label>
                        </div>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="search_all" value="false"> Erste <input type="number" name="count" value="20" min="1" max="100" style="width: 60px;"> Minen</label>
                        </div>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="search_all" value="true"> <strong>Alle {mine_count} Minen durchsuchen</strong></label>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label><strong>Suchtyp:</strong></label>
                        <select name="search_type" style="width: 200px; padding: 5px;">
                            <option value="standard">Standard-Suche</option>
                            <option value="comprehensive">Umfassende Suche</option>
                        </select>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <button type="submit" class="batch-search-button" style="background: #4CAF50; color: white; padding: 15px 30px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer;">
                            🚀 Batch-Suche starten
                        </button>
                    </div>
                </form>
            </div>
            
            <div class="csv-info-details" style="margin-top: 20px; background: #f5f5f5; padding: 15px; border-radius: 5px;">
                <h4>📋 CSV Details:</h4>
                <p><strong>Spalten gefunden:</strong></p>
                <ul>
                    {"".join([f"<li>{col}</li>" for col in columns[:10]])}
                    {f"<li><em>... und {len(columns) - 10} weitere</em></li>" if len(columns) > 10 else ""}
                </ul>
            </div>
        </div>
        
        <div id="batch-results" style="margin-top: 30px;"></div>
        """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
        
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
        
        # DEBUG: Schaue erste Minen an
        logger.info(f"[BATCH-DEBUG] Erste 3 Minen: {mines_to_search[:3]}")
        if mines_to_search:
            first_mine = mines_to_search[0]
            logger.info(f"[BATCH-DEBUG] Erste Mine Keys: {list(first_mine.keys())}")
            logger.info(f"[BATCH-DEBUG] Erste Mine Values: {first_mine}")
        
        # Führe Suchen durch - ALLE IMPORTS HIER
        results = []
        
        logger.info("[BATCH-DEBUG] Vor Import-Bereich")
        
        # PHASE 2.3: COMPREHENSIVE SEARCH ORCHESTRATOR Integration
        # Optional: nur wenn vorhanden (Legacy)
        try:
            from minesearch_v2.backend.comprehensive_search_orchestrator import comprehensive_search_orchestrator
        except Exception:
            comprehensive_search_orchestrator = None
            logger.info("[BATCH] Comprehensive search orchestrator nicht verfügbar")
            
        logger.info("[BATCH] Starte Mine-Processing-Schleife")
        
        for idx, mine in enumerate(mines_to_search):
            # ERWEITERTE FIELD-MAPPING für Quebec-CSV und internationale Formate
            mine_name = (mine.get("mine_name", "") or 
                        mine.get("Name", "") or 
                        mine.get("name", "") or 
                        mine.get("Mine Name", "") or 
                        mine.get("MINE_NAME", "") or
                        mine.get("Mine", "") or
                        mine.get("Site", "")).strip()
            
            country = (mine.get("country", "") or 
                      mine.get("Country", "") or 
                      mine.get("COUNTRY", "") or 
                      mine.get("Land", "") or
                      mine.get("Pays", "") or  # Französisch
                      "Canada").strip()  # Quebec-Default
            
            commodity = (mine.get("commodity", "") or 
                        mine.get("Commodity", "") or 
                        mine.get("Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "") or
                        mine.get("Rohstoff", "") or
                        mine.get("Produit", "") or  # Französisch
                        mine.get("Mineral", "")).strip()
            
            region = (mine.get("region", "") or 
                     mine.get("Region", "") or 
                     mine.get("REGION", "") or
                     mine.get("Province", "") or
                     mine.get("État", "") or  # Französisch
                     "Quebec").strip()  # Quebec-Default
            
            if not mine_name:
                logger.warning(f"[BATCH] Mine {idx+1} hat keinen Namen, überspringe. Keys: {list(mine.keys())[:5]}...")
                logger.debug(f"[BATCH-DEBUG] Mine {idx+1} Values: {dict(list(mine.items())[:3])}")
                continue
                
            # SUCCESS: Mine erfolgreich geparst
            logger.info(f"[BATCH-SUCCESS] Mine {idx+1}: '{mine_name}' in {country}, {region}")
                
            logger.info(f"Suche {idx+1}/{len(mines_to_search)}: {mine_name}")
            
            try:
                # PHASE 2.3: COMPREHENSIVE SEARCH Option
                if comprehensive_search == "true" and comprehensive_search_orchestrator is not None:
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
                    # ECHTE PROVIDER-BASIERTE SUCHE (REGEL 10: Keine Mock-Daten)
                    try:
                        model_id = models_to_use[0]
                        
                        # Verwende MineSearchService für echte Suche
                        from minesearch.search_service import MineSearchService
                        search_service = MineSearchService()
                        
                        logger.info(f"[BATCH-REAL] Starte echte Suche für {mine_name} mit {model_id}")
                        
                        # Führe echte Suche durch
                        real_result = await search_service.search_mine(
                            mine_name=mine_name,
                            model=model_id,
                            country=country,
                            commodity=commodity, 
                            region=region
                        )
                        
                        if real_result.get('success'):
                            result = {
                                'success': True,
                                'data': real_result.get('data', {}),
                                'model_used': model_id,
                                'search_duration': real_result.get('data', {}).get('search_duration', 0)
                            }
                            logger.info(f"[BATCH-REAL] Echte Suche erfolgreich für {mine_name} mit {model_id}")
                        else:
                            result = {
                                'success': False,
                                'error': real_result.get('error', 'Unknown search error'),
                                'data': {}
                            }
                            logger.warning(f"[BATCH-REAL] Echte Suche fehlgeschlagen für {mine_name}: {real_result.get('error')}")
                        
                    except Exception as search_error:
                        logger.error(f"[BATCH-REAL] Echter Such-Service fehler für {mine_name}: {str(search_error)}")
                        result = {
                            'success': False,
                            'error': f"Real search failed: {str(search_error)}",
                            'data': {}
                        }
                    
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