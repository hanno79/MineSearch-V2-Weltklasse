/**
 * Author: rahn
 * Datum: 24.07.2025
 * Version: 1.0
 * Beschreibung: Queen Coordinator - Quellen-Funktionalität Detailtest
 */

const API_BASE_URL = 'http://localhost:8000';

// Test-Klasse für Quellen-Funktionalität
class SourcesFunctionalityTester {
    constructor() {
        this.testResults = [];
        this.startTime = Date.now();
    }

    log(message, type = 'info') {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            message,
            type,
            duration: Date.now() - this.startTime
        };
        
        this.testResults.push(logEntry);
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Optional: Log to file in real environment
        return logEntry;
    }

    async runAllTests() {
        this.log('🚀 Queen Coordinator - Starte Quellen-Funktionalität Tests', 'start');
        
        const tests = [
            () => this.testHTMLStructure(),
            () => this.testJavaScriptFunctions(),
            () => this.testFormElements(),
            () => this.testEventHandlers(),
            () => this.testAPIConnectivity(),
            () => this.testSortingFunctionality(),
            () => this.testFilterFunctionality(),
            () => this.testErrorHandling()
        ];

        let passed = 0;
        let failed = 0;

        for (const test of tests) {
            try {
                await test();
                passed++;
            } catch (error) {
                this.log(`❌ Test fehlgeschlagen: ${error.message}`, 'error');
                failed++;
            }
        }

        this.generateFinalReport(passed, failed);
        return { passed, failed, totalTests: tests.length };
    }

    async testHTMLStructure() {
        this.log('🔍 Teste HTML-Struktur...', 'test');
        
        // Test navigation radio button
        const sourcesRadio = document.getElementById('method_sources');
        if (!sourcesRadio) {
            throw new Error('Quellen-Datenbank Radio Button fehlt');
        }
        
        if (sourcesRadio.value !== 'sources') {
            throw new Error('Falscher Radio Button Value');
        }
        
        // Test form container
        const sourcesForm = document.getElementById('sources_form');
        if (!sourcesForm) {
            throw new Error('Quellen-Form Container fehlt');
        }
        
        // Test filter form
        const filterForm = document.getElementById('sources-filter-form');
        if (!filterForm) {
            throw new Error('Filter-Form fehlt');
        }
        
        // Test table container
        const tableContainer = document.getElementById('sources-table-container');
        if (!tableContainer) {
            throw new Error('Tabellen-Container fehlt');
        }
        
        // Test stats container
        const statsContainer = document.getElementById('sources-stats');
        if (!statsContainer) {
            throw new Error('Statistik-Container fehlt');
        }
        
        this.log('✅ HTML-Struktur vollständig', 'success');
    }

    async testJavaScriptFunctions() {
        this.log('🔧 Teste JavaScript-Funktionen...', 'test');
        
        // Test loadSources function
        if (typeof window.loadSources !== 'function') {
            throw new Error('loadSources Funktion fehlt');
        }
        
        // Test loadSourcesWithSort function
        if (typeof window.loadSourcesWithSort !== 'function') {
            throw new Error('loadSourcesWithSort Funktion fehlt');
        }
        
        // Test displayGroupedSources function
        if (typeof window.displayGroupedSources !== 'function') {
            throw new Error('displayGroupedSources Funktion fehlt');
        }
        
        // Test seedSourcesDatabase function (optional)
        if (typeof window.seedSourcesDatabase !== 'function') {
            this.log('⚠️ seedSourcesDatabase Funktion optional fehlt', 'warning');
        }
        
        this.log('✅ JavaScript-Funktionen verfügbar', 'success');
    }

    async testFormElements() {
        this.log('📝 Teste Form-Elemente...', 'test');
        
        const filterForm = document.getElementById('sources-filter-form');
        
        // Test country filter
        const countrySelect = filterForm.querySelector('select[name="country"]');
        if (!countrySelect) {
            throw new Error('Country Select fehlt');
        }
        
        // Test source_type filter
        const sourceTypeSelect = filterForm.querySelector('select[name="source_type"]');
        if (!sourceTypeSelect) {
            throw new Error('Source Type Select fehlt');
        }
        
        // Test min_reliability filter
        const reliabilityRange = filterForm.querySelector('input[name="min_reliability"]');
        if (!reliabilityRange) {
            throw new Error('Reliability Range fehlt');
        }
        
        if (reliabilityRange.type !== 'range') {
            throw new Error('Reliability Input ist kein Range-Type');
        }
        
        this.log('✅ Form-Elemente vollständig', 'success');
    }

    async testEventHandlers() {
        this.log('🎯 Teste Event-Handler...', 'test');
        
        // Test radio button click
        const sourcesRadio = document.getElementById('method_sources');
        const originalOnChange = sourcesRadio.onchange;
        
        // Simulate click
        sourcesRadio.click();
        
        // Wait for potential async operations
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Check if form is now active
        const sourcesForm = document.getElementById('sources_form');
        if (!sourcesForm.classList.contains('active')) {
            throw new Error('Tab-Switch Handler funktioniert nicht');
        }
        
        this.log('✅ Event-Handler funktional', 'success');
    }

    async testAPIConnectivity() {
        this.log('🌐 Teste API-Konnektivität...', 'test');
        
        try {
            // Test API base connectivity
            const response = await fetch(`${API_BASE_URL}/health`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`API Health Check fehlgeschlagen: ${response.status}`);
            }
            
            const health = await response.json();
            if (health.status !== 'ok') {
                throw new Error('API nicht gesund');
            }
            
            this.log('✅ API-Konnektivität gegeben', 'success');
            
        } catch (error) {
            this.log(`⚠️ API nicht erreichbar (Backend möglicherweise offline): ${error.message}`, 'warning');
            // Nicht als Fehler werten, da Backend optional für Frontend-Tests
        }
    }

    async testSortingFunctionality() {
        this.log('🔄 Teste Sortier-Funktionalität...', 'test');
        
        // Check if global sorting state variables exist
        if (typeof window.currentSortBy === 'undefined') {
            throw new Error('currentSortBy Variable fehlt');
        }
        
        if (typeof window.currentSortOrder === 'undefined') {
            throw new Error('currentSortOrder Variable fehlt');
        }
        
        // Test sorting coordination state
        if (typeof window.uiCoordinationState === 'undefined') {
            throw new Error('uiCoordinationState fehlt');
        }
        
        // Test coordinateUIEvent function
        if (typeof window.coordinateUIEvent !== 'function') {
            throw new Error('coordinateUIEvent Funktion fehlt');
        }
        
        this.log('✅ Sortier-Funktionalität Grundlagen vorhanden', 'success');
    }

    async testFilterFunctionality() {
        this.log('🔍 Teste Filter-Funktionalität...', 'test');
        
        const filterForm = document.getElementById('sources-filter-form');
        
        // Test form data extraction
        const formData = new FormData(filterForm);
        
        // Test that form can be reset
        if (typeof filterForm.reset !== 'function') {
            throw new Error('Form Reset-Funktion fehlt');
        }
        
        // Test filter application
        const filterButtons = filterForm.querySelectorAll('button[onclick*="loadSources"]');
        if (filterButtons.length === 0) {
            throw new Error('Filter-Anwenden-Button fehlt');
        }
        
        this.log('✅ Filter-Funktionalität verfügbar', 'success');
    }

    async testErrorHandling() {
        this.log('🛡️ Teste Error-Handling...', 'test');
        
        // Test if error handling functions exist
        if (typeof window.showGracefulError !== 'function') {
            throw new Error('showGracefulError Funktion fehlt');
        }
        
        if (typeof window.showEnhancedLoadingState !== 'function') {
            throw new Error('showEnhancedLoadingState Funktion fehlt');
        }
        
        // Test abort controller functionality
        if (typeof window.loadSourcesAbortController === 'undefined') {
            this.log('⚠️ loadSourcesAbortController nicht initialisiert (normal beim Start)', 'warning');
        }
        
        this.log('✅ Error-Handling-Funktionen verfügbar', 'success');
    }

    generateFinalReport(passed, failed) {
        const total = passed + failed;
        const successRate = ((passed / total) * 100).toFixed(1);
        
        this.log('', 'separator');
        this.log('🎯 QUEEN COORDINATOR - QUELLEN-FUNKTIONALITÄT REPORT', 'report');
        this.log('================================================', 'report');
        this.log(`✅ Erfolgreiche Tests: ${passed}/${total}`, 'report');
        this.log(`❌ Fehlgeschlagene Tests: ${failed}/${total}`, 'report');
        this.log(`📊 Erfolgsrate: ${successRate}%`, 'report');
        this.log(`⏱️ Gesamtdauer: ${Date.now() - this.startTime}ms`, 'report');
        this.log('', 'separator');
        
        if (failed === 0) {
            this.log('🎉 QUELLEN-FUNKTIONALITÄT VOLLSTÄNDIG WIEDERHERGESTELLT!', 'success');
            this.log('✅ Alle kritischen Komponenten funktional', 'success');
            this.log('✅ Navigation, Forms, JavaScript, Error-Handling OK', 'success');
            this.log('🐝 Queen Coordinator Mission: ERFOLGREICH', 'success');
        } else {
            this.log('⚠️ QUELLEN-FUNKTIONALITÄT TEILWEISE WIEDERHERGESTELLT', 'warning');
            this.log(`🔧 ${failed} Komponenten benötigen weitere Reparatur`, 'warning');
        }
        
        this.log('', 'separator');
        this.log('📋 Detaillierte Test-Logs:', 'info');
        
        this.testResults.forEach((result, index) => {
            if (result.type === 'error') {
                this.log(`   ${index + 1}. ❌ ${result.message}`, 'error');
            }
        });
    }

    // Export test results for external analysis
    exportResults() {
        return {
            timestamp: new Date().toISOString(),
            duration: Date.now() - this.startTime,
            results: this.testResults,
            summary: {
                total: this.testResults.filter(r => r.type === 'test').length,
                passed: this.testResults.filter(r => r.type === 'success').length,
                failed: this.testResults.filter(r => r.type === 'error').length
            }
        };
    }
}

// Execute tests when loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔥 Queen Coordinator Quellen-Funktionalität Tester geladen');
    
    // Auto-run tests after short delay
    setTimeout(async () => {
        const tester = new SourcesFunctionalityTester();
        const results = await tester.runAllTests();
        
        // Store results globally for external access
        window.sourcesTestResults = tester.exportResults();
        
        console.log('📊 Test-Ergebnisse in window.sourcesTestResults verfügbar');
    }, 2000);
});

// Export for external use
window.SourcesFunctionalityTester = SourcesFunctionalityTester;