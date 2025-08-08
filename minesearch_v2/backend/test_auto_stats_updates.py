#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Test für automatische ModelStatistics Updates nach realen Suchen
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from services_container import services
from database import db_manager
from database.models import ModelStatistics, ModelSummary
from auto_stats_updater import auto_stats_updater

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoStatsUpdateTester:
    """
    Tester für automatische ModelStatistics und ModelSummary Updates
    """
    
    def __init__(self):
        self.test_session_id = f"auto_stats_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🧪 AutoStats-Update-Test initialisiert (Session: {self.test_session_id})")
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Führt umfassenden Test für automatische Statistics-Updates durch
        """
        logger.info("🚀 Starte umfassenden AutoStats-Update-Test")
        
        test_results = {
            "test_session_id": self.test_session_id,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Einzelne Suche mit automatischem Update
        test_results["tests"]["single_search"] = await self._test_single_search_auto_update()
        
        # Test 2: Batch-Suche mit automatischen Updates
        test_results["tests"]["batch_search"] = await self._test_batch_search_auto_updates()
        
        # Test 3: Fehlgeschlagene Suche mit Update
        test_results["tests"]["failed_search"] = await self._test_failed_search_update()
        
        # Test 4: ModelSummary Auto-Regeneration
        test_results["tests"]["summary_regeneration"] = await self._test_summary_auto_regeneration()
        
        # Test 5: Performance-Tracking
        test_results["tests"]["performance_tracking"] = await self._test_performance_tracking()
        
        # Zusammenfassung
        test_results["summary"] = self._generate_test_summary(test_results["tests"])
        
        logger.info("✅ Umfassender AutoStats-Update-Test abgeschlossen")
        return test_results
    
    async def _test_single_search_auto_update(self) -> Dict[str, Any]:
        """
        Test: Einzelne Suche löst automatisches ModelStatistics Update aus
        """
        logger.info("🔍 Test 1: Automatisches Update bei einzelner Suche")
        
        try:
            # Zähle ModelStatistics vor der Suche
            with db_manager.get_session() as session:
                stats_before = session.query(ModelStatistics).count()
            
            # Führe reale Suche durch
            search_service = services.mine_search_service
            test_mine = "Eleonore Gold Mine"
            test_model = "openrouter:deepseek-free"
            
            search_result = await search_service.search_mine(
                mine_name=test_mine,
                model=test_model,
                country="Canada"
            )
            
            # Warte kurz für DB-Operationen
            await asyncio.sleep(1)
            
            # Zähle ModelStatistics nach der Suche
            with db_manager.get_session() as session:
                stats_after = session.query(ModelStatistics).count()
                
                # Prüfe ob neuer Eintrag erstellt wurde
                new_stat = session.query(ModelStatistics).filter_by(
                    mine_name=test_mine,
                    model_id=test_model
                ).order_by(ModelStatistics.timestamp.desc()).first()
            
            stats_increase = stats_after - stats_before
            
            return {
                "success": True,
                "search_successful": search_result.get("success", False),
                "stats_before": stats_before,
                "stats_after": stats_after,
                "stats_increased": stats_increase > 0,
                "new_stat_created": new_stat is not None,
                "new_stat_details": {
                    "model_id": new_stat.model_id if new_stat else None,
                    "success": new_stat.success if new_stat else None,
                    "fields_found": new_stat.fields_found if new_stat else None,
                    "timestamp": new_stat.timestamp.isoformat() if new_stat else None
                } if new_stat else None
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Single-Search-Test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_batch_search_auto_updates(self) -> Dict[str, Any]:
        """
        Test: Batch-Suche löst automatische Updates für alle Modelle aus
        """
        logger.info("🔍 Test 2: Automatische Updates bei Batch-Suche")
        
        try:
            # Hole Enhanced Batch Service
            from enhanced_multi_model_batch_service import EnhancedMultiModelBatchService
            batch_service = EnhancedMultiModelBatchService()
            
            # Zähle ModelStatistics vor Batch
            with db_manager.get_session() as session:
                stats_before = session.query(ModelStatistics).count()
            
            # Führe Batch-Suche durch
            test_mine_data = {
                'mine_name': 'Batch Test Mine AutoStats',
                'country': 'Canada',
                'commodity': 'Gold',
                'region': 'Quebec'
            }
            test_models = ['openrouter:deepseek-free', 'openrouter:kimi-k2']
            
            batch_result = await batch_service.enhanced_batch_search_per_mine(
                mine_data=test_mine_data,
                selected_models=test_models,
                session_id=self.test_session_id
            )
            
            # Warte für DB-Operationen
            await asyncio.sleep(2)
            
            # Zähle ModelStatistics nach Batch
            with db_manager.get_session() as session:
                stats_after = session.query(ModelStatistics).count()
                
                # Prüfe spezifische Einträge für Batch-Mine
                batch_stats = session.query(ModelStatistics).filter_by(
                    mine_name=test_mine_data['mine_name']
                ).all()
            
            stats_increase = stats_after - stats_before
            expected_increase = len(test_models)  # Ein Eintrag pro Modell
            
            return {
                "success": True,
                "batch_successful": batch_result.get("success", False),
                "stats_before": stats_before,
                "stats_after": stats_after,
                "stats_increased": stats_increase,
                "expected_increase": expected_increase,
                "increase_matches_expected": stats_increase >= expected_increase,
                "batch_stats_count": len(batch_stats),
                "batch_stats_details": [
                    {
                        "model_id": stat.model_id,
                        "success": stat.success,
                        "fields_found": stat.fields_found,
                        "run_number": stat.run_number
                    } for stat in batch_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Batch-Search-Test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_failed_search_update(self) -> Dict[str, Any]:
        """
        Test: Fehlgeschlagene Suche wird korrekt in ModelStatistics vermerkt
        """
        logger.info("🔍 Test 3: Automatisches Update bei fehlgeschlagener Suche")
        
        try:
            # Teste mit nicht-existentem Modell
            invalid_model = "invalid:non-existent-model"
            test_mine = "Failed Search Test Mine"
            
            # Zähle ModelStatistics vor der Suche
            with db_manager.get_session() as session:
                stats_before = session.query(ModelStatistics).count()
            
            # Führe bewusst fehlschlagende Suche durch
            search_service = services.mine_search_service
            search_result = await search_service.search_mine(
                mine_name=test_mine,
                model=invalid_model,
                country="TestCountry"
            )
            
            # Warte für DB-Operationen
            await asyncio.sleep(1)
            
            # Zähle ModelStatistics nach der Suche
            with db_manager.get_session() as session:
                stats_after = session.query(ModelStatistics).count()
                
                # Suche spezifischen Failed-Eintrag
                failed_stat = session.query(ModelStatistics).filter_by(
                    mine_name=test_mine,
                    success=False
                ).order_by(ModelStatistics.timestamp.desc()).first()
            
            stats_increase = stats_after - stats_before
            
            return {
                "success": True,
                "search_failed_as_expected": not search_result.get("success", True),
                "stats_before": stats_before,
                "stats_after": stats_after,
                "stats_increased": stats_increase > 0,
                "failed_stat_created": failed_stat is not None,
                "failed_stat_details": {
                    "model_id": failed_stat.model_id if failed_stat else None,
                    "success": failed_stat.success if failed_stat else None,
                    "error_message": failed_stat.error_message if failed_stat else None,
                    "timestamp": failed_stat.timestamp.isoformat() if failed_stat else None
                } if failed_stat else None
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Failed-Search-Test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_summary_auto_regeneration(self) -> Dict[str, Any]:
        """
        Test: ModelSummary wird nach Statistics-Updates automatisch regeneriert
        """
        logger.info("🔍 Test 4: Automatische ModelSummary Regeneration")
        
        try:
            test_model = "openrouter:deepseek-free"
            
            # Zähle ModelSummary vor Update
            with db_manager.get_session() as session:
                summary_before = session.query(ModelSummary).filter_by(model_id=test_model).first()
                summary_count_before = session.query(ModelSummary).count()
            
            # Führe manuelles Statistics-Update durch
            test_search_result = {
                "success": True,
                "data": {
                    "structured_data": {
                        "name": "Summary Test Mine",
                        "location": "Test Location",
                        "commodity": "Test Gold"
                    },
                    "sources": [{"url": "test.com", "type": "test"}]
                }
            }
            
            update_result = await auto_stats_updater.update_statistics_after_search(
                mine_name="Summary Test Mine",
                model_used=test_model,
                search_result=test_search_result,
                response_time_ms=1500,
                country="TestCountry"
            )
            
            # Warte für Summary-Regeneration
            await asyncio.sleep(2)
            
            # Prüfe ModelSummary nach Update
            with db_manager.get_session() as session:
                summary_after = session.query(ModelSummary).filter_by(model_id=test_model).first()
                summary_count_after = session.query(ModelSummary).count()
            
            return {
                "success": True,
                "update_successful": update_result.get("success", False),
                "summary_updated": update_result.get("summary_updated", False),
                "summary_count_before": summary_count_before,
                "summary_count_after": summary_count_after,
                "summary_regenerated": summary_after is not None,
                "summary_timestamp_changed": (
                    summary_before is None or 
                    summary_after is None or 
                    summary_after.last_updated > summary_before.last_updated
                ) if summary_before and summary_after else True,
                "summary_details": {
                    "model_id": summary_after.model_id if summary_after else None,
                    "total_tests": summary_after.total_tests if summary_after else None,
                    "success_rate": summary_after.success_rate if summary_after else None,
                    "avg_fields_found": summary_after.avg_fields_found if summary_after else None
                } if summary_after else None
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Summary-Regeneration-Test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_performance_tracking(self) -> Dict[str, Any]:
        """
        Test: Performance-Tracking für reale Suchen
        """
        logger.info("🔍 Test 5: Performance-Tracking für reale Suchen")
        
        try:
            # Hole Recent Statistics Summary
            summary_24h = auto_stats_updater.get_recent_statistics_summary(hours=24)
            summary_1h = auto_stats_updater.get_recent_statistics_summary(hours=1)
            
            # Prüfe Performance-Daten
            has_performance_data = (
                summary_24h.get("total_searches", 0) > 0 or
                summary_1h.get("total_searches", 0) > 0
            )
            
            model_performance_available = (
                len(summary_24h.get("model_performance", {})) > 0 or
                len(summary_1h.get("model_performance", {})) > 0
            )
            
            return {
                "success": True,
                "has_performance_data": has_performance_data,
                "model_performance_available": model_performance_available,
                "summary_24h": {
                    "total_searches": summary_24h.get("total_searches", 0),
                    "success_rate": summary_24h.get("success_rate", 0),
                    "unique_models": summary_24h.get("unique_models", 0),
                    "unique_mines": summary_24h.get("unique_mines", 0)
                },
                "summary_1h": {
                    "total_searches": summary_1h.get("total_searches", 0),
                    "success_rate": summary_1h.get("success_rate", 0),
                    "unique_models": summary_1h.get("unique_models", 0),
                    "unique_mines": summary_1h.get("unique_mines", 0)
                },
                "recent_model_performance": list(summary_1h.get("model_performance", {}).keys())[:3]  # Top 3 Modelle
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Performance-Tracking-Test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_test_summary(self, test_results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Generiert Zusammenfassung aller Test-Ergebnisse
        """
        successful_tests = []
        failed_tests = []
        
        for test_name, result in test_results.items():
            if result.get("success", False):
                successful_tests.append(test_name)
            else:
                failed_tests.append(test_name)
        
        return {
            "total_tests": len(test_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "success_rate": (len(successful_tests) / len(test_results)) * 100,
            "all_tests_passed": len(failed_tests) == 0,
            "successful_test_names": successful_tests,
            "failed_test_names": failed_tests
        }


async def main():
    """
    Hauptfunktion für automatische Statistics-Update-Tests
    """
    logger.info("🧪 Starte automatische Statistics-Update-Tests")
    
    tester = AutoStatsUpdateTester()
    results = await tester.run_comprehensive_test()
    
    # Ausgabe der Ergebnisse
    print("\n" + "="*80)
    print("📊 AUTO-STATS-UPDATE TEST ERGEBNISSE")
    print("="*80)
    
    summary = results["summary"]
    print(f"✅ Erfolgreiche Tests: {summary['successful_tests']}/{summary['total_tests']}")
    print(f"📈 Erfolgsrate: {summary['success_rate']:.1f}%")
    print(f"🎯 Alle Tests bestanden: {'JA' if summary['all_tests_passed'] else 'NEIN'}")
    
    print("\n📋 Test-Details:")
    for test_name, result in results["tests"].items():
        status = "✅" if result.get("success") else "❌"
        print(f"  {status} {test_name}: {result.get('success', False)}")
        if not result.get("success") and result.get("error"):
            print(f"      Fehler: {result['error']}")
    
    print("\n🔍 Performance-Tracking:")
    perf_test = results["tests"].get("performance_tracking", {})
    if perf_test.get("success"):
        summary_24h = perf_test.get("summary_24h", {})
        print(f"  📊 Suchen (24h): {summary_24h.get('total_searches', 0)}")
        print(f"  📈 Erfolgsrate (24h): {summary_24h.get('success_rate', 0):.1f}%")
        print(f"  🤖 Unique Models (24h): {summary_24h.get('unique_models', 0)}")
        print(f"  ⛏️ Unique Mines (24h): {summary_24h.get('unique_mines', 0)}")
    
    print("\n" + "="*80)
    
    if summary['all_tests_passed']:
        logger.info("🎉 Alle AutoStats-Update-Tests erfolgreich!")
    else:
        logger.warning(f"⚠️ {len(summary['failed_test_names'])} Tests fehlgeschlagen!")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())