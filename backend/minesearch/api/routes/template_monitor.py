"""
Author: rahn
Datum: 26.08.2025
Version: 1.0
Beschreibung: API Endpoints für Template-Monitoring System
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from minesearch.template_monitor import template_monitor, TemplateAlert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/template-monitor", tags=["Template Monitor"])

@router.get("/alerts")
async def get_template_alerts(
    days_back: int = Query(7, description="Anzahl Tage zurück zu analysieren"),
    min_occurrences: int = Query(3, description="Minimum Vorkommen für Alert"),
    severity: Optional[str] = Query(None, description="Filter nach Schweregrad")
) -> Dict[str, Any]:
    """
    Hole aktuelle Template-Alerts
    
    Returns:
        Dictionary mit Alerts und Statistiken
    """
    try:
        alerts = template_monitor.analyze_patterns(days_back, min_occurrences)
        
        # Filter nach Schweregrad falls angegeben
        if severity:
            alerts = [a for a in alerts if a.severity == severity.lower()]
        
        # Konvertiere zu Dictionaries
        alert_data = [alert.to_dict() for alert in alerts]
        
        # Statistiken
        stats = {
            'total_alerts': len(alert_data),
            'by_severity': {},
            'most_affected_fields': {},
            'recent_alerts': len([a for a in alerts if 
                                (datetime.now() - a.last_seen).days <= 1])
        }
        
        # Gruppiere nach Schweregrad
        for alert in alerts:
            severity = alert.severity
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        # Gruppiere nach Feldern
        for alert in alerts:
            field = alert.field
            stats['most_affected_fields'][field] = stats['most_affected_fields'].get(field, 0) + 1
        
        return {
            'success': True,
            'data': {
                'alerts': alert_data,
                'statistics': stats,
                'generated_at': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[TEMPLATE_MONITOR_API] Fehler beim Abrufen der Alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Template-Alerts: {str(e)}")

@router.get("/violations")
async def get_rule10_violations() -> Dict[str, Any]:
    """
    Prüfe auf REGEL 10 Verstöße
    
    Returns:
        Dictionary mit detaillierten Verstoß-Informationen
    """
    try:
        violations = template_monitor.check_for_rule10_violations()
        
        return {
            'success': True,
            'data': {
                'violations': violations,
                'summary': {
                    'total_violations': violations['total_violations'],
                    'critical_fields': len(violations['duplicate_values']),
                    'fake_sources_count': len(violations['fake_sources']),
                    'round_number_fields': len(violations['round_number_clusters'])
                },
                'generated_at': datetime.now().isoformat(),
                'rule10_status': 'VIOLATED' if violations['total_violations'] > 0 else 'COMPLIANT'
            }
        }
        
    except Exception as e:
        logger.error(f"[TEMPLATE_MONITOR_API] Fehler bei REGEL 10 Prüfung: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler bei REGEL 10 Prüfung: {str(e)}")

@router.get("/report")
async def generate_monitoring_report() -> Dict[str, Any]:
    """
    Generiere vollständigen Template-Monitoring Report
    
    Returns:
        Dictionary mit formatiertem Report
    """
    try:
        report_text = template_monitor.generate_report()
        
        return {
            'success': True,
            'data': {
                'report': report_text,
                'generated_at': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[TEMPLATE_MONITOR_API] Fehler bei Report-Generierung: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler bei Report-Generierung: {str(e)}")

@router.post("/record-pattern")
async def record_suspicious_pattern(
    pattern_type: str,
    field: str,
    mine_name: str,
    value: str,
    source_info: Optional[str] = None,
    severity: str = "medium"
) -> Dict[str, Any]:
    """
    Erfasse manuell ein verdächtiges Pattern
    
    Args:
        pattern_type: Art des Patterns
        field: Betroffenes Feld
        mine_name: Name der Mine
        value: Verdächtiger Wert
        source_info: Quelleninformation (optional)
        severity: Schweregrad
    
    Returns:
        Bestätigung der Erfassung
    """
    try:
        template_monitor.record_pattern(
            pattern_type, field, mine_name, value, source_info, severity
        )
        
        return {
            'success': True,
            'data': {
                'message': f"Pattern erfasst: {pattern_type} in {field}",
                'recorded_at': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[TEMPLATE_MONITOR_API] Fehler beim Erfassen des Patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Erfassen: {str(e)}")

@router.get("/status")
async def get_monitor_status() -> Dict[str, Any]:
    """
    Status des Template-Monitoring Systems
    
    Returns:
        System-Status Informationen
    """
    try:
        # Prüfe Datenbankverbindung
        db_connected = True
        try:
            import sqlite3
            with sqlite3.connect(template_monitor.db_path) as conn:
                conn.execute("SELECT 1")
        except Exception:
            db_connected = False
        
        # Hole letzte Aktivität
        recent_alerts = template_monitor.analyze_patterns(days_back=1, min_occurrences=1)
        
        return {
            'success': True,
            'data': {
                'system_status': 'operational' if db_connected else 'error',
                'database_connected': db_connected,
                'database_path': str(template_monitor.db_path),
                'recent_activity': {
                    'alerts_last_24h': len(recent_alerts),
                    'critical_alerts': len([a for a in recent_alerts if a.severity == 'critical'])
                },
                'monitoring_active': True,
                'rule10_monitoring': True,
                'last_check': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[TEMPLATE_MONITOR_API] Fehler beim Status-Abruf: {e}")
        return {
            'success': False,
            'data': {
                'system_status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
        }

@router.delete("/clear-patterns")
async def clear_old_patterns(days_back: int = Query(30, description="Lösche Pattern älter als X Tage")) -> Dict[str, Any]:
    """
    Lösche alte Pattern-Einträge zur Datenbankbereinigung
    
    Args:
        days_back: Lösche Einträge älter als X Tage
        
    Returns:
        Bestätigung der Bereinigung
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        import sqlite3
        with sqlite3.connect(template_monitor.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM template_patterns WHERE detected_at < ?", 
                (cutoff_date.isoformat(),)
            )
            deleted_count = cursor.rowcount
        
        return {
            'success': True,
            'data': {
                'deleted_patterns': deleted_count,
                'cutoff_date': cutoff_date.isoformat(),
                'cleaned_at': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[TEMPLATE_MONITOR_API] Fehler bei Pattern-Bereinigung: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler bei Bereinigung: {str(e)}")