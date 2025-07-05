"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Source Aggregator für Multi-Provider Suchen
"""

import logging
from typing import Dict, Any, List
from collections import Counter

logger = logging.getLogger(__name__)


class SourceAggregator:
    """
    Klasse für Quellen-Aggregation und Deduplizierung
    """
    
    def __init__(self):
        self.sources_by_url = {}
        self.provider_results = {}
        self.field_values = {}
        
    def add_provider_result(self, provider_id: str, result: Dict[str, Any]):
        """Füge Provider-Ergebnis zur Aggregation hinzu"""
        self.provider_results[provider_id] = result
        
        # Sammle Feldwerte für Konfidenz-Berechnung
        if result.get('data'):
            for field, value in result['data'].items():
                if value and value != '-':
                    if field not in self.field_values:
                        self.field_values[field] = []
                    self.field_values[field].append({
                        'value': value,
                        'provider': provider_id,
                        'phase': 'phase2' if '_phase2' in provider_id else 'phase1'
                    })
    
    def deduplicate_sources(self, sources: List[Dict]) -> List[Dict]:
        """Dedupliziere Quellen basierend auf URL"""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get('url') or source.get('value', '')
            
            # Normalisiere URL für Vergleich
            normalized_url = self._normalize_url(url)
            
            if normalized_url and normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_sources.append(source)
                self.sources_by_url[normalized_url] = source
        
        # Sortiere nach Relevanz
        return self._rank_sources(unique_sources)
    
    def _normalize_url(self, url: str) -> str:
        """Normalisiere URL für Deduplizierung"""
        if not url:
            return ""
            
        # Entferne trailing slashes und fragments
        url = url.rstrip('/').split('#')[0]
        
        # Entferne www. für Vergleich
        url = url.replace('://www.', '://')
        
        return url.lower()
    
    def _rank_sources(self, sources: List[Dict]) -> List[Dict]:
        """Ranke Quellen nach Relevanz"""
        
        def source_score(source):
            score = 0
            url = source.get('url') or source.get('value', '')
            title = source.get('title', '').lower()
            
            # Priorisiere offizielle Quellen
            if any(gov in url for gov in ['.gov', '.gc.ca', '.gouv']):
                score += 10
            
            # Priorisiere Mining-spezifische Seiten
            if any(mining in url for mining in ['mining.com', 'infomine', 'mern.gouv']):
                score += 8
                
            # Priorisiere Dokumente
            if source.get('type') == 'document' or '.pdf' in url:
                score += 5
                
            # Priorisiere Seiten mit relevanten Keywords im Titel
            if any(kw in title for kw in ['closure', 'cost', 'coordinate', 'owner', 'operator']):
                score += 3
                
            return score
        
        return sorted(sources, key=source_score, reverse=True)
    
    def get_best_data(self) -> Dict[str, Any]:
        """Ermittle beste Werte basierend auf Mehrheitsentscheidung"""
        best_data = {}
        
        for field, values in self.field_values.items():
            if not values:
                continue
                
            # Zähle Vorkommen jedes Werts
            value_counts = Counter(v['value'] for v in values)
            
            # Wähle häufigsten Wert
            most_common_value, count = value_counts.most_common(1)[0]
            
            # Bevorzuge Phase 2 Werte bei Gleichstand
            phase2_values = [v for v in values if v['phase'] == 'phase2']
            if phase2_values and count == 1:
                # Bei Gleichstand nimm Phase 2 Wert
                best_data[field] = phase2_values[0]['value']
            else:
                best_data[field] = most_common_value
        
        return best_data
    
    def get_confidence_scores(self) -> Dict[str, float]:
        """Berechne Konfidenz-Scores für jedes Feld"""
        confidence = {}
        
        for field, values in self.field_values.items():
            if not values:
                continue
                
            # Berechne Übereinstimmung
            value_counts = Counter(v['value'] for v in values)
            most_common_count = value_counts.most_common(1)[0][1]
            
            # Konfidenz = Anzahl Übereinstimmungen / Gesamtanzahl
            confidence[field] = most_common_count / len(values)
            
            # Bonus für Phase 2 Bestätigung
            if any(v['phase'] == 'phase2' for v in values):
                confidence[field] = min(1.0, confidence[field] * 1.2)
        
        return confidence