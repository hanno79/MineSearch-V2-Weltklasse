"""
Author: rahn
Datum: 21.06.2025
Version: 1.0
Beschreibung: Erweiterungen für das Datenbank-Schema (Sources und Agent Results)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Index, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Source(Base):
    """Gefundene Informationsquellen für Minen"""
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    url = Column(Text, nullable=False, unique=True)
    title = Column(Text)
    source_type = Column(String(50), nullable=False)  # website, pdf, api, database, news, government
    mine_id = Column(Integer, ForeignKey('mines.id'))
    discovered_by = Column(String(100))  # Agent der die Quelle gefunden hat
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_crawled = Column(DateTime)
    content_hash = Column(String(64))  # SHA256 Hash des Inhalts
    reliability_score = Column(Float, default=0.5)
    meta_data = Column(JSON)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('source_type IN ("website", "pdf", "api", "database", "news", "government", "technical_report", "company")', 
                       name='check_source_type'),
        Index('idx_source_type', 'source_type'),
        Index('idx_mine_source', 'mine_id', 'source_type'),
    )
    
    # Relationships
    mine = relationship("Mine")
    agent_results = relationship("AgentResult", back_populates="source")


class AgentResult(Base):
    """Ergebnisse einzelner Agenten mit Quellenbezug"""
    __tablename__ = 'agent_results'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100), nullable=False)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    source_id = Column(Integer, ForeignKey('sources.id'))
    field_name = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    validation_status = Column(String(20), default='pending')  # pending, validated, rejected
    meta_data = Column(JSON)
    
    # Indices für Performance
    __table_args__ = (
        Index('idx_agent_mine', 'agent_name', 'mine_id'),
        Index('idx_field', 'field_name'),
        Index('idx_validation', 'validation_status'),
    )
    
    # Relationships
    mine = relationship("Mine")
    source = relationship("Source", back_populates="agent_results")


class ContentCache(Base):
    """Cache für geladene Webseiten-Inhalte"""
    __tablename__ = 'content_cache'
    
    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False)
    content = Column(Text)
    content_type = Column(String(50))
    headers = Column(JSON)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    access_count = Column(Integer, default=1)
    
    # Indices
    __table_args__ = (
        Index('idx_url', 'url'),
        Index('idx_expires', 'expires_at'),
    )


class SourceDiscoveryLog(Base):
    """Log für Source Discovery Prozess"""
    __tablename__ = 'source_discovery_logs'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    discovery_run_id = Column(String(36))  # UUID für einen Discovery Run
    discovered_at = Column(DateTime, default=datetime.utcnow)
    agent_name = Column(String(100))
    sources_found = Column(Integer, default=0)
    execution_time = Column(Float)  # Sekunden
    meta_data = Column(JSON)
    
    # Relationships
    mine = relationship("Mine")
    
    # Index
    __table_args__ = (
        Index('idx_discovery_run', 'discovery_run_id'),
    )