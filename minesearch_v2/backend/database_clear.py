#!/usr/bin/env python3
"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Robustes Database-Clear-Script mit Backup-Mechanismus für MineSearch v2

Funktionen:
- Sofortige Datenbank-Bereinigung mit verschiedenen Modi
- Automatisches Backup vor Löschung
- Wiederherstellung aus Backup
- Detaillierte Verifizierung der Bereinigung
- Sichere SQLAlchemy-basierte Operationen
"""

import os
import sys
import json
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Füge Backend-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_db, get_session
from database.models import (
    SearchResult, ModelStatistics, ModelSummary, 
    FieldStatistics, FieldConsistency, Source, Mine
)
from config.base import config as Config


class DatabaseCleaner:
    """Robuste Datenbank-Bereinigung mit Backup-Funktionalität"""
    
    def __init__(self):
        """Initialisierung"""
        self.config = Config()
        self.db_path = self._get_db_path()
        self.backup_dir = Path("database_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Tabellen-Mapping für verschiedene Clear-Modi
        self.table_groups = {
            'all': [SearchResult, ModelStatistics, ModelSummary, FieldStatistics, FieldConsistency],
            'results': [SearchResult],
            'statistics': [ModelStatistics, ModelSummary, FieldStatistics, FieldConsistency],
            'model_stats': [ModelStatistics],
            'summaries': [ModelSummary],
            'field_stats': [FieldStatistics],
            'consistency': [FieldConsistency],
            'sources': [Source],
            'mines': [Mine]
        }
        
        print(f"🔧 DatabaseCleaner initialisiert")
        print(f"📂 Datenbank: {self.db_path}")
        print(f"💾 Backup-Verzeichnis: {self.backup_dir}")
    
    def _get_db_path(self) -> str:
        """Ermittle Datenbank-Pfad aus Config"""
        database_url = self.config.DATABASE_URL
        if database_url.startswith('sqlite:///'):
            return database_url.replace('sqlite:///', '')
        else:
            raise ValueError(f"Nur SQLite-Datenbanken unterstützt: {database_url}")
    
    def get_current_counts(self) -> Dict[str, int]:
        """Hole aktuelle Tabellen-Größen"""
        init_db()
        session = get_session()
        
        try:
            counts = {}
            for group_name, tables in self.table_groups.items():
                if group_name == 'all':
                    continue
                    
                group_count = 0
                for table_class in tables:
                    count = session.query(table_class).count()
                    table_name = table_class.__tablename__
                    counts[table_name] = count
                    group_count += count
                
                if len(tables) > 1:
                    counts[f"{group_name}_total"] = group_count
            
            # Gesamtanzahl
            total = sum(count for key, count in counts.items() 
                       if not key.endswith('_total'))
            counts['grand_total'] = total
            
            return counts
            
        finally:
            session.close()
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Erstelle Backup der Datenbank"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_file = self.backup_dir / f"{backup_name}.db"
        
        print(f"💾 Erstelle Backup: {backup_file}")
        
        try:
            # Kopiere Datenbankdatei
            shutil.copy2(self.db_path, backup_file)
            
            # Erstelle Metadaten-Datei
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'original_path': self.db_path,
                'backup_name': backup_name,
                'counts_before_backup': self.get_current_counts()
            }
            
            metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Backup erfolgreich erstellt: {backup_file}")
            print(f"📋 Metadaten gespeichert: {metadata_file}")
            
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ Backup-Fehler: {e}")
            raise
    
    def restore_backup(self, backup_name: str) -> bool:
        """Stelle Backup wieder her"""
        backup_file = self.backup_dir / f"{backup_name}.db"
        metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
        
        if not backup_file.exists():
            print(f"❌ Backup nicht gefunden: {backup_file}")
            return False
        
        print(f"🔄 Stelle Backup wieder her: {backup_file}")
        
        try:
            # Erstelle Sicherheitskopie der aktuellen DB
            current_backup = f"current_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(current_backup)
            
            # Stelle Backup wieder her
            shutil.copy2(backup_file, self.db_path)
            
            print(f"✅ Backup erfolgreich wiederhergestellt")
            
            # Zeige Metadaten an
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                print(f"📋 Backup-Datum: {metadata.get('timestamp', 'Unbekannt')}")
                
                if 'counts_before_backup' in metadata:
                    print("📊 Datenstand aus Backup:")
                    for table, count in metadata['counts_before_backup'].items():
                        if not table.endswith('_total') and table != 'grand_total':
                            print(f"   {table}: {count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Wiederherstellungs-Fehler: {e}")
            return False
    
    def clear_tables(self, mode: str = 'all', create_backup_first: bool = True) -> bool:
        """Leere Tabellen basierend auf Modus"""
        if mode not in self.table_groups:
            print(f"❌ Ungültiger Modus: {mode}")
            print(f"   Verfügbare Modi: {list(self.table_groups.keys())}")
            return False
        
        # Hole aktuelle Anzahl vor Bereinigung
        counts_before = self.get_current_counts()
        print(f"📊 Aktueller Datenstand:")
        for table, count in counts_before.items():
            if not table.endswith('_total') and table != 'grand_total':
                print(f"   {table}: {count}")
        print(f"   Gesamt: {counts_before.get('grand_total', 0)}")
        
        # Erstelle Backup falls gewünscht
        if create_backup_first:
            backup_name = f"before_clear_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(backup_name)
        
        # Ermittle zu löschende Tabellen
        tables_to_clear = self.table_groups[mode]
        
        print(f"🧹 Beginne Bereinigung (Modus: {mode})")
        print(f"📋 Tabellen: {[t.__tablename__ for t in tables_to_clear]}")
        
        init_db()
        session = get_session()
        
        try:
            deleted_counts = {}
            
            for table_class in tables_to_clear:
                table_name = table_class.__tablename__
                
                # Zähle Einträge vor Löschung
                count_before = session.query(table_class).count()
                
                if count_before > 0:
                    print(f"🗑️  Lösche {count_before} Einträge aus {table_name}...")
                    
                    # Lösche alle Einträge
                    deleted = session.query(table_class).delete()
                    session.commit()
                    
                    deleted_counts[table_name] = deleted
                    print(f"   ✅ {deleted} Einträge gelöscht")
                else:
                    print(f"   ℹ️  {table_name} bereits leer")
                    deleted_counts[table_name] = 0
            
            print(f"✅ Bereinigung abgeschlossen")
            
            # Verifiziere Bereinigung
            verification_success = self.verify_cleanup(tables_to_clear)
            
            if verification_success:
                print(f"✅ Bereinigung erfolgreich verifiziert")
                return True
            else:
                print(f"❌ Bereinigung fehlgeschlagen - Einträge noch vorhanden")
                return False
                
        except Exception as e:
            print(f"❌ Bereinigungsfehler: {e}")
            session.rollback()
            return False
            
        finally:
            session.close()
    
    def verify_cleanup(self, tables_to_verify: List) -> bool:
        """Verifiziere erfolgreiche Bereinigung"""
        print(f"🔍 Verifiziere Bereinigung...")
        
        init_db()
        session = get_session()
        
        try:
            all_clean = True
            
            for table_class in tables_to_verify:
                table_name = table_class.__tablename__
                count = session.query(table_class).count()
                
                if count == 0:
                    print(f"   ✅ {table_name}: 0 Einträge")
                else:
                    print(f"   ❌ {table_name}: {count} Einträge (sollte 0 sein)")
                    all_clean = False
            
            return all_clean
            
        finally:
            session.close()
    
    def list_backups(self) -> List[Dict]:
        """Liste verfügbare Backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db"):
            backup_name = backup_file.stem
            metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
            
            backup_info = {
                'name': backup_name,
                'file': str(backup_file),
                'size_mb': backup_file.stat().st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            }
            
            # Lade Metadaten falls vorhanden
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    backup_info.update(metadata)
                except:
                    pass
            
            backups.append(backup_info)
        
        # Sortiere nach Erstellungsdatum (neueste zuerst)
        backups.sort(key=lambda x: x.get('timestamp', x['created']), reverse=True)
        
        return backups
    
    def vacuum_database(self) -> bool:
        """Komprimiere Datenbank nach Bereinigung"""
        print(f"🗜️  Komprimiere Datenbank...")
        
        try:
            # Direkte SQLite-Verbindung für VACUUM
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            
            print(f"✅ Datenbank komprimiert")
            return True
            
        except Exception as e:
            print(f"❌ Komprimierungsfehler: {e}")
            return False


def main():
    """Hauptfunktion mit CLI-Interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MineSearch v2 Database Cleaner")
    parser.add_argument('--mode', '-m', 
                       choices=['all', 'results', 'statistics', 'model_stats', 
                               'summaries', 'field_stats', 'consistency', 'sources', 'mines'],
                       default='all',
                       help='Bereinigungsmodus (default: all)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Kein Backup vor Bereinigung erstellen')
    parser.add_argument('--vacuum', action='store_true',
                       help='Datenbank nach Bereinigung komprimieren')
    parser.add_argument('--list-backups', action='store_true',
                       help='Verfügbare Backups auflisten')
    parser.add_argument('--restore', type=str,
                       help='Backup wiederherstellen (Backup-Name)')
    parser.add_argument('--counts-only', action='store_true',
                       help='Nur aktuelle Einträge zählen, keine Bereinigung')
    
    args = parser.parse_args()
    
    cleaner = DatabaseCleaner()
    
    # Nur Anzahl anzeigen
    if args.counts_only:
        counts = cleaner.get_current_counts()
        print(f"\n📊 Aktuelle Datenbank-Einträge:")
        for table, count in counts.items():
            if not table.endswith('_total') and table != 'grand_total':
                print(f"   {table}: {count}")
        print(f"   Gesamt: {counts.get('grand_total', 0)}")
        return
    
    # Backups auflisten
    if args.list_backups:
        backups = cleaner.list_backups()
        if backups:
            print(f"\n💾 Verfügbare Backups:")
            for backup in backups:
                print(f"   {backup['name']} ({backup['size_mb']:.1f} MB) - {backup['created']}")
        else:
            print(f"ℹ️  Keine Backups gefunden")
        return
    
    # Backup wiederherstellen
    if args.restore:
        success = cleaner.restore_backup(args.restore)
        if success:
            print(f"✅ Wiederherstellung erfolgreich")
        else:
            print(f"❌ Wiederherstellung fehlgeschlagen")
        return
    
    # Bereinigung durchführen
    print(f"\n🧹 Starte Database-Clear (Modus: {args.mode})")
    
    success = cleaner.clear_tables(
        mode=args.mode,
        create_backup_first=not args.no_backup
    )
    
    if success:
        print(f"✅ Bereinigung erfolgreich abgeschlossen")
        
        # Komprimierung falls gewünscht
        if args.vacuum:
            cleaner.vacuum_database()
        
        # Zeige finale Einträge
        counts_after = cleaner.get_current_counts()
        print(f"\n📊 Datenstand nach Bereinigung:")
        for table, count in counts_after.items():
            if not table.endswith('_total') and table != 'grand_total':
                print(f"   {table}: {count}")
        print(f"   Gesamt: {counts_after.get('grand_total', 0)}")
        
    else:
        print(f"❌ Bereinigung fehlgeschlagen")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())