"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Agent-Fähigkeiten und Stärken-Definitionen
"""

from typing import Dict
from .models import AgentCapability, AgentStrength


class CapabilityManager:
    """Verwaltet Agent-Fähigkeiten für verschiedene Felder"""
    
    @staticmethod
    def get_all_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Gibt alle Agent-Fähigkeiten zurück"""
        return {
            **CapabilityManager._get_tavily_capabilities(),
            **CapabilityManager._get_claude_capabilities(),
            **CapabilityManager._get_gpt4_capabilities(),
            **CapabilityManager._get_perplexity_capabilities(),
            **CapabilityManager._get_scraper_capabilities(),
            **CapabilityManager._get_deep_web_capabilities(),
            **CapabilityManager._get_browser_capabilities(),
            **CapabilityManager._get_document_finder_capabilities(),
            **CapabilityManager._get_specialized_capabilities(),
        }
    
    @staticmethod
    def _get_tavily_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Tavily Agent Fähigkeiten"""
        return {
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
            }
        }
    
    @staticmethod
    def _get_claude_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Claude Agent Fähigkeiten"""
        return {
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
            }
        }
    
    @staticmethod
    def _get_gpt4_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """GPT-4 Agent Fähigkeiten"""
        return {
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
            }
        }
    
    @staticmethod
    def _get_perplexity_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Perplexity Agent Fähigkeiten"""
        return {
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
            }
        }
    
    @staticmethod
    def _get_scraper_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Scraper Agent Fähigkeiten"""
        return {
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
    
    @staticmethod
    def _get_deep_web_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """ÄNDERUNG 21.06.2025: Neue erweiterte Agenten"""
        return {
            "deep_web_crawler": {
                "betreiber": AgentCapability(
                    agent_name="deep_web_crawler",
                    field="betreiber",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["company websites", "deep web"],
                    notes="Tiefes Crawling von Unternehmensseiten"
                ),
                "produktionsdaten": AgentCapability(
                    agent_name="deep_web_crawler",
                    field="produktionsdaten",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["technical pages", "data tables"],
                    notes="Findet versteckte Produktionsdaten"
                ),
                "jahresproduktion": AgentCapability(
                    agent_name="deep_web_crawler",
                    field="jahresproduktion",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["annual reports", "production pages"],
                    notes="Crawlt tief für Produktionszahlen"
                )
            }
        }
    
    @staticmethod
    def _get_browser_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Browser Agent Fähigkeiten"""
        return {
            "browser": {
                "koordinaten": AgentCapability(
                    agent_name="browser",
                    field="koordinaten",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["government portals", "interactive maps"],
                    notes="Extrahiert aus JavaScript-basierten Karten"
                ),
                "aktivitaetsstatus": AgentCapability(
                    agent_name="browser",
                    field="aktivitaetsstatus",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["government databases", "regulatory sites"],
                    notes="Zugriff auf dynamische Regierungsportale"
                ),
                "betreiber": AgentCapability(
                    agent_name="browser",
                    field="betreiber",
                    strength=AgentStrength.GOOD,
                    preferred_sources=["regulatory filings", "sedar"],
                    notes="SEDAR und andere Portale"
                )
            }
        }
    
    @staticmethod
    def _get_document_finder_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Document Finder Agent Fähigkeiten"""
        return {
            "document_finder": {
                "sanierungskosten": AgentCapability(
                    agent_name="document_finder",
                    field="sanierungskosten",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["closure plans", "financial documents"],
                    notes="Spezialisiert auf Sanierungsdokumente"
                ),
                "umweltauswirkungen": AgentCapability(
                    agent_name="document_finder",
                    field="umweltauswirkungen",
                    strength=AgentStrength.EXCELLENT,
                    preferred_sources=["EIA reports", "environmental studies"],
                    notes="Findet Umweltverträglichkeitsprüfungen"
                ),
                "rohstofftyp": AgentCapability(
                    agent_name="document_finder",
                    field="rohstofftyp",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["technical reports", "NI 43-101"],
                    notes="Analysiert technische Berichte"
                )
            }
        }
    
    @staticmethod
    def _get_specialized_capabilities() -> Dict[str, Dict[str, AgentCapability]]:
        """Weitere spezialisierte Agenten"""
        return {
            "dynamic_keyword_generator": {
                "sanierungskosten": AgentCapability(
                    agent_name="dynamic_keyword_generator",
                    field="sanierungskosten",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["specialized searches", "keyword optimization"],
                    notes="Generiert spezialisierte Suchbegriffe"
                ),
                "umweltauswirkungen": AgentCapability(
                    agent_name="dynamic_keyword_generator",
                    field="umweltauswirkungen",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["environmental terms", "impact keywords"],
                    notes="Umweltspezifische Suchbegriffe"
                )
            },
            
            "dynamic_source_discovery": {
                "betreiber": AgentCapability(
                    agent_name="dynamic_source_discovery",
                    field="betreiber",
                    strength=AgentStrength.VERY_GOOD,
                    preferred_sources=["new sources", "undiscovered sites"],
                    notes="Entdeckt neue Informationsquellen"
                ),
                "produktionsdaten": AgentCapability(
                    agent_name="dynamic_source_discovery",
                    field="produktionsdaten",
                    strength=AgentStrength.GOOD,
                    preferred_sources=["industry sites", "trade publications"],
                    notes="Findet Branchenpublikationen"
                )
            }
        }
    
    @staticmethod
    def get_field_priorities() -> Dict[str, int]:
        """Definiert Prioritäten für verschiedene Felder"""
        return {
            # Kritische Felder (Priorität 1)
            "koordinaten": 1,
            "betreiber": 1,
            "aktivitaetsstatus": 1,
            "sanierungskosten": 1,
            
            # Wichtige Felder (Priorität 2)
            "rohstofftyp": 2,
            "flaeche": 2,
            "produktionsdaten": 2,
            "jahresproduktion": 2,
            
            # Sekundäre Felder (Priorität 3)
            "mitarbeiter": 3,
            "umweltauswirkungen": 3,
            "gruendungsjahr": 3,
            "schliessungsjahr": 3,
            
            # Ergänzende Felder (Priorität 4)
            "tiefe": 4,
            "reserven": 4,
            "website": 4
        }
