"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Research Phase Management für Premium Mining Research
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from .models import ResearchPhase, ResearchMetadata, CrawlResult, SearchQuery
from ..base_agent import MineQuery, SearchResult
from ..dynamic_source_discovery import DynamicSourceDiscovery, SourceType
from ..dynamic_keyword_generator import DynamicKeywordGenerator
from ..deep_web_crawler import DeepWebCrawler
from src.core.logger import get_logger


class ResearchPhaseManager:
    """Verwaltet die verschiedenen Research-Phasen"""
    
    def __init__(self, agents: Dict[str, Any], config: Dict[str, Any]):
        self.agents = agents
        self.config = config
        self.logger = get_logger("research_phase_manager", agent_type="premium_research")
        
        # Initialisiere Komponenten
        self.source_discovery = DynamicSourceDiscovery(agents)
        self.keyword_generator = DynamicKeywordGenerator(agents)
        
        # Web Crawler mit Scraper-Agenten
        scraper_agents = {
            name: agent for name, agent in self.agents.items()
            if name in ['scraper', 'brightdata', 'scrapingbee', 'apify', 'firecrawl']
        }
        # ÄNDERUNG 23.06.2025: Korrektur der DeepWebCrawler Initialisierung
        self.web_crawler = DeepWebCrawler(
            name="premium_web_crawler",
            config={},
            scraper_agents=scraper_agents
        )
        
        # Cache für Quellen
        self.source_cache = {}
    
    def get_research_phases(self) -> List[ResearchPhase]:
        """Definiert Research-Phasen"""
        return [
            ResearchPhase(
                name="Discovery",
                description="Entdecke relevante Quellen für das Land/Region",
                max_duration=300,  # 5 Minuten
                required_agents=["tavily", "perplexity"],
                focus_areas=["source_discovery", "initial_scan"]
            ),
            ResearchPhase(
                name="Deep_Dive",
                description="Tauche tief in entdeckte Quellen ein",
                max_duration=600,  # 10 Minuten
                required_agents=["scraper", "brightdata", "firecrawl"],
                focus_areas=["document_extraction", "table_parsing", "deep_crawl"]
            ),
            ResearchPhase(
                name="Analysis",
                description="Analysiere und extrahiere spezifische Daten",
                max_duration=480,  # 8 Minuten
                required_agents=["claude", "gpt4"],
                focus_areas=["complex_analysis", "data_correlation", "validation"]
            ),
            ResearchPhase(
                name="Verification",
                description="Verifiziere und konsolidiere Ergebnisse",
                max_duration=240,  # 4 Minuten
                required_agents=["tavily", "claude"],
                focus_areas=["fact_checking", "cross_reference"]
            )
        ]
    
    async def execute_discovery_phase(self, query: MineQuery) -> List[Any]:
        """Phase 1: Dynamische Quellenentdeckung"""
        cache_key = f"{query.country}_{query.region}_{query.mine_name}"
        
        if cache_key in self.source_cache:
            self.logger.info(f"📦 Nutze gecachte Quellen für {cache_key}")
            return self.source_cache[cache_key]
        
        try:
            # Nutze DynamicSourceDiscovery
            sources = await self.source_discovery.discover_sources_for_country(
                query.country, query.region, query.mine_name, query.languages
            )
            
            # Cache Ergebnisse für 24 Stunden
            if sources:
                self.source_cache[cache_key] = sources
                self.logger.info(f"💾 {len(sources)} Quellen gecached für {cache_key}")
            
            return sources
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Quellenentdeckung: {e}")
            return []
    
    async def execute_keyword_generation(self, query: MineQuery, 
                                       sources: List[Any]) -> Dict[str, List[str]]:
        """Phase 2: Intelligente Keyword-Generierung"""
        keywords = await self.keyword_generator.generate_keywords_for_search(
            country=query.country,
            region=query.region,
            mine_name=query.mine_name,
            fields=query.required_fields,
            languages=query.languages
        )
        
        # Erweitere Keywords basierend auf entdeckten Quellen
        for source in sources[:10]:  # Top 10 Quellen
            if source.source_type == SourceType.GOVERNMENT:
                # Extrahiere spezifische Behördennamen aus URLs
                domain = source.url.split('/')[2]
                keywords.setdefault("official_sources", []).append(domain)
            elif source.source_type == SourceType.INDUSTRY:
                # Füge Industrieverbände hinzu
                keywords.setdefault("industry_orgs", []).append(source.url)
        
        return keywords
    
    async def execute_deep_dive(self, query: MineQuery, sources: List[Any],
                              keywords: Dict[str, List[str]]) -> List[CrawlResult]:
        """Phase 3: Deep Web Crawling"""
        crawl_results = []
        
        self.logger.info(f"\n🕷️ Starte Deep Web Crawling für {len(sources)} Quellen")
        
        # Priorisiere Quellen
        priority_sources = sorted(
            sources, 
            key=lambda x: (x.priority, x.relevance_score), 
            reverse=True
        )[:20]  # Top 20 Quellen
        
        # Crawle Quellen in Batches
        batch_size = 5
        for i in range(0, len(priority_sources), batch_size):
            batch = priority_sources[i:i+batch_size]
            batch_tasks = []
            
            for source in batch:
                # Nutze integrierten Crawler
                batch_tasks.append(
                    self.web_crawler.deep_crawl(
                        start_url=source.url,
                        max_depth=source.depth_to_explore,
                        mine_name=query.mine_name,
                        target_fields=query.required_fields
                    )
                )
            
            # Führe Batch parallel aus
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for results in batch_results:
                if isinstance(results, list):
                    crawl_results.extend(results)
                elif isinstance(results, Exception):
                    self.logger.error(f"❌ Crawl-Fehler: {results}")
        
        self.logger.info(f"✅ Deep Crawl abgeschlossen: {len(crawl_results)} Seiten analysiert")
        
        return crawl_results
    
    async def execute_intelligent_search(self, query: MineQuery, 
                                       keywords: Dict[str, List[str]],
                                       sources: List[Any], 
                                       query_optimizer) -> List[SearchResult]:
        """Phase 4: Intelligente Multi-Agent Suche"""
        all_results = []
        
        # Erstelle optimierte Suchanfragen
        search_queries = query_optimizer.build_intelligent_queries(query, keywords, sources)
        
        # Teile Queries auf Agenten auf
        agent_assignments = query_optimizer.assign_queries_to_agents(search_queries)
        
        # Führe Suchen parallel durch
        search_tasks = []
        
        for agent_name, assigned_queries in agent_assignments.items():
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                for search_query in assigned_queries:
                    # Erstelle temporäre MineQuery für Agent
                    temp_query = MineQuery(
                        mine_name=query.mine_name,
                        region=query.region,
                        country=query.country,
                        languages=[search_query.language],
                        required_fields=[search_query.target_field]
                    )
                    
                    search_tasks.append(
                        self._execute_agent_search(agent, temp_query, search_query)
                    )
        
        # Führe alle Suchen parallel aus
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        for result in search_results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"❌ Such-Fehler: {result}")
        
        return all_results
    
    async def execute_analysis_phase(self, query: MineQuery, 
                                   crawl_results: List[CrawlResult]) -> List[SearchResult]:
        """Phase 5: KI-gestützte Dokumentenanalyse"""
        analysis_results = []
        analysis_agents = ["claude", "gpt4"]
        
        # Gruppiere Crawl-Ergebnisse nach Sprache
        results_by_language = {}
        for result in crawl_results:
            lang = result.language or "unknown"
            results_by_language.setdefault(lang, []).append(result)
        
        for agent_name in analysis_agents:
            if agent_name not in self.agents:
                continue
            
            agent = self.agents[agent_name]
            
            for lang, lang_results in results_by_language.items():
                # Analysiere in Batches
                batch_size = 3
                for i in range(0, len(lang_results), batch_size):
                    batch = lang_results[i:i+batch_size]
                    
                    # Erstelle Analyse-Prompt
                    analysis_prompt = self._create_analysis_prompt(query, batch)
                    
                    try:
                        # Nutze Agent für Analyse
                        analysis_result = await agent.analyze_documents(
                            documents=batch,
                            prompt=analysis_prompt,
                            target_fields=query.required_fields
                        )
                        
                        if analysis_result:
                            analysis_results.append(analysis_result)
                    
                    except Exception as e:
                        self.logger.error(f"❌ Analyse-Fehler mit {agent_name}: {e}")
        
        return analysis_results
    
    async def execute_verification_phase(self, all_results: List[SearchResult], 
                                       query: MineQuery) -> List[SearchResult]:
        """Phase 6: Ergebnisverifikation"""
        # Gruppiere Ergebnisse nach Feld
        results_by_field = {}
        for result in all_results:
            field = result.field_name
            results_by_field.setdefault(field, []).append(result)
        
        verified_results = []
        verification_agents = ["tavily", "claude"]
        
        for field, field_results in results_by_field.items():
            if len(field_results) < 2:
                # Einzelergebnisse direkt übernehmen
                verified_results.extend(field_results)
                continue
            
            # Verifiziere widersprüchliche Werte
            unique_values = set(r.value for r in field_results)
            
            if len(unique_values) > 1:
                # Nutze Verification Agents
                for agent_name in verification_agents:
                    if agent_name in self.agents:
                        try:
                            verification_result = await self._verify_field_values(
                                self.agents[agent_name],
                                query,
                                field,
                                field_results
                            )
                            if verification_result:
                                verified_results.append(verification_result)
                                break
                        except Exception as e:
                            self.logger.error(f"❌ Verifikations-Fehler: {e}")
            else:
                # Konsistente Werte - wähle höchste Konfidenz
                best_result = max(field_results, key=lambda r: r.confidence_score)
                verified_results.append(best_result)
        
        return verified_results
    
    # Private Hilfsmethoden
    async def _execute_agent_search(self, agent, query: MineQuery, 
                                  search_query: SearchQuery) -> List[SearchResult]:
        """Führt Suche mit einzelnem Agent aus"""
        try:
            # Setze custom query text
            if hasattr(agent, 'set_custom_query'):
                agent.set_custom_query(search_query.query_text)
            
            # Führe Suche aus
            results = await agent.search(query)
            
            # Füge Metadaten hinzu
            for result in results:
                result.search_query = search_query.query_text
                result.target_field = search_query.target_field
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei Agent {agent.name}: {e}")
            return []
    
    def _create_analysis_prompt(self, query: MineQuery, 
                              crawl_results: List[CrawlResult]) -> str:
        """Erstellt Analyse-Prompt für KI-Agenten"""
        prompt = f"""Analysiere die folgenden Dokumente für die Mine '{query.mine_name}' 
in {query.country}, {query.region}.

Extrahiere spezifisch diese Felder:
{', '.join(query.required_fields)}

Dokumente:
"""
        for i, result in enumerate(crawl_results, 1):
            prompt += f"\n{i}. URL: {result.url}\n"
            prompt += f"   Inhalt: {result.content[:500]}...\n"
        
        prompt += "\nBitte extrahiere alle relevanten Informationen mit Quellenangaben."
        
        return prompt
    
    async def _verify_field_values(self, agent, query: MineQuery, 
                                 field: str, results: List[SearchResult]) -> Optional[SearchResult]:
        """Verifiziert widersprüchliche Feldwerte"""
        verification_prompt = f"""Verifiziere den korrekten Wert für '{field}' 
der Mine '{query.mine_name}' in {query.country}.

Gefundene Werte:
"""
        for result in results:
            verification_prompt += f"\n- {result.value} (Quelle: {result.source}, Konfidenz: {result.confidence_score})"
        
        verification_prompt += "\n\nWelcher Wert ist korrekt? Begründe deine Entscheidung."
        
        try:
            # Nutze Agent zur Verifikation
            verified_value = await agent.verify_information(
                prompt=verification_prompt,
                mine_name=query.mine_name,
                field=field
            )
            
            if verified_value:
                return SearchResult(
                    field_name=field,
                    value=verified_value,
                    source=f"Verified by {agent.name}",
                    confidence_score=0.95,
                    metadata={"verification_method": "ai_consensus"}
                )
        except Exception as e:
            self.logger.error(f"Verifikation fehlgeschlagen: {e}")
        
        return None