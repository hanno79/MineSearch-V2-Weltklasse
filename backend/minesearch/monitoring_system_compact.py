"""
Compact Monitoring System
Kompakte Version des Monitoring Systems

Author: MineSearch Development Team
Date: 2025-01-11
"""

import logging
import sqlite3
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class DataQualityMonitor:
    """Datenqualitäts-Monitor für kontinuierliche Überwachung"""

    def __init__(self, db_path: str = None):
        """Initialisiert das Monitoring-System"""
        self.db_path = db_path or "mines.db"
        self.alerts = []
        self.metrics = defaultdict(list)
        self.last_check = None

    def check_data_quality(self) -> Dict[str, Any]:
        """Prüfe Datenqualität"""
        try:
            logger.info("🔍 Prüfe Datenqualität...")
            
            quality_report = {
                'timestamp': datetime.now().isoformat(),
                'overall_score': 0.0,
                'issues': [],
                'recommendations': []
            }
            
            # Prüfe verschiedene Qualitätsaspekte
            self._check_field_contamination(quality_report)
            self._check_data_completeness(quality_report)
            self._check_data_consistency(quality_report)
            self._check_performance_metrics(quality_report)
            
            # Berechne Gesamt-Score
            quality_report['overall_score'] = self._calculate_quality_score(quality_report)
            
            logger.info(f"✅ Datenqualität geprüft: {quality_report['overall_score']:.1f}%")
            return quality_report
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Datenqualitätsprüfung: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _check_field_contamination(self, report: Dict[str, Any]):
        """Prüfe Feldkontamination"""
        try:
            # Simuliere Feldkontaminationsprüfung
            contamination_issues = []
            
            # Hier würden echte Datenbankabfragen stattfinden
            # Simuliere einige Probleme
            if len(contamination_issues) > 0:
                report['issues'].extend(contamination_issues)
                report['recommendations'].append("Feldkontamination bereinigen")
            
        except Exception as e:
            logger.warning(f"Fehler bei Feldkontaminationsprüfung: {e}")

    def _check_data_completeness(self, report: Dict[str, Any]):
        """Prüfe Datenvollständigkeit"""
        try:
            # Simuliere Vollständigkeitsprüfung
            completeness_issues = []
            
            # Hier würden echte Datenbankabfragen stattfinden
            # Simuliere einige Probleme
            if len(completeness_issues) > 0:
                report['issues'].extend(completeness_issues)
                report['recommendations'].append("Fehlende Daten ergänzen")
            
        except Exception as e:
            logger.warning(f"Fehler bei Vollständigkeitsprüfung: {e}")

    def _check_data_consistency(self, report: Dict[str, Any]):
        """Prüfe Datenkonsistenz"""
        try:
            # Simuliere Konsistenzprüfung
            consistency_issues = []
            
            # Hier würden echte Datenbankabfragen stattfinden
            # Simuliere einige Probleme
            if len(consistency_issues) > 0:
                report['issues'].extend(consistency_issues)
                report['recommendations'].append("Datenkonsistenz verbessern")
            
        except Exception as e:
            logger.warning(f"Fehler bei Konsistenzprüfung: {e}")

    def _check_performance_metrics(self, report: Dict[str, Any]):
        """Prüfe Performance-Metriken"""
        try:
            # Simuliere Performance-Prüfung
            performance_issues = []
            
            # Hier würden echte Performance-Metriken geprüft
            # Simuliere einige Probleme
            if len(performance_issues) > 0:
                report['issues'].extend(performance_issues)
                report['recommendations'].append("Performance optimieren")
            
        except Exception as e:
            logger.warning(f"Fehler bei Performance-Prüfung: {e}")

    def _calculate_quality_score(self, report: Dict[str, Any]) -> float:
        """Berechne Qualitäts-Score"""
        try:
            # Basis-Score
            base_score = 100.0
            
            # Abzüge für Probleme
            issue_penalty = len(report['issues']) * 5.0
            
            # Abzüge für Empfehlungen
            recommendation_penalty = len(report['recommendations']) * 2.0
            
            # Berechne finalen Score
            final_score = max(0.0, base_score - issue_penalty - recommendation_penalty)
            
            return final_score
            
        except Exception as e:
            logger.error(f"Fehler bei Score-Berechnung: {e}")
            return 0.0

    def generate_alert(self, severity: str, message: str, details: Dict[str, Any] = None):
        """Generiere Alert"""
        try:
            alert = {
                'id': f"alert_{int(time.time())}",
                'severity': severity,
                'message': message,
                'details': details or {},
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            }
            
            self.alerts.append(alert)
            logger.warning(f"🚨 Alert generiert: {severity} - {message}")
            
        except Exception as e:
            logger.error(f"Fehler beim Generieren des Alerts: {e}")

    def get_alerts(self, severity: str = None, acknowledged: bool = None) -> List[Dict[str, Any]]:
        """Hole Alerts"""
        try:
            filtered_alerts = self.alerts
            
            if severity:
                filtered_alerts = [a for a in filtered_alerts if a['severity'] == severity]
            
            if acknowledged is not None:
                filtered_alerts = [a for a in filtered_alerts if a['acknowledged'] == acknowledged]
            
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Alerts: {e}")
            return []

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Bestätige Alert"""
        try:
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_at'] = datetime.now().isoformat()
                    logger.info(f"✅ Alert bestätigt: {alert_id}")
                    return True
            
            logger.warning(f"Alert nicht gefunden: {alert_id}")
            return False
            
        except Exception as e:
            logger.error(f"Fehler beim Bestätigen des Alerts: {e}")
            return False

    def get_metrics(self, metric_name: str = None) -> Dict[str, Any]:
        """Hole Metriken"""
        try:
            if metric_name:
                return {metric_name: self.metrics.get(metric_name, [])}
            else:
                return dict(self.metrics)
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Metriken: {e}")
            return {}

    def add_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """Füge Metrik hinzu"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            metric_entry = {
                'value': value,
                'timestamp': timestamp.isoformat()
            }
            
            self.metrics[metric_name].append(metric_entry)
            
            # Behalte nur die letzten 1000 Einträge
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Metrik: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Hole Gesundheitsstatus"""
        try:
            return {
                'status': 'healthy',
                'last_check': self.last_check.isoformat() if self.last_check else None,
                'active_alerts': len([a for a in self.alerts if not a['acknowledged']]),
                'total_alerts': len(self.alerts),
                'metrics_count': len(self.metrics),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Gesundheitsstatus: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def cleanup_old_data(self, days: int = 30):
        """Bereinige alte Daten"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Bereinige alte Alerts
            self.alerts = [a for a in self.alerts if 
                          datetime.fromisoformat(a['timestamp']) > cutoff_date]
            
            # Bereinige alte Metriken
            for metric_name in self.metrics:
                self.metrics[metric_name] = [
                    m for m in self.metrics[metric_name]
                    if datetime.fromisoformat(m['timestamp']) > cutoff_date
                ]
            
            logger.info(f"✅ Alte Daten bereinigt (älter als {days} Tage)")
            
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen alter Daten: {e}")

    def export_report(self, file_path: str = None) -> str:
        """Exportiere Bericht"""
        try:
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"monitoring_report_{timestamp}.json"
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'health_status': self.get_health_status(),
                'data_quality': self.check_data_quality(),
                'alerts': self.get_alerts(),
                'metrics': self.get_metrics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Bericht exportiert: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren des Berichts: {e}")
            return ""

    def start_monitoring(self, interval_seconds: int = 300):
        """Starte kontinuierliches Monitoring"""
        try:
            logger.info(f"🚀 Starte Monitoring (Intervall: {interval_seconds}s)")
            
            while True:
                try:
                    # Führe Qualitätsprüfung durch
                    quality_report = self.check_data_quality()
                    self.last_check = datetime.now()
                    
                    # Prüfe auf kritische Probleme
                    if quality_report.get('overall_score', 0) < 70:
                        self.generate_alert(
                            'critical',
                            'Datenqualität kritisch niedrig',
                            {'score': quality_report.get('overall_score', 0)}
                        )
                    
                    # Warte auf nächste Prüfung
                    time.sleep(interval_seconds)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Monitoring gestoppt")
                    break
                except Exception as e:
                    logger.error(f"Fehler im Monitoring-Loop: {e}")
                    time.sleep(60)  # Warte 1 Minute bei Fehlern
            
        except Exception as e:
            logger.error(f"Fehler beim Starten des Monitorings: {e}")


# Globale Instanz für einfache Verwendung
_monitor = None


def get_monitor() -> DataQualityMonitor:
    """Hole globale Monitor-Instanz"""
    global _monitor
    if _monitor is None:
        _monitor = DataQualityMonitor()
    return _monitor


def start_monitoring(interval_seconds: int = 300):
    """Starte globales Monitoring"""
    monitor = get_monitor()
    monitor.start_monitoring(interval_seconds)


__all__ = [
    "DataQualityMonitor",
    "get_monitor",
    "start_monitoring"
]
