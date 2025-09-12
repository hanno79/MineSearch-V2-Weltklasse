"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Search-Modelle für MineSearch v2 (aufgeteilt aus models.py)
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Text, Boolean, 
    Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .models_base import Base


class SearchResult(Base):
    """Datenbank-Tabelle für Suchergebnisse"""
    __tablename__ = 'search_results'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), ForeignKey('search_sessions.session_id'), nullable=False, index=True)
    mine_name = Column(String(255), nullable=False, index=True)
    model_id = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)

    # Extraktions-Ergebnisse
    field_name = Column(String(100), nullable=False, index=True)
    extracted_value = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    extraction_method = Column(String(50), nullable=True)  # direct, inferred, calculated

    # Quelle und Kontext
    source_url = Column(String(500), nullable=True, index=True)
    source_domain = Column(String(255), nullable=True, index=True)
    extraction_context = Column(Text, nullable=True)

    # Qualitätsbewertung
    is_placeholder = Column(Boolean, nullable=False, default=False)
    is_fallback = Column(Boolean, nullable=False, default=False)
    validation_status = Column(String(50), nullable=False, default='pending')  # pending, validated, rejected

    # Zeitstempel
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Beziehungen
    session = relationship("SearchSession", back_populates="results")

    # Indizes
    __table_args__ = (
        Index('idx_results_mine_field', 'mine_name', 'field_name'),
        Index('idx_results_model_provider', 'model_id', 'provider'),
        Index('idx_results_source_domain', 'source_domain'),
        Index('idx_results_validation_status', 'validation_status'),
        UniqueConstraint('session_id', 'field_name', name='uq_session_field'),
    )

    def __repr__(self):
        return f"<SearchResult(id={self.id}, mine='{self.mine_name}', field='{self.field_name}',
value='{self.extracted_value[:50] if self.extracted_value else None}...')>"

    def to_dict(self):
        """Konvertiert SearchResult zu Dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'mine_name': self.mine_name,
            'model_id': self.model_id,
            'provider': self.provider,
            'field_name': self.field_name,
            'extracted_value': self.extracted_value,
            'confidence_score': self.confidence_score,
            'extraction_method': self.extraction_method,
            'source_url': self.source_url,
            'source_domain': self.source_domain,
            'extraction_context': self.extraction_context,
            'is_placeholder': self.is_placeholder,
            'is_fallback': self.is_fallback,
            'validation_status': self.validation_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ModelPerformance(Base):
    """Datenbank-Tabelle für Modell-Performance-Tracking"""
    __tablename__ = 'model_performance'

    id = Column(Integer, primary_key=True)
    model_id = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)

    # Performance-Metriken
    total_searches = Column(Integer, nullable=False, default=0)
    successful_extractions = Column(Integer, nullable=False, default=0)
    failed_extractions = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)

    # Qualitäts-Metriken
    average_confidence = Column(Float, nullable=False, default=0.0)
    placeholder_rate = Column(Float, nullable=False, default=0.0)
    fallback_rate = Column(Float, nullable=False, default=0.0)

    # Zeitstempel
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Indizes
    __table_args__ = (
        Index('idx_performance_model_field', 'model_id', 'field_name'),
        Index('idx_performance_provider', 'provider'),
        Index('idx_performance_success_rate', 'success_rate'),
        UniqueConstraint('model_id', 'field_name', name='uq_model_field_performance'),
    )

    def __repr__(self):
        return f"<ModelPerformance(id={self.id}, model='{self.model_id}', field='{self.field_name}',
success_rate={self.success_rate:.2f})>"

    def to_dict(self):
        """Konvertiert ModelPerformance zu Dictionary"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'provider': self.provider,
            'field_name': self.field_name,
            'total_searches': self.total_searches,
            'successful_extractions': self.successful_extractions,
            'failed_extractions': self.failed_extractions,
            'success_rate': self.success_rate,
            'average_confidence': self.average_confidence,
            'placeholder_rate': self.placeholder_rate,
            'fallback_rate': self.fallback_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
