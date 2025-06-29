"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Spezialisierter Prozessor für Financial Reports
"""

import re
from typing import Dict, List, Any
from pathlib import Path

from ..base import BasePDFProcessor, ExtractionResult
from ..extractors import TextExtractor, TableExtractor
from ....core.logger import get_logger


class FinancialReportProcessor(BasePDFProcessor):
    """Prozessor für Financial Reports"""
    
    def __init__(self):
        logger = get_logger("financial_processor")
        super().__init__(logger)
        self.text_extractor = TextExtractor(logger)
        self.table_extractor = TableExtractor(logger)
    
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet Financial Report"""
        result = ExtractionResult("financial")
        
        if not self.can_process(pdf_path):
            result.add_error("Kann PDF nicht verarbeiten")
            return result.to_dict()
        
        try:
            # Text und Tabellen
            text = await self.text_extractor.extract_text(pdf_path)
            tables = await self.table_extractor.extract_tables(pdf_path)
            
            # Financial-spezifische Extraktion
            result.add_data("financial_highlights", self._extract_highlights(text))
            result.add_data("revenue_data", self._extract_revenue(text, tables))
            result.add_data("cost_breakdown", self._extract_costs(text, tables))
            result.add_data("key_metrics", self._extract_key_metrics(text))
            
        except Exception as e:
            result.add_error(f"Verarbeitungsfehler: {str(e)}")
            self.logger.error(f"Fehler bei Financial Report: {e}")
        
        return result.to_dict()
    
    def _extract_highlights(self, text: str) -> Dict[str, str]:
        """Extrahiert Financial Highlights"""
        highlights = {}
        
        # Währungsmuster
        currency_pattern = r'\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|M|B)?'
        
        # Key Financial Terms
        terms = {
            'revenue': r'revenue[s]?\s*:?\s*' + currency_pattern,
            'ebitda': r'ebitda\s*:?\s*' + currency_pattern,
            'net_income': r'net\s+income\s*:?\s*' + currency_pattern,
            'cash_flow': r'cash\s+flow\s*:?\s*' + currency_pattern,
        }
        
        for key, pattern in terms.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                highlights[key] = match.group(0)
        
        return highlights
    
    def _extract_revenue(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrahiert Revenue-Daten"""
        revenue_data = {}
        
        # Aus Tabellen
        for table in tables:
            data = table.get('data', [])
            if not data:
                continue
            
            # Suche Revenue-Tabelle
            headers = list(data[0].keys()) if data else []
            if any('revenue' in h.lower() for h in headers):
                revenue_data['table_data'] = data[:10]  # Max 10 Zeilen
                break
        
        return revenue_data
    
    def _extract_costs(self, text: str, tables: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extrahiert Kosten-Breakdown"""
        costs = {}
        
        # Cost-Kategorien
        cost_types = {
            'operating_costs': r'operating\s+cost[s]?\s*:?\s*\$?[\d,]+',
            'capital_costs': r'capital\s+cost[s]?\s*:?\s*\$?[\d,]+',
            'cash_costs': r'cash\s+cost[s]?\s*:?\s*\$?[\d,]+',
            'aisc': r'aisc\s*:?\s*\$?[\d,]+',
        }
        
        for key, pattern in cost_types.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                costs[key] = match.group(0)
        
        return costs
    
    def _extract_key_metrics(self, text: str) -> Dict[str, str]:
        """Extrahiert Key Performance Metrics"""
        metrics = {}
        
        # Metriken
        metric_patterns = {
            'production': r'production\s*:?\s*(\d+(?:,\d{3})*)\s*(?:ounces|oz|tonnes|tons)',
            'grade': r'grade\s*:?\s*(\d+(?:\.\d+)?)\s*(?:g/t|ppm|%)',
            'recovery': r'recovery\s*:?\s*(\d+(?:\.\d+)?)\s*%',
        }
        
        for key, pattern in metric_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics[key] = match.group(0)
        
        return metrics