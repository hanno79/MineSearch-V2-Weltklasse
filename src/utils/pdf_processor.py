"""
Author: rahn
Datum: 21.06.2025
Version: 1.0
Beschreibung: PDF Processor für Mining-Dokumente
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib
import json

# PDF-Verarbeitungsbibliotheken
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from ..core.logger import get_logger


class PDFProcessor:
    """Verarbeitet PDF-Dokumente für Mining-Daten"""
    
    def __init__(self):
        self.logger = get_logger("pdf_processor")
        self._check_dependencies()
        
    def _check_dependencies(self):
        """Prüft verfügbare PDF-Bibliotheken"""
        available = []
        if PYPDF2_AVAILABLE:
            available.append("PyPDF2")
        if PDFPLUMBER_AVAILABLE:
            available.append("pdfplumber")
        if CAMELOT_AVAILABLE:
            available.append("camelot")
        if OCR_AVAILABLE:
            available.append("OCR (pytesseract)")
            
        self.logger.info(f"Verfügbare PDF-Bibliotheken: {', '.join(available)}")
        
        if not available:
            self.logger.warning("Keine PDF-Bibliotheken verfügbar! Installation empfohlen: pip install PyPDF2 pdfplumber camelot-py[cv] pytesseract")
    
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
        if pdf_type == 'ni43-101':
            return await self._process_ni43101(pdf_path)
        elif pdf_type == 'environmental':
            return await self._process_environmental_report(pdf_path)
        elif pdf_type == 'financial':
            return await self._process_financial_report(pdf_path)
        elif pdf_type == 'technical':
            return await self._process_technical_report(pdf_path)
        else:
            return await self._process_generic_pdf(pdf_path)
    
    async def _detect_pdf_type(self, pdf_path: Path) -> str:
        """Erkennt den Typ eines PDFs basierend auf Inhalt"""
        # Lese erste Seiten für Typ-Erkennung
        text = await self._extract_text_pages(pdf_path, max_pages=5)
        text_lower = text.lower()
        
        # NI 43-101 Indikatoren
        if any(indicator in text_lower for indicator in ['ni 43-101', 'national instrument 43-101', 'technical report']):
            return 'ni43-101'
        
        # Environmental Report Indikatoren
        elif any(indicator in text_lower for indicator in ['environmental impact', 'eia', 'closure plan', 'rehabilitation']):
            return 'environmental'
        
        # Financial Report Indikatoren
        elif any(indicator in text_lower for indicator in ['financial statements', 'annual report', 'quarterly report', 'md&a']):
            return 'financial'
        
        # Technical Report Indikatoren
        elif any(indicator in text_lower for indicator in ['feasibility study', 'pea', 'preliminary economic assessment', 'resource estimate']):
            return 'technical'
        
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
                    coords = self._extract_coordinates(section_data)
                    if coords:
                        extracted_data['key_data']['coordinates'] = coords
                        
                elif section == 'Mineral Resource Estimate':
                    resources = self._extract_resource_data(section_data)
                    if resources:
                        extracted_data['key_data']['resources'] = resources
                        
                elif section == 'Capital and Operating Costs':
                    costs = self._extract_cost_data(section_data)
                    if costs:
                        extracted_data['key_data']['costs'] = costs
        
        # Extrahiere alle Tabellen
        tables = await self._extract_all_tables(pdf_path)
        extracted_data['tables'] = tables
        
        # Extrahiere Key Mining Data
        key_data = await self._extract_mining_key_data(pdf_path)
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
        env_patterns = {
            'sanierungskosten': [
                r'closure\s+cost[s]?\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
                r'rehabilitation\s+cost[s]?\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
                r'environmental\s+bond\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?'
            ],
            'water_usage': [
                r'water\s+consumption\s*[:=]\s*([\d,]+)\s*(?:m3|cubic\s+meters|litres)',
                r'water\s+usage\s*[:=]\s*([\d,]+)\s*(?:m3|cubic\s+meters|litres)'
            ],
            'land_disturbance': [
                r'disturbed\s+area\s*[:=]\s*([\d,]+(?:\.\d+)?)\s*(?:hectares|ha|km2)',
                r'footprint\s*[:=]\s*([\d,]+(?:\.\d+)?)\s*(?:hectares|ha|km2)'
            ]
        }
        
        for key, patterns in env_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    extracted_data['environmental_data'][key] = matches[0]
                    break
        
        # Extrahiere Tabellen mit Umweltdaten
        tables = await self._extract_all_tables(pdf_path)
        env_tables = []
        
        for table in tables:
            # Prüfe ob Tabelle Umweltdaten enthält
            if self._is_environmental_table(table):
                env_tables.append(table)
        
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
            revenue = self._find_financial_value(table_data, ['revenue', 'umsatz', 'sales'])
            if revenue:
                extracted_data['financial_data']['revenue'] = revenue
            
            # Suche nach Operating Costs
            op_costs = self._find_financial_value(table_data, ['operating cost', 'betriebskosten', 'opex'])
            if op_costs:
                extracted_data['financial_data']['operating_costs'] = op_costs
            
            # Suche nach Capital Expenditure
            capex = self._find_financial_value(table_data, ['capital expenditure', 'capex', 'investitionen'])
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
        tech_patterns = {
            'jahresproduktion': [
                r'annual\s+production\s*[:=]\s*([\d,]+)\s*(?:tonnes|tons|ounces|oz)',
                r'production\s+capacity\s*[:=]\s*([\d,]+)\s*(?:tonnes|tons|ounces|oz)\s*(?:per\s+year|/year|p\.a\.)'
            ],
            'reserve_life': [
                r'mine\s+life\s*[:=]\s*([\d.]+)\s*years',
                r'reserve\s+life\s*[:=]\s*([\d.]+)\s*years'
            ],
            'grade': [
                r'average\s+grade\s*[:=]\s*([\d.]+)\s*(?:%|g/t|ppm)',
                r'head\s+grade\s*[:=]\s*([\d.]+)\s*(?:%|g/t|ppm)'
            ],
            'recovery': [
                r'recovery\s+rate\s*[:=]\s*([\d.]+)\s*%',
                r'metallurgical\s+recovery\s*[:=]\s*([\d.]+)\s*%'
            ]
        }
        
        for key, patterns in tech_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    extracted_data['technical_data'][key] = matches[0]
                    break
        
        # Extrahiere technische Tabellen
        tables = await self._extract_all_tables(pdf_path)
        tech_tables = []
        
        for table in tables:
            if self._is_technical_table(table):
                tech_tables.append(table)
        
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
        mining_data = await self._extract_mining_key_data(pdf_path)
        extracted_data['mining_data'] = mining_data
        
        # Alle Tabellen extrahieren
        tables = await self._extract_all_tables(pdf_path)
        extracted_data['tables'] = tables
        
        return extracted_data
    
    async def _extract_text_pages(self, pdf_path: Path, max_pages: int = None) -> str:
        """Extrahiert Text aus PDF-Seiten"""
        text = ""
        
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    pages_to_read = min(len(pdf.pages), max_pages) if max_pages else len(pdf.pages)
                    for i in range(pages_to_read):
                        page_text = pdf.pages[i].extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                self.logger.error(f"pdfplumber Fehler: {e}")
        
        elif PYPDF2_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    pages_to_read = min(len(reader.pages), max_pages) if max_pages else len(reader.pages)
                    for i in range(pages_to_read):
                        page_text = reader.pages[i].extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                self.logger.error(f"PyPDF2 Fehler: {e}")
        
        return text
    
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
        
        # Extrahiere Seiten
        text = ""
        if PDFPLUMBER_AVAILABLE:
            with pdfplumber.open(pdf_path) as pdf:
                end_page = end_page or len(pdf.pages)
                for i in range(start_page - 1, min(end_page, len(pdf.pages))):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        text += page_text + "\n"
        
        return text
    
    async def _extract_all_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert alle Tabellen aus PDF"""
        tables = []
        
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        page_tables = page.extract_tables()
                        
                        for table_idx, table in enumerate(page_tables):
                            if table and len(table) > 1:  # Mindestens Header + 1 Zeile
                                tables.append({
                                    'page': page_num + 1,
                                    'table_index': table_idx,
                                    'data': table,
                                    'headers': table[0] if table else [],
                                    'rows': len(table) - 1 if table else 0
                                })
            except Exception as e:
                self.logger.error(f"Fehler bei Tabellenextraktion mit pdfplumber: {e}")
        
        # Fallback zu Camelot für komplexe Tabellen
        if CAMELOT_AVAILABLE and len(tables) == 0:
            try:
                camelot_tables = camelot.read_pdf(
                    str(pdf_path),
                    pages='all',
                    flavor='lattice',
                    suppress_stdout=True
                )
                
                for table in camelot_tables:
                    tables.append({
                        'page': table.page,
                        'data': table.df.values.tolist(),
                        'headers': table.df.columns.tolist(),
                        'accuracy': table.accuracy
                    })
            except Exception as e:
                self.logger.error(f"Fehler bei Tabellenextraktion mit Camelot: {e}")
        
        return tables
    
    async def _extract_mining_key_data(self, pdf_path: Path) -> Dict[str, Any]:
        """Extrahiert wichtige Mining-Daten aus PDF"""
        full_text = await self._extract_full_text(pdf_path)
        key_data = {}
        
        # Muster für verschiedene Mining-Daten
        patterns = {
            'betreiber': [
                r'operated\s+by\s+([A-Z][^,.]+(?:\s+[A-Z][^,.]+)*)',
                r'operator\s*[:=]\s*([A-Z][^,.]+(?:\s+[A-Z][^,.]+)*)',
                r'company\s*[:=]\s*([A-Z][^,.]+(?:\s+[A-Z][^,.]+)*)'
            ],
            'koordinaten': [
                r'([\d.]+°[\d.]+\'[\d.]*"?[NS])\s*,?\s*([\d.]+°[\d.]+\'[\d.]*"?[EW])',
                r'latitude\s*[:=]\s*([-]?[\d.]+)\s*,?\s*longitude\s*[:=]\s*([-]?[\d.]+)',
                r'coordinates\s*[:=]\s*([-]?[\d.]+)\s*,\s*([-]?[\d.]+)'
            ],
            'jahresproduktion': [
                r'([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)\s*(?:per\s+year|annually|/year|p\.a\.)',
                r'annual\s+production\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)',
                r'production\s+capacity\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)'
            ],
            'rohstofftyp': [
                r'commodity\s*[:=]\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)',
                r'mineral\s*[:=]\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)',
                r'producing\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?:mine|deposit)'
            ],
            'aktivitaetsstatus': [
                r'status\s*[:=]\s*(active|operating|suspended|closed|care\s+and\s+maintenance)',
                r'mine\s+is\s+(active|operating|suspended|closed|on\s+care\s+and\s+maintenance)',
                r'currently\s+(active|operating|suspended|closed|on\s+care\s+and\s+maintenance)'
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        key_data[field] = ' '.join(matches[0])
                    else:
                        key_data[field] = matches[0]
                    break
        
        return key_data
    
    def _extract_coordinates(self, text: str) -> Optional[str]:
        """Extrahiert Koordinaten aus Text"""
        coord_patterns = [
            r'([\d.]+°[\d.]+\'[\d.]*"?[NS])\s*,?\s*([\d.]+°[\d.]+\'[\d.]*"?[EW])',
            r'latitude\s*[:=]\s*([-]?[\d.]+)\s*,?\s*longitude\s*[:=]\s*([-]?[\d.]+)',
            r'(\d{1,2}°\s*\d{1,2}\'\s*\d{1,2}(?:\.\d+)?"?\s*[NS])\s*,?\s*(\d{1,3}°\s*\d{1,2}\'\s*\d{1,2}(?:\.\d+)?"?\s*[EW])'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)}, {match.group(2)}"
        
        return None
    
    def _extract_resource_data(self, text: str) -> Dict[str, Any]:
        """Extrahiert Ressourcendaten aus Text"""
        resources = {}
        
        # Measured Resources
        measured_pattern = r'measured\s+resources?\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)'
        match = re.search(measured_pattern, text, re.IGNORECASE)
        if match:
            resources['measured'] = match.group(1)
        
        # Indicated Resources
        indicated_pattern = r'indicated\s+resources?\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)'
        match = re.search(indicated_pattern, text, re.IGNORECASE)
        if match:
            resources['indicated'] = match.group(1)
        
        # Inferred Resources
        inferred_pattern = r'inferred\s+resources?\s*[:=]\s*([\d,]+)\s*(?:tonnes?|tons?|ounces?|oz)'
        match = re.search(inferred_pattern, text, re.IGNORECASE)
        if match:
            resources['inferred'] = match.group(1)
        
        return resources
    
    def _extract_cost_data(self, text: str) -> Dict[str, Any]:
        """Extrahiert Kostendaten aus Text"""
        costs = {}
        
        # Capital Costs
        capex_pattern = r'capital\s+cost\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|M)?'
        match = re.search(capex_pattern, text, re.IGNORECASE)
        if match:
            costs['capex'] = match.group(1)
        
        # Operating Costs
        opex_pattern = r'operating\s+cost\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:per\s+(?:tonne|ton|ounce|oz))?'
        match = re.search(opex_pattern, text, re.IGNORECASE)
        if match:
            costs['opex'] = match.group(1)
        
        # All-in Sustaining Costs
        aisc_pattern = r'AISC\s*[:=]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:per\s+(?:ounce|oz))?'
        match = re.search(aisc_pattern, text, re.IGNORECASE)
        if match:
            costs['aisc'] = match.group(1)
        
        return costs
    
    def _is_environmental_table(self, table: Dict) -> bool:
        """Prüft ob eine Tabelle Umweltdaten enthält"""
        env_keywords = [
            'environmental', 'closure', 'rehabilitation', 'water', 
            'emission', 'waste', 'contamination', 'restoration'
        ]
        
        # Prüfe Headers
        headers = table.get('headers', [])
        headers_text = ' '.join(str(h).lower() for h in headers)
        
        return any(keyword in headers_text for keyword in env_keywords)
    
    def _is_technical_table(self, table: Dict) -> bool:
        """Prüft ob eine Tabelle technische Daten enthält"""
        tech_keywords = [
            'production', 'grade', 'recovery', 'tonnage', 'resource',
            'reserve', 'ore', 'mineral', 'capacity', 'throughput'
        ]
        
        headers = table.get('headers', [])
        headers_text = ' '.join(str(h).lower() for h in headers)
        
        return any(keyword in headers_text for keyword in tech_keywords)
    
    def _find_financial_value(self, table_data: List[List], keywords: List[str]) -> Optional[str]:
        """Findet Finanzwerte in Tabellendaten"""
        for row in table_data:
            row_text = ' '.join(str(cell).lower() for cell in row)
            
            for keyword in keywords:
                if keyword in row_text:
                    # Suche nach Zahlen in der Zeile
                    for cell in row:
                        cell_str = str(cell)
                        # Muster für Finanzwerte
                        if re.match(r'^\$?[\d,]+(?:\.\d+)?(?:M|million|B|billion)?$', cell_str):
                            return cell_str
        
        return None
    
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