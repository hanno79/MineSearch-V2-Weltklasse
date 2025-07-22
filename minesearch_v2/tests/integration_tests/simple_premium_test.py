#!/usr/bin/env python3
"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Vereinfachter Premium Provider Test via API
"""

import requests
import time
import json
from datetime import datetime
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
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

# Test-Minen
TEST_MINES = [
    {"name": "Éléonore", "country": "Canada", "region": "Quebec", "commodity": "Gold"},
    {"name": "Niobec", "country": "Canada", "region": "Quebec", "commodity": "Niobium"},
    {"name": "LaRonde", "country": "Canada", "region": "Quebec", "commodity": "Gold"}
]

class SimplePremiumTester:
    """Vereinfachter Premium Provider Tester"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def test_single_model_mine(self, model_id, mine, runs=5):
        """Teste ein Modell mit einer Mine"""
        logger.info(f"🧪 Teste {model_id} mit {mine['name']} ({runs} Runs)")
        
        for run in range(1, runs + 1):
            try:
                # Starte Benchmark
                start_data = {
                    "model_ids": [model_id],
                    "mine_name": mine["name"],
                    "country": mine["country"],
                    "region": mine["region"],
                    "commodity": mine["commodity"],
                    "runs": 1
                }
                
                response = requests.post(f"{self.base_url}/api/benchmark/start", 
                                       json=start_data, timeout=300)
                
                if response.status_code == 200:
                    session_data = response.json()
                    session_id = session_data.get("session_id")
                    
                    if session_id:
                        # Warte auf Abschluss
                        self._wait_for_completion(session_id, model_id, mine["name"], run)
                    else:
                        logger.error(f"❌ Keine Session-ID für {model_id} {mine['name']} Run {run}")
                else:
                    logger.error(f"❌ API-Fehler für {model_id} {mine['name']} Run {run}: {response.status_code}")
                    
                # Pause zwischen Runs
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ Exception bei {model_id} {mine['name']} Run {run}: {e}")
    
    def _wait_for_completion(self, session_id, model_id, mine_name, run_number, max_wait=300):
        """Warte auf Benchmark-Abschluss"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.base_url}/api/benchmark/status/{session_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status")
                    
                    if status == "completed":
                        # Hole Ergebnisse
                        self._get_results(session_id, model_id, mine_name, run_number)
                        return
                    elif status == "failed":
                        logger.error(f"❌ Benchmark fehlgeschlagen: {model_id} {mine_name} Run {run_number}")
                        return
                        
                # Warte 5 Sekunden vor nächster Abfrage
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Status-Abfrage Fehler: {e}")
                time.sleep(5)
                
        logger.error(f"❌ Timeout bei {model_id} {mine_name} Run {run_number}")
    
    def _get_results(self, session_id, model_id, mine_name, run_number):
        """Hole und verarbeite Ergebnisse"""
        try:
            response = requests.get(f"{self.base_url}/api/benchmark/results/{session_id}")
            
            if response.status_code == 200:
                results_data = response.json()
                
                # Extrahiere wichtige Metriken
                fields_found = 0
                success = False
                
                if "results" in results_data:
                    for result in results_data["results"]:
                        if result.get("model_id") == model_id:
                            fields_found = result.get("fields_found", 0)
                            success = result.get("success", False)
                            break
                
                # Speichere Ergebnis
                result = {
                    "model_id": model_id,
                    "mine_name": mine_name,
                    "run_number": run_number,
                    "success": success,
                    "fields_found": fields_found,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                
                logger.info(f"✅ {model_id} {mine_name} Run {run_number}: "
                          f"Success={success}, Felder={fields_found}")
                
            else:
                logger.error(f"❌ Ergebnisse-Abruf fehlgeschlagen: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Ergebnisse-Verarbeitung Fehler: {e}")
    
    def run_all_tests(self):
        """Führe alle Premium Provider Tests durch"""
        logger.info("🚀 [PREMIUM-TESTS] Starte alle 14 Premium Modelle")
        
        total_tests = len(PREMIUM_MODELS) * len(TEST_MINES) * 5
        completed_tests = 0
        
        for model_idx, model_id in enumerate(PREMIUM_MODELS, 1):
            logger.info(f"🎯 [{model_idx}/{len(PREMIUM_MODELS)}] {model_id}")
            
            for mine in TEST_MINES:
                self.test_single_model_mine(model_id, mine, runs=5)
                completed_tests += 5
                
                progress = (completed_tests / total_tests) * 100
                logger.info(f"📈 Fortschritt: {progress:.1f}% ({completed_tests}/{total_tests})")
    
    def generate_summary(self):
        """Generiere Zusammenfassung"""
        if not self.results:
            logger.warning("Keine Ergebnisse verfügbar!")
            return
            
        # Gruppiere nach Provider
        providers = {}
        for result in self.results:
            provider = result["model_id"].split(":")[0]
            if provider not in providers:
                providers[provider] = {"total": 0, "successful": 0, "avg_fields": 0}
                
            providers[provider]["total"] += 1
            if result["success"]:
                providers[provider]["successful"] += 1
                providers[provider]["avg_fields"] += result["fields_found"]
        
        # Berechne Durchschnitte
        for provider, stats in providers.items():
            if stats["successful"] > 0:
                stats["avg_fields"] /= stats["successful"]
                stats["success_rate"] = stats["successful"] / stats["total"]
            else:
                stats["success_rate"] = 0
        
        # Zeige Zusammenfassung
        logger.info("\n" + "="*80)
        logger.info("🏆 PREMIUM PROVIDER SUMMARY:")
        
        for provider, stats in sorted(providers.items(), 
                                    key=lambda x: x[1]["success_rate"], 
                                    reverse=True):
            logger.info(f"{provider}: {stats['success_rate']:.1%} Erfolg, "
                       f"{stats['avg_fields']:.1f} Felder/Test")
        
        logger.info(f"\n📊 Total: {len(self.results)} Tests abgeschlossen")
        logger.info("="*80)
        
        # Speichere Ergebnisse
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"premium_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"💾 Ergebnisse gespeichert: {filename}")

def main():
    """Hauptfunktion"""
    logger.info("🎯 Premium LLM Provider Test Suite - API Version")
    
    tester = SimplePremiumTester()
    tester.run_all_tests()
    tester.generate_summary()

if __name__ == "__main__":
    main()