#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.07.2025
Version: 1.0
Beschreibung: Test der beiden problematischen Models einzeln
"""

import logging
from datetime import datetime
from model_summary_generator import ModelSummaryGenerator
from database import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_problem_models():
    """
    Testet die beiden Models die vorher Fehler verursacht haben
    """
    problem_models = ['tavily-search', 'perplexity:sonar-reasoning']
    
    logger.info("🔧 TESTE PROBLEMATISCHE MODELS")
    logger.info("="*50)
    
    generator = ModelSummaryGenerator()
    
    for model_id in problem_models:
        logger.info(f"\n🧪 TESTE MODEL: {model_id}")
        logger.info("-" * 30)
        
        try:
            with db_manager.get_session() as session:
                # Teste einzelne Summary-Generierung
                summary = generator._generate_model_summary(session, model_id)
                
                if summary:
                    logger.info(f"✅ Summary erfolgreich generiert!")
                    logger.info(f"   Model ID: {summary.model_id}")
                    logger.info(f"   Total Tests: {summary.total_tests}")
                    logger.info(f"   Success Rate: {summary.success_rate:.1%}")
                    logger.info(f"   Avg Fields: {summary.avg_fields_found:.1f}")
                    logger.info(f"   Avg Sources: {summary.avg_sources_count:.1f}")
                    logger.info(f"   Consistency: {summary.overall_consistency:.1%}")
                    
                    # Teste ob wir es in DB speichern können
                    session.add(summary)
                    session.commit()
                    logger.info(f"✅ Erfolgreich in Database gespeichert!")
                    
                else:
                    logger.warning(f"⚠️ Keine Summary generiert - keine Daten gefunden")
                    
        except Exception as e:
            logger.error(f"❌ Fehler bei {model_id}: {e}")
            return False
    
    logger.info(f"\n🎉 ALLE PROBLEM-MODELS ERFOLGREICH GETESTET!")
    return True

def run_full_regeneration():
    """
    Führt vollständige Regenerierung aller Models durch
    """
    logger.info(f"\n🔄 VOLLSTÄNDIGE REGENERIERUNG ALLER MODELS")
    logger.info("="*50)
    
    generator = ModelSummaryGenerator()
    result = generator.generate_all_model_summaries()
    
    if result["success"]:
        logger.info(f"✅ Regenerierung erfolgreich!")
        logger.info(f"📊 {result['summaries_generated']} von {result['total_models_processed']} Models generiert")
        logger.info(f"💾 {result['summaries_in_database']} Summaries in Database")
        
        if result['summaries_generated'] == result['total_models_processed']:
            logger.info(f"🎯 PERFEKT: Alle Models erfolgreich generiert!")
            return True
        else:
            logger.warning(f"⚠️ {result['total_models_processed'] - result['summaries_generated']} Models konnten nicht generiert werden")
            return False
    else:
        logger.error(f"❌ Regenerierung fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
        return False

if __name__ == "__main__":
    logger.info(f"🕒 Test Time: {datetime.now().isoformat()}")
    
    # Teste problematische Models einzeln
    individual_success = test_problem_models()
    
    # Führe vollständige Regenerierung durch
    full_success = run_full_regeneration()
    
    logger.info(f"\n" + "="*60)
    if individual_success and full_success:
        logger.info(f"🎯 VOLLSTÄNDIGER ERFOLG - Alle Models repariert!")
        logger.info(f"🎉 39/39 Models sollten jetzt verfügbar sein")
    else:
        logger.warning(f"⚠️ Nicht alle Tests erfolgreich - weitere Debugging erforderlich")