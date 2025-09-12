#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Automatisches Script zum Hinzufügen von Author-Headern zu Python-Dateien (REGEL 8)
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def has_author_header(file_path):
    """Prüft ob eine Datei bereits einen Author-Header hat"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_lines = f.read(500)  # Erste 500 Zeichen lesen
            return 'Author: rahn' in first_lines
    except Exception as e:
        print(f"❌ Fehler beim Lesen von {file_path}: {e}")
        return True  # Fehler als "hat Header" behandeln

def get_description_from_filename(file_path):
    """Generiert eine Beschreibung basierend auf dem Dateinamen"""
    filename = Path(file_path).name.replace('.py', '')
    
    # Mapping für bekannte Module
    descriptions = {
        'main': 'Haupteinstiegspunkt der Anwendung',
        'config': 'Konfigurationseinstellungen',
        'models': 'Datenmodell-Definitionen',
        'utils': 'Hilfsfunktionen und Utilities',
        'test_': 'Test-Suite',
        'api': 'API-Endpunkt-Definitionen',
        'database': 'Datenbank-Operationen',
        'provider': 'Provider-Implementation',
        'routes': 'API-Route-Handler',
        'manager': 'Management-Funktionen',
        'service': 'Service-Layer-Implementation',
        'processor': 'Datenverarbeitungs-Logic',
        'orchestrator': 'Orchestrierungs-Logic',
        'extractor': 'Datenextraktions-Logic'
    }
    
    for key, desc in descriptions.items():
        if key in filename.lower():
            return desc
    
    # Fallback: Generische Beschreibung
    return f"{filename.replace('_', ' ').title()}-Modul"

def add_author_header(file_path):
    """Fügt Author-Header zu einer Python-Datei hinzu"""
    try:
        # Lese Original-Datei
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Prüfe ob bereits ein anderer Docstring vorhanden ist
        lines = original_content.split('\n')
        
        # Suche erste echte Code-Zeile (nicht Shebang, nicht leere Zeile)
        insert_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#!'):  # Shebang überspringen
                insert_index = i + 1
                continue
            elif line.strip() == '':  # Leere Zeile überspringen
                continue
            elif line.strip().startswith('"""') and i < 10:  # Bestehender Docstring
                print(f"⚠️  {file_path} hat bereits einen Docstring - überspringe")
                return False
            else:
                break
        
        # Beschreibung generieren
        description = get_description_from_filename(file_path)
        
        # Header erstellen
        header = f'"""\nAuthor: rahn\nDatum: 11.09.2025\nVersion: 1.0\nBeschreibung: {description}\n"""\n\n'
        
        # Header einfügen
        if insert_index < len(lines):
            lines.insert(insert_index, header.rstrip())
        else:
            lines.append(header.rstrip())
        
        # Datei schreiben
        new_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Header hinzugefügt: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Bearbeiten von {file_path}: {e}")
        return False

def find_python_files_without_header(root_dir):
    """Findet alle Python-Dateien ohne Author-Header"""
    python_files = []
    root_path = Path(root_dir)
    
    for py_file in root_path.rglob('*.py'):
        # Überspringe to_delete Ordner
        if 'to_delete' in str(py_file):
            continue
        
        # Überspringe __pycache__
        if '__pycache__' in str(py_file):
            continue
            
        if not has_author_header(py_file):
            python_files.append(py_file)
    
    return python_files

def main():
    """Hauptfunktion"""
    print("🚀 AUTHOR-HEADER AUTOMATISIERUNG (REGEL 8)")
    print("=" * 50)
    
    # Backend-Verzeichnis
    backend_dir = "/home/hanno/projects/MineSearch/backend"
    
    if not os.path.exists(backend_dir):
        print(f"❌ Backend-Verzeichnis nicht gefunden: {backend_dir}")
        sys.exit(1)
    
    # Finde Dateien ohne Header
    files_without_header = find_python_files_without_header(backend_dir)
    
    print(f"📊 {len(files_without_header)} Dateien ohne Author-Header gefunden:")
    print("-" * 50)
    
    for file_path in files_without_header:
        print(f"  📄 {file_path}")
    
    if not files_without_header:
        print("✅ Alle Python-Dateien haben bereits Author-Header!")
        return
    
    print(f"\n🔧 Füge Header zu {len(files_without_header)} Dateien hinzu...")
    print("-" * 50)
    
    success_count = 0
    for file_path in files_without_header:
        if add_author_header(file_path):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 ERGEBNIS: {success_count}/{len(files_without_header)} Header erfolgreich hinzugefügt")
    
    if success_count == len(files_without_header):
        print("🎯 ✅ REGEL 8 - 100% COMPLIANCE ERREICHT!")
    else:
        print(f"⚠️  {len(files_without_header) - success_count} Dateien konnten nicht bearbeitet werden")
    
    print("=" * 50)

if __name__ == "__main__":
    main()