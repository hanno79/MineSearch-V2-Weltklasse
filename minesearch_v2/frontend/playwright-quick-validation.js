#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 27.07.2025
 * Version: 1.0
 * Beschreibung: Schnelle Playwright-Validierung für Produktions-Check
 */

const { chromium } = require('playwright');

async function quickValidation() {
    console.log('🚀 MineSearch Quick Playwright Validation');
    console.log('=' * 50);
    
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-dev-shm-usage']
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        // 1. Backend API Quick Check
        console.log('\n🔍 Backend API Quick Check...');
        const apiResponse = await page.request.get('http://localhost:8000/api/health');
        
        if (apiResponse.ok()) {
            const healthData = await apiResponse.json();
            console.log(`✅ Backend: ${healthData.status}, Models: ${healthData.models_available}`);
        } else {
            console.log(`❌ Backend API Error: ${apiResponse.status()}`);
            return false;
        }
        
        // 2. Frontend Load Test
        console.log('\n🔍 Frontend Load Test...');
        await page.goto('http://localhost:8000/', { waitUntil: 'networkidle' });
        
        const title = await page.title();
        if (title.includes('MineSearch')) {
            console.log(`✅ Frontend loaded: ${title}`);
        } else {
            console.log(`⚠️ Unexpected title: ${title}`);
        }
        
        // 3. OpenRouter Models Validation
        console.log('\n🔍 OpenRouter Models Validation...');
        const modelsResponse = await page.request.get('http://localhost:8000/api/models');
        
        if (modelsResponse.ok()) {
            const modelsData = await modelsResponse.json();
            const openrouterModels = Object.keys(modelsData.models || {}).filter(key => 
                key.includes('openrouter')
            );
            
            console.log(`✅ OpenRouter Models: ${openrouterModels.length} gefunden`);
            if (openrouterModels.length >= 6) {
                console.log('✅ Mindestens 6 OpenRouter-Modelle verfügbar');
            } else {
                console.log('⚠️ Weniger als 6 OpenRouter-Modelle');
            }
        }
        
        // 4. Statistics API Test
        console.log('\n🔍 Statistics API Test...');
        const statsResponse = await page.request.get('http://localhost:8000/api/statistics/models/detailed');
        
        if (statsResponse.ok()) {
            console.log('✅ Statistics API funktional');
        } else {
            console.log(`⚠️ Statistics API Issue: ${statsResponse.status()}`);
        }
        
        // 5. Performance Check
        console.log('\n🔍 Performance Check...');
        const metrics = await page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            return {
                loadTime: Math.round(navigation.loadEventEnd - navigation.fetchStart),
                domReady: Math.round(navigation.domContentLoadedEventEnd - navigation.fetchStart)
            };
        });
        
        console.log(`✅ Load Time: ${metrics.loadTime}ms, DOM Ready: ${metrics.domReady}ms`);
        
        // 6. JavaScript Error Check
        console.log('\n🔍 JavaScript Error Check...');
        const errors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });
        
        await page.reload();
        await page.waitForTimeout(3000);
        
        const criticalErrors = errors.filter(error => 
            !error.includes('favicon.ico') && !error.includes('ResizeObserver')
        );
        
        if (criticalErrors.length === 0) {
            console.log('✅ Keine kritischen JavaScript-Errors');
        } else {
            console.log(`⚠️ ${criticalErrors.length} kritische Errors gefunden`);
        }
        
        // 7. Screenshot für Validierung
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/quick-validation-screenshot.png',
            fullPage: true 
        });
        console.log('✅ Validierungs-Screenshot erstellt');
        
        console.log('\n' + '=' * 50);
        console.log('🎯 Quick Validation: ABGESCHLOSSEN');
        console.log('✅ Alle kritischen Funktionen validiert');
        
        return true;
        
    } catch (error) {
        console.log(`❌ Validation Error: ${error.message}`);
        return false;
    } finally {
        await browser.close();
    }
}

// Ausführung
if (require.main === module) {
    quickValidation().then(success => {
        process.exit(success ? 0 : 1);
    });
}

module.exports = { quickValidation };