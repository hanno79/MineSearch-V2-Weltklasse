"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Datenextraktion für BrightData Agent
"""

import re
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from ..base_agent import SearchResult, MineQuery
from ..extraction_patterns import ExtractorBase


class MiningDataExtractor:
    """Extrahiert Mining-spezifische Daten aus HTML und strukturierten Formaten"""
    
    def __init__(self, agent_name: str, logger):
        self.agent_name = agent_name
        self.logger = logger
        self.base_extractor = ExtractorBase()
        
    def extract_mining_data(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert Mining-Daten aus HTML mit kontextbasierter Extraktion"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Entferne Scripts und Styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Nutze kontextbasierte Extraktion für alle erforderlichen Felder
            for field in query.required_fields:
                extracted_values = self.base_extractor._extract_with_context(text, field)
                
                for value, confidence in extracted_values[:3]:  # Top 3 Ergebnisse
                    if confidence >= 0.4:  # Mindest-Konfidenz
                        result = SearchResult(
                            mine_name=query.mine_name,
                            field_name=field,
                            value=value,
                            source=f"BrightData: {urlparse(url).netloc}",
                            source_url=url,
                            source_date=self.base_extractor._extract_year_from_text(text),
                            confidence_score=confidence,
                            agent_name=self.agent_name,
                            timestamp=datetime.now(),
                            metadata={
                                "extraction_method": "contextual",
                                "page_title": soup.title.string if soup.title else None
                            }
                        )
                        results.append(result)
                        self.logger.info(f"Gefunden: {field} = {value} (Konfidenz: {confidence:.2f})")
            
            # Strukturierte Daten-Extraktion
            # Suche nach JSON-LD
            json_lds = soup.find_all('script', type='application/ld+json')
            for json_ld in json_lds:
                try:
                    data = json.loads(json_ld.string)
                    structured_results = self.extract_from_json_ld(data, url, query)
                    results.extend(structured_results)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"HTML Extraction Fehler: {e}")
        
        return results
    
    def extract_government_data(self, html: str, url: str, query: MineQuery) -> List[SearchResult]:
        """Spezielle Extraktion für Regierungsseiten"""
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Suche nach Government-spezifischen Strukturen
            # Oft in Tabellen oder Definition Lists
            
            # Tabellen mit Mining-Daten
            tables = soup.find_all('table')
            for table in tables:
                # Prüfe ob relevante Tabelle
                table_text = table.get_text().lower()
                if query.mine_name.lower() in table_text:
                    # Extrahiere Tabellenzeilen
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label = cells[0].get_text().strip().lower()
                            value = cells[1].get_text().strip()
                            
                            # Mapping zu unseren Feldern
                            field_mapping = {
                                'operator': 'betreiber',
                                'exploitant': 'betreiber',
                                'titulaire': 'betreiber',
                                'coordinates': 'koordinaten',
                                'coordonnées': 'koordinaten',
                                'status': 'aktivitaetsstatus',
                                'statut': 'aktivitaetsstatus',
                                'commodity': 'rohstofftyp',
                                'substance': 'rohstofftyp',
                                'area': 'flaeche',
                                'superficie': 'flaeche'
                            }
                            
                            for key, field_name in field_mapping.items():
                                if key in label:
                                    result = SearchResult(
                                        mine_name=query.mine_name,
                                        field_name=field_name,
                                        value=value,
                                        source=f"Gov Data: {url.split('/')[2]}",
                                        source_url=url,
                                        source_date=datetime.now().year,
                                        confidence_score=0.9,
                                        agent_name=self.agent_name,
                                        timestamp=datetime.now(),
                                        metadata={}
                                    )
                                    results.append(result)
                                    break
                                    
        except Exception as e:
            self.logger.error(f"Government Data Extraction Fehler: {e}")
        
        return results
    
    def extract_from_json_ld(self, data: Dict[str, Any], url: str, query: MineQuery) -> List[SearchResult]:
        """Extrahiert aus JSON-LD strukturierten Daten"""
        results = []
        
        try:
            # Rekursive Suche nach relevanten Daten
            def extract_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['operator', 'owner'] and isinstance(value, (str, dict)):
                            org_name = value if isinstance(value, str) else value.get('name', '')
                            if org_name:
                                results.append(SearchResult(
                                    mine_name=query.mine_name,
                                    field_name='betreiber',
                                    value=org_name,
                                    source=f"Bright Data JSON-LD: {url.split('/')[2]}",
                                    source_url=url,
                                    source_date=datetime.now().year,
                                    confidence_score=0.9,
                                    agent_name=self.agent_name,
                                    timestamp=datetime.now(),
                                    metadata={}
                                ))
                        elif key == 'geo' and isinstance(value, dict):
                            lat = value.get('latitude')
                            lon = value.get('longitude')
                            if lat and lon:
                                results.append(SearchResult(
                                    mine_name=query.mine_name,
                                    field_name='koordinaten',
                                    value=f"{lat}, {lon}",
                                    source=f"Bright Data JSON-LD: {url.split('/')[2]}",
                                    source_url=url,
                                    source_date=datetime.now().year,
                                    confidence_score=0.9,
                                    agent_name=self.agent_name,
                                    timestamp=datetime.now(),
                                    metadata={}
                                ))
                        elif isinstance(value, (dict, list)):
                            extract_recursive(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for item in obj:
                        extract_recursive(item, path)
            
            extract_recursive(data)
            
        except Exception as e:
            self.logger.error(f"JSON-LD Extraction Fehler: {e}")
        
        return results
    
    def parse_dataset_record(self, record: Dict[str, Any], dataset_type: str, query: MineQuery) -> List[SearchResult]:
        """Parst Dataset-Record zu SearchResults"""
        results = []
        
        # Dataset-spezifisches Mapping
        if dataset_type == 'canadian_business_registry':
            if 'company_name' in record and query.mine_name.lower() in record['company_name'].lower():
                if 'legal_name' in record:
                    results.append(SearchResult(
                        mine_name=query.mine_name,
                        field_name='betreiber',
                        value=record['legal_name'],
                        source="Bright Data Business Registry",
                        source_url="",
                        source_date=datetime.now().year,
                        confidence_score=0.9,
                        agent_name=self.agent_name,
                        timestamp=datetime.now(),
                        metadata={}
                    ))
                    
        elif dataset_type == 'environmental_permits':
            if 'permit_holder' in record:
                results.append(SearchResult(
                    mine_name=query.mine_name,
                    field_name='betreiber',
                    value=record['permit_holder'],
                    source="Bright Data Environmental Permits",
                    source_url="",
                    source_date=record.get('issue_date', datetime.now()).year,
                    confidence_score=0.9,
                    agent_name=self.agent_name,
                    timestamp=datetime.now(),
                    metadata={}
                ))
            
            if 'financial_assurance' in record:
                results.append(SearchResult(
                    mine_name=query.mine_name,
                    field_name='sanierungskosten',
                    value=f"{record['financial_assurance']:,} CAD",
                    source="Bright Data Environmental Permits",
                    source_url="",
                    source_date=record.get('issue_date', datetime.now()).year,
                    confidence_score=0.9,
                    agent_name=self.agent_name,
                    timestamp=datetime.now(),
                    metadata={}
                ))
        
        return results
    
    def clean_value(self, value: str, field_name: str) -> str:
        """Bereinigt extrahierte Werte"""
        # Entferne übermäßige Whitespaces
        value = re.sub(r'\s+', ' ', value).strip()
        
        if field_name == 'sanierungskosten':
            # Normalisiere Währungsbeträge
            value = value.replace(' ', '')
            if 'million' in value.lower() or 'M' in value:
                try:
                    num_match = re.search(r'([\d,\.]+)', value)
                    if num_match:
                        num = float(num_match.group(1).replace(',', ''))
                        value = f"{int(num * 1000000):,} CAD"
                except:
                    pass
        
        elif field_name == 'koordinaten':
            # Normalisiere Koordinaten
            if 'UTM' in value:
                # Konvertiere UTM zu Lat/Lon wenn möglich
                # (Implementierung würde UTM-Konvertierung benötigen)
                pass
            else:
                # Entferne Grad-Zeichen
                value = value.replace('°', '').replace("'", '').replace('"', '')
        
        return value
    
    def is_mining_relevant(self, url: str, title: str) -> bool:
        """Prüft ob URL/Title mining-relevant ist"""
        # Positive Indikatoren
        positive_keywords = [
            'mining', 'mine', 'mineral', 'resources', 'extraction',
            'operator', 'environmental', 'restoration', 'production',
            'mern', 'nrcan', 'gov', 'sedar'
        ]
        
        # Negative Indikatoren
        negative_keywords = [
            'jobs', 'careers', 'recruitment', 'stock', 'trading',
            'wikipedia', 'facebook', 'twitter', 'youtube'
        ]
        
        combined = (url + ' ' + title).lower()
        
        # Prüfe negative Keywords
        if any(neg in combined for neg in negative_keywords):
            return False
        
        # Prüfe positive Keywords
        return any(pos in combined for pos in positive_keywords)