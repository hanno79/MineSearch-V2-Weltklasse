"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Gestaffelte Suchstrategie für Mining-Daten
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class SearchStage(Enum):
    """Verschiedene Suchphasen"""
    BASIC = 1  # Basis-Informationen
    PRODUCTION = 2  # Produktionsdaten
    FINANCIAL = 3  # Finanzdaten
    ENVIRONMENTAL = 4  # Umweltdaten
    COMPLETE = 5  # Alle Daten

@dataclass
class StageDefinition:
    """Definition einer Suchphase"""
    name: str
    fields: List[str]
    priority: int
    max_agents: int  # Maximale Anzahl Agenten für diese Phase
    timeout: int  # Timeout in Sekunden

class StagedSearchStrategy:
    """Definiert gestaffelte Suchstrategie für Mining-Daten"""
    
    def __init__(self, config=None):
        # ÄNDERUNG 17.06.2025: Nutze Konfigurationswerte für flexible Limits
        self.max_agents_per_stage = config.max_agents_per_stage if config else 50
        self.stages = self._initialize_stages()
        
    def _initialize_stages(self) -> Dict[SearchStage, StageDefinition]:
        """Initialisiert die verschiedenen Suchphasen"""
        
        return {
            SearchStage.BASIC: StageDefinition(
                name="Basis-Informationen",
                fields=[
                    "betreiber", "operator", "owner", "company",
                    "koordinaten", "coordinates", "location", "GPS",
                    "rohstofftyp", "commodity", "mineral", "resource",
                    "aktivitaetsstatus", "status", "operational_status",
                    "mine_type"
                ],
                priority=1,
                max_agents=self.max_agents_per_stage,
                timeout=300  # 5 Minuten
            ),
            
            SearchStage.PRODUCTION: StageDefinition(
                name="Produktionsdaten",
                fields=[
                    "production_start", "production_end", "mine_life", "closure_date",
                    "annual_production", "capacity", "throughput",
                    "produktionsdaten", "jahresproduktion",
                    "startjahr", "schließungsjahr",
                    "employees", "mitarbeiter", "flaeche"
                ],
                priority=2,
                max_agents=self.max_agents_per_stage,
                timeout=240  # 4 Minuten
            ),
            
            SearchStage.FINANCIAL: StageDefinition(
                name="Finanzdaten",
                fields=[
                    "sanierungskosten", "remediation_costs", "closure_costs",
                    "rehabilitation", "environmental_liability", "restoration_costs",
                    "environmental_bond", "financial_assurance",
                    "umweltkosten", "marktwert", "investitionen"
                ],
                priority=3,
                max_agents=self.max_agents_per_stage,  # Erhöht für maximale Parallelität bei wichtigen Finanzdaten
                timeout=240  # 4 Minuten
            ),
            
            SearchStage.ENVIRONMENTAL: StageDefinition(
                name="Umweltdaten",
                fields=[
                    "umweltauswirkungen",
                    "kontamination",
                    "wassermanagement",
                    "restaurationsplan"
                ],
                priority=4,
                max_agents=self.max_agents_per_stage,  # Erhöht von 3 auf 50 für bessere Umweltdaten-Abdeckung
                timeout=180  # 3 Minuten
            ),
            
            SearchStage.COMPLETE: StageDefinition(
                name="Vollständige Suche",
                fields=[],  # Alle Felder
                priority=5,
                max_agents=self.max_agents_per_stage,  # Erhöht von 5 auf 50 für vollständige Suche
                timeout=600  # 10 Minuten
            )
        }
    
    def get_stages_for_fields(self, required_fields: List[str]) -> List[SearchStage]:
        """
        Bestimmt welche Suchphasen für die geforderten Felder benötigt werden
        
        Returns:
            Liste der benötigten Suchphasen, sortiert nach Priorität
        """
        needed_stages = []
        
        for stage, definition in self.stages.items():
            if stage == SearchStage.COMPLETE:
                continue  # Complete nur wenn explizit angefordert
                
            # Prüfe ob Felder aus dieser Phase benötigt werden
            if any(field in required_fields for field in definition.fields):
                needed_stages.append(stage)
        
        # Sortiere nach Priorität
        needed_stages.sort(key=lambda s: self.stages[s].priority)
        
        return needed_stages
    
    def get_fields_for_stage(self, stage: SearchStage, required_fields: List[str]) -> List[str]:
        """
        Gibt die zu suchenden Felder für eine bestimmte Phase zurück
        
        Returns:
            Liste der Felder, die in dieser Phase gesucht werden sollen
        """
        if stage == SearchStage.COMPLETE:
            return required_fields
            
        stage_fields = self.stages[stage].fields
        
        # Nur Felder zurückgeben, die auch angefordert wurden
        return [f for f in required_fields if f in stage_fields]
    
    def get_best_agents_for_stage(self, stage: SearchStage, available_agents: List[str]) -> List[str]:
        """
        Wählt die besten Agenten für eine bestimmte Suchphase
        
        Returns:
            Liste der empfohlenen Agenten für diese Phase
        """
        # ÄNDERUNG 17.06.2025: Nutze ALLE verfügbaren Agenten, die der Nutzer ausgewählt hat
        # Keine künstliche Begrenzung - der Nutzer hat sie aus gutem Grund ausgewählt
        # Max_agents wurde auf 50 erhöht für maximale Parallelität
        
        # Optional: Priorisierung für bessere Ergebnisse
        stage_agent_priorities = {
            SearchStage.BASIC: [
                "tavily", "perplexity", "exa", "firecrawl", "brightdata",
                "scraper", "claude", "gpt4", "deepseek", "openrouter"
            ],
            SearchStage.PRODUCTION: [
                "gpt4", "claude", "deepseek", "scraper", 
                "firecrawl", "brightdata", "tavily", "perplexity", "openrouter"
            ],
            SearchStage.FINANCIAL: [
                "claude", "gpt4", "deepseek", "tavily", 
                "firecrawl", "brightdata", "perplexity", "openrouter"
            ],
            SearchStage.ENVIRONMENTAL: [
                "claude", "gpt4", "deepseek", "perplexity", 
                "tavily", "firecrawl", "brightdata", "openrouter"
            ]
        }
        
        priorities = stage_agent_priorities.get(stage, [])
        max_agents = self.stages[stage].max_agents
        
        # Sortiere verfügbare Agenten nach Priorität
        selected = []
        
        # Erst priorisierte Agenten (inkl. OpenRouter Modelle)
        for agent in priorities:
            # Füge alle Agenten hinzu, die mit dem Prioritätsnamen beginnen
            for available in available_agents:
                if available.startswith(agent) and available not in selected:
                    selected.append(available)
        
        # Dann alle anderen verfügbaren Agenten
        for agent in available_agents:
            if agent not in selected:
                selected.append(agent)
        
        # Nutze alle verfügbaren Agenten (respektiere max_agents)
        return selected[:max_agents]
    
    def should_continue_to_next_stage(self, current_stage: SearchStage, 
                                     results_found: Dict[str, int],
                                     required_fields: List[str]) -> bool:
        """
        Entscheidet ob zur nächsten Phase übergegangen werden soll
        
        Args:
            current_stage: Aktuelle Suchphase
            results_found: Dict mit field -> Anzahl gefundener Ergebnisse
            required_fields: Liste der benötigten Felder
            
        Returns:
            True wenn zur nächsten Phase übergegangen werden soll
        """
        stage_fields = self.get_fields_for_stage(current_stage, required_fields)
        
        # Prüfe ob mindestens 50% der Felder dieser Phase gefunden wurden
        fields_found = sum(1 for f in stage_fields if results_found.get(f, 0) > 0)
        completion_rate = fields_found / len(stage_fields) if stage_fields else 0
        
        # Fortfahren wenn mindestens 50% gefunden oder kritische Felder fehlen
        return completion_rate >= 0.5 or current_stage == SearchStage.BASIC
    
    def get_stage_info(self, stage: SearchStage) -> StageDefinition:
        """Gibt Informationen zu einer Suchphase zurück"""
        return self.stages[stage]