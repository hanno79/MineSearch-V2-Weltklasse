"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Haupt PDF Processor - Refactored
"""

import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .base import PDFLibraryChecker, PDFTypeDetector
from .extractors import TextExtractor, TableExtractor, MetadataExtractor
from .document_types import (
    NI43101Processor,
    EnvironmentalReportProcessor,
    FinancialReportProcessor,
    TechnicalReportProcessor
)
from ...core.logger import get_logger


class PDFProcessor:
    """
    Haupt-Klasse für PDF-Verarbeitung
    
    Refactored: Delegiert an spezialisierte Prozessoren
    """
    
    def __init__(self):
        self.logger = get_logger("pdf_processor")
        
        # Prüfe Abhängigkeiten
        self.libraries = PDFLibraryChecker.check_dependencies(self.logger)
        
        # Initialisiere Komponenten
        self.text_extractor = TextExtractor(self.logger)
        self.table_extractor = TableExtractor(self.logger)
        self.metadata_extractor = MetadataExtractor(self.logger)
        
        # Spezialisierte Prozessoren
        self.processors = {
            'ni43-101': NI43101Processor(),
            'environmental': EnvironmentalReportProcessor(),
            'financial': FinancialReportProcessor(),
            'technical': TechnicalReportProcessor()
        }
        
        # Cache für verarbeitete PDFs
        self.cache = {}
        self.cache_ttl = 3600  # 1 Stunde
    
    async def process_pdf(self, 
                         pdf_path: str, 
                         pdf_type: str = 'auto',
                         force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Hauptmethode für PDF-Verarbeitung
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            pdf_type: Typ des PDFs ('auto' für automatische Erkennung)
            force_reprocess: Cache ignorieren
            
        Returns:
            Dictionary mit extrahierten Daten
        """
        pdf_path = Path(pdf_path)
        
        # Cache prüfen
        cache_key = f"{pdf_path}_{pdf_type}"
        if not force_reprocess and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                self.logger.info(f"Verwende gecachte Daten für {pdf_path.name}")
                return cached_data
        
        # Validierung
        if not pdf_path.exists():
            self.logger.error(f"PDF nicht gefunden: {pdf_path}")
            return {"error": "PDF nicht gefunden", "success": False}
        
        if not any(self.libraries.values()):
            self.logger.error("Keine PDF-Bibliotheken verfügbar")
            return {"error": "Keine PDF-Bibliotheken installiert", "success": False}
        
        # Typ erkennen
        if pdf_type == 'auto':
            pdf_type = await self._detect_pdf_type(pdf_path)
            self.logger.info(f"Erkannter PDF-Typ: {pdf_type}")
        
        # Verarbeitung delegieren
        try:
            if pdf_type in self.processors:
                result = await self.processors[pdf_type].process(pdf_path)
            else:
                result = await self._process_generic_pdf(pdf_path)
            
            # Cache speichern
            self.cache[cache_key] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            self.logger.error(f"PDF-Verarbeitung fehlgeschlagen: {e}")
            return {
                "error": str(e),
                "success": False,
                "pdf_type": pdf_type
            }
    
    async def _detect_pdf_type(self, pdf_path: Path) -> str:
        """Erkennt den Typ eines PDFs"""
        try:
            # Extrahiere Text für Analyse
            text = await self.text_extractor.extract_text(pdf_path, max_pages=5)
            
            # Nutze TypeDetector
            pdf_type = PDFTypeDetector.detect_type(text, pdf_path.name)
            
            return pdf_type
            
        except Exception as e:
            self.logger.warning(f"Typ-Erkennung fehlgeschlagen: {e}")
            return 'generic'
    
    async def _process_generic_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Generische PDF-Verarbeitung"""
        result = {
            'pdf_type': 'generic',
            'success': True,
            'data': {},
            'metadata': {},
            'errors': []
        }
        
        try:
            # Metadaten
            metadata = await self.metadata_extractor.extract_metadata(pdf_path)
            result['metadata'] = metadata
            
            # Text
            text = await self.text_extractor.extract_text(pdf_path)
            sections = self.text_extractor.extract_sections(text)
            
            result['data']['text_length'] = len(text)
            result['data']['sections'] = list(sections.keys())
            result['data']['preview'] = text[:1000]  # Erste 1000 Zeichen
            
            # Tabellen
            tables = await self.table_extractor.extract_tables(pdf_path)
            result['data']['table_count'] = len(tables)
            
            if tables:
                # Zusammenfassung der Tabellen
                result['data']['tables_summary'] = [
                    {
                        'page': t['page'],
                        'rows': len(t.get('data', [])),
                        'method': t.get('method', 'unknown')
                    }
                    for t in tables[:5]  # Max 5 Tabellen
                ]
            
            # Mining-relevante Informationen suchen
            mining_info = await self._extract_mining_info(text)
            if mining_info:
                result['data']['mining_info'] = mining_info
            
        except Exception as e:
            result['errors'].append(str(e))
            result['success'] = False
            self.logger.error(f"Generische Verarbeitung fehlgeschlagen: {e}")
        
        return result
    
    async def _extract_mining_info(self, text: str) -> Dict[str, Any]:
        """Extrahiert allgemeine Mining-Informationen"""
        import re
        
        mining_info = {}
        
        # Rohstoffe/Mineralien
        minerals = []
        mineral_pattern = r'\b(gold|silver|copper|iron|coal|uranium|zinc|lead|nickel|platinum)\b'
        mineral_matches = re.findall(mineral_pattern, text, re.IGNORECASE)
        if mineral_matches:
            minerals = list(set(m.lower() for m in mineral_matches))
            mining_info['minerals'] = minerals
        
        # Produktionszahlen
        production_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:tonnes?|tons?|ounces?|oz)\s*(?:per\s*year|annually)?'
        production_matches = re.findall(production_pattern, text, re.IGNORECASE)
        if production_matches:
            mining_info['production_mentions'] = production_matches[:5]
        
        # Unternehmensnamen
        company_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Mining|Metals|Resources|Minerals)'
        company_matches = re.findall(company_pattern, text)
        if company_matches:
            mining_info['companies'] = list(set(company_matches))[:5]
        
        return mining_info if mining_info else None
    
    async def process_multiple_pdfs(self, 
                                  pdf_paths: List[str],
                                  max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Verarbeitet mehrere PDFs parallel
        
        Args:
            pdf_paths: Liste von PDF-Pfaden
            max_concurrent: Maximale gleichzeitige Verarbeitungen
            
        Returns:
            Liste von Verarbeitungsergebnissen
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(pdf_path):
            async with semaphore:
                return await self.process_pdf(pdf_path)
        
        tasks = [process_with_semaphore(path) for path in pdf_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Exceptions zu Fehlern konvertieren
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'error': str(result),
                    'success': False,
                    'pdf_path': pdf_paths[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_supported_types(self) -> List[str]:
        """Gibt unterstützte PDF-Typen zurück"""
        return list(self.processors.keys()) + ['generic']
    
    def clear_cache(self):
        """Leert den Cache"""
        self.cache.clear()
        self.logger.info("PDF-Cache geleert")