"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Spezialisierter Prozessor für allgemeine Technical Reports
"""

import re
from typing import Dict, List, Any
from pathlib import Path

from ..base import BasePDFProcessor, ExtractionResult
from ..extractors import TextExtractor, TableExtractor
from ....core.logger import get_logger


class TechnicalReportProcessor(BasePDFProcessor):
    """Prozessor für allgemeine Technical Reports"""
    
    def __init__(self):
        logger = get_logger("technical_processor")
        super().__init__(logger)
        self.text_extractor = TextExtractor(logger)
        self.table_extractor = TableExtractor(logger)
    
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet Technical Report"""
        result = ExtractionResult("technical")
        
        if not self.can_process(pdf_path):
            result.add_error("Kann PDF nicht verarbeiten")
            return result.to_dict()
        
        try:
            # Basis-Extraktion
            text = await self.text_extractor.extract_text(pdf_path)
            sections = self.text_extractor.extract_sections(text)
            tables = await self.table_extractor.extract_tables(pdf_path)
            
            # Strukturierte Daten
            result.add_data("sections", list(sections.keys()))
            result.add_data("technical_data", self._extract_technical_data(text))
            result.add_data("conclusions", self._extract_conclusions(sections))
            result.add_data("tables_summary", self._summarize_tables(tables))
            
        except Exception as e:
            result.add_error(f"Verarbeitungsfehler: {str(e)}")
            self.logger.error(f"Fehler bei Technical Report: {e}")
        
        return result.to_dict()
    
    def _extract_technical_data(self, text: str) -> Dict[str, List[str]]:
        """Extrahiert technische Daten"""
        tech_data = {
            'measurements': [],
            'specifications': [],
            'methods': []
        }
        
        # Messungen (Zahlen mit Einheiten)
        measure_pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+/?[a-zA-Z]*)'
        measures = re.findall(measure_pattern, text)
        tech_data['measurements'] = [f"{m[0]} {m[1]}" for m in measures[:20]]
        
        # Methoden
        method_pattern = r'(?:method|technique|process):\s*([^\n]+)'
        methods = re.findall(method_pattern, text, re.IGNORECASE)
        tech_data['methods'] = methods[:10]
        
        return tech_data
    
    def _extract_conclusions(self, sections: Dict[str, str]) -> List[str]:
        """Extrahiert Schlussfolgerungen"""
        conclusions = []
        
        for section_name, content in sections.items():
            if 'conclusion' in section_name.lower():
                # Erste Sätze als Zusammenfassung
                sentences = content.split('.')[:5]
                conclusions.extend(s.strip() for s in sentences if s.strip())
                break
        
        return conclusions
    
    def _summarize_tables(self, tables: List[Dict[str, Any]]) -> Dict[str, int]:
        """Zusammenfassung der Tabellen"""
        summary = {
            'total_tables': len(tables),
            'pages_with_tables': len(set(t['page'] for t in tables)),
            'average_accuracy': sum(t.get('accuracy', 0) for t in tables) / len(tables) if tables else 0
        }
        
        return summary