"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Datenbank-Schema und Models für Mining Research System
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

from .config import Config

Base = declarative_base()
logger = logging.getLogger(__name__)


class Mine(Base):
    """Mine Entität"""
    __tablename__ = 'mines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    region = Column(String(255))
    country = Column(String(100))
    languages = Column(JSON)  # Liste von Sprachen
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    searches = relationship("Search", back_populates="mine", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="mine", cascade="all, delete-orphan")


class Search(Base):
    """Suchlauf für eine Mine"""
    __tablename__ = 'searches'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50), default='running')  # running, completed, failed
    agents_used = Column(JSON)  # Liste der verwendeten Agenten
    total_results = Column(Integer, default=0)
    success_rate = Column(Float)
    
    # Relationships
    mine = relationship("Mine", back_populates="searches")
    results = relationship("Result", back_populates="search", cascade="all, delete-orphan")


class Result(Base):
    """Einzelnes Suchergebnis"""
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    search_id = Column(Integer, ForeignKey('searches.id'), nullable=True)  # ÄNDERUNG 21.06.2025: Nullable für direkte Speicherung
    field_name = Column(String(100), nullable=False, index=True)
    value = Column(Text)
    source = Column(String(255))
    source_url = Column(Text)
    source_date = Column(Integer)  # Jahr
    confidence_score = Column(Float)
    agent_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON)
    
    # Relationships
    mine = relationship("Mine", back_populates="results")
    search = relationship("Search", back_populates="results")


class AggregatedData(Base):
    """Aggregierte Daten für eine Mine"""
    __tablename__ = 'aggregated_data'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False, unique=True)
    data = Column(JSON)  # Vollständige aggregierte Daten
    last_updated = Column(DateTime, default=datetime.utcnow)
    quality_score = Column(Float)
    completeness_score = Column(Float)
    
    # Relationship
    mine = relationship("Mine")


class DatabaseManager:
    """Manager für Datenbank-Operationen"""
    
    def __init__(self):
        self.config = Config()
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self):
        """Initialisiert die Datenbank"""
        # Stelle sicher, dass das Verzeichnis existiert
        db_path = Path('data/minesearch.db')
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ÄNDERUNG 21.06.2025: Erweiterte SQLite-Konfiguration für bessere Schreibrechte
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={
                'check_same_thread': False,
                'timeout': 30.0  # Erhöhe Timeout für Lock-Konflikte
            },
            poolclass=StaticPool,
            echo=False
        )
        
        # ÄNDERUNG 21.06.2025: Aktiviere WAL-Mode für bessere Concurrency und Schreibrechte
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA busy_timeout=30000"))  # 30 Sekunden Timeout
            conn.commit()
        
        # ÄNDERUNG 21.06.2025: Importiere erweiterte Models
        from .database_extensions import Source, AgentResult, ContentCache, SourceDiscoveryLog
        
        # Erstelle Tabellen
        Base.metadata.create_all(bind=self.engine)
        
        # Session Factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Datenbank initialisiert: {db_path} (WAL-Mode aktiviert)")
    
    def get_session(self) -> Session:
        """Gibt eine neue Session zurück"""
        if not self.SessionLocal:
            self.initialize()
        return self.SessionLocal()
    
    def create_mine(self, name: str, region: str, country: str, languages: list) -> Mine:
        """Erstellt eine neue Mine"""
        with self.get_session() as session:
            mine = Mine(
                name=name,
                region=region,
                country=country,
                languages=languages
            )
            session.add(mine)
            session.commit()
            session.refresh(mine)
            return mine
    
    def get_or_create_mine(self, name: str, region: str, country: str, languages: list) -> int:
        """Holt existierende Mine oder erstellt neue und gibt ID zurück"""
        # ÄNDERUNG 21.06.2025: Return ID statt Mine-Objekt für konsistente Verwendung
        with self.get_session() as session:
            mine = session.query(Mine).filter_by(
                name=name,
                region=region,
                country=country
            ).first()
            
            if not mine:
                mine = Mine(
                    name=name,
                    region=region,
                    country=country,
                    languages=languages
                )
                session.add(mine)
                session.commit()
                session.refresh(mine)
            
            return mine.id
    
    def create_search(self, mine_id: int, agents: list) -> Search:
        """Erstellt einen neuen Suchlauf"""
        with self.get_session() as session:
            search = Search(
                mine_id=mine_id,
                agents_used=agents
            )
            session.add(search)
            session.commit()
            session.refresh(search)
            return search
    
    def add_result(self, mine_id: int, agent_name: str, field_name: str, 
                  value: str, source: str, source_url: str = None,
                  source_date: int = None, confidence_score: float = 0.5,
                  extra_data: dict = None):
        """Fügt ein Suchergebnis direkt hinzu"""
        # ÄNDERUNG 21.06.2025: Vereinfachte Signatur für direkten Aufruf
        with self.get_session() as session:
            result = Result(
                mine_id=mine_id,
                search_id=None,  # ÄNDERUNG 21.06.2025: Setze search_id auf None für direkte Speicherung
                field_name=field_name,
                value=value,
                source=source,
                source_url=source_url,
                source_date=source_date,
                confidence_score=confidence_score,
                agent_name=agent_name,
                extra_data=extra_data or {}
            )
            session.add(result)
            session.commit()
            logger.info(f"DEBUG: Ergebnis gespeichert - Mine: {mine_id}, Field: {field_name}, Value: {value[:50]}...")
    
    def complete_search(self, search_id: int, status: str = 'completed'):
        """Markiert einen Suchlauf als abgeschlossen"""
        with self.get_session() as session:
            search = session.query(Search).filter_by(id=search_id).first()
            if search:
                search.completed_at = datetime.utcnow()
                search.status = status
                
                # Berechne Erfolgsrate
                total_results = session.query(Result).filter_by(search_id=search_id).count()
                search.total_results = total_results
                
                session.commit()
    
    def get_mine_results(self, mine_id: int) -> list:
        """Holt alle Ergebnisse für eine Mine"""
        with self.get_session() as session:
            results = session.query(Result).filter_by(mine_id=mine_id).all()
            return [r for r in results]
    
    def get_latest_search(self, mine_id: int) -> Search:
        """Holt den neuesten Suchlauf für eine Mine"""
        with self.get_session() as session:
            return session.query(Search).filter_by(
                mine_id=mine_id
            ).order_by(Search.started_at.desc()).first()
    
    def update_aggregated_data(self, mine_id: int, aggregated_data: dict, 
                             quality_score: float, completeness_score: float):
        """Aktualisiert aggregierte Daten für eine Mine"""
        with self.get_session() as session:
            agg_data = session.query(AggregatedData).filter_by(mine_id=mine_id).first()
            
            if not agg_data:
                agg_data = AggregatedData(mine_id=mine_id)
                session.add(agg_data)
            
            agg_data.data = aggregated_data
            agg_data.quality_score = quality_score
            agg_data.completeness_score = completeness_score
            agg_data.last_updated = datetime.utcnow()
            
            session.commit()
    
    # ÄNDERUNG 21.06.2025: Neue Methoden für Source Management
    def add_source(self, mine_id: int, source_data: dict) -> int:
        """Fügt eine neue Quelle hinzu oder aktualisiert bestehende"""
        from .database_extensions import Source
        
        with self.get_session() as session:
            # Prüfe ob URL bereits existiert
            existing = session.query(Source).filter_by(url=source_data['url']).first()
            
            if existing:
                # Aktualisiere Relevanz-Score wenn höher
                if source_data.get('reliability_score', 0) > existing.reliability_score:
                    existing.reliability_score = source_data['reliability_score']
                existing.last_crawled = datetime.utcnow()
                session.commit()
                return existing.id
            
            # Erstelle neue Quelle
            source = Source(
                url=source_data['url'],
                title=source_data.get('title'),
                source_type=source_data['source_type'],
                mine_id=mine_id,
                discovered_by=source_data.get('discovered_by'),
                reliability_score=source_data.get('reliability_score', 0.5),
                meta_data=source_data.get('metadata', {})
            )
            session.add(source)
            session.commit()
            session.refresh(source)
            return source.id
    
    def get_sources_for_mine(self, mine_id: int, source_type: str = None) -> list:
        """Holt alle Quellen für eine Mine"""
        from .database_extensions import Source
        
        with self.get_session() as session:
            query = session.query(Source).filter_by(mine_id=mine_id)
            
            if source_type:
                query = query.filter_by(source_type=source_type)
            
            return query.order_by(Source.reliability_score.desc()).all()
    
    def add_agent_result(self, agent_name: str, mine_id: int, source_id: int, 
                        field_name: str, value: str, confidence: float = 0.5,
                        meta_data: dict = None):
        """Fügt ein Agent-spezifisches Ergebnis hinzu"""
        from .database_extensions import AgentResult
        
        with self.get_session() as session:
            result = AgentResult(
                agent_name=agent_name,
                mine_id=mine_id,
                source_id=source_id,
                field_name=field_name,
                value=value,
                confidence=confidence,
                meta_data=meta_data or {}
            )
            session.add(result)
            session.commit()
    
    def get_agent_results(self, mine_id: int, agent_name: str = None) -> list:
        """Holt Agent-spezifische Ergebnisse"""
        from .database_extensions import AgentResult
        
        with self.get_session() as session:
            query = session.query(AgentResult).filter_by(mine_id=mine_id)
            
            if agent_name:
                query = query.filter_by(agent_name=agent_name)
            
            return query.order_by(AgentResult.confidence.desc()).all()
    
    def cache_content(self, url: str, content: str, content_type: str = 'html',
                     expires_hours: int = 24):
        """Cached Webseiten-Inhalt"""
        from .database_extensions import ContentCache
        
        with self.get_session() as session:
            # Prüfe ob bereits gecached
            existing = session.query(ContentCache).filter_by(url=url).first()
            
            if existing:
                existing.content = content
                existing.cached_at = datetime.utcnow()
                existing.expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
                existing.access_count += 1
            else:
                cache = ContentCache(
                    url=url,
                    content=content,
                    content_type=content_type,
                    expires_at=datetime.utcnow() + timedelta(hours=expires_hours)
                )
                session.add(cache)
            
            session.commit()
    
    def get_cached_content(self, url: str) -> Optional[str]:
        """Holt gecachten Content wenn noch gültig"""
        from .database_extensions import ContentCache
        
        with self.get_session() as session:
            cache = session.query(ContentCache).filter_by(url=url).first()
            
            if cache and cache.expires_at > datetime.utcnow():
                cache.access_count += 1
                session.commit()
                return cache.content
            
            return None


# Singleton Instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Gibt die globale DatabaseManager Instanz zurück"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager