#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 26.07.2025
 * Version: 1.0
 * Beschreibung: Test der Tab-Aktivierung für Sources-Problem
 */

const http = require('http');

function makeRequest(path) {
    const options = {
        hostname: 'localhost',
        port: 3000,
        path: path,
        method: 'GET'
    };

    return new Promise((resolve, reject) => {
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ status: res.statusCode, data }));
        });
        req.on('error', reject);
        req.end();
    });
}

async function analyzeTabActivation() {
    console.log('🔍 Analysiere Tab-Aktivierung für Sources-Problem...\n');
    
    try {
        const result = await makeRequest('/');
        const html = result.data;
        
        console.log('📄 HTML-Struktur-Test:');
        
        // 1. Radio-Button-Struktur prüfen
        const hasMethodSources = html.includes('id="method_sources"');
        const hasSourcesForm = html.includes('id="sources_form"');
        const hasSourcesContainer = html.includes('id="sources-table-container"');
        
        console.log(`   ✅ method_sources Radio-Button: ${hasMethodSources}`);
        console.log(`   ✅ sources_form Container: ${hasSourcesForm}`);
        console.log(`   ✅ sources-table-container: ${hasSourcesContainer}`);
        
        // 2. Event-Handler prüfen
        const hasEventListener = html.includes('addEventListener(\'change\', handleTabChange)');
        const hasHandleTabChange = html.includes('function handleTabChange()');
        
        console.log('\n🔧 Event-Handler:');
        console.log(`   ✅ addEventListener für change: ${hasEventListener}`);
        console.log(`   ✅ handleTabChange Funktion: ${hasHandleTabChange}`);
        
        // 3. Switch-Case für sources prüfen
        const switchMatch = html.match(/switch\(selectedTab\)[\s\S]*?case\s+['"]sources['"][\s\S]*?break;/);
        const hasSourcesCase = !!switchMatch;
        const callsLoadSources = switchMatch ? switchMatch[0].includes('loadSources()') : false;
        
        console.log('\n🔀 Switch-Statement:');
        console.log(`   ✅ 'sources' case vorhanden: ${hasSourcesCase}`);
        console.log(`   ✅ Ruft loadSources() auf: ${callsLoadSources}`);
        
        // 4. Standard-Tab-Aktivierung prüfen
        const hasInitialTab = html.includes('sessionStorage.getItem(\'currentTab\')') || 
                             html.includes('method_csv').includes('checked');
        
        console.log('\n🎯 Standard-Tab:');
        console.log(`   ✅ Tab-Initialisierung vorhanden: ${hasInitialTab}`);
        
        // 5. Mögliche Probleme identifizieren
        console.log('\n🩺 PROBLEM-ANALYSE:');
        
        if (!hasMethodSources) {
            console.log('   ❌ KRITISCH: method_sources Radio-Button fehlt');
        } else if (!hasSourcesForm) {
            console.log('   ❌ KRITISCH: sources_form Container fehlt');
        } else if (!hasEventListener) {
            console.log('   ❌ KRITISCH: Event-Listener nicht gebunden');
        } else if (!hasHandleTabChange) {
            console.log('   ❌ KRITISCH: handleTabChange Funktion fehlt');
        } else if (!hasSourcesCase) {
            console.log('   ❌ KRITISCH: sources case im Switch fehlt');
        } else if (!callsLoadSources) {
            console.log('   ❌ KRITISCH: loadSources() wird nicht aufgerufen');
        } else {
            console.log('   ✅ STRUKTUR OK: Alle kritischen Komponenten vorhanden');
            console.log('   💡 VERMUTUNG: Tab wird nicht automatisch aktiviert oder Default-State Problem');
        }
        
        // 6. Extrahiere relevante Code-Abschnitte
        console.log('\n📝 CODE-ANALYSE:');
        
        // Event Listener Binding
        const eventListenerMatch = html.match(/document\.querySelectorAll\([^}]+addEventListener[^}]+\}/);
        if (eventListenerMatch) {
            console.log('   Event-Listener-Code gefunden:');
            console.log(`   ${eventListenerMatch[0].substring(0, 100)}...`);
        }
        
        // handleTabChange Funktion 
        const handleTabChangeMatch = html.match(/function handleTabChange\(\)[^}]+\{[\s\S]*?\n\}/);
        if (handleTabChangeMatch) {
            console.log('\n   handleTabChange-Code gefunden:');
            const codeLines = handleTabChangeMatch[0].split('\n');
            codeLines.slice(0, 10).forEach(line => {
                console.log(`   ${line.trim()}`);
            });
            if (codeLines.length > 10) console.log('   ...');
        }
        
        // 7. Mögliche Lösungsansätze
        console.log('\n💡 LÖSUNGSANSÄTZE:');
        console.log('   1. Prüfen ob Tab initial aktiviert wird (DOM-ready)');
        console.log('   2. Manuell sources-Tab aktivieren nach Seitenaufruf');
        console.log('   3. Console-Logs in Browser überprüfen');
        console.log('   4. Event-Handler-Binding zeitlich verschieben (nach DOM-ready)');
        
    } catch (error) {
        console.error(`❌ Analyse-Fehler: ${error.message}`);
    }
}

analyzeTabActivation();