"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Query-Generierung für Mining-Informationen
"""

from typing import List, Optional
from datetime import datetime
from ...utils.text_normalization import get_mine_name_variants, get_french_search_terms
from .domain_manager import get_mining_domains, get_country_specific_domains
from .search_strategies import (
    get_source_types, 
    get_document_search_patterns,
    get_multilingual_queries,
    create_geographic_constraints
)


def get_mining_search_queries(mine_name: str, region: str = "", country: str = "", 
                           required_fields: Optional[List[str]] = None) -> list:
    """Generate comprehensive search queries for mining information"""
    
    # Get all name variants (with and without accents)
    name_variants = get_mine_name_variants(mine_name)
    
    queries = []
    
    # ÄNDERUNG 23.06.2025: Verstärkte geografische Einschränkungen
    geo_constraints = create_geographic_constraints(region, country)
    geo_context = f'"{region}" "{country}"' if region and country else ''
    
    # Geografische Ausschlüsse für bessere Ergebnisse
    exclusions = _get_geographic_exclusions(country)
    
    # 1. BASIC QUERIES - For each name variant mit geografischen Einschränkungen
    for name in name_variants[:3]:  # Use top 3 variants
        # English queries mit geografischen Einschränkungen und Ausschlüssen
        queries.extend([
            f'"{name}" mine operator owner company {geo_context} {geo_constraints} {exclusions}',
            f'"{name}" mining coordinates location GPS {geo_context} {geo_constraints} {exclusions}',
            f'"{name}" commodity mineral resource production {geo_context} {geo_constraints} {exclusions}',
            f'"{name}" status operational closure {geo_context} {geo_constraints} {exclusions}',
            f'"{name}" remediation costs environmental {geo_context} {geo_constraints} {exclusions}',
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
    
    # 6. DETAILED TECHNICAL QUERIES mit geografischen Einschränkungen
    queries.extend([
        f'"{main_name}" annual report {datetime.now().year - 1} {datetime.now().year} {geo_context} {geo_constraints}',
        f'"{main_name}" environmental impact assessment EIA {geo_context} {geo_constraints}',
        f'"{main_name}" feasibility study technical report {geo_context} {geo_constraints}',
        f'"{main_name}" NI 43-101 JORC resource estimate {geo_context} {geo_constraints}',
        f'"{main_name}" tailings dam waste management {geo_context} {geo_constraints}',
        f'"{main_name}" water usage environmental monitoring {geo_context} {geo_constraints}',
        f'"{main_name}" community relations social impact {geo_context} {geo_constraints}',
        f'"{main_name}" processing plant mill capacity {geo_context} {geo_constraints}',
    ])
    
    # 7. REGIONAL QUERIES with more variations und Ausschlüssen
    if region:
        region_variants = [region, region.lower(), region.upper()]
        for variant in region_variants[:2]:
            queries.extend([
                f'"{mine_name}" {variant} {country} mining operation {geo_constraints}',
                f'{variant} {country} mines "{mine_name}" production data {geo_constraints}',
                f'{variant} {country} mining registry "{mine_name}" {geo_constraints}',
                f'{variant} {country} mining department "{mine_name}" {geo_constraints}',
                f'"{mine_name}" {variant} {country} environmental report {geo_constraints}',
                f'"{mine_name}" {variant} {country} mining news {geo_constraints}',
            ])
    
    # 8. ACADEMIC AND RESEARCH QUERIES mit geografischen Einschränkungen
    queries.extend([
        f'site:scholar.google.com "{main_name}" mine {geo_context}',
        f'site:researchgate.net "{main_name}" mining {geo_context}',
        f'"{main_name}" thesis dissertation mining {geo_context} {geo_constraints}',
        f'"{main_name}" university research mining {geo_context} {geo_constraints}'
    ])
    
    # 9. FINANCIAL AND INVESTMENT QUERIES mit geografischen Einschränkungen
    queries.extend([
        f'"{main_name}" stock price mining investment {geo_context} {geo_constraints}',
        f'"{main_name}" market cap valuation mining {geo_context} {geo_constraints}',
        f'"{main_name}" investor presentation mining {geo_context} {geo_constraints}',
        f'"{main_name}" quarterly earnings mining {geo_context} {geo_constraints}'
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