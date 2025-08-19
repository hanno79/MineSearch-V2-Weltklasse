#!/usr/bin/env python3
"""
Debug der Modal-Struktur und Land-Feld
"""

import asyncio
from playwright.async_api import async_playwright

async def test_modal_struktur():
    print("🔍 MODAL STRUKTUR DEBUG")
    print("======================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(4000)
        
        # Teste mit Mock-Data für bessere Kontrolle
        print("\n🧪 Teste mit Mock-Daten...")
        modal_content = await page.evaluate("""
            // Mock-Daten mit country auf Top-Level
            const mockData = {
                mine_name: 'Test Mine',
                country: 'Deutschland',
                region: 'Bayern', 
                best_values: {
                    'Rohstoffe': 'Gold, Silber',
                    'Betreiber': 'Test Corp'
                },
                source_summary: {
                    total_unique_sources: 5
                }
            };
            
            console.log('🔧 [DEBUG] Mock-Daten:', mockData);
            
            // Rufe showConsolidatedDetailModal direkt auf
            window.showConsolidatedDetailModal('Test Mine', mockData);
            
            // Warte kurz und analysiere Modal-Struktur
            setTimeout(() => {
                const modal = document.querySelector('.modal-overlay');
                if (modal) {
                    const modalHTML = modal.innerHTML;
                    console.log('🔧 [DEBUG] Modal HTML (first 500 chars):', modalHTML.substring(0, 500));
                    
                    // Suche speziell nach Land-Information
                    const landRegex = /Land:.*?</g;
                    const landMatch = modalHTML.match(landRegex);
                    console.log('🔧 [DEBUG] Land-Match:', landMatch);
                    
                    return {
                        modalExists: true,
                        hasLandField: modalHTML.includes('Land:'),
                        landContent: landMatch ? landMatch[0] : null,
                        fullHTML: modalHTML.length
                    };
                }
                return { modalExists: false };
            }, 1000);
        """)
        
        await page.wait_for_timeout(2000)
        
        # Prüfe Modal nach Mock-Daten
        final_check = await page.evaluate("""
            () => {
                const modal = document.querySelector('.modal-overlay');
                if (modal) {
                    const modalText = modal.textContent;
                    console.log('🔧 [DEBUG] Modal Text:', modalText);
                    
                    // Suche nach Land-Zeile
                    const lines = modalText.split('\\n');
                    const landLine = lines.find(line => line.includes('Land:'));
                    
                    return {
                        modalExists: true,
                        modalText: modalText.substring(0, 200),
                        landLine: landLine ? landLine.trim() : null
                    };
                }
                return { modalExists: false };
            }
        """)
        
        print(f"📋 Modal-Analyse nach Mock-Daten:")
        print(f"   Modal existiert: {final_check.get('modalExists', False)}")
        print(f"   Modal Text (ersten 200 Zeichen): {final_check.get('modalText', 'N/A')}")
        print(f"   Land-Zeile: {final_check.get('landLine', 'Nicht gefunden')}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_modal_struktur())
