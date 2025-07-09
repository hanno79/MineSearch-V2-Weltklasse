"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Prüfe Perplexity Daten und Berechnungen
"""

import logging
from sqlalchemy import func, and_
from database import db_manager, ModelStatistics, ModelSummary, FieldStatistics, Source

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_data():
    """Prüfe die Perplexity Daten im Detail"""
    
    with db_manager.get_session() as session:
        # 1. Prüfe ModelStatistics
        logger.info("=== MODEL STATISTICS DETAILS ===")
        
        perplexity_models = ['perplexity:sonar', 'perplexity:sonar-pro']
        
        for model_id in perplexity_models:
            logger.info(f"\n{model_id}:")
            
            # Alle Stats für dieses Modell
            stats = session.query(ModelStatistics).filter_by(model_id=model_id).all()
            
            logger.info(f"  - Gesamt Einträge: {len(stats)}")
            
            # Zähle erfolgreiche Tests
            successful = [s for s in stats if s.success]
            logger.info(f"  - Erfolgreiche Tests: {len(successful)}")
            logger.info(f"  - Berechnete Erfolgsrate: {len(successful)/len(stats)*100:.1f}%")
            
            # Prüfe die ModelSummary
            summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
            if summary:
                logger.info(f"  - ModelSummary Erfolgsrate: {summary.success_rate:.1f}%")
                logger.info(f"  - ModelSummary total_tests: {summary.total_tests}")
                logger.info(f"  - ModelSummary successful_tests: {summary.successful_tests}")
                
                # Prüfe ob die Werte übereinstimmen
                if summary.total_tests != len(stats):
                    logger.warning(f"  ⚠️  WARNUNG: total_tests ({summary.total_tests}) != tatsächliche Tests ({len(stats)})")
                
                expected_rate = (summary.successful_tests / summary.total_tests * 100) if summary.total_tests > 0 else 0
                if abs(summary.success_rate - expected_rate) > 0.1:
                    logger.warning(f"  ⚠️  WARNUNG: success_rate ({summary.success_rate:.1f}%) != berechnet ({expected_rate:.1f}%)")
            
            # Zeige die letzten 5 Tests im Detail
            recent_stats = sorted(stats, key=lambda x: x.timestamp, reverse=True)[:5]
            logger.info(f"  - Letzte 5 Tests:")
            for i, stat in enumerate(recent_stats, 1):
                logger.info(f"    {i}. {stat.mine_name}: {'✅' if stat.success else '❌'} "
                           f"{stat.fields_found} Felder, Run #{stat.run_number}")
        
        # 2. Prüfe die Berechnungslogik
        logger.info("\n\n=== BERECHNUNGSLOGIK PRÜFUNG ===")
        
        # Simuliere die Berechnung für sonar
        sonar_stats = session.query(ModelStatistics).filter_by(model_id='perplexity:sonar').all()
        successful = len([s for s in sonar_stats if s.success])
        total = len(sonar_stats)
        
        logger.info(f"perplexity:sonar:")
        logger.info(f"  - Erfolgreiche: {successful}")
        logger.info(f"  - Gesamt: {total}")
        logger.info(f"  - Rate: {successful}/{total} = {successful/total*100:.1f}%")
        
        # 3. Prüfe ob es doppelte Einträge gibt
        logger.info("\n\n=== DATENINTEGRITÄT ===")
        
        # Gruppiere nach model_id, mine_name, run_number
        duplicates = session.query(
            ModelStatistics.model_id,
            ModelStatistics.mine_name,
            ModelStatistics.run_number,
            func.count(ModelStatistics.id).label('count')
        ).group_by(
            ModelStatistics.model_id,
            ModelStatistics.mine_name,
            ModelStatistics.run_number
        ).having(func.count(ModelStatistics.id) > 1).all()
        
        if duplicates:
            logger.warning("⚠️  DOPPELTE EINTRÄGE GEFUNDEN:")
            for model_id, mine_name, run_number, count in duplicates:
                logger.warning(f"  - {model_id} / {mine_name} / Run {run_number}: {count} Einträge")
        else:
            logger.info("✅ Keine doppelten Einträge gefunden")

if __name__ == "__main__":
    check_data()