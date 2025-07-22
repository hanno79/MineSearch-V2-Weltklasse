#!/usr/bin/env python3
"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Systematische Tests für alle Perplexity Modelle
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any

from provider_test_framework import ProviderTestFramework, TestMine
from database import db_manager

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test-Minen (Quebec, Canada)
TEST_MINES = [
    TestMine(name="Éléonore", country="Canada", region="Quebec", commodity="Gold"),
    TestMine(name="Niobec", country="Canada", region="Quebec", commodity="Niobium"),
    TestMine(name="LaRonde", country="Canada", region="Quebec", commodity="Gold")
]

# Perplexity Modelle
PERPLEXITY_MODELS = [
    "perplexity:sonar",
    "perplexity:sonar-pro", 
    "perplexity:sonar-deep-research",
    "perplexity:sonar-reasoning"
]

class PerplexityTestRunner:
    """Systematischer Test-Runner für Perplexity Provider"""
    
    def __init__(self):
        self.framework = ProviderTestFramework()
        self.results = {}
        
    async def run_complete_test_suite(self, runs_per_mine: int = 5):
        """
        Führt komplette Test-Suite für alle Perplexity Modelle durch
        
        Args:
            runs_per_mine: Anzahl Durchläufe pro Mine (Standard: 5)
        """
        logger.info(f"🚀 Starte systematische Perplexity-Tests mit {runs_per_mine} Runs pro Mine")
        
        total_tests = len(PERPLEXITY_MODELS) * len(TEST_MINES) * runs_per_mine
        completed_tests = 0
        
        for model_id in PERPLEXITY_MODELS:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 TESTE MODELL: {model_id}")
            logger.info(f"{'='*60}")
            
            model_results = []
            
            for mine in TEST_MINES:
                logger.info(f"\n📍 Mine: {mine.name} ({mine.country}/{mine.region})")
                mine_results = []
                
                # Mehrere Durchläufe für statistische Aussagekraft
                for run in range(1, runs_per_mine + 1):
                    try:
                        logger.info(f"   🔄 Run {run}/{runs_per_mine}")
                        
                        start_time = time.time()
                        result = await self.framework._test_single_run(model_id, mine, run)
                        test_time = time.time() - start_time
                        
                        mine_results.append(result)
                        completed_tests += 1
                        
                        logger.info(f"   ✅ Erfolg: {result.success}, Felder: {result.fields_found}, Zeit: {result.response_time_ms:.1f}ms")
                        
                        # Progress
                        progress = (completed_tests / total_tests) * 100
                        logger.info(f"   📊 Fortschritt: {completed_tests}/{total_tests} ({progress:.1f}%)")
                        
                        # Pause zwischen Runs um Provider nicht zu überlasten
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"   ❌ Fehler bei Run {run}: {str(e)}")
                        completed_tests += 1
                        continue
                
                # Zusammenfassung für diese Mine
                successful_runs = [r for r in mine_results if r.success]
                if successful_runs:
                    avg_fields = sum(r.fields_found for r in successful_runs) / len(successful_runs)
                    avg_time = sum(r.response_time_ms for r in successful_runs) / len(successful_runs)
                    success_rate = len(successful_runs) / len(mine_results) * 100
                    
                    logger.info(f"   📈 {mine.name}: {len(successful_runs)}/{len(mine_results)} erfolgreich ({success_rate:.1f}%), Ø{avg_fields:.1f} Felder, Ø{avg_time:.0f}ms")
                
                model_results.extend(mine_results)
                
            # Gesamtzusammenfassung für dieses Modell
            self.results[model_id] = model_results
            self._log_model_summary(model_id, model_results)
            
        # Abschließende Gesamtanalyse
        self._generate_final_report()
        
    def _log_model_summary(self, model_id: str, results: List):
        """Loggt Zusammenfassung für ein Modell"""
        successful = [r for r in results if r.success]
        total = len(results)
        
        if not successful:
            logger.warning(f"🔴 {model_id}: 0/{total} erfolgreich")
            return
            
        success_rate = len(successful) / total * 100
        avg_fields = sum(r.fields_found for r in successful) / len(successful)
        avg_time = sum(r.response_time_ms for r in successful) / len(successful)
        
        logger.info(f"🟢 {model_id}: {len(successful)}/{total} erfolgreich ({success_rate:.1f}%)")
        logger.info(f"   📊 Durchschnitt: {avg_fields:.1f} Felder, {avg_time:.0f}ms")
        
    def _generate_final_report(self):
        """Erstellt abschließenden Bericht"""
        logger.info(f"\n{'='*80}")
        logger.info("📋 FINAL REPORT - PERPLEXITY PROVIDER TESTS")
        logger.info(f"{'='*80}")
        
        report_data = {}
        
        for model_id, results in self.results.items():
            successful = [r for r in results if r.success]
            total = len(results)
            
            if successful:
                success_rate = len(successful) / total
                avg_fields = sum(r.fields_found for r in successful) / len(successful)
                avg_time = sum(r.response_time_ms for r in successful) / len(successful)
                
                # Performance Score (normalisiert)
                performance_score = (
                    success_rate * 40 +  # 40% Gewicht Erfolgsrate
                    min(avg_fields / 15, 1) * 30 +  # 30% Gewicht Datenqualität
                    max(0, 1 - (avg_time / 30000)) * 30  # 30% Gewicht Geschwindigkeit
                ) * 100
                
                report_data[model_id] = {
                    'success_rate': success_rate,
                    'avg_fields': avg_fields,
                    'avg_response_time': avg_time,
                    'total_tests': total,
                    'successful_tests': len(successful),
                    'performance_score': performance_score
                }
                
                logger.info(f"{model_id}:")
                logger.info(f"  ✅ Erfolgsrate: {success_rate*100:.1f}% ({len(successful)}/{total})")
                logger.info(f"  📊 Ø Felder: {avg_fields:.1f}")
                logger.info(f"  ⏱️  Ø Zeit: {avg_time:.0f}ms")
                logger.info(f"  🏆 Performance Score: {performance_score:.1f}/100")
                logger.info("")
            else:
                logger.info(f"{model_id}: ❌ Komplett fehlgeschlagen")
                report_data[model_id] = {
                    'success_rate': 0,
                    'avg_fields': 0,
                    'avg_response_time': 0,
                    'total_tests': total,
                    'successful_tests': 0,
                    'performance_score': 0
                }
        
        # Sortiere nach Performance Score
        sorted_models = sorted(report_data.items(), key=lambda x: x[1]['performance_score'], reverse=True)
        
        logger.info("🏆 RANKING:")
        for i, (model_id, data) in enumerate(sorted_models, 1):
            score = data['performance_score']
            logger.info(f"  {i}. {model_id}: {score:.1f}/100")
        
        # Speichere Report in Datei
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"perplexity_test_report_{timestamp}.json"
        
        with open(report_filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'test_summary': {
                    'total_models': len(PERPLEXITY_MODELS),
                    'total_mines': len(TEST_MINES),
                    'runs_per_mine': 5,
                    'total_tests': len(PERPLEXITY_MODELS) * len(TEST_MINES) * 5
                },
                'results': report_data,
                'ranking': [(model, data['performance_score']) for model, data in sorted_models]
            }, indent=2)
        
        logger.info(f"📄 Detaillierter Report gespeichert: {report_filename}")


async def main():
    """Hauptfunktion"""
    runner = PerplexityTestRunner()
    await runner.run_complete_test_suite(runs_per_mine=5)


if __name__ == "__main__":
    asyncio.run(main())