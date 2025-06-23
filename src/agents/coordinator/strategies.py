"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Such-Strategien für Agent Coordinator
"""

from typing import Dict, Any, List, Optional


class SearchStrategyManager:
    """Verwaltet spezielle Suchstrategien für verschiedene Agenten und Felder"""
    
    @staticmethod
    def get_specialized_search_strategy(agent: str, field: str) -> Dict[str, Any]:
        """Gibt spezielle Suchstrategie für einen Agenten und ein Feld zurück"""
        
        strategies = {
            "tavily": {
                "koordinaten": {
                    "search_terms": ["coordinates", "latitude longitude", "GPS", "location"],
                    "sources": ["government databases", "mining registries"],
                    "filters": {"site_type": "government", "data_type": "coordinates"}
                },
                "betreiber": {
                    "search_terms": ["operator", "owner", "company", "betreiber"],
                    "sources": ["corporate websites", "regulatory filings"],
                    "filters": {"recent": True, "official": True}
                }
            },
            
            "claude": {
                "sanierungskosten": {
                    "search_terms": ["remediation costs", "closure costs", "environmental liability"],
                    "sources": ["technical reports", "financial statements"],
                    "analysis_type": "deep_financial",
                    "extract_tables": True
                },
                "umweltauswirkungen": {
                    "search_terms": ["environmental impact", "EIA", "environmental assessment"],
                    "sources": ["environmental reports", "regulatory documents"],
                    "analysis_type": "environmental_technical"
                }
            },
            
            "scraper": {
                "koordinaten": {
                    "target_elements": ["table", "coordinates-div", "location-data"],
                    "patterns": [r"\d+\.\d+[NS].*\d+\.\d+[EW]", r"lat.*lon"],
                    "structured_data": True
                },
                "produktionsdaten": {
                    "target_elements": ["production-table", "data-table", "statistics"],
                    "patterns": [r"\d+.*tonnes", r"production.*\d+"],
                    "table_extraction": True
                }
            },
            
            "deep_web_crawler": {
                "betreiber": {
                    "crawl_depth": 3,
                    "follow_links": ["about", "company", "corporate", "investor"],
                    "extract_from": ["management", "leadership", "board"]
                },
                "produktionsdaten": {
                    "crawl_depth": 2,
                    "follow_links": ["production", "operations", "technical"],
                    "data_patterns": ["annual production", "monthly output"]
                }
            },
            
            "browser": {
                "koordinaten": {
                    "wait_for": ["map-loaded", "coordinates-displayed"],
                    "javascript_extract": True,
                    "map_interaction": True
                },
                "aktivitaetsstatus": {
                    "form_interaction": True,
                    "search_fields": ["mine_name", "permit_number"],
                    "wait_for_results": True
                }
            },
            
            "document_finder": {
                "sanierungskosten": {
                    "document_types": ["closure plan", "ARO", "asset retirement"],
                    "file_formats": ["pdf", "xlsx", "docx"],
                    "sections": ["financial", "cost estimate", "liability"]
                },
                "umweltauswirkungen": {
                    "document_types": ["EIA", "environmental report", "impact study"],
                    "keywords": ["impact", "contamination", "remediation"],
                    "regulatory_focus": True
                }
            }
        }
        
        # Standard-Strategie falls keine spezielle definiert
        default_strategy = {
            "search_terms": [field],
            "sources": ["general"],
            "filters": {}
        }
        
        return strategies.get(agent, {}).get(field, default_strategy)
    
    @staticmethod
    def get_coordination_strategy(fields: List[str], available_agents: List[str]) -> Dict[str, Any]:
        """Erstellt Koordinations-Strategie für mehrere Felder und Agenten"""
        
        strategy = {
            "phases": [],
            "parallel_execution": True,
            "fallback_agents": {},
            "retry_policy": {
                "max_attempts": 2,
                "backoff_seconds": 5
            }
        }
        
        # Phase 1: Kritische Felder mit besten Agenten
        critical_fields = [f for f in fields if f in ["koordinaten", "betreiber", "aktivitaetsstatus", "sanierungskosten"]]
        if critical_fields:
            strategy["phases"].append({
                "phase": 1,
                "priority": "high",
                "fields": critical_fields,
                "timeout_seconds": 60,
                "concurrent_limit": 5
            })
        
        # Phase 2: Wichtige Felder
        important_fields = [f for f in fields if f in ["rohstofftyp", "produktionsdaten", "jahresproduktion", "flaeche"]]
        if important_fields:
            strategy["phases"].append({
                "phase": 2,
                "priority": "medium",
                "fields": important_fields,
                "timeout_seconds": 45,
                "concurrent_limit": 4
            })
        
        # Phase 3: Ergänzende Felder
        supplementary_fields = [f for f in fields if f not in critical_fields + important_fields]
        if supplementary_fields:
            strategy["phases"].append({
                "phase": 3,
                "priority": "low",
                "fields": supplementary_fields,
                "timeout_seconds": 30,
                "concurrent_limit": 3
            })
        
        return strategy
    
    @staticmethod
    def get_source_priority_strategy(query_type: str) -> List[str]:
        """Gibt priorisierte Quellen für verschiedene Abfragetypen zurück"""
        
        source_priorities = {
            "official_data": [
                "government_databases",
                "regulatory_filings",
                "sedar",
                "official_registries"
            ],
            "financial_data": [
                "annual_reports",
                "financial_statements",
                "investor_presentations",
                "sedar_filings"
            ],
            "technical_data": [
                "ni_43_101_reports",
                "technical_reports",
                "feasibility_studies",
                "resource_estimates"
            ],
            "current_status": [
                "news_articles",
                "press_releases",
                "company_updates",
                "social_media"
            ],
            "environmental_data": [
                "environmental_assessments",
                "closure_plans",
                "monitoring_reports",
                "regulatory_compliance"
            ]
        }
        
        return source_priorities.get(query_type, ["general_search"])
