"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Analysiere vorhandene Perplexity Benchmark-Ergebnisse aus der Datenbank
"""

import logging
from datetime import datetime
from sqlalchemy import func, and_
from database import db_manager, ModelStatistics, ModelSummary, FieldStatistics, Source

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_perplexity_results():
    """Analysiere alle Perplexity Ergebnisse in der Datenbank"""
    
    logger.info("=== ANALYSE DER PERPLEXITY BENCHMARK-ERGEBNISSE ===")
    
    with db_manager.get_session() as session:
        # 1. Überblick über alle Perplexity Modelle
        perplexity_models = ['perplexity:sonar', 'perplexity:sonar-pro', 
                            'perplexity:sonar-deep-research', 'perplexity:sonar-reasoning']
        
        logger.info("\n📊 PERPLEXITY MODELL-ZUSAMMENFASSUNGEN:")
        logger.info("="*70)
        
        for model_id in perplexity_models:
            summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
            
            if summary:
                logger.info(f"\n{model_id}:")
                logger.info(f"  - Gesamt-Tests: {summary.total_tests}")
                logger.info(f"  - Erfolgsrate: {summary.success_rate:.1f}%")
                logger.info(f"  - Daten-Erfolgsrate: {summary.data_success_rate:.1f}%")
                logger.info(f"  - Ø Felder gefunden: {summary.avg_fields_found:.1f}")
                logger.info(f"  - Ø Antwortzeit: {summary.avg_response_time_ms:.0f}ms")
                logger.info(f"  - Konsistenz-Score: {summary.overall_consistency:.2f}")
                logger.info(f"  - Letztes Update: {summary.last_updated}")
                
                # Warnung bei 0-Werten
                if summary.success_rate == 0:
                    logger.warning(f"  ⚠️  WARNUNG: Erfolgsrate ist 0%!")
                if summary.overall_consistency == 0:
                    logger.warning(f"  ⚠️  WARNUNG: Konsistenz ist 0!")
            else:
                logger.info(f"\n{model_id}: ❌ Keine Daten vorhanden")
        
        # 2. Detaillierte Statistiken pro Mine
        logger.info("\n\n📍 ERGEBNISSE PRO MINE:")
        logger.info("="*70)
        
        mines = ['Éléonore', 'Niobec', 'LaRonde']
        
        for mine in mines:
            logger.info(f"\n{mine}:")
            
            for model_id in perplexity_models:
                # Hole die letzten 5 Tests für diese Kombination
                stats = session.query(ModelStatistics).filter(
                    and_(
                        ModelStatistics.model_id == model_id,
                        ModelStatistics.mine_name == mine
                    )
                ).order_by(ModelStatistics.timestamp.desc()).limit(5).all()
                
                if stats:
                    success_count = sum(1 for s in stats if s.success)
                    avg_fields = sum(s.fields_found for s in stats) / len(stats)
                    
                    logger.info(f"  {model_id}:")
                    logger.info(f"    - Tests: {len(stats)}")
                    logger.info(f"    - Erfolge: {success_count}/{len(stats)} ({success_count/len(stats)*100:.0f}%)")
                    logger.info(f"    - Ø Felder: {avg_fields:.1f}")
                    
                    # Details der letzten Tests
                    for i, stat in enumerate(stats[:3], 1):  # Zeige nur die letzten 3
                        logger.info(f"    - Test {i}: {'✅' if stat.success else '❌'} "
                                   f"{stat.fields_found} Felder, {stat.sources_count} Quellen")
        
        # 3. Feld-Statistiken
        logger.info("\n\n📋 FELD-STATISTIKEN:")
        logger.info("="*70)
        
        for model_id in perplexity_models:
            field_stats = session.query(FieldStatistics).filter_by(
                model_id=model_id
            ).order_by(FieldStatistics.times_found.desc()).limit(10).all()
            
            if field_stats:
                logger.info(f"\n{model_id} - Top 10 gefundene Felder:")
                for fs in field_stats:
                    if fs.times_found > 0:
                        logger.info(f"  - {fs.field_name}: {fs.times_found}x gefunden")
        
        # 4. Quellen-Statistiken
        logger.info("\n\n🔗 QUELLEN-STATISTIKEN:")
        logger.info("="*70)
        
        total_sources = session.query(func.count(Source.id)).scalar()
        logger.info(f"Gesamt-Quellen in Datenbank: {total_sources}")
        
        # Prüfe ob 319 Quellen erreicht
        if total_sources >= 319:
            logger.info("✅ ALLE 319 QUELLEN WERDEN GENUTZT!")
        else:
            logger.warning(f"⚠️  NUR {total_sources} VON 319 QUELLEN WERDEN GENUTZT!")
        
        # Top Quellen nach Zuverlässigkeit
        top_sources = session.query(Source).order_by(
            Source.reliability_score.desc()
        ).limit(5).all()
        
        logger.info("\nTop 5 zuverlässigste Quellen:")
        for i, source in enumerate(top_sources, 1):
            logger.info(f"  {i}. {source.domain} ({source.source_type})")
            logger.info(f"     - Score: {source.reliability_score:.1f}")
            logger.info(f"     - Erfolge: {source.successful_searches}/{source.total_searches}")
        
        # 5. Zusammenfassung und Empfehlungen
        logger.info("\n\n🎯 ZUSAMMENFASSUNG UND EMPFEHLUNGEN:")
        logger.info("="*70)
        
        # Beste Modelle nach Erfolgsrate
        best_models = session.query(
            ModelSummary.model_id,
            ModelSummary.success_rate,
            ModelSummary.avg_fields_found,
            ModelSummary.overall_consistency
        ).filter(
            ModelSummary.model_id.like('perplexity:%')
        ).order_by(
            ModelSummary.success_rate.desc(),
            ModelSummary.avg_fields_found.desc()
        ).all()
        
        if best_models:
            logger.info("\nModell-Ranking nach Erfolgsrate:")
            for i, (model_id, success_rate, avg_fields, consistency) in enumerate(best_models, 1):
                logger.info(f"  {i}. {model_id}: {success_rate:.0f}% Erfolg, "
                           f"{avg_fields:.1f} Felder, {consistency:.2f} Konsistenz")
            
            # Empfehlung
            best_model = best_models[0]
            logger.info(f"\n✨ EMPFEHLUNG: {best_model[0]} ist das beste Perplexity-Modell!")
            logger.info(f"   Mit {best_model[1]:.0f}% Erfolgsrate und durchschnittlich "
                       f"{best_model[2]:.1f} gefundenen Feldern.")

if __name__ == "__main__":
    analyze_perplexity_results()