"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für dynamische Quellenentdeckung
"""

from typing import List, Dict, Optional, Set, Tuple, Any
import asyncio

from .models import DiscoveredSource, SourceType
from .pattern_manager import SourcePatternManager
from .query_builder import DiscoveryQueryBuilder
from .source_analyzer import SourceAnalyzer
from src.core.logger import get_logger

class DynamicSourceDiscovery:
    """Entdeckt dynamisch relevante Quellen für jedes Land/Region"""
    
    def __init__(self, agents=None):
        self.discovered_sources = {}
        self.pattern_manager = SourcePatternManager()
        self.query_builder = DiscoveryQueryBuilder()
        self.source_analyzer = SourceAnalyzer()
        self.agents = agents or {}  # Dictionary von verfügbaren Agenten
        self.logger = get_logger("agent.dynamic_source_discovery", agent_type="source_discovery")
        
    async def discover_sources_for_country(self, country: str, region: str, 
                                         mine_name: str, languages: List[str]) -> List[DiscoveredSource]:
        """
        Entdeckt dynamisch relevante Quellen für ein Land/Region
        
        Dies ist der Kern der Flexibilität - KEINE hardcodierten Listen!
        """
        sources = []
        
        self.logger.info(f"\n🔍 Starte dynamische Quellenentdeckung für {country}")
        
        # Phase 1: Erstelle Suchanfragen zur Quellenentdeckung
        discovery_queries = self.query_builder.build_discovery_queries(
            country, region, mine_name, languages
        )
        self.logger.info(f"📝 Erstellt {len(discovery_queries)} Suchanfragen")
        
        # Phase 2: Führe Quellensuche durch
        # Nutze verfügbare Search-Agenten (Tavily, Perplexity bevorzugt)
        search_agent = self._select_search_agent()
        
        initial_sources = await self._execute_discovery_search(
            discovery_queries, search_agent
        )
        self.logger.info(f"🌐 {len(initial_sources)} initiale Quellen gefunden")
        
        # Phase 3: Analysiere und kategorisiere gefundene Quellen
        for source in initial_sources:
            categorized_source = self.source_analyzer.categorize_source(source)
            if categorized_source:
                sources.append(categorized_source)
        
        self.logger.info(f"📊 {len(sources)} relevante Quellen kategorisiert")
        
        # Phase 4: Erweitere mit spezialisierten Quellen
        specialized_sources = await self._find_specialized_sources(
            country, region, sources
        )
        sources.extend(specialized_sources)
        
        # Phase 5: Priorisiere und sortiere
        prioritized = self._prioritize_sources(sources)
        
        # Cache Ergebnisse für spätere Verwendung
        cache_key = f"{country}_{region}_{mine_name}"
        self.discovered_sources[cache_key] = prioritized
        
        self.logger.info(f"✨ Quellenentdeckung abgeschlossen: {len(prioritized)} Quellen priorisiert")
        
        return prioritized
    
    async def discover_sources(self, query, agents=None, status_callback=None, cancellation_token=None):
        """
        Wrapper-Methode für Kompatibilität mit SourceDiscoveryService
        
        Args:
            query: MineQuery Objekt
            agents: Liste verfügbarer Agenten
            status_callback: Optional Callback für Status
            cancellation_token: Optional für Abbruch
            
        Returns:
            Liste von entdeckten Quellen
        """
        # Update agents if provided
        if agents:
            self.agents = {agent.name: agent for agent in agents}
        
        # Extract parameters from query
        country = query.country if hasattr(query, 'country') else ""
        region = query.region if hasattr(query, 'region') else ""
        mine_name = query.mine_name if hasattr(query, 'mine_name') else ""
        languages = query.languages if hasattr(query, 'languages') else ["en"]
        
        # Call the existing method
        return await self.discover_sources_for_country(
            country=country,
            region=region,
            mine_name=mine_name,
            languages=languages
        )
    
    def _select_search_agent(self):
        """Wählt den besten verfügbaren Such-Agent"""
        # ÄNDERUNG 23.06.2025: Erweiterte Agent-Suche mit Debug-Logging
        self.logger.info(f"🔍 Verfügbare Agenten: {list(self.agents.keys())}")
        
        # Priorisierte Agenten für Quellensuche
        priority_agents = ['tavily', 'perplexity', 'exa', 'perplexity_deep']
        
        for agent_name in priority_agents:
            if agent_name in self.agents and self.agents[agent_name]:
                agent = self.agents[agent_name]
                # Prüfe ob Agent initialisiert ist
                if hasattr(agent, 'status') and agent.status:
                    self.logger.info(f"✅ Nutze {agent_name} für Quellensuche (Status: {agent.status})")
                    return agent
                else:
                    self.logger.info(f"✅ Nutze {agent_name} für Quellensuche")
                    return agent
        
        # Fallback: Nutze ersten verfügbaren Agent
        if self.agents:
            first_agent = list(self.agents.values())[0]
            self.logger.warning(f"⚠️ Nutze Fallback-Agent: {list(self.agents.keys())[0]}")
            return first_agent
            
        self.logger.error("❌ Keine Agenten verfügbar für Quellensuche")
        return None
    
    async def _execute_discovery_search(self, queries: List[str], 
                                      search_agent=None) -> List[Dict[str, Any]]:
        """
        Führt die initiale Quellensuche durch
        
        ÄNDERUNG 17.06.2025: Direkte Integration mit Search-Agenten
        """
        all_results = []
        
        if not search_agent:
            # ÄNDERUNG 23.06.2025: Verwende Fallback-Quellen wenn kein Agent verfügbar
            self.logger.warning("⚠️ Kein Such-Agent verfügbar für Quellenentdeckung")
            return self._get_fallback_sources()
        
        # Führe Suchen mit übergebenem Agent durch
        for query in queries[:10]:  # Limitiere auf 10 Anfragen pro Phase
            try:
                # Erstelle temporäre MineQuery für Quellensuche
                from ..base_agent import MineQuery
                temp_query = MineQuery(
                    mine_name=query,  # Nutze query als Suchbegriff
                    country="",
                    region="",
                    languages=[],
                    required_fields=[]
                )
                
                # Führe Suche durch
                results = await search_agent.search_mine(temp_query)
                
                # Konvertiere zu erwarteter Struktur
                for result in results:
                    all_results.append({
                        'url': result.source or "",
                        'title': result.field_name or "",
                        'snippet': result.value or ""
                    })
                    
            except Exception as e:
                self.logger.error(f"Fehler bei Quellensuche: {e}")
                continue
        
        # Dedupliziere nach URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def _find_specialized_sources(self, country: str, region: str,
                                      initial_sources: List[DiscoveredSource]) -> List[DiscoveredSource]:
        """Findet spezialisierte Quellen basierend auf initialen Funden"""
        specialized = []
        
        # Analysiere initiale Quellen für Hinweise auf weitere
        for source in initial_sources[:10]:  # Top 10
            # Hier würden wir die Seite analysieren und Links zu
            # verwandten Organisationen, Partnern etc. finden
            pass
        
        return specialized
    
    def _prioritize_sources(self, sources: List[DiscoveredSource]) -> List[DiscoveredSource]:
        """Sortiert Quellen nach Priorität"""
        return sorted(sources, key=lambda x: (x.priority, x.relevance_score), reverse=True)
    
    def get_search_strategy_for_source(self, source: DiscoveredSource) -> Dict[str, Any]:
        """Gibt spezifische Suchstrategie für eine Quelle zurück"""
        return {
            "url": source.url,
            "depth": source.depth_to_explore,
            "keywords": source.keywords_found,
            "language": source.language,
            "focus_areas": self.pattern_manager.get_focus_areas(source.source_type),
            "extraction_hints": self.pattern_manager.get_extraction_hints(source.source_type)
        }
    
    def _get_fallback_sources(self) -> List[Dict[str, Any]]:
        """
        ÄNDERUNG 23.06.2025: Gibt Fallback-Quellen zurück wenn keine Agenten verfügbar
        """
        # Minimale Standard-Quellen für Mining-Recherche
        fallback_sources = [
            {
                'url': 'https://www.mining.com',
                'title': 'Mining.com - Global Mining News',
                'snippet': 'Leading global mining news and analysis'
            },
            {
                'url': 'https://www.mining-technology.com',
                'title': 'Mining Technology',
                'snippet': 'Mining news, mining projects and companies'
            },
            {
                'url': 'https://www.nrcan.gc.ca',
                'title': 'Natural Resources Canada',
                'snippet': 'Canadian government mining information'
            },
            {
                'url': 'https://mern.gouv.qc.ca',
                'title': 'Quebec Mining Ministry',
                'snippet': 'Quebec provincial mining resources'
            },
            {
                'url': 'https://www.infomine.com',
                'title': 'InfoMine',
                'snippet': 'Mining intelligence and technology'
            }
        ]
        
        self.logger.info(f"📌 Verwende {len(fallback_sources)} Fallback-Quellen")
        return fallback_sources