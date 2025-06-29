"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Spezialisierter Prozessor für Environmental Reports
"""

import re
from typing import Dict, List, Any
from pathlib import Path

from ..base import BasePDFProcessor, ExtractionResult
from ..extractors import TextExtractor, TableExtractor
from ....core.logger import get_logger


class EnvironmentalReportProcessor(BasePDFProcessor):
    """Prozessor für Environmental Reports"""
    
    def __init__(self):
        logger = get_logger("environmental_processor")
        super().__init__(logger)
        self.text_extractor = TextExtractor(logger)
        self.table_extractor = TableExtractor(logger)
    
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet Environmental Report"""
        result = ExtractionResult("environmental")
        
        if not self.can_process(pdf_path):
            result.add_error("Kann PDF nicht verarbeiten")
            return result.to_dict()
        
        try:
            # Text extrahieren
            text = await self.text_extractor.extract_text(pdf_path)
            
            # Environmental-spezifische Extraktion
            result.add_data("environmental_impacts", self._extract_impacts(text))
            result.add_data("mitigation_measures", self._extract_mitigation(text))
            result.add_data("monitoring_plan", self._extract_monitoring(text))
            result.add_data("compliance_status", self._extract_compliance(text))
            
            # Tabellen
            tables = await self.table_extractor.extract_tables(pdf_path)
            result.add_data("environmental_data", self._process_environmental_tables(tables))
            
        except Exception as e:
            result.add_error(f"Verarbeitungsfehler: {str(e)}")
            self.logger.error(f"Fehler bei Environmental Report: {e}")
        
        return result.to_dict()
    
    def _extract_impacts(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Environmental Impacts"""
        impacts = []
        
        # Impact-Kategorien
        categories = ['air', 'water', 'soil', 'noise', 'biodiversity', 'social']
        
        for category in categories:
            pattern = rf'{category}\s+(?:quality\s+)?impact[s]?:?\s*([^.]+\.)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                impacts.append({
                    'category': category,
                    'description': match.strip()
                })
        
        return impacts
    
    def _extract_mitigation(self, text: str) -> List[str]:
        """Extrahiert Mitigation Measures"""
        measures = []
        
        # Suche Mitigation-Sektion
        sections = self.text_extractor.extract_sections(text)
        
        for section_name, content in sections.items():
            if 'mitigation' in section_name.lower():
                # Extrahiere Maßnahmen
                measure_pattern = r'[•\-\*]\s*([^•\-\*\n]+)'
                matches = re.findall(measure_pattern, content)
                measures.extend(matches[:20])  # Max 20 Maßnahmen
                break
        
        return measures
    
    def _extract_monitoring(self, text: str) -> Dict[str, Any]:
        """Extrahiert Monitoring Plan"""
        monitoring = {
            'parameters': [],
            'frequency': [],
            'locations': []
        }
        
        # Parameter
        param_pattern = r'monitor(?:ing)?\s+(?:of\s+)?([a-zA-Z\s]+)(?:\s+levels?)?'
        params = re.findall(param_pattern, text, re.IGNORECASE)
        monitoring['parameters'] = list(set(p.strip() for p in params))[:10]
        
        # Frequenz
        freq_pattern = r'(daily|weekly|monthly|quarterly|annually|continuous)'
        freqs = re.findall(freq_pattern, text, re.IGNORECASE)
        monitoring['frequency'] = list(set(freqs))
        
        return monitoring
    
    def _extract_compliance(self, text: str) -> Dict[str, str]:
        """Extrahiert Compliance-Status"""
        compliance = {}
        
        # Compliance-Aussagen
        patterns = {
            'status': r'compliance\s+status:?\s*([^\n]+)',
            'regulations': r'(?:comply|compliance)\s+with\s+([^\n]+)',
            'permits': r'permit\s+(?:number|no\.?):?\s*([A-Z0-9\-]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                compliance[key] = match.group(1).strip()
        
        return compliance
    
    def _process_environmental_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verarbeitet Environmental-Tabellen"""
        processed = []
        
        for table in tables:
            data = table.get('data', [])
            if not data:
                continue
            
            # Kategorisiere nach Inhalt
            headers = list(data[0].keys()) if data else []
            
            if any('emission' in h.lower() for h in headers):
                table['table_type'] = 'emissions'
            elif any('water' in h.lower() for h in headers):
                table['table_type'] = 'water_quality'
            elif any('species' in h.lower() or 'biodiversity' in h.lower() for h in headers):
                table['table_type'] = 'biodiversity'
            else:
                table['table_type'] = 'other'
            
            processed.append(table)
        
        return processed