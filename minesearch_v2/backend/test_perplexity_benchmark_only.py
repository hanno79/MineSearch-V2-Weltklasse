"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Benchmark-Test nur für Perplexity Provider mit 3 kanadischen Minen
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

from model_benchmark_service import ModelBenchmarkService
from database import db_manager, ModelStatistics, FieldConsistency, ModelSummary, FieldStatistics, SearchResult, Source
from search_service_multi import MultiProviderSearchService
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test-Minen
TEST_MINES = [
    {'name': 'Éléonore', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'},
    {'name': 'Niobec', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Niobium'},
    {'name': 'LaRonde', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'}
]

# Nur Perplexity Provider
PERPLEXITY_MODELS = ['sonar', 'sonar-pro', 'sonar-deep-research', 'sonar-reasoning']

class PerplexityBenchmarkTester:
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.search_service = MultiProviderSearchService()
        self.results = defaultdict(lambda: defaultdict(dict))
        
    async def validate_database_entries(self, model_id: str, mine_name: str) -> Dict[str, Any]:
        """Validiere Datenbank-Einträge nach einem Test"""
        validation = {
            'model_statistics': {'count': 0, 'success_count': 0, 'avg_fields': 0},
            'field_consistency': {'count': 0, 'avg_consistency': 0},
            'model_summary': {'exists': False, 'total_tests': 0, 'success_rate': 0, 'consistency': 0},
            'field_statistics': {'count': 0, 'fields_with_data': 0},
            'search_results': {'count': 0},
            'sources': {'total': 0, 'new_in_session': 0}
        }
        
        with db_manager.get_session() as session:
            # ModelStatistics
            stats = session.query(ModelStatistics).filter_by(
                model_id=model_id, 
                mine_name=mine_name
            ).all()
            validation['model_statistics']['count'] = len(stats)
            validation['model_statistics']['success_count'] = len([s for s in stats if s.success])
            if stats:
                validation['model_statistics']['avg_fields'] = sum(s.fields_found for s in stats) / len(stats)
            
            # FieldConsistency
            consistencies = session.query(FieldConsistency).filter_by(
                model_id=model_id,
                mine_name=mine_name
            ).all()
            validation['field_consistency']['count'] = len(consistencies)
            if consistencies:
                validation['field_consistency']['avg_consistency'] = sum(c.consistency_score for c in consistencies) / len(consistencies)
            
            # ModelSummary
            summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
            if summary:
                validation['model_summary']['exists'] = True
                validation['model_summary']['total_tests'] = summary.total_tests
                validation['model_summary']['success_rate'] = summary.success_rate
                validation['model_summary']['consistency'] = summary.overall_consistency
            
            # FieldStatistics
            field_stats = session.query(FieldStatistics).filter_by(model_id=model_id).all()
            validation['field_statistics']['count'] = len(field_stats)
            validation['field_statistics']['fields_with_data'] = len([f for f in field_stats if f.times_found > 0])
            
            # SearchResults
            results = session.query(SearchResult).filter_by(
                model_used=model_id,
                mine_name=mine_name
            ).all()
            validation['search_results']['count'] = len(results)
            
            # Sources
            validation['sources']['total'] = session.query(func.count(Source.id)).scalar()
            
        return validation
    
    async def test_single_model(self, model: str, mine_data: Dict[str, str]) -> Dict[str, Any]:
        """Teste ein einzelnes Perplexity Modell mit einer Mine"""
        model_id = f"perplexity:{model}"
        logger.info(f"\n{'='*60}")
        logger.info(f"Teste {model_id} mit {mine_data['name']}")
        logger.info(f"{'='*60}")
        
        # Benchmark durchführen (5 Durchläufe)
        try:
            result = await self.benchmark_service.benchmark_model(
                model_id=model_id,
                mine_data=mine_data,
                runs=5
            )
            
            # Validiere Datenbank-Einträge
            validation = await self.validate_database_entries(model_id, mine_data['name'])
            
            # Zusammenfassung
            summary = {
                'success': True,
                'model_id': model_id,
                'mine': mine_data['name'],
                'benchmark_result': result,
                'validation': validation,
                'timestamp': datetime.now().isoformat()
            }
            
            # Logs
            logger.info(f"✅ Benchmark abgeschlossen für {model_id}")
            logger.info(f"   - Erfolgsrate: {result['success_rate']:.0%}")
            logger.info(f"   - Ø Felder: {result['avg_fields_found']:.1f}")
            logger.info(f"   - Konsistenz: {result['consistency_analysis']['overall_consistency']:.2f}")
            logger.info(f"   - DB Stats: {validation['model_statistics']['count']} Einträge")
            logger.info(f"   - DB Summary: Tests={validation['model_summary']['total_tests']}, "
                       f"Erfolg={validation['model_summary']['success_rate']:.0%}")
            
            # Detaillierte Validierungsinformationen
            logger.info(f"\n📊 DETAILLIERTE VALIDIERUNG:")
            logger.info(f"   ModelStatistics:")
            logger.info(f"     - Einträge: {validation['model_statistics']['count']}")
            logger.info(f"     - Erfolge: {validation['model_statistics']['success_count']}")
            logger.info(f"     - Ø Felder: {validation['model_statistics']['avg_fields']:.1f}")
            
            logger.info(f"   FieldConsistency:")
            logger.info(f"     - Einträge: {validation['field_consistency']['count']}")
            logger.info(f"     - Ø Konsistenz: {validation['field_consistency']['avg_consistency']:.2f}")
            
            logger.info(f"   ModelSummary:")
            logger.info(f"     - Existiert: {validation['model_summary']['exists']}")
            logger.info(f"     - Gesamt-Tests: {validation['model_summary']['total_tests']}")
            logger.info(f"     - Erfolgsrate: {validation['model_summary']['success_rate']:.0%}")
            logger.info(f"     - Konsistenz: {validation['model_summary']['consistency']:.2f}")
            
            logger.info(f"   Sources:")
            logger.info(f"     - Gesamt in DB: {validation['sources']['total']}")
            
            # Warnungen bei Problemen
            if validation['model_summary']['success_rate'] == 0:
                logger.warning(f"⚠️  Erfolgsrate ist 0% für {model_id}!")
            if validation['model_summary']['consistency'] == 0:
                logger.warning(f"⚠️  Konsistenz ist 0 für {model_id}!")
            if validation['model_statistics']['count'] == 0:
                logger.error(f"❌ Keine ModelStatistics für {model_id}!")
                
            return summary
            
        except Exception as e:
            logger.error(f"❌ Fehler bei {model_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'model_id': model_id,
                'mine': mine_data['name'],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_perplexity_benchmark(self):
        """Führe Benchmark nur für Perplexity Provider durch"""
        logger.info("=== STARTE PERPLEXITY BENCHMARK ===")
        logger.info(f"Test-Minen: {', '.join([m['name'] for m in TEST_MINES])}")
        logger.info(f"Perplexity Modelle: {', '.join(PERPLEXITY_MODELS)}")
        
        # Initiale Statistiken
        with db_manager.get_session() as session:
            initial_sources = session.query(func.count(Source.id)).scalar()
            logger.info(f"Initiale Quellen in DB: {initial_sources}")
        
        # Teste alle Perplexity Modelle
        all_results = {}
        
        for model in PERPLEXITY_MODELS:
            model_results = {}
            
            # Teste mit allen 3 Minen
            for mine_data in TEST_MINES:
                result = await self.test_single_model(model, mine_data)
                model_results[mine_data['name']] = result
                
                # Kurze Pause zwischen Tests
                await asyncio.sleep(2)
            
            all_results[model] = model_results
        
        # Finale Statistiken
        with db_manager.get_session() as session:
            final_sources = session.query(func.count(Source.id)).scalar()
            
            # Perplexity-spezifische Statistiken
            perplexity_stats = session.query(ModelStatistics).filter(
                ModelStatistics.model_id.like('perplexity:%')
            ).all()
            
            perplexity_summaries = session.query(ModelSummary).filter(
                ModelSummary.model_id.like('perplexity:%')
            ).all()
            
            logger.info(f"\n{'='*60}")
            logger.info("FINALE PERPLEXITY STATISTIKEN:")
            logger.info(f"  - Quellen: {initial_sources} → {final_sources} (+{final_sources - initial_sources})")
            logger.info(f"  - Perplexity ModelStatistics: {len(perplexity_stats)}")
            logger.info(f"  - Perplexity ModelSummaries: {len(perplexity_summaries)}")
            
            # Perplexity Modell Performance
            logger.info("\nPERPLEXITY MODELL PERFORMANCE:")
            for summary in perplexity_summaries:
                logger.info(f"  - {summary.model_id}:")
                logger.info(f"    - Erfolgsrate: {summary.success_rate:.0%}")
                logger.info(f"    - Ø Felder: {summary.avg_fields_found:.1f}")
                logger.info(f"    - Konsistenz: {summary.overall_consistency:.2f}")
                logger.info(f"    - Tests: {summary.total_tests}")
            
            # Prüfe ob alle 319 Quellen genutzt werden
            if final_sources >= 319:
                logger.info(f"✅ Alle 319 Quellen werden genutzt! (Aktuell: {final_sources})")
            else:
                logger.warning(f"⚠️  Nur {final_sources} von 319 Quellen werden genutzt!")
        
        return all_results

async def main():
    """Hauptfunktion"""
    tester = PerplexityBenchmarkTester()
    results = await tester.run_perplexity_benchmark()
    
    # Speichere Ergebnisse
    import json
    with open('perplexity_benchmark_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info("\n✅ Perplexity Benchmark abgeschlossen! Ergebnisse in perplexity_benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(main())