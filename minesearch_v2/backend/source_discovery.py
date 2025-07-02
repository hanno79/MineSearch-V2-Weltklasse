"""
Author: rahn
Datum: 30.06.2025
Version: 1.0
Beschreibung: Quellenextraktion und -verarbeitung für MineSearch
"""

import re
import logging
from typing import List, Dict, Any, Optional

# ÄNDERUNG 30.06.2025: Strukturiertes Logging (Regel 16)
logger = logging.getLogger(__name__)


class SourceDiscovery:
    """Service für die Extraktion und Verarbeitung von Quellen aus Mining-Dokumenten"""
    
    def __init__(self):
        # Invalide Einträge die gefiltert werden sollen
        self.invalid_entries = [
            '', ' ', '...', 'k.A.', 'k.a.', '[', ']', 
            'Perplexity Search', 'keine', 'nicht gefunden',
            'nicht verfügbar', 'no specific'
        ]
        
        # Mindestlänge für valide Quellen
        self.min_source_length = 10
    
    def extract_sources_from_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Extrahiere alle Quellen aus dem Content
        
        Args:
            content: Text mit Quellenangaben
            
        Returns:
            Liste von Quellen-Dictionaries
        """
        sources = []
        seen_values = set()
        
        # ÄNDERUNG 30.06.2025: Try-catch für Quellenextraktion (Regel 13)
        try:
            # 1. Inline-Quellen
            sources.extend(self._extract_inline_sources(content, seen_values))
            
            # 2. Nummerierte Quellen
            sources.extend(self._extract_numbered_sources(content, seen_values))
            
            # 3. URLs
            sources.extend(self._extract_urls(content, seen_values))
            
            # 4. Dokument-Referenzen
            sources.extend(self._extract_document_references(content, seen_values))
            
            # 5. Organisationen
            sources.extend(self._extract_organizations(content, seen_values))
            
            # 6. Quellen-Sektion
            sources.extend(self._extract_source_section(content, seen_values))
            
            logger.debug(f"[SOURCE EXTRACTION] {len(sources)} Quellen extrahiert")
            
        except Exception as e:
            logger.error(f"[SOURCE EXTRACTION ERROR] {str(e)}")
        
        return sources
    
    def _extract_inline_sources(self, content: str, seen_values: set) -> List[Dict[str, Any]]:
        """Extrahiere Inline-Quellen im Format [Quelle: ...] oder [Source: ...]"""
        sources = []
        
        inline_patterns = [
            r'\[Quelle:\s*([^\]]+)\]',
            r'\[Source:\s*([^\]]+)\]',
            r'\(Quelle:\s*([^\)]+)\)',
            r'\(Source:\s*([^\)]+)\)'
        ]
        
        for pattern in inline_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                value = match.strip()
                if self._is_valid_source(value, seen_values):
                    seen_values.add(value)
                    source_type = 'url' if self._is_url(value) else 'document'
                    sources.append({
                        'type': source_type,
                        'value': value
                    })
        
        return sources
    
    def _extract_numbered_sources(self, content: str, seen_values: set) -> List[Dict[str, Any]]:
        """Extrahiere nummerierte Quellen [1], [2], etc."""
        sources = []
        
        numbered_sources = re.findall(r'\[(\d+)\]\s*([^\n\[]+)', content)
        for num, source in numbered_sources:
            value = source.strip().rstrip('.,;:)]')
            
            if self._is_valid_source(value, seen_values):
                seen_values.add(value)
                
                if self._is_url(value):
                    # Validiere URL zusätzlich
                    if re.match(r'https?://[^\s]+\.[^\s]+', value):
                        sources.append({'type': 'url', 'value': value})
                else:
                    sources.append({'type': 'document', 'value': value})
        
        return sources
    
    def _extract_urls(self, content: str, seen_values: set) -> List[Dict[str, Any]]:
        """Extrahiere URLs aus dem Content"""
        sources = []
        
        # Verbessertes URL-Pattern
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        urls = re.findall(url_pattern, content)
        
        for url in urls:
            # Bereinige URL
            url = url.rstrip('.,;:)')
            
            if url not in seen_values:
                seen_values.add(url)
                sources.append({
                    'type': 'url',
                    'value': url,
                    'context': self._extract_context(content, url)
                })
        
        return sources
    
    def _extract_document_references(self, content: str, seen_values: set) -> List[Dict[str, Any]]:
        """Extrahiere Dokument-Referenzen"""
        sources = []
        
        doc_patterns = [
            r'(NI\s*43-101\s*(?:Technical\s+)?Report[^,\n]*)',
            r'(Annual\s+Report\s+\d{4}[^,\n]*)',
            r'((?:Environmental|Closure|Feasibility)\s+(?:Impact\s+)?(?:Assessment|Study|Report)[^,\n]*)',
            r'(SEDAR\s+(?:filing|document)[^,\n]*)',
            r'((?:Q\d|Year-end)\s+\d{4}\s+(?:Report|Results)[^,\n]*)',
            r'(Jahresbericht\s+\d{4}[^,\n]*)',
            r'(Umweltbericht[^,\n]*)',
            r'(Machbarkeitsstudie[^,\n]*)',
            r'(Sustainability\s+Report[^,\n]*)',
            r'(Technical\s+Study[^,\n]*)',
            r'(Resource\s+Estimate[^,\n]*)'
        ]
        
        for pattern in doc_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                value = match.strip()
                if self._is_valid_source(value, seen_values, min_length=5):
                    seen_values.add(value)
                    sources.append({
                        'type': 'document',
                        'value': value,
                        'context': self._extract_context(content, match)
                    })
        
        return sources
    
    def _extract_organizations(self, content: str, seen_values: set) -> List[Dict[str, Any]]:
        """Extrahiere Organisationen und Datenbanken"""
        sources = []
        
        org_patterns = [
            r'(?:according to|per|from|source:|quelle:|laut)\s+([A-Z][^,\n]{3,50})',
            r'((?:SEDAR|EDGAR|InfoMine|Mining\.com|S&P Global|Natural Resources Canada|USGS)[^,\n]*)',
            r'((?:MERN|GESTIM|BLM|DMIRS|SERNAGEOMIN|INGEMMET)[^,\n]*)',
            r'((?:TSX|ASX|JSE|NYSE|NASDAQ)[^,\n]*)'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                value = match.strip()
                if self._is_valid_source(value, seen_values, min_length=3):
                    seen_values.add(value)
                    sources.append({
                        'type': 'organization',
                        'value': value,
                        'context': self._extract_context(content, match)
                    })
        
        return sources
    
    def _extract_source_section(self, content: str, seen_values: set) -> List[Dict[str, Any]]:
        """Extrahiere dedizierte Quellen-Sektion"""
        sources = []
        
        # Patterns für Quellen-Sektionen
        quellen_patterns = [
            r'\*\*QUELLEN-SEKTION:\*\*(.*?)(?:\*\*|$)',
            r'QUELLEN[:\-\s]*\n(.*?)(?:\n\n|$)',
            r'(?:References|Referenzen|Sources)[:\-\s]*\n(.*?)(?:\n\n|$)'
        ]
        
        for pattern in quellen_patterns:
            quellen_section = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if quellen_section:
                quellen_text = quellen_section.group(1)
                
                # Extrahiere nummerierte Quellen
                quellen_items = re.findall(r'\[(\d+)\]\s*([^\[\n]+)', quellen_text)
                for num, item in quellen_items:
                    value = item.strip().rstrip('.,;:)]')
                    
                    if self._is_valid_source(value, seen_values):
                        seen_values.add(value)
                        
                        if value.startswith('http'):
                            if re.match(r'https?://[^\s]+\.[^\s]+', value):
                                sources.append({'type': 'url', 'value': value})
                        else:
                            sources.append({'type': 'document', 'value': value})
                
                break  # Nur erste gefundene Sektion verarbeiten
        
        return sources
    
    def _extract_context(self, content: str, target: str, context_length: int = 100) -> str:
        """Extrahiere Kontext um einen gefundenen Begriff"""
        try:
            index = content.find(target)
            if index == -1:
                return ""
            
            start = max(0, index - context_length)
            end = min(len(content), index + len(target) + context_length)
            
            context = content[start:end]
            # Bereinige Kontext
            context = ' '.join(context.split())
            
            return f"...{context}..."
        except Exception:
            return ""
    
    def _is_valid_source(self, value: str, seen_values: set, min_length: Optional[int] = None) -> bool:
        """Prüfe ob eine Quelle valide ist"""
        if not value:
            return False
        
        # Verwende Standard-Mindestlänge wenn nicht spezifiziert
        min_len = min_length or self.min_source_length
        
        # Prüfe auf invalide Einträge
        value_lower = value.lower()
        for invalid in self.invalid_entries:
            if invalid in value_lower:
                return False
        
        # Prüfe ob bereits gesehen
        if value in seen_values:
            return False
        
        # Prüfe Mindestlänge
        if len(value) < min_len:
            return False
        
        return True
    
    def _is_url(self, value: str) -> bool:
        """Prüfe ob ein Wert eine URL ist"""
        return 'http' in value.lower() or 'www.' in value.lower()


# Globale Instanz
source_discovery = SourceDiscovery()


# Wrapper-Funktionen für Kompatibilität
def extract_sources_from_content(content: str) -> List[Dict[str, Any]]:
    """Wrapper für extract_sources_from_content"""
    return source_discovery.extract_sources_from_content(content)


def extract_source_numbers(text: str) -> List[int]:
    """
    Extrahiere Quellennummern aus Text wie [1], [2,3], [Quelle: 1]
    
    Args:
        text: Text mit Quellennummern
        
    Returns:
        Liste von Quellennummern
    """
    numbers = []
    
    # Pattern für [1], [2], [1,2,3] etc.
    matches = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', text)
    for match in matches:
        # Splitte bei Komma für multiple Quellen
        for num in match.split(','):
            try:
                numbers.append(int(num.strip()))
            except ValueError:
                pass
    
    # Pattern für [Quelle: 1], [Source: 2] etc.
    matches = re.findall(r'\[(?:Quelle|Source):\s*(\d+)\]', text, re.IGNORECASE)
    for match in matches:
        try:
            numbers.append(int(match))
        except ValueError:
            pass
    
    return sorted(list(set(numbers)))  # Entferne Duplikate und sortiere


def _extract_context(content: str, target: str, context_length: int = 100) -> str:
    """
    Extrahiere Kontext um einen gefundenen Begriff
    
    Args:
        content: Gesamter Text
        target: Gesuchter Begriff
        context_length: Länge des Kontexts
        
    Returns:
        Kontext-String
    """
    try:
        index = content.find(target)
        if index == -1:
            return ""
        
        start = max(0, index - context_length)
        end = min(len(content), index + len(target) + context_length)
        
        context = content[start:end]
        # Bereinige Kontext
        context = ' '.join(context.split())
        
        return f"...{context}..."
    except Exception:
        return ""