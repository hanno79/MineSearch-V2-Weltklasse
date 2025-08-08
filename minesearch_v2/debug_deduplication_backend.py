#!/usr/bin/env python3
"""
Author: rahn
Datum: 28.07.2025
Version: 1.0
Beschreibung: Backend-Debug-Script für Deduplizierungs-Integration
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def check_file_exists(file_path):
    """Check if a file exists and return its size"""
    try:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            return True, size
        return False, 0
    except Exception as e:
        return False, str(e)

def check_deduplication_files():
    """Check if all deduplication-related files exist"""
    print("=== DEDUPLIZIERUNGS-DATEI-ANALYSE ===\n")
    
    files_to_check = [
        "/app/minesearch_v2/frontend/js/deduplication-engine.js",
        "/app/frontend/index.html",
        "/app/minesearch_v2/frontend/debug_deduplication_live.html"
    ]
    
    for file_path in files_to_check:
        exists, size = check_file_exists(file_path)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        size_info = f"({size} bytes)" if exists else ""
        print(f"{status} {file_path} {size_info}")
    
    print()

def check_html_integration():
    """Check if the integration code exists in index.html"""
    print("=== HTML-INTEGRATIONS-ANALYSE ===\n")
    
    html_file = "/app/frontend/index.html"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key integration points
        checks = [
            ('Script-Import', '<script src="js/deduplication-engine.js"></script>'),
            ('detectFieldType Funktion', 'function detectFieldType(fieldName)'),
            ('displayConsolidatedResults Funktion', 'function displayConsolidatedResults(results, sortBy, order)'),
            ('Deduplication-Logic', 'window.deduplicationEngine.deduplicateValues'),
            ('Debug-Output', 'console.log(`Deduplication applied to ${field}:'),
            ('Field-Type-Detection', 'const fieldType = detectFieldType(field);')
        ]
        
        for check_name, search_string in checks:
            found = search_string in content
            status = "✅ FOUND" if found else "❌ MISSING"
            print(f"{status} {check_name}")
            
            if found:
                # Find line number
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if search_string in line:
                        print(f"         Zeile {i}: {line.strip()[:100]}...")
                        break
            print()
        
    except Exception as e:
        print(f"❌ ERROR reading {html_file}: {e}")

def check_browser_server():
    """Check if we can start a simple HTTP server to test in browser"""
    print("=== BROWSER-TEST-SERVER ===\n")
    
    frontend_dir = "/app/frontend"
    
    try:
        # Change to frontend directory
        os.chdir(frontend_dir)
        
        print(f"Starting HTTP server in {frontend_dir}")
        print("To test deduplication:")
        print("1. Open http://localhost:8001/debug_deduplication_live.html")
        print("2. Check browser console for errors")
        print("3. Run all tests in the browser")
        print("\nServer starting... (Press Ctrl+C to stop)")
        
        # Start simple HTTP server (Python 3)
        subprocess.run([sys.executable, "-m", "http.server", "8001"])
        
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"❌ ERROR starting server: {e}")

def analyze_deduplication_logic():
    """Analyze the deduplication logic in the JavaScript file"""
    print("=== JAVASCRIPT-LOGIC-ANALYSE ===\n")
    
    js_file = "/app/minesearch_v2/frontend/js/deduplication-engine.js"
    
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ('DeduplicationEngine Class', 'class DeduplicationEngine'),
            ('Global Instance', 'window.deduplicationEngine = new DeduplicationEngine()'),
            ('Synonym Maps', 'initializeSynonymMaps()'),
            ('Main Function', 'deduplicateValues(valuesString, fieldType'),
            ('DOM Ready Listener', 'document.addEventListener(\'DOMContentLoaded\''),
            ('Console Logging', 'console.log(\'Deduplication Engine initialized')
        ]
        
        for check_name, search_string in checks:
            found = search_string in content
            status = "✅ FOUND" if found else "❌ MISSING"
            print(f"{status} {check_name}")
        
        print(f"\n📊 Total file size: {len(content)} characters")
        print(f"📊 Total lines: {len(content.split(chr(10)))}")
        
        # Check synonym coverage
        country_synonyms = content.count("'canada'") + content.count("'usa'") + content.count("'germany'")
        status_synonyms = content.count("'aktiv'") + content.count("'geplant'") + content.count("'stillgelegt'")
        mineral_synonyms = content.count("'gold'") + content.count("'silver'") + content.count("'copper'")
        
        print(f"📊 Country synonyms defined: ~{country_synonyms}")
        print(f"📊 Status synonyms defined: ~{status_synonyms}")
        print(f"📊 Mineral synonyms defined: ~{mineral_synonyms}")
        
    except Exception as e:
        print(f"❌ ERROR reading {js_file}: {e}")

def main():
    """Main debug function"""
    print("🔧 DEDUPLIZIERUNGS-INTEGRATION DEBUG TOOL\n")
    print("Author: rahn")
    print("Datum: 28.07.2025")
    print("Version: 1.0\n")
    
    check_deduplication_files()
    analyze_deduplication_logic()
    check_html_integration()
    
    print("=== BROWSER-TEST EMPFEHLUNG ===\n")
    print("Für vollständige Tests:")
    print("1. cd /app/minesearch_v2/frontend")
    print("2. python3 -m http.server 8001")
    print("3. Browser: http://localhost:8001/debug_deduplication_live.html")
    print("4. Öffne Browser-Entwicklertools (F12)")
    print("5. Prüfe Console auf Fehler")
    print("6. Führe alle Tests aus")
    
    print("\n=== NÄCHSTE SCHRITTE ===\n")
    print("Wenn Deduplizierung nicht funktioniert:")
    print("1. Prüfe Browser-Console auf JavaScript-Fehler")
    print("2. Teste ob window.deduplicationEngine existiert")
    print("3. Prüfe ob displayConsolidatedResults aufgerufen wird")
    print("4. Validiere Datenformat (müssen ' / ' enthalten)")
    print("5. Prüfe ob detectFieldType korrekte Typen zurückgibt")
    
    choice = input("\nMöchten Sie den Browser-Test-Server starten? (y/n): ").lower()
    if choice == 'y':
        check_browser_server()

if __name__ == "__main__":
    main()