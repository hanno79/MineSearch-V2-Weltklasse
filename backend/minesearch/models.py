"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Datenmodelle für MineSearch v2 - Source Registry
"""

# ÄNDERUNG 01.07.2025: Source Registry Modell für intelligente Quellenverwaltung

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

@dataclass
class SourceRecord:
    """Einzelner Eintrag in der Source Registry"""
    url: str
    domain: str
    country: Optional[str] = None
    region: Optional[str] = None
    source_type: str = "unknown"  # government, exchange, industry, database, document
    reliability_score: float = 50.0  # 0-100
    last_successful_access: Optional[datetime] = None
    last_attempted_access: Optional[datetime] = None
    total_searches: int = 0
    successful_searches: int = 0
    typical_content_types: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für JSON-Serialisierung"""
        return {
            "url": self.url,
            "domain": self.domain,
            "country": self.country,
            "region": self.region,
            "source_type": self.source_type,
            "reliability_score": self.reliability_score,
            "last_successful_access": self.last_successful_access.isoformat() if self.last_successful_access else None,
            "last_attempted_access": self.last_attempted_access.isoformat() if self.last_attempted_access else None,
            "total_searches": self.total_searches,
            "successful_searches": self.successful_searches,
            "typical_content_types": [],  # Entfernt in Migration vom 04.09.2025
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceRecord':
        """Erstelle aus Dictionary"""
        if data.get('last_successful_access'):
            data['last_successful_access'] = datetime.fromisoformat(data['last_successful_access'])
        if data.get('last_attempted_access'):
            data['last_attempted_access'] = datetime.fromisoformat(data['last_attempted_access'])
        return cls(**data)
    
    def update_access(self, success: bool, content_type: Optional[str] = None):
        """Aktualisiere Zugriffstatistiken"""
        self.total_searches += 1
        self.last_attempted_access = datetime.now()
        
        if success:
            self.successful_searches += 1
            self.last_successful_access = datetime.now()
            
            # Aktualisiere Reliability Score
            success_rate = self.successful_searches / self.total_searches
            self.reliability_score = min(100, success_rate * 100)
            
            # Content-Type Funktionalität entfernt in Migration vom 04.09.2025
            # typical_content_types wurde in normalisierte Tabellen migriert
            pass  # Placeholder für zukünftige Content-Type Logik
    
    @property
    def success_rate(self) -> float:
        """Berechne Erfolgsquote"""
        if self.total_searches == 0:
            return 0.0
        return self.successful_searches / self.total_searches


@dataclass
class SearchSession:
    """Tracking einer Such-Session mit allen durchsuchten Quellen"""
    session_id: str
    mine_name: str
    country: Optional[str]
    region: Optional[str]
    started_at: datetime = field(default_factory=datetime.now)
    
    # Quellen-Tracking
    discovered_sources: List[str] = field(default_factory=list)  # Alle gefundenen URLs
    searched_sources: List[str] = field(default_factory=list)    # Tatsächlich durchsuchte URLs
    successful_sources: List[Dict[str, Any]] = field(default_factory=list)  # Quellen mit Ergebnissen
    failed_sources: List[Dict[str, Any]] = field(default_factory=list)      # Quellen ohne Ergebnisse
    
    # Statistiken
    total_discovered: int = 0
    total_searched: int = 0
    total_successful: int = 0
    search_duration_seconds: Optional[float] = None
    
    def add_discovered_source(self, url: str):
        """Füge entdeckte Quelle hinzu"""
        if url not in self.discovered_sources:
            self.discovered_sources.append(url)
            self.total_discovered += 1
    
    def add_searched_source(self, url: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """Füge durchsuchte Quelle hinzu"""
        if url not in self.searched_sources:
            self.searched_sources.append(url)
            self.total_searched += 1
        
        source_info = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        # Überprüfe ob bereits in failed_sources (für Updates)
        existing_failed = None
        for i, failed_source in enumerate(self.failed_sources):
            if failed_source['url'] == url:
                existing_failed = i
                break
        
        if success:
            # Entferne aus failed wenn vorhanden (Status-Update)
            if existing_failed is not None:
                self.failed_sources.pop(existing_failed)
            else:
                self.total_successful += 1
            self.successful_sources.append(source_info)
        else:
            # Nur hinzufügen wenn nicht bereits erfolgreich
            already_successful = any(s['url'] == url for s in self.successful_sources)
            if not already_successful and existing_failed is None:
                self.failed_sources.append(source_info)
    
    def finalize(self):
        """Beende Session und berechne Dauer"""
        self.search_duration_seconds = (datetime.now() - self.started_at).total_seconds()
    
    def get_summary(self) -> Dict[str, Any]:
        """Erstelle Zusammenfassung der Session"""
        return {
            "session_id": self.session_id,
            "mine_name": self.mine_name,
            "country": self.country,
            "region": self.region,
            "started_at": self.started_at.isoformat(),
            "duration_seconds": self.search_duration_seconds,
            "statistics": {
                "discovered": self.total_discovered,
                "searched": self.total_searched,
                "successful": self.total_successful,
                "failed": self.total_searched - self.total_successful,
                "success_rate": (self.total_successful / self.total_searched * 100) if self.total_searched > 0 else 0
            },
            "sources": {
                "successful": self.successful_sources,
                "failed": self.failed_sources
            }
        }


class SourceRegistry:
    """Source Registry mit Datenbank-Backend"""
    
    def __init__(self):
        # Import hier um zirkuläre Imports zu vermeiden
        from minesearch.database import db_manager
        self.db = db_manager
        self.sessions: Dict[str, SearchSession] = {}  # Sessions bleiben in-memory
    
    def add_source(self, source: SourceRecord):
        """Füge Quelle zur Registry hinzu"""
        # Konvertiere SourceRecord zu DB-Eintrag
        self.db.add_or_update_source(
            url=source.url,
            domain=source.domain,
            country=source.country,
            region=source.region,
            source_type=source.source_type,
            metadata=source.metadata
        )
    
    def get_source(self, url: str) -> Optional[SourceRecord]:
        """Hole Quelle aus Registry"""
        from minesearch.database import Source
        with self.db.get_session() as session:
            db_source = session.query(Source).filter_by(url=url).first()
            if db_source:
                return SourceRecord(
                    url=db_source.url,
                    domain=db_source.domain,
                    country=db_source.country,
                    region=db_source.region,
                    source_type=db_source.source_type,
                    reliability_score=db_source.reliability_score,
                    last_successful_access=db_source.last_successful_access,
                    last_attempted_access=db_source.last_attempted_access,
                    total_searches=db_source.total_searches,
                    successful_searches=db_source.successful_searches,
                    # NORMALISIERUNG FIX 04.09.2025: JSON-Spalten entfernt
                    typical_content_types=[],
                    metadata={}
                )
        return None
    
    def get_sources_for_country(self, country: str, min_reliability: float = 50.0) -> List[SourceRecord]:
        """Hole alle Quellen für ein Land mit Mindest-Zuverlässigkeit"""
        db_sources = self.db.get_sources_for_search(country=country, min_reliability=min_reliability)
        return self._convert_db_sources(db_sources)
    
    def get_sources_for_region(self, country: str, region: str, min_reliability: float = 50.0) -> List[SourceRecord]:
        """Hole alle Quellen für eine Region"""
        db_sources = self.db.get_sources_for_search(
            country=country, region=region, min_reliability=min_reliability
        )
        return self._convert_db_sources(db_sources)
    
    def get_top_sources(self, limit: int = 10, source_type: Optional[str] = None) -> List[SourceRecord]:
        """Hole Top-Quellen sortiert nach Zuverlässigkeit"""
        from minesearch.database import Source
        with self.db.get_session() as session:
            query = session.query(Source)
            if source_type:
                query = query.filter_by(source_type=source_type)
            db_sources = query.order_by(Source.reliability_score.desc()).limit(limit).all()
            return self._convert_db_sources(db_sources)
    
    def create_session(self, mine_name: str, country: Optional[str] = None, region: Optional[str] = None) -> SearchSession:
        """Erstelle neue Such-Session"""
        import uuid
        session_id = str(uuid.uuid4())
        session = SearchSession(
            session_id=session_id,
            mine_name=mine_name,
            country=country,
            region=region
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SearchSession]:
        """Hole Session"""
        return self.sessions.get(session_id)
    
    def _convert_db_sources(self, db_sources) -> List[SourceRecord]:
        """Konvertiere DB Sources zu SourceRecord Objekten"""
        records = []
        for db_source in db_sources:
            records.append(SourceRecord(
                url=db_source.url,
                domain=db_source.domain,
                country=db_source.country,
                region=db_source.region,
                source_type=db_source.source_type,
                reliability_score=db_source.reliability_score,
                last_successful_access=db_source.last_successful_access,
                last_attempted_access=db_source.last_attempted_access,
                total_searches=db_source.total_searches,
                successful_searches=db_source.successful_searches,
                # NORMALISIERUNG FIX 04.09.2025: JSON-Spalten entfernt
                typical_content_types=[],
                metadata={}
            ))
        return records
    
    def save_to_file(self, filepath: str):
        """Legacy Methode - Daten sind jetzt in DB"""
        # Nicht mehr benötigt, aber für Kompatibilität behalten
        pass
    
    def load_from_file(self, filepath: str):
        """Legacy Methode - Daten sind jetzt in DB"""
        # Nicht mehr benötigt, aber für Kompatibilität behalten
        pass


# Globale Registry-Instanz
source_registry = SourceRegistry()

# Lade vorhandene Daten beim Import
import os
registry_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'source_registry.json')
if os.path.exists(os.path.dirname(registry_file)):
    source_registry.load_from_file(registry_file)