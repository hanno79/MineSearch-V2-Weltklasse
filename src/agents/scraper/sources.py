"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Mining-Quellen und URLs für Scraper
"""

from typing import Dict, List
from urllib.parse import quote_plus

from ..enhanced_search import get_mining_domains


class MiningSourceManager:
    """Verwaltet Mining-spezifische Informationsquellen"""
    
    @staticmethod
    def get_mining_sources() -> Dict[str, List[str]]:
        """Erweiterte Liste von Mining-Informationsquellen"""
        mining_domains = get_mining_domains()
        
        return {
            'government': [
                'https://www.nrcan.gc.ca/mining-materials',
                'https://mern.gouv.qc.ca',
                'https://www.ontario.ca/page/mines-and-minerals',
                'https://www.gov.bc.ca/gov/content/industry/mineral-exploration-mining',
                'https://www.alberta.ca/energy-minerals.aspx',
                'https://www.saskatchewan.ca/business/agriculture-natural-resources-and-industry/mineral-exploration-and-mining',
                'https://www.gov.mb.ca/iem/mines/index.html'
            ],
            'industry': [
                f'https://{domain}' for domain in mining_domains[:15]
            ],
            'environmental': [
                'https://miningwatch.ca',
                'https://www.environmentaldefence.ca',
                'https://www.ecojustice.ca',
                'https://www.pembina.org'
            ],
            'financial': [
                'https://www.sedar.com',
                'https://www.sec.gov/edgar',
                'https://www.tsx.com',
                'https://ca.finance.yahoo.com'
            ],
            'technical': [
                'https://www.geologyontario.mndm.gov.on.ca',
                'https://sigeom.mines.gouv.qc.ca',
                'https://www.usgs.gov',
                'https://www.ga.gov.au'
            ]
        }
    
    @staticmethod
    def get_government_urls(country: str, region: str) -> Dict[str, List[str]]:
        """Government-spezifische URLs nach Land/Region"""
        gov_urls = {
            'Canada': [
                f"https://www.nrcan.gc.ca/search?q={quote_plus('{query}')}%s",
                f"https://www.canada.ca/en/services/environment/pollution-waste-management/managing-reducing-waste/sites-contaminated-federal-activities.html"
            ],
            'Quebec': [
                f"https://mern.gouv.qc.ca/en/search/?q={quote_plus('{query}')}%s",
                f"https://gestim.mines.gouv.qc.ca/"
            ],
            'Ontario': [
                f"https://www.ontario.ca/search/search-results?query={quote_plus('{query}')}%s",
                f"https://www.mndm.gov.on.ca/en/mines-and-minerals"
            ],
            'British Columbia': [
                f"https://www2.gov.bc.ca/gov/search?q={quote_plus('{query}')}%s",
                f"https://www.empr.gov.bc.ca/Mining"
            ],
            'Alberta': [
                f"https://www.alberta.ca/search-results.aspx?q={quote_plus('{query}')}%s",
                f"https://www.alberta.ca/energy-minerals.aspx"
            ]
        }
        
        # Suche nach Land/Region
        urls = []
        if country in gov_urls:
            urls.extend(gov_urls[country])
        if region in gov_urls:
            urls.extend(gov_urls[region])
        
        return urls
    
    @staticmethod
    def get_search_url(domain: str, query: str) -> str:
        """Konstruiert Such-URL für eine Domain"""
        if "mining.com" in domain:
            return f"https://{domain}/search/?q={quote_plus(query)}"
        elif "mindat.org" in domain:
            return f"https://{domain}/search.php?search={quote_plus(query)}"
        else:
            # Generische Suche
            return f"https://{domain}/search?q={quote_plus(query + ' mine')}"
    
    @staticmethod
    def get_registry_urls() -> Dict[str, Dict[str, str]]:
        """URLs für Mining-Registries"""
        return {
            'quebec': {
                'base_url': 'https://gestim.mines.gouv.qc.ca',
                'search_url': 'https://gestim.mines.gouv.qc.ca/fiche_titre.asp?nom_mine={query}',
                'name': 'GESTIM Quebec'
            },
            'ontario': {
                'base_url': 'https://www.ontario.ca/page/mining-claims',
                'search_url': 'https://www.ontario.ca/page/mining-claims',
                'name': 'CLAIMaps Ontario'
            },
            'british_columbia': {
                'base_url': 'https://www.mtonline.gov.bc.ca',
                'search_url': 'https://www.mtonline.gov.bc.ca/mtov/search',
                'name': 'Mineral Titles Online BC'
            }
        }
