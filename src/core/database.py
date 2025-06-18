"""
Datenbank-Schema und Models für Mining Research System
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime
from pathlib import Path
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
    search_id = Column(Integer, ForeignKey('searches.id'), nullable=False)
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
        
        # Erstelle Engine
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=False
        )
        
        # Erstelle Tabellen
        Base.metadata.create_all(bind=self.engine)
        
        # Session Factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Datenbank initialisiert: {db_path}")
    
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
    
    def get_or_create_mine(self, name: str, region: str, country: str, languages: list) -> Mine:
        """Holt existierende Mine oder erstellt neue"""
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
            
            return mine
    
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
    
    def add_result(self, search_id: int, mine_id: int, result_data: dict):
        """Fügt ein Suchergebnis hinzu"""
        with self.get_session() as session:
            result = Result(
                search_id=search_id,
                mine_id=mine_id,
                field_name=result_data['field_name'],
                value=result_data['value'],
                source=result_data['source'],
                source_url=result_data.get('source_url'),
                source_date=result_data.get('source_date'),
                confidence_score=result_data['confidence_score'],
                agent_name=result_data['agent_name'],
                extra_data=result_data.get('metadata', {})
            )
            session.add(result)
            session.commit()
    
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


# Singleton Instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Gibt die globale DatabaseManager Instanz zurück"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager