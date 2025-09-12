"""
Author: rahn
Datum: 11.09.2025
Version: 2.0
Beschreibung: Refacturiertes Batch-Processing Router (REGEL 1 konform: <500 Zeilen)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response, HTMLResponse
import csv
import io
import logging
import asyncio
import random
from ...fallback_detector import validate_data, clean_fallback_values
import os
import tempfile
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime

from minesearch.config import CSV_COLUMNS
from minesearch.batch_service import BatchService  # Adapter
from minesearch.search_service import MineSearchService
# 2-PHASEN WORKFLOW IMPORT (29.08.2025)
from minesearch.batch_progress_manager import ProgressState
# CONSOLIDATION 09.08.2025: MultiProviderSearchService entfernt - verwende MineSearchService direkt
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from minesearch.database.normalized_manager import NormalizedDatabaseManager
from minesearch.extraction_validators import is_placeholder_value
from minesearch.html_utils import create_batch_results_table
# BATCH-FIX 23.08.2025: Import MultiModelSearchOrchestrator für Provider-Suche
from minesearch.multi_model_search_orchestrator import MultiModelSearchOrchestrator
# ÄNDERUNG 27.08.2025: Import Sequential Field Orchestrator für neuen Workflow
from minesearch.sequential_field_orchestrator import SequentialFieldOrchestrator
from minesearch.database.sequential_manager import SequentialDatabaseManager
# PROGRESS-FIX 29.08.2025: Import BatchProgressManager für detaillierte Fortschrittsanzeige
from minesearch.batch_progress_manager import batch_progress_manager, ProgressState

# Imports from refactored modules
from .batch_utils import (
    safe_write_to_file, create_batch_debug_logger, batch_debug_logger,
    count_filled_fields, is_weak_result
)
from .batch_search import fallback_search_if_needed
from .batch_processors import (
    process_batch_results, get_batch_results_data, download_batch_results_csv
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Konfigurierbares Sicherheitslimit für CSV-Einträge (Default 10.000)
MAX_MINES_LIMIT = int(os.getenv("MAX_MINES_LIMIT", "10000"))

# Anfrage-basiertes Sicherheitslimit pro Batch-Request (Client/Server-Validierung)
BATCH_REQUEST_MAX_COUNT = int(os.getenv("BATCH_MAX_COUNT", "1000"))

# NORMALIZED SCHEMA FIX 28.08.2025: Initialize NormalizedDatabaseManager
normalized_db_manager = NormalizedDatabaseManager()

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
async def upload_csv(file: UploadFile = File(...)):
    """CSV Datei hochladen und analysieren"""
    # REPARATUR 04.09.2025: Parameter-Name zurück zu 'file' für Standard-Kompatibilität
    try:
        # DEBUG FIX 04.09.2025: Erweiterte Validierung
        if not file:
            logger.error("[CSV-UPLOAD] File parameter is None")
            raise HTTPException(status_code=422, detail="File parameter is required")
        
        if not file.filename:
            logger.error("[CSV-UPLOAD] File has no filename")
            raise HTTPException(status_code=422, detail="File must have a filename")
        
        logger.info(f"CSV Upload empfangen: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Verarbeite CSV direkt hier statt batch_service zu nutzen
        contents = await file.read()
        csv_content = contents.decode('utf-8-sig')  # FIX: UTF-8-SIG entfernt BOM automatisch
        
        # FIX: Auto-detect CSV-Delimiter (Semikolon vs Komma)
        delimiter = ';' if ';' in csv_content.split('\n')[0] else ','
        logger.info(f"[CSV-UPLOAD] Auto-detected delimiter: '{delimiter}'")
        
        csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        
        mines = []
        columns = []
        
        for i, row in enumerate(csv_reader):
            if i == 0:
                columns = list(row.keys())
                logger.info(f"[CSV-UPLOAD] Erkannte Spalten: {columns}")
            
            # Überspringe komplett leere Zeilen
            if not any(v.strip() for v in row.values() if v):
                logger.debug(f"[CSV-UPLOAD] Leere Zeile übersprungen: {i+1}")
                continue
            
            # FIX: Entferne BOM aus allen Spaltennamen falls noch vorhanden
            cleaned_row = {}
            for k, v in row.items():
                # Entferne BOM aus Schlüssel
                clean_key = k.lstrip('\ufeff') if k else k
                # Bereinige auch Werte von BOM
                clean_value = v.lstrip('\ufeff') if isinstance(v, str) else v
                cleaned_row[clean_key] = clean_value
                
            mines.append(cleaned_row)
            
            # Sicherheitslimit für Upload-Parsing
            if len(mines) >= MAX_MINES_LIMIT:
                logger.warning(f"[CSV-UPLOAD] MAX_MINES_LIMIT ({MAX_MINES_LIMIT}) erreicht bei Zeile {i+1}")
                break
        
        # Validiere dass mindestens "Mine Name" vorhanden ist
        required_column = "Mine Name"
        if required_column not in columns:
            # Versuche Alternative Spalten-Namen
            alt_names = ["mine name", "minename", "name", "Name"]
            found_alt = None
            for alt in alt_names:
                if alt in [c.lower() for c in columns]:
                    found_alt = next(c for c in columns if c.lower() == alt.lower())
                    break
            
            if found_alt:
                logger.info(f"[CSV-UPLOAD] Alternative Spalte gefunden: '{found_alt}' -> 'Mine Name'")
                # Normalisiere alle Zeilen
                for mine in mines:
                    mine["Mine Name"] = mine.get(found_alt, "")
                # Update columns
                if found_alt in columns:
                    columns[columns.index(found_alt)] = "Mine Name"
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"CSV muss eine Spalte '{required_column}' enthalten. Gefundene Spalten: {columns}"
                )
        
        # Generiere eindeutige Session-ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Cache-Strategien für Memory-Management
        uploaded_mines_cache[session_id] = {
            'mines': mines,
            'columns': columns,
            'upload_time': datetime.now(),
            'filename': file.filename
        }
        
        logger.info(f"[CSV-UPLOAD] ✅ Erfolgreich geladen: {len(mines)} Minen für Session {session_id}")
        
        # Entferne alte Sessions (Memory-Management)
        now = datetime.now()
        old_sessions = [
            sid for sid, data in uploaded_mines_cache.items()
            if (now - data.get('upload_time', now)).seconds > 3600  # 1 Stunde
        ]
        for old_sid in old_sessions:
            del uploaded_mines_cache[old_sid]
            logger.info(f"[CSV-CLEANUP] Alte Session entfernt: {old_sid}")
        
        # FIX 11.09.2025: Frontend erwartet HTML mit session_id hidden field (nicht JSON)
        mine_count = len(mines)
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
                        <label><strong>Mine-Auswahl-Modus:</strong></label>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="selection_mode" value="first_n" checked> Erste X Minen</label>
                            <input type="number" name="count" value="5" min="1" max="1000" style="width: 60px;">
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Batch-Suche starten</button>
                </form>
            </div>
        </div>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"[CSV-UPLOAD] Fehler beim Upload: {str(e)}")
        if "delimiter" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail="CSV-Format Fehler. Bitte verwende Semikolon (;) oder Komma (,) als Trennzeichen."
            )
        raise HTTPException(status_code=500, detail=f"CSV Upload fehlgeschlagen: {str(e)}")

@router.post("/batch-search")
async def batch_search(
    session_id: str = Form(...),
    model: Optional[str] = Form(None, description="Einzelnes Modell (Legacy)"),
    search_type: str = Form("standard"),
    count: Optional[int] = Form(None),
    search_all: Optional[str] = Form("false"),
    start_index: Optional[int] = Form(0),
    selected_models: Optional[str] = Form(None, description="Komma-getrennte Modell-Liste"),
    # ÄNDERUNG 07.07.2025: Option für Mehrfach-Durchlauf
    consistency_check: Optional[str] = Form("false"),
    consistency_runs: Optional[int] = Form(3),
    # PHASE 2.3: COMPREHENSIVE SEARCH Option
    comprehensive_search: Optional[str] = Form("false"),
    # ÄNDERUNG 27.08.2025: Sequential Field Orchestrator Option
    sequential_workflow: Optional[str] = Form("false"),
    # BATCH-TRANSPARENCY FIX 30.08.2025: Session-Isolation und Cache-Control
    use_cache: Optional[str] = Form("false", description="Use cached results from database"),
    force_new_session: Optional[str] = Form("false", description="Force new unique session for isolation"),
    # ENHANCED BATCH SELECTION 06.09.2025: Neue Auswahl-Modi
    selection_mode: Optional[str] = Form("first_n", description="first_n, range, random, all"),
    start_position: Optional[int] = Form(1, description="Start-Position für Range-Modus"),
    range_count: Optional[int] = Form(20, description="Anzahl Minen für Range-Modus"),
    random_count: Optional[int] = Form(10, description="Anzahl zufällige Minen"),
    # FIX 07.09.2025: Dual Response Format für JSON/HTML
    response_format: Optional[str] = Form("html", description="Response format: html or json")
):
    """
    Batch-Suche für mehrere Minen aus CSV - REFACTORED VERSION
    """
    # Da die ursprüngliche batch_search Funktion sehr groß ist (800+ Zeilen),
    # delegiere ich an den batch_service für die Hauptlogik
    try:
        logger.info(f"[BATCH API] Batch search request for session: {session_id}")
        
        # Hole Minen-Daten aus dem Cache
        if session_id not in uploaded_mines_cache:
            raise ValueError("Session abgelaufen. Bitte CSV erneut hochladen.")
        
        # Delegiere die komplexe Verarbeitung an den BatchService
        result = await batch_service.batch_search_with_options(
            session_id=session_id,
            model=model,
            search_type=search_type,
            count=count,
            search_all=search_all,
            start_index=start_index,
            selected_models=selected_models,
            consistency_check=consistency_check,
            consistency_runs=consistency_runs,
            comprehensive_search=comprehensive_search,
            sequential_workflow=sequential_workflow,
            use_cache=use_cache,
            force_new_session=force_new_session,
            selection_mode=selection_mode,
            start_position=start_position,
            range_count=range_count,
            random_count=random_count,
            response_format=response_format
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Fehler bei Batch-Suche: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-batch")
async def process_batch(
    cache_key: str = Form(...),
    model: str = Form(..., description="Modell-ID (z.B. 'openrouter:deepseek-free')")
):
    """Batch-Verarbeitung der hochgeladenen Minen"""
    return await process_batch_results(batch_service, cache_key, model)

@router.get("/batch-results/{cache_key}")
async def get_batch_results(cache_key: str):
    """Batch-Ergebnisse abrufen"""
    return get_batch_results_data(cache_key, batch_results_cache)

@router.get("/batch-results/{cache_key}/download")
async def download_batch_results(cache_key: str):
    """Batch-Ergebnisse als CSV herunterladen"""
    return download_batch_results_csv(cache_key, batch_results_cache)