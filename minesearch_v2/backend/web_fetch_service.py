"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Web Fetch Service für aktives URL-Crawling
"""

import httpx
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class WebFetchService:
    """Service für das Abrufen und Analysieren von Webseiten"""
    
    def __init__(self):
        self.timeout = 30  # 30 Sekunden Timeout pro URL
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def fetch_and_analyze(self, url: str, mine_name: str, 
                               keywords: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        Ruft eine URL ab und analysiert den Inhalt
        
        Args:
            url: Die abzurufende URL
            mine_name: Name der Mine für kontextuelle Suche
            keywords: Spezifische Schlüsselwörter nach Kategorie
            
        Returns:
            Dict mit extrahierten Informationen
        """
        result = {
            'url': url,
            'success': False,
            'data': {},
            'error': None,
            'links': []
        }
        
        # Default Keywords wenn nicht angegeben
        if not keywords:
            keywords = {
                'restoration': [
                    'restoration cost', 'closure cost', 'reclamation', 
                    'asset retirement', 'environmental liability', 'ARO',
                    'restaurationskosten', 'sanierungskosten'
                ],
                'operator': [
                    'operator', 'operated by', 'owner', 'company',
                    'betreiber', 'eigentümer'
                ],
                'coordinates': [
                    'latitude', 'longitude', 'coordinates', 'location',
                    'koordinaten', 'lage'
                ],
                'commodities': [
                    'commodity', 'commodities', 'mineral', 'ore',
                    'gold', 'copper', 'silver', 'zinc', 'lead',
                    'rohstoff', 'mineral'
                ],
                'production': [
                    'production', 'output', 'tonnes', 'ounces',
                    'produktion', 'förderung'
                ],
                'status': [
                    'operating', 'closed', 'active', 'inactive',
                    'aktiv', 'geschlossen', 'betrieb'
                ]
            }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Entferne Script und Style Tags
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extrahiere Text
                text = soup.get_text()
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                text = ' '.join(lines)
                
                # Suche nach Mine-Namen
                mine_pattern = re.compile(re.escape(mine_name), re.IGNORECASE)
                mine_mentions = len(mine_pattern.findall(text))
                
                if mine_mentions == 0:
                    result['error'] = f"Mine '{mine_name}' nicht auf der Seite gefunden"
                    return result
                
                result['data']['mine_mentions'] = mine_mentions
                
                # Extrahiere relevante Informationen nach Kategorie
                for category, category_keywords in keywords.items():
                    found_data = self._extract_category_data(text, category_keywords, mine_name)
                    if found_data:
                        result['data'][category] = found_data
                
                # Suche nach PDF-Links
                pdf_links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.endswith('.pdf') or 'pdf' in href.lower():
                        link_text = link.get_text(strip=True)
                        # Prüfe ob relevant für die Mine
                        if mine_name.lower() in href.lower() or mine_name.lower() in link_text.lower():
                            pdf_links.append({
                                'url': href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/'),
                                'text': link_text
                            })
                
                result['links'] = pdf_links[:5]  # Max 5 PDFs
                result['success'] = bool(result['data'])
                
                logger.info(f"[WEB FETCH] {url}: {len(result['data'])} Kategorien gefunden")
                
        except httpx.TimeoutException:
            result['error'] = f"Timeout nach {self.timeout} Sekunden"
            logger.warning(f"[WEB FETCH] Timeout für {url}")
        except httpx.HTTPStatusError as e:
            result['error'] = f"HTTP {e.response.status_code}"
            logger.warning(f"[WEB FETCH] HTTP-Fehler {e.response.status_code} für {url}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[WEB FETCH] Fehler für {url}: {str(e)}")
        
        return result
    
    def _extract_category_data(self, text: str, keywords: List[str], mine_name: str) -> Optional[Dict[str, Any]]:
        """Extrahiert Daten für eine spezifische Kategorie"""
        results = []
        
        # Suche nach jedem Keyword
        for keyword in keywords:
            pattern = re.compile(
                rf'({re.escape(keyword)}[^.]*?[\d,]+[^.]*?\.)',
                re.IGNORECASE | re.DOTALL
            )
            matches = pattern.findall(text)
            
            for match in matches[:3]:  # Max 3 Treffer pro Keyword
                # Prüfe ob Mine erwähnt wird im Kontext
                if mine_name.lower() in match.lower():
                    results.append({
                        'keyword': keyword,
                        'context': match.strip()
                    })
        
        return results if results else None

# Singleton-Instanz
web_fetch_service = WebFetchService()