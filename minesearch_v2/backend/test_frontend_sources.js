#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 26.07.2025
 * Version: 1.0
 * Beschreibung: Test der Frontend loadSources-Funktion via Node.js
 */

const http = require('http');

// Simuliere Browser-Fetch für /api/sources/grouped
function testSourcesAPI() {
    const options = {
        hostname: 'localhost',
        port: 8000,
        path: '/api/sources/grouped?sort_by=count&order=desc&min_reliability=30',
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    };

    return new Promise((resolve, reject) => {
        const req = http.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve({
                        status: res.statusCode,
                        data: jsonData
                    });
                } catch (e) {
                    reject(new Error(`JSON Parse Error: ${e.message}`));
                }
            });
        });
        
        req.on('error', (err) => {
            reject(err);
        });
        
        req.end();
    });
}

// Teste Frontend index.html loadSources-Verfügbarkeit
function testFrontendHTML() {
    const options = {
        hostname: 'localhost',
        port: 3000,
        path: '/',
        method: 'GET'
    };

    return new Promise((resolve, reject) => {
        const req = http.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                resolve({
                    status: res.statusCode,
                    hasLoadSources: data.includes('async function loadSources'),
                    hasPlaceholderLoadSources: data.includes('function loadSources() {') && data.includes('console.log(\'Loading sources...\')'),
                    content: data.substring(0, 500) + '...'
                });
            });
        });
        
        req.on('error', (err) => {
            reject(err);
        });
        
        req.end();
    });
}

async function runTests() {
    console.log('🔍 Testing Frontend Sources Problem...\n');
    
    try {
        // Test 1: API-Funktionalität
        console.log('1. API /api/sources/grouped Test:');
        const apiResult = await testSourcesAPI();
        
        if (apiResult.status === 200 && apiResult.data.success) {
            const sources = apiResult.data.data.grouped_sources || [];
            console.log(`✅ API funktioniert: ${sources.length} Domain-Gruppen`);
            console.log(`   Total Quellen: ${apiResult.data.data.total_sources}`);
            
            if (sources.length > 0) {
                console.log(`   Beispiel: ${sources[0].domain} (${sources[0].count} Quellen)`);
            }
        } else {
            console.log(`❌ API Problem: Status ${apiResult.status}`);
            console.log(`   Response: ${JSON.stringify(apiResult.data, null, 2)}`);
        }
        
        console.log('\n2. Frontend HTML Test:');
        const frontendResult = await testFrontendHTML();
        
        if (frontendResult.status === 200) {
            console.log(`✅ Frontend erreichbar`);
            
            if (frontendResult.hasLoadSources) {
                console.log(`✅ Echte loadSources-Funktion gefunden`);
            } else if (frontendResult.hasPlaceholderLoadSources) {
                console.log(`❌ NUR PLACEHOLDER loadSources-Funktion!`);
                console.log(`   → Das ist die Ursache für "Keine Quellen"`);
            } else {
                console.log(`❌ Keine loadSources-Funktion gefunden`);
            }
        } else {
            console.log(`❌ Frontend nicht erreichbar: Status ${frontendResult.status}`);
        }
        
    } catch (error) {
        console.error(`❌ Test-Fehler: ${error.message}`);
    }
}

runTests();