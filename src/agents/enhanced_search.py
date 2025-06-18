"""
Author: rahn
Datum: 18.06.2025
Version: 2.0
Beschreibung: Enhanced search queries for deep mining information retrieval with dynamic source discovery
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_normalization import get_mine_name_variants, get_french_search_terms
from typing import List, Dict, Set
from datetime import datetime

def get_mining_search_queries(mine_name: str, region: str = "", country: str = "", 
                           required_fields: List[str] = None) -> list:
    """Generate comprehensive search queries for mining information"""
    
    # Get all name variants (with and without accents)
    name_variants = get_mine_name_variants(mine_name)
    
    queries = []
    
    # 1. BASIC QUERIES - For each name variant
    for name in name_variants[:3]:  # Use top 3 variants
        # English queries
        queries.extend([
            f'"{name}" mine operator owner company',
            f'"{name}" mining coordinates location GPS',
            f'"{name}" commodity mineral resource production',
            f'"{name}" status operational closure',
            f'"{name}" remediation costs environmental',
        ])
    
    # 2. MULTILINGUAL QUERIES
    if country:
        for field in (required_fields or ["operator", "coordinates", "production"]):
            multilingual = get_multilingual_queries(name_variants[0], country, field)
            queries.extend(multilingual)
    
    # 3. SOURCE-TYPE SPECIFIC QUERIES
    source_types = get_source_types()
    main_name = name_variants[0]
    
    # Government sources
    for gov_pattern in source_types["government"][:2]:
        queries.append(f'{gov_pattern} "{main_name}"')
    
    # Mining operator sources
    for operator_term in source_types["mining_operators"][:3]:
        queries.append(f'"{main_name}" {operator_term}')
    
    # NGO and environmental sources
    for ngo_term in source_types["ngo_watchdogs"][:2]:
        queries.append(f'"{main_name}" {ngo_term}')
    
    # News and media
    for news_term in source_types["news_media"][:2]:
        queries.append(f'"{main_name}" {news_term} {region or country}')
    
    # 4. COUNTRY-SPECIFIC DOMAIN SEARCHES
    if country:
        country_domains = get_country_specific_domains(country)
        for domain in country_domains[:5]:  # Top 5 country-specific domains
            queries.append(f'site:{domain} "{main_name}"')
    
    # 5. DOCUMENT-SPECIFIC SEARCHES
    if required_fields:
        for field in required_fields[:3]:  # Focus on top fields
            doc_patterns = get_document_search_patterns(main_name, field)
            queries.extend(doc_patterns[:3])  # Top 3 document patterns per field
    
    # 6. DETAILED TECHNICAL QUERIES
    queries.extend([
        f'"{main_name}" annual report {datetime.now().year - 1} {datetime.now().year}',
        f'"{main_name}" environmental impact assessment EIA',
        f'"{main_name}" feasibility study technical report',
        f'"{main_name}" NI 43-101 JORC resource estimate',
        f'"{main_name}" tailings dam waste management',
        f'"{main_name}" water usage environmental monitoring',
        f'"{main_name}" community relations social impact',
        f'"{main_name}" processing plant mill capacity',
    ])
    
    # 7. REGIONAL QUERIES with more variations
    if region:
        region_variants = [region, region.lower(), region.upper()]
        for variant in region_variants[:2]:
            queries.extend([
                f'"{mine_name}" {variant} mining operation',
                f'{variant} mines "{mine_name}" production data',
                f'{variant} mining registry "{mine_name}"',
                f'{variant} mining department "{mine_name}"',
                f'"{mine_name}" {variant} environmental report',
                f'"{mine_name}" {variant} mining news',
            ])
    
    # 8. ACADEMIC AND RESEARCH QUERIES
    queries.extend([
        f'site:scholar.google.com "{main_name}" mine',
        f'site:researchgate.net "{main_name}" mining',
        f'"{main_name}" thesis dissertation mining',
        f'"{main_name}" university research mining'
    ])
    
    # 9. FINANCIAL AND INVESTMENT QUERIES
    queries.extend([
        f'"{main_name}" stock price mining investment',
        f'"{main_name}" market cap valuation mining',
        f'"{main_name}" investor presentation mining',
        f'"{main_name}" quarterly earnings mining'
    ])
    
    # 10. EXPANDED SITE-SPECIFIC SEARCHES
    all_domains = get_mining_domains() + (get_country_specific_domains(country) if country else [])
    
    # Prioritize domains based on query needs
    priority_domains = []
    if required_fields:
        if any(f in str(required_fields) for f in ["cost", "financial", "sanierung"]):
            priority_domains.extend(["bloomberg.com", "reuters.com", "marketwatch.com"])
        if any(f in str(required_fields) for f in ["environmental", "impact", "umwelt"]):
            priority_domains.extend(["earthworks.org", "miningwatch.ca", "ejatlas.org"])
    
    # Add priority domain searches
    for domain in priority_domains[:5]:
        for name in name_variants[:2]:
            queries.append(f'site:{domain} "{name}"')
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    
    return unique_queries


def get_mining_domains() -> list:
    """Get list of mining-specific domains to prioritize - dynamically expandable"""
    # Base domains that are globally relevant
    base_domains = [
        # Core mining information sites
        "mining.com",
        "mindat.org",
        "infomine.com",
        "mining-technology.com",
        "miningreview.com",
        "miningweekly.com",
        "northernminer.com",
        
        # Financial sites (global coverage)
        "bloomberg.com",
        "reuters.com",
        "marketwatch.com",
        "nasdaq.com",
        
        # Technical/open databases
        "geonames.org",
        "openstreetmap.org",
        "wikidata.org",
        
        # NGO and Environmental sites
        "miningwatch.ca",
        "earthworks.org",
        "ejatlas.org",
        "goodelectronics.org",
        
        # Industry associations
        "pdac.ca",
        "nma.org",
        "minerals.org.au",
        "icmm.com",
        
        # Academic and research
        "researchgate.net",
        "scholar.google.com",
        "sciencedirect.com",
        
        # Regional news
        "thenorthernminer.com",
        "australianmining.com.au",
        "canadianminingjournal.com",
        "miningnewsnorth.com"
    ]
    
    # This list can be dynamically expanded based on:
    # 1. Country/region specific sources discovered during search
    # 2. Language-specific mining portals
    # 3. User-provided additional domains
    # 4. Dynamically discovered sources from initial searches
    
    return base_domains


def get_country_specific_domains(country: str) -> List[str]:
    """Get country-specific domains for mining information"""
    country_domains = {
        "canada": [
            "nrcan.gc.ca",
            "ontario.ca/page/mines-and-minerals",
            "gov.bc.ca/gov/content/industry/mineral-exploration-mining",
            "gouv.qc.ca/en/mining",
            "gov.mb.ca/iem/mines",
            "gov.sk.ca/business/agriculture-natural-resources/mineral-exploration-and-mining",
            "miningnorth.com",
            "oma.on.ca",
            "mining.ca",
            "cim.org"
        ],
        "australia": [
            "ga.gov.au",
            "industry.gov.au/mining",
            "dmp.wa.gov.au",
            "resources.qld.gov.au",
            "energymining.sa.gov.au",
            "earthresources.vic.gov.au",
            "mrt.tas.gov.au",
            "minerals.org.au",
            "ausimm.com"
        ],
        "usa": [
            "usgs.gov",
            "blm.gov/programs/energy-and-minerals/mining-and-minerals",
            "msha.gov",
            "osmre.gov",
            "epa.gov/superfund",
            "nma.org",
            "smenet.org"
        ],
        "chile": [
            "sernageomin.cl",
            "cochilco.cl",
            "sonami.cl",
            "consejominero.cl",
            "minmineria.cl"
        ],
        "peru": [
            "gob.pe/minem",
            "ingemmet.gob.pe",
            "osinergmin.gob.pe",
            "oefa.gob.pe",
            "snmpe.org.pe"
        ],
        "brazil": [
            "gov.br/anm",
            "mme.gov.br",
            "ibram.org.br",
            "dnpm.gov.br"
        ],
        "south africa": [
            "dmr.gov.za",
            "mineralscouncil.org.za",
            "geoscience.org.za",
            "wits.ac.za/wmi"
        ],
        "mexico": [
            "gob.mx/se/acciones-y-programas/mineria",
            "sgm.gob.mx",
            "camimex.org.mx"
        ],
        "germany": [
            "bgr.bund.de",
            "lbeg.niedersachsen.de",
            "vbgu.de"
        ],
        "china": [
            "mnr.gov.cn",
            "cgs.gov.cn",
            "chinamining.com.cn"
        ]
    }
    
    return country_domains.get(country.lower(), [])


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