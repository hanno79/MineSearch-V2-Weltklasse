"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für dynamische Keyword-Generierung
"""

from typing import List, Dict, Set, Optional, Tuple, Any
import asyncio

from .models import KeywordSet
from .language_patterns import LanguagePatternManager
from .translator import KeywordTranslator
from .concept_mapper import ConceptMapper
from src.core.logger import get_logger

class DynamicKeywordGenerator:
    """Generiert dynamisch Keywords für Mining-Recherche in verschiedenen Sprachen"""
    
    def __init__(self, ai_agents=None):
        self.keyword_cache = {}
        self.language_manager = LanguagePatternManager()
        self.translator = KeywordTranslator(ai_agents)
        self.concept_mapper = ConceptMapper()
        self.logger = get_logger("agent.dynamic_keyword_generator", agent_type="keyword_generator")
        
    async def generate_keywords_for_search(self, country: str, region: str, 
                                         mine_name: str, fields: List[str],
                                         languages: List[str]) -> Dict[str, List[str]]:
        """
        Generiert Keywords für die Suche
        
        Dies ist DYNAMISCH - keine hardcodierten Listen!
        """
        all_keywords = {}
        
        # Phase 1: Basis-Keywords generieren
        base_keywords = await self._generate_base_keywords(
            country, region, mine_name, fields, languages
        )
        
        # Phase 2: Erweitere mit Kontext
        context_keywords = await self._generate_contextual_keywords(
            base_keywords, country, region, languages
        )
        
        # Phase 3: Generiere Variationen
        variations = self._generate_variations(context_keywords, languages)
        
        # Phase 4: Kombiniere intelligent
        combined_keywords = self._combine_keywords_intelligently(
            base_keywords, context_keywords, variations, mine_name
        )
        
        return combined_keywords
    
    async def _generate_base_keywords(self, country: str, region: str,
                                    mine_name: str, fields: List[str],
                                    languages: List[str]) -> Dict[str, List[str]]:
        """Generiert Basis-Keywords"""
        keywords = {}
        
        # ÄNDERUNG 17.06.2025: Nutze nur Englisch als Basis
        # Übersetzungen werden dynamisch generiert
        core_concepts = self.concept_mapper.core_concepts
        
        # Übersetze Konzepte für alle Sprachen
        self.logger.info("🌐 Generiere dynamische Keywords für alle Sprachen...")
        
        # Cache-Key für diese Anfrage
        cache_key = f"{country}_{region}_{'_'.join(languages)}"
        
        if cache_key in self.keyword_cache:
            self.logger.info("📦 Nutze gecachte Keywords")
            return self.keyword_cache[cache_key]
        
        # Übersetze alle Konzepte
        for concept_name, terms in core_concepts.items():
            translations = await self.translator.translate_with_ai(terms, languages, concept_name)
            
            # Generiere feldspezifische Keywords
            for field in fields:
                field_keywords = []
                
                # Nutze Konzept-Mapper
                concept = self.concept_mapper.get_concept_for_field(field)
                
                # Nutze Übersetzungen für alle Sprachen
                for lang in languages:
                    if lang in translations:
                        field_keywords.extend(translations[lang])
                    elif concept == concept_name and lang == 'en':
                        field_keywords.extend(terms)
                
                # Kombiniere mit Kontext
                enhanced_keywords = self._enhance_keywords_with_context(
                    field_keywords, country, region, mine_name
                )
                
                keywords[field] = field_keywords
                keywords[f"{field}_enhanced"] = enhanced_keywords
        
        # Cache Ergebnisse
        self.keyword_cache[cache_key] = keywords
        
        return keywords
    
    def _enhance_keywords_with_context(self, keywords: List[str], 
                                     country: str, region: str, 
                                     mine_name: str) -> List[str]:
        """Erweitert Keywords mit Kontext"""
        enhanced = []
        for kw in keywords:
            enhanced.extend([
                f"{country} {kw}",
                f"{region} {kw}",
                f"{mine_name} {kw}",
                f"{kw} {mine_name}"
            ])
        return enhanced
    
    async def _generate_contextual_keywords(self, base_keywords: Dict[str, List[str]],
                                          country: str, region: str,
                                          languages: List[str]) -> Dict[str, List[str]]:
        """Generiert kontextuelle Keywords basierend auf Land/Region"""
        contextual = {}
        
        # Hole Kontext-Muster
        context_patterns = self.language_manager.get_context_patterns()
        
        # Generiere kontextuelle Begriffe
        for pattern_type, patterns in context_patterns.items():
            contextual[pattern_type] = []
            
            for lang in languages:
                if lang in patterns:
                    for pattern in patterns[lang]:
                        # Fülle Muster mit Land/Region
                        contextual[pattern_type].extend([
                            pattern.format(country),
                            pattern.format(region)
                        ])
        
        # Ressourcentyp-spezifische Keywords
        resource_keywords = await self._generate_resource_keywords(country, languages)
        contextual.update(resource_keywords)
        
        return contextual
    
    async def _generate_resource_keywords(self, country: str, 
                                        languages: List[str]) -> Dict[str, List[str]]:
        """Generiert ressourcenspezifische Keywords basierend auf Land"""
        # Dynamische Generierung - würde aus Recherche oder API kommen
        # Statt hardcodierter Liste verwenden wir generische Mining-Ressourcen
        
        # Basis-Ressourcen die global relevant sind
        base_resources = [
            "mineral", "ore", "resource", "commodity",
            "metal", "stone", "material", "deposit"
        ]
        
        # Diese würden durch initiale Recherche für das spezifische Land
        # dynamisch ermittelt werden
        resources = base_resources
        
        # Hole Mining-Begriffe aus Language Manager
        generic_mining_terms = self.language_manager.generic_mining_terms
        
        keywords = {"resources": []}
        
        # Füge Basis-Ressourcen hinzu
        keywords["resources"].extend(resources)
        
        # Füge Übersetzungen hinzu wo vorhanden
        for term in resources:
            if term in generic_mining_terms:
                for lang in languages:
                    if lang in generic_mining_terms[term]:
                        keywords["resources"].append(generic_mining_terms[term][lang])
        
        return keywords
    
    def _generate_variations(self, keywords: Dict[str, List[str]], 
                           languages: List[str]) -> Dict[str, List[str]]:
        """Generiert Variationen von Keywords"""
        variations = {}
        abbreviations = self.language_manager.get_abbreviations()
        
        for category, kw_list in keywords.items():
            category_variations = []
            
            for keyword in kw_list:
                # Basis-Variationen
                category_variations.extend(self._generate_basic_variations(keyword))
                
                # Abkürzungen
                for full, abbrevs in abbreviations.items():
                    if full in keyword.lower():
                        for abbrev in abbrevs:
                            category_variations.append(
                                keyword.lower().replace(full, abbrev)
                            )
            
            variations[category] = list(set(category_variations))
        
        return variations
    
    def _generate_basic_variations(self, keyword: str) -> List[str]:
        """Generiert Basis-Variationen eines Keywords"""
        variations = [
            keyword,
            keyword.lower(),
            keyword.upper(),
            keyword.title()
        ]
        
        # Plural/Singular (vereinfacht)
        if keyword.endswith('y'):
            variations.append(keyword[:-1] + 'ies')
        elif keyword.endswith('s'):
            variations.append(keyword[:-1])
        else:
            variations.append(keyword + 's')
        
        # Mit/ohne Bindestriche
        if ' ' in keyword:
            variations.append(keyword.replace(' ', '-'))
            variations.append(keyword.replace(' ', '_'))
        
        return variations
    
    def _combine_keywords_intelligently(self, base: Dict[str, List[str]],
                                      contextual: Dict[str, List[str]],
                                      variations: Dict[str, List[str]],
                                      mine_name: str) -> Dict[str, List[str]]:
        """Kombiniert Keywords intelligent für optimale Suchergebnisse"""
        combined = {}
        
        # Erstelle Suchphrasen für verschiedene Zwecke
        search_purposes = {
            "broad_search": [],      # Breite Suche
            "specific_search": [],   # Spezifische Suche
            "document_search": [],   # Dokumentensuche
            "news_search": [],       # Nachrichtensuche
            "official_search": []    # Offizielle Quellen
        }
        
        # Breite Suche - einzelne Keywords
        all_keywords = []
        for kw_list in list(base.values()) + list(contextual.values()):
            all_keywords.extend(kw_list)
        
        search_purposes["broad_search"] = list(set(all_keywords))[:50]  # Top 50
        
        # Spezifische Suche - Kombinationen
        search_purposes["specific_search"] = self._generate_specific_searches(
            base, contextual
        )
        
        # Dokumentensuche
        search_purposes["document_search"] = self._generate_document_searches(
            base
        )
        
        # News-Suche
        search_purposes["news_search"] = self._generate_news_searches(
            mine_name
        )
        
        # Offizielle Quellen
        search_purposes["official_search"] = self._generate_official_searches(
            contextual
        )
        
        return search_purposes
    
    def _generate_specific_searches(self, base: Dict, contextual: Dict) -> List[str]:
        """Generiert spezifische Suchkombinationen"""
        specific_combinations = []
        
        # Kombiniere Basis mit Kontext
        for base_kw in base.get("mining_operation", [])[:5]:
            for ctx_kw in contextual.get("ministry_patterns", [])[:3]:
                specific_combinations.append(f'"{base_kw}" AND "{ctx_kw}"')
        
        return specific_combinations[:20]
    
    def _generate_document_searches(self, base: Dict) -> List[str]:
        """Generiert Dokumenten-Suchphrasen"""
        doc_keywords = ["report", "document", "PDF", "study", "assessment", "plan"]
        doc_searches = []
        
        for doc_kw in doc_keywords:
            for field_kw in base.get("betreiber", [])[:3]:
                doc_searches.append(f'"{field_kw}" filetype:pdf OR "{field_kw}" {doc_kw}')
        
        return doc_searches[:15]
    
    def _generate_news_searches(self, mine_name: str) -> List[str]:
        """Generiert News-Suchphrasen"""
        news_keywords = ["news", "announcement", "update", "press release"]
        news_searches = []
        
        for news_kw in news_keywords:
            news_searches.append(f'"{mine_name}" {news_kw}')
        
        return news_searches[:10]
    
    def _generate_official_searches(self, contextual: Dict) -> List[str]:
        """Generiert Suchphrasen für offizielle Quellen"""
        official_searches = []
        for pattern in contextual.get("ministry_patterns", [])[:5]:
            official_searches.append(f'"{pattern}" site:gov OR "{pattern}" site:gob')
        
        return official_searches[:10]
    
    async def generate_field_specific_keywords(self, field: str, country: str,
                                             language: str) -> KeywordSet:
        """Generiert feldspezifische Keywords für ein Land/Sprache"""
        # Diese Methode würde KI/ML nutzen um kontextspezifische Keywords zu generieren
        
        # Hole Konzept vom Mapper
        concept_map = self.concept_mapper.get_field_concept_map()
        concept = concept_map.get(field, "mining information")
        
        # Würde normalerweise eine Übersetzungs-API verwenden
        primary_terms = await self.translator.translate_terms([concept], language)
        
        # Generiere verwandte Begriffe
        related_terms = await self._generate_related_terms(concept, language)
        
        # Generiere Variationen
        variations = self._generate_term_variations(primary_terms + related_terms, language)
        
        # Kontext-Modifikatoren
        context_modifiers = await self._generate_context_modifiers(field, country, language)
        
        return KeywordSet(
            concept=concept,
            language=language,
            primary_terms=primary_terms,
            related_terms=related_terms,
            variations=variations,
            context_modifiers=context_modifiers
        )
    
    async def _generate_related_terms(self, concept: str, language: str) -> List[str]:
        """Generiert verwandte Begriffe für ein Konzept"""
        # ÄNDERUNG 22.06.2025: PARTIAL_IMPLEMENTATION
        # Vollständige Implementierung würde KI/Thesaurus verwenden
        # Momentan: Nutze Concept Mapper
        return self.concept_mapper.get_related_terms(concept)
    
    def _generate_term_variations(self, terms: List[str], language: str) -> List[str]:
        """Generiert Variationen von Begriffen"""
        variations = []
        
        for term in terms:
            # Basis-Variationen
            variations.extend([
                term,
                term.replace(' ', '-'),
                term.replace(' ', '_'),
                f'"{term}"'  # Exakte Phrase
            ])
            
            # Sprachspezifische Variationen
            patterns = self.language_manager.patterns
            if language in patterns["word_formation"]:
                lang_patterns = patterns["word_formation"][language]
                
                # Füge Suffixe hinzu
                for suffix in lang_patterns.get("common_suffixes", []):
                    if not term.endswith(suffix):
                        variations.append(term + suffix)
        
        return list(set(variations))
    
    async def _generate_context_modifiers(self, field: str, country: str,
                                        language: str) -> List[str]:
        """Generiert Kontext-Modifikatoren für Suchanfragen"""
        modifiers = []
        
        # Zeitliche Modifikatoren
        modifiers.extend(self.language_manager.get_time_modifiers(language))
        
        # Geografische Modifikatoren
        modifiers.extend([country, f"near:{country}", f"location:{country}"])
        
        # Feldspezifische Modifikatoren
        modifiers.extend(self.concept_mapper.get_field_modifiers(field))
        
        return modifiers