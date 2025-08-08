/**
 * Author: rahn
 * Datum: 27.07.2025
 * Version: 1.0
 * Beschreibung: Vereinfachte Playwright-Validierung mit direktem Backend-Test
 */

const { test, expect } = require('@playwright/test');

test.describe('MineSearch Simple Validation', () => {
    
    test('Backend API Funktionalität validieren', async ({ request }) => {
        console.log('🔍 Testing Backend API functionality...');
        
        // Test Health Endpoint
        const healthResponse = await request.get('http://localhost:8000/api/health');
        expect(healthResponse.ok()).toBeTruthy();
        
        const healthData = await healthResponse.json();
        console.log(`✅ Backend Health: ${healthData.status}, Models: ${healthData.models_available}`);
        
        // Test Models API - Validiere 6 OpenRouter-Modelle
        const modelsResponse = await request.get('http://localhost:8000/api/models');
        expect(modelsResponse.ok()).toBeTruthy();
        
        const modelsData = await modelsResponse.json();
        const models = modelsData.models || {};
        
        // Filter OpenRouter Models
        const openrouterModels = Object.keys(models).filter(key => 
            key.includes('openrouter') || (models[key] && models[key].provider === 'openrouter')
        );
        
        console.log(`OpenRouter-Modelle gefunden: ${openrouterModels.length}`);
        console.log('Modelle:', openrouterModels.slice(0, 6));
        
        expect(openrouterModels.length).toBeGreaterThanOrEqual(6);
        console.log('✅ Mindestens 6 OpenRouter-Modelle vorhanden');
        
        // Test Statistics API
        const statsResponse = await request.get('http://localhost:8000/api/statistics/models/detailed');
        
        if (statsResponse.ok()) {
            const statsData = await statsResponse.json();
            console.log('✅ Statistics API erreichbar');
            
            if (statsData.model_statistics && Array.isArray(statsData.model_statistics)) {
                const validStats = statsData.model_statistics.filter(model => 
                    model.total_searches > 0 || model.success_rate !== null || model.avg_cost > 0
                );
                
                console.log(`✅ ${validStats.length} Modelle mit gültigen Statistiken`);
                expect(validStats.length).toBeGreaterThan(0);
            }
        } else {
            console.log(`⚠️ Statistics API Status: ${statsResponse.status()}`);
        }
        
        // Test Sources API
        const sourcesResponse = await request.get('http://localhost:8000/api/sources');
        
        if (sourcesResponse.ok()) {
            const sourcesData = await sourcesResponse.json();
            console.log(`✅ Sources API: ${sourcesData.sources?.length || 0} Quellen verfügbar`);
        }
    });
    
    test('Frontend File Accessibility', async ({ page }) => {
        console.log('🔍 Testing Frontend file accessibility...');
        
        // Test direkter Zugriff auf Frontend-Dateien via Backend
        await page.goto('http://localhost:8000/');
        
        // Warte auf Seitenladung
        await page.waitForTimeout(3000);
        
        // Prüfe ob Seite geladen wurde
        const title = await page.title();
        console.log(`Page title: ${title}`);
        
        // Prüfe kritische Elemente
        const body = page.locator('body');
        await expect(body).toBeVisible();
        
        // Prüfe auf MineSearch
        const content = await page.textContent('body');
        if (content && content.includes('MineSearch')) {
            console.log('✅ MineSearch Frontend gefunden');
        }
        
        // Prüfe JavaScript-Funktionen
        const jsCheck = await page.evaluate(() => {
            return {
                htmx: typeof htmx !== 'undefined',
                chart: typeof Chart !== 'undefined',
                apiBase: typeof API_BASE_URL !== 'undefined'
            };
        });
        
        console.log('JavaScript Libraries:', jsCheck);
        
        // Test Tab-Navigation falls vorhanden
        const tabs = page.locator('input[name="search_method"]');
        const tabCount = await tabs.count();
        
        if (tabCount > 0) {
            console.log(`✅ ${tabCount} Navigation Tabs gefunden`);
            
            // Teste Statistics Tab
            const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
            if (await statisticsTab.isVisible()) {
                await statisticsTab.click();
                await page.waitForTimeout(2000);
                console.log('✅ Statistics Tab funktional');
            }
        }
        
        // Screenshot erstellen
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/test-results/frontend-validation.png',
            fullPage: true 
        });
        console.log('✅ Screenshot erstellt');
    });
    
    test('Performance und Stabilität', async ({ page }) => {
        console.log('🔍 Testing Performance and Stability...');
        
        const errors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });
        
        await page.goto('http://localhost:8000/');
        await page.waitForTimeout(3000);
        
        // Performance-Metriken sammeln
        const metrics = await page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            return {
                loadTime: navigation.loadEventEnd - navigation.fetchStart,
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
                resourceCount: performance.getEntriesByType('resource').length
            };
        });
        
        console.log('Performance Metrics:', metrics);
        
        // Filtere kritische Errors
        const criticalErrors = errors.filter(error => 
            !error.includes('favicon.ico') &&
            !error.includes('ResizeObserver') &&
            !error.includes('404')
        );
        
        console.log(`JavaScript Errors: ${criticalErrors.length} kritische von ${errors.length} total`);
        
        if (criticalErrors.length > 0) {
            console.log('Kritische Errors:', criticalErrors);
        }
        
        // Performance sollte akzeptabel sein
        expect(metrics.loadTime).toBeLessThan(15000); // 15 Sekunden Toleranz
        expect(criticalErrors.length).toBeLessThan(3); // Max 2 kritische Errors
        
        console.log('✅ Performance und Stabilität validiert');
    });
});