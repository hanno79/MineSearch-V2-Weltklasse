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

# Import EnhancedSourceDiscovery für Export
from .enhanced_source_discovery import EnhancedSourceDiscovery

logger = logging.getLogger(__name__)

# Export EnhancedSourceDiscovery für andere Module
__all__ = ['SourceManager', 'SourceReference', 'EnhancedSourceDiscovery']


@dataclass
class SourceReference:
    """Einzelne Quellenreferenz"""
    id: int
    url: str
    title: str = ""
    type: str = None  # REGEL 10: NULL statt "unknown" Fallback-Wert
    reliability: float = None  # REGEL 10: Keine Fallback-Werte - nur echte Zuverlässigkeit oder None


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
        """__init__ - TODO: Dokumentation hinzufügen"""
        self.sources: Dict[int, SourceReference] = {}
        self.next_id = 1
        self.field_sources: Dict[str, List[int]] = {}

    def add_source(self, url: str, title: str = "", source_type: str = None, reliability: float = None) -> int:
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

        # Pattern für verschiedene URL-Formate und generische Quellen-Referenzen
        source_patterns = [
            # Echte URLs
            (r'https?://[^\s\]]+', 'url'),
            (r'www\.[^\s\]]+', 'url'),
            (r'\[(\d+)\]\s*(https?://[^\s\]]+)', 'numbered_url'),

            # Generische Quellen-Referenzen (häufig in Provider-Responses)
            (r'\[Quelle:\s*([^\]]+)\]', 'generic_source'),
            (r'Quelle:\s*([^\n\]\.]+)', 'generic_source'),
            (r'Source:\s*([^\n\]\.]+)', 'generic_source'),
            (r'\[Source:\s*([^\]]+)\]', 'generic_source'),

            # Weitere mögliche Formate
            (r'\[Ref:\s*([^\]]+)\]', 'reference'),
            (r'Referenz:\s*([^\n\]\.]+)', 'reference'),
        ]

        for pattern, source_type_hint in source_patterns:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                if source_type_hint == 'numbered_url':
                    url = match.group(2)
                elif len(match.groups()) > 0:
                    url = match.group(1)
                else:
                    url = match.group(0)

                # Bereinige URL/Quelle
                url = url.strip('.,;!? \n\r\t[])')

                # Für generische Quellen: Behandle als "Quelle" auch wenn es keine URL ist
                if source_type_hint in ['generic_source', 'reference']:
                    # Generische Quelle hinzufügen (auch ohne gültige URL)
                    source_type = self._classify_generic_source(url)
                    reliability = self._calculate_generic_reliability(url, source_type)

                    # Verwende beschreibenden "URL" für generische Quellen
                    formatted_url = f"generic_source:{url}"
                    source_id = self.add_source(formatted_url, url, source_type, reliability)
                    if source_id not in found_sources:
                        found_sources.append(source_id)
                elif self._is_valid_url(url):
                    # Echte URL
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
            # REGEL 10 FIX 29.08.2025: Keine Dummy-Werte - leerer String wenn keine Quellen
            return ""

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
            'industry': 0.5  # Legitimer Score für Industrie-Quellen
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

    def _classify_generic_source(self, source_description: str) -> str:
        """Klassifiziert generische Quellen-Beschreibungen"""
        desc_lower = source_description.lower()

        # KRITISCHE VERBESSERUNG 26.08.2025: Erkenne Schätzungs-Quellen für niedrigen Reliability Score
        if any(term in desc_lower for term in ['fachwissen', 'allgemeines fachwissen', 'schätzung',
'geschätzt', 'typisch', 'estimated', 'generic_source']):
            return 'unreliable_estimate'  # NEUE KATEGORIE für Schätzungen
        elif any(term in desc_lower for term in ['expert', 'knowledge', 'expertise']):
            return 'expert_knowledge'
        elif any(term in desc_lower for term in ['database', 'datenbank', 'data']):
            return 'database'
        elif any(term in desc_lower for term in ['company', 'unternehmen', 'corporate', 'reports']):
            return 'corporate'
        elif any(term in desc_lower for term in ['mining', 'bergbau', 'geological']):
            return 'mining_industry'
        elif any(term in desc_lower for term in ['government', 'regierung', 'official']):
            return 'government'
        elif any(term in desc_lower for term in ['research', 'forschung', 'study']):
            return 'research'
        else:
            return 'general'

    def _calculate_generic_reliability(self, source_description: str, source_type: str) -> float:
        """Berechnet Zuverlässigkeits-Score für generische Quellen"""
        base_scores = {
            'government': 0.9,
            'research': 0.8,
            'database': 0.7,
            'expert_knowledge': 0.6,
            'corporate': 0.5,  # Legitimer Score für Corporate-Quellen
            'mining_industry': 0.6,
            'unreliable_estimate': 0.1,  # KRITISCHE VERBESSERUNG 26.08.2025: Niedrigster Score für Schätzungen
            'general': 0.4
        }

        return base_scores.get(source_type, 0.4)
