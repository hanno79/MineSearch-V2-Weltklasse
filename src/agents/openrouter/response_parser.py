"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Response Parser für OpenRouter Agent
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..base_agent import SearchResult, MineQuery
from src.utils.safe_dict_access import safe_get, safe_nested_get, ensure_dict, ensure_list


class OpenRouterResponseParser:
    """Parst und verarbeitet OpenRouter-Antworten"""
    
    def __init__(self, agent_name: str, model_name: str, logger: Optional[logging.Logger] = None):
        self.agent_name = agent_name
        self.model_name = model_name
        self.logger = logger or logging.getLogger(__name__)
        
        # Feld-Mappings
        self.field_mappings = {
            'operator': 'betreiber',
            'owner': 'betreiber',
            'coordinates': 'koordinaten',
            'location': 'koordinaten',
            'remediation_cost': 'sanierungskosten',
            'closure_cost': 'sanierungskosten',
            'environmental_bond': 'sanierungskosten',
            'commodity': 'rohstofftyp',
            'mineral': 'rohstofftyp',
            'status': 'aktivitaetsstatus',
            'operational_status': 'aktivitaetsstatus',
            'production': 'jahresproduktion',
            'annual_production': 'jahresproduktion',
            'area': 'flaeche',
            'employees': 'mitarbeiter',
            'depth': 'tiefe',
            'founded': 'gruendungsjahr',
            'closed': 'schliessungsjahr'
        }
    
    def parse_response(self, content: str, query: MineQuery) -> List[SearchResult]:
        """Parse LLM response into SearchResults"""
        results = []
        
        try:
            # Try to extract JSON from response
            json_data = self._extract_json(content)
            
            if json_data:
                results.extend(self._parse_json_results(json_data, query))
            else:
                # Fallback: try to extract information from text
                results.extend(self._parse_text_results(content, query))
                
        except Exception as e:
            self.logger.error(f"Failed to parse OpenRouter response: {str(e)}")
            # Last resort: basic extraction
            results.extend(self._basic_extraction(content, query))
        
        return results
    
    def _extract_json(self, content: str) -> Any:
        """Extrahiert JSON aus der Antwort"""
        # ÄNDERUNG 21.06.2025: Robusteres JSON Parsing
        json_patterns = [
            r'\[\s*\{[\s\S]*\}\s*\]',  # Array of objects
            r'\{[\s\S]*\}',  # Single object
            r'```json\s*([\s\S]*?)\s*```',  # JSON in code block
            r'```\s*([\s\S]*?)\s*```'  # Code block without json marker
        ]
        
        json_str = None
        for pattern in json_patterns:
            match = re.search(pattern, content)
            if match:
                json_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
                break
        
        if not json_str:
            return None
        
        # Clean up common issues
        json_str = json_str.strip()
        # Remove trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON decode error: {e}. Trying to fix...")
            # Try to fix common issues
            json_str = json_str.replace("'", '"')  # Single to double quotes
            try:
                return json.loads(json_str)
            except:
                return None
    
    def _parse_json_results(self, data: Any, query: MineQuery) -> List[SearchResult]:
        """Parst JSON-Daten zu SearchResults"""
        results = []
        
        # ÄNDERUNG 21.06.2025: Handle both array and single object
        if isinstance(data, dict):
            data = [data]  # Convert single object to array
        elif not isinstance(data, list):
            self.logger.warning(f"Unexpected data type: {type(data)}")
            return results
        
        for item in data:
            if not isinstance(item, dict):
                continue
                
            if all(k in item for k in ['field', 'value', 'confidence']):
                # Map field names to German if needed
                field_name = item['field'].lower().replace(' ', '_')
                field_name = self.field_mappings.get(field_name, field_name)
                
                result = SearchResult(
                    mine_name=query.mine_name,
                    field_name=field_name,
                    value=str(item['value']),
                    source=safe_get(item, 'source', f'OpenRouter {self.model_name}'),
                    source_url=None,
                    source_date=safe_get(item, 'date', datetime.now().year),
                    confidence_score=float(safe_get(item, 'confidence', 0.5)),
                    agent_name=self.agent_name,
                    timestamp=datetime.now(),
                    metadata={
                        'model': self.model_name,
                        'date': safe_get(item, 'date', ''),
                        'search_type': 'llm_mining_search'
                    }
                )
                results.append(result)
        
        return results
    
    def _parse_text_results(self, content: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Informationen aus Freitext"""
        results = []
        
        # Koordinaten-Extraktion
        coord_pattern = r'([-]?\d{1,3}\.\d+)[,\s]+([-]?\d{1,3}\.\d+)'
        coord_matches = re.findall(coord_pattern, content)
        if coord_matches:
            for match in coord_matches:
                coord_str = f"{match[0]}, {match[1]}"
                results.append(SearchResult(
                    mine_name=query.mine_name,
                    field_name='koordinaten',
                    value=coord_str,
                    source=f'OpenRouter {self.model_name}',
                    source_url=None,
                    source_date=datetime.now().year,
                    confidence_score=0.8,
                    agent_name=self.agent_name,
                    timestamp=datetime.now(),
                    metadata={'extraction_method': 'regex'}
                ))
        
        # Kosten-Extraktion
        cost_patterns = [
            r'(\$|CAD|USD|EUR)\s*([\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?)',
            r'([\d,]+(?:\.\d{2})?)\s*(\$|CAD|USD|EUR)(?:\s*(?:million|billion|M|B))?'
        ]
        
        for pattern in cost_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Check context for costs
                    context = content[max(0, content.find(str(match[0]))-100):content.find(str(match[0]))+100]
                    if any(word in context.lower() for word in ['closure', 'bond', 'remediation', 'restoration', 'environmental']):
                        if match[0] in ['$', 'CAD', 'USD', 'EUR']:
                            value = f"{match[1]} {match[0]}"
                        else:
                            value = f"{match[0]} {match[1] if len(match) > 1 else 'CAD'}"
                        
                        results.append(SearchResult(
                            mine_name=query.mine_name,
                            field_name='sanierungskosten',
                            value=value,
                            source=f'OpenRouter {self.model_name}',
                            source_url=None,
                            source_date=datetime.now().year,
                            confidence_score=0.7,
                            agent_name=self.agent_name,
                            timestamp=datetime.now(),
                            metadata={'extraction_method': 'regex'}
                        ))
        
        return results
    
    def _basic_extraction(self, content: str, query: MineQuery) -> List[SearchResult]:
        """Basis-Extraktion als Fallback"""
        results = []
        
        # Try to extract any useful information
        for field in query.required_fields:
            if field.lower() in content.lower():
                # Try to extract value near field mention
                lines = content.split('\n')
                for line in lines:
                    if field.lower() in line.lower():
                        # Clean up the line
                        value = line.strip()
                        # Remove field name from value
                        value = re.sub(f'{field}[:\s]*', '', value, flags=re.IGNORECASE)
                        
                        if value and len(value) > 3:
                            result = SearchResult(
                                mine_name=query.mine_name,
                                field_name=field,
                                value=value,
                                source=f"OpenRouter {self.model_name}",
                                source_url=None,
                                source_date=datetime.now().year,
                                confidence_score=0.5,
                                agent_name=self.agent_name,
                                timestamp=datetime.now(),
                                metadata={'extraction_method': 'basic'}
                            )
                            results.append(result)
                            break
        
        return results
