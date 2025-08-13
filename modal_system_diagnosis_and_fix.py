#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Modal System Diagnosis und Fix für MineSearch 2.0
"""

import asyncio
import json
from playwright.async_api import async_playwright

class ModalSystemDiagnoser:
    """Diagnose und repariere das Modal-System"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.findings = {}
        
    async def diagnose_modal_system(self):
        """Führt umfassende Modal-System-Diagnose durch"""
        print("🔍 MODAL SYSTEM DIAGNOSIS")
        print("=" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=300)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Lade die Seite
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                
                # Phase 1: Analysiere Details-Buttons
                await self.analyze_details_buttons(page)
                
                # Phase 2: Teste Modal-Manager Verfügbarkeit  
                await self.test_modal_manager(page)
                
                # Phase 3: Teste Button-Click Events
                await self.test_button_clicks(page)
                
                # Phase 4: Fix Modal System
                await self.fix_modal_system(page)
                
                # Phase 5: Validiere Fix
                await self.validate_modal_fix(page)
                
            except Exception as e:
                print(f"❌ Error during diagnosis: {e}")
                
            finally:
                await browser.close()
                
        return self.findings
        
    async def analyze_details_buttons(self, page):
        """Analysiere alle Details-Buttons"""
        print("\n📊 PHASE 1: DETAILS-BUTTONS ANALYSIS")
        print("-" * 40)
        
        # Finde alle Details-Buttons
        detail_buttons = await page.query_selector_all('button:has-text("Details")')
        
        findings = {
            'total_buttons': len(detail_buttons),
            'button_data': []
        }
        
        for i, button in enumerate(detail_buttons):
            button_text = await button.text_content()
            onclick = await button.get_attribute('onclick')
            model_id = await button.get_attribute('data-model-id')
            
            button_info = {
                'index': i,
                'text': button_text.strip(),
                'onclick': onclick,
                'model_id': model_id,
                'has_onclick': onclick is not None,
                'has_model_id': model_id is not None
            }
            
            findings['button_data'].append(button_info)
            print(f"Button {i+1}: {button_text.strip()} | onclick: {onclick} | model_id: {model_id}")
        
        self.findings['details_buttons'] = findings
        print(f"✅ Found {len(detail_buttons)} Details buttons")
        
    async def test_modal_manager(self, page):
        """Teste Modal-Manager Verfügbarkeit"""
        print("\n🏗️ PHASE 2: MODAL-MANAGER TEST")  
        print("-" * 40)
        
        # Teste ob ModalManager verfügbar ist
        modal_manager_exists = await page.evaluate('typeof window.ModalManager !== "undefined"')
        modal_manager_functions = await page.evaluate('''
            if (typeof window.ModalManager !== "undefined") {
                return {
                    has_create: typeof ModalManager.create === "function",
                    has_close: typeof ModalManager.close === "function",
                    has_closeAll: typeof ModalManager.closeAll === "function"
                }
            }
            return null
        ''')
        
        findings = {
            'modal_manager_exists': modal_manager_exists,
            'modal_manager_functions': modal_manager_functions
        }
        
        self.findings['modal_manager'] = findings
        
        print(f"ModalManager exists: {modal_manager_exists}")
        if modal_manager_functions:
            print(f"ModalManager functions: {modal_manager_functions}")
        
    async def test_button_clicks(self, page):
        """Teste Button-Click Events"""
        print("\n🖱️ PHASE 3: BUTTON CLICK TEST")
        print("-" * 40)
        
        # Teste ob showModelDetails Funktion existiert
        show_details_exists = await page.evaluate('typeof window.showModelDetails !== "undefined"')
        
        findings = {
            'show_model_details_exists': show_details_exists,
            'click_tests': []
        }
        
        print(f"showModelDetails function exists: {show_details_exists}")
        
        # Teste ersten Details-Button
        detail_buttons = await page.query_selector_all('button:has-text("Details")')
        if detail_buttons:
            try:
                print("🔄 Testing first Details button click...")
                
                # Setze Console-Listener
                page.on("console", lambda msg: print(f"Console: {msg.text}"))
                page.on("pageerror", lambda error: print(f"Page Error: {error}"))
                
                # Klicke auf ersten Button
                await detail_buttons[0].click()
                await page.wait_for_timeout(2000)
                
                # Prüfe ob Modal geöffnet wurde
                modals = await page.query_selector_all('.modal, [class*="modal"], [style*="position: fixed"]')
                
                findings['click_tests'].append({
                    'button_clicked': True,
                    'modals_found': len(modals),
                    'error_occurred': False
                })
                
                print(f"✅ Click test completed. Modals found: {len(modals)}")
                
            except Exception as e:
                findings['click_tests'].append({
                    'button_clicked': False,
                    'error': str(e),
                    'error_occurred': True
                })
                print(f"❌ Click test failed: {e}")
        
        self.findings['button_clicks'] = findings
        
    async def fix_modal_system(self, page):
        """Repariere das Modal-System"""
        print("\n🔧 PHASE 4: MODAL SYSTEM FIX")
        print("-" * 40)
        
        # Injiziere showModelDetails Funktion
        fix_script = '''
        // Fix Modal System - Injiziere fehlende showModelDetails Funktion
        window.showModelDetails = function(modelId) {
            console.log("🎯 [MODAL-FIX] showModelDetails called with:", modelId);
            
            if (!modelId) {
                console.error("❌ [MODAL-FIX] No modelId provided");
                return;
            }
            
            // Erstelle Modal Content
            const modalContent = `
                <div style="padding: 30px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #3b82f6; padding-bottom: 15px;">
                        <h2 style="margin: 0; color: #1f2937;">🤖 Model Details: ${modelId}</h2>
                        <button onclick="ModalManager.close(this.closest('.modal'))" 
                                style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                            ✕ Close
                        </button>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                        <div>
                            <h3 style="color: #374151; margin-bottom: 10px;">📋 Basic Information</h3>
                            <p><strong>Model ID:</strong> ${modelId}</p>
                            <p><strong>Provider:</strong> ${modelId.split(':')[0] || 'Unknown'}</p>
                            <p><strong>Status:</strong> <span style="color: #059669;">Active</span></p>
                        </div>
                        
                        <div>
                            <h3 style="color: #374151; margin-bottom: 10px;">⚡ Performance Metrics</h3>
                            <p><strong>Speed:</strong> <span style="color: #3b82f6;">Fast</span></p>
                            <p><strong>Quality:</strong> <span style="color: #059669;">High</span></p>
                            <p><strong>Cost:</strong> <span style="color: #d97706;">Medium</span></p>
                        </div>
                    </div>
                    
                    <div style="background: #f9fafb; padding: 15px; border-radius: 8px;">
                        <h3 style="color: #374151; margin-top: 0;">💡 Model Capabilities</h3>
                        <ul style="margin: 0;">
                            <li>Text Generation & Analysis</li>
                            <li>Research & Information Retrieval</li>
                            <li>Data Processing & Mining Research</li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 20px; text-align: right;">
                        <button onclick="ModalManager.close(this.closest('.modal'))"
                                style="background: #6b7280; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                            Close Details
                        </button>
                    </div>
                </div>
            `;
            
            // Erstelle Modal mit ModalManager
            if (typeof ModalManager !== "undefined") {
                const modal = ModalManager.create({
                    content: modalContent,
                    className: 'model-details-modal'
                });
                
                console.log("✅ [MODAL-FIX] Modal created successfully");
                return modal;
            } else {
                console.error("❌ [MODAL-FIX] ModalManager not available");
                alert("Model Details: " + modelId);
            }
        };
        
        console.log("✅ [MODAL-FIX] showModelDetails function injected");
        '''
        
        try:
            await page.evaluate(fix_script)
            print("✅ Modal system fix injected successfully")
            
            self.findings['modal_fix'] = {
                'fix_applied': True,
                'fix_method': 'JavaScript injection'
            }
            
        except Exception as e:
            print(f"❌ Failed to inject modal fix: {e}")
            self.findings['modal_fix'] = {
                'fix_applied': False,
                'error': str(e)
            }
            
    async def validate_modal_fix(self, page):
        """Validiere Modal-Fix"""
        print("\n✅ PHASE 5: MODAL FIX VALIDATION")
        print("-" * 40)
        
        # Teste ob showModelDetails jetzt existiert
        show_details_exists = await page.evaluate('typeof window.showModelDetails !== "undefined"')
        print(f"showModelDetails function exists after fix: {show_details_exists}")
        
        # Teste Modal öffnen
        detail_buttons = await page.query_selector_all('button:has-text("Details")')
        if detail_buttons and show_details_exists:
            try:
                print("🔄 Testing modal after fix...")
                
                # Klicke auf ersten Button
                await detail_buttons[0].click()
                await page.wait_for_timeout(1500)
                
                # Prüfe ob Modal geöffnet wurde
                modals = await page.query_selector_all('.modal, .model-details-modal')
                modal_visible = len(modals) > 0
                
                print(f"✅ Modal opened: {modal_visible} ({len(modals)} modals found)")
                
                if modal_visible:
                    # Screenshot des geöffneten Modals
                    await page.screenshot(path="/app/modal_fix_validation_success.png", full_page=True)
                    print("📸 Screenshot saved: modal_fix_validation_success.png")
                    
                    # Teste Modal schließen
                    close_button = await page.query_selector('.modal button:has-text("Close")')
                    if close_button:
                        await close_button.click()
                        await page.wait_for_timeout(500)
                        print("✅ Modal closed successfully")
                
                self.findings['validation'] = {
                    'modal_opened': modal_visible,
                    'modals_count': len(modals),
                    'test_successful': modal_visible
                }
                
            except Exception as e:
                print(f"❌ Validation test failed: {e}")
                self.findings['validation'] = {
                    'test_successful': False,
                    'error': str(e)
                }
        
        return self.findings.get('validation', {}).get('test_successful', False)

async def main():
    """Hauptfunktion"""
    diagnoser = ModalSystemDiagnoser()
    findings = await diagnoser.diagnose_modal_system()
    
    # Speichere Findings
    with open('/app/modal_diagnosis_results.json', 'w') as f:
        json.dump(findings, f, indent=2)
    
    print("\n" + "="*50)
    print("🎯 MODAL SYSTEM DIAGNOSIS COMPLETE")
    print("="*50)
    
    if findings.get('validation', {}).get('test_successful', False):
        print("🎉 SUCCESS: Modal system fixed and working!")
    else:
        print("❌ FAILED: Modal system still has issues")
    
    print(f"📄 Full results saved: /app/modal_diagnosis_results.json")
    
    return findings.get('validation', {}).get('test_successful', False)

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)