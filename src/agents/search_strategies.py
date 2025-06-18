"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Flexible Such-Strategien für Mining Research - Anpassbar an alle Szenarien
"""

from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

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

class SearchStrategies:
    """
    Verwaltung flexibler Such-Strategien
    
    - Adaptiv: Passt sich an verschiedene Szenarien an
    - Effizient: Optimiert Zeit und Ressourcen
    - Flexibel: Keine hardcodierten Annahmen
    """
    
    def __init__(self):
        self.strategies = self._initialize_strategies()
        self.active_strategy = None
        self.search_history = []
        
    def _initialize_strategies(self) -> Dict[str, SearchStrategy]:
        """Initialisiert verschiedene Such-Strategien"""
        return {
            "quick_scan": SearchStrategy(
                name="Quick Scan",
                scope=SearchScope.GLOBAL,
                depth=SearchDepth.SHALLOW,
                time_budget=60,  # 1 Minute
                agent_preferences=["tavily", "perplexity"],
                keyword_strategy="broad",
                parallel_searches=5,
                retry_strategy={"max_retries": 1, "backoff": 1}
            ),
            
            "standard_search": SearchStrategy(
                name="Standard Search",
                scope=SearchScope.REGIONAL,
                depth=SearchDepth.STANDARD,
                time_budget=300,  # 5 Minuten
                agent_preferences=["tavily", "perplexity", "scraper", "claude"],
                keyword_strategy="balanced",
                parallel_searches=10,
                retry_strategy={"max_retries": 2, "backoff": 2}
            ),
            
            "deep_research": SearchStrategy(
                name="Deep Research",
                scope=SearchScope.REGIONAL,
                depth=SearchDepth.DEEP,
                time_budget=600,  # 10 Minuten
                agent_preferences=["brightdata", "firecrawl", "claude", "gpt4"],
                keyword_strategy="comprehensive",
                parallel_searches=15,
                retry_strategy={"max_retries": 3, "backoff": 3}
            ),
            
            "government_focus": SearchStrategy(
                name="Government Sources",
                scope=SearchScope.GOVERNMENT,
                depth=SearchDepth.DEEP,
                time_budget=480,  # 8 Minuten
                agent_preferences=["scraper", "brightdata", "firecrawl"],
                keyword_strategy="official",
                parallel_searches=8,
                retry_strategy={"max_retries": 3, "backoff": 5}
            ),
            
            "news_monitoring": SearchStrategy(
                name="News & Updates",
                scope=SearchScope.NEWS,
                depth=SearchDepth.STANDARD,
                time_budget=180,  # 3 Minuten
                agent_preferences=["tavily", "perplexity"],
                keyword_strategy="recent",
                parallel_searches=12,
                retry_strategy={"max_retries": 2, "backoff": 1}
            ),
            
            "financial_analysis": SearchStrategy(
                name="Financial Research",
                scope=SearchScope.FINANCIAL,
                depth=SearchDepth.DEEP,
                time_budget=420,  # 7 Minuten
                agent_preferences=["claude", "gpt4", "brightdata"],
                keyword_strategy="financial",
                parallel_searches=6,
                retry_strategy={"max_retries": 2, "backoff": 3}
            ),
            
            "exhaustive_search": SearchStrategy(
                name="Exhaustive Search",
                scope=SearchScope.GLOBAL,
                depth=SearchDepth.EXHAUSTIVE,
                time_budget=1200,  # 20 Minuten
                agent_preferences=["all"],  # Alle verfügbaren Agenten
                keyword_strategy="exhaustive",
                parallel_searches=20,
                retry_strategy={"max_retries": 5, "backoff": 5}
            )
        }
    
    def select_strategy(self, mine_name: str, country: str, region: str,
                       required_fields: List[str], available_agents: List[str],
                       time_constraint: Optional[int] = None) -> SearchStrategy:
        """
        Wählt die beste Strategie basierend auf Kontext
        
        Vollständig dynamisch - keine hardcodierten Annahmen!
        """
        # Analysiere Anforderungen
        analysis = self._analyze_requirements(
            mine_name, country, region, required_fields
        )
        
        # Berücksichtige Zeit-Constraint
        if time_constraint:
            suitable_strategies = [
                s for s in self.strategies.values()
                if s.time_budget <= time_constraint
            ]
        else:
            suitable_strategies = list(self.strategies.values())
        
        # Score Strategien
        strategy_scores = {}
        for strategy in suitable_strategies:
            score = self._score_strategy(
                strategy, analysis, available_agents
            )
            strategy_scores[strategy.name] = (score, strategy)
        
        # Wähle beste Strategie
        if strategy_scores:
            best_strategy = max(
                strategy_scores.values(),
                key=lambda x: x[0]
            )[1]
        else:
            # Fallback zu Standard
            best_strategy = self.strategies["standard_search"]
        
        self.active_strategy = best_strategy
        return best_strategy
    
    def _analyze_requirements(self, mine_name: str, country: str,
                            region: str, required_fields: List[str]) -> Dict[str, Any]:
        """Analysiert Such-Anforderungen"""
        analysis = {
            "complexity": self._assess_complexity(required_fields),
            "geographic_scope": self._assess_geographic_scope(country, region),
            "field_types": self._categorize_fields(required_fields),
            "language_needs": self._assess_language_needs(country),
            "source_preferences": self._determine_source_preferences(required_fields)
        }
        
        return analysis
    
    def _assess_complexity(self, required_fields: List[str]) -> str:
        """Bewertet Komplexität der Suche"""
        field_count = len(required_fields)
        
        # Komplexe Felder
        complex_fields = [
            'sanierungskosten', 'remediation_costs', 'closure_costs',
            'environmental_impact', 'technical_details', 'financial_data'
        ]
        
        complex_count = sum(
            1 for field in required_fields
            if any(complex in field.lower() for complex in complex_fields)
        )
        
        if field_count <= 3 and complex_count == 0:
            return "low"
        elif field_count <= 8 and complex_count <= 2:
            return "medium"
        else:
            return "high"
    
    def _assess_geographic_scope(self, country: str, region: str) -> str:
        """Bewertet geografischen Suchbereich"""
        # Major Mining Countries (würde dynamisch erweitert)
        major_mining_countries = [
            "canada", "australia", "chile", "peru", "south africa",
            "china", "russia", "usa", "brazil", "mexico"
        ]
        
        if country.lower() in major_mining_countries:
            if region:
                return "regional"
            else:
                return "national"
        else:
            return "global"
    
    def _categorize_fields(self, required_fields: List[str]) -> Dict[str, int]:
        """Kategorisiert Felder nach Typ"""
        categories = {
            "operational": 0,
            "financial": 0,
            "environmental": 0,
            "technical": 0,
            "legal": 0,
            "general": 0
        }
        
        # Feld-Kategorisierung (erweiterbar)
        field_categories = {
            "operational": ["operator", "status", "production", "employees"],
            "financial": ["costs", "revenue", "investment", "budget"],
            "environmental": ["environmental", "restoration", "contamination"],
            "technical": ["coordinates", "reserves", "grade", "geology"],
            "legal": ["permit", "license", "compliance", "ownership"]
        }
        
        for field in required_fields:
            field_lower = field.lower()
            categorized = False
            
            for category, keywords in field_categories.items():
                if any(keyword in field_lower for keyword in keywords):
                    categories[category] += 1
                    categorized = True
                    break
            
            if not categorized:
                categories["general"] += 1
        
        return categories
    
    def _assess_language_needs(self, country: str) -> List[str]:
        """Bestimmt benötigte Sprachen"""
        # Basis-Sprachzuordnung (würde aus Datenbank kommen)
        country_languages = {
            "canada": ["en", "fr"],
            "mexico": ["es", "en"],
            "brazil": ["pt", "en"],
            "peru": ["es", "en"],
            "chile": ["es", "en"],
            "argentina": ["es", "en"],
            "spain": ["es", "en"],
            "france": ["fr", "en"],
            "germany": ["de", "en"],
            "china": ["zh", "en"],
            "russia": ["ru", "en"],
            "south africa": ["en", "af"],
            "australia": ["en"],
            "usa": ["en"],
            "uk": ["en"]
        }
        
        languages = country_languages.get(country.lower(), ["en"])
        return languages
    
    def _determine_source_preferences(self, required_fields: List[str]) -> List[str]:
        """Bestimmt bevorzugte Quellentypen"""
        preferences = []
        
        # Analysiere Felder für Quellenpräferenzen
        for field in required_fields:
            field_lower = field.lower()
            
            if any(term in field_lower for term in ["permit", "license", "legal"]):
                preferences.append("government")
            elif any(term in field_lower for term in ["financial", "cost", "revenue"]):
                preferences.append("financial")
            elif any(term in field_lower for term in ["environmental", "impact"]):
                preferences.extend(["government", "ngo"])
            elif any(term in field_lower for term in ["news", "recent", "update"]):
                preferences.append("news")
        
        # Dedupliziere
        return list(set(preferences)) if preferences else ["general"]
    
    def _score_strategy(self, strategy: SearchStrategy, 
                       analysis: Dict[str, Any],
                       available_agents: List[str]) -> float:
        """Bewertet eine Strategie"""
        score = 0.0
        
        # Komplexitäts-Matching
        complexity_match = {
            ("low", SearchDepth.SHALLOW): 1.0,
            ("low", SearchDepth.STANDARD): 0.8,
            ("medium", SearchDepth.STANDARD): 1.0,
            ("medium", SearchDepth.DEEP): 0.9,
            ("high", SearchDepth.DEEP): 1.0,
            ("high", SearchDepth.EXHAUSTIVE): 0.9
        }
        
        score += complexity_match.get(
            (analysis["complexity"], strategy.depth), 0.5
        ) * 0.3
        
        # Agent-Verfügbarkeit
        if strategy.agent_preferences[0] == "all":
            agent_score = 1.0
        else:
            available_preferred = sum(
                1 for agent in strategy.agent_preferences
                if agent in available_agents
            )
            agent_score = available_preferred / len(strategy.agent_preferences)
        
        score += agent_score * 0.4
        
        # Quellen-Präferenz
        if strategy.scope.value in analysis["source_preferences"]:
            score += 0.2
        
        # Zeit-Effizienz
        if analysis["complexity"] == "low" and strategy.time_budget <= 180:
            score += 0.1
        elif analysis["complexity"] == "high" and strategy.time_budget >= 600:
            score += 0.1
        
        return score
    
    def adapt_strategy(self, current_results: List[Any], 
                      time_elapsed: float) -> Optional[SearchStrategy]:
        """
        Passt Strategie basierend auf bisherigen Ergebnissen an
        
        Ermöglicht dynamische Anpassung während der Suche
        """
        if not self.active_strategy:
            return None
        
        # Analysiere bisherige Ergebnisse
        result_quality = self._assess_result_quality(current_results)
        remaining_time = self.active_strategy.time_budget - time_elapsed
        
        # Entscheide über Anpassung
        if result_quality < 0.3 and remaining_time > 60:
            # Schlechte Ergebnisse - intensiviere
            return self._intensify_strategy(self.active_strategy)
        elif result_quality > 0.8 and remaining_time < 60:
            # Gute Ergebnisse und wenig Zeit - beende früh
            return self._simplify_strategy(self.active_strategy)
        
        return None
    
    def _assess_result_quality(self, results: List[Any]) -> float:
        """Bewertet Qualität der bisherigen Ergebnisse"""
        if not results:
            return 0.0
        
        # Vereinfachte Qualitätsbewertung
        # (würde in Praxis komplexer sein)
        quality_indicators = {
            "high_confidence": sum(1 for r in results if hasattr(r, 'confidence_score') and r.confidence_score > 0.8),
            "diverse_sources": len(set(r.source for r in results if hasattr(r, 'source'))),
            "total_results": len(results)
        }
        
        quality_score = 0.0
        
        if quality_indicators["total_results"] > 0:
            quality_score += min(quality_indicators["high_confidence"] / quality_indicators["total_results"], 1.0) * 0.5
            quality_score += min(quality_indicators["diverse_sources"] / 10, 1.0) * 0.3
            quality_score += min(quality_indicators["total_results"] / 50, 1.0) * 0.2
        
        return quality_score
    
    def _intensify_strategy(self, strategy: SearchStrategy) -> SearchStrategy:
        """Intensiviert eine Such-Strategie"""
        intensified = SearchStrategy(
            name=f"{strategy.name} (Intensified)",
            scope=strategy.scope,
            depth=SearchDepth.DEEP if strategy.depth == SearchDepth.STANDARD else SearchDepth.EXHAUSTIVE,
            time_budget=int(strategy.time_budget * 1.5),
            agent_preferences=strategy.agent_preferences + ["claude", "gpt4"],
            keyword_strategy="comprehensive",
            parallel_searches=min(strategy.parallel_searches * 2, 30),
            retry_strategy={
                "max_retries": strategy.retry_strategy["max_retries"] + 2,
                "backoff": strategy.retry_strategy["backoff"]
            }
        )
        return intensified
    
    def _simplify_strategy(self, strategy: SearchStrategy) -> SearchStrategy:
        """Vereinfacht eine Such-Strategie"""
        simplified = SearchStrategy(
            name=f"{strategy.name} (Simplified)",
            scope=strategy.scope,
            depth=SearchDepth.SHALLOW,
            time_budget=60,
            agent_preferences=strategy.agent_preferences[:2],
            keyword_strategy="focused",
            parallel_searches=5,
            retry_strategy={
                "max_retries": 1,
                "backoff": 1
            }
        )
        return simplified
    
    def get_keyword_strategy_params(self, strategy_type: str) -> Dict[str, Any]:
        """Gibt Parameter für Keyword-Strategie zurück"""
        keyword_strategies = {
            "broad": {
                "max_keywords": 50,
                "include_variations": True,
                "include_translations": True,
                "specificity": "low"
            },
            "balanced": {
                "max_keywords": 30,
                "include_variations": True,
                "include_translations": True,
                "specificity": "medium"
            },
            "focused": {
                "max_keywords": 15,
                "include_variations": False,
                "include_translations": True,
                "specificity": "high"
            },
            "comprehensive": {
                "max_keywords": 100,
                "include_variations": True,
                "include_translations": True,
                "specificity": "mixed"
            },
            "official": {
                "max_keywords": 20,
                "include_variations": False,
                "include_translations": True,
                "specificity": "official_terms"
            },
            "recent": {
                "max_keywords": 25,
                "include_variations": False,
                "include_translations": False,
                "specificity": "temporal"
            },
            "financial": {
                "max_keywords": 20,
                "include_variations": False,
                "include_translations": True,
                "specificity": "financial_terms"
            },
            "exhaustive": {
                "max_keywords": 200,
                "include_variations": True,
                "include_translations": True,
                "specificity": "all"
            }
        }
        
        return keyword_strategies.get(strategy_type, keyword_strategies["balanced"])
    
    def log_strategy_performance(self, strategy: SearchStrategy, 
                                results_count: int, time_taken: float,
                                quality_score: float):
        """Protokolliert Strategie-Performance für Lernen"""
        self.search_history.append({
            "strategy": strategy.name,
            "results": results_count,
            "time": time_taken,
            "quality": quality_score,
            "efficiency": results_count / time_taken if time_taken > 0 else 0
        })
        
        # Könnte für ML-basierte Strategieverbesserung genutzt werden