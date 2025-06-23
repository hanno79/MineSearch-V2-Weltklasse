"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Kern-Definitionen für Such-Strategien
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


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


@dataclass
class SearchContext:
    """Kontext für Strategieauswahl"""
    mine_name: str
    country: str
    region: str
    required_fields: List[str]
    available_agents: List[str]
    time_constraint: Optional[int] = None
    previous_results: int = 0
    search_iteration: int = 1


@dataclass
class StrategyAnalysis:
    """Analyse-Ergebnis für Strategieauswahl"""
    complexity_score: float
    geographic_scope: str
    field_complexity: float
    agent_availability: float
    time_pressure: float
    recommended_strategy: Optional[str] = None


# Vordefinierte Strategien
PREDEFINED_STRATEGIES = {
    "quick_scan": SearchStrategy(
        name="Quick Scan",
        scope=SearchScope.GLOBAL,
        depth=SearchDepth.SHALLOW,
        time_budget=60,
        agent_preferences=["tavily", "perplexity"],
        keyword_strategy="broad",
        parallel_searches=5,
        retry_strategy={"max_retries": 1, "backoff": 1}
    ),
    
    "standard_search": SearchStrategy(
        name="Standard Search",
        scope=SearchScope.REGIONAL,
        depth=SearchDepth.STANDARD,
        time_budget=300,
        agent_preferences=["tavily", "perplexity", "scraper", "claude"],
        keyword_strategy="balanced",
        parallel_searches=10,
        retry_strategy={"max_retries": 2, "backoff": 2}
    ),
    
    "deep_research": SearchStrategy(
        name="Deep Research",
        scope=SearchScope.REGIONAL,
        depth=SearchDepth.DEEP,
        time_budget=600,
        agent_preferences=["brightdata", "firecrawl", "claude", "gpt4"],
        keyword_strategy="comprehensive",
        parallel_searches=15,
        retry_strategy={"max_retries": 3, "backoff": 3}
    ),
    
    "government_focus": SearchStrategy(
        name="Government Sources",
        scope=SearchScope.GOVERNMENT,
        depth=SearchDepth.DEEP,
        time_budget=480,
        agent_preferences=["scraper", "brightdata", "firecrawl"],
        keyword_strategy="official",
        parallel_searches=8,
        retry_strategy={"max_retries": 3, "backoff": 5}
    ),
    
    "news_monitoring": SearchStrategy(
        name="News & Updates",
        scope=SearchScope.NEWS,
        depth=SearchDepth.STANDARD,
        time_budget=180,
        agent_preferences=["tavily", "perplexity"],
        keyword_strategy="recent",
        parallel_searches=12,
        retry_strategy={"max_retries": 2, "backoff": 1}
    ),
    
    "financial_analysis": SearchStrategy(
        name="Financial Research",
        scope=SearchScope.FINANCIAL,
        depth=SearchDepth.DEEP,
        time_budget=420,
        agent_preferences=["claude", "gpt4", "brightdata"],
        keyword_strategy="financial",
        parallel_searches=6,
        retry_strategy={"max_retries": 2, "backoff": 3}
    ),
    
    "exhaustive_search": SearchStrategy(
        name="Exhaustive Search",
        scope=SearchScope.GLOBAL,
        depth=SearchDepth.EXHAUSTIVE,
        time_budget=1200,
        agent_preferences=["all"],
        keyword_strategy="exhaustive",
        parallel_searches=20,
        retry_strategy={"max_retries": 5, "backoff": 5}
    )
}


# Field-Kategorien für Komplexitätsbewertung
FIELD_CATEGORIES = {
    "basic": ["location", "coordinates", "ownership", "status"],
    "technical": ["depth", "production", "reserves", "ore_grade"],
    "financial": ["revenue", "costs", "investment", "valuation"],
    "regulatory": ["permits", "licenses", "environmental", "compliance"],
    "operational": ["employees", "equipment", "infrastructure", "capacity"],
    "geological": ["geology", "mineralization", "exploration", "drilling"]
}


# Agent-Capabilities für bessere Zuordnung
AGENT_CAPABILITIES = {
    "tavily": ["general", "news", "quick"],
    "perplexity": ["general", "ai_analysis", "comprehensive"],
    "scraper": ["deep_web", "government", "technical"],
    "brightdata": ["enterprise", "deep_web", "large_scale"],
    "firecrawl": ["javascript", "modern_sites", "structured"],
    "claude": ["analysis", "complex", "multilingual"],
    "gpt4": ["analysis", "technical", "financial"],
    "exa": ["semantic", "research", "academic"],
    "apify": ["automation", "scaling", "custom"]
}