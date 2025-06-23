"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Spezialisierte Prozessoren für verschiedene Dokumenttypen
"""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .base import BasePDFProcessor, ExtractionResult
from .extractors import TextExtractor, TableExtractor, MetadataExtractor
from ...core.logger import get_logger


class NI43101Processor(BasePDFProcessor):
    """Prozessor für NI 43-101 Technical Reports"""
    
    def __init__(self):
        logger = get_logger("ni43101_processor")
        super().__init__(logger)
        self.text_extractor = TextExtractor(logger)
        self.table_extractor = TableExtractor(logger)
        self.metadata_extractor = MetadataExtractor(logger)
    
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet NI 43-101 Report"""
        result = ExtractionResult("ni43-101")
        
        if not self.can_process(pdf_path):
            result.add_error("Kann PDF nicht verarbeiten")
            return result.to_dict()
        
        try:
            # Metadaten
            metadata = await self.metadata_extractor.extract_metadata(pdf_path)
            result.add_metadata("pdf_metadata", metadata)
            
            # Text extrahieren
            text = await self.text_extractor.extract_text(pdf_path)
            
            # Spezifische NI 43-101 Felder extrahieren
            result.add_data("qualified_persons", self._extract_qualified_persons(text))
            result.add_data("property_description", self._extract_property_description(text))
            result.add_data("mineral_resources", await self._extract_mineral_resources(pdf_path, text))
            result.add_data("recommendations", self._extract_recommendations(text))
            result.add_data("effective_date", self._extract_effective_date(text))
            
            # Tabellen extrahieren
            tables = await self.table_extractor.extract_tables(pdf_path)
            result.add_data("tables", self._process_ni43101_tables(tables))
            
            self.logger.info(f"NI 43-101 erfolgreich verarbeitet: {pdf_path.name}")
            
        except Exception as e:
            result.add_error(f"Verarbeitungsfehler: {str(e)}")
            self.logger.error(f"Fehler bei NI 43-101 Verarbeitung: {e}")
        
        return result.to_dict()
    
    def _extract_qualified_persons(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Qualified Persons"""
        qps = []
        
        # Muster für QP-Erkennung
        patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s*(?:P\.?(?:Eng|Geo)|M\.?Sc|Ph\.?D)',
            r'Qualified Person[s]?:?\s*([^,\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0]
                else:
                    name = match
                
                qps.append({
                    'name': name.strip(),
                    'designation': 'Qualified Person'
                })
        
        return qps
    
    def _extract_property_description(self, text: str) -> Dict[str, str]:
        """Extrahiert Property-Beschreibung"""
        description = {}
        
        # Suche nach Property-Sektion
        sections = self.text_extractor.extract_sections(text)
        
        for section_name, content in sections.items():
            if 'property' in section_name.lower() and 'description' in section_name.lower():
                # Extrahiere Details
                description['full_text'] = content[:1000]  # Erste 1000 Zeichen
                
                # Koordinaten
                coord_pattern = r'(\d+°\d+[\'"]?\s*[NS])\s*(?:and|,)\s*(\d+°\d+[\'"]?\s*[EW])'
                coord_match = re.search(coord_pattern, content)
                if coord_match:
                    description['coordinates'] = f"{coord_match.group(1)}, {coord_match.group(2)}"
                
                # Fläche
                area_pattern = r'(\d+(?:,\d+)?)\s*(?:hectares?|ha|km2|square kilometers?)'
                area_match = re.search(area_pattern, content, re.IGNORECASE)
                if area_match:
                    description['area'] = area_match.group(0)
                
                break
        
        return description
    
    async def _extract_mineral_resources(self, pdf_path: Path, text: str) -> Dict[str, Any]:
        """Extrahiert Mineral Resources"""
        resources = {
            'measured': {},
            'indicated': {},
            'inferred': {}
        }
        
        # Suche Resource-Tabellen
        tables = await self.table_extractor.extract_tables(pdf_path)
        
        for table in tables:
            table_data = table.get('data', [])
            if not table_data:
                continue
            
            # Prüfe ob Resource-Tabelle
            headers = list(table_data[0].keys()) if table_data else []
            if any('resource' in h.lower() for h in headers):
                # Verarbeite Resource-Daten
                for row in table_data:
                    category = None
                    for key, value in row.items():
                        if 'measured' in str(value).lower():
                            category = 'measured'
                        elif 'indicated' in str(value).lower():
                            category = 'indicated'
                        elif 'inferred' in str(value).lower():
                            category = 'inferred'
                        
                        # Extrahiere Tonnage und Grade
                        if category and any(term in key.lower() for term in ['tonnes', 'tons', 'mt']):
                            resources[category]['tonnage'] = value
                        elif category and any(term in key.lower() for term in ['grade', 'g/t', 'ppm', '%']):
                            resources[category]['grade'] = value
        
        return resources
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extrahiert Empfehlungen"""
        recommendations = []
        
        # Suche Recommendations-Sektion
        sections = self.text_extractor.extract_sections(text)
        
        for section_name, content in sections.items():
            if 'recommendation' in section_name.lower():
                # Extrahiere nummerierte Empfehlungen
                rec_pattern = r'(?:\d+\.?\s*)?([A-Z][^.!?]+[.!?])'
                matches = re.findall(rec_pattern, content)
                recommendations.extend(matches[:10])  # Max 10 Empfehlungen
                break
        
        return recommendations
    
    def _extract_effective_date(self, text: str) -> Optional[str]:
        """Extrahiert Effective Date"""
        # Verschiedene Datums-Formate
        patterns = [
            r'Effective Date:?\s*([A-Za-z]+\s+\d+,?\s+\d{4})',
            r'effective\s+(?:as\s+of\s+)?([A-Za-z]+\s+\d+,?\s+\d{4})',
            r'Report Date:?\s*([A-Za-z]+\s+\d+,?\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _process_ni43101_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verarbeitet NI 43-101 spezifische Tabellen"""
        processed = []
        
        for table in tables:
            # Kategorisiere Tabelle
            table_type = self._categorize_table(table)
            if table_type:
                table['table_type'] = table_type
                processed.append(table)
        
        return processed
    
    def _categorize_table(self, table: Dict[str, Any]) -> Optional[str]:
        """Kategorisiert Tabelle nach Inhalt"""
        data = table.get('data', [])
        if not data:
            return None
        
        # Prüfe erste Zeile (Headers)
        first_row = data[0] if data else {}
        headers_text = ' '.join(str(v).lower() for v in first_row.values())
        
        # Kategorisierung
        if any(term in headers_text for term in ['resource', 'tonnes', 'grade']):
            return 'mineral_resources'
        elif any(term in headers_text for term in ['drill', 'hole', 'from', 'to']):
            return 'drill_results'
        elif any(term in headers_text for term in ['sample', 'assay', 'au', 'ag']):
            return 'assay_results'
        elif any(term in headers_text for term in ['cost', 'capex', 'opex', '$']):
            return 'economics'
        
        return 'other'


class EnvironmentalReportProcessor(BasePDFProcessor):
    """Prozessor für Environmental Reports"""
    
    def __init__(self):
        logger = get_logger("environmental_processor")
        super().__init__(logger)
        self.text_extractor = TextExtractor(logger)
        self.table_extractor = TableExtractor(logger)
    
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet Environmental Report"""
        result = ExtractionResult("environmental")
        
        if not self.can_process(pdf_path):
            result.add_error("Kann PDF nicht verarbeiten")
            return result.to_dict()
        
        try:
            # Text extrahieren
            text = await self.text_extractor.extract_text(pdf_path)
            
            # Environmental-spezifische Extraktion
            result.add_data("environmental_impacts", self._extract_impacts(text))
            result.add_data("mitigation_measures", self._extract_mitigation(text))
            result.add_data("monitoring_plan", self._extract_monitoring(text))
            result.add_data("compliance_status", self._extract_compliance(text))
            
            # Tabellen
            tables = await self.table_extractor.extract_tables(pdf_path)
            result.add_data("environmental_data", self._process_environmental_tables(tables))
            
        except Exception as e:
            result.add_error(f"Verarbeitungsfehler: {str(e)}")
            self.logger.error(f"Fehler bei Environmental Report: {e}")
        
        return result.to_dict()
    
    def _extract_impacts(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Environmental Impacts"""
        impacts = []
        
        # Impact-Kategorien
        categories = ['air', 'water', 'soil', 'noise', 'biodiversity', 'social']
        
        for category in categories:
            pattern = rf'{category}\s+(?:quality\s+)?impact[s]?:?\s*([^.]+\.)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                impacts.append({
                    'category': category,
                    'description': match.strip()
                })
        
        return impacts
    
    def _extract_mitigation(self, text: str) -> List[str]:
        """Extrahiert Mitigation Measures"""
        measures = []
        
        # Suche Mitigation-Sektion
        sections = self.text_extractor.extract_sections(text)
        
        for section_name, content in sections.items():
            if 'mitigation' in section_name.lower():
                # Extrahiere Maßnahmen
                measure_pattern = r'[•\-\*]\s*([^•\-\*\n]+)'
                matches = re.findall(measure_pattern, content)
                measures.extend(matches[:20])  # Max 20 Maßnahmen
                break
        
        return measures
    
    def _extract_monitoring(self, text: str) -> Dict[str, Any]:
        """Extrahiert Monitoring Plan"""
        monitoring = {
            'parameters': [],
            'frequency': [],
            'locations': []
        }
        
        # Parameter
        param_pattern = r'monitor(?:ing)?\s+(?:of\s+)?([a-zA-Z\s]+)(?:\s+levels?)?'
        params = re.findall(param_pattern, text, re.IGNORECASE)
        monitoring['parameters'] = list(set(p.strip() for p in params))[:10]
        
        # Frequenz
        freq_pattern = r'(daily|weekly|monthly|quarterly|annually|continuous)'
        freqs = re.findall(freq_pattern, text, re.IGNORECASE)
        monitoring['frequency'] = list(set(freqs))
        
        return monitoring
    
    def _extract_compliance(self, text: str) -> Dict[str, str]:
        """Extrahiert Compliance-Status"""
        compliance = {}
        
        # Compliance-Aussagen
        patterns = {
            'status': r'compliance\s+status:?\s*([^\n]+)',
            'regulations': r'(?:comply|compliance)\s+with\s+([^\n]+)',
            'permits': r'permit\s+(?:number|no\.?):?\s*([A-Z0-9\-]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                compliance[key] = match.group(1).strip()
        
        return compliance
    
    def _process_environmental_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verarbeitet Environmental-Tabellen"""
        processed = []
        
        for table in tables:
            data = table.get('data', [])
            if not data:
                continue
            
            # Kategorisiere nach Inhalt
            headers = list(data[0].keys()) if data else []
            
            if any('emission' in h.lower() for h in headers):
                table['table_type'] = 'emissions'
            elif any('water' in h.lower() for h in headers):
                table['table_type'] = 'water_quality'
            elif any('species' in h.lower() or 'biodiversity' in h.lower() for h in headers):
                table['table_type'] = 'biodiversity'
            else:
                table['table_type'] = 'other'
            
            processed.append(table)
        
        return processed


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


class TechnicalReportProcessor(BasePDFProcessor):
    """Prozessor für allgemeine Technical Reports"""
    
    def __init__(self):
        logger = get_logger("technical_processor")
        super().__init__(logger)
        self.text_extractor = TextExtractor(logger)
        self.table_extractor = TableExtractor(logger)
    
    async def process(self, pdf_path: Path) -> Dict[str, Any]:
        """Verarbeitet Technical Report"""
        result = ExtractionResult("technical")
        
        if not self.can_process(pdf_path):
            result.add_error("Kann PDF nicht verarbeiten")
            return result.to_dict()
        
        try:
            # Basis-Extraktion
            text = await self.text_extractor.extract_text(pdf_path)
            sections = self.text_extractor.extract_sections(text)
            tables = await self.table_extractor.extract_tables(pdf_path)
            
            # Strukturierte Daten
            result.add_data("sections", list(sections.keys()))
            result.add_data("technical_data", self._extract_technical_data(text))
            result.add_data("conclusions", self._extract_conclusions(sections))
            result.add_data("tables_summary", self._summarize_tables(tables))
            
        except Exception as e:
            result.add_error(f"Verarbeitungsfehler: {str(e)}")
            self.logger.error(f"Fehler bei Technical Report: {e}")
        
        return result.to_dict()
    
    def _extract_technical_data(self, text: str) -> Dict[str, List[str]]:
        """Extrahiert technische Daten"""
        tech_data = {
            'measurements': [],
            'specifications': [],
            'methods': []
        }
        
        # Messungen (Zahlen mit Einheiten)
        measure_pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+/?[a-zA-Z]*)'
        measures = re.findall(measure_pattern, text)
        tech_data['measurements'] = [f"{m[0]} {m[1]}" for m in measures[:20]]
        
        # Methoden
        method_pattern = r'(?:method|technique|process):\s*([^\n]+)'
        methods = re.findall(method_pattern, text, re.IGNORECASE)
        tech_data['methods'] = methods[:10]
        
        return tech_data
    
    def _extract_conclusions(self, sections: Dict[str, str]) -> List[str]:
        """Extrahiert Schlussfolgerungen"""
        conclusions = []
        
        for section_name, content in sections.items():
            if 'conclusion' in section_name.lower():
                # Erste Sätze als Zusammenfassung
                sentences = content.split('.')[:5]
                conclusions.extend(s.strip() for s in sentences if s.strip())
                break
        
        return conclusions
    
    def _summarize_tables(self, tables: List[Dict[str, Any]]) -> Dict[str, int]:
        """Zusammenfassung der Tabellen"""
        summary = {
            'total_tables': len(tables),
            'pages_with_tables': len(set(t['page'] for t in tables)),
            'average_accuracy': sum(t.get('accuracy', 0) for t in tables) / len(tables) if tables else 0
        }
        
        return summary