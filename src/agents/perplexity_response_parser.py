"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Response Parser für Perplexity Agent
"""

import re
from typing import List, Dict, Any
from datetime import datetime

from .base_agent import MineQuery, SearchResult
from src.utils.safe_dict_access import safe_get
from src.core.logger import get_logger


class PerplexityResponseParser:
    """Parst Responses von der Perplexity API"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger(f"parser.{agent_name}", agent_type="perplexity")
    
    def parse_response(self, response: Dict[str, Any], query: MineQuery, search_type: str) -> List[SearchResult]:
        """Parst Perplexity-Antwort mit Fokus auf Faktenextraktion"""
        # ÄNDERUNG 27.06.2025: Extrahiert aus perplexity_agent.py für bessere Modularität
        results = []
        
        try:
            if response is None:
                self.logger.error("Response ist None")
                return results
            
            # Behandle verschiedene Response-Typen
            if isinstance(response, str):
                # Wenn Response ein String ist, konvertiere zu Dict-Format
                self.logger.warning(f"Response ist ein String, konvertiere zu Dict-Format")
                response = {
                    "choices": [{"message": {"content": response}}],
                    "type": "text_response"
                }
            elif hasattr(response, '__dict__'):
                # Wenn Response ein Objekt ist, konvertiere zu Dict
                self.logger.warning(f"Response ist ein Objekt vom Typ {type(response)}, konvertiere zu Dict")
                try:
                    response = response.__dict__
                except Exception as e:
                    self.logger.error(f"Konnte Objekt nicht zu Dict konvertieren: {e}")
                    return results
            
            if not isinstance(response, dict):
                self.logger.error(f"Response ist kein Dictionary: {type(response)}")
                return results
                
            # Sichere Navigation durch Response-Struktur
            content = ""
            citations = []
            
            if safe_get(response, 'type') == 'text_response':
                # Direkte Text-Response
                choices = safe_get(response, 'choices', [])
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = safe_get(first_choice, 'message', {})
                        if isinstance(message, dict):
                            content = safe_get(message, 'content', '')
                        elif isinstance(message, str):
                            content = message
                    elif isinstance(first_choice, str):
                        content = first_choice
            elif 'choices' in response and response['choices']:
                # Standard API Response
                choices = safe_get(response, 'choices', [])
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = safe_get(first_choice, 'message', '')
                        if isinstance(message, str):
                            content = message
                        elif isinstance(message, dict):
                            content = safe_get(message, 'content', '')
                        else:
                            self.logger.error(f"Unerwarteter message Typ: {type(message)}")
                    
                citations = safe_get(response, 'citations', [])
                if not isinstance(citations, list):
                    citations = []
                
            # Nur wenn Content vorhanden ist, extrahiere Daten
            if content:
                # Extrahiere strukturierte Daten aus dem Text
                extracted_data = self._extract_structured_data(content, citations)
                
                for field_name, value_data in extracted_data.items():
                    if isinstance(value_data, dict) and safe_get(value_data, 'value') and value_data['value'] != 'nichts gefunden':
                        confidence_mapping = {'high': 0.9, 'medium': 0.7, 'low': 0.5}
                        confidence_score = confidence_mapping.get(safe_get(value_data, 'confidence', 'medium'), 0.7)
                        
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field_name,
                            value=value_data['value'],
                            source=safe_get(value_data, 'source', 'Perplexity Web Search'),
                            source_url=safe_get(value_data, 'url', ''),
                            source_date=safe_get(value_data, 'year', datetime.now().year),
                            confidence_score=confidence_score,
                            agent_name=self.agent_name,
                            timestamp=datetime.now(),
                            metadata={'search_type': search_type, 'language': 'en'}
                        )
                        results.append(result)
                        self.logger.info(f"Gefunden: {result.field_name} = {result.value}")
            else:
                self.logger.warning("Kein Content in Response gefunden")
                        
        except Exception as e:
            self.logger.error(f"Response Parse Fehler: {e}")
            self.logger.error(f"Response Type: {type(response)}")
            if isinstance(response, str):
                self.logger.error(f"Response String: {response[:200]}...")
            elif isinstance(response, dict):
                self.logger.error(f"Response Keys: {list(response.keys())}")
            import traceback
            self.logger.error(f"Stack Trace:\n{traceback.format_exc()}")
            
        return results
    
    def _extract_structured_data(self, content: str, citations: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Extrahiert strukturierte Daten aus Perplexity-Antwort"""
        # ÄNDERUNG 27.06.2025: Extrahiert aus perplexity_agent.py für bessere Modularität
        extracted = {}
        
        # Entferne Prompt-Echo aus Response
        if "Search Query:" in content or "extract:" in content.lower():
            # Versuche nur den tatsächlichen Antwort-Teil zu extrahieren
            parts = content.split("\n\n", 2)
            if len(parts) > 1:
                # Suche nach dem Start der tatsächlichen Antwort
                for i, part in enumerate(parts):
                    if any(keyword in part.lower() for keyword in ["based on", "according to", "found", "shows", "indicates"]):
                        content = "\n\n".join(parts[i:])
                        break
        
        # Patterns für verschiedene Datentypen
        patterns = {
            'betreiber': [
                r'operated by\s+([^,\.\n]+)',
                r'operator[:\s]+([^,\.\n]+)',
                r'owned by\s+([^,\.\n]+)',
                r'owner[:\s]+([^,\.\n]+)'
            ],
            'koordinaten': [
                r'coordinates[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'located at[:\s]*([-\d\.]+)[,\s]+([-\d\.]+)',
                r'latitude[:\s]*([-\d\.]+).*longitude[:\s]*([-\d\.]+)',
                r'(\d+°\d+\'[\d\.]+\"[NS])[,\s]+(\d+°\d+\'[\d\.]+\"[EW])'
            ],
            'aktivitaetsstatus': [
                r'status[:\s]+(\w+)',
                r'currently\s+(\w+)',
                r'mine is\s+(\w+)',
                r'operations?\s+(?:are\s+)?(\w+)'
            ],
            'sanierungskosten': [
                r'rehabilitation cost[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?',
                r'closure bond[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?',
                r'financial assurance[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?',
                r'restoration cost[s]?[:\s]+\$?([\d,\.]+)\s*(?:million|M)?(?:\s+CAD)?'
            ],
            'rohstofftyp': [
                r'produces?\s+([^,\.\n]+(?:,\s*[^,\.\n]+)*)',
                r'commodit(?:y|ies)[:\s]+([^,\.\n]+(?:,\s*[^,\.\n]+)*)',
                r'extract(?:s|ing)?\s+([^,\.\n]+(?:,\s*[^,\.\n]+)*)'
            ],
            'flaeche': [
                r'area[:\s]+([\d,\.]+)\s*(?:km²|km2|hectares?|ha)',
                r'covers?\s+([\d,\.]+)\s*(?:km²|km2|hectares?|ha)',
                r'property size[:\s]+([\d,\.]+)\s*(?:km²|km2|hectares?|ha)'
            ],
            'mitarbeiter': [
                r'employs?\s+([\d,]+)\s*(?:people|workers|employees)',
                r'([\d,]+)\s*employees',
                r'workforce[:\s]+([\d,]+)'
            ]
        }
        
        content_lower = content.lower()
        
        # Suche nach Mustern
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, content_lower, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if len(match.groups()) > 1:  # Für Koordinaten
                        value = f"{match.group(1)}, {match.group(2)}"
                    
                    # Bereinige Wert
                    value = value.strip()
                    
                    # Validiere extrahierte Werte
                    if self._validate_extracted_value(field_name, value):
                        # Bestimme Quelle aus Citations
                        source = "Perplexity Web Search"
                        url = ""
                        if citations and isinstance(citations, list) and len(citations) > 0:
                            # Versuche die relevanteste Citation zu finden
                            first_citation = citations[0]
                            if isinstance(first_citation, dict):
                                source = safe_get(first_citation, 'title', source)
                                url = safe_get(first_citation, 'url', '')
                            elif isinstance(first_citation, str):
                                source = first_citation
                                url = ""
                        
                        extracted[field_name] = {
                            'value': value,
                            'source': source,
                            'url': url,
                            'year': datetime.now().year,
                            'confidence': 'high' if citations else 'medium'
                        }
                        break
        
        return extracted
    
    def _validate_extracted_value(self, field_name: str, value: str) -> bool:
        """Validiert extrahierte Werte"""
        # ÄNDERUNG 27.06.2025: Ausgelagerte Validierungslogik
        # Vermeide Extraktion von Prompt-Fragmenten
        invalid_values = [
            "or owner company", "lac expanse", "quebec", "canada",
            "extract", "search", "find", "look for", "provide",
            "information", "data", "details", "based on", "according to",
            "search query", "find information", "please provide",
            "i need", "looking for", "tell me", "what is",
            "comprehensive information", "search for", "extract:"
        ]
        
        # Prüfe ob der Wert verdächtig aussieht
        if any(invalid in value.lower() for invalid in invalid_values):
            return False
        
        # Prüfe Mindestlänge für sinnvolle Werte
        if len(value) < 3:
            return False
        
        # Zusätzliche Validierung für spezifische Felder
        if field_name == 'betreiber':
            # Betreiber sollte wie ein Firmenname aussehen
            if not any(char.isupper() for char in value):
                return False  # Sollte mindestens einen Großbuchstaben haben
            if len(value.split()) > 10:
                return False  # Zu lang für einen Firmennamen
        
        elif field_name == 'koordinaten':
            # Koordinaten sollten Zahlen enthalten
            if not any(char.isdigit() for char in value):
                return False
        
        elif field_name == 'sanierungskosten':
            # Kosten sollten Zahlen enthalten
            if not any(char.isdigit() for char in value):
                return False
        
        return True