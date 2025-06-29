"""
Author: rahn
Datum: 21.06.2025
Version: 1.1
Beschreibung: PDF Processor für Mining-Dokumente

ÄNDERUNG 27.06.2025: Refactoring für Regel 1 (500 Zeilen Limit)
Extrahierte PDF-Extraction-Methoden in separate Module
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib
import json

from ..core.logger import get_logger
from .pdf_extractors import PyPDF2Extractor, PDFPlumberExtractor, CamelotExtractor, OCRExtractor
from .pdf_extractors.mining_patterns import MiningPatternExtractor


class PDFProcessor:
    """Verarbeitet PDF-Dokumente für Mining-Daten"""
    
    def __init__(self):
        self.logger = get_logger("pdf_processor")
        
        # Initialisiere Extractors
        self.pypdf2_extractor = PyPDF2Extractor()
        self.pdfplumber_extractor = PDFPlumberExtractor()
        self.camelot_extractor = CamelotExtractor()
        self.ocr_extractor = OCRExtractor()
        self.pattern_extractor = MiningPatternExtractor()
        
        self._check_dependencies()
        
    def _check_dependencies(self):
        """Prüft verfügbare PDF-Bibliotheken"""
        available = []
        if self.pypdf2_extractor.is_available():
            available.append("PyPDF2")
        if self.pdfplumber_extractor.is_available():
            available.append("pdfplumber")
        if self.camelot_extractor.is_available():
            available.append("camelot")
        if self.ocr_extractor.is_available():
            available.append("OCR (pytesseract)")
            
        self.logger.info(f"Verfügbare PDF-Bibliotheken: {', '.join(available)}")
        
        if not available:
            self.logger.warning(
                "Keine PDF-Bibliotheken verfügbar! Installation empfohlen: "
                "pip install PyPDF2 pdfplumber camelot-py[cv] pytesseract"
            )
    
    async def process_pdf(self, pdf_path: str, pdf_type: str = 'auto') -> Dict[str, Any]:
        """Hauptmethode für PDF-Verarbeitung"""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            self.logger.error(f"PDF nicht gefunden: {pdf_path}")
            return {}
        
        # Typ erkennen
        if pdf_type == 'auto':
            pdf_type = await self._detect_pdf_type(pdf_path)
        
        self.logger.info(f"Verarbeite PDF: {pdf_path.name} (Typ: {pdf_type})")
        
        # Typ-spezifische Verarbeitung
        processors = {
            'ni43-101': self._process_ni43101,
            'environmental': self._process_environmental_report,
            'financial': self._process_financial_report,
            'technical': self._process_technical_report
        }
        
        processor = processors.get(pdf_type, self._process_generic_pdf)
        return await processor(pdf_path)
    
    async def _detect_pdf_type(self, pdf_path: Path) -> str:
        """Erkennt den Typ eines PDFs basierend auf Inhalt"""
        # Lese erste Seiten für Typ-Erkennung
        text = await self._extract_text_pages(pdf_path, max_pages=5)
        text_lower = text.lower()
        
        # Typ-Indikatoren
        type_indicators = {
            'ni43-101': ['ni 43-101', 'national instrument 43-101', 'technical report'],
            'environmental': ['environmental impact', 'eia', 'closure plan', 'rehabilitation'],
            'financial': ['financial statements', 'annual report', 'quarterly report', 'md&a'],
            'technical': ['feasibility study', 'pea', 'preliminary economic assessment', 'resource estimate']
        }
        
        for pdf_type, indicators in type_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return pdf_type
        
        return 'generic'
    
    async def _process_ni43101(self, pdf_path: Path) -> Dict[str, Any]:
        """Spezialisierte Verarbeitung für NI 43-101 Reports"""
        extracted_data = {
            'report_type': 'NI 43-101',
            'file_path': str(pdf_path),
            'processed_at': datetime.now().isoformat(),
            'sections': {},
            'key_data': {},
            'tables': []
        }
        
        # Extrahiere Inhaltsverzeichnis
        toc = await self._extract_table_of_contents(pdf_path)
        extracted_data['table_of_contents'] = toc
        
        # Wichtige NI 43-101 Sektionen
        important_sections = [
            'Executive Summary',
            'Property Description and Location',
            'Mineral Resource Estimate',
            'Mineral Reserve Estimate',
            'Mining Methods',
            'Recovery Methods',
            'Project Infrastructure',
            'Environmental Studies',
            'Capital and Operating Costs',
            'Economic Analysis',
            'Conclusions and Recommendations'
        ]
        
        # Extrahiere jede wichtige Sektion
        for section in important_sections:
            section_data = await self._extract_section(pdf_path, section, toc)
            if section_data:
                extracted_data['sections'][section] = section_data
                
                # Extrahiere spezifische Daten aus Sektionen
                if section == 'Property Description and Location':
                    coords = self.pattern_extractor.extract_coordinates(section_data)
                    if coords:
                        extracted_data['key_data']['coordinates'] = coords
                        
                elif section == 'Mineral Resource Estimate':
                    resources = self.pattern_extractor.extract_resource_data(section_data)
                    if resources:
                        extracted_data['key_data']['resources'] = resources
                        
                elif section == 'Capital and Operating Costs':
                    costs = self.pattern_extractor.extract_cost_data(section_data)
                    if costs:
                        extracted_data['key_data']['costs'] = costs
        
        # Extrahiere alle Tabellen
        tables = await self._extract_all_tables(pdf_path)
        extracted_data['tables'] = tables
        
        # Extrahiere Key Mining Data
        full_text = await self._extract_full_text(pdf_path)
        key_data = self.pattern_extractor.extract_key_data(full_text)
        extracted_data['key_data'].update(key_data)
        
        return extracted_data
    
    async def _process_environmental_report(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet Umweltberichte"""
        extracted_data = {
            'report_type': 'Environmental',
            'file_path': str(pdf_path),
            'processed_at': datetime.now().isoformat(),
            'environmental_data': {}
        }
        
        # Volltext extrahieren
        full_text = await self._extract_full_text(pdf_path)
        
        # Extrahiere Umweltdaten
        env_data = self.pattern_extractor.extract_environmental_data(full_text)
        extracted_data['environmental_data'] = env_data
        
        # Extrahiere Tabellen mit Umweltdaten
        tables = await self._extract_all_tables(pdf_path)
        env_tables = [
            table for table in tables 
            if self.pattern_extractor.is_environmental_table(table)
        ]
        extracted_data['environmental_tables'] = env_tables
        
        return extracted_data
    
    async def _process_financial_report(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet Finanzberichte"""
        extracted_data = {
            'report_type': 'Financial',
            'file_path': str(pdf_path),
            'processed_at': datetime.now().isoformat(),
            'financial_data': {}
        }
        
        # Extrahiere Finanztabellen
        tables = await self._extract_all_tables(pdf_path)
        
        # Suche nach wichtigen Finanzdaten
        for table in tables:
            table_data = table.get('data', [])
            
            # Suche nach Revenue/Umsatz
            revenue = self.pattern_extractor.find_financial_value(
                table_data, ['revenue', 'umsatz', 'sales']
            )
            if revenue:
                extracted_data['financial_data']['revenue'] = revenue
            
            # Suche nach Operating Costs
            op_costs = self.pattern_extractor.find_financial_value(
                table_data, ['operating cost', 'betriebskosten', 'opex']
            )
            if op_costs:
                extracted_data['financial_data']['operating_costs'] = op_costs
            
            # Suche nach Capital Expenditure
            capex = self.pattern_extractor.find_financial_value(
                table_data, ['capital expenditure', 'capex', 'investitionen']
            )
            if capex:
                extracted_data['financial_data']['capex'] = capex
        
        return extracted_data
    
    async def _process_technical_report(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet technische Berichte"""
        extracted_data = {
            'report_type': 'Technical',
            'file_path': str(pdf_path),
            'processed_at': datetime.now().isoformat(),
            'technical_data': {}
        }
        
        # Volltext für Pattern Matching
        full_text = await self._extract_full_text(pdf_path)
        
        # Technische Daten extrahieren
        tech_data = self.pattern_extractor.extract_technical_data(full_text)
        extracted_data['technical_data'] = tech_data
        
        # Extrahiere technische Tabellen
        tables = await self._extract_all_tables(pdf_path)
        tech_tables = [
            table for table in tables 
            if self.pattern_extractor.is_technical_table(table)
        ]
        extracted_data['technical_tables'] = tech_tables
        
        return extracted_data
    
    async def _process_generic_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Generische PDF-Verarbeitung"""
        extracted_data = {
            'report_type': 'Generic',
            'file_path': str(pdf_path),
            'processed_at': datetime.now().isoformat(),
            'content': {},
            'tables': []
        }
        
        # Volltext extrahieren
        full_text = await self._extract_full_text(pdf_path)
        extracted_data['content']['full_text'] = full_text[:5000]  # Erste 5000 Zeichen
        
        # Mining-relevante Daten suchen
        mining_data = self.pattern_extractor.extract_key_data(full_text)
        extracted_data['mining_data'] = mining_data
        
        # Alle Tabellen extrahieren
        tables = await self._extract_all_tables(pdf_path)
        extracted_data['tables'] = tables
        
        return extracted_data
    
    async def _extract_text_pages(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """Extrahiert Text aus PDF-Seiten mit verfügbarem Extractor"""
        # Priorisiere pdfplumber für bessere Textextraktion
        if self.pdfplumber_extractor.is_available():
            return await self.pdfplumber_extractor.extract_text(pdf_path, max_pages)
        elif self.pypdf2_extractor.is_available():
            return await self.pypdf2_extractor.extract_text(pdf_path, max_pages)
        elif self.ocr_extractor.is_available():
            return await self.ocr_extractor.extract_text(pdf_path, max_pages)
        else:
            self.logger.error("Keine Text-Extraktoren verfügbar")
            return ""
    
    async def _extract_full_text(self, pdf_path: Path) -> str:
        """Extrahiert den gesamten Text aus einem PDF"""
        return await self._extract_text_pages(pdf_path)
    
    async def _extract_table_of_contents(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert das Inhaltsverzeichnis"""
        toc = []
        text = await self._extract_text_pages(pdf_path, max_pages=10)
        
        # Suche nach TOC Mustern
        toc_patterns = [
            r'(\d+\.?\d*)\s+([A-Z][^.]+?)\.+\s*(\d+)',  # 1.1 Section Name........12
            r'([A-Z][^.]+?)\s*\.+\s*(\d+)',  # Section Name........12
            r'(\d+)\.\s+([^.]+?)\s+(\d+)'  # 1. Section Name 12
        ]
        
        for pattern in toc_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                for match in matches:
                    if len(match) == 3:
                        toc.append({
                            'number': match[0],
                            'title': match[1].strip(),
                            'page': int(match[2])
                        })
                    elif len(match) == 2:
                        toc.append({
                            'title': match[0].strip(),
                            'page': int(match[1])
                        })
                break
        
        return toc
    
    async def _extract_section(self, pdf_path: Path, section_name: str, toc: List[Dict]) -> Optional[str]:
        """Extrahiert eine spezifische Sektion basierend auf TOC"""
        # Finde Sektion in TOC
        start_page = None
        end_page = None
        
        for i, entry in enumerate(toc):
            if section_name.lower() in entry['title'].lower():
                start_page = entry['page']
                # Nächste Sektion bestimmt Ende
                if i + 1 < len(toc):
                    end_page = toc[i + 1]['page']
                break
        
        if not start_page:
            # Fallback: Suche im Text
            full_text = await self._extract_full_text(pdf_path)
            section_pattern = rf'{re.escape(section_name)}.*?(?=\n[A-Z][^.]+\n|\Z)'
            match = re.search(section_pattern, full_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0)
            return None
        
        # Extrahiere Seiten mit pdfplumber wenn verfügbar
        if self.pdfplumber_extractor.is_available():
            return await self.pdfplumber_extractor.extract_section(pdf_path, start_page, end_page)
        
        return None
    
    async def _extract_all_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert alle Tabellen aus PDF"""
        tables = []
        
        # Versuche zuerst pdfplumber
        if self.pdfplumber_extractor.is_available():
            tables = await self.pdfplumber_extractor.extract_tables(pdf_path)
        
        # Falls keine Tabellen gefunden, versuche Camelot
        if len(tables) == 0 and self.camelot_extractor.is_available():
            tables = await self.camelot_extractor.extract_tables(pdf_path)
        
        return tables
    
    async def extract_from_url(self, pdf_url: str, mine_name: str) -> Dict[str, Any]:
        """Lädt und verarbeitet PDF von URL"""
        import aiohttp
        import tempfile
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        # Speichere temporär
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                            content = await response.read()
                            tmp_file.write(content)
                            tmp_path = tmp_file.name
                        
                        # Verarbeite PDF
                        result = await self.process_pdf(tmp_path)
                        result['source_url'] = pdf_url
                        result['mine_name'] = mine_name
                        
                        # Lösche temporäre Datei
                        Path(tmp_path).unlink()
                        
                        return result
                    else:
                        self.logger.error(f"Fehler beim Laden von PDF: HTTP {response.status}")
                        return {}
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten von PDF-URL: {e}")
            return {}