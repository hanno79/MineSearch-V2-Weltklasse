"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Bright Data Parsing und Datenextraktion
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
from src.agents.base_agent import MineQuery


class BrightDataParser:
    """Parser für Bright Data Scraping-Ergebnisse"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
        # Mining-spezifische Patterns
        self.mining_patterns = {
            'coordinates': r'(?:latitude|lat)[:\s]+([+-]?\d+\.?\d*)[,\s]+(?:longitude|long?)[:\s]+([+-]?\d+\.?\d*)',
            'depth': r'(\d+(?:,\d+)?)\s*(?:meters?|m|feet|ft)\s+(?:deep|depth)',
            'production': r'(\d+(?:,\d+)?)\s*(?:tons?|tonnes?|ounces?|oz|kg)\s*(?:per|/)\s*(?:year|month|day)',
            'established': r'(?:established|founded|opened|started)\s*(?:in)?\s*(\d{4})',
            'employees': r'(\d+(?:,\d+)?)\s*(?:employees?|workers?|staff)',
            'reserves': r'(?:reserves?|resources?)\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(?:million|billion)?\s*(?:tons?|tonnes?|ounces?)',
        }
        
        # Relevante HTML-Selektoren
        self.selectors = {
            'title': ['h1', 'h2', '.title', '#title', '[class*="title"]'],
            'content': ['article', 'main', '.content', '#content', '[class*="content"]'],
            'metadata': ['meta[property]', 'meta[name]', '[itemprop]'],
            'tables': ['table', '.data-table', '[class*="table"]'],
            'lists': ['ul', 'ol', 'dl', '.list', '[class*="list"]']
        }
    
    def extract_mining_data(self, 
                           html_content: str, 
                           url: str,
                           query: MineQuery) -> List[Dict[str, Any]]:
        """Extrahiert Mining-spezifische Daten aus HTML"""
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Basis-Informationen extrahieren
            base_data = self._extract_base_info(soup, url)
            
            # Mining-spezifische Daten suchen
            mining_data = self._extract_mining_specific(soup, query)
            
            # Strukturierte Daten extrahieren
            structured_data = self._extract_structured_data(soup)
            
            # Kombiniere alle Daten
            if base_data or mining_data or structured_data:
                result = {
                    **base_data,
                    'mining_data': mining_data,
                    'structured_data': structured_data,
                    'source_type': 'web',
                    'extracted_at': datetime.now().isoformat()
                }
                
                # Berechne Konfidenz basierend auf gefundenen Daten
                result['confidence'] = self._calculate_confidence(result, query)
                
                results.append(result)
            
            # Zusätzliche Ergebnisse aus Tabellen/Listen
            additional = self._extract_additional_results(soup, query, url)
            results.extend(additional)
            
        except Exception as e:
            self.logger.error(f"Parsing-Fehler: {e}")
        
        return results
    
    def parse_specialized_data(self, 
                              data: Dict[str, Any],
                              collector_type: str,
                              query: MineQuery) -> List[Dict[str, Any]]:
        """Parst spezialisierte Collector-Daten"""
        results = []
        
        try:
            if collector_type == 'business_data':
                results = self._parse_business_data(data, query)
            elif collector_type == 'news':
                results = self._parse_news_data(data, query)
            elif collector_type == 'social_media':
                results = self._parse_social_data(data, query)
            else:
                # Generisches Parsing
                results = self._parse_generic_data(data, query)
                
        except Exception as e:
            self.logger.error(f"Specialized parsing error: {e}")
        
        return results
    
    def _extract_base_info(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extrahiert Basis-Informationen"""
        info = {
            'url': url,
            'title': '',
            'snippet': '',
            'metadata': {}
        }
        
        # Titel extrahieren
        for selector in self.selectors['title']:
            title_elem = soup.select_one(selector)
            if title_elem:
                info['title'] = title_elem.get_text(strip=True)
                break
        
        # Fallback auf <title> Tag
        if not info['title']:
            title_tag = soup.find('title')
            if title_tag:
                info['title'] = title_tag.get_text(strip=True)
        
        # Meta-Description als Snippet
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            info['snippet'] = meta_desc.get('content', '')
        
        # Weitere Metadaten
        for meta in soup.find_all('meta', attrs={'property': True}):
            prop = meta.get('property', '')
            content = meta.get('content', '')
            if prop and content:
                info['metadata'][prop] = content
        
        return info
    
    def _extract_mining_specific(self, soup: BeautifulSoup, query: MineQuery) -> Dict[str, Any]:
        """Extrahiert Mining-spezifische Informationen"""
        mining_info = {}
        text_content = soup.get_text()
        
        # Suche nach Mining-Patterns
        for pattern_name, pattern in self.mining_patterns.items():
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                if pattern_name == 'coordinates' and len(matches[0]) == 2:
                    mining_info[pattern_name] = {
                        'latitude': float(matches[0][0]),
                        'longitude': float(matches[0][1])
                    }
                else:
                    # Erste Übereinstimmung verwenden
                    mining_info[pattern_name] = matches[0]
        
        # Suche nach Mineralien/Rohstoffen
        if query.mining_type:
            mineral_mentions = len(re.findall(
                rf'\b{query.mining_type}\b', 
                text_content, 
                re.IGNORECASE
            ))
            if mineral_mentions > 0:
                mining_info['mineral_mentions'] = mineral_mentions
        
        # Suche nach Firmennamen
        company_patterns = [
            r'(?:owned|operated|managed)\s+by\s+([A-Z][A-Za-z\s&]+(?:Corp|Inc|Ltd|Limited|Company|Co\.))',
            r'([A-Z][A-Za-z\s&]+(?:Mining|Metals|Resources|Minerals)(?:\s+(?:Corp|Inc|Ltd|Limited|Company|Co\.)?)?)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                mining_info['companies'] = list(set(matches))[:3]
                break
        
        return mining_info
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrahiert strukturierte Daten (JSON-LD, Microdata)"""
        structured = {}
        
        # JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        if json_ld_scripts:
            structured['json_ld'] = []
            for script in json_ld_scripts[:2]:  # Nur erste 2
                try:
                    import json
                    data = json.loads(script.string)
                    structured['json_ld'].append(data)
                except:
                    pass
        
        # Microdata
        microdata_items = soup.find_all(attrs={'itemscope': True})
        if microdata_items:
            structured['microdata'] = len(microdata_items)
        
        return structured
    
    def _extract_additional_results(self, 
                                   soup: BeautifulSoup,
                                   query: MineQuery,
                                   base_url: str) -> List[Dict[str, Any]]:
        """Extrahiert zusätzliche Ergebnisse aus Tabellen und Listen"""
        results = []
        
        # Tabellen mit Mining-Daten
        for table in soup.find_all('table')[:3]:  # Maximal 3 Tabellen
            rows = table.find_all('tr')
            if len(rows) > 1:  # Header + Daten
                headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                
                # Prüfe ob relevante Headers
                relevant_headers = ['mine', 'location', 'production', 'mineral', 'company']
                if any(h.lower() in ' '.join(headers).lower() for h in relevant_headers):
                    for row in rows[1:5]:  # Maximal 4 Datenzeilen
                        cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                        if cells:
                            table_data = dict(zip(headers, cells))
                            
                            # Erstelle Ergebnis aus Tabellendaten
                            title = table_data.get(headers[0], 'Mining Data')
                            snippet = ' | '.join([f"{k}: {v}" for k, v in table_data.items()][:3])
                            
                            results.append({
                                'title': title,
                                'url': base_url + '#table',
                                'snippet': snippet,
                                'metadata': {
                                    'table_data': table_data,
                                    'source_type': 'table'
                                },
                                'confidence': 0.6
                            })
        
        return results
    
    def _calculate_confidence(self, data: Dict[str, Any], query: MineQuery) -> float:
        """Berechnet Konfidenz-Score basierend auf gefundenen Daten"""
        score = 0.5  # Basis-Score
        
        # Title-Match
        if query.mine_name.lower() in data.get('title', '').lower():
            score += 0.2
        
        # Mining-spezifische Daten gefunden
        mining_data = data.get('mining_data', {})
        if mining_data:
            score += min(0.3, len(mining_data) * 0.05)
        
        # Strukturierte Daten vorhanden
        if data.get('structured_data'):
            score += 0.1
        
        # Mineral-Typ erwähnt
        if 'mineral_mentions' in mining_data:
            score += min(0.1, mining_data['mineral_mentions'] * 0.02)
        
        return min(1.0, score)
    
    def _parse_business_data(self, data: Dict[str, Any], query: MineQuery) -> List[Dict[str, Any]]:
        """Parst Business/Company Daten"""
        results = []
        
        companies = data.get('companies', [])
        for company in companies[:5]:
            if query.mine_name.lower() in company.get('name', '').lower():
                results.append({
                    'title': company.get('name', 'Unknown Company'),
                    'url': company.get('website', ''),
                    'snippet': company.get('description', ''),
                    'metadata': {
                        'industry': company.get('industry'),
                        'employees': company.get('employee_count'),
                        'founded': company.get('founded_year'),
                        'headquarters': company.get('headquarters')
                    }
                })
        
        return results
    
    def _parse_news_data(self, data: Dict[str, Any], query: MineQuery) -> List[Dict[str, Any]]:
        """Parst News-Daten"""
        results = []
        
        articles = data.get('articles', [])
        for article in articles[:10]:
            # Relevanz prüfen
            title = article.get('title', '')
            content = article.get('content', '')
            
            if query.mine_name.lower() in (title + content).lower():
                results.append({
                    'title': title,
                    'url': article.get('url', ''),
                    'snippet': article.get('summary', content[:200]),
                    'metadata': {
                        'published_date': article.get('published_date'),
                        'author': article.get('author'),
                        'source': article.get('source')
                    }
                })
        
        return results
    
    def _parse_social_data(self, data: Dict[str, Any], query: MineQuery) -> List[Dict[str, Any]]:
        """Parst Social Media Daten"""
        results = []
        
        posts = data.get('posts', [])
        for post in posts[:5]:
            if query.mine_name.lower() in post.get('text', '').lower():
                results.append({
                    'title': f"{post.get('platform', 'Social')} Post",
                    'url': post.get('url', ''),
                    'snippet': post.get('text', '')[:200],
                    'metadata': {
                        'platform': post.get('platform'),
                        'author': post.get('author'),
                        'engagement': post.get('engagement_metrics', {})
                    }
                })
        
        return results
    
    def _parse_generic_data(self, data: Dict[str, Any], query: MineQuery) -> List[Dict[str, Any]]:
        """Generisches Parsing für unbekannte Datentypen"""
        results = []
        
        # Versuche Standard-Felder zu finden
        if isinstance(data, dict):
            if 'results' in data:
                for item in data['results'][:10]:
                    if isinstance(item, dict):
                        results.append({
                            'title': item.get('title', item.get('name', 'Unknown')),
                            'url': item.get('url', item.get('link', '')),
                            'snippet': item.get('description', item.get('snippet', '')),
                            'metadata': {k: v for k, v in item.items() 
                                       if k not in ['title', 'url', 'description', 'snippet']}
                        })
        
        return results