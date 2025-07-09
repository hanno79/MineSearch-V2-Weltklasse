"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Datenbank-Schema und -Verwaltung für MineSearch v2
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from config import Config

logger = logging.getLogger(__name__)

# Datenbank-Basis
Base = declarative_base()

# Globale Engine und Session Factory
engine = None
SessionLocal = None

def init_db():
    """Initialisiere Datenbank-Verbindung"""
    global engine, SessionLocal
    
    config = Config()
    database_url = config.get('DATABASE_URL', 'sqlite:///./mines.db')
    
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith('sqlite') else {}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Erstelle Tabellen
    Base.metadata.create_all(bind=engine)
    
    logger.info(f"Datenbank initialisiert: {database_url}")

def get_db():
    """Dependency für FastAPI/andere Frameworks"""
    if SessionLocal is None:
        init_db()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        Index('idx_country_region', 'country', 'region'),
        Index('idx_source_type_score', 'source_type', 'reliability_score'),
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
            'typical_content_types': self.typical_content_types or [],
            'metadata': self.extra_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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
    
    @classmethod
    def classify_source_type(cls, url: str, domain: str) -> str:
        """
        Automatische Klassifizierung des Quellentyps basierend auf URL/Domain
        
        ÄNDERUNG 02.07.2025: Verbesserte Typerkennung
        ÄNDERUNG 08.07.2025: Erweiterte Patterns aus Bereinigungsskript
        """
        import re
        
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
        ÄNDERUNG 08.07.2025: Ermittle Land basierend auf Domain
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
            # ÄNDERUNG 08.07.2025: Spezifische kanadische .com Domains
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
            
            # Südafrika
            '.gov.za': 'South Africa',
            '.co.za': 'South Africa',
        }
        
        # Prüfe spezifische Domains zuerst
        for domain_pattern, country in domain_country_map.items():
            if domain_pattern in domain_lower:
                return country
        
        # Prüfe TLD
        if domain_lower.endswith('.ca'):
            return 'Canada'
        elif domain_lower.endswith('.us'):
            return 'USA'
        elif domain_lower.endswith('.au'):
            return 'Australia'
        elif domain_lower.endswith('.za'):
            return 'South Africa'
        elif domain_lower.endswith('.cl'):
            return 'Chile'
        elif domain_lower.endswith('.pe'):
            return 'Peru'
        elif domain_lower.endswith('.mx'):
            return 'Mexico'
        elif domain_lower.endswith('.br'):
            return 'Brazil'
        elif domain_lower.endswith('.ar'):
            return 'Argentina'
        elif domain_lower.endswith('.co'):
            return 'Colombia'
        
        return None


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
    
    # Ergebnisse
    structured_data = Column(JSON, nullable=True)  # Alle extrahierten Felder
    structured_data_with_sources = Column(JSON, nullable=True)  # Mit Quellennummern
    sources = Column(JSON, nullable=True)  # Gefundene Quellen
    source_index = Column(JSON, nullable=True)  # Quellen-Index
    
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
            'data_success_rate': self.data_success_rate,  # ÄNDERUNG 07.07.2025: Daten-Erfolgsrate
            'overall_consistency': self.overall_consistency,
            'critical_fields_consistency': self.critical_fields_consistency,
            'estimated_cost_per_request': self.estimated_cost_per_request,
            'total_estimated_cost': self.total_estimated_cost,
            'first_test_at': self.first_test_at.isoformat() if self.first_test_at else None,
            'last_test_at': self.last_test_at.isoformat() if self.last_test_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class FieldStatistics(Base):
    """Datenbank-Tabelle für Feld-spezifische Statistiken"""
    __tablename__ = 'field_statistics'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(100), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    total_searches = Column(Integer, nullable=False, default=0)
    times_found = Column(Integer, nullable=False, default=0)
    times_empty = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)  # 0.0 bis 1.0
    avg_confidence = Column(Float, nullable=True)  # Durchschnittliche Konfidenz wenn gefunden
    last_updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Indizes für Performance
    __table_args__ = (
        Index('idx_model_field', 'model_id', 'field_name'),
        Index('idx_field_success', 'field_name', 'success_rate'),
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
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class DatabaseManager:
    """Verwaltung der Datenbankverbindung und -operationen"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(
            self.database_url, 
            echo=False,  # Setze auf True für SQL-Debugging
            connect_args={"check_same_thread": False}  # Nur für SQLite
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Erstelle Tabellen wenn nicht vorhanden
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Datenbank initialisiert: {self.database_url}")
    
    def get_session(self) -> Session:
        """Hole eine neue Datenbank-Session"""
        return self.SessionLocal()
    
    def add_or_update_source(self, url: str, domain: str, country: Optional[str] = None,
                            region: Optional[str] = None, source_type: str = 'unknown',
                            metadata: Optional[Dict[str, Any]] = None) -> Source:
        """Füge neue Quelle hinzu oder aktualisiere bestehende"""
        # ÄNDERUNG 02.07.2025: URL-Normalisierung zur Vermeidung von Duplikaten
        from urllib.parse import urlparse
        
        # Normalisiere URL - entferne Query-Parameter für Vergleiche
        if not url.startswith('search:'):
            try:
                parsed = urlparse(url)
                # Basis-URL ohne Query für Datenbanksuche
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
                # Verwende Domain aus URL falls nicht gegeben
                if not domain:
                    domain = parsed.netloc
            except:
                base_url = url
        else:
            # Spezialbehandlung für Document-Search
            base_url = url
            domain = 'document_search'
        
        # ÄNDERUNG 08.07.2025: Automatische Quellentyp-Klassifizierung und Land-Erkennung
        if source_type == 'unknown' or source_type == 'url':
            source_type = Source.classify_source_type(url, domain)
        
        # Automatische Land-Erkennung wenn nicht angegeben
        if not country:
            detected_country = Source.get_country_from_domain(url, domain)
            if detected_country:
                country = detected_country
            
        with self.get_session() as session:
            # ÄNDERUNG 08.07.2025: Suche nach URL statt Domain für genaueres Tracking
            # Prüfe ob Quelle bereits existiert - suche nach exakter URL
            source = session.query(Source).filter_by(url=base_url).first()
            
            if source:
                # Aktualisiere bestehende Quelle
                if country and not source.country:
                    source.country = country
                if region and not source.region:
                    source.region = region
                # Aktualisiere Typ nur wenn neuer Typ spezifischer ist
                if source_type != 'unknown' and (source.source_type == 'unknown' or source_type != source.source_type):
                    logger.info(f"[DB] Aktualisiere Quellentyp für {domain}: {source.source_type} → {source_type}")
                    source.source_type = source_type
                if metadata:
                    source.extra_metadata = {**(source.extra_metadata or {}), **metadata}
                # Neuberechnung des Scores bei Aktualisierung
                source.reliability_score = source.calculate_reliability_score()
            else:
                # Erstelle neue Quelle mit normalisierter URL
                source = Source(
                    url=base_url,  # Verwende normalisierte URL
                    domain=domain,
                    country=country,
                    region=region,
                    source_type=source_type,
                    extra_metadata=metadata
                )
                session.add(source)
                logger.info(f"[DB] Neue Quelle hinzugefügt: {domain} (Typ: {source_type})")
            
            session.commit()
            session.refresh(source)
            return source
    
    def get_sources_for_search(self, country: Optional[str] = None, region: Optional[str] = None,
                              source_type: Optional[str] = None, min_reliability: float = 30.0, 
                              limit: int = 50, offset: int = 0) -> List[Source]:
        """Hole relevante Quellen für eine Suche"""
        with self.get_session() as session:
            query = session.query(Source).filter(Source.reliability_score >= min_reliability)
            
            if country:
                # Länderspezifische und globale Quellen
                query = query.filter(
                    (Source.country == country) | (Source.country.is_(None))
                )
                
                if region:
                    # Regionsspezifische Quellen priorisieren
                    query = query.filter(
                        (Source.region == region) | (Source.region.is_(None))
                    )
            
            # Filter nach Quellentyp wenn angegeben
            if source_type:
                query = query.filter(Source.source_type == source_type)
            
            # Sortiere nach Zuverlässigkeit und Erfolgsquote
            sources = query.order_by(
                Source.reliability_score.desc(),
                Source.successful_searches.desc()
            ).offset(offset).limit(limit).all()
            
            return sources
    
    def update_source_statistics(self, url: str, success: bool, content_type: Optional[str] = None):
        """Aktualisiere Statistiken nach einer Suche"""
        with self.get_session() as session:
            # ÄNDERUNG 08.07.2025: Flexible URL-Suche
            source = session.query(Source).filter_by(url=url).first()
            
            # Fallback: Versuche mit normalisierter URL
            if not source:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
                    source = session.query(Source).filter_by(url=normalized_url).first()
                except:
                    pass
            
            # Fallback: Suche nach Domain
            if not source:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    if parsed.netloc:
                        source = session.query(Source).filter_by(domain=parsed.netloc).first()
                except:
                    pass
            
            if source:
                source.update_access(success, content_type)
                session.commit()
            else:
                logger.debug(f"[DB] Source nicht gefunden für Update: {url}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hole Gesamt-Statistiken"""
        with self.get_session() as session:
            total_sources = session.query(Source).count()
            
            # Quellen pro Land
            country_stats = session.query(
                Source.country, 
                func.count(Source.id)
            ).group_by(Source.country).all()
            
            # Top Quellen
            top_sources = session.query(Source).order_by(
                Source.reliability_score.desc()
            ).limit(10).all()
            
            # Erfolgsraten
            avg_success_rate = session.query(
                func.avg(Source.successful_searches * 100.0 / Source.total_searches)
            ).filter(Source.total_searches > 0).scalar() or 0
            
            return {
                'total_sources': total_sources,
                'sources_by_country': {
                    country or 'Global': count for country, count in country_stats
                },
                'top_sources': [source.to_dict() for source in top_sources],
                'average_success_rate': round(avg_success_rate, 2)
            }
    
    # ÄNDERUNG 07.07.2025: Fehlende Methode für Quellen-Statistiken
    def get_source_statistics(self) -> Dict[str, Any]:
        """Hole detaillierte Quellen-Statistiken für die API"""
        return self.get_statistics()  # Verwende existierende Methode
    
    # ÄNDERUNG 02.07.2025: Methoden für SearchResult Management
    def save_search_result(self, result_data: Dict[str, Any]) -> SearchResult:
        """Speichere ein Suchergebnis in der Datenbank"""
        with self.get_session() as session:
            search_result = SearchResult(
                session_id=result_data.get('session_id'),
                mine_name=result_data['mine_name'],
                country=result_data.get('country'),
                region=result_data.get('region'),
                commodity=result_data.get('commodity'),
                model_used=result_data['model_used'],
                search_type=result_data.get('search_type'),
                search_duration=result_data.get('search_duration'),
                structured_data=result_data.get('structured_data'),
                structured_data_with_sources=result_data.get('structured_data_with_sources'),
                sources=result_data.get('sources'),
                source_index=result_data.get('source_index'),
                data_quality=result_data.get('data_quality'),
                success=result_data.get('success', True),
                error_message=result_data.get('error_message'),
                source_discovery_session=result_data.get('source_discovery_session')
            )
            session.add(search_result)
            session.commit()
            logger.info(f"[DB] Suchergebnis gespeichert: {search_result.mine_name} (ID: {search_result.id})")
            return search_result
    
    def get_search_results(self, limit: int = 50, offset: int = 0, 
                          mine_name: Optional[str] = None,
                          country: Optional[str] = None,
                          session_id: Optional[str] = None,
                          days_back: Optional[int] = None) -> List[SearchResult]:
        """Hole Suchergebnisse mit Filtern"""
        with self.get_session() as session:
            query = session.query(SearchResult)
            
            if mine_name:
                query = query.filter(SearchResult.mine_name.ilike(f'%{mine_name}%'))
            if country:
                query = query.filter(SearchResult.country == country)
            if session_id:
                query = query.filter(SearchResult.session_id == session_id)
            if days_back:
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(days=days_back)
                query = query.filter(SearchResult.search_timestamp >= cutoff)
            
            results = query.order_by(
                SearchResult.search_timestamp.desc()
            ).offset(offset).limit(limit).all()
            
            return results
    
    def get_search_result_by_id(self, result_id: int) -> Optional[SearchResult]:
        """Hole einzelnes Suchergebnis nach ID"""
        with self.get_session() as session:
            return session.query(SearchResult).filter_by(id=result_id).first()
    
    def get_result_statistics(self) -> Dict[str, Any]:
        """Hole Statistiken über gespeicherte Ergebnisse"""
        with self.get_session() as session:
            total = session.query(SearchResult).count()
            successful = session.query(SearchResult).filter(SearchResult.success == True).count()
            
            # Ergebnisse nach Modell
            by_model = {}
            model_counts = session.query(
                SearchResult.model_used,
                func.count(SearchResult.id)
            ).group_by(SearchResult.model_used).all()
            
            for model, count in model_counts:
                by_model[model] = count
            
            # Durchschnittliche Datenqualität
            avg_quality = session.query(
                func.avg(
                    func.json_extract(SearchResult.data_quality, '$.completeness_percentage')
                )
            ).filter(SearchResult.success == True).scalar() or 0
            
            # Letzte Suchen
            recent = session.query(SearchResult).order_by(
                SearchResult.search_timestamp.desc()
            ).limit(10).all()
            
            return {
                'total_results': total,
                'successful_results': successful,
                'results_by_model': by_model,
                'average_data_quality': float(avg_quality),
                'recent_searches': [r.to_dict() for r in recent]
            }
    
    def get_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Hole gruppierte Sessions"""
        with self.get_session() as session:
            # Gruppiere nach session_id
            sessions = session.query(
                SearchResult.session_id,
                func.count(SearchResult.id).label('count'),
                func.min(SearchResult.search_timestamp).label('start_time'),
                func.max(SearchResult.search_timestamp).label('end_time')
            ).filter(
                SearchResult.session_id.isnot(None)
            ).group_by(
                SearchResult.session_id
            ).order_by(
                func.max(SearchResult.search_timestamp).desc()
            ).limit(limit).all()
            
            result = []
            for sess_id, count, start, end in sessions:
                # Hole erste Mine als Beispiel
                first_result = session.query(SearchResult).filter_by(
                    session_id=sess_id
                ).first()
                
                result.append({
                    'session_id': sess_id,
                    'mine_count': count,
                    'start_time': start.isoformat() if start else None,
                    'end_time': end.isoformat() if end else None,
                    'example_mine': first_result.mine_name if first_result else None
                })
            
            return result


# Globale Datenbank-Instanz
db_manager = DatabaseManager()