"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Koordinator für feldspezifische Agentenzuweisung
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

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

class AgentCoordinator:
    """Koordiniert Agenten basierend auf ihren Stärken für verschiedene Felder"""
    
    def __init__(self, config=None):
        self.agent_capabilities = self._initialize_capabilities()
        self.field_priorities = self._initialize_field_priorities()
        # ÄNDERUNG 17.06.2025: Nutze Konfigurationswerte für flexible Limits
        self.max_agents_per_field = config.max_agents_per_field if config else 10
        
    def _initialize_capabilities(self) -> Dict[str, Dict[str, AgentCapability]]:
        """Definiert Agenten-Stärken für verschiedene Felder"""
        
        capabilities = {
            "tavily": {
                "koordinaten": AgentCapability(
                    agent_name="tavily",
                    field="koordinaten",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["gov sites", "mining databases"],
                    notes="Exzellent für offizielle Koordinaten aus Regierungsquellen"
                ),
                "betreiber": AgentCapability(
                    agent_name="tavily",
                    field="betreiber",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["company websites", "gov registries"],
                    notes="Sehr gut für aktuelle Betreiberinformationen"
                ),
                "aktivitaetsstatus": AgentCapability(
                    agent_name="tavily",
                    field="aktivitaetsstatus",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["news", "company updates"],
                    notes="Gut für aktuelle Statusupdates"
                ),
                "sanierungskosten": AgentCapability(
                    agent_name="tavily",
                    field="sanierungskosten",
                    strength=AgentStrength.GOOD,
                    preferred_sources=["gov reports", "financial docs"],
                    notes="Kann offizielle Berichte finden"
                )
            },
            
            "claude": {
                "sanierungskosten": AgentCapability(
                    agent_name="claude",
                    field="sanierungskosten",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["technical reports", "complex documents"],
                    notes="Exzellent für Analyse komplexer Finanzberichte"
                ),
                "umweltauswirkungen": AgentCapability(
                    agent_name="claude",
                    field="umweltauswirkungen",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["environmental assessments", "technical docs"],
                    notes="Sehr gut für Analyse von Umweltberichten"
                ),
                "rohstofftyp": AgentCapability(
                    agent_name="claude",
                    field="rohstofftyp",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["technical reports", "geological surveys"],
                    notes="Gut für technische Rohstoffanalysen"
                ),
                "betreiber": AgentCapability(
                    agent_name="claude",
                    field="betreiber",
                    strength=AgentStrength.GOOD,
                    preferred_sources=["complex ownership structures"],
                    notes="Kann komplexe Eigentümerstrukturen analysieren"
                )
            },
            
            "gpt4": {
                "produktionsdaten": AgentCapability(
                    agent_name="gpt4",
                    field="produktionsdaten",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["annual reports", "production statistics"],
                    notes="Sehr gut für Extraktion von Produktionszahlen"
                ),
                "sanierungskosten": AgentCapability(
                    agent_name="gpt4",
                    field="sanierungskosten",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["financial reports", "regulatory filings"],
                    notes="Gut für Finanzanalysen"
                ),
                "mitarbeiter": AgentCapability(
                    agent_name="gpt4",
                    field="mitarbeiter",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["company reports", "news"],
                    notes="Gut für Mitarbeiterzahlen"
                ),
                "jahresproduktion": AgentCapability(
                    agent_name="gpt4",
                    field="jahresproduktion",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["production reports", "statistics"],
                    notes="Exzellent für Produktionsdaten"
                )
            },
            
            "perplexity": {
                "aktivitaetsstatus": AgentCapability(
                    agent_name="perplexity",
                    field="aktivitaetsstatus",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["recent news", "current updates"],
                    notes="Exzellent für aktuelle Statusinformationen"
                ),
                "betreiber": AgentCapability(
                    agent_name="perplexity",
                    field="betreiber",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["recent changes", "news"],
                    notes="Gut für aktuelle Betreiberwechsel"
                ),
                "umweltauswirkungen": AgentCapability(
                    agent_name="perplexity",
                    field="umweltauswirkungen",
                    strength=AgentStrength.GOOD,
                    preferred_sources=["recent incidents", "news"],
                    notes="Gut für aktuelle Umweltvorfälle"
                )
            },
            
            "scraper": {
                "koordinaten": AgentCapability(
                    agent_name="scraper",
                    field="koordinaten",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["structured tables", "databases"],
                    notes="Sehr gut für strukturierte Daten"
                ),
                "produktionsdaten": AgentCapability(
                    agent_name="scraper",
                    field="produktionsdaten",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["data tables", "statistics pages"],
                    notes="Gut für tabellarische Produktionsdaten"
                ),
                "flaeche": AgentCapability(
                    agent_name="scraper",
                    field="flaeche",
                    strength=AgentStrength.GOOD,
                    preferred_sources=["property listings", "gov databases"],
                    notes="Gut für strukturierte Flächendaten"
                )
            }
        }
        
        return capabilities
    
    def _initialize_field_priorities(self) -> Dict[str, int]:
        """Definiert Prioritäten für verschiedene Felder"""
        return {
            "koordinaten": 10,
            "betreiber": 9,
            "sanierungskosten": 9,
            "aktivitaetsstatus": 8,
            "rohstofftyp": 7,
            "umweltauswirkungen": 7,
            "produktionsdaten": 6,
            "jahresproduktion": 6,
            "startjahr": 5,
            "schließungsjahr": 5,
            "mitarbeiter": 4,
            "flaeche": 3,
            "minentyp": 3,
            "website": 2
        }
    
    def get_agent_assignment(self, fields: List[str], available_agents: List[str]) -> Dict[str, List[str]]:
        """
        Weist Agenten optimal zu Feldern zu basierend auf ihren Stärken
        
        Returns:
            Dict mit agent_name -> [assigned_fields]
        """
        assignments = {agent: [] for agent in available_agents}
        field_coverage = {field: [] for field in fields}
        
        # Sortiere Felder nach Priorität
        sorted_fields = sorted(fields, key=lambda f: self.field_priorities.get(f, 0), reverse=True)
        
        # Erste Runde: Weise Agenten mit EXCELLENT Stärke zu
        for field in sorted_fields:
            for agent in available_agents:
                if agent in self.agent_capabilities:
                    if field in self.agent_capabilities[agent]:
                        capability = self.agent_capabilities[agent][field]
                        if capability.strength == AgentStrength.EXCELLENT:
                            assignments[agent].append(field)
                            field_coverage[field].append(agent)
        
        # Zweite Runde: Weise Agenten mit VERY_GOOD Stärke zu
        # ÄNDERUNG 17.06.2025: Limit von 2 auf 10 Agenten pro Feld erhöht für bessere Abdeckung
        for field in sorted_fields:
            if len(field_coverage[field]) < self.max_agents_per_field:
                for agent in available_agents:
                    if agent in self.agent_capabilities:
                        if field in self.agent_capabilities[agent]:
                            capability = self.agent_capabilities[agent][field]
                            if capability.strength == AgentStrength.VERY_GOOD and field not in assignments[agent]:
                                assignments[agent].append(field)
                                field_coverage[field].append(agent)
                                if len(field_coverage[field]) >= self.max_agents_per_field:
                                    break
        
        # Dritte Runde: Stelle sicher, dass jedes Feld mindestens einen Agenten hat
        for field in sorted_fields:
            if not field_coverage[field]:
                # Weise dem Agenten mit der wenigsten Last zu
                agent_loads = [(agent, len(assignments[agent])) for agent in available_agents]
                agent_loads.sort(key=lambda x: x[1])
                
                for agent, _ in agent_loads:
                    if field not in assignments[agent]:
                        assignments[agent].append(field)
                        field_coverage[field].append(agent)
                        break
        
        # ÄNDERUNG 17.06.2025: Vierte Runde - Weise alle verfügbaren Agenten zu wenn weniger als 5 pro Feld
        # Dies stellt sicher, dass wir die volle Kapazität nutzen
        for field in sorted_fields:
            if len(field_coverage[field]) < 5:
                for agent in available_agents:
                    if field not in assignments[agent] and len(field_coverage[field]) < self.max_agents_per_field:
                        assignments[agent].append(field)
                        field_coverage[field].append(agent)
        
        # Entferne leere Zuweisungen
        assignments = {k: v for k, v in assignments.items() if v}
        
        return assignments
    
    def get_specialized_search_strategy(self, agent: str, field: str) -> Dict[str, any]:
        """Gibt spezialisierte Suchstrategie für Agent/Feld-Kombination zurück"""
        
        if agent not in self.agent_capabilities or field not in self.agent_capabilities[agent]:
            return {"strategy": "general", "focus": None}
        
        capability = self.agent_capabilities[agent][field]
        
        strategy = {
            "strategy": "specialized",
            "focus": capability.preferred_sources,
            "strength": capability.strength.value,
            "notes": capability.notes
        }
        
        # Feldspezifische Anpassungen
        if field == "sanierungskosten":
            strategy["keywords"] = ["closure plan", "financial assurance", "restoration bond", "rehabilitation cost"]
            strategy["document_types"] = ["pdf", "technical report"]
            
        elif field == "koordinaten":
            strategy["keywords"] = ["latitude", "longitude", "coordinates", "location", "GPS"]
            strategy["formats"] = ["decimal degrees", "DMS", "UTM"]
            
        elif field == "aktivitaetsstatus":
            strategy["time_filter"] = "recent"  # Letzte 2 Jahre
            strategy["keywords"] = ["status", "operating", "closed", "suspended", "active"]
            
        elif field == "produktionsdaten":
            strategy["keywords"] = ["production", "output", "tonnes", "ounces", "annual"]
            strategy["look_for_tables"] = True
            
        return strategy
    
    def get_agent_recommendations(self, field: str, available_agents: List[str]) -> List[Tuple[str, int]]:
        """
        Gibt Empfehlungen für die besten Agenten für ein Feld
        
        Returns:
            Liste von (agent_name, strength_score) sortiert nach Stärke
        """
        recommendations = []
        
        for agent in available_agents:
            if agent in self.agent_capabilities and field in self.agent_capabilities[agent]:
                capability = self.agent_capabilities[agent][field]
                recommendations.append((agent, capability.strength.value))
            else:
                # Default-Stärke für nicht spezialisierte Agenten
                recommendations.append((agent, AgentStrength.AVERAGE.value))
        
        # Sortiere nach Stärke (absteigend)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations