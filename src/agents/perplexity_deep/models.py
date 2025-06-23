"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Modell-Definitionen für Perplexity Deep Research
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ResearchPhase:
    """Eine Phase der Deep Research"""
    phase_number: int
    focus_area: str
    search_queries: List[str]
    findings: List[Dict[str, Any]]
    confidence: float
    next_steps: List[str]

@dataclass
class DeepResearchResult:
    """Ergebnis der Deep Research"""
    total_sources_analyzed: int
    total_search_iterations: int
    confidence_score: float
    key_findings: List[Dict[str, Any]]
    research_phases: List[ResearchPhase]
    comprehensive_report: str