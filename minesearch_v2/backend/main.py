"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: MineSearch 2.0 - Radikal vereinfachtes Mining-Recherche-System
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Response, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import os
import asyncio
from datetime import datetime
import logging
from config import config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
import csv
import io
import re

# ÄNDERUNG 01.07.2025: Import der refactorierten Module zur Code-Vereinfachung
from data_extraction import DataExtractor, extract_structured_data_with_sources
from search_service import MineSearchService
from source_discovery import extract_sources_from_content
from batch_service import BatchService
from html_utils import create_result_card, create_error_card, create_batch_results_table
from utils import (
    normalize_accents, 
    generate_name_variants, 
    clean_extracted_value,
    get_country_config,
    generate_multilingual_search_terms
)

# Logging auf Deutsch
logging.basicConfig(
    level=logging.INFO,  # ÄNDERUNG 28.06.2025: Zurück auf INFO nach erfolgreicher Implementierung
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Temporärer Speicher für CSV-Daten (in Production würde man Redis/DB nutzen)
uploaded_mines_cache = {}

# ÄNDERUNG 28.06.2025: Cache für Batch-Ergebnisse zum Download
batch_results_cache = {}

# ÄNDERUNG 01.07.2025: Initialisiere Services aus den refactorierten Modulen
mine_search_service = MineSearchService()
data_extractor = DataExtractor()
batch_service = BatchService(uploaded_mines_cache, batch_results_cache)

# ÄNDERUNG 01.07.2025: CSV_COLUMNS und FIELDS_WITHOUT_SOURCES aus config.py importiert

# FastAPI App
app = FastAPI(
    title="MineSearch 2.0",
    description="Einfaches Mining-Recherche-System mit Perplexity API",
    version="2.0.0"
)

# Statische Dateien f�r Frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Request/Response Modelle
class MineSearchRequest(BaseModel):
    mine_name: str
    country: Optional[str] = None
    commodity: Optional[str] = None
    region: Optional[str] = None

class MineSearchResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()
    search_query: str

# Perplexity API Konfiguration aus config.py
PERPLEXITY_API_KEY = config.PERPLEXITY_API_KEY
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Root Route - serviert die HTML Seite
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Hauptseite mit Suchformular"""
    try:
        with open("../frontend/index.html", "rb") as f:
            content = f.read()
            # Versuche verschiedene Encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # Fallback: Ignoriere fehlerhafte Zeichen
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Fehler beim Laden der HTML-Datei: {e}")
        return "<h1>Fehler beim Laden der Seite</h1>"

# ÄNDERUNG 01.07.2025: Hilfsfunktionen aus utils.py verwenden statt Duplikate

# ÄNDERUNG 01.07.2025: get_country_config und generate_multilingual_search_terms aus utils.py verwenden

# ÄNDERUNG 01.07.2025: generate_name_variants aus utils.py verwenden

# ÄNDERUNG 01.07.2025: extract_structured_data_with_sources aus data_extraction.py verwenden

# Haupt-Such-Endpoint
@app.post("/api/search", response_model=MineSearchResponse)
async def search_mine(request: MineSearchRequest, model: str = "sonar-pro"):
    """
    Sucht nach Mining-Informationen über Perplexity API.
    ÄNDERUNG 01.07.2025: Nutzt jetzt den refactorierten MineSearchService
    """
    try:
        # Delegiere an den MineSearchService
        result = await mine_search_service.search_mine(
            mine_name=request.mine_name,
            country=request.country,
            commodity=request.commodity,
            model=model,
            region=request.region
        )
        return MineSearchResponse(**result)
    except ValueError as e:
        logger.error(f"Fehler bei der Suche: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler")
@app.post("/api/upload-csv")
async def upload_csv(csv_file: UploadFile = File(...)):
    """
    CSV Datei hochladen und analysieren.
    ÄNDERUNG 01.07.2025: Nutzt jetzt den BatchService
    """
    return await batch_service.process_csv_upload(csv_file)

# Batch Search Endpoint
@app.post("/api/batch-search")
async def batch_search(
    session_id: str = Form(...),
    model: str = Form("sonar-pro"),
    search_type: str = Form("standard"),  # Neu: standard oder enhanced
    count: Optional[int] = Form(None),
    search_all: Optional[str] = Form("false")
):
    """
    Batch-Suche für mehrere Minen aus CSV.
    """
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
        
        # Führe Suchen durch
        results = []
        errors = []
        
        for i, mine in enumerate(mines_to_search):
            logger.info(f"Batch-Suche {i+1}/{len(mines_to_search)}: {mine['mine_name']}")
            
            try:
                # Nutze existierende search_mine Funktion mit gewähltem Modell
                request = MineSearchRequest(**mine)
                
                # ÄNDERUNG 28.06.2025: Unterstützung für erweiterte Suche
                # Verwende IMMER das gewählte Modell
                if search_type == "enhanced" and model != "sonar-deep-research":
                    # 2-Phasen-Suche mit dem gewählten Modell
                    result = await enhanced_search(request, model=model)
                else:
                    # Normale Suche mit gewähltem Modell (auch für Deep Research)
                    result = await search_mine(request, model=model)
                
                if result.success:
                    results.append({
                        'mine': mine,
                        'data': result.data
                    })
                else:
                    errors.append({
                        'mine': mine,
                        'error': result.error
                    })
                    
                # Kleine Pause zwischen Requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                errors.append({
                    'mine': mine,
                    'error': str(e)
                })
        
        # ÄNDERUNG 01.07.2025: Nutze BatchService für Speicherung
        batch_service.save_batch_results(session_id, results, errors, model)
        
        # ÄNDERUNG 01.07.2025: Nutze create_batch_results_table aus html_utils
        csv_table_html = create_batch_results_table(results) if results else ""
        
        # Erstelle HTML Response
        html_response = f"""
        <div class="batch-results">
            <h3>Batch-Suche abgeschlossen</h3>
            <p>✓ {len(results)} erfolgreich | ❌ {len(errors)} Fehler</p>
            
            <!-- ÄNDERUNG 28.06.2025: Download-Button hinzufügen -->
            <div style="margin: 20px 0;">
                <button onclick="downloadResults('{session_id}')" 
                        style="background: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                    📥 Ergebnisse als CSV herunterladen (mit Quellenreferenzen)
                </button>
                <script>
                    function downloadResults(sessionId) {{
                        window.location.href = '/api/download-results?session_id=' + sessionId;
                    }}
                </script>
            </div>
            
            {csv_table_html}
            
            <div class="results-container">
                <h4 style="margin-top: 30px;">📋 Detaillierte Einzelergebnisse:</h4>
                {"".join([create_result_card(r) for r in results])}
                {"".join([create_error_card(e) for e in errors])}
            </div>
        </div>
        """
        
        return HTMLResponse(content=html_response)
        
    except ValueError as e:
        logger.error(f"Wert-Fehler bei Batch-Suche: {e}")
        return HTMLResponse(
            content=f'<div class="result-card error"><h3>❌ Fehler bei Batch-Suche</h3><p>{str(e)}</p><p><small>Tipp: Laden Sie die CSV-Datei erneut hoch.</small></p></div>'
        )
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei Batch-Suche: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<div class="result-card error"><h3>❌ Fehler bei Batch-Suche</h3><p>Ein unerwarteter Fehler ist aufgetreten: {str(e)}</p></div>'
        )

# Zwei-Phasen-Suche Endpoint
@app.post("/api/enhanced-search")
async def enhanced_search(request: MineSearchRequest, model: str = Query("sonar-pro")):
    """
    Erweiterte Zwei-Phasen-Suche für umfangreichere Ergebnisse.
    ÄNDERUNG 01.07.2025: Nutzt jetzt den MineSearchService
    """
    try:
        result = await mine_search_service.enhanced_search(
            mine_name=request.mine_name,
            country=request.country,
            commodity=request.commodity,
            model=model,
            region=request.region
        )
        return MineSearchResponse(**result)
    except Exception as e:
        logger.error(f"Fehler bei erweiterter Suche: {str(e)}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler")

# ÄNDERUNG 28.06.2025: Download-Endpoint für CSV-Export
@app.get("/api/download-results")
async def download_results(session_id: str):
    """
    Download alle Suchergebnisse einer Session als CSV.
    ÄNDERUNG 01.07.2025: Nutzt jetzt BatchService
    """
    try:
        csv_content = batch_service.get_csv_download_content(session_id)
        filename = f"minesearch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Favicon Route (verhindert 404 Fehler)
@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors"""
    return Response(status_code=204)  # No Content

# Chrome DevTools Route (verhindert 404 Fehler)
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
    """Return empty JSON for Chrome DevTools"""
    return {"configVersion": 1.0, "configurations": []}

# Health Check
@app.get("/health")
async def health_check():
    """System Status Check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api_key_configured": bool(PERPLEXITY_API_KEY),
        "timestamp": datetime.now()
    }

# Lifespan Context Manager für moderne FastAPI Version
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisierung beim Start"""
    logger.info("MineSearch 2.0 gestartet")
    logger.info(f"Konfiguration: {config.get_summary()}")
    
    try:
        config.validate()
        logger.info("Konfiguration validiert - alle Systeme bereit")
    except ValueError as e:
        logger.error(f"Konfigurationsfehler: {e}")
        logger.warning("System startet trotzdem - bitte Konfiguration prüfen!")
    
    yield
    
    # Cleanup beim Shutdown
    logger.info("MineSearch 2.0 beendet")

# App mit Lifespan erstellen
app.router.lifespan_context = lifespan

# Smart-Search Endpoint mit automatischem Fallback
@app.post("/api/smart-search")
async def smart_search(request: MineSearchRequest, auto_upgrade: bool = True):
    """
    Intelligente Suche mit automatischem Modell-Upgrade bei schlechten Ergebnissen
    
    1. Startet mit schnellem Modell (sonar)
    2. Wenn Datenqualität < 40%: Automatisch Standard-Modell (sonar-pro)
    3. Transparente Rückmeldung über Suchverlauf
    """
    search_history = []
    
    # Phase 1: Schnelle Suche
    logger.info(f"Smart-Search Phase 1: Schnelle Suche für {request.mine_name}")
    phase1_result = await search_mine(request, model="sonar")
    search_history.append({
        "phase": 1,
        "model": "sonar",
        "model_name": "Schnell",
        "duration": "30 Sekunden"
    })
    
    if not phase1_result.success or not phase1_result.data:
        return phase1_result
    
    # Prüfe Datenqualität
    data_quality = phase1_result.data.get('data_quality', {})
    completeness = data_quality.get('completeness_percentage', 0)
    
    # Phase 2: Automatisches Upgrade wenn nötig und erlaubt
    if auto_upgrade and completeness < 40:
        logger.info(f"Smart-Search Phase 2: Datenqualität nur {completeness}% - Upgrade auf Standard-Modell")
        
        # Informiere Frontend über Upgrade
        phase1_result.data['search_status'] = {
            "upgrading": True,
            "reason": f"Nur {completeness}% der Daten gefunden",
            "next_model": "Standard (60 Sekunden)"
        }
        
        # Führe erweiterte Suche durch
        phase2_result = await search_mine(request, model="sonar-pro")
        search_history.append({
            "phase": 2,
            "model": "sonar-pro",
            "model_name": "Standard",
            "duration": "60 Sekunden",
            "reason": "Automatisches Upgrade wegen niedriger Datenqualität"
        })
        
        if phase2_result.success and phase2_result.data:
            # Füge Suchverlauf hinzu
            phase2_result.data['search_history'] = search_history
            phase2_result.data['search_summary'] = f"Suche automatisch erweitert: Schnell → Standard (Datenqualität verbessert von {completeness}% auf {phase2_result.data.get('data_quality', {}).get('completeness_percentage', 0)}%)"
            return phase2_result
    
    # Füge Suchverlauf zur ursprünglichen Antwort hinzu
    phase1_result.data['search_history'] = search_history
    if completeness < 40:
        phase1_result.data['recommendation'] = "Empfehlung: Verwenden Sie die erweiterte Suche oder Deep Research für bessere Ergebnisse"
    
    return phase1_result

if __name__ == "__main__":
    import uvicorn
    # ÄNDERUNG 29.06.2025: Fix für reload warning
    if config.DEBUG:
        uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
    else:
        uvicorn.run(app, host=config.HOST, port=config.PORT)