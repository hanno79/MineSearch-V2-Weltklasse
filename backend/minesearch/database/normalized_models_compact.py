"""
Compact Normalized Database Models
Kompakte Version der normalisierten Datenbank-Modelle

Author: MineSearch Development Team
Date: 2025-01-11
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, UniqueConstraint, Index, Numeric, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

# Normalisierte Datenbank-Basis
NormalizedBase = declarative_base()


class Country(NormalizedBase):
    """Länder-Lookup-Tabelle"""
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(3), unique=True, nullable=False)
    region = Column(String(100))
    created_at = Column(DateTime, default=func.now())

    # Beziehungen
    mines = relationship("Mine", back_populates="country_ref")


class Mine(NormalizedBase):
    """Minen-Entität (Normalisierung: 3NF)"""
    __tablename__ = 'mines'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'))
    region = Column(String(100))
    commodity = Column(String(100))
    operational_status = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Beziehungen
    country_ref = relationship("Country", back_populates="mines")
    search_results = relationship("SearchResult", back_populates="mine_ref")
    field_values = relationship("FieldValue", back_populates="mine_ref")


class Source(NormalizedBase):
    """Quellen-Entität (Normalisierung: 1NF)"""
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    source_type = Column(String(100))
    domain = Column(String(200))
    discovered_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)
    reliability_score = Column(Float, default=0.0)

    # Beziehungen
    field_value_sources = relationship("FieldValueSource", back_populates="source_ref")


class SearchResult(NormalizedBase):
    """Suchergebnis-Entität (Normalisierung: 2NF)"""
    __tablename__ = 'search_results'

    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    model_used = Column(String(100), nullable=False)
    search_timestamp = Column(DateTime, default=func.now())
    execution_time = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    confidence_score = Column(Float, default=0.0)

    # Beziehungen
    mine_ref = relationship("Mine", back_populates="search_results")
    field_values = relationship("FieldValue", back_populates="search_result_ref")


class FieldValue(NormalizedBase):
    """Feldwert-Entität (Normalisierung: 1NF - atomare Werte)"""
    __tablename__ = 'field_values'

    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    search_result_id = Column(Integer, ForeignKey('search_results.id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    atomic_value = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)
    extraction_method = Column(String(100))
    created_at = Column(DateTime, default=func.now())

    # Beziehungen
    mine_ref = relationship("Mine", back_populates="field_values")
    search_result_ref = relationship("SearchResult", back_populates="field_values")
    field_value_sources = relationship("FieldValueSource", back_populates="field_value_ref")


class FieldValueSource(NormalizedBase):
    """Feldwert-Quellen-Verknüpfung (Normalisierung: BCNF)"""
    __tablename__ = 'field_value_sources'

    id = Column(Integer, primary_key=True)
    field_value_id = Column(Integer, ForeignKey('field_values.id'), nullable=False)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    extraction_confidence = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())

    # Beziehungen
    field_value_ref = relationship("FieldValue", back_populates="field_value_sources")
    source_ref = relationship("Source", back_populates="field_value_sources")

    # Eindeutige Constraint
    __table_args__ = (
        UniqueConstraint('field_value_id', 'source_id', name='uq_field_value_source'),
        Index('idx_field_value_source', 'field_value_id', 'source_id')
    )


class ModelPerformance(NormalizedBase):
    """Modell-Performance-Entität (Normalisierung: 3NF)"""
    __tablename__ = 'model_performance'

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    field_name = Column(String(100), nullable=False)
    total_searches = Column(Integer, default=0)
    successful_searches = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    avg_execution_time = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Eindeutige Constraint
    __table_args__ = (
        UniqueConstraint('model_name', 'field_name', name='uq_model_field'),
        Index('idx_model_performance', 'model_name', 'field_name')
    )


class FieldConsistency(NormalizedBase):
    """Feld-Konsistenz-Entität (Normalisierung: 3NF)"""
    __tablename__ = 'field_consistency'

    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    unique_values_count = Column(Integer, default=0)
    most_common_value = Column(Text)
    consistency_score = Column(Float, default=0.0)
    last_analyzed = Column(DateTime, default=func.now())

    # Beziehungen
    mine_ref = relationship("Mine")

    # Eindeutige Constraint
    __table_args__ = (
        UniqueConstraint('mine_id', 'field_name', name='uq_mine_field'),
        Index('idx_field_consistency', 'mine_id', 'field_name')
    )


class DataQualityMetrics(NormalizedBase):
    """Datenqualitäts-Metriken (Normalisierung: 3NF)"""
    __tablename__ = 'data_quality_metrics'

    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    completeness_score = Column(Float, default=0.0)
    accuracy_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    timeliness_score = Column(Float, default=0.0)
    overall_quality_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Beziehungen
    mine_ref = relationship("Mine")

    # Eindeutige Constraint
    __table_args__ = (
        UniqueConstraint('mine_id', 'field_name', name='uq_mine_field_quality'),
        Index('idx_data_quality', 'mine_id', 'field_name')
    )


class AuditLog(NormalizedBase):
    """Audit-Log-Entität (Normalisierung: 3NF)"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    operation = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    old_values = Column(JSON)
    new_values = Column(JSON)
    user_id = Column(String(100))
    timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String(45))

    # Index für Performance
    __table_args__ = (
        Index('idx_audit_log', 'table_name', 'record_id', 'timestamp'),
    )


class SystemConfiguration(NormalizedBase):
    """System-Konfiguration (Normalisierung: 3NF)"""
    __tablename__ = 'system_configuration'

    id = Column(Integer, primary_key=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    config_type = Column(String(50), default='string')  # string, int, float, boolean, json
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Index für Performance
    __table_args__ = (
        Index('idx_system_config', 'config_key'),
    )


# Hilfsfunktionen für die normalisierten Modelle
def get_model_by_name(model_name: str) -> Optional[NormalizedBase]:
    """Hole Modell-Klasse nach Namen"""
    models = {
        'Country': Country,
        'Mine': Mine,
        'Source': Source,
        'SearchResult': SearchResult,
        'FieldValue': FieldValue,
        'FieldValueSource': FieldValueSource,
        'ModelPerformance': ModelPerformance,
        'FieldConsistency': FieldConsistency,
        'DataQualityMetrics': DataQualityMetrics,
        'AuditLog': AuditLog,
        'SystemConfiguration': SystemConfiguration
    }
    return models.get(model_name)


def get_all_models() -> List[NormalizedBase]:
    """Hole alle Modell-Klassen"""
    return [
        Country, Mine, Source, SearchResult, FieldValue, FieldValueSource,
        ModelPerformance, FieldConsistency, DataQualityMetrics, AuditLog, SystemConfiguration
    ]


def get_table_names() -> List[str]:
    """Hole alle Tabellennamen"""
    return [
        'countries', 'mines', 'sources', 'search_results', 'field_values',
        'field_value_sources', 'model_performance', 'field_consistency',
        'data_quality_metrics', 'audit_logs', 'system_configuration'
    ]


# Exportiere alle Modelle
__all__ = [
    'NormalizedBase',
    'Country', 'Mine', 'Source', 'SearchResult', 'FieldValue', 'FieldValueSource',
    'ModelPerformance', 'FieldConsistency', 'DataQualityMetrics', 'AuditLog', 'SystemConfiguration',
    'get_model_by_name', 'get_all_models', 'get_table_names'
]
