"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Scoring-System für Datenaggregation
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics

from src.agents.base_agent import SearchResult
from .logger import get_logger


class ScoringEngine:
    """Engine für Bewertung und Aggregation von Suchergebnissen"""
    
    def __init__(self):
        self.logger = get_logger("scoring_engine")
        
        # NEUE Gewichtungen für Gesamtscore - Konsistenz und Qualität priorisiert
        self.weights = {
            'consistency': 0.35,    # Konsistenz zwischen Quellen
            'quality': 0.30,        # Quellenqualität  
            'completeness': 0.15,    # Vollständigkeit
            'actuality': 0.20        # Aktualität (wichtiger für neueste Daten)
        }
        
        # Quellenqualität-Scores
        self.source_quality_scores = {
            # Regierungsquellen
            'government': 100,
            'gestim': 100,
            'nrcan': 100,
            'mern': 100,
            'ontario.ca': 100,
            
            # Unternehmensberichte
            'company_report': 90,
            'annual_report': 90,
            'sedar': 90,
            
            # Branchenpublikationen
            'mining.com': 70,
            'mining-technology': 70,
            'infomine': 70,
            
            # Nachrichten
            'reuters': 60,
            'bloomberg': 60,
            'local_news': 50,
            
            # NGOs
            'miningwatch': 40,
            'environmental': 40,
            
            # Sonstige
            'wikipedia': 30,
            'unknown': 20
        }
    
    def calculate_total_score(self, result: SearchResult, 
                            all_results: List[SearchResult]) -> float:
        """Berechnet Gesamtscore für ein Ergebnis"""
        scores = {
            'actuality': self._calculate_actuality_score(result),
            'quality': self._calculate_quality_score(result),
            'completeness': self._calculate_completeness_score(result, all_results),
            'consistency': self._calculate_consistency_score(result, all_results)
        }
        
        # Gewichteter Durchschnitt
        total_score = sum(
            scores[key] * self.weights[key] 
            for key in self.weights
        )
        
        return round(total_score, 2)
    
    def _calculate_actuality_score(self, result: SearchResult) -> float:
        """Berechnet Aktualitäts-Score (0-100) - angepasst für Mining-Daten"""
        if not result.source_date:
            return 50  # Mittlerer Score wenn kein Datum
        
        current_year = datetime.now().year
        age = current_year - result.source_date
        
        # Differenzierte Bewertung nach Feldtyp
        if result.field_name in ['koordinaten', 'betreiber', 'rohstofftyp']:
            # Diese Felder ändern sich selten
            if age <= 10:
                return 100
            elif age <= 20:
                return 80
            else:
                return 60
                
        elif result.field_name in ['aktivitaetsstatus', 'sanierungskosten']:
            # Diese Felder benötigen aktuelle Daten
            if age == 0:
                return 100
            elif age <= 2:
                return 80
            elif age <= 5:
                return 60
            else:
                return 30
                
        else:
            # Standard-Bewertung
            if age <= 5:
                return 90
            elif age <= 10:
                return 70
            else:
                return 40
    
    def _calculate_quality_score(self, result: SearchResult) -> float:
        """Berechnet Quellenqualitäts-Score (0-100)"""
        source_lower = result.source.lower()
        
        # Prüfe bekannte Quellen
        for key, score in self.source_quality_scores.items():
            if key in source_lower:
                return score
        
        # Agent-basierte Scores
        if result.agent_name == 'claude':
            return 85
        elif result.agent_name == 'gpt4':
            return 85
        elif result.agent_name == 'perplexity':
            return 80
        elif result.agent_name == 'scraper':
            return 70
        
        return self.source_quality_scores['unknown']
    
    def _calculate_completeness_score(self, result: SearchResult, 
                                    all_results: List[SearchResult]) -> float:
        """Berechnet Vollständigkeits-Score für Feld"""
        # Zähle wie viele Agenten dieses Feld gefunden haben
        field_results = [
            r for r in all_results 
            if r.field_name == result.field_name
        ]
        
        agents_found = len(set(r.agent_name for r in field_results))
        total_agents = len(set(r.agent_name for r in all_results))
        
        if total_agents == 0:
            return 0
        
        completeness = (agents_found / total_agents) * 100
        return round(completeness, 2)
    
    def _calculate_consistency_score(self, result: SearchResult,
                                   all_results: List[SearchResult]) -> float:
        """Berechnet erweiterten Konsistenz-Score mit anderen Ergebnissen"""
        # Finde alle Ergebnisse für gleiches Feld
        field_results = [
            r for r in all_results 
            if r.field_name == result.field_name and r != result
        ]
        
        if not field_results:
            # Einzelnes Ergebnis - prüfe Konfidenz
            if hasattr(result, 'confidence_score'):
                return min(100, result.confidence_score * 120)  # Boost für hohe Konfidenz
            return 70  # Mittlerer Score für Einzelergebnis
        
        # Zusätzlicher Boost für Werte, die mehrfach gefunden wurden
        identical_count = sum(1 for r in field_results if str(r.value).lower() == str(result.value).lower())
        if identical_count > 0:
            # Je mehr Agenten denselben Wert finden, desto höher die Konsistenz
            consistency_boost = min(20, identical_count * 5)  # Max 20 Punkte Bonus
        else:
            consistency_boost = 0
        
        # Vergleiche Werte
        if result.field_name in ['betreiber', 'rohstofftyp', 'minentyp']:
            # Kategorische Felder - Fuzzy Matching
            from difflib import SequenceMatcher
            
            similarities = []
            for r in field_results:
                similarity = SequenceMatcher(None, 
                    str(result.value).lower(), 
                    str(r.value).lower()
                ).ratio()
                similarities.append(similarity)
            
            avg_similarity = statistics.mean(similarities)
            consistency = avg_similarity * 100
            
        elif result.field_name == 'koordinaten':
            # Spezielle Behandlung für Koordinaten
            try:
                # Parse result coordinates
                import re
                coords_match = re.findall(r'[-]?\d+\.?\d*', str(result.value))
                if len(coords_match) >= 2:
                    result_lat, result_lon = float(coords_match[0]), float(coords_match[1])
                    
                    distances = []
                    for r in field_results:
                        other_match = re.findall(r'[-]?\d+\.?\d*', str(r.value))
                        if len(other_match) >= 2:
                            other_lat, other_lon = float(other_match[0]), float(other_match[1])
                            # Einfache Distanzberechnung
                            distance = ((result_lat - other_lat)**2 + (result_lon - other_lon)**2)**0.5
                            distances.append(distance)
                    
                    if distances:
                        avg_distance = statistics.mean(distances)
                        # Score basierend auf Distanz (0.01 Grad ≈ 1km)
                        if avg_distance < 0.01:
                            consistency = 100
                        elif avg_distance < 0.1:
                            consistency = 80
                        elif avg_distance < 1:
                            consistency = 60
                        else:
                            consistency = 40
                    else:
                        consistency = 70
                else:
                    consistency = 50
            except:
                consistency = 50
                
        elif result.field_name in ['sanierungskosten', 'umweltkosten', 'jahresproduktion']:
            # Numerische Felder mit Toleranz
            try:
                # Extrahiere numerischen Wert
                result_val = self._extract_numeric_value(str(result.value))
                other_vals = []
                
                for r in field_results:
                    val = self._extract_numeric_value(str(r.value))
                    if val is not None:
                        other_vals.append(val)
                
                if other_vals and result_val is not None:
                    # Berechne relative Abweichung mit Toleranz
                    median_val = statistics.median(other_vals)
                    if median_val != 0:
                        deviation = abs(result_val - median_val) / median_val
                        # Tolerantere Bewertung
                        if deviation <= 0.1:  # 10% Abweichung
                            consistency = 100
                        elif deviation <= 0.25:  # 25% Abweichung
                            consistency = 80
                        elif deviation <= 0.5:  # 50% Abweichung
                            consistency = 60
                        else:
                            consistency = max(30, 100 - deviation * 50)
                    else:
                        consistency = 100 if result_val == 0 else 50
                else:
                    consistency = 70
                    
            except:
                consistency = 50
        else:
            # Standard-Konsistenz
            consistency = 75
        
        # Füge Boost für mehrfach gefundene Werte hinzu
        consistency = min(100, consistency + consistency_boost)
        
        return round(consistency, 2)
    
    def _extract_numeric_value(self, value_str: str) -> Optional[float]:
        """Extrahiert numerischen Wert aus String"""
        import re
        
        # Entferne Währungssymbole und Text
        cleaned = re.sub(r'[^\d,.-]', '', value_str)
        cleaned = cleaned.replace(',', '')
        
        try:
            value = float(cleaned)
            
            # Prüfe auf Millionen/Milliarden Notation
            if 'million' in value_str.lower() or ' m' in value_str.lower():
                value *= 1_000_000
            elif 'billion' in value_str.lower() or ' b' in value_str.lower():
                value *= 1_000_000_000
                
            return value
        except:
            return None
    
    def aggregate_results(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Aggregiert alle Ergebnisse zu finalem Datensatz mit Mehrfachwerten"""
        if not results:
            return {}
        
        # Gruppiere nach Feldname
        field_groups = defaultdict(list)
        for result in results:
            score = self.calculate_total_score(result, results)
            field_groups[result.field_name].append((result, score))
        
        # Aggregiere mit Unterstützung für mehrere Werte
        aggregated = {}
        alternatives: Dict[str, List[Dict[str, Any]]] = {}  # Sammle alternative Werte für jedes Feld
        
        for field_name, scored_results in field_groups.items():
            # Sortiere nach Score
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            # Gruppiere ähnliche Werte
            value_groups = self._group_similar_values(scored_results)
            
            if len(value_groups) == 1:
                # Nur ein eindeutiger Wert
                best_result, best_score = scored_results[0]
                aggregated[field_name] = {
                    'value': best_result.value,
                    'source': best_result.source,
                    'source_url': best_result.source_url,
                    'source_date': best_result.source_date,
                    'confidence': self._get_confidence_indicator(best_score),
                    'score': best_score,
                    'agent': best_result.agent_name,
                    'all_values': None  # Keine alternativen Werte
                }
                alternatives[field_name] = None  # Keine Alternativen
            else:
                # Mehrere unterschiedliche Werte gefunden
                best_group = value_groups[0]
                best_result = best_group['results'][0]
                
                # Hauptwert ist der mit dem höchsten Score
                aggregated[field_name] = {
                    'value': best_result.value,
                    'source': best_result.source,
                    'source_url': best_result.source_url,
                    'source_date': best_result.source_date,
                    'confidence': self._get_confidence_indicator(best_group['avg_score']),
                    'score': best_group['avg_score'],
                    'agent': best_result.agent_name,
                    'all_values': self._format_all_values(value_groups)
                }
                
                # Sammle alle alternativen Werte
                alternatives[field_name] = self._format_all_values(value_groups)
        
        # Berechne Gesamt-Metriken
        all_scores = [score for _, scored_results in field_groups.items() 
                     for _, score in scored_results]
        
        metadata = {
            'total_results': len(results),
            'fields_found': len(aggregated),
            'average_score': round(statistics.mean(all_scores), 2) if all_scores else 0,
            'highest_score': round(max(all_scores), 2) if all_scores else 0,
            'lowest_score': round(min(all_scores), 2) if all_scores else 0,
            'agents_used': list(set(r.agent_name for r in results))
        }
        
        return {
            'data': aggregated,
            'alternatives': alternatives,
            'metadata': metadata
        }
    
    def _get_confidence_indicator(self, score: float) -> str:
        """Gibt Konfidenz-Indikator basierend auf Score zurück"""
        if score >= 80:
            return "🟢"  # Hoch
        elif score >= 50:
            return "🟡"  # Mittel
        else:
            return "🔴"  # Niedrig
    
    def calculate_data_quality_metrics(self, aggregated_data: Dict[str, Any]) -> Dict[str, float]:
        """Berechnet Qualitätsmetriken für aggregierte Daten"""
        if not aggregated_data or 'data' not in aggregated_data:
            return {'quality_score': 0, 'completeness_score': 0}
        
        data = aggregated_data['data']
        
        # Pflichtfelder
        required_fields = [
            'betreiber', 'koordinaten', 'aktivitaetsstatus',
            'sanierungskosten', 'rohstofftyp'
        ]
        
        # Vollständigkeit
        fields_found = sum(1 for field in required_fields if field in data)
        completeness_score = (fields_found / len(required_fields)) * 100
        
        # Qualität (Durchschnitt der Feld-Scores)
        field_scores = [field_data['score'] for field_data in data.values()]
        quality_score = statistics.mean(field_scores) if field_scores else 0
        
        return {
            'quality_score': round(quality_score, 2),
            'completeness_score': round(completeness_score, 2)
        }
    
    def _group_similar_values(self, scored_results: List[Tuple[SearchResult, float]]) -> List[Dict[str, Any]]:
        """Gruppiert ähnliche Werte zusammen"""
        from difflib import SequenceMatcher
        
        groups = []
        used = set()
        
        for i, (result, score) in enumerate(scored_results):
            if i in used:
                continue
                
            group = {
                'results': [(result, score)],
                'values': [result.value],
                'scores': [score]
            }
            used.add(i)
            
            # Finde ähnliche Werte
            for j, (other_result, other_score) in enumerate(scored_results[i+1:], i+1):
                if j in used:
                    continue
                    
                # Prüfe Ähnlichkeit
                similarity = self._calculate_value_similarity(result.value, other_result.value, result.field_name)
                
                if similarity > 0.85:  # 85% Ähnlichkeit
                    group['results'].append((other_result, other_score))
                    group['values'].append(other_result.value)
                    group['scores'].append(other_score)
                    used.add(j)
            
            # Berechne Durchschnittsscore für Gruppe
            group['avg_score'] = statistics.mean(group['scores'])
            
            # Sortiere innerhalb der Gruppe nach Datum (neueste zuerst)
            group['results'].sort(key=lambda x: (x[0].source_date or 0, x[1]), reverse=True)
            
            groups.append(group)
        
        # Sortiere Gruppen nach Durchschnittsscore
        groups.sort(key=lambda g: g['avg_score'], reverse=True)
        
        return groups
    
    def _calculate_value_similarity(self, value1: Any, value2: Any, field_name: str) -> float:
        """Berechnet Ähnlichkeit zwischen zwei Werten"""
        
        # Konvertiere zu Strings
        str1 = str(value1).lower().strip()
        str2 = str(value2).lower().strip()
        
        # Spezielle Behandlung für numerische Felder
        if field_name in ['koordinaten', 'sanierungskosten', 'jahresproduktion']:
            try:
                # Extrahiere numerische Werte
                num1 = self._extract_numeric_value(str1)
                num2 = self._extract_numeric_value(str2)
                
                if num1 is not None and num2 is not None:
                    # Berechne relative Differenz
                    if num1 == 0 and num2 == 0:
                        return 1.0
                    max_val = max(abs(num1), abs(num2))
                    diff = abs(num1 - num2) / max_val
                    return max(0, 1 - diff)
            except:
                pass
        
        # Standard String-Ähnlichkeit
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _format_all_values(self, value_groups: List[Dict[str, Any]]) -> str:
        """Formatiert alle gefundenen Werte mit +++ als Trenner und Häufigkeitsangabe"""
        all_values = []
        
        for group in value_groups:
            # Nimm den repräsentativsten Wert der Gruppe
            best_result = group['results'][0][0]
            count = len(group['results'])
            
            if count > 1:
                # Mehrere Agenten haben diesen Wert gefunden
                agents = [r[0].agent_name for r in group['results'][:3]]  # Max 3 Agenten anzeigen
                agents_str = ", ".join(agents)
                if len(group['results']) > 3:
                    agents_str += f" +{len(group['results'])-3}"
                value_str = f"{best_result.value} ({count}x: {agents_str})"
            else:
                # Nur ein Agent hat diesen Wert gefunden
                value_str = f"{best_result.value} ({best_result.agent_name})"
            
            all_values.append(value_str)
        
        # Verbinde mit +++ als Trenner
        return " +++ ".join(all_values)