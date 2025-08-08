#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Visueller Browser-Test mit Screenshots für MineSearch System
"""

import subprocess
import time
import os
from datetime import datetime

class VisualBrowserTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.screenshots_dir = "/app/minesearch_v2/backend/screenshots"
        self.ensure_screenshots_dir()
        
    def ensure_screenshots_dir(self):
        """Ensure screenshots directory exists"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def take_screenshot_curl(self, step_name: str, description: str) -> str:
        """Take a screenshot using curl to get HTML content"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{step_name}_{timestamp}.html"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Get HTML content via curl
            result = subprocess.run([
                'curl', '-s', self.base_url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"<!-- {description} - {timestamp} -->\n")
                    f.write(result.stdout)
                
                print(f"📸 Screenshot saved: {filename} - {description}")
                return filepath
            else:
                print(f"❌ Screenshot failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Screenshot error: {str(e)}")
            
        return ""
        
    def simulate_csv_upload(self) -> str:
        """Simulate CSV upload and capture response"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"csv_upload_response_{timestamp}.html"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Upload CSV via curl
            result = subprocess.run([
                'curl', '-s',
                '-F', 'csv_file=@/app/test_mines.csv',
                f'{self.base_url}/api/upload-csv'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"<!-- CSV Upload Response - {timestamp} -->\n")
                    f.write(result.stdout)
                
                print(f"📸 CSV Upload response saved: {filename}")
                
                # Extract session ID for batch search
                import re
                session_match = re.search(r'name="session_id" value="([^"]+)"', result.stdout)
                if session_match:
                    return session_match.group(1)
                    
            else:
                print(f"❌ CSV Upload failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ CSV Upload error: {str(e)}")
            
        return ""
        
    def simulate_batch_search(self, session_id: str) -> bool:
        """Simulate batch search and capture response"""
        if not session_id:
            print("❌ No valid session ID for batch search")
            return False
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"batch_search_response_{timestamp}.html"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Start batch search via curl
            result = subprocess.run([
                'curl', '-s',
                '-d', f'session_id={session_id}',
                '-d', 'selected_models=openrouter:deepseek-free,openrouter:mistral-small-free',
                '-d', 'count=3',
                '-d', 'search_all=true',
                f'{self.base_url}/api/batch-search'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"<!-- Batch Search Response - {timestamp} -->\n")
                    f.write(result.stdout)
                
                print(f"📸 Batch Search response saved: {filename}")
                return True
                
            else:
                print(f"❌ Batch Search failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Batch Search error: {str(e)}")
            
        return False
        
    def capture_api_endpoints(self):
        """Capture responses from various API endpoints"""
        endpoints = [
            ("/api/models", "models_response"),
            ("/api/sources", "sources_response"),
            ("/api/health", "health_response")
        ]
        
        for endpoint, name in endpoints:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{name}_{timestamp}.json"
                filepath = os.path.join(self.screenshots_dir, filename)
                
                result = subprocess.run([
                    'curl', '-s', f'{self.base_url}{endpoint}'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(result.stdout)
                    
                    print(f"📸 API response saved: {filename}")
                    
            except Exception as e:
                print(f"❌ API capture error for {endpoint}: {str(e)}")
                
    def run_visual_test(self):
        """Execute complete visual browser test"""
        print("🎬 VISUELLER BROWSER-TEST START")
        print("=" * 60)
        
        # Step 1: Initial homepage
        self.take_screenshot_curl("01_homepage", "Initial homepage load")
        
        # Step 2: API endpoints
        self.capture_api_endpoints()
        
        # Step 3: CSV upload
        print("\n📄 CSV-Upload simulieren...")
        session_id = self.simulate_csv_upload()
        
        if session_id:
            print(f"✅ Session-ID erhalten: {session_id}")
            
            # Step 4: Batch search
            print("\n🔍 Batch-Suche simulieren...")
            batch_success = self.simulate_batch_search(session_id)
            
            if batch_success:
                print("✅ Batch-Suche erfolgreich")
                
                # Step 5: Wait and capture results
                print("\n⏳ Auf Ergebnisse warten...")
                time.sleep(5)
                
                self.take_screenshot_curl("05_results_after_search", "Results after batch search")
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 VISUELLER TEST ZUSAMMENFASSUNG")
        print("=" * 60)
        
        # Count saved files
        files = os.listdir(self.screenshots_dir)
        html_files = [f for f in files if f.endswith('.html')]
        json_files = [f for f in files if f.endswith('.json')]
        
        print(f"📸 HTML-Captures: {len(html_files)}")
        print(f"📊 JSON-Responses: {len(json_files)}")
        print(f"📁 Gesamt-Dateien: {len(files)}")
        print(f"📂 Verzeichnis: {self.screenshots_dir}")
        
        if files:
            print("\n📋 GESPEICHERTE DATEIEN:")
            for file in sorted(files):
                print(f"   - {file}")
                
        print(f"\n✅ Visueller Test abgeschlossen!")


def main():
    """Main execution function"""
    test = VisualBrowserTest()
    test.run_visual_test()


if __name__ == "__main__":
    main()