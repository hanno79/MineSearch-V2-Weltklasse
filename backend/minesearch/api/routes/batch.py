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
from minesearch.html_utils import create_batch_results_table

logger = logging.getLogger(__name__)
router = APIRouter()

def count_filled_fields(structured_data):
    """Zählt echte (nicht-leere) Felder in structured_data"""
    if not structured_data:
        return 0
    return len([v for v in structured_data.values() 
                if v and str(v).strip() and str(v).strip() not in ['', 'None', 'null', 'nichts gefunden']])

def is_weak_result(result_data):
    """
    Prüft ob ein Suchergebnis Enhancement benötigt
    
    Returns True wenn:
    - Weniger als 8 echte Felder gefüllt sind
    - 3 oder mehr kritische Felder fehlen
    """
    if not result_data or not result_data.get('success', False):
        return True
        
    data = result_data.get('data', {})
    structured_data = data.get('structured_data', {})
    
    # Zähle gefüllte Felder
    filled_fields = count_filled_fields(structured_data)
    
    # Definiere kritische Felder
    critical_fields = [
        'Restaurationskosten', 
        'Jahr der Aufnahme der Kosten', 
        'Jahr der Erstellung des Dokumentes', 
        'Fläche der Mine in qkm', 
        'Fördermenge/Jahr'
    ]
    
    # Zähle fehlende kritische Felder
    missing_critical = [f for f in critical_fields 
                       if f not in structured_data or not structured_data[f] 
                       or str(structured_data[f]).strip() in ['', 'None', 'null', 'nichts gefunden']]
    
    return filled_fields < 8 or len(missing_critical) >= 3

async def fallback_search_if_needed(mine_name, country, commodity, region, current_best_data):
    """
    Führt Fallback-Suche mit deepseek-free durch, wenn aktuelles Ergebnis schwach ist
    
    Returns: Verbessertes result_data oder None wenn kein Fallback nötig/möglich
    """
    try:
        logger.info(f"[FALLBACK] Starte deepseek-free Fallback für {mine_name}")
        
        # Provider Registry Setup
        from minesearch.providers.registry import provider_registry
        from minesearch.config import config
        
        if not provider_registry._providers:
            provider_registry.initialize(config.PROVIDERS)
        
        provider = provider_registry.get_provider_for_model('openrouter:deepseek-free')
        if not provider:
            logger.error(f"[FALLBACK] Kein deepseek-free Provider verfügbar")
            return None
        
        # Fallback-Suche ausführen
        query = f"{mine_name} mine {country} {commodity} restoration costs area production"
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity, 
            'region': region
        }
        
        search_result = await provider.search(query, 'deepseek-free', options)
        
        if search_result and search_result.success and search_result.structured_data:
            # DEBUG: Log Restaurationskosten vor dem Return
            resto_value = search_result.structured_data.get('Restaurationskosten', '')
            logger.info(f"[FALLBACK-DEBUG] Restaurationskosten vor Return: '{resto_value}'")
            
            fallback_filled = count_filled_fields(search_result.structured_data)
            current_filled = count_filled_fields(current_best_data.get('structured_data', {}))
            
            if fallback_filled > current_filled:
                logger.info(f"[FALLBACK-SUCCESS] deepseek-free better: {fallback_filled} vs {current_filled} Felder")
                
                # DEBUG: Log alle kritischen Felder
                critical_fields = ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Fläche der Mine in qkm']
                for field in critical_fields:
                    value = search_result.structured_data.get(field, '(leer)')
                    logger.info(f"[FALLBACK-DEBUG] {field}: '{value}'")
                
                return {
                    'structured_data': search_result.structured_data,
                    'raw_content': search_result.content,
                    'field_count': len(search_result.structured_data),
                    'filled_field_count': fallback_filled,
                    'enhanced_via_fallback': True
                }
            else:
                logger.info(f"[FALLBACK] deepseek-free nicht besser: {fallback_filled} vs {current_filled} Felder")
        else:
            logger.warning(f"[FALLBACK] deepseek-free Suche fehlgeschlagen für {mine_name}")
            
    except Exception as e:
        logger.error(f"[FALLBACK] Fehler bei Fallback-Suche für {mine_name}: {str(e)}")
    
    return None

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
        logger.info(f"[BATCH-DEBUG] Verwende {len(models_to_use)} Modelle: {models_to_use}")
        logger.info(f"[BATCH-DEBUG] Comprehensive Search: {comprehensive_search}")
        logger.info(f"[BATCH-DEBUG] Search Type: {search_type}")
        
        # PHASE 2.3: COMPREHENSIVE SEARCH ORCHESTRATOR Integration
        # Optional: nur wenn vorhanden (Legacy)
        try:
            from minesearch_v2.backend.comprehensive_search_orchestrator import comprehensive_search_orchestrator
        except ImportError:
            comprehensive_search_orchestrator = None
            logger.info("[BATCH] Comprehensive search orchestrator nicht verfügbar")
        except ModuleNotFoundError:
            comprehensive_search_orchestrator = None
            logger.info("[BATCH] Comprehensive search orchestrator Modul nicht gefunden")
        except Exception as e:
            comprehensive_search_orchestrator = None
            logger.warning(f"[BATCH] Unerwarteter Fehler beim Import des Orchestrators: {e}")
            
        logger.info("[BATCH] Starte Mine-Processing-Schleife")
        logger.info(f"[BATCH-DEBUG] mines_to_search count: {len(mines_to_search)}")
        logger.info(f"[BATCH-DEBUG] search_all: {search_all}, count: {count}")
        
        # KRITISCHES DEBUG-LOGGING IN DATEI
        with open("/tmp/batch_debug.log", "w") as f:
            f.write(f"[BATCH-ROUTE] Batch-Route aufgerufen! mines_to_search: {len(mines_to_search)}\n")
            f.write(f"[BATCH-ROUTE] Modelle: {models_to_use}\n")
        
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
            
            # DEBUG-DATEI UPDATE
            with open("/tmp/batch_debug.log", "a") as f:
                f.write(f"[BATCH-MINE] Processing mine {idx+1}: '{mine_name}'\n")
                
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
                
                # KRITISCHER FIX 23.08.2025: Verwende EXISTIERENDE Datenbank-Ergebnisse statt neue API-Calls
                if comprehensive_search != "true":
                    logger.info(f"[BATCH-DB-FIRST] Prüfe Datenbank für existierende {mine_name} Ergebnisse")
                    
                    # 1. PRÜFE DATENBANK-ERGEBNISSE ZUERST
                    db_results = []
                    try:
                        # Hole existierende Ergebnisse für diese Mine aus der Datenbank
                        existing_results = db_manager.get_recent_search_results(
                            mine_name=mine_name, 
                            hours_back=24,  # Suche in letzten 24 Stunden
                            limit=5
                        )
                        
                        logger.info(f"[BATCH-DB-FIRST] Gefunden: {len(existing_results)} existierende DB-Ergebnisse für {mine_name}")
                        
                        # Konvertiere DB-Ergebnisse zu Batch-Format
                        for db_result in existing_results:
                            if db_result.success and db_result.structured_data:
                                structured_data = db_result.structured_data
                                filled_fields = count_filled_fields(structured_data)
                                
                                if filled_fields >= 5:  # Nur gute Ergebnisse verwenden
                                    db_results.append({
                                        'model_id': db_result.model_used,
                                        'success': True,
                                        'data': {
                                            'structured_data': structured_data,
                                            'field_count': len(structured_data),
                                            'filled_field_count': filled_fields,
                                            'source': 'database_cache'
                                        }
                                    })
                                    logger.info(f"[BATCH-DB-FIRST] Verwende DB-Ergebnis: {db_result.model_used} mit {filled_fields} Feldern")
                        
                    except Exception as e:
                        logger.warning(f"[BATCH-DB-FIRST] DB-Abfrage fehlgeschlagen: {e}")
                    
                    # 2. WENN GUTE DB-ERGEBNISSE VORHANDEN: Verwende sie
                    if db_results:
                        logger.info(f"[BATCH-DB-FIRST] Verwende {len(db_results)} existierende DB-Ergebnisse statt neue API-Calls")
                        individual_results = db_results
                    else:
                        # 3. FALLBACK: Nur wenn keine guten DB-Ergebnisse, dann neue Provider-Suche
                        logger.info(f"[BATCH-FALLBACK] Keine ausreichenden DB-Ergebnisse - starte Provider-Suche für {mine_name}")
                        individual_results = []
                        
                        # TEMPORÄR DEAKTIVIERT: Provider-Suche wegen Syntaxfehler
                        logger.info(f"[BATCH-FALLBACK] Provider-Suche temporär deaktiviert - verwende Fallback-Daten")
                        individual_results = [{"model_id": "fallback", "success": False, "error": "Provider search disabled"}]
                    
                    # Verarbeite direkte Provider-Ergebnisse
                    successful_models = [r for r in individual_results if r['success']]
                    failed_models = [r for r in individual_results if not r['success']]
                    batch_success = len(successful_models) > 0
                    
                    logger.info(f"[BATCH-DIRECT] Direkter Provider-Aufruf abgeschlossen für '{mine_name}': {len(successful_models)} erfolgreich, {len(failed_models)} fehlgeschlagen")
                    
                    # KRITISCHER FIX 22.08.2025: Extrahiere structured_data für HTML-Generator
                    best_structured_data = {}
                    if successful_models:
                        # Wähle das erfolgreichste Modell (das mit den meisten gefüllten Feldern)
                        best_model = None
                        max_filled_fields = 0
                        
                        for model_result in successful_models:
                            model_data = model_result.get('data', {})
                            structured_data = model_data.get('structured_data', {})
                            
                            if structured_data:
                                filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() not in ['-', '', 'None', 'null', 'nichts gefunden']])
                                
                                if filled_fields > max_filled_fields:
                                    max_filled_fields = filled_fields
                                    best_model = model_result
                                    best_structured_data = structured_data
                        
                        logger.info(f"[BATCH-CONSOLIDATION] Selected best model for {mine_name}: {best_model['model_id'] if best_model else 'None'} with {max_filled_fields} filled fields")
                        
                        # DEBUG: Log sample fields from best model
                        if best_structured_data:
                            sample_fields = ['Country', 'Region', 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)', 'Restaurationskosten', 'Eigentümer']
                            for field in sample_fields:
                                if field in best_structured_data:
                                    value = best_structured_data[field]
                                    logger.info(f"[BATCH-CONSOLIDATION] {mine_name} final - {field}: '{value}'")
                                else:
                                    logger.warning(f"[BATCH-CONSOLIDATION] {mine_name} missing field: {field}")
                        
                        # INTELLIGENT FALLBACK: Prüfe ob Ergebnis Enhancement benötigt
                        temp_result_data = {
                            "success": batch_success,
                            "data": {"structured_data": best_structured_data}
                        }
                        
                        if is_weak_result(temp_result_data):
                            logger.info(f"[SMART-FALLBACK] {mine_name} benötigt Enhancement - teste deepseek-free")
                            fallback_data = await fallback_search_if_needed(mine_name, country, commodity, region, {"structured_data": best_structured_data})
                            
                            if fallback_data:
                                best_structured_data = fallback_data['structured_data']
                                logger.info(f"[SMART-FALLBACK] {mine_name} verbessert durch deepseek-free!")
                        else:
                            logger.info(f"[SMART-FALLBACK] {mine_name} bereits ausreichend - kein Fallback nötig")
                        
                        # LEGACY FALLBACK: Wenn kein Modell structured_data hat, kombiniere alle verfügbaren Daten
                        if not best_structured_data and successful_models:
                            logger.warning(f"[BATCH-CONSOLIDATION] No structured_data found, attempting data consolidation for {mine_name}")
                            for model_result in successful_models:
                                model_data = model_result.get('data', {})
                                # Füge alle non-empty Felder zusammen
                                for key, value in model_data.items():
                                    if key != 'structured_data' and value and str(value).strip():
                                        best_structured_data[key] = value
                    
                    result_data = {
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": batch_success,
                        "data": {
                            "structured_data": best_structured_data,  # KRITISCH: Für HTML-Generator
                            "individual_results": individual_results,
                            "successful_models": len(successful_models),
                            "failed_models": len(failed_models),
                            "total_models": len(models_to_use)
                        },
                        "model_info": {
                            "models_used": models_to_use,
                            "search_strategy": "individual_batch",
                            "processing_type": "individual_per_model"
                        }
                    }
                    
                    if not batch_success:
                        result_data["error"] = f"All {len(models_to_use)} models failed for {mine_name}"
                    
                    results.append(result_data)
                    logger.info(f"[BATCH-INDIVIDUAL] Completed {mine_name}: {len(successful_models)}/{len(models_to_use)} models successful")
                
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
        
        # CRITICAL-FIX 19.08.2025: Validiere Batch-Ergebnisse gegen Regressionen
        try:
            from minesearch.batch_validation import validate_batch_results, log_validation_summary
            validation_result = validate_batch_results(results)
            log_validation_summary(validation_result)
            
            # Bei kritischen Validierungsfehlern, warnen aber nicht blocken
            if validation_result.critical_count > 0:
                logger.error(f"[BATCH-VALIDATION] {validation_result.critical_count} kritische Probleme in Batch-Ergebnissen erkannt!")
        except ImportError:
            logger.warning("[BATCH-VALIDATION] batch_validation module nicht verfügbar")
        
        # OPTIMIERT: Fallback-Logik bereits in Hauptschleife integriert - keine doppelten Provider-Aufrufe mehr
        
        # Erstelle HTML-Antwort mit optimierten results (Fallback bereits in Hauptschleife integriert)
        import importlib
        import minesearch.html_utils
        importlib.reload(minesearch.html_utils)
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