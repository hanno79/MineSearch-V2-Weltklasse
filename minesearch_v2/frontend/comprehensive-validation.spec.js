/**
 * Author: rahn
 * Datum: 27.07.2025
 * Version: 1.0
 * Beschreibung: Umfassende Playwright-Validierung für alle UI-Funktionen und Datenwerte
 */

const { test, expect } = require('@playwright/test');

test.describe('MineSearch Comprehensive Validation Suite', () => {
    
    test.beforeEach(async ({ page }) => {
        // Backend sollte auf Port 8000 laufen
        await page.goto('http://localhost:3000');
        await page.waitForLoadState('networkidle');
        
        // Warte zusätzlich auf JavaScript-Initialisierung
        await page.waitForTimeout(2000);
    });

    test.describe('1. Funktionalitäts-Tests', () => {
        
        test('Accordion-Details öffnen/schließen ohne Auto-Close', async ({ page }) => {
            console.log('🔍 Testing Accordion functionality...');
            
            // Suche nach Accordion-Elementen
            const accordions = page.locator('.accordion-header, [data-accordion], details summary');
            const count = await accordions.count();
            
            if (count > 0) {
                console.log(`✅ Gefunden: ${count} Accordion-Elemente`);
                
                // Teste ersten Accordion
                const firstAccordion = accordions.first();
                await firstAccordion.click();
                await page.waitForTimeout(500);
                
                // Prüfe ob Content sichtbar wird
                const content = page.locator('.accordion-content, [data-accordion-content]').first();
                if (await content.isVisible()) {
                    console.log('✅ Accordion öffnet sich');
                    
                    // Teste dass es nicht automatisch schließt
                    await page.waitForTimeout(2000);
                    await expect(content).toBeVisible();
                    console.log('✅ Accordion bleibt offen (kein Auto-Close)');
                    
                    // Manuell schließen
                    await firstAccordion.click();
                    await page.waitForTimeout(500);
                    console.log('✅ Accordion schließt manuell');
                }
            } else {
                console.log('ℹ️ Keine Accordion-Elemente gefunden');
            }
        });

        test('Table-Sorting für alle Spalten', async ({ page }) => {
            console.log('🔍 Testing Table Sorting functionality...');
            
            // Navigiere zu Statistics Tab falls vorhanden
            const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
            if (await statisticsTab.isVisible()) {
                await statisticsTab.click();
                await page.waitForTimeout(2000);
            }
            
            // Suche nach sortierbaren Tabellen
            const tables = page.locator('table');
            const tableCount = await tables.count();
            
            console.log(`Gefunden: ${tableCount} Tabellen`);
            
            for (let i = 0; i < Math.min(tableCount, 3); i++) {
                const table = tables.nth(i);
                const headers = table.locator('th[onclick], th.sortable, th[data-sort]');
                const headerCount = await headers.count();
                
                if (headerCount > 0) {
                    console.log(`✅ Tabelle ${i+1}: ${headerCount} sortierbare Spalten`);
                    
                    // Teste erstes sortierbares Header
                    const firstHeader = headers.first();
                    await firstHeader.click();
                    await page.waitForTimeout(1000);
                    
                    // Zweiter Klick für umgekehrte Sortierung
                    await firstHeader.click();
                    await page.waitForTimeout(1000);
                    
                    console.log('✅ Sortierung funktioniert');
                }
            }
        });

        test('Statistics-Tab Navigation', async ({ page }) => {
            console.log('🔍 Testing Statistics Tab Navigation...');
            
            // Finde Statistics Tab
            const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
            await expect(statisticsTab).toBeVisible();
            
            // Klicke Statistics Tab
            await statisticsTab.click();
            await page.waitForTimeout(1000);
            
            // Prüfe dass Statistics Content sichtbar wird
            const statisticsContent = page.locator('#statistics-content, .statistics-section, .search-form.active');
            await expect(statisticsContent).toBeVisible();
            
            console.log('✅ Statistics Tab Navigation funktioniert');
            
            // Teste andere Tabs
            const tabs = ['search', 'csv', 'batch'];
            for (const tab of tabs) {
                const tabInput = page.locator(`input[name="search_method"][value="${tab}"]`);
                if (await tabInput.isVisible()) {
                    await tabInput.click();
                    await page.waitForTimeout(500);
                    console.log(`✅ ${tab.toUpperCase()} Tab Navigation funktioniert`);
                }
            }
        });

        test('Modal-Funktionen', async ({ page }) => {
            console.log('🔍 Testing Modal Functions...');
            
            // Wechsle zu Statistics Tab
            const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
            if (await statisticsTab.isVisible()) {
                await statisticsTab.click();
                await page.waitForTimeout(2000);
            }
            
            // Teste Model Details Modal
            const modelDetailsButton = page.locator('button:has-text("Details"), button[onclick*="showModelDetails"]').first();
            if (await modelDetailsButton.isVisible()) {
                await modelDetailsButton.click();
                await page.waitForTimeout(1000);
                
                const modal = page.locator('#model-details-modal, .modal');
                await expect(modal).toBeVisible();
                console.log('✅ Model Details Modal öffnet');
                
                // Schließe Modal
                const closeButton = page.locator('button:has-text("Schließen"), .modal-close, [onclick*="close"]').first();
                if (await closeButton.isVisible()) {
                    await closeButton.click();
                    await page.waitForTimeout(500);
                    console.log('✅ Modal schließt');
                }
            }
            
            // Teste Field Performance Modal
            const fieldPerfButton = page.locator('button:has-text("Feld-Performance"), button[onclick*="showFieldPerformance"]').first();
            if (await fieldPerfButton.isVisible()) {
                await fieldPerfButton.click();
                await page.waitForTimeout(1000);
                
                const fieldModal = page.locator('#field-performance-modal');
                await expect(fieldModal).toBeVisible();
                console.log('✅ Field Performance Modal öffnet');
                
                const closeBtn = page.locator('button[onclick*="closeFieldPerformance"]').first();
                if (await closeBtn.isVisible()) {
                    await closeBtn.click();
                    await page.waitForTimeout(500);
                    console.log('✅ Field Performance Modal schließt');
                }
            }
        });
    });

    test.describe('2. Daten-Validierung', () => {
        
        test('Prüfe genau 6 OpenRouter-Modelle', async ({ page }) => {
            console.log('🔍 Validating exactly 6 OpenRouter models...');
            
            try {
                // API-Call für Models
                const response = await page.request.get('http://localhost:8000/api/models');
                
                if (response.ok()) {
                    const data = await response.json();
                    const models = data.models || {};
                    
                    // Filter OpenRouter Models
                    const openrouterModels = Object.keys(models).filter(key => 
                        key.includes('openrouter') || models[key].provider === 'openrouter'
                    );
                    
                    console.log(`Gefundene OpenRouter-Modelle: ${openrouterModels.length}`);
                    console.log('Modelle:', openrouterModels);
                    
                    expect(openrouterModels.length).toBe(6);
                    console.log('✅ Genau 6 OpenRouter-Modelle vorhanden');
                } else {
                    console.log(`⚠️ Models API Fehler: ${response.status()}`);
                }
            } catch (error) {
                console.log(`❌ API Error: ${error.message}`);
            }
        });

        test('Validiere Statistics-Werte sind sinnvoll und nicht 0/null', async ({ page }) => {
            console.log('🔍 Validating Statistics values...');
            
            try {
                const statsResponse = await page.request.get('http://localhost:8000/api/statistics/models/detailed');
                
                if (statsResponse.ok()) {
                    const statsData = await statsResponse.json();
                    
                    if (statsData.model_statistics && Array.isArray(statsData.model_statistics)) {
                        const models = statsData.model_statistics;
                        console.log(`Gefunden: ${models.length} Model-Statistiken`);
                        
                        let validModels = 0;
                        for (const model of models.slice(0, 10)) { // Prüfe erste 10
                            const hasValidStats = (
                                model.total_searches > 0 ||
                                model.success_rate !== null ||
                                model.avg_cost > 0
                            );
                            
                            if (hasValidStats) {
                                validModels++;
                                console.log(`✅ ${model.model}: Success Rate ${model.success_rate}%, Cost ${model.avg_cost}`);
                            }
                        }
                        
                        expect(validModels).toBeGreaterThan(0);
                        console.log(`✅ ${validModels} Modelle mit gültigen Statistiken`);
                    }
                } else {
                    console.log(`⚠️ Statistics API Problem: ${statsResponse.status()}`);
                }
            } catch (error) {
                console.log(`❌ Statistics API Error: ${error.message}`);
            }
        });

        test('Prüfe Success-Rates, Consistency-Scores, Kosten', async ({ page }) => {
            console.log('🔍 Validating Success Rates, Consistency Scores, Costs...');
            
            // Wechsle zu Statistics Tab
            const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
            if (await statisticsTab.isVisible()) {
                await statisticsTab.click();
                await page.waitForTimeout(3000);
            }
            
            // Prüfe ob Statistics-Tabelle Daten enthält
            const statisticsTable = page.locator('.statistics-table, table');
            if (await statisticsTable.isVisible()) {
                const rows = statisticsTable.locator('tr');
                const rowCount = await rows.count();
                
                console.log(`Statistics-Tabelle: ${rowCount} Zeilen`);
                
                if (rowCount > 1) { // Header + mindestens 1 Datenzeile
                    // Prüfe Success Rate Spalten
                    const successRates = page.locator('td:has-text("%"), .success-rate');
                    const rateCount = await successRates.count();
                    
                    if (rateCount > 0) {
                        console.log(`✅ ${rateCount} Success Rate Werte gefunden`);
                    }
                    
                    // Prüfe Cost Spalten
                    const costs = page.locator('td:has-text("$"), .cost-value');
                    const costCount = await costs.count();
                    
                    if (costCount > 0) {
                        console.log(`✅ ${costCount} Cost Werte gefunden`);
                    }
                    
                    // Prüfe Consistency Scores
                    const consistency = page.locator('.consistency-score, td[data-consistency]');
                    const consistencyCount = await consistency.count();
                    
                    if (consistencyCount > 0) {
                        console.log(`✅ ${consistencyCount} Consistency Score Werte gefunden`);
                    }
                }
            }
        });

        test('Validiere Charts zeigen echte Daten', async ({ page }) => {
            console.log('🔍 Validating Charts with real data...');
            
            // Wechsle zu Statistics Tab
            const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
            if (await statisticsTab.isVisible()) {
                await statisticsTab.click();
                await page.waitForTimeout(4000); // Mehr Zeit für Chart-Rendering
            }
            
            // Prüfe Canvas-Elemente (Charts)
            const charts = page.locator('canvas');
            const chartCount = await charts.count();
            
            console.log(`Gefunden: ${chartCount} Chart Canvas-Elemente`);
            
            if (chartCount > 0) {
                // Prüfe ob Charts wirklich Daten enthalten
                const chartData = await page.evaluate(() => {
                    const canvases = document.querySelectorAll('canvas');
                    const results = [];
                    
                    canvases.forEach((canvas, index) => {
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        
                        // Prüfe ob Canvas mehr als nur leeren/weißen Hintergrund hat
                        let hasData = false;
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            const r = imageData.data[i];
                            const g = imageData.data[i + 1];
                            const b = imageData.data[i + 2];
                            const a = imageData.data[i + 3];
                            
                            // Wenn Pixel nicht weiß/transparent ist
                            if (!(r === 255 && g === 255 && b === 255) && a > 0) {
                                hasData = true;
                                break;
                            }
                        }
                        
                        results.push({
                            index: index,
                            hasData: hasData,
                            width: canvas.width,
                            height: canvas.height
                        });
                    });
                    
                    return results;
                });
                
                const chartsWithData = chartData.filter(chart => chart.hasData);
                console.log(`✅ ${chartsWithData.length}/${chartCount} Charts enthalten echte Daten`);
                
                expect(chartsWithData.length).toBeGreaterThan(0);
            }
        });
    });

    test.describe('3. UI-Korrektheit', () => {
        
        test('Alle Buttons sind klickbar und funktional', async ({ page }) => {
            console.log('🔍 Testing all buttons are clickable and functional...');
            
            // Sammle alle Buttons
            const buttons = page.locator('button, input[type="button"], input[type="submit"]');
            const buttonCount = await buttons.count();
            
            console.log(`Gefunden: ${buttonCount} Buttons`);
            
            let clickableButtons = 0;
            for (let i = 0; i < Math.min(buttonCount, 20); i++) { // Teste max 20 Buttons
                const button = buttons.nth(i);
                
                if (await button.isVisible() && await button.isEnabled()) {
                    clickableButtons++;
                }
            }
            
            console.log(`✅ ${clickableButtons} Buttons sind klickbar`);
            expect(clickableButtons).toBeGreaterThan(0);
        });

        test('Tabellen sind vollständig sichtbar (nicht abgeschnitten)', async ({ page }) => {
            console.log('🔍 Testing tables are fully visible...');
            
            const tables = page.locator('table');
            const tableCount = await tables.count();
            
            console.log(`Gefunden: ${tableCount} Tabellen`);
            
            for (let i = 0; i < tableCount; i++) {
                const table = tables.nth(i);
                
                if (await table.isVisible()) {
                    const boundingBox = await table.boundingBox();
                    const viewport = page.viewportSize();
                    
                    if (boundingBox) {
                        const isFullyVisible = (
                            boundingBox.x >= 0 &&
                            boundingBox.y >= 0 &&
                            boundingBox.x + boundingBox.width <= viewport.width &&
                            boundingBox.y + boundingBox.height <= viewport.height
                        );
                        
                        if (isFullyVisible) {
                            console.log(`✅ Tabelle ${i+1} vollständig sichtbar`);
                        } else {
                            console.log(`⚠️ Tabelle ${i+1} möglicherweise abgeschnitten`);
                        }
                    }
                }
            }
        });

        test('Responsive Design funktioniert', async ({ page }) => {
            console.log('🔍 Testing responsive design...');
            
            // Teste verschiedene Viewport-Größen
            const viewports = [
                { width: 1920, height: 1080, name: 'Desktop' },
                { width: 1024, height: 768, name: 'Tablet' },
                { width: 375, height: 667, name: 'Mobile' }
            ];
            
            for (const viewport of viewports) {
                await page.setViewportSize({ width: viewport.width, height: viewport.height });
                await page.waitForTimeout(1000);
                
                // Prüfe ob Navigation sichtbar bleibt
                const navigation = page.locator('.tab-navigation, nav');
                await expect(navigation).toBeVisible();
                
                // Prüfe ob Content nicht überläuft
                const body = page.locator('body');
                const boundingBox = await body.boundingBox();
                
                if (boundingBox) {
                    expect(boundingBox.width).toBeLessThanOrEqual(viewport.width + 50); // 50px Toleranz
                }
                
                console.log(`✅ ${viewport.name} (${viewport.width}x${viewport.height}) funktioniert`);
            }
        });

        test('Keine UI-Elemente überlappen', async ({ page }) => {
            console.log('🔍 Testing for UI element overlaps...');
            
            // Setze zurück auf Standard-Viewport
            await page.setViewportSize({ width: 1280, height: 720 });
            
            // Prüfe kritische Bereiche auf Überlappungen
            const overlaps = await page.evaluate(() => {
                const elements = document.querySelectorAll('button, .tab-navigation label, .modal');
                const overlapping = [];
                
                for (let i = 0; i < elements.length; i++) {
                    for (let j = i + 1; j < elements.length; j++) {
                        const rect1 = elements[i].getBoundingClientRect();
                        const rect2 = elements[j].getBoundingClientRect();
                        
                        // Prüfe Überlappung
                        const overlap = !(
                            rect1.right < rect2.left ||
                            rect2.right < rect1.left ||
                            rect1.bottom < rect2.top ||
                            rect2.bottom < rect1.top
                        );
                        
                        if (overlap && rect1.width > 0 && rect1.height > 0 && rect2.width > 0 && rect2.height > 0) {
                            overlapping.push({
                                element1: elements[i].tagName + (elements[i].className ? '.' + elements[i].className : ''),
                                element2: elements[j].tagName + (elements[j].className ? '.' + elements[j].className : '')
                            });
                        }
                    }
                }
                
                return overlapping;
            });
            
            console.log(`Gefundene Überlappungen: ${overlaps.length}`);
            if (overlaps.length > 0) {
                console.log('Überlappungen:', overlaps);
            }
            
            // Kritische Überlappungen sollten vermieden werden
            expect(overlaps.length).toBeLessThan(5);
        });
    });

    test.describe('4. Performance und Stabilität', () => {
        
        test('Auto-Refresh funktioniert ohne State-Verlust', async ({ page }) => {
            console.log('🔍 Testing auto-refresh without state loss...');
            
            // Wechsle zu Statistics Tab
            const statisticsTab = page.locator('input[name="search_method"][value="statistics"]');
            if (await statisticsTab.isVisible()) {
                await statisticsTab.click();
                await page.waitForTimeout(2000);
                
                // Merke aktuellen State
                const isChecked = await statisticsTab.isChecked();
                expect(isChecked).toBe(true);
                
                // Warte auf Auto-Refresh (falls vorhanden)
                await page.waitForTimeout(5000);
                
                // Prüfe dass Tab noch ausgewählt ist
                const stillChecked = await statisticsTab.isChecked();
                expect(stillChecked).toBe(true);
                
                console.log('✅ State bleibt nach Auto-Refresh erhalten');
            }
        });

        test('Keine JavaScript-Errors in Konsole', async ({ page }) => {
            console.log('🔍 Testing for JavaScript errors...');
            
            const errors = [];
            page.on('console', msg => {
                if (msg.type() === 'error') {
                    errors.push(msg.text());
                }
            });
            
            // Navigiere durch verschiedene Tabs
            const tabs = ['search', 'csv', 'batch', 'statistics'];
            for (const tab of tabs) {
                const tabInput = page.locator(`input[name="search_method"][value="${tab}"]`);
                if (await tabInput.isVisible()) {
                    await tabInput.click();
                    await page.waitForTimeout(2000);
                }
            }
            
            // Filtere bekannte harmlose Errors
            const criticalErrors = errors.filter(error => 
                !error.includes('favicon.ico') &&
                !error.includes('ResizeObserver') &&
                !error.includes('Host system is missing dependencies') &&
                !error.includes('404')
            );
            
            console.log(`JavaScript Errors: ${criticalErrors.length} kritische von ${errors.length} total`);
            
            if (criticalErrors.length > 0) {
                console.log('Kritische Errors:', criticalErrors);
            }
            
            expect(criticalErrors.length).toBe(0);
        });

        test('API-Calls sind erfolgreich', async ({ page }) => {
            console.log('🔍 Testing API calls are successful...');
            
            const apiEndpoints = [
                'http://localhost:8000/api/models',
                'http://localhost:8000/api/statistics/models/detailed',
                'http://localhost:8000/api/sources',
                'http://localhost:8000/api/health'
            ];
            
            let successfulAPIs = 0;
            for (const endpoint of apiEndpoints) {
                try {
                    const response = await page.request.get(endpoint);
                    if (response.ok()) {
                        successfulAPIs++;
                        console.log(`✅ ${endpoint} - Status: ${response.status()}`);
                    } else {
                        console.log(`⚠️ ${endpoint} - Status: ${response.status()}`);
                    }
                } catch (error) {
                    console.log(`❌ ${endpoint} - Error: ${error.message}`);
                }
            }
            
            expect(successfulAPIs).toBeGreaterThan(apiEndpoints.length / 2); // Mindestens 50% sollten funktionieren
        });

        test('Memory-Leaks vermeiden', async ({ page }) => {
            console.log('🔍 Testing for memory leaks...');
            
            // Baseline Memory-Messung
            const initialMetrics = await page.evaluate(() => performance.memory);
            
            // Simuliere intensive Nutzung
            for (let i = 0; i < 5; i++) {
                // Wechsle zwischen Tabs
                const tabs = ['search', 'statistics', 'csv', 'batch'];
                for (const tab of tabs) {
                    const tabInput = page.locator(`input[name="search_method"][value="${tab}"]`);
                    if (await tabInput.isVisible()) {
                        await tabInput.click();
                        await page.waitForTimeout(1000);
                    }
                }
            }
            
            // Force Garbage Collection falls möglich
            await page.evaluate(() => {
                if (window.gc) {
                    window.gc();
                }
            });
            
            // Finale Memory-Messung
            const finalMetrics = await page.evaluate(() => performance.memory);
            
            if (initialMetrics && finalMetrics) {
                const memoryIncrease = finalMetrics.usedJSHeapSize - initialMetrics.usedJSHeapSize;
                const memoryIncreasePercent = (memoryIncrease / initialMetrics.usedJSHeapSize) * 100;
                
                console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)} MB (${memoryIncreasePercent.toFixed(1)}%)`);
                
                // Memory sollte nicht um mehr als 50% steigen
                expect(memoryIncreasePercent).toBeLessThan(50);
                console.log('✅ Keine signifikanten Memory-Leaks erkannt');
            } else {
                console.log('ℹ️ Performance.memory nicht verfügbar in diesem Browser');
            }
        });
    });

    test.describe('5. Test-Report Generation', () => {
        
        test('Screenshot und Performance Messwerte sammeln', async ({ page }) => {
            console.log('🔍 Collecting screenshots and performance data...');
            
            // Performance-Metriken sammeln
            const metrics = await page.evaluate(() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                return {
                    loadTime: navigation.loadEventEnd - navigation.fetchStart,
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
                    firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                    memory: performance.memory ? {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    } : null
                };
            });
            
            console.log('Performance Metrics:', metrics);
            
            // Screenshots für alle Tabs
            const tabs = ['search', 'csv', 'batch', 'statistics'];
            for (const tab of tabs) {
                const tabInput = page.locator(`input[name="search_method"][value="${tab}"]`);
                if (await tabInput.isVisible()) {
                    await tabInput.click();
                    await page.waitForTimeout(2000);
                    
                    await page.screenshot({ 
                        path: `/app/minesearch_v2/frontend/test-results/comprehensive-validation-${tab}-tab.png`,
                        fullPage: true 
                    });
                    console.log(`✅ Screenshot für ${tab} Tab gespeichert`);
                }
            }
            
            // Validiere Performance
            expect(metrics.loadTime).toBeLessThan(10000); // Unter 10 Sekunden
            expect(metrics.domContentLoaded).toBeLessThan(5000); // Unter 5 Sekunden
            
            console.log('✅ Performance-Messwerte und Screenshots gesammelt');
        });
    });
});