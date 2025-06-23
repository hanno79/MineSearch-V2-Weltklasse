"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: URL Builder für Firecrawl Agent
"""

from typing import List
from urllib.parse import quote_plus

from ..base_agent import MineQuery


class FirecrawlURLBuilder:
    """Erstellt URLs für Firecrawl-Suchen"""
    
    @staticmethod
    def create_seed_urls(query: MineQuery) -> List[str]:
        """Erstelle Seed-URLs für Crawling"""
        mine_name_encoded = quote_plus(query.mine_name)
        seed_urls = []
        
        # Google-Suche für offizielle Seiten
        seed_urls.append(
            f"https://www.google.com/search?q={mine_name_encoded}+mine+{quote_plus(query.region)}+official+site"
        )
        
        # Mining-spezifische Portale
        if query.country.lower() == "canada":
            seed_urls.extend([
                "https://www.nrcan.gc.ca/mining-materials",
                "https://www.sedar.com",
                "https://www.mining.ca"
            ])
            
            # Provinz-spezifische URLs
            if query.region.lower() in ["quebec", "québec"]:
                seed_urls.extend([
                    "https://mern.gouv.qc.ca",
                    "https://gestim.mines.gouv.qc.ca"
                ])
            elif query.region.lower() == "ontario":
                seed_urls.extend([
                    "https://www.ontario.ca/page/mining-and-minerals",
                    "https://www.mndm.gov.on.ca"
                ])
            elif query.region.lower() in ["british columbia", "bc"]:
                seed_urls.extend([
                    "https://www2.gov.bc.ca/gov/content/industry/mineral-exploration-mining",
                    "https://www.empr.gov.bc.ca"
                ])
        
        # Mining-Nachrichten und Datenbanken
        seed_urls.extend([
            "https://www.mining.com",
            "https://www.mindat.org",
            "https://www.infomine.com"
        ])
        
        return seed_urls
    
    @staticmethod
    def create_targeted_urls(query: MineQuery) -> List[str]:
        """Erstelle gezielte URLs basierend auf Minenname"""
        target_urls = []
        mine_name_encoded = quote_plus(query.mine_name)
        
        # Kanadische Regierungsdatenbanken
        if query.country.lower() == 'canada':
            target_urls.extend([
                f"https://www.nrcan.gc.ca/mining-materials/mining/canadian-minerals-yearbook/search?text={mine_name_encoded}",
                f"https://www.sedar.com/search/search_form_pc_en.htm?searchType=Company&searchText={mine_name_encoded}"
            ])
            
            if query.region.lower() in ['quebec', 'québec']:
                target_urls.append(
                    f"https://sigeom.mines.gouv.qc.ca/signet/classes/I1108_rechercheEntite?C_ETIQ_NOM_MINE={mine_name_encoded}"
                )
            elif query.region.lower() == 'ontario':
                target_urls.append(
                    f"https://www.ontario.ca/search/search-results?query={mine_name_encoded}+mine"
                )
        
        # Umwelt-Datenbanken
        target_urls.extend([
            f"https://www.canada.ca/en/services/environment/pollution-waste-management/contaminated-sites/search.html?search={mine_name_encoded}",
            f"https://www.ec.gc.ca/lcpe-cepa/default.asp?lang=En&n=5F213FA8-1&wsdoc=search&search={mine_name_encoded}"
        ])
        
        # Mining-Industrie Seiten
        target_urls.extend([
            f"https://www.mining.com/?s={mine_name_encoded}",
            f"https://www.northernminer.com/?s={mine_name_encoded}",
            f"https://www.miningweekly.com/search?q={mine_name_encoded}"
        ])
        
        return target_urls
    
    @staticmethod
    def create_crawl_config(query: MineQuery, url: str) -> dict:
        """Erstellt Crawl-Konfiguration für eine URL"""
        mine_pattern = query.mine_name.lower().replace(' ', '-')
        
        return {
            "url": url,
            "includePaths": [  # v1 verwendet includePaths
                f"/{mine_pattern}/",
                f"/{query.mine_name.lower().replace(' ', '_')}/",
                "/mining/", "/mine/", "/mineral/", "/resources/"
            ],
            "excludePaths": [  # v1 verwendet excludePaths
                "/privacy", "/terms", "/login", "/signup",
                "/subscribe", "/newsletter", "/contact"
            ],
            "maxDepth": 2,
            "limit": 50,
            "scrapeOptions": {  # v1 nutzt scrapeOptions
                "formats": ["markdown"],
                "onlyMainContent": True
            }
        }
