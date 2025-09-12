#!/usr/bin/env python3
"""
DATENBANK BACKUP CREATOR
Erstellt Sicherheits-Backups aller aktiven Datenbanken vor Konsolidierung

Author: rahn
Datum: 20.08.2025
Version: 1.0
"""

import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# Liste der identifizierten aktiven Datenbanken (aus vorheriger Analyse)
# ÄNDERUNG 28.08.2025: Konsolidierung auf eine Datenbank
ACTIVE_DATABASES = [
    '/app/backend/minesearch/database/mines.db',  # Einzige produktive Datenbank
    '/app/.claude-flow/metrics/memory.db',
    '/app/.swarm/memory.db',
    '/app/.claude-flow/knowledge.db'
]

def verify_database_integrity(db_path):
    """Verifiziert die Integrität einer Datenbank"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # PRAGMA integrity_check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]

        conn.close()

        return result == 'ok'
    except Exception as e:
        print(f"❌ Integritätsprüfung fehlgeschlagen für {db_path}: {e}")
        return False

def create_backup(source_path, backup_dir):
    """Erstellt ein Backup einer Datenbank"""
    if not os.path.exists(source_path):
        print(f"⚠️  Quelle nicht gefunden: {source_path}")
        return None

    # Integrität prüfen vor Backup
    if not verify_database_integrity(source_path):
        print(f"❌ Integritätsprüfung fehlgeschlagen: {source_path}")
        return None

    # Backup-Dateinamen erstellen
    source_name = Path(source_path).name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{source_name}_backup_consolidation_{timestamp}"
    backup_path = backup_dir / backup_name

    try:
        # SQLite BACKUP API verwenden für saubere Kopie
        source_conn = sqlite3.connect(source_path)
        backup_conn = sqlite3.connect(str(backup_path))

        # Online Backup
        source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()

        # Backup-Integrität prüfen
        if verify_database_integrity(str(backup_path)):
            size_mb = os.path.getsize(str(backup_path)) / (1024 * 1024)
            print(f"✅ Backup erstellt: {backup_name} ({size_mb:.2f} MB)")
            return str(backup_path)
        else:
            print(f"❌ Backup-Integrität fehlgeschlagen: {backup_name}")
            if backup_path.exists():
                backup_path.unlink()
            return None

    except Exception as e:
        print(f"❌ Backup-Erstellung fehlgeschlagen für {source_path}: {e}")
        return None

def analyze_backup_requirements():
    """Analysiert Backup-Anforderungen"""
    print("🔍 BACKUP-ANFORDERUNGEN ANALYSE")
    print("=" * 50)

    total_size = 0
    active_count = 0

    for db_path in ACTIVE_DATABASES:
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            total_size += size_mb
            active_count += 1

            print(f"📄 {db_path}")
            print(f"   Größe: {size_mb:.2f} MB")

            # Analysiere Tabellen
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"   Tabellen: {len(tables)}")

                for table in tables[:3]:  # Erste 3 Tabellen
                    table_name = table[0]
                    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                    count = cursor.fetchone()[0]
                    print(f"     • {table_name}: {count} Einträge")

                conn.close()
            except Exception as e:
                print(f"   ❌ Analyse-Fehler: {e}")
        else:
            print(f"❌ Nicht gefunden: {db_path}")

    print()
    print(f"📊 BACKUP-ÜBERSICHT:")
    print(f"   Aktive DBs: {active_count}/{len(ACTIVE_DATABASES)}")
    print(f"   Gesamtgröße: {total_size:.2f} MB")
    print(f"   Geschätzte Backup-Zeit: {total_size * 0.1:.1f} Sekunden")

    return active_count, total_size

def main():
    """main - TODO: Dokumentation hinzufügen"""
    print("🔒 DATENBANK KONSOLIDIERUNG - BACKUP PHASE")
    print("=" * 60)
    print(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Backup-Verzeichnis erstellen
    backup_dir = Path('/app/database_backups_consolidation')
    backup_dir.mkdir(exist_ok=True)

    print(f"📁 Backup-Verzeichnis: {backup_dir}")
    print()

    # Analysiere Backup-Anforderungen
    active_count, total_size = analyze_backup_requirements()

    if active_count == 0:
        print("❌ Keine aktiven Datenbanken gefunden!")
        return

    print()
    print("🚀 BACKUP-ERSTELLUNG STARTET...")
    print("-" * 40)

    successful_backups = []
    failed_backups = []

    for i, db_path in enumerate(ACTIVE_DATABASES, 1):
        print(f"\n[{i}/{len(ACTIVE_DATABASES)}] Backup: {db_path}")

        if os.path.exists(db_path):
            backup_path = create_backup(db_path, backup_dir)
            if backup_path:
                successful_backups.append((db_path, backup_path))
            else:
                failed_backups.append(db_path)
        else:
            print(f"⚠️  Übersprungen: Datei nicht gefunden")

    # Zusammenfassung
    print()
    print("=" * 60)
    print("📋 BACKUP-ZUSAMMENFASSUNG")
    print("=" * 60)

    print(f"✅ Erfolgreiche Backups: {len(successful_backups)}")
    for source, backup in successful_backups:
        backup_size = os.path.getsize(backup) / (1024 * 1024)
        print(f"   📄 {Path(source).name} → {Path(backup).name} ({backup_size:.2f} MB)")

    if failed_backups:
        print(f"\n❌ Fehlgeschlagene Backups: {len(failed_backups)}")
        for failed in failed_backups:
            print(f"   📄 {failed}")

    # Backup-Verzeichnis Info
    if successful_backups:
        total_backup_size = sum(os.path.getsize(backup) for _, backup in successful_backups)
        total_backup_mb = total_backup_size / (1024 * 1024)

        print(f"\n📊 BACKUP-STATISTIK:")
        print(f"   Backup-Verzeichnis: {backup_dir}")
        print(f"   Gesamte Backup-Größe: {total_backup_mb:.2f} MB")
        print(f"   Verfügbarer Speicher: Prüfung empfohlen")

        # Empfehlung für nächste Schritte
        print(f"\n💡 NÄCHSTE SCHRITTE:")
        print("1. ✅ Backups erfolgreich erstellt")
        print("2. 🎯 Primäre Datenbank identifizieren")
        print("3. 📦 Datenmigration durchführen")
        print("4. ⚙️  Konfiguration anpassen")
        print("5. 🧹 Verwaiste Datenbanken entfernen")

        print(f"\n🔒 BACKUP-SICHERHEIT:")
        print("   • Alle Backups mit SQLite BACKUP API erstellt")
        print("   • Integritätsprüfung vor und nach Backup")
        print("   • Zeitstempel für eindeutige Identifikation")
        print("   • Sichere Aufbewahrung in separatem Verzeichnis")

    return len(successful_backups) == active_count

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ALLE BACKUPS ERFOLGREICH ERSTELLT!")
        print("System bereit für Datenmigration.")
    else:
        print("\n⚠️  BACKUP-PROZESS MIT FEHLERN ABGESCHLOSSEN")
        print("Überprüfung erforderlich vor Fortsetzung.")
