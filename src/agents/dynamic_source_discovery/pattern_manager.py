"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Muster und Kategorisierung für Quellentypen
"""

from typing import Dict, List
from .models import SourceType

class SourcePatternManager:
    """Verwaltet Muster zur Identifikation und Kategorisierung von Quellen"""
    
    def __init__(self):
        self.source_patterns = self._initialize_source_patterns()
        self.type_priorities = self._initialize_type_priorities()
        self.focus_areas = self._initialize_focus_areas()
        self.extraction_hints = self._initialize_extraction_hints()
        
    def _initialize_source_patterns(self) -> Dict[SourceType, List[str]]:
        """Initialisiert Muster zur Identifikation von Quellentypen"""
        return {
            SourceType.GOVERNMENT: [
                "gov", "gob", "gouv", "government", "ministry", "department",
                "ministerio", "ministère", "behörde", "amt"
            ],
            SourceType.INDUSTRY: [
                "mining", "minerals", "resources", "association", "council",
                "chamber", "federation", "instituto", "société"
            ],
            SourceType.NEWS: [
                "news", "journal", "times", "post", "gazette", "herald",
                "zeitung", "presse", "noticias", "nouvelles"
            ],
            SourceType.NGO: [
                "org", "ngo", "foundation", "watch", "alliance", "coalition",
                "environmental", "conservation", "protection"
            ],
            SourceType.ACADEMIC: [
                "university", "universidad", "université", "institute",
                "research", "académie", "wissenschaft"
            ],
            SourceType.LEGAL: [
                "law", "legal", "justice", "court", "tribunal",
                "derecho", "droit", "recht", "juridique"
            ],
            SourceType.REGIONAL: [
                "provincial", "state", "regional", "local", "municipal",
                "prefecture", "canton", "département"
            ],
            SourceType.FINANCIAL: [
                "stock", "exchange", "bourse", "bolsa", "finance",
                "investor", "securities", "commission"
            ]
        }
    
    def _initialize_type_priorities(self) -> Dict[SourceType, int]:
        """Initialisiert Basis-Prioritäten für Quellentypen"""
        return {
            SourceType.GOVERNMENT: 10,
            SourceType.LEGAL: 9,
            SourceType.INDUSTRY: 8,
            SourceType.FINANCIAL: 7,
            SourceType.REGIONAL: 7,
            SourceType.ACADEMIC: 6,
            SourceType.NGO: 5,
            SourceType.NEWS: 4,
            SourceType.COMMUNITY: 3
        }
    
    def _initialize_focus_areas(self) -> Dict[SourceType, List[str]]:
        """Initialisiert Fokus-Bereiche für jeden Quellentyp"""
        return {
            SourceType.GOVERNMENT: ["permits", "regulations", "statistics", "maps"],
            SourceType.INDUSTRY: ["production", "employees", "technology", "investments"],
            SourceType.NEWS: ["recent events", "accidents", "expansions", "closures"],
            SourceType.NGO: ["environmental impact", "community issues", "protests"],
            SourceType.LEGAL: ["licenses", "lawsuits", "compliance", "violations"],
            SourceType.FINANCIAL: ["revenue", "costs", "investments", "stock price"],
            SourceType.ACADEMIC: ["studies", "research", "geological data", "impact assessments"],
            SourceType.ENVIRONMENTAL: ["contamination", "restoration", "monitoring", "incidents"]
        }
    
    def _initialize_extraction_hints(self) -> Dict[SourceType, Dict[str, str]]:
        """Initialisiert Extraktions-Hinweise für Quellentypen"""
        return {
            SourceType.GOVERNMENT: {
                "structure": "often in tables or official documents",
                "formats": ["PDF", "databases", "maps"],
                "reliability": "high"
            },
            SourceType.NEWS: {
                "structure": "narrative text",
                "formats": ["articles", "interviews"],
                "reliability": "medium, needs verification"
            },
            SourceType.LEGAL: {
                "structure": "formal documents",
                "formats": ["PDF", "legal databases"],
                "reliability": "very high"
            }
        }
    
    def get_patterns_for_type(self, source_type: SourceType) -> List[str]:
        """Gibt Muster für einen Quellentyp zurück"""
        return self.source_patterns.get(source_type, [])
    
    def get_base_priority(self, source_type: SourceType) -> int:
        """Gibt Basis-Priorität für einen Quellentyp zurück"""
        return self.type_priorities.get(source_type, 5)
    
    def get_focus_areas(self, source_type: SourceType) -> List[str]:
        """Gibt Fokus-Bereiche für einen Quellentyp zurück"""
        return self.focus_areas.get(source_type, ["general information"])
    
    def get_extraction_hints(self, source_type: SourceType) -> Dict[str, str]:
        """Gibt Extraktions-Hinweise für einen Quellentyp zurück"""
        return self.extraction_hints.get(
            source_type, 
            {"structure": "varied", "reliability": "medium"}
        )
    
    def get_base_crawl_depth(self, source_type: SourceType) -> int:
        """Gibt Basis-Crawl-Tiefe für einen Quellentyp zurück"""
        base_depth = {
            SourceType.GOVERNMENT: 5,
            SourceType.INDUSTRY: 4,
            SourceType.NEWS: 2,
            SourceType.NGO: 3,
            SourceType.ACADEMIC: 3,
            SourceType.LEGAL: 4,
            SourceType.REGIONAL: 4,
            SourceType.FINANCIAL: 3
        }
        return base_depth.get(source_type, 2)