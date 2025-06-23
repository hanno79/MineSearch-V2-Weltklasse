#!/usr/bin/env python
"""
Test-Runner-Skript für MineSearch
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Automatisiertes Test- und Qualitätsprüfungs-Skript
"""
import sys
import subprocess
from pathlib import Path


def run_command(cmd: list) -> int:
    """Befehl ausführen und Exit-Code zurückgeben"""
    print(f"\n{'='*60}")
    print(f"Ausführung: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Tests mit verschiedenen Optionen ausführen"""
    project_root = Path(__file__).parent
    
    # Prüfung ob virtuelle Umgebung aktiv ist
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warnung: Keine virtuelle Umgebung aktiv!")
        print("   Aktivieren Sie zuerst venv: source venv/bin/activate\n")
    
    # Test-Abhängigkeiten installieren falls benötigt
    print("📦 Installiere Test-Abhängigkeiten...")
    run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    
    # Unit-Tests ausführen
    print("\n🧪 Führe Unit-Tests aus...")
    exit_code = run_command([
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "not slow and not integration",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html"
    ])
    
    if exit_code != 0:
        print("\n❌ Unit-Tests fehlgeschlagen!")
        return exit_code
    
    print("\n✅ Unit-Tests erfolgreich!")
    
    # Integrations-Tests falls angefordert
    if "--integration" in sys.argv:
        print("\n🔗 Führe Integrations-Tests aus...")
        exit_code = run_command([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v", 
            "-m", "integration",
            "--cov=src",
            "--cov-append",
            "--cov-report=term-missing"
        ])
        
        if exit_code != 0:
            print("\n⚠️  Integrations-Tests fehlgeschlagen (nicht kritisch)")
    
    # Langsame Tests falls angefordert
    if "--slow" in sys.argv:
        print("\n🐌 Führe langsame Tests aus...")
        run_command([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "-m", "slow",
            "--cov=src",
            "--cov-append"
        ])
    
    # Finalen Coverage-Report generieren
    print("\n📊 Generiere Coverage-Report...")
    run_command([sys.executable, "-m", "coverage", "report", "-m"])
    
    print("\n📄 HTML Coverage-Report generiert in: htmlcov/index.html")
    print("   Öffnen mit: open htmlcov/index.html\n")
    
    # Code-Qualitätsprüfungen falls angefordert
    if "--quality" in sys.argv:
        print("\n🎨 Führe Code-Qualitätsprüfungen aus...")
        
        # Ruff
        print("\n🔍 Führe Ruff aus...")
        run_command([sys.executable, "-m", "ruff", "check", "src/", "tests/"])
        
        # Black
        print("\n⚫ Prüfe Black-Formatierung...")
        run_command([sys.executable, "-m", "black", "--check", "src/", "tests/"])
        
        # isort
        print("\n📦 Prüfe Import-Sortierung...")
        run_command([sys.executable, "-m", "isort", "--check-only", "src/", "tests/"])
        
        # mypy
        print("\n🔍 Führe Type-Checking aus...")
        run_command([sys.executable, "-m", "mypy", "src/", "--ignore-missing-imports"])
    
    print("\n✨ Alle Tests abgeschlossen!")
    return 0


if __name__ == "__main__":
    sys.exit(main())