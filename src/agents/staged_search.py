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
    SOURCE_DISCOVERY = 0  # Quellensuche
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
            SearchStage.SOURCE_DISCOVERY: StageDefinition(
                name="Quellensuche",
                fields=[
                    "sources", "websites", "databases", "government_sites",
                    "company_websites", "news_sources", "technical_reports"
                ],
                priority=0,  # Höchste Priorität - wird zuerst ausgeführt
                max_agents=self.max_agents_per_stage,
                timeout=90  # ÄNDERUNG 21.06.2025: Reduziert von 300 auf 90 Sekunden
            ),
            
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
                timeout=90  # ÄNDERUNG 21.06.2025: Reduziert von 300 auf 90 Sekunden
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
                timeout=60  # ÄNDERUNG 21.06.2025: Reduziert von 240 auf 60 Sekunden
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
                timeout=60  # ÄNDERUNG 21.06.2025: Reduziert von 240 auf 60 Sekunden
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
                timeout=60  # ÄNDERUNG 21.06.2025: Reduziert von 180 auf 60 Sekunden
            ),
            
            SearchStage.COMPLETE: StageDefinition(
                name="Vollständige Suche",
                fields=[],  # Alle Felder
                priority=5,
                max_agents=self.max_agents_per_stage,  # Erhöht von 5 auf 50 für vollständige Suche
                timeout=120  # ÄNDERUNG 21.06.2025: Reduziert von 600 auf 120 Sekunden
            )
        }
    
    def get_stages_for_fields(self, required_fields: List[str]) -> List[SearchStage]:
        """
        Bestimmt welche Suchphasen für die geforderten Felder benötigt werden
        
        Returns:
            Liste der benötigten Suchphasen, sortiert nach Priorität
        """
        needed_stages = []
        
        # ÄNDERUNG 18.06.2025: Source Discovery wird NICHT automatisch hinzugefügt
        # Das passiert jetzt im Orchestrator
        
        for stage, definition in self.stages.items():
            # ÄNDERUNG 18.06.2025: Verwende try/except statt hasattr
            try:
                if stage.value == 5:  # COMPLETE
                    continue  # Complete nur wenn explizit angefordert
            except AttributeError:
                # Falls kein value Attribut, überspringen
                continue
                
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
        # ÄNDERUNG 19.06.2025: Robusterer Zugriff auf stages Dictionary
        # Verwende stage direkt oder suche nach value
        stage_def = None
        
        # Versuche direkten Zugriff
        if stage in self.stages:
            stage_def = self.stages[stage]
        else:
            # Falls nicht gefunden, suche nach value
            try:
                stage_value = stage.value
                for s, definition in self.stages.items():
                    if hasattr(s, 'value') and s.value == stage_value:
                        stage_def = definition
                        break
            except AttributeError:
                pass
        
        if not stage_def:
            return []
            
        # Spezialbehandlung für COMPLETE
        try:
            if stage.value == 5:  # COMPLETE
                return required_fields
        except AttributeError:
            pass
            
        stage_fields = stage_def.fields
        
        # Nur Felder zurückgeben, die auch angefordert wurden
        return [f for f in required_fields if f in stage_fields]
    
    def get_best_agents_for_stage(self, stage: SearchStage, available_agents: List[str]) -> List[str]:
        """
        Wählt die besten Agenten für eine bestimmte Suchphase
        
        Returns:
            Liste der empfohlenen Agenten für diese Phase
        """
        # ÄNDERUNG 21.06.2025: Debug-Logging für Agent-Auswahl
        from src.core.logger import get_logger
        logger = get_logger("staged_search")
        logger.info(f"DEBUG: get_best_agents_for_stage - Stage: {stage}, Available: {available_agents}")
        
        # ÄNDERUNG 17.06.2025: Nutze ALLE verfügbaren Agenten, die der Nutzer ausgewählt hat
        # Keine künstliche Begrenzung - der Nutzer hat sie aus gutem Grund ausgewählt
        # Max_agents wurde auf 50 erhöht für maximale Parallelität
        
        # Für SOURCE_DISCOVERY: Nutze ALLE verfügbaren Agenten
        try:
            if stage.value == 0:  # SOURCE_DISCOVERY
                logger.info(f"DEBUG: SOURCE_DISCOVERY - returning all {len(available_agents)} agents")
                return available_agents[:self.stages[stage].max_agents]
        except:
            pass
        
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
        
        # ÄNDERUNG 21.06.2025: Aggressivere Beendigung für bessere Performance
        # Prüfe ob genug Felder dieser Phase gefunden wurden
        fields_found = sum(1 for f in stage_fields if results_found.get(f, 0) > 0)
        completion_rate = fields_found / len(stage_fields) if stage_fields else 0
        
        # Prüfe Gesamtabdeckung
        total_fields_needed = len(required_fields)
        total_fields_found = sum(1 for f in required_fields if results_found.get(f, 0) > 0)
        total_completion_rate = total_fields_found / total_fields_needed if total_fields_needed else 0
        
        # Beende früh wenn:
        # 1. 80% aller Felder gefunden wurden (gesamt)
        # 2. 70% der aktuellen Phase gefunden wurden
        # 3. Wir in BASIC sind und schon 60% aller Felder haben
        if total_completion_rate >= 0.8:
            return False  # Genug Daten, stoppe Suche
            
        if completion_rate >= 0.7:
            return True  # Phase gut abgedeckt, weiter zur nächsten
            
        if current_stage == SearchStage.BASIC and total_completion_rate >= 0.6:
            return False  # Basis-Daten reichen aus
            
        # Standard: Fortfahren wenn mindestens 50% gefunden oder kritische Phase
        return completion_rate >= 0.5 or current_stage == SearchStage.BASIC
    
    def get_stage_info(self, stage: SearchStage) -> StageDefinition:
        """Gibt Informationen zu einer Suchphase zurück"""
        # ÄNDERUNG 19.06.2025: Robusterer Zugriff auf stages Dictionary
        if stage in self.stages:
            return self.stages[stage]
        
        # Falls nicht gefunden, suche nach value
        try:
            stage_value = stage.value
            for s, definition in self.stages.items():
                if hasattr(s, 'value') and s.value == stage_value:
                    return definition
        except AttributeError:
            pass
            
        # ÄNDERUNG 19.06.2025: Fallback auf BASIC Stage statt None
        # Dies verhindert Type Error und gibt eine sinnvolle Standard-Definition zurück
        return self.stages.get(SearchStage.BASIC, StageDefinition(
            name="Basis-Informationen",
            fields=[],
            priority=1,
            max_agents=self.max_agents_per_stage,
            timeout=300
        ))
    
    async def execute_staged_search(self, query, agents, discovered_sources=None, cancellation_token=None):
        """
        Führt die gestaffelte Suche aus
        
        Args:
            query: MineQuery Objekt
            agents: Liste verfügbarer Agenten
            discovered_sources: Optional bereits entdeckte Quellen
            cancellation_token: Optional für Abbruch
            
        Returns:
            Liste von SearchResults
        """
        from src.core.logger import get_logger
        logger = get_logger("staged_search")
        
        all_results = []
        results_by_field = {}
        
        # Bestimme benötigte Stages basierend auf required_fields
        needed_stages = self.get_stages_for_fields(query.required_fields)
        
        logger.info(f"Führe Staged Search aus mit {len(needed_stages)} Phasen")
        
        for stage in needed_stages:
            if cancellation_token and cancellation_token.is_cancelled():
                logger.info("Suche wurde abgebrochen")
                break
                
            stage_info = self.get_stage_info(stage)
            logger.info(f"🔍 PHASE {stage.value}: {stage_info.name}")
            
            # Wähle Agenten für diese Phase
            stage_agents = self.get_best_agents_for_stage(stage, [a.name for a in agents])
            selected_agents = [a for a in agents if a.name in stage_agents]
            
            if not selected_agents:
                logger.warning(f"Keine Agenten für Phase {stage_info.name} verfügbar")
                continue
            
            # Führe Suche mit ausgewählten Agenten aus
            import asyncio
            search_tasks = []
            
            for agent in selected_agents:
                if hasattr(agent, 'search_mine'):
                    search_tasks.append(agent.search_mine(query))
            
            if search_tasks:
                try:
                    # Führe alle Suchen parallel aus mit Timeout
                    stage_results = await asyncio.wait_for(
                        asyncio.gather(*search_tasks, return_exceptions=True),
                        timeout=stage_info.timeout
                    )
                    
                    # Verarbeite Ergebnisse
                    for result in stage_results:
                        if isinstance(result, list):
                            all_results.extend(result)
                            # Tracke gefundene Felder
                            for r in result:
                                if hasattr(r, 'data') and r.data:
                                    for field in r.data.keys():
                                        results_by_field[field] = results_by_field.get(field, 0) + 1
                        elif isinstance(result, Exception):
                            logger.error(f"Fehler bei Agent: {result}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout in Phase {stage_info.name}")
            
            # Prüfe ob wir zur nächsten Phase gehen sollen
            if not self.should_continue_to_next_stage(stage, results_by_field, query.required_fields):
                logger.info(f"Genügend Daten gefunden, beende Suche nach Phase {stage_info.name}")
                break
        
        logger.info(f"Staged Search abgeschlossen mit {len(all_results)} Ergebnissen")
        return all_results