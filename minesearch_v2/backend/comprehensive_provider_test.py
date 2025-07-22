#!/usr/bin/env python3
"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Umfassender Provider-Test für alle verfügbaren Provider im MineSearch v2 System
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from providers.registry import provider_registry
from search_service_multi_enhanced import EnhancedMultiProviderSearchService
from model_benchmark_service import ModelBenchmarkService
from database import db_manager, ModelStatistics, FieldStatistics, Source
from config.base import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_provider_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_MINES = [
    {"name": "Éléonore", "country": "Canada", "region": "Quebec", "commodity": "Gold"},
    {"name": "Niobec", "country": "Canada", "region": "Quebec", "commodity": "Niobium"}, 
    {"name": "LaRonde", "country": "Canada", "region": "Quebec", "commodity": "Gold"}
]

RUNS_PER_MINE = 5
MAX_PARALLEL_TESTS = 5

class ComprehensiveProviderTester:
    """Umfassender Provider-Tester für MineSearch v2"""
    
    def __init__(self):
        self.enhanced_service = EnhancedMultiProviderSearchService()
        self.benchmark_service = ModelBenchmarkService()
        self.test_results = {}
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Initialisiere Test-Services"""
        logger.info("🔧 Initialisiere Provider-Registry...")
        provider_registry.initialize(config.PROVIDERS)
        
        logger.info("📊 Verfügbare Provider:")
        all_models = provider_registry.get_all_models()
        provider_names = set(mid.split(':')[0] for mid in all_models.keys())
        for provider_name in sorted(provider_names):
            provider_models = [mid for mid in all_models.keys() if mid.startswith(f"{provider_name}:")]
            logger.info(f"  - {provider_name}: {len(provider_models)} Modelle")
        
        logger.info(f"🎯 Gesamt: {len(all_models)} testbare Modelle")
        
    async def run_comprehensive_test(self):
        """Führe umfassende Tests für alle Provider durch"""
        logger.info("🚀 STARTE UMFASSENDEN PROVIDER-TEST")
        logger.info("=" * 80)
        logger.info(f"Test-Start: {self.start_time}")
        logger.info(f"Test-Minen: {[mine['name'] for mine in TEST_MINES]}")
        logger.info(f"Durchläufe pro Mine: {RUNS_PER_MINE}")
        logger.info(f"Max parallele Tests: {MAX_PARALLEL_TESTS}")
        logger.info("=" * 80)
        
        # Hole alle verfügbaren Modelle
        all_models = provider_registry.get_all_models()
        testable_models = []
        
        for model_id, model_config in all_models.items():
            provider_name = model_id.split(':')[0]
            provider = provider_registry.get_provider(provider_name)
            if provider and provider.validate_config():
                testable_models.append(model_id)
            else:
                logger.warning(f"⚠️ Provider {provider_name} nicht verfügbar - überspringe {model_id}")
        
        logger.info(f"🧪 Testbare Modelle: {len(testable_models)}")
        
        # Gruppiere Tests für Parallelisierung
        test_tasks = []
        for model_id in testable_models:
            for mine in TEST_MINES:
                for run in range(1, RUNS_PER_MINE + 1):
                    test_tasks.append({
                        'model_id': model_id,
                        'mine': mine,
                        'run_number': run
                    })
        
        total_tests = len(test_tasks)
        logger.info(f"📋 Gesamt-Tests: {total_tests}")
        logger.info(f"⏱️ Geschätzte Dauer: {total_tests * 45 / 60:.1f} Minuten")
        
        # Führe Tests in Batches durch
        semaphore = asyncio.Semaphore(MAX_PARALLEL_TESTS)
        completed_tests = 0
        failed_tests = 0
        
        async def run_single_test(task):
            nonlocal completed_tests, failed_tests
            async with semaphore:
                try:
                    result = await self._run_single_search(
                        task['model_id'], 
                        task['mine'], 
                        task['run_number']
                    )
                    completed_tests += 1
                    
                    if completed_tests % 50 == 0:  # Progress update every 50 tests
                        progress = (completed_tests / total_tests) * 100
                        logger.info(f"📊 Progress: {completed_tests}/{total_tests} ({progress:.1f}%)")
                    
                    return result
                except Exception as e:
                    failed_tests += 1
                    logger.error(f"❌ Test fehlgeschlagen: {task['model_id']} - {task['mine']['name']} Run {task['run_number']}: {e}")
                    return None
        
        # Starte alle Tests parallel
        logger.info("🏃 Starte parallele Test-Ausführung...")
        results = await asyncio.gather(*[run_single_test(task) for task in test_tasks], return_exceptions=True)
        
        # Sammle Ergebnisse
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        logger.info("=" * 80)
        logger.info("📊 TEST-ZUSAMMENFASSUNG")
        logger.info("=" * 80)
        logger.info(f"✅ Erfolgreiche Tests: {completed_tests - failed_tests}")
        logger.info(f"❌ Fehlgeschlagene Tests: {failed_tests}")
        logger.info(f"📊 Erfolgsrate: {((completed_tests - failed_tests) / total_tests * 100):.1f}%")
        
        # Validiere Datenbank-Einträge
        await self._validate_database_entries()
        
        # Erstelle Abschlussbericht
        await self._generate_final_report(successful_results)
        
    async def _run_single_search(self, model_id: str, mine: Dict, run_number: int) -> Dict:
        """Führe eine einzelne Suche durch"""
        start_time = time.time()
        
        try:
            logger.debug(f"🔍 Test: {model_id} - {mine['name']} Run {run_number}")
            
            # Führe Suche durch
            result = await self.enhanced_service.search_single_model(
                model_id=model_id,
                mine_name=mine['name'],
                country=mine['country'],
                region=mine['region'],
                commodity=mine['commodity']
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Validiere Ergebnis
            success = result.get('success', False)
            if success and result.get('data'):
                data = result['data']
                structured_data = data.get('structured_data', {})
                
                # Zähle gefüllte Felder
                filled_fields = sum(1 for v in structured_data.values() if v and v != '-' and str(v).strip())
                sources_count = len(data.get('sources', []))
                
                # Prüfe auf Dummy-Werte
                has_dummy_values = self._check_for_dummy_values(structured_data)
                
                if has_dummy_values:
                    logger.warning(f"⚠️ Dummy-Werte gefunden in {model_id} - {mine['name']}")
                
                # Speichere in ModelStatistics
                await self.benchmark_service.save_model_statistics(
                    model_id=model_id,
                    mine_name=mine['name'],
                    country=mine['country'],
                    region=mine['region'],
                    commodity=mine['commodity'],
                    run_number=run_number,
                    success=True,
                    response_time_ms=duration_ms,
                    fields_found=filled_fields,
                    sources_count=sources_count,
                    raw_result=result,
                    structured_data=structured_data
                )
                
                return {
                    'model_id': model_id,
                    'mine_name': mine['name'],
                    'run_number': run_number,
                    'success': True,
                    'duration_ms': duration_ms,
                    'filled_fields': filled_fields,
                    'sources_count': sources_count,
                    'has_dummy_values': has_dummy_values
                }
            else:
                # Fehlschlag speichern
                await self.benchmark_service.save_model_statistics(
                    model_id=model_id,
                    mine_name=mine['name'],
                    country=mine['country'],
                    region=mine['region'],
                    commodity=mine['commodity'],
                    run_number=run_number,
                    success=False,
                    response_time_ms=duration_ms,
                    fields_found=0,
                    sources_count=0,
                    error_message=result.get('error', 'Unbekannter Fehler')
                )
                
                return {
                    'model_id': model_id,
                    'mine_name': mine['name'],
                    'run_number': run_number,
                    'success': False,
                    'duration_ms': duration_ms,
                    'error': result.get('error', 'Unbekannter Fehler')
                }
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Exception in {model_id} - {mine['name']}: {e}")
            
            # Speichere Fehler
            try:
                await self.benchmark_service.save_model_statistics(
                    model_id=model_id,
                    mine_name=mine['name'],
                    country=mine['country'],
                    region=mine['region'],
                    commodity=mine['commodity'],
                    run_number=run_number,
                    success=False,
                    response_time_ms=duration_ms,
                    fields_found=0,
                    sources_count=0,
                    error_message=str(e)
                )
            except Exception as save_error:
                logger.error(f"❌ Fehler beim Speichern der Statistiken: {save_error}")
            
            return {
                'model_id': model_id,
                'mine_name': mine['name'],
                'run_number': run_number,
                'success': False,
                'duration_ms': duration_ms,
                'error': str(e)
            }
    
    def _check_for_dummy_values(self, structured_data: Dict) -> bool:
        """Prüfe auf Dummy-Werte in strukturierten Daten"""
        dummy_patterns = [
            '$1', '$2', '$3', 'Company A', 'Company B', 
            'N/A', 'Unknown', 'TBD', 'Lorem ipsum',
            'Test Company', 'Example Corp', 'Dummy'
        ]
        
        for field, value in structured_data.items():
            if value and isinstance(value, str):
                value_lower = value.lower().strip()
                for pattern in dummy_patterns:
                    if pattern.lower() in value_lower:
                        return True
        
        return False
    
    async def _validate_database_entries(self):
        """Validiere Datenbank-Einträge nach Tests"""
        logger.info("🔍 VALIDIERE DATENBANK-EINTRÄGE")
        logger.info("-" * 60)
        
        with db_manager.get_session() as session:
            # ModelStatistics Validierung
            total_stats = session.query(ModelStatistics).count()
            successful_stats = session.query(ModelStatistics).filter(ModelStatistics.success == True).count()
            failed_stats = session.query(ModelStatistics).filter(ModelStatistics.success == False).count()
            
            logger.info(f"📊 ModelStatistics:")
            logger.info(f"  - Gesamt-Einträge: {total_stats}")
            logger.info(f"  - Erfolgreiche: {successful_stats}")
            logger.info(f"  - Fehlgeschlagene: {failed_stats}")
            
            # FieldStatistics Validierung
            field_stats = session.query(FieldStatistics).count()
            logger.info(f"📈 FieldStatistics: {field_stats} Einträge")
            
            # Sources Validierung
            sources_count = session.query(Source).count()
            recent_sources = session.query(Source).filter(
                Source.last_attempted_access >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
            
            logger.info(f"🔗 Sources:")
            logger.info(f"  - Gesamt-Quellen: {sources_count}")
            logger.info(f"  - Heute aktualisiert: {recent_sources}")
    
    async def _generate_final_report(self, results: List[Dict]):
        """Erstelle detaillierten Abschlussbericht"""
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        # Analysiere Ergebnisse
        provider_stats = {}
        total_tests = len(results)
        successful_tests = len([r for r in results if r.get('success')])
        
        for result in results:
            model_id = result['model_id']
            provider_name = model_id.split(':')[0]
            
            if provider_name not in provider_stats:
                provider_stats[provider_name] = {
                    'total': 0,
                    'successful': 0,
                    'avg_duration': 0,
                    'avg_fields': 0,
                    'dummy_values': 0
                }
            
            stats = provider_stats[provider_name]
            stats['total'] += 1
            
            if result.get('success'):
                stats['successful'] += 1
                stats['avg_duration'] += result.get('duration_ms', 0)
                stats['avg_fields'] += result.get('filled_fields', 0)
                
                if result.get('has_dummy_values'):
                    stats['dummy_values'] += 1
        
        # Berechne Durchschnitte
        for provider_name, stats in provider_stats.items():
            if stats['successful'] > 0:
                stats['avg_duration'] = stats['avg_duration'] / stats['successful']
                stats['avg_fields'] = stats['avg_fields'] / stats['successful']
            stats['success_rate'] = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
        
        # Erstelle Report
        report = {
            'test_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_minutes': total_duration.total_seconds() / 60,
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'overall_success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'provider_performance': provider_stats,
            'test_configuration': {
                'mines': TEST_MINES,
                'runs_per_mine': RUNS_PER_MINE,
                'max_parallel_tests': MAX_PARALLEL_TESTS
            }
        }
        
        # Speichere Report
        report_filename = f'comprehensive_provider_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Ausgabe Zusammenfassung
        logger.info("=" * 80)
        logger.info("🎉 UMFASSENDER PROVIDER-TEST ABGESCHLOSSEN")
        logger.info("=" * 80)
        logger.info(f"⏱️ Gesamtdauer: {total_duration.total_seconds() / 60:.1f} Minuten")
        logger.info(f"📊 Tests gesamt: {total_tests}")
        logger.info(f"✅ Erfolgreiche Tests: {successful_tests}")
        logger.info(f"📈 Gesamt-Erfolgsrate: {(successful_tests / total_tests * 100):.1f}%")
        logger.info("")
        logger.info("📋 PROVIDER-PERFORMANCE:")
        
        for provider_name, stats in sorted(provider_stats.items(), key=lambda x: x[1]['success_rate'], reverse=True):
            logger.info(f"  🔹 {provider_name:12} | {stats['success_rate']:5.1f}% | "
                       f"Ø {stats['avg_duration']:6.0f}ms | "
                       f"Ø {stats['avg_fields']:4.1f} Felder | "
                       f"{stats['dummy_values']:2d} Dummy-Werte")
        
        logger.info("")
        logger.info(f"📄 Detaillierter Report: {report_filename}")
        logger.info("=" * 80)

async def main():
    """Hauptfunktion für den umfassenden Provider-Test"""
    tester = ComprehensiveProviderTester()
    
    try:
        await tester.initialize()
        await tester.run_comprehensive_test()
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler im Provider-Test: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())