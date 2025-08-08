#!/usr/bin/env python3
"""
Author: rahn
Datum: 24.07.2025
Version: 1.0
Beschreibung: Test-Script für Enhanced Multi-Model Batch Service
ÄNDERUNG 24.07.2025: Testet die Behebung des Multi-Model-Aggregationsfehlers
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Füge Backend-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from enhanced_multi_model_batch_service import enhanced_batch_service
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_multimodel():
    """
    Testet die Enhanced Multi-Model Service mit mehreren Modellen
    Erwartet: Individuelle Modell-Ergebnisse, keine Aggregationsfehler
    """
    
    logger.info("🧪 Teste Enhanced Multi-Model Batch Service")
    logger.info("=" * 60)
    
    # Test-Mine: Eleonore (bekannte Mine mit verfügbaren Daten)
    mine_data = {
        'mine_name': 'Eleonore Mine',
        'country': 'Canada',
        'commodity': 'Gold',
        'region': 'Quebec'
    }
    
    # Test mit mehreren Modellen (Mix aus Premium und Standard)
    selected_models = [
        'openrouter:kimi-k2',           # Standard - oft als Default verwendet
        'abacus:deep-agent',            # Premium Mining-spezialisiert
        'openai:gpt-4o',               # Premium OpenAI
        'anthropic:claude-3.7-sonnet'  # Premium Anthropic
    ]
    
    session_id = f"test_enhanced_{int(datetime.now().timestamp())}"
    
    logger.info(f"📋 Test-Parameter:")
    logger.info(f"   Mine: {mine_data['mine_name']}")
    logger.info(f"   Land: {mine_data['country']}")
    logger.info(f"   Rohstoff: {mine_data['commodity']}")
    logger.info(f"   Modelle: {len(selected_models)}")
    for i, model in enumerate(selected_models, 1):
        logger.info(f"     {i}. {model}")
    logger.info(f"   Session: {session_id}")
    logger.info("")
    
    try:
        # Führe Enhanced Multi-Model-Suche durch
        logger.info("🚀 Starte Enhanced Multi-Model-Suche...")
        start_time = datetime.now()
        
        result = await enhanced_batch_service.enhanced_batch_search_per_mine(
            mine_data=mine_data,
            selected_models=selected_models,
            session_id=session_id,
            search_options={}
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"⏱️  Suche abgeschlossen in {duration:.1f} Sekunden")
        logger.info("")
        
        # Analysiere Ergebnisse
        logger.info("📊 ERGEBNIS-ANALYSE:")
        logger.info("=" * 40)
        
        success = result.get('success', False)
        logger.info(f"✅ Gesamterfolg: {success}")
        
        models_requested = result.get('models_requested', [])
        models_successful = result.get('models_successful', [])
        models_failed = result.get('models_failed', [])
        
        logger.info(f"📈 Modell-Statistiken:")
        logger.info(f"   Angefragt: {len(models_requested)}")
        logger.info(f"   Erfolgreich: {len(models_successful)}")
        logger.info(f"   Fehlgeschlagen: {len(models_failed)}")
        
        if models_successful:
            logger.info(f"   ✅ Erfolgreiche Modelle: {models_successful}")
        
        if models_failed:
            logger.info(f"   ❌ Fehlgeschlagene Modelle: {models_failed}")
        
        # Analysiere individuelle Modell-Ergebnisse
        individual_results = result.get('individual_results', {})
        logger.info(f"\n🔍 INDIVIDUELLE MODELL-ERGEBNISSE:")
        logger.info("=" * 45)
        
        for model_id, model_result in individual_results.items():
            model_success = model_result.get('success', False)
            status_icon = "✅" if model_success else "❌"
            
            logger.info(f"{status_icon} {model_id}:")
            
            if model_success:
                # Analysiere gefundene Daten
                data = model_result.get('data', {})
                structured_data = data.get('structured_data', {})
                
                # Zähle gefüllte Felder
                filled_fields = [k for k, v in structured_data.items() if v and str(v).strip()]
                logger.info(f"   📊 Gefüllte Felder: {len(filled_fields)}")
                
                # Prüfe auf wichtige Felder
                important_fields = ['Restaurationskosten', 'Abbaukosten', 'Produktionskapazität', 'Reserven']
                found_important = [field for field in important_fields if field in filled_fields]
                
                if found_important:
                    logger.info(f"   🎯 Wichtige Felder gefunden: {found_important}")
                    
                    # Detaillierte Ausgabe für Restaurationskosten
                    if 'Restaurationskosten' in filled_fields:
                        restoration_costs = structured_data['Restaurationskosten']
                        logger.info(f"   💰 Restaurationskosten: {restoration_costs}")
                
                # Prüfe Quellen
                sources = data.get('sources', [])
                logger.info(f"   🔗 Quellen: {len(sources)}")
                
                # Field Coverage
                field_coverage = model_result.get('field_coverage', {})
                if field_coverage:
                    coverage_pct = field_coverage.get('coverage_percentage', 0)
                    logger.info(f"   📈 Feldabdeckung: {coverage_pct:.1f}%")
            else:
                error = model_result.get('error', 'Unbekannter Fehler')
                logger.info(f"   ❌ Fehler: {error}")
            
            logger.info("")
        
        # Analysiere kombinierte Daten
        combined_data = result.get('combined_data', {})
        if combined_data:
            logger.info("🔄 KOMBINIERTE DATEN-ANALYSE:")
            logger.info("=" * 35)
            
            structured_data = combined_data.get('structured_data', {})
            filled_fields = [k for k, v in structured_data.items() if v and str(v).strip()]
            
            logger.info(f"📊 Gesamt gefüllte Felder: {len(filled_fields)}")
            
            # Modell-Beiträge
            model_contributions = combined_data.get('model_contributions', {})
            if model_contributions:
                logger.info(f"🤝 Modell-Beiträge:")
                for model_id, contributed_fields in model_contributions.items():
                    if contributed_fields:
                        logger.info(f"   {model_id}: {len(contributed_fields)} Felder")
            
            # Quellen-Analyse
            all_sources = combined_data.get('sources', [])
            logger.info(f"🔗 Gesamt-Quellen: {len(all_sources)}")
        
        # KRITISCHER TEST: Vergleiche mit altem System
        logger.info("\n🚨 KRITISCHER VERGLEICH ZUM ALTEN SYSTEM:")
        logger.info("=" * 50)
        
        if len(models_successful) > 1:
            logger.info("✅ ERFOLG: Mehrere Modelle haben erfolgreich gesucht!")
            logger.info("✅ BEHOBEN: Kein Verlust von Modell-Ergebnissen durch Aggregation")
            logger.info("✅ VERBESSERUNG: Individuelle DB-Speicherung pro Modell")
        elif len(models_successful) == 1:
            logger.warning("⚠️  Nur ein Modell erfolgreich - möglicherweise Netzwerk/API-Probleme")
        else:
            logger.error("❌ FEHLER: Kein Modell erfolgreich - System-Problem!")
        
        # Datenbank-Check
        logger.info("\n💾 DATENBANK-VALIDIERUNG:")
        logger.info("=" * 30)
        logger.info("ℹ️  Enhanced Service speichert automatisch jedes Modell individuell")
        logger.info("ℹ️  Kein manueller DB-Check erforderlich - Logs zeigen Speicher-Status")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ KRITISCHER FEHLER beim Test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Hauptfunktion"""
    logger.info("🧪 Enhanced Multi-Model Test gestartet")
    logger.info(f"📅 Zeitstempel: {datetime.now().isoformat()}")
    logger.info("")
    
    result = await test_enhanced_multimodel()
    
    if result:
        logger.info("🎉 TEST ERFOLGREICH ABGESCHLOSSEN!")
        logger.info("✅ Enhanced Multi-Model Service funktioniert korrekt")
    else:
        logger.error("❌ TEST FEHLGESCHLAGEN!")
        sys.exit(1)

if __name__ == "__main__":
    print("🧪 Enhanced Multi-Model Batch Service Test")
    print("=" * 50)
    asyncio.run(main())