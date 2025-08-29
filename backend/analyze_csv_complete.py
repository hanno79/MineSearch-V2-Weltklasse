#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Vollständige CSV-Analyse für Sonderbarkeiten

CSV-ANALYSE 25.08.2025: Findet alle auffälligen Muster und Probleme im CSV
"""

import sys
sys.path.insert(0, '.')

import csv
import re
import os
import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional

def _get_default_csv_path() -> str:
    """Gibt den Standard-CSV-Pfad zurück"""
    return "/app/docs/minesearch_ohne_quellenangaben_25082025_korrigiert.csv"

def _get_csv_file_path(csv_file_path: Optional[str] = None) -> str:
    """
    Bestimmt den CSV-Dateipfad aus verschiedenen Quellen:
    1. Explizit übergebener Parameter
    2. Umgebungsvariable CSV_FILE_PATH  
    3. Standard-Pfad als Fallback
    """
    if csv_file_path:
        return csv_file_path
    
    env_path = os.environ.get('CSV_FILE_PATH')
    if env_path:
        return env_path
    
    return _get_default_csv_path()

def _create_default_statistics() -> Dict[str, Any]:
    """Erstellt eine Standard-Statistik-Struktur für Fehlerfälle"""
    return {
        'total_rows': 0,
        'empty_fields': defaultdict(int),
        'suspicious_values': defaultdict(list),
        'field_contamination': defaultdict(list),
        'encoding_issues': [],
        'format_inconsistencies': defaultdict(int),
        'duplicate_columns': [],
        'error': None  # Feld für Fehlermeldungen
    }

def analyze_csv_complete(csv_file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    VOLLSTÄNDIGE CSV-ANALYSE 25.08.2025
    Analysiert alle Aspekte des CSV auf Probleme und Eigenartigkeiten
    
    Args:
        csv_file_path: Optionaler Pfad zur CSV-Datei. Falls None, wird der Pfad
                      aus der Umgebungsvariable CSV_FILE_PATH oder der Standard-Pfad verwendet.
    
    Returns:
        Dict mit Analyseergebnissen und Statistiken
    """
    
    csv_file = _get_csv_file_path(csv_file_path)
    
    if not Path(csv_file).exists():
        print(f"❌ CSV-Datei nicht gefunden: {csv_file}")
        error_stats = _create_default_statistics()
        error_stats['error'] = f"CSV-Datei nicht gefunden: {csv_file}"
        return error_stats
    
    print("🔍 VOLLSTÄNDIGE CSV-ANALYSE")
    print("=" * 50)
    
    problems = []
    statistics = _create_default_statistics()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Entferne BOM falls vorhanden
            content = f.read()
            if content.startswith('\ufeff'):
                content = content[1:]
                problems.append("⚠️ BOM (Byte Order Mark) gefunden und entfernt")
            
            lines = content.split('\n')
            reader = csv.reader(lines, delimiter='|')
            
            # Header analysieren
            header = next(reader, None)
            if not header:
                problems.append("❌ KRITISCH: Kein Header gefunden!")
                statistics['error'] = "Kein Header im CSV gefunden"
                return statistics
            
            print(f"📋 HEADER-ANALYSE:")
            print(f"   Spalten: {len(header)}")
            for i, col in enumerate(header):
                print(f"   {i+1:2d}. {col.strip()}")
            
            # Duplikate im Header suchen
            header_clean = [col.strip() for col in header]
            seen = set()
            for col in header_clean:
                if col in seen:
                    statistics['duplicate_columns'].append(col)
                    problems.append(f"❌ DUPLIKAT-SPALTE: '{col}' erscheint mehrfach!")
                seen.add(col)
            
            # Spezielle Spalten-Checks
            if "Quellenangaben" in header_clean:
                problems.append("❌ REDUNDANTE SPALTE: 'Quellenangaben' sollte entfernt werden")
            
            if "Exakte Quellenangaben" not in header_clean:
                problems.append("⚠️ FEHLENDE SPALTE: 'Exakte Quellenangaben' nicht gefunden")
            
            # Datenzeilen analysieren
            for row_num, row in enumerate(reader, 2):
                statistics['total_rows'] += 1
                
                if len(row) != len(header):
                    problems.append(f"❌ ZEILE {row_num}: Spaltenanzahl stimmt nicht ({len(row)} statt {len(header)})")
                
                # Jedes Feld analysieren
                for i, (field_name, value) in enumerate(zip(header_clean, row)):
                    if i >= len(row):
                        break
                        
                    value = value.strip() if value else ""
                    
                    # Leere Felder zählen
                    if not value or value.lower() in ['nichts gefunden', 'leer', '']:
                        statistics['empty_fields'][field_name] += 1
                    
                    # Feldkontamination suchen
                    if value and is_field_contamination(value, field_name, header_clean):
                        statistics['field_contamination'][field_name].append({
                            'row': row_num,
                            'value': value[:50] + "..." if len(value) > 50 else value
                        })
                    
                    # Verdächtige Werte
                    if is_suspicious_value(value, field_name):
                        statistics['suspicious_values'][field_name].append({
                            'row': row_num,
                            'value': value[:50] + "..." if len(value) > 50 else value,
                            'reason': get_suspicious_reason(value, field_name)
                        })
                    
                    # Format-Inkonsistenzen
                    if field_name in ['x-Koordinate', 'y-Koordinate'] and value:
                        if not is_valid_coordinate(value, field_name):
                            statistics['format_inconsistencies'][f'{field_name}_format'] += 1
                    
                    # Encoding-Probleme
                    if has_encoding_issues(value):
                        statistics['encoding_issues'].append({
                            'row': row_num,
                            'field': field_name,
                            'value': value[:30] + "..." if len(value) > 30 else value
                        })
                
                # Nur erste 100 Zeilen für Performance
                if statistics['total_rows'] >= 100:
                    print(f"\n⚠️ Analyse auf erste 100 Zeilen beschränkt (Performance)")
                    break
    
    except Exception as e:
        problems.append(f"❌ KRITISCHER FEHLER beim CSV-Lesen: {e}")
        statistics['error'] = f"Kritischer Fehler beim CSV-Lesen: {e}"
    
    # ERGEBNISSE AUSGEBEN
    print(f"\n📊 ANALYSE-ERGEBNISSE:")
    print(f"   📈 Analysierte Zeilen: {statistics.get('total_rows', 0)}")
    print(f"   🚨 Gefundene Probleme: {len(problems)}")
    
    # PROBLEME AUFLISTEN
    if problems:
        print(f"\n🚨 IDENTIFIZIERTE PROBLEME:")
        for i, problem in enumerate(problems, 1):
            print(f"   {i:2d}. {problem}")
    else:
        print(f"\n✅ Keine kritischen Probleme gefunden!")
    
    # FELDKONTAMINATION
    if statistics.get('field_contamination'):
        print(f"\n🔴 FELDKONTAMINATION GEFUNDEN:")
        for field, contaminations in statistics.get('field_contamination', {}).items():
            print(f"   💥 Feld '{field}': {len(contaminations)} Kontaminationen")
            for cont in contaminations[:3]:  # Nur erste 3 zeigen
                print(f"      - Zeile {cont['row']}: '{cont['value']}'")
            if len(contaminations) > 3:
                print(f"      ... und {len(contaminations)-3} weitere")
    
    # VERDÄCHTIGE WERTE
    if statistics.get('suspicious_values'):
        print(f"\n⚠️ VERDÄCHTIGE WERTE:")
        for field, suspicions in statistics.get('suspicious_values', {}).items():
            if len(suspicions) > 3:  # Nur Felder mit mehreren verdächtigen Werten
                print(f"   🔍 Feld '{field}': {len(suspicions)} verdächtige Werte")
                for susp in suspicions[:2]:
                    print(f"      - Zeile {susp['row']}: '{susp['value']}' ({susp['reason']})")
    
    # LEERE FELDER STATISTIK
    print(f"\n📊 LEERE FELDER (Top 10):")
    empty_sorted = sorted(statistics.get('empty_fields', {}).items(), key=lambda x: x[1], reverse=True)
    for field, count in empty_sorted[:10]:
        percentage = (count / statistics.get('total_rows', 1)) * 100
        print(f"   📉 {field}: {count} ({percentage:.1f}%)")
    
    # ENCODING-PROBLEME
    if statistics.get('encoding_issues'):
        print(f"\n🔤 ENCODING-PROBLEME:")
        for issue in statistics.get('encoding_issues', [])[:5]:
            print(f"   - Zeile {issue['row']}, Feld '{issue['field']}': '{issue['value']}'")
    
    # EMPFEHLUNGEN
    print(f"\n💡 EMPFEHLUNGEN:")
    
    if "Quellenangaben" in [col.strip() for col in header if col]:
        print(f"   🔧 ENTFERNE redundante 'Quellenangaben' Spalte")
    
    if statistics.get('field_contamination'):
        print(f"   🛡️ AKTIVIERE Feldkontamination-Schutz (bereits implementiert)")
    
    empty_fields = statistics.get('empty_fields', {})
    if empty_fields:
        most_empty = max(empty_fields.items(), key=lambda x: x[1])
        if most_empty[1] > statistics.get('total_rows', 1) * 0.8:
            print(f"   📉 Feld '{most_empty[0]}' ist zu {(most_empty[1]/statistics.get('total_rows', 1)*100):.1f}% leer - prüfen ob nötig")
    
    if not statistics.get('field_contamination') and len(problems) <= 2:
        print(f"   ✅ CSV-Qualität ist gut - nur kleinere Korrekturen nötig")
    
    return statistics

def is_field_contamination(value, field_name, all_fields):
    """Prüft ob ein Wert eine Feldkontamination ist"""
    if not value or len(value) < 3:
        return False
    
    # Entferne Quellenreferenzen
    clean_value = re.sub(r'\s*\[[0-9,\s]+\]$', '', value).strip()
    
    # Prüfe ob bereinigter Wert ein Feldname ist
    for other_field in all_fields:
        if other_field.lower() == clean_value.lower():
            return True
        
        # Auch ähnliche Feldnamen
        if other_field.lower().replace('-', '').replace(' ', '') == clean_value.lower().replace('-', '').replace(' ', ''):
            return True
    
    return False

def is_suspicious_value(value, field_name):
    """Prüft ob ein Wert verdächtig ist"""
    if not value:
        return False
    
    suspicious_patterns = [
        r'^TEMPLATE:',
        r'^LEER\s*-',
        r'^\s*""\s*',
        r'Nothing available.*No data',
        r'pdf\s*\[',
        r'^is in Quebec, which has',
        r'nur exploration',
        r'only exploration'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False

def get_suspicious_reason(value, field_name):
    """Gibt den Grund zurück warum ein Wert verdächtig ist"""
    if 'TEMPLATE:' in value:
        return "Template-Marker"
    elif 'Nothing available' in value:
        return "Englischer Platzhalter"
    elif value.strip().startswith('""'):
        return "Doppelte Anführungszeichen"
    elif 'pdf [' in value:
        return "PDF-Referenz als Datentyp"
    elif 'is in Quebec' in value:
        return "Erklärungstext statt Daten"
    else:
        return "Ungewöhnliches Format"

def is_valid_coordinate(value, field_name: Optional[str] = None):
    """Prüft ob ein Koordinatenwert valide ist.

    - Leere/Platzhalter-Werte gelten als valide (True)
    - Wenn das Feld ein Breitengrad (Latitude) zu sein scheint ("y" oder "lat" im Feldnamen),
      dann muss der Wert in [-90, 90] liegen
    - Andernfalls wird der Wert als Längengrad (Longitude) behandelt und muss in [-180, 180] liegen
    """
    if not value or value.lower() in ['nichts gefunden', 'leer']:
        return True  # Leere Werte sind OK
    
    # Bestimme, ob es sich um Latitude handelt
    is_latitude = False
    if field_name:
        name_lower = field_name.lower()
        if ('lat' in name_lower) or ('y' in name_lower):
            is_latitude = True
    
    try:
        float_val = float(value)
        if is_latitude:
            return -90 <= float_val <= 90
        else:
            return -180 <= float_val <= 180
    except ValueError:
        return False

def has_encoding_issues(value):
    """Prüft auf Encoding-Probleme"""
    if not value:
        return False
    
    # Suche nach verdächtigen Zeichen
    suspicious_chars = ['�', '\ufffd', '\x00']
    for char in suspicious_chars:
        if char in value:
            return True
    
    # Sehr seltene Unicode-Bereiche
    for char in value:
        if ord(char) > 65535:  # Bereich außerhalb BMP
            return True
    
    return False

def _parse_arguments() -> argparse.Namespace:
    """Parst Kommandozeilenargumente"""
    parser = argparse.ArgumentParser(
        description="Vollständige CSV-Analyse für Sonderbarkeiten",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python analyze_csv_complete.py
  python analyze_csv_complete.py --csv-file /pfad/zur/datei.csv
  CSV_FILE_PATH=/pfad/zur/datei.csv python analyze_csv_complete.py

Priorität der Pfad-Bestimmung:
  1. --csv-file Argument (höchste Priorität)
  2. CSV_FILE_PATH Umgebungsvariable  
  3. Standard-Pfad (niedrigste Priorität)
        """
    )
    
    parser.add_argument(
        '--csv-file', '-f',
        type=str,
        help=f'Pfad zur CSV-Datei (Standard: {_get_default_csv_path()})'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Zeigt die aktuelle Konfiguration an und beendet das Programm'
    )
    
    return parser.parse_args()

def main():
    """Hauptfunktion"""
    args = _parse_arguments()
    
    # Konfiguration anzeigen falls gewünscht
    if args.show_config:
        csv_file = _get_csv_file_path(args.csv_file)
        print("🔧 KONFIGURATION:")
        print(f"   Standard-Pfad: {_get_default_csv_path()}")
        print(f"   Umgebungsvariable CSV_FILE_PATH: {os.environ.get('CSV_FILE_PATH', '(nicht gesetzt)')}")
        print(f"   Kommandozeilen-Argument: {args.csv_file or '(nicht gesetzt)'}")
        print(f"   Verwendeter Pfad: {csv_file}")
        print(f"   Datei existiert: {'✅ Ja' if Path(csv_file).exists() else '❌ Nein'}")
        return
    
    # Hauptanalyse durchführen
    statistics = analyze_csv_complete(args.csv_file)
    
    # Prüfe auf kritische Fehler
    if statistics.get('error'):
        print(f"\n❌ CSV-ANALYSE FEHLGESCHLAGEN - Kritischer Fehler aufgetreten!")
        exit(1)
    elif not statistics.get('field_contamination') and len(statistics.get('duplicate_columns', [])) == 0:
        print(f"\n🎉 CSV-ANALYSE ERFOLGREICH - Keine kritischen Probleme!")
        exit(0)
    else:
        print(f"\n⚠️ CSV benötigt Korrekturen")
        exit(1)

if __name__ == "__main__":
    main()