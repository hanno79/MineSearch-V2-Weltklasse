"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Gemeinsamer Result Processor für Agent-Ergebnisse
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import re
import hashlib
from ..base_agent import SearchResult
from src.utils.safe_dict_access import safe_get, safe_nested_get, ensure_dict, ensure_list, MineQuery
import logging

logger = logging.getLogger(__name__)

class ResultProcessor:
    """Basis-Klasse für Result Processing"""
    
    def __init__(self, agent_name: str):
        """
        Initialisiert den Result Processor
        
        Args:
            agent_name: Name des Agenten für Source Attribution
        """
        self.agent_name = agent_name
        self.duplicate_threshold = 0.85  # Ähnlichkeitsschwelle für Duplikate
    
    def create_result(self,
                     title: str,
                     url: str,
                     snippet: str,
                     confidence: float = 0.5,
                     metadata: Optional[Dict[str, Any]] = None,
                     source_type: str = "web") -> SearchResult:
        """
        Erstellt ein standardisiertes SearchResult
        
        Args:
            title: Titel des Ergebnisses
            url: URL der Quelle
            snippet: Kurzbeschreibung/Auszug
            confidence: Konfidenz-Score (0-1)
            metadata: Zusätzliche Metadaten
            source_type: Art der Quelle
            
        Returns:
            SearchResult Objekt
        """
        # URL normalisieren
        url = self._normalize_url(url)
        
        # Basis-Metadaten
        base_metadata = {
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "source_type": source_type
        }
        
        # Mit benutzerdefinierten Metadaten kombinieren
        if metadata:
            base_metadata.update(metadata)
        
        # SearchResult erwartet spezifische Felder
        return SearchResult(
            mine_name=safe_get(metadata, 'mine_name', ''),
            field_name='general_info',  # Wird von Subklassen überschrieben
            value={
                'title': self._clean_text(title),
                'url': url,
                'snippet': self._clean_text(snippet)
            },
            source=self.agent_name,
            source_url=url,
            source_date=safe_get(metadata, 'source_date'),
            confidence_score=self._normalize_confidence(confidence),
            agent_name=self.agent_name,
            timestamp=datetime.now(),
            metadata=base_metadata
        )
    
    def process_results(self, 
                       raw_results: List[Dict[str, Any]], 
                       query: MineQuery) -> List[SearchResult]:
        """
        Verarbeitet rohe Ergebnisse zu SearchResults
        
        Args:
            raw_results: Liste von rohen Ergebnisdaten
            query: Die ursprüngliche Suchanfrage
            
        Returns:
            Liste von SearchResult Objekten
        """
        processed = []
        seen_urls = set()
        
        for raw in raw_results:
            try:
                # Ergebnis extrahieren
                result = self._extract_result(raw, query)
                
                if result and result.url not in seen_urls:
                    processed.append(result)
                    seen_urls.add(result.url)
                    
            except Exception as e:
                logger.warning(f"Fehler beim Verarbeiten von Ergebnis: {e}")
                continue
        
        # Duplikate entfernen
        return self._remove_duplicates(processed)
    
    def _extract_result(self, raw: Dict[str, Any], query: MineQuery) -> Optional[SearchResult]:
        """
        Extrahiert ein SearchResult aus rohen Daten
        Muss von Subklassen überschrieben werden
        """
        raise NotImplementedError("Subklassen müssen _extract_result implementieren")
    
    def _normalize_url(self, url: str) -> str:
        """Normalisiert eine URL"""
        if not url:
            return ""
        
        # Protokoll hinzufügen falls fehlt
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Trailing Slash entfernen
        url = url.rstrip('/')
        
        # Fragment entfernen
        url = url.split('#')[0]
        
        return url
    
    def _clean_text(self, text: str) -> str:
        """Bereinigt Text von HTML und Sonderzeichen"""
        if not text:
            return ""
        
        # HTML Tags entfernen
        text = re.sub(r'<[^>]+>', '', text)
        
        # Mehrfache Leerzeichen reduzieren
        text = re.sub(r'\s+', ' ', text)
        
        # Leading/Trailing Whitespace entfernen
        text = text.strip()
        
        return text
    
    def _normalize_confidence(self, confidence: float) -> float:
        """Normalisiert Konfidenz-Score auf 0-1"""
        return max(0.0, min(1.0, confidence))
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Berechnet Ähnlichkeit zwischen zwei Texten (0-1)
        Einfache Implementierung basierend auf gemeinsamen Wörtern
        """
        if not text1 or not text2:
            return 0.0
        
        # In Wörter aufteilen und normalisieren
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Jaccard-Ähnlichkeit
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _remove_duplicates(self, results: List[SearchResult]) -> List[SearchResult]:
        """Entfernt Duplikate basierend auf URL und Titel-Ähnlichkeit"""
        unique_results = []
        
        for result in results:
            is_duplicate = False
            
            for unique in unique_results:
                # Exakte URL-Übereinstimmung
                if result.url == unique.url:
                    is_duplicate = True
                    break
                
                # Titel-Ähnlichkeit prüfen
                similarity = self._calculate_similarity(result.title, unique.title)
                if similarity > self.duplicate_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def calculate_relevance_score(self, 
                                 result: SearchResult, 
                                 query: MineQuery) -> float:
        """
        Berechnet Relevanz-Score für ein Ergebnis
        
        Args:
            result: Das zu bewertende Ergebnis
            query: Die ursprüngliche Suchanfrage
            
        Returns:
            Relevanz-Score (0-1)
        """
        score = 0.0
        
        # Minenname im Titel
        if query.mine_name.lower() in result.title.lower():
            score += 0.3
        
        # Minenname im Snippet
        if query.mine_name.lower() in result.snippet.lower():
            score += 0.2
        
        # Standort-Übereinstimmung
        if query.location:
            if query.location.lower() in result.title.lower():
                score += 0.2
            if query.location.lower() in result.snippet.lower():
                score += 0.1
        
        # Bergbauart-Übereinstimmung
        if query.mining_type:
            keywords = self._get_mining_keywords(query.mining_type)
            for keyword in keywords:
                if keyword in result.title.lower() or keyword in result.snippet.lower():
                    score += 0.1
                    break
        
        # Mit Agent-Konfidenz kombinieren
        final_score = (score * 0.7) + (result.confidence * 0.3)
        
        return min(1.0, final_score)
    
    def _get_mining_keywords(self, mining_type: str) -> List[str]:
        """Gibt relevante Keywords für Bergbauarten zurück"""
        keywords_map = {
            "gold": ["gold", "or", "aurum", "goldmine", "gold mine"],
            "silver": ["silver", "argent", "silber", "silvermine", "silver mine"],
            "copper": ["copper", "cuivre", "kupfer", "coppermine", "copper mine"],
            "coal": ["coal", "charbon", "kohle", "coalmine", "coal mine"],
            "iron": ["iron", "fer", "eisen", "ironmine", "iron mine"],
            "uranium": ["uranium", "uran", "uranmine", "uranium mine"],
            "diamond": ["diamond", "diamant", "diamantmine", "diamond mine"],
        }
        
        return safe_get(keywords_map, mining_type.lower(), [mining_type.lower()])
    
    def deduplicate_across_sources(self, 
                                  all_results: List[SearchResult]) -> List[SearchResult]:
        """
        Dedupliziert Ergebnisse über mehrere Quellen hinweg
        
        Args:
            all_results: Alle Ergebnisse von verschiedenen Agenten
            
        Returns:
            Deduplizierte Ergebnisliste
        """
        # Gruppiere nach URL
        url_groups = {}
        for result in all_results:
            if result.url not in url_groups:
                url_groups[result.url] = []
            url_groups[result.url].append(result)
        
        # Wähle bestes Ergebnis pro URL
        deduplicated = []
        for url, group in url_groups.items():
            # Wähle Ergebnis mit höchster Konfidenz
            best = max(group, key=lambda r: r.confidence)
            
            # Kombiniere Quellen in Metadaten
            sources = list(set(r.source for r in group))
            best.metadata["combined_sources"] = sources
            best.metadata["source_count"] = len(sources)
            
            deduplicated.append(best)
        
        return deduplicated