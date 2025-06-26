"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenmodelle für Dynamic Source Discovery
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

class SourceType(Enum):
    """Verschiedene Quellentypen für Mining-Informationen"""
    GOVERNMENT = "government"  # Regierungsseiten
    INDUSTRY = "industry"  # Industrieverbände
    NEWS = "news"  # Nachrichtenportale
    NGO = "ngo"  # Umwelt- und Naturschutzorganisationen
    ACADEMIC = "academic"  # Universitäten und Forschung
    LEGAL = "legal"  # Rechtsdokumente, Konzessionen
    REGIONAL = "regional"  # Regionale Behörden
    COMMUNITY = "community"  # Lokale Gemeinden
    FINANCIAL = "financial"  # Börsen, Finanzberichte
    TECHNICAL = "technical"  # Technische Berichte, Gutachten
    ENVIRONMENTAL = "environmental"  # Umweltbehörden
    INDIGENOUS = "indigenous"  # Indigene Organisationen
    UNION = "union"  # Gewerkschaften
    INTERNATIONAL = "international"  # Internationale Organisationen

@dataclass
class DiscoveredSource:
    """Eine entdeckte Informationsquelle"""
    url: str
    source_type: SourceType
    relevance_score: float
    language: str
    keywords_found: List[str]
    depth_to_explore: int  # Wie tief soll gecrawlt werden
    priority: int
    discovered_by: str = "unknown"  # ÄNDERUNG 25.06.2025: Neues Attribut für Tracking