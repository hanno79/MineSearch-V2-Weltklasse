/**
 * Author: rahn
 * Datum: 16.07.2025
 * Version: 1.0
 * Beschreibung: Schnelle API-Diagnose für MineSearch v2.1 - Minimal-Version für erste Problemerkennung
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';

test.describe('MineSearch v2.1 - Quick API Diagnosis', () => {
    let apiResults = {};

    test('Quick API Endpoint Check', async ({ page }) => {
        console.log('🔍 Schnelle API-Diagnose...');
        
        const endpoints = [
            '/api/sources/grouped',
            '/api/benchmark/summary',
            '/api/benchmark/field-statistics',
            '/api/benchmark/field-comparison',
            '/api/models'
        ];

        for (const endpoint of endpoints) {
            try {
                console.log(`Teste: ${endpoint}`);
                const response = await page.goto(`${BASE_URL}${endpoint}`);
                
                apiResults[endpoint] = {
                    status: response.status(),
                    ok: response.ok(),
                };
                
                if (response.ok()) {
                    const text = await response.text();
                    try {
                        const json = JSON.parse(text);
                        apiResults[endpoint].hasData = Object.keys(json).length > 0;
                        apiResults[endpoint].dataPreview = JSON.stringify(json).substring(0, 200);
                    } catch (e) {
                        apiResults[endpoint].hasData = text.length > 0;
                        apiResults[endpoint].dataPreview = text.substring(0, 200);
                    }
                }
                
                console.log(`  Status: ${response.status()}, OK: ${response.ok()}`);
            } catch (error) {
                console.log(`  Fehler: ${error.message}`);
                apiResults[endpoint] = { error: error.message };
            }
        }
    });

    test('Frontend Load Test', async ({ page }) => {
        console.log('🌐 Teste Frontend-Laden...');
        
        try {
            await page.goto(BASE_URL);
            console.log('  Frontend lädt erfolgreich');
            
            // Teste ob wichtige Elemente vorhanden sind
            const elements = [
                { name: 'Database Tab', selector: '#database-tab' },
                { name: 'Field Statistics Button', selector: 'button[onclick*="showFieldStatistics"]' },
                { name: 'Field Comparison Button', selector: 'button[onclick*="showFieldComparison"]' }
            ];
            
            for (const element of elements) {
                const found = await page.$(element.selector);
                console.log(`  ${element.name}: ${found ? 'Gefunden' : 'Nicht gefunden'}`);
            }
            
        } catch (error) {
            console.log(`  Frontend-Fehler: ${error.message}`);
        }
    });

    test.afterAll(async () => {
        console.log('\n📊 Schnelle Diagnose-Ergebnisse:');
        console.log('================================');
        
        for (const [endpoint, result] of Object.entries(apiResults)) {
            console.log(`\n${endpoint}:`);
            if (result.error) {
                console.log(`  ❌ Fehler: ${result.error}`);
            } else {
                console.log(`  Status: ${result.status}`);
                console.log(`  OK: ${result.ok}`);
                if (result.hasData !== undefined) {
                    console.log(`  Hat Daten: ${result.hasData}`);
                    if (result.dataPreview) {
                        console.log(`  Datenvorschau: ${result.dataPreview}...`);
                    }
                }
            }
        }
        
        console.log('\n💡 Wenn APIs "OK" sind aber keine Daten liefern, liegt das Problem in der Datenbank-Logik.');
        console.log('   Führe für detaillierte Analyse aus: ./run_investigation.sh');
    });
});