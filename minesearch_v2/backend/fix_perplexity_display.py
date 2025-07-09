"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Korrigiere Anzeige der Perplexity Benchmark-Ergebnisse
"""

import logging
from sqlalchemy import func, and_
from database import db_manager, ModelStatistics, ModelSummary, FieldStatistics, Source

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_perplexity():
    """Analysiere Perplexity Ergebnisse mit korrekter Formatierung"""
    
    with db_manager.get_session() as session:
        logger.info("=== PERPLEXITY BENCHMARK ERGEBNISSE ===\n")
        
        # 1. Modell-Zusammenfassungen
        perplexity_models = ['perplexity:sonar', 'perplexity:sonar-pro', 
                            'perplexity:sonar-deep-research', 'perplexity:sonar-reasoning']
        
        logger.info("📊 MODELL-ÜBERSICHT:")
        logger.info("-" * 70)
        
        tested_models = []
        for model_id in perplexity_models:
            summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
            
            if summary:
                tested_models.append((model_id, summary))
                logger.info(f"\n{model_id}:")
                logger.info(f"  ✅ Tests durchgeführt: {summary.total_tests}")
                logger.info(f"  ✅ Erfolgsrate: {summary.success_rate * 100:.1f}%")  # Korrigiert!
                logger.info(f"  ✅ Daten-Erfolgsrate: {summary.data_success_rate * 100:.1f}%")  # Korrigiert!
                logger.info(f"  📊 Ø Felder gefunden: {summary.avg_fields_found:.1f}")
                logger.info(f"  ⏱️  Ø Antwortzeit: {summary.avg_response_time_ms/1000:.1f}s")
                logger.info(f"  🎯 Konsistenz-Score: {summary.overall_consistency:.2f}")
            else:
                logger.info(f"\n{model_id}:")
                logger.info(f"  ❌ Noch nicht getestet")
        
        # 2. Detaillierte Validierung pro Modell/Mine
        logger.info("\n\n📍 VALIDIERUNG PRO MINE:")
        logger.info("-" * 70)
        
        mines = ['Éléonore', 'Niobec', 'LaRonde']
        
        for model_id, summary in tested_models:
            logger.info(f"\n{model_id}:")
            
            for mine in mines:
                stats = session.query(ModelStatistics).filter(
                    and_(
                        ModelStatistics.model_id == model_id,
                        ModelStatistics.mine_name == mine
                    )
                ).order_by(ModelStatistics.timestamp.desc()).all()
                
                if stats:
                    successful = len([s for s in stats if s.success])
                    avg_fields = sum(s.fields_found for s in stats) / len(stats) if stats else 0
                    
                    logger.info(f"  {mine}: {successful}/{len(stats)} Erfolge "
                               f"({successful/len(stats)*100:.0f}%), "
                               f"Ø {avg_fields:.1f} Felder")
        
        # 3. Konsistenz-Analyse
        logger.info("\n\n🎯 KONSISTENZ-ANALYSE:")
        logger.info("-" * 70)
        
        for model_id, summary in tested_models:
            if summary.critical_fields_consistency:
                logger.info(f"\n{model_id} - Kritische Felder:")
                for field, consistency in sorted(summary.critical_fields_consistency.items(), 
                                               key=lambda x: x[1], reverse=True)[:5]:
                    logger.info(f"  - {field}: {consistency:.2f} Konsistenz")
        
        # 4. Quellen-Status
        logger.info("\n\n🔗 QUELLEN-STATUS:")
        logger.info("-" * 70)
        
        total_sources = session.query(func.count(Source.id)).scalar()
        logger.info(f"\nGesamt-Quellen: {total_sources}")
        
        if total_sources >= 319:
            logger.info("✅ ZIEL ERREICHT: Alle 319 Quellen werden genutzt!")
        else:
            logger.info(f"⚠️  FORTSCHRITT: {total_sources}/319 Quellen ({total_sources/319*100:.1f}%)")
        
        # Quellen nach Typ
        source_types = session.query(
            Source.source_type,
            func.count(Source.id)
        ).group_by(Source.source_type).all()
        
        logger.info("\nQuellen nach Typ:")
        for source_type, count in sorted(source_types, key=lambda x: x[1], reverse=True):
            logger.info(f"  - {source_type}: {count}")
        
        # 5. Empfehlung
        logger.info("\n\n✨ EMPFEHLUNG:")
        logger.info("-" * 70)
        
        if tested_models:
            # Sortiere nach Erfolgsrate * Durchschnittliche Felder
            best_model = max(tested_models, 
                           key=lambda x: x[1].success_rate * x[1].avg_fields_found)
            
            logger.info(f"\nBestes Perplexity-Modell: {best_model[0]}")
            logger.info(f"  - {best_model[1].success_rate * 100:.0f}% Erfolgsrate")
            logger.info(f"  - Ø {best_model[1].avg_fields_found:.1f} Felder pro Suche")
            logger.info(f"  - {best_model[1].overall_consistency:.2f} Konsistenz-Score")
            
            # Prüfe ob deep-research und reasoning getestet wurden
            untested = [m for m in ['perplexity:sonar-deep-research', 'perplexity:sonar-reasoning']
                       if m not in [x[0] for x in tested_models]]
            
            if untested:
                logger.info(f"\n⚠️  Noch zu testen: {', '.join(untested)}")

if __name__ == "__main__":
    analyze_perplexity()