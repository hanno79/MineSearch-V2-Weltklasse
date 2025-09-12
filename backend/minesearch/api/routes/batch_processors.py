"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Verarbeitungslogik für Batch-Processing (Refactoring aus batch.py)
"""

import logging
import csv
import io
from typing import Dict, Any, List
from fastapi import HTTPException
from fastapi.responses import Response

from minesearch.config import CSV_COLUMNS
from minesearch.html_utils import create_batch_results_table

logger = logging.getLogger(__name__)

async def process_batch_results(batch_service, cache_key: str, model: str):
    """Batch-Verarbeitung der hochgeladenen Minen"""
    try:
        return await batch_service.process_batch(cache_key, model)
        except KeyError as e:
        logger.error(f"Fehler bei Batch-Verarbeitung: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_batch_results_data(cache_key: str, batch_results_cache: Dict[str, Any]):
    """SESSION-ISOLATION FIX 30.08.2025: Batch-Ergebnisse session-spezifisch abrufen"""

    # Suche nach session-spezifischen Cache-Keys (unterstützt alte und neue Formate)
    matching_keys = [key for key in batch_results_cache.keys() if cache_key in key]

    if not matching_keys:
        logger.warning(f"[SESSION-ISOLATION] No results found for cache_key: {cache_key}")
        logger.debug(f"[SESSION-ISOLATION] Available keys: {list(batch_results_cache.keys())}")
        raise HTTPException(status_code=404, detail="Keine Ergebnisse gefunden")

    # Verwende den neuesten/ersten passenden Key
    actual_key = matching_keys[0]
    logger.info(f"[SESSION-ISOLATION] Using cache key: {actual_key} for request: {cache_key}")

    # Note: create_batch_results_table is imported at module scope (line 26)
    cached_data = batch_results_cache[actual_key]
    results = cached_data.get("results", cached_data)  # Backward compatibility
    html = create_batch_results_table(results)

    return {"html": html, "results": results}

def download_batch_results_csv(cache_key: str, batch_results_cache: Dict[str, Any]) -> Response:
    """SESSION-ISOLATION FIX 30.08.2025: Batch-Ergebnisse session-spezifisch als CSV herunterladen"""

    # Suche nach session-spezifischen Cache-Keys (unterstützt alte und neue Formate)
    matching_keys = [key for key in batch_results_cache.keys() if cache_key in key]

    if not matching_keys:
        logger.warning(f"[SESSION-ISOLATION] No download results found for cache_key: {cache_key}")
        raise HTTPException(status_code=404, detail="Keine Ergebnisse gefunden")

    # Verwende den neuesten/ersten passenden Key
    actual_key = matching_keys[0]
    logger.info(f"[SESSION-ISOLATION] Downloading from cache key: {actual_key}")

    cached_data = batch_results_cache[actual_key]
    results = cached_data.get("results", cached_data)  # Backward compatibility

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
                row[key] = structured_data.get(key, "")  # REGEL 10: NULL statt "k.A." Fallback

            writer.writerow(row)

    content = output.getvalue()

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=mine_search_results_{cache_key}.csv"
        }
    )
