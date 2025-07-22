#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.07.2025
Version: 1.0
Beschreibung: Auto-Updater für ModelSummary - Aktualisiert Summaries nach neuen Tests
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from database import db_manager
from database.models import ModelStatistics, ModelSummary
from model_summary_generator import ModelSummaryGenerator

logger = logging.getLogger(__name__)

class ModelSummaryAutoUpdater:
    """
    Automatische Aktualisierung von ModelSummary-Einträgen
    """
    
    def __init__(self):
        self.generator = ModelSummaryGenerator()
        self.logger = logger
        
    def update_after_new_tests(self, model_ids: List[str] = None) -> Dict[str, Any]:
        """
        Aktualisiert ModelSummary nach neuen Tests
        
        Args:
            model_ids: Liste der zu aktualisierenden Model-IDs (None = alle)
            
        Returns:
            Update-Report
        """
        start_time = datetime.now()
        
        try:
            with db_manager.get_session() as session:
                # Bestimme welche Models aktualisiert werden müssen
                if model_ids is None:
                    model_ids = self._find_models_needing_update(session)
                
                self.logger.info(f"🔄 Aktualisiere ModelSummary für {len(model_ids)} Models")
                
                updated_count = 0
                errors = []
                
                for model_id in model_ids:
                    try:
                        # Lösche alte Summary
                        session.query(ModelSummary).filter_by(model_id=model_id).delete()
                        
                        # Generiere neue Summary
                        new_summary = self.generator._generate_model_summary(session, model_id)
                        if new_summary:
                            session.add(new_summary)
                            updated_count += 1
                            self.logger.debug(f"✅ ModelSummary aktualisiert: {model_id}")
                        else:
                            errors.append(f"{model_id}: Keine Daten gefunden")
                            
                    except Exception as e:
                        errors.append(f"{model_id}: {str(e)}")
                        self.logger.error(f"❌ Fehler bei {model_id}: {e}")
                
                session.commit()
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": True,
                    "models_processed": len(model_ids),
                    "summaries_updated": updated_count,
                    "errors": errors,
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"💥 Kritischer Fehler bei Auto-Update: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _find_models_needing_update(self, session) -> List[str]:
        """
        Findet Models die ein Update benötigen
        """
        # Alle Models mit neuen Tests (letzten 24h)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        recent_stats = session.query(ModelStatistics.model_id).filter(
            ModelStatistics.timestamp >= cutoff_time
        ).distinct().all()
        
        model_ids = [stat.model_id for stat in recent_stats]
        
        self.logger.debug(f"🔍 {len(model_ids)} Models mit Tests in letzten 24h gefunden")
        return model_ids
    
    def update_single_model(self, model_id: str) -> Dict[str, Any]:
        """
        Aktualisiert ModelSummary für ein einzelnes Model
        
        Args:
            model_id: Model-ID (z.B. 'openai:o4-mini')
            
        Returns:
            Update-Report für einzelnes Model
        """
        try:
            with db_manager.get_session() as session:
                # Lösche alte Summary
                deleted_count = session.query(ModelSummary).filter_by(model_id=model_id).delete()
                
                # Generiere neue Summary
                new_summary = self.generator._generate_model_summary(session, model_id)
                
                if new_summary:
                    session.add(new_summary)
                    session.commit()
                    
                    self.logger.info(f"✅ ModelSummary für {model_id} aktualisiert")
                    
                    return {
                        "success": True,
                        "model_id": model_id,
                        "updated": True,
                        "previous_summary_deleted": deleted_count > 0,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    self.logger.warning(f"⚠️ Keine Daten für {model_id} gefunden")
                    return {
                        "success": False,
                        "model_id": model_id,
                        "error": "Keine Test-Daten gefunden",
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Single-Model Update {model_id}: {e}")
            return {
                "success": False,
                "model_id": model_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_summary_status(self) -> Dict[str, Any]:
        """
        Holt Status der ModelSummary-Tabelle
        """
        try:
            with db_manager.get_session() as session:
                # ModelSummary Statistiken
                total_summaries = session.query(ModelSummary).count()
                
                # ModelStatistics Statistiken
                total_stats = session.query(ModelStatistics).count()
                unique_models_in_stats = session.query(ModelStatistics.model_id).distinct().count()
                
                # Finde Models ohne Summary
                models_with_summaries = session.query(ModelSummary.model_id).all()
                summary_model_ids = {summary.model_id for summary in models_with_summaries}
                
                all_model_ids = session.query(ModelStatistics.model_id).distinct().all()
                all_model_id_set = {stat.model_id for stat in all_model_ids}
                
                missing_summaries = all_model_id_set - summary_model_ids
                
                return {
                    "total_summaries": total_summaries,
                    "total_statistics": total_stats,
                    "unique_models_in_stats": unique_models_in_stats,
                    "models_missing_summaries": list(missing_summaries),
                    "missing_count": len(missing_summaries),
                    "up_to_date": len(missing_summaries) == 0,
                    "coverage_percentage": (total_summaries / unique_models_in_stats * 100) if unique_models_in_stats > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Status-Check: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Integration Hook für ModelBenchmarkService
def auto_update_model_summary(model_id: str) -> bool:
    """
    Hook-Funktion die nach jedem Test aufgerufen werden kann
    
    Args:
        model_id: Model-ID des getesteten Models
        
    Returns:
        True wenn Update erfolgreich
    """
    try:
        updater = ModelSummaryAutoUpdater()
        result = updater.update_single_model(model_id)
        return result.get("success", False)
    except Exception as e:
        logger.error(f"❌ Auto-Update Hook fehlgeschlagen für {model_id}: {e}")
        return False


def main():
    """
    Hauptfunktion für manuellen Auto-Update
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    updater = ModelSummaryAutoUpdater()
    
    # Status-Check
    status = updater.get_summary_status()
    logger.info(f"📊 ModelSummary Status:")
    logger.info(f"   Summaries: {status.get('total_summaries', 0)}")
    logger.info(f"   Statistics: {status.get('total_statistics', 0)}")
    logger.info(f"   Coverage: {status.get('coverage_percentage', 0):.1f}%")
    
    missing = status.get('models_missing_summaries', [])
    if missing:
        logger.info(f"🔄 Aktualisiere {len(missing)} fehlende Summaries")
        result = updater.update_after_new_tests(missing)
        
        if result["success"]:
            logger.info(f"✅ Auto-Update erfolgreich!")
            logger.info(f"📊 {result['summaries_updated']} Summaries aktualisiert")
        else:
            logger.error(f"❌ Auto-Update fehlgeschlagen: {result['error']}")
    else:
        logger.info(f"✅ Alle ModelSummaries sind aktuell")


if __name__ == "__main__":
    main()