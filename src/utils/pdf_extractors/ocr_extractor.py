"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: OCR Extractor für gescannte PDFs
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_extractor import BasePDFExtractor
import tempfile

try:
    from PIL import Image
    import pytesseract
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class OCRExtractor(BasePDFExtractor):
    """Extractor für OCR-basierte PDF-Verarbeitung"""
    
    def _check_availability(self) -> bool:
        """Prüft ob OCR-Bibliotheken verfügbar sind"""
        return OCR_AVAILABLE
        
    async def extract_text(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """Extrahiert Text aus gescannten PDFs mit OCR"""
        if not self.available:
            self.logger.warning("OCR-Bibliotheken nicht verfügbar")
            return ""
            
        text = ""
        try:
            # Konvertiere PDF zu Bildern
            images = pdf2image.convert_from_path(pdf_path)
            pages_to_process = min(len(images), max_pages) if max_pages else len(images)
            
            for i in range(pages_to_process):
                # OCR auf jeder Seite
                page_text = pytesseract.image_to_string(images[i], lang='eng+deu')
                if page_text:
                    text += f"--- Seite {i+1} ---\n{page_text}\n"
                    
        except Exception as e:
            self.logger.error(f"OCR Fehler beim Textextraktion: {e}")
            
        return text
        
    async def extract_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """OCR ist nicht optimal für Tabellenextraktion"""
        self.logger.info("OCR-basierte Tabellenextraktion nicht implementiert")
        return []
        
    async def extract_text_from_image_pdf(self, pdf_path: Path, language: str = 'eng+deu') -> str:
        """Spezialisierte Methode für Bild-PDFs mit Sprachauswahl"""
        if not self.available:
            return ""
            
        text = ""
        try:
            images = pdf2image.convert_from_path(pdf_path)
            
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang=language)
                if page_text:
                    text += f"--- Seite {i+1} ---\n{page_text}\n"
                    
        except Exception as e:
            self.logger.error(f"OCR Fehler: {e}")
            
        return text