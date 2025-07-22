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
    FIXED 14.07.2025: Flexible Model Parameter für Frontend-Kompatibilität
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
        
        # FIXED 14.07.2025: Robuste Model-Auswahl mit Fallback
        models_to_use = []
        if selected_models:
            # Parse comma-separated model list
            models_to_use = [m.strip() for m in selected_models.split(',') if m.strip()]
            logger.info(f"Verwende ausgewählte Modelle aus Frontend: {models_to_use}")
        elif model:
            # Fallback auf einzelnes Modell
            models_to_use = [model]
            logger.info(f"Verwende einzelnes Modell: {model}")
        else:
            # ÄNDERUNG 14.07.2025: Kimi K2 als Default-Modell für beste Performance
            models_to_use = ["openrouter:kimi-k2"]
            logger.warning(f"Kein Modell angegeben, verwende Default: {models_to_use[0]}")
        
        if not models_to_use:
            raise ValueError("Mindestens ein Modell muss ausgewählt werden")
        
        # Führe Suchen durch
        results = []
        
        # Multi-Provider Search Service für alle Modelle mit Provider-Präfix
        multi_search_service = MultiProviderSearchService()
        
        # PHASE 2.3: COMPREHENSIVE SEARCH ORCHESTRATOR Integration
        from comprehensive_search_orchestrator import comprehensive_search_orchestrator
        
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
                # Standard-Suche mit ausgewählten Modellen
                if len(models_to_use) > 1:
                    # Multi-Model-Suche
                    result = await multi_search_service.search_with_multiple_models(
                        model_ids=models_to_use,
                        mine_name=mine_name,
                        country=country,
                        commodity=commodity,
                        region=region
                    )
                else:
                    # Single-Model-Suche
                    result = await multi_search_service.search_with_model(
                        model_id=models_to_use[0],
                        mine_name=mine_name,
                        country=country,
                        commodity=commodity,
                        region=region
                    )
                # Führe Standard-Suche durch
                if len(models_to_use) > 1:
                    # Multi-Model-Suche
                    result = await multi_search_service.search_with_multiple_models(
                        model_ids=models_to_use,
                        mine_name=mine_name,
                        country=country,
                        commodity=commodity,
                        region=region
                    )
                else:
                    # Single-Model-Suche
                    result = await multi_search_service.search_with_model(
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
                        logger.info(f"[BATCH-DEBUG] {model_id} result keys: {list(model_result.keys())}")
                        logger.info(f"[BATCH-DEBUG] {model_id} success: {model_result.get('success')}")
                        logger.info(f"[BATCH-DEBUG] {model_id} result type: {type(model_result)}")
                        
                        # Log detaillierte Struktur für fehlerhafte Modelle
                        if not model_result.get('success'):
                            logger.warning(f"[BATCH-DEBUG] {model_id} FAILED - Error: {model_result.get('error', 'Unknown error')}")
                            logger.info(f"[BATCH-DEBUG] {model_id} complete failed result: {model_result}")
                        
                        # Flexible Datenextraktion
                        model_data = {}
                        model_data_with_sources = {}
                        
                        # FIXED 15.07.2025: Robuste Datenextraktion für verschiedene Response-Formate
                        if model_result.get('success'):
                            logger.info(f"[BATCH-DEBUG] {model_id} ist erfolgreich, extrahiere Daten...")
                            
                            # Option 1: Daten in model_result['data']['structured_data']
                            if model_result.get('data') and isinstance(model_result['data'], dict):
                                data = model_result['data']
                                logger.info(f"[BATCH-DEBUG] {model_id} data keys: {list(data.keys())}")
                                
                                if 'structured_data' in data:
                                    logger.info(f"[BATCH-DEBUG] {model_id} hat structured_data in data")
                                    model_data = data.get('structured_data', {})
                                    model_data_with_sources = data.get('structured_data_with_sources', {})
                                # Prüfe ob data direkt die CSV-Spalten enthält
                                elif any(col in data for col in CSV_COLUMNS):
                                    logger.info(f"[BATCH-DEBUG] {model_id} hat CSV-Spalten direkt in data")
                                    model_data = data
                                    model_data_with_sources = data.get('structured_data_with_sources', {})
                                else:
                                    logger.warning(f"[BATCH-DEBUG] {model_id} unbekannte data-Struktur: {list(data.keys())[:5]}")
                            
                            # Option 2: structured_data direkt in model_result
                            elif 'structured_data' in model_result:
                                logger.info(f"[BATCH-DEBUG] {model_id} hat structured_data direkt in model_result")
                                model_data = model_result.get('structured_data', {})
                                model_data_with_sources = model_result.get('structured_data_with_sources', {})
                            
                            # Option 3: CSV-Spalten direkt in model_result
                            elif any(col in model_result for col in CSV_COLUMNS):
                                logger.info(f"[BATCH-DEBUG] {model_id} hat CSV-Spalten direkt in model_result")
                                model_data = {col: model_result.get(col, '') for col in CSV_COLUMNS}
                                model_data_with_sources = model_result.get('structured_data_with_sources', {})
                            
                            # Option 4: Fallback - suche in allen Ebenen
                            else:
                                logger.warning(f"[BATCH-DEBUG] {model_id} FALLBACK: Durchsuche alle Ebenen")
                                logger.info(f"[BATCH-DEBUG] {model_id} model_result keys: {list(model_result.keys())}")
                                
                                # Versuche verschiedene Strukturen zu finden
                                for key in ['data', 'result', 'response']:
                                    if key in model_result and isinstance(model_result[key], dict):
                                        potential_data = model_result[key]
                                        if any(col in potential_data for col in CSV_COLUMNS):
                                            logger.info(f"[BATCH-DEBUG] {model_id} Daten in {key} gefunden")
                                            model_data = potential_data
                                            break
                                
                                # Wenn immer noch keine Daten gefunden, leere Struktur
                                if not model_data:
                                    logger.error(f"[BATCH-DEBUG] {model_id} KEINE DATEN GEFUNDEN! Erstelle leere Struktur")
                                    model_data = {col: '' for col in CSV_COLUMNS}
                        
                        else:
                            logger.info(f"[BATCH-DEBUG] {model_id} nicht erfolgreich, überspringe Datenextraktion")
                        
                        # FIXED 15.07.2025: Verbesserte Fehlerbehandlung und Datenverarbeitung
                        if model_data:
                            logger.info(f"[BATCH-DEBUG] {model_id} hat {len(model_data)} Felder in structured_data")
                            # Debug - zeige alle extrahierten Felder
                            filled_fields = [(k, v) for k, v in model_data.items() if v and str(v).strip()]
                            logger.info(f"[BATCH-DEBUG] {model_id} gefüllte Felder: {len(filled_fields)}")
                            for field, value in filled_fields[:5]:  # Erste 5 Felder loggen
                                logger.info(f"[BATCH-DEBUG] {model_id} - {field}: '{str(value)[:50]}...' (Länge: {len(str(value))})")
                            
                            # Intelligente Feld-Aggregation mit Platzhalter-Erkennung
                            successful_aggregation = 0
                            for field, value in model_data.items():
                                if value and str(value).strip():
                                    try:
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
                                            successful_aggregation += 1
                                            logger.debug(f"[BATCH-AGG-POST] Feld '{field}' aktualisiert mit '{value}'")
                                            # Übernehme auch die Quellennummern
                                            if field in model_data_with_sources:
                                                best_data_with_sources[field] = model_data_with_sources[field]
                                    
                                    except Exception as agg_error:
                                        logger.error(f"[BATCH-AGG] Fehler bei Aggregation von Feld '{field}': {str(agg_error)}")
                                        continue
                            
                            logger.info(f"[BATCH-DEBUG] {model_id} erfolgreich aggregiert: {successful_aggregation} Felder")
                            
                            # Sammle Quellen und erstelle Index - flexible Extraktion
                            try:
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
                            except Exception as source_error:
                                logger.error(f"[BATCH-DEBUG] Fehler bei Quellen-Extraktion für {model_id}: {str(source_error)}")
                        
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
                    # ÄNDERUNG 09.07.2025: Berechne data_quality für result_data
                    filled_fields = len([v for v in best_data.values() if v and str(v).strip() and not is_placeholder_value(v, '')])
                    total_fields = len(CSV_COLUMNS)
                    completeness_percentage = (filled_fields / total_fields * 100) if total_fields > 0 else 0
                    
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
                            "source_index": source_index,
                            "data_quality": {
                                "filled_fields": filled_fields,
                                "total_fields": total_fields,
                                "completeness_percentage": completeness_percentage,
                                "score": completeness_percentage / 100  # Normalisiert auf 0-1
                            }
                        }
                    }
                    results.append(result_data)
                    
                    # MIKRO-TASK 1 FIX 15.07.2025: Korrekte Parameter für save_search_result()
                    if result_data["success"] and best_data:
                        try:
                            # Verwende die korrekte Methodensignatur: save_search_result(mine_name, model_used, structured_data, sources, session_id, **kwargs)
                            db_manager.save_search_result(
                                mine_name=mine_name,
                                model_used='multi_model_batch',
                                structured_data=best_data,
                                sources=all_sources[:20],
                                session_id=session_id,
                                # Additional kwargs
                                country=country,
                                region=region,
                                commodity=commodity,
                                search_type='batch_multi',
                                search_duration=None,
                                structured_data_with_sources=best_data_with_sources,
                                source_index=source_index,
                                data_quality={
                                    'filled_fields': len([v for v in best_data.values() if v and str(v).strip()]),
                                    'total_fields': len(CSV_COLUMNS),
                                    'models_used': len(models_to_use)
                                },
                                success=True
                            )
                            logger.info(f"[BATCH-DB] Ergebnis für {mine_name} in Datenbank gespeichert")
                        except Exception as db_error:
                            logger.error(f"[BATCH-DB] Fehler beim Speichern in DB für {mine_name}: {str(db_error)}")
                            # MIKRO-TASK 2 FIX 15.07.2025: Defensive Behandlung für DB-Parameter
                            try:
                                # Fallback mit minimalen Parametern
                                db_manager.save_search_result(
                                    mine_name=mine_name,
                                    model_used='multi_model_batch_fallback',
                                    structured_data=best_data or {},
                                    sources=all_sources[:5] if all_sources else []
                                )
                                logger.info(f"[BATCH-DB] Fallback-Speicherung für {mine_name} erfolgreich")
                            except Exception as fallback_error:
                                logger.error(f"[BATCH-DB] Auch Fallback-Speicherung für {mine_name} fehlgeschlagen: {str(fallback_error)}")
                            # Fehler nicht propagieren - Suche soll weiterlaufen
                    
                except Exception as e:
                    logger.error(f"Fehler bei Multi-Model-Suche für {mine_name}: {str(e)}")
                    # MIKRO-TASK 6 FIX 15.07.2025: Robuste Batch-Verarbeitung - Einzelfehler isolieren
                    logger.error(f"[BATCH-ROBUST] Mine {mine_name} fehlgeschlagen: {str(e)}")
                    logger.info(f"[BATCH-ROBUST] Setze Batch-Verarbeitung mit verbleidenden {len(mines_to_search) - mines_to_search.index({'mine_name': mine_name, 'country': country, 'region': region, 'commodity': commodity}) - 1} Minen fort")
                    
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