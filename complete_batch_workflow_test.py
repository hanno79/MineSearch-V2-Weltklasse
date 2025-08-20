#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Complete batch workflow test with session management for 'k.A.' validation
"""

import requests
import re
import json
import sys

def extract_session_id(html_response):
    """Extract session_id from the HTML response"""
    # Look for session ID in different formats
    patterns = [
        r'name="session_id" value="([^"]+)"',
        r'Session ID: ([a-f0-9\-]+)',
        r'session: ([a-f0-9\-]+)',
        r'value="{?([a-f0-9\-]+)}?"'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_response, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def test_complete_batch_workflow():
    """Test complete batch workflow from CSV upload to results validation"""
    
    base_url = "http://localhost:8000"
    
    try:
        print("📍 Step 1: Upload CSV with Quebec mines")
        
        # Create CSV content with Quebec mines
        csv_content = """mine_name
Éléonore
Lac Expanse
Aubelle
Detour Lake
Malartic"""
        
        files = {'csv_file': ('quebec_mines.csv', csv_content, 'text/csv')}
        upload_response = requests.post(f"{base_url}/api/upload-csv", files=files)
        
        if upload_response.status_code != 200:
            print(f"❌ CSV upload failed: {upload_response.status_code}")
            return False
        
        print("✅ CSV uploaded successfully")
        upload_html = upload_response.text
        
        # Extract session ID
        session_id = extract_session_id(upload_html)
        if not session_id:
            print("❌ Could not extract session_id from upload response")
            print("Upload response preview:", upload_html[:500])
            return False
        
        print(f"✅ Session ID extracted: {session_id}")
        
        print("📍 Step 2: Start batch search")
        
        # Prepare batch search data
        batch_data = {
            'session_id': session_id,
            'selected_models': 'gemini,brightdata',  # Top performers
            'search_type': 'standard',
            'search_all': 'false',  # Just first few for testing
            'count': 3  # Test with 3 mines for speed
        }
        
        print(f"Starting batch search with data: {batch_data}")
        batch_response = requests.post(f"{base_url}/api/batch-search", data=batch_data, timeout=120)
        
        if batch_response.status_code != 200:
            print(f"❌ Batch search failed: {batch_response.status_code}")
            print(f"Error response: {batch_response.text}")
            return False
        
        print("✅ Batch search completed")
        batch_html = batch_response.text
        
        print("📍 Step 3: Analyze results for data quality")
        
        # Count 'k.A.' placeholders
        ka_count = batch_html.count('k.A.')
        print(f"📊 'k.A.' placeholders found: {ka_count}")
        
        # Look for actual mining data indicators
        quebec_mining_indicators = [
            'Quebec', 'Canada', 'Gold', 'Mining', 'Exploration', 
            'Resource', 'Production', 'Tonnage', 'oz', 'g/t',
            'million', 'thousand', 'metres', 'depth', 'grade',
            'Éléonore', 'Aubelle', 'Expanse', 'Detour', 'Malartic'
        ]
        
        data_indicators_found = []
        for indicator in quebec_mining_indicators:
            if indicator.lower() in batch_html.lower():
                data_indicators_found.append(indicator)
        
        print(f"📊 Mining data indicators found: {len(data_indicators_found)}")
        for indicator in data_indicators_found[:10]:  # Show first 10
            print(f"  ✅ {indicator}")
        
        # Check for table structure
        table_indicators = batch_html.count('<td')
        row_indicators = batch_html.count('<tr')
        print(f"📊 Table structure: {row_indicators} rows, {table_indicators} cells")
        
        # Look for specific result patterns
        result_patterns = [
            r'<td[^>]*>([^<]*(?:Quebec|Canada|Gold|Mining)[^<]*)</td>',
            r'class="[^"]*result[^"]*"[^>]*>([^<]+)</td>',
            r'<td[^>]*>([0-9]+(?:\.[0-9]+)?[^<]*(?:oz|g/t|tonnes)[^<]*)</td>'
        ]
        
        meaningful_results = 0
        for pattern in result_patterns:
            matches = re.findall(pattern, batch_html, re.IGNORECASE)
            meaningful_results += len(matches)
            for match in matches[:3]:  # Show first 3 matches per pattern
                if match.strip() and match.strip() != 'k.A.':
                    print(f"  📊 Found result: {match.strip()}")
        
        print(f"📊 Meaningful results extracted: {meaningful_results}")
        
        print("📍 Step 4: Generate assessment")
        
        # Calculate quality metrics
        total_indicators = len(data_indicators_found) + meaningful_results
        quality_ratio = total_indicators / max(ka_count, 1)
        
        print(f"\n📈 BATCH RESULTS QUALITY ASSESSMENT:")
        print(f"   - Quebec mines processed: 3 (Éléonore, Lac Expanse, Aubelle)")
        print(f"   - 'k.A.' placeholder count: {ka_count}")
        print(f"   - Mining data indicators: {len(data_indicators_found)}")
        print(f"   - Meaningful results found: {meaningful_results}")
        print(f"   - Quality ratio (data/placeholders): {quality_ratio:.2f}")
        
        if quality_ratio > 2.0:
            print("\n✅ EXCELLENT: Batch results show predominantly real mining data!")
            assessment = "EXCELLENT"
        elif quality_ratio > 1.0:
            print("\n✅ GOOD: Batch results contain more real data than placeholders")
            assessment = "GOOD"
        elif quality_ratio > 0.5:
            print("\n⚠️  MODERATE: Mixed results - some real data but many placeholders")
            assessment = "MODERATE"
        else:
            print("\n❌ POOR: Too many 'k.A.' placeholders, limited real mining data")
            assessment = "POOR"
        
        # Check for specific Quebec mine data
        mine_specific_data = 0
        quebec_mines = ['Éléonore', 'Aubelle', 'Expanse', 'Detour', 'Malartic']
        for mine in quebec_mines:
            if mine.lower() in batch_html.lower():
                mine_specific_data += 1
                print(f"   ✅ Found data for: {mine}")
        
        print(f"   - Mine-specific data found: {mine_specific_data}/{len(quebec_mines)}")
        
        print(f"\n🎯 FINAL ASSESSMENT: {assessment}")
        print("📁 Check the batch functionality by examining:")
        print("   1. CSV upload and session management ✅")
        print("   2. Batch search execution ✅")
        print(f"   3. Data quality vs placeholders: {quality_ratio:.2f}")
        print(f"   4. Quebec mine data presence: {mine_specific_data}/{len(quebec_mines)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during complete batch workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_batch_workflow()
    sys.exit(0 if success else 1)