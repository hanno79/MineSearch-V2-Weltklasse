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
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import CSV_COLUMNS
from batch_service import BatchService
from search_service import MineSearchService
from search_service_multi import MultiProviderSearchService
from providers.registry import provider_registry
from database import db_manager
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
    model: str = Form("sonar-pro"),
    search_type: str = Form("standard"),
    count: Optional[int] = Form(None),
    search_all: Optional[str] = Form("false"),
    selected_models: Optional[str] = Form(None),
    # ÄNDERUNG 07.07.2025: Option für Mehrfach-Durchlauf
    consistency_check: Optional[str] = Form("false"),
    consistency_runs: Optional[int] = Form(3)
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
        
        # ÄNDERUNG 07.07.2025: Session-ID für Batch-Gruppierung in der Datenbank
        # Verwende die gleiche Session-ID wie für den Cache
        
        for idx, mine in enumerate(mines_to_search):
            mine_name = mine.get("mine_name", "")
            country = mine.get("country", "")
            commodity = mine.get("commodity", "")
            region = mine.get("region", "")
            
            if not mine_name:
                continue
                
            logger.info(f"Suche {idx+1}/{len(mines_to_search)}: {mine_name}")
            
            # ÄNDERUNG 07.07.2025: Mehrfach-Durchlauf für Konsistenz
            if consistency_check == "true" and consistency_runs > 1:
                logger.info(f"[CONSISTENCY] Starte {consistency_runs}x Durchlauf für {mine_name}")
                
                # Importiere Konsistenz-Validator
                from consistency_validator import ConsistencyValidator
                validator = ConsistencyValidator()
                
                # Führe mehrere Durchläufe durch
                for run in range(consistency_runs):
                    logger.info(f"[CONSISTENCY] Durchlauf {run+1}/{consistency_runs}")
                    
                    if len(models_to_use) > 1:
                        # Multi-Model-Suche
                        run_result = await multi_search_service.search_with_multiple_models(
                            model_ids=models_to_use,
                            mine_name=mine_name,
                            country=country,
                            commodity=commodity,
                            region=region
                        )
                    else:
                        # Single-Model-Suche
                        run_result = await multi_search_service.search_with_model(
                            model_id=models_to_use[0],
                            mine_name=mine_name,
                            country=country,
                            commodity=commodity,
                            region=region
                        )
                    
                    # Füge Ergebnis zum Validator hinzu
                    if run_result.get('success'):
                        # Bei Multi-Model: Aggregiere zuerst
                        if len(models_to_use) > 1 and 'results' in run_result:
                            # Nutze die gleiche Aggregationslogik wie unten
                            aggregated_data = {}
                            for model_id, model_result in run_result.get('results', {}).items():
                                if model_result.get('success') and model_result.get('data'):
                                    data = model_result['data']
                                    structured_data = data.get('structured_data', data) if isinstance(data, dict) else {}
                                    for field, value in structured_data.items():
                                        if value and not is_placeholder_value(value, field):
                                            aggregated_data[field] = value
                            validator.add_result(aggregated_data)
                        else:
                            # Single-Model: Direkt hinzufügen
                            data = run_result.get('data', {})
                            structured_data = data.get('structured_data', data) if isinstance(data, dict) else {}
                            validator.add_result(structured_data)
                    
                    # Kleine Pause zwischen Durchläufen
                    if run < consistency_runs - 1:
                        await asyncio.sleep(1)
                
                # Validiere Konsistenz
                consistency_result = validator.validate_consistency()
                logger.info(f"[CONSISTENCY] Gesamt-Score: {consistency_result['overall_score']:.2%}")
                logger.info(f"[CONSISTENCY] Konsistent: {consistency_result['consistent']}")
                
                # Hole Konsens-Ergebnis
                consensus = validator.get_consensus_result()
                
                # Erstelle finales Ergebnis mit Konsens-Daten
                result_data = {
                    "mine_name": mine_name,
                    "country": country,
                    "commodity": commodity,
                    "region": region,
                    "success": True,
                    "data": {
                        "structured_data": consensus['consensus_data'],
                        "structured_data_with_sources": {},
                        "sources": [],
                        "source_index": {}
                    },
                    "consistency_info": {
                        "runs": consistency_runs,
                        "overall_score": consistency_result['overall_score'],
                        "consistent": consistency_result['consistent'],
                        "confidence_scores": consensus['confidence_scores'],
                        "average_confidence": consensus['average_confidence']
                    }
                }
                results.append(result_data)
                
                # Speichere in Datenbank mit Konsistenz-Info
                if consensus['consensus_data']:
                    try:
                        db_manager.save_search_result({
                            'session_id': session_id,
                            'mine_name': mine_name,
                            'country': country,
                            'region': region,
                            'commodity': commodity,
                            'model_used': 'consistency_validated',
                            'search_type': 'batch_consistency',
                            'search_duration': None,
                            'structured_data': consensus['consensus_data'],
                            'structured_data_with_sources': {},
                            'sources': [],
                            'source_index': {},
                            'data_quality': {
                                'filled_fields': len([v for v in consensus['consensus_data'].values() if v and str(v).strip()]),
                                'total_fields': len(CSV_COLUMNS),
                                'consistency_score': consistency_result['overall_score'],
                                'confidence_scores': consensus['confidence_scores']
                            },
                            'success': True
                        })
                        logger.info(f"[BATCH-DB] Konsistenz-validiertes Ergebnis für {mine_name} gespeichert")
                    except Exception as db_error:
                        logger.error(f"[BATCH-DB] Fehler beim Speichern: {str(db_error)}")
                
            # Standard-Durchlauf (ohne Konsistenz-Check)
            elif len(models_to_use) > 1:
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
                    
                    # Debug: Log die Struktur
                    logger.info(f"[BATCH-DEBUG] multi_result keys: {list(multi_result.keys())}")
                    logger.info(f"[BATCH-DEBUG] multi_result.success: {multi_result.get('success')}")
                    logger.info(f"[BATCH-DEBUG] multi_result.results keys: {list(multi_result.get('results', {}).keys())}")
                    
                    # Aggregiere beste Ergebnisse aus allen Modellen
                    best_data = {}
                    best_data_with_sources = {}
                    all_sources = []
                    source_index = {}
                    current_source_num = 1
                    
                    for model_id, model_result in multi_result.get('results', {}).items():
                        logger.info(f"[BATCH-DEBUG] {model_id} result keys: {list(model_result.keys())}")
                        logger.info(f"[BATCH-DEBUG] {model_id} success: {model_result.get('success')}")
                        
                        # Flexible Datenextraktion
                        model_data = {}
                        model_data_with_sources = {}
                        
                        # ÄNDERUNG 07.07.2025: Flexiblere Datenextraktion für verschiedene Response-Formate
                        if model_result.get('success') and model_result.get('data'):
                            data = model_result['data']
                            
                            # Prüfe verschiedene Datenstrukturen
                            if isinstance(data, dict):
                                # Option 1: structured_data ist vorhanden
                                if 'structured_data' in data:
                                    logger.info(f"[BATCH-DEBUG] {model_id} hat structured_data in data")
                                    model_data = data.get('structured_data', {})
                                    model_data_with_sources = data.get('structured_data_with_sources', {})
                                # Option 2: Daten sind direkt in data (flaches Dict mit CSV-Spalten)
                                elif any(col in data for col in CSV_COLUMNS):
                                    logger.info(f"[BATCH-DEBUG] {model_id} hat CSV-Spalten direkt in data")
                                    model_data = data
                                    # Versuche auch structured_data_with_sources aus metadata zu holen
                                    if 'metadata' in model_result and 'structured_data_with_sources' in model_result['metadata']:
                                        model_data_with_sources = model_result['metadata']['structured_data_with_sources']
                                # Option 3: Andere Struktur
                                else:
                                    logger.warning(f"[BATCH-DEBUG] {model_id} hat unbekannte Datenstruktur: {list(data.keys())[:5]}")
                        
                        # Fallback: Prüfe ob structured_data direkt in model_result ist
                        elif 'structured_data' in model_result:
                            logger.info(f"[BATCH-DEBUG] {model_id} hat structured_data direkt in model_result")
                            model_data = model_result.get('structured_data', {})
                            model_data_with_sources = model_result.get('structured_data_with_sources', {})
                        
                        if model_data:
                            logger.info(f"[BATCH-DEBUG] {model_id} hat {len(model_data)} Felder in structured_data")
                            # ÄNDERUNG 07.07.2025: Debug - zeige alle extrahierten Felder
                            filled_fields = [(k, v) for k, v in model_data.items() if v and str(v).strip()]
                            logger.info(f"[BATCH-DEBUG] {model_id} gefüllte Felder: {len(filled_fields)}")
                            for field, value in filled_fields[:5]:  # Erste 5 Felder loggen
                                logger.info(f"[BATCH-DEBUG] {model_id} - {field}: '{value[:50]}...' (Länge: {len(str(value))})")
                            
                            # ÄNDERUNG 07.07.2025: Intelligente Feld-Aggregation mit Platzhalter-Erkennung
                            for field, value in model_data.items():
                                if value:
                                    # Debug: Log vor Platzhalter-Check
                                    logger.debug(f"[BATCH-AGG-PRE] Prüfe Feld '{field}' mit Wert '{value}'")
                                    
                                    # Prüfe ob aktueller best_data Wert ein Platzhalter ist
                                    current_value = best_data.get(field, "")
                                    
                                    # Entscheide ob wir den neuen Wert übernehmen
                                    should_update = False
                                    
                                    if not current_value:
                                        # Feld ist leer, neuen Wert übernehmen
                                        should_update = True
                                        logger.debug(f"[BATCH-AGG] Feld '{field}' ist leer, nehme '{value}'")
                                    elif is_placeholder_value(current_value, field):
                                        # Aktueller Wert ist ein Platzhalter
                                        logger.info(f"[BATCH-AGG] Ersetze Platzhalter '{current_value}' mit '{value}' für Feld '{field}'")
                                        should_update = True
                                    elif is_placeholder_value(value, field):
                                        # Neuer Wert ist ein Platzhalter, behalte den alten
                                        logger.info(f"[BATCH-AGG] WARNUNG: '{value}' wurde als Platzhalter für Feld '{field}' erkannt! Behalte '{current_value}'")
                                        should_update = False
                                    else:
                                        # Beide sind echte Werte - behalte den mit mehr Quellen (wenn verfügbar)
                                        current_sources = best_data_with_sources.get(field, {}).get('sources', [])
                                        new_sources = model_data_with_sources.get(field, {}).get('sources', [])
                                        
                                        if len(new_sources) > len(current_sources):
                                            logger.info(f"[BATCH-AGG] Ersetze '{current_value}' mit '{value}' für Feld '{field}' (mehr Quellen)")
                                            should_update = True
                                        else:
                                            logger.debug(f"[BATCH-AGG] Behalte '{current_value}' für Feld '{field}' (gleich viele/mehr Quellen)")
                                    
                                    if should_update:
                                        best_data[field] = value
                                        logger.debug(f"[BATCH-AGG-POST] Feld '{field}' aktualisiert mit '{value}'")
                                        # Übernehme auch die Quellennummern
                                        if field in model_data_with_sources:
                                            best_data_with_sources[field] = model_data_with_sources[field]
                            
                            # Sammle Quellen und erstelle Index - flexible Extraktion
                            sources = []
                            if 'sources' in model_result:
                                sources = model_result.get('sources', [])
                            elif model_result.get('data') and 'sources' in model_result['data']:
                                sources = model_result['data'].get('sources', [])
                            
                            if sources:
                                logger.info(f"[BATCH-DEBUG] {model_id} hat {len(sources)} Quellen")
                                for source in sources:
                                    if source not in all_sources:
                                        all_sources.append(source)
                                        source_index[current_source_num] = source
                                        current_source_num += 1
                        else:
                            logger.info(f"[BATCH-DEBUG] {model_id} hat keine Daten in structured_data")
                    
                    # ÄNDERUNG 09.07.2025: Stelle sicher, dass Minenname und alle CSV-Felder vorhanden sind
                    # Füge Minenname als 'Name' hinzu (CSV-Spaltenname)
                    if 'Name' not in best_data or not best_data.get('Name'):
                        best_data['Name'] = mine_name
                        logger.info(f"[BATCH-FIX] Minenname '{mine_name}' zu structured_data['Name'] hinzugefügt")
                    
                    # Stelle sicher, dass alle CSV-Felder vorhanden sind
                    for csv_field in CSV_COLUMNS:
                        if csv_field not in best_data:
                            best_data[csv_field] = ""
                    
                    logger.info(f"[BATCH-DEBUG] Aggregierte Daten: {len(best_data)} Felder")
                    logger.info(f"[BATCH-DEBUG] Erste 3 Felder: {dict(list(best_data.items())[:3])}")
                    
                    # ÄNDERUNG 07.07.2025: Detailliertes Debug-Logging für aggregierte Felder
                    filled_fields_detail = []
                    placeholder_fields = []
                    empty_fields = []
                    
                    for field, value in best_data.items():
                        if not value or not str(value).strip():
                            empty_fields.append(field)
                        elif is_placeholder_value(value, field):
                            placeholder_fields.append((field, value))
                        else:
                            filled_fields_detail.append((field, value))
                    
                    logger.info(f"[BATCH-DEBUG] Gefüllte Felder ({len(filled_fields_detail)}): {[f[0] for f in filled_fields_detail]}")
                    logger.info(f"[BATCH-DEBUG] Platzhalter-Felder ({len(placeholder_fields)}): {placeholder_fields[:5]}")
                    logger.info(f"[BATCH-DEBUG] Leere Felder ({len(empty_fields)}): {empty_fields[:10]}")
                    
                    # Log einige gefüllte Felder mit Werten
                    for field, value in filled_fields_detail[:5]:
                        logger.info(f"[BATCH-DEBUG] {field}: '{str(value)[:100]}...'")
                    
                    # Ergebnis zur Liste hinzufügen
                    result_data = {
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": bool(best_data),
                        "data": {
                            "structured_data": best_data,
                            "structured_data_with_sources": best_data_with_sources,
                            "sources": all_sources[:20],  # Top 20 Quellen
                            "source_index": source_index
                        }
                    }
                    results.append(result_data)
                    
                    # ÄNDERUNG 07.07.2025: Speichere erfolgreiche Ergebnisse in der Datenbank
                    if result_data["success"] and best_data:
                        try:
                            db_manager.save_search_result({
                                'session_id': session_id,  # Für Batch-Gruppierung
                                'mine_name': mine_name,
                                'country': country,
                                'region': region,
                                'commodity': commodity,
                                'model_used': 'multi_model_batch',
                                'search_type': 'batch_multi',
                                'search_duration': None,  # Könnte später hinzugefügt werden
                                'structured_data': best_data,
                                'structured_data_with_sources': best_data_with_sources,
                                'sources': all_sources[:20],
                                'source_index': source_index,
                                'data_quality': {
                                    'filled_fields': len([v for v in best_data.values() if v and str(v).strip()]),
                                    'total_fields': len(CSV_COLUMNS),
                                    'models_used': len(models_to_use)
                                },
                                'success': True
                            })
                            logger.info(f"[BATCH-DB] Ergebnis für {mine_name} in Datenbank gespeichert")
                        except Exception as db_error:
                            logger.error(f"[BATCH-DB] Fehler beim Speichern in DB für {mine_name}: {str(db_error)}")
                            # Fehler nicht propagieren - Suche soll weiterlaufen
                    
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
                    
                    # Ergebnis zur Liste hinzufügen
                    result_data = {
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": result.get("success", False),
                        "data": result.get("data", {})
                    }
                    
                    # ÄNDERUNG 09.07.2025: Stelle sicher, dass der Minenname in structured_data vorhanden ist
                    if result_data["success"] and result_data.get("data"):
                        structured_data = result_data["data"].get("structured_data", {})
                        if structured_data and ('Name' not in structured_data or not structured_data.get('Name')):
                            structured_data['Name'] = mine_name
                            logger.info(f"[BATCH-FIX] Minenname '{mine_name}' zu Single-Model structured_data['Name'] hinzugefügt")
                    
                    results.append(result_data)
                    
                    # ÄNDERUNG 07.07.2025: Speichere erfolgreiche Single-Model Ergebnisse in der Datenbank
                    if result_data["success"] and result_data.get("data"):
                        try:
                            data = result_data["data"]
                            structured_data = data.get("structured_data", {})
                            
                            if structured_data:  # Nur speichern wenn Daten vorhanden
                                db_manager.save_search_result({
                                    'session_id': session_id,  # Für Batch-Gruppierung
                                    'mine_name': mine_name,
                                    'country': country,
                                    'region': region,
                                    'commodity': commodity,
                                    'model_used': model_id,
                                    'search_type': 'batch_single',
                                    'search_duration': result.get('duration'),
                                    'structured_data': structured_data,
                                    'structured_data_with_sources': data.get('structured_data_with_sources', {}),
                                    'sources': data.get('sources', []),
                                    'source_index': data.get('source_index', {}),
                                    'data_quality': data.get('data_quality', {
                                        'filled_fields': len([v for v in structured_data.values() if v and str(v).strip()]),
                                        'total_fields': len(CSV_COLUMNS)
                                    }),
                                    'success': True
                                })
                                logger.info(f"[BATCH-DB] Single-Model Ergebnis für {mine_name} in Datenbank gespeichert")
                        except Exception as db_error:
                            logger.error(f"[BATCH-DB] Fehler beim Speichern in DB für {mine_name}: {str(db_error)}")
                            # Fehler nicht propagieren - Suche soll weiterlaufen
                    
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
            if 'data' in first_result:
                logger.info(f"[BATCH-DEBUG] Data Keys: {list(first_result['data'].keys())}")
                if 'structured_data' in first_result['data']:
                    logger.info(f"[BATCH-DEBUG] Structured Data Keys: {list(first_result['data']['structured_data'].keys())}")
                    logger.info(f"[BATCH-DEBUG] Structured Data Sample: {dict(list(first_result['data']['structured_data'].items())[:3])}")
        
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
        
        # Debug: Log einen Teil des generierten HTML
        logger.info(f"[BATCH-DEBUG] HTML-Länge: {len(html_content)}")
        logger.info(f"[BATCH-DEBUG] HTML-Anfang: {html_content[:200]}...")
        
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