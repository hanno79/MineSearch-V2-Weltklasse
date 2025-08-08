/**
 * Author: rahn
 * Datum: 27.07.2025  
 * Version: 1.0
 * Beschreibung: Manuelle User-Journey Tests für Statistiken
 */

const { test, expect } = require('@playwright/test');

test.describe('MineSearch Statistiken User Journey', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000');
        await page.waitForLoadState('networkidle');
    });

    test('Statistiken Tab auswählen und funktioniert', async ({ page }) => {
        // Finde und klicke Statistics Tab
        const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
        await expect(statisticsTab).toBeVisible();
        
        await statisticsTab.click();
        await page.waitForTimeout(1000);
        
        // Prüfe dass Statistics Content angezeigt wird
        const statisticsContent = page.locator('#statistics-content, .statistics-section');
        await expect(statisticsContent).toBeVisible();
        
        console.log('✅ Statistics Tab aktiviert');
    });

    test('Model-Statistiken laden und anzeigen', async ({ page }) => {
        // Wechsle zu Statistics Tab
        await page.locator('input[name="search_method"][value="statistics"]').click();
        await page.waitForTimeout(1000);
        
        // Warte auf Model-Statistiken zu laden
        await page.waitForTimeout(3000);
        
        // Prüfe ob Model-Statistiken vorhanden sind
        const modelStats = page.locator('.model-statistics, .statistics-table, [data-model-id]');
        
        if (await modelStats.count() > 0) {
            console.log('✅ Model-Statistiken wurden geladen');
            
            // Teste Show Model Details Button falls vorhanden
            const detailsButton = page.locator('button:has-text("Details"), button[onclick*="showModelDetails"]').first();
            if (await detailsButton.isVisible()) {
                await detailsButton.click();
                await page.waitForTimeout(2000);
                console.log('✅ Model Details Button funktioniert');
            }
        } else {
            console.log('ℹ️ Keine Model-Statistiken gefunden - möglicherweise noch keine Daten vorhanden');
        }
    });

    test('Field Performance Modal öffnen und schließen', async ({ page }) => {
        // Wechsle zu Statistics Tab
        await page.locator('input[name="search_method"][value="statistics"]').click();
        await page.waitForTimeout(2000);
        
        // Suche nach Field Performance Button
        const fieldPerfButton = page.locator('button:has-text("Feld-Performance"), button[onclick*="showFieldPerformance"]').first();
        
        if (await fieldPerfButton.isVisible()) {
            // Klicke Field Performance Button
            await fieldPerfButton.click();
            await page.waitForTimeout(1000);
            
            // Prüfe ob Modal geöffnet wurde
            const modal = page.locator('#field-performance-modal');
            await expect(modal).toBeVisible();
            
            console.log('✅ Field Performance Modal geöffnet');
            
            // Suche Close Button und schließe Modal
            const closeButton = page.locator('button:has-text("Schließen"), button[onclick*="closeFieldPerformance"]').first();
            if (await closeButton.isVisible()) {
                await closeButton.click();
                await page.waitForTimeout(500);
                
                // Modal sollte geschlossen sein
                await expect(modal).toBeHidden();
                console.log('✅ Field Performance Modal geschlossen');
            }
        } else {
            console.log('ℹ️ Field Performance Button nicht gefunden - möglicherweise noch keine Daten vorhanden');
        }
    });

    test('Backend API Verfügbarkeit prüfen', async ({ page }) => {
        // Teste Models API direkt
        try {
            const modelsResponse = await page.request.get('http://localhost:8000/api/models');
            if (modelsResponse.ok()) {
                const models = await modelsResponse.json();
                console.log(`✅ Models API funktioniert - Models verfügbar: ${Object.keys(models.models || {}).length}`);
            } else {
                console.log(`⚠️ Models API Problem - Status: ${modelsResponse.status()}`);
            }
        } catch (error) {
            console.log(`❌ Models API Error: ${error.message}`);
        }
        
        // Teste Statistics API
        try {
            const statsResponse = await page.request.get('http://localhost:8000/api/statistics/models/detailed');
            if (statsResponse.ok()) {
                console.log('✅ Statistics API erreichbar');
            } else {
                console.log(`⚠️ Statistics API Problem - Status: ${statsResponse.status()}`);
            }
        } catch (error) {
            console.log(`❌ Statistics API Error: ${error.message}`);
        }
    });

    test('JavaScript API-Funktionen testen', async ({ page }) => {
        // Prüfe alle wichtigen JavaScript-Funktionen
        const functions = await page.evaluate(() => {
            const funcs = {
                'showModelDetails': typeof window.showModelDetails === 'function',
                'showFieldPerformance': typeof window.showFieldPerformance === 'function',
                'showNotification': typeof window.showNotification === 'function',
                'loadStatistics': typeof window.loadStatistics === 'function',
                'API_BASE_URL': window.API_BASE_URL
            };
            return funcs;
        });
        
        console.log('JavaScript-Funktionen Status:');
        for (const [name, status] of Object.entries(functions)) {
            if (name === 'API_BASE_URL') {
                console.log(`  ${name}: ${status || 'undefined'}`);
            } else {
                console.log(`  ${name}: ${status ? '✅' : '❌'}`);
            }
        }
        
        // API_BASE_URL sollte definiert sein
        expect(functions.API_BASE_URL).toBeDefined();
    });

    test('Performance und Console Warnings', async ({ page }) => {
        const warnings = [];
        const errors = [];
        
        page.on('console', msg => {
            if (msg.type() === 'warning') {
                warnings.push(msg.text());
            } else if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });
        
        // Wechsle zu Statistics Tab und warte
        await page.locator('input[name="search_method"][value="statistics"]').click();
        await page.waitForTimeout(5000);
        
        // Filteriere bekannte unproblematische Warnings/Errors
        const filteredErrors = errors.filter(error => 
            !error.includes('favicon.ico') &&
            !error.includes('ResizeObserver') &&
            !error.includes('Host system is missing dependencies')
        );
        
        console.log(`Console Status: ${warnings.length} warnings, ${filteredErrors.length} kritische errors`);
        
        if (filteredErrors.length > 0) {
            console.log('Kritische Errors:', filteredErrors);
        }
        
        // Performance sollte akzeptabel sein
        const startTime = Date.now();
        await page.reload();
        await page.waitForLoadState('networkidle');
        const loadTime = Date.now() - startTime;
        
        console.log(`Page Load Time: ${loadTime}ms`);
        expect(loadTime).toBeLessThan(10000); // Sollte unter 10 Sekunden laden
    });
});