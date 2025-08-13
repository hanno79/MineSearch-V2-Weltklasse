/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Finale Validierung aller drei UI-Fixes der Tabellen-Revolution
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function finaleUIValidierung() {
    const browser = await chromium.launch({ 
        headless: false,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    console.log('🚀 FINALE UI-VALIDIERUNG STARTET...');
    
    try {
        // Phase 1: Navigation zur Anwendung
        console.log('\n📍 PHASE 1: Navigation zu http://localhost:8000');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
        
        // Warte auf das Laden der Tab-Navigation
        await page.waitForSelector('label[for="statistics-tab"]', { timeout: 10000 });
        
        // Navigation zum Statistiken Tab
        console.log('📊 Navigiere zum Statistiken Tab...');
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(3000);
        
        // Warte auf das Laden der Statistiken-Inhalte
        await page.waitForSelector('#model-statistics-table-container', { timeout: 15000 });
        await page.waitForTimeout(2000);
        
        console.log('✅ Statistiken Tab erfolgreich geladen');
        
        // Phase 2: FIX 1 Validierung - Performance-Score Lesbarkeit
        console.log('\n🎯 PHASE 2: FIX 1 - Performance-Score Lesbarkeit validieren');
        
        // Screenshot der Performance-Score Badges
        await page.screenshot({ 
            path: 'fix1_performance_scores_validation.png',
            fullPage: true
        });
        
        // Prüfe Performance-Score Badges
        const performanceBadges = await page.$$('.performance-score');
        console.log(`📊 Gefunden: ${performanceBadges.length} Performance-Score Badges`);
        
        if (performanceBadges.length > 0) {
            for (let i = 0; i < Math.min(3, performanceBadges.length); i++) {
                const badge = performanceBadges[i];
                const styles = await badge.evaluate(el => {
                    const computed = window.getComputedStyle(el);
                    return {
                        backgroundColor: computed.backgroundColor,
                        color: computed.color,
                        border: computed.border,
                        fontSize: computed.fontSize
                    };
                });
                console.log(`📈 Badge ${i+1} Styling:`, styles);
            }
        }
        
        // Phase 3: FIX 2 Validierung - Responsive Design
        console.log('\n📱 PHASE 3: FIX 2 - Responsive Design validieren');
        
        // Desktop View (bereits gesetzt)
        console.log('🖥️ Desktop View (1920x1080) Screenshot...');
        await page.screenshot({ 
            path: 'fix2_desktop_view_validation.png',
            fullPage: true
        });
        
        // Tablet View
        console.log('📱 Tablet View (768x1024) Screenshot...');
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.waitForTimeout(1000);
        await page.screenshot({ 
            path: 'fix2_tablet_view_validation.png',
            fullPage: true
        });
        
        // Mobile View
        console.log('📱 Mobile View (375x667) Screenshot...');
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        await page.screenshot({ 
            path: 'fix2_mobile_view_validation.png',
            fullPage: true
        });
        
        // Zurück zur Desktop-Ansicht
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.waitForTimeout(1000);
        
        // Phase 4: FIX 3 Validierung - Quellenangaben
        console.log('\n📝 PHASE 4: FIX 3 - Quellenangaben validieren');
        
        // Prüfe auf "Keine Quellen verfügbar" Nachrichten
        const sourceElements = await page.$$('*');
        let quellenNachrichten = [];
        
        for (const element of sourceElements) {
            const text = await element.textContent();
            if (text && text.includes('Keine Quellen verfügbar')) {
                quellenNachrichten.push(text.trim());
            }
        }
        
        console.log(`📋 Gefundene Quellenangaben: ${quellenNachrichten.length}`);
        quellenNachrichten.forEach((msg, i) => {
            console.log(`   ${i+1}. ${msg}`);
        });
        
        // Screenshot der Quellenangaben
        await page.screenshot({ 
            path: 'fix3_quellenangaben_validation.png',
            fullPage: true
        });
        
        // Phase 5: Funktionalitätsprüfung
        console.log('\n🔧 PHASE 5: Funktionalitätsprüfung');
        
        // Prüfe Details-Buttons
        const detailsButtons = await page.$$('button[onclick*="showModelDetails"]');
        console.log(`🔘 Gefundene Details-Buttons: ${detailsButtons.length}`);
        
        if (detailsButtons.length > 0) {
            console.log('🧪 Teste ersten Details-Button...');
            await detailsButtons[0].click();
            await page.waitForTimeout(2000);
            
            // Prüfe ob Modal geöffnet wurde
            const modal = await page.$('.modal, .popup, [id*="modal"], [class*="modal"]');
            if (modal) {
                console.log('✅ Modal erfolgreich geöffnet');
                await page.screenshot({ 
                    path: 'fix_validation_modal_test.png',
                    fullPage: true
                });
                
                // Modal schließen (ESC-Taste)
                await page.keyboard.press('Escape');
                await page.waitForTimeout(1000);
            } else {
                console.log('⚠️ Kein Modal gefunden');
            }
        }
        
        // Phase 6: Finale Gesamtansicht
        console.log('\n📸 PHASE 6: Finale Gesamtansicht');
        await page.screenshot({ 
            path: 'finale_ui_validierung_gesamt.png',
            fullPage: true
        });
        
        // Abschließende Analyse
        console.log('\n📊 ABSCHLIESSENDE ANALYSE:');
        
        // Prüfe Tab-System
        const tabs = await page.$$('[data-tab]');
        console.log(`📑 Verfügbare Tabs: ${tabs.length}`);
        
        // Prüfe Responsive Elemente
        const responsiveElements = await page.$$('[class*="responsive"], [class*="mobile"], [class*="tablet"]');
        console.log(`📱 Responsive Elemente: ${responsiveElements.length}`);
        
        // Prüfe Performance-Indikatoren
        const performanceElements = await page.$$('[class*="performance"], [class*="score"], [class*="badge"]');
        console.log(`⚡ Performance-Elemente: ${performanceElements.length}`);
        
        console.log('\n✅ FINALE UI-VALIDIERUNG ABGESCHLOSSEN!');
        console.log('📁 Screenshots gespeichert:');
        console.log('   - fix1_performance_scores_validation.png');
        console.log('   - fix2_desktop_view_validation.png');
        console.log('   - fix2_tablet_view_validation.png');
        console.log('   - fix2_mobile_view_validation.png');
        console.log('   - fix3_quellenangaben_validation.png');
        console.log('   - finale_ui_validierung_gesamt.png');
        
    } catch (error) {
        console.error('❌ Fehler bei der UI-Validierung:', error);
        await page.screenshot({ 
            path: 'ui_validierung_fehler.png',
            fullPage: true
        });
    } finally {
        await browser.close();
    }
}

// Test ausführen
finaleUIValidierung().catch(console.error);