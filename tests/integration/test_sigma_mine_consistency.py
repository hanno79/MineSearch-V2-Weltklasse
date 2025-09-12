#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Test der Konsistenz für Sigma Mine mit mehreren Modellen und wiederholten Suchen
"""

import asyncio
import sys
import os
import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

# Add backend to path
sys.path.append('/app/backend')

from minesearch.database.manager import DatabaseManager
from minesearch.database.normalized_manager import NormalizedDatabaseManager
from minesearch.search_service import MineSearchService

class SigmaMineConsistencyTest:
    """Test der Konsistenz für wiederholte Sigma Mine Suchen"""

    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_manager = NormalizedDatabaseManager()
        self.search_service = MineSearchService()

        # Test-Konfiguration
        self.test_mine = {
            'name': 'Sigma Mine',
            'country': 'Kanada',
            'region': 'Quebec'
        }

        # Kostenlose Modelle für Test
        self.test_models = [
            'meta/llama-3.1-8b-instruct:free',
            'google/gemma-2-9b-it:free'
        ]

        self.results = []

    async def run_single_search(self, model_name: str, iteration: int) -> Dict[str, Any]:
        """Führe eine einzelne Suche durch"""
        print(f"\n🔍 Iteration {iteration} mit Modell: {model_name}")

        start_time = time.time()
        try:
            # Führe die Suche durch
            result = await self.search_service.search_mine(
                mine_name=self.test_mine['name'],
                country=self.test_mine['country'],
                model=model_name
            )

            end_time = time.time()
            duration = end_time - start_time

            search_data = {
                'iteration': iteration,
                'model': model_name,
                'duration': duration,
                'success': result.get("success", False),
                'fields_found': len(result.get("structured_data", {})),
                'structured_data': result.get("structured_data", {}),
                'sources_count': len(result.get("sources", [])),
                'timestamp': datetime.now().isoformat()
            }

            print(f"✅ Suche erfolgreich: {search_data['fields_found']} Felder, {duration:.2f}s")
            return search_data

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            search_data = {
                'iteration': iteration,
                'model': model_name,
                'duration': duration,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

            print(f"❌ Suche fehlgeschlagen: {e}")
            return search_data

    async def run_consistency_test(self, iterations_per_model: int = 5):
        """Führe Konsistenztest durch"""
        print(f"\n🚀 STARTE KONSISTENZTEST für {self.test_mine['name']}")
        print(f"📊 {len(self.test_models)} Modelle × {iterations_per_model} Iterationen =
{len(self.test_models) * iterations_per_model} Suchen")

        for model in self.test_models:
            print(f"\n🤖 TESTE MODELL: {model}")

            for iteration in range(1, iterations_per_model + 1):
                search_result = await self.run_single_search(model, iteration)
                self.results.append(search_result)

                # Kurze Pause zwischen Suchen
                await asyncio.sleep(2)

        print(f"\n✅ ALLE SUCHEN ABGESCHLOSSEN: {len(self.results)} Ergebnisse")

    def analyze_database_entries(self):
        """Analysiere die Datenbankeinträge für Sigma Mine"""
        print(f"\n📊 ANALYSIERE DATENBANKEINTRÄGE für {self.test_mine['name']}")

        try:
            with self.db_manager.get_session() as session:
                from sqlalchemy import text

                # 1. Finde alle Sigma Mine Einträge
                mine_query = text("""
                    SELECT id, name, country_id, region_id, latitude, longitude, created_at
                    FROM mines
                    WHERE name LIKE :mine_name
                """)

                mines = session.execute(mine_query, {'mine_name': f'%{self.test_mine["name"]}%'}).fetchall()

                print(f"🏭 GEFUNDENE MINEN: {len(mines)}")
                for mine in mines:
                    print(f"   - Mine ID {mine[0]}: {mine[1]} (Lat: {mine[4]}, Lon: {mine[5]})")

                if not mines:
                    print("❌ Keine Minen gefunden!")
                    return

                # Nimm die erste gefundene Mine
                mine_id = mines[0][0]

                # 2. Finde alle Suchsitzungen
                sessions_query = text("""
                    SELECT id, session_id, search_timestamp, search_duration_ms
                    FROM search_sessions
                    WHERE mine_id = :mine_id
                    ORDER BY search_timestamp DESC
                """)

                sessions = session.execute(sessions_query, {'mine_id': mine_id}).fetchall()
                print(f"🔍 SUCHSITZUNGEN: {len(sessions)}")

                # 3. Analysiere Feldwerte für Konsistenz
                fields_query = text("""
                    SELECT field_name, normalized_value, model_used, confidence_score, search_result_id
                    FROM mine_data_fields
                    WHERE mine_id = :mine_id
                    ORDER BY field_name, search_result_id
                """)

                fields = session.execute(fields_query, {'mine_id': mine_id}).fetchall()
                print(f"📋 FELDWERTE: {len(fields)}")

                # Gruppiere Feldwerte nach field_name
                field_groups = {}
                for field in fields:
                    field_name = field[0]
                    if field_name not in field_groups:
                        field_groups[field_name] = []

                    field_groups[field_name].append({
                        'value': field[1],
                        'model': field[2],
                        'confidence': field[3],
                        'search_id': field[4]
                    })

                # Analysiere Konsistenz
                print(f"\n📊 KONSISTENZ-ANALYSE:")
                for field_name, values in field_groups.items():
                    unique_values = list(set([v['value'] for v in values if v['value']]))
                    consistency_score = len(unique_values) / len(values) if values else 0

                    print(f"   📝 {field_name}:")
                    print(f"      - {len(values)} Werte insgesamt")
                    print(f"      - {len(unique_values)} verschiedene Werte")
                    print(f"      - Konsistenz: {(1-consistency_score)*100:.1f}% (je höher desto konsistenter)")

                    if len(unique_values) <= 3:  # Zeige nur bei wenigen verschiedenen Werten
                        for unique_val in unique_values:
                            count = len([v for v in values if v['value'] == unique_val])
                            print(f"        • '{unique_val}': {count}× gefunden")

        except Exception as e:
            print(f"❌ Fehler bei Datenbankanalyse: {e}")
            import traceback
            traceback.print_exc()

    def save_results(self):
        """Speichere Testergebnisse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/sigma_mine_consistency_test_{timestamp}.json"

        test_summary = {
            'test_info': {
                'mine': self.test_mine,
                'models_tested': self.test_models,
                'total_searches': len(self.results),
                'timestamp': datetime.now().isoformat()
            },
            'results': self.results,
            'statistics': self.calculate_statistics()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, indent=2, ensure_ascii=False)

        print(f"📄 ERGEBNISSE GESPEICHERT: {filename}")

    def calculate_statistics(self) -> Dict[str, Any]:
        """Berechne Statistiken"""
        if not self.results:
            return {}

        successful_results = [r for r in self.results if r.get("success", False)]

        # Modell-spezifische Statistiken
        model_stats = {}
        for model in self.test_models:
            model_results = [r for r in self.results if r.get('model') == model]
            model_successful = [r for r in model_results if r.get("success", False)]

            model_stats[model] = {
                'total_searches': len(model_results),
                'successful_searches': len(model_successful),
                'success_rate': len(model_successful) / len(model_results) * 100 if model_results else 0,
                'avg_duration': sum(r.get("duration", 0) for r in model_successful) /
len(model_successful) if model_successful else 0,
                'avg_fields_found': sum(r.get("fields_found", 0) for r in model_successful) /
len(model_successful) if model_successful else 0
            }

        return {
            'total_searches': len(self.results),
            'successful_searches': len(successful_results),
            'overall_success_rate': len(successful_results) / len(self.results) * 100 if self.results else 0,
            'model_statistics': model_stats
        }

    def print_summary(self):
        """Drucke Zusammenfassung"""
        stats = self.calculate_statistics()

        print(f"\n" + "="*60)
        print(f"📊 ZUSAMMENFASSUNG - SIGMA MINE KONSISTENZTEST")
        print(f"="*60)
        print(f"🏭 Mine: {self.test_mine['name']} ({self.test_mine['country']}, {self.test_mine['region']})")
        print(f"🔍 Gesamte Suchen: {stats['total_searches']}")
        print(f"✅ Erfolgreiche Suchen: {stats['successful_searches']}")
        print(f"📈 Erfolgsquote: {stats['overall_success_rate']:.1f}%")

        print(f"\n🤖 MODELL-VERGLEICH:")
        for model, model_stat in stats.get("model_statistics", {}).items():
            print(f"   {model}:")
            print(f"      - Erfolgsquote: {model_stat['success_rate']:.1f}%")
            print(f"      - Ø Dauer: {model_stat['avg_duration']:.2f}s")
            print(f"      - Ø Felder: {model_stat['avg_fields_found']:.1f}")

async def main():
    """Hauptfunktion"""
    print("🚀 SIGMA MINE KONSISTENZTEST GESTARTET")
    print("="*60)

    tester = SigmaMineConsistencyTest()

    # 1. Führe die Konsistenztests durch
    await tester.run_consistency_test(iterations_per_model=5)

    # 2. Analysiere die Datenbankeinträge
    tester.analyze_database_entries()

    # 3. Drucke Zusammenfassung
    tester.print_summary()

    # 4. Speichere Ergebnisse
    tester.save_results()

    print(f"\n🏁 TEST ABGESCHLOSSEN!")

if __name__ == "__main__":
    asyncio.run(main())
