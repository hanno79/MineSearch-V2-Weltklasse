#!/usr/bin/env python3
"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Test Runner mit Coverage Report
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", coverage=True, verbose=False):
    """Führt Tests aus mit optionalem Coverage Report"""
    
    # Base command
    cmd = ["pytest"]
    
    # Test-Pfad
    if test_type == "all":
        cmd.append("tests/")
    elif test_type == "unit":
        cmd.extend(["tests/", "-m", "not integration and not e2e and not slow"])
    elif test_type == "integration":
        cmd.extend(["tests/", "-m", "integration"])
    elif test_type == "e2e":
        cmd.extend(["tests/", "-m", "e2e"])
    elif test_type == "fast":
        cmd.extend(["tests/", "-m", "not slow"])
    else:
        # Spezifische Test-Datei
        cmd.append(f"tests/test_{test_type}.py")
    
    # Coverage
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=json"
        ])
    
    # Verbose
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Weitere Optionen
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "-ra"
    ])
    
    # Farben
    cmd.append("--color=yes")
    
    print(f"Führe Tests aus: {' '.join(cmd)}")
    print("-" * 80)
    
    # Führe Tests aus
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if coverage and result.returncode == 0:
        print("\n" + "=" * 80)
        print("Coverage Report wurde erstellt:")
        print("- HTML Report: htmlcov/index.html")
        print("- JSON Report: coverage.json")
        print("=" * 80)
    
    return result.returncode


def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description="Mining Research System Test Runner"
    )
    
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "e2e", "fast"] + [
            "agents_base", "claude_agent", "perplexity_agent", "scraper_agent",
            "orchestrator", "database", "search_strategies", "premium_mining_research",
            "deepseek_research", "browser_agent", "data_models", "config",
            "logger", "consolidation", "agent_factory", "agent_integration"
        ],
        help="Typ der Tests oder spezifische Test-Datei"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Tests ohne Coverage Report ausführen"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose Output"
    )
    
    parser.add_argument(
        "--markers",
        action="store_true",
        help="Zeige verfügbare Test-Marker"
    )
    
    args = parser.parse_args()
    
    if args.markers:
        print("Verfügbare Test-Marker:")
        print("- unit: Unit Tests")
        print("- integration: Integration Tests")
        print("- e2e: End-to-End Tests")
        print("- slow: Langsame Tests")
        print("- performance: Performance Tests")
        print("- asyncio: Async Tests")
        return 0
    
    # Führe Tests aus
    return run_tests(
        test_type=args.test_type,
        coverage=not args.no_coverage,
        verbose=args.verbose
    )


if __name__ == "__main__":
    sys.exit(main())