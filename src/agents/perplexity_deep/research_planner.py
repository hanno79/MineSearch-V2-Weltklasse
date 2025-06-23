"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Research Planning für Deep Research
"""

from typing import List, Dict, Any
from ..base_agent import MineQuery

class ResearchPlanner:
    """Plant und strukturiert Deep Research Prozess"""
    
    def __init__(self):
        self.phase_templates = self._initialize_phase_templates()
        
    def _initialize_phase_templates(self) -> Dict[str, List[str]]:
        """Initialisiert Vorlagen für Research-Phasen"""
        return {
            "initial_overview": [
                "What is {mine_name} mine in {country}?",
                "{mine_name} mine location coordinates {region}",
                "{mine_name} mine operator company owner"
            ],
            "operational_details": [
                "{mine_name} mine production data statistics",
                "{mine_name} mining operational status active closed",
                "{mine_name} mine annual production volume"
            ],
            "environmental_impact": [
                "{mine_name} mine environmental impact assessment",
                "{mine_name} mine contamination pollution issues",
                "{mine_name} mine restoration rehabilitation plans"
            ],
            "financial_data": [
                "{mine_name} mine revenue costs financial data",
                "{mine_name} mine investment budget expenditure",
                "{mine_name} mine economic impact {region}"
            ],
            "regulatory_compliance": [
                "{mine_name} mine permits licenses concessions",
                "{mine_name} mine regulatory compliance violations",
                "{mine_name} mine legal framework {country}"
            ]
        }
    
    def create_research_plan(self, query: MineQuery) -> Dict[str, Any]:
        """Erstellt einen strukturierten Research-Plan"""
        plan = {
            "mine_name": query.mine_name,
            "country": query.country,
            "region": query.region,
            "phases": [],
            "total_expected_sources": 100,
            "expected_iterations": 5
        }
        
        # Erstelle Phasen basierend auf angeforderten Feldern
        phases = self._determine_research_phases(query.required_fields)
        
        for idx, (phase_name, templates) in enumerate(phases):
            phase_queries = self._generate_phase_queries(
                templates, query.mine_name, query.country, query.region
            )
            
            plan["phases"].append({
                "phase_number": idx + 1,
                "focus_area": phase_name,
                "search_queries": phase_queries,
                "expected_sources": 20,
                "success_criteria": self._get_success_criteria(phase_name)
            })
        
        return plan
    
    def _determine_research_phases(self, required_fields: List[str]) -> List[tuple]:
        """Bestimmt welche Research-Phasen benötigt werden"""
        phases = []
        
        # Immer mit Overview starten
        phases.append(("initial_overview", self.phase_templates["initial_overview"]))
        
        # Füge relevante Phasen basierend auf Feldern hinzu
        field_to_phase = {
            "produktionsdaten": "operational_details",
            "umweltauswirkungen": "environmental_impact",
            "finanzdaten": "financial_data",
            "genehmigungen": "regulatory_compliance"
        }
        
        for field in required_fields:
            if field in field_to_phase:
                phase_name = field_to_phase[field]
                if phase_name in self.phase_templates:
                    phases.append((phase_name, self.phase_templates[phase_name]))
        
        return phases
    
    def _generate_phase_queries(self, templates: List[str], mine_name: str, 
                               country: str, region: str) -> List[str]:
        """Generiert Suchanfragen für eine Phase"""
        queries = []
        
        for template in templates:
            query = template.format(
                mine_name=mine_name,
                country=country,
                region=region
            )
            queries.append(query)
        
        return queries
    
    def _get_success_criteria(self, phase_name: str) -> Dict[str, Any]:
        """Definiert Erfolgskriterien für eine Phase"""
        criteria = {
            "initial_overview": {
                "min_sources": 5,
                "required_info": ["location", "operator", "basic_facts"],
                "confidence_threshold": 0.7
            },
            "operational_details": {
                "min_sources": 10,
                "required_info": ["production_volume", "status", "timeline"],
                "confidence_threshold": 0.8
            },
            "environmental_impact": {
                "min_sources": 8,
                "required_info": ["impact_assessment", "incidents", "restoration"],
                "confidence_threshold": 0.75
            },
            "financial_data": {
                "min_sources": 5,
                "required_info": ["revenue", "costs", "investments"],
                "confidence_threshold": 0.7
            },
            "regulatory_compliance": {
                "min_sources": 7,
                "required_info": ["permits", "compliance_status", "legal_issues"],
                "confidence_threshold": 0.8
            }
        }
        
        return criteria.get(phase_name, {
            "min_sources": 5,
            "required_info": [],
            "confidence_threshold": 0.7
        })