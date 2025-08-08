#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 26.07.2025
 * Version: 1.0
 * Beschreibung: Einfacher Test der Frontend-HTML für loadSources-Problem
 */

const http = require('http');

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
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                resolve({
                    status: res.statusCode,
                    html: data
                });
            });
        });
        
        req.on('error', err => reject(err));
        req.end();
    });
}

async function analyzeHTML() {
    console.log('🔍 Analysiere Frontend HTML für Sources-Problem...\n');
    
    try {
        const result = await testFrontendHTML();
        const html = result.html;
        
        console.log('📄 HTML-Analyse:');
        console.log(`   Status: ${result.status}`);
        console.log(`   HTML-Größe: ${html.length} Zeichen`);
        
        // Prüfe kritische Funktionen
        const hasLoadSources = html.includes('async function loadSources');
        const hasDisplayGroupedSources = html.includes('function displayGroupedSources');
        const hasSourcesContainer = html.includes('sources-table-container');
        const hasSelectSearchMethod = html.includes('function selectSearchMethod');
        
        console.log('\n🔧 JavaScript-Funktionen:');
        console.log(`   ✅ loadSources (async): ${hasLoadSources}`);
        console.log(`   ✅ displayGroupedSources: ${hasDisplayGroupedSources}`);
        console.log(`   ✅ sources-table-container: ${hasSourcesContainer}`);
        console.log(`   ✅ selectSearchMethod: ${hasSelectSearchMethod}`);
        
        // Prüfe Tab-Aktivierung
        const hasTabSources = html.includes('tab-sources');
        const hasSourcesForm = html.includes('sources-form');
        
        console.log('\n📋 HTML-Elemente:');
        console.log(`   ✅ tab-sources Element: ${hasTabSources}`);
        console.log(`   ✅ sources-form Element: ${hasSourcesForm}`);
        
        // Suche nach möglichen Problemen
        const hasPlaceholderLoadSources = html.includes('console.log(\'Loading sources...\');');
        const hasAPIBaseURL = html.includes('API_BASE_URL');
        
        console.log('\n⚠️ Potentielle Probleme:');
        console.log(`   ❌ Placeholder loadSources: ${hasPlaceholderLoadSources}`);
        console.log(`   ✅ API_BASE_URL definiert: ${hasAPIBaseURL}`);
        
        // Extrahiere selectSearchMethod für 'sources'
        const selectSearchMethodMatch = html.match(/function selectSearchMethod\([^}]+\{[\s\S]*?\}/);
        if (selectSearchMethodMatch) {
            const methodFunction = selectSearchMethodMatch[0];
            const hasSourcesCase = methodFunction.includes("case 'sources':");
            const callsLoadSources = methodFunction.includes('loadSources()');
            
            console.log('\n🔀 selectSearchMethod-Analyse:');
            console.log(`   ✅ 'sources' case vorhanden: ${hasSourcesCase}`);
            console.log(`   ✅ Ruft loadSources() auf: ${callsLoadSources}`);
            
            if (hasSourcesCase && !callsLoadSources) {
                console.log('   ❌ PROBLEM: sources-case ruft loadSources() nicht auf!');
            }
        }
        
        // Suche nach aktueller Tab-Selection-Logik
        const tabSourcesElements = html.match(/id="tab-sources"[^>]*>/g);
        console.log('\n📊 Tab-Elemente:');
        if (tabSourcesElements) {
            console.log(`   Tab-Sources gefunden: ${tabSourcesElements.length}`);
            console.log(`   Element: ${tabSourcesElements[0]}`);
        }
        
        // Final Diagnosis
        console.log('\n🩺 DIAGNOSE:');
        if (hasLoadSources && hasDisplayGroupedSources && hasSourcesContainer) {
            if (hasPlaceholderLoadSources) {
                console.log('   ❌ PROBLEM: Placeholder loadSources überschreibt echte Funktion');
            } else {
                console.log('   ✅ Alle kritischen Funktionen vorhanden');
                console.log('   💡 Problem könnte in Tab-Aktivierung oder API-Call liegen');
            }
        } else {
            console.log('   ❌ PROBLEM: Kritische Funktionen fehlen');
        }
        
    } catch (error) {
        console.error(`❌ Test-Fehler: ${error.message}`);
    }
}

analyzeHTML();