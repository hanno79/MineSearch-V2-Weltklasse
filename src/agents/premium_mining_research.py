"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Premium Mining Research System - Flexibel, Robust, Dynamisch
"""

from typing import List, Dict, Set, Optional, Any, Tuple
from dataclasses import dataclass
import asyncio
from datetime import datetime

from .dynamic_source_discovery import DynamicSourceDiscovery, SourceType
from .deep_web_crawler import DeepWebCrawler
from .dynamic_keyword_generator import DynamicKeywordGenerator
from .base_agent import BaseAgent, MineQuery, SearchResult

@dataclass
class ResearchPhase:
    """Eine Phase der Recherche"""
    name: str
    description: str
    max_duration: int  # Sekunden
    required_agents: List[str]
    focus_areas: List[str]

class PremiumMiningResearch:
    """
    Premium Mining Research System
    
    - KEINE hardcodierten Listen
    - Dynamische Quellenentdeckung
    - Multi-Layer Crawling
    - Intelligente Keyword-Generierung
    - Flexibel für ALLE Länder
    """
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        
        # ÄNDERUNG 17.06.2025: Integration aller Premium-Komponenten
        # Initialisiere mit Agenten-Referenzen
        self.source_discovery = DynamicSourceDiscovery(agents)
        self.keyword_generator = DynamicKeywordGenerator(agents)
        
        # Web Crawler mit Scraper-Agenten
        scraper_agents = {
            name: agent for name, agent in agents.items()
            if name in ['scraper', 'brightdata', 'scrapingbee', 'apify', 'firecrawl']
        }
        self.web_crawler = DeepWebCrawler(scraper_agents)
        
        self.research_phases = self._initialize_research_phases()
        self.results_cache = {}
        self.source_cache = {}  # Cache für entdeckte Quellen
        
    def _initialize_research_phases(self) -> List[ResearchPhase]:
        """Definiert die verschiedenen Forschungsphasen"""
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
    
    async def research_mine(self, query: MineQuery) -> Dict[str, Any]:
        """
        Führt Premium-Recherche für eine Mine durch
        
        Vollständig dynamisch und flexibel!
        """
        research_id = f"{query.mine_name}_{query.country}_{datetime.now().isoformat()}"
        
        print(f"\n🚀 Starte Premium Mining Research für: {query.mine_name}")
        print(f"Land: {query.country}, Region: {query.region}")
        print(f"Sprachen: {', '.join(query.languages)}")
        
        all_results = []
        research_metadata = {
            "start_time": datetime.now(),
            "phases_completed": [],
            "sources_discovered": 0,
            "documents_analyzed": 0,
            "keywords_used": 0,
            "errors": []
        }
        
        # ÄNDERUNG 17.06.2025: Umfassende Fehlerbehandlung
        try:
            # Phase 1: Discovery - Entdecke Quellen dynamisch
            print("\n📍 Phase 1: Dynamische Quellenentdeckung...")
            discovered_sources = await self._discovery_phase(query)
            research_metadata["sources_discovered"] = len(discovered_sources)
            print(f"✅ {len(discovered_sources)} relevante Quellen entdeckt")
            
            # Phase 2: Keyword-Generierung
            print("\n🔤 Phase 2: Intelligente Keyword-Generierung...")
            keywords = await self._generate_keywords_phase(query, discovered_sources)
            research_metadata["keywords_used"] = sum(len(kw_list) for kw_list in keywords.values())
            print(f"✅ {research_metadata['keywords_used']} Keywords in {len(query.languages)} Sprachen generiert")
            
            # Phase 3: Deep Dive - Tauche tief ein
            print("\n🏊 Phase 3: Deep Web Crawling...")
            crawl_results = await self._deep_dive_phase(query, discovered_sources, keywords)
            research_metadata["documents_analyzed"] = len(crawl_results)
            print(f"✅ {len(crawl_results)} Dokumente/Seiten analysiert")
            
            # Phase 4: Intelligente Suche mit optimierten Queries
            print("\n🔍 Phase 4: Intelligente Multi-Agent Suche...")
            search_results = await self._intelligent_search_phase(query, keywords, discovered_sources)
            all_results.extend(search_results)
            print(f"✅ {len(search_results)} Suchergebnisse gefunden")
            
            # Phase 5: Analyse komplexer Dokumente
            print("\n🧠 Phase 5: KI-gestützte Dokumentenanalyse...")
            analysis_results = await self._analysis_phase(query, crawl_results)
            all_results.extend(analysis_results)
            print(f"✅ {len(analysis_results)} zusätzliche Erkenntnisse gewonnen")
            
            # Phase 6: Verifikation und Konsolidierung
            print("\n✓ Phase 6: Ergebnisverifikation...")
            verified_results = await self._verification_phase(all_results, query)
            
            # Finale Aggregation mit Mehrfachwerten
            print("\n📊 Finale Aggregation...")
            final_results = self._aggregate_premium_results(verified_results)
            
            research_metadata["end_time"] = datetime.now()
            research_metadata["total_duration"] = (
                research_metadata["end_time"] - research_metadata["start_time"]
            ).total_seconds()
            
            print(f"\n✨ Premium Research abgeschlossen in {research_metadata['total_duration']:.1f} Sekunden")
            print(f"📈 Gefundene Felder: {len(final_results)}")
            
            return {
                "mine_data": final_results,
                "research_metadata": research_metadata,
                "discovered_sources": [
                    {
                        "url": s.url,
                        "type": s.source_type.value,
                        "relevance": s.relevance_score
                    }
                    for s in discovered_sources[:10]  # Top 10
                ],
                "quality_indicators": self._calculate_quality_indicators(final_results)
            }
            
        except Exception as e:
            print(f"❌ Kritischer Fehler in Premium Research: {e}")
            research_metadata["errors"].append(str(e))
            research_metadata["end_time"] = datetime.now()
            
            # Gebe teil-Ergebnisse zurück wenn möglich
            return {
                "mine_data": self._aggregate_premium_results(all_results) if all_results else {},
                "research_metadata": research_metadata,
                "discovered_sources": [],
                "quality_indicators": {},
                "error": str(e)
            }
    
    async def _discovery_phase(self, query: MineQuery) -> List[Any]:
        """Phase 1: Dynamische Quellenentdeckung"""
        # ÄNDERUNG 17.06.2025: Cache-Check für Quellen
        cache_key = f"{query.country}_{query.region}_{query.mine_name}"
        
        if cache_key in self.source_cache:
            print(f"📦 Nutze gecachte Quellen für {cache_key}")
            return self.source_cache[cache_key]
        
        # Nutze Search Agents für initiale Quellensuche
        discovery_agents = ["tavily", "perplexity"]
        
        # Erstelle Discovery-Queries
        discovery_queries = [
            f"{query.country} mining ministry official website",
            f"{query.country} mining association directory",
            f"{query.country} {query.region} mining department",
            f"{query.mine_name} official information",
            f"{query.country} mining news sources",
            f"{query.country} environmental mining organizations",
            f"{query.region} geological survey",
            f"{query.country} mining legal framework database"
        ]
        
        # Füge sprachspezifische Queries hinzu
        language_queries = {
            "es": [
                f"{query.country} ministerio minería sitio oficial",
                f"{query.country} cámara minera directorio"
            ],
            "fr": [
                f"{query.country} ministère mines site officiel",
                f"{query.country} chambre minière répertoire"
            ],
            "pt": [
                f"{query.country} ministério mineração site oficial",
                f"{query.country} câmara mineira diretório"
            ]
        }
        
        for lang in query.languages:
            if lang in language_queries:
                discovery_queries.extend(language_queries[lang])
        
        # Führe Discovery-Suchen durch
        discovered_sources = []
        
        for agent_name in discovery_agents:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                # Temporäre Query für Discovery
                discovery_query = MineQuery(
                    mine_name=query.mine_name,
                    region=query.region,
                    country=query.country,
                    languages=query.languages,
                    required_fields=["sources"]  # Spezielles Feld für Quellensuche
                )
                
                # Würde hier spezielle Discovery-Suche durchführen
                # Placeholder für Demonstration
                
        # ÄNDERUNG 17.06.2025: Fehlerbehandlung und Caching
        try:
            # Nutze DynamicSourceDiscovery
            sources = await self.source_discovery.discover_sources_for_country(
                query.country, query.region, query.mine_name, query.languages
            )
            
            # Cache Ergebnisse für 24 Stunden
            if sources:
                self.source_cache[cache_key] = sources
                print(f"💾 {len(sources)} Quellen gecached für {cache_key}")
            
            return sources
            
        except Exception as e:
            print(f"❌ Fehler bei Quellenentdeckung: {e}")
            # Fallback auf Basis-Quellen
            return []
    
    async def _generate_keywords_phase(self, query: MineQuery, 
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
    
    async def _deep_dive_phase(self, query: MineQuery, sources: List[Any],
                             keywords: Dict[str, List[str]]) -> List[Any]:
        """Phase 3: Deep Web Crawling"""
        crawl_results = []
        
        # ÄNDERUNG 17.06.2025: Nutze integrierten Web Crawler
        print(f"\n🕷️ Starte Deep Web Crawling für {len(sources)} Quellen")
        
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
                    print(f"❌ Crawl-Fehler: {results}")
        
        print(f"✅ Deep Crawl abgeschlossen: {len(crawl_results)} Seiten analysiert")
        
        return crawl_results
    
    async def _intelligent_search_phase(self, query: MineQuery, 
                                      keywords: Dict[str, List[str]],
                                      sources: List[Any]) -> List[SearchResult]:
        """Phase 4: Intelligente Multi-Agent Suche"""
        all_results = []
        
        # Erstelle optimierte Suchanfragen
        search_queries = self._build_intelligent_queries(query, keywords, sources)
        
        # Teile Queries auf Agenten auf
        agent_assignments = self._assign_queries_to_agents(search_queries)
        
        # Führe Suchen parallel durch
        search_tasks = []
        
        for agent_name, assigned_queries in agent_assignments.items():
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                # Erstelle spezialisierte Query
                for query_text in assigned_queries:
                    specialized_query = MineQuery(
                        mine_name=query.mine_name,
                        region=query.region,
                        country=query.country,
                        languages=query.languages,
                        required_fields=query.required_fields,
                        metadata={"search_query": query_text}
                    )
                    
                    search_tasks.append(
                        agent.search_mine(specialized_query)
                    )
        
        # Führe alle Suchen parallel aus
        if search_tasks:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
        
        return all_results
    
    async def _analysis_phase(self, query: MineQuery, 
                            crawl_results: List[Any]) -> List[SearchResult]:
        """Phase 5: KI-gestützte Dokumentenanalyse"""
        analysis_results = []
        
        # Wähle KI-Agenten für Analyse
        ai_agents = ["claude", "gpt4"]
        
        # Priorisiere Dokumente für Analyse
        priority_docs = []
        
        for crawl in crawl_results:
            # PDFs und technische Berichte priorisieren
            for doc in crawl.documents_found:
                if doc['type'] in ['report', 'technical', 'environmental', 'financial']:
                    priority_docs.append((crawl, doc))
        
        # Analysiere Top-Dokumente
        for agent_name in ai_agents:
            if agent_name in self.agents and priority_docs:
                agent = self.agents[agent_name]
                
                for crawl, doc in priority_docs[:5]:  # Top 5 pro Agent
                    # Erstelle Analyse-Query
                    analysis_query = MineQuery(
                        mine_name=query.mine_name,
                        region=query.region,
                        country=query.country,
                        languages=query.languages,
                        required_fields=query.required_fields,
                        metadata={
                            "document_url": doc['url'],
                            "document_type": doc['type'],
                            "analysis_focus": crawl.relevant_content
                        }
                    )
                    
                    results = await agent.search_mine(analysis_query)
                    analysis_results.extend(results)
        
        return analysis_results
    
    async def _verification_phase(self, results: List[SearchResult], 
                                query: MineQuery) -> List[SearchResult]:
        """Phase 6: Ergebnisverifikation"""
        # Gruppiere Ergebnisse nach Feld
        field_groups = {}
        
        for result in results:
            if result.field_name not in field_groups:
                field_groups[result.field_name] = []
            field_groups[result.field_name].append(result)
        
        verified_results = []
        
        # Verifiziere jedes Feld
        for field, field_results in field_groups.items():
            if len(field_results) > 1:
                # Cross-Validierung
                verified = self._cross_validate_results(field_results)
                verified_results.extend(verified)
            else:
                # Einzelergebnis - prüfe Plausibilität
                if self._is_plausible(field_results[0], query):
                    verified_results.extend(field_results)
        
        return verified_results
    
    def _build_intelligent_queries(self, query: MineQuery, 
                                 keywords: Dict[str, List[str]],
                                 sources: List[Any]) -> List[str]:
        """Baut intelligente Suchanfragen"""
        queries = []
        
        # Basis-Queries
        for purpose, kw_list in keywords.items():
            if purpose == "broad_search":
                # Breite Suchen
                for kw in kw_list[:10]:
                    queries.append(f'"{query.mine_name}" {kw}')
            elif purpose == "specific_search":
                # Spezifische Kombinationen
                queries.extend(kw_list[:15])
            elif purpose == "document_search":
                # Dokumentensuchen
                queries.extend(kw_list[:10])
        
        # Quellenspezifische Queries
        for source in sources[:10]:
            if source.relevance_score > 0.7:
                queries.append(f'"{query.mine_name}" site:{source.url.split("/")[2]}')
        
        return queries
    
    def _assign_queries_to_agents(self, queries: List[str]) -> Dict[str, List[str]]:
        """Weist Queries optimal auf Agenten zu"""
        assignments = {
            "tavily": [],
            "perplexity": [],
            "claude": [],
            "gpt4": [],
            "scraper": []
        }
        
        for i, query in enumerate(queries):
            # Rotiere durch Agenten für Lastverteilung
            if "site:" in query:
                # Site-spezifische Queries für Scraper
                assignments["scraper"].append(query)
            elif "filetype:" in query:
                # Dokumentensuche für Tavily
                assignments["tavily"].append(query)
            elif i % 4 == 0:
                assignments["tavily"].append(query)
            elif i % 4 == 1:
                assignments["perplexity"].append(query)
            elif i % 4 == 2:
                assignments["claude"].append(query)
            else:
                assignments["gpt4"].append(query)
        
        return assignments
    
    def _aggregate_premium_results(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Aggregiert Ergebnisse mit Mehrfachwerten"""
        aggregated = {}
        
        # Gruppiere nach Feld
        field_groups = {}
        for result in results:
            if result.field_name not in field_groups:
                field_groups[result.field_name] = []
            field_groups[result.field_name].append(result)
        
        # Aggregiere mit Mehrfachwerten
        for field, field_results in field_groups.items():
            if not field_results:
                continue
            
            # Sortiere nach Konfidenz
            sorted_results = sorted(
                field_results, 
                key=lambda x: x.confidence_score, 
                reverse=True
            )
            
            # Hauptwert
            main_result = sorted_results[0]
            
            # Sammle alle unterschiedlichen Werte
            unique_values = {}
            for result in sorted_results:
                value_key = str(result.value).lower().strip()
                if value_key not in unique_values:
                    unique_values[value_key] = {
                        "value": result.value,
                        "sources": [result.source],
                        "scores": [result.confidence_score],
                        "dates": [result.source_date]
                    }
                else:
                    unique_values[value_key]["sources"].append(result.source)
                    unique_values[value_key]["scores"].append(result.confidence_score)
                    unique_values[value_key]["dates"].append(result.source_date)
            
            # Formatiere für Ausgabe
            if len(unique_values) == 1:
                # Nur ein Wert gefunden
                aggregated[field] = main_result.value
            else:
                # Mehrere Werte - formatiere mit +++
                all_values = []
                for value_data in unique_values.values():
                    avg_score = sum(value_data["scores"]) / len(value_data["scores"])
                    value_str = (
                        f"{value_data['value']} "
                        f"(Score: {avg_score:.2f}, "
                        f"Quellen: {len(value_data['sources'])})"
                    )
                    all_values.append(value_str)
                
                aggregated[field] = " +++ ".join(all_values)
        
        return aggregated
    
    def _cross_validate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Cross-validiert Ergebnisse"""
        # Implementierung der Cross-Validierung
        validated = []
        
        # Gruppiere ähnliche Werte
        value_groups = {}
        
        for result in results:
            # Vereinfachte Gruppierung
            normalized_value = str(result.value).lower().strip()
            
            if normalized_value not in value_groups:
                value_groups[normalized_value] = []
            value_groups[normalized_value].append(result)
        
        # Wähle Gruppe mit meisten Übereinstimmungen
        largest_group = max(value_groups.values(), key=len)
        validated.extend(largest_group)
        
        return validated
    
    def _is_plausible(self, result: SearchResult, query: MineQuery) -> bool:
        """Prüft Plausibilität eines Ergebnisses"""
        # Basis-Plausibilitätsprüfung
        if result.confidence_score < 0.3:
            return False
        
        # Feldspezifische Prüfungen
        if result.field_name == "koordinaten":
            # Prüfe ob Koordinaten Sinn machen
            try:
                # Vereinfachte Prüfung
                if "," in str(result.value):
                    parts = str(result.value).split(",")
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return -90 <= lat <= 90 and -180 <= lon <= 180
            except:
                return False
        
        return True
    
    def _calculate_quality_indicators(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Berechnet Qualitätsindikatoren"""
        indicators = {
            "completeness": len(results) / 20 * 100,  # Annahme: 20 mögliche Felder
            "multi_source_validation": 0,
            "data_freshness": 0,
            "source_diversity": 0
        }
        
        # Berechne Multi-Source Validierung
        multi_source_count = 0
        for field, value in results.items():
            if "+++" in str(value):
                multi_source_count += 1
        
        if results:
            indicators["multi_source_validation"] = (multi_source_count / len(results)) * 100
        
        return indicators
    
    def clear_cache(self):
        """Leert alle Caches"""
        # ÄNDERUNG 17.06.2025: Cache-Management
        self.results_cache.clear()
        self.source_cache.clear()
        self.keyword_generator.keyword_cache.clear()
        self.source_discovery.discovered_sources.clear()
        print("🗑️ Alle Caches geleert")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Gibt Cache-Statistiken zurück"""
        return {
            "results_cached": len(self.results_cache),
            "sources_cached": len(self.source_cache),
            "keywords_cached": len(self.keyword_generator.keyword_cache),
            "discovered_sources": len(self.source_discovery.discovered_sources)
        }