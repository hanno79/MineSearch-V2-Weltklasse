"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Such-Strategien und Dokumentmuster für Mining-Recherchen
"""

from typing import List, Dict


def create_geographic_constraints(region: str, country: str) -> str:
    """ÄNDERUNG 21.06.2025: Verbesserte geografische Einschränkungen - Fokus auf positive Verstärkung"""
    # WICHTIG: Viele Suchmaschinen ignorieren "-" Operator oder interpretieren ihn falsch
    # Besser: Positive geografische Verstärkung an den Anfang jeder Query
    
    constraints = []
    
    # 1. POSITIVE VERSTÄRKUNG - Betone explizit die gewünschte Region
    if region and country:
        constraints.extend([
            f'"{region}, {country}"',  # Exakte Phrase
            f'"{region}" "{country}"',   # Beide Begriffe müssen vorkommen
            f'located in {region}',      # Explizite Ortsangabe
            f'site:{country.lower()}'    # Länderspezifische Websites bevorzugen
        ])
    elif country:
        constraints.extend([
            f'"{country}"',
            f'located in {country}',
            f'site:{country.lower()}'
        ])
    
    # 2. NEGATIVE AUSSCHLÜSSE - Nur für kritische Verwechslungen
    # Verwende verschiedene Syntax-Varianten für bessere Kompatibilität
    critical_exclusions = {
        ("quebec", "canada"): [
            'NOT Greenland', 'NOT "Greenland"', '-Greenland',  # Alle Varianten
            'NOT Grönland', '-Grönland',
            'NOT Iceland', '-Iceland',
            'NOT Nunavut', '-Nunavut'
        ],
        ("canada", ""): [
            'NOT "United States"', '-USA',
            'NOT Greenland', '-Greenland'
        ],
        ("australia", ""): [
            'NOT "New Zealand"', '-"New Zealand"',
            'NOT Indonesia', '-Indonesia'
        ]
    }
    
    # Füge kritische Ausschlüsse hinzu
    key = (region.lower() if region else "", country.lower() if country else "")
    if key in critical_exclusions:
        constraints.extend(critical_exclusions[key])
    # Prüfe auch nur nach Land
    elif ("", country.lower() if country else "") in critical_exclusions:
        constraints.extend(critical_exclusions[("", country.lower())])
    
    # 3. REGIONALE MARKER für bessere Präzision
    regional_markers = {
        "quebec": ["QC", "Québec", "Province of Quebec"],
        "ontario": ["ON", "Province of Ontario"],
        "british columbia": ["BC", "British Columbia"],
        "alberta": ["AB", "Province of Alberta"],
        "western australia": ["WA", "Western Australia"],
        "new south wales": ["NSW", "New South Wales"],
        "queensland": ["QLD", "Queensland"],
        "bavaria": ["Bayern", "Bavaria Germany"],
        "nordrhein-westfalen": ["NRW", "North Rhine-Westphalia"]
    }
    
    if region and region.lower() in regional_markers:
        # Füge den ersten regionalen Marker hinzu
        constraints.append(f'"{regional_markers[region.lower()][0]}"')
    
    # Kombiniere alle Constraints
    constraint_string = " ".join(constraints)
    
    return constraint_string


def get_source_types() -> Dict[str, List[str]]:
    """Get different types of sources for comprehensive search"""
    return {
        "government": [
            "site:*.gov site:*.gc.ca site:*.gov.au site:*.gob.* site:*.gouv.*",
            "ministry mining", "department mining resources", "geological survey",
            "mining cadastre", "mining registry", "environmental agency"
        ],
        "mining_operators": [
            "mining company", "mine operator", "mining corporation",
            "annual report", "sustainability report", "technical report",
            "NI 43-101", "JORC report", "feasibility study"
        ],
        "regional_government": [
            "provincial mining", "state mining department", "regional mining office",
            "mining permits", "environmental permits", "mining licenses"
        ],
        "news_media": [
            "mining news", "mining journal", "mining magazine",
            "local news mine", "regional newspaper mine"
        ],
        "ngo_watchdogs": [
            "mining watch", "environmental justice", "community impact",
            "indigenous rights mining", "water pollution mine",
            "tailings dam failure", "mine closure"
        ],
        "academic_research": [
            "mining research", "university mining study", "mining thesis",
            "environmental impact assessment", "social impact mining",
            "mining engineering research"
        ],
        "industry_associations": [
            "mining association", "chamber of mines", "mining council",
            "mining federation", "prospectors developers"
        ],
        "financial_reports": [
            "mining stocks", "mining investment", "commodity prices",
            "mining finance", "resource estimate", "mining valuation"
        ],
        "technical_databases": [
            "mineral database", "geological database", "mining statistics",
            "production data", "reserve estimates", "mining maps"
        ],
        "environmental_monitoring": [
            "water quality monitoring", "air quality mine", "contamination assessment",
            "environmental compliance", "remediation plan", "closure plan"
        ]
    }


def get_document_search_patterns(mine_name: str, field_type: str) -> List[str]:
    """Generate document-specific search patterns"""
    patterns = []
    
    # PDF searches for different document types
    document_patterns = {
        "technical": [
            f'filetype:pdf "{mine_name}" technical report',
            f'filetype:pdf "{mine_name}" feasibility study',
            f'filetype:pdf "{mine_name}" NI 43-101',
            f'filetype:pdf "{mine_name}" JORC',
            f'filetype:pdf "{mine_name}" resource estimate'
        ],
        "environmental": [
            f'filetype:pdf "{mine_name}" environmental impact',
            f'filetype:pdf "{mine_name}" EIA assessment',
            f'filetype:pdf "{mine_name}" water management plan',
            f'filetype:pdf "{mine_name}" closure plan',
            f'filetype:pdf "{mine_name}" remediation'
        ],
        "financial": [
            f'filetype:pdf "{mine_name}" annual report',
            f'filetype:pdf "{mine_name}" financial statement',
            f'filetype:pdf "{mine_name}" investor presentation',
            f'filetype:xlsx "{mine_name}" production data',
            f'filetype:csv "{mine_name}" commodity prices'
        ],
        "regulatory": [
            f'filetype:pdf "{mine_name}" mining permit',
            f'filetype:pdf "{mine_name}" environmental permit',
            f'filetype:pdf "{mine_name}" compliance report',
            f'filetype:pdf "{mine_name}" inspection report'
        ],
        "community": [
            f'filetype:pdf "{mine_name}" community agreement',
            f'filetype:pdf "{mine_name}" social impact',
            f'filetype:pdf "{mine_name}" indigenous consultation',
            f'filetype:pdf "{mine_name}" public hearing'
        ]
    }
    
    # Get patterns based on field type
    if field_type in ["sanierungskosten", "remediation_costs", "closure_costs"]:
        patterns.extend(document_patterns["financial"])
        patterns.extend(document_patterns["environmental"])
    elif field_type in ["betreiber", "operator", "owner"]:
        patterns.extend(document_patterns["technical"])
        patterns.extend(document_patterns["regulatory"])
    elif field_type in ["umweltauswirkungen", "environmental_impact"]:
        patterns.extend(document_patterns["environmental"])
        patterns.extend(document_patterns["community"])
    else:
        # Use all patterns for comprehensive search
        for pattern_list in document_patterns.values():
            patterns.extend(pattern_list[:2])  # Top 2 from each category
    
    return patterns


def get_multilingual_queries(mine_name: str, country: str, field: str) -> List[str]:
    """Generate multilingual search queries based on country"""
    queries = []
    
    # Language mappings by country
    language_map = {
        "canada": ["en", "fr"],
        "mexico": ["es", "en"],
        "spain": ["es", "ca", "eu"],
        "peru": ["es", "qu"],
        "chile": ["es"],
        "brazil": ["pt"],
        "argentina": ["es"],
        "bolivia": ["es", "qu", "ay"],
        "germany": ["de", "en"],
        "france": ["fr"],
        "china": ["zh", "en"],
        "russia": ["ru", "en"],
        "south africa": ["en", "af", "zu"],
        "morocco": ["ar", "fr"],
        "algeria": ["ar", "fr"],
        "tunisia": ["ar", "fr"]
    }
    
    # Field translations
    field_translations = {
        "operator": {
            "es": ["operador", "empresa minera", "compañía"],
            "fr": ["exploitant", "société minière", "entreprise"],
            "pt": ["operador", "empresa mineradora", "companhia"],
            "de": ["Betreiber", "Bergbauunternehmen", "Firma"],
            "ru": ["оператор", "горнодобывающая компания"],
            "zh": ["运营商", "矿业公司"],
            "ar": ["المشغل", "شركة التعدين"]
        },
        "coordinates": {
            "es": ["coordenadas", "ubicación", "localización"],
            "fr": ["coordonnées", "emplacement", "localisation"],
            "pt": ["coordenadas", "localização", "posição"],
            "de": ["Koordinaten", "Standort", "Lage"],
            "ru": ["координаты", "местоположение"],
            "zh": ["坐标", "位置"],
            "ar": ["إحداثيات", "موقع"]
        },
        "production": {
            "es": ["producción", "extracción", "rendimiento"],
            "fr": ["production", "extraction", "rendement"],
            "pt": ["produção", "extração", "rendimento"],
            "de": ["Produktion", "Förderung", "Ertrag"],
            "ru": ["производство", "добыча"],
            "zh": ["生产", "产量"],
            "ar": ["إنتاج", "استخراج"]
        },
        "environmental": {
            "es": ["ambiental", "medio ambiente", "impacto ecológico"],
            "fr": ["environnemental", "environnement", "impact écologique"],
            "pt": ["ambiental", "meio ambiente", "impacto ecológico"],
            "de": ["Umwelt", "ökologisch", "Umweltauswirkungen"],
            "ru": ["экологический", "окружающая среда"],
            "zh": ["环境", "生态影响"],
            "ar": ["بيئي", "التأثير البيئي"]
        }
    }
    
    # Get languages for country
    languages = language_map.get(country.lower(), ["en"])
    
    # Generate queries for each language
    for lang in languages:
        if lang == "en":
            continue  # English queries already generated
            
        # Get field keywords in target language
        field_keywords = []
        for field_key, translations in field_translations.items():
            if field_key in field.lower() and lang in translations:
                field_keywords.extend(translations[lang])
        
        # Create queries with translated terms
        if field_keywords:
            for keyword in field_keywords[:2]:  # Top 2 translations
                queries.append(f'"{mine_name}" {keyword}')
    
    return queries