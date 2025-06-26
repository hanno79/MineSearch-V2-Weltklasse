"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Query Builder für Exa Search
"""

from typing import Dict, List, Any
from urllib.parse import urlparse
from ..base_agent import MineQuery
from ..enhanced_search import get_mining_search_queries, get_mining_domains
from .utils import normalize_domains_for_exa, extract_base_domain

class ExaQueryBuilder:
    """Erstellt semantische Suchanfragen für Exa"""
    
    def __init__(self):
        self.query_templates = self._initialize_query_templates()
        
    def _initialize_query_templates(self) -> Dict[str, str]:
        """Initialisiert Query-Templates"""
        return {
            'overview': "comprehensive information about {mine_name} mine in {region}, {country}",
            'operator': "{mine_name} mine operator owner company {country}",
            'coordinates': "{mine_name} mine GPS coordinates location {region}",
            'production': "{mine_name} mine production statistics annual output",
            'environmental': "{mine_name} mine environmental impact closure costs rehabilitation",
            'technical': "{mine_name} mine reserves resources geological data",
            'regulatory': "{mine_name} mine permits licenses compliance {country}",
            'recent_news': "{mine_name} mine latest news updates {year}",
            'historical': "{mine_name} mine history timeline development",
            'financial': "{mine_name} mine revenue costs investment financial data"
        }
    
    def create_semantic_queries(self, query: MineQuery) -> Dict[str, Dict[str, Any]]:
        """Erstellt semantische Suchanfragen für verschiedene Informationstypen"""
        search_queries = {}
        
        # Standard-Suchkonfiguration
        base_config = {
            "num_results": 20,
            "use_autoprompt": True,
            "start_crawl_date": "2020-01-01",
            "include_domains": self._get_priority_domains(query.country),
            "category": "company"
        }
        
        # Erstelle Queries für jedes Template
        for query_type, template in self.query_templates.items():
            search_queries[query_type] = {
                "query": template.format(
                    mine_name=query.mine_name,
                    region=query.region,
                    country=query.country,
                    year=2024
                ),
                **base_config
            }
        
        # Spezielle Queries für angeforderte Felder
        field_specific_queries = self._create_field_specific_queries(query)
        search_queries.update(field_specific_queries)
        
        return search_queries
    
    def create_mining_specific_queries(self, query: MineQuery) -> List[Dict[str, Any]]:
        """Erstellt Mining-spezifische Suchanfragen"""
        queries = []
        
        # Hole Mining-spezifische Suchbegriffe
        mining_queries = get_mining_search_queries(
            query.mine_name, 
            query.region, 
            query.country
        )
        
        mining_domains = get_mining_domains()
        
        # ÄNDERUNG 24.06.2025: Nutze neue Utility für Domain-Bereinigung
        cleaned_domains = normalize_domains_for_exa(mining_domains, max_domains=20)
        
        # Erstelle Queries für Top Mining-Suchbegriffe
        for idx, mining_query in enumerate(mining_queries[:10]):
            queries.append({
                "query": mining_query,
                "num_results": 15,
                "use_autoprompt": True,
                "include_domains": cleaned_domains,  # Top Mining-Domains (bereits bereinigt und limitiert)
                "category": "research"
            })
        
        return queries
    
    def _create_field_specific_queries(self, query: MineQuery) -> Dict[str, Dict[str, Any]]:
        """Erstellt feldspezifische Suchanfragen"""
        field_queries = {}
        
        field_mappings = {
            'betreiber': 'operator owner company',
            'koordinaten': 'GPS coordinates location latitude longitude',
            'aktivitaetsstatus': 'operational status active closed production',
            'sanierungskosten': 'closure costs rehabilitation bond environmental liability',
            'jahresproduktion': 'annual production output tonnage volume',
            'rohstofftyp': 'commodity minerals ore type extracted',
            'umweltauswirkungen': 'environmental impact assessment contamination',
            'genehmigungen': 'permits licenses concessions regulatory approval'
        }
        
        for field in query.required_fields:
            if field in field_mappings:
                field_queries[f'field_{field}'] = {
                    "query": f"{query.mine_name} mine {field_mappings[field]} {query.country}",
                    "num_results": 10,
                    "use_autoprompt": True,
                    "category": "research"
                }
        
        return field_queries
    
    def _get_priority_domains(self, country: str) -> List[str]:
        """Gibt prioritäre Domains für ein Land zurück"""
        # Basis Mining-Domains
        base_domains = get_mining_domains()[:10]
        
        # Länderspezifische Domains (würde normalerweise aus Datenbank kommen)
        country_domains = {
            "Canada": ["nrcan.gc.ca", "mining.ca", "miningwatch.ca"],
            "Australia": ["ga.gov.au", "minerals.org.au", "industry.gov.au"],
            "Chile": ["sernageomin.cl", "cochilco.cl", "consejominero.cl"],
            "Peru": ["minem.gob.pe", "ingemmet.gob.pe", "snmpe.org.pe"],
            "South Africa": ["dmr.gov.za", "mineralscouncil.org.za", "miningweekly.com"]
        }
        
        # Kombiniere Domains
        all_domains = base_domains + country_domains.get(country, [])
        
        # ÄNDERUNG 24.06.2025: Nutze normalize_domains_for_exa für konsistente Bereinigung
        return normalize_domains_for_exa(all_domains, max_domains=20)
    
