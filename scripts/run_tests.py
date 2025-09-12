#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Test-Runner für alle Unit Tests
"""

import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Führt alle Tests aus"""
    print("🧪 Starte Test-Suite...")
    
    # Füge Backend-Pfad hinzu
    backend_path = os.path.join(os.getcwd(), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    # Finde alle Test-Dateien
    test_files = []
    test_dirs = ['tests/unit', 'tests/integration', 'tests/e2e']
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for root, dirs, files in os.walk(test_dir):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files.append(os.path.join(root, file))
    
    print(f"📊 Gefunden: {len(test_files)} Test-Dateien")
    
    if not test_files:
        print("⚠️  Keine Test-Dateien gefunden!")
        return
    
    # Führe Tests aus
    results = []
    for test_file in test_files:
        print(f"\n🔬 Führe Tests aus: {test_file}")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ {test_file}: Alle Tests bestanden")
                results.append(('PASS', test_file, result.stdout))
            else:
                print(f"❌ {test_file}: Tests fehlgeschlagen")
                results.append(('FAIL', test_file, result.stderr))
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file}: Timeout")
            results.append(('TIMEOUT', test_file, 'Test timeout'))
        except Exception as e:
            print(f"💥 {test_file}: Fehler - {e}")
            results.append(('ERROR', test_file, str(e)))
    
    # Zusammenfassung
    print(f"\n🎯 TEST-ZUSAMMENFASSUNG:")
    print("=" * 50)
    
    passed = len([r for r in results if r[0] == 'PASS'])
    failed = len([r for r in results if r[0] == 'FAIL'])
    errors = len([r for r in results if r[0] in ['ERROR', 'TIMEOUT']])
    
    print(f"✅ Bestanden: {passed}")
    print(f"❌ Fehlgeschlagen: {failed}")
    print(f"💥 Fehler: {errors}")
    print(f"📊 Gesamt: {len(results)}")
    
    if failed > 0 or errors > 0:
        print(f"\n❌ FEHLGESCHLAGENE TESTS:")
        for status, test_file, output in results:
            if status in ['FAIL', 'ERROR', 'TIMEOUT']:
                print(f"  - {test_file}: {status}")
    
    # Berechne Test-Coverage (vereinfacht)
    coverage_percentage = (passed / len(results)) * 100 if results else 0
    print(f"\n📈 Test-Coverage: {coverage_percentage:.1f}%")
    
    return results

def main():
    """Hauptfunktion"""
    try:
        results = run_tests()
        
        # Exit-Code basierend auf Ergebnissen
        failed_tests = len([r for r in results if r[0] in ['FAIL', 'ERROR', 'TIMEOUT']])
        if failed_tests > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"💥 Kritischer Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
