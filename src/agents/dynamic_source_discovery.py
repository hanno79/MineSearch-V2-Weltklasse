"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Dynamische Quellenentdeckung für Mining-Recherche - KEINE hardcodierten Listen
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import re

class SourceType(Enum):
    """Verschiedene Quellentypen für Mining-Informationen"""
    GOVERNMENT = "government"  # Regierungsseiten
    INDUSTRY = "industry"  # Industrieverbände
    NEWS = "news"  # Nachrichtenportale
    NGO = "ngo"  # Umwelt- und Naturschutzorganisationen
    ACADEMIC = "academic"  # Universitäten und Forschung
    LEGAL = "legal"  # Rechtsdokumente, Konzessionen
    REGIONAL = "regional"  # Regionale Behörden
    COMMUNITY = "community"  # Lokale Gemeinden
    FINANCIAL = "financial"  # Börsen, Finanzberichte
    TECHNICAL = "technical"  # Technische Berichte, Gutachten
    ENVIRONMENTAL = "environmental"  # Umweltbehörden
    INDIGENOUS = "indigenous"  # Indigene Organisationen
    UNION = "union"  # Gewerkschaften
    INTERNATIONAL = "international"  # Internationale Organisationen

@dataclass
class DiscoveredSource:
    """Eine entdeckte Informationsquelle"""
    url: str
    source_type: SourceType
    relevance_score: float
    language: str
    keywords_found: List[str]
    depth_to_explore: int  # Wie tief soll gecrawlt werden
    priority: int

class DynamicSourceDiscovery:
    """Entdeckt dynamisch relevante Quellen für jedes Land/Region"""
    
    def __init__(self, agents=None):
        self.discovered_sources = {}
        self.source_patterns = self._initialize_source_patterns()
        self.agents = agents or {}  # Dictionary von verfügbaren Agenten
        
    def _initialize_source_patterns(self) -> Dict[SourceType, List[str]]:
        """Initialisiert Muster zur Identifikation von Quellentypen"""
        return {
            SourceType.GOVERNMENT: [
                "gov", "gob", "gouv", "government", "ministry", "department",
                "ministerio", "ministère", "behörde", "amt"
            ],
            SourceType.INDUSTRY: [
                "mining", "minerals", "resources", "association", "council",
                "chamber", "federation", "instituto", "société"
            ],
            SourceType.NEWS: [
                "news", "journal", "times", "post", "gazette", "herald",
                "zeitung", "presse", "noticias", "nouvelles"
            ],
            SourceType.NGO: [
                "org", "ngo", "foundation", "watch", "alliance", "coalition",
                "environmental", "conservation", "protection"
            ],
            SourceType.ACADEMIC: [
                "university", "universidad", "université", "institute",
                "research", "académie", "wissenschaft"
            ],
            SourceType.LEGAL: [
                "law", "legal", "justice", "court", "tribunal",
                "derecho", "droit", "recht", "juridique"
            ],
            SourceType.REGIONAL: [
                "provincial", "state", "regional", "local", "municipal",
                "prefecture", "canton", "département"
            ],
            SourceType.FINANCIAL: [
                "stock", "exchange", "bourse", "bolsa", "finance",
                "investor", "securities", "commission"
            ]
        }
    
    async def discover_sources_for_country(self, country: str, region: str, 
                                         mine_name: str, languages: List[str]) -> List[DiscoveredSource]:
        """
        Entdeckt dynamisch relevante Quellen für ein Land/Region
        
        Dies ist der Kern der Flexibilität - KEINE hardcodierten Listen!
        """
        sources = []
        
        print(f"\n🔍 Starte dynamische Quellenentdeckung für {country}")
        
        # Phase 1: Erstelle Suchanfragen zur Quellenentdeckung
        discovery_queries = self._build_discovery_queries(country, region, mine_name, languages)
        print(f"📝 Erstellt {len(discovery_queries)} Suchanfragen")
        
        # Phase 2: Führe Quellensuche durch
        # Nutze verfügbare Search-Agenten (Tavily, Perplexity bevorzugt)
        search_agent = None
        for agent_name in ['tavily', 'perplexity', 'exa']:
            if agent_name in self.agents and self.agents[agent_name]:
                search_agent = self.agents[agent_name]
                print(f"✅ Nutze {agent_name} für Quellensuche")
                break
        
        initial_sources = await self._execute_discovery_search(discovery_queries, search_agent)
        print(f"🌐 {len(initial_sources)} initiale Quellen gefunden")
        
        # Phase 3: Analysiere und kategorisiere gefundene Quellen
        for source in initial_sources:
            categorized_source = self._categorize_source(source)
            if categorized_source:
                sources.append(categorized_source)
        
        print(f"📊 {len(sources)} relevante Quellen kategorisiert")
        
        # Phase 4: Erweitere mit spezialisierten Quellen
        specialized_sources = await self._find_specialized_sources(country, region, sources)
        sources.extend(specialized_sources)
        
        # Phase 5: Priorisiere und sortiere
        prioritized = self._prioritize_sources(sources)
        
        # Cache Ergebnisse für spätere Verwendung
        cache_key = f"{country}_{region}_{mine_name}"
        self.discovered_sources[cache_key] = prioritized
        
        print(f"✨ Quellenentdeckung abgeschlossen: {len(prioritized)} Quellen priorisiert")
        
        return prioritized
    
    def _build_discovery_queries(self, country: str, region: str, 
                               mine_name: str, languages: List[str]) -> List[str]:
        """Erstellt Suchanfragen zur Quellenentdeckung"""
        queries = []
        
        # Basis-Queries für verschiedene Quellentypen
        source_type_keywords = {
            SourceType.GOVERNMENT: [
                f"{country} mining ministry",
                f"{country} natural resources department",
                f"{country} mining regulation authority",
                f"{region} mining department",
                f"{country} geological survey"
            ],
            SourceType.INDUSTRY: [
                f"{country} mining association",
                f"{country} mining chamber",
                f"{country} mineral council",
                f"{region} mining companies"
            ],
            SourceType.NEWS: [
                f"{country} mining news",
                f"{region} mining newspaper",
                f"{mine_name} news articles",
                f"{country} mining journalism"
            ],
            SourceType.NGO: [
                f"{country} mining environmental groups",
                f"{country} mining watchdog",
                f"{region} conservation organizations mining",
                f"{country} indigenous rights mining"
            ],
            SourceType.LEGAL: [
                f"{country} mining law",
                f"{country} mining concessions database",
                f"{region} mining permits",
                f"{country} mining legal framework"
            ],
            SourceType.FINANCIAL: [
                f"{country} stock exchange mining",
                f"{country} mining investment reports",
                f"{mine_name} financial reports"
            ]
        }
        
        # Erstelle Queries für jeden Typ
        for source_type, keywords in source_type_keywords.items():
            queries.extend(keywords)
        
        # Füge mehrsprachige Varianten hinzu
        if languages:
            multilingual_queries = self._create_multilingual_queries(
                country, region, mine_name, languages
            )
            queries.extend(multilingual_queries)
        
        return queries
    
    def _create_multilingual_queries(self, country: str, region: str, 
                                   mine_name: str, languages: List[str]) -> List[str]:
        """Erstellt Suchanfragen in verschiedenen Sprachen"""
        queries = []
        
        # Übersetzungen für Mining-bezogene Begriffe
        translations = {
            "mining": {
                "es": "minería",
                "fr": "exploitation minière",
                "pt": "mineração",
                "de": "Bergbau",
                "ru": "горнодобывающая",
                "zh": "采矿",
                "ar": "التعدين",
                "hi": "खनन",
                "id": "pertambangan",
                "sw": "uchimbaji madini"
            },
            "ministry": {
                "es": "ministerio",
                "fr": "ministère",
                "pt": "ministério",
                "de": "Ministerium",
                "ru": "министерство",
                "zh": "部",
                "ar": "وزارة",
                "hi": "मंत्रालय",
                "id": "kementerian",
                "sw": "wizara"
            },
            "resources": {
                "es": "recursos",
                "fr": "ressources",
                "pt": "recursos",
                "de": "Ressourcen",
                "ru": "ресурсы",
                "zh": "资源",
                "ar": "موارد",
                "hi": "संसाधन",
                "id": "sumber daya",
                "sw": "rasilimali"
            },
            "environmental": {
                "es": "ambiental",
                "fr": "environnemental",
                "pt": "ambiental",
                "de": "Umwelt",
                "ru": "экологический",
                "zh": "环境",
                "ar": "بيئي",
                "hi": "पर्यावरण",
                "id": "lingkungan",
                "sw": "mazingira"
            }
        }
        
        for lang in languages:
            if lang in translations.get("mining", {}):
                mining_term = translations["mining"][lang]
                ministry_term = translations["ministry"].get(lang, "ministry")
                resources_term = translations["resources"].get(lang, "resources")
                
                queries.extend([
                    f"{country} {mining_term} {ministry_term}",
                    f"{country} {resources_term} {mining_term}",
                    f"{region} {mining_term}",
                    f'"{mine_name}" {mining_term}'
                ])
        
        return queries
    
    async def _execute_discovery_search(self, queries: List[str], search_agent=None) -> List[Dict[str, any]]:
        """
        Führt die initiale Quellensuche durch
        
        ÄNDERUNG 17.06.2025: Direkte Integration mit Search-Agenten
        """
        all_results = []
        
        if not search_agent:
            # Wenn kein Agent übergeben, erstelle temporären Suchauftrag
            # Dies wird vom Orchestrator übernommen
            print(f"🔍 Dynamische Quellensuche für {len(queries)} Anfragen...")
            return []
        
        # Führe Suchen mit übergebenem Agent durch
        for query in queries[:10]:  # Limitiere auf 10 Anfragen pro Phase
            try:
                # Erstelle temporäre MineQuery für Quellensuche
                from .base_agent import MineQuery
                temp_query = MineQuery(
                    mine_name=query,  # Nutze query als Suchbegriff
                    country="",
                    region="",
                    languages=[]
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
                print(f"Fehler bei Quellensuche: {e}")
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
    
    def _categorize_source(self, source: Dict[str, any]) -> Optional[DiscoveredSource]:
        """Kategorisiert eine gefundene Quelle"""
        url = source.get('url', '')
        title = source.get('title', '').lower()
        snippet = source.get('snippet', '').lower()
        
        # Bestimme Quellentyp
        source_type = self._determine_source_type(url, title, snippet)
        
        # Berechne Relevanz
        relevance_score = self._calculate_relevance(url, title, snippet)
        
        # Bestimme Sprache
        language = self._detect_language(title + " " + snippet)
        
        # Extrahiere gefundene Keywords
        keywords = self._extract_keywords(title + " " + snippet)
        
        if relevance_score > 0.3:  # Mindest-Relevanz
            return DiscoveredSource(
                url=url,
                source_type=source_type,
                relevance_score=relevance_score,
                language=language,
                keywords_found=keywords,
                depth_to_explore=self._determine_crawl_depth(source_type, relevance_score),
                priority=self._calculate_priority(source_type, relevance_score)
            )
        
        return None
    
    def _determine_source_type(self, url: str, title: str, snippet: str) -> SourceType:
        """Bestimmt den Typ einer Quelle"""
        combined_text = f"{url} {title} {snippet}".lower()
        
        # Prüfe gegen Muster
        for source_type, patterns in self.source_patterns.items():
            for pattern in patterns:
                if pattern in combined_text:
                    return source_type
        
        return SourceType.INDUSTRY  # Default
    
    def _calculate_relevance(self, url: str, title: str, snippet: str) -> float:
        """Berechnet Relevanz-Score einer Quelle"""
        score = 0.5  # Basis-Score
        
        # Erhöhe Score für offizielle Domains
        official_indicators = ['gov', 'gob', 'gouv', 'official', 'ministry']
        for indicator in official_indicators:
            if indicator in url.lower():
                score += 0.2
                break
        
        # Mining-spezifische Keywords
        mining_keywords = ['mining', 'mineral', 'mine', 'extraction', 'resources']
        keyword_count = sum(1 for kw in mining_keywords if kw in snippet.lower())
        score += keyword_count * 0.1
        
        # Domain-Endungen
        if url.endswith(('.gov', '.gob', '.gouv', '.edu', '.ac')):
            score += 0.2
        
        return min(score, 1.0)
    
    def _detect_language(self, text: str) -> str:
        """Einfache Spracherkennung"""
        # Vereinfachte Implementierung
        language_indicators = {
            'en': ['the', 'and', 'of', 'mining', 'resources'],
            'es': ['el', 'la', 'de', 'minería', 'recursos'],
            'fr': ['le', 'la', 'de', 'exploitation', 'ressources'],
            'pt': ['o', 'a', 'de', 'mineração', 'recursos'],
            'de': ['der', 'die', 'das', 'Bergbau', 'Ressourcen']
        }
        
        text_lower = text.lower()
        scores = {}
        
        for lang, indicators in language_indicators.items():
            score = sum(1 for ind in indicators if ind in text_lower)
            scores[lang] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'en'  # Default
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrahiert relevante Keywords aus Text"""
        # Vereinfachte Keyword-Extraktion
        mining_terms = [
            'mining', 'mine', 'mineral', 'extraction', 'resources',
            'copper', 'gold', 'silver', 'zinc', 'coal', 'iron',
            'environmental', 'permit', 'license', 'concession',
            'production', 'reserves', 'exploration'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for term in mining_terms:
            if term in text_lower:
                found_keywords.append(term)
        
        return found_keywords
    
    def _determine_crawl_depth(self, source_type: SourceType, relevance: float) -> int:
        """Bestimmt wie tief eine Quelle gecrawlt werden soll"""
        base_depth = {
            SourceType.GOVERNMENT: 5,
            SourceType.INDUSTRY: 4,
            SourceType.NEWS: 2,
            SourceType.NGO: 3,
            SourceType.ACADEMIC: 3,
            SourceType.LEGAL: 4,
            SourceType.REGIONAL: 4,
            SourceType.FINANCIAL: 3
        }
        
        depth = base_depth.get(source_type, 2)
        
        # Erhöhe Tiefe für hochrelevante Quellen
        if relevance > 0.8:
            depth += 2
        elif relevance > 0.6:
            depth += 1
        
        return min(depth, 7)  # Maximal 7 Ebenen
    
    def _calculate_priority(self, source_type: SourceType, relevance: float) -> int:
        """Berechnet Priorität einer Quelle"""
        type_priority = {
            SourceType.GOVERNMENT: 10,
            SourceType.LEGAL: 9,
            SourceType.INDUSTRY: 8,
            SourceType.FINANCIAL: 7,
            SourceType.REGIONAL: 7,
            SourceType.ACADEMIC: 6,
            SourceType.NGO: 5,
            SourceType.NEWS: 4,
            SourceType.COMMUNITY: 3
        }
        
        base_priority = type_priority.get(source_type, 5)
        
        # Adjustiere basierend auf Relevanz
        priority = base_priority + int(relevance * 5)
        
        return min(priority, 15)
    
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
    
    def get_search_strategy_for_source(self, source: DiscoveredSource) -> Dict[str, any]:
        """Gibt spezifische Suchstrategie für eine Quelle zurück"""
        return {
            "url": source.url,
            "depth": source.depth_to_explore,
            "keywords": source.keywords_found,
            "language": source.language,
            "focus_areas": self._get_focus_areas_for_type(source.source_type),
            "extraction_hints": self._get_extraction_hints(source.source_type)
        }
    
    def _get_focus_areas_for_type(self, source_type: SourceType) -> List[str]:
        """Gibt Fokus-Bereiche für einen Quellentyp zurück"""
        focus_map = {
            SourceType.GOVERNMENT: ["permits", "regulations", "statistics", "maps"],
            SourceType.INDUSTRY: ["production", "employees", "technology", "investments"],
            SourceType.NEWS: ["recent events", "accidents", "expansions", "closures"],
            SourceType.NGO: ["environmental impact", "community issues", "protests"],
            SourceType.LEGAL: ["licenses", "lawsuits", "compliance", "violations"],
            SourceType.FINANCIAL: ["revenue", "costs", "investments", "stock price"],
            SourceType.ACADEMIC: ["studies", "research", "geological data", "impact assessments"],
            SourceType.ENVIRONMENTAL: ["contamination", "restoration", "monitoring", "incidents"]
        }
        
        return focus_map.get(source_type, ["general information"])
    
    def _get_extraction_hints(self, source_type: SourceType) -> Dict[str, str]:
        """Gibt Hinweise zur Datenextraktion für einen Quellentyp"""
        hints_map = {
            SourceType.GOVERNMENT: {
                "structure": "often in tables or official documents",
                "formats": ["PDF", "databases", "maps"],
                "reliability": "high"
            },
            SourceType.NEWS: {
                "structure": "narrative text",
                "formats": ["articles", "interviews"],
                "reliability": "medium, needs verification"
            },
            SourceType.LEGAL: {
                "structure": "formal documents",
                "formats": ["PDF", "legal databases"],
                "reliability": "very high"
            }
        }
        
        return hints_map.get(source_type, {"structure": "varied", "reliability": "medium"})