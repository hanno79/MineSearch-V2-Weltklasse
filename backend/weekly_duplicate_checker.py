#!/usr/bin/env python3
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
from email.mime.text import MIMEText


class WeeklyDuplicateChecker:
    """📅 Automatischer wöchentlicher Duplikat-Checker"""

    def __init__(self, db_path: str = 'mines.db'):
    """__init__ - TODO: Dokumentation hinzufügen"""
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

            print(f"\n✅ WEEKLY CHECK ABGESCHLOSSEN")
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
    """_check_table_duplicates - TODO: Dokumentation hinzufügen"""
                               key_columns: list, description: str) -> dict:
        """Prüft eine Tabelle auf Duplikate"""
        print(f"\n🔍 Prüfe {table_name}...")

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

    if results.get("critical_issues", 0) > 0:
        exit(1)  # Exit code für Cron-Job Alerts
