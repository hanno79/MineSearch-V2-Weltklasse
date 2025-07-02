"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Datenbank-Schema und -Verwaltung für MineSearch v2
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from config import Config

logger = logging.getLogger(__name__)

# Datenbank-Basis
Base = declarative_base()

class Source(Base):
    """Datenbank-Tabelle für Mining-Quellen"""
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    source_type = Column(String(50), nullable=False, default='unknown')  # government, exchange, industry, database, document
    reliability_score = Column(Float, nullable=False, default=50.0)
    
    # Zugriffs-Statistiken
    last_successful_access = Column(DateTime, nullable=True)
    last_attempted_access = Column(DateTime, nullable=True)
    total_searches = Column(Integer, nullable=False, default=0)
    successful_searches = Column(Integer, nullable=False, default=0)
    
    # Metadaten
    typical_content_types = Column(JSON, nullable=True)  # ['pdf', 'html', 'api', etc.]
    extra_metadata = Column(JSON, nullable=True)  # Zusätzliche Informationen
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_country_region', 'country', 'region'),
        Index('idx_source_type_score', 'source_type', 'reliability_score'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'url': self.url,
            'domain': self.domain,
            'country': self.country,
            'region': self.region,
            'source_type': self.source_type,
            'reliability_score': self.reliability_score,
            'last_successful_access': self.last_successful_access.isoformat() if self.last_successful_access else None,
            'last_attempted_access': self.last_attempted_access.isoformat() if self.last_attempted_access else None,
            'total_searches': self.total_searches,
            'successful_searches': self.successful_searches,
            'success_rate': (self.successful_searches / self.total_searches * 100) if self.total_searches > 0 else 0,
            'typical_content_types': self.typical_content_types or [],
            'metadata': self.extra_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SearchResult(Base):
    """Datenbank-Tabelle für Suchergebnisse"""
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=True, index=True)  # Für Batch-Gruppierung
    mine_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    commodity = Column(String(100), nullable=True)
    
    # Such-Metadaten
    search_timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    model_used = Column(String(50), nullable=False)
    search_type = Column(String(50), nullable=True)  # standard, enhanced, deep-research
    search_duration = Column(Float, nullable=True)  # Sekunden
    
    # Ergebnisse
    structured_data = Column(JSON, nullable=True)  # Alle extrahierten Felder
    structured_data_with_sources = Column(JSON, nullable=True)  # Mit Quellennummern
    sources = Column(JSON, nullable=True)  # Gefundene Quellen
    source_index = Column(JSON, nullable=True)  # Quellen-Index
    
    # Qualitätsmetriken
    data_quality = Column(JSON, nullable=True)  # Qualitäts-Informationen
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Source Discovery Session
    source_discovery_session = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_search_results_mine_country', 'mine_name', 'country'),
        Index('idx_search_results_session', 'session_id'),
        Index('idx_search_results_timestamp', 'search_timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'mine_name': self.mine_name,
            'country': self.country,
            'region': self.region,
            'commodity': self.commodity,
            'search_timestamp': self.search_timestamp.isoformat() if self.search_timestamp else None,
            'model_used': self.model_used,
            'search_type': self.search_type,
            'search_duration': self.search_duration,
            'structured_data': self.structured_data or {},
            'structured_data_with_sources': self.structured_data_with_sources or {},
            'sources': self.sources or [],
            'source_index': self.source_index or {},
            'data_quality': self.data_quality or {},
            'success': self.success,
            'error_message': self.error_message,
            'source_discovery_session': self.source_discovery_session or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_access(self, success: bool, content_type: Optional[str] = None):
        """Aktualisiere Zugriffs-Statistiken"""
        self.last_attempted_access = datetime.now()
        self.total_searches += 1
        
        if success:
            self.last_successful_access = datetime.now()
            self.successful_searches += 1
            
            # Aktualisiere Content-Types
            if content_type and self.typical_content_types is not None:
                if content_type not in self.typical_content_types:
                    self.typical_content_types.append(content_type)
        
        # Berechne neue Zuverlässigkeit (einfache Formel)
        if self.total_searches >= 5:  # Mindestens 5 Versuche für aussagekräftige Statistik
            self.reliability_score = min(100.0, (self.successful_searches / self.total_searches) * 100)


class DatabaseManager:
    """Verwaltung der Datenbankverbindung und -operationen"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(
            self.database_url, 
            echo=False,  # Setze auf True für SQL-Debugging
            connect_args={"check_same_thread": False}  # Nur für SQLite
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Erstelle Tabellen wenn nicht vorhanden
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Datenbank initialisiert: {self.database_url}")
    
    def get_session(self) -> Session:
        """Hole eine neue Datenbank-Session"""
        return self.SessionLocal()
    
    def add_or_update_source(self, url: str, domain: str, country: Optional[str] = None,
                            region: Optional[str] = None, source_type: str = 'unknown',
                            metadata: Optional[Dict[str, Any]] = None) -> Source:
        """Füge neue Quelle hinzu oder aktualisiere bestehende"""
        with self.get_session() as session:
            # Prüfe ob Quelle bereits existiert
            source = session.query(Source).filter_by(url=url).first()
            
            if source:
                # Aktualisiere bestehende Quelle
                if country and not source.country:
                    source.country = country
                if region and not source.region:
                    source.region = region
                if source_type != 'unknown' and source.source_type == 'unknown':
                    source.source_type = source_type
                if metadata:
                    source.extra_metadata = {**(source.extra_metadata or {}), **metadata}
            else:
                # Erstelle neue Quelle
                source = Source(
                    url=url,
                    domain=domain,
                    country=country,
                    region=region,
                    source_type=source_type,
                    extra_metadata=metadata
                )
                session.add(source)
            
            session.commit()
            session.refresh(source)
            return source
    
    def get_sources_for_search(self, country: Optional[str] = None, region: Optional[str] = None,
                              min_reliability: float = 30.0, limit: int = 50) -> List[Source]:
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
            
            # Sortiere nach Zuverlässigkeit und Erfolgsquote
            sources = query.order_by(
                Source.reliability_score.desc(),
                Source.successful_searches.desc()
            ).limit(limit).all()
            
            return sources
    
    def update_source_statistics(self, url: str, success: bool, content_type: Optional[str] = None):
        """Aktualisiere Statistiken nach einer Suche"""
        with self.get_session() as session:
            source = session.query(Source).filter_by(url=url).first()
            if source:
                source.update_access(success, content_type)
                session.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hole Gesamt-Statistiken"""
        with self.get_session() as session:
            total_sources = session.query(Source).count()
            
            # Quellen pro Land
            country_stats = session.query(
                Source.country, 
                func.count(Source.id)
            ).group_by(Source.country).all()
            
            # Top Quellen
            top_sources = session.query(Source).order_by(
                Source.reliability_score.desc()
            ).limit(10).all()
            
            # Erfolgsraten
            avg_success_rate = session.query(
                func.avg(Source.successful_searches * 100.0 / Source.total_searches)
            ).filter(Source.total_searches > 0).scalar() or 0
            
            return {
                'total_sources': total_sources,
                'sources_by_country': {
                    country or 'Global': count for country, count in country_stats
                },
                'top_sources': [source.to_dict() for source in top_sources],
                'average_success_rate': round(avg_success_rate, 2)
            }
    
    # ÄNDERUNG 02.07.2025: Methoden für SearchResult Management
    def save_search_result(self, result_data: Dict[str, Any]) -> SearchResult:
        """Speichere ein Suchergebnis in der Datenbank"""
        with self.get_session() as session:
            search_result = SearchResult(
                session_id=result_data.get('session_id'),
                mine_name=result_data['mine_name'],
                country=result_data.get('country'),
                region=result_data.get('region'),
                commodity=result_data.get('commodity'),
                model_used=result_data['model_used'],
                search_type=result_data.get('search_type'),
                search_duration=result_data.get('search_duration'),
                structured_data=result_data.get('structured_data'),
                structured_data_with_sources=result_data.get('structured_data_with_sources'),
                sources=result_data.get('sources'),
                source_index=result_data.get('source_index'),
                data_quality=result_data.get('data_quality'),
                success=result_data.get('success', True),
                error_message=result_data.get('error_message'),
                source_discovery_session=result_data.get('source_discovery_session')
            )
            session.add(search_result)
            session.commit()
            logger.info(f"[DB] Suchergebnis gespeichert: {search_result.mine_name} (ID: {search_result.id})")
            return search_result
    
    def get_search_results(self, limit: int = 50, offset: int = 0, 
                          mine_name: Optional[str] = None,
                          country: Optional[str] = None,
                          session_id: Optional[str] = None,
                          days_back: Optional[int] = None) -> List[SearchResult]:
        """Hole Suchergebnisse mit Filtern"""
        with self.get_session() as session:
            query = session.query(SearchResult)
            
            if mine_name:
                query = query.filter(SearchResult.mine_name.ilike(f'%{mine_name}%'))
            if country:
                query = query.filter(SearchResult.country == country)
            if session_id:
                query = query.filter(SearchResult.session_id == session_id)
            if days_back:
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(days=days_back)
                query = query.filter(SearchResult.search_timestamp >= cutoff)
            
            results = query.order_by(
                SearchResult.search_timestamp.desc()
            ).offset(offset).limit(limit).all()
            
            return results
    
    def get_search_result_by_id(self, result_id: int) -> Optional[SearchResult]:
        """Hole einzelnes Suchergebnis nach ID"""
        with self.get_session() as session:
            return session.query(SearchResult).filter_by(id=result_id).first()
    
    def get_result_statistics(self) -> Dict[str, Any]:
        """Hole Statistiken über gespeicherte Ergebnisse"""
        with self.get_session() as session:
            total = session.query(SearchResult).count()
            successful = session.query(SearchResult).filter(SearchResult.success == True).count()
            
            # Ergebnisse nach Modell
            by_model = {}
            model_counts = session.query(
                SearchResult.model_used,
                func.count(SearchResult.id)
            ).group_by(SearchResult.model_used).all()
            
            for model, count in model_counts:
                by_model[model] = count
            
            # Durchschnittliche Datenqualität
            avg_quality = session.query(
                func.avg(
                    func.json_extract(SearchResult.data_quality, '$.completeness_percentage')
                )
            ).filter(SearchResult.success == True).scalar() or 0
            
            # Letzte Suchen
            recent = session.query(SearchResult).order_by(
                SearchResult.search_timestamp.desc()
            ).limit(10).all()
            
            return {
                'total_results': total,
                'successful_results': successful,
                'results_by_model': by_model,
                'average_data_quality': float(avg_quality),
                'recent_searches': [r.to_dict() for r in recent]
            }
    
    def get_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Hole gruppierte Sessions"""
        with self.get_session() as session:
            # Gruppiere nach session_id
            sessions = session.query(
                SearchResult.session_id,
                func.count(SearchResult.id).label('count'),
                func.min(SearchResult.search_timestamp).label('start_time'),
                func.max(SearchResult.search_timestamp).label('end_time')
            ).filter(
                SearchResult.session_id.isnot(None)
            ).group_by(
                SearchResult.session_id
            ).order_by(
                func.max(SearchResult.search_timestamp).desc()
            ).limit(limit).all()
            
            result = []
            for sess_id, count, start, end in sessions:
                # Hole erste Mine als Beispiel
                first_result = session.query(SearchResult).filter_by(
                    session_id=sess_id
                ).first()
                
                result.append({
                    'session_id': sess_id,
                    'mine_count': count,
                    'start_time': start.isoformat() if start else None,
                    'end_time': end.isoformat() if end else None,
                    'example_mine': first_result.mine_name if first_result else None
                })
            
            return result


# Globale Datenbank-Instanz
db_manager = DatabaseManager()