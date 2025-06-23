"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Research-Phasen Definition und Management
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..base_agent import MineQuery


class PhaseType(Enum):
    """Typen von Research-Phasen"""
    DISCOVERY = "discovery"
    DEEP_DIVE = "deep_dive"
    ANALYSIS = "analysis"
    VERIFICATION = "verification"
    SPECIALIZED = "specialized"


@dataclass
class ResearchPhase:
    """Definition einer Research-Phase"""
    name: str
    type: PhaseType
    description: str
    max_duration: int  # Sekunden
    required_agents: List[str]
    focus_areas: List[str]
    priority: int = 1  # 1 = höchste Priorität
    conditional: bool = False  # Ob Phase bedingt ausgeführt wird
    condition: Optional[Dict[str, Any]] = None  # Bedingungen für Ausführung


class ResearchPhaseManager:
    """Verwaltet Research-Phasen"""
    
    def __init__(self):
        self.phases = self._initialize_default_phases()
        self.custom_phases = {}
    
    def _initialize_default_phases(self) -> Dict[str, ResearchPhase]:
        """Initialisiert Standard-Phasen"""
        return {
            "discovery": ResearchPhase(
                name="Discovery",
                type=PhaseType.DISCOVERY,
                description="Entdecke relevante Quellen für das Land/Region",
                max_duration=300,  # 5 Minuten
                required_agents=["tavily", "perplexity"],
                focus_areas=["source_discovery", "initial_scan", "quick_overview"],
                priority=1
            ),
            
            "deep_dive": ResearchPhase(
                name="Deep_Dive",
                type=PhaseType.DEEP_DIVE,
                description="Tauche tief in entdeckte Quellen ein",
                max_duration=600,  # 10 Minuten
                required_agents=["scraper", "brightdata", "firecrawl"],
                focus_areas=["document_extraction", "table_parsing", "deep_crawl"],
                priority=2
            ),
            
            "analysis": ResearchPhase(
                name="Analysis",
                type=PhaseType.ANALYSIS,
                description="Analysiere und extrahiere spezifische Daten",
                max_duration=480,  # 8 Minuten
                required_agents=["claude", "gpt4"],
                focus_areas=["complex_analysis", "data_correlation", "validation"],
                priority=3
            ),
            
            "verification": ResearchPhase(
                name="Verification",
                type=PhaseType.VERIFICATION,
                description="Verifiziere und konsolidiere Ergebnisse",
                max_duration=240,  # 4 Minuten
                required_agents=["tavily", "claude"],
                focus_areas=["fact_checking", "cross_reference"],
                priority=4
            ),
            
            # Spezialisierte Phasen
            "government_sources": ResearchPhase(
                name="Government_Sources",
                type=PhaseType.SPECIALIZED,
                description="Durchsuche Regierungsquellen",
                max_duration=360,
                required_agents=["scraper", "brightdata"],
                focus_areas=["government", "official_records", "permits"],
                priority=2,
                conditional=True,
                condition={"has_government_sources": True}
            ),
            
            "news_monitoring": ResearchPhase(
                name="News_Monitoring",
                type=PhaseType.SPECIALIZED,
                description="Aktuelle Nachrichten und Updates",
                max_duration=180,
                required_agents=["tavily", "perplexity"],
                focus_areas=["news", "recent_updates", "press_releases"],
                priority=3,
                conditional=True,
                condition={"include_news": True}
            ),
            
            "financial_research": ResearchPhase(
                name="Financial_Research",
                type=PhaseType.SPECIALIZED,
                description="Finanzielle Informationen",
                max_duration=300,
                required_agents=["claude", "gpt4"],
                focus_areas=["financial", "investment", "valuation"],
                priority=3,
                conditional=True,
                condition={"fields_contain": ["revenue", "cost", "investment"]}
            )
        }
    
    def get_phases_for_query(self, query: MineQuery) -> List[ResearchPhase]:
        """
        Wählt relevante Phasen für eine Query
        
        Dynamische Auswahl basierend auf:
        - Land/Region
        - Gefordertem Feldern
        - Verfügbaren Agenten
        """
        selected_phases = []
        
        # Standard-Phasen (immer)
        for phase_name in ["discovery", "deep_dive", "analysis", "verification"]:
            if phase_name in self.phases:
                selected_phases.append(self.phases[phase_name])
        
        # Bedingte Phasen prüfen
        for phase in self.phases.values():
            if phase.conditional and phase not in selected_phases:
                if self._check_condition(phase.condition, query):
                    selected_phases.append(phase)
        
        # Nach Priorität sortieren
        selected_phases.sort(key=lambda p: p.priority)
        
        return selected_phases
    
    def _check_condition(self, condition: Dict[str, Any], query: MineQuery) -> bool:
        """Prüft ob Bedingung für Phase erfüllt ist"""
        if not condition:
            return True
        
        # has_government_sources
        if "has_government_sources" in condition:
            # Heuristik: Bestimmte Länder haben gute Gov-Quellen
            gov_countries = ["Canada", "Australia", "USA", "UK", "South Africa"]
            if query.country in gov_countries:
                return True
        
        # include_news
        if "include_news" in condition:
            # Immer News für aktive Minen
            return True
        
        # fields_contain
        if "fields_contain" in condition:
            required_terms = condition["fields_contain"]
            for field in query.required_fields:
                if any(term in field.lower() for term in required_terms):
                    return True
        
        return False
    
    def add_custom_phase(self, phase: ResearchPhase):
        """Fügt benutzerdefinierte Phase hinzu"""
        self.custom_phases[phase.name] = phase
        self.phases[phase.name] = phase
    
    def get_phase_by_name(self, name: str) -> Optional[ResearchPhase]:
        """Holt Phase nach Name"""
        return self.phases.get(name)
    
    def get_phase_by_type(self, phase_type: PhaseType) -> List[ResearchPhase]:
        """Holt alle Phasen eines Typs"""
        return [
            phase for phase in self.phases.values()
            if phase.type == phase_type
        ]
    
    def adjust_phase_duration(self, phase_name: str, duration: int):
        """Passt Dauer einer Phase an"""
        if phase_name in self.phases:
            self.phases[phase_name].max_duration = duration
    
    def get_total_duration(self, phases: List[ResearchPhase]) -> int:
        """Berechnet Gesamtdauer aller Phasen"""
        return sum(phase.max_duration for phase in phases)