"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: API-Endpoints für Modell-Benchmarks und Statistiken
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from model_benchmark_service import ModelBenchmarkService
from minesearch.database import db_manager
from model_summary_auto_updater import ModelSummaryAutoUpdater

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

@router.get("/recent")
async def get_recent_search_results(
    days_back: int = Query(7, description="Tage zurück"),
    limit: int = Query(50, description="Maximale Anzahl Ergebnisse"),
    sort_by: str = Query("search_timestamp", description="Sortierfeld"),
    order: str = Query("desc", description="Sortierreihenfolge (asc/desc)"),
    mine_name: Optional[str] = Query(None, description="Filter nach Mine"),
    country: Optional[str] = Query(None, description="Filter nach Land"),
    session_id: Optional[str] = Query(None, description="Filter nach Session")
):
    """
    FRONTEND-FIX 19.07.2025: Erweitert um Sortierung und Filterung
    """
    try:
        from database import SearchResult
        from sqlalchemy import desc, asc, func
        from datetime import datetime, timedelta
        
        with db_manager.get_session() as session:
            query = session.query(SearchResult)
            
            # Zeitfilter
            if days_back < 9999:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                query = query.filter(SearchResult.search_timestamp >= cutoff_date)
            
            # Filter anwenden
            if mine_name:
                query = query.filter(SearchResult.mine_name.ilike(f"%{mine_name}%"))
            if country:
                query = query.filter(SearchResult.country == country)
            if session_id:
                query = query.filter(SearchResult.session_id == session_id)
            
            # Hole alle Ergebnisse erstmal ohne Sortierung für berechnete Felder
            results = query.limit(limit * 2).all()  # Mehr holen für korrekte Sortierung
            
            # Erweitere Daten um berechnete Felder
            enriched_data = []
            for result in results:
                result_dict = result.to_dict()
                
                # Berechne fields_count aus structured_data
                if result_dict.get('structured_data'):
                    fields_count = len([k for k, v in result_dict['structured_data'].items() 
                                      if v and str(v).strip() and v != 'X' and v != '-'])
                    result_dict['fields_count'] = fields_count
                    result_dict['score'] = fields_count  # Score als Alias
                else:
                    result_dict['fields_count'] = 0
                    result_dict['score'] = 0
                
                enriched_data.append(result_dict)
            
            # Python-Sortierung für berechnete Felder
            if sort_by in ["fields_count", "score"]:
                reverse_order = order.lower() == "desc"
                enriched_data.sort(key=lambda x: x[sort_by], reverse=reverse_order)
            elif sort_by in ["search_timestamp", "mine_name", "model_used", "country"]:
                # Für Datenbankfelder: nochmal sortieren
                sort_column_map = {
                    "search_timestamp": SearchResult.search_timestamp,
                    "mine_name": SearchResult.mine_name,
                    "model_used": SearchResult.model_used,
                    "country": SearchResult.country
                }
                
                sort_column = sort_column_map.get(sort_by, SearchResult.search_timestamp)
                
                if order.lower() == "asc":
                    query = query.order_by(asc(sort_column))
                else:
                    query = query.order_by(desc(sort_column))
                
                # Re-hole mit korrekter Sortierung
                results = query.limit(limit).all()
                enriched_data = []
                for result in results:
                    result_dict = result.to_dict()
                    
                    # Berechne fields_count aus structured_data
                    if result_dict.get('structured_data'):
                        fields_count = len([k for k, v in result_dict['structured_data'].items() 
                                          if v and str(v).strip() and v != 'X' and v != '-'])
                        result_dict['fields_count'] = fields_count
                        result_dict['score'] = fields_count
                    else:
                        result_dict['fields_count'] = 0
                        result_dict['score'] = 0
                    
                    enriched_data.append(result_dict)
            
            # Limitiere auf gewünschte Anzahl
            enriched_data = enriched_data[:limit]
            
            return {
                "success": True,
                "data": enriched_data,
                "total": len(enriched_data),
                "sort_by": sort_by,
                "order": order
            }
    except Exception as e:
        logger.error(f"Error fetching recent results: {e}")
        return {"success": False, "error": str(e), "data": []}

# Service-Instanzen
benchmark_service = ModelBenchmarkService()
summary_updater = ModelSummaryAutoUpdater()

# Laufende Benchmark-Sessions
benchmark_sessions = {}


class BenchmarkRequest(BaseModel):
    """Request-Model für Benchmark-Start"""
    model_ids: List[str] = Field(..., description="Liste der zu testenden Modell-IDs")
    mine_name: str = Field(..., description="Name der Mine")
    country: Optional[str] = Field(None, description="Land")
    region: Optional[str] = Field(None, description="Region")
    commodity: Optional[str] = Field(None, description="Rohstoff")
    runs: int = Field(5, ge=1, le=10, description="Anzahl Durchläufe pro Modell")


class BenchmarkStatus(BaseModel):
    """Status einer Benchmark-Session"""
    session_id: str
    status: str  # running, completed, failed
    progress: float  # 0.0 bis 1.0
    current_model: Optional[str]
    models_completed: int
    total_models: int
    started_at: str
    completed_at: Optional[str]
    error: Optional[str]


async def run_benchmark_task(
    session_id: str,
    model_ids: List[str],
    mine_data: Dict[str, str],
    runs: int
):
    """Background-Task für Benchmark-Durchführung"""
    session = benchmark_sessions[session_id]
    
    try:
        session['status'] = 'running'
        session['started_at'] = datetime.now().isoformat()
        
        for i, model_id in enumerate(model_ids):
            session['current_model'] = model_id
            session['progress'] = i / len(model_ids)
            
            logger.info(f"[BENCHMARK] Session {session_id}: Teste {model_id}")
            
            try:
                result = await benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=mine_data,
                    runs=runs,
                    session_id=session_id
                )
                
                session['results'][model_id] = result
                session['models_completed'] += 1
                
            except Exception as e:
                logger.error(f"[BENCHMARK] Fehler bei {model_id}: {str(e)}")
                session['results'][model_id] = {
                    'error': str(e),
                    'success': False
                }
        
        session['status'] = 'completed'
        session['progress'] = 1.0
        session['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"[BENCHMARK] Session {session_id} fehlgeschlagen: {str(e)}")
        session['status'] = 'failed'
        session['error'] = str(e)


@router.post("/start", response_model=Dict[str, str])
async def start_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks
):
    """
    Startet einen neuen Benchmark-Durchlauf
    
    Returns:
        Dict mit session_id
    """
    # Erstelle Session-ID
    session_id = str(uuid.uuid4())
    
    # Erstelle Mine-Daten
    mine_data = {
        'name': request.mine_name,
        'country': request.country or '',
        'region': request.region or '',
        'commodity': request.commodity or ''
    }
    
    # Initialisiere Session
    benchmark_sessions[session_id] = {
        'session_id': session_id,
        'status': 'pending',
        'progress': 0.0,
        'current_model': None,
        'models_completed': 0,
        'total_models': len(request.model_ids),
        'model_ids': request.model_ids,
        'mine_data': mine_data,
        'runs': request.runs,
        'results': {},
        'started_at': None,
        'completed_at': None,
        'error': None
    }
    
    # Starte Background-Task
    background_tasks.add_task(
        run_benchmark_task,
        session_id,
        request.model_ids,
        mine_data,
        request.runs
    )
    
    logger.info(f"[BENCHMARK] Session {session_id} gestartet für {len(request.model_ids)} Modelle")
    
    return {"session_id": session_id}


@router.get("/status/{session_id}", response_model=BenchmarkStatus)
async def get_benchmark_status(session_id: str):
    """
    Ruft den Status einer Benchmark-Session ab
    
    Args:
        session_id: ID der Benchmark-Session
        
    Returns:
        BenchmarkStatus
    """
    if session_id not in benchmark_sessions:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    
    session = benchmark_sessions[session_id]
    
    return BenchmarkStatus(
        session_id=session_id,
        status=session['status'],
        progress=session['progress'],
        current_model=session['current_model'],
        models_completed=session['models_completed'],
        total_models=session['total_models'],
        started_at=session['started_at'] or datetime.now().isoformat(),
        completed_at=session.get('completed_at'),
        error=session.get('error')
    )


@router.get("/results")
async def get_all_benchmark_results(
    model_id: Optional[str] = Query(None, description="Filtere nach Modell-ID"),
    mine_name: Optional[str] = Query(None, description="Filtere nach Mine"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Ruft alle Benchmark-Ergebnisse ab
    
    Args:
        model_id: Optional Filter nach Modell
        mine_name: Optional Filter nach Mine
        limit: Maximale Anzahl Ergebnisse
        
    Returns:
        Liste von Benchmark-Ergebnissen
    """
    with db_manager.get_session() as session:
        from database import ModelStatistics
        
        query = session.query(ModelStatistics)
        
        if model_id:
            query = query.filter_by(model_id=model_id)
        if mine_name:
            query = query.filter_by(mine_name=mine_name)
        
        results = query.order_by(
            ModelStatistics.timestamp.desc()
        ).limit(limit).all()
        
        return {
            'total': len(results),
            'results': [r.to_dict() for r in results]
        }


@router.get("/model/{model_id}")
async def get_model_benchmark_summary(model_id: str):
    """
    Ruft Benchmark-Zusammenfassung für ein Modell ab
    
    Args:
        model_id: ID des Modells
        
    Returns:
        Modell-Zusammenfassung mit Statistiken
    """
    summary = await benchmark_service.get_benchmark_summary(model_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Keine Benchmark-Daten für dieses Modell")
    
    return summary


@router.get("/field-consistency")
async def get_field_consistency_data(
    model_id: Optional[str] = Query(None, description="Filtere nach Modell-ID"),
    mine_name: Optional[str] = Query(None, description="Filtere nach Mine"),
    field_name: Optional[str] = Query(None, description="Filtere nach Feld")
):
    """
    Ruft Feld-Konsistenz-Daten ab
    
    Args:
        model_id: Optional Filter nach Modell
        mine_name: Optional Filter nach Mine
        field_name: Optional Filter nach Feld
        
    Returns:
        Liste von Feld-Konsistenz-Daten
    """
    consistencies = await benchmark_service.get_field_consistencies(
        model_id=model_id,
        mine_name=mine_name
    )
    
    # Filtere nach Feld wenn gewünscht
    if field_name:
        consistencies = [c for c in consistencies if c['field_name'] == field_name]
    
    return {
        'total': len(consistencies),
        'results': consistencies
    }


# ÄNDERUNG 09.07.2025: Doppelte Endpoints entfernt - siehe Zeilen 331 und 474 für die aktiven Definitionen


@router.get("/summary")
async def get_benchmark_summary():
    """
    Ruft Gesamt-Zusammenfassung aller Benchmarks ab
    
    Returns:
        Zusammenfassung mit Top-Modellen und Statistiken
    """
    summaries = await benchmark_service.get_all_benchmarks()
    
    # Sortiere nach verschiedenen Kriterien
    by_success_rate = sorted(summaries, key=lambda x: x['success_rate'], reverse=True)
    by_consistency = sorted(summaries, key=lambda x: x['overall_consistency'], reverse=True)
    by_fields = sorted(summaries, key=lambda x: x['avg_fields_found'], reverse=True)
    by_speed = sorted(summaries, key=lambda x: x['avg_response_time'])
    
    return {
        'total_models': len(summaries),
        'top_by_success_rate': by_success_rate[:5],
        'top_by_consistency': by_consistency[:5],
        'top_by_fields': by_fields[:5],
        'fastest_models': by_speed[:5],
        'all_models': summaries
    }


@router.get("/field-statistics")
async def get_field_statistics(
    model_id: Optional[str] = Query(None, description="Filtere nach Modell-ID"),
    field_name: Optional[str] = Query(None, description="Filtere nach Feld-Name"),
    min_success_rate: float = Query(0.0, ge=0.0, le=1.0, description="Minimale Erfolgsrate")
):
    """
    Ruft feld-spezifische Statistiken ab
    
    ÄNDERUNG 08.07.2025: Neuer Endpoint für detaillierte Feld-Statistiken
    
    Args:
        model_id: Optional Filter nach Modell
        field_name: Optional Filter nach Feld
        min_success_rate: Minimale Erfolgsrate (0.0-1.0)
        
    Returns:
        Liste von Feld-Statistiken pro Modell
    """
    with db_manager.get_session() as session:
        from database import FieldStatistics
        
        query = session.query(FieldStatistics)
        
        if model_id:
            query = query.filter_by(model_id=model_id)
        if field_name:
            query = query.filter_by(field_name=field_name)
        
        query = query.filter(FieldStatistics.success_rate >= min_success_rate)
        
        # Sortiere nach Erfolgsrate absteigend
        results = query.order_by(
            FieldStatistics.success_rate.desc(),
            FieldStatistics.total_searches.desc()
        ).all()
        
        # Gruppiere nach Feld für bessere Übersicht
        field_groups = {}
        for stat in results:
            if stat.field_name not in field_groups:
                field_groups[stat.field_name] = []
            field_groups[stat.field_name].append(stat.to_dict())
        
        return {
            'total_stats': len(results),
            'fields_analyzed': len(field_groups),
            'by_field': field_groups,
            'all_stats': [r.to_dict() for r in results]
        }


@router.get("/charts")
async def get_benchmark_charts(
    mine_name: Optional[str] = Query(None, description="Filtere nach Mine"),
    limit: int = Query(10, ge=1, le=50, description="Anzahl Modelle")
):
    """
    Ruft Chart-Daten für Frontend-Visualisierungen ab
    
    ÄNDERUNG 08.07.2025: Neuer Endpoint für interaktive Charts
    
    Args:
        mine_name: Optional Filter nach Mine
        limit: Anzahl der Top-Modelle
        
    Returns:
        Strukturierte Daten für verschiedene Chart-Typen
    """
    with db_manager.get_session() as session:
        from database import ModelSummary
        from sqlalchemy import desc
        
        query = session.query(ModelSummary)
        
        if mine_name:
            # Filter nach Mine in den letzten Suchen
            query = query.filter(ModelSummary.last_mine_searched.contains(mine_name))
        
        # Hole Top-Modelle nach verschiedenen Kriterien
        summaries = query.order_by(desc(ModelSummary.total_tests)).all()
        
        # Limitiere auf die gewünschte Anzahl
        summaries = summaries[:limit]
        
        # Bereite Daten für Charts vor
        labels = []
        success_rates = []
        consistency_scores = []
        avg_fields = []
        response_times = []
        
        for summary in summaries:
            model_name = summary.model_id.split(':')[-1]  # Entferne Provider-Präfix
            labels.append(model_name)
            success_rates.append(round(summary.success_rate * 100, 1))
            consistency_scores.append(round(summary.overall_consistency * 100, 1))
            avg_fields.append(round(summary.avg_fields_found, 1))
            response_times.append(round(summary.avg_response_time_ms / 1000, 1))  # In Sekunden
        
        # Radar-Chart Daten (normalisiert auf 0-100)
        radar_data = []
        for i, summary in enumerate(summaries[:5]):  # Top 5 für Radar-Chart
            radar_data.append({
                'model': labels[i],
                'data': [
                    success_rates[i],  # Erfolgsrate
                    consistency_scores[i],  # Konsistenz
                    min(100, avg_fields[i] * 5),  # Datenqualität (20 Felder = 100%)
                    max(0, 100 - response_times[i] * 10),  # Geschwindigkeit (10s = 0%)
                    round(summary.data_success_rate * 100, 1) if hasattr(summary, 'data_success_rate') else success_rates[i]  # Daten-Erfolg
                ]
            })
        
        return {
            'success_rates': {
                'labels': labels,
                'data': success_rates
            },
            'consistency_scores': {
                'labels': labels,
                'data': consistency_scores
            },
            'avg_fields': {
                'labels': labels,
                'data': avg_fields
            },
            'response_times': {
                'labels': labels,
                'data': response_times
            },
            'radar_chart': {
                'labels': ['Erfolgsrate', 'Konsistenz', 'Datenqualität', 'Geschwindigkeit', 'Daten-Erfolg'],
                'datasets': radar_data
            },
            'metadata': {
                'total_models': len(summaries),
                'mine_filter': mine_name,
                'generated_at': datetime.now().isoformat()
            }
        }


def _get_exclusion_reason(field_name: str) -> str:
    """Gibt Begründung für Feld-Ausschlüsse zurück"""
    exclusion_reasons = {
        "Produktionsende": "Aktive/geplante Minen ausgeschlossen (haben logisch kein Produktionsende)",
        "Fördermenge/Jahr": "Nicht-produzierende Minen ausgeschlossen (haben keine aktuellen Fördermengen)"
    }
    return exclusion_reasons.get(field_name, "Conditional logic angewendet")

@router.get("/field-comparison")
async def get_field_comparison():
    """
    Vergleiche Feld-Performance über alle Modelle
    
    ÄNDERUNG 08.07.2025: Zeigt welche Felder gut/schlecht gefunden werden
    ÄNDERUNG 13.07.2025: Erweitert um conditional logic für mining-spezifische Statistiken
    
    Returns:
        Vergleichsdaten für alle Felder über alle Modelle mit conditional metadata
    """
    with db_manager.get_session() as session:
        from database import FieldStatistics
        from sqlalchemy import func
        
        # REPARIERT 14.07.2025: SQLite-kompatible Aggregation (bool_or existiert nicht in SQLite)
        # Aggregiere Statistiken pro Feld mit conditional logic awareness
        field_stats = session.query(
            FieldStatistics.field_name,
            func.avg(FieldStatistics.success_rate).label('avg_success_rate'),
            func.sum(FieldStatistics.times_found).label('total_times_found'),
            func.sum(FieldStatistics.total_searches).label('total_searches'),
            func.sum(FieldStatistics.excluded_count).label('total_excluded'),
            func.count(FieldStatistics.model_id).label('models_tested'),
            func.max(FieldStatistics.conditional_logic_applied).label('has_conditional_logic')
        ).group_by(FieldStatistics.field_name).all()
        
        # Sortiere nach durchschnittlicher Erfolgsrate mit conditional metadata
        results = []
        for field_name, avg_rate, times_found, searches, excluded, models, has_conditional in field_stats:
            results.append({
                'field_name': field_name,
                'avg_success_rate': float(avg_rate) if avg_rate else 0.0,
                'total_times_found': int(times_found) if times_found else 0,
                'total_searches': int(searches) if searches else 0,
                'models_tested': int(models) if models else 0,
                'difficulty': 'Einfach' if avg_rate > 0.7 else 'Mittel' if avg_rate > 0.3 else 'Schwer',
                # ÄNDERUNG 13.07.2025: Conditional logic metadata
                'excluded_count': int(excluded) if excluded else 0,
                'conditional_logic_applied': bool(has_conditional) if has_conditional is not None else False,
                'effective_searches': int(searches) if searches else 0,  # Für UI-Kompatibilität
                'exclusion_reason': _get_exclusion_reason(field_name) if has_conditional else None
            })
        
        # Sortiere: Schwere Felder zuerst
        results.sort(key=lambda x: x['avg_success_rate'])
        
        return {
            'total_fields': len(results),
            'hardest_fields': results[:10],  # Top 10 schwerste Felder
            'easiest_fields': results[-10:][::-1],  # Top 10 einfachste Felder
            'all_fields': results
        }


@router.delete("/session/{session_id}")
async def delete_benchmark_session(session_id: str):
    """
    Löscht eine Benchmark-Session aus dem Speicher
    
    Args:
        session_id: ID der zu löschenden Session
        
    Returns:
        Bestätigung
    """
    if session_id not in benchmark_sessions:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    
    del benchmark_sessions[session_id]
    
    return {"message": "Session gelöscht", "session_id": session_id}


@router.post("/capture")
async def capture_search_statistics(stats_data: Dict[str, Any]):
    """
    Erfasst Statistiken von normalen Suchen
    
    ÄNDERUNG 07.07.2025: Unterscheide zwischen API-Erfolg und Daten-Erfolg
    
    Args:
        stats_data: Statistik-Daten von einer normalen Suche
        
    Returns:
        Bestätigung
    """
    try:
        # ÄNDERUNG 07.07.2025: Debug-Logging für alle eingehenden Statistiken
        logger.info(f"[BENCHMARK] 📊 Empfange Statistiken von {stats_data.get('model_id')} für {stats_data.get('mine_name')}")
        
        # ÄNDERUNG 07.07.2025: Bestimme Daten-Erfolg basierend auf gefüllten Feldern
        api_success = stats_data.get('success', False)
        fields_found = stats_data.get('fields_found', 0)
        structured_data = stats_data.get('structured_data', {})
        
        # Zähle nur Felder mit echten Daten (nach Validierung)
        real_fields_count = 0
        critical_fields_found = []
        
        # Kritische Felder die wir tracken wollen
        critical_fields = ['Eigentümer', 'Betreiber', 'Restaurationskosten', 
                         'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus']
        
        for field, value in structured_data.items():
            if value and str(value).strip():
                real_fields_count += 1
                if field in critical_fields:
                    critical_fields_found.append(field)
        
        # ÄNDERUNG 09.07.2025: Verbesserte Erfolgs-Definition
        # API-Erfolg: Modell hat ohne Fehler geantwortet
        # Daten-Erfolg: Mindestens 3 Felder gefunden (nicht nur kritische)
        data_success = api_success and real_fields_count >= 3
        
        # Für Statistik verwenden wir api_success als success
        # (damit auch Antworten ohne Daten als "erfolgreich" gezählt werden)
        statistical_success = api_success
        
        # Erstelle ModelStatistics-Eintrag
        with db_manager.get_session() as session:
            from database import ModelStatistics
            
            stat = ModelStatistics(
                model_id=stats_data['model_id'],
                mine_name=stats_data['mine_name'],
                country=stats_data.get('country'),
                region=stats_data.get('region'),
                commodity=stats_data.get('commodity'),
                run_number=stats_data.get('run_number', 1),
                success=statistical_success,  # ÄNDERUNG 09.07.2025: Nutze api_success für konsistente Zählung
                response_time_ms=stats_data.get('response_time_ms'),
                fields_found=real_fields_count,  # ÄNDERUNG: Nutze echte Feldanzahl
                sources_count=stats_data.get('sources_count', 0),
                structured_data=structured_data,
                error_message=None if api_success else stats_data.get('error_message', 'API call failed'),
                # Zusätzliche Metadaten für bessere Analyse
                raw_result={
                    'api_success': api_success,
                    'data_success': data_success,
                    'critical_fields_found': critical_fields_found,
                    'raw_fields_count': fields_found,
                    'validated_fields_count': real_fields_count,
                    'metadata': stats_data.get('metadata', {})
                }
            )
            session.add(stat)
            session.commit()
            
            logger.info(f"[BENCHMARK] Statistiken erfasst für {stats_data['model_id']} - {stats_data['mine_name']}")
            logger.info(f"[BENCHMARK] API-Erfolg: {api_success}, Daten-Erfolg: {data_success}, Felder: {real_fields_count}")
            
            # ÄNDERUNG 08.07.2025: Erfasse feld-spezifische Statistiken
            from database import FieldStatistics
            from config import CSV_COLUMNS
            
            # Gehe durch alle möglichen Felder
            for field_name in CSV_COLUMNS:
                field_stat = session.query(FieldStatistics).filter_by(
                    model_id=stats_data['model_id'],
                    field_name=field_name
                ).first()
                
                if not field_stat:
                    field_stat = FieldStatistics(
                        model_id=stats_data['model_id'],
                        field_name=field_name,
                        total_searches=0,
                        times_found=0,
                        times_empty=0,
                        success_rate=0.0
                    )
                    session.add(field_stat)
                
                # Aktualisiere Statistiken
                field_stat.total_searches += 1
                
                # Prüfe ob Feld gefunden wurde
                field_value = structured_data.get(field_name, "")
                if field_value and str(field_value).strip():
                    field_stat.times_found += 1
                else:
                    field_stat.times_empty += 1
                
                # Berechne Erfolgsrate
                field_stat.success_rate = field_stat.times_found / field_stat.total_searches
                
            session.commit()
        
        # Aktualisiere Modell-Zusammenfassung im Hintergrund
        # Konvertiere stats_data in das erwartete Format
        result_format = {
            'run_number': 1,
            'success': statistical_success,  # ÄNDERUNG 09.07.2025: Verwende api_success
            'response_time_ms': stats_data.get('response_time_ms', 0),
            'fields_found': real_fields_count,
            'sources_count': stats_data.get('sources_count', 0),
            'structured_data': structured_data
        }
        
        logger.info(f"[BENCHMARK] Rufe _update_model_summary auf für {stats_data['model_id']}")
        
        await benchmark_service._update_model_summary(
            stats_data['model_id'], 
            [result_format]  # Als Liste im erwarteten Format
        )
        
        logger.info(f"[BENCHMARK] ModelSummary aktualisiert für {stats_data['model_id']}")
        
        return {"success": True, "message": "Statistiken erfasst"}
        
    except Exception as e:
        logger.error(f"[BENCHMARK] Fehler beim Erfassen der Statistiken: {str(e)}")
        # Keine Exception werfen, da dies eine fire-and-forget Operation ist
        return {"success": False, "error": str(e)}


@router.get("/model-summaries")
async def get_model_summaries(
    sort_by: str = Query("success_rate", description="Sortierung: success_rate, consistency, fields, speed, total_tests"),
    order: str = Query("desc", description="Reihenfolge: asc oder desc"),
    exclude_disabled: bool = Query(True, description="Deaktivierte Provider ausblenden"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Ruft sortierbare Modell-Zusammenfassungen ab
    
    ÄNDERUNG 09.07.2025: Neuer Endpoint für sortierbare Modell-Statistiken mit Exa-Filter
    
    Args:
        sort_by: Sortierkriterium
        order: Sortierreihenfolge (asc/desc)
        exclude_disabled: Deaktivierte Provider (z.B. Exa) ausblenden
        limit: Maximale Anzahl der Ergebnisse
        
    Returns:
        Sortierte Liste von Modell-Zusammenfassungen
    """
    with db_manager.get_session() as session:
        from database import ModelSummary
        from sqlalchemy import desc as sql_desc, asc as sql_asc
        
        query = session.query(ModelSummary)
        
        # Filter deaktivierte Provider (Exa) wenn gewünscht
        if exclude_disabled:
            query = query.filter(~ModelSummary.model_id.like('exa:%'))
        
        # Sortierung
        sort_column = {
            'success_rate': ModelSummary.success_rate,
            'consistency': ModelSummary.overall_consistency,
            'fields': ModelSummary.avg_fields_found,
            'speed': ModelSummary.avg_response_time_ms,
            'total_tests': ModelSummary.total_tests
        }.get(sort_by, ModelSummary.success_rate)
        
        if order == 'asc':
            query = query.order_by(sql_asc(sort_column))
        else:
            query = query.order_by(sql_desc(sort_column))
        
        # Limitiere Ergebnisse
        summaries = query.limit(limit).all()
        
        # Konvertiere zu Dict und füge zusätzliche Informationen hinzu
        results = []
        for summary in summaries:
            result = summary.to_dict()
            
            # Füge Provider-Info hinzu
            provider = summary.model_id.split(':')[0] if ':' in summary.model_id else 'unknown'
            result['provider'] = provider
            
            # Füge Performance-Indikatoren hinzu
            result['performance_score'] = (
                (summary.success_rate * 100 * 0.3) +  # 30% Gewicht
                (summary.overall_consistency * 100 * 0.3) +  # 30% Gewicht
                (min(summary.avg_fields_found / 18, 1) * 100 * 0.3) +  # 30% Gewicht
                (max(0, 100 - summary.avg_response_time_ms / 100) * 0.1)  # 10% Gewicht
            )
            
            results.append(result)
        
        return {
            'success': True,
            'total': len(results),
            'sort_by': sort_by,
            'order': order,
            'data': results
        }


@router.post("/regenerate-summaries")
async def regenerate_model_summaries():
    """
    ÄNDERUNG 14.07.2025: Regeneriert alle ModelSummary-Einträge
    
    Endpoint für Frontend um Model-Summaries zu regenerieren wenn sie fehlen
    """
    try:
        from model_summary_generator import ModelSummaryGenerator
        
        generator = ModelSummaryGenerator()
        result = generator.generate_all_model_summaries()
        
        if result["success"]:
            return {
                "success": True,
                "message": f"{result['summaries_generated']} Model-Summaries regeneriert",
                "total_generated": result["summaries_generated"],
                "duration_seconds": result["duration_seconds"]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Fehler bei Regenerierung: {result.get('error', 'Unbekannter Fehler')}"
            )
            
    except Exception as e:
        logger.error(f"Fehler bei ModelSummary-Regenerierung: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary-status")
async def get_summary_status():
    """
    ÄNDERUNG 14.07.2025: Status der ModelSummary-Tabelle
    
    Returns:
        Status über ModelSummary-Coverage und fehlende Einträge
    """
    try:
        status = summary_updater.get_summary_status()
        return status
        
    except Exception as e:
        logger.error(f"Fehler bei Summary-Status: {e}")
        raise HTTPException(status_code=500, detail=str(e))