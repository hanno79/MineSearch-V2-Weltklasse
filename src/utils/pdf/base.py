"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Basis-Klassen für PDF Processing
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# PDF-Bibliothek Verfügbarkeit prüfen
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


class PDFLibraryChecker:
    """Prüft verfügbare PDF-Bibliotheken"""
    
    @staticmethod
    def get_available_libraries() -> Dict[str, bool]:
        """Gibt verfügbare Bibliotheken zurück"""
        return {
            'PyPDF2': PYPDF2_AVAILABLE,
            'pdfplumber': PDFPLUMBER_AVAILABLE,
            'camelot': CAMELOT_AVAILABLE,
            'OCR': OCR_AVAILABLE
        }
    
    @staticmethod
    def check_dependencies(logger: logging.Logger):
        """Prüft und loggt verfügbare Bibliotheken"""
        available = []
        libraries = PDFLibraryChecker.get_available_libraries()
        
        for lib, is_available in libraries.items():
            if is_available:
                available.append(lib)
        
        logger.info(f"Verfügbare PDF-Bibliotheken: {', '.join(available)}")
        
        if not available:
            logger.warning(
                "Keine PDF-Bibliotheken verfügbar! Installation empfohlen: "
                "pip install PyPDF2 pdfplumber camelot-py[cv] pytesseract"
            )
        
        return libraries


class BasePDFProcessor(ABC):
    """Abstrakte Basis-Klasse für PDF-Prozessoren"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.libraries = PDFLibraryChecker.get_available_libraries()
    
    @abstractmethod
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet PDF-Datei"""
        pass
    
    def can_process(self, pdf_path: Path) -> bool:
        """Prüft ob Datei verarbeitet werden kann"""
        if not pdf_path.exists():
            self.logger.error(f"PDF nicht gefunden: {pdf_path}")
            return False
        
        if not pdf_path.suffix.lower() == '.pdf':
            self.logger.error(f"Keine PDF-Datei: {pdf_path}")
            return False
        
        if not any(self.libraries.values()):
            self.logger.error("Keine PDF-Bibliotheken verfügbar")
            return False
        
        return True


class PDFTypeDetector:
    """Erkennt PDF-Dokumenttypen"""
    
    # Typ-Erkennungsmuster
    TYPE_PATTERNS = {
        'ni43-101': [
            r'ni\s*43-?101',
            r'national\s+instrument\s+43-?101',
            r'technical\s+report.*mineral\s+resource',
            r'qualified\s+person',
            r'mineral\s+resource\s+estimate'
        ],
        'environmental': [
            r'environmental\s+impact',
            r'eia\s+report',
            r'environmental\s+assessment',
            r'environmental\s+management\s+plan',
            r'biodiversity'
        ],
        'financial': [
            r'financial\s+statement',
            r'annual\s+report',
            r'quarterly\s+report',
            r'financial\s+results',
            r'balance\s+sheet'
        ],
        'technical': [
            r'technical\s+report',
            r'feasibility\s+study',
            r'engineering\s+report',
            r'metallurgical\s+test',
            r'geological\s+report'
        ],
        'permit': [
            r'mining\s+permit',
            r'environmental\s+permit',
            r'license\s+application',
            r'regulatory\s+approval',
            r'permit\s+number'
        ]
    }
    
    @classmethod
    def detect_type(cls, text: str, filename: str = '') -> str:
        """Erkennt Dokumenttyp basierend auf Text und Dateiname"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Prüfe Muster
        for doc_type, patterns in cls.TYPE_PATTERNS.items():
            for pattern in patterns:
                import re
                if re.search(pattern, text_lower) or re.search(pattern, filename_lower):
                    return doc_type
        
        # Standard
        return 'generic'


class ExtractionResult:
    """Container für Extraktionsergebnisse"""
    
    def __init__(self, content_type: str):
        self.content_type = content_type
        self.data = {}
        self.metadata = {}
        self.errors = []
        self.warnings = []
    
    def add_data(self, key: str, value: Any):
        """Fügt Daten hinzu"""
        self.data[key] = value
    
    def add_metadata(self, key: str, value: Any):
        """Fügt Metadaten hinzu"""
        self.metadata[key] = value
    
    def add_error(self, error: str):
        """Fügt Fehler hinzu"""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Fügt Warnung hinzu"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'content_type': self.content_type,
            'data': self.data,
            'metadata': self.metadata,
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }