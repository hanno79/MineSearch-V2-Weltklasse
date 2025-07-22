"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Vollständiger Anthropic Model Test Runner - ALLE 45 Tests (3 models × 3 mines × 5 runs)
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from provider_test_framework import ProviderTestFramework, TestMine, TestResult
from model_benchmark_service import ModelBenchmarkService
from database import db_manager
from database.models import ModelStatistics

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/minesearch_v2/backend/anthropic_tests.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass 
class AnthropicTestResult:
    """Spezialisiertes Test-Ergebnis für Anthropic Models"""
    model_id: str
    mine_name: str
    run_number: int
    success: bool
    response_time_ms: float
    fields_found: int
    sources_count: int
    data_quality: float
    error: Optional[str] = None
    retry_count: int = 0
    timestamp: datetime = None


class AnthropicCompleteTestRunner:
    """
    Specialized Test Runner für VOLLSTÄNDIGE Anthropic Model Tests
    
    Führt ALLE 45 Tests durch:
    - 3 Anthropic Models (claude-sonnet-4, claude-opus-4, claude-3.7-sonnet)
    - 3 Quebec Mines (Éléonore, Niobec, LaRonde)  
    - 5 Runs pro Mine pro Model
    = 45 Total Tests
    """
    
    # ANTHROPIC MODELS zu testen
    ANTHROPIC_MODELS = [
        'anthropic:claude-sonnet-4',
        'anthropic:claude-opus-4', 
        'anthropic:claude-3.7-sonnet'
    ]
    
    # QUEBEC TEST MINES
    QUEBEC_MINES = [
        TestMine(
            name="Éléonore",
            country="Canada", 
            region="Quebec",
            commodity="Gold",
            expected_operator="Newmont",
            expected_status="Active"
        ),
        TestMine(
            name="Niobec", 
            country="Canada",
            region="Quebec", 
            commodity="Niobium",
            expected_operator="IAMGOLD",
            expected_status="Active"
        ),
        TestMine(
            name="LaRonde",
            country="Canada",
            region="Quebec",
            commodity="Gold", 
            expected_operator="Agnico Eagle",
            expected_status="Active"
        )
    ]
    
    def __init__(self):
        self.test_framework = ProviderTestFramework()
        self.benchmark_service = ModelBenchmarkService()
        self.start_time = None
        self.test_results = []
        self.failed_tests = []
        self.retry_attempts = 3
        
    async def run_complete_anthropic_tests(self) -> Dict[str, Any]:
        """
        Führt ALLE 45 Anthropic Tests durch mit vollständiger Abdeckung
        
        Returns:
            Comprehensive test results with database validation
        """
        self.start_time = datetime.now()
        total_tests = len(self.ANTHROPIC_MODELS) * len(self.QUEBEC_MINES) * 5  # 45 tests
        completed_tests = 0
        
        logger.info("🚀 ANTHROPIC COMPLETE TEST RUNNER STARTED")
        logger.info(f"📊 SCOPE: {len(self.ANTHROPIC_MODELS)} models × {len(self.QUEBEC_MINES)} mines × 5 runs = {total_tests} total tests")
        logger.info(f"🎯 TARGET: ALL {total_tests} tests must complete successfully and be stored in database")
        
        try:
            # 1. Pre-test validation
            await self._validate_anthropic_configuration()
            
            # 2. Execute systematic tests for ALL models
            for model_idx, model_id in enumerate(self.ANTHROPIC_MODELS):
                logger.info(f"\n🧠 TESTING MODEL {model_idx + 1}/{len(self.ANTHROPIC_MODELS)}: {model_id}")
                
                for mine_idx, mine in enumerate(self.QUEBEC_MINES):
                    logger.info(f"⛏️  Mine {mine_idx + 1}/{len(self.QUEBEC_MINES)}: {mine.name}")
                    
                    # Execute 5 runs for this model-mine combination
                    for run in range(1, 6):
                        test_start = time.time()
                        
                        try:
                            # Execute single test with retry logic
                            result = await self._execute_single_test_with_retry(
                                model_id, mine, run
                            )
                            
                            self.test_results.append(result)
                            completed_tests += 1
                            
                            # Progress reporting
                            progress = (completed_tests / total_tests) * 100
                            elapsed = time.time() - test_start
                            
                            status_icon = "✅" if result.success else "❌"
                            logger.info(f"{status_icon} Test {completed_tests}/{total_tests} ({progress:.1f}%) - "
                                      f"{model_id} {mine.name} Run {run} - "
                                      f"Success: {result.success}, Fields: {result.fields_found}, "
                                      f"Time: {elapsed:.1f}s")
                            
                            # Short pause to avoid rate limits
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            logger.error(f"💥 CRITICAL ERROR in test {completed_tests + 1}: {e}")
                            completed_tests += 1
                            self.failed_tests.append({
                                'model_id': model_id,
                                'mine_name': mine.name,
                                'run_number': run,
                                'error': str(e)
                            })
                
                # Pause between models
                logger.info(f"⏸️  Model {model_id} completed. Pausing 10s before next model...")
                await asyncio.sleep(10)
            
            # 3. Validate database completeness
            logger.info(f"\n🔍 VALIDATING DATABASE COMPLETENESS...")
            validation_results = await self._validate_database_completeness()
            
            # 4. Generate comprehensive report
            final_report = await self._generate_final_report(validation_results)
            
            # 5. Summary
            duration = (datetime.now() - self.start_time).total_seconds()
            successful_tests = len([r for r in self.test_results if r.success])
            
            logger.info(f"\n🏁 ANTHROPIC COMPLETE TEST RUNNER FINISHED")
            logger.info(f"⏱️  Duration: {duration:.1f}s")
            logger.info(f"✅ Success: {successful_tests}/{total_tests} tests")
            logger.info(f"📁 Database entries: {validation_results['database_entries']}")
            
            if successful_tests == total_tests and validation_results['database_entries'] == total_tests:
                logger.info("🎉 RESULT: ✅ 45/45 Anthropic tests completed, all in database")
            else:
                logger.warning(f"⚠️  PARTIAL SUCCESS: {successful_tests}/{total_tests} tests, {validation_results['database_entries']} DB entries")
            
            return final_report
            
        except Exception as e:
            logger.error(f"💥 CRITICAL FAILURE in Anthropic Test Runner: {e}")
            return {
                'success': False,
                'error': str(e),
                'completed_tests': completed_tests,
                'partial_results': self.test_results
            }
    
    async def _validate_anthropic_configuration(self):
        """Validiert dass alle Anthropic Models konfiguriert sind"""
        logger.info("🔧 Validating Anthropic configuration...")
        
        from config.providers import PROVIDERS_CONFIG
        
        anthropic_config = PROVIDERS_CONFIG.get('anthropic', {})
        if not anthropic_config.get('enabled', False):
            raise ValueError("Anthropic provider not enabled in configuration")
        
        if not anthropic_config.get('api_key'):
            raise ValueError("Anthropic API key not configured")
        
        logger.info("✅ Anthropic configuration validated")
    
    async def _execute_single_test_with_retry(self, model_id: str, mine: TestMine, 
                                            run_number: int) -> AnthropicTestResult:
        """
        Führt einen einzelnen Test mit Retry-Logic durch
        
        Args:
            model_id: Anthropic model ID (e.g., 'anthropic:claude-sonnet-4')
            mine: Test mine configuration
            run_number: Run number (1-5)
            
        Returns:
            AnthropicTestResult with detailed information
        """
        last_error = None
        
        for retry in range(self.retry_attempts):
            try:
                if retry > 0:
                    wait_time = 5 * retry  # Exponential backoff
                    logger.info(f"🔄 Retry {retry}/{self.retry_attempts - 1} for {model_id} {mine.name} Run {run_number} (waiting {wait_time}s)")
                    await asyncio.sleep(wait_time)
                
                # Use existing test framework
                result = await self.test_framework._test_single_run(model_id, mine, run_number)
                
                # Convert to AnthropicTestResult
                anthropic_result = AnthropicTestResult(
                    model_id=result.model_id,
                    mine_name=result.mine_name,
                    run_number=result.run_number,
                    success=result.success,
                    response_time_ms=result.response_time_ms,
                    fields_found=result.fields_found,
                    sources_count=result.sources_count,
                    data_quality=result.data_quality,
                    error=result.error,
                    retry_count=retry,
                    timestamp=result.timestamp
                )
                
                if result.success:
                    return anthropic_result
                else:
                    last_error = result.error
                    logger.warning(f"⚠️  Test failed (attempt {retry + 1}): {result.error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Test attempt {retry + 1} failed: {e}")
        
        # All retries failed
        return AnthropicTestResult(
            model_id=model_id,
            mine_name=mine.name,
            run_number=run_number,
            success=False,
            response_time_ms=0.0,
            fields_found=0,
            sources_count=0,
            data_quality=0.0,
            error=f"Failed after {self.retry_attempts} attempts: {last_error}",
            retry_count=self.retry_attempts,
            timestamp=datetime.now()
        )
    
    async def _validate_database_completeness(self) -> Dict[str, Any]:
        """
        Validiert dass ALLE 45 Anthropic Tests in der Database gespeichert sind
        
        Returns:
            Dictionary mit Validierungs-Ergebnissen
        """
        validation_results = {
            'total_expected': 45,
            'database_entries': 0,
            'missing_entries': [],
            'success': False
        }
        
        try:
            with db_manager.get_session() as session:
                # Count all Anthropic entries
                total_anthropic_entries = session.query(ModelStatistics).filter(
                    ModelStatistics.model_id.like('anthropic:%')
                ).count()
                
                validation_results['database_entries'] = total_anthropic_entries
                
                # Check specific model-mine-run combinations
                for model_id in self.ANTHROPIC_MODELS:
                    for mine in self.QUEBEC_MINES:
                        for run in range(1, 6):
                            entry = session.query(ModelStatistics).filter_by(
                                model_id=model_id,
                                mine_name=mine.name,
                                run_number=run
                            ).first()
                            
                            if not entry:
                                validation_results['missing_entries'].append(
                                    f"{model_id} - {mine.name} - Run {run}"
                                )
                
                # Determine success
                validation_results['success'] = (
                    total_anthropic_entries >= 45 and 
                    len(validation_results['missing_entries']) == 0
                )
                
                logger.info(f"📊 Database validation: {total_anthropic_entries}/45 entries found")
                if validation_results['missing_entries']:
                    logger.warning(f"❌ Missing entries: {len(validation_results['missing_entries'])}")
                    for missing in validation_results['missing_entries'][:5]:  # Show first 5
                        logger.warning(f"   Missing: {missing}")
                
        except Exception as e:
            logger.error(f"💥 Database validation failed: {e}")
            validation_results['error'] = str(e)
        
        return validation_results
    
    async def _generate_final_report(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert finalen Comprehensive Report"""
        
        # Calculate statistics
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.success])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Model performance breakdown
        model_performance = {}
        for model_id in self.ANTHROPIC_MODELS:
            model_results = [r for r in self.test_results if r.model_id == model_id]
            model_successful = [r for r in model_results if r.success]
            
            model_performance[model_id] = {
                'total_tests': len(model_results),
                'successful_tests': len(model_successful),
                'success_rate': len(model_successful) / len(model_results) if model_results else 0,
                'avg_fields_found': sum(r.fields_found for r in model_successful) / len(model_successful) if model_successful else 0,
                'avg_response_time': sum(r.response_time_ms for r in model_successful) / len(model_successful) if model_successful else 0,
                'avg_data_quality': sum(r.data_quality for r in model_successful) / len(model_successful) if model_successful else 0
            }
        
        # Mine performance breakdown  
        mine_performance = {}
        for mine in self.QUEBEC_MINES:
            mine_results = [r for r in self.test_results if r.mine_name == mine.name]
            mine_successful = [r for r in mine_results if r.success]
            
            mine_performance[mine.name] = {
                'total_tests': len(mine_results),
                'successful_tests': len(mine_successful),
                'success_rate': len(mine_successful) / len(mine_results) if mine_results else 0,
                'avg_fields_found': sum(r.fields_found for r in mine_successful) / len(mine_successful) if mine_successful else 0
            }
        
        # Generate comprehensive report
        report = {
            'test_type': 'ANTHROPIC_COMPLETE_45_TESTS',
            'success': validation_results.get('success', False),
            'execution_summary': {
                'total_tests_executed': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate,
                'total_duration_seconds': (datetime.now() - self.start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            },
            'model_performance': model_performance,
            'mine_performance': mine_performance,
            'database_validation': validation_results,
            'failed_tests': self.failed_tests,
            'recommendations': self._generate_recommendations(model_performance, validation_results),
            'final_status': "✅ 45/45 Anthropic tests completed, all in database" if validation_results.get('success') else f"⚠️ Partial completion: {successful_tests}/{total_tests} tests"
        }
        
        return report
    
    def _generate_recommendations(self, model_performance: Dict, validation_results: Dict) -> List[str]:
        """Generiert Empfehlungen basierend auf Test-Ergebnissen"""
        recommendations = []
        
        # Model ranking
        best_model = max(model_performance.items(), 
                        key=lambda x: (x[1]['success_rate'], x[1]['avg_fields_found']))
        recommendations.append(f"🏆 Best Anthropic Model: {best_model[0]} ({best_model[1]['success_rate']:.1%} success, {best_model[1]['avg_fields_found']:.1f} avg fields)")
        
        # Performance warnings
        poor_models = [model for model, perf in model_performance.items() if perf['success_rate'] < 0.8]
        if poor_models:
            recommendations.append(f"⚠️ Models with <80% success rate: {', '.join(poor_models)}")
        
        # Database issues
        if not validation_results.get('success'):
            recommendations.append(f"🔧 Database completeness issue: {validation_results.get('database_entries', 0)}/45 entries found")
        
        # General status
        if validation_results.get('success'):
            recommendations.append("✅ All Anthropic models ready for production use")
        else:
            recommendations.append("❌ Further testing required before production deployment")
        
        return recommendations


async def main():
    """Main execution function"""
    logger.info("🚀 Starting Anthropic Complete Test Runner...")
    
    runner = AnthropicCompleteTestRunner()
    
    try:
        results = await runner.run_complete_anthropic_tests()
        
        logger.info("\n" + "="*80)
        logger.info("FINAL RESULTS:")
        logger.info(f"Success: {results.get('success', False)}")
        logger.info(f"Status: {results.get('final_status', 'Unknown')}")
        logger.info("="*80)
        
        return results
        
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())