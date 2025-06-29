"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: PyPDF2 Extractor für PDF-Verarbeitung
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_extractor import BasePDFExtractor

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


class PyPDF2Extractor(BasePDFExtractor):
    """Extractor für PDF-Verarbeitung mit PyPDF2"""
    
    def _check_availability(self) -> bool:
        """Prüft ob PyPDF2 verfügbar ist"""
        return PYPDF2_AVAILABLE
        
    async def extract_text(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """Extrahiert Text aus PDF mit PyPDF2"""
        if not self.available:
            self.logger.warning("PyPDF2 nicht verfügbar")
            return ""
            
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                pages_to_read = min(len(reader.pages), max_pages) if max_pages else len(reader.pages)
                
                for i in range(pages_to_read):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
        except Exception as e:
            self.logger.error(f"PyPDF2 Fehler beim Textextraktion: {e}")
            
        return text
        
    async def extract_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """PyPDF2 unterstützt keine direkte Tabellenextraktion"""
        self.logger.info("PyPDF2 unterstützt keine Tabellenextraktion")
        return []