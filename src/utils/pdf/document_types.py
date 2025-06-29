"""
Author: rahn
Datum: 27.06.2025
Version: 2.0
Beschreibung: Zentrale Verwaltung für spezialisierte Dokumenttyp-Prozessoren
"""

# ÄNDERUNG 27.06.2025: Refactoring - Prozessoren in separate Module ausgelagert
# Die spezialisierten Prozessoren wurden in einzelne Dateien im processors/ Verzeichnis verschoben

from typing import Dict, Type, Optional
from pathlib import Path
from datetime import datetime

from .base import BasePDFProcessor
from .processors import (
    NI43101Processor,
    EnvironmentalReportProcessor,
    FinancialReportProcessor,
    TechnicalReportProcessor
)
from ...core.logger import get_logger


class DocumentTypeManager:
    """
    Verwaltet verschiedene Dokumenttyp-Prozessoren und wählt 
    den passenden Prozessor basierend auf dem Dokumenttyp aus
    """
    
    def __init__(self):
        self.logger = get_logger("document_type_manager")
        self._processors: Dict[str, Type[BasePDFProcessor]] = {
            'ni43-101': NI43101Processor,
            'environmental': EnvironmentalReportProcessor,
            'financial': FinancialReportProcessor,
            'technical': TechnicalReportProcessor,
        }
        self._processor_instances: Dict[str, BasePDFProcessor] = {}
    
    def get_processor(self, doc_type: str) -> Optional[BasePDFProcessor]:
        """
        Gibt den passenden Prozessor für einen Dokumenttyp zurück
        
        Args:
            doc_type: Der Dokumenttyp (z.B. 'ni43-101', 'environmental')
            
        Returns:
            Der passende Prozessor oder None wenn nicht gefunden
        """
        doc_type = doc_type.lower()
        
        # Prüfe ob Prozessor-Typ existiert
        if doc_type not in self._processors:
            self.logger.warning(f"Kein Prozessor für Dokumenttyp '{doc_type}' gefunden")
            return None
        
        # Erstelle Instanz wenn noch nicht vorhanden (Singleton-Pattern)
        if doc_type not in self._processor_instances:
            processor_class = self._processors[doc_type]
            self._processor_instances[doc_type] = processor_class()
            self.logger.info(f"Prozessor für '{doc_type}' erstellt")
        
        return self._processor_instances[doc_type]
    
    def detect_document_type(self, pdf_path: Path) -> str:
        """
        Versucht den Dokumenttyp anhand des Dateinamens und Inhalts zu erkennen
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Erkannter Dokumenttyp oder 'technical' als Fallback
        """
        filename = pdf_path.name.lower()
        
        # Erkennung anhand des Dateinamens
        if any(term in filename for term in ['ni43-101', 'ni_43_101', 'technical_report']):
            return 'ni43-101'
        elif any(term in filename for term in ['environmental', 'esia', 'eis']):
            return 'environmental'
        elif any(term in filename for term in ['financial', 'annual_report', 'quarterly']):
            return 'financial'
        
        # Standard-Fallback
        return 'technical'
    
    def list_available_processors(self) -> Dict[str, str]:
        """
        Listet alle verfügbaren Prozessoren mit Beschreibungen auf
        
        Returns:
            Dictionary mit Prozessor-Namen und Beschreibungen
        """
        descriptions = {
            'ni43-101': 'NI 43-101 Technical Reports (Mining)',
            'environmental': 'Environmental Impact Assessments',
            'financial': 'Financial Reports and Statements',
            'technical': 'General Technical Documents'
        }
        
        return {
            doc_type: descriptions.get(doc_type, 'No description available')
            for doc_type in self._processors.keys()
        }
    
    def register_processor(self, doc_type: str, processor_class: Type[BasePDFProcessor]):
        """
        Registriert einen neuen Prozessor-Typ
        
        Args:
            doc_type: Der Dokumenttyp-Bezeichner
            processor_class: Die Prozessor-Klasse
        """
        if not issubclass(processor_class, BasePDFProcessor):
            raise ValueError(f"{processor_class} muss von BasePDFProcessor erben")
        
        self._processors[doc_type.lower()] = processor_class
        
        # Entferne existierende Instanz um Neuinitialisierung zu erzwingen
        if doc_type.lower() in self._processor_instances:
            del self._processor_instances[doc_type.lower()]
        
        self.logger.info(f"Prozessor für '{doc_type}' registriert")
    
    async def process_document(self, pdf_path: Path, doc_type: Optional[str] = None) -> Dict[str, any]:
        """
        Verarbeitet ein Dokument mit dem passenden Prozessor
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            doc_type: Optionaler Dokumenttyp, wird automatisch erkannt wenn nicht angegeben
            
        Returns:
            Extraktionsergebnis
        """
        # Dokumenttyp erkennen wenn nicht angegeben
        if doc_type is None:
            doc_type = self.detect_document_type(pdf_path)
            self.logger.info(f"Automatisch erkannter Dokumenttyp: {doc_type}")
        
        # Prozessor abrufen
        processor = self.get_processor(doc_type)
        if processor is None:
            # Fallback auf Technical Processor
            self.logger.warning(f"Verwende Technical Processor als Fallback")
            processor = self.get_processor('technical')
        
        # Dokument verarbeiten
        start_time = datetime.now()
        result = await processor.process(pdf_path)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Processing-Metadaten hinzufügen
        if isinstance(result, dict):
            result['processing_info'] = {
                'document_type': doc_type,
                'processor': processor.__class__.__name__,
                'processing_time_seconds': processing_time,
                'timestamp': datetime.now().isoformat()
            }
        
        return result


# Globale Instanz für einfachen Zugriff
document_manager = DocumentTypeManager()


# Export für Rückwärtskompatibilität
__all__ = [
    'DocumentTypeManager',
    'document_manager',
    'NI43101Processor',
    'EnvironmentalReportProcessor', 
    'FinancialReportProcessor',
    'TechnicalReportProcessor'
]