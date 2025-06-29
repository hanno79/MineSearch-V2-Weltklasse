"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Spezialisierter Prozessor für NI 43-101 Technical Reports
"""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..base import BasePDFProcessor, ExtractionResult
from ..extractors import TextExtractor, TableExtractor, MetadataExtractor
from ....core.logger import get_logger


class NI43101Processor(BasePDFProcessor):
    """Prozessor für NI 43-101 Technical Reports"""
    
    def __init__(self):
        logger = get_logger("ni43101_processor")
        super().__init__(logger)
        self.text_extractor = TextExtractor(logger)
        self.table_extractor = TableExtractor(logger)
        self.metadata_extractor = MetadataExtractor(logger)
    
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet NI 43-101 Report"""
        result = ExtractionResult("ni43-101")
        
        if not self.can_process(pdf_path):
            result.add_error("Kann PDF nicht verarbeiten")
            return result.to_dict()
        
        try:
            # Metadaten
            metadata = await self.metadata_extractor.extract_metadata(pdf_path)
            result.add_metadata("pdf_metadata", metadata)
            
            # Text extrahieren
            text = await self.text_extractor.extract_text(pdf_path)
            
            # Spezifische NI 43-101 Felder extrahieren
            result.add_data("qualified_persons", self._extract_qualified_persons(text))
            result.add_data("property_description", self._extract_property_description(text))
            result.add_data("mineral_resources", await self._extract_mineral_resources(pdf_path, text))
            result.add_data("recommendations", self._extract_recommendations(text))
            result.add_data("effective_date", self._extract_effective_date(text))
            
            # Tabellen extrahieren
            tables = await self.table_extractor.extract_tables(pdf_path)
            result.add_data("tables", self._process_ni43101_tables(tables))
            
            self.logger.info(f"NI 43-101 erfolgreich verarbeitet: {pdf_path.name}")
            
        except Exception as e:
            result.add_error(f"Verarbeitungsfehler: {str(e)}")
            self.logger.error(f"Fehler bei NI 43-101 Verarbeitung: {e}")
        
        return result.to_dict()
    
    def _extract_qualified_persons(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Qualified Persons"""
        qps = []
        
        # Muster für QP-Erkennung
        patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s*(?:P\.?(?:Eng|Geo)|M\.?Sc|Ph\.?D)',
            r'Qualified Person[s]?:?\s*([^,\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0]
                else:
                    name = match
                
                qps.append({
                    'name': name.strip(),
                    'designation': 'Qualified Person'
                })
        
        return qps
    
    def _extract_property_description(self, text: str) -> Dict[str, str]:
        """Extrahiert Property-Beschreibung"""
        description = {}
        
        # Suche nach Property-Sektion
        sections = self.text_extractor.extract_sections(text)
        
        for section_name, content in sections.items():
            if 'property' in section_name.lower() and 'description' in section_name.lower():
                # Extrahiere Details
                description['full_text'] = content[:1000]  # Erste 1000 Zeichen
                
                # Koordinaten
                coord_pattern = r'(\d+°\d+[\'"]?\s*[NS])\s*(?:and|,)\s*(\d+°\d+[\'"]?\s*[EW])'
                coord_match = re.search(coord_pattern, content)
                if coord_match:
                    description['coordinates'] = f"{coord_match.group(1)}, {coord_match.group(2)}"
                
                # Fläche
                area_pattern = r'(\d+(?:,\d+)?)\s*(?:hectares?|ha|km2|square kilometers?)'
                area_match = re.search(area_pattern, content, re.IGNORECASE)
                if area_match:
                    description['area'] = area_match.group(0)
                
                break
        
        return description
    
    async def _extract_mineral_resources(self, pdf_path: Path, text: str) -> Dict[str, Any]:
        """Extrahiert Mineral Resources"""
        resources = {
            'measured': {},
            'indicated': {},
            'inferred': {}
        }
        
        # Suche Resource-Tabellen
        tables = await self.table_extractor.extract_tables(pdf_path)
        
        for table in tables:
            table_data = table.get('data', [])
            if not table_data:
                continue
            
            # Prüfe ob Resource-Tabelle
            headers = list(table_data[0].keys()) if table_data else []
            if any('resource' in h.lower() for h in headers):
                # Verarbeite Resource-Daten
                for row in table_data:
                    category = None
                    for key, value in row.items():
                        if 'measured' in str(value).lower():
                            category = 'measured'
                        elif 'indicated' in str(value).lower():
                            category = 'indicated'
                        elif 'inferred' in str(value).lower():
                            category = 'inferred'
                        
                        # Extrahiere Tonnage und Grade
                        if category and any(term in key.lower() for term in ['tonnes', 'tons', 'mt']):
                            resources[category]['tonnage'] = value
                        elif category and any(term in key.lower() for term in ['grade', 'g/t', 'ppm', '%']):
                            resources[category]['grade'] = value
        
        return resources
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extrahiert Empfehlungen"""
        recommendations = []
        
        # Suche Recommendations-Sektion
        sections = self.text_extractor.extract_sections(text)
        
        for section_name, content in sections.items():
            if 'recommendation' in section_name.lower():
                # Extrahiere nummerierte Empfehlungen
                rec_pattern = r'(?:\d+\.?\s*)?([A-Z][^.!?]+[.!?])'
                matches = re.findall(rec_pattern, content)
                recommendations.extend(matches[:10])  # Max 10 Empfehlungen
                break
        
        return recommendations
    
    def _extract_effective_date(self, text: str) -> Optional[str]:
        """Extrahiert Effective Date"""
        # Verschiedene Datums-Formate
        patterns = [
            r'Effective Date:?\s*([A-Za-z]+\s+\d+,?\s+\d{4})',
            r'effective\s+(?:as\s+of\s+)?([A-Za-z]+\s+\d+,?\s+\d{4})',
            r'Report Date:?\s*([A-Za-z]+\s+\d+,?\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _process_ni43101_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verarbeitet NI 43-101 spezifische Tabellen"""
        processed = []
        
        for table in tables:
            # Kategorisiere Tabelle
            table_type = self._categorize_table(table)
            if table_type:
                table['table_type'] = table_type
                processed.append(table)
        
        return processed
    
    def _categorize_table(self, table: Dict[str, Any]) -> Optional[str]:
        """Kategorisiert Tabelle nach Inhalt"""
        data = table.get('data', [])
        if not data:
            return None
        
        # Prüfe erste Zeile (Headers)
        first_row = data[0] if data else {}
        headers_text = ' '.join(str(v).lower() for v in first_row.values())
        
        # Kategorisierung
        if any(term in headers_text for term in ['resource', 'tonnes', 'grade']):
            return 'mineral_resources'
        elif any(term in headers_text for term in ['drill', 'hole', 'from', 'to']):
            return 'drill_results'
        elif any(term in headers_text for term in ['sample', 'assay', 'au', 'ag']):
            return 'assay_results'
        elif any(term in headers_text for term in ['cost', 'capex', 'opex', '$']):
            return 'economics'
        
        return 'other'