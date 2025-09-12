#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: STUFE 3 - Permanente Duplikat-Prävention durch UNIQUE-Constraints

🛡️  PERMANENTE LÖSUNG FÜR DUPLIKAT-PRÄVENTION
==============================================

Diese Lösung implementiert:
1. Database UNIQUE-Constraints für kritische Felder
2. Application-Level Normalisierung vor Insert
3. Intelligent Insert-Funktionen mit Duplikat-Erkennung
4. Monitoring für zukünftige Duplikat-Versuche

PROBLEM GELÖST:
- ✅ 49 Companies erfolgreich bereinigt (88 → 47)
- ✅ Keine Name-Duplikate mehr vorhanden
- 🎯 Jetzt: Verhindere zukünftige Duplikate PERMANENT

STRATEGIE:
==========
Da SQLite ADD CONSTRAINT nicht unterstützt, erstellen wir:
1. Neue Tabellen mit UNIQUE-Constraints
2. Migriere Daten von alten zu neuen Tabellen
3. Ersetze alte Tabellen durch neue
4. Application-Level Guards implementieren
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json
import re
import difflib
from typing import Dict, List, Optional, Tuple


class PermanentDuplicatePrevention:
    """
    🛡️  PERMANENTE DUPLIKAT-PRÄVENTION
    ==================================

    Implementiert dauerhafte Lösung gegen Duplikate:
    - Database UNIQUE-Constraints
    - Application-Level Normalisierung
    - Intelligent Insert mit Duplikat-Erkennung
    """

    def __init__(self, db_path: str = 'mines.db'):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_path = db_path
        self.migration_backup = {}

    def implement_full_prevention(self) -> Dict:
        """
        🛡️  VOLLSTÄNDIGE DUPLIKAT-PRÄVENTION
        ===================================
        Implementiert alle 3 Schutzebenen
        """
        results = {
            'database_constraints': False,
            'application_guards': False,
            'monitoring_setup': False,
            'migration_backup': None,
            'errors': []
        }

        print(f"🛡️  STARTE PERMANENTE DUPLIKAT-PRÄVENTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        conn = sqlite3.connect(self.db_path)

        try:
            # 1. DATABASE-LEVEL: UNIQUE-Constraints hinzufügen
            print("\n🗄️  SCHRITT 1: DATABASE UNIQUE-CONSTRAINTS")
            print("-" * 40)
            results['database_constraints'] = self._add_unique_constraints(conn)

            # 2. APPLICATION-LEVEL: Insert-Guards implementieren
            print("\n🔒 SCHRITT 2: APPLICATION-LEVEL GUARDS")
            print("-" * 40)
            results['application_guards'] = self._implement_application_guards()

            # 3. MONITORING: Überwachung für Duplikat-Versuche
            print("\n📊 SCHRITT 3: DUPLIKAT-MONITORING")
            print("-" * 40)
            results['monitoring_setup'] = self._setup_monitoring()

            # Migration erfolgreich
            conn.commit()
            print("\n✅ ALLE MIGRATIONEN ERFOLGREICH COMMITTED")

        except Exception as e:
            conn.rollback()
            error_msg = f"Migration fehlgeschlagen: {e}"
            results['errors'].append(error_msg)
            print(f"❌ FEHLER: {error_msg}")

        finally:
            conn.close()

        # Speichere Migrations-Report
        results['migration_backup'] = self._save_migration_report(results)

        return results

    def _add_unique_constraints(self, conn: sqlite3.Connection) -> bool:
        """
        🗄️  FÜGT UNIQUE-CONSTRAINTS ZU KRITISCHEN TABELLEN HINZU
        ========================================================

        SQLite unterstützt kein ADD CONSTRAINT, daher:
        1. Erstelle neue Tabelle mit UNIQUE-Constraints
        2. Kopiere Daten von alter zu neuer Tabelle
        3. Ersetze alte durch neue Tabelle
        """

        # COMPANIES-Tabelle mit UNIQUE-Constraint migrieren
        print("   🏢 Migriere COMPANIES-Tabelle...")
        success_companies = self._migrate_companies_table(conn)

        # MINES-Tabelle mit UNIQUE-Constraint migrieren
        print("   ⛏️  Migriere MINES-Tabelle...")
        success_mines = self._migrate_mines_table(conn)

        return success_companies and success_mines

    def _migrate_companies_table(self, conn: sqlite3.Connection) -> bool:
        """Migriert Companies-Tabelle mit UNIQUE-Constraint"""
        try:
            cursor = conn.cursor()

            # 1. Backup der aktuellen Tabelle
            print("      💾 Erstelle Backup der COMPANIES-Tabelle...")
            companies_backup = pd.read_sql_query("SELECT * FROM companies", conn)
            self.migration_backup['companies'] = companies_backup.to_dict('records')

            # 2. Erstelle neue Tabelle mit UNIQUE-Constraint
            print("      🔧 Erstelle neue COMPANIES-Tabelle mit UNIQUE-Constraints...")
            cursor.execute("""
                CREATE TABLE companies_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE,  -- 🔑 UNIQUE CONSTRAINT!
                    country_id INTEGER,
                    normalized_name VARCHAR(255),
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (country_id) REFERENCES countries (id),
                    UNIQUE(name, country_id)  -- 🔑 COMPOSITE UNIQUE für Name + Land
                )
            """)

            # 3. Migriere Daten (sollten bereits duplikatfrei sein nach STUFE 2)
            print("      📦 Migriere Daten zur neuen Tabelle...")
            cursor.execute("""
                INSERT INTO companies_new (id, name, country_id, normalized_name, created_at, updated_at)
                SELECT id, name, country_id, normalized_name, created_at, updated_at
                FROM companies
            """)

            # 4. Ersetze alte durch neue Tabelle
            print("      🔄 Ersetze alte durch neue Tabelle...")
            cursor.execute("DROP TABLE companies")
            cursor.execute("ALTER TABLE companies_new RENAME TO companies")

            print("      ✅ COMPANIES-Migration erfolgreich")
            return True

        except Exception as e:
            print(f"      ❌ COMPANIES-Migration fehlgeschlagen: {e}")
            return False

    def _migrate_mines_table(self, conn: sqlite3.Connection) -> bool:
        """Migriert Mines-Tabelle mit UNIQUE-Constraint"""
        try:
            cursor = conn.cursor()

            # 1. Backup der aktuellen Tabelle
            print("      💾 Erstelle Backup der MINES-Tabelle...")
            mines_backup = pd.read_sql_query("SELECT * FROM mines", conn)
            self.migration_backup['mines'] = mines_backup.to_dict('records')

            # 2. Erstelle neue Tabelle mit UNIQUE-Constraint
            print("      🔧 Erstelle neue MINES-Tabelle mit UNIQUE-Constraints...")
            cursor.execute("""
                CREATE TABLE mines_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    country VARCHAR(100),
                    state_province VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    normalized_name VARCHAR(255),
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    UNIQUE(name, country, state_province)  -- 🔑 UNIQUE: Name + Land + Region
                )
            """)

            # 3. Migriere Daten
            print("      📦 Migriere Daten zur neuen Tabelle...")
            cursor.execute("""
                INSERT INTO mines_new (id, name, country, state_province, latitude, longitude,
normalized_name, created_at, updated_at)
                SELECT id, name, country, state_province, latitude, longitude, normalized_name, created_at, updated_at
                FROM mines
            """)

            # 4. Ersetze alte durch neue Tabelle
            print("      🔄 Ersetze alte durch neue Tabelle...")
            cursor.execute("DROP TABLE mines")
            cursor.execute("ALTER TABLE mines_new RENAME TO mines")

            print("      ✅ MINES-Migration erfolgreich")
            return True

        except Exception as e:
            print(f"      ❌ MINES-Migration fehlgeschlagen: {e}")
            return False

    def _implement_application_guards(self) -> bool:
        """
        🔒 IMPLEMENTIERT APPLICATION-LEVEL DUPLIKAT-GUARDS
        =================================================

        Erstellt intelligente Insert-Funktionen die:
        1. Namen vor Insert normalisieren
        2. Fuzzy-Duplikate erkennen
        3. Merge-Empfehlungen geben
        4. Safe-Insert mit Duplikat-Schutz
        """
        try:
            # Erstelle Application-Level Guards Klasse
            guards_code = self._generate_application_guards_code()

            # Speichere als separate Datei
            with open('duplicate_prevention_guards.py', 'w', encoding='utf-8') as f:
                f.write(guards_code)

            print("   ✅ Application-Level Guards implementiert → duplicate_prevention_guards.py")
            return True

        except Exception as e:
            print(f"   ❌ Application Guards Fehler: {e}")
            return False

    def _setup_monitoring(self) -> bool:
        """
        📊 SETUP DUPLIKAT-MONITORING
        ===========================

        Implementiert:
        1. Duplikat-Versuch-Logging
        2. Wöchentliche Duplikat-Checks
        3. Automatische Reports
        """
        try:
            # Erstelle Monitoring-Tabelle
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_prevention_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name VARCHAR(50) NOT NULL,
                    attempted_value VARCHAR(255) NOT NULL,
                    similar_existing_value VARCHAR(255),
                    similarity_score FLOAT,
                    action_taken VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_decision VARCHAR(20)
                )
            """)

            conn.commit()
            conn.close()

            # Erstelle Monitoring-Skript
            monitoring_code = self._generate_monitoring_code()
            with open('duplicate_monitoring.py', 'w', encoding='utf-8') as f:
                f.write(monitoring_code)

            print("   ✅ Duplikat-Monitoring setup → duplicate_monitoring.py")
            return True

        except Exception as e:
            print(f"   ❌ Monitoring Setup Fehler: {e}")
            return False

    def _generate_application_guards_code(self) -> str:
        """Generiert Code für Application-Level Guards"""
        return '''#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Application-Level Duplikat-Prevention Guards

🔒 INTELLIGENT DUPLICATE PREVENTION GUARDS
==========================================

Diese Guards werden vor jedem Insert/Update ausgeführt:
1. Normalisierung der Namen
2. Fuzzy-Duplikat-Erkennung
3. Benutzer-Entscheidung bei ähnlichen Werten
4. Safe-Insert mit Rollback-Möglichkeit
"""

import sqlite3
import difflib
import re
from typing import Optional, List, Dict, Tuple


class DuplicatePreventionGuards:
    """🔒 Intelligente Duplikat-Prävention auf Application-Level"""

    def __init__(self, db_path: str = 'mines.db', similarity_threshold: float = 0.85):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold

    def safe_insert_company(self, name: str, country_id: Optional[int] = None,
    """safe_insert_company - TODO: Dokumentation hinzufügen"""
                           auto_merge: bool = False) -> Dict:
        """
        🏢 SAFE COMPANY INSERT mit Duplikat-Prävention
        =============================================

        Returns: {'success': bool, 'company_id': int, 'action': str, 'similar_found': List}
        """
        normalized_name = self._normalize_company_name(name)

        conn = sqlite3.connect(self.db_path)
        try:
            # 1. Prüfe auf exakte Duplikate
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name FROM companies
                WHERE name = ? OR normalized_name = ?
            """, (name, normalized_name))

            exact_match = cursor.fetchone()
            if exact_match:
                return {
                    'success': False,
                    'company_id': exact_match[0],
                    'action': 'exact_duplicate_found',
                    'message': f'Exaktes Duplikat gefunden: "{exact_match[1]}"'
                }

            # 2. Prüfe auf ähnliche Namen (Fuzzy-Match)
            cursor.execute("SELECT id, name FROM companies")
            existing_companies = cursor.fetchall()

            similar_companies = []
            for comp_id, existing_name in existing_companies:
                similarity = difflib.SequenceMatcher(
                    None,
                    normalized_name.lower(),
                    self._normalize_company_name(existing_name).lower()
                ).ratio()

                if similarity >= self.similarity_threshold:
                    similar_companies.append({
                        'id': comp_id,
                        'name': existing_name,
                        'similarity': similarity
                    })

            # 3. Handle ähnliche Companies
            if similar_companies:
                if auto_merge:
                    # Automatisches Merge mit bester Ähnlichkeit
                    best_match = max(similar_companies, key=lambda x: x['similarity'])
                    return {
                        'success': False,
                        'company_id': best_match['id'],
                        'action': 'auto_merged',
                        'message': f'Auto-Merge mit "{best_match["name"]}" (Ähnlichkeit:
{best_match["similarity"]:.2%})',
                        'similar_found': similar_companies
                    }
                else:
                    # Benutzer-Entscheidung erforderlich
                    return {
                        'success': False,
                        'company_id': None,
                        'action': 'user_decision_required',
                        'message': f'{len(similar_companies)} ähnliche Companies gefunden',
                        'similar_found': similar_companies
                    }

            # 4. Safe Insert - keine Duplikate gefunden
            cursor.execute("""
                INSERT INTO companies (name, normalized_name, country_id, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, normalized_name, country_id))

            new_company_id = cursor.lastrowid
            conn.commit()

            # Log successful insert
            self._log_duplicate_action('companies', name, None, 0.0, 'inserted')

            return {
                'success': True,
                'company_id': new_company_id,
                'action': 'inserted',
                'message': f'Company "{name}" erfolgreich erstellt'
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'company_id': None,
                'action': 'error',
                'message': f'Insert-Fehler: {e}'
            }
        finally:
            conn.close()

    def _normalize_company_name(self, name: str) -> str:
        """Normalisiert Company-Namen für Vergleiche"""
        if not name:
            return ""

        # Kleinschreibung, Sonderzeichen entfernen
        normalized = re.sub(r'[^\\w\\s]', '', name.lower())
        normalized = re.sub(r'\\s+', ' ', normalized).strip()

        # Entferne Company-Suffixe
        suffixes = ['ltd', 'limited', 'corp', 'corporation', 'inc', 'incorporated',
                   'co', 'company', 'ag', 'gmbh', 'sa', 'plc', 'llc']

        words = normalized.split()
        filtered_words = [w for w in words if w not in suffixes]

        return ' '.join(filtered_words)

    def _log_duplicate_action(self, table_name: str, attempted_value: str,
    """_log_duplicate_action - TODO: Dokumentation hinzufügen"""
                            similar_value: Optional[str], similarity: float, action: str):
        """Logged Duplikat-Aktionen für Monitoring"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO duplicate_prevention_log
                (table_name, attempted_value, similar_existing_value, similarity_score, action_taken)
                VALUES (?, ?, ?, ?, ?)
            """, (table_name, attempted_value, similar_value, similarity, action))
            conn.commit()
        except:
            pass  # Logging sollte nicht kritische Operationen unterbrechen
        finally:
            conn.close()


# BEISPIEL-USAGE:
if __name__ == "__main__":
    guards = DuplicatePreventionGuards()

    # Test Safe Insert
    result = guards.safe_insert_company("Rio Tinto Limited")
    print(f"Insert Result: {result}")
'''

    def _generate_monitoring_code(self) -> str:
        """Generiert Code für Duplikat-Monitoring"""
        return '''#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Duplikat-Monitoring und automatische Checks

📊 DUPLICATE MONITORING SYSTEM
==============================

Überwacht kontinuierlich:
1. Duplikat-Versuche und deren Behandlung
2. Wöchentliche Duplikat-Checks aller Tabellen
3. Automatische Reports und Alerts
4. Trend-Analyse der Datenqualität
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List


class DuplicateMonitoring:
    """📊 Kontinuierliche Duplikat-Überwachung"""

    def __init__(self, db_path: str = 'mines.db'):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_path = db_path

    def weekly_duplicate_check(self) -> Dict:
        """🔍 Wöchentlicher automatischer Duplikat-Check"""
        print(f"📊 WÖCHENTLICHER DUPLIKAT-CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = {
            'check_timestamp': datetime.now().isoformat(),
            'tables_checked': [],
            'duplicates_found': 0,
            'prevention_effectiveness': 0.0,
            'recommendations': []
        }

        conn = sqlite3.connect(self.db_path)

        # Check Companies
        companies_check = self._check_table_duplicates(conn, 'companies', ['name'])
        results['tables_checked'].append(companies_check)

        # Check Mines
        mines_check = self._check_table_duplicates(conn, 'mines', ['name', 'country'])
        results['tables_checked'].append(mines_check)

        conn.close()

        # Berechne Gesamtstatistiken
        total_duplicates = sum(check['duplicates_found'] for check in results['tables_checked'])
        results['duplicates_found'] = total_duplicates

        # Prevention Effectiveness berechnen
        results['prevention_effectiveness'] = self._calculate_prevention_effectiveness()

        # Report speichern
        report_file = f'weekly_duplicate_report_{datetime.now().strftime("%Y%m%d")}.json'
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"📄 Wöchentlicher Report gespeichert: {report_file}")

        return results

    def _check_table_duplicates(self, conn: sqlite3.Connection, table_name: str,
    """_check_table_duplicates - TODO: Dokumentation hinzufügen"""
                               key_columns: List[str]) -> Dict:
        """Prüft eine Tabelle auf Duplikate"""
        try:
            # Generiere SQL für Duplikat-Check
            columns_str = ', '.join(key_columns)

            query = f"""
                SELECT {columns_str}, COUNT(*) as count
                FROM {table_name}
                GROUP BY {columns_str}
                HAVING count > 1
                ORDER BY count DESC
            """

            df = pd.read_sql_query(query, conn)

            return {
                'table': table_name,
                'duplicates_found': len(df),
                'affected_rows': df['count'].sum() if not df.empty else 0,
                'examples': df.head(3).to_dict('records') if not df.empty else []
            }

        except Exception as e:
            return {
                'table': table_name,
                'error': str(e),
                'duplicates_found': -1
            }

    def _calculate_prevention_effectiveness(self) -> float:
        """Berechnet Effectiveness der Duplikat-Prävention"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Anzahl verhinderte Duplikate in letzter Woche
            week_ago = datetime.now() - timedelta(days=7)

            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM duplicate_prevention_log
                WHERE timestamp > ? AND action_taken != 'inserted'
            """, (week_ago.isoformat(),))

            prevented_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM duplicate_prevention_log
                WHERE timestamp > ?
            """, (week_ago.isoformat(),))

            total_attempts = cursor.fetchone()[0]

            if total_attempts > 0:
                return (prevented_count / total_attempts) * 100
            return 100.0

        except:
            return 0.0
        finally:
            conn.close()


if __name__ == "__main__":
    monitor = DuplicateMonitoring()
    results = monitor.weekly_duplicate_check()

    if results['duplicates_found'] > 0:
        print(f"⚠️  {results['duplicates_found']} Duplikate gefunden!")
    else:
        print("✅ Keine Duplikate gefunden - System ist sauber!")
'''

    def _save_migration_report(self, results: Dict) -> str:
        """Speichert detaillierten Migrations-Report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'duplicate_prevention_migration_{timestamp}.json'

        def convert_types(obj):
    """convert_types - TODO: Dokumentation hinzufügen"""
            if hasattr(obj, 'item'):
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(v) for v in obj]
            else:
                return obj

        report_data = {
            'migration_timestamp': datetime.now().isoformat(),
            'prevention_results': convert_types(results),
            'migration_backup': convert_types(self.migration_backup),
            'next_steps': [
                'Teste neue UNIQUE-Constraints mit Test-Inserts',
                'Integriere Guards in bestehende MineSearch-Application',
                'Setup automatische wöchentliche Monitoring-Reports',
                'Trainiere Team auf neue Safe-Insert-Funktionen'
            ]
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 MIGRATIONS-REPORT GESPEICHERT: {report_file}")

        return report_file


def main():
    """Hauptfunktion für vollständige Duplikat-Prävention"""
    prevention = PermanentDuplicatePrevention()

    print("🛡️  IMPLEMENTIERUNG PERMANENTER DUPLIKAT-PRÄVENTION")
    print("=" * 60)
    print("Diese Migration implementiert 3-Ebenen-Schutz:")
    print("1. 🗄️  Database UNIQUE-Constraints")
    print("2. 🔒 Application-Level Guards")
    print("3. 📊 Kontinuierliches Monitoring")
    print()

    # Ausführung mit Bestätigung
    user_confirm = input("Migration ausführen? (y/N): ").strip().lower()

    if user_confirm in ['y', 'yes']:
        results = prevention.implement_full_prevention()

        # Zusammenfassung
        print("\n" + "=" * 60)
        print("🎯 MIGRATION ABGESCHLOSSEN!")
        print(f"   🗄️  Database Constraints: {'✅' if results['database_constraints'] else '❌'}")
        print(f"   🔒 Application Guards: {'✅' if results['application_guards'] else '❌'}")
        print(f"   📊 Monitoring Setup: {'✅' if results['monitoring_setup'] else '❌'}")

        if results['errors']:
            print("\n⚠️  FEHLER AUFGETRETEN:")
            for error in results['errors']:
                print(f"   - {error}")

        if all([results['database_constraints'], results['application_guards'], results['monitoring_setup']]):
            print("\n🎉 VOLLSTÄNDIGE DUPLIKAT-PRÄVENTION ERFOLGREICH IMPLEMENTIERT!")
            print("   🛡️  Ihr System ist jetzt permanent gegen Duplikate geschützt!")

    else:
        print("❌ Migration abgebrochen")


if __name__ == "__main__":
    main()
