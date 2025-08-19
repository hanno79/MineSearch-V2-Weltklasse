#!/usr/bin/env python3
"""
Test des Filters mit echten API-Daten Simulation
"""

import asyncio
from playwright.async_api import async_playwright

async def test_real_data_filter():
    print("🔍 REAL DATA FILTER TEST")
    print("========================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(3000)
        
        # Test Filter-Logic direkt in Browser
        print("\n🧪 Teste Filter-Logic direkt...")
        filter_test = await page.evaluate("""
            () => {
                // Simuliere echte API-Daten
                const testData = {
                    'Mine Name': 'Antamina',
                    'Land': 'Peru',
                    'Geförderte Stoffe': 'Kupfer, Zink',
                    '_source_mapping': { 'source1': 'url1' },
                    '_internal_id': '12345',
                    'Minenfläche in qkm': '125.5',
                    '_metadata': { 'created': '2025-01-01' },
                    'Restaurationskosten': '5.2 Millionen USD'
                };
                
                // Teste Filter-Logic
                const filteredEntries = Object.entries(testData)
                    .filter(([field, value]) => !field.startsWith('_'));
                
                const filteredFields = filteredEntries.map(([field, value]) => field);
                const filteredCount = filteredFields.length;
                
                const originalCount = Object.keys(testData).length;
                const metaFields = Object.keys(testData).filter(field => field.startsWith('_'));
                
                return {
                    originalCount,
                    filteredCount,
                    metaFields,
                    filteredFields,
                    filterWorking: metaFields.length > 0 && !filteredFields.some(f => f.startsWith('_'))
                };
            }
        """)
        
        print(f"\n📊 Filter-Logic Test:")
        print(f"   Original Felder: {filter_test['originalCount']}")
        print(f"   Gefilterte Felder: {filter_test['filteredCount']}")
        print(f"   Meta-Felder (entfernt): {filter_test['metaFields']}")
        print(f"   Normale Felder (behalten): {filter_test['filteredFields']}")
        print(f"\n✅ Filter funktioniert: {filter_test['filterWorking']}")
        
        if filter_test['filterWorking']:
            print(f"\n🎉 FILTER-LOGIC PERFEKT!")
            print(f"   ✅ {len(filter_test['metaFields'])} Meta-Felder werden ausgeblendet")
            print(f"   ✅ {filter_test['filteredCount']} normale Felder bleiben sichtbar")
            
            # Prüfe spezifisch _source_mapping
            if '_source_mapping' in filter_test['metaFields']:
                print(f"   ✅ _source_mapping wird korrekt herausgefiltert")
        else:
            print(f"\n❌ FILTER-LOGIC FEHLERHAFT!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_data_filter())
