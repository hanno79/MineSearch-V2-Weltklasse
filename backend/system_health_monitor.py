#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: System Health Monitor für Datenqualität

🏥 SYSTEM HEALTH MONITOR
========================

Überwacht kontinuierlich:
- Datenbank-Größe und Performance
- UNIQUE-Constraint-Violations 
- Insert/Update-Performance
- Allgemeine Systemgesundheit

USAGE: python3 system_health_monitor.py
CRON:  */15 * * * *  # Alle 15 Minuten
"""

import sqlite3
import time
import psutil
from datetime import datetime


class SystemHealthMonitor:
    """🏥 Kontinuierliche System-Gesundheits-Überwachung"""
    
    def __init__(self, db_path: str = 'mines.db'):
        self.db_path = db_path
    
    def check_system_health(self) -> dict:
        """Führt vollständigen Health-Check durch"""
        print(f"🏥 SYSTEM HEALTH CHECK - {datetime.now().strftime('%H:%M:%S')}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'database_size': self._check_database_size(),
            'table_counts': self._check_table_counts(),
            'constraint_violations': self._check_recent_violations(),
            'system_performance': self._check_system_performance(),
            'overall_status': 'OK'
        }
        
        # Bestimme Overall Status
        if results['constraint_violations'] > 5:
            results['overall_status'] = 'WARNING'
        if results['constraint_violations'] > 20:
            results['overall_status'] = 'CRITICAL'
        
        # Speichere Metriken
        self._save_health_metrics(results)
        
        return results
    
    def _check_database_size(self) -> dict:
        """Prüft Datenbank-Größe"""
        try:
            import os
            size_bytes = os.path.getsize(self.db_path)
            size_mb = size_bytes / (1024 * 1024)
            
            return {
                'size_mb': round(size_mb, 2),
                'size_bytes': size_bytes,
                'status': 'OK' if size_mb < 100 else 'WARNING'
            }
        except:
            return {'error': 'Could not check database size'}
    
    def _check_table_counts(self) -> dict:
        """Prüft Anzahl Einträge in kritischen Tabellen"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            counts = {}
            for table in ['companies', 'mines']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            
            return counts
            
        except Exception as e:
            return {'error': str(e)}
        finally:
            conn.close()
    
    def _check_recent_violations(self) -> int:
        """Prüft UNIQUE-Constraint-Violations der letzten Stunde"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM duplicate_prevention_log 
                WHERE timestamp > datetime('now', '-1 hour') 
                AND action_taken = 'constraint_violation'
            """)
            
            violations = cursor.fetchone()[0]
            return violations
            
        except:
            return 0
        finally:
            conn.close()
    
    def _check_system_performance(self) -> dict:
        """Prüft System-Performance"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('.').percent
            }
        except:
            return {'error': 'Could not check system performance'}
    
    def _save_health_metrics(self, results: dict):
        """Speichert Health-Metriken in DB"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Database Size Metric
            if 'size_mb' in results['database_size']:
                cursor.execute("""
                    INSERT INTO system_health_log (metric_name, metric_value, status)
                    VALUES (?, ?, ?)
                """, ('database_size_mb', results['database_size']['size_mb'], 
                     results['database_size']['status']))
            
            # Constraint Violations Metric
            cursor.execute("""
                INSERT INTO system_health_log (metric_name, metric_value, status)
                VALUES (?, ?, ?)
            """, ('constraint_violations', results['constraint_violations'],
                 'OK' if results['constraint_violations'] < 5 else 'WARNING'))
            
            conn.commit()
            
        except Exception as e:
            print(f"Warning: Could not save health metrics: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    monitor = SystemHealthMonitor()
    health = monitor.check_system_health()
    
    print(f"Status: {health['overall_status']}")
    if health['overall_status'] != 'OK':
        print(f"⚠️ Issues detected - check logs for details")
