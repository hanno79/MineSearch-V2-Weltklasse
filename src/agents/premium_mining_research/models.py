"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für Premium Mining Research
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


@dataclass
class ResearchPhase:
    """Eine Phase der Recherche"""
    name: str
    description: str
    max_duration: int  # Sekunden
    required_agents: List[str]
    focus_areas: List[str]


@dataclass
class ResearchMetadata:
    """Metadaten für Research-Session"""
    start_time: datetime
    end_time: Optional[datetime] = None
    phases_completed: List[str] = None
    sources_discovered: int = 0
    documents_analyzed: int = 0
    keywords_used: int = 0
    errors: List[str] = None
    total_duration: Optional[float] = None
    
    def __post_init__(self):
        if self.phases_completed is None:
            self.phases_completed = []
        if self.errors is None:
            self.errors = []


@dataclass
class QualityIndicators:
    """Qualitätsindikatoren für Recherche-Ergebnisse"""
    completeness_score: float  # 0-1
    source_diversity: float  # 0-1
    confidence_average: float  # 0-1
    verification_ratio: float  # 0-1
    language_coverage: float  # 0-1
    
    @property
    def overall_quality(self) -> float:
        """Berechnet Gesamt-Qualitätsscore"""
        return (
            self.completeness_score * 0.3 +
            self.source_diversity * 0.2 +
            self.confidence_average * 0.2 +
            self.verification_ratio * 0.2 +
            self.language_coverage * 0.1
        )


@dataclass
class SearchQuery:
    """Optimierte Suchanfrage"""
    query_text: str
    target_field: str
    priority: str  # high, medium, low
    language: str
    agent_preferences: List[str]
    source_restrictions: List[str] = None
    
    def __post_init__(self):
        if self.source_restrictions is None:
            self.source_restrictions = []


class SourceReliability(Enum):
    """Zuverlässigkeit von Quellen"""
    OFFICIAL = "official"  # Regierungsquellen
    VERIFIED = "verified"  # Verifizierte Industriequellen
    TRUSTED = "trusted"  # Bekannte vertrauenswürdige Quellen
    STANDARD = "standard"  # Standard-Quellen
    UNVERIFIED = "unverified"  # Nicht verifizierte Quellen


@dataclass
class CrawlResult:
    """Ergebnis eines Web-Crawls"""
    url: str
    content: str
    extracted_data: Dict[str, Any]
    confidence_score: float
    source_reliability: SourceReliability
    extraction_timestamp: datetime
    language: str
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []