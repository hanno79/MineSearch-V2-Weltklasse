"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Seiten-Analyse für Browser Agent
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from .models import ExtractionStrategy, ExtractionRule, JavaScriptCheck, ScrapeResult
from ..base_agent import MineQuery, SearchResult
from src.core.logger import get_logger


class PageAnalyzer:
    """Analysiert und extrahiert Daten aus Webseiten"""
    
    def __init__(self, logger=None):
        self.logger = logger or get_logger("page_analyzer")
        
        # Muster für verschiedene Datentypen
        self.patterns = {
            "coordinates": [
                r"(\d+\.?\d*)[°\s]+([NS])[,\s]+(\d+\.?\d*)[°\s]+([EW])",
                r"lat(?:itude)?[:\s]+(-?\d+\.?\d*)[,\s]+lon(?:gitude)?[:\s]+(-?\d+\.?\d*)",
                r"(-?\d+\.\d{3,})[,\s]+(-?\d+\.\d{3,})"  # Dezimalgrad
            ],
            "costs": [
                r"(\d+(?:[,\.]\d+)*)\s*(?:million|mln|M)?\s*(?:USD|EUR|CAD|AUD|\$|€)",
                r"(?:cost|budget|investment)[:\s]+(\d+(?:[,\.]\d+)*)",
                r"(\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d+)?)\s*(?:dollars|euros)"
            ],
            "production": [
                r"(\d+(?:[,\.]\d+)*)\s*(?:tons?|tonnes?|t\/year|tpa|kt|Mt)",
                r"(?:production|capacity)[:\s]+(\d+(?:[,\.]\d+)*)",
                r"(\d+(?:[,\.]\d+)*)\s*(?:ounces?|oz|kg)"
            ],
            "dates": [
                r"(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})",
                r"(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})",
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{4})"
            ]
        }
        
        # Feld-Mapping für verschiedene Sprachen
        self.field_mappings = {
            "en": {
                "operator": ["operator", "owner", "company", "operated by"],
                "coordinates": ["coordinates", "location", "gps", "latitude", "longitude"],
                "production": ["production", "capacity", "output", "tonnes"],
                "status": ["status", "operational", "active", "closed"],
                "commodity": ["commodity", "mineral", "resource", "product"],
                "remediation_costs": ["remediation", "closure costs", "restoration", "rehabilitation"]
            },
            "es": {
                "operator": ["operador", "propietario", "empresa", "compañía"],
                "coordinates": ["coordenadas", "ubicación", "localización"],
                "production": ["producción", "capacidad", "toneladas"],
                "status": ["estado", "estatus", "operacional", "activo"],
                "commodity": ["mineral", "recurso", "producto"],
                "remediation_costs": ["remediación", "costos de cierre", "restauración"]
            },
            "fr": {
                "operator": ["opérateur", "propriétaire", "entreprise", "société"],
                "coordinates": ["coordonnées", "emplacement", "localisation"],
                "production": ["production", "capacité", "tonnes"],
                "status": ["statut", "état", "opérationnel", "actif"],
                "commodity": ["minéral", "ressource", "produit"],
                "remediation_costs": ["remédiation", "coûts de fermeture", "restauration"]
            }
        }
    
    def needs_browser_rendering(self, url: str) -> bool:
        """Prüft ob URL Browser-Rendering benötigt"""
        # Domains die oft JavaScript nutzen
        js_heavy_domains = [
            'arcgis.com', 'maps.google.com', 'openstreetmap.org',
            'tableau.com', 'powerbi.com', 'qlik.com',
            'shinyapps.io', 'plotly.com'
        ]
        
        # Pfade die auf dynamische Inhalte hinweisen
        dynamic_paths = [
            '/map', '/dashboard', '/visualization', '/app',
            '/portal', '/viewer', '/search', '/query'
        ]
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Prüfe Domain
        for js_domain in js_heavy_domains:
            if js_domain in domain:
                return True
        
        # Prüfe Pfad
        for dynamic_path in dynamic_paths:
            if dynamic_path in path:
                return True
        
        # Prüfe Query-Parameter
        if parsed.query and any(param in parsed.query.lower() for param in ['search', 'query', 'filter']):
            return True
        
        return False
    
    async def analyze_page_structure(self, page_content: str, url: str) -> Dict[str, Any]:
        """Analysiert Seitenstruktur"""
        analysis = {
            "has_tables": bool(re.search(r'<table', page_content, re.IGNORECASE)),
            "has_forms": bool(re.search(r'<form', page_content, re.IGNORECASE)),
            "has_maps": bool(re.search(r'(mapbox|leaflet|google.*maps|arcgis)', page_content, re.IGNORECASE)),
            "has_charts": bool(re.search(r'(chart|graph|plot|visualization)', page_content, re.IGNORECASE)),
            "language": self._detect_language(page_content),
            "extraction_strategy": self._determine_extraction_strategy(page_content)
        }
        
        return analysis
    
    def extract_from_page(self, page_content: str, query: MineQuery, 
                         url: str, source_type: str = "web") -> List[SearchResult]:
        """Extrahiert Daten aus Seiteninhalt"""
        results = []
        
        # Analysiere Seitenstruktur
        structure = {
            "language": self._detect_language(page_content),
            "has_tables": "<table" in page_content.lower(),
            "has_lists": "<ul" in page_content.lower() or "<ol" in page_content.lower()
        }
        
        # Extrahiere basierend auf Struktur
        if structure["has_tables"]:
            table_results = self._extract_from_tables(page_content, query, structure["language"])
            results.extend(table_results)
        
        # Pattern-basierte Extraktion
        pattern_results = self._extract_with_patterns(page_content, query, structure["language"])
        results.extend(pattern_results)
        
        # Konvertiere zu SearchResult
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                field_name=result["field"],
                value=result["value"],
                source=f"{source_type}: {url}",
                confidence_score=result.get("confidence", 0.7),
                metadata={
                    "url": url,
                    "extraction_method": result.get("method", "pattern"),
                    "language": structure["language"]
                }
            ))
        
        return search_results
    
    def create_extraction_rules(self, required_fields: List[str], 
                              language: str = "en") -> List[ExtractionRule]:
        """Erstellt Extraktionsregeln für Felder"""
        rules = []
        
        # Standard-Selektoren für verschiedene Feldtypen
        field_selectors = {
            "betreiber": [
                "td:contains('Operator') + td",
                "td:contains('Owner') + td",
                "span.operator-name",
                "div.company-info"
            ],
            "operator": [
                "td:contains('Operator') + td",
                "td:contains('Owner') + td",
                "span.operator-name"
            ],
            "koordinaten": [
                "td:contains('Coordinates') + td",
                "td:contains('Location') + td",
                "span.coordinates",
                "div.gps-info"
            ],
            "coordinates": [
                "td:contains('Coordinates') + td",
                "td:contains('GPS') + td",
                "span.coordinates"
            ],
            "produktion": [
                "td:contains('Production') + td",
                "td:contains('Capacity') + td",
                "span.production-value"
            ],
            "production": [
                "td:contains('Production') + td",
                "td:contains('Output') + td",
                "span.production-value"
            ]
        }
        
        for field in required_fields:
            selectors = field_selectors.get(field, [f"*:contains('{field}')"])
            
            for selector in selectors[:2]:  # Max 2 Selektoren pro Feld
                rules.append(ExtractionRule(
                    field_name=field,
                    selector=selector,
                    strategy=ExtractionStrategy.TEXT,
                    transform="trim",
                    multiple=False,
                    required=field in ["betreiber", "operator", "koordinaten", "coordinates"]
                ))
        
        return rules
    
    def validate_extraction(self, field: str, value: Any) -> Tuple[bool, float]:
        """Validiert extrahierten Wert"""
        if not value:
            return False, 0.0
        
        value_str = str(value).strip()
        
        # Feldspezifische Validierung
        if field in ["koordinaten", "coordinates"]:
            # Prüfe Koordinatenformat
            for pattern in self.patterns["coordinates"]:
                if re.match(pattern, value_str):
                    return True, 0.9
            return False, 0.0
        
        elif field in ["sanierungskosten", "remediation_costs"]:
            # Prüfe Kostenformat
            for pattern in self.patterns["costs"]:
                if re.search(pattern, value_str):
                    return True, 0.85
            return False, 0.0
        
        elif field in ["produktion", "production"]:
            # Prüfe Produktionsformat
            for pattern in self.patterns["production"]:
                if re.search(pattern, value_str):
                    return True, 0.85
            return False, 0.0
        
        # Generische Validierung
        if len(value_str) > 2 and len(value_str) < 1000:
            return True, 0.7
        
        return False, 0.0
    
    # Private Hilfsmethoden
    def _detect_language(self, content: str) -> str:
        """Erkennt Sprache des Inhalts"""
        # Einfache Spracherkennung basierend auf häufigen Wörtern
        language_indicators = {
            "es": ["de", "la", "el", "en", "por", "para", "mina", "minería"],
            "fr": ["le", "la", "de", "et", "pour", "dans", "mine", "minier"],
            "pt": ["o", "a", "de", "da", "do", "para", "mina", "mineração"],
            "de": ["der", "die", "das", "und", "für", "mit", "bergwerk"],
            "en": ["the", "of", "and", "to", "in", "for", "mine", "mining"]
        }
        
        content_lower = content.lower()
        scores = {}
        
        for lang, words in language_indicators.items():
            score = sum(1 for word in words if f" {word} " in content_lower)
            scores[lang] = score
        
        # Wähle Sprache mit höchstem Score
        if scores:
            return max(scores, key=scores.get)
        
        return "en"  # Default
    
    def _determine_extraction_strategy(self, content: str) -> ExtractionStrategy:
        """Bestimmt beste Extraktionsstrategie"""
        content_lower = content.lower()
        
        if "<table" in content_lower:
            return ExtractionStrategy.TABLE
        elif "<form" in content_lower:
            return ExtractionStrategy.FORM
        elif "<ul" in content_lower or "<ol" in content_lower:
            return ExtractionStrategy.LIST
        elif any(tag in content_lower for tag in ["<div", "<span", "<p"]):
            return ExtractionStrategy.STRUCTURED
        else:
            return ExtractionStrategy.TEXT
    
    def _extract_from_tables(self, content: str, query: MineQuery, language: str) -> List[Dict[str, Any]]:
        """Extrahiert Daten aus Tabellen"""
        results = []
        
        # Finde alle Tabellen
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for table in tables:
            # Extrahiere Zeilen
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(row_pattern, table, re.IGNORECASE | re.DOTALL)
            
            for row in rows:
                # Extrahiere Zellen
                cell_pattern = r'<t[dh][^>]*>(.*?)</t[dh]>'
                cells = re.findall(cell_pattern, row, re.IGNORECASE | re.DOTALL)
                
                if len(cells) >= 2:
                    # Prüfe ob erste Zelle ein gesuchtes Feld ist
                    label = re.sub(r'<[^>]+>', '', cells[0]).strip().lower()
                    value = re.sub(r'<[^>]+>', '', cells[1]).strip()
                    
                    # Prüfe gegen Feld-Mappings
                    mappings = self.field_mappings.get(language, self.field_mappings["en"])
                    
                    for field, keywords in mappings.items():
                        if field in query.required_fields:
                            if any(keyword in label for keyword in keywords):
                                results.append({
                                    "field": field,
                                    "value": value,
                                    "confidence": 0.8,
                                    "method": "table_extraction"
                                })
        
        return results
    
    def _extract_with_patterns(self, content: str, query: MineQuery, language: str) -> List[Dict[str, Any]]:
        """Extrahiert Daten mit Regex-Patterns"""
        results = []
        
        # Entferne HTML-Tags für Pattern-Matching
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text)
        
        # Suche nach Mustern für jedes Feld
        for field in query.required_fields:
            if field in ["koordinaten", "coordinates"]:
                for pattern in self.patterns["coordinates"]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        results.append({
                            "field": field,
                            "value": match.group(0),
                            "confidence": 0.75,
                            "method": "pattern_extraction"
                        })
                        break  # Nur erste Übereinstimmung
            
            elif field in ["sanierungskosten", "remediation_costs"]:
                for pattern in self.patterns["costs"]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # Prüfe Kontext
                        context = text[max(0, match.start()-50):match.end()+50].lower()
                        if any(word in context for word in ["remediation", "closure", "restoration", "sanierung"]):
                            results.append({
                                "field": field,
                                "value": match.group(0),
                                "confidence": 0.8,
                                "method": "pattern_extraction"
                            })
                            break
            
            elif field in ["produktion", "production"]:
                for pattern in self.patterns["production"]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        results.append({
                            "field": field,
                            "value": match.group(0),
                            "confidence": 0.75,
                            "method": "pattern_extraction"
                        })
                        break
        
        return results