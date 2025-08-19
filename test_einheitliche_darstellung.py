#!/usr/bin/env python3
"""
Test der einheitlichen "Nichts gefunden" Darstellung
Prüft ob alle Platzhalter-Werte konsistent als "Nichts gefunden" angezeigt werden
"""

import asyncio
from playwright.async_api import async_playwright

async def test_einheitliche_darstellung():
    print("🎯 TESTE EINHEITLICHE 'NICHTS GEFUNDEN' DARSTELLUNG")
    print("=================================================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            console_messages.append(msg.text)
            if any(keyword in msg.text for keyword in ['LEER', 'NICHTS GEFUNDEN', 'UNBEKANNT']):
                print(f"📝 Console: {msg.text}")
        page.on("console", handle_console)
        
        # Force-refresh mit Cache-Buster für neue Backend-Änderungen
        await page.goto('http://localhost:8000/?test_nichts_gefunden=' + str(asyncio.get_event_loop().time()), wait_until='networkidle')
        await page.wait_for_timeout(4000)
        
        print("\\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(5000)  # Zeit für Backend-Änderungen
        
        # Test 1: Card-Ansicht auf einheitliche Darstellung prüfen
        print("\\n🧪 TEST 1: Card-Ansicht Konsistenz...")
        card_analysis = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.field-based-card, .mine-card');
                const results = {
                    totalCards: cards.length,
                    inconsistentTexts: [],
                    nichtsgefundenCount: 0,
                    unbekanntCount: 0,
                    leerCount: 0,
                    otherPlaceholderCount: 0
                };
                
                cards.forEach((card, index) => {
                    const cardText = card.textContent || '';
                    
                    // Zähle verschiedene Platzhalter-Texte
                    const lowerText = cardText.toLowerCase();
                    if (lowerText.includes('nichts gefunden')) {
                        results.nichtsgefundenCount++;
                    }
                    if (lowerText.includes('unbekannt')) {
                        results.unbekanntCount++;
                    }
                    if (lowerText.includes('leer')) {
                        results.leerCount++;
                    }
                    if (lowerText.includes('n/a') || lowerText.includes('k.a.') || lowerText.includes('keine angaben')) {
                        results.otherPlaceholderCount++;
                    }
                    
                    // Sammle inkonsistente Beispiele (nur ersten 3)
                    if (results.inconsistentTexts.length < 3 && 
                        (lowerText.includes('unbekannt') || lowerText.includes('leer') || 
                         lowerText.includes('n/a') || lowerText.includes('k.a.'))) {
                        
                        const mineName = card.querySelector('.mine-title, h3')?.textContent?.trim() || `Card ${index + 1}`;
                        results.inconsistentTexts.push({
                            mine: mineName,
                            issue: lowerText.includes('unbekannt') ? 'Unbekannt gefunden' :
                                  lowerText.includes('leer') ? 'LEER gefunden' : 'Andere Platzhalter'
                        });
                    }
                });
                
                return results;
            }
        """)
        
        print(f"   📋 Card-Analyse:")
        print(f"      Total Cards: {card_analysis.get('totalCards', 0)}")
        print(f"      'Nichts gefunden': {card_analysis.get('nichtsgefundenCount', 0)}")
        print(f"      'Unbekannt' (alt): {card_analysis.get('unbekanntCount', 0)}")
        print(f"      'LEER' (alt): {card_analysis.get('leerCount', 0)}")
        print(f"      Andere Platzhalter: {card_analysis.get('otherPlaceholderCount', 0)}")
        
        if card_analysis.get('inconsistentTexts'):
            print(f"   ⚠️ Inkonsistenzen gefunden:")
            for issue in card_analysis['inconsistentTexts']:
                print(f"      - {issue['mine']}: {issue['issue']}")
        
        # Test 2: Details-Modal für spezifische Minen prüfen
        test_mines = ['Antamina', 'Canadian Malartic', 'Eleonore']
        modal_results = []
        
        for mine_name in test_mines:
            print(f"\\n🧪 TEST 2: Details-Modal für {mine_name}...")
            
            try:
                await page.evaluate(f"window.viewConsolidatedDetail('{mine_name}')")
                await page.wait_for_timeout(6000)  # Zeit für API-Call
                
                # Analysiere Modal-Inhalt auf Platzhalter-Konsistenz
                modal_analysis = await page.evaluate("""
                    () => {
                        const modal = document.querySelector('.modal-overlay');
                        if (modal) {
                            const modalText = modal.textContent;
                            const lines = modalText.split('\\\\n').map(l => l.trim()).filter(l => l);
                            
                            const analysis = {
                                modalExists: true,
                                totalLines: lines.length,
                                nichtsgefundenLines: [],
                                unbekanntLines: [],
                                leerLines: [],
                                otherPlaceholderLines: []
                            };
                            
                            lines.forEach(line => {
                                const lowerLine = line.toLowerCase();
                                if (lowerLine.includes('nichts gefunden')) {
                                    analysis.nichtsgefundenLines.push(line.substring(0, 50) + '...');
                                } else if (lowerLine.includes('unbekannt')) {
                                    analysis.unbekanntLines.push(line.substring(0, 50) + '...');
                                } else if (lowerLine.includes('leer')) {
                                    analysis.leerLines.push(line.substring(0, 50) + '...');
                                } else if (lowerLine.includes('n/a') || lowerLine.includes('k.a.') || 
                                         lowerLine.includes('keine angaben') || lowerLine.includes('not found')) {
                                    analysis.otherPlaceholderLines.push(line.substring(0, 50) + '...');
                                }
                            });
                            
                            return analysis;
                        }
                        return { modalExists: false };
                    }
                """)
                
                print(f"   📋 {mine_name} Modal-Analyse:")
                print(f"      Modal existiert: {modal_analysis.get('modalExists', False)}")
                if modal_analysis.get('modalExists'):
                    print(f"      'Nichts gefunden' Zeilen: {len(modal_analysis.get('nichtsgefundenLines', []))}")
                    print(f"      'Unbekannt' Zeilen (alt): {len(modal_analysis.get('unbekanntLines', []))}")
                    print(f"      'LEER' Zeilen (alt): {len(modal_analysis.get('leerLines', []))}")
                    print(f"      Andere Platzhalter: {len(modal_analysis.get('otherPlaceholderLines', []))}")
                    
                    # Zeige Beispiele für Inkonsistenzen
                    if modal_analysis.get('unbekanntLines'):
                        print(f"      Beispiel 'Unbekannt': {modal_analysis['unbekanntLines'][0]}")
                    if modal_analysis.get('leerLines'):
                        print(f"      Beispiel 'LEER': {modal_analysis['leerLines'][0]}")
                
                modal_results.append({
                    'mine': mine_name,
                    'consistent': (len(modal_analysis.get('unbekanntLines', [])) == 0 and 
                                 len(modal_analysis.get('leerLines', [])) == 0 and
                                 len(modal_analysis.get('otherPlaceholderLines', [])) == 0),
                    'nichts_gefunden_count': len(modal_analysis.get('nichtsgefundenLines', []))
                })
                
                # Schließe Modal
                await page.evaluate("window.closeModal()")
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"      ❌ Fehler bei {mine_name}: {e}")
                modal_results.append({'mine': mine_name, 'consistent': False, 'nichts_gefunden_count': 0})
        
        # Finale Bewertung
        print(f"\\n🎯 FINALE BEWERTUNG:")
        print(f"==================")
        
        # Card-Konsistenz bewerten
        card_total_issues = (card_analysis.get('unbekanntCount', 0) + 
                           card_analysis.get('leerCount', 0) + 
                           card_analysis.get('otherPlaceholderCount', 0))
        
        card_consistency_rate = 0
        if card_analysis.get('totalCards', 0) > 0:
            card_consistent = card_analysis.get('totalCards', 0) - card_total_issues
            card_consistency_rate = (card_consistent / card_analysis.get('totalCards', 0)) * 100
        
        print(f"📊 CARD-KONSISTENZ: {card_consistency_rate:.1f}%")
        if card_consistency_rate >= 95:
            print(f"   ✅ HERVORRAGEND: Fast alle Cards verwenden 'Nichts gefunden'")
        elif card_consistency_rate >= 80:
            print(f"   ✅ GUT: Meiste Cards sind konsistent")
        else:
            print(f"   ⚠️ VERBESSERUNG NÖTIG: Viele inkonsistente Platzhalter")
        
        # Modal-Konsistenz bewerten
        consistent_modals = len([m for m in modal_results if m['consistent']])
        modal_consistency_rate = (consistent_modals / len(modal_results)) * 100 if modal_results else 0
        
        print(f"📊 MODAL-KONSISTENZ: {modal_consistency_rate:.1f}% ({consistent_modals}/{len(modal_results)})")
        if modal_consistency_rate >= 95:
            print(f"   ✅ HERVORRAGEND: Fast alle Details-Modals sind konsistent")
        elif modal_consistency_rate >= 80:
            print(f"   ✅ GUT: Meiste Details-Modals sind konsistent")
        else:
            print(f"   ⚠️ VERBESSERUNG NÖTIG: Viele inkonsistente Details-Modals")
        
        # Gesamtbewertung
        overall_score = (card_consistency_rate + modal_consistency_rate) / 2
        print(f"\\n📊 GESAMTKONSISTENZ: {overall_score:.1f}%")
        
        if overall_score >= 95:
            print(f"🎉 EINHEITLICHE DARSTELLUNG PERFEKT!")
            print(f"   ✅ 'Nichts gefunden' wird konsistent verwendet")
            print(f"   ✅ Alte Platzhalter erfolgreich eliminiert")
        elif overall_score >= 80:
            print(f"✅ EINHEITLICHE DARSTELLUNG ERFOLGREICH!")
            print(f"   ✅ Deutliche Verbesserung der Konsistenz")
        else:
            print(f"⚠️ WEITERE VERBESSERUNG NÖTIG")
            print(f"   ⚠️ Inkonsistente Platzhalter-Darstellung")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_einheitliche_darstellung())