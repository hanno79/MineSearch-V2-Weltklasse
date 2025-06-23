"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für Agent Coordinator
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional


class AgentStrength(Enum):
    """Stärken der verschiedenen Agenten"""
    EXCELLENT = 5
    VERY_GOOD = 4
    GOOD = 3
    AVERAGE = 2
    WEAK = 1


@dataclass
class AgentCapability:
    """Fähigkeiten eines Agenten für ein bestimmtes Feld"""
    agent_name: str
    field: str
    strength: AgentStrength
    preferred_sources: List[str]
    notes: str


@dataclass
class SearchPhase:
    """Eine Phase der Suchausführung"""
    phase_number: int
    agents: List[str]
    fields: List[str]
    priority: str


@dataclass
class AgentAssignment:
    """Zuweisung von Agenten zu Feldern"""
    field: str
    agents: List[str]
    priority: int
    strategy: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetric:
    """Leistungsmetriken für Agenten"""
    agent_name: str
    field: str
    success_count: int = 0
    failure_count: int = 0
    average_score: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Berechnet Erfolgsrate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
