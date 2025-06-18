"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Multi-Layer Web Crawler für tiefes Eintauchen in Mining-Websites
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import asyncio
import re
from bs4 import BeautifulSoup

@dataclass
class CrawlResult:
    """Ergebnis eines Crawl-Vorgangs"""
    url: str
    depth: int
    content_type: str
    relevant_content: Dict[str, List[str]]
    linked_pages: List[str]
    documents_found: List[Dict[str, str]]  # PDFs, Excel, etc.
    data_tables: List[Dict[str, any]]
    relevance_score: float

class DeepWebCrawler:
    """Crawlt Websites in mehreren Ebenen für Mining-Informationen"""
    
    def __init__(self, scraper_agents=None):
        self.visited_urls = set()
        self.queued_urls = set()
        self.results = []
        self.mining_keywords = self._initialize_mining_keywords()
        self.scraper_agents = scraper_agents or {}  # Dictionary von Scraper-Agenten
        self.active_scraper = None
        
    def _initialize_mining_keywords(self) -> Dict[str, List[str]]:
        """Initialisiert Mining-relevante Keywords in verschiedenen Sprachen"""
        return {
            "operations": [
                "mine", "mining", "extraction", "exploitation",
                "mina", "minería", "extracción",
                "mine", "exploitation minière",
                "bergwerk", "bergbau", "abbau",
                "шахта", "добыча", "рудник"
            ],
            "documents": [
                "permit", "license", "concession", "report", "assessment",
                "permiso", "licencia", "concesión", "informe",
                "permis", "licence", "rapport", "évaluation",
                "genehmigung", "lizenz", "bericht"
            ],
            "data": [
                "production", "reserves", "resources", "output", "capacity",
                "producción", "reservas", "recursos",
                "production", "réserves", "ressources",
                "produktion", "reserven", "ressourcen"
            ],
            "environmental": [
                "environmental", "impact", "restoration", "contamination",
                "ambiental", "impacto", "restauración", "contaminación",
                "environnemental", "impact", "restauration",
                "umwelt", "auswirkung", "sanierung"
            ],
            "financial": [
                "cost", "investment", "revenue", "expenditure", "budget",
                "costo", "inversión", "ingresos", "gastos",
                "coût", "investissement", "revenus",
                "kosten", "investition", "einnahmen"
            ]
        }
    
    def set_scraper_agents(self, agents: Dict[str, any]):
        """Setzt verfügbare Scraper-Agenten"""
        # ÄNDERUNG 17.06.2025: Methode zur Agent-Integration
        self.scraper_agents = {
            name: agent for name, agent in agents.items() 
            if name in ['scraper', 'brightdata', 'scrapingbee', 'apify', 'firecrawl']
        }
        
    async def deep_crawl(self, start_url: str, max_depth: int, 
                        mine_name: str, target_fields: List[str]) -> List[CrawlResult]:
        """
        Führt einen tiefen Crawl einer Website durch
        
        Args:
            start_url: Ausgangs-URL
            max_depth: Maximale Crawl-Tiefe
            mine_name: Name der Mine für Relevanz-Filterung
            target_fields: Gesuchte Datenfelder
        """
        self.mine_name = mine_name.lower()
        self.target_fields = target_fields
        
        # Starte mit der Haupt-URL
        await self._crawl_page(start_url, 0, max_depth)
        
        # Crawle Warteschlange ab
        while self.queued_urls and len(self.visited_urls) < 1000:  # Limit
            batch = list(self.queued_urls)[:10]  # 10 parallel
            self.queued_urls -= set(batch)
            
            tasks = []
            for url in batch:
                if url not in self.visited_urls:
                    # Bestimme Tiefe basierend auf URL-Struktur
                    depth = self._calculate_url_depth(start_url, url)
                    if depth <= max_depth:
                        tasks.append(self._crawl_page(url, depth, max_depth))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        return self.results
    
    async def _crawl_page(self, url: str, depth: int, max_depth: int) -> Optional[CrawlResult]:
        """Crawlt eine einzelne Seite"""
        if url in self.visited_urls or depth > max_depth:
            return None
            
        self.visited_urls.add(url)
        
        try:
            # Hier würde der tatsächliche HTTP-Request stattfinden
            # Placeholder für Demonstration
            content = await self._fetch_page(url)
            
            if not content:
                return None
            
            # Analysiere Inhalt
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extrahiere relevante Inhalte
            relevant_content = self._extract_relevant_content(soup, url)
            
            # Finde verlinkte Seiten
            linked_pages = self._find_relevant_links(soup, url)
            
            # Finde Dokumente (PDFs, Excel, etc.)
            documents = self._find_documents(soup, url)
            
            # Extrahiere Datentabellen
            tables = self._extract_data_tables(soup)
            
            # Berechne Relevanz
            relevance = self._calculate_page_relevance(relevant_content, url)
            
            result = CrawlResult(
                url=url,
                depth=depth,
                content_type=self._determine_content_type(soup, url),
                relevant_content=relevant_content,
                linked_pages=linked_pages,
                documents_found=documents,
                data_tables=tables,
                relevance_score=relevance
            )
            
            self.results.append(result)
            
            # Füge relevante Links zur Queue hinzu
            if depth < max_depth and relevance > 0.3:
                for link in linked_pages[:20]:  # Max 20 Links pro Seite
                    if link not in self.visited_urls:
                        self.queued_urls.add(link)
            
            return result
            
        except Exception as e:
            print(f"Fehler beim Crawlen von {url}: {e}")
            return None
    
    def _extract_relevant_content(self, soup: BeautifulSoup, url: str) -> Dict[str, List[str]]:
        """Extrahiert relevante Inhalte von einer Seite"""
        content = {field: [] for field in self.target_fields}
        
        # Textkörper analysieren
        text_elements = soup.find_all(['p', 'div', 'span', 'li', 'td', 'h1', 'h2', 'h3'])
        
        for element in text_elements:
            text = element.get_text(strip=True)
            if not text or len(text) < 20:
                continue
            
            # Prüfe ob Mine erwähnt wird
            if self.mine_name in text.lower():
                # Analysiere Text für verschiedene Felder
                extracted = self._analyze_text_for_fields(text)
                for field, values in extracted.items():
                    if field in content:
                        content[field].extend(values)
            
        # Suche auch ohne Minenname in spezifischen Bereichen
        self._extract_from_specific_sections(soup, content)
        
        return content
    
    def _analyze_text_for_fields(self, text: str) -> Dict[str, List[str]]:
        """Analysiert Text auf verschiedene Datenfelder"""
        extracted = {}
        
        # Koordinaten
        coord_patterns = [
            r'(\d{1,2}[°\s]\d{1,2}[′\'\s]\d{1,2}(?:\.\d+)?[″"]*\s*[NS])[,\s]+(\d{1,3}[°\s]\d{1,2}[′\'\s]\d{1,2}(?:\.\d+)?[″"]*\s*[EW])',
            r'latitude[:\s]*([-]?\d+\.?\d*)[,\s]+longitude[:\s]*([-]?\d+\.?\d*)',
            r'(\-?\d{1,2}\.\d{3,})[,\s]+(\-?\d{1,3}\.\d{3,})'
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if 'koordinaten' not in extracted:
                    extracted['koordinaten'] = []
                extracted['koordinaten'].extend([f"{m[0]}, {m[1]}" for m in matches])
        
        # Produktionsdaten
        prod_patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:tonnes?|tons?|ounces?|oz)\s*(?:per|/)\s*(?:year|annual)',
            r'annual\s+production[:\s]*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:tonnes?|tons?)',
            r'produces?\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:tonnes?|tons?)'
        ]
        
        for pattern in prod_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if 'produktionsdaten' not in extracted:
                    extracted['produktionsdaten'] = []
                extracted['produktionsdaten'].extend(matches)
        
        # Weitere Felder...
        # Implementierung für andere Felder würde hier folgen
        
        return extracted
    
    def _find_relevant_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Findet relevante Links auf einer Seite"""
        relevant_links = []
        
        # Keywords die auf relevante Seiten hinweisen
        relevant_keywords = [
            'mine', 'project', 'operation', 'production', 'report',
            'data', 'statistics', 'information', 'details', 'about',
            'environmental', 'permit', 'license', 'document',
            'mina', 'proyecto', 'operación', 'producción',
            'mine', 'projet', 'exploitation', 'production'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            
            # Mache URL absolut
            absolute_url = urljoin(base_url, href)
            
            # Prüfe ob Link relevant ist
            if any(keyword in link_text for keyword in relevant_keywords):
                relevant_links.append(absolute_url)
            elif any(keyword in href.lower() for keyword in relevant_keywords):
                relevant_links.append(absolute_url)
            elif self.mine_name in link_text or self.mine_name in href.lower():
                relevant_links.append(absolute_url)
        
        # Dedupliziere und filtere
        return list(set(link for link in relevant_links if self._is_valid_url(link)))
    
    def _find_documents(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Findet herunterladbare Dokumente"""
        documents = []
        doc_extensions = ['.pdf', '.xlsx', '.xls', '.doc', '.docx', '.csv', '.zip']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True)
            
            # Prüfe auf Dokumenten-Endungen
            if any(href.lower().endswith(ext) for ext in doc_extensions):
                absolute_url = urljoin(base_url, href)
                
                # Versuche Dokumenttyp zu bestimmen
                doc_type = self._determine_document_type(href, link_text)
                
                documents.append({
                    'url': absolute_url,
                    'title': link_text or 'Unnamed Document',
                    'type': doc_type,
                    'extension': href.split('.')[-1].lower()
                })
        
        return documents
    
    def _extract_data_tables(self, soup: BeautifulSoup) -> List[Dict[str, any]]:
        """Extrahiert Datentabellen von der Seite"""
        tables = []
        
        for table in soup.find_all('table'):
            # Versuche Tabellenkopf zu finden
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Prüfe ob Tabelle relevant ist
            if self._is_relevant_table(headers):
                rows = []
                for row in table.find_all('tr')[1:]:  # Skip header
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                
                if rows:
                    tables.append({
                        'headers': headers,
                        'rows': rows,
                        'relevance': self._calculate_table_relevance(headers, rows)
                    })
        
        return tables
    
    def _calculate_page_relevance(self, content: Dict[str, List[str]], url: str) -> float:
        """Berechnet Relevanz einer Seite"""
        score = 0.0
        
        # Basis-Score wenn Mine erwähnt wird
        page_text = str(content).lower()
        if self.mine_name in page_text:
            score += 0.3
        
        # Score für gefundene Daten
        for field, values in content.items():
            if values:
                score += 0.1 * min(len(values), 3)  # Max 0.3 pro Feld
        
        # URL-basierte Relevanz
        url_lower = url.lower()
        if self.mine_name.replace(' ', '-') in url_lower:
            score += 0.2
        
        # Keywords in URL
        url_keywords = ['project', 'mine', 'operation', 'data', 'information']
        for keyword in url_keywords:
            if keyword in url_lower:
                score += 0.05
        
        return min(score, 1.0)
    
    def _determine_content_type(self, soup: BeautifulSoup, url: str) -> str:
        """Bestimmt den Inhaltstyp einer Seite"""
        # Prüfe Meta-Tags
        content_type = soup.find('meta', attrs={'name': 'content-type'})
        if content_type:
            return content_type.get('content', 'unknown')
        
        # Prüfe Seitenstruktur
        if soup.find_all('article'):
            return 'article'
        elif len(soup.find_all('table')) > 2:
            return 'data_page'
        elif soup.find('form'):
            return 'form_page'
        else:
            return 'general'
    
    def _is_relevant_table(self, headers: List[str]) -> bool:
        """Prüft ob eine Tabelle relevant ist"""
        if not headers:
            return False
        
        relevant_terms = [
            'production', 'output', 'reserves', 'cost', 'employee',
            'year', 'mineral', 'grade', 'tonnage', 'revenue'
        ]
        
        headers_lower = ' '.join(headers).lower()
        return any(term in headers_lower for term in relevant_terms)
    
    def _calculate_table_relevance(self, headers: List[str], rows: List[List[str]]) -> float:
        """Berechnet Relevanz einer Tabelle"""
        if not headers or not rows:
            return 0.0
        
        score = 0.5  # Basis-Score für Tabellen
        
        # Prüfe auf numerische Daten
        numeric_cells = 0
        total_cells = 0
        
        for row in rows[:10]:  # Prüfe erste 10 Zeilen
            for cell in row:
                total_cells += 1
                if re.search(r'\d+', cell):
                    numeric_cells += 1
        
        if total_cells > 0:
            numeric_ratio = numeric_cells / total_cells
            score += numeric_ratio * 0.3
        
        # Prüfe auf Mining-Keywords
        table_text = ' '.join(headers + [cell for row in rows for cell in row]).lower()
        mining_terms = ['mine', 'production', 'tonnage', 'grade', 'reserve']
        
        for term in mining_terms:
            if term in table_text:
                score += 0.1
        
        return min(score, 1.0)
    
    def _is_valid_url(self, url: str) -> bool:
        """Prüft ob URL gültig ist"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _calculate_url_depth(self, start_url: str, current_url: str) -> int:
        """Berechnet die Tiefe einer URL relativ zur Start-URL"""
        start_parts = urlparse(start_url).path.strip('/').split('/')
        current_parts = urlparse(current_url).path.strip('/').split('/')
        
        # Wenn andere Domain, zähle als Tiefe 2
        if urlparse(start_url).netloc != urlparse(current_url).netloc:
            return 2
        
        return len(current_parts) - len(start_parts) + 1
    
    def _determine_document_type(self, url: str, link_text: str) -> str:
        """Bestimmt den Typ eines Dokuments"""
        url_lower = url.lower()
        text_lower = link_text.lower()
        
        if 'report' in url_lower or 'report' in text_lower:
            return 'report'
        elif 'permit' in url_lower or 'license' in url_lower:
            return 'permit'
        elif 'environmental' in url_lower or 'environmental' in text_lower:
            return 'environmental'
        elif 'financial' in url_lower or 'financial' in text_lower:
            return 'financial'
        elif 'technical' in url_lower or 'technical' in text_lower:
            return 'technical'
        else:
            return 'general'
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetcht eine Seite mit verfügbaren Scraper-Agenten"""
        # ÄNDERUNG 17.06.2025: Integration mit Scraper-Agenten
        
        if not self.scraper_agents:
            print(f"⚠️ Keine Scraper-Agenten verfügbar für {url}")
            return None
        
        # Wähle besten Scraper für URL
        scraper = self._select_best_scraper(url)
        
        if not scraper:
            return None
        
        try:
            # Erstelle temporäre Query für Scraping
            from .base_agent import MineQuery
            temp_query = MineQuery(
                mine_name="",  # Nicht relevant für reines Scraping
                country="",
                region="",
                languages=[]
            )
            
            # Nutze Scraper-spezifische Methode wenn verfügbar
            if hasattr(scraper, 'scrape_url'):
                content = await scraper.scrape_url(url)
            else:
                # Fallback: Nutze search_mine mit URL als "Mine"
                results = await scraper.search_mine(temp_query)
                content = results[0].value if results else None
            
            return content
            
        except Exception as e:
            print(f"❌ Fehler beim Scrapen von {url}: {e}")
            return None
    
    def _select_best_scraper(self, url: str):
        """Wählt den besten Scraper für eine URL"""
        # Prioritätsliste für verschiedene URL-Typen
        domain = urlparse(url).netloc.lower()
        
        # Regierungsseiten brauchen oft spezialisierte Scraper
        if any(gov in domain for gov in ['.gov', '.gob', '.gouv']):
            priority_order = ['brightdata', 'scrapingbee', 'apify', 'firecrawl']
        # PDFs und Dokumente
        elif url.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
            priority_order = ['firecrawl', 'apify', 'scraper']
        # News-Seiten
        elif any(news in domain for news in ['news', 'journal', 'times', 'post']):
            priority_order = ['scraper', 'scrapingbee', 'brightdata']
        # Standard
        else:
            priority_order = ['scraper', 'firecrawl', 'scrapingbee', 'brightdata', 'apify']
        
        # Wähle ersten verfügbaren Scraper
        for scraper_name in priority_order:
            if scraper_name in self.scraper_agents and self.scraper_agents[scraper_name]:
                self.active_scraper = scraper_name
                return self.scraper_agents[scraper_name]
        
        # Fallback: Erster verfügbarer Scraper
        if self.scraper_agents:
            first_available = list(self.scraper_agents.keys())[0]
            self.active_scraper = first_available
            return self.scraper_agents[first_available]
        
        return None
    
    def _extract_from_specific_sections(self, soup: BeautifulSoup, content: Dict[str, List[str]]):
        """Extrahiert aus spezifischen Seitenbereichen"""
        # Suche nach Info-Boxen, Sidebars, etc.
        info_sections = soup.find_all(['aside', 'div'], class_=re.compile('info|sidebar|facts|details'))
        
        for section in info_sections:
            section_text = section.get_text()
            extracted = self._analyze_text_for_fields(section_text)
            
            for field, values in extracted.items():
                if field in content:
                    content[field].extend(values)