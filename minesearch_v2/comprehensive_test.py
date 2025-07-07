"""
Author: rahn
Datum: 03.07.2025
Version: 1.0
Beschreibung: Umfassender Test aller Modelle und Kombinationen
"""

import httpx
import json
import time
import csv
from datetime import datetime
from pathlib import Path
from itertools import combinations
import asyncio
from typing import Dict, List, Any, Tuple

# Konfiguration
BASE_URL = "http://localhost:8000"
TEST_CSV = "test_mines_quebec.csv"
RESULTS_DIR = Path("test_results")
RESULTS_DIR.mkdir(exist_ok=True)

# Alle verfügbaren Modelle
MODELS = [
    "perplexity:sonar",
    "perplexity:sonar-pro", 
    "perplexity:sonar-deep-research",
    "perplexity:sonar-reasoning-pro",
    "openrouter:deepseek-free",
    "openrouter:deepseek-chat"
]

# Test-Minen
MINES = [
    {"id": "1", "name": "Jeffrey Mine", "country": "Canada", "region": "Quebec"},
    {"id": "2", "name": "LAB Chrysotile Mine", "country": "Canada", "region": "Quebec"},
    {"id": "3", "name": "Horne Mine", "country": "Canada", "region": "Quebec"},
    {"id": "4", "name": "East Malartic Mine", "country": "Canada", "region": "Quebec"}
]

class MineSearchTester:
    def __init__(self):
        self.client = httpx.Client(timeout=3600.0)  # 60 Minuten Timeout
        self.results = []
        self.session_id = None
        
    def upload_csv(self) -> str:
        """Lädt Test-CSV hoch und gibt Cache-Key zurück"""
        with open(TEST_CSV, 'rb') as f:
            response = self.client.post(
                f"{BASE_URL}/api/upload-csv",
                files={"csv_file": ("test.csv", f, "text/csv")}
            )
        data = response.json()
        return data.get("cache_key", "")
    
    def test_single_model(self, model: str, cache_key: str) -> Dict[str, Any]:
        """Testet ein einzelnes Modell mit allen Minen"""
        print(f"\n🔍 Teste Modell: {model}")
        start_time = time.time()
        
        request_data = {
            "cache_key": cache_key,
            "search_all": True,
            "search_type": "enhanced",
            "models": [model]
        }
        
        try:
            response = self.client.post(
                f"{BASE_URL}/api/batch-search",
                json=request_data
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Erfolgreich in {duration:.1f}s")
                return {
                    "models": [model],
                    "success": True,
                    "duration": duration,
                    "data": result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ Fehler: {response.status_code}")
                return {
                    "models": [model],
                    "success": False,
                    "duration": duration,
                    "error": response.text,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Exception: {str(e)}")
            return {
                "models": [model],
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def test_model_combination(self, models: List[str], cache_key: str) -> Dict[str, Any]:
        """Testet eine Kombination von Modellen"""
        model_str = ", ".join(models)
        print(f"\n🔍 Teste Kombination: {model_str}")
        start_time = time.time()
        
        request_data = {
            "cache_key": cache_key,
            "search_all": True,
            "search_type": "multi",  # Multi-Model-Suche
            "models": models
        }
        
        try:
            response = self.client.post(
                f"{BASE_URL}/api/batch-search",
                json=request_data
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Erfolgreich in {duration:.1f}s")
                return {
                    "models": models,
                    "success": True,
                    "duration": duration,
                    "data": result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ Fehler: {response.status_code}")
                return {
                    "models": models,
                    "success": False,
                    "duration": duration,
                    "error": response.text,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Exception: {str(e)}")
            return {
                "models": models,
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiert die Ergebnisse einer Suche"""
        if not result.get("success"):
            return {
                "models": result["models"],
                "success": False,
                "error": result.get("error", "Unknown error")
            }
        
        analysis = {
            "models": result["models"],
            "duration": result["duration"],
            "mines_analyzed": {}
        }
        
        # Analysiere Batch-Ergebnisse
        if "data" in result and "batch_results" in result["data"]:
            for mine_result in result["data"]["batch_results"]:
                mine_name = mine_result.get("mine_name", "Unknown")
                
                # Zähle ausgefüllte Felder
                structured_data = mine_result.get("structured_data", {})
                filled_fields = sum(1 for v in structured_data.values() if v and v != "-")
                
                # Prüfe auf Restaurationskosten
                restoration_costs = structured_data.get("Restaurationskosten", "-")
                has_costs = restoration_costs != "-" and restoration_costs != ""
                
                # Sammle Koordinaten
                x_coord = structured_data.get("x-Koordinate", "-")
                y_coord = structured_data.get("y-Koordinate", "-")
                has_coords = x_coord != "-" and y_coord != "-"
                
                analysis["mines_analyzed"][mine_name] = {
                    "filled_fields": filled_fields,
                    "total_fields": 20,
                    "completeness": f"{(filled_fields/20)*100:.1f}%",
                    "has_restoration_costs": has_costs,
                    "restoration_costs_value": restoration_costs,
                    "has_coordinates": has_coords,
                    "coordinates": f"{x_coord}, {y_coord}",
                    "sources_count": len(mine_result.get("sources", [])),
                    "data_quality": mine_result.get("data_quality", {})
                }
        
        return analysis
    
    def run_all_tests(self):
        """Führt alle Tests systematisch durch"""
        print("=" * 80)
        print("🚀 Starte umfassenden MineSearch v2 Test")
        print("=" * 80)
        
        # CSV hochladen
        print("\n📤 Lade Test-CSV hoch...")
        cache_key = self.upload_csv()
        if not cache_key:
            print("❌ Fehler beim CSV-Upload!")
            return
        print(f"✅ CSV erfolgreich hochgeladen. Cache-Key: {cache_key}")
        
        all_results = []
        
        # 1. Einzelmodell-Tests
        print("\n" + "=" * 80)
        print("📊 PHASE 1: Einzelmodell-Tests")
        print("=" * 80)
        
        for model in MODELS:
            result = self.test_single_model(model, cache_key)
            analysis = self.analyze_results(result)
            all_results.append(analysis)
            time.sleep(2)  # Kurze Pause zwischen Tests
        
        # 2. Zweier-Kombinationen
        print("\n" + "=" * 80)
        print("📊 PHASE 2: Zweier-Kombinationen")
        print("=" * 80)
        
        for combo in combinations(MODELS, 2):
            result = self.test_model_combination(list(combo), cache_key)
            analysis = self.analyze_results(result)
            all_results.append(analysis)
            time.sleep(2)
        
        # 3. Dreier-Kombinationen (Auswahl)
        print("\n" + "=" * 80)
        print("📊 PHASE 3: Dreier-Kombinationen (Auswahl)")
        print("=" * 80)
        
        # Teste nur sinnvolle 3er-Kombinationen
        selected_3_combos = [
            ["perplexity:sonar", "perplexity:sonar-pro", "openrouter:deepseek-free"],
            ["perplexity:sonar-pro", "perplexity:sonar-reasoning-pro", "openrouter:deepseek-chat"],
            ["perplexity:sonar-deep-research", "openrouter:deepseek-free", "openrouter:deepseek-chat"]
        ]
        
        for combo in selected_3_combos:
            result = self.test_model_combination(combo, cache_key)
            analysis = self.analyze_results(result)
            all_results.append(analysis)
            time.sleep(2)
        
        # 4. Alle Modelle gleichzeitig
        print("\n" + "=" * 80)
        print("📊 PHASE 4: Alle Modelle gleichzeitig")
        print("=" * 80)
        
        result = self.test_model_combination(MODELS, cache_key)
        analysis = self.analyze_results(result)
        all_results.append(analysis)
        
        # Speichere Ergebnisse
        self.save_results(all_results)
        self.print_summary(all_results)
        
    def save_results(self, results: List[Dict[str, Any]]):
        """Speichert alle Testergebnisse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON-Export
        json_path = RESULTS_DIR / f"test_results_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Ergebnisse gespeichert: {json_path}")
        
        # CSV-Export für Analyse
        csv_path = RESULTS_DIR / f"test_results_{timestamp}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Modelle", "Dauer (s)", "Mine", "Ausgefüllte Felder", 
                "Vollständigkeit (%)", "Restaurationskosten", "Koordinaten", "Quellen"
            ])
            
            for result in results:
                if "mines_analyzed" in result:
                    for mine_name, mine_data in result["mines_analyzed"].items():
                        writer.writerow([
                            ", ".join(result["models"]),
                            f"{result.get('duration', 0):.1f}",
                            mine_name,
                            mine_data["filled_fields"],
                            mine_data["completeness"],
                            "Ja" if mine_data["has_restoration_costs"] else "Nein",
                            "Ja" if mine_data["has_coordinates"] else "Nein",
                            mine_data["sources_count"]
                        ])
        print(f"💾 CSV-Export: {csv_path}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Druckt eine Zusammenfassung der Ergebnisse"""
        print("\n" + "=" * 80)
        print("📊 ZUSAMMENFASSUNG")
        print("=" * 80)
        
        # Beste Modelle nach Vollständigkeit
        model_scores = {}
        for result in results:
            if "mines_analyzed" in result:
                model_key = ", ".join(result["models"])
                total_completeness = 0
                count = 0
                
                for mine_data in result["mines_analyzed"].values():
                    completeness = float(mine_data["completeness"].rstrip("%"))
                    total_completeness += completeness
                    count += 1
                
                if count > 0:
                    avg_completeness = total_completeness / count
                    model_scores[model_key] = {
                        "completeness": avg_completeness,
                        "duration": result.get("duration", 0)
                    }
        
        # Sortiere nach Vollständigkeit
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1]["completeness"], reverse=True)
        
        print("\n🏆 TOP 10 Modelle/Kombinationen nach Vollständigkeit:")
        for i, (model, score) in enumerate(sorted_models[:10], 1):
            print(f"{i}. {model}: {score['completeness']:.1f}% in {score['duration']:.1f}s")
        

if __name__ == "__main__":
    tester = MineSearchTester()
    tester.run_all_tests()