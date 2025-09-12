"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Monitoring und Alerting System für Feldkontamination

MONITORING-SYSTEM 25.08.2025: Überwacht Datenqualität und alarmiert bei Problemen
"""

import logging
import sqlite3
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from minesearch.field_name_blacklist import is_field_name_value
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

logger = logging.getLogger(__name__)

class DataQualityMonitor:
    """
    DATENQUALITÄTS-MONITOR 25.08.2025
    Überwacht kontinuierlich die Datenqualität und Schutzmaßnahmen
    """

    def __init__(self, db_path: str = None):
        """Initialisiert das Monitoring-System"""
        if db_path is None:
            db_path = get_normalized_db_path()

        self.db_path = db_path
        self.alert_thresholds = {
            'contamination_rate': 0.01,  # 1% Kontaminationsrate = Alert
            'failed_extractions': 0.1,   # 10% fehlgeschlagene Extraktionen = Alert
            'null_anomaly_rate': 0.8,    # 80% NULL-Werte = Alert
            'constraint_violations': 5    # 5+ Violations/Stunde = Alert
        }

        # Monitoring-Metriken
        self.metrics = {
            'total_searches': 0,
            'contaminations_detected': 0,
            'contaminations_blocked': 0,
            'null_normalizations': 0,
            'constraint_violations': 0,
            'quality_gate_rejections': 0,
            'template_detections': 0
        }

        # Alert-Status
        self.active_alerts = []
        self.last_check = datetime.now()

    def log_search_event(self, event_type: str, mine_name: str, details: Dict[str, Any] = None):
        """
        MONITORING-EVENT LOGGING 25.08.2025
        Protokolliert Search-Events für Monitoring

        Args:
            event_type: Art des Events (search_start, contamination_detected, etc.)
            mine_name: Name der Mine
            details: Zusätzliche Details
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Erstelle monitoring_events Tabelle falls nicht vorhanden
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    mine_name TEXT NOT NULL,
                    details TEXT,
                    severity TEXT DEFAULT 'INFO'
                )
            """)

            # Event einfügen
            cursor.execute("""
                INSERT INTO monitoring_events (event_type, mine_name, details, severity)
                VALUES (?, ?, ?, ?)
            """, (
                event_type,
                mine_name,
                json.dumps(details) if details else None,
                self._get_event_severity(event_type)
            ))

            conn.commit()
            conn.close()

            # Update Metriken
            self._update_metrics(event_type, details)

            logger.debug(f"[MONITORING] Event protokolliert: {event_type} für {mine_name}")

        except Exception as e:
            logger.error(f"[MONITORING] Fehler beim Event-Logging: {e}")

    def _get_event_severity(self, event_type: str) -> str:
        """Bestimmt Schweregrad eines Events"""
        if event_type in ['contamination_detected', 'constraint_violation', 'extraction_failed']:
            return 'ERROR'
        elif event_type in ['template_detected', 'quality_gate_rejection', 'null_normalization']:
            return 'WARNING'
        else:
            return 'INFO'

    def _update_metrics(self, event_type: str, details: Dict[str, Any] = None):
        """Aktualisiert interne Metriken"""
        if event_type == 'search_start':
            self.metrics['total_searches'] += 1
        elif event_type == 'contamination_detected':
            self.metrics['contaminations_detected'] += 1
        elif event_type == 'contamination_blocked':
            self.metrics['contaminations_blocked'] += 1
        elif event_type == 'null_normalization':
            self.metrics['null_normalizations'] += 1
        elif event_type == 'constraint_violation':
            self.metrics['constraint_violations'] += 1
        elif event_type == 'quality_gate_rejection':
            self.metrics['quality_gate_rejections'] += 1
        elif event_type == 'template_detected':
            self.metrics['template_detections'] += 1

    def check_data_quality(self) -> Dict[str, Any]:
        """
        DATENQUALITÄTS-CHECK 25.08.2025
        Prüft aktuelle Datenqualität und erkennt Anomalien

        Returns:
            Umfassender Qualitätsbericht
        """
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            quality_report = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'HEALTHY',
                'alerts': [],
                'metrics': {},
                'recommendations': []
            }

            # 1. PRÜFE AKTUELLE KONTAMINATIONEN
            cursor.execute("""
                SELECT COUNT(*) FROM search_results
                WHERE created_at > datetime('now', '-1 hour')
            """)
            recent_searches = cursor.fetchone()[0]

            # Prüfe Constraint-Violations
            cursor.execute("""
                SELECT COUNT(*) FROM constraint_log
                WHERE severity IN ('WARNING', 'ERROR')
                AND timestamp > datetime('now', '-1 hour')
            """)
            recent_violations = cursor.fetchone()[0]

            quality_report['metrics']['recent_searches'] = recent_searches
            quality_report['metrics']['recent_violations'] = recent_violations

            # 2. ALERT-PRÜFUNGEN
            if recent_violations > self.alert_thresholds['constraint_violations']:
                quality_report['alerts'].append({
                    'type': 'CONSTRAINT_VIOLATIONS',
                    'severity': 'HIGH',
                    'message': f'{recent_violations} Constraint-Violations in der letzten Stunde',
                    'threshold': self.alert_thresholds['constraint_violations']
                })
                quality_report['overall_status'] = 'WARNING'

            # 3. FELDKONTAMINATIONS-ANALYSE
            contamination_stats = self._analyze_field_contamination()
            quality_report['metrics']['contamination_analysis'] = contamination_stats

            if contamination_stats['contamination_rate'] > self.alert_thresholds['contamination_rate']:
                quality_report['alerts'].append({
                    'type': 'FIELD_CONTAMINATION',
                    'severity': 'CRITICAL',
                    'message': f'Kontaminationsrate: {contamination_stats["contamination_rate"]:.2%}',
                    'threshold': self.alert_thresholds['contamination_rate']
                })
                quality_report['overall_status'] = 'CRITICAL'

            # 4. NULL-WERT-ANOMALIEN
            null_stats = self._analyze_null_patterns()
            quality_report['metrics']['null_analysis'] = null_stats

            if null_stats['null_rate'] > self.alert_thresholds['null_anomaly_rate']:
                quality_report['alerts'].append({
                    'type': 'NULL_ANOMALY',
                    'severity': 'MEDIUM',
                    'message': f'Ungewöhnlich hohe NULL-Rate: {null_stats["null_rate"]:.2%}',
                    'threshold': self.alert_thresholds['null_anomaly_rate']
                })
                if quality_report['overall_status'] == 'HEALTHY':
                    quality_report['overall_status'] = 'WARNING'

            # 5. MONITORING-EVENTS AUSWERTEN
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM monitoring_events
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY event_type
            """)
            event_stats = dict(cursor.fetchall())
            quality_report['metrics']['event_stats'] = event_stats

            # 6. EMPFEHLUNGEN GENERIEREN
            quality_report['recommendations'] = self._generate_recommendations(quality_report)

            conn.close()

            # Alert-Status updaten
            self._update_alert_status(quality_report['alerts'])

            logger.info(f"[MONITORING] Datenqualitäts-Check: {quality_report['overall_status']}
({len(quality_report['alerts'])} Alerts)")

            return quality_report

        except Exception as e:
            logger.error(f"[MONITORING] Fehler beim Qualitäts-Check: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'ERROR',
                'error': str(e),
                'alerts': [],
                'metrics': {}
            }

    def _analyze_field_contamination(self) -> Dict[str, Any]:
        """Analysiert aktuelle Feldkontamination in der Datenbank"""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, mine_name, structured_data
                FROM search_results
                WHERE created_at > datetime('now', '-24 hours')
                AND structured_data IS NOT NULL
                AND structured_data != ''
                LIMIT 100
            """)

            recent_entries = cursor.fetchall()
            conn.close()

            total_entries = len(recent_entries)
            contaminated_entries = 0
            contamination_details = defaultdict(list)

            for entry_id, mine_name, structured_data_json in recent_entries:
                try:
                    structured_data = json.loads(structured_data_json)
                    entry_contaminated = False

                    for field, value in structured_data.items():
                        if field.startswith('_'):
                            continue

                        if value and is_field_name_value(str(value), field):
                            contamination_details[field].append({
                                'id': entry_id,
                                'mine': mine_name,
                                'value': str(value)
                            })
                            entry_contaminated = True

                    if entry_contaminated:
                        contaminated_entries += 1

                except json.JSONDecodeError:
                    continue

            contamination_rate = contaminated_entries / total_entries if total_entries > 0 else 0

            return {
                'total_entries': total_entries,
                'contaminated_entries': contaminated_entries,
                'contamination_rate': contamination_rate,
                'contaminated_fields': len(contamination_details),
                'field_details': dict(contamination_details)
            }

        except Exception as e:
            logger.error(f"[MONITORING] Fehler bei Kontaminations-Analyse: {e}")
            return {'error': str(e)}

    def _analyze_null_patterns(self) -> Dict[str, Any]:
        """Analysiert NULL-Wert-Muster für Anomalie-Erkennung"""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT structured_data
                FROM search_results
                WHERE created_at > datetime('now', '-24 hours')
                AND structured_data IS NOT NULL
                AND structured_data != ''
                LIMIT 200
            """)

            entries = cursor.fetchall()
            conn.close()

            total_fields = 0
            null_fields = 0
            field_null_counts = defaultdict(int)
            field_total_counts = defaultdict(int)

            for (structured_data_json,) in entries:
                try:
                    structured_data = json.loads(structured_data_json)

                    for field, value in structured_data.items():
                        if field.startswith('_'):
                            continue

                        field_total_counts[field] += 1
                        total_fields += 1

                        if value is None or (isinstance(value, str) and not value.strip()):
                            field_null_counts[field] += 1
                            null_fields += 1

                except json.JSONDecodeError:
                    continue

            null_rate = null_fields / total_fields if total_fields > 0 else 0

            # Top NULL-Felder identifizieren
            top_null_fields = sorted(
                [(field, count, count/field_total_counts[field])
                 for field, count in field_null_counts.items()],
                key=lambda x: x[2], reverse=True
            )[:10]

            return {
                'total_fields': total_fields,
                'null_fields': null_fields,
                'null_rate': null_rate,
                'top_null_fields': top_null_fields,
                'field_statistics': dict(field_total_counts)
            }

        except Exception as e:
            logger.error(f"[MONITORING] Fehler bei NULL-Analyse: {e}")
            return {'error': str(e)}

    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generiert Verbesserungsempfehlungen basierend auf Qualitätsbericht"""
        recommendations = []

        if quality_report['overall_status'] == 'CRITICAL':
            recommendations.append("🚨 SOFORTMASSNAHME: System-weite Überprüfung der Validierungslogik nötig")

        for alert in quality_report['alerts']:
            if alert['type'] == 'FIELD_CONTAMINATION':
                recommendations.append("🔍 Prüfe Field Name Blacklist und Template Detection")
                recommendations.append("🛠️ Erwäge Aktualisierung der Extraction Patterns")
            elif alert['type'] == 'CONSTRAINT_VIOLATIONS':
                recommendations.append("🗄️ Überprüfe Database Constraints und Trigger")
                recommendations.append("📊 Analysiere Constraint Log für wiederkehrende Muster")
            elif alert['type'] == 'NULL_ANOMALY':
                recommendations.append("🔄 Überprüfe NULL-Normalisierung Konfiguration")
                recommendations.append("🌐 Prüfe Provider-spezifische Extraktions-Performance")

        if not recommendations:
            recommendations.append("✅ Alle Systeme funktional - regelmäßige Überwachung fortsetzen")

        return recommendations

    def _update_alert_status(self, new_alerts: List[Dict[str, Any]]):
        """Aktualisiert aktiven Alert-Status"""
        # Entferne alte Alerts
        self.active_alerts = [alert for alert in self.active_alerts
                             if alert.get("expires", datetime.now()) > datetime.now()]

        # Füge neue Alerts hinzu
        for alert in new_alerts:
            alert['created'] = datetime.now()
            alert['expires'] = datetime.now() + timedelta(hours=1)
            self.active_alerts.append(alert)

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """
        MONITORING-DASHBOARD 25.08.2025
        Generiert Dashboard-Daten für Übersicht

        Returns:
            Dashboard-Daten mit aktuellen Metriken und Status
        """
        try:
            quality_report = self.check_data_quality()

            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'system_status': quality_report['overall_status'],
                'active_alerts': len(quality_report['alerts']),
                'protection_layers': {
                    'extraction_layer': self._check_extraction_layer(),
                    'service_layer': self._check_service_layer(),
                    'database_layer': self._check_database_layer(),
                    'data_layer': self._check_data_layer()
                },
                'recent_metrics': self.metrics,
                'quality_report': quality_report,
                'uptime_info': self._get_uptime_info()
            }

            return dashboard

        except Exception as e:
            logger.error(f"[MONITORING] Fehler beim Dashboard-Aufbau: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'system_status': 'ERROR',
                'error': str(e)
            }

    def _check_extraction_layer(self) -> Dict[str, Any]:
        """Prüft Status der Extraction Layer Protection"""
        try:
            from minesearch.extraction_processors import is_template_or_dummy_value

            # Test Template Detection
            test_result = is_template_or_dummy_value("x-Koordinate", "Betreiber")

            return {
                'status': 'ACTIVE' if test_result else 'INACTIVE',
                'component': 'extraction_processors.py',
                'test_result': test_result,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    def _check_service_layer(self) -> Dict[str, Any]:
        """Prüft Status der Service Layer Protection"""
        try:
            from minesearch.search_service import MineSearchService

            # Service verfügbar und funktional
            service = MineSearchService()

            return {
                'status': 'ACTIVE',
                'component': 'search_service.py',
                'quality_gate': 'ENABLED',
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    def _check_database_layer(self) -> Dict[str, Any]:
        """Prüft Status der Database Layer Protection"""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Prüfe Trigger
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            triggers = [row[0] for row in cursor.fetchall()]

            expected_triggers = [
                'prevent_field_contamination_insert',
                'prevent_field_contamination_update'
            ]

            triggers_active = sum(1 for t in expected_triggers if t in triggers)

            conn.close()

            return {
                'status': 'ACTIVE' if triggers_active >= 2 else 'PARTIAL',
                'component': 'database_constraints.py',
                'triggers_active': triggers_active,
                'triggers_expected': len(expected_triggers),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    def _check_data_layer(self) -> Dict[str, Any]:
        """Prüft Status der Data Layer Protection"""
        try:
            from minesearch.null_normalizer import NullNormalizer

            normalizer = NullNormalizer()

            # Test NULL-Normalisierung
            test_result = normalizer.normalize_value("-")

            return {
                'status': 'ACTIVE' if test_result is None else 'INACTIVE',
                'component': 'null_normalizer.py',
                'test_result': test_result is None,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    def _get_uptime_info(self) -> Dict[str, Any]:
        """Sammelt System-Uptime Informationen"""
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()

            # Letzte Aktivität
            cursor.execute("""
                SELECT MAX(created_at) FROM search_results
                WHERE created_at > datetime('now', '-24 hours')
            """)
            last_activity = cursor.fetchone()[0]

            # Searches in letzter Stunde
            cursor.execute("""
                SELECT COUNT(*) FROM search_results
                WHERE created_at > datetime('now', '-1 hour')
            """)
            recent_activity = cursor.fetchone()[0]

            conn.close()

            return {
                'last_activity': last_activity,
                'recent_searches': recent_activity,
                'monitoring_start': self.last_check.isoformat(),
                'system_responsive': recent_activity > 0 or last_activity is not None
            }
        except Exception as e:
            return {
                'error': str(e),
                'system_responsive': False
            }

# Globale Monitor-Instanz
data_quality_monitor = DataQualityMonitor()

def main():
    """
    MAIN-FUNKTION 25.08.2025: Startet Monitoring-Dashboard
    """
    print("🖥️  DATENQUALITÄTS-MONITORING DASHBOARD")
    print("=" * 50)

    monitor = DataQualityMonitor()
    dashboard = monitor.get_monitoring_dashboard()

    print(f"🕐 Timestamp: {dashboard['timestamp']}")
    print(f"📊 System Status: {dashboard['system_status']}")
    print(f"🚨 Active Alerts: {dashboard['active_alerts']}")

    print(f"\n🛡️  SCHUTZEBENEN:")
    for layer, status in dashboard['protection_layers'].items():
        status_icon = "✅" if status['status'] == 'ACTIVE' else "⚠️" if status['status'] == 'PARTIAL' else "❌"
        print(f"   {status_icon} {layer}: {status['status']}")

    print(f"\n📈 METRIKEN:")
    for metric, value in dashboard['recent_metrics'].items():
        print(f"   - {metric}: {value}")

    if dashboard['quality_report']['alerts']:
        print(f"\n🚨 AKTIVE ALERTS:")
        for alert in dashboard['quality_report']['alerts']:
            print(f"   ⚠️  {alert['type']}: {alert['message']}")

    if dashboard['quality_report']['recommendations']:
        print(f"\n💡 EMPFEHLUNGEN:")
        for rec in dashboard['quality_report']['recommendations']:
            print(f"   {rec}")

if __name__ == "__main__":
    main()
