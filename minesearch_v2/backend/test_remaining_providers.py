"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Test der verbleibenden Provider nach den initialen Tests
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os

from model_benchmark_service import ModelBenchmarkService
from database import db_manager, ModelStatistics, ModelSummary, Source
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test-Minen
TEST_MINES = [
    {'name': 'Éléonore', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'},
    {'name': 'Niobec', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Niobium'},
    {'name': 'LaRonde', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'}
]

# Bereits getestete Provider (überspringen)
TESTED_PROVIDERS = {
    'perplexity': ['sonar', 'sonar-pro'],
    'tavily': ['search', 'deep-research'],
    'exa': ['neural-search'],  # research und research-pro haben 404
    'grok': ['grok-3']
}

# Verbleibende Provider
REMAINING_PROVIDERS = {
    'Grok (Rest)': [
        ('grok', ['grok-3-mini', 'grok-3-fast'])
    ],
    'Premium LLMs': [
        ('gemini', ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite']),
        ('anthropic', ['claude-sonnet-4', 'claude-3.7-sonnet', 'claude-opus-4']),
        ('openai', ['o3-deep-research', 'gpt-4.1', 'o3', 'o4-mini']),
        ('deepseek', ['deepseek-chat', 'deepseek-reasoner'])
    ],
    'Scraping-Provider': [
        ('firecrawl', ['scrape', 'crawl', 'extract']),
        ('scrapingbee', ['basic-scrape', 'js-render', 'ai-extract']),
        ('brightdata', ['web-scraper', 'browser-api', 'serp'])
    ],
    'Router-Provider': [
        ('openrouter', ['deepseek-free', 'deepseek-chat', 'deepseek-reasoner'])
    ]
}

# Bekannte problematische Provider
KNOWN_ISSUES = {
    'exa:research': '404 - Endpoint nicht verfügbar',
    'exa:research-pro': '404 - Endpoint nicht verfügbar'
}


class RemainingProviderTester:
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.results = self.load_existing_results()
        
    def load_existing_results(self) -> Dict:
        """Lade existierende Ergebnisse falls vorhanden"""
        if os.path.exists('benchmark_results_complete.json'):
            with open('benchmark_results_complete.json', 'r') as f:
                return json.load(f)
        return {}
    
    def save_results(self):
        """Speichere Ergebnisse"""
        with open('benchmark_results_complete.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
    
    async def test_single_model(self, provider: str, model: str, mine_data: Dict) -> Optional[Dict]:
        """Teste ein einzelnes Modell"""
        model_id = f"{provider}:{model}"
        
        # Skip wenn bekanntes Problem
        if model_id in KNOWN_ISSUES:
            logger.warning(f"⚠️  Überspringe {model_id}: {KNOWN_ISSUES[model_id]}")
            return None
            
        logger.info(f"\nTeste {model_id} mit {mine_data['name']}...")
        
        try:
            # Timeout für langsame Provider
            result = await asyncio.wait_for(
                self.benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=mine_data,
                    runs=5
                ),
                timeout=600  # 10 Minuten max
            )
            
            # Validierung
            with db_manager.get_session() as session:
                summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                
                if summary:
                    logger.info(f"✅ {model_id}: {summary.success_rate:.0%} Erfolg, "
                               f"{summary.avg_fields_found:.1f} Felder, "
                               f"{summary.overall_consistency:.2f} Konsistenz")
                else:
                    logger.warning(f"⚠️  Keine Summary für {model_id}")
            
            return {
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout bei {model_id}")
            return {'success': False, 'error': 'Timeout', 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"❌ Fehler bei {model_id}: {str(e)}")
            return {'success': False, 'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def test_provider_group_parallel(self, group_name: str, providers: List[tuple]):
        """Teste eine Provider-Gruppe parallel"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Teste Gruppe: {group_name}")
        logger.info(f"{'='*60}")
        
        tasks = []
        
        for provider, models in providers:
            for model in models:
                # Skip bereits getestete
                if provider in TESTED_PROVIDERS and model in TESTED_PROVIDERS[provider]:
                    logger.info(f"Überspringe bereits getestetes {provider}:{model}")
                    continue
                
                # Erstelle Tasks für alle Minen
                for mine_data in TEST_MINES:
                    task = self.test_single_model(provider, model, mine_data)
                    tasks.append((provider, model, mine_data['name'], task))
        
        # Führe alle Tasks parallel aus
        results = {}
        for provider, model, mine, task in tasks:
            result = await task
            if provider not in results:
                results[provider] = {}
            if model not in results[provider]:
                results[provider][model] = {}
            results[provider][model][mine] = result
            
            # Speichere Zwischenergebnisse
            self.results[group_name] = results
            self.save_results()
            
            # Kurze Pause zwischen Tasks
            await asyncio.sleep(1)
        
        return results
    
    async def run_all_remaining_tests(self):
        """Führe alle verbleibenden Tests durch"""
        logger.info("=== TESTE VERBLEIBENDE PROVIDER ===")
        
        # Initiale Statistiken
        with db_manager.get_session() as session:
            initial_sources = session.query(func.count(Source.id)).scalar()
            initial_tests = session.query(func.count(ModelStatistics.id)).scalar()
            logger.info(f"Start: {initial_sources} Quellen, {initial_tests} Tests")
        
        # Teste alle Gruppen
        for group_name, providers in REMAINING_PROVIDERS.items():
            await self.test_provider_group_parallel(group_name, providers)
        
        # Finale Statistiken
        with db_manager.get_session() as session:
            final_sources = session.query(func.count(Source.id)).scalar()
            final_tests = session.query(func.count(ModelStatistics.id)).scalar()
            
            # Top Performer
            top_models = session.query(
                ModelSummary.model_id,
                ModelSummary.success_rate,
                ModelSummary.avg_fields_found,
                ModelSummary.overall_consistency
            ).filter(
                ModelSummary.success_rate > 0
            ).order_by(
                ModelSummary.avg_fields_found.desc(),
                ModelSummary.success_rate.desc()
            ).limit(10).all()
            
            logger.info(f"\n{'='*60}")
            logger.info("FINALE STATISTIKEN:")
            logger.info(f"Quellen: {initial_sources} → {final_sources}")
            logger.info(f"Tests: {initial_tests} → {final_tests}")
            logger.info("\nTOP 10 MODELLE (nach Feldern):")
            for i, (model_id, success_rate, avg_fields, consistency) in enumerate(top_models, 1):
                logger.info(f"{i}. {model_id}: {avg_fields:.1f} Felder, "
                           f"{success_rate:.0%} Erfolg, {consistency:.2f} Konsistenz")
        
        return self.results


async def main():
    """Hauptfunktion"""
    tester = RemainingProviderTester()
    
    # Führe Tests durch
    results = await tester.run_all_remaining_tests()
    
    # Erstelle Zusammenfassung
    logger.info("\n✅ Alle Tests abgeschlossen!")
    logger.info("Ergebnisse gespeichert in: benchmark_results_complete.json")
    
    # Zeige Zusammenfassung
    successful_models = 0
    failed_models = 0
    
    for group, providers in results.items():
        for provider, models in providers.items():
            for model, mines in models.items():
                for mine, result in mines.items():
                    if result and result.get('success'):
                        successful_models += 1
                    else:
                        failed_models += 1
    
    logger.info(f"\nZUSAMMENFASSUNG:")
    logger.info(f"✅ Erfolgreiche Tests: {successful_models}")
    logger.info(f"❌ Fehlgeschlagene Tests: {failed_models}")


if __name__ == "__main__":
    asyncio.run(main())