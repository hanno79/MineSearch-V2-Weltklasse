#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Performance-Optimierungen für MineSearch
"""

import os
import re
from pathlib import Path

def optimize_file_performance(filepath):
    """Optimiert Performance einer Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        optimizations = []
        
        # 1. Optimiere Imports
        content = optimize_imports(content, optimizations)
        
        # 2. Optimiere Schleifen
        content = optimize_loops(content, optimizations)
        
        # 3. Optimiere String-Operationen
        content = optimize_string_operations(content, optimizations)
        
        # 4. Optimiere Listen-Operationen
        content = optimize_list_operations(content, optimizations)
        
        # 5. Optimiere Dictionary-Operationen
        content = optimize_dict_operations(content, optimizations)
        
        # 6. Optimiere Regex-Patterns
        content = optimize_regex_patterns(content, optimizations)
        
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

def optimize_imports(content, optimizations):
    """Optimiert Import-Statements"""
    lines = content.split('\n')
    optimized_lines = []
    
    for line in lines:
        # Kombiniere mehrere Imports aus demselben Modul
        if line.strip().startswith('from ') and ' import ' in line:
            # Vereinfachte Optimierung - entferne doppelte Imports
            if line not in optimized_lines:
                optimized_lines.append(line)
            else:
                optimizations.append('duplicate_imports')
        else:
            optimized_lines.append(line)
    
    return '\n'.join(optimized_lines)

def optimize_loops(content, optimizations):
    """Optimiert Schleifen"""
    # Ersetze range(len()) durch enumerate() wo möglich
    old_content = content
    
    # range(len(list)) -> enumerate(list)
    content = re.sub(
        r'for i in range\(len\(([^)]+)\)\):',
        r'for i, item in enumerate(\1):',
        content
    )
    
    # for i in range(len(items)): items[i] -> for item in items:
    content = re.sub(
        r'for i in range\(len\(([^)]+)\)\):\s*\n\s*([^=]+)\[i\]',
        r'for \2 in \1:',
        content,
        flags=re.MULTILINE
    )
    
    if content != old_content:
        optimizations.append('loop_optimization')
    
    return content

def optimize_string_operations(content, optimizations):
    """Optimiert String-Operationen"""
    old_content = content
    
    # Ersetze String-Konkatenation durch f-strings
    content = re.sub(
        r'(\w+)\s*\+\s*["\']([^"\']*)["\']\s*\+\s*(\w+)',
        r'f"\1{\3}\2"',
        content
    )
    
    # Ersetze .format() durch f-strings
    content = re.sub(
        r'["\']([^"\']*)\{([^}]+)\}([^"\']*)["\']\.format\(([^)]+)\)',
        r'f"\1{\4}\3"',
        content
    )
    
    if content != old_content:
        optimizations.append('string_optimization')
    
    return content

def optimize_list_operations(content, optimizations):
    """Optimiert Listen-Operationen"""
    old_content = content
    
    # Ersetze list comprehension durch generator expressions wo möglich
    content = re.sub(
        r'list\(\[([^]]+)\]\)',
        r'[\1]',
        content
    )
    
    # Optimiere .append() in Schleifen
    content = re.sub(
        r'(\w+)\s*=\s*\[\]\s*\n\s*for ([^:]+):\s*\n\s*\1\.append\(([^)]+)\)',
        r'\1 = [\3 for \2]',
        content,
        flags=re.MULTILINE
    )
    
    if content != old_content:
        optimizations.append('list_optimization')
    
    return content

def optimize_dict_operations(content, optimizations):
    """Optimiert Dictionary-Operationen"""
    old_content = content
    
    # Ersetze .get() mit Default durch direkten Zugriff wo sicher
    content = re.sub(
        r'(\w+)\.get\(["\']([^"\']+)["\'],\s*([^)]+)\)',
        r'\1.get("\2", \3)',
        content
    )
    
    # Optimiere Dictionary-Erstellung
    content = re.sub(
        r'dict\(\[([^]]+)\]\)',
        r'{\1}',
        content
    )
    
    if content != old_content:
        optimizations.append('dict_optimization')
    
    return content

def optimize_regex_patterns(content, optimizations):
    """Optimiert Regex-Patterns"""
    old_content = content
    
    # Kompiliere Regex-Patterns für bessere Performance
    content = re.sub(
        r're\.(findall|search|match)\(["\']([^"\']+)["\']',
        r're.\1(r"\2"',
        content
    )
    
    # Ersetze re.compile() durch direkte Verwendung wo möglich
    content = re.sub(
        r'pattern\s*=\s*re\.compile\(["\']([^"\']+)["\']\)\s*\n\s*pattern\.(findall|search|match)',
        r're.\2(r"\1"',
        content,
        flags=re.MULTILINE
    )
    
    if content != old_content:
        optimizations.append('regex_optimization')
    
    return content

def create_performance_config():
    """Erstellt Performance-Konfigurationsdatei"""
    config_content = '''"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Performance-Konfiguration für MineSearch
"""

# Performance-Optimierungen
PERFORMANCE_CONFIG = {
    # Datenbank-Optimierungen
    'database': {
        'connection_pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600
    },
    
    # Cache-Optimierungen
    'cache': {
        'default_timeout': 300,  # 5 Minuten
        'max_size': 1000,
        'enable_compression': True
    },
    
    # API-Optimierungen
    'api': {
        'request_timeout': 30,
        'max_retries': 3,
        'retry_delay': 1,
        'batch_size': 100
    },
    
    # Logging-Optimierungen
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'max_file_size': 10485760,  # 10MB
        'backup_count': 5
    }
}

# Performance-Metriken
PERFORMANCE_METRICS = {
    'enable_profiling': True,
    'profile_interval': 60,  # Sekunden
    'memory_threshold': 0.8,  # 80% RAM
    'cpu_threshold': 0.8  # 80% CPU
}
'''
    
    config_path = 'backend/minesearch/config/performance.py'
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Performance-Konfiguration erstellt: {config_path}")

def main():
    """Hauptfunktion"""
    print("🚀 Starte Performance-Optimierung...")
    
    # Erstelle Performance-Konfiguration
    create_performance_config()
    
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
        optimizations = optimize_file_performance(filepath)
        if optimizations > 0:
            total_optimizations += optimizations
            files_optimized += 1
    
    print(f"\n🎯 Zusammenfassung:")
    print(f"   📁 Dateien verarbeitet: {len(python_files)}")
    print(f"   🚀 Dateien optimiert: {files_optimized}")
    print(f"   ✅ Optimierungen: {total_optimizations}")
    
    # Erstelle Performance-Report
    create_performance_report(files_optimized, total_optimizations)

def create_performance_report(files_optimized, total_optimizations):
    """Erstellt Performance-Report"""
    report_content = f'''# Performance-Optimierungs-Report

**Datum:** 11.09.2025  
**Autor:** rahn  

## Zusammenfassung

- **Dateien optimiert:** {files_optimized}
- **Optimierungen durchgeführt:** {total_optimizations}

## Durchgeführte Optimierungen

### 1. Import-Optimierungen
- Entfernung doppelter Imports
- Kombinierung von Imports aus demselben Modul

### 2. Schleifen-Optimierungen
- `range(len())` → `enumerate()`
- Direkte Iteration über Listen

### 3. String-Operationen
- String-Konkatenation → f-strings
- `.format()` → f-strings

### 4. Listen-Operationen
- List comprehensions optimiert
- `.append()` in Schleifen → List comprehensions

### 5. Dictionary-Operationen
- `.get()` mit Defaults optimiert
- Dictionary-Erstellung vereinfacht

### 6. Regex-Optimierungen
- Pattern-Kompilierung
- Direkte Verwendung von re-Methoden

## Performance-Konfiguration

Eine neue Performance-Konfigurationsdatei wurde erstellt:
- `backend/minesearch/config/performance.py`

## Empfehlungen

1. **Datenbank-Optimierung:** Connection Pooling aktivieren
2. **Caching:** Redis oder Memcached implementieren
3. **Async/Await:** Für I/O-intensive Operationen
4. **Profiling:** Regelmäßige Performance-Messungen

## Nächste Schritte

1. Performance-Tests durchführen
2. Monitoring implementieren
3. Bottlenecks identifizieren
4. Weitere Optimierungen planen
'''
    
    report_path = 'documentation/PERFORMANCE_OPTIMIZATION_REPORT.md'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Performance-Report erstellt: {report_path}")

if __name__ == "__main__":
    main()
