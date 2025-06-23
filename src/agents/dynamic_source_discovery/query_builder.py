"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Query Builder für dynamische Quellenentdeckung
"""

from typing import List, Dict
from .models import SourceType

class DiscoveryQueryBuilder:
    """Erstellt Suchanfragen zur Quellenentdeckung"""
    
    def __init__(self):
        self.translations = self._initialize_translations()
        
    def _initialize_translations(self) -> Dict[str, Dict[str, str]]:
        """Initialisiert Übersetzungen für Mining-bezogene Begriffe"""
        return {
            "mining": {
                "es": "minería",
                "fr": "exploitation minière",
                "pt": "mineração",
                "de": "Bergbau",
                "ru": "горнодобывающая",
                "zh": "采矿",
                "ar": "التعدين",
                "hi": "खनन",
                "id": "pertambangan",
                "sw": "uchimbaji madini"
            },
            "ministry": {
                "es": "ministerio",
                "fr": "ministère",
                "pt": "ministério",
                "de": "Ministerium",
                "ru": "министерство",
                "zh": "部",
                "ar": "وزارة",
                "hi": "मंत्रालय",
                "id": "kementerian",
                "sw": "wizara"
            },
            "resources": {
                "es": "recursos",
                "fr": "ressources",
                "pt": "recursos",
                "de": "Ressourcen",
                "ru": "ресурсы",
                "zh": "资源",
                "ar": "موارد",
                "hi": "संसाधन",
                "id": "sumber daya",
                "sw": "rasilimali"
            },
            "environmental": {
                "es": "ambiental",
                "fr": "environnemental",
                "pt": "ambiental",
                "de": "Umwelt",
                "ru": "экологический",
                "zh": "环境",
                "ar": "بيئي",
                "hi": "पर्यावरण",
                "id": "lingkungan",
                "sw": "mazingira"
            }
        }
    
    def build_discovery_queries(self, country: str, region: str, 
                               mine_name: str, languages: List[str]) -> List[str]:
        """Erstellt Suchanfragen zur Quellenentdeckung"""
        queries = []
        
        # Basis-Queries für verschiedene Quellentypen
        source_type_keywords = self._get_source_type_keywords(country, region, mine_name)
        
        # Erstelle Queries für jeden Typ
        for source_type, keywords in source_type_keywords.items():
            queries.extend(keywords)
        
        # Füge mehrsprachige Varianten hinzu
        if languages:
            multilingual_queries = self.create_multilingual_queries(
                country, region, mine_name, languages
            )
            queries.extend(multilingual_queries)
        
        return queries
    
    def _get_source_type_keywords(self, country: str, region: str, 
                                 mine_name: str) -> Dict[SourceType, List[str]]:
        """Gibt Keywords für verschiedene Quellentypen zurück"""
        return {
            SourceType.GOVERNMENT: [
                f"{country} mining ministry",
                f"{country} natural resources department",
                f"{country} mining regulation authority",
                f"{region} mining department",
                f"{country} geological survey"
            ],
            SourceType.INDUSTRY: [
                f"{country} mining association",
                f"{country} mining chamber",
                f"{country} mineral council",
                f"{region} mining companies"
            ],
            SourceType.NEWS: [
                f"{country} mining news",
                f"{region} mining newspaper",
                f"{mine_name} news articles",
                f"{country} mining journalism"
            ],
            SourceType.NGO: [
                f"{country} mining environmental groups",
                f"{country} mining watchdog",
                f"{region} conservation organizations mining",
                f"{country} indigenous rights mining"
            ],
            SourceType.LEGAL: [
                f"{country} mining law",
                f"{country} mining concessions database",
                f"{region} mining permits",
                f"{country} mining legal framework"
            ],
            SourceType.FINANCIAL: [
                f"{country} stock exchange mining",
                f"{country} mining investment reports",
                f"{mine_name} financial reports"
            ]
        }
    
    def create_multilingual_queries(self, country: str, region: str, 
                                   mine_name: str, languages: List[str]) -> List[str]:
        """Erstellt Suchanfragen in verschiedenen Sprachen"""
        queries = []
        
        for lang in languages:
            if lang in self.translations.get("mining", {}):
                mining_term = self.translations["mining"][lang]
                ministry_term = self.translations["ministry"].get(lang, "ministry")
                resources_term = self.translations["resources"].get(lang, "resources")
                
                queries.extend([
                    f"{country} {mining_term} {ministry_term}",
                    f"{country} {resources_term} {mining_term}",
                    f"{region} {mining_term}",
                    f'"{mine_name}" {mining_term}'
                ])
        
        return queries