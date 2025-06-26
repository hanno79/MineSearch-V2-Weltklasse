"""
Author: rahn
Datum: 24.06.2025
Version: 1.0
Beschreibung: Fallback-Scraper ohne Playwright für einfache Seiten
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import asyncio
from urllib.parse import urljoin, urlparse

from src.core.logger import get_logger
from ..base_agent import SearchResult


class FallbackScraper:
    """Fallback-Scraper für wenn Playwright nicht verfügbar ist"""
    
    def __init__(self, logger=None):
        self.logger = logger or get_logger("fallback_scraper")
        self.session = None
        
    async def __aenter__(self):
        """Async Context Manager Entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'MiningResearchBot/1.0 (Fallback Mode)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async Context Manager Exit"""
        if self.session:
            await self.session.close()
    
    async def scrape(self, url: str, mine_name: str) -> List[Dict[str, Any]]:
        """Scrapt eine URL ohne JavaScript-Rendering"""
        results = []
        
        try:
            self.logger.info(f"Fallback-Scraping: {url}")
            
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    self.logger.warning(f"HTTP {response.status} für {url}")
                    return results
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Entferne Script und Style Tags
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Suche nach Mine-Namen im Text
                text_content = soup.get_text()
                if mine_name.lower() in text_content.lower():
                    # Extrahiere relevante Daten
                    data = self._extract_data(soup, mine_name, url)
                    if data:
                        results.extend(data)
                
                # Suche auch in Tabellen
                tables = soup.find_all('table')
                for table in tables:
                    table_data = self._extract_table_data(table, mine_name)
                    if table_data:
                        for row in table_data:
                            row['source_url'] = url
                        results.extend(table_data)
                
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout beim Scrapen von {url}")
        except Exception as e:
            self.logger.error(f"Fehler beim Fallback-Scraping von {url}: {e}")
        
        return results
    
    def _extract_data(self, soup: BeautifulSoup, mine_name: str, url: str) -> List[Dict[str, Any]]:
        """Extrahiert Daten aus der Seite"""
        results = []
        
        # Suche nach strukturierten Daten
        # 1. Definition Lists (dl, dt, dd)
        for dl in soup.find_all('dl'):
            data = {}
            current_key = None
            
            for child in dl.children:
                if child.name == 'dt':
                    current_key = child.get_text(strip=True)
                elif child.name == 'dd' and current_key:
                    data[current_key] = child.get_text(strip=True)
            
            if data and mine_name.lower() in str(data).lower():
                results.append({
                    'type': 'definition_list',
                    'data': data,
                    'source_url': url
                })
        
        # 2. Listen mit Mine-Informationen
        for ul in soup.find_all(['ul', 'ol']):
            items = []
            for li in ul.find_all('li'):
                text = li.get_text(strip=True)
                if mine_name.lower() in text.lower():
                    items.append(text)
            
            if items:
                results.append({
                    'type': 'list',
                    'items': items,
                    'source_url': url
                })
        
        # 3. Paragraphen mit Mine-Erwähnungen
        relevant_paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if mine_name.lower() in text.lower() and len(text) > 50:
                relevant_paragraphs.append(text)
        
        if relevant_paragraphs:
            results.append({
                'type': 'paragraphs',
                'content': relevant_paragraphs[:5],  # Max 5 Paragraphen
                'source_url': url
            })
        
        return results
    
    def _extract_table_data(self, table, mine_name: str) -> List[Dict[str, Any]]:
        """Extrahiert Daten aus Tabellen"""
        results = []
        
        # Hole Header
        headers = []
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
        
        # Durchsuche Zeilen
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
            
            if mine_name.lower() in row_text.lower():
                row_data = {}
                for i, cell in enumerate(cells):
                    key = headers[i] if i < len(headers) else f'column_{i}'
                    row_data[key] = cell.get_text(strip=True)
                
                if row_data:
                    results.append({
                        'type': 'table_row',
                        'data': row_data
                    })
        
        return results
    
    async def search_with_fallback(self, urls: List[str], mine_name: str) -> List[SearchResult]:
        """Führt Fallback-Suche für mehrere URLs durch"""
        all_results = []
        
        # Begrenze auf max 5 URLs
        for url in urls[:5]:
            try:
                data = await self.scrape(url, mine_name)
                
                # Konvertiere zu SearchResult
                for item in data:
                    result = SearchResult(
                        title=f"Fallback: {mine_name} Information",
                        url=item.get('source_url', url),
                        snippet=self._create_snippet(item),
                        source="fallback_scraper",
                        relevance_score=0.5,  # Niedrigerer Score für Fallback
                        metadata={
                            'extraction_type': item.get('type', 'unknown'),
                            'fallback_mode': True,
                            'data': item.get('data', item)
                        }
                    )
                    all_results.append(result)
                    
            except Exception as e:
                self.logger.error(f"Fehler bei Fallback-URL {url}: {e}")
        
        return all_results
    
    def _create_snippet(self, data: Dict[str, Any]) -> str:
        """Erstellt Snippet aus extrahierten Daten"""
        data_type = data.get('type', 'unknown')
        
        if data_type == 'table_row':
            row_data = data.get('data', {})
            parts = [f"{k}: {v}" for k, v in row_data.items() if v]
            return " | ".join(parts[:3])  # Erste 3 Felder
            
        elif data_type == 'paragraphs':
            content = data.get('content', [])
            return content[0][:200] + "..." if content else ""
            
        elif data_type == 'list':
            items = data.get('items', [])
            return " • ".join(items[:2]) if items else ""
            
        elif data_type == 'definition_list':
            dl_data = data.get('data', {})
            parts = [f"{k}: {v}" for k, v in list(dl_data.items())[:2]]
            return " | ".join(parts)
            
        return "Daten gefunden (siehe Details)"