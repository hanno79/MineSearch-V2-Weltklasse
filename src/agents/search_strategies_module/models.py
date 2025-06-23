"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für Search Strategies
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any


class SearchScope(Enum):
    """Suchbereich-Definitionen"""
    GLOBAL = "global"
    REGIONAL = "regional"
    LOCAL = "local"
    SITE_SPECIFIC = "site_specific"
    DEEP_WEB = "deep_web"
    GOVERNMENT = "government"
    INDUSTRY = "industry"
    NEWS = "news"
    ACADEMIC = "academic"
    FINANCIAL = "financial"


class SearchDepth(Enum):
    """Such-Tiefe"""
    SHALLOW = "shallow"  # Schnelle Oberflächensuche
    STANDARD = "standard"  # Normale Suche
    DEEP = "deep"  # Tiefe Suche
    EXHAUSTIVE = "exhaustive"  # Erschöpfende Suche


@dataclass
class SearchStrategy:
    """Eine Such-Strategie"""
    name: str
    scope: SearchScope
    depth: SearchDepth
    time_budget: int  # Sekunden
    agent_preferences: List[str]
    keyword_strategy: str
    parallel_searches: int
    retry_strategy: Dict[str, Any]


@dataclass
class SearchProgress:
    """Fortschritt einer Suche"""
    total_agents: int
    completed_agents: int
    total_results: int
    elapsed_time: float
    estimated_time_remaining: float
    current_phase: str


@dataclass
class SearchResult:
    """Zusammengefasstes Suchergebnis"""
    strategy_name: str
    total_results: int
    unique_results: int
    quality_score: float
    execution_time: float
    agents_used: List[str]
    fields_covered: List[str]
