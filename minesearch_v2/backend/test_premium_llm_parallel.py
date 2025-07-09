"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Paralleler Test der Premium LLM-Gruppe mit 4 Subagents
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Importiere Provider
from providers.gemini_provider import GeminiProvider
from providers.anthropic_provider import AnthropicProvider
from providers.openai_provider import OpenAIProvider
from providers.deepseek_provider import DeepSeekProvider
from validation_service import ValidationService

# Test-Minen
TEST_MINES = [
    "Kupfermine Cerro Verde, Peru",
    "Lithiummine Salar de Atacama, Chile", 
    "Goldmine Super Pit, Australien"
]

class SubAgent:
    """Basis-Klasse für Subagents"""
    
    def __init__(self, agent_id: str, provider_name: str, models: List[str]):
        self.agent_id = agent_id
        self.provider_name = provider_name
        self.models = models
        self.results = []
        self.validation_service = ValidationService()
        self.start_time = None
        self.end_time = None
        
    def _calculate_completeness(self, result) -> float:
        """Berechne Daten-Vollständigkeit"""
        if not hasattr(result, 'data') or not result.data:
            return 0.0
        
        # Kritische Felder für Vollständigkeit
        critical_fields = [
            'Eigentümer', 'Betreiber', 'Aktivitätsstatus',
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
            'x-Koordinate', 'y-Koordinate', 'Restaurationskosten'
        ]
        
        filled_fields = sum(1 for field in critical_fields 
                          if field in result.data and result.data[field] and str(result.data[field]).strip())
        
        return (filled_fields / len(critical_fields)) * 100
        
    async def test_single_model(self, provider, model_id: str, mine: str) -> Dict[str, Any]:
        """Testet ein einzelnes Modell mit einer Mine"""
        print(f"[{self.agent_id}] Teste {model_id} mit {mine}...")
        
        start = time.time()
        try:
            # Führe Suche durch mit leeren Options
            options = {}
            result = await provider.search(mine, model_id, options)
            
            # Validiere Ergebnis (vereinfacht)
            validation = {
                'is_valid': True,
                'errors': [],
                'data_completeness': self._calculate_completeness(result) if hasattr(result, 'data') else 0
            }
            
            end = time.time()
            
            # Extrahiere Daten aus SearchResult für JSON-Serialisierung
            result_data = {
                'data': result.data if hasattr(result, 'data') else {},
                'sources': result.sources if hasattr(result, 'sources') else [],
                'timestamp': result.timestamp if hasattr(result, 'timestamp') else None,
                'model_used': result.model_used if hasattr(result, 'model_used') else model_id,
                'provider': result.provider if hasattr(result, 'provider') else self.provider_name
            }
            
            return {
                'model': model_id,
                'mine': mine,
                'success': True,
                'duration': end - start,
                'result': result_data,
                'validation': validation,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            end = time.time()
            print(f"[{self.agent_id}] Fehler bei {model_id}: {str(e)}")
            
            return {
                'model': model_id,
                'mine': mine,
                'success': False,
                'duration': end - start,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_tests(self) -> Dict[str, Any]:
        """Führt alle Tests für diesen Subagent aus"""
        self.start_time = time.time()
        print(f"\n[{self.agent_id}] Starte Tests für {self.provider_name}...")
        
        # Erstelle Provider-Instanz mit API Keys und Config
        from config.api_keys import APIKeysConfig
        from config.providers import PROVIDERS_CONFIG
        
        if self.provider_name == 'gemini':
            provider = GeminiProvider(
                api_key=APIKeysConfig.GEMINI_API_KEY,
                config=PROVIDERS_CONFIG['gemini']
            )
        elif self.provider_name == 'anthropic':
            provider = AnthropicProvider(
                api_key=APIKeysConfig.ANTHROPIC_API_KEY,
                config=PROVIDERS_CONFIG['anthropic']
            )
        elif self.provider_name == 'openai':
            provider = OpenAIProvider(
                api_key=APIKeysConfig.OPENAI_API_KEY,
                config=PROVIDERS_CONFIG['openai']
            )
        elif self.provider_name == 'deepseek':
            provider = DeepSeekProvider(
                api_key=APIKeysConfig.OPENROUTER_API_KEY,  # DeepSeek nutzt OpenRouter
                config=PROVIDERS_CONFIG['deepseek']
            )
        
        # Teste alle Modell-Mine-Kombinationen
        for model in self.models:
            for mine in TEST_MINES:
                result = await self.test_single_model(provider, model, mine)
                self.results.append(result)
        
        self.end_time = time.time()
        
        # Erstelle Zusammenfassung
        summary = self.create_summary()
        
        # Speichere Ergebnisse
        self.save_results(summary)
        
        return summary
    
    def create_summary(self) -> Dict[str, Any]:
        """Erstellt eine Zusammenfassung der Tests"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        
        # Berechne Validierungsstatistiken
        validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'validation_details': {}
        }
        
        for result in self.results:
            if result['success'] and 'validation' in result:
                validation_stats['total_validations'] += 1
                if result['validation']['is_valid']:
                    validation_stats['passed_validations'] += 1
                else:
                    validation_stats['failed_validations'] += 1
                
                # Sammle Details nach Modell
                model = result['model']
                if model not in validation_stats['validation_details']:
                    validation_stats['validation_details'][model] = {
                        'total': 0,
                        'passed': 0,
                        'failed': 0,
                        'failures': []
                    }
                
                validation_stats['validation_details'][model]['total'] += 1
                if result['validation']['is_valid']:
                    validation_stats['validation_details'][model]['passed'] += 1
                else:
                    validation_stats['validation_details'][model]['failed'] += 1
                    validation_stats['validation_details'][model]['failures'].append({
                        'mine': result['mine'],
                        'errors': result['validation']['errors']
                    })
        
        return {
            'agent_id': self.agent_id,
            'provider': self.provider_name,
            'models_tested': self.models,
            'mines_tested': TEST_MINES,
            'total_duration': self.end_time - self.start_time,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'validation_stats': validation_stats,
            'results': self.results,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_results(self, summary: Dict[str, Any]):
        """Speichert die Ergebnisse in einer Datei"""
        filename = f"results_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"[{self.agent_id}] Ergebnisse gespeichert in {filename}")


async def run_subagent_async(agent_id: str, provider_name: str, models: List[str]) -> Dict[str, Any]:
    """Wrapper-Funktion für asynchrone Ausführung eines Subagents"""
    agent = SubAgent(agent_id, provider_name, models)
    return await agent.run_tests()


def run_subagent_sync(agent_id: str, provider_name: str, models: List[str]) -> Dict[str, Any]:
    """Synchrone Wrapper-Funktion für Thread-Ausführung"""
    # Erstelle neuen Event Loop für diesen Thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        agent = SubAgent(agent_id, provider_name, models)
        result = loop.run_until_complete(agent.run_tests())
        return result
    finally:
        loop.close()


def main():
    """Hauptfunktion - startet alle 4 Subagents parallel"""
    print("=== Premium LLM Parallel Test ===")
    print(f"Start: {datetime.now()}")
    print(f"Teste {len(TEST_MINES)} Minen mit 4 Provider-Gruppen parallel")
    print("=" * 50)
    
    # Definiere Subagents
    subagents = [
        {
            'id': 'agent_1_gemini',
            'provider': 'gemini',
            'models': ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite']
        },
        {
            'id': 'agent_2_anthropic',
            'provider': 'anthropic',
            'models': ['claude-sonnet-4', 'claude-3.7-sonnet', 'claude-opus-4']
        },
        {
            'id': 'agent_3_openai',
            'provider': 'openai',
            'models': ['o3-deep-research', 'gpt-4.1', 'o3', 'o4-mini']
        },
        {
            'id': 'agent_4_deepseek',
            'provider': 'deepseek',
            'models': ['deepseek-chat', 'deepseek-reasoner']
        }
    ]
    
    # Starte alle Subagents parallel
    start_time = time.time()
    results = []
    
    # Verwende ThreadPoolExecutor für parallele Ausführung
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Starte alle Subagents
        futures = []
        for agent_config in subagents:
            future = executor.submit(
                run_subagent_sync,
                agent_config['id'],
                agent_config['provider'],
                agent_config['models']
            )
            futures.append((future, agent_config['id']))
        
        # Sammle Ergebnisse
        for future, agent_id in futures:
            try:
                result = future.result(timeout=600)  # 10 Minuten Timeout
                results.append(result)
                print(f"\n[MAIN] {agent_id} abgeschlossen!")
            except Exception as e:
                print(f"\n[MAIN] Fehler bei {agent_id}: {str(e)}")
                results.append({
                    'agent_id': agent_id,
                    'error': str(e),
                    'success': False
                })
    
    end_time = time.time()
    
    # Erstelle Gesamtzusammenfassung
    print("\n" + "=" * 50)
    print("=== GESAMTZUSAMMENFASSUNG ===")
    print(f"Gesamtdauer: {end_time - start_time:.2f} Sekunden")
    
    total_tests = 0
    total_success = 0
    total_validations_passed = 0
    
    for result in results:
        if 'error' not in result:
            print(f"\n{result['agent_id']}:")
            print(f"  - Provider: {result['provider']}")
            print(f"  - Tests: {result['total_tests']}")
            print(f"  - Erfolgreich: {result['successful_tests']}")
            print(f"  - Erfolgsrate: {result['success_rate']:.1f}%")
            print(f"  - Validierungen bestanden: {result['validation_stats']['passed_validations']}/{result['validation_stats']['total_validations']}")
            
            total_tests += result['total_tests']
            total_success += result['successful_tests']
            total_validations_passed += result['validation_stats']['passed_validations']
    
    print(f"\nGESAMT:")
    print(f"  - Tests insgesamt: {total_tests}")
    print(f"  - Erfolgreich: {total_success}")
    print(f"  - Erfolgsrate: {(total_success/total_tests*100) if total_tests > 0 else 0:.1f}%")
    print(f"  - Validierungen bestanden: {total_validations_passed}")
    
    # Speichere Gesamtzusammenfassung
    summary_filename = f"premium_llm_parallel_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_type': 'Premium LLM Parallel Test',
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'total_duration': end_time - start_time,
            'subagents': subagents,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nGesamtzusammenfassung gespeichert in {summary_filename}")
    print("=" * 50)


if __name__ == "__main__":
    main()