"""
Author: rahn
Datum: 21.06.2025
Version: 1.0
Beschreibung: Document Finder für Mining-relevante Dokumente
"""

from typing import List, Dict, Any, Optional
import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse, quote

from .base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from src.utils.pdf_processor import PDFProcessor
from src.core.logger import get_logger


class DocumentFinder(BaseAgent):
    """Agent für das Finden und Verarbeiten von Mining-Dokumenten"""
    
    DOCUMENT_PATTERNS = {
        'technical_reports': [
            'ni 43-101', 'jorc report', 'feasibility study',
            'preliminary economic assessment', 'pea report',
            'technical report', 'resource estimate', 'reserve report'
        ],
        'environmental': [
            'environmental impact', 'eia', 'closure plan',
            'rehabilitation plan', 'water management', 'sustainability report',
            'environmental assessment', 'remediation plan'
        ],
        'financial': [
            'annual report', 'quarterly report', 'md&a',
            'financial statements', 'investor presentation',
            'earnings report', 'financial results'
        ],
        'operational': [
            'production report', 'operational update', 'mine plan',
            'development plan', 'expansion study', 'optimization study'
        ],
        'regulatory': [
            'permit', 'license', 'compliance report', 'regulatory filing',
            'government submission', 'regulatory approval'
        ]
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.pdf_processor = PDFProcessor()
        self.logger = get_logger(f"agent.{name}", agent_type="document_finder")
        self.max_documents = config.get('document_config', {}).get('max_documents', 10)
        
    async def initialize(self) -> bool:
        """Initialisiert den Document Finder"""
        try:
            self.status = AgentStatus.READY
            self.logger.info("Document Finder Agent initialisiert")
            return True
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def validate_credentials(self) -> bool:
        """Document Finder benötigt keine API Credentials"""
        return True
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Sucht nach Dokumenten für die Mine"""
        results = []
        
        # Nutze entdeckte Quellen wenn verfügbar
        discovered_sources = getattr(query, 'discovered_sources', None)
        if discovered_sources:
            # Filtere Dokument-URLs
            doc_urls = [
                s for s in discovered_sources 
                if self._is_document_url(s.url)
            ][:self.max_documents]
            
            # Verarbeite gefundene Dokumente
            for source in doc_urls:
                try:
                    doc_results = await self._process_document(
                        url=source.url,
                        query=query,
                        source_type=source.source_type
                    )
                    results.extend(doc_results)
                except Exception as e:
                    self.logger.error(f"Fehler bei Dokumentverarbeitung {source.url}: {e}")
        
        # Zusätzliche Dokumentsuche
        search_results = await self._search_for_documents(query)
        results.extend(search_results)
        
        # Update Statistiken
        self.stats['total_requests'] += 1
        self.stats['successful_requests'] += 1 if results else 0
        self.stats['total_fields_found'] += len(results)
        
        return results
    
    def _is_document_url(self, url: str) -> bool:
        """Prüft ob URL auf ein Dokument verweist"""
        doc_extensions = ['.pdf', '.xlsx', '.xls', '.doc', '.docx', '.csv']
        url_lower = url.lower()
        
        return any(url_lower.endswith(ext) for ext in doc_extensions)
    
    async def _process_document(self, url: str, query: MineQuery, 
                              source_type: str = 'document') -> List[SearchResult]:
        """Verarbeitet ein gefundenes Dokument"""
        results = []
        
        # Fokus auf PDFs
        if url.lower().endswith('.pdf'):
            # Verarbeite PDF
            pdf_data = await self.pdf_processor.extract_from_url(url, query.mine_name)
            
            if pdf_data:
                # Extrahiere relevante Felder aus PDF-Daten
                key_data = pdf_data.get('key_data', {})
                
                for field in query.required_fields:
                    if field in key_data:
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field,
                            value=str(key_data[field]),
                            source=f"PDF: {pdf_data.get('report_type', 'Document')}",
                            source_url=url,
                            source_date=self._extract_year_from_url(url),
                            confidence_score=0.9,  # Hohe Konfidenz für extrahierte PDF-Daten
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={
                                'document_type': pdf_data.get('report_type'),
                                'extraction_method': 'pdf_processor',
                                'processed_at': pdf_data.get('processed_at')
                            }
                        )
                        results.append(result)
                
                # Spezialbehandlung für Umweltdaten
                if 'environmental_data' in pdf_data:
                    env_data = pdf_data['environmental_data']
                    if 'sanierungskosten' in env_data and 'sanierungskosten' in query.required_fields:
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name='sanierungskosten',
                            value=env_data['sanierungskosten'],
                            source="Environmental Report (PDF)",
                            source_url=url,
                            source_date=self._extract_year_from_url(url),
                            confidence_score=0.95,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={'document_type': 'environmental'}
                        )
                        results.append(result)
                
                # Speichere gefundene Tabellen als separate Ergebnisse
                tables = pdf_data.get('tables', [])
                for table in tables[:3]:  # Max 3 Tabellen
                    if self._is_relevant_table(table, query.required_fields):
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name='data_table',
                            value=f"Table from page {table.get('page', '?')}",
                            source="PDF Table",
                            source_url=url,
                            source_date=self._extract_year_from_url(url),
                            confidence_score=0.7,
                            agent_name=self.name,
                            timestamp=datetime.now(),
                            metadata={
                                'table_data': table.get('data', [])[:5],  # Erste 5 Zeilen
                                'headers': table.get('headers', [])
                            }
                        )
                        results.append(result)
        
        # Andere Dokumenttypen (Excel, Word, etc.)
        elif any(url.lower().endswith(ext) for ext in ['.xlsx', '.xls', '.csv']):
            # Markiere als gefundenes Dokument für spätere Verarbeitung
            result = SearchResult(
                mine_name=query.mine_name,
                field_name='spreadsheet_document',
                value=f"Spreadsheet: {urlparse(url).path.split('/')[-1]}",
                source="Document Discovery",
                source_url=url,
                source_date=self._extract_year_from_url(url),
                confidence_score=0.6,
                agent_name=self.name,
                timestamp=datetime.now(),
                metadata={
                    'document_type': 'spreadsheet',
                    'requires_processing': True
                }
            )
            results.append(result)
        
        return results
    
    async def _search_for_documents(self, query: MineQuery) -> List[SearchResult]:
        """Sucht aktiv nach Dokumenten"""
        results = []
        
        # Erstelle Suchanfragen für verschiedene Dokumenttypen
        search_queries = self._build_document_queries(query.mine_name, query.required_fields)
        
        # Simuliere Dokumentsuche (in echter Implementierung würde hier eine echte Suche stattfinden)
        # Beispiel-URLs für Demonstration
        example_docs = {
            'technical': [
                f"https://example.com/reports/{query.mine_name.lower().replace(' ', '-')}-ni43101-2024.pdf",
                f"https://example.com/technical/{query.mine_name.lower().replace(' ', '-')}-feasibility-study.pdf"
            ],
            'environmental': [
                f"https://example.com/environmental/{query.mine_name.lower().replace(' ', '-')}-eia-report.pdf"
            ],
            'financial': [
                f"https://example.com/investor/{query.mine_name.lower().replace(' ', '-')}-annual-report-2024.pdf"
            ]
        }
        
        # Für Demonstration: Melde gefundene Dokument-Typen
        for doc_type, urls in example_docs.items():
            for url in urls[:1]:  # Nur 1 pro Typ für Demo
                if self._document_likely_exists(query.mine_name, doc_type):
                    result = SearchResult(
                        mine_name=query.mine_name,
                        field_name='document_reference',
                        value=f"{doc_type.title()} Report Available",
                        source="Document Search",
                        source_url=url,
                        source_date=2024,
                        confidence_score=0.5,
                        agent_name=self.name,
                        timestamp=datetime.now(),
                        metadata={
                            'document_type': doc_type,
                            'search_method': 'pattern_based'
                        }
                    )
                    results.append(result)
        
        return results
    
    def _build_document_queries(self, mine_name: str, fields: List[str]) -> Dict[str, List[str]]:
        """Erstellt Suchanfragen für Dokumente"""
        queries = {}
        
        # Basis-Queries
        base_terms = [
            f'"{mine_name}" filetype:pdf',
            f'"{mine_name}" mine report pdf',
            f'"{mine_name}" mining document'
        ]
        
        # Feldspezifische Queries
        if any(field in ['sanierungskosten', 'environmental_cost'] for field in fields):
            queries['environmental'] = [
                f'"{mine_name}" environmental assessment pdf',
                f'"{mine_name}" closure plan pdf',
                f'"{mine_name}" rehabilitation cost pdf'
            ]
        
        if any(field in ['jahresproduktion', 'production'] for field in fields):
            queries['technical'] = [
                f'"{mine_name}" technical report pdf',
                f'"{mine_name}" ni 43-101 pdf',
                f'"{mine_name}" production report pdf'
            ]
        
        if any(field in ['betreiber', 'operator'] for field in fields):
            queries['financial'] = [
                f'"{mine_name}" annual report pdf',
                f'"{mine_name}" company report pdf'
            ]
        
        return queries
    
    def _document_likely_exists(self, mine_name: str, doc_type: str) -> bool:
        """Heuristik ob ein Dokumenttyp wahrscheinlich existiert"""
        # Vereinfachte Heuristik für Demo
        # In echter Implementierung würde hier eine echte Prüfung stattfinden
        
        # Große Minen haben wahrscheinlich alle Dokumenttypen
        major_mines = ['teck', 'barrick', 'newmont', 'bhp', 'rio tinto']
        
        for major in major_mines:
            if major in mine_name.lower():
                return True
        
        # Technical Reports existieren oft
        if doc_type == 'technical':
            return True
        
        # Environmental für aktive Minen
        if doc_type == 'environmental':
            return True
        
        return False
    
    def _is_relevant_table(self, table: Dict, fields: List[str]) -> bool:
        """Prüft ob eine Tabelle relevante Daten enthält"""
        # Prüfe Headers
        headers = table.get('headers', [])
        headers_text = ' '.join(str(h).lower() for h in headers)
        
        # Prüfe ob relevante Felder in Headers
        relevant_keywords = {
            'jahresproduktion': ['production', 'output', 'tonnage'],
            'sanierungskosten': ['closure', 'cost', 'environmental'],
            'betreiber': ['company', 'operator', 'owner'],
            'koordinaten': ['coordinate', 'location', 'latitude'],
            'rohstofftyp': ['commodity', 'mineral', 'product']
        }
        
        for field in fields:
            if field in relevant_keywords:
                keywords = relevant_keywords[field]
                if any(keyword in headers_text for keyword in keywords):
                    return True
        
        return False
    
    def _extract_year_from_url(self, url: str) -> int:
        """Extrahiert Jahr aus URL wenn möglich"""
        # Suche nach Jahreszahlen in URL
        year_match = re.search(r'(20\d{2}|19\d{2})', url)
        if year_match:
            return int(year_match.group(1))
        
        return datetime.now().year
    
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        self.logger.info("Document Finder Agent beendet")