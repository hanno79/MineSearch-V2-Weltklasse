#!/usr/bin/env python3
"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Test für Source Attribution Fix - Prüft ob alle Provider Quellenangaben konsistent verwenden
"""

import asyncio
import logging
from typing import Dict, List, Any
from minesearch.multi_model_search_orchestrator import MultiModelSearchOrchestrator
from minesearch.source_validation import source_validator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_source_attribution_consistency():
    """
    Haupttest: Prüft ob alle Provider konsistent die gleichen Quellen verwenden
    """
    print("🔍 QUELLENANGABEN KONSISTENZ TEST")
    print("=" * 50)
    
    # Test mit einer bekannten Mine
    mine_name = "Eleonore Mine"
    country = "Canada" 
    region = "Quebec"
    commodity = "Gold"
    
    # Teste mit verfügbaren Providern
    test_models = [
        "openrouter:deepseek-free"
        # Weitere Modelle können hinzugefügt werden wenn API-Keys verfügbar
    ]
    
    print(f"🏗️ Teste Mine: {mine_name}")
    print(f"📍 Land: {country}, Region: {region}")
    print(f"⚡ Modelle: {', '.join(test_models)}")
    print()
    
    try:
        # Führe Multi-Model-Suche durch
        orchestrator = MultiModelSearchOrchestrator()
        
        print("🚀 Starte Multi-Model Orchestration...")
        result = await orchestrator.orchestrate_multi_model_search(
            mine_name=mine_name,
            models=test_models,
            country=country,
            region=region,
            commodity=commodity
        )
        
        print(f"✅ Orchestration abgeschlossen")
        print(f"📊 Erfolgreiche Modelle: {len(result.successful_models)}")
        print(f"❌ Fehlgeschlagene Modelle: {len(result.failed_models)}")
        print(f"🔗 Shared Sources: {len(result.shared_sources)}")
        print()
        
        # Analysiere Source Attribution
        print("🔍 QUELLENANALYSE:")
        print("-" * 30)
        
        all_validation_results = []
        
        for model_result in result.successful_models:
            model_id = model_result.model_id
            sources_count = len(model_result.sources) if model_result.sources else 0
            
            # Prüfe Source Validation aus den Metadaten
            validation_data = model_result.data.get('source_validation', {})
            validation_valid = validation_data.get('valid', False)
            validation_issues = validation_data.get('issues', [])
            discovered_count = validation_data.get('discovered_count', 0)
            result_count = validation_data.get('result_count', 0)
            
            status_icon = "✅" if validation_valid else "❌"
            print(f"{status_icon} {model_id}:")
            print(f"   📋 Sources im Result: {sources_count}")
            print(f"   🔍 Discovered Sources: {discovered_count}")
            print(f"   📊 Result Sources: {result_count}")
            
            if validation_issues:
                print(f"   ⚠️  Issues: {', '.join(validation_issues)}")
            
            print()
            
            # Sammle für Gesamtbericht
            all_validation_results.append({
                'model_id': model_id,
                'valid': validation_valid,
                'issues': validation_issues,
                'sources_count': sources_count,
                'discovered_count': discovered_count,
                'result_count': result_count
            })
        
        # Gesamtbericht
        print("📋 GESAMTBERICHT:")
        print("-" * 20)
        
        total_models = len(all_validation_results)
        valid_models = sum(1 for r in all_validation_results if r['valid'])
        invalid_models = total_models - valid_models
        
        success_rate = (valid_models / max(total_models, 1)) * 100
        
        print(f"📊 Getestete Modelle: {total_models}")
        print(f"✅ Valide Modelle: {valid_models}")
        print(f"❌ Problematische Modelle: {invalid_models}")
        print(f"🎯 Erfolgsrate: {success_rate:.1f}%")
        
        # Detailanalyse der Probleme
        if invalid_models > 0:
            print()
            print("⚠️ GEFUNDENE PROBLEME:")
            print("-" * 25)
            
            for result in all_validation_results:
                if not result['valid']:
                    print(f"❌ {result['model_id']}:")
                    for issue in result['issues']:
                        print(f"   - {issue}")
                    print()
        
        # Prüfe Source Consistency zwischen Modellen
        print("🔄 QUELLEN-KONSISTENZ CHECK:")
        print("-" * 35)
        
        expected_shared_count = len(result.shared_sources)
        print(f"🎯 Erwartete Shared Sources: {expected_shared_count}")
        
        consistent_models = 0
        for result_data in all_validation_results:
            if result_data['discovered_count'] == expected_shared_count:
                consistent_models += 1
                print(f"✅ {result_data['model_id']}: {result_data['discovered_count']} sources (konsistent)")
            else:
                print(f"❌ {result_data['model_id']}: {result_data['discovered_count']} statt {expected_shared_count} sources")
        
        consistency_rate = (consistent_models / max(total_models, 1)) * 100
        print(f"📊 Konsistenz-Rate: {consistency_rate:.1f}%")
        print()
        
        # Finale Bewertung
        if success_rate >= 90 and consistency_rate >= 90:
            print("🎉 TEST ERFOLGREICH!")
            print("Alle Provider verwenden Quellenangaben konsistent.")
            return True
        elif success_rate >= 70:
            print("⚠️ TEST TEILWEISE ERFOLGREICH")
            print("Einige Provider haben noch Probleme mit Quellenangaben.")
            return False
        else:
            print("❌ TEST FEHLGESCHLAGEN")
            print("Kritische Probleme mit Quellenangaben gefunden.")
            return False
            
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {e}")
        print(f"💥 UNERWARTETER FEHLER: {e}")
        return False


async def main():
    """Hauptfunktion"""
    print("🚀 MineSearch v2.1 - Source Attribution Test")
    print("=" * 60)
    print()
    
    success = await test_source_attribution_consistency()
    
    print()
    print("=" * 60)
    if success:
        print("✅ ALLE TESTS BESTANDEN - Source Attribution funktioniert korrekt!")
    else:
        print("❌ TESTS TEILWEISE FEHLGESCHLAGEN - Reparaturen nötig!")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())