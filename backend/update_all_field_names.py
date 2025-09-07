#!/usr/bin/env python3
"""
Automatisch generiertes Update-Skript für Feldnamen-Umbenennung
Generiert: 2025-09-07T08:40:21.608841
"""

import os
import re

# Definiere alle Ersetzungen
REPLACEMENTS = [
    # Vollständige Namen
    (r'"Rohstoffabbau \(Gold/ Kupfer/ Kohle/ usw\.\)"', '"Rohstoff"'),
    (r"'Rohstoffabbau \(Gold/ Kupfer/ Kohle/ usw\.\)'", "'Rohstoff'"),
    (r'"Minentyp \(Untertage/ Open-Pit/ usw\.\)"', '"Minentyp"'),
    (r"'Minentyp \(Untertage/ Open-Pit/ usw\.\)'", "'Minentyp'"),
    
    # In Kommentaren und Strings
    (r'Rohstoffabbau \(Gold/ Kupfer/ Kohle/ usw\.\)', 'Rohstoff'),
    (r'Minentyp \(Untertage/ Open-Pit/ usw\.\)', 'Minentyp'),
    
    # Kurze Versionen (nur Rohstoffabbau → Rohstoff)
    (r'"Rohstoffabbau"', '"Rohstoff"'),
    (r"'Rohstoffabbau'", "'Rohstoff'"),
]

# Dateien die aktualisiert werden sollen
FILES_TO_UPDATE = [
    # Backend Python-Dateien
    'backend/minesearch/extraction_processors.py',
    'backend/minesearch/enhanced_extraction_patterns.py',
    'backend/minesearch/comprehensive_search_orchestrator.py',
    'backend/minesearch/multi_model_search_orchestrator.py',
    'backend/minesearch/sequential_field_orchestrator.py',
    'backend/minesearch/search_utils.py',
    'backend/minesearch/data_extraction.py',
    'backend/minesearch/api/routes/batch.py',
    'backend/minesearch/api/routes/consolidated_field_utils.py',
    'backend/minesearch/providers/base_provider.py',
    'backend/minesearch/unified_extraction_service.py',
    
    # Frontend-Dateien
    'frontend/display.js',
    'frontend/comparison-engine.js',
    'frontend/index.html',
]

def update_file(filepath):
    """Aktualisiert eine einzelne Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Fehler bei {filepath}: {e}")
        return None

# Führe Updates durch
updated = 0
failed = 0
skipped = 0

for file in FILES_TO_UPDATE:
    filepath = f"/home/hanno/projects/MineSearch/{file}"
    if os.path.exists(filepath):
        result = update_file(filepath)
        if result is True:
            print(f"✅ {file}")
            updated += 1
        elif result is False:
            print(f"ℹ️  {file} - keine Änderungen")
            skipped += 1
        else:
            print(f"❌ {file} - Fehler")
            failed += 1
    else:
        print(f"⚠️  {file} - nicht gefunden")
        failed += 1

print(f"\n📊 Zusammenfassung:")
print(f"   ✅ Aktualisiert: {updated}")
print(f"   ℹ️  Übersprungen: {skipped}")
print(f"   ❌ Fehler: {failed}")
