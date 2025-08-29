#!/usr/bin/env python3
"""
Author: rahn
Datum: 24.08.2025
Version: 1.0
Beschreibung: Test für Statistik-Tab Fix
"""

import subprocess
import time
import sys
from pathlib import Path

def test_statistics_tab_fix():
    """
    Teste ob der Statistik-Tab Fix funktioniert
    """
    print("🔧 [STATISTICS-FIX-TEST] Testing statistics tab fix...")
    
    # Erstelle Playwright Test Script
    test_script = """
const { chromium } = require('playwright');

(async () => {
    console.log('🚀 Starting statistics tab test...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Aktiviere detailliertes Logging
    page.on('console', msg => {
        if (msg.text().includes('[STATISTICS') || msg.text().includes('[TAB-AUTOLOADER]')) {
            console.log('🔍 BROWSER LOG:', msg.text());
        }
    });
    
    page.on('pageerror', error => {
        console.error('❌ PAGE ERROR:', error.message);
    });
    
    try {
        // Lade die Seite
        console.log('📱 Loading MineSearch page...');
        await page.goto('http://localhost:8000');
        await page.waitForTimeout(2000);
        
        // Finde den Statistik-Tab Button
        console.log('🔍 Looking for statistics tab...');
        const statsTab = await page.locator('[data-tab="statistics"]').first();
        
        if (!await statsTab.isVisible()) {
            console.error('❌ Statistics tab not found!');
            await browser.close();
            process.exit(1);
        }
        
        // Klicke auf Statistik-Tab
        console.log('👆 Clicking statistics tab...');
        await statsTab.click();
        await page.waitForTimeout(3000); // Warte auf Loading
        
        // Prüfe ob Loading-Text verschwunden ist
        console.log('🔄 Checking if loading completed...');
        // Warte bis der Lade-Text verschwunden ist (max 10 Sekunden)
        try {
            await page.locator('text="Lade Modell-Statistiken..."').waitFor({ state: 'hidden', timeout: 10000 });
            console.log('✅ Loading completed!');
        } catch (e) {
            console.warn('⚠️ Loading timeout, continuing...');
        }
        
        // Prüfe ob Statistik-Cards vorhanden sind
        console.log('📊 Checking for statistics cards...');
        
        // Verschiedene Selektoren für Statistik-Cards
        const cardSelectors = [
            '[style*="grid-template-columns"]', // Grid Container
            '[style*="border-radius: 16px"]',   // Card Style
            'div:has-text("🤖")',               // Model Icon
            'div:has-text("Performance-Score")', // Performance Text
        ];
        
        let cardsFound = false;
        for (const selector of cardSelectors) {
            const cards = await page.locator(selector).count();
            if (cards > 0) {
                console.log(`✅ Found ${cards} elements with selector: ${selector}`);
                cardsFound = true;
                break;
            }
        }
        
        if (cardsFound) {
            console.log('🎉 SUCCESS: Statistics cards are displaying correctly!');
            
            // Screenshot für Verifikation
            await page.screenshot({ 
                path: 'statistics_fix_success.png', 
                fullPage: true 
            });
            console.log('📸 Screenshot saved: statistics_fix_success.png');
            
        } else {
            console.error('❌ FAILURE: No statistics cards found!');
            
            // Debug Screenshot
            await page.screenshot({ 
                path: 'statistics_fix_failure.png', 
                fullPage: true 
            });
            console.log('📸 Debug screenshot saved: statistics_fix_failure.png');
            
            // Debug: Prüfe Tab-Container Inhalt
            const tabContent = await page.locator('#model-statistics-table-container').innerHTML();
            console.log('🔍 Tab container content:', tabContent.substring(0, 500));
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        await page.screenshot({ path: 'statistics_fix_error.png', fullPage: true });
    }
    
    await browser.close();
    console.log('🏁 Test completed.');
})();
"""
    
    # Schreibe Test Script
    with open('/tmp/statistics_test.js', 'w') as f:
        f.write(test_script)
    
    # Vorab-Checks: Node.js und Playwright verfügbar?
    try:
        node_version = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        out = (node_version.stdout or node_version.stderr or '').strip()
        if out:
            print(f"🧩 Node.js gefunden: {out}")
    except FileNotFoundError:
        print("❌ Node.js nicht gefunden. Bitte installieren Sie Node.js und versuchen Sie es erneut.")
        return False
    except subprocess.TimeoutExpired:
        print("⏰ Node.js Versionsabfrage hat zu lange gedauert. Ist Node.js korrekt installiert?")
        return False

    try:
        pw_check = subprocess.run(['node', '-e', 'require("playwright")'], capture_output=True, text=True, timeout=5)
        if pw_check.returncode != 0:
            print("❌ Playwright-Paket nicht verfügbar. Installieren Sie es mit: npm install playwright")
            if pw_check.stderr:
                print("📋 [PLAYWRIGHT-STDERR]:")
                print(pw_check.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Playwright-Check hat zu lange gedauert. Prüfen Sie die Node/npm-Installation.")
        return False
    except FileNotFoundError:
        print("❌ Node.js nicht gefunden. Bitte installieren Sie Node.js.")
        return False
    except Exception as e:
        print(f"❌ Unerwarteter Fehler beim Playwright-Check: {e}")
        return False

    # Führe Test aus
    try:
        result = subprocess.run([
            'node', '/tmp/statistics_test.js'
        ], capture_output=True, text=True, timeout=30)
        
        print("📋 [TEST-OUTPUT]:")
        print(result.stdout)
        if result.stderr:
            print("📋 [TEST-STDERR]:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Test timeout!")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_statistics_tab_fix()
    sys.exit(0 if success else 1)