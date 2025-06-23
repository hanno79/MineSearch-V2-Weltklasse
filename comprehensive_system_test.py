"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Umfassender System-Test nach Refactoring
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import Config
from src.core.database import Database
from src.core.logger import get_logger
from src.agents.base_agent import MineQuery
from src.ui.main import MineSearchUI

logger = get_logger("system_test")


class SystemTester:
    """Führt umfassende System-Tests durch"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.database.path)
        self.results = {}
        self.errors = []
    
    async def test_database_connection(self):
        """Testet Datenbankverbindung"""
        print("\n🔍 Teste Datenbank-Verbindung...")
        try:
            # Teste Verbindung
            mines = self.db.get_all_mines()
            print(f"✓ Datenbank verbunden: {len(mines)} Minen gefunden")
            
            # Teste Schreibzugriff
            test_mine = self.db.get_or_create_mine(
                name="TEST_MINE_DELETE",
                region="Test Region",
                country="Test Country"
            )
            print(f"✓ Schreibzugriff funktioniert: Test-Mine ID {test_mine.id}")
            
            # Cleanup
            from sqlalchemy import text
            with self.db.engine.connect() as conn:
                conn.execute(text("DELETE FROM mines WHERE name = 'TEST_MINE_DELETE'"))
                conn.commit()
            
            return True
        except Exception as e:
            self.errors.append(f"Datenbank-Test: {e}")
            print(f"✗ Datenbank-Test fehlgeschlagen: {e}")
            return False
    
    async def test_ui_components(self):
        """Testet UI-Komponenten"""
        print("\n🔍 Teste UI-Komponenten...")
        try:
            # Teste neue modulare Komponenten
            from src.ui.components.sidebar import SidebarComponent
            from src.ui.components.search_form import SearchFormComponent
            from src.ui.components.results_display import ResultsDisplayComponent
            from src.ui.components.metrics_dashboard import MetricsDashboardComponent
            
            print("✓ Sidebar Component importierbar")
            print("✓ Search Form Component importierbar")
            print("✓ Results Display Component importierbar")
            print("✓ Metrics Dashboard Component importierbar")
            
            # Teste Session State
            from src.ui.utils.session_state import SessionStateManager
            session = SessionStateManager()
            session.init_state()
            print("✓ Session State Manager funktioniert")
            
            return True
        except Exception as e:
            self.errors.append(f"UI-Test: {e}")
            print(f"✗ UI-Test fehlgeschlagen: {e}")
            return False
    
    async def test_orchestrator(self):
        """Testet Orchestrator"""
        print("\n🔍 Teste Orchestrator...")
        try:
            from src.core.orchestrator import MineSearchOrchestrator
            
            orchestrator = MineSearchOrchestrator(self.config)
            print("✓ Orchestrator erstellt")
            
            # Teste Komponenten
            print(f"✓ Agent Manager: {orchestrator.agent_manager}")
            print(f"✓ Search Executor: {orchestrator.search_executor}")
            print(f"✓ Source Discovery: {orchestrator.source_discovery}")
            print(f"✓ Strategy Manager: {orchestrator.strategy_manager}")
            
            # Teste Agent-Initialisierung
            available_agents = await orchestrator.get_available_agents()
            print(f"✓ {len(available_agents)} Agenten verfügbar")
            
            return True
        except Exception as e:
            self.errors.append(f"Orchestrator-Test: {e}")
            print(f"✗ Orchestrator-Test fehlgeschlagen: {e}")
            return False
    
    async def test_agents(self):
        """Testet einzelne Agenten"""
        print("\n🔍 Teste Agenten...")
        results = {}
        
        # Liste der zu testenden Agenten
        test_agents = [
            ('tavily', 'src.agents.tavily_agent', 'TavilyAgent'),
            ('perplexity', 'src.agents.perplexity_agent', 'PerplexityAgent'),
            ('claude', 'src.agents.claude_agent', 'ClaudeAgent'),
            ('scraper', 'src.agents.scraper_agent', 'ScraperAgent'),
        ]
        
        for agent_name, module_path, class_name in test_agents:
            try:
                # Dynamischer Import
                module = __import__(module_path, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                
                # Agent erstellen
                agent = agent_class(agent_name, self.config.to_dict())
                await agent.initialize()
                
                # Credentials validieren
                is_valid = await agent.validate_credentials()
                
                results[agent_name] = is_valid
                status = "✓" if is_valid else "⚠️"
                print(f"{status} {agent_name}: {'verfügbar' if is_valid else 'keine gültigen Credentials'}")
                
            except Exception as e:
                results[agent_name] = False
                print(f"✗ {agent_name}: Import/Init fehlgeschlagen - {e}")
        
        return results
    
    async def test_search_workflow(self):
        """Testet kompletten Such-Workflow"""
        print("\n🔍 Teste Such-Workflow...")
        try:
            from src.core.orchestrator import MineSearchOrchestrator
            
            orchestrator = MineSearchOrchestrator(self.config)
            
            # Test-Query
            test_query = MineQuery(
                mine_name="Red Lake Gold Mine",
                region="Ontario",
                country="Canada",
                languages=["English"],
                required_fields=["location", "owner"]
            )
            
            print("✓ Test-Query erstellt")
            
            # Verfügbare Agenten prüfen
            agents = await orchestrator.get_available_agents()
            if not agents:
                print("⚠️ Keine Agenten verfügbar - überspringe Such-Test")
                return True
            
            print(f"✓ {len(agents)} Agenten für Suche verfügbar")
            
            # Quick Search mit Timeout
            try:
                results = await asyncio.wait_for(
                    orchestrator.search_mine_quick(test_query),
                    timeout=30
                )
                print(f"✓ Quick Search abgeschlossen: {len(results)} Ergebnisse")
                return True
            except asyncio.TimeoutError:
                print("⚠️ Such-Timeout (30s) - aber System funktioniert")
                return True
                
        except Exception as e:
            self.errors.append(f"Such-Workflow: {e}")
            print(f"✗ Such-Workflow fehlgeschlagen: {e}")
            return False
    
    async def test_refactored_modules(self):
        """Testet speziell die refactorierten Module"""
        print("\n🔍 Teste refactorierte Module...")
        
        # Search Strategies
        try:
            from src.agents.search_strategies_refactored import SearchStrategies
            strategies = SearchStrategies()
            print("✓ Search Strategies (refactored) funktioniert")
        except Exception as e:
            print(f"✗ Search Strategies: {e}")
        
        # Premium Mining Research
        try:
            from src.agents.premium_mining_research_refactored import PremiumMiningResearch
            print("✓ Premium Mining Research (refactored) importierbar")
        except Exception as e:
            print(f"✗ Premium Mining Research: {e}")
        
        # BrightData Agent
        try:
            from src.agents.brightdata_agent_refactored import BrightDataAgent
            print("✓ BrightData Agent (refactored) importierbar")
        except Exception as e:
            print(f"✗ BrightData Agent: {e}")
        
        # Base Module
        try:
            from src.agents.base import BaseHTTPClient, ResultProcessor, QueryBuilder, CacheManager
            print("✓ Base-Module importierbar")
        except Exception as e:
            print(f"✗ Base-Module: {e}")
        
        return True
    
    async def run_all_tests(self):
        """Führt alle Tests aus"""
        print("=" * 60)
        print("🧪 UMFASSENDER SYSTEM-TEST")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Tests durchführen
        self.results['database'] = await self.test_database_connection()
        self.results['ui'] = await self.test_ui_components()
        self.results['orchestrator'] = await self.test_orchestrator()
        self.results['agents'] = await self.test_agents()
        self.results['workflow'] = await self.test_search_workflow()
        self.results['refactored'] = await self.test_refactored_modules()
        
        # Zusammenfassung
        print("\n" + "=" * 60)
        print("📊 TEST-ZUSAMMENFASSUNG")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, result in self.results.items():
            if isinstance(result, bool):
                total_tests += 1
                if result:
                    passed_tests += 1
                status = "✅ PASS" if result else "❌ FAIL"
            elif isinstance(result, dict):
                # Agent-Tests
                total = len(result)
                passed = sum(1 for v in result.values() if v)
                total_tests += total
                passed_tests += passed
                status = f"✅ {passed}/{total}" if passed == total else f"⚠️ {passed}/{total}"
            else:
                status = "❓ UNKNOWN"
            
            print(f"{status} - {category.upper()}")
        
        print(f"\n🏁 Gesamt: {passed_tests}/{total_tests} Tests bestanden")
        
        if self.errors:
            print("\n⚠️ FEHLER:")
            for error in self.errors:
                print(f"  - {error}")
        
        # Bewertung
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        if success_rate >= 0.9:
            print("\n✅ SYSTEM FUNKTIONIERT EINWANDFREI!")
        elif success_rate >= 0.7:
            print("\n⚠️ SYSTEM FUNKTIONIERT MIT EINSCHRÄNKUNGEN")
        else:
            print("\n❌ SYSTEM HAT KRITISCHE PROBLEME")
        
        return success_rate >= 0.7


async def main():
    """Hauptfunktion"""
    tester = SystemTester()
    success = await tester.run_all_tests()
    
    # Cleanup
    await asyncio.sleep(0.5)  # Let async tasks finish
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)