#!/usr/bin/env python3
"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Schneller Premium Provider Test (1 Run pro Modell/Mine)
"""

import requests
import time
import json
from datetime import datetime
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Premium Provider Modelle (BATCH 2) - Top Modelle für schnelle Tests
PREMIUM_MODELS = [
    # OpenAI Top Modelle (2)
    'openai:o3-deep-research',
    'openai:gpt-4.1',
    
    # Anthropic Top Modelle (2)
    'anthropic:claude-sonnet-4',
    'anthropic:claude-opus-4',
    
    # Google Gemini (2)
    'gemini:gemini-2.5-pro',
    'gemini:gemini-2.5-flash',
    
    # xAI Grok (2)
    'grok:grok-4',
    'grok:grok-3'
]

# Eine Test-Mine für schnelle Validierung
TEST_MINE = {"name": "Éléonore", "country": "Canada", "region": "Quebec", "commodity": "Gold"}

class QuickPremiumTester:
    """Schneller Premium Provider Tester"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def test_model_quickly(self, model_id):
        """Schneller Test eines Modells"""
        logger.info(f"🚀 Teste {model_id} mit {TEST_MINE['name']}")
        
        try:
            start_time = time.time()
            
            # Starte Benchmark
            start_data = {
                "model_ids": [model_id],
                "mine_name": TEST_MINE["name"],
                "country": TEST_MINE["country"],
                "region": TEST_MINE["region"],
                "commodity": TEST_MINE["commodity"],
                "runs": 1
            }
            
            response = requests.post(f"{self.base_url}/api/benchmark/start", 
                                   json=start_data, timeout=180)
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get("session_id")
                
                if session_id:
                    # Warte auf Abschluss (max 120s)
                    success, fields, response_time = self._wait_for_quick_completion(session_id, model_id, start_time)
                    
                    result = {
                        "model_id": model_id,
                        "provider": model_id.split(":")[0],
                        "success": success,
                        "fields_found": fields,
                        "response_time_ms": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self.results.append(result)
                    
                    status = "✅" if success else "❌"
                    logger.info(f"{status} {model_id}: {fields} Felder, {response_time:.0f}ms")
                    
                else:
                    logger.error(f"❌ Keine Session-ID für {model_id}")
            else:
                logger.error(f"❌ API-Fehler für {model_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Exception bei {model_id}: {e}")
    
    def _wait_for_quick_completion(self, session_id, model_id, start_time, max_wait=120):
        """Warte auf schnellen Abschluss"""
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.base_url}/api/benchmark/status/{session_id}", timeout=10)
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status")
                    
                    if status == "completed":
                        # Hole Ergebnisse
                        fields, success = self._get_quick_results(session_id, model_id)
                        response_time = (time.time() - start_time) * 1000
                        return success, fields, response_time
                    elif status == "failed":
                        return False, 0, (time.time() - start_time) * 1000
                        
                # Warte 3 Sekunden vor nächster Abfrage
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ Status-Abfrage Fehler: {e}")
                time.sleep(3)
                
        # Timeout
        return False, 0, (time.time() - start_time) * 1000
    
    def _get_quick_results(self, session_id, model_id):
        """Hole schnelle Ergebnisse"""
        try:
            response = requests.get(f"{self.base_url}/api/benchmark/results/{session_id}", timeout=10)
            
            if response.status_code == 200:
                results_data = response.json()
                
                # Extrahiere wichtige Metriken
                if "results" in results_data:
                    for result in results_data["results"]:
                        if result.get("model_id") == model_id:
                            fields_found = result.get("fields_found", 0)
                            success = result.get("success", False)
                            return fields_found, success
                
            return 0, False
                
        except Exception as e:
            logger.error(f"❌ Ergebnisse-Abruf Fehler: {e}")
            return 0, False
    
    def run_quick_tests(self):
        """Führe schnelle Tests für Top Premium Provider durch"""
        logger.info("🚀 [QUICK-PREMIUM] Schnelle Tests für Top 8 Premium Modelle")
        logger.info(f"📊 [QUICK-PREMIUM] {len(PREMIUM_MODELS)} Modelle × 1 Mine × 1 Run = {len(PREMIUM_MODELS)} Tests")
        
        for idx, model_id in enumerate(PREMIUM_MODELS, 1):
            logger.info(f"🎯 [{idx}/{len(PREMIUM_MODELS)}] {model_id}")
            self.test_model_quickly(model_id)
            
            # Kurze Pause zwischen Tests
            time.sleep(2)
    
    def generate_quick_summary(self):
        """Generiere schnelle Zusammenfassung"""
        if not self.results:
            logger.warning("Keine Ergebnisse verfügbar!")
            return
            
        # Sortiere nach Performance
        self.results.sort(key=lambda x: (x["success"], x["fields_found"]), reverse=True)
        
        logger.info("\n" + "="*80)
        logger.info("🏆 PREMIUM PROVIDER QUICK RANKING:")
        
        for i, result in enumerate(self.results, 1):
            status = "✅" if result["success"] else "❌"
            logger.info(f"{i:2d}. {status} {result['model_id']:25} | "
                       f"{result['fields_found']:2d} Felder | "
                       f"{result['response_time_ms']:6.0f}ms")
        
        # Provider-Statistiken
        providers = {}
        for result in self.results:
            provider = result["provider"]
            if provider not in providers:
                providers[provider] = {"tests": 0, "successful": 0, "total_fields": 0, "avg_time": 0}
            
            providers[provider]["tests"] += 1
            if result["success"]:
                providers[provider]["successful"] += 1
                providers[provider]["total_fields"] += result["fields_found"]
            providers[provider]["avg_time"] += result["response_time_ms"]
        
        logger.info("\n🏢 PROVIDER OVERVIEW:")
        for provider, stats in sorted(providers.items(), 
                                    key=lambda x: x[1]["successful"], 
                                    reverse=True):
            success_rate = stats["successful"] / stats["tests"] if stats["tests"] > 0 else 0
            avg_fields = stats["total_fields"] / stats["successful"] if stats["successful"] > 0 else 0
            avg_time = stats["avg_time"] / stats["tests"] if stats["tests"] > 0 else 0
            
            logger.info(f"{provider:10s}: {success_rate:.1%} Erfolg | "
                       f"{avg_fields:.1f} Felder | {avg_time:.0f}ms")
        
        logger.info(f"\n📊 Total: {len(self.results)} Premium Tests abgeschlossen")
        logger.info("="*80)
        
        # Speichere Ergebnisse
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"premium_quick_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"💾 Ergebnisse gespeichert: {filename}")

def main():
    """Hauptfunktion"""
    logger.info("🎯 Premium LLM Provider Quick Test Suite")
    logger.info("🏢 Teste: OpenAI, Anthropic, Gemini, Grok (Top Modelle)")
    
    tester = QuickPremiumTester()
    tester.run_quick_tests()
    tester.generate_quick_summary()

if __name__ == "__main__":
    main()