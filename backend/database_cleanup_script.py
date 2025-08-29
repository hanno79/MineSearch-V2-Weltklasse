#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Kritisches Datenbank-Cleanup-Script für Feldkontamination

KRITISCHER FIX 25.08.2025: Behebt die Feldnamen-als-Werte Probleme in der Datenbank
Lösung für:
- 111 Einträge mit "x-Koordinate" in Betreiber-Feld
- 588 Einträge mit "-" statt NULL
- Cross-Field-Kontamination aller Felder
"""

import os
import sys
import sqlite3
import logging
import json
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Füge Backend-Path zum Python-Path hinzu
backend_path = Path(__file__).parent / "minesearch"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from field_name_blacklist import is_field_name_value, validate_extracted_fields

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseCleanupTool:
    """
    KRITISCHES CLEANUP-TOOL 25.08.2025
    Behebt systematische Feldkontamination in der Datenbank
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialisiert das Cleanup-Tool
        
        Args:
            db_path: Pfad zur Datenbank (optional)
        """
        if db_path is None:
            # Standardpfad zur MineSearch-Datenbank
            db_path = "/app/backend/minesearch/database/mines.db"
        
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Statistiken
        self.stats = {
            'total_entries': 0,
            'contaminated_entries': 0,
            'field_name_contaminations': 0,
            'null_normalizations': 0,
            'fixes_by_field': {},
            'backup_created': False,
            'cleanup_successful': False
        }
        
        # Feldnamen der search_results Tabelle (basierend auf CSV_COLUMNS)
        self.field_names = [
            'mine_name', 'country', 'region', 'betreiber', 'eigentuemer', 
            'rohstoffe', 'minentyp', 'aktivitaetsstatus', 'produktionsstart',
            'produktionsende', 'foerdermenge_jahr', 'minenflaeche_qkm',
            'x_koordinate', 'y_koordinate', 'restaurationskosten',
            'kostenjahr', 'dokumentenjahr', 'quellenangaben'
        ]
    
    def create_backup(self) -> bool:
        """
        KRITISCHES BACKUP 25.08.2025: Erstellt Sicherungskopie vor Cleanup
        
        Returns:
            True wenn Backup erfolgreich erstellt
        """
        try:
            logger.info(f"[BACKUP] Erstelle Datenbank-Backup: {self.backup_path}")
            
            # Backup mit sqlite3 .backup kommando
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(self.backup_path)
            
            source_conn.backup(backup_conn)
            source_conn.close()
            backup_conn.close()
            
            # Backup-Größe prüfen
            backup_size = os.path.getsize(self.backup_path)
            original_size = os.path.getsize(self.db_path)
            
            if backup_size != original_size:
                logger.error(f"[BACKUP] FEHLER: Backup-Größe ({backup_size}) != Original-Größe ({original_size})")
                return False
            
            logger.info(f"[BACKUP] ✅ Backup erfolgreich erstellt: {backup_size} Bytes")
            self.stats['backup_created'] = True
            return True
            
        except Exception as e:
            logger.error(f"[BACKUP] KRITISCHER FEHLER bei Backup-Erstellung: {e}")
            return False
    
    def analyze_contamination(self) -> Dict[str, Any]:
        """
        KONTAMINATIONS-ANALYSE 25.08.2025: Analysiert alle Feldkontaminationen
        
        Returns:
            Dictionary mit Kontaminations-Statistiken
        """
        try:
            logger.info("[ANALYSIS] Starte Kontaminations-Analyse...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hole alle Einträge aus structured_data
            cursor.execute("""
                SELECT id, mine_name, structured_data 
                FROM search_results 
                WHERE structured_data IS NOT NULL AND structured_data != ''
            """)
            
            results = cursor.fetchall()
            analysis = {
                'total_entries': len(results),
                'contaminated_entries': 0,
                'contamination_details': {},
                'field_contaminations': {},
                'null_issues': 0,
                'problematic_entries': []
            }
            
            logger.info(f"[ANALYSIS] Analysiere {len(results)} Einträge...")
            
            for entry_id, mine_name, structured_data_json in results:
                try:
                    # Parse structured_data JSON
                    structured_data = json.loads(structured_data_json)
                    entry_contaminated = False
                    contamination_details = {}
                    
                    # Prüfe jeden Feldwert auf Kontamination
                    for field_name, field_value in structured_data.items():
                        if field_value and str(field_value).strip():
                            value_str = str(field_value).strip()
                            
                            # 1. Feldnamen-als-Werte Check
                            if is_field_name_value(value_str, field_name):
                                entry_contaminated = True
                                contamination_details[field_name] = f"FIELD-NAME: {value_str}"
                                
                                # Statistik aktualisieren
                                if field_name not in analysis['field_contaminations']:
                                    analysis['field_contaminations'][field_name] = []
                                analysis['field_contaminations'][field_name].append({
                                    'id': entry_id,
                                    'mine': mine_name,
                                    'contaminated_value': value_str
                                })
                            
                            # 2. NULL-Normalisierung Check
                            elif value_str in ['-', '', 'X', 'nicht gefunden', 'nichts gefunden']:
                                contamination_details[field_name] = f"NULL-ISSUE: {value_str}"
                                analysis['null_issues'] += 1
                    
                    # Entry zur Problembasis hinzufügen wenn kontaminiert
                    if entry_contaminated:
                        analysis['contaminated_entries'] += 1
                        analysis['problematic_entries'].append({
                            'id': entry_id,
                            'mine_name': mine_name,
                            'contaminations': contamination_details
                        })
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"[ANALYSIS] JSON-Parse-Fehler für Entry {entry_id}: {e}")
                    continue
            
            conn.close()
            
            # Zusammenfassung loggen
            logger.info(f"[ANALYSIS] ✅ Analyse abgeschlossen:")
            logger.info(f"[ANALYSIS]   📊 {analysis['total_entries']} Einträge analysiert")
            logger.info(f"[ANALYSIS]   🚨 {analysis['contaminated_entries']} kontaminierte Einträge")
            logger.info(f"[ANALYSIS]   🔍 {len(analysis['field_contaminations'])} Felder betroffen")
            logger.info(f"[ANALYSIS]   🔄 {analysis['null_issues']} NULL-Normalisierungen nötig")
            
            # Details zu kontaminierten Feldern
            for field, contaminations in analysis['field_contaminations'].items():
                logger.info(f"[ANALYSIS]     🔴 Feld '{field}': {len(contaminations)} Kontaminationen")
            
            return analysis
            
        except Exception as e:
            logger.error(f"[ANALYSIS] FEHLER bei Kontaminations-Analyse: {e}")
            return {}
    
    def fix_contaminated_entry(self, entry_id: int, structured_data: dict) -> Tuple[dict, int]:
        """
        KRITISCHER FIX 25.08.2025: Behebt Kontaminationen in einem Eintrag
        
        Args:
            entry_id: ID des Eintrags
            structured_data: Strukturierte Daten des Eintrags
            
        Returns:
            (cleaned_data, fixes_count)
        """
        cleaned_data = structured_data.copy()
        fixes_count = 0
        
        for field_name, field_value in structured_data.items():
            if field_value and str(field_value).strip():
                value_str = str(field_value).strip()
                original_value = value_str
                
                # 1. KRITISCHER FELDNAMEN-CHECK
                if is_field_name_value(value_str, field_name):
                    logger.warning(f"[FIX] Entry {entry_id}: Feldname-Kontamination '{value_str}' in Feld '{field_name}' → NULL")
                    cleaned_data[field_name] = None
                    fixes_count += 1
                    
                    # Statistik aktualisieren
                    self.stats['field_name_contaminations'] += 1
                    if field_name not in self.stats['fixes_by_field']:
                        self.stats['fixes_by_field'][field_name] = 0
                    self.stats['fixes_by_field'][field_name] += 1
                
                # 2. NULL-NORMALISIERUNG
                elif value_str in ['-', '', 'X', 'nicht gefunden', 'nichts gefunden', 'NULL']:
                    logger.debug(f"[FIX] Entry {entry_id}: NULL-Normalisierung '{value_str}' in Feld '{field_name}' → NULL")
                    cleaned_data[field_name] = None
                    fixes_count += 1
                    self.stats['null_normalizations'] += 1
        
        return cleaned_data, fixes_count
    
    def execute_cleanup(self) -> bool:
        """
        KRITISCHES CLEANUP 25.08.2025: Führt das komplette Datenbank-Cleanup durch
        
        Returns:
            True wenn Cleanup erfolgreich
        """
        try:
            logger.info("[CLEANUP] ⚠️  STARTE KRITISCHES DATENBANK-CLEANUP ⚠️")
            
            # 1. BACKUP ERSTELLEN
            if not self.create_backup():
                logger.error("[CLEANUP] ABBRUCH: Backup-Erstellung fehlgeschlagen!")
                return False
            
            # 2. KONTAMINATIONS-ANALYSE
            analysis = self.analyze_contamination()
            if not analysis:
                logger.error("[CLEANUP] ABBRUCH: Kontaminations-Analyse fehlgeschlagen!")
                return False
            
            self.stats['total_entries'] = analysis['total_entries']
            self.stats['contaminated_entries'] = analysis['contaminated_entries']
            
            if analysis['contaminated_entries'] == 0:
                logger.info("[CLEANUP] ✅ Keine Kontaminationen gefunden - Cleanup nicht nötig")
                self.stats['cleanup_successful'] = True
                return True
            
            # 3. CLEANUP DURCHFÜHREN
            logger.info(f"[CLEANUP] 🔧 Bereinige {analysis['contaminated_entries']} kontaminierte Einträge...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cleaned_entries = 0
            total_fixes = 0
            
            for problematic_entry in analysis['problematic_entries']:
                entry_id = problematic_entry['id']
                
                # Aktuellen Eintrag laden
                cursor.execute("SELECT structured_data FROM search_results WHERE id = ?", (entry_id,))
                result = cursor.fetchone()
                
                if not result or not result[0]:
                    continue
                
                try:
                    structured_data = json.loads(result[0])
                    
                    # Eintrag bereinigen
                    cleaned_data, fixes_count = self.fix_contaminated_entry(entry_id, structured_data)
                    
                    if fixes_count > 0:
                        # Bereinigten Eintrag in DB speichern
                        cleaned_json = json.dumps(cleaned_data, ensure_ascii=False)
                        cursor.execute(
                            "UPDATE search_results SET structured_data = ? WHERE id = ?",
                            (cleaned_json, entry_id)
                        )
                        
                        cleaned_entries += 1
                        total_fixes += fixes_count
                        
                        logger.debug(f"[CLEANUP] Entry {entry_id}: {fixes_count} Fixes angewendet")
                
                except Exception as e:
                    logger.error(f"[CLEANUP] FEHLER bei Entry {entry_id}: {e}")
                    continue
            
            # Änderungen committen
            conn.commit()
            conn.close()
            
            # Statistiken aktualisieren
            self.stats['cleanup_successful'] = True
            
            logger.info(f"[CLEANUP] ✅ CLEANUP ERFOLGREICH ABGESCHLOSSEN!")
            logger.info(f"[CLEANUP]   📊 {cleaned_entries} Einträge bereinigt")
            logger.info(f"[CLEANUP]   🔧 {total_fixes} Fixes insgesamt angewendet")
            logger.info(f"[CLEANUP]   🚨 {self.stats['field_name_contaminations']} Feldnamen-Kontaminationen behoben")
            logger.info(f"[CLEANUP]   🔄 {self.stats['null_normalizations']} NULL-Normalisierungen durchgeführt")
            
            return True
            
        except Exception as e:
            logger.error(f"[CLEANUP] KRITISCHER FEHLER während Cleanup: {e}")
            return False
    
    def generate_cleanup_report(self) -> str:
        """
        CLEANUP-BERICHT 25.08.2025: Generiert detaillierten Cleanup-Bericht
        
        Returns:
            Formatierter Cleanup-Bericht
        """
        report_lines = [
            "=" * 60,
            "DATENBANK-CLEANUP-BERICHT",
            f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            "=" * 60,
            "",
            "📊 CLEANUP-STATISTIKEN:",
            f"   Gesamte Einträge: {self.stats['total_entries']}",
            f"   Kontaminierte Einträge: {self.stats['contaminated_entries']}",
            f"   Feldnamen-Kontaminationen: {self.stats['field_name_contaminations']}",
            f"   NULL-Normalisierungen: {self.stats['null_normalizations']}",
            f"   Backup erstellt: {'✅' if self.stats['backup_created'] else '❌'}",
            f"   Cleanup erfolgreich: {'✅' if self.stats['cleanup_successful'] else '❌'}",
            "",
            "🔧 FIXES NACH FELDERN:",
        ]
        
        for field, count in self.stats['fixes_by_field'].items():
            report_lines.append(f"   {field}: {count} Fixes")
        
        report_lines.extend([
            "",
            "💾 BACKUP-INFO:",
            f"   Backup-Pfad: {self.backup_path}",
            f"   Backup-Größe: {os.path.getsize(self.backup_path) if os.path.exists(self.backup_path) else 'N/A'} Bytes",
            "",
            "⚠️  WICHTIG:",
            "   - Backup vor Wiederherstellung prüfen",
            "   - Bei Problemen: Backup mit 'mv' zurückspielen",
            "   - Logs in database_cleanup.log prüfen",
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def restore_from_backup(self) -> bool:
        """
        NOTFALL-WIEDERHERSTELLUNG 25.08.2025: Stellt Datenbank aus Backup wieder her
        
        Returns:
            True wenn Wiederherstellung erfolgreich
        """
        try:
            if not os.path.exists(self.backup_path):
                logger.error(f"[RESTORE] Backup nicht gefunden: {self.backup_path}")
                return False
            
            logger.warning(f"[RESTORE] ⚠️  WIEDERHERSTELLUNG AUS BACKUP: {self.backup_path}")
            
            # Backup in temporäre Datei im selben Verzeichnis kopieren und dann atomar ersetzen
            db_dir = os.path.dirname(self.db_path) or "."
            tmp_fd, tmp_path = tempfile.mkstemp(
                prefix=os.path.basename(self.db_path) + ".restore_",
                suffix=".tmp",
                dir=db_dir
            )
            os.close(tmp_fd)
            try:
                shutil.copy2(self.backup_path, tmp_path)
                os.replace(tmp_path, self.db_path)
                logger.info(f"[RESTORE] ✅ Datenbank aus Backup atomar wiederhergestellt")
                return True
            except Exception as inner_e:
                logger.error(f"[RESTORE] FEHLER während atomarer Wiederherstellung: {inner_e}")
                # Aufräumen: temporäre Datei entfernen, Original bleibt unangetastet
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception as cleanup_e:
                    logger.warning(f"[RESTORE] Konnte temporäre Datei nicht entfernen: {cleanup_e}")
                return False
            
        except Exception as e:
            logger.error(f"[RESTORE] KRITISCHER FEHLER bei Wiederherstellung: {e}")
            return False

def main():
    """
    MAIN-FUNKTION 25.08.2025: Führt das Datenbank-Cleanup durch
    """
    print("🚨 KRITISCHES DATENBANK-CLEANUP-SCRIPT 🚨")
    print("Behebt Feldnamen-als-Werte Kontaminationen")
    print("")
    
    # Sicherheitsabfrage
    response = input("⚠️  WARNUNG: Dieses Script verändert die Datenbank irreversibel!\n"
                    "Ein Backup wird erstellt, aber bitte prüfen Sie vorher.\n"
                    "Fortfahren? (ja/nein): ").lower().strip()
    
    if response not in ['ja', 'j', 'yes', 'y']:
        print("❌ Cleanup abgebrochen.")
        return
    
    # Cleanup-Tool initialisieren und ausführen
    cleanup_tool = DatabaseCleanupTool()
    
    # Cleanup ausführen
    success = cleanup_tool.execute_cleanup()
    
    # Bericht generieren und anzeigen
    report = cleanup_tool.generate_cleanup_report()
    print("\n" + report)
    
    # Bericht in Datei speichern
    report_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Cleanup-Bericht gespeichert: {report_file}")
    
    if success:
        print("\n✅ DATENBANK-CLEANUP ERFOLGREICH ABGESCHLOSSEN!")
        print("💾 Backup verfügbar für Notfall-Wiederherstellung")
    else:
        print("\n❌ CLEANUP FEHLGESCHLAGEN!")
        print("💾 Backup wurde erstellt - Datenbank unverändert")
    
    return success

if __name__ == "__main__":
    main()