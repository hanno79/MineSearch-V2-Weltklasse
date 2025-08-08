#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 26.07.2025
 * Version: 1.0
 * Beschreibung: Simuliert Browser-Test der Frontend-Console für Quellen-Tab
 */

const { chromium } = require('playwright');

async function testFrontendInBrowser() {
    console.log('🌐 Starte Browser-Test für Frontend Sources...\n');
    
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    // Console-Logs abfangen
    const consoleLogs = [];
    page.on('console', msg => {
        consoleLogs.push({
            type: msg.type(),
            text: msg.text(),
            timestamp: new Date().toISOString()
        });
    });
    
    // Errors abfangen
    const pageErrors = [];
    page.on('pageerror', error => {
        pageErrors.push({
            error: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
    });
    
    try {
        // Gehe zur Frontend-Seite
        console.log('📄 Lade Frontend-Seite...');
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        
        // Warte bis Seite geladen
        await page.waitForTimeout(2000);
        
        // Prüfe ob loadSources Funktion existiert
        const hasLoadSources = await page.evaluate(() => {
            return typeof window.loadSources === 'function';
        });
        
        console.log(`✅ loadSources Funktion verfügbar: ${hasLoadSources}`);
        
        // Prüfe ob displayGroupedSources existiert
        const hasDisplayGroupedSources = await page.evaluate(() => {
            return typeof window.displayGroupedSources === 'function';
        });
        
        console.log(`✅ displayGroupedSources Funktion verfügbar: ${hasDisplayGroupedSources}`);
        
        // Aktiviere Quellen-Tab
        console.log('\n📊 Aktiviere Quellen-Tab...');
        await page.click('#tab-sources');
        await page.waitForTimeout(1000);
        
        // Warte auf Tab-Umschaltung und loadSources-Aufruf
        await page.waitForTimeout(3000);
        
        // Prüfe aktuellen Zustand des sources-table-containers
        const containerContent = await page.evaluate(() => {
            const container = document.getElementById('sources-table-container');
            return container ? {
                innerHTML: container.innerHTML,
                hasContent: container.innerHTML.length > 50,
                textContent: container.textContent
            } : null;
        });
        
        console.log('\n📋 Container-Zustand:');
        if (containerContent) {
            console.log(`   Content Length: ${containerContent.innerHTML.length}`);
            console.log(`   Has Content: ${containerContent.hasContent}`);
            console.log(`   Text Preview: ${containerContent.textContent.substring(0, 200)}...`);
        } else {
            console.log('   ❌ Container nicht gefunden!');
        }
        
        // Prüfe Console-Logs
        console.log('\n📝 Console-Logs:');
        consoleLogs.forEach(log => {
            const symbol = log.type === 'error' ? '❌' : 
                          log.type === 'warning' ? '⚠️' : 
                          log.type === 'info' ? 'ℹ️' : '📝';
            console.log(`   ${symbol} [${log.type}] ${log.text}`);
        });
        
        // Prüfe Page-Errors
        if (pageErrors.length > 0) {
            console.log('\n💥 JavaScript-Errors:');
            pageErrors.forEach(error => {
                console.log(`   ❌ ${error.error}`);
                if (error.stack) {
                    console.log(`      Stack: ${error.stack.split('\n')[0]}`);
                }
            });
        } else {
            console.log('\n✅ Keine JavaScript-Errors gefunden');
        }
        
        // Versuche manuell loadSources aufzurufen
        console.log('\n🔧 Teste manuellen loadSources-Aufruf...');
        const manualResult = await page.evaluate(async () => {
            try {
                if (typeof window.loadSources === 'function') {
                    await window.loadSources();
                    return { success: true, message: 'loadSources aufgerufen' };
                } else {
                    return { success: false, message: 'loadSources nicht verfügbar' };
                }
            } catch (error) {
                return { success: false, message: error.message, stack: error.stack };
            }
        });
        
        console.log(`   Result: ${JSON.stringify(manualResult, null, 2)}`);
        
        // Final State Check
        await page.waitForTimeout(2000);
        const finalContainer = await page.evaluate(() => {
            const container = document.getElementById('sources-table-container');
            return container ? container.innerHTML : 'Container nicht gefunden';
        });
        
        console.log('\n🏁 Final Container State:');
        console.log(`   Length: ${finalContainer.length}`);
        console.log(`   Content: ${finalContainer.substring(0, 300)}...`);
        
    } catch (error) {
        console.error(`❌ Browser-Test-Fehler: ${error.message}`);
    } finally {
        await browser.close();
    }
}

// Prüfe ob Playwright verfügbar ist
try {
    testFrontendInBrowser();
} catch (error) {
    console.error('❌ Playwright nicht verfügbar. Teste mit cURL stattdessen...');
    
    // Fallback: Simple cURL-Test
    const http = require('http');
    const options = {
        hostname: 'localhost',
        port: 3000,
        path: '/',
        method: 'GET'
    };

    const req = http.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
            console.log('\n📄 Frontend HTML Test:');
            console.log(`   Status: ${res.statusCode}`);
            console.log(`   Has loadSources: ${data.includes('function loadSources')}`);
            console.log(`   Has displayGroupedSources: ${data.includes('function displayGroupedSources')}`);
            console.log(`   Has sources-table-container: ${data.includes('sources-table-container')}`);
        });
    });
    
    req.on('error', err => console.error(`❌ Request-Fehler: ${err.message}`));
    req.end();
}