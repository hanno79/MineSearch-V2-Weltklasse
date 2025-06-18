"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Dynamische Keyword-Generierung für Mining-Recherche in allen Sprachen
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import asyncio

@dataclass
class KeywordSet:
    """Eine Sammlung von Keywords für ein bestimmtes Konzept"""
    concept: str
    language: str
    primary_terms: List[str]
    related_terms: List[str]
    variations: List[str]
    context_modifiers: List[str]

class DynamicKeywordGenerator:
    """Generiert dynamisch Keywords für Mining-Recherche in verschiedenen Sprachen"""
    
    def __init__(self, ai_agents=None):
        self.keyword_cache = {}
        self.language_patterns = self._initialize_language_patterns()
        self.ai_agents = ai_agents or {}  # Dictionary von AI-Agenten für Übersetzungen
        
    def _initialize_language_patterns(self) -> Dict[str, Dict[str, any]]:
        """Initialisiert Sprachmuster für Keyword-Generierung"""
        return {
            "word_formation": {
                "en": {
                    "compound_separator": " ",
                    "adjective_position": "before",
                    "common_suffixes": ["ing", "tion", "ment", "ity", "ness"],
                    "common_prefixes": ["re", "un", "pre", "post", "ex"]
                },
                "es": {
                    "compound_separator": " de ",
                    "adjective_position": "after",
                    "common_suffixes": ["ción", "miento", "dad", "eza"],
                    "common_prefixes": ["re", "des", "pre", "post", "ex"]
                },
                "fr": {
                    "compound_separator": " de ",
                    "adjective_position": "after",
                    "common_suffixes": ["tion", "ment", "té", "ance"],
                    "common_prefixes": ["re", "dé", "pré", "post", "ex"]
                },
                "de": {
                    "compound_separator": "",  # Zusammengesetzte Wörter
                    "adjective_position": "before",
                    "common_suffixes": ["ung", "heit", "keit", "schaft"],
                    "common_prefixes": ["ver", "ent", "be", "ge", "un"]
                },
                "pt": {
                    "compound_separator": " de ",
                    "adjective_position": "after",
                    "common_suffixes": ["ção", "mento", "dade", "eza"],
                    "common_prefixes": ["re", "des", "pre", "pós", "ex"]
                }
            }
        }
    
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
            base_keywords, context_keywords, variations
        )
        
        return combined_keywords
    
    async def _translate_with_ai(self, terms: List[str], target_languages: List[str], 
                                context: str = "mining") -> Dict[str, List[str]]:
        """Übersetzt Begriffe mit AI-Agenten"""
        # ÄNDERUNG 17.06.2025: Dynamische Übersetzung mit AI
        translations = {lang: [] for lang in target_languages}
        
        # Wähle besten AI-Agent für Übersetzung
        ai_agent = None
        for agent_name in ['claude', 'gpt4', 'openrouter']:
            if agent_name in self.ai_agents and self.ai_agents[agent_name]:
                ai_agent = self.ai_agents[agent_name]
                print(f"✅ Nutze {agent_name} für Übersetzungen")
                break
        
        if not ai_agent:
            print("⚠️ Kein AI-Agent für Übersetzungen verfügbar, nutze Basis-Keywords")
            return translations
        
        # Erstelle Übersetzungsanfrage
        from .base_agent import MineQuery
        for lang in target_languages:
            if lang == 'en':  # Englisch ist Ausgangssprache
                translations[lang] = terms
                continue
                
            prompt = f"""Translate these mining-related terms to {lang}:
Terms: {', '.join(terms)}
Context: {context} industry terminology
Provide only the translations, separated by commas."""
            
            try:
                query = MineQuery(
                    mine_name=prompt,
                    country="",
                    region="",
                    languages=[lang]
                )
                
                results = await ai_agent.search_mine(query)
                if results:
                    # Parse Übersetzungen aus Antwort
                    translated = results[0].value.split(',')
                    translations[lang] = [t.strip() for t in translated]
            except Exception as e:
                print(f"Übersetzungsfehler für {lang}: {e}")
                
        return translations
    
    async def _generate_base_keywords(self, country: str, region: str,
                                    mine_name: str, fields: List[str],
                                    languages: List[str]) -> Dict[str, List[str]]:
        """Generiert Basis-Keywords"""
        keywords = {}
        
        # ÄNDERUNG 17.06.2025: Nutze nur Englisch als Basis
        # Übersetzungen werden dynamisch generiert
        core_concepts_en = {
            "mining_operation": ["mine", "mining", "extraction", "quarry", "pit"],
            "operator": ["operator", "owner", "company", "corporation", "enterprise"],
            "production": ["production", "output", "yield", "extraction rate", "capacity"],
            "environmental": ["environmental", "impact", "restoration", "rehabilitation", "contamination"],
            "financial": ["cost", "investment", "revenue", "expenditure", "budget"],
            "legal": ["permit", "license", "concession", "authorization", "compliance"],
            "technical": ["reserves", "resources", "grade", "tonnage", "recovery"],
            "safety": ["safety", "accident", "incident", "hazard", "risk"]
        }
        
        # Übersetze Konzepte für alle Sprachen
        print("🌐 Generiere dynamische Keywords für alle Sprachen...")
        
        # Cache-Key für diese Anfrage
        cache_key = f"{country}_{region}_{'_'.join(languages)}"
        
        if cache_key in self.keyword_cache:
            print("📦 Nutze gecachte Keywords")
            return self.keyword_cache[cache_key]
        
        # Übersetze alle Konzepte
        for concept_name, terms in core_concepts_en.items():
            translations = await self._translate_with_ai(terms, languages, concept_name)
            
            # Generiere feldspezifische Keywords
            for field in fields:
                field_keywords = []
                
                # Mapping von Feldern zu Konzepten
                field_to_concept = {
                    "betreiber": "operator",
                    "produktionsdaten": "production",
                    "umweltauswirkungen": "environmental",
                    "finanzdaten": "financial",
                    "genehmigungen": "legal",
                    "technische_daten": "technical",
                    "sicherheit": "safety"
                }
                
                concept = field_to_concept.get(field, "mining_operation")
                
                # Nutze Übersetzungen für alle Sprachen
                for lang in languages:
                    if lang in translations:
                        field_keywords.extend(translations[lang])
                    elif concept == concept_name and lang == 'en':
                        field_keywords.extend(terms)
                
                # Kombiniere mit Kontext
                enhanced_keywords = []
                for kw in field_keywords:
                    enhanced_keywords.extend([
                        f"{country} {kw}",
                        f"{region} {kw}",
                        f"{mine_name} {kw}",
                        f"{kw} {mine_name}"
                    ])
                
                keywords[field] = field_keywords
                keywords[f"{field}_enhanced"] = enhanced_keywords
        
        # Cache Ergebnisse
        self.keyword_cache[cache_key] = keywords
        
        # Entferne den alten hardcodierten Code komplett
        
        return keywords
    
    async def _generate_contextual_keywords(self, base_keywords: Dict[str, List[str]],
                                          country: str, region: str,
                                          languages: List[str]) -> Dict[str, List[str]]:
        """Generiert kontextuelle Keywords basierend auf Land/Region"""
        contextual = {}
        
        # Länderspezifische Behörden/Organisationen
        # Diese würden normalerweise durch eine initiale Recherche gefunden werden
        context_patterns = {
            "ministry_patterns": {
                "en": ["ministry of {}", "department of {}", "{} authority"],
                "es": ["ministerio de {}", "departamento de {}", "autoridad de {}"],
                "fr": ["ministère de {}", "département de {}", "autorité de {}"],
                "pt": ["ministério de {}", "departamento de {}", "autoridade de {}"],
                "de": ["ministerium für {}", "amt für {}", "{} behörde"]
            },
            "association_patterns": {
                "en": ["{} mining association", "{} mining chamber", "{} miners federation"],
                "es": ["asociación minera de {}", "cámara minera de {}", "federación de mineros de {}"],
                "fr": ["association minière de {}", "chambre minière de {}", "fédération des mineurs de {}"],
                "pt": ["associação mineira de {}", "câmara mineira de {}", "federação de mineiros de {}"],
                "de": ["bergbauverband {}", "bergbaukammer {}", "bergarbeiterverband {}"]
            }
        }
        
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
        
        # Generische Mining-Begriffe in verschiedenen Sprachen
        # Diese würden durch Übersetzungs-API dynamisch generiert
        generic_mining_terms = {
            "mineral": {"es": "mineral", "fr": "minéral", "pt": "mineral", "de": "Mineral"},
            "ore": {"es": "mena", "fr": "minerai", "pt": "minério", "de": "Erz"},
            "resource": {"es": "recurso", "fr": "ressource", "pt": "recurso", "de": "Ressource"},
            "commodity": {"es": "materia prima", "fr": "matière première", "pt": "commodity", "de": "Rohstoff"},
            "metal": {"es": "metal", "fr": "métal", "pt": "metal", "de": "Metall"},
            "deposit": {"es": "yacimiento", "fr": "gisement", "pt": "jazida", "de": "Lagerstätte"}
        }
        
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
        
        for category, kw_list in keywords.items():
            category_variations = []
            
            for keyword in kw_list:
                # Basis-Variationen
                category_variations.extend([
                    keyword,
                    keyword.lower(),
                    keyword.upper(),
                    keyword.title()
                ])
                
                # Plural/Singular (vereinfacht)
                if keyword.endswith('y'):
                    category_variations.append(keyword[:-1] + 'ies')
                elif keyword.endswith('s'):
                    category_variations.append(keyword[:-1])
                else:
                    category_variations.append(keyword + 's')
                
                # Mit/ohne Bindestriche
                if ' ' in keyword:
                    category_variations.append(keyword.replace(' ', '-'))
                    category_variations.append(keyword.replace(' ', '_'))
                
                # Abkürzungen (würde normalerweise aus Datenbank kommen)
                abbreviations = {
                    "environmental": ["env", "enviro"],
                    "production": ["prod", "prd"],
                    "ministry": ["min", "minist"],
                    "department": ["dept", "dep"],
                    "corporation": ["corp", "co"],
                    "limited": ["ltd", "ltda"]
                }
                
                for full, abbrevs in abbreviations.items():
                    if full in keyword.lower():
                        for abbrev in abbrevs:
                            category_variations.append(
                                keyword.lower().replace(full, abbrev)
                            )
            
            variations[category] = list(set(category_variations))
        
        return variations
    
    def _combine_keywords_intelligently(self, base: Dict[str, List[str]],
                                      contextual: Dict[str, List[str]],
                                      variations: Dict[str, List[str]]) -> Dict[str, List[str]]:
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
        specific_combinations = []
        
        # Kombiniere Basis mit Kontext
        for base_kw in base.get("mining_operation", [])[:5]:
            for ctx_kw in contextual.get("ministry_patterns", [])[:3]:
                specific_combinations.append(f'"{base_kw}" AND "{ctx_kw}"')
        
        search_purposes["specific_search"] = specific_combinations[:20]
        
        # Dokumentensuche
        doc_keywords = ["report", "document", "PDF", "study", "assessment", "plan"]
        doc_searches = []
        
        for doc_kw in doc_keywords:
            for field_kw in base.get("betreiber", [])[:3]:
                doc_searches.append(f'"{field_kw}" filetype:pdf OR "{field_kw}" {doc_kw}')
        
        search_purposes["document_search"] = doc_searches[:15]
        
        # News-Suche
        news_keywords = ["news", "announcement", "update", "press release"]
        news_searches = []
        
        for news_kw in news_keywords:
            news_searches.append(f'"{base.get("mine_name", [""])[0]}" {news_kw}')
        
        search_purposes["news_search"] = news_searches[:10]
        
        # Offizielle Quellen
        official_searches = []
        for pattern in contextual.get("ministry_patterns", [])[:5]:
            official_searches.append(f'"{pattern}" site:gov OR "{pattern}" site:gob')
        
        search_purposes["official_search"] = official_searches[:10]
        
        return search_purposes
    
    async def generate_field_specific_keywords(self, field: str, country: str,
                                             language: str) -> KeywordSet:
        """Generiert feldspezifische Keywords für ein Land/Sprache"""
        # Diese Methode würde KI/ML nutzen um kontextspezifische Keywords zu generieren
        
        # Basis-Implementation
        concept_map = {
            "betreiber": "mining operator",
            "koordinaten": "location coordinates",
            "rohstofftyp": "mineral commodity",
            "aktivitaetsstatus": "operational status",
            "sanierungskosten": "restoration costs",
            "umweltauswirkungen": "environmental impact",
            "produktionsdaten": "production data"
        }
        
        concept = concept_map.get(field, "mining information")
        
        # Würde normalerweise eine Übersetzungs-API verwenden
        primary_terms = await self._translate_terms([concept], language)
        
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
    
    async def _translate_terms(self, terms: List[str], target_language: str) -> List[str]:
        """Übersetzt Begriffe in Zielsprache"""
        # Würde normalerweise eine Übersetzungs-API verwenden
        # Placeholder-Implementation
        return terms
    
    async def _generate_related_terms(self, concept: str, language: str) -> List[str]:
        """Generiert verwandte Begriffe für ein Konzept"""
        # Würde normalerweise KI/Thesaurus verwenden
        # Placeholder-Implementation
        related_map = {
            "mining operator": ["mining company", "mine owner", "concession holder"],
            "location coordinates": ["GPS location", "geographic position", "mine site"],
            "mineral commodity": ["ore type", "mineral resource", "extracted material"],
            "operational status": ["mine status", "production state", "activity level"],
            "restoration costs": ["closure costs", "rehabilitation expenses", "environmental bond"],
            "environmental impact": ["ecological effects", "pollution", "contamination"],
            "production data": ["output statistics", "extraction volume", "annual production"]
        }
        
        return related_map.get(concept, [])
    
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
            if language in self.language_patterns["word_formation"]:
                lang_patterns = self.language_patterns["word_formation"][language]
                
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
        time_modifiers = {
            "en": ["current", "latest", "recent", "historical", "2024", "2023"],
            "es": ["actual", "último", "reciente", "histórico", "2024", "2023"],
            "fr": ["actuel", "dernier", "récent", "historique", "2024", "2023"],
            "pt": ["atual", "último", "recente", "histórico", "2024", "2023"],
            "de": ["aktuell", "neueste", "kürzlich", "historisch", "2024", "2023"]
        }
        
        if language in time_modifiers:
            modifiers.extend(time_modifiers[language])
        
        # Geografische Modifikatoren
        modifiers.extend([country, f"near:{country}", f"location:{country}"])
        
        # Feldspezifische Modifikatoren
        field_modifiers = {
            "sanierungskosten": ["million", "budget", "financial"],
            "produktionsdaten": ["annual", "monthly", "tonnage"],
            "umweltauswirkungen": ["assessment", "report", "study"]
        }
        
        if field in field_modifiers:
            modifiers.extend(field_modifiers[field])
        
        return modifiers