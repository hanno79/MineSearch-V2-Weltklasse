"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: PDFPlumber Extractor für PDF-Verarbeitung mit Tabellen
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_extractor import BasePDFExtractor

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class PDFPlumberExtractor(BasePDFExtractor):
    """Extractor für PDF-Verarbeitung mit pdfplumber"""
    
    def _check_availability(self) -> bool:
        """Prüft ob pdfplumber verfügbar ist"""
        return PDFPLUMBER_AVAILABLE
        
    async def extract_text(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """Extrahiert Text aus PDF mit pdfplumber"""
        if not self.available:
            self.logger.warning("pdfplumber nicht verfügbar")
            return ""
            
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_to_read = min(len(pdf.pages), max_pages) if max_pages else len(pdf.pages)
                
                for i in range(pages_to_read):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
        except Exception as e:
            self.logger.error(f"pdfplumber Fehler beim Textextraktion: {e}")
            
        return text
        
    async def extract_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert Tabellen aus PDF mit pdfplumber"""
        if not self.available:
            self.logger.warning("pdfplumber nicht verfügbar")
            return []
            
        tables = []
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
            self.logger.error(f"pdfplumber Fehler bei Tabellenextraktion: {e}")
            
        return tables
        
    async def extract_section(self, pdf_path: Path, start_page: int, end_page: Optional[int] = None) -> str:
        """Extrahiert Text von bestimmten Seiten"""
        if not self.available:
            return ""
            
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                end_page = end_page or len(pdf.pages)
                
                for i in range(start_page - 1, min(end_page, len(pdf.pages))):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
        except Exception as e:
            self.logger.error(f"pdfplumber Fehler bei Sektionsextraktion: {e}")
            
        return text