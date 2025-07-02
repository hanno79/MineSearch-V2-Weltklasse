"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Test Runner für MineSearch v2
"""

# ÄNDERUNG 01.07.2025: Test Runner mit Coverage-Report erstellt

import sys
import os
import subprocess
import json
from datetime import datetime

def run_tests():
    """Führe alle Tests aus und generiere Coverage-Report"""
    
    print("=" * 60)
    print("MineSearch v2 - Test Suite")
    print("=" * 60)
    print(f"Start: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("-" * 60)
    
    # Test-Kommando mit Coverage
    test_command = [
        sys.executable, "-m", "pytest",
        "-v",  # Verbose output
        "--cov=backend",  # Coverage für backend Modul
        "--cov-report=html",  # HTML Report
        "--cov-report=term-missing",  # Terminal Report mit fehlenden Zeilen
        "--cov-report=json",  # JSON Report für weitere Verarbeitung
        "--cov-fail-under=70",  # Minimum 70% Coverage
        "--tb=short",  # Kurze Traceback-Ausgabe
        "-x",  # Stop bei erstem Fehler
        "tests/"  # Test-Verzeichnis
    ]
    
    # Optional: Nur bestimmte Tests ausführen
    if len(sys.argv) > 1:
        test_filter = sys.argv[1]
        test_command.extend(["-k", test_filter])
        print(f"Führe nur Tests aus die '{test_filter}' enthalten...")
    
    print("\nFühre Tests aus...\n")
    
    # Tests ausführen
    result = subprocess.run(test_command, cwd=os.path.dirname(__file__))
    
    print("\n" + "-" * 60)
    
    # Coverage-Statistiken anzeigen
    if os.path.exists("coverage.json"):
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)
            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            
            print(f"\nGesamte Test-Coverage: {total_coverage:.2f}%")
            
            if total_coverage >= 70:
                print("✅ Coverage-Ziel erreicht!")
            else:
                print("❌ Coverage-Ziel nicht erreicht (Minimum: 70%)")
    
    # HTML Report Info
    if os.path.exists("htmlcov/index.html"):
        print("\n📊 Detaillierter Coverage-Report verfügbar unter:")
        print(f"   file://{os.path.abspath('htmlcov/index.html')}")
    
    print("\n" + "=" * 60)
    print(f"Ende: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 60)
    
    return result.returncode


def run_specific_test_type(test_type):
    """Führe spezifische Test-Typen aus"""
    
    test_commands = {
        "unit": [sys.executable, "-m", "pytest", "-v", "-m", "unit", "tests/"],
        "integration": [sys.executable, "-m", "pytest", "-v", "-m", "integration", "tests/"],
        "fast": [sys.executable, "-m", "pytest", "-v", "-m", "not slow", "tests/"],
        "api": [sys.executable, "-m", "pytest", "-v", "-m", "api", "tests/"],
    }
    
    if test_type in test_commands:
        print(f"\nFühre {test_type.upper()} Tests aus...\n")
        result = subprocess.run(test_commands[test_type])
        return result.returncode
    else:
        print(f"Unbekannter Test-Typ: {test_type}")
        print(f"Verfügbare Typen: {', '.join(test_commands.keys())}")
        return 1


def generate_test_report():
    """Generiere einen Test-Report"""
    
    print("\nGeneriere Test-Report...\n")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "coverage": {}
    }
    
    # Test-Ergebnisse sammeln
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--json-report", "--json-report-file=test_report.json", "tests/"],
        capture_output=True,
        text=True
    )
    
    if os.path.exists("test_report.json"):
        with open("test_report.json", "r") as f:
            test_data = json.load(f)
            report["tests"] = test_data.get("tests", {})
            report["summary"] = test_data.get("summary", {})
    
    # Coverage-Daten hinzufügen
    if os.path.exists("coverage.json"):
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)
            report["coverage"] = coverage_data.get("totals", {})
    
    # Report speichern
    report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Test-Report gespeichert: {report_filename}")
    
    return report_filename


def main():
    """Hauptfunktion"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "report":
            generate_test_report()
        elif command in ["unit", "integration", "fast", "api"]:
            return run_specific_test_type(command)
        else:
            # Als Test-Filter interpretieren
            return run_tests()
    else:
        # Alle Tests ausführen
        return run_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)