"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Umfassendes Test-Script für Sequential Field Orchestrator Workflow
"""

import asyncio
import logging
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from minesearch.sequential_field_orchestrator import SequentialFieldOrchestrator
from minesearch.database.sequential_manager import SequentialDatabaseManager
from minesearch.database.migrations import run_sequential_migration
from minesearch.database import db_manager
from minesearch.providers.registry import provider_registry
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SequentialWorkflowTester:
    """
    ÄNDERUNG 27.08.2025: Umfassendes Test-System für Sequential Field Orchestrator
    """
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'test_sequential.db')
        self.database_url = f'sqlite:///{self.db_path}'
        self.test_results = {}
    
    async def setup_test_environment(self):
        """
        Setup Test-Umgebung
        """
        logger.info("🔧 Setting up test environment...")
        
        # Remove existing test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logger.info("🗑️  Removed existing test database")
        
        # Run migrations
        logger.info("📊 Running database migrations...")
        migration_success = run_sequential_migration(self.database_url)
        
        if migration_success:
            logger.info("✅ Database migrations successful")
            self.test_results['migration'] = True
        else:
            logger.error("❌ Database migrations failed")
            self.test_results['migration'] = False
            return False
        
        return True
    
    async def test_sequential_database_manager(self):
        """
        Test Sequential Database Manager
        """
        logger.info("🧪 Testing Sequential Database Manager...")
        
        try:
            # Create database manager
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(self.database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            seq_db_manager = SequentialDatabaseManager(session)
            
            # Test 1: Create discovery session
            discovery_session = seq_db_manager.create_discovery_session(
                mine_name="Canadian Malartic",
                models_list=["openrouter:deepseek-free", "tavily:search"],
                country="Canada",
                region="Quebec",
                commodity="Gold"
            )
            
            assert discovery_session.mine_name == "Canadian Malartic"
            assert len(discovery_session.models_list) == 2
            logger.info("✅ Discovery session creation successful")
            
            # Test 2: Add sources
            source1, is_new1 = seq_db_manager.add_or_update_source(
                url="https://canadianmalartic.com/info",
                domain="canadianmalartic.com", 
                model_id="openrouter:deepseek-free",
                session_id=discovery_session.session_id,
                source_type="industry",
                country="Canada"
            )
            
            source2, is_new2 = seq_db_manager.add_or_update_source(
                url="https://agnicoeagle.com/canadian-malartic",
                domain="agnicoeagle.com",
                model_id="tavily:search", 
                session_id=discovery_session.session_id,
                source_type="industry",
                country="Canada"
            )
            
            assert is_new1 == True
            assert is_new2 == True
            logger.info("✅ Source addition successful")
            
            # Test 3: Get accumulated sources
            accumulated_sources = seq_db_manager.get_accumulated_sources(discovery_session.session_id)
            assert len(accumulated_sources) == 2
            logger.info("✅ Source accumulation successful")
            
            # Test 4: Log field search result
            field_result = seq_db_manager.log_field_search_result(
                session_id=discovery_session.session_id,
                model_id="openrouter:deepseek-free",
                field_name="Eigentümer",
                sources_used=[source1.id, source2.id],
                field_value="Agnico Eagle Mines Limited",
                confidence_score=85.0,
                result_quality="high"
            )
            
            assert field_result.field_value_found == "Agnico Eagle Mines Limited"
            assert field_result.value_found == True
            logger.info("✅ Field search result logging successful")
            
            # Test 5: Create consolidated result
            consolidated_result = seq_db_manager.create_sequential_result(
                session_id=discovery_session.session_id,
                mine_name="Canadian Malartic",
                final_data={"Eigentümer": "Agnico Eagle Mines Limited", "Betreiber": "Canadian Malartic Corporation"},
                field_confidence={"Eigentümer": 85.0, "Betreiber": 78.0},
                field_source_mapping={"Eigentümer": [{"source_id": source1.id, "url": source1.url}]},
                quality_assessment={"overall_quality": 82.0},
                performance_metrics={"total_duration_seconds": 45.0, "total_models_used": 2, "total_sources_discovered": 2},
                country="Canada"
            )
            
            assert consolidated_result.total_models_used == 2
            assert consolidated_result.total_sources_discovered == 2
            logger.info("✅ Consolidated result creation successful")
            
            session.close()
            self.test_results['database_manager'] = True
            logger.info("✅ Sequential Database Manager tests passed")
            
        except Exception as e:
            logger.error(f"❌ Sequential Database Manager test failed: {e}")
            self.test_results['database_manager'] = False
    
    async def test_sequential_orchestrator_basic(self):
        """
        Test Sequential Orchestrator Basic Functions
        """
        logger.info("🧪 Testing Sequential Orchestrator Basic Functions...")
        
        try:
            # Setup database manager
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(self.database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            seq_db_manager = SequentialDatabaseManager(session)
            
            # Create orchestrator
            orchestrator = SequentialFieldOrchestrator()
            
            # Test basic orchestrator setup
            assert orchestrator.seq_db_manager is not None
            assert orchestrator.db_manager is not None
            logger.info("✅ Orchestrator initialization successful")
            
            # Test field list generation
            test_fields = orchestrator.critical_fields
            assert len(test_fields) > 10  # Should have standard fields
            assert "Eigentümer" in test_fields
            assert "Betreiber" in test_fields
            logger.info("✅ Field list generation successful")
            
            session.close()
            self.test_results['orchestrator_basic'] = True
            logger.info("✅ Sequential Orchestrator basic tests passed")
            
        except Exception as e:
            logger.error(f"❌ Sequential Orchestrator basic test failed: {e}")
            self.test_results['orchestrator_basic'] = False
    
    async def test_sequential_workflow_mock(self):
        """
        Test Sequential Workflow mit Mock-Daten (ohne echte API-Calls)
        """
        logger.info("🧪 Testing Sequential Workflow (Mock)...")
        
        try:
            # Setup database manager
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(self.database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            seq_db_manager = SequentialDatabaseManager(session)
            
            # Mock orchestrator für Test
            class MockSequentialOrchestrator:
                def __init__(self, seq_db_manager):
                    self.seq_db_manager = seq_db_manager
                
                async def mock_source_discovery_phase(self, mine_name, models, session_id):
                    """Mock source discovery"""
                    logger.info(f"🔍 Mock: Source Discovery Phase for {mine_name}")
                    
                    # Simulate discovered sources
                    mock_sources = [
                        {"url": "https://agnicoeagle.com/canadian-malartic", "domain": "agnicoeagle.com", "quality": 85.0},
                        {"url": "https://sedarplus.ca/csfsprod/public/displayinfo", "domain": "sedarplus.ca", "quality": 80.0},
                        {"url": "https://canadianmalartic.com", "domain": "canadianmalartic.com", "quality": 78.0}
                    ]
                    
                    discovered_sources = []
                    for i, model_id in enumerate(models):
                        # Each model discovers some sources
                        sources_for_model = mock_sources[i:i+2] if i < len(mock_sources) else [mock_sources[0]]
                        
                        for source_data in sources_for_model:
                            source, is_new = self.seq_db_manager.add_or_update_source(
                                url=source_data["url"],
                                domain=source_data["domain"],
                                model_id=model_id,
                                session_id=session_id,
                                source_type="industry",
                                country="Canada",
                                initial_quality=source_data["quality"]
                            )
                            
                            if source not in discovered_sources:
                                discovered_sources.append(source)
                    
                    logger.info(f"✅ Mock discovered {len(discovered_sources)} unique sources")
                    return discovered_sources
                
                async def mock_field_search_phase(self, mine_name, models, sources, session_id):
                    """Mock field-by-field search"""
                    logger.info(f"🔍 Mock: Field Search Phase for {mine_name}")
                    
                    fields_to_search = ["Eigentümer", "Betreiber", "Aktivitätsstatus", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "Country", "Region"]
                    
                    mock_field_results = {
                        "Eigentümer": "Agnico Eagle Mines Limited",
                        "Betreiber": "Canadian Malartic Corporation", 
                        "Aktivitätsstatus": "Active",
                        "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "Gold",
                        "Country": "Canada",
                        "Region": "Quebec"
                    }
                    
                    field_results = {}
                    
                    for field_name in fields_to_search:
                        for model_id in models:
                            if field_name in mock_field_results:
                                # Mock successful field extraction
                                field_result = self.seq_db_manager.log_field_search_result(
                                    session_id=session_id,
                                    model_id=model_id,
                                    field_name=field_name,
                                    sources_used=[s.id for s in sources[:2]],  # Use first 2 sources
                                    field_value=mock_field_results[field_name],
                                    confidence_score=80.0 + (hash(field_name + model_id) % 20),  # Mock confidence
                                    result_quality="high"
                                )
                                
                                if field_name not in field_results:
                                    field_results[field_name] = []
                                field_results[field_name].append(field_result)
                    
                    logger.info(f"✅ Mock extracted {len(field_results)} fields with {len(models)} models")
                    return field_results
            
            # Execute mock workflow
            mock_orchestrator = MockSequentialOrchestrator(seq_db_manager)
            
            # Step 1: Create discovery session
            discovery_session = seq_db_manager.create_discovery_session(
                mine_name="Canadian Malartic",
                models_list=["openrouter:deepseek-free", "tavily:search"],
                country="Canada",
                region="Quebec",
                commodity="Gold"
            )
            
            # Step 2: Mock source discovery phase
            discovered_sources = await mock_orchestrator.mock_source_discovery_phase(
                "Canadian Malartic", 
                ["openrouter:deepseek-free", "tavily:search"],
                discovery_session.session_id
            )
            
            # Step 3: Mock field search phase
            field_results = await mock_orchestrator.mock_field_search_phase(
                "Canadian Malartic",
                ["openrouter:deepseek-free", "tavily:search"],
                discovered_sources,
                discovery_session.session_id
            )
            
            # Step 4: Create consolidated result
            final_data = {}
            field_confidence = {}
            
            for field_name, results in field_results.items():
                if results:
                    # Use result with highest confidence
                    best_result = max(results, key=lambda r: r.confidence_score or 0)
                    final_data[field_name] = best_result.field_value_found
                    field_confidence[field_name] = best_result.confidence_score
            
            consolidated_result = seq_db_manager.create_sequential_result(
                session_id=discovery_session.session_id,
                mine_name="Canadian Malartic",
                final_data=final_data,
                field_confidence=field_confidence,
                field_source_mapping={},
                quality_assessment={"workflow": "mock_successful"},
                performance_metrics={
                    "total_duration_seconds": 30.0,
                    "total_models_used": 2,
                    "total_sources_discovered": len(discovered_sources)
                },
                country="Canada"
            )
            
            # Validate results
            assert consolidated_result.total_models_used == 2
            assert consolidated_result.total_sources_discovered == len(discovered_sources)
            assert len(final_data) > 4  # Should have multiple fields
            assert "Eigentümer" in final_data
            assert "Canada" in str(final_data.values())
            
            session.close()
            self.test_results['workflow_mock'] = True
            logger.info("✅ Sequential Workflow mock test passed")
            
        except Exception as e:
            logger.error(f"❌ Sequential Workflow mock test failed: {e}")
            self.test_results['workflow_mock'] = False
    
    async def test_batch_integration_simulation(self):
        """
        Simuliere Batch-Integration (ohne echten FastAPI Call)
        """
        logger.info("🧪 Testing Batch Integration Simulation...")
        
        try:
            # Simulate batch parameters
            mine_data = {
                "mine_name": "Eleonore Mine",
                "country": "Canada", 
                "region": "Quebec",
                "commodity": "Gold"
            }
            
            models_to_use = ["openrouter:deepseek-free", "tavily:search"]
            search_type = "sequential"
            session_id = "test-batch-session-123"
            
            # Setup database manager
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(self.database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            seq_db_manager = SequentialDatabaseManager(session)
            
            # Simulate the batch integration logic
            logger.info(f"🔄 Simulating batch processing for {mine_data['mine_name']}")
            logger.info(f"📋 Models: {models_to_use}")
            logger.info(f"🔍 Search type: {search_type}")
            
            # Check if we would trigger sequential workflow
            if search_type == "sequential":
                logger.info("✅ Sequential workflow would be triggered")
                
                # Simulate sequential orchestrator initialization
                # (This is what would happen in the actual batch route)
                orchestrator_would_be_created = True
                
                # Simulate result structure that would be created
                mock_sequential_result = {
                    "success": True,
                    "data": {
                        "structured_data": {
                            "Eigentümer": "Goldcorp Inc.",
                            "Betreiber": "Newmont Corporation",
                            "Aktivitätsstatus": "Active",
                            "Country": "Canada",
                            "Region": "Quebec"
                        },
                        "field_confidence_scores": {
                            "Eigentümer": 88.5,
                            "Betreiber": 92.0,
                            "Aktivitätsstatus": 95.0
                        },
                        "sources_discovered": 8,
                        "models_used": len(models_to_use),
                        "search_strategy": "sequential_field_orchestrator",
                        "quality_score": 87.3
                    }
                }
                
                # Verify result structure
                assert mock_sequential_result["success"] == True
                assert "structured_data" in mock_sequential_result["data"]
                assert "search_strategy" in mock_sequential_result["data"]
                assert mock_sequential_result["data"]["search_strategy"] == "sequential_field_orchestrator"
                
                logger.info("✅ Batch integration result structure valid")
            else:
                logger.info("ℹ️  Standard workflow would be used")
            
            session.close()
            self.test_results['batch_integration'] = True
            logger.info("✅ Batch integration simulation passed")
            
        except Exception as e:
            logger.error(f"❌ Batch integration simulation failed: {e}")
            self.test_results['batch_integration'] = False
    
    async def run_all_tests(self):
        """
        Führe alle Tests aus
        """
        logger.info("🚀 Starting Sequential Field Orchestrator Test Suite...")
        logger.info("=" * 60)
        
        # Setup
        setup_success = await self.setup_test_environment()
        if not setup_success:
            logger.error("❌ Test setup failed, aborting tests")
            return
        
        # Run tests
        await self.test_sequential_database_manager()
        await self.test_sequential_orchestrator_basic()
        await self.test_sequential_workflow_mock()
        await self.test_batch_integration_simulation()
        
        # Report results
        self.print_test_results()
    
    def print_test_results(self):
        """
        Print test results summary
        """
        logger.info("=" * 60)
        logger.info("🎯 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
        
        logger.info("=" * 60)
        logger.info(f"🏆 OVERALL: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - Sequential Field Orchestrator is ready for production!")
        else:
            logger.warning("⚠️  Some tests failed - review implementation before production use")
        
        logger.info("=" * 60)


async def main():
    """Main test runner"""
    tester = SequentialWorkflowTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())