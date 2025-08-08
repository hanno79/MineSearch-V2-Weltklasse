"""
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: DatabaseManager Klasse für MineSearch v2 (extrahiert aus database.py)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse

from minesearch.config.base import config
from .models import Base, Source, SearchResult, ModelStatistics, FieldConsistency, ModelSummary, FieldStatistics

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
            except Exception:
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
                          **kwargs) -> SearchResult:
        """Speichere Suchergebnis in der Datenbank"""
        result = SearchResult(
            mine_name=mine_name,
            model_used=model_used,
            structured_data=structured_data,
            sources=sources,
            session_id=session_id,
            **kwargs
        )
        
        with self.get_session() as session:
            session.add(result)
            session.commit()
            session.refresh(result)
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
                'model_performance': {},
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
            
            # Model-Performance aus aggregierten ModelStatistics + alle konfigurierten Modelle
            from sqlalchemy import cast, Float
            from minesearch.config.providers import PROVIDERS_CONFIG
            
            # Hole alle konfigurierten Modelle
            all_configured_models = []
            for provider_name, config in PROVIDERS_CONFIG.items():
                if config.get('enabled', False):
                    for model in config.get('models', []):
                        all_configured_models.append(f'{provider_name}:{model}')
            
            # Hole getestete Modelle
            model_stats_query = session.query(
                ModelStatistics.model_id,
                func.count(ModelStatistics.id).label('total_tests'),
                func.avg(cast(ModelStatistics.success, Float)).label('success_rate'),
                func.avg(ModelStatistics.fields_found).label('avg_fields'),
                func.avg(ModelStatistics.response_time_ms).label('avg_response_time'),
                func.max(ModelStatistics.timestamp).label('last_test')
            ).group_by(ModelStatistics.model_id).all()
            
            # Erstelle Dict mit getesteten Modellen
            tested_models = {}
            for model_stat in model_stats_query:
                # KORRIGIERT 15.07.2025: success_rate ist bereits 0.0-1.0, nicht nochmal * 100
                success_rate_pct = (model_stat.success_rate or 0) * 100
                reliability_score = success_rate_pct * 0.7 + (model_stat.avg_fields / 19.0 * 100) * 0.3
                
                tested_models[model_stat.model_id] = {
                    'total_tests': model_stat.total_tests,
                    'average_success_rate': round(success_rate_pct, 1),
                    'average_fields_found': round(model_stat.avg_fields or 0, 1),
                    'reliability_score': round(reliability_score, 1),
                    'average_response_time': round((model_stat.avg_response_time or 0) / 1000, 2),
                    'last_updated': model_stat.last_test.isoformat() if model_stat.last_test else None,
                    'status': 'tested'
                }
            
            # Füge alle konfigurierten Modelle hinzu (auch ungetestete)
            for model_id in all_configured_models:
                if model_id in tested_models:
                    stats['model_performance'][model_id] = tested_models[model_id]
                else:
                    # Ungetestetes Modell
                    stats['model_performance'][model_id] = {
                        'total_tests': 0,
                        'average_success_rate': 0.0,
                        'average_fields_found': 0.0,
                        'reliability_score': 0.0,
                        'average_response_time': 0.0,
                        'last_updated': None,
                        'status': 'not_tested'
                    }
            
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