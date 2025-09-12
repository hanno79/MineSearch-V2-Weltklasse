"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Suchergebnis-Management Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/results")
async def get_results(
    mine_name: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    days_back: int = Query(30),
    limit: int = Query(50),
    offset: int = Query(0),
    sort_by: str = Query("timestamp", description="Sort by: timestamp, mine_name, model_id,
fields_found, response_time"),
    order: str = Query("desc", description="Order: asc or desc"),
    exclude_exa: bool = Query(True, description="Exa-Modelle ausblenden")
):
    """
    Hole gespeicherte Suchergebnisse mit Filtern und Sortierung

    ÄNDERUNG 09.07.2025: Erweitert um Sortierung und Exa-Filter
    """
    from minesearch.database import db_manager, SearchResult
    from sqlalchemy import desc as sql_desc, asc as sql_asc

    with db_manager.get_session() as session:
        query = session.query(SearchResult)

        # Filter
        if exclude_exa:
            query = query.filter(~SearchResult.model_used.like('exa:%'))

        if mine_name:
            query = query.filter(SearchResult.mine_name == mine_name)

        if country:
            query = query.filter(SearchResult.country == country)

        if session_id:
            query = query.filter(SearchResult.session_id == session_id)

        # Zeitfilter
        if days_back > 0:
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=days_back)
            query = query.filter(SearchResult.search_timestamp >= cutoff)

        # Sortierung
        sort_columns = {
            'timestamp': SearchResult.search_timestamp,
            'mine_name': SearchResult.mine_name,
            'model_id': SearchResult.model_used,
            'response_time': SearchResult.search_duration
        }
        sort_column = sort_columns.get(sort_by, SearchResult.search_timestamp)

        if order == 'asc':
            query = query.order_by(sql_asc(sort_column))
        else:
            query = query.order_by(sql_desc(sort_column))

        # Gesamtanzahl
        total = query.count()

        # Pagination
        results = query.offset(offset).limit(limit).all()

        # Erweitere Ergebnisse mit zusätzlichen Infos
        data_dict = []
        for result in results:
            item = result.to_dict()

            # Provider extrahieren
            item['provider'] = result.model_used.split(':')[0] if ':' in result.model_used else 'unknown'

            # Datenqualität berechnen
            if result.structured_data:
                filled_fields = sum(1 for v in result.structured_data.values() if v)
                total_fields = len(result.structured_data)
                item['data_quality'] = round((filled_fields / total_fields) * 100, 1) if total_fields > 0 else 0
            else:
                item['data_quality'] = 0

            data.append(item)

        return {
            "success": True,
            "data": {
                "results": data,
                "total": total,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by,
                "order": order
            }
        }

@router.get("/results/stats")
async def get_result_statistics():
    """Hole Statistiken über gespeicherte Ergebnisse inkl. Modell-Performance"""
    from minesearch.database import db_manager

    # Basis-Statistiken
    stats = db_manager.get_statistics()

    # Erweitere um Modell-Statistiken für Frontend-Kompatibilität
    try:
        models_data = db_manager.get_model_statistics_comprehensive()
    except Exception as exc:
        logger.exception("Fehler beim Abrufen der Modell-Statistiken in /results/stats; setze leeres
Fallback.", exc_info=True)
        models_data = []
    stats['models'] = models_data

    return {
        "success": True,
        "data": stats
    }

@router.get("/results/sessions")
async def get_result_sessions(limit: int = Query(20)):
    """Hole gruppierte Such-Sessions"""

    sessions = db_manager.get_sessions(limit=limit)
    return {
        "success": True,
        "data": sessions
    }

@router.get("/results/{result_id}")
async def get_result_by_id(result_id: int):
    """Hole einzelnes Suchergebnis nach ID"""

    result = db_manager.get_search_result_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Ergebnis nicht gefunden")

    return {
        "success": True,
        "data": result.to_dict()
    }

@router.delete("/results/{result_id}")
async def delete_result(result_id: int):
    """Lösche einzelnes Suchergebnis"""

    with db_manager.get_session() as session:
        result = session.query(SearchResult).filter_by(id=result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Ergebnis nicht gefunden")

        session.delete(result)
        session.commit()

    return {
        "success": True,
        "message": f"Ergebnis {result_id} gelöscht"
    }

@router.get("/results/export/csv")
async def export_results_csv(
    mine_name: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    days_back: int = Query(30),
    sort_by: str = Query("timestamp"),
    order: str = Query("desc"),
    exclude_exa: bool = Query(True)
):
    """
    Exportiere Suchergebnisse als CSV mit Pipe-Trennzeichen

    CSV-EXPORT 19.07.2025: Neue Route für CSV-Download mit | als Separator
    """
    from fastapi.responses import StreamingResponse
    import io
    from typing import List

    # CSV-FIX 25.08.2025: Verwende einfache CSV-Generation statt externen Service

    with db_manager.get_session() as session:
        query = session.query(SearchResult)

        # Filter anwenden (gleiche Logik wie /results)
        if exclude_exa:
            query = query.filter(~SearchResult.model_used.like('exa:%'))

        if mine_name:
            query = query.filter(SearchResult.mine_name == mine_name)

        if country:
            query = query.filter(SearchResult.country == country)

        if session_id:
            query = query.filter(SearchResult.session_id == session_id)

        # Zeitfilter
        if days_back > 0:
            cutoff = datetime.now() - timedelta(days=days_back)
            query = query.filter(SearchResult.search_timestamp >= cutoff)

        # Sortierung
        sort_columns = {
            'timestamp': SearchResult.search_timestamp,
            'mine_name': SearchResult.mine_name,
            'model_id': SearchResult.model_used,
            'response_time': SearchResult.search_duration
        }
        sort_column = sort_columns.get(sort_by, SearchResult.search_timestamp)

        if order == 'asc':
            query = query.order_by(sql_asc(sort_column))
        else:
            query = query.order_by(sql_desc(sort_column))

        # Alle Ergebnisse laden
        results = query.all()

        # CSV-FIX: Einfache CSV-Generation
        csv_lines = []

        # Header
        header = ["Mine", "Land", "Session ID", "Modell", "Timestamp", "Dauer (s)", "Felder", "Strukturierte Daten"]
        csv_lines.append("|".join(header))

        # Daten
        for result in results:
            row = [
                result.mine_name or "nichts gefunden",
                result.country or "nichts gefunden",
                result.session_id or "nichts gefunden",
                result.model_used or "nichts gefunden",
                str(result.search_timestamp) or "nichts gefunden",
                str(result.search_duration) or "0",
                str(len(result.structured_data) if result.structured_data else 0),
                str(result.structured_data)[:100] + "..." if result.structured_data else "nichts gefunden"
            ]
            # Ersetze Pipe-Zeichen in Werten durch Semikolons
            escaped_row = [str(cell).replace("|", ";") for cell in row]
            csv_lines.append("|".join(escaped_row))

        csv_content = "\n".join(csv_lines)

        # Dateiname mit Timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"minesearch_results_{timestamp}.csv"

        # Stream Response erstellen
        def iter_csv():
    """iter_csv - TODO: Dokumentation hinzufügen"""
            yield csv_content.encode('utf-8-sig')  # UTF-8 BOM für Excel

        return StreamingResponse(
            iter_csv(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
