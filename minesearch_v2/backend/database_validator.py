"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Umfassende Datenbank-Validierung für Provider-Tests
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import re

from database import db_manager
from database.models import ModelStatistics, FieldStatistics, FieldConsistency, Source, ModelSummary
from config import CSV_COLUMNS

logger = logging.getLogger(__name__)


class DatabaseValidator:
    """Validator für umfassende Datenbank-Konsistenz-Prüfungen"""
    
    def __init__(self):
        self.validation_start = None
        self.critical_fields = [
            'Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate', 
            'Aktivitätsstatus', 'Restaurationskosten'
        ]
        
        # Dummy-Werte die als ungültig gelten
        self.dummy_patterns = {
            'generic_dummies': [
                r'^\$[0-9]+$',  # $1, $2, etc.
                r'^(n/a|k\.a\.?|keine\s+(angabe|daten)|unbekannt|nicht\s+verfügbar)$',
                r'^company\s+[a-z]$',  # Company A, Company B
                r'^mine\s+operator$',
                r'^unknown\s+company$',
                r'^(null|none|undefined)$',
                r'^0+(\.0+)?$',  # 0, 0.0, 000
            ],
            'coordinate_patterns': [
                r'^[0-9]+\.[0-9]+$',  # Nur Zahlen ohne Kontext
                r'^-?[0-9]{1,2}\.[0-9]+$',  # Verdächtig einfache Koordinaten
            ],
            'cost_patterns': [
                r'^\$[0-9]+$',  # $1, $2 als Kosten
                r'^[0-9]+\s*\$$',  # 123$ Format
            ]
        }
    
    async def validate_comprehensive(self, models_to_check: Optional[List[str]] = None,
                                   mines_to_check: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Führt umfassende Datenbank-Validierung durch
        
        Args:
            models_to_check: Spezifische Modelle oder None für alle
            mines_to_check: Spezifische Minen oder None für alle
            
        Returns:
            Umfassende Validierungs-Ergebnisse
        """
        self.validation_start = datetime.now()
        logger.info("[DB-VALIDATOR] Starte umfassende Datenbank-Validierung")
        
        validation_results = {
            "timestamp": self.validation_start.isoformat(),
            "scope": {
                "models_checked": models_to_check or "all",
                "mines_checked": mines_to_check or "all"
            },
            "statistics_validation": {},
            "consistency_validation": {},
            "data_quality_validation": {},
            "plausibility_checks": {},
            "issues_summary": {
                "critical": [],
                "warnings": [],
                "info": []
            },
            "overall_status": "UNKNOWN"
        }
        
        try:
            # 1. ModelStatistics Validierung
            validation_results["statistics_validation"] = await self._validate_model_statistics(models_to_check, mines_to_check)
            
            # 2. FieldStatistics Validierung
            validation_results["field_statistics_validation"] = await self._validate_field_statistics(models_to_check)
            
            # 3. FieldConsistency Validierung
            validation_results["consistency_validation"] = await self._validate_field_consistency(models_to_check, mines_to_check)
            
            # 4. Datenqualitäts-Validierung
            validation_results["data_quality_validation"] = await self._validate_data_quality(models_to_check, mines_to_check)
            
            # 5. Plausibilitäts-Prüfungen
            validation_results["plausibility_checks"] = await self._validate_data_plausibility(models_to_check, mines_to_check)
            
            # 6. Quellen-Validierung
            validation_results["sources_validation"] = await self._validate_sources()
            
            # 7. Sammle alle Issues
            self._collect_all_issues(validation_results)
            
            # 8. Bestimme Overall-Status
            validation_results["overall_status"] = self._determine_overall_status(validation_results)
            
            duration = (datetime.now() - self.validation_start).total_seconds()
            validation_results["validation_duration_seconds"] = duration
            
            logger.info(f"[DB-VALIDATOR] Validierung abgeschlossen in {duration:.1f}s - Status: {validation_results['overall_status']}")
            
        except Exception as e:
            validation_results["error"] = str(e)
            validation_results["overall_status"] = "ERROR"
            logger.error(f"[DB-VALIDATOR] Kritischer Fehler bei Validierung: {e}")
        
        return validation_results
    
    async def _validate_model_statistics(self, models: Optional[List[str]], mines: Optional[List[str]]) -> Dict[str, Any]:
        """
        Validiert ModelStatistics Tabelle
        """
        validation = {
            "total_entries": 0,
            "entries_by_model": {},
            "entries_by_mine": {},
            "missing_run_numbers": [],
            "invalid_timestamps": [],
            "zero_response_times": [],
            "success_rates": {},
            "issues": []
        }
        
        try:
            with db_manager.get_session() as session:
                # Basis-Query
                query = session.query(ModelStatistics)
                if models:
                    query = query.filter(ModelStatistics.model_id.in_(models))
                if mines:
                    query = query.filter(ModelStatistics.mine_name.in_(mines))
                
                all_stats = query.all()
                validation["total_entries"] = len(all_stats)
                
                # Gruppiere nach Modell
                for stat in all_stats:
                    model_id = stat.model_id
                    if model_id not in validation["entries_by_model"]:
                        validation["entries_by_model"][model_id] = 0
                    validation["entries_by_model"][model_id] += 1
                
                # Gruppiere nach Mine
                for stat in all_stats:
                    mine_name = stat.mine_name
                    if mine_name not in validation["entries_by_mine"]:
                        validation["entries_by_mine"][mine_name] = 0
                    validation["entries_by_mine"][mine_name] += 1
                
                # Prüfe run_numbers pro Modell/Mine-Kombination
                model_mine_combinations = defaultdict(list)
                for stat in all_stats:
                    key = f"{stat.model_id}:{stat.mine_name}"
                    model_mine_combinations[key].append(stat.run_number)
                
                for combination, run_numbers in model_mine_combinations.items():
                    expected_runs = set(range(1, 6))  # 1-5
                    actual_runs = set(run_numbers)
                    if expected_runs != actual_runs:
                        missing = expected_runs - actual_runs
                        validation["missing_run_numbers"].append({
                            "combination": combination,
                            "missing_runs": list(missing),
                            "actual_runs": sorted(run_numbers)
                        })
                
                # Prüfe Timestamps
                for stat in all_stats:
                    if not stat.timestamp:
                        validation["invalid_timestamps"].append(f"{stat.model_id}:{stat.mine_name}:run{stat.run_number}")
                    elif stat.timestamp < datetime.now() - timedelta(days=30):
                        validation["issues"].append(f"Sehr alter Timestamp: {stat.model_id}:{stat.mine_name} vom {stat.timestamp}")
                
                # Prüfe Response-Zeiten
                for stat in all_stats:
                    if stat.success and stat.response_time_ms <= 0:
                        validation["zero_response_times"].append(f"{stat.model_id}:{stat.mine_name}:run{stat.run_number}")
                
                # Berechne Erfolgsraten
                for model_id in set(stat.model_id for stat in all_stats):
                    model_stats = [s for s in all_stats if s.model_id == model_id]
                    successful = len([s for s in model_stats if s.success])
                    validation["success_rates"][model_id] = {
                        "total": len(model_stats),
                        "successful": successful,
                        "rate": successful / len(model_stats) if model_stats else 0
                    }
                
        except Exception as e:
            validation["error"] = str(e)
            logger.error(f"[DB-VALIDATOR] Fehler bei ModelStatistics Validierung: {e}")
        
        return validation
    
    async def _validate_field_statistics(self, models: Optional[List[str]]) -> Dict[str, Any]:
        """
        Validiert FieldStatistics Tabelle
        """
        validation = {
            "total_entries": 0,
            "fields_by_model": {},
            "zero_success_fields": [],
            "inconsistent_calculations": [],
            "missing_critical_fields": [],
            "issues": []
        }
        
        try:
            with db_manager.get_session() as session:
                query = session.query(FieldStatistics)
                if models:
                    query = query.filter(FieldStatistics.model_id.in_(models))
                
                all_field_stats = query.all()
                validation["total_entries"] = len(all_field_stats)
                
                # Gruppiere nach Modell
                for field_stat in all_field_stats:
                    model_id = field_stat.model_id
                    if model_id not in validation["fields_by_model"]:
                        validation["fields_by_model"][model_id] = []
                    validation["fields_by_model"][model_id].append(field_stat.field_name)
                
                # Prüfe auf Felder mit 0% Erfolgsrate
                for field_stat in all_field_stats:
                    if field_stat.success_rate == 0.0 and field_stat.total_searches > 0:
                        validation["zero_success_fields"].append({
                            "model_id": field_stat.model_id,
                            "field_name": field_stat.field_name,
                            "total_searches": field_stat.total_searches
                        })
                
                # Prüfe Berechnungs-Konsistenz
                for field_stat in all_field_stats:
                    if field_stat.total_searches > 0:
                        calculated_rate = field_stat.times_found / field_stat.total_searches
                        if abs(calculated_rate - field_stat.success_rate) > 0.01:  # 1% Toleranz
                            validation["inconsistent_calculations"].append({
                                "model_id": field_stat.model_id,
                                "field_name": field_stat.field_name,
                                "stored_rate": field_stat.success_rate,
                                "calculated_rate": calculated_rate
                            })
                
                # Prüfe fehlende kritische Felder
                for model_id in set(fs.model_id for fs in all_field_stats):
                    model_fields = set(fs.field_name for fs in all_field_stats if fs.model_id == model_id)
                    missing_critical = set(self.critical_fields) - model_fields
                    if missing_critical:
                        validation["missing_critical_fields"].append({
                            "model_id": model_id,
                            "missing_fields": list(missing_critical)
                        })
                
        except Exception as e:
            validation["error"] = str(e)
            logger.error(f"[DB-VALIDATOR] Fehler bei FieldStatistics Validierung: {e}")
        
        return validation
    
    async def _validate_field_consistency(self, models: Optional[List[str]], mines: Optional[List[str]]) -> Dict[str, Any]:
        """
        Validiert FieldConsistency Tabelle
        """
        validation = {
            "total_entries": 0,
            "consistency_scores": {},
            "inconsistent_fields": [],
            "missing_consistency_data": [],
            "issues": []
        }
        
        try:
            with db_manager.get_session() as session:
                query = session.query(FieldConsistency)
                if models:
                    query = query.filter(FieldConsistency.model_id.in_(models))
                if mines:
                    query = query.filter(FieldConsistency.mine_name.in_(mines))
                
                all_consistency = query.all()
                validation["total_entries"] = len(all_consistency)
                
                # Analysiere Konsistenz-Scores
                for cons in all_consistency:
                    field_key = f"{cons.model_id}:{cons.field_name}"
                    validation["consistency_scores"][field_key] = cons.consistency_score
                    
                    # Prüfe auf inkonsistente Felder
                    if cons.consistency_score < 0.7 and cons.total_runs >= 3:
                        validation["inconsistent_fields"].append({
                            "model_id": cons.model_id,
                            "field_name": cons.field_name,
                            "mine_name": cons.mine_name,
                            "consistency_score": cons.consistency_score,
                            "total_runs": cons.total_runs
                        })
                
                # Prüfe auf fehlende Konsistenz-Daten für Modell/Mine-Kombinationen
                if models and mines:
                    for model_id in models:
                        for mine_name in mines:
                            model_mine_consistency = [
                                c for c in all_consistency 
                                if c.model_id == model_id and c.mine_name == mine_name
                            ]
                            if len(model_mine_consistency) < len(self.critical_fields):
                                validation["missing_consistency_data"].append({
                                    "model_id": model_id,
                                    "mine_name": mine_name,
                                    "consistency_entries": len(model_mine_consistency)
                                })
                
        except Exception as e:
            validation["error"] = str(e)
            logger.error(f"[DB-VALIDATOR] Fehler bei FieldConsistency Validierung: {e}")
        
        return validation
    
    async def _validate_data_quality(self, models: Optional[List[str]], mines: Optional[List[str]]) -> Dict[str, Any]:
        """
        Validiert Datenqualität durch Dummy-Wert-Erkennung
        """
        validation = {
            "total_checked": 0,
            "dummy_values_found": [],
            "suspicious_patterns": [],
            "quality_scores": {},
            "issues": []
        }
        
        try:
            with db_manager.get_session() as session:
                query = session.query(ModelStatistics).filter_by(success=True)
                if models:
                    query = query.filter(ModelStatistics.model_id.in_(models))
                if mines:
                    query = query.filter(ModelStatistics.mine_name.in_(mines))
                
                successful_stats = query.all()
                validation["total_checked"] = len(successful_stats)
                
                for stat in successful_stats:
                    if stat.structured_data:
                        # Prüfe jedes Feld auf Dummy-Werte
                        for field_name, value in stat.structured_data.items():
                            if value and str(value).strip():
                                value_str = str(value).strip()
                                
                                # Prüfe verschiedene Dummy-Pattern
                                for pattern_type, patterns in self.dummy_patterns.items():
                                    for pattern in patterns:
                                        if re.match(pattern, value_str, re.IGNORECASE):
                                            validation["dummy_values_found"].append({
                                                "model_id": stat.model_id,
                                                "mine_name": stat.mine_name,
                                                "run_number": stat.run_number,
                                                "field_name": field_name,
                                                "value": value_str,
                                                "pattern_type": pattern_type,
                                                "pattern": pattern
                                            })
                
                # Berechne Qualitäts-Scores pro Modell
                for model_id in set(stat.model_id for stat in successful_stats):
                    model_stats = [s for s in successful_stats if s.model_id == model_id]
                    total_fields = sum(len(s.structured_data) for s in model_stats if s.structured_data)
                    dummy_fields = len([d for d in validation["dummy_values_found"] if d["model_id"] == model_id])
                    
                    quality_score = 1.0 - (dummy_fields / total_fields) if total_fields > 0 else 0.0
                    validation["quality_scores"][model_id] = {
                        "total_fields": total_fields,
                        "dummy_fields": dummy_fields,
                        "quality_score": quality_score
                    }
                
        except Exception as e:
            validation["error"] = str(e)
            logger.error(f"[DB-VALIDATOR] Fehler bei Datenqualitäts-Validierung: {e}")
        
        return validation
    
    async def _validate_data_plausibility(self, models: Optional[List[str]], mines: Optional[List[str]]) -> Dict[str, Any]:
        """
        Prüft Plausibilität der extrahierten Daten
        """
        validation = {
            "coordinate_checks": [],
            "cost_plausibility": [],
            "operator_validation": [],
            "date_validation": [],
            "issues": []
        }
        
        try:
            with db_manager.get_session() as session:
                query = session.query(ModelStatistics).filter_by(success=True)
                if models:
                    query = query.filter(ModelStatistics.model_id.in_(models))
                if mines:
                    query = query.filter(ModelStatistics.mine_name.in_(mines))
                
                successful_stats = query.all()
                
                for stat in successful_stats:
                    if stat.structured_data:
                        # Koordinaten-Plausibilität (für Quebec)
                        x_coord = stat.structured_data.get('x-Koordinate')
                        y_coord = stat.structured_data.get('y-Koordinate')
                        
                        if x_coord and y_coord:
                            try:
                                x_val = float(str(x_coord).replace(',', '.'))
                                y_val = float(str(y_coord).replace(',', '.'))
                                
                                # Quebec liegt etwa zwischen -79° bis -57° (Länge) und 45° bis 62° (Breite)
                                if not (-79 <= x_val <= -57 and 45 <= y_val <= 62):
                                    validation["coordinate_checks"].append({
                                        "model_id": stat.model_id,
                                        "mine_name": stat.mine_name,
                                        "x_coord": x_val,
                                        "y_coord": y_val,
                                        "issue": "Koordinaten außerhalb Quebec"
                                    })
                            except (ValueError, TypeError):
                                validation["coordinate_checks"].append({
                                    "model_id": stat.model_id,
                                    "mine_name": stat.mine_name,
                                    "x_coord": x_coord,
                                    "y_coord": y_coord,
                                    "issue": "Ungültiges Koordinaten-Format"
                                })
                        
                        # Kosten-Plausibilität
                        costs = stat.structured_data.get('Restaurationskosten')
                        if costs:
                            cost_str = str(costs).strip()
                            # Prüfe auf unrealistische Kosten
                            cost_numbers = re.findall(r'[\d,]+', cost_str)
                            if cost_numbers:
                                try:
                                    cost_value = float(cost_numbers[0].replace(',', ''))
                                    if cost_value < 1000 or cost_value > 10000000000:  # 1K bis 10B
                                        validation["cost_plausibility"].append({
                                            "model_id": stat.model_id,
                                            "mine_name": stat.mine_name,
                                            "cost_value": cost_value,
                                            "cost_string": cost_str,
                                            "issue": "Unrealistische Kostenhöhe"
                                        })
                                except (ValueError, TypeError):
                                    pass
                        
                        # Betreiber-Validierung
                        operator = stat.structured_data.get('Betreiber') or stat.structured_data.get('Eigentümer')
                        if operator:
                            operator_str = str(operator).strip().lower()
                            # Bekannte Quebec-Bergbau-Unternehmen
                            known_operators = [
                                'newmont', 'agnico eagle', 'iamgold', 'barrick', 'goldcorp',
                                'yamana', 'eldorado', 'osisko', 'quebec nickel'
                            ]
                            
                            is_known = any(known in operator_str for known in known_operators)
                            if not is_known and len(operator_str) > 5:  # Nicht trivial kurz
                                validation["operator_validation"].append({
                                    "model_id": stat.model_id,
                                    "mine_name": stat.mine_name,
                                    "operator": operator,
                                    "issue": "Unbekannter Betreiber"
                                })
                
        except Exception as e:
            validation["error"] = str(e)
            logger.error(f"[DB-VALIDATOR] Fehler bei Plausibilitäts-Validierung: {e}")
        
        return validation
    
    async def _validate_sources(self) -> Dict[str, Any]:
        """
        Validiert Quellen-Tabelle
        """
        validation = {
            "total_sources": 0,
            "sources_with_access_data": 0,
            "recent_activity": 0,
            "broken_urls": [],
            "issues": []
        }
        
        try:
            with db_manager.get_session() as session:
                all_sources = session.query(Source).all()
                validation["total_sources"] = len(all_sources)
                
                # Prüfe Access-Daten
                sources_with_access = [s for s in all_sources if s.last_attempted_access or s.last_successful_access]
                validation["sources_with_access_data"] = len(sources_with_access)
                
                # Prüfe aktuelle Aktivität (letzte 7 Tage)
                recent_cutoff = datetime.now() - timedelta(days=7)
                recent_sources = [
                    s for s in all_sources 
                    if s.last_attempted_access and s.last_attempted_access > recent_cutoff
                ]
                validation["recent_activity"] = len(recent_sources)
                
                # Prüfe URL-Validität (basic)
                for source in all_sources:
                    if source.url:
                        if not (source.url.startswith('http://') or source.url.startswith('https://')):
                            validation["broken_urls"].append({
                                "source_id": source.id,
                                "url": source.url,
                                "issue": "Ungültiges URL-Format"
                            })
                
        except Exception as e:
            validation["error"] = str(e)
            logger.error(f"[DB-VALIDATOR] Fehler bei Quellen-Validierung: {e}")
        
        return validation
    
    def _collect_all_issues(self, validation_results: Dict[str, Any]):
        """
        Sammelt alle Issues aus allen Validierungs-Bereichen
        """
        issues = validation_results["issues_summary"]
        
        # ModelStatistics Issues
        model_stats = validation_results.get("statistics_validation", {})
        if model_stats.get("missing_run_numbers"):
            issues["critical"].append(f"Fehlende run_numbers: {len(model_stats['missing_run_numbers'])} Kombinationen")
        
        if model_stats.get("zero_response_times"):
            issues["warnings"].append(f"Null Response-Zeiten: {len(model_stats['zero_response_times'])} Einträge")
        
        # FieldStatistics Issues
        field_stats = validation_results.get("field_statistics_validation", {})
        if field_stats.get("zero_success_fields"):
            issues["warnings"].append(f"Felder mit 0% Erfolg: {len(field_stats['zero_success_fields'])}")
        
        if field_stats.get("inconsistent_calculations"):
            issues["critical"].append(f"Inkonsistente Berechnungen: {len(field_stats['inconsistent_calculations'])}")
        
        # Data Quality Issues
        data_quality = validation_results.get("data_quality_validation", {})
        if data_quality.get("dummy_values_found"):
            dummy_count = len(data_quality["dummy_values_found"])
            if dummy_count > 10:
                issues["critical"].append(f"Viele Dummy-Werte gefunden: {dummy_count}")
            else:
                issues["warnings"].append(f"Dummy-Werte gefunden: {dummy_count}")
        
        # Plausibility Issues
        plausibility = validation_results.get("plausibility_checks", {})
        if plausibility.get("coordinate_checks"):
            issues["warnings"].append(f"Koordinaten-Probleme: {len(plausibility['coordinate_checks'])}")
    
    def _determine_overall_status(self, validation_results: Dict[str, Any]) -> str:
        """
        Bestimmt Overall-Status basierend auf gefundenen Issues
        """
        issues = validation_results["issues_summary"]
        
        if validation_results.get("error"):
            return "ERROR"
        elif issues["critical"]:
            return "CRITICAL_ISSUES"
        elif len(issues["warnings"]) > 5:
            return "MULTIPLE_WARNINGS"
        elif issues["warnings"]:
            return "WARNINGS_FOUND"
        else:
            return "HEALTHY"