#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.07.2025
Version: 1.0
Beschreibung: ModelSummary Generator - Aggregiert ModelStatistics zu ModelSummary für Frontend-Statistics
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import statistics

from database import db_manager
from database.models import ModelStatistics, ModelSummary

logger = logging.getLogger(__name__)

class ModelSummaryGenerator:
    """
    Generiert ModelSummary-Einträge aus ModelStatistics-Daten
    """
    
    def __init__(self):
        self.logger = logger
        
    def generate_all_model_summaries(self) -> Dict[str, Any]:
        """
        Generiert ModelSummary für alle verfügbaren Models
        
        Returns:
            Report über generierte Summaries
        """
        start_time = datetime.now()
        
        try:
            with db_manager.get_session() as session:
                # Lösche existierende ModelSummaries
                session.query(ModelSummary).delete()
                session.commit()
                
                # Hole alle unique Model-IDs
                unique_models = session.query(ModelStatistics.model_id).distinct().all()
                model_ids = [model.model_id for model in unique_models]
                
                self.logger.info(f"🔄 Generiere ModelSummary für {len(model_ids)} Models")
                
                generated_count = 0
                
                for model_id in model_ids:
                    try:
                        summary = self._generate_model_summary(session, model_id)
                        if summary:
                            session.add(summary)
                            generated_count += 1
                            self.logger.debug(f"✅ ModelSummary generiert für: {model_id}")
                        else:
                            self.logger.warning(f"⚠️ Keine Daten für Model: {model_id}")
                            
                    except Exception as e:
                        self.logger.error(f"❌ Fehler bei {model_id}: {e}")
                
                session.commit()
                
                # Validierung
                total_summaries = session.query(ModelSummary).count()
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": True,
                    "total_models_processed": len(model_ids),
                    "summaries_generated": generated_count,
                    "summaries_in_database": total_summaries,
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"💥 Kritischer Fehler bei ModelSummary-Generierung: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_model_summary(self, session, model_id: str) -> ModelSummary:
        """
        Generiert ModelSummary für einzelnes Model
        
        Args:
            session: Database-Session
            model_id: Model-ID (z.B. 'openai:o4-mini')
            
        Returns:
            ModelSummary-Objekt oder None
        """
        # Hole alle Tests für dieses Model
        stats = session.query(ModelStatistics).filter_by(model_id=model_id).all()
        
        if not stats:
            return None
            
        # Grundlegende Statistiken
        total_tests = len(stats)
        successful_tests = [s for s in stats if s.success]
        successful_count = len(successful_tests)
        
        if successful_count == 0:
            success_rate = 0.0
            avg_response_time = 0.0
            avg_fields_found = 0.0
            avg_sources_count = 0.0
        else:
            success_rate = successful_count / total_tests
            avg_response_time = sum(getattr(s, 'response_time_ms', 0) or 0 for s in successful_tests) / successful_count
            avg_fields_found = sum(getattr(s, 'fields_found', 0) or 0 for s in successful_tests) / successful_count
            avg_sources_count = sum(getattr(s, 'sources_count', 0) or 0 for s in successful_tests) / successful_count
        
        # Erweiterte Metriken
        mine_stats = self._calculate_mine_statistics(stats)
        consistency_metrics = self._calculate_consistency_metrics(stats)
        performance_metrics = self._calculate_performance_metrics(stats)
        
        # Data-Erfolgsrate (Models die tatsächlich Felder gefunden haben)
        data_successful_tests = [s for s in successful_tests if getattr(s, 'fields_found', 0) > 0]
        data_success_rate = len(data_successful_tests) / total_tests if total_tests > 0 else 0.0
        
        return ModelSummary(
            model_id=model_id,
            total_tests=total_tests,
            total_mines_tested=mine_stats['mine_count'],
            avg_response_time_ms=avg_response_time,
            avg_fields_found=avg_fields_found,
            avg_sources_count=avg_sources_count,
            success_rate=success_rate,
            data_success_rate=data_success_rate,
            overall_consistency=consistency_metrics['overall_consistency'],
            critical_fields_consistency=consistency_metrics['field_details']
        )
    
    def _calculate_mine_statistics(self, stats: List[ModelStatistics]) -> Dict[str, Any]:
        """
        Berechnet Mine-spezifische Statistiken
        """
        mine_names = list(set(getattr(s, 'mine_name', '') for s in stats if getattr(s, 'mine_name', '')))
        mine_count = len(mine_names)
        
        return {
            "mine_names": mine_names,
            "mine_count": mine_count
        }
    
    def _calculate_consistency_metrics(self, stats: List[ModelStatistics]) -> Dict[str, float]:
        """
        Berechnet Konsistenz-Metriken
        """
        if not stats:
            field_details = {
                "field_consistency": 0.0,
                "source_consistency": 0.0,
                "calculation_timestamp": datetime.now().isoformat(),
                "note": "No statistics available"
            }
            return {
                "overall_consistency": 0.0,
                "field_consistency": 0.0,
                "source_consistency": 0.0,
                "field_details": field_details
            }
        
        successful_tests = [s for s in stats if s.success]
        
        if not successful_tests:
            field_details = {
                "field_consistency": 0.0,
                "source_consistency": 0.0,
                "calculation_timestamp": datetime.now().isoformat(),
                "note": "No successful tests available"
            }
            return {
                "overall_consistency": 0.0,
                "field_consistency": 0.0,
                "source_consistency": 0.0,
                "field_details": field_details
            }
        
        # Feld-Konsistenz: Standardabweichung der gefundenen Felder
        fields_found = [getattr(s, 'fields_found', 0) for s in successful_tests]
        field_consistency = 1.0 - (statistics.stdev(fields_found) / max(fields_found)) if len(fields_found) > 1 and max(fields_found) > 0 else 1.0
        field_consistency = max(0.0, min(1.0, field_consistency))  # Clamp zwischen 0 und 1
        
        # Quellen-Konsistenz: Standardabweichung der Quellen-Anzahl
        sources_counts = [getattr(s, 'sources_count', 0) for s in successful_tests if getattr(s, 'sources_count', None) is not None]
        if sources_counts and len(sources_counts) > 1 and max(sources_counts) > 0:
            source_consistency = 1.0 - (statistics.stdev(sources_counts) / max(sources_counts))
            source_consistency = max(0.0, min(1.0, source_consistency))
        else:
            source_consistency = 1.0
        
        # Gesamt-Konsistenz: Gewichteter Durchschnitt
        overall_consistency = (field_consistency * 0.7) + (source_consistency * 0.3)
        
        # Critical Fields Details für JSON-Spalte
        field_details = {
            "field_consistency": field_consistency,
            "source_consistency": source_consistency,
            "calculation_timestamp": datetime.now().isoformat()
        }
        
        return {
            "overall_consistency": overall_consistency,
            "field_consistency": field_consistency,
            "source_consistency": source_consistency,
            "field_details": field_details
        }
    
    def _calculate_performance_metrics(self, stats: List[ModelStatistics]) -> Dict[str, Any]:
        """
        Berechnet Performance-Tier basierend auf Erfolgsrate und Feld-Anzahl
        """
        successful_tests = [s for s in stats if s.success]
        
        if not successful_tests:
            return {"tier": "unknown"}
        
        success_rate = len(successful_tests) / len(stats)
        avg_fields = sum(getattr(s, 'fields_found', 0) for s in successful_tests) / len(successful_tests)
        
        # Performance-Tier Logic
        if success_rate >= 0.9 and avg_fields >= 12:
            tier = "tier1_enterprise"
        elif success_rate >= 0.8 and avg_fields >= 9:
            tier = "tier2_production"
        elif success_rate >= 0.6 and avg_fields >= 6:
            tier = "tier3_development"
        else:
            tier = "tier4_experimental"
        
        return {"tier": tier}


def main():
    """
    Hauptfunktion für ModelSummary-Generierung
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 MODELSUMMARY GENERATOR GESTARTET")
    
    generator = ModelSummaryGenerator()
    
    try:
        report = generator.generate_all_model_summaries()
        
        if report["success"]:
            logger.info(f"✅ ModelSummary-Generierung erfolgreich!")
            logger.info(f"📊 {report['summaries_generated']} Summaries generiert")
            logger.info(f"💾 {report['summaries_in_database']} Summaries in Database")
            logger.info(f"⏱️  Dauer: {report['duration_seconds']:.1f} Sekunden")
        else:
            logger.error(f"❌ ModelSummary-Generierung fehlgeschlagen: {report['error']}")
            
    except Exception as e:
        logger.error(f"💥 Kritischer Fehler: {e}")


if __name__ == "__main__":
    main()