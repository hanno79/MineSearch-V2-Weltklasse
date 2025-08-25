#!/usr/bin/env python3
"""
KRITISCHER FIX: Komplette DB-First Batch-API Route
Die original Route hat zu viele verschachtelte Code-Pfade.
Diese neue Version ist sauber und verwendet DB-Ergebnisse zuerst.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
import logging
import json
import csv
import io
import uuid
from cachetools import TTLCache
from datetime import datetime
from minesearch.search_utils import count_filled_fields

logger = logging.getLogger(__name__)

def create_fixed_batch_route(db_manager, batch_results_cache):
    """Erstelle eine saubere DB-First Batch-Route"""
    
    router = APIRouter()
    
    # Cache für hochgeladene CSV-Daten (max 100 Sessions, 30min TTL)
    mine_lists_cache = TTLCache(maxsize=100, ttl=1800)
    
    def get_cache_stats():
        """Gibt Cache-Statistiken zurück für Monitoring"""
        return {
            'current_size': len(mine_lists_cache),
            'max_size': mine_lists_cache.maxsize,
            'ttl': mine_lists_cache.ttl
        }

    def detect_csv_delimiter(csv_content: str) -> tuple[str, str]:
        """
        Robust CSV delimiter detection with fallback strategies
        
        Returns:
            tuple[str, str]: (delimiter, detection_method)
        """
        # Strip BOM if present
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]
            logger.debug("[CSV-DELIMITER] BOM detected and stripped")
        
        # Sample first N lines for detection (max 10 lines or 2KB)
        lines = csv_content.split('\n')[:10]
        sample_text = '\n'.join(lines)[:2048]
        
        # Strategy 1: Use csv.Sniffer
        try:
            sniffer = csv.Sniffer()
            # Provide delimiters to try
            dialect = sniffer.sniff(sample_text, delimiters=',;\t|')
            delimiter = dialect.delimiter
            logger.info(f"[CSV-DELIMITER] Sniffer detected: '{delimiter}'")
            return delimiter, "sniffer"
        except (csv.Error, Exception) as e:
            logger.debug(f"[CSV-DELIMITER] Sniffer failed: {e}")
        
        # Strategy 2: Quote-aware delimiter counting
        candidates = [',', ';', '\t', '|']
        delimiter_counts = {}
        
        for delimiter in candidates:
            count = 0
            for line in lines[:5]:  # Count in first 5 lines only
                if not line.strip():
                    continue
                    
                # Use csv.reader to properly handle quotes
                try:
                    reader = csv.reader([line], delimiter=delimiter)
                    row = next(reader)
                    # Count successful splits (more than 1 field means delimiter found)
                    if len(row) > 1:
                        count += len(row) - 1  # Count delimiter occurrences
                except csv.Error:
                    continue
            
            delimiter_counts[delimiter] = count
            logger.debug(f"[CSV-DELIMITER] Delimiter '{delimiter}' count: {count}")
        
        # Find delimiter with highest count
        if delimiter_counts:
            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
            best_count = delimiter_counts[best_delimiter]
            
            if best_count > 0:
                logger.info(f"[CSV-DELIMITER] Quote-aware counting detected: '{best_delimiter}' (count: {best_count})")
                return best_delimiter, "quote_aware_counting"
        
        # Strategy 3: Simple character counting fallback
        comma_count = sample_text.count(',')
        semicolon_count = sample_text.count(';')
        
        if semicolon_count > comma_count:
            logger.info(f"[CSV-DELIMITER] Fallback to ';' (count: {semicolon_count} vs {comma_count})")
            return ';', "simple_counting"
        elif comma_count > 0:
            logger.info(f"[CSV-DELIMITER] Fallback to ',' (count: {comma_count})")
            return ',', "simple_counting"
        
        # Strategy 4: Ultimate fallback
        logger.warning("[CSV-DELIMITER] No delimiter detected, using default ','")
        return ',', "default_fallback"

    @router.post("/upload-csv")
    async def upload_csv_fixed(csv_file: UploadFile = File(...)):
        """CSV Upload Route - Fixed Version"""
        try:
            logger.info(f"[FIXED-CSV] Upload empfangen: {csv_file.filename}")
            
            # CSV verarbeiten
            contents = await csv_file.read()
            csv_content = contents.decode('utf-8-sig')
            
            # Robust CSV-Delimiter Detection
            delimiter, detection_method = detect_csv_delimiter(csv_content)
            logger.info(f"[FIXED-CSV] Detected delimiter: '{delimiter}' via {detection_method}")
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
            mines = []
            columns = []
            
            for i, row in enumerate(csv_reader):
                if i == 0:
                    columns = list(row.keys())
                mines.append(row)
                if i >= 100:  # Limit für Demo
                    break
            
            # Erstelle Session
            session_id = str(uuid.uuid4())
            
            # Speichere in Cache (TTL automatisch verwaltet)
            mine_lists_cache[session_id] = {
                'mines': mines,
                'columns': columns
            }
            
            mine_count = len(mines)
            cache_stats = get_cache_stats()
            logger.info(f"[FIXED-CSV] Processed: {mine_count} mines, session: {session_id}")
            logger.debug(f"[CACHE] Session stored. Cache size: {cache_stats['current_size']}/{cache_stats['max_size']}")
            
            # HTML Interface für Batch-Suche
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
                          hx-indicator="#loading-spinner">
                        
                        <input type="hidden" name="session_id" value="{session_id}">
                        
                        <div class="form-group">
                            <label for="selected_models">AI-Modelle auswählen:</label>
                            <select name="selected_models" id="selected_models" multiple required>
                                <option value="openrouter:deepseek-free">DeepSeek Free</option>
                                <option value="perplexity:sonar">Perplexity Sonar</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="count">Anzahl Minen verarbeiten:</label>
                            <input type="number" name="count" value="5" min="1" max="{mine_count}">
                        </div>
                        
                        <div class="form-group">
                            <input type="checkbox" name="search_all" value="true">
                            <label for="search_all">Alle {mine_count} Minen verarbeiten</label>
                        </div>
                        
                        <button type="submit">🚀 Batch-Suche starten</button>
                    </form>
                </div>
            </div>
            
            <div id="batch-results"></div>
            <div id="loading-spinner" class="htmx-indicator">Verarbeitung läuft...</div>
            """
            
            return HTMLResponse(content=html_content)
            
        except Exception as e:
            logger.error(f"[FIXED-CSV] ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=f"CSV Upload Fehler: {str(e)}")

    @router.post("/batch-search")
    async def batch_search_fixed(
        session_id: str = Form(...),
        selected_models: str = Form(...),
        search_type: str = Form("standard"),
        count: int = Form(5),
        search_all: str = Form("false")
    ):
        """
        FIXED BATCH-SEARCH: DB-First Ansatz ohne verschachtelte Fallbacks
        """
        
        logger.info(f"[FIXED-BATCH] START: session_id={session_id}, models={selected_models}")
        
        try:
            # 1. HOLE MINES AUS SESSION CACHE
            if session_id not in mine_lists_cache:
                cache_stats = get_cache_stats()
                logger.warning(f"[CACHE] Session {session_id} nicht gefunden. Cache size: {cache_stats['current_size']}")
                raise HTTPException(status_code=400, detail="Session abgelaufen oder nicht gefunden. Bitte CSV erneut hochladen.")
            
            mines = mine_lists_cache[session_id]['mines']
            columns = mine_lists_cache[session_id]['columns']
            logger.debug(f"[CACHE] Session {session_id} gefunden mit {len(mines)} Minen")
            
            # Bestimme welche Minen zu verarbeiten sind
            if search_all.lower() == "true":
                mines_to_search = mines
            else:
                mines_to_search = mines[:int(count)]
            
            logger.info(f"[FIXED-BATCH] Processing {len(mines_to_search)} mines")
            
            # 2. VERARBEITE JEDE MINE: DB-FIRST
            results = []
            models_list = [m.strip() for m in selected_models.split(',') if m.strip()]
            
            for idx, mine_data in enumerate(mines_to_search):
                mine_name = mine_data.get('Name', 'Unknown')
                country = mine_data.get('Country', 'Unknown')
                region = mine_data.get('Region', 'Unknown')
                commodity = mine_data.get('Commodity', 'Gold')
                
                logger.info(f"[FIXED-BATCH] Processing mine {idx+1}: '{mine_name}'")
                
                # 3. DB-FIRST: Suche existierende Ergebnisse
                best_structured_data = {}
                db_source_used = False
                
                try:
                    existing_results = db_manager.get_recent_search_results(
                        mine_name=mine_name, 
                        hours_back=24,
                        limit=5
                    )
                    
                    logger.info(f"[FIXED-BATCH] DB found {len(existing_results)} existing results for {mine_name}")
                    
                    # Wähle bestes DB-Ergebnis
                    best_db_result = None
                    max_filled_fields = 0
                    
                    for db_result in existing_results:
                        if db_result.success and db_result.structured_data:
                            filled_count = count_filled_fields(db_result.structured_data)
                            if filled_count > max_filled_fields and filled_count >= 5:
                                max_filled_fields = filled_count
                                best_db_result = db_result
                    
                    if best_db_result:
                        best_structured_data = best_db_result.structured_data
                        db_source_used = True
                        logger.info(f"[FIXED-BATCH] Using DB result: {best_db_result.model_used} with {max_filled_fields} fields")
                    
                except Exception as e:
                    logger.warning(f"[FIXED-BATCH] DB query failed: {e}")
                
                # 4. FALLBACK: Nur wenn keine guten DB-Ergebnisse
                if not best_structured_data:
                    logger.info(f"[FIXED-BATCH] No good DB results - starting provider search for {mine_name}")
                    
                    # Provider-Suche als Fallback
                    try:
                        from minesearch.providers.registry import provider_registry
                        from minesearch.config import config
                        
                        if not provider_registry._providers:
                            provider_registry.initialize(config.PROVIDERS)
                        
                        # Verwende erstes verfügbares Modell
                        model_id = models_list[0] if models_list else 'openrouter:deepseek-free'
                        provider = provider_registry.get_provider_for_model(model_id)
                        
                        if provider:
                            query = f"{mine_name} mine {country} {commodity}"
                            model_name = model_id.split(':')[1] if ':' in model_id else model_id
                            options = {
                                'mine_name': mine_name,
                                'country': country,
                                'commodity': commodity,
                                'region': region
                            }
                            
                            search_result = await provider.search(query, model_name, options)
                            
                            if search_result and search_result.success and search_result.structured_data:
                                filled_count = count_filled_fields(search_result.structured_data)
                                logger.info(f"[FIXED-BATCH] Provider success: {filled_count} fields for {mine_name}")
                                best_structured_data = search_result.structured_data
                            else:
                                logger.warning(f"[FIXED-BATCH] Provider search failed for {mine_name}")
                        
                    except Exception as e:
                        logger.error(f"[FIXED-BATCH] Provider search exception: {e}")
                
                # 5. ERSTELLE RESULT-DATA
                final_filled_count = count_filled_fields(best_structured_data)
                success = final_filled_count > 0
                
                result_data = {
                    "mine_name": mine_name,
                    "country": country,
                    "commodity": commodity,
                    "region": region,
                    "success": success,
                    "data": {
                        "structured_data": best_structured_data,
                        "source": "database_cache" if db_source_used else "provider_search",
                        "filled_field_count": final_filled_count,
                        "total_fields": len(best_structured_data)
                    }
                }
                
                results.append(result_data)
                
                logger.info(f"[FIXED-BATCH] Completed {mine_name}: {final_filled_count} fields, source: {'DB' if db_source_used else 'Provider'}")
            
            # 6. GENERIERE HTML mit reparierten Daten
            from minesearch.html_utils import create_batch_results_table
            html_content = create_batch_results_table(results)
            
            # Cache für Download
            batch_results_cache[session_id] = {
                'results': results,
                'columns': columns,
                'timestamp': 'now'
            }
            
            logger.info(f"[FIXED-BATCH] COMPLETE: {len(results)} results generated, HTML length: {len(html_content)}")
            
            return HTMLResponse(content=html_content)
        
        except Exception as e:
            logger.error(f"[FIXED-BATCH] ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/cache/stats")
    async def get_cache_statistics():
        """Zeigt Cache-Statistiken für Monitoring"""
        stats = get_cache_stats()
        return {
            "success": True,
            "cache_stats": stats
        }
    
    @router.post("/cache/clear")
    async def clear_cache():
        """Leert den gesamten Cache (für Admin/Debug-Zwecke)"""
        mine_lists_cache.clear()
        logger.info("[CACHE] Cache manuell geleert")
        return {
            "success": True,
            "message": "Cache erfolgreich geleert"
        }
    
    return router
