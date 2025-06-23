"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Analyse und Auswahl von Such-Strategien
"""

from typing import List, Dict, Optional, Set, Tuple, Any
import re
from dataclasses import dataclass

from .search_strategies_core import (
    SearchStrategy, SearchContext, StrategyAnalysis,
    PREDEFINED_STRATEGIES, FIELD_CATEGORIES, AGENT_CAPABILITIES,
    SearchScope, SearchDepth
)


class StrategyAnalyzer:
    """Analysiert Kontexte und wählt optimale Strategien"""
    
    def __init__(self):
        self.strategies = PREDEFINED_STRATEGIES.copy()
        self.custom_strategies = {}
        self.selection_history = []
    
    def analyze_context(self, context: SearchContext) -> StrategyAnalysis:
        """
        Analysiert den Such-Kontext
        
        Returns:
            StrategyAnalysis mit Bewertungen
        """
        # Komplexität bewerten
        complexity_score = self._calculate_complexity(
            context.mine_name,
            context.required_fields
        )
        
        # Geografischen Scope bestimmen
        geographic_scope = self._determine_geographic_scope(
            context.country,
            context.region
        )
        
        # Field-Komplexität bewerten
        field_complexity = self._calculate_field_complexity(
            context.required_fields
        )
        
        # Agent-Verfügbarkeit bewerten
        agent_availability = self._calculate_agent_availability(
            context.available_agents
        )
        
        # Zeitdruck bewerten
        time_pressure = self._calculate_time_pressure(
            context.time_constraint,
            complexity_score
        )
        
        return StrategyAnalysis(
            complexity_score=complexity_score,
            geographic_scope=geographic_scope,
            field_complexity=field_complexity,
            agent_availability=agent_availability,
            time_pressure=time_pressure
        )
    
    def select_strategy(self, 
                       context: SearchContext,
                       analysis: Optional[StrategyAnalysis] = None) -> SearchStrategy:
        """
        Wählt optimale Strategie basierend auf Kontext
        
        Vollständig dynamisch ohne hardcodierte Annahmen
        """
        # Analyse durchführen falls nicht vorhanden
        if not analysis:
            analysis = self.analyze_context(context)
        
        # Score für jede Strategie berechnen
        strategy_scores = {}
        
        for name, strategy in self.strategies.items():
            score = self._score_strategy(strategy, context, analysis)
            strategy_scores[name] = score
        
        # Beste Strategie wählen
        best_strategy_name = max(strategy_scores, key=strategy_scores.get)
        best_strategy = self.strategies[best_strategy_name]
        
        # Anpassungen basierend auf Kontext
        adjusted_strategy = self._adjust_strategy(
            best_strategy,
            context,
            analysis
        )
        
        # In History speichern
        self.selection_history.append({
            "context": context,
            "analysis": analysis,
            "selected": adjusted_strategy.name,
            "scores": strategy_scores
        })
        
        return adjusted_strategy
    
    def _calculate_complexity(self, mine_name: str, fields: List[str]) -> float:
        """Berechnet Gesamt-Komplexität der Anfrage"""
        score = 0.5  # Basis
        
        # Name-Komplexität
        if len(mine_name.split()) > 3:
            score += 0.1
        if any(char in mine_name for char in ['&', '/', '-']):
            score += 0.1
        if re.search(r'\d', mine_name):  # Zahlen im Namen
            score += 0.05
        
        # Field-Anzahl
        score += min(0.3, len(fields) * 0.05)
        
        return min(1.0, score)
    
    def _determine_geographic_scope(self, country: str, region: str) -> str:
        """Bestimmt geografischen Scope"""
        # Große Länder mit regionaler Unterteilung
        large_countries = ['Canada', 'Australia', 'USA', 'Russia', 'China', 'Brazil']
        
        if country in large_countries and region:
            return "regional"
        elif country:
            return "national"
        else:
            return "global"
    
    def _calculate_field_complexity(self, fields: List[str]) -> float:
        """Berechnet Komplexität der angeforderten Felder"""
        if not fields:
            return 0.1
        
        complexity_scores = {
            "basic": 0.2,
            "technical": 0.5,
            "financial": 0.7,
            "regulatory": 0.8,
            "operational": 0.6,
            "geological": 0.9
        }
        
        total_score = 0
        categories_found = 0
        
        for field in fields:
            for category, category_fields in FIELD_CATEGORIES.items():
                if any(cf in field.lower() for cf in category_fields):
                    total_score += complexity_scores[category]
                    categories_found += 1
                    break
        
        if categories_found == 0:
            return 0.5  # Unbekannte Felder = mittlere Komplexität
        
        return min(1.0, total_score / categories_found)
    
    def _calculate_agent_availability(self, available_agents: List[str]) -> float:
        """Bewertet verfügbare Agenten"""
        if not available_agents:
            return 0.0
        
        # Premium-Agenten
        premium_agents = ['brightdata', 'firecrawl', 'gpt4', 'claude']
        premium_count = sum(1 for a in available_agents if a in premium_agents)
        
        # Basis-Score nach Anzahl
        base_score = min(1.0, len(available_agents) / 10)
        
        # Premium-Bonus
        premium_bonus = min(0.3, premium_count * 0.1)
        
        return min(1.0, base_score + premium_bonus)
    
    def _calculate_time_pressure(self, 
                               time_constraint: Optional[int],
                               complexity: float) -> float:
        """Berechnet Zeitdruck"""
        if not time_constraint:
            return 0.1  # Kein Zeitdruck
        
        # Erwartete Zeit basierend auf Komplexität
        expected_time = 300 + (complexity * 600)  # 5-15 Minuten
        
        if time_constraint < expected_time * 0.5:
            return 0.9  # Hoher Zeitdruck
        elif time_constraint < expected_time:
            return 0.5  # Mittlerer Zeitdruck
        else:
            return 0.2  # Niedriger Zeitdruck
    
    def _score_strategy(self,
                       strategy: SearchStrategy,
                       context: SearchContext,
                       analysis: StrategyAnalysis) -> float:
        """Bewertet eine Strategie für den Kontext"""
        score = 0.0
        
        # Zeit-Score
        if context.time_constraint:
            if strategy.time_budget <= context.time_constraint:
                score += 0.3
            else:
                score -= 0.5
        
        # Komplexitäts-Match
        if strategy.depth == SearchDepth.SHALLOW and analysis.complexity_score < 0.3:
            score += 0.2
        elif strategy.depth == SearchDepth.STANDARD and 0.3 <= analysis.complexity_score < 0.7:
            score += 0.3
        elif strategy.depth == SearchDepth.DEEP and analysis.complexity_score >= 0.7:
            score += 0.4
        
        # Agent-Match
        available_set = set(context.available_agents)
        preferred_set = set(strategy.agent_preferences)
        
        if "all" in preferred_set:
            score += 0.2
        else:
            overlap = len(available_set & preferred_set)
            score += min(0.3, overlap * 0.1)
        
        # Field-Komplexitäts-Match
        if analysis.field_complexity > 0.7:
            if strategy.depth in [SearchDepth.DEEP, SearchDepth.EXHAUSTIVE]:
                score += 0.2
        
        # Iterations-Bonus (lerne aus vorherigen Versuchen)
        if context.search_iteration > 1:
            if strategy.depth.value > SearchDepth.STANDARD.value:
                score += 0.1 * context.search_iteration
        
        return score
    
    def _adjust_strategy(self,
                        strategy: SearchStrategy,
                        context: SearchContext,
                        analysis: StrategyAnalysis) -> SearchStrategy:
        """Passt Strategie an spezifischen Kontext an"""
        # Kopie erstellen
        adjusted = SearchStrategy(
            name=f"{strategy.name} (adjusted)",
            scope=strategy.scope,
            depth=strategy.depth,
            time_budget=strategy.time_budget,
            agent_preferences=strategy.agent_preferences.copy(),
            keyword_strategy=strategy.keyword_strategy,
            parallel_searches=strategy.parallel_searches,
            retry_strategy=strategy.retry_strategy.copy()
        )
        
        # Zeit-Anpassung
        if context.time_constraint:
            adjusted.time_budget = min(
                strategy.time_budget,
                int(context.time_constraint * 0.8)
            )
        
        # Parallele Suchen anpassen
        if analysis.agent_availability < 0.5:
            adjusted.parallel_searches = max(3, strategy.parallel_searches // 2)
        
        # Retry-Anpassung bei Zeitdruck
        if analysis.time_pressure > 0.7:
            adjusted.retry_strategy["max_retries"] = 1
            adjusted.retry_strategy["backoff"] = 1
        
        return adjusted
    
    def add_custom_strategy(self, name: str, strategy: SearchStrategy):
        """Fügt benutzerdefinierte Strategie hinzu"""
        self.custom_strategies[name] = strategy
        self.strategies[name] = strategy
    
    def get_strategy_recommendation(self, 
                                   context: SearchContext) -> Dict[str, Any]:
        """Gibt detaillierte Strategie-Empfehlung"""
        analysis = self.analyze_context(context)
        selected = self.select_strategy(context, analysis)
        
        # Alternative Strategien
        all_scores = {}
        for name, strategy in self.strategies.items():
            all_scores[name] = self._score_strategy(strategy, context, analysis)
        
        sorted_strategies = sorted(
            all_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "selected_strategy": selected,
            "analysis": analysis,
            "alternatives": [
                {"name": name, "score": score}
                for name, score in sorted_strategies[:3]
            ],
            "reasoning": self._generate_reasoning(context, analysis, selected)
        }
    
    def _generate_reasoning(self,
                          context: SearchContext,
                          analysis: StrategyAnalysis,
                          strategy: SearchStrategy) -> str:
        """Generiert Erklärung für Strategiewahl"""
        reasons = []
        
        if analysis.complexity_score > 0.7:
            reasons.append("Hohe Anfrage-Komplexität erfordert tiefe Suche")
        
        if analysis.time_pressure > 0.7:
            reasons.append("Hoher Zeitdruck - schnelle Strategie gewählt")
        
        if analysis.agent_availability > 0.7:
            reasons.append("Viele Premium-Agenten verfügbar")
        
        if context.search_iteration > 1:
            reasons.append(f"Iteration {context.search_iteration} - erweiterte Suche")
        
        return "; ".join(reasons) if reasons else "Standard-Auswahl basierend auf Kontext"