"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Search Execution für Perplexity Deep Research
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..base_agent import MineQuery, SearchResult
from .models import ResearchPhase, DeepResearchResult
from src.core.logger import get_logger

class SearchExecutor:
    """Führt die Deep Research Suchen aus und verarbeitet Ergebnisse"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialisiert Regex-Muster für Datenextraktion"""
        return {
            'betreiber': [
                r'(?:owner|operator|operated by|owned by)[:\s]+([A-Za-z0-9\s\.\&\-,]+?)(?:\s*[,\.]|\s*\n)',
                r'([A-Z][A-Za-z0-9\s\.\&\-]+?)\s+(?:operates|owns|is the operator)',
                r'current operator[:\s]+([^\n,]+)'
            ],
            'koordinaten': [
                r'coordinates[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'GPS[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'located at[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'(\d+°\d+\'[\d\.]*\"[NS])[,\s]+(\d+°\d+\'[\d\.]*\"[EW])'
            ],
            'aktivitaetsstatus': [
                r'(?:operational\s+)?status[:\s]+(\w+)',
                r'mine is\s+currently\s+(\w+)',
                r'(?:production\s+)?status[:\s]+([^\n,]+)',
                r'currently\s+in\s+(\w+)\s+(?:status|phase)'
            ],
            'sanierungskosten': [
                r'(?:rehabilitation|closure|remediation)\s+(?:cost|bond)[s]?[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)',
                r'financial assurance[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)',
                r'environmental bond[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)',
                r'closure liability[:\s]+\$?([\d,\.]+\s*(?:million|M)?(?:\s+CAD)?)'
            ],
            'jahresproduktion': [
                r'annual production[:\s]+([^\n]+)',
                r'produces?\s+([\d,\.]+\s*(?:tonnes?|ounces?|oz|kg|tons?)\s*(?:per year|annually)?)',
                r'production capacity[:\s]+([^\n]+)',
                r'([\d,\.]+\s*(?:tonnes?|ounces?|oz)\s*(?:of\s+\w+\s+)?(?:per year|annually))'
            ],
            'rohstofftyp': [
                r'commodit(?:y|ies)[:\s]+([^\n,]+(?:,\s*[^\n,]+)*)',
                r'produces?\s+(?:primarily\s+)?([^\n,]+(?:,\s*[^\n,]+)*)',
                r'main minerals?[:\s]+([^\n,]+(?:,\s*[^\n,]+)*)',
                r'extract(?:s|ing)?\s+([^\n,]+(?:,\s*[^\n,]+)*)'
            ]
        }
    
    def parse_search_results(self, response: Dict[str, Any], query: MineQuery, 
                           source_tag: str) -> List[SearchResult]:
        """Parst Suchergebnisse aus API Response"""
        results = []
        
        if not response or 'choices' not in response:
            return results
        
        content = response['choices'][0]['message']['content']
        citations = response.get('citations', [])
        
        # Durchsuche Content mit Patterns
        for field_name, field_patterns in self.patterns.items():
            for pattern in field_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    value = self._extract_value(match)
                    
                    # Bereinige Wert
                    value = value.strip().rstrip('.,')
                    
                    # Finde relevante Citation
                    source_info = self._find_best_citation(field_name, citations)
                    
                    # Extrahiere Datum
                    source_date = self._extract_date(content, match)
                    
                    result = SearchResult(
                        mine_name=query.mine_name,
                        field_name=field_name,
                        value=value,
                        source=source_info['source'],
                        source_url=source_info['url'],
                        source_date=source_date,
                        confidence_score=source_info['confidence'],
                        agent_name="perplexity_deep_research",
                        timestamp=datetime.now(),
                        metadata={
                            'search_mode': 'deep_research',
                            'iteration': source_tag
                        }
                    )
                    
                    # Vermeide Duplikate
                    if not self._is_duplicate(result, results):
                        results.append(result)
                        self.logger.info(
                            f"Deep Research found: {field_name} = {value} "
                            f"(confidence: {source_info['confidence']:.2f})"
                        )
        
        return results
    
    def _extract_value(self, match) -> str:
        """Extrahiert Wert aus Regex-Match"""
        if len(match.groups()) > 1:  # Für Koordinaten
            return f"{match.group(1)}, {match.group(2)}"
        return match.group(1)
    
    def _find_best_citation(self, field_name: str, citations: List[Dict]) -> Dict[str, Any]:
        """Findet beste Citation für ein Feld"""
        source_info = {
            'source': "Perplexity Deep Research",
            'url': "",
            'confidence': 0.8
        }
        
        if citations:
            for citation in citations:
                if field_name in str(citation.get('snippet', '')).lower():
                    source_info['source'] = citation.get('title', source_info['source'])
                    source_info['url'] = citation.get('url', '')
                    source_info['confidence'] = 0.95
                    break
        
        return source_info
    
    def _extract_date(self, content: str, match) -> int:
        """Extrahiert Datum aus Content"""
        date_match = re.search(
            r'(20\d{2})', 
            content[max(0, match.start()-100):match.end()+100]
        )
        if date_match:
            return int(date_match.group(1))
        return datetime.now().year
    
    def _is_duplicate(self, result: SearchResult, existing: List[SearchResult]) -> bool:
        """Prüft ob Ergebnis bereits vorhanden"""
        return any(
            r.field_name == result.field_name and r.value == result.value 
            for r in existing
        )
    
    def create_adaptive_prompt(self, query: MineQuery, context: Dict[str, Any]) -> str:
        """Erstellt adaptive Suchanfrage basierend auf bisherigen Erkenntnissen"""
        
        # Was wir bereits wissen
        known_info = "\n".join([
            f"- {field}: {value}"
            for field, value in context["discovered_info"].items()
        ])
        
        # Was noch fehlt
        missing_fields = [
            field for field in query.required_fields
            if field not in context["discovered_info"]
        ]
        
        # Erstelle fokussierte Suchanfrage
        if context["search_iterations"] == 0:
            # Erste Iteration - breite Suche
            prompt = f"""Conduct comprehensive research on {query.mine_name} mine in {query.region}, {query.country}.

Focus on finding:
1. Official government sources and mining registries
2. Current ownership and operational status
3. Technical reports and production data
4. Environmental assessments and closure costs
5. Recent news and updates (2020-2025)

Search multiple authoritative sources and provide specific data with references."""
        
        else:
            # Folge-Iterationen - gezielte Suche nach fehlenden Informationen
            prompt = f"""Continue deep research on {query.mine_name} mine in {query.region}, {query.country}.

Already discovered:
{known_info if known_info else "No confirmed data yet"}

Still needed:
{chr(10).join('- ' + field for field in missing_fields[:5])}

Search strategies:
1. Look for alternative sources not yet checked
2. Search in {', '.join(query.languages)} languages
3. Check specialized mining databases
4. Look for PDF reports and technical documents
5. Verify through cross-references

Provide new information not already found, with specific sources."""
        
        return prompt
    
    def is_research_complete(self, context: Dict[str, Any], query: MineQuery, 
                           max_iterations: int) -> bool:
        """Prüft ob Research-Ziele erreicht wurden"""
        
        # Prüfe ob kritische Felder gefunden wurden
        critical_fields = ['betreiber', 'koordinaten', 'aktivitaetsstatus']
        found_critical = sum(
            1 for field in critical_fields
            if field in context["discovered_info"]
        )
        
        # Prüfe Gesamtabdeckung
        total_found = len(context["discovered_info"])
        total_required = len(query.required_fields)
        coverage = total_found / total_required if total_required > 0 else 0
        
        # Research ist komplett wenn:
        # - Alle kritischen Felder gefunden wurden, oder
        # - 80% der Felder gefunden wurden, oder
        # - Maximale Iterationen erreicht wurden
        return (
            found_critical == len(critical_fields) or
            coverage >= 0.8 or
            context["search_iterations"] >= max_iterations
        )