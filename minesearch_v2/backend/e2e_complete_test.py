#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Vollständiger End-to-End Test für MineSearch System
"""

import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MineSearchE2ETest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_url = "http://localhost:8000"
        self.test_csv_path = "/app/test_mines.csv"
        self.results = {
            'server_start': False,
            'api_health': False,
            'csv_upload': False,
            'model_selection': False,
            'batch_search': False,
            'search_completion': False,
            'results_validation': False,
            'performance_metrics': {},
            'errors': []
        }
        self.start_time = datetime.now()
        
    def log_step(self, step_name: str, status: bool, details: str = ""):
        """Log test step with status"""
        status_icon = "✅" if status else "❌"
        logger.info(f"{status_icon} {step_name}: {details}")
        
    def wait_with_progress(self, duration: int, description: str = "Waiting"):
        """Wait with progress indication"""
        logger.info(f"⏳ {description} for {duration} seconds...")
        for i in range(duration):
            time.sleep(1)
            if i % 10 == 9:  # Progress every 10 seconds
                logger.info(f"   ... {i+1}/{duration} seconds elapsed")
    
    def check_server_health(self) -> bool:
        """Check if backend server is running"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_step("Backend Server Health", True, "Server responding")
                self.results['server_start'] = True
                return True
        except requests.exceptions.RequestException as e:
            self.log_step("Backend Server Health", False, f"Server not responding: {str(e)}")
            self.results['errors'].append(f"Server health check failed: {str(e)}")
            
        return False
    
    def check_api_endpoints(self) -> bool:
        """Check critical API endpoints"""
        endpoints = [
            ("/api/models", "Models endpoint"),
            ("/api/sources", "Sources endpoint"),
        ]
        
        working_endpoints = 0
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_step(f"API - {description}", True, f"Status: {response.status_code}")
                    working_endpoints += 1
                else:
                    self.log_step(f"API - {description}", False, f"Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_step(f"API - {description}", False, f"Error: {str(e)}")
                self.results['errors'].append(f"API endpoint {endpoint} failed: {str(e)}")
        
        self.results['api_health'] = working_endpoints >= 1
        return self.results['api_health']
    
    def test_csv_upload(self) -> Tuple[bool, Optional[str]]:
        """Test CSV file upload and return success status and session_id"""
        try:
            if not os.path.exists(self.test_csv_path):
                self.log_step("CSV Upload", False, f"Test CSV file not found: {self.test_csv_path}")
                return False, None
            
            # Read CSV content
            with open(self.test_csv_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            self.log_step("CSV Upload", True, f"CSV file loaded ({len(csv_content)} bytes)")
            
            # Try upload via API
            files = {'csv_file': ('test_mines.csv', csv_content, 'text/csv')}
            response = requests.post(f"{self.api_url}/api/upload-csv", files=files, timeout=30)
            
            if response.status_code == 200:
                # Check if response is HTML (HTMX response)
                content_type = response.headers.get('content-type', '').lower()
                if 'html' in content_type:
                    # Extract session_id from HTML content
                    import re
                    html_content = response.text
                    session_match = re.search(r'name="session_id" value="([^"]+)"', html_content)
                    session_id = session_match.group(1) if session_match else "extracted_session"
                    mines_match = re.search(r'<strong>(\d+)</strong> Minen gefunden', html_content)
                    mines_count = mines_match.group(1) if mines_match else "0"
                    
                    self.log_step("CSV Upload API", True, f"Upload successful, session: {session_id}, mines: {mines_count}")
                    self.results['csv_upload'] = True
                    return True, session_id
                else:
                    # Try JSON response
                    try:
                        result = response.json()
                        session_id = result.get('session_id') or result.get('id') or "test_session"
                        self.log_step("CSV Upload API", True, f"Upload successful, session: {session_id}")
                        self.results['csv_upload'] = True
                        return True, session_id
                    except:
                        self.log_step("CSV Upload API", True, "Upload successful but could not extract session")
                        self.results['csv_upload'] = True
                        return True, "default_session"
            else:
                self.log_step("CSV Upload API", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_step("CSV Upload", False, f"Error: {str(e)}")
            self.results['errors'].append(f"CSV upload failed: {str(e)}")
            
        return False, None
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.api_url}/api/models", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'models' in data:
                    models_dict = data['models']
                    # Convert dict to list with model keys
                    models_list = [{'name': key, **value} for key, value in models_dict.items()]
                    free_models = [m for m in models_list if m.get('is_free') == True]
                    
                    self.log_step("Model Discovery", True, f"Found {len(models_list)} total models, {len(free_models)} free")
                    return free_models[:3]  # Return first 3 free models
                
        except Exception as e:
            self.log_step("Model Discovery", False, f"Error: {str(e)}")
            
        # Fallback models
        return [
            {'name': 'openrouter:deepseek-free', 'provider': 'openrouter'},
            {'name': 'openrouter:claude-haiku', 'provider': 'openrouter'}
        ]
    
    def start_batch_search(self, models: List[Dict], session_id: str = "test_session") -> Optional[str]:
        """Start batch search with selected models"""
        try:
            # Use form data instead of JSON as per API
            search_data = {
                'session_id': session_id,
                'selected_models': ','.join([m['name'] for m in models])
            }
            
            self.log_step("Batch Search Start", True, f"Starting with {len(models)} models")
            
            response = requests.post(f"{self.api_url}/api/batch-search", data=search_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                search_id = result.get('search_id')
                self.log_step("Batch Search Initiated", True, f"Search ID: {search_id}")
                self.results['batch_search'] = True
                return search_id
            else:
                self.log_step("Batch Search Initiated", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_step("Batch Search Start", False, f"Error: {str(e)}")
            self.results['errors'].append(f"Batch search failed: {str(e)}")
            
        return None
    
    def wait_for_search_completion(self, search_id: str, max_wait: int = 120) -> bool:
        """Wait for search to complete"""
        if not search_id:
            return False
            
        logger.info(f"⏳ Waiting for search completion (max {max_wait} seconds)")
        
        start_wait = time.time()
        check_interval = 10
        
        while time.time() - start_wait < max_wait:
            try:
                response = requests.get(f"{self.api_url}/api/search_status/{search_id}", timeout=10)
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status', 'unknown')
                    progress = status_data.get('progress', 0)
                    
                    elapsed = int(time.time() - start_wait)
                    logger.info(f"   Search status: {status}, Progress: {progress}% ({elapsed}s elapsed)")
                    
                    if status in ['completed', 'finished']:
                        self.log_step("Search Completion", True, f"Completed in {elapsed} seconds")
                        self.results['search_completion'] = True
                        return True
                    elif status in ['failed', 'error']:
                        self.log_step("Search Completion", False, f"Search failed: {status}")
                        return False
                        
            except Exception as e:
                logger.warning(f"   Status check failed: {str(e)}")
                
            time.sleep(check_interval)
        
        self.log_step("Search Completion", False, "Timeout reached")
        return False
    
    def validate_results(self, search_id: str) -> bool:
        """Validate search results"""
        try:
            # Get results summary
            response = requests.get(f"{self.api_url}/api/results/{search_id}", timeout=15)
            
            if response.status_code == 200:
                results = response.json()
                
                total_results = results.get('total_results', 0)
                successful_searches = results.get('successful_searches', 0)
                failed_searches = results.get('failed_searches', 0)
                
                self.log_step("Results Validation", True, 
                             f"Total: {total_results}, Success: {successful_searches}, Failed: {failed_searches}")
                
                # Performance metrics
                self.results['performance_metrics'] = {
                    'total_results': total_results,
                    'successful_searches': successful_searches,
                    'failed_searches': failed_searches,
                    'success_rate': successful_searches / max(successful_searches + failed_searches, 1)
                }
                
                self.results['results_validation'] = total_results > 0
                return self.results['results_validation']
                
        except Exception as e:
            self.log_step("Results Validation", False, f"Error: {str(e)}")
            self.results['errors'].append(f"Results validation failed: {str(e)}")
            
        return False
    
    def test_additional_endpoints(self) -> Dict[str, bool]:
        """Test additional system endpoints"""
        endpoints_status = {}
        
        additional_endpoints = [
            ("/api/statistics", "Statistics"),
            ("/api/sources", "Sources"),
            ("/api/export", "Export")
        ]
        
        for endpoint, name in additional_endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                status = response.status_code == 200
                endpoints_status[name] = status
                self.log_step(f"Endpoint - {name}", status, f"Status: {response.status_code}")
                
            except Exception as e:
                endpoints_status[name] = False
                self.log_step(f"Endpoint - {name}", False, f"Error: {str(e)}")
        
        return endpoints_status
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate success metrics
        total_tests = len([k for k in self.results.keys() if k not in ['performance_metrics', 'errors']])
        passed_tests = sum(1 for k, v in self.results.items() if k not in ['performance_metrics', 'errors'] and v is True)
        
        report = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'overall_status': 'PASS' if passed_tests >= total_tests * 0.7 else 'FAIL'  # 70% threshold
            },
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not self.results.get('server_start'):
            recommendations.append("Ensure backend server is running on port 8001")
            
        if not self.results.get('csv_upload'):
            recommendations.append("Check CSV upload functionality and file permissions")
            
        if not self.results.get('batch_search'):
            recommendations.append("Verify model selection and search initialization")
            
        if not self.results.get('search_completion'):
            recommendations.append("Investigate search timeout issues and provider availability")
            
        if not self.results.get('results_validation'):
            recommendations.append("Check result processing and data formatting")
            
        if len(self.results.get('errors', [])) > 2:
            recommendations.append("Multiple errors detected - perform comprehensive system check")
            
        # Performance recommendations
        success_rate = self.results.get('performance_metrics', {}).get('success_rate', 0)
        if success_rate < 0.5:
            recommendations.append("Low success rate - check provider configurations and API keys")
            
        return recommendations
    
    def run_complete_test(self) -> Dict:
        """Execute complete end-to-end test suite"""
        logger.info("🚀 Starting Complete MineSearch E2E Test")
        logger.info("=" * 60)
        
        try:
            # Step 1: Server Health
            if not self.check_server_health():
                logger.error("❌ Server health check failed - cannot proceed")
                return self.generate_report()
            
            # Step 2: API Endpoints
            self.check_api_endpoints()
            
            # Step 3: CSV Upload
            csv_success, session_id = self.test_csv_upload()
            
            # Step 4: Model Discovery
            available_models = self.get_available_models()
            if available_models:
                self.results['model_selection'] = True
                self.log_step("Model Selection", True, f"Selected {len(available_models)} models")
            
            # Step 5: Batch Search
            if csv_success and session_id:
                search_id = self.start_batch_search(available_models, session_id)
            else:
                search_id = self.start_batch_search(available_models)  # Use default session
            
            # Step 6: Wait for Completion
            if search_id:
                self.wait_for_search_completion(search_id)
                
                # Step 7: Validate Results
                self.validate_results(search_id)
            
            # Step 8: Additional Endpoints
            additional_status = self.test_additional_endpoints()
            
            # Generate final report
            report = self.generate_report()
            
            # Save report
            report_path = f"/app/minesearch_v2/backend/e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"💾 Test report saved to: {report_path}")
            
            # Print summary
            self._print_summary(report)
            
            return report
            
        except Exception as e:
            logger.error(f"💥 Test execution failed: {str(e)}")
            self.results['errors'].append(f"Test execution error: {str(e)}")
            return self.generate_report()
    
    def _print_summary(self, report: Dict):
        """Print test summary to console"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 FINAL TEST SUMMARY")
        logger.info("=" * 60)
        
        summary = report['test_summary']
        logger.info(f"📊 Overall Status: {summary['overall_status']}")
        logger.info(f"⏱️  Duration: {report['duration_seconds']:.1f} seconds")
        logger.info(f"✅ Passed: {summary['passed_tests']}/{summary['total_tests']}")
        logger.info(f"❌ Failed: {summary['failed_tests']}/{summary['total_tests']}")
        logger.info(f"📈 Success Rate: {summary['success_rate']:.1%}")
        
        if report.get('recommendations'):
            logger.info("\n🔧 RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'], 1):
                logger.info(f"   {i}. {rec}")
        
        if self.results.get('errors'):
            logger.info(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'], 1):
                logger.info(f"   {i}. {error}")
        
        perf = self.results.get('performance_metrics', {})
        if perf:
            logger.info("\n📈 PERFORMANCE METRICS:")
            logger.info(f"   Total Results: {perf.get('total_results', 0)}")
            logger.info(f"   Successful Searches: {perf.get('successful_searches', 0)}")
            logger.info(f"   Failed Searches: {perf.get('failed_searches', 0)}")
            logger.info(f"   Search Success Rate: {perf.get('success_rate', 0):.1%}")


def main():
    """Main execution function"""
    test = MineSearchE2ETest()
    report = test.run_complete_test()
    
    # Exit with appropriate code
    exit_code = 0 if report['test_summary']['overall_status'] == 'PASS' else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()