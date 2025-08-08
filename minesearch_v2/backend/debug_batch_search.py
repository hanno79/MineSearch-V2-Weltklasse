#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Debug batch search to find why results are empty
"""

import requests
import json
import time
import re
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchSearchDebugger:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def debug_batch_search_process(self):
        """Debug the complete batch search process step by step"""
        print("🔍 DEBUG: Starting detailed batch search analysis")
        print("=" * 60)
        
        # Step 1: Upload CSV and get session
        print("\n1️⃣ DEBUGGING CSV Upload...")
        csv_content = "Name,Country,Commodity\nGrasberg,Indonesia,Copper"
        files = {'csv_file': ('test_mines.csv', csv_content, 'text/csv')}
        
        upload_response = self.session.post(f"{self.base_url}/api/batch/upload-csv", files=files)
        print(f"✅ Upload Status: {upload_response.status_code}")
        
        # Extract session_id
        session_match = re.search(r'name="session_id" value="([^"]+)"', upload_response.text)
        if not session_match:
            print("❌ CRITICAL: No session_id found!")
            return False
            
        session_id = session_match.group(1)
        print(f"✅ Session ID: {session_id}")
        
        # Step 2: Check what models are available
        print("\n2️⃣ DEBUGGING Model Selection...")
        models_response = self.session.get(f"{self.base_url}/api/models")
        models_data = models_response.json()
        available_models = models_data.get('models', [])
        
        print(f"✅ Available models: {len(available_models)}")
        perplexity_models = [m for m in available_models if 'perplexity' in m]
        print(f"✅ Perplexity models: {perplexity_models}")
        
        # Step 3: Execute batch search with maximum debug info
        print("\n3️⃣ DEBUGGING Batch Search Execution...")
        
        selected_model = 'perplexity:sonar'
        batch_data = {
            'session_id': session_id,
            'selected_models': selected_model,
            'search_type': 'standard',
            'count': '1',
            'search_all': 'false'
        }
        
        print(f"📤 Request data: {batch_data}")
        
        # Make the request with timing
        start_time = time.time()
        batch_response = self.session.post(
            f"{self.base_url}/api/batch-search",
            data=batch_data,
            timeout=180
        )
        duration = time.time() - start_time
        
        print(f"📥 Response Status: {batch_response.status_code}")
        print(f"📥 Duration: {duration:.2f} seconds")
        print(f"📥 Content-Type: {batch_response.headers.get('content-type')}")
        print(f"📥 Content-Length: {len(batch_response.text)}")
        
        # Step 4: Analyze response content in detail
        print("\n4️⃣ DEBUGGING Response Content...")
        content = batch_response.text
        
        # Check for error patterns
        error_indicators = ['error', 'exception', 'failed', 'timeout', '404', 'not found']
        found_errors = []
        for indicator in error_indicators:
            if indicator.lower() in content.lower():
                found_errors.append(indicator)
                
        if found_errors:
            print(f"❌ ERROR INDICATORS: {found_errors}")
        else:
            print("✅ No error indicators found")
        
        # Check table structure
        if '<table' in content:
            print("✅ HTML table found")
            
            # Count table rows
            tbody_content = re.search(r'<tbody>(.*?)</tbody>', content, re.DOTALL)
            if tbody_content:
                tbody_text = tbody_content.group(1).strip()
                if tbody_text:
                    row_count = len(re.findall(r'<tr', tbody_text))
                    print(f"✅ Table rows: {row_count}")
                else:
                    print("❌ EMPTY TBODY: No data rows found!")
            else:
                print("❌ No tbody found in table")
        else:
            print("❌ No HTML table found")
        
        # Step 5: Test individual search to compare
        print("\n5️⃣ DEBUGGING Individual Search for Comparison...")
        try:
            # Make a direct search request
            search_data = {
                'mine_name': 'Grasberg',
                'country': 'Indonesia',
                'commodity': 'Copper',
                'model': selected_model
            }
            
            search_response = self.session.post(
                f"{self.base_url}/api/search",
                data=search_data,
                timeout=60
            )
            
            print(f"🔍 Individual search status: {search_response.status_code}")
            if search_response.status_code == 200:
                search_content = search_response.text
                if 'structured_data' in search_content or len(search_content) > 1000:
                    print("✅ Individual search returned data")
                else:
                    print("❌ Individual search returned minimal data")
            else:
                print(f"❌ Individual search failed: {search_response.status_code}")
                
        except Exception as e:
            print(f"❌ Individual search error: {e}")
        
        # Step 6: Save detailed response for analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response_file = f"/app/minesearch_v2/backend/debug_batch_response_{timestamp}.html"
        
        with open(response_file, 'w') as f:
            f.write(content)
        print(f"💾 Detailed response saved to: {response_file}")
        
        # Step 7: Summary
        print("\n📊 DEBUG SUMMARY:")
        print("=" * 40)
        if batch_response.status_code == 200:
            if '<tbody></tbody>' in content or re.search(r'<tbody>\s*</tbody>', content):
                print("⚠️  ISSUE IDENTIFIED: Batch search runs successfully but returns empty results")
                print("🔍 POSSIBLE CAUSES:")
                print("   1. Batch coordination logic issue")
                print("   2. Model execution failing silently")
                print("   3. Data extraction/processing error")
                print("   4. Database save/retrieve issue")
            else:
                print("✅ Batch search appears to work correctly")
        else:
            print(f"❌ Batch search HTTP error: {batch_response.status_code}")
        
        return batch_response.status_code == 200

if __name__ == "__main__":
    debugger = BatchSearchDebugger()
    success = debugger.debug_batch_search_process()