"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: Umfassender Benchmark-Test für alle Perplexity-Modelle
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any

from model_benchmark_service import ModelBenchmarkService
from database import db_manager

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test-Konfiguration
PERPLEXITY_MODELS = [
    "perplexity:sonar",
    "perplexity:sonar-pro",
    "perplexity:sonar-deep-research",
    "perplexity:sonar-reasoning"
]

# Test-Minen mit unterschiedlichen Charakteristiken
TEST_MINES = [
    {
        'name': 'Canadian Malartic',
        'country': 'Canada',
        'region': 'Quebec',
        'commodity': 'Gold',
        'description': 'Große Goldmine in Kanada'
    },
    {
        'name': 'Jeffrey Mine',
        'country': 'Canada',
        'region': 'Quebec',
        'commodity': 'Asbestos',
        'description': 'Historische Asbestmine'
    },
    {
        'name': 'Grasberg Mine',
        'country': 'Indonesia',
        'region': 'Papua',
        'commodity': 'Gold, Copper',
        'description': 'Eine der größten Gold- und Kupferminen der Welt'
    }
]

# Anzahl Durchläufe pro Modell/Mine
BENCHMARK_RUNS = 5


class PerplexityBenchmarkRunner:
    """Runner für umfassende Perplexity-Benchmarks"""
    
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.results = {}
        self.start_time = None
        
    async def run_comprehensive_benchmarks(self):
        """Führt umfassende Benchmarks für alle Perplexity-Modelle durch"""
        self.start_time = datetime.now()
        
        logger.info("="*80)
        logger.info("PERPLEXITY MODELL-BENCHMARK TEST")
        logger.info("="*80)
        logger.info(f"Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Modelle: {', '.join(PERPLEXITY_MODELS)}")
        logger.info(f"Test-Minen: {len(TEST_MINES)}")
        logger.info(f"Durchläufe pro Modell/Mine: {BENCHMARK_RUNS}")
        logger.info("="*80)
        
        # Datenbank ist bereits initialisiert
        
        # Teste jedes Modell mit jeder Mine
        for model_id in PERPLEXITY_MODELS:
            logger.info(f"\n{'='*60}")
            logger.info(f"TESTE MODELL: {model_id}")
            logger.info("="*60)
            
            self.results[model_id] = {
                'mine_results': {},
                'overall_stats': {}
            }
            
            for mine in TEST_MINES:
                logger.info(f"\nMine: {mine['name']} ({mine['commodity']})")
                
                try:
                    # Führe Benchmark durch
                    result = await self.benchmark_service.benchmark_model(
                        model_id=model_id,
                        mine_data=mine,
                        runs=BENCHMARK_RUNS
                    )
                    
                    self.results[model_id]['mine_results'][mine['name']] = result
                    
                    # Zeige Zusammenfassung
                    self._print_mine_summary(model_id, mine['name'], result)
                    
                except Exception as e:
                    logger.error(f"Fehler bei {model_id} - {mine['name']}: {str(e)}")
                    self.results[model_id]['mine_results'][mine['name']] = {
                        'error': str(e),
                        'success': False
                    }
                
                # Pause zwischen Minen
                await asyncio.sleep(3)
            
            # Berechne Gesamt-Statistiken für Modell
            self._calculate_model_stats(model_id)
        
        # Erstelle Gesamt-Bericht
        await self._generate_final_report()
    
    def _print_mine_summary(self, model_id: str, mine_name: str, result: Dict):
        """Gibt Zusammenfassung für eine Mine aus"""
        logger.info(f"\n  📊 Ergebnisse für {mine_name}:")
        logger.info(f"     Erfolgsrate: {result['success_rate']:.0%} ({result['successful_runs']}/{result['total_runs']})")
        logger.info(f"     Ø Response-Zeit: {result['avg_response_time_ms']:.0f}ms")
        logger.info(f"     Ø Gefundene Felder: {result['avg_fields_found']:.1f}")
        logger.info(f"     Ø Quellen: {result['avg_sources_count']:.1f}")
        
        # Konsistenz-Details
        consistency = result.get('consistency_analysis', {})
        logger.info(f"     Gesamt-Konsistenz: {consistency.get('overall_consistency', 0):.1%}")
        logger.info(f"     Kritische Felder gefunden: {consistency.get('critical_fields_found', 0)}/6")
        
        # Top 5 konsistente Felder
        field_consistency = consistency.get('field_consistency', {})
        if field_consistency:
            sorted_fields = sorted(
                field_consistency.items(), 
                key=lambda x: x[1]['consistency_score'], 
                reverse=True
            )[:5]
            
            logger.info("     Top 5 konsistente Felder:")
            for field, data in sorted_fields:
                logger.info(f"       - {field}: {data['consistency_score']:.1%} (Wert: {data['most_common_value']})")
    
    def _calculate_model_stats(self, model_id: str):
        """Berechnet Gesamt-Statistiken für ein Modell"""
        mine_results = self.results[model_id]['mine_results']
        
        # Sammle alle Metriken
        success_rates = []
        response_times = []
        fields_counts = []
        consistency_scores = []
        
        for mine_name, result in mine_results.items():
            if isinstance(result, dict) and not result.get('error'):
                success_rates.append(result.get('success_rate', 0))
                response_times.append(result.get('avg_response_time_ms', 0))
                fields_counts.append(result.get('avg_fields_found', 0))
                
                consistency = result.get('consistency_analysis', {})
                consistency_scores.append(consistency.get('overall_consistency', 0))
        
        # Berechne Durchschnitte
        if success_rates:
            self.results[model_id]['overall_stats'] = {
                'avg_success_rate': sum(success_rates) / len(success_rates),
                'avg_response_time': sum(response_times) / len(response_times),
                'avg_fields_found': sum(fields_counts) / len(fields_counts),
                'avg_consistency': sum(consistency_scores) / len(consistency_scores),
                'mines_tested': len(mine_results),
                'successful_mines': len(success_rates)
            }
    
    async def _generate_final_report(self):
        """Erstellt finalen Bericht"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Erstelle Report-Struktur
        report = {
            'metadata': {
                'test_name': 'Perplexity Models Comprehensive Benchmark',
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'models_tested': len(PERPLEXITY_MODELS),
                'mines_tested': len(TEST_MINES),
                'runs_per_combination': BENCHMARK_RUNS
            },
            'model_results': self.results,
            'rankings': self._create_rankings()
        }
        
        # Speichere JSON-Report
        filename = f"perplexity_benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Ausgabe Zusammenfassung
        self._print_final_summary(report, filename)
    
    def _create_rankings(self) -> Dict[str, List[Dict]]:
        """Erstellt Rankings nach verschiedenen Kriterien"""
        rankings = {
            'by_success_rate': [],
            'by_consistency': [],
            'by_fields_found': [],
            'by_response_time': []
        }
        
        for model_id, data in self.results.items():
            stats = data.get('overall_stats', {})
            if stats:
                model_entry = {
                    'model_id': model_id,
                    'success_rate': stats.get('avg_success_rate', 0),
                    'consistency': stats.get('avg_consistency', 0),
                    'fields_found': stats.get('avg_fields_found', 0),
                    'response_time': stats.get('avg_response_time', 0)
                }
                
                rankings['by_success_rate'].append(model_entry)
                rankings['by_consistency'].append(model_entry)
                rankings['by_fields_found'].append(model_entry)
                rankings['by_response_time'].append(model_entry)
        
        # Sortiere Rankings
        rankings['by_success_rate'].sort(key=lambda x: x['success_rate'], reverse=True)
        rankings['by_consistency'].sort(key=lambda x: x['consistency'], reverse=True)
        rankings['by_fields_found'].sort(key=lambda x: x['fields_found'], reverse=True)
        rankings['by_response_time'].sort(key=lambda x: x['response_time'])  # Niedrigste zuerst
        
        return rankings
    
    def _print_final_summary(self, report: Dict, filename: str):
        """Gibt finale Zusammenfassung aus"""
        logger.info("\n" + "="*80)
        logger.info("FINALE ZUSAMMENFASSUNG - PERPLEXITY MODELLE")
        logger.info("="*80)
        
        rankings = report['rankings']
        
        # Erfolgsrate Ranking
        logger.info("\n🏆 RANKING NACH ERFOLGSRATE:")
        for i, model in enumerate(rankings['by_success_rate'], 1):
            logger.info(f"  {i}. {model['model_id']}: {model['success_rate']:.1%}")
        
        # Konsistenz Ranking
        logger.info("\n🎯 RANKING NACH KONSISTENZ:")
        for i, model in enumerate(rankings['by_consistency'], 1):
            logger.info(f"  {i}. {model['model_id']}: {model['consistency']:.1%}")
        
        # Datenqualität Ranking
        logger.info("\n📊 RANKING NACH GEFUNDENEN FELDERN:")
        for i, model in enumerate(rankings['by_fields_found'], 1):
            logger.info(f"  {i}. {model['model_id']}: Ø {model['fields_found']:.1f} Felder")
        
        # Geschwindigkeit Ranking
        logger.info("\n⚡ RANKING NACH GESCHWINDIGKEIT:")
        for i, model in enumerate(rankings['by_response_time'], 1):
            logger.info(f"  {i}. {model['model_id']}: Ø {model['response_time']:.0f}ms")
        
        # Detaillierte Modell-Analyse
        logger.info("\n" + "="*60)
        logger.info("DETAILLIERTE MODELL-ANALYSE")
        logger.info("="*60)
        
        for model_id in PERPLEXITY_MODELS:
            stats = self.results[model_id].get('overall_stats', {})
            if stats:
                logger.info(f"\n{model_id}:")
                logger.info(f"  - Erfolgsrate: {stats['avg_success_rate']:.1%}")
                logger.info(f"  - Konsistenz: {stats['avg_consistency']:.1%}")
                logger.info(f"  - Ø Felder: {stats['avg_fields_found']:.1f}")
                logger.info(f"  - Ø Zeit: {stats['avg_response_time']:.0f}ms")
                logger.info(f"  - Getestete Minen: {stats['mines_tested']}")
                
                # Feld-Konsistenz Details
                logger.info("  - Häufigste konsistente Felder:")
                for mine_name, result in self.results[model_id]['mine_results'].items():
                    if isinstance(result, dict) and 'consistency_analysis' in result:
                        field_consistency = result['consistency_analysis'].get('field_consistency', {})
                        for field, data in list(field_consistency.items())[:3]:
                            if data['is_consistent']:
                                logger.info(f"    • {field}: {data['consistency_score']:.0%} konsistent")
        
        # Empfehlungen
        logger.info("\n" + "="*60)
        logger.info("💡 EMPFEHLUNGEN")
        logger.info("="*60)
        
        # Bestes Modell gesamt
        if rankings['by_success_rate']:
            best_overall = rankings['by_success_rate'][0]
            logger.info(f"\n✅ BESTES MODELL GESAMT: {best_overall['model_id']}")
            logger.info(f"   - {best_overall['success_rate']:.0%} Erfolgsrate")
            logger.info(f"   - {best_overall['consistency']:.0%} Konsistenz")
        
        # Warnung bei inkonsistenten Modellen
        inconsistent_models = [m for m in rankings['by_consistency'] if m['consistency'] < 0.5]
        if inconsistent_models:
            logger.info("\n⚠️  INKONSISTENTE MODELLE (<50% Konsistenz):")
            for model in inconsistent_models:
                logger.info(f"   - {model['model_id']}: {model['consistency']:.0%}")
        
        # Test-Details
        logger.info(f"\n📄 Detaillierte Ergebnisse gespeichert: {filename}")
        logger.info(f"⏱️  Gesamtdauer: {report['metadata']['duration_seconds']/60:.1f} Minuten")
        logger.info(f"🔄 Gesamt-Anfragen: {len(PERPLEXITY_MODELS) * len(TEST_MINES) * BENCHMARK_RUNS}")
        logger.info("="*80)


async def main():
    """Hauptfunktion"""
    runner = PerplexityBenchmarkRunner()
    await runner.run_comprehensive_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())