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
from datetime import datetime
from urllib.parse import urlparse

from config import Config
from .models import Base, Source, SearchResult, ModelStatistics, FieldConsistency, ModelSummary, FieldStatistics

logger = logging.getLogger(__name__)


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

    def cleanup_old_results(self, days: int = 30):
        """Lösche alte Suchergebnisse"""
        from sqlalchemy import func
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        
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

    def get_statistics(self) -> Dict[str, Any]:
        """Hole Datenbank-Statistiken"""
        with self.get_session() as session:
            stats = {
                'total_sources': session.query(Source).count(),
                'total_search_results': session.query(SearchResult).count(),
                'sources_by_type': {},
                'sources_by_country': {},
            }
            
            # Quellen nach Typ
            from sqlalchemy import func
            type_counts = session.query(Source.source_type, func.count(Source.id)).group_by(Source.source_type).all()
            stats['sources_by_type'] = {type_name: count for type_name, count in type_counts}
            
            # Quellen nach Land
            country_counts = session.query(Source.country, func.count(Source.id)).filter(
                Source.country.isnot(None)
            ).group_by(Source.country).all()
            stats['sources_by_country'] = {country: count for country, count in country_counts}
            
            return stats