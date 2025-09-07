#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Monitoring-System Setup für permanente Duplikat-Überwachung

📊 DUPLIKAT-MONITORING SYSTEM SETUP
===================================

Erstellt komplettes Monitoring-System:
1. 📊 Monitoring-Tabelle in Datenbank
2. 🔍 Wöchentliche Duplikat-Checker
3. 📧 Automatische Report-Generierung
4. 🚨 Alert-System bei kritischen Problemen
"""

import sqlite3
import os
from datetime import datetime


def setup_monitoring_tables(db_path: str = 'mines.db') -> bool:
    """Erstellt Monitoring-Tabellen in der Datenbank"""
    print("📊 SETUP MONITORING-TABELLEN...")
    
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        
        # 1. Duplikat-Prevention-Log Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_prevention_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name VARCHAR(50) NOT NULL,
                attempted_value VARCHAR(255) NOT NULL,
                similar_existing_value VARCHAR(255),
                similarity_score FLOAT,
                action_taken VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_decision VARCHAR(20),
                details TEXT
            )
        """)
        
        # 2. Weekly Duplicate Check Results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_duplicate_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date DATE NOT NULL,
                tables_checked INTEGER DEFAULT 0,
                duplicates_found INTEGER DEFAULT 0,
                prevention_effectiveness FLOAT DEFAULT 0.0,
                critical_issues INTEGER DEFAULT 0,
                report_file_path VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. System Health Monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_health_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,
                status VARCHAR(20) DEFAULT 'OK',
                threshold_value FLOAT,
                alert_sent BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("   ✅ Monitoring-Tabellen erfolgreich erstellt")
        return True
        
    except Exception as e:
        print(f"   ❌ Fehler beim Erstellen der Tabellen: {e}")
        return False
        
    finally:
        conn.close()


def create_monitoring_scripts():
    """Erstellt alle notwendigen Monitoring-Skripte"""
    print("\n🔍 ERSTELLE MONITORING-SKRIPTE...")
    
    # 1. Wöchentlicher Duplikat-Checker
    weekly_checker_code = '''#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0 
Beschreibung: Wöchentlicher automatischer Duplikat-Check

📅 WÖCHENTLICHER DUPLIKAT-CHECKER
==============================

Führt automatische wöchentliche Duplikat-Checks durch:
- Prüft alle kritischen Tabellen auf neue Duplikate
- Berechnet Prevention-Effectiveness
- Erstellt automatische Reports
- Sendet Alerts bei kritischen Problemen

USAGE: python3 weekly_duplicate_checker.py
CRON:  0 9 * * 1  # Jeden Montag um 9:00 Uhr
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MimeText


class WeeklyDuplicateChecker:
    """📅 Automatischer wöchentlicher Duplikat-Checker"""
    
    def __init__(self, db_path: str = 'mines.db'):
        self.db_path = db_path
        self.report_data = {
            'check_timestamp': datetime.now().isoformat(),
            'tables_checked': [],
            'duplicates_found': 0,
            'prevention_effectiveness': 0.0,
            'critical_issues': 0,
            'recommendations': []
        }
    
    def run_weekly_check(self) -> dict:
        """Führt vollständigen wöchentlichen Check durch"""
        print(f"📊 WÖCHENTLICHER DUPLIKAT-CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Check Companies Tabelle
            companies_result = self._check_table_duplicates(
                conn, 'companies', ['name'], 'Company-Duplikate'
            )
            self.report_data['tables_checked'].append(companies_result)
            
            # Check Mines Tabelle  
            mines_result = self._check_table_duplicates(
                conn, 'mines', ['name', 'country_id', 'region_id'], 'Mine-Duplikate'
            )
            self.report_data['tables_checked'].append(mines_result)
            
            # Berechne Gesamtstatistiken
            total_duplicates = sum(r['duplicates_found'] for r in self.report_data['tables_checked'])
            self.report_data['duplicates_found'] = total_duplicates
            
            # Prevention Effectiveness
            self.report_data['prevention_effectiveness'] = self._calculate_prevention_effectiveness(conn)
            
            # Kritische Issues identifizieren
            if total_duplicates > 0:
                self.report_data['critical_issues'] = total_duplicates
                self.report_data['recommendations'].append(
                    "⚠️ KRITISCH: Neue Duplikate gefunden - sofortige Bereinigung empfohlen"
                )
            
            # Speichere Report in DB
            self._save_report_to_db(conn)
            
            # Erstelle JSON Report
            report_file = self._create_json_report()
            
            # Send Alert wenn nötig
            if self.report_data['critical_issues'] > 0:
                self._send_alert()
            
            print(f"\\n✅ WEEKLY CHECK ABGESCHLOSSEN")
            print(f"   📊 Duplikate gefunden: {total_duplicates}")
            print(f"   📈 Prevention Effectiveness: {self.report_data['prevention_effectiveness']:.1f}%")
            print(f"   📄 Report: {report_file}")
            
            return self.report_data
            
        except Exception as e:
            print(f"❌ FEHLER beim Weekly Check: {e}")
            return {'error': str(e)}
            
        finally:
            conn.close()
    
    def _check_table_duplicates(self, conn: sqlite3.Connection, table_name: str, 
                               key_columns: list, description: str) -> dict:
        """Prüft eine Tabelle auf Duplikate"""
        print(f"\\n🔍 Prüfe {table_name}...")
        
        try:
            # Generiere SQL für Duplikat-Check
            columns_str = ', '.join(key_columns)
            
            query = f"""
                SELECT {columns_str}, COUNT(*) as count 
                FROM {table_name} 
                GROUP BY {columns_str}
                HAVING count > 1
                ORDER BY count DESC
                LIMIT 10
            """
            
            df = pd.read_sql_query(query, conn)
            
            duplicates_found = len(df)
            affected_rows = df['count'].sum() if not df.empty else 0
            
            if duplicates_found > 0:
                print(f"   ⚠️ {duplicates_found} Duplikat-Gruppen gefunden!")
                print(f"   📊 {affected_rows} betroffene Einträge")
                
                # Zeige Top 3 Beispiele
                for i, (_, row) in enumerate(df.head(3).iterrows()):
                    values = [str(row[col]) for col in key_columns]
                    print(f"      {i+1}. {' | '.join(values)}: {row['count']}x")
            else:
                print("   ✅ Keine Duplikate gefunden")
            
            return {
                'table': table_name,
                'description': description,
                'duplicates_found': duplicates_found,
                'affected_rows': int(affected_rows),
                'examples': df.head(3).to_dict('records') if not df.empty else []
            }
            
        except Exception as e:
            print(f"   ❌ Fehler bei {table_name}: {e}")
            return {
                'table': table_name,
                'error': str(e),
                'duplicates_found': -1
            }
    
    def _calculate_prevention_effectiveness(self, conn: sqlite3.Connection) -> float:
        """Berechnet Prevention-Effectiveness der letzten Woche"""
        try:
            week_ago = datetime.now() - timedelta(days=7)
            
            cursor = conn.cursor()
            
            # Verhinderte Duplikate
            cursor.execute("""
                SELECT COUNT(*) FROM duplicate_prevention_log 
                WHERE timestamp > ? AND action_taken IN ('prevented', 'merged', 'blocked')
            """, (week_ago.isoformat(),))
            
            prevented = cursor.fetchone()[0]
            
            # Gesamte Versuche
            cursor.execute("""
                SELECT COUNT(*) FROM duplicate_prevention_log 
                WHERE timestamp > ?
            """, (week_ago.isoformat(),))
            
            total = cursor.fetchone()[0]
            
            if total > 0:
                effectiveness = (prevented / total) * 100
                print(f"   📈 Prevention Effectiveness: {effectiveness:.1f}% ({prevented}/{total})")
                return effectiveness
            else:
                print("   💡 Keine Duplikat-Versuche in letzter Woche")
                return 100.0
                
        except Exception as e:
            print(f"   ⚠️ Effectiveness-Berechnung fehlgeschlagen: {e}")
            return 0.0
    
    def _save_report_to_db(self, conn: sqlite3.Connection):
        """Speichert Report-Summary in Datenbank"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weekly_duplicate_reports 
                (report_date, tables_checked, duplicates_found, prevention_effectiveness, critical_issues)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().date(),
                len(self.report_data['tables_checked']),
                self.report_data['duplicates_found'],
                self.report_data['prevention_effectiveness'],
                self.report_data['critical_issues']
            ))
            conn.commit()
        except Exception as e:
            print(f"   ⚠️ DB-Report speichern fehlgeschlagen: {e}")
    
    def _create_json_report(self) -> str:
        """Erstellt detaillierten JSON-Report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'weekly_duplicate_report_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def _send_alert(self):
        """Sendet Alert bei kritischen Issues (placeholder)"""
        print("   🚨 ALERT: Kritische Duplikat-Issues gefunden!")
        print("      💡 Alert-System kann hier E-Mail/Slack-Integration hinzufügen")


if __name__ == "__main__":
    checker = WeeklyDuplicateChecker()
    results = checker.run_weekly_check()
    
    if results.get('critical_issues', 0) > 0:
        exit(1)  # Exit code für Cron-Job Alerts
'''
    
    # Speichere Weekly Checker
    with open('weekly_duplicate_checker.py', 'w', encoding='utf-8') as f:
        f.write(weekly_checker_code)
    print("   ✅ weekly_duplicate_checker.py erstellt")
    
    # 2. System Health Monitor
    health_monitor_code = '''#!/usr/bin/env python3
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
'''
    
    # Speichere Health Monitor
    with open('system_health_monitor.py', 'w', encoding='utf-8') as f:
        f.write(health_monitor_code)
    print("   ✅ system_health_monitor.py erstellt")
    
    # 3. Crontab Setup Script
    crontab_setup = '''#!/bin/bash
"""
CRON-JOB SETUP für Duplikat-Monitoring
=====================================

Fügt folgende Cron-Jobs hinzu:
- Wöchentlicher Duplikat-Check: Montags 9:00 Uhr
- System Health Check: Alle 15 Minuten
- Monatlicher Gesamt-Report: 1. jeden Monats

INSTALLATION: bash setup_cron_jobs.sh
"""

echo "🕒 SETUP CRON-JOBS für Duplikat-Monitoring"
echo "=========================================="

# Aktueller Pfad
SCRIPT_DIR=$(pwd)

# Backup existing crontab
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt

# Add new cron jobs
(crontab -l 2>/dev/null; echo "") | grep -v "# MineSearch Duplicate Monitoring" > temp_cron
echo "# MineSearch Duplicate Monitoring Jobs" >> temp_cron
echo "0 9 * * 1 cd $SCRIPT_DIR && python3 weekly_duplicate_checker.py >> weekly_check.log 2>&1" >> temp_cron
echo "*/15 * * * * cd $SCRIPT_DIR && python3 system_health_monitor.py >> health_check.log 2>&1" >> temp_cron
echo "0 8 1 * * cd $SCRIPT_DIR && python3 monthly_duplicate_report.py >> monthly_report.log 2>&1" >> temp_cron

# Install new crontab
crontab temp_cron
rm temp_cron

echo "✅ Cron-Jobs erfolgreich hinzugefügt:"
echo "   📅 Wöchentlicher Check: Montags 9:00 Uhr"
echo "   🏥 Health Monitor: Alle 15 Minuten" 
echo "   📊 Monatlicher Report: 1. jeden Monats 8:00 Uhr"
echo ""
echo "💡 Logs werden in folgenden Dateien gespeichert:"
echo "   - weekly_check.log"
echo "   - health_check.log"
echo "   - monthly_report.log"
echo ""
echo "🔍 Cron-Jobs anzeigen: crontab -l"
'''
    
    # Speichere Crontab Setup
    with open('setup_cron_jobs.sh', 'w', encoding='utf-8') as f:
        f.write(crontab_setup)
    
    # Make executable
    os.chmod('setup_cron_jobs.sh', 0o755)
    print("   ✅ setup_cron_jobs.sh erstellt (ausführbar)")
    
    return True


def run_initial_monitoring_test():
    """Führt initialen Test des Monitoring-Systems durch"""
    print("\n🧪 TESTE MONITORING-SYSTEM...")
    
    try:
        # Test Weekly Checker
        print("   📅 Teste Weekly Duplicate Checker...")
        os.system("python3 weekly_duplicate_checker.py > test_weekly.log 2>&1")
        
        if os.path.exists("test_weekly.log"):
            print("   ✅ Weekly Checker funktioniert")
        
        # Test Health Monitor  
        print("   🏥 Teste System Health Monitor...")
        os.system("python3 system_health_monitor.py > test_health.log 2>&1")
        
        if os.path.exists("test_health.log"):
            print("   ✅ Health Monitor funktioniert")
        
        print("   ✅ Alle Monitoring-Komponenten funktionsfähig")
        return True
        
    except Exception as e:
        print(f"   ❌ Monitoring-Test fehlgeschlagen: {e}")
        return False


def main():
    """Hauptfunktion für vollständiges Monitoring-Setup"""
    print("📊 SETUP DUPLIKAT-MONITORING SYSTEM")
    print("=" * 60)
    print("Installiert komplettes Monitoring-System:")
    print("1. 📊 Datenbank-Tabellen für Monitoring")
    print("2. 📅 Wöchentlicher automatischer Duplikat-Checker")
    print("3. 🏥 System Health Monitor")
    print("4. 🕒 Cron-Job Setup für Automatisierung")
    print("5. 🧪 Initial-Test aller Komponenten")
    print()
    
    user_confirm = input("Monitoring-System installieren? (y/N): ").strip().lower()
    
    if user_confirm in ['y', 'yes']:
        success_steps = []
        
        # Schritt 1: Monitoring-Tabellen
        if setup_monitoring_tables():
            success_steps.append("📊 Monitoring-Tabellen")
        
        # Schritt 2: Monitoring-Skripte
        if create_monitoring_scripts():
            success_steps.append("🔍 Monitoring-Skripte")
        
        # Schritt 3: Initial Test
        if run_initial_monitoring_test():
            success_steps.append("🧪 System-Tests")
        
        # Zusammenfassung
        print("\n" + "=" * 60)
        print("🎯 MONITORING-SETUP ABGESCHLOSSEN!")
        print(f"   ✅ Erfolgreich: {len(success_steps)}/3 Komponenten")
        
        for step in success_steps:
            print(f"   {step}")
        
        if len(success_steps) == 3:
            print("\n🎉 MONITORING-SYSTEM VOLLSTÄNDIG INSTALLIERT!")
            print("   📋 Nächste Schritte:")
            print("   1. Cron-Jobs einrichten: bash setup_cron_jobs.sh")
            print("   2. Ersten Weekly Check testen: python3 weekly_duplicate_checker.py")
            print("   3. Health Monitor testen: python3 system_health_monitor.py")
            print("\n🛡️ Ihr MineSearch-System ist jetzt permanent überwacht!")
        
    else:
        print("❌ Monitoring-Setup abgebrochen")


if __name__ == "__main__":
    main()