"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Query-Optimierung für Premium Mining Research
"""

from typing import List, Dict, Any, Set
from .models import SearchQuery, SourceReliability
from ..base_agent import MineQuery


class QueryOptimizer:
    """Optimiert Suchanfragen für maximale Effizienz"""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.agent_capabilities = self._analyze_agent_capabilities()
    
    def _analyze_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Analysiert Fähigkeiten der verfügbaren Agenten"""
        capabilities = {}
        
        # Standard-Fähigkeiten für bekannte Agenten
        agent_profiles = {
            "tavily": {
                "speed": "fast",
                "depth": "shallow",
                "languages": ["en", "es", "fr", "de"],
                "specialties": ["news", "recent", "overview"],
                "rate_limit": 100
            },
            "perplexity": {
                "speed": "fast",
                "depth": "medium",
                "languages": ["en", "es", "fr", "pt"],
                "specialties": ["comprehensive", "academic"],
                "rate_limit": 50
            },
            "claude": {
                "speed": "medium",
                "depth": "deep",
                "languages": ["all"],
                "specialties": ["analysis", "extraction", "verification"],
                "rate_limit": 30
            },
            "gpt4": {
                "speed": "medium",
                "depth": "deep",
                "languages": ["all"],
                "specialties": ["analysis", "translation", "complex"],
                "rate_limit": 30
            },
            "scraper": {
                "speed": "slow",
                "depth": "deep",
                "languages": ["all"],
                "specialties": ["tables", "pdfs", "structured"],
                "rate_limit": 20
            },
            "brightdata": {
                "speed": "slow",
                "depth": "deep",
                "languages": ["all"],
                "specialties": ["government", "restricted", "regional"],
                "rate_limit": 10
            },
            "firecrawl": {
                "speed": "medium",
                "depth": "deep",
                "languages": ["all"],
                "specialties": ["javascript", "dynamic", "modern"],
                "rate_limit": 25
            }
        }
        
        for agent_name in self.agents:
            if agent_name in agent_profiles:
                capabilities[agent_name] = agent_profiles[agent_name]
            else:
                # Default für unbekannte Agenten
                capabilities[agent_name] = {
                    "speed": "medium",
                    "depth": "medium",
                    "languages": ["en"],
                    "specialties": ["general"],
                    "rate_limit": 20
                }
        
        return capabilities
    
    def build_intelligent_queries(self, query: MineQuery, 
                                keywords: Dict[str, List[str]],
                                sources: List[Any]) -> List[SearchQuery]:
        """Erstellt optimierte Suchanfragen"""
        search_queries = []
        
        # Basis-Query-Templates für verschiedene Feldtypen
        query_templates = self._get_query_templates()
        
        for field in query.required_fields:
            field_lower = field.lower()
            
            # Wähle passende Templates
            templates = query_templates.get(field_lower, query_templates["default"])
            
            # Erstelle Queries für jede Sprache
            for lang in query.languages:
                lang_keywords = keywords.get(lang, keywords.get("en", []))
                
                for template in templates:
                    # Ersetze Platzhalter
                    query_text = template.format(
                        mine_name=query.mine_name,
                        country=query.country,
                        region=query.region,
                        keywords=' '.join(lang_keywords[:5])  # Top 5 Keywords
                    )
                    
                    # Bestimme Priorität basierend auf Feld
                    priority = self._determine_priority(field_lower)
                    
                    # Bestimme beste Agenten für diese Query
                    agent_prefs = self._select_agents_for_query(
                        field_lower, lang, sources
                    )
                    
                    search_queries.append(SearchQuery(
                        query_text=query_text,
                        target_field=field,
                        priority=priority,
                        language=lang,
                        agent_preferences=agent_prefs,
                        source_restrictions=self._get_source_restrictions(field_lower)
                    ))
        
        # Sortiere nach Priorität
        search_queries.sort(key=lambda q: (
            0 if q.priority == "high" else (1 if q.priority == "medium" else 2)
        ))
        
        return search_queries
    
    def assign_queries_to_agents(self, queries: List[SearchQuery]) -> Dict[str, List[SearchQuery]]:
        """Teilt Queries optimal auf Agenten auf"""
        assignments = {agent: [] for agent in self.agents}
        agent_loads = {agent: 0 for agent in self.agents}
        
        for query in queries:
            # Finde besten verfügbaren Agenten
            best_agent = None
            best_score = -1
            
            for agent_pref in query.agent_preferences:
                if agent_pref not in self.agents:
                    continue
                
                # Berechne Score basierend auf Last und Fähigkeiten
                capability = self.agent_capabilities.get(agent_pref, {})
                current_load = agent_loads[agent_pref]
                rate_limit = capability.get("rate_limit", 20)
                
                # Score basiert auf:
                # - Verfügbare Kapazität
                # - Sprachunterstützung
                # - Spezialisierung
                load_factor = 1 - (current_load / rate_limit)
                lang_factor = 1.0 if query.language in capability.get("languages", []) else 0.5
                specialty_factor = 1.0 if any(
                    spec in query.query_text.lower() 
                    for spec in capability.get("specialties", [])
                ) else 0.7
                
                score = load_factor * lang_factor * specialty_factor
                
                if score > best_score and current_load < rate_limit:
                    best_agent = agent_pref
                    best_score = score
            
            # Fallback auf ersten verfügbaren Agenten
            if not best_agent:
                for agent in self.agents:
                    if agent_loads[agent] < self.agent_capabilities[agent].get("rate_limit", 20):
                        best_agent = agent
                        break
            
            if best_agent:
                assignments[best_agent].append(query)
                agent_loads[best_agent] += 1
        
        # Entferne leere Assignments
        return {k: v for k, v in assignments.items() if v}
    
    def optimize_for_parallel_execution(self, queries: List[SearchQuery], 
                                      max_parallel: int = 20) -> List[List[SearchQuery]]:
        """Gruppiert Queries für parallele Ausführung"""
        # Sortiere nach geschätzter Ausführungszeit
        sorted_queries = sorted(queries, key=lambda q: self._estimate_execution_time(q))
        
        # Erstelle Batches
        batches = []
        current_batch = []
        current_batch_time = 0
        max_batch_time = 10  # Sekunden
        
        for query in sorted_queries:
            est_time = self._estimate_execution_time(query)
            
            if len(current_batch) >= max_parallel or current_batch_time + est_time > max_batch_time:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [query]
                current_batch_time = est_time
            else:
                current_batch.append(query)
                current_batch_time += est_time
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    # Private Hilfsmethoden
    def _get_query_templates(self) -> Dict[str, List[str]]:
        """Gibt Query-Templates für verschiedene Feldtypen zurück"""
        return {
            "betreiber": [
                '"{mine_name}" operator owner company {country}',
                '"{mine_name}" mine operator {region} {country}',
                '"{mine_name}" mining company ownership'
            ],
            "operator": [
                '"{mine_name}" operator owner company {country}',
                '"{mine_name}" mine operator {region} {country}'
            ],
            "koordinaten": [
                '"{mine_name}" coordinates GPS location {country}',
                '"{mine_name}" latitude longitude {region}',
                '"{mine_name}" mine location map'
            ],
            "coordinates": [
                '"{mine_name}" coordinates GPS location {country}',
                '"{mine_name}" latitude longitude {region}'
            ],
            "sanierungskosten": [
                '"{mine_name}" remediation costs environmental bond',
                '"{mine_name}" closure costs rehabilitation {country}',
                '"{mine_name}" mine restoration budget'
            ],
            "remediation_costs": [
                '"{mine_name}" remediation costs environmental bond',
                '"{mine_name}" closure costs rehabilitation {country}'
            ],
            "default": [
                '"{mine_name}" {keywords} {country}',
                '"{mine_name}" mine {keywords} {region}'
            ]
        }
    
    def _determine_priority(self, field: str) -> str:
        """Bestimmt Priorität basierend auf Feldtyp"""
        high_priority_fields = [
            "sanierungskosten", "remediation_costs", "environmental_impact",
            "closure_date", "contamination", "legal_issues"
        ]
        
        medium_priority_fields = [
            "operator", "betreiber", "owner", "production", "status",
            "coordinates", "koordinaten", "commodity"
        ]
        
        if field in high_priority_fields:
            return "high"
        elif field in medium_priority_fields:
            return "medium"
        else:
            return "low"
    
    def _select_agents_for_query(self, field: str, language: str, 
                               sources: List[Any]) -> List[str]:
        """Wählt beste Agenten für eine Query"""
        # Feldspezifische Agenten-Präferenzen
        field_preferences = {
            "sanierungskosten": ["claude", "gpt4", "brightdata", "scraper"],
            "remediation_costs": ["claude", "gpt4", "brightdata", "scraper"],
            "operator": ["tavily", "perplexity", "scraper"],
            "betreiber": ["tavily", "perplexity", "scraper"],
            "coordinates": ["tavily", "perplexity", "firecrawl"],
            "koordinaten": ["tavily", "perplexity", "firecrawl"]
        }
        
        # Basis-Präferenzen
        preferences = field_preferences.get(field, ["tavily", "perplexity", "claude"])
        
        # Filtere basierend auf Sprachunterstützung
        suitable_agents = []
        for agent in preferences:
            if agent in self.agents:
                capability = self.agent_capabilities.get(agent, {})
                languages = capability.get("languages", [])
                if "all" in languages or language in languages:
                    suitable_agents.append(agent)
        
        # Fallback auf alle verfügbaren Agenten
        if not suitable_agents:
            suitable_agents = list(self.agents.keys())
        
        return suitable_agents[:5]  # Max 5 Agenten
    
    def _get_source_restrictions(self, field: str) -> List[str]:
        """Gibt Quellen-Beschränkungen für bestimmte Felder zurück"""
        restrictions = {
            "sanierungskosten": ["government", "official", "regulatory"],
            "remediation_costs": ["government", "official", "regulatory"],
            "permit": ["government", "regulatory"],
            "license": ["government", "regulatory"]
        }
        
        return restrictions.get(field, [])
    
    def _estimate_execution_time(self, query: SearchQuery) -> float:
        """Schätzt Ausführungszeit einer Query"""
        # Basis-Schätzung
        base_time = 2.0
        
        # Anpassung basierend auf Query-Komplexität
        if len(query.query_text) > 100:
            base_time += 1.0
        
        # Anpassung basierend auf Agent
        if query.agent_preferences:
            agent = query.agent_preferences[0]
            capability = self.agent_capabilities.get(agent, {})
            speed = capability.get("speed", "medium")
            
            if speed == "fast":
                base_time *= 0.7
            elif speed == "slow":
                base_time *= 1.5
        
        return base_time