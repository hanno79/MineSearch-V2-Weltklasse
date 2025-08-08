#!/usr/bin/env python3
"""
Author: rahn
Datum: 24.07.2025
Version: 1.0
Beschreibung: Sichere Datenbankbereinigung für MineSearch v2
ÄNDERUNG 24.07.2025: Erstellt für sichere Bereinigung ohne Schema-Verlust
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Füge Backend-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

from database.connection import get_session
from database.models import Base, Source, Mine, SearchResult, ModelStatistics, FieldConsistency, ModelSummary, FieldStatistics
from sqlalchemy import text
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_cleanup_database():
    """
    Sichere Datenbankbereinigung:
    - Löscht nur Daten, behält Schema bei
    - Behält Tabellenstruktur und Indizes
    - Validiert nach Bereinigung
    """
    
    logger.info("🧹 Starte sichere Datenbankbereinigung...")
    
    try:
        # Datenbank-Session erstellen
        session = get_session()
        
        # 1. Anzahl Datensätze VORHER zählen
        logger.info("📊 Datensätze vor Bereinigung:")
        tables_data = {}
        
        table_classes = [
            ('sources', Source),
            ('mines', Mine), 
            ('search_results', SearchResult),
            ('model_statistics', ModelStatistics),
            ('field_consistency', FieldConsistency),
            ('model_summaries', ModelSummary),
            ('field_statistics', FieldStatistics)
        ]
        
        for table_name, table_class in table_classes:
            try:
                count = session.query(table_class).count()
                tables_data[table_name] = count
                logger.info(f"  {table_name}: {count} Datensätze")
            except Exception as e:
                logger.warning(f"  {table_name}: Tabelle existiert nicht oder Fehler: {e}")
                tables_data[table_name] = 0
        
        total_before = sum(tables_data.values())
        logger.info(f"📈 GESAMT vor Bereinigung: {total_before} Datensätze")
        
        # 2. Sichere Bereinigung - nur Daten, NICHT Schema
        logger.info("🗑️  Bereinige Tabellendaten...")
        
        cleanup_queries = [
            "DELETE FROM field_statistics",
            "DELETE FROM model_summaries", 
            "DELETE FROM field_consistency",
            "DELETE FROM model_statistics",
            "DELETE FROM search_results",
            "DELETE FROM mines",
            "DELETE FROM sources"
        ]
        
        for query in cleanup_queries:
            try:
                result = session.execute(text(query))
                affected_rows = result.rowcount
                table_name = query.split('FROM ')[1].strip()
                logger.info(f"  ✅ {table_name}: {affected_rows} Datensätze gelöscht")
            except Exception as e:
                logger.error(f"  ❌ Fehler bei {query}: {e}")
        
        # 3. Commit der Änderungen
        session.commit()
        logger.info("💾 Änderungen committet")
        
        # 4. Validierung NACH Bereinigung
        logger.info("🔍 Validierung nach Bereinigung:")
        
        total_after = 0
        for table_name, table_class in table_classes:
            try:
                count = session.query(table_class).count()
                total_after += count
                status = "✅" if count == 0 else "⚠️ "
                logger.info(f"  {status} {table_name}: {count} Datensätze")
            except Exception as e:
                logger.warning(f"  ❓ {table_name}: {e}")
        
        logger.info(f"📉 GESAMT nach Bereinigung: {total_after} Datensätze")
        
        # 5. Schema-Validierung
        logger.info("🏗️  Schema-Validierung:")
        
        # Prüfe ob Tabellen noch existieren
        schema_queries = [
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
            "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        ]
        
        tables = session.execute(text(schema_queries[0])).fetchall()
        indices = session.execute(text(schema_queries[1])).fetchall()
        
        logger.info(f"  ✅ Tabellen erhalten: {len(tables)} ({[t[0] for t in tables]})")
        logger.info(f"  ✅ Indizes erhalten: {len(indices)}")
        
        # 6. Erfolgsbestätigung
        if total_after == 0 and len(tables) >= 6:  # Erwarten mindestens 6 Haupttabellen
            logger.info("🎉 BEREINIGUNG ERFOLGREICH!")
            logger.info(f"   📊 {total_before} Datensätze gelöscht")
            logger.info(f"   🏗️  {len(tables)} Tabellen + {len(indices)} Indizes erhalten")
            logger.info("   ✅ Datenbank bereit für sauberen Start")
            return True
        else:
            logger.error("❌ BEREINIGUNG UNVOLLSTÄNDIG!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler: {e}")
        try:
            if 'session' in locals():
                session.rollback()
        except:
            pass
        return False
    finally:
        try:
            if 'session' in locals():
                session.close()
        except:
            pass

def verify_backup_exists():
    """Prüft ob Backup existiert vor Bereinigung"""
    backup_dir = Path("backups")
    if not backup_dir.exists():
        logger.error("❌ Kein Backup-Verzeichnis gefunden!")
        return False
    
    backups = list(backup_dir.glob("mines_backup_*.db"))
    if not backups:
        logger.error("❌ Kein Backup gefunden!")
        return False
    
    latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
    backup_age = datetime.now().timestamp() - latest_backup.stat().st_mtime
    
    if backup_age > 300:  # 5 Minuten
        logger.warning("⚠️  Backup ist älter als 5 Minuten")
    
    logger.info(f"✅ Backup gefunden: {latest_backup.name}")
    return True

if __name__ == "__main__":
    print("🧹 MineSearch v2 - Sichere Datenbankbereinigung")
    print("=" * 50)
    
    # Backup-Prüfung
    if not verify_backup_exists():
        print("❌ Kein aktuelles Backup gefunden. Bereinigung abgebrochen.")
        sys.exit(1)
    
    # Benutzerbestätigung
    response = input("⚠️  ACHTUNG: Alle Daten werden gelöscht (Schema bleibt erhalten).\n   Fortfahren? (ja/nein): ")
    
    if response.lower() not in ['ja', 'j', 'yes', 'y']:
        print("❌ Bereinigung abgebrochen.")
        sys.exit(0)
    
    # Bereinigung durchführen
    success = safe_cleanup_database()
    
    if success:
        print("\n🎉 BEREINIGUNG ABGESCHLOSSEN!")
        print("   Die Datenbank ist jetzt sauber und bereit für neue Tests.")
        sys.exit(0)
    else:
        print("\n❌ BEREINIGUNG FEHLGESCHLAGEN!")
        print("   Backup kann wiederhergestellt werden aus backups/")
        sys.exit(1)