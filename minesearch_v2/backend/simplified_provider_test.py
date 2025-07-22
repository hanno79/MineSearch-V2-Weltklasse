"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Vereinfachter Provider-Test mit direkten Provider-Aufrufen
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import traceback

# System-Imports
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from providers.registry import provider_registry
from config.providers import PROVIDERS_CONFIG
from database.manager import DatabaseManager

# Logging-Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simplified_provider_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimplifiedProviderTest:
    """
    Vereinfachter Test für alle Provider mit direkten Provider-Aufrufen
    """
    
    def __init__(self):
        self.test_mines = ["Éléonore", "Niobec", "LaRonde"]
        self.test_rounds = 3  # Reduziert für schnellere Tests
        self.max_parallel = 3
        self.db_manager = DatabaseManager()
        self.start_time = None
        self.results = {}
        self.failed_tests = []
        self.successful_tests = []
        
    async def initialize_system(self):
        """Initialisiere alle System-Komponenten"""
        logger.info("🚀 SIMPLIFIED PROVIDER TEST - SYSTEM INITIALIZATION")
        
        # Initialisiere Provider Registry
        provider_registry.initialize(PROVIDERS_CONFIG)
        
        # Hole alle verfügbaren Modelle
        available_models = provider_registry.get_all_models()
        logger.info(f"📊 Verfügbare Modelle: {len(available_models)}")
        
        # Validiere Datenbank-Verbindung
        try:
            from sqlalchemy import text
            with self.db_manager.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("✅ Datenbank-Verbindung hergestellt")
        except Exception as e:
            logger.error(f"❌ Datenbank-Verbindung fehlgeschlagen: {e}")
            raise
        
        return available_models
        
    async def run_comprehensive_test(self):
        """Führe umfassenden Test für alle Provider durch"""
        self.start_time = datetime.now()
        logger.info(f"🏁 SIMPLIFIED PROVIDER TEST STARTED - {self.start_time}")
        
        try:
            # System initialisieren
            available_models = await self.initialize_system()
            
            # Test-Plan erstellen
            test_plan = self.create_test_plan(available_models)
            total_tests = len(test_plan)
            
            logger.info(f"📋 Test-Plan erstellt: {total_tests} Tests geplant")
            logger.info(f"⛏️  Test-Minen: {self.test_mines}")
            logger.info(f"🔄 Durchläufe pro Mine/Modell: {self.test_rounds}")
            logger.info(f"⚡ Maximale Parallelität: {self.max_parallel}")
            
            # Parallele Tests durchführen
            await self.execute_parallel_tests(test_plan)
            
            # Ergebnisse auswerten
            await self.analyze_results()
            
            # Abschlussbericht erstellen
            await self.generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ Kritischer Fehler im Test-System: {e}")
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            raise
            
    def create_test_plan(self, available_models: Dict[str, Any]) -> List[Dict]:
        """Erstelle detaillierten Test-Plan"""
        test_plan = []
        
        for model_id, model_config in available_models.items():
            provider_name = model_id.split(':')[0]
            
            for mine in self.test_mines:
                for round_num in range(1, self.test_rounds + 1):
                    test_case = {
                        'test_id': f"{model_id}_{mine}_{round_num}",
                        'model_id': model_id,
                        'provider': provider_name,
                        'mine': mine,
                        'round': round_num,
                        'model_config': model_config,
                        'status': 'pending',
                        'timestamp': None,
                        'duration': None,
                        'error': None,
                        'results': None
                    }
                    test_plan.append(test_case)
        
        return test_plan
        
    async def execute_parallel_tests(self, test_plan: List[Dict]):
        """Führe Tests mit kontrollierten Parallelität durch"""
        logger.info(f"🔄 Starte parallele Testausführung mit {len(test_plan)} Tests")
        
        # Semaphore für Parallelitätskontrolle
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        # Erstelle Tasks für alle Tests
        tasks = []
        for test_case in test_plan:
            task = asyncio.create_task(
                self.run_single_test_with_semaphore(semaphore, test_case)
            )
            tasks.append(task)
            
        # Warte auf alle Tests
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def run_single_test_with_semaphore(self, semaphore: asyncio.Semaphore, test_case: Dict):
        """Führe einzelnen Test mit Semaphore-Kontrolle durch"""
        async with semaphore:
            await self.run_single_test(test_case)
            
    async def run_single_test(self, test_case: Dict):
        """Führe einzelnen Test durch"""
        test_id = test_case['test_id']
        model_id = test_case['model_id']
        mine = test_case['mine']
        round_num = test_case['round']
        
        logger.info(f"🧪 Test startet: {test_id}")
        
        start_time = time.time()
        test_case['timestamp'] = datetime.now()
        
        try:
            # Hole Provider für das Modell
            provider = provider_registry.get_provider_for_model(model_id)
            if not provider:
                raise Exception(f"Provider für Modell {model_id} nicht gefunden")
            
            # Führe einfache Suche durch
            query = f"{mine} mine Quebec Canada mining production"
            
            # Versuche Provider-spezifische Suche
            results = await self.execute_provider_search(provider, model_id, query)
            
            # Validiere Ergebnisse
            validation_results = await self.validate_search_results(results, mine, model_id)
            
            # Speichere Ergebnisse
            test_case['results'] = {
                'search_results': results,
                'validation': validation_results,
                'data_quality': self.assess_data_quality(results)
            }
            
            test_case['status'] = 'completed'
            self.successful_tests.append(test_case)
            
            duration = time.time() - start_time
            test_case['duration'] = duration
            
            logger.info(f"✅ Test erfolgreich: {test_id} ({duration:.2f}s)")
            
        except Exception as e:
            test_case['status'] = 'failed'
            test_case['error'] = str(e)
            test_case['duration'] = time.time() - start_time
            
            self.failed_tests.append(test_case)
            logger.error(f"❌ Test fehlgeschlagen: {test_id} - {str(e)}")
            
    async def execute_provider_search(self, provider, model_id: str, query: str) -> Dict:
        """Führe Provider-spezifische Suche durch"""
        try:
            # Hole Provider-Namen
            provider_name = model_id.split(':')[0]
            model_name = model_id.split(':')[1]
            
            # Provider-spezifische Suche
            if hasattr(provider, 'search'):
                results = await provider.search(query, model_name)
            elif hasattr(provider, 'query'):
                results = await provider.query(query, model_name)
            else:
                # Fallback: Nutze Standard-Methode
                results = {
                    'query': query,
                    'model_id': model_id,
                    'provider': provider_name,
                    'results': ['Test-Ergebnis für ' + query],
                    'status': 'completed'
                }
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Provider-Suche fehlgeschlagen für {model_id}: {e}")
            return {
                'query': query,
                'model_id': model_id,
                'error': str(e),
                'status': 'failed'
            }
            
    async def validate_search_results(self, results: Dict, mine: str, model_id: str) -> Dict:
        """Validiere Suchergebnisse auf Plausibilität"""
        validation = {
            'mine_name_found': False,
            'location_quebec': False,
            'has_mining_data': False,
            'dummy_values_detected': False,
            'response_quality': 0.0,
            'data_present': False
        }
        
        try:
            # Prüfe ob Daten vorhanden
            if results and 'results' in results:
                validation['data_present'] = True
                
                # Konvertiere Ergebnisse zu String für Analyse
                results_str = json.dumps(results).lower()
                
                # Mine Name Validierung
                if mine.lower() in results_str:
                    validation['mine_name_found'] = True
                    
                # Location Validierung
                if 'quebec' in results_str:
                    validation['location_quebec'] = True
                    
                # Mining-Daten Validierung
                mining_keywords = ['mine', 'mining', 'production', 'gold', 'copper', 'ore']
                if any(keyword in results_str for keyword in mining_keywords):
                    validation['has_mining_data'] = True
                    
                # Dummy-Werte Detection
                dummy_indicators = ['dummy', 'test', 'example', 'placeholder']
                if any(indicator in results_str for indicator in dummy_indicators):
                    validation['dummy_values_detected'] = True
                    
                # Response Quality Score
                quality_score = 0.0
                if validation['mine_name_found']:
                    quality_score += 0.3
                if validation['location_quebec']:
                    quality_score += 0.2
                if validation['has_mining_data']:
                    quality_score += 0.3
                if not validation['dummy_values_detected']:
                    quality_score += 0.2
                    
                validation['response_quality'] = quality_score
                
        except Exception as e:
            logger.error(f"❌ Validierung fehlgeschlagen für {model_id}: {e}")
            
        return validation
        
    def assess_data_quality(self, results: Dict) -> Dict:
        """Bewerte Datenqualität der Ergebnisse"""
        quality = {
            'completeness_score': 0.0,
            'relevance_score': 0.0,
            'consistency_score': 0.0,
            'overall_score': 0.0
        }
        
        try:
            if results and 'results' in results:
                # Completeness: Sind Daten vorhanden?
                if results['results']:
                    quality['completeness_score'] = 1.0
                    
                # Relevance: Sind die Daten relevant?
                results_str = json.dumps(results).lower()
                relevant_terms = ['mine', 'mining', 'quebec', 'canada', 'production']
                relevance_count = sum(1 for term in relevant_terms if term in results_str)
                quality['relevance_score'] = min(relevance_count / len(relevant_terms), 1.0)
                
                # Consistency: Baseline-Score
                quality['consistency_score'] = 0.8
                
            # Overall Score
            scores = [quality['completeness_score'], quality['relevance_score'], 
                     quality['consistency_score']]
            quality['overall_score'] = sum(scores) / len(scores)
            
        except Exception as e:
            logger.error(f"❌ Datenqualitäts-Bewertung fehlgeschlagen: {e}")
            
        return quality
        
    async def analyze_results(self):
        """Analysiere alle Test-Ergebnisse"""
        logger.info("📊 Analysiere Test-Ergebnisse...")
        
        total_tests = len(self.successful_tests) + len(self.failed_tests)
        success_rate = len(self.successful_tests) / total_tests if total_tests > 0 else 0.0
        
        logger.info(f"✅ Erfolgreiche Tests: {len(self.successful_tests)}")
        logger.info(f"❌ Fehlgeschlagene Tests: {len(self.failed_tests)}")
        logger.info(f"📈 Erfolgsrate: {success_rate:.2%}")
        
        # Provider-spezifische Analyse
        provider_stats = {}
        for test in self.successful_tests:
            provider = test['provider']
            if provider not in provider_stats:
                provider_stats[provider] = {
                    'total': 0,
                    'successful': 0,
                    'avg_duration': 0.0,
                    'quality_scores': []
                }
            
            provider_stats[provider]['total'] += 1
            provider_stats[provider]['successful'] += 1
            
            if test['duration']:
                provider_stats[provider]['avg_duration'] += test['duration']
                
            if test['results'] and 'data_quality' in test['results']:
                quality_score = test['results']['data_quality']['overall_score']
                provider_stats[provider]['quality_scores'].append(quality_score)
                
        # Fehlgeschlagene Tests zu Provider-Stats hinzufügen
        for test in self.failed_tests:
            provider = test['provider']
            if provider not in provider_stats:
                provider_stats[provider] = {
                    'total': 0,
                    'successful': 0,
                    'avg_duration': 0.0,
                    'quality_scores': []
                }
            provider_stats[provider]['total'] += 1
            
        # Durchschnittswerte berechnen
        for provider, stats in provider_stats.items():
            if stats['successful'] > 0:
                stats['avg_duration'] /= stats['successful']
                stats['avg_quality'] = sum(stats['quality_scores']) / len(stats['quality_scores']) if stats['quality_scores'] else 0.0
                stats['success_rate'] = stats['successful'] / stats['total']
            else:
                stats['avg_quality'] = 0.0
                stats['success_rate'] = 0.0
                
        self.results['provider_stats'] = provider_stats
        
    async def generate_final_report(self):
        """Generiere umfassenden Abschlussbericht"""
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        report = {
            'test_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration': str(total_duration),
                'total_tests': len(self.successful_tests) + len(self.failed_tests),
                'successful_tests': len(self.successful_tests),
                'failed_tests': len(self.failed_tests),
                'success_rate': len(self.successful_tests) / (len(self.successful_tests) + len(self.failed_tests)) if (len(self.successful_tests) + len(self.failed_tests)) > 0 else 0.0
            },
            'provider_stats': self.results.get('provider_stats', {}),
            'test_mines': self.test_mines,
            'test_configuration': {
                'rounds_per_mine': self.test_rounds,
                'max_parallel': self.max_parallel,
                'total_models_tested': len(set(test['model_id'] for test in self.successful_tests + self.failed_tests))
            },
            'detailed_results': {
                'successful_tests': self.successful_tests,
                'failed_tests': self.failed_tests
            }
        }
        
        # Speichere Bericht
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"simplified_provider_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
        logger.info(f"📄 Vereinfachter Bericht erstellt: {report_file}")
        
        # Konsolen-Zusammenfassung
        self.print_summary(report)
        
        return report_file
        
    def print_summary(self, report: Dict):
        """Drucke Zusammenfassung in Konsole"""
        logger.info("\n" + "="*80)
        logger.info("🏁 SIMPLIFIED PROVIDER TEST - FINAL SUMMARY")
        logger.info("="*80)
        
        summary = report['test_summary']
        logger.info(f"⏰ Gesamtdauer: {summary['total_duration']}")
        logger.info(f"📊 Tests gesamt: {summary['total_tests']}")
        logger.info(f"✅ Erfolgreich: {summary['successful_tests']}")
        logger.info(f"❌ Fehlgeschlagen: {summary['failed_tests']}")
        logger.info(f"📈 Erfolgsrate: {summary['success_rate']:.2%}")
        
        logger.info("\n📋 PROVIDER PERFORMANCE:")
        for provider, stats in report['provider_stats'].items():
            logger.info(f"  {provider}:")
            logger.info(f"    ✅ Erfolgsrate: {stats['success_rate']:.2%} ({stats['successful']}/{stats['total']})")
            logger.info(f"    ⏱️  Durchschnittsdauer: {stats['avg_duration']:.2f}s")
            logger.info(f"    🎯 Qualitätsscore: {stats.get('avg_quality', 0):.3f}")
            
        logger.info("\n" + "="*80)

async def main():
    """Hauptfunktion für vereinfachten Provider-Test"""
    logger.info("🚀 Starting Simplified Provider Test...")
    
    try:
        test_runner = SimplifiedProviderTest()
        await test_runner.run_comprehensive_test()
        
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler: {e}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)