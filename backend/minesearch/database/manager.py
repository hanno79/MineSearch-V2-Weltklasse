"""
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: DatabaseManager Klasse für MineSearch v2 (extrahiert aus database.py)
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Dict, List, Any
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from minesearch.config.base import config, CSV_COLUMNS
from .models import Base, Source, SearchResult, ModelStatistics, FieldConsistency, ModelSummary, FieldStatistics, ModelStatisticsComprehensive

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Verwaltung der Datenbankverbindung und -operationen"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or config.DATABASE_URL
        
        # PERFORMANCE-FIX: Connection Pool für bessere Performance
        self.engine = create_engine(
            self.database_url, 
            echo=False,  # Setze auf True für SQL-Debugging
            connect_args={"check_same_thread": False},  # Nur für SQLite
            # Connection Pool Einstellungen
            pool_size=20,  # Anzahl permanenter Verbindungen
            max_overflow=30,  # Zusätzliche Verbindungen bei Bedarf
            pool_timeout=30,  # Timeout für neue Verbindungen
            pool_recycle=3600,  # Verbindungen nach 1 Stunde recyceln
            pool_pre_ping=True  # Teste Verbindung vor Nutzung
        )

        # Stelle sicher, dass Foreign Keys in SQLite erzwungen werden
        if (self.database_url or "").startswith("sqlite"):
            @event.listens_for(self.engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, connection_record):
                try:
                    if isinstance(dbapi_connection, sqlite3.Connection):
                        cursor = dbapi_connection.cursor()
                        cursor.execute("PRAGMA foreign_keys=ON")
                        cursor.close()
                except Exception as e:
                    logger.warning(f"[DB] Konnte PRAGMA foreign_keys=ON nicht setzen: {e}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Erstelle Tabellen wenn nicht vorhanden
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Datenbank initialisiert mit Connection Pool: {self.database_url}")
    
    def get_session(self) -> Session:
        """Hole eine neue Datenbank-Session"""
        return self.SessionLocal()
    
    def add_or_update_source(self, url: str, domain: str, country: Optional[str] = None,
                            region: Optional[str] = None, source_type: str = 'unknown',
                            metadata: Optional[Dict[str, Any]] = None) -> Source:
        """Füge neue Quelle hinzu oder aktualisiere bestehende"""
        # Normalisiere URL - entferne Query-Parameter für Vergleiche
        if not url.startswith('search:'):
            try:
                parsed = urlparse(url)
                # Basis-URL ohne Query für Datenbanksuche
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
                # Verwende Domain aus URL falls nicht gegeben
                if not domain:
                    domain = parsed.netloc
            except (ValueError, AttributeError) as e:
                logger.debug(f"[DB] URL-Parsing-Fehler für '{url}': {e}")
                base_url = url
            except Exception as e:
                logger.warning(f"[DB] Unerwarteter Fehler beim URL-Parsing: {e}")
                base_url = url
        else:
            # Spezialbehandlung für Document-Search
            base_url = url
            domain = 'document_search'
        
        # Automatische Quellentyp-Klassifizierung und Land-Erkennung
        if source_type == 'unknown' or source_type == 'url':
            source_type = Source.classify_source_type(url, domain)
        
        # Automatische Land-Erkennung wenn nicht angegeben
        if not country:
            detected_country = Source.get_country_from_domain(url, domain)
            if detected_country:
                country = detected_country
                
        with self.get_session() as session:
            # Prüfe ob Quelle bereits existiert - suche nach exakter URL
            source = session.query(Source).filter_by(url=base_url).first()
            
            # Wenn Quelle existiert und Region unterschiedlich ist, erstelle neue Quelle nur wenn Region relevant
            if source and region and source.region != region:
                # Prüfe ob Region-spezifische Quelle bereits existiert
                source_with_region = session.query(Source).filter_by(url=base_url, region=region).first()
                if source_with_region:
                    source = source_with_region
                else:
                    # Nur neue Quelle erstellen wenn Region für diese Domain relevant ist
                    if source.source_type in ['government', 'database']:
                        source = None  # Erstelle neue Quelle mit Region
            
            if source:
                # Aktualisiere bestehende Quelle
                if country and not source.country:
                    source.country = country
                if region and not source.region:
                    source.region = region
                if source_type != 'unknown' and (source.source_type == 'unknown' or source_type != source.source_type):
                    logger.info(f"[DB] Aktualisiere Quellentyp für {domain}: {source.source_type} → {source_type}")
                    source.source_type = source_type
                if metadata:
                    source.extra_metadata = {**(source.extra_metadata or {}), **metadata}
                # Neuberechnung des Scores bei Aktualisierung
                source.reliability_score = source.calculate_reliability_score()
            else:
                # Erstelle neue Quelle mit normalisierter URL
                source = Source(
                    url=base_url,  # Verwende normalisierte URL
                    domain=domain,
                    country=country,
                    region=region,
                    source_type=source_type,
                    extra_metadata=metadata
                )
                session.add(source)
                logger.info(f"[DB] Neue Quelle hinzugefügt: {domain} (Typ: {source_type})")
            
            session.commit()
            session.refresh(source)
            return source

    def update_source_access(self, source_id: int, success: bool, content_type: Optional[str] = None):
        """Aktualisiere Zugriffs-Statistiken einer Quelle"""
        with self.get_session() as session:
            source = session.get(Source, source_id)
            if source:
                source.update_access(success, content_type)
                session.commit()

    def get_sources_by_type(self, source_type: str, limit: int = 100) -> List[Source]:
        """Hole Quellen nach Typ"""
        with self.get_session() as session:
            return session.query(Source).filter_by(source_type=source_type).limit(limit).all()

    def get_best_sources(self, country: Optional[str] = None, limit: int = 50) -> List[Source]:
        """Hole die besten Quellen nach Zuverlässigkeitsscore"""
        with self.get_session() as session:
            query = session.query(Source).filter(Source.reliability_score > 50)
            if country:
                query = query.filter_by(country=country)
            return query.order_by(Source.reliability_score.desc()).limit(limit).all()

    def save_search_result(self, mine_name: str, model_used: str, structured_data: Dict[str, Any],
                          sources: List[Dict[str, Any]], session_id: Optional[str] = None,
                          session: Optional[Session] = None,
                          **kwargs) -> SearchResult:
        """
        Speichere Suchergebnis in der Datenbank und aktualisiere automatisch Statistiken
        
        STATISTICS INTEGRATION FIX: Nach jedem gespeicherten SearchResult werden die
        ModelStatisticsComprehensive automatisch aktualisiert für Live-Statistik-Updates
        """
        result = SearchResult(
            mine_name=mine_name,
            model_used=model_used,
            structured_data=structured_data,
            sources=sources,
            session_id=session_id,
            **kwargs
        )
        
        # Wenn eine externe Session übergeben wurde, verwende diese ohne eigenen Commit
        if session is not None:
            session.add(result)
            # Stelle sicher, dass IDs generiert werden
            try:
                session.flush()
            except Exception:
                # Flush-Fehler sollen nicht still geschluckt werden
                raise
            return result
        
        # Ansonsten eigene Session öffnen und vollständig committen inkl. Statistik-Update
        with self.get_session() as local_session:
            local_session.add(result)
            local_session.commit()
            local_session.refresh(result)
            
            # AUTO-UPDATE STATISTIKEN für Live-Updates im Statistik-Tab
            try:
                # Handle both single models and model combinations (split by underscore)
                if '_' in model_used:
                    # Multiple models combined with underscore - update each individually
                    individual_models = model_used.split('_')
                    logger.info(f"[AUTO-STATS] Updating statistics for combined models: {individual_models}")
                    for individual_model in individual_models:
                        individual_model = individual_model.strip()
                        if individual_model:
                            self.update_model_statistics_comprehensive(individual_model)
                else:
                    # Single model
                    logger.info(f"[AUTO-STATS] Updating statistics for single model: {model_used}")
                    self.update_model_statistics_comprehensive(model_used)
                    
            except Exception as e:
                logger.warning(f"[AUTO-STATS] Failed to update statistics after search result save: {e}")
                # Don't fail the search result save if statistics update fails
                
            return result

    def get_search_results(self, mine_name: Optional[str] = None, limit: int = 100) -> List[SearchResult]:
        """Hole Suchergebnisse"""
        with self.get_session() as session:
            query = session.query(SearchResult)
            if mine_name:
                query = query.filter_by(mine_name=mine_name)
            return query.order_by(SearchResult.search_timestamp.desc()).limit(limit).all()

    def get_search_result_by_id(self, result_id: int) -> Optional[SearchResult]:
        """Hole einzelnes Suchergebnis nach ID"""
        with self.get_session() as session:
            return session.get(SearchResult, result_id)

    def cleanup_old_results(self, days: int = 30):
        """Lösche alte Suchergebnisse"""
        from sqlalchemy import func
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.get_session() as session:
            deleted = session.query(SearchResult).filter(
                SearchResult.search_timestamp < cutoff_date
            ).delete()
            session.commit()
            logger.info(f"[DB] {deleted} alte Suchergebnisse gelöscht (älter als {days} Tage)")

    def get_sources_for_search(self, country: Optional[str] = None, region: Optional[str] = None,
                              source_type: Optional[str] = None, min_reliability: float = 30.0, 
                              limit: int = 50, offset: int = 0) -> List[Source]:
        """Hole relevante Quellen für eine Suche"""
        with self.get_session() as session:
            query = session.query(Source).filter(Source.reliability_score >= min_reliability)
            
            if country:
                # Länderspezifische und globale Quellen
                query = query.filter(
                    (Source.country == country) | (Source.country.is_(None))
                )
                
                if region:
                    # Regionsspezifische Quellen priorisieren
                    query = query.filter(
                        (Source.region == region) | (Source.region.is_(None))
                    )
            
            # Filter nach Quellentyp wenn angegeben
            if source_type:
                query = query.filter(Source.source_type == source_type)
            
            # Sortiere nach Zuverlässigkeit und Erfolgsquote
            sources = query.order_by(
                Source.reliability_score.desc(),
                Source.successful_searches.desc()
            ).offset(offset).limit(limit).all()
            
            return sources

    def get_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Hole gruppierte Such-Sessions mit Statistiken"""
        with self.get_session() as session:
            from sqlalchemy import func, distinct
            
            # Gruppiere nach session_id und hole Statistiken
            sessions_query = session.query(
                SearchResult.session_id,
                func.count(SearchResult.id).label('total_searches'),
                func.count(distinct(SearchResult.mine_name)).label('unique_mines'),
                func.count(distinct(SearchResult.model_used)).label('unique_models'),
                func.min(SearchResult.search_timestamp).label('start_time'),
                func.max(SearchResult.search_timestamp).label('end_time'),
                func.avg(SearchResult.search_duration).label('avg_duration')
            ).filter(
                SearchResult.session_id.isnot(None)
            ).group_by(SearchResult.session_id).order_by(
                func.max(SearchResult.search_timestamp).desc()
            ).limit(limit)
            
            sessions_data = []
            for row in sessions_query.all():
                # Hole detaillierte Ergebnisse für diese Session
                session_results = session.query(SearchResult).filter_by(
                    session_id=row.session_id
                ).all()
                
                # Berechne Erfolgsquote und Datenqualität
                successful_searches = 0
                total_fields = 0
                filled_fields = 0
                
                for result in session_results:
                    if result.structured_data:
                        successful_searches += 1
                        data_fields = len(result.structured_data)
                        filled = sum(1 for v in result.structured_data.values() if v and str(v).strip())
                        total_fields += data_fields
                        filled_fields += filled
                
                success_rate = (successful_searches / row.total_searches * 100) if row.total_searches > 0 else 0
                data_quality = (filled_fields / total_fields * 100) if total_fields > 0 else 0
                
                sessions_data.append({
                    'session_id': row.session_id,
                    'total_searches': row.total_searches,
                    'unique_mines': row.unique_mines,
                    'unique_models': row.unique_models,
                    'start_time': row.start_time.isoformat() if row.start_time else None,
                    'end_time': row.end_time.isoformat() if row.end_time else None,
                    'duration_minutes': round((row.end_time - row.start_time).total_seconds() / 60, 1) if row.start_time and row.end_time else 0,
                    'avg_response_time': round(row.avg_duration or 0, 2),
                    'success_rate': round(success_rate, 1),
                    'data_quality': round(data_quality, 1)
                })
            
            return sessions_data

    def get_statistics(self) -> Dict[str, Any]:
        """Hole erweiterte Datenbank-Statistiken mit Model-Performance"""
        with self.get_session() as session:
            from sqlalchemy import func
            
            # ÄNDERUNG 15.07.2025: Frontend-kompatible Statistiken hinzufügen
            total_results = session.query(SearchResult).count()
            successful_results = session.query(SearchResult).filter(
                SearchResult.success == True
            ).count()
            
            # Berechne durchschnittliche Datenqualität aus structured_data
            quality_sum = 0
            quality_count = 0
            for result in session.query(SearchResult).filter(SearchResult.structured_data.isnot(None)).all():
                if result.structured_data:
                    filled = sum(1 for v in result.structured_data.values() if v and str(v).strip())
                    total = len(result.structured_data)
                    if total > 0:
                        quality_sum += (filled / total) * 100
                        quality_count += 1
            
            average_data_quality = (quality_sum / quality_count) if quality_count > 0 else 0
            
            # Ergebnisse nach Modell
            model_counts = session.query(
                SearchResult.model_used, 
                func.count(SearchResult.id)
            ).group_by(SearchResult.model_used).all()
            results_by_model = {model: count for model, count in model_counts}
            
            # Basis-Statistiken
            stats = {
                'total_results': total_results,
                'successful_results': successful_results,
                'average_data_quality': round(average_data_quality, 1),
                'results_by_model': results_by_model,
                'total_sources': session.query(Source).count(),
                'total_search_results': total_results,  # Backward compatibility
                'sources_by_type': {},
                'sources_by_country': {},
                # CLEANUP 24.08.2025: model_performance entfernt - ersetzt durch models array in results/stats
                'field_statistics': {}
            }
            
            # Quellen nach Typ
            type_counts = session.query(Source.source_type, func.count(Source.id)).group_by(Source.source_type).all()
            stats['sources_by_type'] = {type_name: count for type_name, count in type_counts}
            
            # ÄNDERUNG 15.07.2025: Overall success rate für Sources hinzufügen
            total_source_searches = session.query(func.sum(Source.total_searches)).scalar() or 0
            total_source_successes = session.query(func.sum(Source.successful_searches)).scalar() or 0
            stats['overall_success_rate'] = round((total_source_successes / total_source_searches * 100), 1) if total_source_searches > 0 else 0
            
            # Quellen nach Land
            country_counts = session.query(Source.country, func.count(Source.id)).filter(
                Source.country.isnot(None)
            ).group_by(Source.country).all()
            stats['sources_by_country'] = {country: count for country, count in country_counts}
            
            # CLEANUP 24.08.2025: model_performance Generierung ENTFERNT
            # Grund: Veraltete Struktur, ersetzt durch ModelStatisticsComprehensive in /api/results/stats
            # Die neue Struktur liefert nur getestete Modelle mit echten Werten
            # Alle 55 konfigurierten Modelle (inkl. ungetestete mit 0-Werten) sind nicht mehr nötig
            
            # Field-Statistiken
            field_stats = session.query(FieldStatistics).all()
            for field_stat in field_stats:
                if field_stat.field_name not in stats['field_statistics']:
                    stats['field_statistics'][field_stat.field_name] = {}
                
                stats['field_statistics'][field_stat.field_name][field_stat.model_id] = {
                    'success_rate': round((field_stat.success_rate or 0) * 100, 1),
                    'total_searches': field_stat.total_searches,
                    'times_found': field_stat.times_found,
                    'times_empty': field_stat.times_empty,
                    'avg_confidence': round(field_stat.avg_confidence or 0, 2)
                }
            
            return stats

    def get_model_statistics_comprehensive(self) -> List[Dict[str, Any]]:
        """
        Hole alle comprehensive model statistics aus der Datenbank
        Kompatibel mit Frontend statistics-loader.js
        """
        with self.get_session() as session:
            from minesearch.database.models import ModelStatisticsComprehensive
            
            # Hole alle comprehensive statistics
            comprehensive_stats = session.query(ModelStatisticsComprehensive).all()
            
            models_data = []
            for stat in comprehensive_stats:
                models_data.append({
                    'model_name': stat.model_id,  # Frontend erwartet model_name
                    'model_id': stat.model_id,
                    'total_searches': stat.total_searches,
                    'successful_searches': stat.successful_searches,
                    'success_rate': round(stat.success_rate_percent, 1),
                    'avg_fields_filled': round(stat.avg_fields_found, 1),
                    'completeness_score': round(stat.completeness_score, 1),
                    'consistency_score': round(stat.consistency_score, 1),
                    'consistency_grade': stat.consistency_grade,
                    'performance_category': stat.performance_category,
                    'overall_score': round(stat.overall_score, 1),
                    'score_category': stat.score_category,
                    'avg_response_time_ms': round(stat.avg_response_time_ms or 0, 1),
                    'avg_search_duration_ms': round(stat.avg_search_duration_ms or 0, 1),
                    'unique_sources_total': stat.unique_sources_total,
                    'last_search_at': stat.last_search_at.isoformat() if stat.last_search_at else None,
                    'last_updated': stat.last_updated.isoformat() if stat.last_updated else None
                })
            
            logger.info(f"[STATS-DB] Retrieved {len(models_data)} comprehensive model statistics")
            return models_data
    
    def update_model_statistics_comprehensive(self, model_id: str):
        """
        🚀 CRITICAL FIX: Update ModelStatisticsComprehensive nach neuen Searches
        Recalculates comprehensive statistics for specific model from SearchResult table
        """
        logger.info(f"[STATS-UPDATE] Updating comprehensive statistics for model: {model_id}")
        
        with self.get_session() as session:
            try:
                # Query all SearchResult records for this model
                search_results = session.query(SearchResult).filter_by(model_used=model_id).all()
                
                if not search_results:
                    logger.warning(f"[STATS-UPDATE] No search results found for model: {model_id}")
                    return
                
                # Calculate comprehensive metrics
                total_searches = len(search_results)
                successful_searches = sum(1 for r in search_results if r.success)
                success_rate = successful_searches / total_searches if total_searches > 0 else 0.0
                
                # Calculate average response time (skip None values)
                response_times = [r.search_duration for r in search_results if r.search_duration is not None]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
                
                # Calculate data quality metrics
                quality_scores = [r.data_quality for r in search_results if r.data_quality is not None]
                avg_data_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
                
                # CRITICAL FIX 23.08.2025: Calculate avg_fields_found from structured_data directly
                total_filled_fields = 0
                valid_data_searches = 0
                
                for result in search_results:
                    if result.structured_data:
                        try:
                            import json
                            data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                            if isinstance(data, dict):
                                # Count filled fields (exclude N/A, empty strings, null values)
                                na_values = ['N/A', '', None, 'null', 'Unknown', 'Keine Angabe']
                                filled_count = len([v for v in data.values() if v and str(v) not in na_values and not str(v).startswith('_')])
                                total_filled_fields += filled_count
                                valid_data_searches += 1
                        except Exception as e:
                            logger.warning(f"[STATS-UPDATE] Error parsing structured_data for search {result.id}: {e}")
                
                # Calculate actual average fields found
                actual_avg_fields_found = total_filled_fields / valid_data_searches if valid_data_searches > 0 else 0.0
                logger.info(f"[STATS-CALC] Model {model_id}: {total_filled_fields} total fields / {valid_data_searches} searches = {actual_avg_fields_found:.2f} avg_fields_found")
                
                # Count unique sources across all searches
                all_sources = []
                for result in search_results:
                    if result.sources:
                        all_sources.extend([s.get('url', '') for s in result.sources if s.get('url')])
                unique_sources = len(set(all_sources))
                
                # Extract provider from model_id
                provider = model_id.split(':')[0] if ':' in model_id else 'unknown'
                
                # Calculate overall score (simplified version of revolutionary scoring)
                # CRITICAL FIX 23.08.2025: Use actual_avg_fields_found for completeness calculation
                total_expected_fields = 19  # Based on CSV_COLUMNS structure
                field_completeness = (actual_avg_fields_found / total_expected_fields) * 100 if total_expected_fields > 0 else 0
                
                field_quality_score = field_completeness  # Use actual field completeness
                consistency_score = success_rate * 100  # Success rate as consistency
                speed_score = max(0, 100 - (avg_response_time * 2)) if avg_response_time > 0 else 100  # Penalty for slow responses
                cost_efficiency_score = 85  # Default good score, could be improved with actual cost data
                trustworthiness_score = min(80 + (unique_sources * 2), 100)  # More sources = more trustworthy
                
                overall_score = (
                    field_quality_score * 0.25 +
                    consistency_score * 0.25 +
                    speed_score * 0.25 +
                    cost_efficiency_score * 0.20 +
                    trustworthiness_score * 0.05
                )
                
                # Update or create ModelStatisticsComprehensive record
                existing = session.query(ModelStatisticsComprehensive).filter_by(model_id=model_id).first()
                
                if existing:
                    # Update existing record
                    existing.total_searches = total_searches
                    existing.successful_searches = successful_searches
                    existing.success_rate_percent = success_rate * 100  # Convert to percentage
                    existing.avg_response_time_ms = avg_response_time * 1000 if avg_response_time else 0
                    # CRITICAL FIX 23.08.2025: Use actual calculated avg_fields_found
                    existing.avg_fields_found = actual_avg_fields_found
                    existing.completeness_score = field_completeness
                    existing.consistency_score = consistency_score  
                    existing.unique_sources_total = unique_sources
                    existing.overall_score = overall_score
                    
                    logger.info(f"[STATS-UPDATE] Updated existing record for {model_id}: "
                              f"{total_searches} searches, {success_rate:.1%} success, score: {overall_score:.1f}")
                else:
                    # Create new record
                    new_stats = ModelStatisticsComprehensive(
                        model_id=model_id,
                        total_searches=total_searches,
                        successful_searches=successful_searches,
                        success_rate_percent=success_rate * 100,  # Convert to percentage
                        avg_response_time_ms=avg_response_time * 1000 if avg_response_time else 0,
                        # CRITICAL FIX 23.08.2025: Use actual calculated avg_fields_found
                        avg_fields_found=actual_avg_fields_found,
                        completeness_score=field_completeness,
                        consistency_score=consistency_score,
                        unique_sources_total=unique_sources,
                        overall_score=overall_score
                    )
                    session.add(new_stats)
                    
                    logger.info(f"[STATS-UPDATE] Created new record for {model_id}: "
                              f"{total_searches} searches, {success_rate:.1%} success, score: {overall_score:.1f}")
                
                session.commit()
                logger.info(f"[STATS-UPDATE] Successfully updated comprehensive statistics for {model_id}")
                
            except Exception as e:
                logger.error(f"[STATS-UPDATE] Error updating statistics for {model_id}: {e}")
                session.rollback()
                raise
    
    def get_recent_search_results(self, mine_name: str, hours_back: int = 24, limit: int = 10, session_id: Optional[str] = None) -> List[SearchResult]:
        """
        SESSION-ISOLATION FIX 30.08.2025: Hole existierende Suchergebnisse mit optionaler Session-Filterung
        
        Args:
            mine_name: Name der Mine
            hours_back: Anzahl Stunden zurück zu suchen
            limit: Maximale Anzahl Ergebnisse
            session_id: Optional - Filter nach spezifischer Session für Batch-Isolation
            
        Returns:
            Liste von SearchResult-Objekten
        """
        with self.get_session() as session:
            from sqlalchemy import and_
            
            # Use timezone-aware datetime and convert to naive for consistent DB comparison
            cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours_back)
            
            # BASIS-FILTER: Mine, Zeit, Erfolg, structured_data
            filters = [
                SearchResult.mine_name == mine_name,
                SearchResult.created_at >= cutoff_time,
                SearchResult.success == True,
                SearchResult.structured_data.isnot(None)
            ]
            
            # SESSION-ISOLATION FIX: Füge Session-Filter hinzu wenn angegeben
            if session_id:
                filters.append(SearchResult.session_id == session_id)
                logger.info(f"[SESSION-ISOLATION] Filtering results for session: {session_id}")
            else:
                logger.warning(f"[SESSION-ISOLATION] NO session filter - will return results from ALL sessions!")
            
            results = session.query(SearchResult).filter(
                and_(*filters)
            ).order_by(
                SearchResult.created_at.desc()
            ).limit(limit).all()
            
            logger.info(f"[SESSION-ISOLATION] Found {len(results)} results for mine='{mine_name}', session='{session_id or 'ALL'}'")
            return results