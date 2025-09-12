#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Automatisches Beheben der häufigsten Linter-Fehler
"""

import os
import re
import glob
from pathlib import Path

def fix_file(filepath):
    """Behebt Linter-Fehler in einer Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # W293: blank line contains whitespace
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            if line.strip() == '' and line != '':
                fixed_lines.append('')
                fixes_applied.append('W293')
            else:
                fixed_lines.append(line)
        content = '\n'.join(fixed_lines)
        
        # W291: trailing whitespace
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            fixed_line = line.rstrip()
            if line != fixed_line:
                fixes_applied.append('W291')
            fixed_lines.append(fixed_line)
        content = '\n'.join(fixed_lines)
        
        # W292: no newline at end of file
        if content and not content.endswith('\n'):
            content += '\n'
            fixes_applied.append('W292')
        
        # E501: line too long (vereinfacht - nur sehr lange Zeilen)
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            if len(line) > 120:  # Nur sehr lange Zeilen
                # Versuche Zeile zu brechen
                if ' ' in line:
                    words = line.split(' ')
                    new_line = ''
                    for word in words:
                        if len(new_line + word) > 100:
                            fixed_lines.append(new_line.rstrip())
                            new_line = word + ' '
                        else:
                            new_line += word + ' '
                    fixed_lines.append(new_line.rstrip())
                    fixes_applied.append('E501')
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        content = '\n'.join(fixed_lines)
        
        # F401: unused imports (vereinfacht - nur offensichtliche)
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            # Entferne offensichtlich ungenutzte Imports
            if re.match(r'^from typing import.*Dict.*$', line.strip()) and 'Dict' not in content:
                continue
            elif re.match(r'^from typing import.*List.*$', line.strip()) and 'List' not in content:
                continue
            elif re.match(r'^from typing import.*Any.*$', line.strip()) and 'Any' not in content:
                continue
            elif re.match(r'^from typing import.*Optional.*$', line.strip()) and 'Optional' not in content:
                continue
            else:
                fixed_lines.append(line)
        content = '\n'.join(fixed_lines)
        
        # E302: expected 2 blank lines (vereinfacht)
        lines = content.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            fixed_lines.append(line)
            # Füge Leerzeile vor Klassen/Funktionen hinzu
            if (line.strip().startswith('class ') or line.strip().startswith('def ')) and i > 0:
                if lines[i-1].strip() != '' and lines[i-2].strip() != '':
                    fixed_lines.insert(-1, '')
                    fixes_applied.append('E302')
        
        # Speichere nur wenn Änderungen vorgenommen wurden
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            unique_fixes = list(set(fixes_applied))
            print(f"✅ {filepath}: {', '.join(unique_fixes)}")
            return len(unique_fixes)
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Fehler bei {filepath}: {e}")
        return 0

def main():
    """Hauptfunktion"""
    print("🔧 Starte automatische Linter-Fehler-Behebung...")
    
    # Finde alle Python-Dateien
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Überspringe bestimmte Verzeichnisse
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                python_files.append(filepath)
    
    print(f"📊 Gefunden: {len(python_files)} Python-Dateien")
    
    total_fixes = 0
    files_fixed = 0
    
    # Behebe Fehler in jeder Datei
    for filepath in python_files:
        fixes = fix_file(filepath)
        if fixes > 0:
            total_fixes += fixes
            files_fixed += 1
    
    print(f"\n🎯 Zusammenfassung:")
    print(f"   📁 Dateien verarbeitet: {len(python_files)}")
    print(f"   🔧 Dateien geändert: {files_fixed}")
    print(f"   ✅ Fehler behoben: {total_fixes}")

if __name__ == "__main__":
    main()
