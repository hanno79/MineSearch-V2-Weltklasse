"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Analysefunktionen für entdeckte Quellen
"""

from typing import Dict, List, Optional, Any
import re
from .models import SourceType, DiscoveredSource
from .pattern_manager import SourcePatternManager

class SourceAnalyzer:
    """Analysiert und kategorisiert entdeckte Quellen"""
    
    def __init__(self):
        self.pattern_manager = SourcePatternManager()
        self.mining_terms = self._initialize_mining_terms()
        self.language_indicators = self._initialize_language_indicators()
        
    def _initialize_mining_terms(self) -> List[str]:
        """Initialisiert Mining-bezogene Begriffe"""
        return [
            'mining', 'mine', 'mineral', 'extraction', 'resources',
            'copper', 'gold', 'silver', 'zinc', 'coal', 'iron',
            'environmental', 'permit', 'license', 'concession',
            'production', 'reserves', 'exploration'
        ]
    
    def _initialize_language_indicators(self) -> Dict[str, List[str]]:
        """Initialisiert Sprach-Indikatoren"""
        return {
            'en': ['the', 'and', 'of', 'mining', 'resources'],
            'es': ['el', 'la', 'de', 'minería', 'recursos'],
            'fr': ['le', 'la', 'de', 'exploitation', 'ressources'],
            'pt': ['o', 'a', 'de', 'mineração', 'recursos'],
            'de': ['der', 'die', 'das', 'Bergbau', 'Ressourcen']
        }
    
    def categorize_source(self, source: Dict[str, Any]) -> Optional[DiscoveredSource]:
        """Kategorisiert eine gefundene Quelle"""
        url = source.get('url', '')
        title = source.get('title', '').lower()
        snippet = source.get('snippet', '').lower()
        
        # Bestimme Quellentyp
        source_type = self.determine_source_type(url, title, snippet)
        
        # Berechne Relevanz
        relevance_score = self.calculate_relevance(url, title, snippet)
        
        # Bestimme Sprache
        language = self.detect_language(title + " " + snippet)
        
        # Extrahiere gefundene Keywords
        keywords = self.extract_keywords(title + " " + snippet)
        
        if relevance_score > 0.3:  # Mindest-Relevanz
            return DiscoveredSource(
                url=url,
                source_type=source_type,
                relevance_score=relevance_score,
                language=language,
                keywords_found=keywords,
                depth_to_explore=self.determine_crawl_depth(source_type, relevance_score),
                priority=self.calculate_priority(source_type, relevance_score)
            )
        
        return None
    
    def determine_source_type(self, url: str, title: str, snippet: str) -> SourceType:
        """Bestimmt den Typ einer Quelle"""
        combined_text = f"{url} {title} {snippet}".lower()
        
        # Prüfe gegen Muster
        for source_type in SourceType:
            patterns = self.pattern_manager.get_patterns_for_type(source_type)
            for pattern in patterns:
                if pattern in combined_text:
                    return source_type
        
        return SourceType.INDUSTRY  # Default
    
    def calculate_relevance(self, url: str, title: str, snippet: str) -> float:
        """Berechnet Relevanz-Score einer Quelle"""
        score = 0.5  # Basis-Score
        
        # Erhöhe Score für offizielle Domains
        official_indicators = ['gov', 'gob', 'gouv', 'official', 'ministry']
        for indicator in official_indicators:
            if indicator in url.lower():
                score += 0.2
                break
        
        # Mining-spezifische Keywords
        keyword_count = sum(1 for kw in self.mining_terms if kw in snippet.lower())
        score += keyword_count * 0.1
        
        # Domain-Endungen
        if url.endswith(('.gov', '.gob', '.gouv', '.edu', '.ac')):
            score += 0.2
        
        return min(score, 1.0)
    
    def detect_language(self, text: str) -> str:
        """Einfache Spracherkennung"""
        text_lower = text.lower()
        scores = {}
        
        for lang, indicators in self.language_indicators.items():
            score = sum(1 for ind in indicators if ind in text_lower)
            scores[lang] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'en'  # Default
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrahiert relevante Keywords aus Text"""
        found_keywords = []
        text_lower = text.lower()
        
        for term in self.mining_terms:
            if term in text_lower:
                found_keywords.append(term)
        
        return found_keywords
    
    def determine_crawl_depth(self, source_type: SourceType, relevance: float) -> int:
        """Bestimmt wie tief eine Quelle gecrawlt werden soll"""
        depth = self.pattern_manager.get_base_crawl_depth(source_type)
        
        # Erhöhe Tiefe für hochrelevante Quellen
        if relevance > 0.8:
            depth += 2
        elif relevance > 0.6:
            depth += 1
        
        return min(depth, 7)  # Maximal 7 Ebenen
    
    def calculate_priority(self, source_type: SourceType, relevance: float) -> int:
        """Berechnet Priorität einer Quelle"""
        base_priority = self.pattern_manager.get_base_priority(source_type)
        
        # Adjustiere basierend auf Relevanz
        priority = base_priority + int(relevance * 5)
        
        return min(priority, 15)