"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Erweiterte E2E Tests um 400 Errors zu provozieren
"""

import asyncio
import json
import logging
from playwright.async_api import async_playwright
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorProvocationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_scenarios = []
        self.all_requests = []
        self.all_errors = []
        
    async def setup_browser(self, playwright):
        """Browser setup mit Network-Monitoring"""
        browser = await playwright.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # Network Listeners
        async def handle_request(request):
            request_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'post_data': request.post_data if request.method == 'POST' else None
            }
            self.all_requests.append(request_data)
            logger.info(f"REQUEST: {request.method} {request.url}")
            
        async def handle_response(response):
            if response.status >= 400:
                error_data = {
                    'timestamp': datetime.now().isoformat(),
                    'url': response.url,
                    'status': response.status,
                    'headers': dict(response.headers)
                }
                
                if '/api/' in response.url:
                    try:
                        error_data['body'] = await response.text()
                    except:
                        error_data['body'] = 'UNREADABLE'
                
                self.all_errors.append(error_data)
                logger.error(f"ERROR: {response.status} {response.url}")
                
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        return browser, context, page
    
    async def test_scenario_1_no_models_selected(self, page):
        """Szenario 1: Keine Modelle ausgewählt"""
        logger.info("=== SZENARIO 1: Keine Modelle ausgewählt ===")
        
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # CSV hochladen
            file_input = page.locator('input#csv_file')
            await file_input.set_input_files('/app/minesearch_v2/backend/test_csv.csv')
            
            upload_button = page.locator('button:has-text("CSV hochladen und weiter")')
            await upload_button.click()
            await page.wait_for_timeout(3000)
            
            # ALLE Modelle deaktivieren
            checkboxes = page.locator('input[type="checkbox"]')
            count = await checkboxes.count()
            
            for i in range(count):
                checkbox = checkboxes.nth(i)
                if await checkbox.is_checked():
                    await checkbox.click()
            
            logger.info("✓ Alle Modelle deaktiviert")
            
            # Batch Search versuchen
            batch_button = page.locator('#csv-info button').first
            if await batch_button.count() > 0:
                await batch_button.click()
                await page.wait_for_timeout(3000)
                logger.info("✓ Batch Search mit 0 Modellen versucht")
            
            return True
            
        except Exception as e:
            logger.error(f"Szenario 1 fehlgeschlagen: {str(e)}")
            return False
    
    async def test_scenario_2_invalid_session(self, page):
        """Szenario 2: Ungültige Session ID"""
        logger.info("=== SZENARIO 2: Manipulierte Session ID ===")
        
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # CSV hochladen
            file_input = page.locator('input#csv_file')
            await file_input.set_input_files('/app/minesearch_v2/backend/test_csv.csv')
            
            upload_button = page.locator('button:has-text("CSV hochladen und weiter")')
            await upload_button.click()
            await page.wait_for_timeout(3000)
            
            # Ein Modell auswählen
            first_checkbox = page.locator('input[type="checkbox"]').first
            if not await first_checkbox.is_checked():
                await first_checkbox.click()
            
            # Session ID manipulieren via JavaScript
            await page.evaluate("""
                // Session ID im localStorage/sessionStorage manipulieren falls vorhanden
                if (typeof window.sessionId !== 'undefined') {
                    window.sessionId = 'INVALID_SESSION_ID_12345';
                }
                // Hidden input fields manipulieren
                const sessionInputs = document.querySelectorAll('input[name="session_id"]');
                sessionInputs.forEach(input => input.value = 'INVALID_SESSION_ID_12345');
            """)
            
            logger.info("✓ Session ID manipuliert")
            
            # Batch Search versuchen
            batch_button = page.locator('#csv-info button').first
            await batch_button.click()
            await page.wait_for_timeout(3000)
            
            return True
            
        except Exception as e:
            logger.error(f"Szenario 2 fehlgeschlagen: {str(e)}")
            return False
    
    async def test_scenario_3_malformed_request(self, page):
        """Szenario 3: Direct API Call mit fehlerhaften Daten"""
        logger.info("=== SZENARIO 3: Direct API Call mit fehlerhaften Daten ===")
        
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # Verschiedene fehlerhafte API-Calls via JavaScript
            test_calls = [
                # Leerer POST
                {
                    'name': 'Leerer POST Body',
                    'data': ''
                },
                # Fehlende Parameter
                {
                    'name': 'Nur session_id',
                    'data': 'session_id=test-123'
                },
                # Ungültige Modelle
                {
                    'name': 'Ungültige Modelle',
                    'data': 'session_id=test-123&selected_models=invalid:model,nonexistent:model&count=3'
                },
                # Negative count
                {
                    'name': 'Negative count',
                    'data': 'session_id=test-123&selected_models=openrouter:deepseek-free&count=-1'
                },
                # Überlange count
                {
                    'name': 'Überlange count',
                    'data': 'session_id=test-123&selected_models=openrouter:deepseek-free&count=999999'
                }
            ]
            
            for test_call in test_calls:
                logger.info(f"Teste: {test_call['name']}")
                
                await page.evaluate(f"""
                    fetch('/api/batch-search', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded'
                        }},
                        body: '{test_call['data']}'
                    }})
                    .then(response => console.log('Response:', response.status, response.statusText))
                    .catch(error => console.error('Error:', error));
                """)
                
                await page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            logger.error(f"Szenario 3 fehlgeschlagen: {str(e)}")
            return False
    
    async def test_scenario_4_concurrent_requests(self, page):
        """Szenario 4: Gleichzeitige Batch-Requests"""
        logger.info("=== SZENARIO 4: Gleichzeitige Batch-Requests ===")
        
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # CSV hochladen
            file_input = page.locator('input#csv_file')
            await file_input.set_input_files('/app/minesearch_v2/backend/test_csv.csv')
            
            upload_button = page.locator('button:has-text("CSV hochladen und weiter")')
            await upload_button.click()
            await page.wait_for_timeout(3000)
            
            # Ein Modell auswählen
            first_checkbox = page.locator('input[type="checkbox"]').first
            if not await first_checkbox.is_checked():
                await first_checkbox.click()
            
            # Mehrere schnelle Batch-Requests via JavaScript
            await page.evaluate("""
                const formData = 'session_id=concurrent-test&selected_models=openrouter:deepseek-free&count=3&search_all=false';
                
                // 5 gleichzeitige Requests
                for (let i = 0; i < 5; i++) {
                    fetch('/api/batch-search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded'
                        },
                        body: formData
                    })
                    .then(response => console.log(`Concurrent ${i}:`, response.status))
                    .catch(error => console.error(`Concurrent ${i} Error:`, error));
                }
            """)
            
            await page.wait_for_timeout(5000)
            
            return True
            
        except Exception as e:
            logger.error(f"Szenario 4 fehlgeschlagen: {str(e)}")
            return False
    
    async def run_all_scenarios(self):
        """Alle Szenarien durchführen"""
        logger.info("🔥 STARTE ERROR-PROVOKATIONS-TESTS")
        
        async with async_playwright() as playwright:
            browser, context, page = await self.setup_browser(playwright)
            
            try:
                scenarios = [
                    self.test_scenario_1_no_models_selected,
                    self.test_scenario_2_invalid_session,
                    self.test_scenario_3_malformed_request,
                    self.test_scenario_4_concurrent_requests
                ]
                
                for i, scenario in enumerate(scenarios, 1):
                    logger.info(f"\n--- SZENARIO {i} STARTEN ---")
                    success = await scenario(page)
                    logger.info(f"--- SZENARIO {i} {'ERFOLG' if success else 'FEHLER'} ---\n")
                    
                    # Zwischen Szenarien warten
                    await page.wait_for_timeout(2000)
                
                # Ergebnisse analysieren
                logger.info(f"\n📊 ERGEBNISSE:")
                logger.info(f"Total Requests: {len(self.all_requests)}")
                logger.info(f"Total Errors: {len(self.all_errors)}")
                
                # 400 Errors hervorheben
                error_400s = [e for e in self.all_errors if e['status'] == 400]
                logger.info(f"400 Errors: {len(error_400s)}")
                
                for error in error_400s:
                    logger.error(f"400 ERROR: {error['url']}")
                    logger.error(f"  Body: {error.get('body', 'NO_BODY')[:200]}...")
                
                # Ergebnisse speichern
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                results = {
                    'timestamp': timestamp,
                    'total_requests': len(self.all_requests),
                    'total_errors': len(self.all_errors),
                    'error_400_count': len(error_400s),
                    'requests': self.all_requests,
                    'errors': self.all_errors
                }
                
                result_file = f'/tmp/error_provocation_results_{timestamp}.json'
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✓ Ergebnisse gespeichert: {result_file}")
                return result_file
                
            finally:
                await browser.close()

async def main():
    tester = ErrorProvocationTester()
    result_file = await tester.run_all_scenarios()
    print(f"\n🎯 ERROR-PROVOKATIONS-TEST ABGESCHLOSSEN")
    print(f"Ergebnisse: {result_file}")

if __name__ == "__main__":
    asyncio.run(main())