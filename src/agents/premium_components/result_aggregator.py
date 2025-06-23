"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Aggregation und Konsolidierung von Research-Ergebnissen
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime
import logging

from ..base_agent import MineQuery, SearchResult


class ResultAggregator:
    """Aggregiert und konsolidiert Research-Ergebnisse"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
        # Konfigurations-Parameter
        self.confidence_threshold = 0.6
        self.consensus_threshold = 0.7
        self.max_values_per_field = 5
    
    async def aggregate_results(self,
                              all_results: List[Any],
                              phase_results: Dict[str, Dict[str, Any]],
                              query: MineQuery,
                              research_id: str) -> Dict[str, Any]:
        """
        Aggregiert alle Ergebnisse zu einem finalen Research-Result
        
        Args:
            all_results: Alle gesammelten Ergebnisse
            phase_results: Ergebnisse nach Phase gruppiert
            query: Original-Query
            research_id: Eindeutige Research-ID
            
        Returns:
            Aggregiertes Ergebnis mit mine_data, sources, confidence_scores
        """
        self.logger.info(f"Aggregiere {len(all_results)} Ergebnisse...")
        
        # 1. Gruppiere Ergebnisse nach Feld
        field_groups = self._group_by_field(all_results)
        
        # 2. Dedupliziere und bewerte
        consolidated_fields = {}
        confidence_scores = {}
        sources = {}
        
        for field_name, field_results in field_groups.items():
            # Dedupliziere Werte
            unique_values = self._deduplicate_values(field_results)
            
            # Berechne Konsens und Konfidenz
            best_values = self._select_best_values(unique_values, field_results)
            
            if best_values:
                consolidated_fields[field_name] = best_values
                
                # Konfidenz-Score für Feld
                confidence_scores[field_name] = self._calculate_field_confidence(
                    field_results,
                    best_values
                )
                
                # Quellen sammeln
                sources[field_name] = self._collect_sources(field_results, best_values)
        
        # 3. Spezielle Aggregationen
        special_aggregations = self._perform_special_aggregations(
            consolidated_fields,
            phase_results
        )
        consolidated_fields.update(special_aggregations)
        
        # 4. Validierung und Bereinigung
        validated_fields = self._validate_fields(consolidated_fields, query)
        
        # 5. Finales Ergebnis erstellen
        result = {
            'mine_data': validated_fields,
            'sources': sources,
            'confidence_scores': confidence_scores,
            'aggregation_stats': {
                'total_results': len(all_results),
                'unique_fields': len(validated_fields),
                'average_confidence': sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0,
                'phases_used': list(phase_results.keys())
            }
        }
        
        self.logger.info(f"Aggregation abgeschlossen: {len(validated_fields)} Felder konsolidiert")
        
        return result
    
    def _group_by_field(self, results: List[Any]) -> Dict[str, List[Any]]:
        """Gruppiert Ergebnisse nach Feld"""
        groups = defaultdict(list)
        
        for result in results:
            if hasattr(result, 'field_name'):
                groups[result.field_name].append(result)
            elif isinstance(result, dict) and 'field_name' in result:
                groups[result['field_name']].append(result)
        
        return dict(groups)
    
    def _deduplicate_values(self, field_results: List[Any]) -> Dict[str, List[Any]]:
        """Dedupliziert Werte für ein Feld"""
        value_map = defaultdict(list)
        
        for result in field_results:
            # Wert extrahieren
            if hasattr(result, 'value'):
                value = str(result.value).strip()
            elif isinstance(result, dict) and 'value' in result:
                value = str(result['value']).strip()
            else:
                continue
            
            # Normalisieren für Vergleich
            normalized = self._normalize_value(value)
            value_map[normalized].append(result)
        
        return dict(value_map)
    
    def _normalize_value(self, value: str) -> str:
        """Normalisiert Wert für Deduplizierung"""
        # Basis-Normalisierung
        normalized = value.lower().strip()
        
        # Zahlen normalisieren (1,000 -> 1000)
        normalized = normalized.replace(',', '')
        
        # Einheiten vereinheitlichen
        unit_map = {
            'meters': 'm',
            'metres': 'm',
            'feet': 'ft',
            'kilometers': 'km',
            'kilometres': 'km',
            'million': 'M',
            'billion': 'B'
        }
        
        for long_form, short_form in unit_map.items():
            normalized = normalized.replace(long_form, short_form)
        
        return normalized
    
    def _select_best_values(self, 
                          unique_values: Dict[str, List[Any]],
                          all_results: List[Any]) -> Any:
        """Wählt beste Werte basierend auf Konsens und Konfidenz"""
        if not unique_values:
            return None
        
        # Score für jeden unique value
        value_scores = {}
        
        for normalized_value, results in unique_values.items():
            # Anzahl der Quellen die diesen Wert haben
            source_count = len(set(
                r.agent_name if hasattr(r, 'agent_name') 
                else r.get('agent_name', 'unknown')
                for r in results
            ))
            
            # Durchschnittliche Konfidenz
            confidences = [
                r.confidence_score if hasattr(r, 'confidence_score')
                else r.get('confidence_score', 0.5)
                for r in results
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Gesamtscore
            score = (source_count * 0.6) + (avg_confidence * 0.4)
            value_scores[normalized_value] = {
                'score': score,
                'count': len(results),
                'sources': source_count,
                'confidence': avg_confidence,
                'original': results[0].value if hasattr(results[0], 'value') else results[0].get('value')
            }
        
        # Sortiere nach Score
        sorted_values = sorted(
            value_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        # Wähle beste Werte
        if len(sorted_values) == 1:
            # Nur ein Wert - nehmen wenn Konfidenz ausreicht
            if sorted_values[0][1]['confidence'] >= self.confidence_threshold:
                return sorted_values[0][1]['original']
        else:
            # Mehrere Werte - nehme Top-Werte mit gutem Score
            top_values = []
            for _, value_info in sorted_values[:self.max_values_per_field]:
                if value_info['score'] >= self.consensus_threshold:
                    top_values.append(value_info['original'])
            
            if top_values:
                return top_values[0] if len(top_values) == 1 else top_values
        
        return None
    
    def _calculate_field_confidence(self,
                                  field_results: List[Any],
                                  selected_values: Any) -> float:
        """Berechnet Konfidenz für ein Feld"""
        if not field_results:
            return 0.0
        
        # Faktoren für Konfidenz
        factors = []
        
        # 1. Anzahl der Quellen
        unique_sources = set(
            r.agent_name if hasattr(r, 'agent_name')
            else r.get('agent_name', 'unknown')
            for r in field_results
        )
        source_factor = min(1.0, len(unique_sources) / 5)  # Max bei 5 Quellen
        factors.append(source_factor)
        
        # 2. Durchschnittliche Agent-Konfidenz
        confidences = [
            r.confidence_score if hasattr(r, 'confidence_score')
            else r.get('confidence_score', 0.5)
            for r in field_results
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        factors.append(avg_confidence)
        
        # 3. Konsistenz der Werte
        unique_values = len(self._deduplicate_values(field_results))
        consistency_factor = 1.0 if unique_values == 1 else 0.5 + (0.5 / unique_values)
        factors.append(consistency_factor)
        
        # Gewichteter Durchschnitt
        weights = [0.4, 0.4, 0.2]  # Source-Count wichtiger als Konsistenz
        weighted_confidence = sum(f * w for f, w in zip(factors, weights))
        
        return min(1.0, weighted_confidence)
    
    def _collect_sources(self,
                        field_results: List[Any],
                        selected_values: Any) -> List[Dict[str, Any]]:
        """Sammelt Quellen-Informationen"""
        sources = []
        seen_urls = set()
        
        # Konvertiere selected_values zu Liste
        if not isinstance(selected_values, list):
            selected_values = [selected_values]
        
        for result in field_results:
            # Prüfe ob dieser Result zu den selected values gehört
            result_value = str(result.value if hasattr(result, 'value') else result.get('value', ''))
            
            if any(str(sv) == result_value for sv in selected_values):
                source_info = {
                    'agent': result.agent_name if hasattr(result, 'agent_name') else result.get('agent_name'),
                    'confidence': result.confidence_score if hasattr(result, 'confidence_score') else result.get('confidence_score', 0.5),
                    'timestamp': result.timestamp.isoformat() if hasattr(result, 'timestamp') and result.timestamp else datetime.now().isoformat()
                }
                
                # URL wenn vorhanden
                if hasattr(result, 'source_url') and result.source_url:
                    source_info['url'] = result.source_url
                elif isinstance(result, dict) and 'source_url' in result:
                    source_info['url'] = result['source_url']
                
                # Deduplizierung nach URL
                if 'url' in source_info:
                    if source_info['url'] not in seen_urls:
                        seen_urls.add(source_info['url'])
                        sources.append(source_info)
                else:
                    sources.append(source_info)
        
        return sources[:10]  # Limitiere Quellen
    
    def _perform_special_aggregations(self,
                                    fields: Dict[str, Any],
                                    phase_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Führt spezielle Aggregationen durch"""
        special_fields = {}
        
        # 1. Koordinaten aggregieren
        if 'latitude' in fields and 'longitude' in fields:
            special_fields['coordinates'] = {
                'lat': fields['latitude'],
                'lon': fields['longitude']
            }
        
        # 2. Produktionsdaten aggregieren
        production_fields = [k for k in fields.keys() if 'production' in k.lower()]
        if production_fields:
            production_data = {}
            for field in production_fields:
                # Extrahiere Jahr wenn vorhanden
                import re
                year_match = re.search(r'(\d{4})', field)
                if year_match:
                    year = year_match.group(1)
                    production_data[year] = fields[field]
                else:
                    production_data['current'] = fields[field]
            
            if production_data:
                special_fields['production_history'] = production_data
        
        # 3. Analyse-Insights aus Analysis-Phase
        if 'Analysis' in phase_results:
            analysis_results = phase_results['Analysis'].get('results', [])
            insights = []
            
            for result in analysis_results:
                if hasattr(result, 'field_name') and 'insight' in result.field_name.lower():
                    insights.append(result.value if hasattr(result, 'value') else result.get('value'))
            
            if insights:
                special_fields['analysis_insights'] = insights[:3]  # Top 3 Insights
        
        return special_fields
    
    def _validate_fields(self, fields: Dict[str, Any], query: MineQuery) -> Dict[str, Any]:
        """Validiert und bereinigt Felder"""
        validated = {}
        
        for field_name, value in fields.items():
            # Skip leere Werte
            if not value or value == 'N/A':
                continue
            
            # Validiere numerische Felder
            if any(term in field_name.lower() for term in ['production', 'depth', 'employees', 'cost']):
                validated_value = self._validate_numeric(value)
                if validated_value is not None:
                    validated[field_name] = validated_value
            else:
                validated[field_name] = value
        
        # Stelle sicher dass required_fields vorhanden sind
        for required in query.required_fields:
            if required not in validated:
                # Suche ähnliche Felder
                for field_name in fields.keys():
                    if required.lower() in field_name.lower():
                        validated[required] = fields[field_name]
                        break
        
        return validated
    
    def _validate_numeric(self, value: Any) -> Optional[Any]:
        """Validiert numerische Werte"""
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            # Versuche zu parsen
            import re
            # Entferne nicht-numerische Zeichen (außer Punkt und Minus)
            cleaned = re.sub(r'[^\d.-]', '', value)
            try:
                return float(cleaned)
            except:
                return value  # Behalte Original wenn Parsing fehlschlägt
        
        if isinstance(value, list):
            # Bei Listen nehme ersten validierten Wert
            for v in value:
                validated = self._validate_numeric(v)
                if validated is not None:
                    return validated
        
        return None