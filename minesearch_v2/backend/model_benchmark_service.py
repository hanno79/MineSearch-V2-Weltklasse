"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: Service für umfassende Modell-Benchmarks und Konsistenz-Analyse
"""

import asyncio
import logging
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import (
    DatabaseManager, ModelStatistics, FieldConsistency, 
    ModelSummary, get_db
)
from search_service_multi import MultiProviderSearchService
from config import CSV_COLUMNS, Config
from extraction_validators import is_placeholder_value

logger = logging.getLogger(__name__)


class ModelBenchmarkService:
    """Service für Modell-Benchmarks und Konsistenz-Analyse"""
    
    # Kritische Felder für Mining-Daten
    CRITICAL_FIELDS = [
        'Eigentümer', 
        'Betreiber', 
        'Restaurationskosten',
        'x-Koordinate',
        'y-Koordinate',
        'Aktivitätsstatus'
    ]
    
    # Kosten-Schätzungen pro 1000 Tokens
    MODEL_COSTS = {
        'perplexity:sonar': 0.05,
        'perplexity:sonar-pro': 0.50,
        'perplexity:sonar-deep-research': 1.00,
        'perplexity:sonar-reasoning': 0.75,
        'openrouter:deepseek-free': 0.00,
        'openrouter:deepseek-chat': 0.14,
        'openrouter:deepseek-reasoner': 0.50,
        'tavily:search': 0.01,
        'exa:neural-search': 0.01,
        'openai:gpt-4.1': 1.00,
        'openai:o3-deep-research': 2.00,
        'anthropic:claude-sonnet-4': 3.00,
        'gemini:gemini-2.5-flash': 0.20,
        'grok:grok-3': 1.00
    }
    
    def __init__(self):
        self.search_service = MultiProviderSearchService()
        self.db_manager = DatabaseManager()
        
    async def benchmark_model(
        self, 
        model_id: str, 
        mine_data: Dict[str, str], 
        runs: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Führt Benchmark für ein Modell durch
        
        Args:
            model_id: ID des zu testenden Modells
            mine_data: Dict mit mine_name, country, region, commodity
            runs: Anzahl der Durchläufe (default: 5)
            session_id: Optional Session-ID für Gruppierung
            
        Returns:
            Dict mit Benchmark-Ergebnissen
        """
        logger.info(f"[BENCHMARK] Starte Benchmark für {model_id} - {mine_data['name']} ({runs} Durchläufe)")
        
        results = []
        
        for run_number in range(1, runs + 1):
            logger.info(f"[BENCHMARK] Durchlauf {run_number}/{runs}")
            
            # Zeitmessung starten
            start_time = time.time()
            
            try:
                # Führe Suche durch
                result = await self.search_service.search_with_model(
                    model_id=model_id,
                    mine_name=mine_data['name'],
                    country=mine_data.get('country', ''),
                    region=mine_data.get('region', ''),
                    commodity=mine_data.get('commodity', '')
                )
                
                # Zeitmessung beenden
                response_time_ms = (time.time() - start_time) * 1000
                
                if result.get('success') and result.get('data'):
                    # Erfolgreiche Suche
                    data = result['data']
                    structured_data = data.get('structured_data', {})
                    sources = data.get('sources', [])
                    
                    # Zähle gefundene Felder (ohne Platzhalter)
                    fields_found = 0
                    for field, value in structured_data.items():
                        if value and not is_placeholder_value(str(value), field):
                            fields_found += 1
                    
                    # Speichere in Datenbank
                    await self._save_benchmark_result(
                        model_id=model_id,
                        mine_data=mine_data,
                        run_number=run_number,
                        success=True,
                        response_time_ms=response_time_ms,
                        fields_found=fields_found,
                        sources_count=len(sources),
                        raw_result=result,
                        structured_data=structured_data,
                        error_message=None
                    )
                    
                    results.append({
                        'run_number': run_number,
                        'success': True,
                        'response_time_ms': response_time_ms,
                        'fields_found': fields_found,
                        'sources_count': len(sources),
                        'structured_data': structured_data
                    })
                    
                else:
                    # Fehlgeschlagene Suche
                    error_message = result.get('error', 'Unbekannter Fehler')
                    
                    await self._save_benchmark_result(
                        model_id=model_id,
                        mine_data=mine_data,
                        run_number=run_number,
                        success=False,
                        response_time_ms=response_time_ms,
                        fields_found=0,
                        sources_count=0,
                        raw_result=result,
                        structured_data={},
                        error_message=error_message
                    )
                    
                    results.append({
                        'run_number': run_number,
                        'success': False,
                        'response_time_ms': response_time_ms,
                        'error': error_message
                    })
                    
            except Exception as e:
                logger.error(f"[BENCHMARK] Fehler bei Durchlauf {run_number}: {str(e)}")
                
                response_time_ms = (time.time() - start_time) * 1000
                
                await self._save_benchmark_result(
                    model_id=model_id,
                    mine_data=mine_data,
                    run_number=run_number,
                    success=False,
                    response_time_ms=response_time_ms,
                    fields_found=0,
                    sources_count=0,
                    raw_result={},
                    structured_data={},
                    error_message=str(e)
                )
                
                results.append({
                    'run_number': run_number,
                    'success': False,
                    'response_time_ms': response_time_ms,
                    'error': str(e)
                })
            
            # Rate-Limiting zwischen Durchläufen
            if run_number < runs:
                await asyncio.sleep(2.0)
        
        # Berechne Konsistenz
        consistency_analysis = await self.calculate_field_consistency(
            model_id, mine_data['name'], results
        )
        
        # Aktualisiere Modell-Zusammenfassung
        await self._update_model_summary(model_id, results)
        
        # Zusammenfassung erstellen
        successful_runs = [r for r in results if r.get('success')]
        
        summary = {
            'model_id': model_id,
            'mine_name': mine_data['name'],
            'total_runs': runs,
            'successful_runs': len(successful_runs),
            'success_rate': len(successful_runs) / runs,
            'avg_response_time_ms': statistics.mean([r['response_time_ms'] for r in results]) if results else 0,
            'avg_fields_found': statistics.mean([r.get('fields_found', 0) for r in successful_runs]) if successful_runs else 0,
            'avg_sources_count': statistics.mean([r.get('sources_count', 0) for r in successful_runs]) if successful_runs else 0,
            'consistency_analysis': consistency_analysis,
            'detailed_results': results
        }
        
        logger.info(f"[BENCHMARK] Abgeschlossen für {model_id}: {summary['success_rate']:.0%} Erfolg, Ø {summary['avg_fields_found']:.1f} Felder")
        
        return summary
    
    async def calculate_field_consistency(
        self, 
        model_id: str, 
        mine_name: str, 
        results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Berechnet Feld-Konsistenz über mehrere Durchläufe
        
        Args:
            model_id: ID des Modells
            mine_name: Name der Mine
            results: Liste der Benchmark-Ergebnisse
            
        Returns:
            Dict mit Konsistenz-Analyse
        """
        # Sammle alle Felder und ihre Werte
        field_values = defaultdict(list)
        successful_results = [r for r in results if r.get('success') and r.get('structured_data')]
        
        if not successful_results:
            return {
                'overall_consistency': 0.0,
                'field_consistency': {},
                'critical_fields_ok': False
            }
        
        # Sammle Werte für jedes Feld
        for result in successful_results:
            structured_data = result.get('structured_data', {})
            for field, value in structured_data.items():
                if value and not is_placeholder_value(str(value), field):
                    field_values[field].append(str(value))
        
        # Analysiere Konsistenz pro Feld
        field_consistency = {}
        
        for field_name, values in field_values.items():
            if not values:
                continue
            
            # Zähle Vorkommen jedes Werts
            value_counts = Counter(values)
            most_common_value, occurrence_count = value_counts.most_common(1)[0]
            
            # Berechne Konsistenz-Score
            consistency_score = occurrence_count / len(successful_results)
            is_consistent = consistency_score >= 0.8  # 80% Schwellenwert
            
            field_consistency[field_name] = {
                'consistency_score': consistency_score,
                'values_found': list(value_counts.keys()),
                'most_common_value': most_common_value,
                'occurrence_count': occurrence_count,
                'total_runs': len(successful_results),
                'is_consistent': is_consistent
            }
            
            # Speichere in Datenbank
            await self._save_field_consistency(
                model_id=model_id,
                mine_name=mine_name,
                field_name=field_name,
                consistency_score=consistency_score,
                values_found=list(value_counts.keys()),
                most_common_value=most_common_value,
                occurrence_count=occurrence_count,
                total_runs=len(successful_results),
                is_consistent=is_consistent
            )
        
        # Berechne Gesamt-Konsistenz
        if field_consistency:
            overall_consistency = statistics.mean([
                fc['consistency_score'] for fc in field_consistency.values()
            ])
        else:
            overall_consistency = 0.0
        
        # Prüfe kritische Felder
        critical_fields_found = sum(1 for field in self.CRITICAL_FIELDS if field in field_consistency)
        critical_fields_ok = critical_fields_found >= len(self.CRITICAL_FIELDS) / 2
        
        return {
            'overall_consistency': overall_consistency,
            'field_consistency': field_consistency,
            'critical_fields_found': critical_fields_found,
            'critical_fields_ok': critical_fields_ok,
            'total_fields_analyzed': len(field_consistency)
        }
    
    async def _save_benchmark_result(self, **kwargs):
        """Speichert Benchmark-Ergebnis in Datenbank"""
        with self.db_manager.get_session() as session:
            stat = ModelStatistics(
                model_id=kwargs['model_id'],
                mine_name=kwargs['mine_data']['name'],
                country=kwargs['mine_data'].get('country'),
                region=kwargs['mine_data'].get('region'),
                commodity=kwargs['mine_data'].get('commodity'),
                run_number=kwargs['run_number'],
                success=kwargs['success'],
                response_time_ms=kwargs['response_time_ms'],
                fields_found=kwargs['fields_found'],
                sources_count=kwargs['sources_count'],
                raw_result=kwargs.get('raw_result'),
                structured_data=kwargs['structured_data'],
                error_message=kwargs.get('error_message')
            )
            session.add(stat)
            session.commit()
    
    async def _save_field_consistency(self, **kwargs):
        """Speichert oder aktualisiert Feld-Konsistenz in Datenbank"""
        with self.db_manager.get_session() as session:
            # Prüfe ob bereits vorhanden
            existing = session.query(FieldConsistency).filter_by(
                model_id=kwargs['model_id'],
                mine_name=kwargs['mine_name'],
                field_name=kwargs['field_name']
            ).first()
            
            if existing:
                # Aktualisiere
                existing.consistency_score = kwargs['consistency_score']
                existing.values_found = kwargs['values_found']
                existing.most_common_value = kwargs['most_common_value']
                existing.occurrence_count = kwargs['occurrence_count']
                existing.total_runs = kwargs['total_runs']
                existing.is_consistent = kwargs['is_consistent']
                existing.last_updated = datetime.now()
            else:
                # Neu erstellen
                consistency = FieldConsistency(**kwargs)
                session.add(consistency)
            
            session.commit()
    
    async def _update_model_summary(self, model_id: str, results: List[Dict]):
        """Aktualisiert Modell-Zusammenfassung"""
        with self.db_manager.get_session() as session:
            # Hole oder erstelle Summary
            summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
            
            if not summary:
                summary = ModelSummary(
                    model_id=model_id,
                    total_tests=0,
                    total_mines_tested=0,
                    avg_response_time_ms=0.0,
                    avg_fields_found=0.0,
                    avg_sources_count=0.0,
                    success_rate=0.0,
                    overall_consistency=0.0,
                    total_estimated_cost=0.0,
                    estimated_cost_per_request=self.MODEL_COSTS.get(model_id, 0.1)
                )
                session.add(summary)
            
            # Berechne neue Statistiken
            successful_runs = [r for r in results if r.get('success')]
            
            if results:
                # Aktualisiere Zähler
                summary.total_tests = (summary.total_tests or 0) + len(results)
                summary.total_mines_tested = session.query(
                    func.count(func.distinct(ModelStatistics.mine_name))
                ).filter_by(model_id=model_id).scalar() or 0
                
                # Berechne neue Durchschnitte
                all_stats = session.query(ModelStatistics).filter_by(
                    model_id=model_id
                ).all()
                
                if all_stats:
                    summary.avg_response_time_ms = statistics.mean([
                        s.response_time_ms for s in all_stats if s.response_time_ms
                    ])
                    
                    successful_stats = [s for s in all_stats if s.success]
                    if successful_stats:
                        summary.avg_fields_found = statistics.mean([
                            s.fields_found for s in successful_stats
                        ])
                        summary.avg_sources_count = statistics.mean([
                            s.sources_count for s in successful_stats
                        ])
                    
                    summary.success_rate = len(successful_stats) / len(all_stats)
                
                # Berechne Gesamt-Konsistenz
                all_consistencies = session.query(FieldConsistency).filter_by(
                    model_id=model_id
                ).all()
                
                if all_consistencies:
                    summary.overall_consistency = statistics.mean([
                        c.consistency_score for c in all_consistencies
                    ])
                    
                    # Kritische Felder Konsistenz
                    critical_consistencies = {}
                    for field in self.CRITICAL_FIELDS:
                        field_consistency = next(
                            (c for c in all_consistencies if c.field_name == field), 
                            None
                        )
                        if field_consistency:
                            critical_consistencies[field] = field_consistency.consistency_score
                    
                    summary.critical_fields_consistency = critical_consistencies
                
                # Kosten-Schätzung
                cost_per_request = self.MODEL_COSTS.get(model_id, 0.1)
                summary.total_estimated_cost = summary.total_tests * cost_per_request * 10  # ~10k tokens
                
                # Timestamps
                if not summary.first_test_at:
                    summary.first_test_at = datetime.now()
                summary.last_test_at = datetime.now()
            
            session.commit()
    
    async def get_benchmark_summary(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Hole Benchmark-Zusammenfassung für ein Modell"""
        with self.db_manager.get_session() as session:
            summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
            
            if summary:
                return summary.to_dict()
            
            return None
    
    async def get_all_benchmarks(self) -> List[Dict[str, Any]]:
        """Hole alle Benchmark-Zusammenfassungen"""
        with self.db_manager.get_session() as session:
            summaries = session.query(ModelSummary).all()
            return [s.to_dict() for s in summaries]
    
    async def get_field_consistencies(
        self, 
        model_id: Optional[str] = None,
        mine_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Hole Feld-Konsistenz-Daten"""
        with self.db_manager.get_session() as session:
            query = session.query(FieldConsistency)
            
            if model_id:
                query = query.filter_by(model_id=model_id)
            if mine_name:
                query = query.filter_by(mine_name=mine_name)
            
            consistencies = query.all()
            return [c.to_dict() for c in consistencies]
    
    async def benchmark_multiple_models(
        self,
        model_ids: List[str],
        mine_data: Dict[str, str],
        runs: int = 5
    ) -> Dict[str, Any]:
        """
        Führt Benchmarks für mehrere Modelle durch
        
        Args:
            model_ids: Liste der zu testenden Modell-IDs
            mine_data: Dict mit mine_name, country, region, commodity
            runs: Anzahl der Durchläufe pro Modell
            
        Returns:
            Dict mit allen Benchmark-Ergebnissen
        """
        logger.info(f"[BENCHMARK] Starte Multi-Modell-Benchmark für {len(model_ids)} Modelle")
        
        results = {}
        
        for model_id in model_ids:
            try:
                result = await self.benchmark_model(model_id, mine_data, runs)
                results[model_id] = result
            except Exception as e:
                logger.error(f"[BENCHMARK] Fehler bei {model_id}: {str(e)}")
                results[model_id] = {
                    'error': str(e),
                    'success': False
                }
        
        return {
            'mine_data': mine_data,
            'total_models': len(model_ids),
            'runs_per_model': runs,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }