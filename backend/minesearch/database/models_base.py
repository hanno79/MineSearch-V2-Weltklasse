"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Basis-Modelle für MineSearch v2 (aufgeteilt aus models.py)
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Text, Boolean, 
    Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import re

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

    # NORMALISIERUNG FIX 04.09.2025: JSON-Spalten entfernt
    # Akkumulations-Tracking
    discovery_count = Column(Integer, nullable=False, default=1)  # Wie oft wurde diese Quelle entdeckt
    first_discovered_by = Column(String(100), nullable=True)  # Modell das diese Quelle zuerst fand
    last_discovery_session = Column(String(100), nullable=True, index=True)  # Letzte Session die diese Quelle fand

    # Qualitätsbewertung für Akkumulation
    cumulative_quality_score = Column(Float, nullable=False, default=0.0)  # Akkumulierte Qualitätsbewertung

    # Verwendungs-Statistiken für Sequential Search
    times_used_in_field_search = Column(Integer, nullable=False, default=0)
    successful_field_extractions = Column(Integer, nullable=False, default=0)
    field_extraction_success_rate = Column(Float, nullable=False, default=0.0)

    # Zugriffs-Statistiken
    last_successful_access = Column(DateTime, nullable=True)
    last_attempted_access = Column(DateTime, nullable=True)
    total_searches = Column(Integer, nullable=False, default=0)
    successful_searches = Column(Integer, nullable=False, default=0)
    failed_searches = Column(Integer, nullable=False, default=0)
    search_success_rate = Column(Float, nullable=False, default=0.0)

    # Zeitstempel
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Indizes für Performance
    __table_args__ = (
        Index('idx_sources_domain_country', 'domain', 'country'),
        Index('idx_sources_type_reliability', 'source_type', 'reliability_score'),
        Index('idx_sources_discovery_session', 'last_discovery_session'),
    )

    def __repr__(self):
        return f"<Source(id={self.id}, domain='{self.domain}', url='{self.url[:50]}...')>"

    def to_dict(self):
        """Konvertiert Source zu Dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'domain': self.domain,
            'country': self.country,
            'region': self.region,
            'source_type': self.source_type,
            'reliability_score': self.reliability_score,
            'discovery_count': self.discovery_count,
            'first_discovered_by': self.first_discovered_by,
            'last_discovery_session': self.last_discovery_session,
            'cumulative_quality_score': self.cumulative_quality_score,
            'times_used_in_field_search': self.times_used_in_field_search,
            'successful_field_extractions': self.successful_field_extractions,
            'field_extraction_success_rate': self.field_extraction_success_rate,
            'last_successful_access': self.last_successful_access.isoformat() if self.last_successful_access else None,
            'last_attempted_access': self.last_attempted_access.isoformat() if self.last_attempted_access else None,
            'total_searches': self.total_searches,
            'successful_searches': self.successful_searches,
            'failed_searches': self.failed_searches,
            'search_success_rate': self.search_success_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SearchSession(Base):
    """Datenbank-Tabelle für Such-Sessions"""
    __tablename__ = 'search_sessions'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    mine_name = Column(String(255), nullable=False, index=True)
    search_type = Column(String(50), nullable=False, default='single')  # single, batch, comprehensive
    model_id = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)

    # Such-Parameter
    search_query = Column(Text, nullable=True)
    search_options = Column(JSON, nullable=True)
    selected_fields = Column(JSON, nullable=True)

    # Status und Ergebnisse
    status = Column(String(50), nullable=False, default='pending')  # pending, running, completed, failed
    results_count = Column(Integer, nullable=False, default=0)
    sources_found = Column(Integer, nullable=False, default=0)
    extraction_success_rate = Column(Float, nullable=False, default=0.0)

    # Zeitstempel
    started_at = Column(DateTime, nullable=False, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Beziehungen
    results = relationship("SearchResult", back_populates="session", cascade="all, delete-orphan")

    # Indizes
    __table_args__ = (
        Index('idx_sessions_mine_model', 'mine_name', 'model_id'),
        Index('idx_sessions_provider_status', 'provider', 'status'),
        Index('idx_sessions_started_at', 'started_at'),
    )

    def __repr__(self):
        return f"<SearchSession(id={self.id}, session_id='{self.session_id}', mine='{self.mine_name}', status='{self.status}')>"

    def to_dict(self):
        """Konvertiert SearchSession zu Dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'mine_name': self.mine_name,
            'search_type': self.search_type,
            'model_id': self.model_id,
            'provider': self.provider,
            'search_query': self.search_query,
            'search_options': self.search_options,
            'selected_fields': self.selected_fields,
            'status': self.status,
            'results_count': self.results_count,
            'sources_found': self.sources_found,
            'extraction_success_rate': self.extraction_success_rate,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds
        }
