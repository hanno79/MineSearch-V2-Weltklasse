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
            "typical_content_types": self.typical_content_types,
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
            
            # Füge Content-Type hinzu wenn neu
            if content_type and content_type not in self.typical_content_types:
                self.typical_content_types.append(content_type)
    
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
    """In-Memory Source Registry (später durch Datenbank ersetzen)"""
    
    def __init__(self):
        self.sources: Dict[str, SourceRecord] = {}
        self.sessions: Dict[str, SearchSession] = {}
    
    def add_source(self, source: SourceRecord):
        """Füge Quelle zur Registry hinzu"""
        self.sources[source.url] = source
    
    def get_source(self, url: str) -> Optional[SourceRecord]:
        """Hole Quelle aus Registry"""
        return self.sources.get(url)
    
    def get_sources_for_country(self, country: str, min_reliability: float = 50.0) -> List[SourceRecord]:
        """Hole alle Quellen für ein Land mit Mindest-Zuverlässigkeit"""
        return [
            source for source in self.sources.values()
            if source.country == country and source.reliability_score >= min_reliability
        ]
    
    def get_sources_for_region(self, country: str, region: str, min_reliability: float = 50.0) -> List[SourceRecord]:
        """Hole alle Quellen für eine Region"""
        return [
            source for source in self.sources.values()
            if source.country == country and source.region == region and source.reliability_score >= min_reliability
        ]
    
    def get_top_sources(self, limit: int = 10, source_type: Optional[str] = None) -> List[SourceRecord]:
        """Hole Top-Quellen sortiert nach Zuverlässigkeit"""
        sources = list(self.sources.values())
        
        if source_type:
            sources = [s for s in sources if s.source_type == source_type]
        
        # Sortiere nach Reliability Score
        sources.sort(key=lambda s: s.reliability_score, reverse=True)
        
        return sources[:limit]
    
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
    
    def save_to_file(self, filepath: str):
        """Speichere Registry in Datei (temporär bis DB implementiert)"""
        data = {
            "sources": {url: source.to_dict() for url, source in self.sources.items()},
            "sessions": {sid: session.get_summary() for sid, session in self.sessions.items()}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """Lade Registry aus Datei"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Lade Quellen
            for url, source_data in data.get("sources", {}).items():
                self.sources[url] = SourceRecord.from_dict(source_data)
            
            # Sessions werden nicht geladen (nur aktuelle Session relevant)
            
        except FileNotFoundError:
            # Keine gespeicherte Registry - starte leer
            pass


# Globale Registry-Instanz
source_registry = SourceRegistry()

# Lade vorhandene Daten beim Import
import os
registry_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'source_registry.json')
if os.path.exists(os.path.dirname(registry_file)):
    source_registry.load_from_file(registry_file)