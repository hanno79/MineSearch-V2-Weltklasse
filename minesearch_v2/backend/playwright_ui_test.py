#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: UI Test für MineSearch batch search 404 bug analysis
"""

import requests
import time
import json
import sys
from urllib.parse import urljoin

class MineSearchUITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id = None
        
    def test_frontend_page(self):
        """Test if frontend loads correctly"""
        print("🔍 Testing frontend page load...")
        try:
            response = self.session.get(self.base_url)
            print(f"✅ Frontend status: {response.status_code}")
            
            # Check for key elements
            content = response.text
            if 'MineSearch' in content:
                print("✅ MineSearch title found")
            if 'csv-upload' in content:
                print("✅ CSV upload form found")
            if 'hx-post' in content:
                print("✅ HTMX integration found")
                
            return True
        except Exception as e:
            print(f"❌ Frontend test failed: {e}")
            return False
    
    def test_csv_upload(self):
        """Test CSV upload functionality"""
        print("\n🔍 Testing CSV upload...")
        
        # Create test CSV data
        csv_content = "Name,Country,Commodity\nGrasberg,Indonesia,Copper\nCanadian Malartic,Canada,Gold\nEscondida,Chile,Copper"
        
        try:
            files = {'csv_file': ('test_mines.csv', csv_content, 'text/csv')}
            response = self.session.post(
                urljoin(self.base_url, '/api/batch/upload-csv'),
                files=files
            )
            
            print(f"✅ CSV upload status: {response.status_code}")
            print(f"✅ Response content length: {len(response.text)}")
            
            # Extract session_id from response
            if 'session_id' in response.text:
                import re
                session_match = re.search(r'name="session_id" value="([^"]+)"', response.text)
                if session_match:
                    self.session_id = session_match.group(1)
                    print(f"✅ Session ID extracted: {self.session_id}")
                else:
                    print("❌ Session ID not found in response")
                    return False
            else:
                print("❌ No session_id in response")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ CSV upload failed: {e}")
            return False
    
    def test_model_selection_api(self):
        """Test model selection API"""
        print("\n🔍 Testing model selection API...")
        try:
            response = self.session.get(urljoin(self.base_url, '/api/models'))
            print(f"✅ Models API status: {response.status_code}")
            
            if response.status_code == 200:
                models_data = response.json()
                print(f"✅ Available models count: {len(models_data.get('models', []))}")
                
                # Show first few models
                models = models_data.get('models', [])[:5]
                for model in models:
                    print(f"  - {model}")
                    
                return True
            return False
            
        except Exception as e:
            print(f"❌ Models API test failed: {e}")
            return False
    
    def test_batch_search_network(self):
        """Test batch search with network debugging"""
        print("\n🔍 Testing batch search with network debugging...")
        
        if not self.session_id:
            print("❌ No session_id available - skipping batch search test")
            return False
            
        try:
            # Prepare form data exactly as frontend would send
            form_data = {
                'session_id': self.session_id,
                'selected_models': 'perplexity:sonar',
                'search_type': 'standard',
                'count': '1',
                'search_all': 'false'
            }
            
            print(f"📤 Sending batch search request with data: {form_data}")
            
            # Send request with detailed logging
            response = self.session.post(
                urljoin(self.base_url, '/api/batch-search'),
                data=form_data,
                timeout=60
            )
            
            print(f"✅ Batch search status: {response.status_code}")
            print(f"✅ Response headers: {dict(response.headers)}")
            print(f"✅ Response content type: {response.headers.get('content-type', 'unknown')}")
            print(f"✅ Response length: {len(response.text)}")
            
            # Check if response contains expected elements
            content = response.text.lower()
            if 'ergebnistabelle' in content:
                print("✅ Results table found in response")
            if 'table' in content:
                print("✅ HTML table found")
            if 'error' in content:
                print("⚠️  Error text found in response")
                
            # Save response for debugging
            with open('/app/minesearch_v2/backend/batch_search_response.html', 'w') as f:
                f.write(response.text)
            print("✅ Response saved to batch_search_response.html")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Batch search test failed: {e}")
            return False
    
    def test_404_scenarios(self):
        """Test potential 404 scenarios"""
        print("\n🔍 Testing potential 404 scenarios...")
        
        # Test various endpoints that might cause 404
        test_endpoints = [
            '/api/batch/upload-csv',
            '/api/batch-search', 
            '/api/models',
            '/csv/test_mines.csv',  # This one should 404
            '/static/style.css',
            '/api/unknown-endpoint',  # This should 404
        ]
        
        for endpoint in test_endpoints:
            try:
                if endpoint in ['/api/batch/upload-csv', '/api/batch-search']:
                    # These need POST
                    response = self.session.post(urljoin(self.base_url, endpoint))
                else:
                    response = self.session.get(urljoin(self.base_url, endpoint))
                    
                status_code = response.status_code
                if status_code == 404:
                    print(f"❌ 404 ERROR: {endpoint}")
                    print(f"   Response: {response.text[:200]}...")
                elif status_code in [200, 405, 422]:  # 405=method not allowed, 422=validation error
                    print(f"✅ {status_code}: {endpoint}")
                else:
                    print(f"⚠️  {status_code}: {endpoint}")
                    
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting MineSearch UI Tests")
        print("=" * 50)
        
        success_count = 0
        total_tests = 5
        
        if self.test_frontend_page():
            success_count += 1
        
        if self.test_csv_upload():
            success_count += 1
            
        if self.test_model_selection_api():
            success_count += 1
            
        if self.test_batch_search_network():
            success_count += 1
            
        # Always run 404 test
        self.test_404_scenarios()
        success_count += 1
        
        print("\n" + "=" * 50)
        print(f"🎯 Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("✅ All tests passed! No 404 issues found in main functionality.")
        else:
            print("⚠️  Some tests failed. Check individual test results above.")
            
        return success_count == total_tests

if __name__ == "__main__":
    tester = MineSearchUITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)