#!/usr/bin/env python3
"""
Author: rahn
Datum: 12.07.2025
Version: 1.0
Beschreibung: Ausführung der umfassenden Provider-Tests entsprechend /test_provider Slash-Command
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any

# Test Framework Import
from provider_test_framework import ProviderTestFramework
from database_validator import DatabaseValidator

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Hauptfunktion für systematische Provider-Tests
    Entspricht dem /test_provider all Kommando
    """
    logger.info("🚀 [PROVIDER-TESTS] Starte umfassende Provider-Tests für Quebec-Minen")
    
    try:
        # 1. Initialisiere Test-Framework
        test_framework = ProviderTestFramework()
        
        # 2. Führe umfassende Tests durch
        logger.info("📊 [PROVIDER-TESTS] Starte systematische Tests für alle Provider...")
        test_results = await test_framework.run_comprehensive_tests(
            provider_filter="all",
            runs_per_mine=5
        )
        
        # 3. Führe Datenbank-Validierung durch
        logger.info("🔍 [PROVIDER-TESTS] Starte Datenbank-Validierung...")
        validator = DatabaseValidator()
        
        # Bestimme getestete Modelle für Validierung
        tested_models = None
        if test_results.get("success"):
            tested_models = list(test_results.get("model_performance", {}).keys())
        
        validation_results = await validator.validate_comprehensive(
            models_to_check=tested_models,
            mines_to_check=["Éléonore", "Niobec", "LaRonde"]
        )
        
        # 4. Erstelle finalen Report
        final_report = {
            "test_execution": test_results,
            "database_validation": validation_results,
            "execution_timestamp": datetime.now().isoformat(),
            "quebec_mines_tested": ["Éléonore", "Niobec", "LaRonde"],
            "runs_per_mine": 5
        }
        
        # 5. Speichere Ergebnisse
        report_filename = f"provider_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False, default=str)
        
        # 6. Ausgabe der wichtigsten Ergebnisse
        print("\n" + "="*80)
        print("🎯 PROVIDER-TEST ZUSAMMENFASSUNG")
        print("="*80)
        
        if test_results.get("success"):
            summary = test_results.get("test_summary", {})
            print(f"✅ Tests erfolgreich: {summary.get('successful_tests', 0)}/{summary.get('total_tests_executed', 0)}")
            print(f"📈 Gesamt-Erfolgsrate: {summary.get('overall_success_rate', 0):.1%}")
            print(f"⏱️  Test-Dauer: {summary.get('test_duration_seconds', 0):.1f}s")
            print(f"🔢 Modelle getestet: {summary.get('total_models_tested', 0)}")
            
            # Top-Performer
            top_performers = test_results.get("top_performers", {})
            if top_performers:
                print(f"\n🏆 TOP PERFORMER:")
                for i, (model_id, perf) in enumerate(list(top_performers.items())[:3]):
                    print(f"  {i+1}. {model_id} - {perf['success_rate']:.1%} Erfolg, {perf['avg_data_quality']:.2f} Qualität")
            
            # Problem-Modelle
            model_performance = test_results.get("model_performance", {})
            poor_performers = [
                model_id for model_id, perf in model_performance.items()
                if perf["success_rate"] < 0.3
            ]
            if poor_performers:
                print(f"\n⚠️  PROBLEMATISCHE MODELLE (< 30% Erfolg):")
                for model_id in poor_performers[:5]:
                    rate = model_performance[model_id]["success_rate"]
                    print(f"  • {model_id} - {rate:.1%}")
        else:
            print(f"❌ Tests fehlgeschlagen: {test_results.get('error', 'Unbekannter Fehler')}")
        
        # Datenbank-Validierung
        print(f"\n🗄️  DATENBANK-VALIDIERUNG:")
        db_status = validation_results.get("overall_status", "UNKNOWN")
        print(f"   Status: {db_status}")
        
        issues = validation_results.get("issues_summary", {})
        if issues.get("critical"):
            print(f"   🚨 Kritische Issues: {len(issues['critical'])}")
        if issues.get("warnings"):
            print(f"   ⚠️  Warnungen: {len(issues['warnings'])}")
        if not issues.get("critical") and not issues.get("warnings"):
            print(f"   ✅ Keine kritischen Probleme gefunden")
        
        print(f"\n📄 Detaillierter Report gespeichert: {report_filename}")
        print("="*80)
        
        # Empfehlungen
        recommendations = test_results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 EMPFEHLUNGEN:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        return final_report
        
    except Exception as e:
        logger.error(f"🚨 [PROVIDER-TESTS] Kritischer Fehler: {e}")
        print(f"\n❌ FEHLER: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())