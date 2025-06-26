"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Verwaltung von Mining-spezifischen Domains und länderspezifischen Ressourcen
"""

from typing import List


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
            "ontario.ca",  # ÄNDERUNG 24.06.2025: Nur Basis-Domains ohne Pfade
            "gov.bc.ca",
            "gouv.qc.ca",
            "gov.mb.ca",
            "gov.sk.ca",
            "miningnorth.com",
            "oma.on.ca",
            "mining.ca",
            "cim.org"
        ],
        "australia": [
            "ga.gov.au",
            "industry.gov.au",  # ÄNDERUNG 24.06.2025: Nur Basis-Domains
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
            "blm.gov",  # ÄNDERUNG 24.06.2025: Nur Basis-Domains
            "msha.gov",
            "osmre.gov",
            "epa.gov",
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
            "gob.pe",  # ÄNDERUNG 24.06.2025: Nur Basis-Domains
            "ingemmet.gob.pe",
            "osinergmin.gob.pe",
            "oefa.gob.pe",
            "snmpe.org.pe"
        ],
        "brazil": [
            "gov.br",  # ÄNDERUNG 24.06.2025: Nur Basis-Domains
            "mme.gov.br",
            "ibram.org.br",
            "dnpm.gov.br"
        ],
        "south africa": [
            "dmr.gov.za",
            "mineralscouncil.org.za",
            "geoscience.org.za",
            "wits.ac.za"  # ÄNDERUNG 24.06.2025: Nur Basis-Domain
        ],
        "mexico": [
            "gob.mx",  # ÄNDERUNG 24.06.2025: Nur Basis-Domains
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