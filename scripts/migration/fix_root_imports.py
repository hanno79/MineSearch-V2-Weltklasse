#!/usr/bin/env python3
"""
Korrigiere Root-Level-Imports für DB-Utils
"""

import os
from pathlib import Path

# Import-Pattern für Root-Level-Scripts
ROOT_IMPORT_PATTERN = '''# Import für Root-Level-Scripts
try:
    # Versuche Backend-Import  
    from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
except ImportError:
    # Fallback für Root-Level-Scripts
    from db_utils_root.db_utils import get_normalized_db_path, get_sqlite_connection'''

def fix_root_import(file_path: Path):
    """Korrigiere Import in Root-Level-Datei"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ersetze problematische Imports
    if 'from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection' in content:
        content = content.replace(
            'from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection',
            ROOT_IMPORT_PATTERN
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Korrigiert: {file_path}")
        return True
    return False

def main():
    """Korrigiere alle Root-Level-Dateien"""
    print("🔧 Korrigiere Root-Level-Imports")
    
    # Wichtigste Root-Level-Dateien
    root_files = [
        "/app/normalized_model_evaluation.py",
        "/app/model_evaluation_system.py",
        "/app/test_batch_search.py",
        "/app/final_coordinate_fix.py",
        "/app/update_mine_coordinates.py",
        "/app/migrate_existing_mines_complete.py",
        "/app/test_complete_data_transfer.py"
    ]
    
    fixed_count = 0
    for file_path in root_files:
        path = Path(file_path)
        if path.exists():
            if fix_root_import(path):
                fixed_count += 1
    
    print(f"📊 {fixed_count} Dateien korrigiert")

if __name__ == "__main__":
    main()