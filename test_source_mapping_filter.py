#!/usr/bin/env python3
"""
Test des _source_mapping Filters in Details-Modal
"""

import asyncio
from playwright.async_api import async_playwright

async def test_source_mapping_filter():
    print("🔍 SOURCE_MAPPING FILTER TEST")
    print("=============================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            if any(keyword in msg.text for keyword in ['MODAL', 'CONSOLIDATED', 'ERROR']):
                print(f"📝 {msg.text}")
        page.on("console", handle_console)
        
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(3000)
        
        # Test mit Mock-Data
        print("\n🧪 Teste Details-Modal mit Mock-Data...")
        await page.evaluate("""
            // Erstelle Mock-Daten mit _source_mapping
            const mockMineData = {
                best_values: {
                    'Mine Name': 'Test Mine',
                    'Land': 'Deutschland',
                    '_source_mapping': {
                        'source1': 'url1',
                        'source2': 'url2'
                    },
                    'Minenfläche in qkm': '125.5',
                    '_internal_id': '12345',
                    'Geförderte Stoffe': 'Gold, Silber'
                },
                source_summary: {
                    total_unique_sources: 3
                }
            };
            
            console.log('🔧 [TEST] Erstelle Mock-Details-Modal...');
            window.showConsolidatedDetailModal('Test Mine', mockMineData);
        """)
        await page.wait_for_timeout(3000)
        
        # Prüfe Modal-Inhalt
        modal_content = await page.evaluate("""
            () => {
                const modal = document.querySelector('.modal-overlay');
                if (modal) {
                    // Sammle alle Feld-Namen im Modal
                    const fieldNames = Array.from(modal.querySelectorAll('.field-name'))
                        .map(el => el.textContent.trim());
                    
                    return {
                        modalExists: true,
                        fieldCount: fieldNames.length,
                        fieldNames: fieldNames,
                        hasSourceMapping: fieldNames.includes('_source_mapping'),
                        hasInternalId: fieldNames.includes('_internal_id'),
                        hasNormalFields: fieldNames.includes('Mine Name') || fieldNames.includes('Land')
                    };
                }
                return { modalExists: false };
            }
        """)
        
        print(f"\n📋 Modal-Content-Analyse:")
        print(f"   Modal existiert: {modal_content.get('modalExists', False)}")
        
        if modal_content.get('modalExists'):
            print(f"   Anzahl Felder: {modal_content.get('fieldCount', 0)}")
            print(f"   Feld-Namen: {modal_content.get('fieldNames', [])}")
            print(f"\n✅ Filter-Ergebnisse:")
            print(f"   ❌ _source_mapping gefiltert: {not modal_content.get('hasSourceMapping', True)}")
            print(f"   ❌ _internal_id gefiltert: {not modal_content.get('hasInternalId', True)}")
            print(f"   ✅ Normale Felder angezeigt: {modal_content.get('hasNormalFields', False)}")
            
            if not modal_content.get('hasSourceMapping') and not modal_content.get('hasInternalId'):
                print(f"\n🎉 FILTER ERFOLGREICH!")
                print(f"   ✅ Meta-Felder (mit '_' Präfix) werden ausgeblendet")
                print(f"   ✅ Normale Felder werden weiterhin angezeigt")
            else:
                print(f"\n❌ FILTER FEHLGESCHLAGEN!")
                if modal_content.get('hasSourceMapping'):
                    print(f"   ❌ _source_mapping wird noch angezeigt")
                if modal_content.get('hasInternalId'):
                    print(f"   ❌ _internal_id wird noch angezeigt")
            
            # Schließe Modal für Clean-Up
            await page.evaluate("window.closeModal()")
            await page.wait_for_timeout(1000)
        else:
            print("❌ Modal wurde nicht erstellt")
        
        print(f"\n🎯 SOURCE_MAPPING FILTER TEST ABGESCHLOSSEN")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_source_mapping_filter())
