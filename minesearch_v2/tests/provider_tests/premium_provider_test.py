#!/usr/bin/env python3
"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Spezieller Test für Premium LLM Provider (BATCH 2)
"""

import asyncio
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

from provider_test_framework import ProviderTestFramework, TestMine

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('premium_provider_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Premium Provider Modelle (BATCH 2)
PREMIUM_MODELS = [
    # OpenAI Modelle (4)
    'openai:o3-deep-research',
    'openai:gpt-4.1',
    'openai:o3',
    'openai:o4-mini',
    
    # Anthropic Modelle (3)
    'anthropic:claude-sonnet-4',
    'anthropic:claude-3.7-sonnet',
    'anthropic:claude-opus-4',
    
    # Google Gemini Modelle (3)
    'gemini:gemini-2.5-pro',
    'gemini:gemini-2.5-flash',
    'gemini:gemini-2.5-flash-lite',
    
    # xAI Grok Modelle (4)
    'grok:grok-4',
    'grok:grok-3',
    'grok:grok-3-mini',
    'grok:grok-3-fast'
]

# Test-Minen (Quebec, Canada)
TEST_MINES = [
    TestMine(name="Éléonore", country="Canada", region="Quebec", commodity="Gold"),
    TestMine(name="Niobec", country="Canada", region="Quebec", commodity="Niobium"),
    TestMine(name="LaRonde", country="Canada", region="Quebec", commodity="Gold")
]

@dataclass
class PremiumTestResult:
    """Premium Provider Test-Ergebnis"""
    provider: str
    model_id: str
    mine_name: str
    run_number: int
    success: bool
    response_time_ms: float
    fields_found: int
    sources_count: int
    api_errors: List[str]
    validation_errors: List[str]
    dummy_values_detected: bool
    intelligence_score: float  # 0-10 basierend auf Feldqualität
    
class PremiumProviderTester:
    """Spezialisierter Tester für Premium Provider"""
    
    def __init__(self):
        self.framework = ProviderTestFramework()
        self.results: List[PremiumTestResult] = []
        
    async def test_single_model(self, model_id: str, mine: TestMine, runs: int = 5):
        """Teste ein einzelnes Premium-Modell"""
        provider = model_id.split(':')[0]
        logger.info(f"🧪 [PREMIUM-TEST] Teste {model_id} mit {mine.name} ({runs} Runs)")
        
        for run in range(1, runs + 1):
            try:
                start_time = time.time()
                
                # Führe einzelnen Test durch
                result = await self.framework._test_single_run(
                    model_id=model_id,
                    mine=mine,
                    run_number=run
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                # Berechne Intelligence Score basierend auf Feldqualität
                intelligence_score = self._calculate_intelligence_score(result)
                
                # Speichere Premium-spezifische Ergebnisse
                premium_result = PremiumTestResult(
                    provider=provider,
                    model_id=model_id,
                    mine_name=mine.name,
                    run_number=run,
                    success=result.success,
                    response_time_ms=response_time,
                    fields_found=result.fields_found,
                    sources_count=result.sources_count,
                    api_errors=result.api_errors or [],
                    validation_errors=result.validation_errors or [],
                    dummy_values_detected=result.dummy_values_detected,
                    intelligence_score=intelligence_score
                )
                
                self.results.append(premium_result)
                
                logger.info(f"✅ [PREMIUM-TEST] {model_id} {mine.name} Run {run}: "
                          f"{result.fields_found} Felder, {response_time:.0f}ms, "
                          f"Intelligence: {intelligence_score:.1f}/10")
                
                # Kurze Pause zwischen Runs
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ [PREMIUM-TEST] Fehler bei {model_id} {mine.name} Run {run}: {e}")
                
                error_result = PremiumTestResult(
                    provider=provider,
                    model_id=model_id,
                    mine_name=mine.name,
                    run_number=run,
                    success=False,
                    response_time_ms=0,
                    fields_found=0,
                    sources_count=0,
                    api_errors=[str(e)],
                    validation_errors=[],
                    dummy_values_detected=False,
                    intelligence_score=0.0
                )
                
                self.results.append(error_result)
    
    def _calculate_intelligence_score(self, result) -> float:
        """Berechne Intelligence Score für Premium Provider (0-10)"""
        score = 0.0
        
        # Basis-Score basierend auf gefundenen Feldern
        if result.fields_found >= 10:
            score += 4.0
        elif result.fields_found >= 8:
            score += 3.0
        elif result.fields_found >= 6:
            score += 2.0
        elif result.fields_found >= 4:
            score += 1.0
            
        # Bonus für kritische Felder
        if hasattr(result, 'critical_fields_found') and result.critical_fields_found > 0:
            score += 2.0
            
        # Abzug für Dummy-Werte (inakzeptabel bei Premium)
        if result.dummy_values_detected:
            score -= 3.0
            
        # Abzug für Validierungsfehler
        if result.validation_errors:
            score -= 1.0
            
        # Bonus für schnelle Response bei hoher Qualität
        if result.response_time_ms < 30000 and result.fields_found >= 8:
            score += 1.0
            
        return max(0.0, min(10.0, score))
    
    async def run_all_premium_tests(self):
        """Führe alle Premium Provider Tests durch"""
        logger.info("🚀 [PREMIUM-BATCH] Starte systematische Tests für 14 Premium Modelle")
        logger.info(f"📊 [PREMIUM-BATCH] {len(PREMIUM_MODELS)} Modelle × {len(TEST_MINES)} Minen × 5 Runs = {len(PREMIUM_MODELS) * len(TEST_MINES) * 5} Tests")
        
        total_tests = len(PREMIUM_MODELS) * len(TEST_MINES) * 5
        completed_tests = 0
        
        for model_idx, model_id in enumerate(PREMIUM_MODELS, 1):
            logger.info(f"🎯 [PREMIUM-BATCH] Modell {model_idx}/{len(PREMIUM_MODELS)}: {model_id}")
            
            for mine in TEST_MINES:
                await self.test_single_model(model_id, mine, runs=5)
                completed_tests += 5
                
                progress = (completed_tests / total_tests) * 100
                logger.info(f"📈 [PREMIUM-BATCH] Fortschritt: {progress:.1f}% ({completed_tests}/{total_tests})")
                
        logger.info("✅ [PREMIUM-BATCH] Alle Premium Provider Tests abgeschlossen!")
        
    def generate_premium_report(self) -> Dict[str, Any]:
        """Generiere umfassenden Premium Provider Report"""
        logger.info("📊 [PREMIUM-REPORT] Generiere Premium Provider Performance Report")
        
        # Gruppiere Ergebnisse nach Provider
        provider_stats = {}
        for result in self.results:
            if result.provider not in provider_stats:
                provider_stats[result.provider] = {
                    'total_tests': 0,
                    'successful_tests': 0,
                    'avg_fields': 0,
                    'avg_response_time': 0,
                    'avg_intelligence': 0,
                    'dummy_violations': 0,
                    'models': {}
                }
            
            stats = provider_stats[result.provider]
            stats['total_tests'] += 1
            
            if result.success:
                stats['successful_tests'] += 1
                stats['avg_fields'] += result.fields_found
                stats['avg_response_time'] += result.response_time_ms
                stats['avg_intelligence'] += result.intelligence_score
                
            if result.dummy_values_detected:
                stats['dummy_violations'] += 1
                
            # Model-spezifische Stats
            if result.model_id not in stats['models']:
                stats['models'][result.model_id] = {
                    'tests': 0,
                    'successes': 0,
                    'avg_fields': 0,
                    'avg_intelligence': 0
                }
                
            model_stats = stats['models'][result.model_id]
            model_stats['tests'] += 1
            if result.success:
                model_stats['successes'] += 1
                model_stats['avg_fields'] += result.fields_found
                model_stats['avg_intelligence'] += result.intelligence_score
        
        # Berechne Durchschnitte
        for provider, stats in provider_stats.items():
            if stats['successful_tests'] > 0:
                stats['avg_fields'] /= stats['successful_tests']
                stats['avg_response_time'] /= stats['successful_tests']
                stats['avg_intelligence'] /= stats['successful_tests']
            stats['success_rate'] = stats['successful_tests'] / stats['total_tests'] if stats['total_tests'] > 0 else 0
                
            for model_id, model_stats in stats['models'].items():
                if model_stats['successes'] > 0:
                    model_stats['avg_fields'] /= model_stats['successes']
                    model_stats['avg_intelligence'] /= model_stats['successes']
                model_stats['success_rate'] = model_stats['successes'] / model_stats['tests'] if model_stats['tests'] > 0 else 0
        
        # Provider Ranking
        provider_ranking = sorted(
            provider_stats.items(),
            key=lambda x: (x[1]['avg_intelligence'], x[1]['avg_fields'], x[1]['success_rate']),
            reverse=True
        )
        
        # Model Ranking (über alle Provider)
        model_performance = []
        for provider, stats in provider_stats.items():
            for model_id, model_stats in stats['models'].items():
                if model_stats['successes'] > 0:
                    model_performance.append({
                        'model_id': model_id,
                        'provider': provider,
                        'avg_intelligence': model_stats['avg_intelligence'],
                        'avg_fields': model_stats['avg_fields'],
                        'success_rate': model_stats['success_rate']
                    })
        
        model_ranking = sorted(
            model_performance,
            key=lambda x: (x['avg_intelligence'], x['avg_fields'], x['success_rate']),
            reverse=True
        )
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'total_models': len(PREMIUM_MODELS),
            'total_providers': len(provider_stats),
            'provider_stats': provider_stats,
            'provider_ranking': provider_ranking,
            'model_ranking': model_ranking,
            'premium_standards': {
                'min_fields_expected': 8,
                'max_dummy_tolerance': 0,
                'min_intelligence_score': 7.0
            }
        }
        
        return report
    
    def save_results(self, filename: str = None):
        """Speichere Ergebnisse in JSON-Datei"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"premium_provider_results_{timestamp}.json"
            
        report = self.generate_premium_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info(f"💾 [PREMIUM-RESULTS] Ergebnisse gespeichert: {filename}")
        return filename

async def main():
    """Hauptfunktion für Premium Provider Tests"""
    logger.info("🎯 [PREMIUM-MAIN] Premium LLM Provider Test Suite (BATCH 2)")
    logger.info("🏢 [PREMIUM-MAIN] Teste: OpenAI, Anthropic, Gemini, Grok")
    
    tester = PremiumProviderTester()
    
    # Führe alle Tests durch
    await tester.run_all_premium_tests()
    
    # Generiere und speichere Report
    filename = tester.save_results()
    
    # Zeige Quick Summary
    report = tester.generate_premium_report()
    logger.info("\n" + "="*80)
    logger.info("🏆 [PREMIUM-SUMMARY] TOP 5 PREMIUM MODELS:")
    for i, model in enumerate(report['model_ranking'][:5], 1):
        logger.info(f"{i}. {model['model_id']}: {model['avg_intelligence']:.1f} Intelligence, "
                   f"{model['avg_fields']:.1f} Felder, {model['success_rate']:.1%} Erfolg")
    
    logger.info("\n🏢 [PREMIUM-SUMMARY] PROVIDER RANKING:")
    for i, (provider, stats) in enumerate(report['provider_ranking'], 1):
        logger.info(f"{i}. {provider}: {stats['avg_intelligence']:.1f} Intelligence, "
                   f"{stats['avg_fields']:.1f} Felder, {stats['success_rate']:.1%} Erfolg")
    
    logger.info(f"\n📊 [PREMIUM-SUMMARY] Vollständiger Report: {filename}")
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(main())