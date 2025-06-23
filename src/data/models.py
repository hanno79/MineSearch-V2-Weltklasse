"""
Datenbankmodelle für MineSearch
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Mine(Base):
    """Mine Entität"""
    __tablename__ = 'mines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    region = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Beziehungen
    search_results = relationship("SearchResultDB", back_populates="mine", cascade="all, delete-orphan")
    searches = relationship("Search", back_populates="mine", cascade="all, delete-orphan")


class SearchResultDB(Base):
    """Suchergebnis von Agenten (Datenbank-Modell)"""
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    source = Column(String(255))
    source_url = Column(Text)
    source_date = Column(Integer)  # Jahr
    confidence_score = Column(Float)
    agent_name = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)
    
    # Beziehungen
    mine = relationship("Mine", back_populates="search_results")
    
    def to_dict(self):
        """Konvertiert zu Dictionary"""
        return {
            'id': self.id,
            'mine_id': self.mine_id,
            'field_name': self.field_name,
            'value': self.value,
            'source': self.source,
            'source_url': self.source_url,
            'source_date': self.source_date,
            'confidence_score': self.confidence_score,
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metadata': self.extra_data
        }


class Search(Base):
    """Such-Session"""
    __tablename__ = 'searches'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    agents_used = Column(JSON, default=list)
    results_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Beziehungen
    mine = relationship("Mine", back_populates="searches")

# Alias für Kompatibilität
SearchSession = Search


class AgentStatistics(Base):
    """Statistiken für Agenten"""
    __tablename__ = 'agent_statistics'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(50), nullable=False, unique=True)
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_fields_found = Column(Integer, default=0)
    average_confidence = Column(Float, default=0.0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FieldDefinition(Base):
    """Definition der möglichen Felder"""
    __tablename__ = 'field_definitions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255))
    description = Column(Text)
    data_type = Column(String(50))  # string, number, coordinates, etc.
    is_required = Column(Boolean, default=False)
    validation_regex = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)