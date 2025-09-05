"""
Author: rahn
Datum: 03.09.2025
Version: 1.0
Beschreibung: Normalisierte Datenbank-Modelle für MineSearch v3.0 - Vollständige Normalisierung

DATENBANK-NORMALISIERUNG 03.09.2025: Komplette Überarbeitung der Datenbankstruktur
- 1NF: Atomare Werte, keine mehrwertigen Felder
- 2NF: Alle Nicht-Schlüssel-Attribute voll funktional abhängig vom Primärschlüssel
- 3NF: Keine transitiven Abhängigkeiten
- BCNF: Jeder Determinant ist Kandidatenschlüssel
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
    """Länder-Lookup-Tabelle (Normalisierung: Referenzielle Integrität)"""
    __tablename__ = 'countries'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    iso_code_2 = Column(String(2), nullable=True, unique=True, index=True)  # CA, US, AU, etc.
    iso_code_3 = Column(String(3), nullable=True, unique=True)  # CAN, USA, AUS, etc.
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships (1:N)
    regions = relationship("Region", back_populates="country", cascade="all, delete-orphan")
    mines = relationship("Mine", back_populates="country")
    companies = relationship("Company", back_populates="country")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'iso_code_2': self.iso_code_2,
            'iso_code_3': self.iso_code_3,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Region(NormalizedBase):
    """Regionen-Lookup-Tabelle (Normalisierung: Hierarchische Struktur)"""
    __tablename__ = 'regions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey('countries.id', ondelete='CASCADE'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="regions")
    mines = relationship("Mine", back_populates="region")
    
    # Eindeutigkeit: Region-Name pro Land
    __table_args__ = (
        UniqueConstraint('name', 'country_id', name='uix_region_country'),
        Index('idx_region_country', 'country_id', 'name'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'country_id': self.country_id,
            'country_name': self.country.name if self.country else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MineType(NormalizedBase):
    """Minentyp-Lookup-Tabelle (Normalisierung: Kontrollierte Werte)"""
    __tablename__ = 'mine_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # Untertage, Open-Pit, etc.
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships (1:N)
    mines = relationship("Mine", back_populates="mine_type")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ActivityStatus(NormalizedBase):
    """Aktivitätsstatus-Lookup-Tabelle (Normalisierung: Kontrollierte Werte)"""
    __tablename__ = 'activity_statuses'
    
    id = Column(Integer, primary_key=True)
    status = Column(String(50), nullable=False, unique=True, index=True)  # aktiv, geschlossen, geplant, etc.
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships (1:N)
    mines = relationship("Mine", back_populates="activity_status")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Commodity(NormalizedBase):
    """Rohstoff-Lookup-Tabelle (Normalisierung: N:M Beziehung zu Minen)"""
    __tablename__ = 'commodities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # Gold, Kupfer, Kohle, etc.
    symbol = Column(String(10), nullable=True)  # Au, Cu, C, etc.
    unit = Column(String(20), nullable=True)  # kg, t, oz, etc.
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships (N:M über Assoziationstabelle)
    mine_commodities = relationship("MineCommodity", back_populates="commodity", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'unit': self.unit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Company(NormalizedBase):
    """Unternehmen-Tabelle (Normalisierung: Eigentümer/Betreiber als separate Entitäten)"""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=True)
    company_type = Column(String(50), nullable=True)  # public, private, government, etc.
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="companies")
    mine_owners = relationship("MineOwner", back_populates="company", cascade="all, delete-orphan")
    mine_operators = relationship("MineOperator", back_populates="company", cascade="all, delete-orphan")
    
    # Indizes
    __table_args__ = (
        Index('idx_company_name_country', 'name', 'country_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'country_id': self.country_id,
            'country_name': self.country.name if self.country else None,
            'company_type': self.company_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Mine(NormalizedBase):
    """Haupttabelle für Minen (Vereinfachtes Schema nach 04.09.2025 Bereinigung)"""
    __tablename__ = 'mines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Foreign Keys (nur Country und Region nach Schema-Bereinigung)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=True, index=True)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships (nur noch Country und Region nach Schema-Bereinigung)
    country = relationship("Country", back_populates="mines")
    region = relationship("Region", back_populates="mines")
    
    # Search Sessions (normalisierte Datenbank verwendet mine_data_fields für alle anderen Daten)
    search_sessions = relationship("SearchSession", back_populates="mine", cascade="all, delete-orphan")
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_mine_country_region', 'country_id', 'region_id'),
        Index('idx_mine_name', 'name'),  # Für schnelle Name-Suchen
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'country_id': self.country_id,
            'country_name': self.country.name if self.country else None,
            'region_id': self.region_id,
            'region_name': self.region.name if self.region else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MineCommodity(NormalizedBase):
    """N:M Beziehungstabelle: Mine ↔ Rohstoffe (Normalisierung: Auflösung mehrwertiger Felder)"""
    __tablename__ = 'mine_commodities'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id', ondelete='CASCADE'), nullable=False, index=True)
    commodity_id = Column(Integer, ForeignKey('commodities.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Produktionsvolumen pro Jahr (optional)
    production_volume_per_year = Column(Numeric(precision=15, scale=3), nullable=True)
    unit = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mine = relationship("Mine", back_populates="mine_commodities")
    commodity = relationship("Commodity", back_populates="mine_commodities")
    
    # Eindeutigkeit: Ein Rohstoff pro Mine nur einmal
    __table_args__ = (
        UniqueConstraint('mine_id', 'commodity_id', name='uix_mine_commodity'),
        Index('idx_mine_commodity_mine', 'mine_id'),
        Index('idx_mine_commodity_commodity', 'commodity_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'mine_id': self.mine_id,
            'commodity_id': self.commodity_id,
            'commodity_name': self.commodity.name if self.commodity else None,
            'production_volume_per_year': float(self.production_volume_per_year) if self.production_volume_per_year is not None else None,
            'unit': self.unit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MineOwner(NormalizedBase):
    """N:M Beziehungstabelle: Mine ↔ Eigentümer (Normalisierung: Historisierung)"""
    __tablename__ = 'mine_owners'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id', ondelete='CASCADE'), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Eigentumsanteil und Gültigkeitszeitraum
    ownership_percentage = Column(Numeric(precision=5, scale=2), nullable=True)  # 0.00 bis 100.00
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)  # NULL = noch gültig
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mine = relationship("Mine", back_populates="mine_owners")
    company = relationship("Company", back_populates="mine_owners")
    
    # Indizes für Performance und Historie-Abfragen
    __table_args__ = (
        Index('idx_mine_owner_mine', 'mine_id'),
        Index('idx_mine_owner_company', 'company_id'),
        Index('idx_mine_owner_validity', 'valid_from', 'valid_to'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'mine_id': self.mine_id,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'ownership_percentage': float(self.ownership_percentage) if self.ownership_percentage is not None else None,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MineOperator(NormalizedBase):
    """N:M Beziehungstabelle: Mine ↔ Betreiber (Normalisierung: Historisierung)"""
    __tablename__ = 'mine_operators'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id', ondelete='CASCADE'), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Gültigkeitszeitraum
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)  # NULL = noch gültig
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mine = relationship("Mine", back_populates="mine_operators")
    company = relationship("Company", back_populates="mine_operators")
    
    # Indizes für Performance und Historie-Abfragen
    __table_args__ = (
        Index('idx_mine_operator_mine', 'mine_id'),
        Index('idx_mine_operator_company', 'company_id'),
        Index('idx_mine_operator_validity', 'valid_from', 'valid_to'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'mine_id': self.mine_id,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProductionPeriod(NormalizedBase):
    """Produktionszeiträume (Normalisierung: Historisierung von Produktionsstart/-ende)"""
    __tablename__ = 'production_periods'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Produktionszeitraum
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)  # NULL = noch in Produktion
    
    # Status und Grund
    status = Column(String(50), nullable=True)  # aktiv, pausiert, beendet
    reason = Column(Text, nullable=True)  # Grund für Statusänderung
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mine = relationship("Mine", back_populates="production_periods")
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_production_period_mine', 'mine_id'),
        Index('idx_production_period_dates', 'start_date', 'end_date'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'mine_id': self.mine_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RestorationCost(NormalizedBase):
    """Restaurationskosten (Normalisierung: Historisierung von Kostenangaben)"""
    __tablename__ = 'restoration_costs'
    
    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('mines.id', ondelete='CASCADE'), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=True)  # Quelle der Information
    
    # Kosten-Details
    amount = Column(Numeric(precision=15, scale=2), nullable=True)
    currency = Column(String(3), nullable=True)  # USD, CAD, EUR, etc.
    
    # Jahr-Angaben (getrennt normalisiert)
    year_recorded = Column(Integer, nullable=True)  # Jahr der Aufnahme der Kosten
    document_year = Column(Integer, nullable=True)  # Jahr der Erstellung des Dokuments
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mine = relationship("Mine", back_populates="restoration_costs")
    source = relationship("Source", backref="restoration_costs")
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_restoration_cost_mine', 'mine_id'),
        Index('idx_restoration_cost_year', 'year_recorded', 'document_year'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'mine_id': self.mine_id,
            'source_id': self.source_id,
            'amount': float(self.amount) if self.amount is not None else None,
            'currency': self.currency,
            'year_recorded': self.year_recorded,
            'document_year': self.document_year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AIModel(NormalizedBase):
    """AI-Modelle-Tabelle (Normalisierung: Referenzen statt String-Duplikate)"""
    __tablename__ = 'ai_models'
    
    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False, index=True)  # openrouter, anthropic, etc.
    model_name = Column(String(100), nullable=False)  # grok-2, claude-3.5-sonnet, etc.
    full_model_id = Column(String(200), nullable=False, unique=True, index=True)  # openrouter:grok-2
    version = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    search_sessions = relationship("SearchSession", back_populates="ai_model")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'provider': self.provider,
            'model_name': self.model_name,
            'full_model_id': self.full_model_id,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SearchSession(NormalizedBase):
    """Suchsitzungen (Normalisierung: Trennung von Suchvorgang und Ergebnissen)"""
    __tablename__ = 'search_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    mine_id = Column(Integer, ForeignKey('mines.id', ondelete='CASCADE'), nullable=False, index=True)
    ai_model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=True, index=True)
    
    # Such-Metadaten
    search_timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    search_duration_ms = Column(Integer, nullable=True)
    search_type = Column(String(50), nullable=True)  # standard, enhanced, deep-research
    
    # Erfolg
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mine = relationship("Mine", back_populates="search_sessions")
    ai_model = relationship("AIModel", back_populates="search_sessions")
    field_values = relationship("FieldValue", back_populates="search_session", cascade="all, delete-orphan")
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_search_session_mine', 'mine_id'),
        Index('idx_search_session_timestamp', 'search_timestamp'),
        Index('idx_search_session_model', 'ai_model_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'mine_id': self.mine_id,
            'ai_model_id': self.ai_model_id,
            'ai_model_name': self.ai_model.full_model_id if self.ai_model else None,
            'search_timestamp': self.search_timestamp.isoformat() if self.search_timestamp else None,
            'search_duration_ms': self.search_duration_ms,
            'search_type': self.search_type,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FieldValue(NormalizedBase):
    """Feldwerte (Normalisierung: Atomare Werte ohne Quellenreferenzen)"""
    __tablename__ = 'field_values'
    
    id = Column(Integer, primary_key=True)
    search_session_id = Column(Integer, ForeignKey('search_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    
    # Atomarer Wert (nur der reine Wert, z.B. "Kanada")
    atomic_value = Column(Text, nullable=True)
    confidence_score = Column(Numeric(precision=5, scale=2), nullable=False, default=0.0)  # 0.00 bis 100.00
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    search_session = relationship("SearchSession", back_populates="field_values")
    field_sources = relationship("FieldValueSource", back_populates="field_value", cascade="all, delete-orphan")
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_field_value_session', 'search_session_id'),
        Index('idx_field_value_field', 'field_name'),
        Index('idx_field_value_session_field', 'search_session_id', 'field_name'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'search_session_id': self.search_session_id,
            'field_name': self.field_name,
            'atomic_value': self.atomic_value,
            'confidence_score': float(self.confidence_score) if self.confidence_score is not None else 0.0,
            'source_count': len(self.field_sources) if self.field_sources else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FieldValueSource(NormalizedBase):
    """N:M Beziehung: Feldwerte ↔ Quellen (Normalisierung: Trennung Wert/Quelle)"""
    __tablename__ = 'field_value_sources'
    
    id = Column(Integer, primary_key=True)
    field_value_id = Column(Integer, ForeignKey('field_values.id', ondelete='CASCADE'), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey('sources.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Extraktions-Konfidenz für diese spezifische Quelle
    extraction_confidence = Column(Numeric(precision=5, scale=2), nullable=False, default=50.0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    field_value = relationship("FieldValue", back_populates="field_sources")
    source = relationship("Source", backref="field_value_sources")
    
    # Eindeutigkeit: Ein Feldwert kann pro Quelle nur einmal referenziert werden
    __table_args__ = (
        UniqueConstraint('field_value_id', 'source_id', name='uix_field_value_source'),
        Index('idx_fvs_field_value', 'field_value_id'),
        Index('idx_fvs_source', 'source_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'field_value_id': self.field_value_id,
            'source_id': self.source_id,
            'extraction_confidence': float(self.extraction_confidence) if self.extraction_confidence is not None else 50.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Source(NormalizedBase):
    """Quellen-Tabelle (Normalisierung: Übernahme existierender Struktur mit Verbesserungen)"""
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    source_type = Column(String(50), nullable=False, default='unknown')  # government, exchange, industry, database, document
    reliability_score = Column(Float, nullable=False, default=50.0)
    
    # KOMPATIBILITÄT: Erweiterte Felder für Sequential Orchestrator (aus legacy source model)
    # Akkumulations-Tracking
    discovery_count = Column(Integer, nullable=False, default=1)  # Wie oft wurde diese Quelle entdeckt
    first_discovered_by = Column(String(100), nullable=True)  # Modell das diese Quelle zuerst fand
    discovery_models = Column(JSON, nullable=True)  # Liste aller Modelle die diese Quelle fanden
    last_discovery_session = Column(String(100), nullable=True, index=True)  # Letzte Session die diese Quelle fand
    
    # Qualitätsbewertung für Akkumulation
    cumulative_quality_score = Column(Float, nullable=False, default=0.0)  # Akkumulierte Qualitätsbewertung
    field_specialization = Column(JSON, nullable=True)  # Welche Felder diese Quelle gut abdeckt
    mine_specialization = Column(JSON, nullable=True)  # Für welche Minen diese Quelle besonders gut ist
    
    # Verwendungs-Statistiken für Sequential Search
    times_used_in_field_search = Column(Integer, nullable=False, default=0)
    successful_field_extractions = Column(Integer, nullable=False, default=0)
    field_extraction_success_rate = Column(Float, nullable=False, default=0.0)
    
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
        Index('idx_source_country_region', 'country', 'region'),
        Index('idx_source_type_score', 'source_type', 'reliability_score'),
        # Neue Indizes für Sequential Orchestrator
        Index('idx_source_discovery_session', 'last_discovery_session', 'discovery_count'),
        Index('idx_source_quality_usage', 'cumulative_quality_score', 'times_used_in_field_search'),
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Alle normalisierten Modelle für Export
__all__ = [
    'NormalizedBase',
    'Country',
    'Region', 
    'MineType',
    'ActivityStatus',
    'Commodity',
    'Company',
    'Mine',
    'MineCommodity',
    'MineOwner',
    'MineOperator',
    'ProductionPeriod',
    'RestorationCost',
    'AIModel',
    'SearchSession',
    'FieldValue',
    'FieldValueSource',
    'Source'
]