"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: E2E Frontend Test mit echtem Browser-Traffic für Batch-Search 400 Error Analyse
"""

import asyncio
import json
import logging
from playwright.async_api import async_playwright
from datetime import datetime
import os

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FrontendE2ETester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.csv_file_path = "/app/minesearch_v2/backend/test_csv.csv"
        self.network_requests = []
        self.console_logs = []
        self.errors = []
        
    async def setup_browser(self, playwright):
        """Browser mit Network-Monitoring starten"""
        browser = await playwright.chromium.launch(
            headless=False,  # Browser sichtbar für Debugging
            slow_mo=1000  # 1s Verzögerung zwischen Aktionen
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        
        # Network Request Listener
        async def handle_request(request):
            request_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'post_data': None
            }
            
            # POST-Daten erfassen wenn vorhanden
            if request.method == 'POST':
                try:
                    request_data['post_data'] = request.post_data
                except:
                    request_data['post_data'] = 'BINARY_DATA'
            
            self.network_requests.append(request_data)
            logger.info(f"REQUEST: {request.method} {request.url}")
            
        # Response Listener
        async def handle_response(response):
            response_data = {
                'timestamp': datetime.now().isoformat(),
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers),
                'body': None
            }
            
            # Response Body erfassen (nur für API-Calls)
            if '/api/' in response.url:
                try:
                    if 'application/json' in response.headers.get('content-type', ''):
                        response_data['body'] = await response.json()
                    else:
                        response_data['body'] = await response.text()
                except Exception as e:
                    response_data['body'] = f'ERROR_READING_BODY: {str(e)}'
            
            # Fehler-Responses hervorheben
            if response.status >= 400:
                logger.error(f"ERROR RESPONSE: {response.status} {response.url}")
                self.errors.append(response_data)
            
            logger.info(f"RESPONSE: {response.status} {response.url}")
            
        # Console Log Listener
        async def handle_console(msg):
            console_data = {
                'timestamp': datetime.now().isoformat(),
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            }
            self.console_logs.append(console_data)
            logger.info(f"CONSOLE {msg.type.upper()}: {msg.text}")
            
        # Event Listener registrieren
        page.on('request', handle_request)
        page.on('response', handle_response)
        page.on('console', handle_console)
        
        return browser, context, page
    
    async def navigate_to_app(self, page):
        """Zur Hauptseite navigieren"""
        logger.info("=== SCHRITT 1: Navigation zu localhost:8000 ===")
        
        try:
            await page.goto(self.base_url, wait_until='networkidle')
            await page.wait_for_load_state('domcontentloaded')
            
            # Screenshot zur Dokumentation
            await page.screenshot(path='/tmp/01_initial_page.png')
            logger.info("✓ Seite erfolgreich geladen")
            
            # DOM-Status prüfen
            title = await page.title()
            logger.info(f"Seitentitel: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Navigation fehlgeschlagen: {str(e)}")
            return False
    
    async def upload_csv_file(self, page):
        """CSV-Datei hochladen"""
        logger.info("=== SCHRITT 2: CSV-Datei hochladen ===")
        
        try:
            # CSV Tab sicherstellen (sollte bereits aktiv sein)
            csv_tab = page.locator('label[for="method_csv"]')
            if await csv_tab.count() > 0:
                await csv_tab.click()
                await page.wait_for_timeout(1000)
            
            # File Input finden
            file_input = page.locator('input#csv_file')
            if await file_input.count() == 0:
                logger.error("✗ CSV File Input nicht gefunden")
                return False
            
            # Datei auswählen
            await file_input.set_input_files(self.csv_file_path)
            logger.info(f"✓ Datei {self.csv_file_path} ausgewählt")
            
            # Upload-Button klicken
            upload_button = page.locator('button:has-text("CSV hochladen und weiter")')
            if await upload_button.count() == 0:
                logger.error("✗ Upload Button nicht gefunden")
                return False
            
            # Request-Counter vor Upload
            requests_before = len(self.network_requests)
            
            # Upload ausführen
            await upload_button.click()
            logger.info("✓ Upload Button geklickt")
            
            # Auf Upload-Verarbeitung warten
            await page.wait_for_timeout(3000)
            
            # Screenshot nach Upload
            await page.screenshot(path='/tmp/02_after_upload.png')
            
            # Neue Requests prüfen
            new_requests = self.network_requests[requests_before:]
            logger.info(f"Upload-Requests: {len(new_requests)}")
            
            # CSV-Info prüfen (sollte nach Upload erscheinen)
            csv_info = page.locator('#csv-info')
            if await csv_info.count() > 0:
                info_text = await csv_info.inner_text()
                logger.info(f"CSV-Info: {info_text[:200]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ CSV Upload fehlgeschlagen: {str(e)}")
            return False
    
    async def select_models(self, page):
        """Modelle für die Suche auswählen"""
        logger.info("=== SCHRITT 3: Modelle auswählen ===")
        
        try:
            # Auf Tab "Search" klicken falls nötig
            search_tab = page.locator('button:has-text("Search"), a:has-text("Search")')
            if await search_tab.count() > 0:
                await search_tab.click()
                await page.wait_for_timeout(1000)
            
            # Modell-Checkboxen finden
            model_checkboxes = page.locator('input[type="checkbox"]')
            checkbox_count = await model_checkboxes.count()
            
            logger.info(f"Gefundene Checkboxen: {checkbox_count}")
            
            # Erste 3 Modelle auswählen
            selected_count = 0
            for i in range(min(checkbox_count, 3)):
                try:
                    checkbox = model_checkboxes.nth(i)
                    if not await checkbox.is_checked():
                        await checkbox.click()
                        selected_count += 1
                        logger.info(f"✓ Modell {i+1} ausgewählt")
                except Exception as e:
                    logger.warning(f"Checkbox {i} nicht klickbar: {str(e)}")
            
            if selected_count == 0:
                logger.error("✗ Keine Modelle ausgewählt")
                return False
            
            # Screenshot nach Modell-Auswahl
            await page.screenshot(path='/tmp/03_models_selected.png')
            logger.info(f"✓ {selected_count} Modelle ausgewählt")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Modell-Auswahl fehlgeschlagen: {str(e)}")
            return False
    
    async def perform_batch_search(self, page):
        """Batch Search durchführen und Network-Traffic überwachen"""
        logger.info("=== SCHRITT 4: Batch Search durchführen ===")
        
        try:
            # DOM-State vor Request dokumentieren
            dom_before = await page.content()
            with open('/tmp/dom_before_batch_search.html', 'w', encoding='utf-8') as f:
                f.write(dom_before)
            
            # Nach CSV-Upload sollte Batch Search in csv-info erscheinen
            # Warten bis CSV-Info geladen ist und Batch Search verfügbar
            await page.wait_for_timeout(2000)
            
            # Batch Search Button in verschiedenen Bereichen suchen
            batch_selectors = [
                'button[onclick*="startBatchSearch"]',
                'button:has-text("Batch Search")',
                'button:has-text("Start Batch")', 
                '#csv-info button',
                '.search-controls button'
            ]
            
            batch_button = None
            for selector in batch_selectors:
                buttons = page.locator(selector)
                if await buttons.count() > 0:
                    batch_button = buttons.first
                    logger.info(f"✓ Batch Button gefunden: {selector}")
                    break
            
            if not batch_button:
                logger.error("✗ Batch Search Button nicht gefunden")
                
                # Gesamten CSV-Info Bereich analysieren
                csv_info = page.locator('#csv-info')
                if await csv_info.count() > 0:
                    info_content = await csv_info.inner_html()
                    logger.info(f"CSV-Info Inhalt: {info_content[:500]}...")
                
                # Alternative Button-Texte suchen
                all_buttons = page.locator('button, input[type="submit"], input[type="button"]')
                button_count = await all_buttons.count()
                logger.info(f"Verfügbare Buttons: {button_count}")
                
                for i in range(min(button_count, 10)):  # Nur erste 10 anzeigen
                    try:
                        btn = all_buttons.nth(i)
                        if await btn.is_visible():
                            text = await btn.inner_text()
                            onclick = await btn.get_attribute('onclick')
                            logger.info(f"Button {i}: text='{text}', onclick='{onclick}'")
                    except:
                        logger.info(f"Button {i}: NICHT ZUGÄNGLICH")
                
                return False
            
            # Request-Counter vor dem Click
            requests_before = len(self.network_requests)
            
            # Batch Search starten
            await batch_button.click()
            logger.info("✓ Batch Search Button geklickt")
            
            # Warten auf Network-Requests
            await page.wait_for_timeout(5000)
            
            # Neue Requests analysieren
            new_requests = self.network_requests[requests_before:]
            logger.info(f"Neue Requests nach Button-Click: {len(new_requests)}")
            
            # Screenshot nach Request
            await page.screenshot(path='/tmp/04_after_batch_search.png')
            
            # DOM-State nach Request dokumentieren
            dom_after = await page.content()
            with open('/tmp/dom_after_batch_search.html', 'w', encoding='utf-8') as f:
                f.write(dom_after)
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Batch Search fehlgeschlagen: {str(e)}")
            return False
    
    async def analyze_errors(self):
        """400 Errors analysieren"""
        logger.info("=== SCHRITT 5: Error-Analyse ===")
        
        error_400s = [err for err in self.errors if err['status'] == 400]
        
        if not error_400s:
            logger.info("✓ Keine 400 Errors gefunden")
            return
        
        logger.error(f"✗ {len(error_400s)} 400 Errors gefunden!")
        
        for i, error in enumerate(error_400s):
            logger.error(f"ERROR {i+1}:")
            logger.error(f"  URL: {error['url']}")
            logger.error(f"  Status: {error['status']}")
            logger.error(f"  Body: {error.get('body', 'NO_BODY')}")
            
            # Entsprechenden Request finden
            matching_requests = [
                req for req in self.network_requests 
                if req['url'] == error['url']
            ]
            
            if matching_requests:
                req = matching_requests[-1]  # Letzter passender Request
                logger.error(f"  Request Method: {req['method']}")
                logger.error(f"  Request Headers: {json.dumps(req['headers'], indent=2)}")
                logger.error(f"  Request Data: {req.get('post_data', 'NO_DATA')}")
    
    async def save_results(self):
        """Testergebnisse speichern"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            'timestamp': timestamp,
            'base_url': self.base_url,
            'csv_file': self.csv_file_path,
            'network_requests': self.network_requests,
            'console_logs': self.console_logs,
            'errors': self.errors,
            'summary': {
                'total_requests': len(self.network_requests),
                'total_errors': len(self.errors),
                'error_400_count': len([e for e in self.errors if e['status'] == 400]),
                'console_errors': len([c for c in self.console_logs if c['type'] == 'error'])
            }
        }
        
        # JSON-Datei speichern
        result_file = f'/tmp/e2e_test_results_{timestamp}.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Ergebnisse gespeichert: {result_file}")
        return result_file
    
    async def run_complete_test(self):
        """Vollständigen E2E Test durchführen"""
        logger.info("🚀 STARTE E2E FRONTEND TEST")
        
        async with async_playwright() as playwright:
            browser, context, page = await self.setup_browser(playwright)
            
            try:
                # Test-Schritte ausführen
                success = True
                success &= await self.navigate_to_app(page)
                success &= await self.upload_csv_file(page)
                success &= await self.select_models(page)
                success &= await self.perform_batch_search(page)
                
                # Error-Analyse
                await self.analyze_errors()
                
                # Ergebnisse speichern
                result_file = await self.save_results()
                
                if success:
                    logger.info("✅ E2E Test erfolgreich abgeschlossen")
                else:
                    logger.warning("⚠️ E2E Test mit Fehlern abgeschlossen")
                
                return result_file
                
            finally:
                await browser.close()

async def main():
    """Hauptfunktion"""
    tester = FrontendE2ETester()
    result_file = await tester.run_complete_test()
    
    print(f"\n📋 TESTERGEBNISSE:")
    print(f"Datei: {result_file}")
    print(f"Screenshots: /tmp/0*_*.png")
    print(f"DOM-Snapshots: /tmp/dom_*.html")

if __name__ == "__main__":
    asyncio.run(main())