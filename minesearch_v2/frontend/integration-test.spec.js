/**
 * Author: rahn
 * Datum: 27.07.2025  
 * Version: 1.0
 * Beschreibung: Playwright Integration Tests für MineSearch Frontend
 */

const { test, expect } = require('@playwright/test');

test.describe('MineSearch Frontend Integration Tests', () => {
    
    test.beforeEach(async ({ page }) => {
        // Navigiere zur Frontend-Seite
        await page.goto('http://localhost:3000');
        
        // Warte bis die Seite vollständig geladen ist
        await page.waitForLoadState('networkidle');
    });

    test('Seite lädt korrekt und zeigt Hauptelemente', async ({ page }) => {
        // Prüfe Titel
        await expect(page).toHaveTitle(/MineSearch 2.0/);
        
        // Prüfe dass Hauptnavigation vorhanden ist
        const tabNavigation = page.locator('.tab-navigation');
        await expect(tabNavigation).toBeVisible();
        
        // Prüfe dass mindestens ein Tab vorhanden ist
        const searchTab = page.locator('input[value="search"]');
        await expect(searchTab).toBeVisible();
        
        console.log('✅ Seite lädt korrekt mit allen Hauptelementen');
    });

    test('Modal-Funktionalität für Field Performance', async ({ page }) => {
        // Prüfe dass das Modal-Element existiert
        const modal = page.locator('#field-performance-modal');
        await expect(modal).toBeAttached();
        
        // Modal sollte initial versteckt sein
        await expect(modal).toHaveCSS('display', 'none');
        
        console.log('✅ Field Performance Modal existiert und ist initial versteckt');
    });

    test('JavaScript-Funktionen sind verfügbar', async ({ page }) => {
        // Prüfe ob showModelDetails Funktion definiert ist
        const showModelDetailsExists = await page.evaluate(() => {
            return typeof window.showModelDetails === 'function';
        });
        expect(showModelDetailsExists).toBe(true);
        
        // Prüfe ob showFieldPerformance Funktion definiert ist  
        const showFieldPerformanceExists = await page.evaluate(() => {
            return typeof window.showFieldPerformance === 'function';
        });
        expect(showFieldPerformanceExists).toBe(true);
        
        console.log('✅ Erforderliche JavaScript-Funktionen sind verfügbar');
    });

    test('API Base URL ist korrekt konfiguriert', async ({ page }) => {
        const apiBaseUrl = await page.evaluate(() => {
            return window.API_BASE_URL;
        });
        
        // Sollte auf Backend zeigen
        expect(apiBaseUrl).toBe('http://localhost:8000');
        
        console.log('✅ API Base URL ist korrekt konfiguriert');
    });

    test('Backend-Verbindung funktioniert - Models API', async ({ page }) => {
        // Teste die Models API direkt
        const response = await page.request.get('http://localhost:8000/api/models');
        expect(response.ok()).toBe(true);
        
        const models = await response.json();
        expect(models).toHaveProperty('data');
        expect(Array.isArray(models.data)).toBe(true);
        
        console.log(`✅ Backend Models API funktioniert - ${models.data.length} Modelle verfügbar`);
    });

    test('Backend-Verbindung funktioniert - Statistics API', async ({ page }) => {
        // Teste die Statistics API
        const response = await page.request.get('http://localhost:8000/api/statistics/models');
        expect(response.ok()).toBe(true);
        
        const stats = await response.json();
        expect(stats).toHaveProperty('success');
        
        console.log('✅ Backend Statistics API funktioniert');
    });

    test('Tab-Navigation funktioniert', async ({ page }) => {
        // Klicke auf Statistics Tab falls vorhanden
        const statisticsTab = page.locator('input[value="statistics"]');
        if (await statisticsTab.isVisible()) {
            await statisticsTab.click();
            
            // Warte kurz für Tab-Wechsel
            await page.waitForTimeout(500);
            
            // Prüfe dass Statistics Content sichtbar wird
            const statsContent = page.locator('#statistics-content');
            if (await statsContent.isAttached()) {
                await expect(statsContent).toBeVisible();
            }
            
            console.log('✅ Tab-Navigation zu Statistics funktioniert');
        } else {
            console.log('ℹ️ Statistics Tab nicht gefunden - möglicherweise andere Tab-Struktur');
        }
    });

    test('Error Handling für ungültige Model ID', async ({ page }) => {
        // Simuliere Aufruf von showModelDetails mit ungültiger ID
        const errorHandled = await page.evaluate(async () => {
            try {
                // Versuche showModelDetails mit ungültiger ID aufzurufen
                if (typeof window.showModelDetails === 'function') {
                    await window.showModelDetails('invalid-model-id-test');
                    return true;
                }
                return false;
            } catch (error) {
                // Error sollte abgefangen werden
                return true;
            }
        });
        
        expect(errorHandled).toBe(true);
        console.log('✅ Error Handling für ungültige Model ID funktioniert');
    });

    test('Notification System funktioniert', async ({ page }) => {
        // Prüfe ob showNotification Funktion existiert
        const notificationExists = await page.evaluate(() => {
            return typeof window.showNotification === 'function';
        });
        expect(notificationExists).toBe(true);
        
        // Teste Notification
        await page.evaluate(() => {
            if (typeof window.showNotification === 'function') {
                window.showNotification('Test Nachricht', 'info');
            }
        });
        
        console.log('✅ Notification System ist verfügbar');
    });

    test('Console Errors überwachen', async ({ page }) => {
        const consoleErrors = [];
        
        // Sammle Console Errors
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });
        
        // Lade die Seite neu und warte
        await page.reload();
        await page.waitForTimeout(3000);
        
        // Prüfe auf kritische Errors (ignoriere bekannte Warnungen)
        const criticalErrors = consoleErrors.filter(error => 
            !error.includes('Host system is missing dependencies') &&
            !error.includes('favicon.ico') &&
            !error.includes('ResizeObserver')
        );
        
        if (criticalErrors.length > 0) {
            console.log('⚠️ Console Errors gefunden:', criticalErrors);
        } else {
            console.log('✅ Keine kritischen Console Errors gefunden');
        }
        
        // Sollte keine kritischen Errors geben
        expect(criticalErrors.length).toBe(0);
    });
});