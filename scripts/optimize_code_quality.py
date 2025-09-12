#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Automatische Code-Qualitäts-Optimierung
"""

import os
import re
import ast
from pathlib import Path

def optimize_file(filepath):
    """Optimiert Code-Qualität einer Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        optimizations = []
        
        # 1. Entferne ungenutzte Imports
        content = remove_unused_imports(content, optimizations)
        
        # 2. Verbessere String-Formatierung
        content = improve_string_formatting(content, optimizations)
        
        # 3. Optimiere Exception-Handling
        content = optimize_exception_handling(content, optimizations)
        
        # 4. Verbessere Funktions-Dokumentation
        content = improve_function_docs(content, optimizations)
        
        # 5. Optimiere Variablen-Namen
        content = optimize_variable_names(content, optimizations)
        
        # 6. Entferne toten Code
        content = remove_dead_code(content, optimizations)
        
        # Speichere nur wenn Änderungen vorgenommen wurden
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {filepath}: {', '.join(optimizations)}")
            return len(optimizations)
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Fehler bei {filepath}: {e}")
        return 0

def remove_unused_imports(content, optimizations):
    """Entfernt ungenutzte Imports"""
    lines = content.split('\n')
    optimized_lines = []
    
    for line in lines:
        # Prüfe auf Import-Zeilen
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            # Vereinfachte Prüfung - entferne offensichtlich ungenutzte Imports
            if 'typing' in line and 'Dict' in line and 'Dict' not in content:
                continue
            elif 'typing' in line and 'List' in line and 'List' not in content:
                continue
            elif 'typing' in line and 'Any' in line and 'Any' not in content:
                continue
            elif 'typing' in line and 'Optional' in line and 'Optional' not in content:
                continue
            else:
                optimized_lines.append(line)
        else:
            optimized_lines.append(line)
    
    if len(optimized_lines) < len(lines):
        optimizations.append('unused_imports')
    
    return '\n'.join(optimized_lines)

def improve_string_formatting(content, optimizations):
    """Verbessert String-Formatierung"""
    # Ersetze %-Formatierung durch f-strings wo möglich
    old_content = content
    
    # Einfache %-Formatierung ersetzen
    content = re.sub(r'(\w+)\s*%\s*\(([^)]+)\)', r'f"\1{\2}"', content)
    
    if content != old_content:
        optimizations.append('string_formatting')
    
    return content

def optimize_exception_handling(content, optimizations):
    """Optimiert Exception-Handling"""
    lines = content.split('\n')
    optimized_lines = []
    
    for i, line in enumerate(lines):
        # Ersetze generische Exception durch spezifische
        if 'except Exception as e:' in line:
            # Versuche spezifischere Exception zu finden
            context = ' '.join(lines[max(0, i-5):i+5])
            if 'ValueError' in context or 'invalid' in context.lower():
                optimized_lines.append('        except ValueError as e:')
                optimizations.append('exception_handling')
            elif 'KeyError' in context or 'key' in context.lower():
                optimized_lines.append('        except KeyError as e:')
                optimizations.append('exception_handling')
            else:
                optimized_lines.append(line)
        else:
            optimized_lines.append(line)
    
    return '\n'.join(optimized_lines)

def improve_function_docs(content, optimizations):
    """Verbessert Funktions-Dokumentation"""
    lines = content.split('\n')
    optimized_lines = []
    
    for i, line in enumerate(lines):
        optimized_lines.append(line)
        
        # Füge Docstring zu Funktionen ohne hinzu
        if line.strip().startswith('def ') and i < len(lines) - 1:
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if not next_line.strip().startswith('"""') and not next_line.strip().startswith("'''"):
                # Füge einfachen Docstring hinzu
                func_name = line.split('(')[0].replace('def ', '').strip()
                optimized_lines.append(f'    """{func_name} - TODO: Dokumentation hinzufügen"""')
                optimizations.append('function_docs')
    
    return '\n'.join(optimized_lines)

def optimize_variable_names(content, optimizations):
    """Optimiert Variablen-Namen"""
    # Ersetze schlechte Variablen-Namen
    replacements = {
        'temp': 'temporary',
        'tmp': 'temporary',
        'var': 'variable',
        'val': 'value',
        'data': 'data_dict' if 'data' in content and 'dict' in content else 'data'
    }
    
    old_content = content
    for old_name, new_name in replacements.items():
        # Ersetze nur wenn es sinnvoll ist
        if f' {old_name} ' in content and len(new_name) > len(old_name):
            content = content.replace(f' {old_name} ', f' {new_name} ')
    
    if content != old_content:
        optimizations.append('variable_names')
    
    return content

def remove_dead_code(content, optimizations):
    """Entfernt toten Code"""
    lines = content.split('\n')
    optimized_lines = []
    
    for line in lines:
        # Entferne offensichtlich toten Code
        if line.strip().startswith('# TODO: Remove') or line.strip().startswith('# FIXME: Remove'):
            continue
        elif 'print(' in line and 'debug' in line.lower():
            # Entferne Debug-Prints
            continue
        else:
            optimized_lines.append(line)
    
    if len(optimized_lines) < len(lines):
        optimizations.append('dead_code')
    
    return '\n'.join(optimized_lines)

def main():
    """Hauptfunktion"""
    print("🔧 Starte Code-Qualitäts-Optimierung...")
    
    # Finde alle Python-Dateien
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Überspringe bestimmte Verzeichnisse
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules', 'to_delete']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                python_files.append(filepath)
    
    print(f"📊 Gefunden: {len(python_files)} Python-Dateien")
    
    total_optimizations = 0
    files_optimized = 0
    
    # Optimiere jede Datei
    for filepath in python_files:
        optimizations = optimize_file(filepath)
        if optimizations > 0:
            total_optimizations += optimizations
            files_optimized += 1
    
    print(f"\n🎯 Zusammenfassung:")
    print(f"   📁 Dateien verarbeitet: {len(python_files)}")
    print(f"   🔧 Dateien optimiert: {files_optimized}")
    print(f"   ✅ Optimierungen: {total_optimizations}")

if __name__ == "__main__":
    main()
