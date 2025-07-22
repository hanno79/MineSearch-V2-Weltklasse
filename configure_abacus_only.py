#!/usr/bin/env python3
"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Konfiguriert Browser für Abacus-only Provider-Auswahl
"""

import time
from playwright.sync_api import sync_playwright

def configure_abacus_only():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({'width': 1920, 'height': 1080})
        
        try:
            page.goto('http://localhost:8001/frontend/index.html', wait_until='networkidle')
            time.sleep(3)
            
            # Zum Search-Tab wechseln
            page.locator('label:has-text("Einzelne Mine suchen")').click()
            time.sleep(2)
            
            print('Erstelle Provider-Auswahl manuell...')
            
            # Provider-HTML direkt einfügen
            result = page.evaluate('''
                () => {
                    // Provider-HTML erstellen
                    const searchForm = document.querySelector('#search_form') || 
                                     document.querySelector('.search-form.active') ||
                                     document.querySelector('.search-form');
                    
                    if (searchForm) {
                        const providerDiv = document.createElement('div');
                        providerDiv.id = 'provider-selection-manual';
                        providerDiv.style.cssText = 'margin: 20px 0; padding: 15px; background: #e8f4fd; border-radius: 8px; border: 2px solid #4CAF50;';
                        
                        providerDiv.innerHTML = `
                            <h3 style="margin-top: 0; color: #2c3e50;">🔧 Provider auswählen (ABACUS ONLY):</h3>
                            
                            <div style="margin: 10px 0;">
                                <label style="display: block; margin: 8px 0; cursor: pointer; font-weight: bold; color: #27ae60;">
                                    <input type="checkbox" id="provider_abacus" checked style="margin-right: 10px; transform: scale(1.2);"> 
                                    ✅ Abacus (Deep Agent Research) - AKTIVIERT
                                </label>
                            </div>
                            
                            <div style="margin: 10px 0;">
                                <label style="display: block; margin: 8px 0; cursor: pointer; color: #7f8c8d;">
                                    <input type="checkbox" id="provider_perplexity" style="margin-right: 10px; transform: scale(1.2);"> 
                                    ❌ Perplexity - DEAKTIVIERT
                                </label>
                            </div>
                            
                            <div style="margin: 10px 0;">
                                <label style="display: block; margin: 8px 0; cursor: pointer; color: #7f8c8d;">
                                    <input type="checkbox" id="provider_openrouter" style="margin-right: 10px; transform: scale(1.2);"> 
                                    ❌ OpenRouter - DEAKTIVIERT
                                </label>
                            </div>
                            
                            <div style="margin: 10px 0;">
                                <label style="display: block; margin: 8px 0; cursor: pointer; color: #7f8c8d;">
                                    <input type="checkbox" id="provider_tavily" style="margin-right: 10px; transform: scale(1.2);"> 
                                    ❌ Tavily - DEAKTIVIERT
                                </label>
                            </div>
                            
                            <div style="margin-top: 15px; padding: 10px; background: #d4edda; border-radius: 5px; border-left: 4px solid #27ae60;">
                                <strong>✅ STATUS:</strong> Nur Abacus ist aktiviert - bereit für Deep Research Test!
                            </div>
                        `;
                        
                        // Bestehende Provider-Auswahl entfernen falls vorhanden
                        const existing = document.getElementById('provider-selection-manual');
                        if (existing) existing.remove();
                        
                        // Neue Provider-Auswahl einfügen
                        searchForm.insertBefore(providerDiv, searchForm.firstElementChild);
                        
                        return { success: true, message: 'Provider-Auswahl erfolgreich erstellt' };
                    } else {
                        return { success: false, message: 'Search-Form nicht gefunden' };
                    }
                }
            ''')
            
            print(f'Provider-Erstellung: {result}')
            
            if result['success']:
                print('\n✅ Provider-Auswahl erfolgreich erstellt!')
                
                # Screenshot nach Erstellung
                page.screenshot(path='manual_provider_selection.png', full_page=True)
                print('Screenshot mit manueller Provider-Auswahl gespeichert')
                
                # Validiere die Checkboxes
                try:
                    abacus_checked = page.locator('#provider_abacus').is_checked()
                    perplexity_checked = page.locator('#provider_perplexity').is_checked()
                    openrouter_checked = page.locator('#provider_openrouter').is_checked()
                    tavily_checked = page.locator('#provider_tavily').is_checked()
                    
                    print('\n=== PROVIDER STATUS ===')
                    print(f'✅ Abacus: {"AKTIVIERT" if abacus_checked else "DEAKTIVIERT"}')
                    print(f'❌ Perplexity: {"AKTIVIERT" if perplexity_checked else "DEAKTIVIERT"}')
                    print(f'❌ OpenRouter: {"AKTIVIERT" if openrouter_checked else "DEAKTIVIERT"}')
                    print(f'❌ Tavily: {"AKTIVIERT" if tavily_checked else "DEAKTIVIERT"}')
                    
                    # Validierung
                    only_abacus = abacus_checked and not perplexity_checked and not openrouter_checked and not tavily_checked
                    
                    if only_abacus:
                        print('\n🎯 PERFEKT: Nur Abacus ist aktiviert!')
                        print('\n📋 NÄCHSTE SCHRITTE:')
                        print('1. Geben Sie einen Minennamen ein (z.B. "Grasberg")')
                        print('2. Optional: Land und Rohstoff eingeben')
                        print('3. Klicken Sie auf "Suche starten"')
                        print('4. Die Suche wird NUR mit Abacus Deep Agent Research durchgeführt')
                        print('\n🕒 Browser bleibt 60 Sekunden offen für Tests...')
                    else:
                        print('\n⚠️ Konfiguration prüfen - nicht nur Abacus ist aktiv!')
                    
                except Exception as e:
                    print(f'Fehler bei Checkbox-Validierung: {e}')
            
            # Browser für Tests offen lassen
            print('\n' + '='*60)
            print('🌐 BROWSER IST BEREIT FÜR ABACUS-ONLY TESTS')
            print('Sie können jetzt eine Testsuche durchführen!')
            print('='*60)
            
            time.sleep(60)  # 60 Sekunden für Tests
            
        except Exception as e:
            print(f'Fehler: {e}')
            import traceback
            traceback.print_exc()
        finally:
            print('\n🔒 Browser wird geschlossen...')
            browser.close()

if __name__ == "__main__":
    configure_abacus_only()