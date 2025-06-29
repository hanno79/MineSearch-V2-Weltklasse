"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Query-Generierung für Mining-Informationen
"""

from typing import List, Optional
from datetime import datetime
from src.utils.text_normalization import get_mine_name_variants, get_french_search_terms
from .domain_manager import get_mining_domains, get_country_specific_domains
from .search_strategies import (
    get_source_types, 
    get_document_search_patterns,
    get_multilingual_queries,
    create_geographic_constraints
)


def get_mining_search_queries(mine_name: str, region: str = "", country: str = "", 
                           required_fields: Optional[List[str]] = None) -> list:
    """Generate comprehensive search queries for mining information
    
    ÄNDERUNG 24.06.2025: Optimiert für Tavily 400-Zeichen-Limit
    Alle Queries werden auf maximale Effizienz getrimmt
    """
    
    # Get all name variants (with and without accents)
    name_variants = get_mine_name_variants(mine_name)
    
    queries = []
    
    # ÄNDERUNG 24.06.2025: Kürzere geografische Kontexte
    # Verwende nur region ODER country, nicht beide
    geo_context = region if region and len(region) < len(country) else country
    
    # 1. BASIC QUERIES - Kompakt und fokussiert
    main_name = name_variants[0]
    
    # Nur die wichtigsten Felder, ohne Redundanz
    if required_fields:
        # Priorisiere angefragte Felder
        for field in required_fields[:3]:  # Max 3 Felder
            if field.lower() in ['operator', 'betreiber']:
                queries.append(f'"{main_name}" operator {geo_context}')
            elif field.lower() in ['coordinates', 'koordinaten', 'gps']:
                queries.append(f'"{main_name}" GPS coordinates')
            elif field.lower() in ['production', 'produktion']:
                queries.append(f'"{main_name}" production tons')
            elif field.lower() in ['closure', 'sanierung', 'remediation']:
                queries.append(f'"{main_name}" closure costs')
            elif field.lower() in ['status']:
                queries.append(f'"{main_name}" operational status')
    else:
        # Standard-Queries wenn keine Felder spezifiziert
        queries.extend([
            f'"{main_name}" mine operator',
            f'"{main_name}" GPS coordinates',
            f'"{main_name}" production',
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
    
    # 6. DETAILED TECHNICAL QUERIES - Ultra-kompakt
    # ÄNDERUNG 24.06.2025: Minimale technische Queries
    year = str(datetime.now().year)
    queries.extend([
        f'"{main_name}" annual report {year}',
        f'"{main_name}" environmental assessment',
        f'"{main_name}" NI 43-101',
    ])
    
    # 7. REGIONAL QUERIES - Nur wenn wirklich nötig
    # ÄNDERUNG 24.06.2025: Nur eine regionale Query
    if region and len(f'"{mine_name}" {region} mining') < 100:
        queries.append(f'"{mine_name}" {region} mining')
    
    # 8. ACADEMIC AND FINANCIAL - Kombiniert und gekürzt
    # ÄNDERUNG 24.06.2025: Nur essenzielle Queries
    if any(f in str(required_fields).lower() for f in ['financial', 'investor', 'cost']):
        queries.append(f'"{main_name}" financial report')
    
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
        if q not in seen and len(q) < 400:  # Strikte Längenbegrenzung
            seen.add(q)
            unique_queries.append(q)
    
    # ÄNDERUNG 24.06.2025: Finale Validierung
    # Logge zu lange Queries
    for q in queries:
        if len(q) >= 400:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Query zu lang und wurde entfernt ({len(q)} chars): {q[:50]}...")
    
    return unique_queries


def _get_geographic_exclusions(country: str) -> str:
    """
    ÄNDERUNG 23.06.2025: Erstellt geografische Ausschlüsse basierend auf Land
    um falsche Ergebnisse zu vermeiden (z.B. Africa für kanadische Minen)
    """
    exclusions = ""
    
    # Länder-spezifische Ausschlüsse
    if country.lower() in ["canada", "kanada"]:
        exclusions = '-Africa -"South Africa" -"West Africa" -"East Africa" -Zimbabwe -Ghana -Tanzania -"Mining Review Africa"'
    elif country.lower() in ["australia", "australien"]:
        exclusions = '-Africa -"South America" -Canada -USA -"United States"'
    elif country.lower() in ["usa", "united states", "amerika"]:
        exclusions = '-Africa -Australia -"South America" -Canada'
    elif country.lower() in ["chile", "peru", "brazil", "argentina"]:
        exclusions = '-Africa -Australia -Canada -USA -"United States" -Europe'
    
    # Allgemeine Ausschlüsse für alle Länder
    general_exclusions = '-"job posting" -"job opening" -"career opportunity" -recruitment'
    
    return f"{exclusions} {general_exclusions}"