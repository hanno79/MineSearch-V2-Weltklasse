"""
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Datenbank-Modelle für MineSearch v2 (aufgeteilt aus database.py)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Boolean, Index, ForeignKey, UniqueConstraint
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
    
    # NORMALISIERUNG FIX 04.09.2025: JSON-Spalten entfernt
    # typical_content_types und extra_metadata wurden in normalisierte Tabellen migriert
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_country_region', 'country', 'region'),
        Index('idx_source_type_score', 'source_type', 'reliability_score'),
        # ÄNDERUNG 27.08.2025: Neue Indizes für Sequential Orchestrator
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
            # NORMALISIERUNG FIX 04.09.2025: JSON-Felder entfernt
            'typical_content_types': [],
            'metadata': {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # ÄNDERUNG 27.08.2025: Neue Felder für Sequential Orchestrator
            'discovery_count': self.discovery_count,
            'first_discovered_by': self.first_discovered_by,
            'last_discovery_session': self.last_discovery_session,
            'cumulative_quality_score': self.cumulative_quality_score,
            'times_used_in_field_search': self.times_used_in_field_search,
            'successful_field_extractions': self.successful_field_extractions,
            'field_extraction_success_rate': self.field_extraction_success_rate
        }
    
    def update_access(self, success: bool, content_type: Optional[str] = None):
        """Aktualisiere Zugriffs-Statistiken"""
        self.last_attempted_access = datetime.now()
        self.total_searches += 1
        
        if success:
            self.last_successful_access = datetime.now()
            self.successful_searches += 1
            
            # Aktualisiere Content-Types
            if content_type and self.typical_content_types is not None:
                if content_type not in self.typical_content_types:
                    self.typical_content_types.append(content_type)
        
        # Berechne neue Zuverlässigkeit mit Multi-Faktor-Bewertung
        self.reliability_score = self.calculate_reliability_score()
    
    def calculate_reliability_score(self) -> float:
        """
        Berechne Multi-Faktor-Zuverlässigkeitsbewertung
        
        Faktoren:
        1. Erfolgsquote (40% Gewichtung)
        2. Quellentyp (20% Gewichtung)
        3. Aktualität (20% Gewichtung)
        4. Datenmenge (20% Gewichtung)
        """
        score = 0.0
        
        # 1. Erfolgsquote (40 Punkte maximal)
        if self.total_searches > 0:
            success_rate = self.successful_searches / self.total_searches
            if self.total_searches >= 10:
                # Volle Gewichtung bei vielen Versuchen
                score += success_rate * 40
            elif self.total_searches >= 5:
                # Reduzierte Gewichtung bei wenigen Versuchen
                score += success_rate * 30
            else:
                # Minimale Gewichtung bei sehr wenigen Versuchen
                score += success_rate * 20
        
        # 2. Quellentyp-Bonus (20 Punkte maximal)
        type_scores = {
            'government': 20,     # Regierungsquellen am zuverlässigsten
            'database': 18,       # Offizielle Datenbanken
            'exchange': 15,       # Börsendokumente
            'industry': 12,       # Industrie-Portale
            'document': 10,       # PDF-Dokumente
            'unknown': 5          # Unbekannte Quellen
        }
        score += type_scores.get(self.source_type, 5)
        
        # 3. Aktualität (20 Punkte maximal)
        if self.last_successful_access:
            days_since_success = (datetime.now() - self.last_successful_access).days
            if days_since_success < 7:
                score += 20  # Sehr aktuell
            elif days_since_success < 30:
                score += 15  # Aktuell
            elif days_since_success < 90:
                score += 10  # Mäßig aktuell
            elif days_since_success < 180:
                score += 5   # Veraltet
            # Älter als 180 Tage: 0 Punkte
        
        # 4. Datenmenge/Konsistenz (20 Punkte maximal)
        if self.total_searches >= 20 and self.successful_searches >= 15:
            score += 20  # Viele erfolgreiche Zugriffe
        elif self.total_searches >= 10 and self.successful_searches >= 7:
            score += 15  # Gute Historie
        elif self.total_searches >= 5 and self.successful_searches >= 3:
            score += 10  # Moderate Historie
        elif self.successful_searches > 0:
            score += 5   # Wenige aber erfolgreiche Zugriffe
        
        # Bonus für Content-Type-Vielfalt
        if self.typical_content_types and len(self.typical_content_types) > 2:
            score += 5  # Bonus für vielfältige Inhaltstypen
        
        # Stelle sicher, dass Score zwischen 0 und 100 liegt
        return min(100.0, max(0.0, score))
    
    def update_discovery_tracking(
        self,
        model_id: str,
        session_id: str,
        is_new_discovery: bool = False
    ):
        """
        ÄNDERUNG 27.08.2025: Update Discovery-Tracking für Sequential Orchestrator
        
        Args:
            model_id: ID des Modells das diese Quelle entdeckt hat
            session_id: ID der Discovery-Session
            is_new_discovery: Ist das die erste Entdeckung dieser Quelle?
        """
        # Erste Entdeckung
        if is_new_discovery or not self.first_discovered_by:
            self.first_discovered_by = model_id
            self.discovery_count = 1
        else:
            # Weitere Entdeckungen - vereinfacht ohne JSON-Spalte
            self.discovery_count += 1
        
        # Update session tracking
        self.last_discovery_session = session_id
    
    def update_field_extraction_stats(self, field_name: str, success: bool, quality_score: float = 0.0):
        """
        ÄNDERUNG 27.08.2025: Update Field Extraction Statistics
        
        Args:
            field_name: Name des extrahierten Feldes
            success: War die Extraktion erfolgreich?
            quality_score: Qualitätsbewertung der Extraktion (0.0-100.0)
        """
        self.times_used_in_field_search += 1
        
        if success:
            self.successful_field_extractions += 1
            
            # Update field specialization
            
            # Gewichteter Durchschnitt der Qualitätsbewertungen
            new_score = ((current_score * (field_count - 1)) + quality_score) / field_count
            
        
        # Update success rate
        self.field_extraction_success_rate = (
            (self.successful_field_extractions / self.times_used_in_field_search * 100)
            if self.times_used_in_field_search > 0 else 0.0
        )
        
        # Update cumulative quality score
        if quality_score > 0:
            current_cumulative = self.cumulative_quality_score * (self.times_used_in_field_search - 1)
            self.cumulative_quality_score = (current_cumulative + quality_score) / self.times_used_in_field_search
    
    def get_quality_for_field(self, field_name: str) -> float:
        """
        ÄNDERUNG 27.08.2025: Ermittle Qualitätsbewertung für spezifisches Feld
        
        Returns:
            Qualitätsscore für das angegebene Feld (0.0-100.0)
        """
        # NORMALISIERUNG FIX 04.09.2025: Fallback auf allgemeine Zuverlässigkeit
        # da field_specialization JSON-Spalte entfernt wurde
        return self.reliability_score
    
    def get_effectiveness_for_mine(self, mine_name: str) -> float:
        """
        ÄNDERUNG 27.08.2025: Ermittle Effektivität für spezifische Mine
        
        Returns:
            Effektivitätsscore für die angegebene Mine (0.0-100.0)
        """
        # NORMALISIERUNG FIX 04.09.2025: Fallback auf allgemeine Zuverlässigkeit
        # da mine_specialization JSON-Spalte entfernt wurde
        return self.reliability_score
    
    @classmethod
    def classify_source_type(cls, url: str, domain: str) -> str:
        """
        Automatische Klassifizierung des Quellentyps basierend auf URL/Domain
        """
        url_lower = url.lower()
        domain_lower = domain.lower()
        
        # Government domains - erweiterte Patterns
        gov_patterns = [
            r'\.gov(\.|$)', r'\.gouv\.', r'\.gob\.', r'\.go\.',
            r'mern\.gouv', r'mrnf\.gouv', r'mines\.gouv', r'bape\.gouv',
            r'gestim.*gouv', r'nrcan\.gc\.ca', r'blm\.gov', r'usgs\.gov',
            'government', 'regierung'
        ]
        for pattern in gov_patterns:
            if re.search(pattern, domain_lower) or re.search(pattern, url_lower):
                return 'government'
        
        # Database domains - erweiterte Patterns
        db_patterns = [
            r'mindat\.org', r'miningdataonline\.com', r'minfind\.com',
            r'gestim.*mines',  # GESTIM ist eine Datenbank
            r'geonames\.nrcan', 'infomine', 'mrdata', 'database', 
            'registry', 'cadastre', 'kataster'
        ]
        for pattern in db_patterns:
            if re.search(pattern, domain_lower) or re.search(pattern, url_lower):
                return 'database'
        
        # Exchange/Financial domains  
        exchange_patterns = [
            r'sedar\.com', r'tsx\.com', r'asx\.com\.au', r'jse\.co\.za',
            'sec.gov', 'bolsa', 'bvl.com', 'idx.co', 'exchange', 'börse'
        ]
        for pattern in exchange_patterns:
            if re.search(pattern, domain_lower):
                return 'exchange'
        
        # Industry/Mining portals - spezifischere Patterns
        industry_patterns = [
            r'mining\.com$', r'miningweekly\.com', r'mining-technology\.com',
            r'miningwatch\.ca', r'northernminer\.com', r'miningfrontier\.com',
            r'resourceworld\.com', 'mineria', 'bergbau'
        ]
        for pattern in industry_patterns:
            if re.search(pattern, domain_lower):
                return 'industry'
        
        # Document repositories - erweiterte Erkennung
        doc_patterns = [
            r'\.pdf$', r'/GM\d+/', r'/DV\d+/',  # Quebec mining documents
            r'q4cdn\.com', r'kaisersearch\.com',
            'document', 'report', '/docs/', '/publications/'
        ]
        for pattern in doc_patterns:
            if re.search(pattern, url_lower):
                return 'document'
        
        # Media sources
        media_patterns = ['youtube.com', 'vimeo.com', 'accessnewswire.com']
        if any(pattern in domain_lower for pattern in media_patterns):
            return 'media'
        
        # Wikipedia
        if 'wikipedia.org' in domain_lower:
            return 'wikipedia'
        
        return 'unknown'
    
    @classmethod
    def get_country_from_domain(cls, url: str, domain: str) -> Optional[str]:
        """
        Ermittle Land basierend auf Domain
        """
        domain_lower = domain.lower()
        
        # Domain-zu-Land Mapping
        domain_country_map = {
            # Kanada
            '.ca': 'Canada',
            '.gc.ca': 'Canada',
            '.qc.ca': 'Canada',
            '.gouv.qc.ca': 'Canada',
            'canadianmalartic.com': 'Canada',
            'agnicoeagle.com': 'Canada',
            'searchminerals.ca': 'Canada',
            'glencore.ca': 'Canada',
            'sedar.com': 'Canada',
            'sedarplus.ca': 'Canada',
            'tsx.com': 'Canada',
            'tmx.com': 'Canada',
            
            # USA
            '.gov': 'USA',
            'blm.gov': 'USA',
            'usgs.gov': 'USA',
            
            # Australien
            '.gov.au': 'Australia',
            '.com.au': 'Australia',
            'asx.com.au': 'Australia',
            
            # Weitere Länder
            '.co.za': 'South Africa',
            'jse.co.za': 'South Africa',
            '.co.uk': 'United Kingdom',
            '.cl': 'Chile',
            '.pe': 'Peru',
            '.mx': 'Mexico',
            '.br': 'Brazil',
            '.ru': 'Russia',
            '.cn': 'China',
            '.in': 'India',
            '.de': 'Germany',
            '.fr': 'France'
        }
        
        # Direkte Domain-Suche
        for domain_pattern, country in domain_country_map.items():
            if domain_pattern in domain_lower:
                return country
        
        # Spezielle URL-Patterns
        if 'quebec' in url.lower() or 'qc.ca' in domain_lower:
            return 'Canada'
        
        return None


class Mine(Base):
    """Datenbank-Tabelle für Mining-Standorte"""
    __tablename__ = 'mines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    commodity = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=True)  # active, closed, planned, etc.
    
    # Metadaten
    mine_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_mine_country_region', 'country', 'region'),
        Index('idx_mine_commodity', 'commodity'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'name': self.name,
            'country': self.country,
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'commodity': self.commodity,
            'status': self.status,
            'metadata': self.mine_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SearchResult(Base):
    """Datenbank-Tabelle für Suchergebnisse"""
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=True, index=True)  # Für Batch-Gruppierung
    mine_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    commodity = Column(String(100), nullable=True)
    
    # Such-Metadaten
    search_timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    model_used = Column(String(50), nullable=False)
    search_type = Column(String(50), nullable=True)  # standard, enhanced, deep-research
    search_duration = Column(Float, nullable=True)  # Sekunden
    
    # Foreign Key Relationships - DEAKTIVIERT für CSV-Export Kompatibilität
    # mine_id = Column(Integer, ForeignKey('mines.id'), nullable=True)
    # mine = relationship("Mine", backref="search_results")
    
    # Ergebnisse
    structured_data = Column(JSON, nullable=True)  # Alle extrahierten Felder
    structured_data_with_sources = Column(JSON, nullable=True)  # Mit Quellennummern
    sources = Column(JSON, nullable=True)  # Gefundene Quellen
    source_index = Column(JSON, nullable=True)  # Quellen-Index
    source_mapping = Column(JSON, nullable=True)  # QUELLENREFERENZEN-FIX 19.07.2025: Neues Quellen-Mapping
    
    # Qualitätsmetriken
    data_quality = Column(JSON, nullable=True)  # Qualitäts-Informationen
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Source Discovery Session
    source_discovery_session = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_search_results_mine_country', 'mine_name', 'country'),
        Index('idx_search_results_session', 'session_id'),
        Index('idx_search_results_timestamp', 'search_timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'mine_name': self.mine_name,
            'country': self.country,
            'region': self.region,
            'commodity': self.commodity,
            'search_timestamp': self.search_timestamp.isoformat() if self.search_timestamp else None,
            'model_used': self.model_used,
            'search_type': self.search_type,
            'search_duration': self.search_duration,
            'structured_data': self.structured_data or {},
            'structured_data_with_sources': self.structured_data_with_sources or {},
            'sources': self.sources or [],
            'source_index': self.source_index or {},
            'source_mapping': self.source_mapping or {},  # QUELLENREFERENZEN-FIX 19.07.2025
            'data_quality': self.data_quality or {},
            'success': self.success,
            'error_message': self.error_message,
            'source_discovery_session': self.source_discovery_session or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ModelStatistics(Base):
    """Datenbank-Tabelle für Modell-Statistiken"""
    __tablename__ = 'model_statistics'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(100), nullable=False, index=True)
    mine_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    commodity = Column(String(100), nullable=True)
    run_number = Column(Integer, nullable=False)  # 1-5 für jeden Durchlauf
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    
    # Ergebnis-Metriken
    success = Column(Boolean, nullable=False, default=False)
    response_time_ms = Column(Float, nullable=True)
    fields_found = Column(Integer, nullable=False, default=0)
    sources_count = Column(Integer, nullable=False, default=0)
    
    # Daten
    raw_result = Column(JSON, nullable=True)  # Komplette API-Antwort
    structured_data = Column(JSON, nullable=True)  # Extrahierte Felder
    error_message = Column(Text, nullable=True)
    
    # Foreign Key Relationships - DEAKTIVIERT für CSV-Export Kompatibilität
    # mine_id = Column(Integer, ForeignKey('mines.id'), nullable=True)
    # mine = relationship("Mine", backref="model_statistics")
    
    # Indizes
    __table_args__ = (
        Index('idx_model_mine', 'model_id', 'mine_name'),
        Index('idx_model_timestamp', 'model_id', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'mine_name': self.mine_name,
            'country': self.country,
            'region': self.region,
            'commodity': self.commodity,
            'run_number': self.run_number,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'response_time_ms': self.response_time_ms,
            'fields_found': self.fields_found,
            'sources_count': self.sources_count,
            'structured_data': self.structured_data,
            'error_message': self.error_message
        }


class FieldConsistency(Base):
    """Datenbank-Tabelle für Feld-Konsistenz-Analyse"""
    __tablename__ = 'field_consistency'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(100), nullable=False, index=True)
    mine_name = Column(String(255), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    consistency_score = Column(Float, nullable=False, default=0.0)  # 0.0 bis 1.0
    values_found = Column(JSON, nullable=False)  # Array aller gefundenen Werte
    most_common_value = Column(Text, nullable=True)
    occurrence_count = Column(Integer, nullable=False, default=0)
    total_runs = Column(Integer, nullable=False, default=5)
    is_consistent = Column(Boolean, nullable=False, default=False)  # True wenn >80% gleich
    last_updated = Column(DateTime, nullable=False, server_default=func.now())
    
    # Foreign Key Relationships - DEAKTIVIERT für CSV-Export Kompatibilität
    # mine_id = Column(Integer, ForeignKey('mines.id'), nullable=True)
    # mine = relationship("Mine", backref="field_consistencies")
    
    # Indizes
    __table_args__ = (
        Index('idx_model_mine_field', 'model_id', 'mine_name', 'field_name'),
        Index('idx_consistency', 'consistency_score'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'mine_name': self.mine_name,
            'field_name': self.field_name,
            'consistency_score': self.consistency_score,
            'values_found': self.values_found,
            'most_common_value': self.most_common_value,
            'occurrence_count': self.occurrence_count,
            'total_runs': self.total_runs,
            'is_consistent': self.is_consistent,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class ModelSummary(Base):
    """Datenbank-Tabelle für Modell-Zusammenfassung"""
    __tablename__ = 'model_summary'
    
    model_id = Column(String(100), primary_key=True)
    total_tests = Column(Integer, nullable=False, default=0)
    total_mines_tested = Column(Integer, nullable=False, default=0)
    avg_response_time_ms = Column(Float, nullable=False, default=0.0)
    avg_fields_found = Column(Float, nullable=False, default=0.0)
    avg_sources_count = Column(Float, nullable=False, default=0.0)
    success_rate = Column(Float, nullable=False, default=0.0)  # 0.0 bis 1.0 (API-Erfolg)
    data_success_rate = Column(Float, nullable=False, default=0.0)  # 0.0 bis 1.0 (Daten-Erfolg)
    overall_consistency = Column(Float, nullable=False, default=0.0)  # 0.0 bis 1.0
    
    # Feld-spezifische Konsistenz
    critical_fields_consistency = Column(JSON, nullable=True)  # {"Eigentümer": 0.8, "Betreiber": 0.6, ...}
    
    # Kosten-Schätzung
    estimated_cost_per_request = Column(Float, nullable=True)
    total_estimated_cost = Column(Float, nullable=False, default=0.0)
    
    # Timestamps
    first_test_at = Column(DateTime, nullable=True)
    last_test_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'model_id': self.model_id,
            'total_tests': self.total_tests,
            'total_mines_tested': self.total_mines_tested,
            'avg_response_time_ms': self.avg_response_time_ms,
            'avg_fields_found': self.avg_fields_found,
            'avg_sources_count': self.avg_sources_count,
            'success_rate': self.success_rate,
            'data_success_rate': self.data_success_rate,
            'overall_consistency': self.overall_consistency,
            'critical_fields_consistency': self.critical_fields_consistency,
            'estimated_cost_per_request': self.estimated_cost_per_request,
            'total_estimated_cost': self.total_estimated_cost,
            'first_test_at': self.first_test_at.isoformat() if self.first_test_at else None,
            'last_test_at': self.last_test_at.isoformat() if self.last_test_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class FieldStatistics(Base):
    """Datenbank-Tabelle für Feld-Statistiken"""
    __tablename__ = 'field_statistics'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(100), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    total_searches = Column(Integer, nullable=False, default=0)
    times_found = Column(Integer, nullable=False, default=0)
    times_empty = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)  # 0.0 bis 1.0
    avg_confidence = Column(Float, nullable=True)  # Durchschnittliche Konfidenz wenn gefunden
    # ÄNDERUNG 13.07.2025: Conditional statistics tracking
    excluded_count = Column(Integer, nullable=False, default=0)  # Anzahl ausgeschlossener Einträge
    conditional_logic_applied = Column(Boolean, nullable=False, default=False)  # Flag für conditional fields
    last_updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_model_statistics_model_field', 'model_id', 'field_name'),
        Index('idx_model_statistics_success', 'field_name', 'success_rate'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'field_name': self.field_name,
            'total_searches': self.total_searches,
            'times_found': self.times_found,
            'times_empty': self.times_empty,
            'success_rate': self.success_rate,
            'avg_confidence': self.avg_confidence,
            # ÄNDERUNG 13.07.2025: Conditional statistics in API response
            'excluded_count': getattr(self, 'excluded_count', 0),
            'conditional_logic_applied': getattr(self, 'conditional_logic_applied', False),
            'effective_searches': self.total_searches,  # Für Rückwärtskompatibilität
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class ModelStatisticsComprehensive(Base):
    """
    Datenbank-Tabelle für umfassende Modell-Statistiken
    Eine Zeile pro AI-Modell mit allen wichtigen Performance-Kennzahlen
    """
    __tablename__ = 'model_statistics_comprehensive'
    
    model_id = Column(String(100), primary_key=True)
    
    # Basis-Performance Metriken
    total_searches = Column(Integer, nullable=False, default=0)
    successful_searches = Column(Integer, nullable=False, default=0)
    success_rate_percent = Column(Float, nullable=False, default=0.0)  # 0.0 bis 100.0
    
    # VOLLSTÄNDIGKEITSSCORE: Gefundene Felder / Erwartete Felder * 100
    total_expected_fields = Column(Integer, nullable=False, default=20)  # Anzahl erwarteter Felder
    avg_fields_found = Column(Float, nullable=False, default=0.0)  # Durchschnittlich gefundene Felder pro Suche
    completeness_score = Column(Float, nullable=False, default=0.0)  # 0.0 bis 100.0
    
    # KONSISTENZSCORE: Wie oft werden gleiche Werte bei mehrfachen Suchen gefunden
    consistency_score = Column(Float, nullable=False, default=0.0)  # 0.0 bis 100.0
    consistency_grade = Column(String(20), nullable=False, default='Unbekannt')  # A, B, C, D, F
    
    # QUELLENVIELFALT: Anzahl verschiedener Quellen pro Modell
    avg_sources_per_search = Column(Float, nullable=False, default=0.0)
    unique_sources_total = Column(Integer, nullable=False, default=0)
    source_diversity_score = Column(Float, nullable=False, default=0.0)  # 0.0 bis 100.0
    
    # PERFORMANCE METRIKEN
    avg_response_time_ms = Column(Float, nullable=False, default=0.0)
    avg_search_duration_ms = Column(Float, nullable=False, default=0.0)
    performance_category = Column(String(20), nullable=False, default='Standard')  # Schnell, Standard, Langsam
    
    # GESAMTSCORE: Normierter Score (0-100) für Modell-Bewertung
    overall_score = Column(Float, nullable=False, default=0.0)  # 0.0 bis 100.0
    score_category = Column(String(20), nullable=False, default='Ungetestet')  # Exzellent, Sehr Gut, Gut, Limitiert, Ungeeignet
    
    # SPEZIALISIERUNG: In welchen Bereichen ist das Modell besonders gut
    best_field_categories = Column(JSON, nullable=True)  # ["Grunddaten", "Finanzdaten", "Koordinaten"]
    specialization_score = Column(JSON, nullable=True)  # {"Grunddaten": 85, "Finanzdaten": 60, ...}
    
    # KOSTEN-EFFIZIENZ
    estimated_cost_per_search = Column(Float, nullable=True)
    cost_efficiency_score = Column(Float, nullable=False, default=50.0)  # 0.0 bis 100.0
    
    # TIMESTAMPS
    first_search_at = Column(DateTime, nullable=True)
    last_search_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_model_overall_score', 'overall_score'),
        Index('idx_model_consistency', 'consistency_score'),
        Index('idx_model_completeness', 'completeness_score'),
    )
    
    def calculate_overall_score(self) -> float:
        """
        Berechne den normierten Gesamtscore (0-100) basierend auf gewichteten Faktoren:
        - Vollständigkeit: 40% (wichtigster Faktor)
        - Konsistenz: 30% (Zuverlässigkeit)
        - Quellenvielfalt: 20% (Robustheit)
        - Performance: 10% (Effizienz)
        """
        # Basis-Score aus den Komponenten
        # BUGFIX 07.08.2025: NULL-Wert-Behandlung für NoneType-Vergleiche
        completeness = self.completeness_score or 0.0
        consistency = self.consistency_score or 0.0
        source_diversity = self.source_diversity_score or 0.0
        response_time = self.avg_response_time_ms or 0.0
        
        weighted_score = (
            completeness * 0.40 +
            consistency * 0.30 +
            source_diversity * 0.20 +
            min(100, (100 - (response_time / 1000 * 10))) * 0.10  # Performance-Penalty für langsame Modelle
        )
        
        # Qualitätsmodifikatoren
        quality_modifier = 1.0
        
        # BUGFIX 07.08.2025: NULL-Wert-Behandlung für NoneType-Vergleiche
        successful_searches = self.successful_searches or 0
        success_rate = self.success_rate_percent or 0.0
        
        # Bonus für viele erfolgreiche Suchen (Vertrauenswürdigkeit)
        if successful_searches >= 50:
            quality_modifier += 0.05
        elif successful_searches >= 20:
            quality_modifier += 0.03
        elif successful_searches >= 10:
            quality_modifier += 0.01
        
        # Malus für sehr niedrige Erfolgsrate
        if success_rate < 50:
            quality_modifier -= 0.10
        elif success_rate < 70:
            quality_modifier -= 0.05
        
        # Finaler Score
        final_score = min(100.0, max(0.0, weighted_score * quality_modifier))
        
        # Score-Kategorie bestimmen
        if final_score >= 86:
            self.score_category = 'Exzellent'
        elif final_score >= 71:
            self.score_category = 'Sehr Gut'
        elif final_score >= 51:
            self.score_category = 'Gut'
        elif final_score >= 31:
            self.score_category = 'Limitiert'
        else:
            self.score_category = 'Ungeeignet'
        
        return final_score
    
    def update_from_search_results(self, search_results: List[Any]):
        """
        Aktualisiere Statistiken basierend auf SearchResult-Objekten
        """
        if not search_results:
            return
        
        # Basis-Statistiken
        self.total_searches = len(search_results)
        self.successful_searches = sum(1 for sr in search_results if sr.structured_data and len(sr.structured_data) > 0)
        self.success_rate_percent = (self.successful_searches / self.total_searches * 100) if self.total_searches > 0 else 0
        
        # Vollständigkeits-Analyse
        field_counts = [len([k for k, v in (sr.structured_data or {}).items() if v and str(v).strip() and str(v).strip().upper() != 'X']) 
                       for sr in search_results]
        self.avg_fields_found = sum(field_counts) / len(field_counts) if field_counts else 0
        # BUGFIX 07.08.2025: NULL-Wert-Behandlung für total_expected_fields
        total_expected = self.total_expected_fields or 18  # Fallback zu Standard-Feldanzahl
        self.completeness_score = (self.avg_fields_found / total_expected * 100) if total_expected > 0 else 0
        
        # Performance-Metriken
        # search_duration wird in Sekunden gespeichert. Die aggregierte Kennzahl in diesem Modell
        # ist jedoch in Millisekunden benannt (…_ms). Daher hier die korrekte Umrechnung.
        durations_sec = [sr.search_duration for sr in search_results if sr.search_duration]
        avg_duration_sec = (sum(durations_sec) / len(durations_sec)) if durations_sec else 0.0
        self.avg_search_duration_ms = avg_duration_sec * 1000.0
        # Halte avg_response_time_ms konsistent (falls an anderer Stelle gelesen wird)
        self.avg_response_time_ms = self.avg_search_duration_ms
        
        # Performance-Kategorie - BUGFIX 07.08.2025: NULL-Wert-Behandlung
        duration_ms = self.avg_search_duration_ms or 0
        if duration_ms < 5000:  # < 5 Sekunden
            self.performance_category = 'Schnell'
        elif duration_ms < 15000:  # < 15 Sekunden
            self.performance_category = 'Standard'
        else:
            self.performance_category = 'Langsam'
        
        # Quellenvielfalt
        all_sources = []
        for sr in search_results:
            if sr.sources:
                all_sources.extend(sr.sources)
        unique_sources = len(set(str(source) for source in all_sources))
        self.unique_sources_total = unique_sources
        self.avg_sources_per_search = len(all_sources) / self.total_searches if self.total_searches > 0 else 0
        self.source_diversity_score = min(100, unique_sources * 5)  # 20 verschiedene Quellen = 100 Punkte
        
        # Timestamps
        timestamps = [sr.search_timestamp for sr in search_results if sr.search_timestamp]
        if timestamps:
            self.first_search_at = min(timestamps)
            self.last_search_at = max(timestamps)
        
        # Gesamtscore berechnen
        self.overall_score = self.calculate_overall_score()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'model_id': self.model_id,
            'model_name': self.model_id.replace(':', ' - ').title(),
            'provider': self.model_id.split(':')[0] if ':' in self.model_id else self.model_id,
            'total_searches': self.total_searches,
            'successful_searches': self.successful_searches,
            'success_rate_percent': round(self.success_rate_percent, 1),
            'completeness_score': round(self.completeness_score, 1),
            'consistency_score': round(self.consistency_score, 1),
            'consistency_grade': self.consistency_grade,
            'source_diversity_score': round(self.source_diversity_score, 1),
            'avg_fields_found': round(self.avg_fields_found, 1),
            'avg_sources_per_search': round(self.avg_sources_per_search, 1),
            'unique_sources_total': self.unique_sources_total,
            'performance_category': self.performance_category,
            'avg_search_duration_ms': round(self.avg_search_duration_ms, 1),
            'overall_score': round(self.overall_score, 1),
            'score_category': self.score_category,
            'best_field_categories': self.best_field_categories or [],
            'specialization_score': self.specialization_score or {},
            'cost_efficiency_score': round(self.cost_efficiency_score, 1),
            'estimated_cost_per_search': self.estimated_cost_per_search,
            'first_search_at': self.first_search_at.isoformat() if self.first_search_at else None,
            'last_search_at': self.last_search_at.isoformat() if self.last_search_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class SourceDiscoverySession(Base):
    """
    ÄNDERUNG 27.08.2025: Neue Tabelle für Sequential Field Orchestrator
    Tracking von Quellensuch-Sessions mit inkrementeller Akkumulation
    """
    __tablename__ = 'source_discovery_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    mine_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    commodity = Column(String(100), nullable=True)
    
    # Workflow-Status
    phase = Column(String(50), nullable=False, default='source_discovery')  # source_discovery, field_search, completed
    current_model_index = Column(Integer, nullable=False, default=0)
    total_models = Column(Integer, nullable=False, default=0)
    models_list = Column(JSON, nullable=False)  # Liste der verwendeten Modelle
    
    # Source Discovery Progress
    sources_discovered_total = Column(Integer, nullable=False, default=0)
    models_completed_discovery = Column(Integer, nullable=False, default=0)
    
    # Field Search Progress
    fields_to_search = Column(JSON, nullable=True)  # Liste aller zu suchenden Felder
    current_field_index = Column(Integer, nullable=False, default=0)
    fields_completed = Column(Integer, nullable=False, default=0)
    
    # Session Metadaten
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    discovery_completed_at = Column(DateTime, nullable=True)
    search_completed_at = Column(DateTime, nullable=True)
    total_duration_seconds = Column(Float, nullable=True)
    
    # Quality Metrics
    quality_score = Column(Float, nullable=False, default=0.0)
    final_results_count = Column(Integer, nullable=False, default=0)
    
    # Indizes
    __table_args__ = (
        Index('idx_source_session_mine', 'mine_name', 'session_id'),
        Index('idx_source_session_phase', 'phase', 'started_at'),
    )
    
    # Relationships
    contributions = relationship("ModelSourceContribution", back_populates="session", cascade="all, delete-orphan")
    field_search_results = relationship("FieldSearchResult", back_populates="session", cascade="all, delete-orphan")
    sequential_result = relationship("SequentialSearchResult", back_populates="session", uselist=False, cascade="all, delete-orphan")
    
    # Bequeme M:N-Relationship zu Sources über Contributions (viewonly)
    sources = relationship(
        "Source",
        secondary="model_source_contributions",
        primaryjoin="SourceDiscoverySession.session_id==ModelSourceContribution.session_id",
        secondaryjoin="Source.id==ModelSourceContribution.source_id",
        viewonly=True,
        backref="discovery_sessions"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'mine_name': self.mine_name,
            'country': self.country,
            'region': self.region,
            'commodity': self.commodity,
            'phase': self.phase,
            'current_model_index': self.current_model_index,
            'total_models': self.total_models,
            'models_list': self.models_list or [],
            'sources_discovered_total': self.sources_discovered_total,
            'models_completed_discovery': self.models_completed_discovery,
            'fields_to_search': self.fields_to_search or [],
            'current_field_index': self.current_field_index,
            'fields_completed': self.fields_completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'discovery_completed_at': self.discovery_completed_at.isoformat() if self.discovery_completed_at else None,
            'search_completed_at': self.search_completed_at.isoformat() if self.search_completed_at else None,
            'total_duration_seconds': self.total_duration_seconds,
            'quality_score': self.quality_score,
            'final_results_count': self.final_results_count
        }


class ModelSourceContribution(Base):
    """
    ÄNDERUNG 27.08.2025: Tracking welches Modell welche Quellen beigetragen hat
    Ermöglicht Analyse der Quellenentdeckungs-Effektivität pro Modell
    """
    __tablename__ = 'model_source_contributions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), ForeignKey('source_discovery_sessions.session_id', ondelete='CASCADE'), nullable=False, index=True)
    model_id = Column(String(100), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    
    # Contribution Details
    discovered_at = Column(DateTime, nullable=False, server_default=func.now())
    contribution_order = Column(Integer, nullable=False)  # Reihenfolge der Entdeckung (1, 2, 3, ...)
    is_unique_contribution = Column(Boolean, nullable=False, default=True)  # War diese Quelle neu?
    discovery_method = Column(String(50), nullable=False, default='search')  # search, related, referenced
    
    # Quality Assessment
    initial_quality_score = Column(Float, nullable=False, default=50.0)
    contribution_value = Column(Float, nullable=False, default=0.0)  # Wie wertvoll war diese Quelle
    
    # Relationships
    source = relationship("Source", backref="model_contributions")
    session = relationship("SourceDiscoverySession", back_populates="contributions")
    
    # Indizes
    __table_args__ = (
        Index('idx_model_contribution_session_model', 'session_id', 'model_id'),
        Index('idx_model_contribution_source', 'source_id', 'discovered_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'model_id': self.model_id,
            'source_id': self.source_id,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'contribution_order': self.contribution_order,
            'is_unique_contribution': self.is_unique_contribution,
            'discovery_method': self.discovery_method,
            'initial_quality_score': self.initial_quality_score,
            'contribution_value': self.contribution_value,
            'source': self.source.to_dict() if self.source else None
        }


class FieldSearchResult(Base):
    """
    ÄNDERUNG 27.08.2025: Ergebnisse der feld-spezifischen Suche
    Speichert Ergebnisse der Phase 2 (Field-by-Field Search)
    """
    __tablename__ = 'field_search_results'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), ForeignKey('source_discovery_sessions.session_id', ondelete='CASCADE'), nullable=False, index=True)
    model_id = Column(String(100), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    
    # Search Details
    searched_at = Column(DateTime, nullable=False, server_default=func.now())
    sources_used_count = Column(Integer, nullable=False, default=0)
    sources_used_ids = Column(JSON, nullable=True)  # Liste der Source-IDs die verwendet wurden
    
    # Results
    field_value_found = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    source_references = Column(JSON, nullable=True)  # Referenzen zu den Quellen die diesen Wert lieferten
    search_duration_seconds = Column(Float, nullable=True)
    
    # Quality Metrics
    result_quality = Column(String(20), nullable=False, default='unknown')  # high, medium, low, none
    verification_status = Column(String(20), nullable=False, default='unverified')  # verified, conflicting, unverified
    alternative_values = Column(JSON, nullable=True)  # Falls mehrere Werte gefunden wurden
    
    # Success Indicators
    search_successful = Column(Boolean, nullable=False, default=False)
    value_found = Column(Boolean, nullable=False, default=False)
    sources_matched = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    session = relationship("SourceDiscoverySession", back_populates="field_search_results")
    # Neue Relation: Assoziation zu verwendeten Quellen über Join-Tabelle
    source_usages = relationship("FieldSearchSourceUsage", back_populates="field_search", cascade="all, delete-orphan")
    # Bequeme ViewOnly M:N-Relation direkt zu Source
    used_sources = relationship(
        "Source",
        secondary="field_search_source_usages",
        primaryjoin="FieldSearchResult.id==FieldSearchSourceUsage.field_search_id",
        secondaryjoin="Source.id==FieldSearchSourceUsage.source_id",
        viewonly=True
    )
    
    # Indizes
    __table_args__ = (
        Index('idx_field_search_session_field', 'session_id', 'field_name'),
        Index('idx_field_search_model_field', 'model_id', 'field_name', 'searched_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'model_id': self.model_id,
            'field_name': self.field_name,
            'searched_at': self.searched_at.isoformat() if self.searched_at else None,
            'sources_used_count': self.sources_used_count,
            'sources_used_ids': self.sources_used_ids or [],
            'field_value_found': self.field_value_found,
            'confidence_score': self.confidence_score,
            'source_references': self.source_references or [],
            'search_duration_seconds': self.search_duration_seconds,
            'result_quality': self.result_quality,
            'verification_status': self.verification_status,
            'alternative_values': self.alternative_values or [],
            'search_successful': self.search_successful,
            'value_found': self.value_found,
            'sources_matched': self.sources_matched
        }


class FieldSearchSourceUsage(Base):
    """
    Assoziationstabelle zwischen FieldSearchResult und Source (welche Quellen wurden verwendet)
    """
    __tablename__ = 'field_search_source_usages'
    
    id = Column(Integer, primary_key=True)
    field_search_id = Column(Integer, ForeignKey('field_search_results.id', ondelete='CASCADE'), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey('sources.id', ondelete='CASCADE'), nullable=False, index=True)
    used_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Beziehungen
    field_search = relationship("FieldSearchResult", back_populates="source_usages")
    source = relationship("Source", backref="field_search_usages")
    
    # Indizes und Eindeutigkeit
    __table_args__ = (
        UniqueConstraint('field_search_id', 'source_id', name='uix_field_search_source'),
        Index('idx_fssu_field_search', 'field_search_id'),
        Index('idx_fssu_source', 'source_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'field_search_id': self.field_search_id,
            'source_id': self.source_id,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }


class SequentialSearchResult(Base):
    """
    ÄNDERUNG 27.08.2025: Konsolidierte Ergebnisse einer Sequential Search Session
    Speichert die finalen, zusammengefassten Ergebnisse des gesamten Workflows
    """
    __tablename__ = 'sequential_search_results'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), ForeignKey('source_discovery_sessions.session_id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    mine_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    commodity = Column(String(100), nullable=True)
    
    # Session Summary
    total_models_used = Column(Integer, nullable=False, default=0)
    total_sources_discovered = Column(Integer, nullable=False, default=0)
    total_fields_searched = Column(Integer, nullable=False, default=0)
    total_values_found = Column(Integer, nullable=False, default=0)
    
    # Final Consolidated Data
    final_structured_data = Column(JSON, nullable=True)  # Beste Werte für alle Felder
    field_confidence_scores = Column(JSON, nullable=True)  # Konfidenz pro Feld
    field_source_mapping = Column(JSON, nullable=True)  # Welche Quelle lieferte welchen Wert
    quality_assessment = Column(JSON, nullable=True)  # Qualitätsbewertung der Gesamtergebnisse
    
    # Performance Metrics
    total_duration_seconds = Column(Float, nullable=True)
    source_discovery_duration = Column(Float, nullable=True)
    field_search_duration = Column(Float, nullable=True)
    consolidation_duration = Column(Float, nullable=True)
    
    # Quality Indicators
    overall_quality_score = Column(Float, nullable=False, default=0.0)  # 0.0 bis 100.0
    completeness_percentage = Column(Float, nullable=False, default=0.0)  # % gefundener Felder
    source_diversity_score = Column(Float, nullable=False, default=0.0)  # Vielfalt der verwendeten Quellen
    model_consensus_score = Column(Float, nullable=False, default=0.0)  # Übereinstimmung zwischen Modellen
    
    # Status
    workflow_completed = Column(Boolean, nullable=False, default=False)
    has_errors = Column(Boolean, nullable=False, default=False)
    error_summary = Column(JSON, nullable=True)  # Zusammenfassung aufgetretener Fehler
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    session = relationship("SourceDiscoverySession", back_populates="sequential_result", uselist=False)
    
    # Indizes
    __table_args__ = (
        Index('idx_sequential_results_mine', 'mine_name', 'created_at'),
        Index('idx_sequential_results_quality', 'overall_quality_score', 'completeness_percentage'),
    )
    
    def calculate_quality_metrics(self):
        """
        Berechne Qualitäts-Metriken basierend auf den Ergebnissen
        """
        # Completeness: Prozentsatz der gefundenen Felder
        expected_fields = 18  # Standard Anzahl erwarteter Felder
        self.completeness_percentage = (self.total_values_found / expected_fields * 100) if expected_fields > 0 else 0
        
        # Source Diversity: Bewertung der Quellenvielfalt
        self.source_diversity_score = min(100, self.total_sources_discovered * 5)  # 20 Quellen = 100 Punkte
        
        # Ensure model_consensus_score is not None
        consensus_score = self.model_consensus_score or 0.0
        
        # Overall Quality: Gewichteter Score
        self.overall_quality_score = (
            self.completeness_percentage * 0.5 +
            self.source_diversity_score * 0.3 +
            consensus_score * 0.2
        )
        
        self.overall_quality_score = min(100.0, max(0.0, self.overall_quality_score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'mine_name': self.mine_name,
            'country': self.country,
            'region': self.region,
            'commodity': self.commodity,
            'total_models_used': self.total_models_used,
            'total_sources_discovered': self.total_sources_discovered,
            'total_fields_searched': self.total_fields_searched,
            'total_values_found': self.total_values_found,
            'final_structured_data': self.final_structured_data or {},
            'field_confidence_scores': self.field_confidence_scores or {},
            'field_source_mapping': self.field_source_mapping or {},
            'quality_assessment': self.quality_assessment or {},
            'total_duration_seconds': self.total_duration_seconds,
            'source_discovery_duration': self.source_discovery_duration,
            'field_search_duration': self.field_search_duration,
            'consolidation_duration': self.consolidation_duration,
            'overall_quality_score': self.overall_quality_score,
            'completeness_percentage': self.completeness_percentage,
            'source_diversity_score': self.source_diversity_score,
            'model_consensus_score': self.model_consensus_score,
            'workflow_completed': self.workflow_completed,
            'has_errors': self.has_errors,
            'error_summary': self.error_summary or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ModelFieldConsistency(Base):
    """
    Datenbank-Tabelle für Feld-spezifische Konsistenz-Analysen
    Tracks wie konsistent jedes Modell bei spezifischen Feldern ist
    """
    __tablename__ = 'model_field_consistency'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(100), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    
    # Konsistenz-Metriken
    total_searches = Column(Integer, nullable=False, default=0)
    times_found = Column(Integer, nullable=False, default=0)
    unique_values_found = Column(Integer, nullable=False, default=0)
    most_common_value = Column(Text, nullable=True)
    most_common_frequency = Column(Integer, nullable=False, default=0)
    
    # Konsistenz-Score für dieses spezifische Feld
    field_consistency_score = Column(Float, nullable=False, default=0.0)  # 0.0 bis 100.0
    
    # Alle gefundenen Werte mit Häufigkeit (für detaillierte Analyse)
    value_distribution = Column(JSON, nullable=True)  # {"Wert1": 5, "Wert2": 3, "Wert3": 1}
    
    # Qualitäts-Indikatoren
    avg_confidence = Column(Float, nullable=True)
    has_high_quality_sources = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    first_found_at = Column(DateTime, nullable=True)
    last_found_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_field_consistency_model_field', 'model_id', 'field_name'),
        Index('idx_field_consistency_score', 'field_name', 'field_consistency_score'),
    )
    
    def calculate_consistency_score(self) -> float:
        """
        Berechne Konsistenz-Score für dieses spezifische Feld:
        - Hohe Konsistenz: Immer der gleiche Wert gefunden
        - Niedrige Konsistenz: Viele verschiedene Werte
        """
        if self.times_found == 0:
            return 0.0
        
        # Basis-Score: Wie oft wurde der häufigste Wert gefunden
        consistency_rate = (self.most_common_frequency / self.times_found) if self.times_found > 0 else 0
        
        # Gewichtung basierend auf Anzahl Fundstellen
        reliability_weight = 1.0
        if self.times_found >= 10:
            reliability_weight = 1.0  # Volle Gewichtung bei vielen Fundstellen
        elif self.times_found >= 5:
            reliability_weight = 0.8  # Reduzierte Gewichtung
        elif self.times_found >= 3:
            reliability_weight = 0.6  # Weitere Reduktion
        else:
            reliability_weight = 0.4  # Minimale Gewichtung bei wenigen Fundstellen
        
        # Bonus für wenige verschiedene Werte (hohe Konsistenz)
        variety_penalty = 0
        if self.unique_values_found > 3:
            variety_penalty = (self.unique_values_found - 3) * 5  # Penalty für viele verschiedene Werte
        
        # Finaler Score
        final_score = min(100.0, max(0.0, (consistency_rate * 100 * reliability_weight) - variety_penalty))
        
        return final_score
    
    def update_from_field_data(self, field_values: List[str]):
        """
        Aktualisiere Konsistenz-Daten basierend auf gefundenen Feldwerten
        """
        if not field_values:
            return
        
        # Bereinige und zähle Werte
        cleaned_values = [str(val).strip() for val in field_values if val and str(val).strip() and str(val).strip().upper() != 'X']
        
        if not cleaned_values:
            return
        
        # Basis-Statistiken
        self.times_found = len(cleaned_values)
        unique_values = list(set(cleaned_values))
        self.unique_values_found = len(unique_values)
        
        # Häufigkeitsverteilung
        from collections import Counter
        value_counts = Counter(cleaned_values)
        self.value_distribution = dict(value_counts)
        
        # Häufigster Wert
        most_common = value_counts.most_common(1)[0]
        self.most_common_value = most_common[0]
        self.most_common_frequency = most_common[1]
        
        # Konsistenz-Score berechnen
        self.field_consistency_score = self.calculate_consistency_score()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'field_name': self.field_name,
            'total_searches': self.total_searches,
            'times_found': self.times_found,
            'unique_values_found': self.unique_values_found,
            'most_common_value': self.most_common_value,
            'most_common_frequency': self.most_common_frequency,
            'field_consistency_score': round(self.field_consistency_score, 1),
            'value_distribution': self.value_distribution or {},
            'avg_confidence': self.avg_confidence,
            'has_high_quality_sources': self.has_high_quality_sources,
            'first_found_at': self.first_found_at.isoformat() if self.first_found_at else None,
            'last_found_at': self.last_found_at.isoformat() if self.last_found_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class FieldValue(Base):
    """
    SCHEMA-NORMALISIERUNG 28.08.2025: Atomische Feldwerte ohne Quellenreferenzen
    Speichert nur den reinen Wert (z.B. "Kanada") ohne [1,2,3] Referenzen
    """
    __tablename__ = 'field_values'
    
    id = Column(Integer, primary_key=True)
    search_result_id = Column(Integer, ForeignKey('search_results.id'), nullable=False)
    field_name = Column(String(100), nullable=False, index=True)
    atomic_value = Column(Text, nullable=True)  # Nur der Wert, z.B. "Kanada"
    confidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    search_result = relationship("SearchResult", backref="field_values")
    field_sources = relationship("FieldValueSource", back_populates="field_value", cascade="all, delete-orphan")
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_field_values_result', 'search_result_id'),
        Index('idx_field_values_name', 'field_name'),
        Index('idx_field_values_atomic', 'atomic_value'),
        Index('idx_field_values_result_field', 'search_result_id', 'field_name'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'search_result_id': self.search_result_id,
            'field_name': self.field_name,
            'atomic_value': self.atomic_value,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'source_count': len(self.field_sources) if self.field_sources else 0
        }


class FieldValueSource(Base):
    """
    SCHEMA-NORMALISIERUNG 28.08.2025: N:M Beziehung zwischen Feldwerten und Quellen
    Ermöglicht saubere Trennung von Wert und Quellenreferenzen
    """
    __tablename__ = 'field_value_sources'
    
    id = Column(Integer, primary_key=True)
    field_value_id = Column(Integer, ForeignKey('field_values.id'), nullable=False)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    extraction_confidence = Column(Float, nullable=False, default=50.0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    field_value = relationship("FieldValue", back_populates="field_sources")
    source = relationship("Source", backref="field_value_sources")
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_fvs_field_value', 'field_value_id'),
        Index('idx_fvs_source', 'source_id'),
        Index('idx_fvs_field_source', 'field_value_id', 'source_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für API-Responses"""
        return {
            'id': self.id,
            'field_value_id': self.field_value_id,
            'source_id': self.source_id,
            'extraction_confidence': self.extraction_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'source': self.source.to_dict() if self.source else None
        }