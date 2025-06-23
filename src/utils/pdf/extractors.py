"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Extraktoren für verschiedene PDF-Inhalte
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from .base import (
    PYPDF2_AVAILABLE, PDFPLUMBER_AVAILABLE, 
    CAMELOT_AVAILABLE, OCR_AVAILABLE,
    ExtractionResult
)


class TextExtractor:
    """Extrahiert Text aus PDFs"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def extract_text(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """Extrahiert Text aus PDF"""
        text = ""
        
        # Versuche pdfplumber zuerst (beste Qualität)
        if PDFPLUMBER_AVAILABLE:
            try:
                text = await self._extract_with_pdfplumber(pdf_path, max_pages)
                if text.strip():
                    return text
            except Exception as e:
                self.logger.warning(f"pdfplumber fehlgeschlagen: {e}")
        
        # Fallback zu PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                text = await self._extract_with_pypdf2(pdf_path, max_pages)
                if text.strip():
                    return text
            except Exception as e:
                self.logger.warning(f"PyPDF2 fehlgeschlagen: {e}")
        
        # OCR als letzter Versuch
        if OCR_AVAILABLE and not text.strip():
            try:
                text = await self._extract_with_ocr(pdf_path, max_pages)
            except Exception as e:
                self.logger.warning(f"OCR fehlgeschlagen: {e}")
        
        return text
    
    async def _extract_with_pdfplumber(self, pdf_path: Path, max_pages: Optional[int]) -> str:
        """Extrahiert Text mit pdfplumber"""
        import pdfplumber
        
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_process = min(len(pdf.pages), max_pages) if max_pages else len(pdf.pages)
            
            for i in range(pages_to_process):
                page = pdf.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    async def _extract_with_pypdf2(self, pdf_path: Path, max_pages: Optional[int]) -> str:
        """Extrahiert Text mit PyPDF2"""
        import PyPDF2
        
        text_parts = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages_to_process = min(len(pdf_reader.pages), max_pages) if max_pages else len(pdf_reader.pages)
            
            for i in range(pages_to_process):
                page = pdf_reader.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    async def _extract_with_ocr(self, pdf_path: Path, max_pages: Optional[int]) -> str:
        """Extrahiert Text mit OCR"""
        # Implementierung für OCR (vereinfacht)
        self.logger.info("OCR-Extraktion noch nicht implementiert")
        return ""
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extrahiert Sektionen aus Text"""
        sections = {}
        
        # Typische Sektions-Muster
        section_patterns = [
            r'^\d+\.?\s+([A-Z][A-Z\s]+)$',  # 1. INTRODUCTION
            r'^([A-Z][A-Z\s]+):?\s*$',      # EXECUTIVE SUMMARY:
            r'^\d+\.\d+\.?\s+(.+)$',        # 1.1 Overview
        ]
        
        current_section = "Introduction"
        current_content = []
        
        lines = text.split('\n')
        for line in lines:
            # Prüfe ob neue Sektion
            is_section = False
            for pattern in section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Speichere vorherige Sektion
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Neue Sektion
                    current_section = match.group(1).strip()
                    current_content = []
                    is_section = True
                    break
            
            if not is_section and line.strip():
                current_content.append(line)
        
        # Letzte Sektion
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections


class TableExtractor:
    """Extrahiert Tabellen aus PDFs"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def extract_tables(self, pdf_path: Path, pages: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Extrahiert alle Tabellen"""
        tables = []
        
        # Camelot ist am besten für Tabellen
        if CAMELOT_AVAILABLE:
            try:
                tables.extend(await self._extract_with_camelot(pdf_path, pages))
            except Exception as e:
                self.logger.warning(f"Camelot fehlgeschlagen: {e}")
        
        # pdfplumber als Fallback
        if PDFPLUMBER_AVAILABLE and not tables:
            try:
                tables.extend(await self._extract_with_pdfplumber_tables(pdf_path, pages))
            except Exception as e:
                self.logger.warning(f"pdfplumber Tabellen fehlgeschlagen: {e}")
        
        return tables
    
    async def _extract_with_camelot(self, pdf_path: Path, pages: Optional[List[int]]) -> List[Dict[str, Any]]:
        """Extrahiert Tabellen mit Camelot"""
        import camelot
        
        tables_data = []
        
        # Seiten-String für Camelot
        if pages:
            pages_str = ','.join(str(p) for p in pages)
        else:
            pages_str = 'all'
        
        # Versuche beide Methoden
        for flavor in ['stream', 'lattice']:
            try:
                tables = camelot.read_pdf(str(pdf_path), pages=pages_str, flavor=flavor)
                
                for i, table in enumerate(tables):
                    table_data = {
                        'page': table.page,
                        'data': table.df.to_dict('records'),
                        'accuracy': table.accuracy,
                        'method': f'camelot_{flavor}'
                    }
                    tables_data.append(table_data)
                    
            except Exception as e:
                self.logger.debug(f"Camelot {flavor} fehlgeschlagen: {e}")
        
        return tables_data
    
    async def _extract_with_pdfplumber_tables(self, pdf_path: Path, pages: Optional[List[int]]) -> List[Dict[str, Any]]:
        """Extrahiert Tabellen mit pdfplumber"""
        import pdfplumber
        
        tables_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_check = pages if pages else range(len(pdf.pages))
            
            for page_num in pages_to_check:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    page_tables = page.extract_tables()
                    
                    for i, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Mindestens Header + 1 Zeile
                            table_data = {
                                'page': page_num + 1,
                                'data': self._table_to_dict(table),
                                'accuracy': 0.8,  # Geschätzt
                                'method': 'pdfplumber'
                            }
                            tables_data.append(table_data)
        
        return tables_data
    
    def _table_to_dict(self, table: List[List[str]]) -> List[Dict[str, str]]:
        """Konvertiert Tabellen-Array zu Dict"""
        if not table or len(table) < 2:
            return []
        
        headers = [str(h).strip() for h in table[0]]
        rows = []
        
        for row in table[1:]:
            row_dict = {}
            for i, cell in enumerate(row):
                if i < len(headers):
                    row_dict[headers[i]] = str(cell).strip() if cell else ''
            rows.append(row_dict)
        
        return rows


class MetadataExtractor:
    """Extrahiert Metadaten aus PDFs"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extrahiert PDF-Metadaten"""
        metadata = {}
        
        # Basis-Informationen
        metadata['filename'] = pdf_path.name
        metadata['file_size'] = pdf_path.stat().st_size
        metadata['file_modified'] = pdf_path.stat().st_mtime
        
        # PDF-spezifische Metadaten
        if PYPDF2_AVAILABLE:
            try:
                metadata.update(await self._extract_with_pypdf2_metadata(pdf_path))
            except Exception as e:
                self.logger.warning(f"Metadaten-Extraktion fehlgeschlagen: {e}")
        
        return metadata
    
    async def _extract_with_pypdf2_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extrahiert Metadaten mit PyPDF2"""
        import PyPDF2
        
        metadata = {}
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Seitenzahl
            metadata['page_count'] = len(pdf_reader.pages)
            
            # Dokumentinfo
            if pdf_reader.metadata:
                info = pdf_reader.metadata
                
                # Standard-Felder
                if info.title:
                    metadata['title'] = info.title
                if info.author:
                    metadata['author'] = info.author
                if info.subject:
                    metadata['subject'] = info.subject
                if info.creator:
                    metadata['creator'] = info.creator
                if info.producer:
                    metadata['producer'] = info.producer
                
                # Datum
                if hasattr(info, 'creation_date'):
                    metadata['creation_date'] = str(info.creation_date)
                if hasattr(info, 'modification_date'):
                    metadata['modification_date'] = str(info.modification_date)
        
        return metadata