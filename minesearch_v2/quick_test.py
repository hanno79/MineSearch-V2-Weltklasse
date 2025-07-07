"""
Author: rahn
Datum: 03.07.2025
Version: 1.0
Beschreibung: Schneller Test mit ausgewählten Modellen
"""

import httpx
import json
import time
from datetime import datetime
from pathlib import Path

# Konfiguration
BASE_URL = "http://localhost:8000"
TEST_CSV = "test_mines_quebec.csv"
RESULTS_DIR = Path("test_results")
RESULTS_DIR.mkdir(exist_ok=True)

# Schnelle Modelle für ersten Test
QUICK_MODELS = [
    "perplexity:sonar",
    "perplexity:sonar-pro",
    "openrouter:deepseek-free"
]

class QuickTester:
    def __init__(self):
        self.client = httpx.Client(timeout=300.0)  # 5 Minuten Timeout
        
    def upload_csv(self) -> str:
        """Lädt Test-CSV hoch und gibt Cache-Key zurück"""
        with open(TEST_CSV, 'rb') as f:
            response = self.client.post(
                f"{BASE_URL}/api/upload-csv",
                files={"csv_file": ("test.csv", f, "text/csv")}
            )
        
        if response.status_code == 200:
            # Parse HTML response to find cache key
            html = response.text
            # Extract cache key from form data-cache-key attribute
            import re
            match = re.search(r'data-cache-key="([^"]+)"', html)
            if match:
                return match.group(1)
        return ""
    
    def test_single_model(self, model: str, cache_key: str):
        """Testet ein einzelnes Modell"""
        print(f"\n🔍 Teste Modell: {model}")
        
        # Verwende Einzelsuche statt Batch für erste Tests
        mines = ["Jeffrey Mine", "LAB Chrysotile Mine", "Horne Mine", "East Malartic Mine"]
        
        for mine in mines[:1]:  # Teste nur erste Mine
            print(f"  → Suche: {mine}")
            start_time = time.time()
            
            request_data = {
                "mine_name": mine,
                "country": "Canada",
                "region": "Quebec",
                "commodity": "",
                "model": model
            }
            
            try:
                response = self.client.post(
                    f"{BASE_URL}/api/search",
                    json=request_data
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"    ✅ Erfolgreich in {duration:.1f}s")
                    
                    # Analysiere Ergebnis
                    structured_data = result.get("structured_data", {})
                    filled = sum(1 for v in structured_data.values() if v and v != "-")
                    print(f"    📊 Ausgefüllte Felder: {filled}/20")
                    
                    # Prüfe Restaurationskosten
                    costs = structured_data.get("Restaurationskosten", "-")
                    if costs != "-":
                        print(f"    💰 Restaurationskosten: {costs}")
                else:
                    print(f"    ❌ Fehler: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Exception: {str(e)}")
    
    def run_quick_test(self):
        """Führt schnellen Test durch"""
        print("=" * 80)
        print("🚀 Starte Quick-Test mit ausgewählten Modellen")
        print("=" * 80)
        
        # CSV hochladen
        print("\n📤 Lade Test-CSV hoch...")
        cache_key = self.upload_csv()
        if not cache_key:
            print("❌ Fehler beim CSV-Upload!")
            return
        print(f"✅ CSV erfolgreich hochgeladen. Cache-Key: {cache_key}")
        
        # Teste schnelle Modelle
        for model in QUICK_MODELS:
            self.test_single_model(model, cache_key)
            time.sleep(2)
        
        print("\n✅ Quick-Test abgeschlossen!")

if __name__ == "__main__":
    tester = QuickTester()
    tester.run_quick_test()