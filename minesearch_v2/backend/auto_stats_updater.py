#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Automatischer Statistics-Updater für ModelStatistics nach jeder realen Suche
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from database import db_manager
from database.models import ModelStatistics, ModelSummary
from model_summary_auto_updater import ModelSummaryAutoUpdater

logger = logging.getLogger(__name__)

class AutoStatsUpdater:
    """
    Automatische Aktualisierung von ModelStatistics nach jeder realen Suche
    """
    
    def __init__(self):
        self.summary_updater = ModelSummaryAutoUpdater()
        self.logger = logger
        
    async def update_statistics_after_search(self, 
                                           mine_name: str,
                                           model_used: str, 
                                           search_result: Dict[str, Any],
                                           response_time_ms: Optional[float] = None,
                                           country: Optional[str] = None,
                                           commodity: Optional[str] = None,
                                           region: Optional[str] = None) -> Dict[str, Any]:
        """
        Aktualisiert ModelStatistics nach einer realen Suche
        
        Args:
            mine_name: Name der Mine
            model_used: Verwendetes Modell (z.B. 'openrouter:deepseek-free')
            search_result: Suchergebnis-Dictionary
            response_time_ms: Antwortzeit in Millisekunden
            country: Land (optional)
            commodity: Rohstoff (optional)
            region: Region (optional)
            
        Returns:
            Update-Report
        """
        start_time = datetime.now()
        
        try:
            # Extrahiere Informationen aus search_result
            success = search_result.get('success', False)
            structured_data = search_result.get('data', {}).get('structured_data', {})
            sources = search_result.get('data', {}).get('sources', [])
            error_message = search_result.get('error', None) if not success else None
            
            # Berechne Metriken
            fields_found = self._count_filled_fields(structured_data)
            sources_count = len(sources) if sources else 0
            
            # Bestimme run_number (für reale Suchen immer 1)
            run_number = 1
            
            # Erstelle ModelStatistics Eintrag
            with db_manager.get_session() as session:
                model_stat = ModelStatistics(
                    model_id=model_used,
                    mine_name=mine_name,
                    country=country,
                    region=region,
                    commodity=commodity,
                    run_number=run_number,
                    timestamp=datetime.now(),
                    success=success,
                    response_time_ms=response_time_ms,
                    fields_found=fields_found,
                    sources_count=sources_count,
                    raw_result=search_result,
                    structured_data=structured_data,
                    error_message=error_message
                )
                
                session.add(model_stat)
                session.commit()
                
                stat_id = model_stat.id
            
            self.logger.info(f"✅ ModelStatistics aktualisiert für {model_used}/{mine_name} (ID: {stat_id})")
            
            # Trigger ModelSummary Update für dieses Modell
            summary_result = await self._trigger_summary_update(model_used)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "model_statistics_id": stat_id,
                "model_id": model_used,
                "mine_name": mine_name,
                "fields_found": fields_found,
                "sources_count": sources_count,
                "summary_updated": summary_result.get("success", False),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Auto-Update für {model_used}/{mine_name}: {e}")
            return {
                "success": False,
                "model_id": model_used,
                "mine_name": mine_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def batch_update_statistics(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch-Update für mehrere Suchergebnisse (z.B. aus Batch-Services)
        
        Args:
            search_results: Liste von Suchergebnis-Dictionaries mit Metadaten
            
        Returns:
            Batch-Update-Report
        """
        start_time = datetime.now()
        
        try:
            successful_updates = 0
            failed_updates = 0
            updated_models = set()
            errors = []
            
            for result_data in search_results:
                try:
                    update_result = await self.update_statistics_after_search(
                        mine_name=result_data.get('mine_name'),
                        model_used=result_data.get('model_used'),
                        search_result=result_data.get('search_result', {}),
                        response_time_ms=result_data.get('response_time_ms'),
                        country=result_data.get('country'),
                        commodity=result_data.get('commodity'),
                        region=result_data.get('region')
                    )
                    
                    if update_result.get('success'):
                        successful_updates += 1
                        updated_models.add(result_data.get('model_used'))
                    else:
                        failed_updates += 1
                        errors.append(f"{result_data.get('model_used')}/{result_data.get('mine_name')}: {update_result.get('error')}")
                        
                except Exception as e:
                    failed_updates += 1
                    errors.append(f"Batch-Item-Fehler: {str(e)}")
            
            # Batch-Update für ModelSummaries der aktualisierten Modelle
            summary_updates = await self._batch_summary_update(list(updated_models))
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "total_results": len(search_results),
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "updated_models": list(updated_models),
                "summary_updates": summary_updates,
                "errors": errors,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Batch-Update: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _count_filled_fields(self, structured_data: Dict[str, Any]) -> int:
        """
        Zählt die gefüllten Felder in structured_data
        
        WICHTIG: "X" bedeutet "keine Daten gefunden" und zählt als LEER!
        """
        if not structured_data:
            return 0
        
        filled_count = 0
        for key, value in structured_data.items():
            # Skip interne Felder
            if key.startswith('_'):
                continue
                
            # Prüfe ob Wert tatsächlich gefüllt ist
            if value is not None and value != "" and value != [] and value != {}:
                # BUGFIX 26.07.2025: "X" bedeutet "keine Daten gefunden"
                if isinstance(value, str) and value.strip() == "X":
                    continue  # "X" zählt als leer
                
                # Für komplexe Werte prüfen ob sie Inhalt haben
                if isinstance(value, (list, dict)):
                    if value:  # Nicht leer
                        filled_count += 1
                else:
                    filled_count += 1
        
        return filled_count
    
    async def _trigger_summary_update(self, model_id: str) -> Dict[str, Any]:
        """
        Triggert ModelSummary Update für ein spezifisches Modell
        """
        try:
            return self.summary_updater.update_single_model(model_id)
        except Exception as e:
            self.logger.warning(f"⚠️ Summary-Update fehlgeschlagen für {model_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _batch_summary_update(self, model_ids: List[str]) -> Dict[str, Any]:
        """
        Batch-Update für ModelSummaries mehrerer Modelle
        """
        try:
            return self.summary_updater.update_after_new_tests(model_ids)
        except Exception as e:
            self.logger.warning(f"⚠️ Batch-Summary-Update fehlgeschlagen: {e}")
            return {"success": False, "error": str(e)}
    
    def get_recent_statistics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Holt eine Zusammenfassung der kürzlich aktualisierten Statistiken
        
        Args:
            hours: Zeitraum in Stunden
            
        Returns:
            Zusammenfassung der Recent Statistics
        """
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with db_manager.get_session() as session:
                recent_stats = session.query(ModelStatistics).filter(
                    ModelStatistics.timestamp >= cutoff_time
                ).all()
                
                if not recent_stats:
                    return {
                        "total_searches": 0,
                        "successful_searches": 0,
                        "unique_models": 0,
                        "unique_mines": 0,
                        "hours_analyzed": hours
                    }
                
                # Aggregiere Daten
                successful_searches = len([s for s in recent_stats if s.success])
                unique_models = len(set(s.model_id for s in recent_stats))
                unique_mines = len(set(s.mine_name for s in recent_stats))
                
                # Modell-Performance
                model_performance = {}
                for stat in recent_stats:
                    if stat.model_id not in model_performance:
                        model_performance[stat.model_id] = {
                            'total': 0,
                            'successful': 0,
                            'avg_fields': 0,
                            'avg_response_time': 0
                        }
                    
                    perf = model_performance[stat.model_id]
                    perf['total'] += 1
                    if stat.success:
                        perf['successful'] += 1
                    perf['avg_fields'] += stat.fields_found
                    if stat.response_time_ms:
                        perf['avg_response_time'] += stat.response_time_ms
                
                # Berechne Durchschnitte
                for model_id, perf in model_performance.items():
                    perf['success_rate'] = (perf['successful'] / perf['total']) * 100
                    perf['avg_fields'] = perf['avg_fields'] / perf['total']
                    perf['avg_response_time'] = (perf['avg_response_time'] / perf['total']) if perf['avg_response_time'] > 0 else 0
                
                return {
                    "total_searches": len(recent_stats),
                    "successful_searches": successful_searches,
                    "success_rate": (successful_searches / len(recent_stats)) * 100,
                    "unique_models": unique_models,
                    "unique_mines": unique_mines,
                    "hours_analyzed": hours,
                    "model_performance": model_performance,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Recent Statistics Summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Globale Instanz für die Services
auto_stats_updater = AutoStatsUpdater()


def main():
    """
    Hauptfunktion für Tests und manuellen Betrieb
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test Recent Statistics Summary
    updater = AutoStatsUpdater()
    summary = updater.get_recent_statistics_summary(hours=24)
    
    logger.info("📊 Recent Statistics Summary (24h):")
    logger.info(f"   Total Searches: {summary.get('total_searches', 0)}")
    logger.info(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
    logger.info(f"   Unique Models: {summary.get('unique_models', 0)}")
    logger.info(f"   Unique Mines: {summary.get('unique_mines', 0)}")


if __name__ == "__main__":
    main()