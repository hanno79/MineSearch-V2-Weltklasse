#!/usr/bin/env python3
"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Quick Provider-Test für repräsentative Stichprobe aller Provider
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

# ABACUS-FIX 18.07.2025: Force reload environment before importing config
from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

from providers.registry import provider_registry
from search_service_multi_enhanced import EnhancedMultiProviderSearchService
from model_benchmark_service import ModelBenchmarkService
from database import db_manager, ModelStatistics, FieldStatistics, Source
from config.base import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration - Representative sample
REPRESENTATIVE_MODELS = [
    # Free models first
    "openrouter:deepseek-free",
    "openrouter:mistral-small-free", 
    
    # Web search models
    "tavily:search",
    "exa:neural-search",
    
    # Deep research models
    "abacus:deep-agent",  # ABACUS-FIX 18.07.2025: Hinzugefügt für Deep Research Testing
    
    # Premium AI models
    "perplexity:sonar-pro",
    "anthropic:claude-3-opus",
    "openai:gpt-4o",
    "gemini:gemini-2.5-flash",
    "grok:grok-3",
    "deepseek:deepseek-reasoner"
]

TEST_MINES = [
    {"name": "Éléonore", "country": "Canada", "region": "Quebec", "commodity": "Gold"},
    {"name": "Niobec", "country": "Canada", "region": "Quebec", "commodity": "Niobium"}
]

RUNS_PER_MINE = 2  # Reduced for quick test

class QuickProviderTester:
    """Quick Provider-Tester für repräsentative Stichprobe"""
    
    def __init__(self):
        self.enhanced_service = EnhancedMultiProviderSearchService()
        self.benchmark_service = ModelBenchmarkService()
        self.test_results = {}
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Initialisiere Test-Services"""
        logger.info("🔧 Initialisiere Provider-Registry...")
        provider_registry.initialize(config.PROVIDERS)
        
        all_models = provider_registry.get_all_models()
        logger.info(f"🎯 {len(all_models)} Modelle verfügbar")
        
    async def run_quick_test(self):
        """Führe Quick-Tests durch"""
        logger.info("🚀 STARTE QUICK PROVIDER-TEST")
        logger.info("=" * 60)
        logger.info(f"Test-Start: {self.start_time}")
        logger.info(f"Repräsentative Modelle: {len(REPRESENTATIVE_MODELS)}")
        logger.info(f"Test-Minen: {[mine['name'] for mine in TEST_MINES]}")
        logger.info(f"Durchläufe pro Mine: {RUNS_PER_MINE}")
        logger.info("=" * 60)
        
        # Filtere verfügbare Modelle
        all_models = provider_registry.get_all_models()
        testable_models = []
        
        for model_id in REPRESENTATIVE_MODELS:
            if model_id in all_models:
                provider_name = model_id.split(':')[0]
                provider = provider_registry.get_provider(provider_name)
                if provider and provider.validate_config():
                    testable_models.append(model_id)
                    logger.info(f"✅ {model_id} - verfügbar")
                else:
                    logger.warning(f"⚠️ {model_id} - Provider nicht verfügbar")
            else:
                logger.warning(f"⚠️ {model_id} - Modell nicht registriert")
        
        logger.info(f"🧪 Testbare Modelle: {len(testable_models)}")
        
        # Teste jedes Modell
        total_tests = len(testable_models) * len(TEST_MINES) * RUNS_PER_MINE
        logger.info(f"📋 Gesamt-Tests: {total_tests}")
        
        completed_tests = 0
        successful_tests = 0
        
        for model_id in testable_models:
            for mine in TEST_MINES:
                for run in range(1, RUNS_PER_MINE + 1):
                    try:
                        logger.info(f"🔍 Test {completed_tests + 1}/{total_tests}: {model_id} - {mine['name']} Run {run}")
                        
                        result = await self._run_single_search(model_id, mine, run)
                        completed_tests += 1
                        
                        if result and result.get('success'):
                            successful_tests += 1
                            logger.info(f"✅ Erfolg: {result.get('filled_fields', 0)} Felder, {result.get('duration_ms', 0):.0f}ms")
                        else:
                            logger.warning(f"❌ Fehlschlag: {result.get('error', 'Unbekannt') if result else 'Keine Antwort'}")
                        
                        # Kurze Pause zwischen Tests
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        completed_tests += 1
                        logger.error(f"❌ Exception: {e}")
        
        # Abschlussbericht
        await self._generate_quick_report(completed_tests, successful_tests)
        
    async def _run_single_search(self, model_id: str, mine: Dict, run_number: int) -> Optional[Dict]:
        """Führe eine einzelne Suche durch"""
        start_time = time.time()
        
        try:
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
    
    async def _generate_quick_report(self, completed_tests: int, successful_tests: int):
        """Erstelle Quick-Report"""
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        logger.info("=" * 60)
        logger.info("🎉 QUICK PROVIDER-TEST ABGESCHLOSSEN")
        logger.info("=" * 60)
        logger.info(f"⏱️ Gesamtdauer: {total_duration.total_seconds():.1f} Sekunden")
        logger.info(f"📊 Tests gesamt: {completed_tests}")
        logger.info(f"✅ Erfolgreiche Tests: {successful_tests}")
        logger.info(f"📈 Erfolgsrate: {(successful_tests / completed_tests * 100):.1f}%" if completed_tests > 0 else "0%")
        
        # Validiere Datenbank-Einträge
        with db_manager.get_session() as session:
            total_stats = session.query(ModelStatistics).count()
            successful_stats = session.query(ModelStatistics).filter(ModelStatistics.success == True).count()
            
            logger.info(f"📊 ModelStatistics in DB: {total_stats} (davon {successful_stats} erfolgreich)")
            
            # Recent sources
            recent_sources = session.query(Source).filter(
                Source.last_attempted_access >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
            
            logger.info(f"🔗 Heute aktualisierte Quellen: {recent_sources}")
        
        # Report speichern
        report = {
            'test_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': total_duration.total_seconds(),
                'completed_tests': completed_tests,
                'successful_tests': successful_tests,
                'success_rate': (successful_tests / completed_tests * 100) if completed_tests > 0 else 0
            },
            'tested_models': REPRESENTATIVE_MODELS,
            'test_mines': TEST_MINES,
            'runs_per_mine': RUNS_PER_MINE
        }
        
        report_filename = f'quick_provider_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Report gespeichert: {report_filename}")
        logger.info("=" * 60)

async def main():
    """Hauptfunktion für den Quick Provider-Test"""
    tester = QuickProviderTester()
    
    try:
        await tester.initialize()
        await tester.run_quick_test()
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler im Quick Provider-Test: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())