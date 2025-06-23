"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Source Discovery Service für MineSearch - entdeckt relevante Datenquellen
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from src.agents.base_agent import MineQuery, SearchResult
from src.agents.dynamic_source_discovery import DynamicSourceDiscovery
from .source_manager import SourceManager, SourceInfo
from .cancellation import CancellationToken, CancellationException
from .logger import get_logger


class SourceDiscoveryService:
    """Service für die Entdeckung relevanter Datenquellen"""
    
    def __init__(self, source_manager: SourceManager):
        self.source_manager = source_manager
        self.logger = get_logger("source_discovery")
        self._discovery_cache = {}
        
    async def discover_sources(
        self,
        query: MineQuery,
        agents: List[Any],
        status_callback=None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[SourceInfo]:
        """
        Entdeckt relevante Quellen für eine Mine
        
        Args:
            query: Such-Query mit Mine-Informationen
            agents: Liste verfügbarer Such-Agenten
            status_callback: Callback für Status-Updates
            cancellation_token: Token für Abbruch
            
        Returns:
            Liste entdeckter Quellen
        """
        cache_key = f"{query.mine_name}_{query.country}_{query.region}"
        
        # Check cache
        if cache_key in self._discovery_cache:
            cached_sources = self._discovery_cache[cache_key]
            if self._is_cache_valid(cached_sources):
                self._report_status(
                    f"Verwende {len(cached_sources['sources'])} gecachte Quellen",
                    status_callback
                )
                return cached_sources['sources']
        
        # Start discovery
        self._report_status("🔍 PHASE 0: QUELLEN-DISCOVERY", status_callback)
        self._report_status(f"Suche Datenquellen für {query.mine_name}...", status_callback)
        
        # Initialize source discovery
        discovery = DynamicSourceDiscovery(None)  # Config wird später gesetzt
        
        # Discover sources using agents
        discovered_sources = []
        
        # 1. Use specialized source discovery
        try:
            sources = await discovery.discover_sources(query)
            discovered_sources.extend(sources)
            self._report_status(
                f"✅ Basis-Discovery: {len(sources)} Quellen gefunden",
                status_callback
            )
        except Exception as e:
            self.logger.error(f"Fehler bei Basis-Discovery: {e}")
        
        # 2. Use search agents for additional sources
        if agents:
            agent_sources = await self._discover_with_agents(
                query, agents[:3], status_callback, cancellation_token
            )
            discovered_sources.extend(agent_sources)
        
        # 3. Process and rank sources
        processed_sources = self._process_sources(discovered_sources, query)
        
        # 4. Cache results
        self._discovery_cache[cache_key] = {
            'sources': processed_sources,
            'timestamp': datetime.now()
        }
        
        self._report_status(
            f"✅ QUELLENSUCHE ABGESCHLOSSEN: {len(processed_sources)} relevante Quellen",
            status_callback
        )
        
        return processed_sources
    
    async def _discover_with_agents(
        self,
        query: MineQuery,
        agents: List[Any],
        status_callback,
        cancellation_token
    ) -> List[SourceInfo]:
        """Nutzt Such-Agenten zur Quellen-Entdeckung"""
        agent_sources = []
        
        for agent in agents:
            if cancellation_token and cancellation_token.is_cancelled():
                break
            
            try:
                agent_name = getattr(agent, 'name', type(agent).__name__)
                self._report_status(f"🤖 {agent_name} sucht Quellen...", status_callback)
                
                # Erstelle spezielle Query für Quellen-Suche
                source_query = MineQuery(
                    mine_name=query.mine_name,
                    region=query.region,
                    country=query.country,
                    languages=query.languages,
                    required_fields=["official_website", "government_portal", "news_source"]
                )
                
                # ÄNDERUNG 23.06.2025: Fix - Verwende search_mine statt search
                results = await agent.search_mine(source_query)
                
                # Extrahiere URLs aus Ergebnissen
                for result in results:
                    if hasattr(result, 'source_url') and result.source_url:
                        source_info = SourceInfo(
                            url=result.source_url,
                            source_type=self._determine_source_type(result.source_url),
                            discovered_by=agent_name,
                            relevance_score=0.7,
                            last_updated=datetime.now()
                        )
                        agent_sources.append(source_info)
                        self._report_status(f"📊 {result.source_url}", status_callback)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Agent-Discovery: {e}")
        
        return agent_sources
    
    def _process_sources(
        self,
        sources: List[SourceInfo],
        query: MineQuery
    ) -> List[SourceInfo]:
        """Verarbeitet und rankt entdeckte Quellen"""
        # Remove duplicates
        unique_sources = {}
        for source in sources:
            if source.url not in unique_sources:
                unique_sources[source.url] = source
        
        # Rank sources
        ranked_sources = []
        for source in unique_sources.values():
            # Calculate relevance based on source type and query
            source.relevance_score = self._calculate_relevance(source, query)
            ranked_sources.append(source)
        
        # Sort by relevance
        ranked_sources.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Store in source manager
        for source in ranked_sources:
            self.source_manager.add_source(
                source.url,
                source.source_type,
                metadata={
                    'mine_name': query.mine_name,
                    'discovered_by': source.discovered_by,
                    'relevance_score': source.relevance_score
                }
            )
        
        return ranked_sources[:50]  # Return top 50 sources
    
    def _calculate_relevance(self, source: SourceInfo, query: MineQuery) -> float:
        """Berechnet Relevanz-Score für eine Quelle"""
        score = 0.5  # Base score
        
        # Source type scoring
        type_scores = {
            'government': 0.9,
            'official': 0.85,
            'technical_report': 0.8,
            'news': 0.6,
            'academic': 0.7,
            'industry': 0.65
        }
        score = type_scores.get(source.source_type, score)
        
        # URL contains mine name
        if query.mine_name.lower() in source.url.lower():
            score += 0.1
        
        # URL contains country/region
        if query.country and query.country.lower() in source.url.lower():
            score += 0.05
        if query.region and query.region.lower() in source.url.lower():
            score += 0.05
        
        return min(score, 1.0)
    
    def _determine_source_type(self, url: str) -> str:
        """Bestimmt den Typ einer Quelle basierend auf URL"""
        url_lower = url.lower()
        
        if any(gov in url_lower for gov in ['.gov', '.gc.ca', '.gouv']):
            return 'government'
        elif any(term in url_lower for term in ['official', 'corporate']):
            return 'official'
        elif any(term in url_lower for term in ['report', 'technical', 'pdf']):
            return 'technical_report'
        elif any(term in url_lower for term in ['news', 'article', 'press']):
            return 'news'
        elif any(term in url_lower for term in ['.edu', 'academic', 'journal']):
            return 'academic'
        elif any(term in url_lower for term in ['mining', 'industry']):
            return 'industry'
        else:
            return 'other'
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Prüft ob Cache noch gültig ist"""
        if 'timestamp' not in cached_data:
            return False
        
        age = (datetime.now() - cached_data['timestamp']).total_seconds()
        return age < 3600  # 1 hour cache
    
    def _report_status(self, message: str, callback):
        """Berichtet Status über Callback"""
        self.logger.info(message)
        if callback:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")