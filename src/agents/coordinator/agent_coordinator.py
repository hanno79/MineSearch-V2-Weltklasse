"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Koordinator für feldspezifische Agentenzuweisung
"""

from typing import Dict, List, Tuple, Optional, Set, Any
import logging
from collections import defaultdict

from .models import AgentStrength, AgentCapability, SearchPhase, PerformanceMetric
from .capabilities import CapabilityManager
from .strategies import SearchStrategyManager


class AgentCoordinator:
    """Koordiniert Agenten basierend auf ihren Stärken für verschiedene Felder"""
    
    def __init__(self, config=None):
        self.capability_manager = CapabilityManager()
        self.strategy_manager = SearchStrategyManager()
        self.agent_capabilities = self.capability_manager.get_all_capabilities()
        self.field_priorities = self.capability_manager.get_field_priorities()
        
        # ÄNDERUNG 17.06.2025: Nutze Konfigurationswerte für flexible Limits
        self.max_agents_per_field = config.max_agents_per_field if config else 10
        
        # ÄNDERUNG 21.06.2025: Erweiterte Koordination
        self.source_manager = None
        self.performance_history = defaultdict(lambda: PerformanceMetric("", ""))  # Track agent performance
        self.logger = logging.getLogger(__name__)
        
    def get_agent_assignment(self, fields: List[str], available_agents: List[str]) -> Dict[str, List[str]]:
        """Weist Agenten basierend auf ihren Stärken zu Feldern zu"""
        
        assignments = {}
        used_agents = set()
        
        # Sortiere Felder nach Priorität
        sorted_fields = sorted(
            fields,
            key=lambda f: self.field_priorities.get(f, 99)
        )
        
        for field in sorted_fields:
            # Hole Empfehlungen für dieses Feld
            recommendations = self.get_agent_recommendations(field, available_agents)
            
            # Wähle beste verfügbare Agenten
            field_agents = []
            for agent, strength in recommendations:
                if agent in available_agents and len(field_agents) < self.max_agents_per_field:
                    # ÄNDERUNG 17.06.2025: Verhindere Mehrfachzuweisung in erster Phase
                    if agent not in used_agents or strength >= AgentStrength.VERY_GOOD.value:
                        field_agents.append(agent)
                        # Markiere nur bei niedrigeren Prioritäten als verwendet
                        if self.field_priorities.get(field, 99) > 2:
                            used_agents.add(agent)
                            
            assignments[field] = field_agents
            
        # ÄNDERUNG 17.06.2025: Zweiter Durchgang für Felder ohne Agenten
        for field in sorted_fields:
            if not assignments[field]:
                # Versuche jeden verfügbaren Agenten
                fallback_agents = []
                for agent in available_agents:
                    if agent not in assignments[field] and len(fallback_agents) < 2:
                        fallback_agents.append(agent)
                        
                if fallback_agents:
                    assignments[field] = fallback_agents
                    self.logger.info(f"Fallback-Zuweisung für {field}: {fallback_agents}")
                    
        return assignments
    
    def get_specialized_search_strategy(self, agent: str, field: str) -> Dict[str, Any]:
        """Gibt spezielle Suchstrategie für einen Agenten und ein Feld zurück"""
        return self.strategy_manager.get_specialized_search_strategy(agent, field)
    
    def get_agent_recommendations(self, field: str, available_agents: List[str]) -> List[Tuple[str, int]]:
        """Gibt sortierte Liste von Agenten mit ihrer Stärke für ein Feld zurück"""
        
        recommendations = []
        
        for agent_name, capabilities in self.agent_capabilities.items():
            if agent_name in available_agents and field in capabilities:
                capability = capabilities[field]
                # Berücksichtige Performance-Historie
                perf_key = f"{agent_name}_{field}"
                if perf_key in self.performance_history:
                    perf = self.performance_history[perf_key]
                    # Adjustiere Stärke basierend auf Erfolgsrate
                    adjusted_strength = capability.strength.value * perf.success_rate
                    recommendations.append((agent_name, int(adjusted_strength)))
                else:
                    recommendations.append((agent_name, capability.strength.value))
        
        # Sortiere nach Stärke (absteigend)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations
    
    def set_source_manager(self, source_manager):
        """ÄNDERUNG 21.06.2025: Setzt Source Manager für erweiterte Koordination"""
        self.source_manager = source_manager
    
    def coordinate_search(self, query: Any, available_agents: List[str], 
                         required_fields: List[str]) -> Dict[str, Any]:
        """
        ÄNDERUNG 21.06.2025: Erweiterte Koordination mit Source Manager
        
        Koordiniert eine komplette Suche über mehrere Agenten und Felder.
        """
        coordination_plan = {
            "assignments": {},
            "phases": [],
            "source_assignments": {},
            "strategies": {}
        }
        
        # Basis-Zuweisung
        assignments = self.get_agent_assignment(required_fields, available_agents)
        coordination_plan["assignments"] = assignments
        
        # Source-basierte Zuweisung wenn Source Manager verfügbar
        if self.source_manager:
            sources = self.source_manager.get_prioritized_sources(query)
            source_assignments = self._assign_agents_to_sources(
                sources, available_agents, required_fields
            )
            coordination_plan["source_assignments"] = source_assignments
        
        # Erstelle Ausführungsphasen
        phases = self._create_execution_phases(assignments, required_fields)
        coordination_plan["phases"] = phases
        
        # Füge Strategien hinzu
        for field, agents in assignments.items():
            coordination_plan["strategies"][field] = {
                agent: self.get_specialized_search_strategy(agent, field)
                for agent in agents
            }
        
        return coordination_plan
    
    def _assign_agents_to_sources(self, sources: List[Any], agents: List[str], 
                                 fields: List[str]) -> Dict[str, List[str]]:
        """Weist Agenten zu spezifischen Quellen zu"""
        source_assignments = defaultdict(list)
        
        for source in sources:
            source_type = source.get('type', 'general')
            
            # Finde beste Agenten für diese Quellenart
            if source_type == 'government':
                preferred_agents = ['tavily', 'browser', 'scraper']
            elif source_type == 'technical':
                preferred_agents = ['claude', 'gpt4', 'document_finder']
            elif source_type == 'news':
                preferred_agents = ['perplexity', 'tavily']
            else:
                preferred_agents = agents
            
            # Wähle verfügbare Agenten
            for agent in preferred_agents:
                if agent in agents:
                    source_assignments[source['name']].append(agent)
                    if len(source_assignments[source['name']]) >= 2:
                        break
        
        return dict(source_assignments)
    
    def _prioritize_fields(self, fields: List[str]) -> List[str]:
        """Priorisiert Felder basierend auf definierten Prioritäten"""
        return sorted(fields, key=lambda f: self.field_priorities.get(f, 99))
    
    def _create_execution_phases(self, assignments: Dict[str, List[str]], 
                               fields: List[str]) -> List[SearchPhase]:
        """Erstellt Ausführungsphasen für die Suche"""
        phases = []
        
        # Gruppiere Felder nach Priorität
        priority_groups = defaultdict(list)
        for field in fields:
            priority = self.field_priorities.get(field, 99)
            priority_groups[priority].append(field)
        
        # Erstelle Phasen
        phase_number = 1
        for priority in sorted(priority_groups.keys()):
            phase_fields = priority_groups[priority]
            phase_agents = set()
            
            for field in phase_fields:
                phase_agents.update(assignments.get(field, []))
            
            if phase_agents:
                phases.append(SearchPhase(
                    phase_number=phase_number,
                    agents=list(phase_agents),
                    fields=phase_fields,
                    priority='high' if priority == 1 else 'medium' if priority == 2 else 'low'
                ))
                phase_number += 1
        
        return phases
    
    def update_performance(self, agent: str, field: str, success: bool):
        """
        ÄNDERUNG 21.06.2025: Aktualisiert Performance-Metriken
        
        Args:
            agent: Agent-Name
            field: Feld-Name
            success: Ob die Suche erfolgreich war
        """
        perf_key = f"{agent}_{field}"
        
        if perf_key not in self.performance_history:
            self.performance_history[perf_key] = PerformanceMetric(agent, field)
        
        metric = self.performance_history[perf_key]
        if success:
            metric.success_count += 1
        else:
            metric.failure_count += 1
    
    def get_adaptive_recommendations(self, field: str, available_agents: List[str]) -> List[Tuple[str, float]]:
        """
        Gibt adaptive Empfehlungen basierend auf Performance-Historie
        
        Returns:
            Liste von (agent_name, adjusted_score) Tupeln
        """
        recommendations = []
        
        for agent in available_agents:
            base_score = 0.5  # Default wenn keine Capability definiert
            
            # Hole Basis-Stärke
            if agent in self.agent_capabilities and field in self.agent_capabilities[agent]:
                capability = self.agent_capabilities[agent][field]
                base_score = capability.strength.value / 5.0  # Normalisiere auf 0-1
            
            # Adjustiere basierend auf Historie
            perf_key = f"{agent}_{field}"
            if perf_key in self.performance_history:
                metric = self.performance_history[perf_key]
                # Gewichtete Kombination aus Basis-Score und Erfolgsrate
                adjusted_score = 0.3 * base_score + 0.7 * metric.success_rate
            else:
                adjusted_score = base_score
            
            recommendations.append((agent, adjusted_score))
        
        # Sortiere nach Score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations
