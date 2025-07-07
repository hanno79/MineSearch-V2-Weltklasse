"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: Validiert Konsistenz von Mining-Suchergebnissen
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import statistics
from extraction_validators import is_placeholder_value
from config import CSV_COLUMNS

logger = logging.getLogger(__name__)


class ConsistencyValidator:
    """Validiert und bewertet die Konsistenz von Suchergebnissen"""
    
    # Felder die immer konsistent sein sollten
    CRITICAL_FIELDS = ['Name', 'Country', 'Region']
    
    # Felder wo kleine Varianz akzeptabel ist
    VARIABLE_FIELDS = ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate', 'Fläche der Mine in qkm']
    
    # Akzeptable Varianz für numerische Felder (Coefficient of Variation)
    ACCEPTABLE_CV = {
        'Restaurationskosten': 0.2,  # 20% Varianz ok
        'x-Koordinate': 0.01,        # 1% Varianz ok (GPS-Präzision)
        'y-Koordinate': 0.01,        # 1% Varianz ok
        'Fläche der Mine in qkm': 0.1  # 10% Varianz ok
    }
    
    def __init__(self):
        self.results = []
        
    def add_result(self, result: Dict[str, Any]):
        """Fügt ein Suchergebnis zur Validierung hinzu"""
        self.results.append(result)
        
    def validate_consistency(self) -> Dict[str, Any]:
        """
        Validiert die Konsistenz aller hinzugefügten Ergebnisse
        
        Returns:
            Dict mit Konsistenz-Scores und Details pro Feld
        """
        if len(self.results) < 2:
            return {
                'overall_score': 1.0,
                'consistent': True,
                'message': 'Nicht genug Ergebnisse für Konsistenz-Validierung',
                'field_scores': {}
            }
            
        # Analysiere jedes Feld
        field_analysis = {}
        for field in CSV_COLUMNS:
            field_values = [r.get(field, '') for r in self.results]
            score, details = self._analyze_field_consistency(field, field_values)
            field_analysis[field] = {
                'score': score,
                'consistent': score >= 0.8,  # 80% Konsistenz-Schwelle
                'details': details
            }
            
        # Berechne Gesamt-Score
        all_scores = [f['score'] for f in field_analysis.values()]
        overall_score = statistics.mean(all_scores) if all_scores else 0
        
        # Prüfe kritische Felder
        critical_consistent = all(
            field_analysis.get(f, {}).get('consistent', False) 
            for f in self.CRITICAL_FIELDS
        )
        
        return {
            'overall_score': overall_score,
            'consistent': overall_score >= 0.8 and critical_consistent,
            'critical_fields_ok': critical_consistent,
            'field_scores': field_analysis,
            'recommendations': self._generate_recommendations(field_analysis)
        }
    
    def _analyze_field_consistency(self, field: str, values: List[Any]) -> Tuple[float, Dict]:
        """Analysiert Konsistenz für ein einzelnes Feld"""
        # Filtere leere Werte und Platzhalter
        clean_values = []
        for v in values:
            if v and not is_placeholder_value(str(v), field):
                clean_values.append(v)
                
        if not clean_values:
            return 0.0, {'type': 'empty', 'message': 'Keine gültigen Werte gefunden'}
            
        # Für kritische Felder: Müssen exakt gleich sein
        if field in self.CRITICAL_FIELDS:
            unique_values = list(set(clean_values))
            if len(unique_values) == 1:
                return 1.0, {'type': 'critical', 'consistent': True, 'value': unique_values[0]}
            else:
                return 0.0, {
                    'type': 'critical', 
                    'consistent': False, 
                    'values': unique_values,
                    'message': f'Inkonsistente Werte: {unique_values}'
                }
                
        # Für numerische variable Felder
        if field in self.VARIABLE_FIELDS:
            try:
                numeric_values = []
                for v in clean_values:
                    # Extrahiere numerischen Wert
                    if isinstance(v, (int, float)):
                        numeric_values.append(float(v))
                    else:
                        # Versuche aus String zu extrahieren
                        import re
                        num_match = re.search(r'[\d,]+(?:\.\d+)?', str(v))
                        if num_match:
                            numeric_values.append(float(num_match.group().replace(',', '')))
                            
                if len(numeric_values) >= 2:
                    mean = statistics.mean(numeric_values)
                    stdev = statistics.stdev(numeric_values)
                    cv = stdev / abs(mean) if mean != 0 else 0
                    
                    # Prüfe ob Varianz akzeptabel ist
                    acceptable_cv = self.ACCEPTABLE_CV.get(field, 0.1)
                    score = max(0, 1 - (cv / acceptable_cv)) if cv <= acceptable_cv else 0
                    
                    return score, {
                        'type': 'numeric_variable',
                        'mean': mean,
                        'stdev': stdev,
                        'cv': cv,
                        'acceptable_cv': acceptable_cv,
                        'values': numeric_values
                    }
            except Exception as e:
                logger.error(f"Fehler bei numerischer Analyse für {field}: {e}")
                
        # Für andere Felder: Textvergleich
        unique_values = list(set(clean_values))
        consistency_score = 1.0 if len(unique_values) == 1 else (1.0 / len(unique_values))
        
        return consistency_score, {
            'type': 'text',
            'unique_values': unique_values,
            'unique_count': len(unique_values),
            'value_distribution': {v: clean_values.count(v) for v in unique_values}
        }
    
    def _generate_recommendations(self, field_analysis: Dict) -> List[str]:
        """Generiert Empfehlungen basierend auf der Analyse"""
        recommendations = []
        
        # Prüfe kritische Felder
        for field in self.CRITICAL_FIELDS:
            if not field_analysis.get(field, {}).get('consistent', False):
                recommendations.append(f"KRITISCH: Feld '{field}' ist inkonsistent!")
                
        # Prüfe variable Felder
        inconsistent_fields = []
        for field, analysis in field_analysis.items():
            if analysis['score'] < 0.8 and field not in self.CRITICAL_FIELDS:
                inconsistent_fields.append((field, analysis['score']))
                
        if inconsistent_fields:
            recommendations.append(
                f"Inkonsistente Felder: {', '.join([f'{f} ({s:.1%})' for f, s in inconsistent_fields])}"
            )
            
        # Allgemeine Empfehlungen
        if not recommendations:
            recommendations.append("Alle Felder zeigen akzeptable Konsistenz")
        else:
            recommendations.append("Empfehlung: Nutze Mehrheitsentscheidung oder beste Quelle")
            
        return recommendations
    
    def get_consensus_result(self) -> Dict[str, Any]:
        """
        Erstellt ein Konsens-Ergebnis aus allen Resultaten
        Nutzt Mehrheitsentscheidung oder besten Wert
        """
        if not self.results:
            return {}
            
        consensus = {}
        confidence_scores = {}
        
        for field in CSV_COLUMNS:
            field_values = [(r.get(field, ''), r) for r in self.results]
            
            # Filtere leere Werte
            non_empty = [(v, r) for v, r in field_values if v and not is_placeholder_value(str(v), field)]
            
            if not non_empty:
                consensus[field] = ''
                confidence_scores[field] = 0.0
                continue
                
            # Für kritische Felder: Mehrheitsentscheidung
            if field in self.CRITICAL_FIELDS:
                value_counts = defaultdict(int)
                for v, _ in non_empty:
                    value_counts[v] += 1
                    
                # Wähle häufigsten Wert
                best_value = max(value_counts.items(), key=lambda x: x[1])[0]
                consensus[field] = best_value
                confidence_scores[field] = value_counts[best_value] / len(non_empty)
                
            # Für numerische Felder: Durchschnitt oder Median
            elif field in self.VARIABLE_FIELDS:
                try:
                    numeric_values = []
                    for v, _ in non_empty:
                        if isinstance(v, (int, float)):
                            numeric_values.append(float(v))
                        else:
                            import re
                            num_match = re.search(r'[\d,]+(?:\.\d+)?', str(v))
                            if num_match:
                                numeric_values.append(float(num_match.group().replace(',', '')))
                                
                    if numeric_values:
                        # Nutze Median für Robustheit gegen Ausreißer
                        median_value = statistics.median(numeric_values)
                        
                        # Finde Original-Wert der am nächsten am Median ist
                        closest_value = min(non_empty, key=lambda x: abs(self._extract_numeric(x[0]) - median_value))[0]
                        consensus[field] = closest_value
                        
                        # Konfidenz basiert auf Varianz
                        if len(numeric_values) > 1:
                            cv = statistics.stdev(numeric_values) / abs(statistics.mean(numeric_values))
                            confidence_scores[field] = max(0, 1 - cv)
                        else:
                            confidence_scores[field] = 1.0
                    else:
                        # Fallback auf Textvergleich
                        consensus[field] = non_empty[0][0]
                        confidence_scores[field] = 1.0 / len(set([v for v, _ in non_empty]))
                        
                except Exception as e:
                    logger.error(f"Fehler bei Konsens für {field}: {e}")
                    consensus[field] = non_empty[0][0]
                    confidence_scores[field] = 0.5
                    
            # Für andere Felder: Wähle Wert mit besten Quellen
            else:
                # Priorisiere nach Anzahl gefüllter Felder im Ergebnis
                best_result = max(non_empty, key=lambda x: len([f for f in x[1].values() if f]))
                consensus[field] = best_result[0]
                
                # Konfidenz basiert auf Übereinstimmung
                unique_values = set([v for v, _ in non_empty])
                confidence_scores[field] = 1.0 / len(unique_values)
                
        return {
            'consensus_data': consensus,
            'confidence_scores': confidence_scores,
            'average_confidence': statistics.mean(confidence_scores.values()) if confidence_scores else 0
        }
    
    def _extract_numeric(self, value: Any) -> float:
        """Extrahiert numerischen Wert aus verschiedenen Formaten"""
        if isinstance(value, (int, float)):
            return float(value)
            
        import re
        num_match = re.search(r'[\d,]+(?:\.\d+)?', str(value))
        if num_match:
            return float(num_match.group().replace(',', ''))
            
        return 0.0