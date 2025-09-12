"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: URL-Builder für Firecrawl Mining-Searches
"""

from typing import List, Dict, Any
from urllib.parse import quote


class FirecrawlURLBuilder:
    """Builder für zielgerichtete Mining-URLs"""

    @staticmethod
    def build_target_urls(options: Dict[str, Any]) -> List[str]:
        """Baut zielgerichtete URLs für Mining-Informationen"""
        mine_name = options.get("mine_name", '')
        country = options.get("country", '')
        region = options.get("region", '')

        urls = []

        # Länderspezifische Domains - FIX 02.09.2025: None-safe .lower() calls
        country_lower = country.lower() if country else ""
        region_lower = region.lower() if region else ""

        if country_lower in ['kanada', 'canada']:
            if region_lower == 'quebec':
                urls.extend([
                    f"https://mern.gouv.qc.ca",
                    f"https://gestim.mines.gouv.qc.ca"
                ])
            urls.append("https://www.nrcan.gc.ca/mining")

        elif country_lower in ['australien', 'australia']:
            urls.extend([
                "https://www.ga.gov.au",
                "https://minedex.dmirs.wa.gov.au"
            ])

        elif country_lower in ['südafrika', 'south africa']:
            urls.extend([
                "https://www.dmre.gov.za",
                "https://www.mineralscouncil.org.za"
            ])

        elif country_lower in ['peru']:
            urls.extend([
                "https://www.minem.gob.pe",
                "https://www.ingemmet.gob.pe"
            ])

        elif country_lower in ['chile']:
            urls.extend([
                "https://www.sernageomin.cl",
                "https://www.cochilco.cl"
            ])

        # Allgemeine Mining-Seiten mit Suchparametern
        if mine_name:
            encoded_name = quote(mine_name)
            urls.extend([
                f"https://www.mining.com/search/?q={encoded_name}",
                f"https://www.infomine.com/search/mines/{encoded_name}",
                f"https://www.mining-technology.com/?s={encoded_name}",
                f"https://www.northernminer.com/?s={encoded_name}"
            ])

        # Mining-Datenbanken
        urls.extend([
            "https://mindat.org",
            "https://www.mineralprices.com",
            "https://mrdata.usgs.gov/mrds/"
        ])

        return urls

    @staticmethod
    def build_search_urls(mine_name: str, country: str = None, commodity: str = None) -> List[str]:
        """Erstellt Suchanfrage-URLs für verschiedene Mining-Portale"""
        urls = []
        encoded_name = quote(mine_name)

        # Basis-Suchmaschinen
        search_queries = [
            f"{mine_name} mine closure costs restoration",
            f"{mine_name} mining environmental liability ARO",
            f"{mine_name} mine coordinates location GPS",
            f"{mine_name} mine owner operator company"
        ]

        if country:
            search_queries.append(f"{mine_name} mine {country}")

        if commodity:
            search_queries.append(f"{mine_name} {commodity} mine production")

        # Google Scholar für technische Reports
        for query in search_queries[:2]:  # Limitiere auf 2 Queries
            encoded_query = quote(query)
            urls.append(f"https://scholar.google.com/scholar?q={encoded_query}")

        return urls

    @staticmethod
    def build_document_search_patterns(mine_name: str) -> List[str]:
        """Erstellt Suchmuster für PDF-Dokumente"""
        patterns = []

        # Verschiedene Namensschreibweisen
        name_variants = [
            mine_name,
            mine_name.replace(' ', '-'),
            mine_name.replace(' ', '_'),
            mine_name.lower(),
            mine_name.upper()
        ]

        # Dokumenttypen
        doc_types = [
            'NI-43-101',
            'technical-report',
            'closure-plan',
            'environmental-assessment',
            'feasibility-study',
            'resource-estimate'
        ]

        for variant in name_variants:
            for doc_type in doc_types:
                patterns.append(f"{variant}-{doc_type}.pdf")
                patterns.append(f"{doc_type}-{variant}.pdf")

        return patterns
