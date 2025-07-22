"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Source Manager für Quellen-Nummerierung und Tracking
"""

import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SourceReference:
    """Einzelne Quellenreferenz"""
    id: int
    url: str
    title: str = ""
    type: str = "unknown"
    reliability: float = 0.5


class SourceManager:
    """
    Verwaltet Quellen-Nummerierung und Tracking für eine Suche
    
    Funktionen:
    - Eindeutige Nummerierung von Quellen (fortlaufend pro Suche)
    - Extraktion von Quellen aus Provider-Responses
    - Zuordnung von Feldern zu ihren Quellen
    - Formatierung für CSV und Frontend
    """
    
    def __init__(self):
        self.sources: Dict[int, SourceReference] = {}
        self.next_id = 1
        self.field_sources: Dict[str, List[int]] = {}
    
    def add_source(self, url: str, title: str = "", source_type: str = "unknown", reliability: float = 0.5) -> int:
        """
        Fügt eine neue Quelle hinzu oder gibt existierende ID zurück
        
        Args:
            url: URL der Quelle
            title: Titel/Beschreibung
            source_type: Typ (government, database, industry, etc.)
            reliability: Zuverlässigkeits-Score 0.0-1.0
            
        Returns:
            Quellen-ID
        """
        # Prüfe ob Quelle bereits existiert
        for source_id, source in self.sources.items():
            if source.url == url:
                return source_id
        
        # Neue Quelle hinzufügen
        source_id = self.next_id
        self.sources[source_id] = SourceReference(
            id=source_id,
            url=url,
            title=title,
            type=source_type,
            reliability=reliability
        )
        self.next_id += 1
        
        logger.debug(f"[SOURCE] Quelle {source_id} hinzugefügt: {url[:60]}...")
        return source_id
    
    def assign_field_sources(self, field_name: str, source_ids: List[int]) -> None:
        """
        Ordnet einem Feld eine Liste von Quellen-IDs zu
        
        Args:
            field_name: Name des Datenfeldes
            source_ids: Liste der Quellen-IDs
        """
        if source_ids:
            self.field_sources[field_name] = source_ids
            logger.debug(f"[SOURCE] Feld '{field_name}' zugeordnet zu Quellen: {source_ids}")
    
    def extract_sources_from_response(self, response_text: str) -> List[int]:
        """
        Extrahiert Quellen aus Provider-Response und fügt sie hinzu
        
        Args:
            response_text: Antwort-Text vom Provider
            
        Returns:
            Liste der gefundenen Quellen-IDs
        """
        found_sources = []
        
        # Pattern für verschiedene URL-Formate
        url_patterns = [
            r'https?://[^\s\]]+',
            r'www\.[^\s\]]+',
            r'\[Quelle: ([^\]]+)\]',
            r'Quelle: ([^\n\]]+)',
            r'Source: ([^\n\]]+)',
            r'\[(\d+)\]\s*(https?://[^\s\]]+)'
        ]
        
        for pattern in url_patterns:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                url = match.group(1) if len(match.groups()) > 0 else match.group(0)
                
                # Bereinige URL
                url = url.strip('.,;!? \n\r\t[])')
                
                # Validiere URL
                if self._is_valid_url(url):
                    # Klassifiziere Quelle
                    source_type = self._classify_source(url)
                    reliability = self._calculate_reliability(url, source_type)
                    
                    source_id = self.add_source(url, "", source_type, reliability)
                    if source_id not in found_sources:
                        found_sources.append(source_id)
        
        logger.info(f"[SOURCE] {len(found_sources)} Quellen aus Response extrahiert")
        return found_sources
    
    def parse_field_with_sources(self, field_text: str) -> Tuple[str, List[int]]:
        """
        Parst Feld-Text und extrahiert Quellen-Referenzen
        
        Beispiel Input: "Open-Pit [1,3] mit großer Kapazität"
        Output: ("Open-Pit mit großer Kapazität", [1, 3])
        
        Args:
            field_text: Text mit potentiellen Quellen-Referenzen
            
        Returns:
            Tuple (bereinigter_text, quellen_ids)
        """
        if not field_text:
            return "", []
        
        # Pattern für Quellen in eckigen Klammern: [1,2,3] oder [1] oder [1,2]
        source_pattern = r'\[(\d+(?:,\s*\d+)*)\]'
        
        source_ids = []
        matches = re.finditer(source_pattern, field_text)
        
        for match in matches:
            ids_str = match.group(1)
            ids = [int(id_str.strip()) for id_str in ids_str.split(',')]
            source_ids.extend(ids)
        
        # Entferne Quellen-Referenzen aus Text
        clean_text = re.sub(source_pattern, '', field_text)
        # Entferne doppelte Leerzeichen und trimme
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text, source_ids
    
    def format_field_with_sources(self, field_value: str, field_name: str) -> str:
        """
        Formatiert Feld-Wert mit Quellen-Referenzen
        
        Args:
            field_value: Original-Feldwert
            field_name: Name des Feldes
            
        Returns:
            Formatierter Wert mit Quellen-Referenzen
        """
        if not field_value or field_value == 'X':
            return field_value
        
        source_ids = self.field_sources.get(field_name, [])
        if not source_ids:
            return field_value
        
        # Sortiere IDs und formatiere
        source_ids = sorted(set(source_ids))
        source_ref = f"[{','.join(map(str, source_ids))}]"
        
        return f"{field_value} {source_ref}"
    
    def get_sources_summary(self) -> str:
        """
        Erstellt Quellenangaben-Summary für CSV-Spalte
        
        Returns:
            Formatierte Quellenangaben
        """
        if not self.sources:
            return "Keine spezifischen Quellen dokumentiert"
        
        formatted_sources = []
        for source_id in sorted(self.sources.keys()):
            source = self.sources[source_id]
            title = source.title if source.title else f"Quelle {source_id}"
            formatted_sources.append(f"[{source_id}] {title}: {source.url}")
        
        return "\n".join(formatted_sources)
    
    def get_sources_dict(self) -> Dict[str, Any]:
        """
        Gibt Quellen als Dictionary für JSON-Speicherung zurück
        
        Returns:
            Dictionary mit allen Quellen und Feld-Zuordnungen
        """
        return {
            "sources": {
                str(sid): {
                    "url": source.url,
                    "title": source.title,
                    "type": source.type,
                    "reliability": source.reliability
                }
                for sid, source in self.sources.items()
            },
            "field_sources": {
                field: ids for field, ids in self.field_sources.items()
            }
        }
    
    def _is_valid_url(self, url: str) -> bool:
        """Validiert URL-Format"""
        if len(url) < 8:  # Mindestlänge für sinnvolle URL
            return False
        
        valid_prefixes = ['http://', 'https://', 'www.', 'ftp://']
        has_valid_prefix = any(url.lower().startswith(prefix) for prefix in valid_prefixes)
        
        # Oder enthält Domain-Pattern
        has_domain = bool(re.search(r'\w+\.\w+', url))
        
        return has_valid_prefix or has_domain
    
    def _classify_source(self, url: str) -> str:
        """Klassifiziert Quellen-Typ basierend auf URL"""
        url_lower = url.lower()
        
        if any(gov in url_lower for gov in ['.gov', '.gouv', 'government', 'regierung']):
            return 'government'
        elif any(db in url_lower for db in ['database', 'data.', 'api.', 'db.']):
            return 'database'
        elif any(exch in url_lower for exch in ['sedar', 'sec.gov', 'exchange', 'tsx', 'nasdaq']):
            return 'exchange'
        elif any(news in url_lower for news in ['reuters', 'bloomberg', 'mining.com', 'kitco']):
            return 'news'
        elif any(acad in url_lower for acad in ['.edu', '.ac.', 'university', 'research']):
            return 'academic'
        else:
            return 'industry'
    
    def _calculate_reliability(self, url: str, source_type: str) -> float:
        """Berechnet Zuverlässigkeits-Score"""
        base_scores = {
            'government': 0.9,
            'academic': 0.8,
            'exchange': 0.8,
            'database': 0.7,
            'news': 0.6,
            'industry': 0.5
        }
        
        base_score = base_scores.get(source_type, 0.4)
        
        # Bonus für bekannte vertrauenswürdige Domains
        trusted_domains = [
            'gov.', 'gouv.', 'nrcan.gc.ca', 'usgs.gov', 
            'sedar.com', 'sec.gov', 'reuters.com', 'bloomberg.com'
        ]
        
        if any(domain in url.lower() for domain in trusted_domains):
            base_score = min(1.0, base_score + 0.1)
        
        return base_score