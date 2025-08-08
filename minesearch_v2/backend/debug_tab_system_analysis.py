"""
Author: rahn
Datum: 07.08.2025  
Version: 1.0
Beschreibung: Spezielle Analyse des Tab-Radio-Button-Systems
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def analyze_tab_system():
    """Analysiert das Radio-Button Tab-System im Detail"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        console_logs = []
        page.on('console', lambda msg: console_logs.append({
            'type': msg.type, 'text': msg.text, 'timestamp': datetime.now().isoformat()
        }))
        
        try:
            print("🎯 ANALYSE: Radio-Button Tab-System")
            print("=" * 50)
            
            await page.goto('http://localhost:8000', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            print("\n1. 🔍 Suche alle Radio-Button Tabs")
            radio_tabs = await page.query_selector_all('input[type="radio"][name="search_method"]')
            print(f"   Gefundene Radio-Tabs: {len(radio_tabs)}")
            
            for i, radio in enumerate(radio_tabs):
                tab_id = await radio.get_attribute('id')
                tab_value = await radio.get_attribute('value')
                is_checked = await radio.is_checked()
                print(f"   Tab {i+1}: ID='{tab_id}' Value='{tab_value}' Checked={is_checked}")
            
            print("\n2. 🔍 Finde Statistics Radio Button")
            stats_radio = await page.query_selector('input[type="radio"][value="statistics"]')
            if stats_radio:
                print("✅ Statistics Radio-Button gefunden")
                is_checked = await stats_radio.is_checked()
                is_visible = await stats_radio.is_visible()
                print(f"   Checked: {is_checked}, Visible: {is_visible}")
                
                # Finde das zugehörige Label
                stats_label = await page.query_selector('label[for="method_statistics"]')
                if stats_label:
                    label_text = await stats_label.inner_text()
                    label_visible = await stats_label.is_visible()
                    print(f"   Label Text: '{label_text}', Visible: {label_visible}")
                    
                    print("\n3. 🖱️ Klick auf Statistics Label")
                    await stats_label.click()
                    await page.wait_for_timeout(2000)
                    
                    # Prüfe ob Radio Button jetzt checked ist
                    is_now_checked = await stats_radio.is_checked()
                    print(f"   Radio Button nach Klick Checked: {is_now_checked}")
                    
                    # Screenshot nach Label-Klick
                    await page.screenshot(path='debug_tab_after_label_click.png')
                    print("📸 Screenshot: debug_tab_after_label_click.png")
            
            print("\n4. 🔍 Prüfe Statistics Form")
            stats_form = await page.query_selector('#statistics_form')
            if stats_form:
                is_visible = await stats_form.is_visible()
                display_style = await stats_form.evaluate('el => getComputedStyle(el).display')
                has_active_class = await stats_form.evaluate('el => el.classList.contains("active")')
                print(f"   Statistics Form gefunden")
                print(f"   Visible: {is_visible}")  
                print(f"   Display Style: {display_style}")
                print(f"   Has 'active' class: {has_active_class}")
                
                if not has_active_class:
                    print("\n5. 🔧 Manuell 'active' Klasse hinzufügen")
                    await stats_form.evaluate('el => el.classList.add("active")')
                    await page.wait_for_timeout(1000)
                    
                    is_now_visible = await stats_form.is_visible()
                    print(f"   Nach 'active' Klasse hinzufügen - Visible: {is_now_visible}")
                    
                    # Screenshot nach Manual-Fix
                    await page.screenshot(path='debug_tab_after_manual_active.png')
                    print("📸 Screenshot: debug_tab_after_manual_active.png")
            
            print("\n6. 🔍 Prüfe JavaScript Tab-Switching Funktionen")
            # Überprüfe ob switchTab Funktion existiert
            switch_tab_exists = await page.evaluate('typeof switchTab !== "undefined"')
            print(f"   switchTab Function exists: {switch_tab_exists}")
            
            if not switch_tab_exists:
                print("   ❌ switchTab Funktion existiert NICHT!")
                print("   🔍 Suche alternative Tab-Switch-Logik...")
                
                # Suche nach Event-Listenern auf Radio-Buttons
                radio_listeners = await page.evaluate('''
                    () => {
                        const radios = document.querySelectorAll('input[type="radio"][name="search_method"]');
                        const info = [];
                        radios.forEach((radio, index) => {
                            const listeners = getEventListeners ? getEventListeners(radio) : "N/A";
                            info.push({
                                index: index,
                                id: radio.id,
                                value: radio.value,
                                hasChangeListener: !!radio.onchange,
                                listeners: listeners
                            });
                        });
                        return info;
                    }
                ''')
                print(f"   Radio-Button Event-Listener Info: {radio_listeners}")
            
            print("\n7. 🔍 Test: Manueller JavaScript Tab-Switch")
            # Versuche manuell den Tab zu aktivieren
            await page.evaluate('''
                () => {
                    const statsRadio = document.getElementById('method_statistics');
                    const statsForm = document.getElementById('statistics_form');
                    const allForms = document.querySelectorAll('.search-form');
                    
                    if (statsRadio && statsForm) {
                        // Alle Forms verstecken
                        allForms.forEach(form => {
                            form.classList.remove('active');
                        });
                        
                        // Statistics Form aktivieren
                        statsRadio.checked = true;
                        statsForm.classList.add('active');
                        
                        console.log('🔧 [MANUAL-FIX] Statistics tab manually activated');
                        return "SUCCESS";
                    }
                    return "FAILED";
                }
            ''')
            
            await page.wait_for_timeout(2000)
            
            # Screenshot nach manuellem JavaScript-Fix
            await page.screenshot(path='debug_tab_after_js_fix.png')
            print("📸 Screenshot: debug_tab_after_js_fix.png")
            
            print("\n8. 🔍 Finale Zustandsprüfung")
            final_radio_checked = await page.is_checked('#method_statistics')
            final_form_visible = await page.is_visible('#statistics_form')
            final_form_active = await page.evaluate('document.getElementById("statistics_form").classList.contains("active")')
            
            print(f"   Final - Radio Checked: {final_radio_checked}")
            print(f"   Final - Form Visible: {final_form_visible}")
            print(f"   Final - Form Active: {final_form_active}")
            
            # Jetzt teste ob Statistics-Buttons funktionieren
            if final_form_visible:
                print("\n9. 🔍 Test Statistics Buttons")
                load_stats_btn = await page.query_selector('#statistics_form button[onclick*="loadModelStatistics"]')
                if load_stats_btn:
                    btn_visible = await load_stats_btn.is_visible()
                    btn_text = await load_stats_btn.inner_text()
                    onclick_attr = await load_stats_btn.get_attribute('onclick')
                    print(f"   Load Statistics Button: Visible={btn_visible}, Text='{btn_text}', onclick='{onclick_attr}'")
                    
                    if btn_visible:
                        print("   🖱️ Klick auf Load Statistics Button")
                        await load_stats_btn.click()
                        await page.wait_for_timeout(5000)
                        
                        # Screenshot nach Button-Klick
                        await page.screenshot(path='debug_tab_after_load_stats.png')
                        print("📸 Screenshot: debug_tab_after_load_stats.png")
            
            # Zusammenfassung der Console Logs
            print(f"\n📋 Console Logs Summary: {len(console_logs)} entries")
            recent_logs = console_logs[-10:] if len(console_logs) > 10 else console_logs
            for log in recent_logs:
                print(f"   {log['type'].upper()}: {log['text']}")
            
            # Report speichern
            report = {
                'timestamp': datetime.now().isoformat(),
                'console_logs': console_logs,
                'findings': {
                    'radio_tabs_found': len(radio_tabs),
                    'stats_tab_working': final_form_active,
                    'switch_tab_function_exists': switch_tab_exists
                }
            }
            
            with open('debug_tab_system_analysis_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print("\n✅ Tab-System Analyse abgeschlossen!")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            await page.screenshot(path='debug_tab_error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_tab_system())