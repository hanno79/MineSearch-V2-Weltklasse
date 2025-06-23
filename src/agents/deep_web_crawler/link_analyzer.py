"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Link-Analyse und -Verwaltung für Deep Web Crawler
"""

import re
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class LinkAnalyzer:
    """Analysiert und verwaltet Links für Deep Web Crawling"""
    
    def __init__(self, mining_keywords: Dict[str, List[str]]):
        self.mining_keywords = mining_keywords
        
        # Positive URL-Muster für Mining
        self.positive_patterns = [
            r'mine', r'mining', r'mineral', r'resource', r'commodity',
            r'environmental', r'remediation', r'restoration', r'closure',
            r'operator', r'owner', r'production', r'reserve',
            r'geology', r'exploration', r'extraction'
        ]
        
        # Negative URL-Muster
        self.negative_patterns = [
            r'login', r'register', r'signup', r'cart', r'shop',
            r'privacy', r'terms', r'cookie', r'disclaimer',
            r'twitter', r'facebook', r'linkedin', r'youtube',
            r'javascript:', r'mailto:', r'#'
        ]
        
        # Dokumenten-Endungen
        self.document_extensions = [
            '.pdf', '.xlsx', '.xls', '.doc', '.docx',
            '.csv', '.zip', '.rar', '.ppt', '.pptx'
        ]
    
    def find_relevant_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Findet relevante Links auf einer Seite"""
        relevant_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Absolute URL erstellen
            absolute_url = urljoin(base_url, href)
            
            # Validiere URL
            if not self._is_valid_url(absolute_url):
                continue
            
            # Prüfe Relevanz
            link_text = link.get_text(strip=True).lower()
            url_lower = absolute_url.lower()
            
            # Bewerte Link
            if self._is_relevant_link(url_lower, link_text):
                relevant_links.append(absolute_url)
        
        # Entferne Duplikate und sortiere nach Relevanz
        unique_links = list(set(relevant_links))
        return sorted(unique_links, key=lambda url: self._score_url_relevance(url), reverse=True)
    
    def find_documents(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Findet Dokumente (PDFs, Excel, etc.) auf einer Seite"""
        documents = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Prüfe auf Dokument
            if any(absolute_url.lower().endswith(ext) for ext in self.document_extensions):
                doc_info = {
                    'url': absolute_url,
                    'type': self._get_document_type(absolute_url),
                    'text': link.get_text(strip=True),
                    'context': self._get_link_context(link)
                }
                
                # Prüfe Relevanz des Dokuments
                if self._is_relevant_document(doc_info):
                    documents.append(doc_info)
        
        return documents
    
    def calculate_url_depth(self, start_url: str, current_url: str) -> int:
        """Berechnet die Tiefe einer URL relativ zur Start-URL"""
        start_parsed = urlparse(start_url)
        current_parsed = urlparse(current_url)
        
        # Andere Domain = Tiefe 10 (außerhalb)
        if start_parsed.netloc != current_parsed.netloc:
            return 10
        
        # Zähle Pfad-Segmente
        start_path = start_parsed.path.strip('/').split('/')
        current_path = current_parsed.path.strip('/').split('/')
        
        # Berechne Differenz
        common_prefix = 0
        for i, segment in enumerate(start_path):
            if i < len(current_path) and segment == current_path[i]:
                common_prefix += 1
            else:
                break
        
        depth = len(current_path) - common_prefix
        return max(0, depth)
    
    def _is_valid_url(self, url: str) -> bool:
        """Prüft ob URL gültig ist"""
        try:
            parsed = urlparse(url)
            
            # Muss HTTP/HTTPS sein
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Muss Host haben
            if not parsed.netloc:
                return False
            
            # Keine negativen Muster
            url_lower = url.lower()
            if any(re.search(pattern, url_lower) for pattern in self.negative_patterns):
                return False
            
            return True
            
        except:
            return False
    
    def _is_relevant_link(self, url: str, link_text: str) -> bool:
        """Prüft ob Link relevant für Mining ist"""
        combined = url + ' ' + link_text
        
        # Prüfe positive Muster
        relevance_score = 0
        for pattern in self.positive_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                relevance_score += 1
        
        # Prüfe Mining-Keywords
        for category, keywords in self.mining_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined:
                    relevance_score += 2
        
        return relevance_score > 0
    
    def _score_url_relevance(self, url: str) -> float:
        """Bewertet die Relevanz einer URL"""
        score = 0.0
        url_lower = url.lower()
        
        # Bonus für Mining-Keywords in URL
        for pattern in self.positive_patterns:
            if pattern in url_lower:
                score += 1.0
        
        # Bonus für bestimmte Pfade
        if any(path in url_lower for path in ['/mining/', '/mines/', '/minerals/', '/resources/']):
            score += 2.0
        
        # Penalty für lange URLs
        if len(url) > 200:
            score -= 0.5
        
        return score
    
    def _get_document_type(self, url: str) -> str:
        """Bestimmt den Dokumenttyp basierend auf URL"""
        url_lower = url.lower()
        
        if url_lower.endswith('.pdf'):
            return 'PDF'
        elif url_lower.endswith(('.xlsx', '.xls')):
            return 'Excel'
        elif url_lower.endswith(('.doc', '.docx')):
            return 'Word'
        elif url_lower.endswith('.csv'):
            return 'CSV'
        elif url_lower.endswith(('.ppt', '.pptx')):
            return 'PowerPoint'
        elif url_lower.endswith(('.zip', '.rar')):
            return 'Archive'
        else:
            return 'Unknown'
    
    def _get_link_context(self, link_element) -> str:
        """Extrahiert Kontext um einen Link"""
        context_parts = []
        
        # Text des Links
        link_text = link_element.get_text(strip=True)
        if link_text:
            context_parts.append(link_text)
        
        # Vorheriger Text
        prev_sibling = link_element.previous_sibling
        if prev_sibling and isinstance(prev_sibling, str):
            context_parts.insert(0, prev_sibling.strip()[-50:])
        
        # Nachfolgender Text
        next_sibling = link_element.next_sibling
        if next_sibling and isinstance(next_sibling, str):
            context_parts.append(next_sibling.strip()[:50])
        
        # Parent-Text
        parent = link_element.parent
        if parent and parent.name in ['p', 'div', 'li', 'td']:
            parent_text = parent.get_text(strip=True)
            if parent_text and parent_text != link_text:
                context_parts.append(parent_text[:100])
        
        return ' '.join(context_parts)
    
    def _is_relevant_document(self, doc_info: Dict[str, str]) -> bool:
        """Prüft ob Dokument relevant für Mining ist"""
        combined_text = doc_info['text'] + ' ' + doc_info['context']
        combined_lower = combined_text.lower()
        
        # Prüfe auf Mining-relevante Keywords
        relevant_keywords = [
            'mining', 'mine', 'mineral', 'environmental', 'assessment',
            'report', 'study', 'plan', 'closure', 'rehabilitation',
            'technical', 'feasibility', 'ni 43-101', 'jorc'
        ]
        
        return any(keyword in combined_lower for keyword in relevant_keywords)
