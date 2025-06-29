"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Basis-Klasse für PDF Extractors
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from ...core.logger import get_logger


class BasePDFExtractor(ABC):
    """Abstrakte Basisklasse für PDF Extractors"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.available = self._check_availability()
        
    @abstractmethod
    def _check_availability(self) -> bool:
        """Prüft ob die benötigten Bibliotheken verfügbar sind"""
        pass
        
    @abstractmethod
    async def extract_text(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """Extrahiert Text aus PDF"""
        pass
        
    @abstractmethod
    async def extract_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert Tabellen aus PDF"""
        pass
        
    def is_available(self) -> bool:
        """Gibt zurück ob der Extractor verfügbar ist"""
        return self.available