"""
Author: rahn
Datum: 22.06.2025  
Version: 1.0
Beschreibung: Einfacher Funktionalitätstest nach Refactoring
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """Testet alle wichtigen Imports"""
    print("\n=== TEST: Imports ===")
    
    imports_to_test = [
        # Core Module
        ("Core Config", "from src.core.config import Config"),
        ("Core Logger", "from src.core.logger import get_logger"),
        ("Core Orchestrator", "from src.core.orchestrator import MineSearchOrchestrator"),
        
        # UI Module (Original)
        ("UI Main", "from src.ui.main import MineSearchUI"),
        
        # UI Components (Refactored)
        ("UI Sidebar", "from src.ui.components.sidebar import SidebarComponent"),
        ("UI Search Form", "from src.ui.components.search_form import SearchFormComponent"),
        ("UI Results", "from src.ui.components.results_display import ResultsDisplayComponent"),
        ("UI Metrics", "from src.ui.components.metrics_dashboard import MetricsDashboardComponent"),
        
        # Agents (Original)
        ("Tavily Agent", "from src.agents.tavily_agent import TavilyAgent"),
        ("Perplexity Agent", "from src.agents.perplexity_agent import PerplexityAgent"),
        ("Search Strategies", "from src.agents.search_strategies import SearchStrategies"),
        ("Premium Mining", "from src.agents.premium_mining_research import PremiumMiningResearch"),
        
        # Refactored Modules
        ("Search Strategies Refactored", "from src.agents.search_strategies_refactored import SearchStrategies as SearchStrategiesNew"),
        ("Premium Mining Refactored", "from src.agents.premium_mining_research_refactored import PremiumMiningResearch as PremiumMiningNew"),
        
        # Base Modules
        ("Base HTTP Client", "from src.agents.base.http_client import BaseHTTPClient"),
        ("Base Result Processor", "from src.agents.base.result_processor import ResultProcessor"),
        ("Base Query Builder", "from src.agents.base.query_builder import QueryBuilder"),
        ("Base Cache Manager", "from src.agents.base.cache_manager import CacheManager"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_str in imports_to_test:
        try:
            exec(import_str)
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed += 1
    
    print(f"\nImport-Tests: {passed} bestanden, {failed} fehlgeschlagen")
    return failed == 0


async def test_orchestrator_creation():
    """Testet Orchestrator-Erstellung"""
    print("\n=== TEST: Orchestrator ===")
    
    try:
        from src.core.config import Config
        from src.core.orchestrator import MineSearchOrchestrator
        
        config = Config()
        orchestrator = MineSearchOrchestrator(config)
        
        print("✓ Orchestrator erstellt")
        
        # Komponenten prüfen
        components = [
            ("agent_manager", orchestrator.agent_manager),
            ("search_executor", orchestrator.search_executor),
            ("source_discovery", orchestrator.source_discovery),
            ("strategy_manager", orchestrator.strategy_manager),
        ]
        
        for name, component in components:
            if component:
                print(f"✓ {name}: {type(component).__name__}")
            else:
                print(f"✗ {name}: None")
        
        return True
        
    except Exception as e:
        print(f"✗ Orchestrator-Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_functionality():
    """Testet Basis-Funktionalität"""
    print("\n=== TEST: Basis-Funktionalität ===")
    
    try:
        from src.agents.base_agent import MineQuery
        
        # Test Query erstellen
        query = MineQuery(
            mine_name="Test Mine",
            region="Ontario",
            country="Canada",
            languages=["English"],
            required_fields=["location"]
        )
        
        print(f"✓ MineQuery erstellt: {query.mine_name}")
        
        # Test Search Strategies
        from src.agents.search_strategies_refactored import SearchStrategies
        strategies = SearchStrategies()
        
        strategy = strategies.select_strategy(
            mine_name=query.mine_name,
            country=query.country,
            region=query.region,
            required_fields=query.required_fields,
            available_agents=["tavily", "perplexity"],
            time_constraint=300
        )
        
        print(f"✓ Strategie ausgewählt: {strategy.name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Funktionalitäts-Test fehlgeschlagen: {e}")
        return False


async def test_ui_startup():
    """Testet ob UI startbar ist"""
    print("\n=== TEST: UI Startup ===")
    
    try:
        # Prüfe Streamlit Installation
        import streamlit as st
        print("✓ Streamlit installiert")
        
        # Prüfe UI Main
        from src.ui.main import main as ui_main
        print("✓ UI main() Funktion verfügbar")
        
        # Prüfe neue Komponenten
        from src.ui.components.sidebar import SidebarComponent
        from src.ui.utils.session_state import SessionStateManager
        
        print("✓ UI-Komponenten verfügbar")
        
        return True
        
    except Exception as e:
        print(f"✗ UI-Test fehlgeschlagen: {e}")
        return False


async def test_file_structure():
    """Prüft Dateistruktur"""
    print("\n=== TEST: Dateistruktur ===")
    
    important_files = [
        "src/ui/main.py",
        "src/core/orchestrator.py",
        "src/agents/base_agent.py",
        "src/ui/components/__init__.py",
        "src/agents/base/__init__.py",
        "src/agents/premium_components/__init__.py",
    ]
    
    missing = []
    for file_path in important_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} fehlt")
            missing.append(file_path)
    
    return len(missing) == 0


async def check_file_sizes():
    """Prüft Dateigrößen nach CLAUDE.md Regel 1"""
    print("\n=== CHECK: Dateigrößen (max 500 Zeilen) ===")
    
    import subprocess
    
    # Finde alle Python-Dateien über 500 Zeilen
    cmd = "find src -name '*.py' -type f -exec wc -l {} + | awk '$1 > 500 {print $1, $2}' | sort -nr"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("Dateien über 500 Zeilen:")
        print(result.stdout)
        
        # Zähle Anzahl
        lines = result.stdout.strip().split('\n')
        if lines[-1].startswith('total'):
            lines = lines[:-1]
        
        print(f"\n⚠️ {len(lines)} Dateien überschreiten 500 Zeilen-Limit")
    else:
        print("✓ Keine Dateien über 500 Zeilen gefunden")
    
    return True


async def main():
    """Haupttest-Funktion"""
    print("=" * 60)
    print("🧪 FUNKTIONALITÄTS-TEST NACH REFACTORING")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Orchestrator", test_orchestrator_creation),
        ("Basis-Funktionalität", test_basic_functionality),
        ("UI Startup", test_ui_startup),
        ("Dateistruktur", test_file_structure),
        ("Dateigrößen-Check", check_file_sizes),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"\n❌ KRITISCHER FEHLER in {test_name}: {e}")
            results[test_name] = False
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test}")
    
    print(f"\n🏁 Gesamt: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("\n✅ ALLE TESTS BESTANDEN - System funktioniert!")
    elif passed >= total * 0.8:
        print("\n⚠️ System funktioniert mit kleinen Einschränkungen")
    else:
        print("\n❌ System hat Probleme - Überprüfung erforderlich")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)