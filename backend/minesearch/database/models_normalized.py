"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Normalized-Modelle für MineSearch v2 (aufgeteilt aus models.py)
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Text, Boolean, 
    Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .models_base import Base


class NormalizedMine(Base):
    """Normalisierte Minen-Datenbank-Tabelle"""
    __tablename__ = 'normalized_mines'

    id = Column(Integer, primary_key=True)
    mine_name = Column(String(255), nullable=False, unique=True, index=True)

    # Grunddaten
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    coordinates_lat = Column(Float, nullable=True)
    coordinates_lon = Column(Float, nullable=True)

    # Bergbau-Informationen
    mineral_type = Column(String(100), nullable=True, index=True)
    mining_method = Column(String(100), nullable=True)
    production_status = Column(String(50), nullable=True, index=True)  # active, inactive, planned, closed

    # Produktionsdaten
    annual_production = Column(Float, nullable=True)
    production_unit = Column(String(50), nullable=True)
    production_year = Column(Integer, nullable=True)

    # Reserven und Ressourcen
    proven_reserves = Column(Float, nullable=True)
    probable_reserves = Column(Float, nullable=True)
    measured_resources = Column(Float, nullable=True)
    indicated_resources = Column(Float, nullable=True)
    inferred_resources = Column(Float, nullable=True)
    reserves_unit = Column(String(50), nullable=True)

    # Eigentumsverhältnisse
    owner_company = Column(String(255), nullable=True, index=True)
    operator_company = Column(String(255), nullable=True, index=True)
    ownership_percentage = Column(Float, nullable=True)

    # Finanzielle Daten
    investment_cost = Column(Float, nullable=True)
    operating_cost = Column(Float, nullable=True)
    cost_unit = Column(String(10), nullable=True)  # USD, EUR, etc.

    # Umwelt und Nachhaltigkeit
    environmental_impact = Column(Text, nullable=True)
    sustainability_rating = Column(Float, nullable=True)
    reclamation_status = Column(String(50), nullable=True)

    # Qualitätsbewertung
    data_quality_score = Column(Float, nullable=False, default=0.0)
    completeness_score = Column(Float, nullable=False, default=0.0)
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Beziehungen
    field_values = relationship("NormalizedFieldValue", back_populates="mine", cascade="all, delete-orphan")

    # Indizes
    __table_args__ = (
        Index('idx_normalized_mines_country_region', 'country', 'region'),
        Index('idx_normalized_mines_mineral_status', 'mineral_type', 'production_status'),
        Index('idx_normalized_mines_owner_operator', 'owner_company', 'operator_company'),
        Index('idx_normalized_mines_data_quality', 'data_quality_score'),
    )

    def __repr__(self):
        return f"<NormalizedMine(id={self.id}, name='{self.mine_name}', country='{self.country}', status='{self.production_status}')>"

    def to_dict(self):
        """Konvertiert NormalizedMine zu Dictionary"""
        return {
            'id': self.id,
            'mine_name': self.mine_name,
            'country': self.country,
            'region': self.region,
            'coordinates_lat': self.coordinates_lat,
            'coordinates_lon': self.coordinates_lon,
            'mineral_type': self.mineral_type,
            'mining_method': self.mining_method,
            'production_status': self.production_status,
            'annual_production': self.annual_production,
            'production_unit': self.production_unit,
            'production_year': self.production_year,
            'proven_reserves': self.proven_reserves,
            'probable_reserves': self.probable_reserves,
            'measured_resources': self.measured_resources,
            'indicated_resources': self.indicated_resources,
            'inferred_resources': self.inferred_resources,
            'reserves_unit': self.reserves_unit,
            'owner_company': self.owner_company,
            'operator_company': self.operator_company,
            'ownership_percentage': self.ownership_percentage,
            'investment_cost': self.investment_cost,
            'operating_cost': self.operating_cost,
            'cost_unit': self.cost_unit,
            'environmental_impact': self.environmental_impact,
            'sustainability_rating': self.sustainability_rating,
            'reclamation_status': self.reclamation_status,
            'data_quality_score': self.data_quality_score,
            'completeness_score': self.completeness_score,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class NormalizedFieldValue(Base):
    """Normalisierte Feld-Werte für Minen"""
    __tablename__ = 'normalized_field_values'

    id = Column(Integer, primary_key=True)
    mine_id = Column(Integer, ForeignKey('normalized_mines.id'), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)

    # Werte
    normalized_value = Column(Text, nullable=True)
    original_value = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Metadaten
    extraction_method = Column(String(50), nullable=True)
    source_url = Column(String(500), nullable=True)
    source_domain = Column(String(255), nullable=True)
    model_id = Column(String(100), nullable=True, index=True)

    # Qualitätsbewertung
    is_placeholder = Column(Boolean, nullable=False, default=False)
    is_fallback = Column(Boolean, nullable=False, default=False)
    validation_status = Column(String(50), nullable=False, default='pending')

    # Zeitstempel
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Beziehungen
    mine = relationship("NormalizedMine", back_populates="field_values")

    # Indizes
    __table_args__ = (
        Index('idx_field_values_mine_field', 'mine_id', 'field_name'),
        Index('idx_field_values_model', 'model_id'),
        Index('idx_field_values_validation', 'validation_status'),
        UniqueConstraint('mine_id', 'field_name', name='uq_mine_field_value'),
    )

    def __repr__(self):
        return f"<NormalizedFieldValue(id={self.id}, mine_id={self.mine_id}, field='{self.field_name}', value='{self.normalized_value[:50] if self.normalized_value else None}...')>"

    def to_dict(self):
        """Konvertiert NormalizedFieldValue zu Dictionary"""
        return {
            'id': self.id,
            'mine_id': self.mine_id,
            'field_name': self.field_name,
            'normalized_value': self.normalized_value,
            'original_value': self.original_value,
            'confidence_score': self.confidence_score,
            'extraction_method': self.extraction_method,
            'source_url': self.source_url,
            'source_domain': self.source_domain,
            'model_id': self.model_id,
            'is_placeholder': self.is_placeholder,
            'is_fallback': self.is_fallback,
            'validation_status': self.validation_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
