"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Camelot Extractor für komplexe Tabellenextraktion
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_extractor import BasePDFExtractor

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False


class CamelotExtractor(BasePDFExtractor):
    """Extractor für komplexe Tabellenextraktion mit Camelot"""
    
    def _check_availability(self) -> bool:
        """Prüft ob Camelot verfügbar ist"""
        return CAMELOT_AVAILABLE
        
    async def extract_text(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """Camelot ist primär für Tabellen, nicht für Text"""
        self.logger.info("Camelot ist für Tabellenextraktion optimiert, nicht für Text")
        return ""
        
    async def extract_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrahiert Tabellen aus PDF mit Camelot"""
        if not self.available:
            self.logger.warning("Camelot nicht verfügbar")
            return []
            
        tables = []
        try:
            # Versuche erst lattice-Methode (für Tabellen mit Linien)
            camelot_tables = camelot.read_pdf(
                str(pdf_path),
                pages='all',
                flavor='lattice',
                suppress_stdout=True
            )
            
            # Falls keine Tabellen gefunden, versuche stream-Methode
            if len(camelot_tables) == 0:
                camelot_tables = camelot.read_pdf(
                    str(pdf_path),
                    pages='all',
                    flavor='stream',
                    suppress_stdout=True
                )
            
            for table in camelot_tables:
                tables.append({
                    'page': table.page,
                    'data': table.df.values.tolist(),
                    'headers': table.df.columns.tolist(),
                    'accuracy': table.accuracy,
                    'extraction_method': 'camelot'
                })
                
        except Exception as e:
            self.logger.error(f"Camelot Fehler bei Tabellenextraktion: {e}")
            
        return tables