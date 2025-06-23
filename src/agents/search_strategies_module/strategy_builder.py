"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Builder für Such-Strategien und Analyse-Funktionen
"""

from typing import List, Dict, Any
from .models import SearchStrategy, SearchScope, SearchDepth


class StrategyBuilder:
    """Erstellt und analysiert Such-Strategien"""
    
    def build_default_strategies(self) -> Dict[str, SearchStrategy]:
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
    
    def analyze_requirements(self, mine_name: str, country: str,
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
    
    def score_strategy(self, strategy: SearchStrategy, 
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
    
    def get_site_recommendations(self, field_type: str) -> List[str]:
        """Gibt feldspezifische Website-Empfehlungen zurück"""
        # Feldspezifische Domain-Empfehlungen
        field_domains = {
            # Betreiber/Eigentümer Informationen
            "betreiber": [
                "sedar.com", "sec.gov", "asx.com.au", "tsx.com",
                "bloomberg.com", "reuters.com", "marketwatch.com"
            ],
            "operator": [
                "sedar.com", "sec.gov", "asx.com.au", "tsx.com",
                "mining.com", "northernminer.com"
            ],
            "owner": [
                "sedar.com", "sec.gov", "companieshouse.gov.uk",
                "corporationsincanada.ic.gc.ca"
            ],
            
            # Koordinaten und Standort
            "koordinaten": [
                "nrcan.gc.ca", "usgs.gov", "ga.gov.au",
                "mindat.org", "geologyontario.mndm.gov.on.ca"
            ],
            "coordinates": [
                "nrcan.gc.ca", "usgs.gov", "ga.gov.au",
                "mindat.org", "maps.google.com"
            ],
            
            # Rohstoffe und Mineralien
            "rohstofftyp": [
                "usgs.gov", "nrcan.gc.ca", "ga.gov.au",
                "mineralseducationcoalition.org", "ima-mineralogy.org"
            ],
            "commodity": [
                "usgs.gov", "mining.com", "kitco.com",
                "lme.com", "infomine.com"
            ],
            
            # Status und Betrieb
            "aktivitaetsstatus": [
                "mining.com", "northernminer.com", "miningweekly.com",
                "nrcan.gc.ca", "mern.gouv.qc.ca"
            ],
            "status": [
                "mining.com", "miningnewsnorth.com", "canadianminingjournal.com",
                "globalminingreview.com"
            ],
            
            # Sanierungskosten
            "sanierungskosten": [
                "epa.gov", "environment.gov.au", "ec.gc.ca",
                "sedar.com", "sec.gov"
            ],
            "remediation_costs": [
                "epa.gov", "environment.gov.au", "ec.gc.ca",
                "environmentalfinance.com"
            ],
            
            # Default/Allgemein
            "default": [
                "mining.com", "northernminer.com", "miningweekly.com",
                "nrcan.gc.ca", "usgs.gov", "ga.gov.au",
                "sedar.com", "asx.com.au"
            ]
        }
        
        # Normalisiere Feldtyp
        field_lower = field_type.lower() if field_type else "default"
        
        # Suche passende Domains
        recommendations = field_domains.get(field_lower, [])
        
        # Wenn keine spezifischen gefunden, suche nach Teilübereinstimmungen
        if not recommendations:
            for key, domains in field_domains.items():
                if key in field_lower or field_lower in key:
                    recommendations.extend(domains)
        
        # Fallback zu Default wenn nichts gefunden
        if not recommendations:
            recommendations = field_domains["default"]
        
        # Dedupliziere und limitiere
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:15]  # Max 15 Empfehlungen
    
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
            "exhaustive": {
                "max_keywords": 200,
                "include_variations": True,
                "include_translations": True,
                "specificity": "all"
            }
        }
        
        return keyword_strategies.get(strategy_type, keyword_strategies["balanced"])
    
    def create_specialized_queries(self, mine_name: str, fields: List[str], 
                                 region: str, country: str, 
                                 languages: List[str]) -> List[Dict[str, Any]]:
        """Erstellt spezialisierte Suchanfragen basierend auf Feldern"""
        queries = []
        
        # Basis-Query für allgemeine Informationen
        base_query = f'"{mine_name}" mine {region} {country}'
        
        # Feldspezifische Queries
        field_templates = {
            "betreiber": f'{base_query} operator owner company',
            "operator": f'{base_query} operator owner company',
            "koordinaten": f'{base_query} coordinates GPS location latitude longitude',
            "coordinates": f'{base_query} coordinates GPS location latitude longitude',
            "sanierungskosten": f'{base_query} remediation costs environmental bond closure',
            "remediation_costs": f'{base_query} remediation costs environmental bond closure',
            "produktion": f'{base_query} production capacity tonnes output',
            "production": f'{base_query} production capacity tonnes output',
            "status": f'{base_query} operational status active closed suspended',
            "rohstofftyp": f'{base_query} commodity mineral resource type',
            "commodity": f'{base_query} commodity mineral resource type'
        }
        
        # Erstelle Queries für jedes Feld
        for field in fields:
            field_lower = field.lower()
            if field_lower in field_templates:
                queries.append({
                    "query": field_templates[field_lower],
                    "field": field,
                    "priority": "high" if field_lower in ["sanierungskosten", "remediation_costs"] else "medium"
                })
        
        # Füge generische Queries hinzu
        queries.extend([
            {
                "query": f'{base_query} mining database government records',
                "field": "general",
                "priority": "high"
            },
            {
                "query": f'{base_query} technical report NI 43-101 feasibility',
                "field": "technical",
                "priority": "medium"
            },
            {
                "query": f'{base_query} news updates recent developments',
                "field": "news",
                "priority": "low"
            }
        ])
        
        return queries
    
    # Private Methoden
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