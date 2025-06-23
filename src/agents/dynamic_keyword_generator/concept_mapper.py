"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Konzept-Mapping und verwandte Begriffe
"""

from typing import List, Dict

class ConceptMapper:
    """Verwaltet Konzept-Mappings und verwandte Begriffe"""
    
    def __init__(self):
        self.core_concepts = self._initialize_core_concepts()
        self.field_to_concept = self._initialize_field_mapping()
        self.related_terms = self._initialize_related_terms()
        
    def _initialize_core_concepts(self) -> Dict[str, List[str]]:
        """Initialisiert Kern-Konzepte"""
        return {
            "mining_operation": ["mine", "mining", "extraction", "quarry", "pit"],
            "operator": ["operator", "owner", "company", "corporation", "enterprise"],
            "production": ["production", "output", "yield", "extraction rate", "capacity"],
            "environmental": ["environmental", "impact", "restoration", "rehabilitation", "contamination"],
            "financial": ["cost", "investment", "revenue", "expenditure", "budget"],
            "legal": ["permit", "license", "concession", "authorization", "compliance"],
            "technical": ["reserves", "resources", "grade", "tonnage", "recovery"],
            "safety": ["safety", "accident", "incident", "hazard", "risk"]
        }
    
    def _initialize_field_mapping(self) -> Dict[str, str]:
        """Initialisiert Feld-zu-Konzept Mapping"""
        return {
            "betreiber": "operator",
            "produktionsdaten": "production",
            "umweltauswirkungen": "environmental",
            "finanzdaten": "financial",
            "genehmigungen": "legal",
            "technische_daten": "technical",
            "sicherheit": "safety",
            "koordinaten": "location",
            "rohstofftyp": "commodity",
            "aktivitaetsstatus": "status",
            "sanierungskosten": "restoration"
        }
    
    def _initialize_related_terms(self) -> Dict[str, List[str]]:
        """Initialisiert verwandte Begriffe"""
        return {
            "mining operator": ["mining company", "mine owner", "concession holder"],
            "location coordinates": ["GPS location", "geographic position", "mine site"],
            "mineral commodity": ["ore type", "mineral resource", "extracted material"],
            "operational status": ["mine status", "production state", "activity level"],
            "restoration costs": ["closure costs", "rehabilitation expenses", "environmental bond"],
            "environmental impact": ["ecological effects", "pollution", "contamination"],
            "production data": ["output statistics", "extraction volume", "annual production"]
        }
    
    def get_concept_for_field(self, field: str) -> str:
        """Gibt das Konzept für ein Feld zurück"""
        return self.field_to_concept.get(field, "mining_operation")
    
    def get_field_concept_map(self) -> Dict[str, str]:
        """Gibt das komplette Feld-Konzept Mapping zurück"""
        concept_map = {
            "betreiber": "mining operator",
            "koordinaten": "location coordinates",
            "rohstofftyp": "mineral commodity",
            "aktivitaetsstatus": "operational status",
            "sanierungskosten": "restoration costs",
            "umweltauswirkungen": "environmental impact",
            "produktionsdaten": "production data"
        }
        return concept_map
    
    def get_related_terms(self, concept: str) -> List[str]:
        """Gibt verwandte Begriffe für ein Konzept zurück"""
        return self.related_terms.get(concept, [])
    
    def get_field_modifiers(self, field: str) -> List[str]:
        """Gibt feldspezifische Modifikatoren zurück"""
        field_modifiers = {
            "sanierungskosten": ["million", "budget", "financial"],
            "produktionsdaten": ["annual", "monthly", "tonnage"],
            "umweltauswirkungen": ["assessment", "report", "study"]
        }
        return field_modifiers.get(field, [])