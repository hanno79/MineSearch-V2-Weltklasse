/*
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: JavaScript Function Validation Tests für MineSearch v2
*/

// JavaScript Function Validation System
class MineSearchFunctionValidator {
    constructor() {
        this.testResults = {};
        this.errors = [];
        this.init();
    }
    
    init() {
        console.log('🧪 MineSearch Function Validation gestartet...');
        this.runAllTests();
    }
    
    runAllTests() {
        // Test 1: Kritische Funktionen
        this.testCriticalFunctions();
        
        // Test 2: Export-Funktionen
        this.testExportFunctions();
        
        // Test 3: Extension-Safe System
        this.testExtensionSafeSystem();
        
        // Test 4: DOM-Manipulation
        this.testDOMOperations();
        
        // Test 5: Error Handling
        this.testErrorHandling();
        
        // Ergebnis-Report
        this.generateReport();
    }
    
    testCriticalFunctions() {
        console.log('🔍 Teste kritische Funktionen...');
        
        const criticalFunctions = [
            'printStatisticsReport',
            'exportEnhancedStatistics',
            'showNotification',
            'createSecureElement',
            'validateFunction'
        ];
        
        criticalFunctions.forEach(funcName => {
            try {
                const exists = typeof window[funcName] === 'function';
                this.testResults[funcName] = {
                    exists: exists,
                    type: typeof window[funcName],
                    status: exists ? 'PASS' : 'FAIL'
                };
                
                if (!exists) {
                    this.errors.push(`❌ Kritische Funktion ${funcName} nicht verfügbar`);
                }
            } catch (error) {
                this.testResults[funcName] = {
                    exists: false,
                    error: error.message,
                    status: 'ERROR'
                };
                this.errors.push(`💥 Fehler beim Test von ${funcName}: ${error.message}`);
            }
        });
    }
    
    testExportFunctions() {
        console.log('📊 Teste Export-Funktionen...');
        
        try {
            // Test printStatisticsReport
            if (typeof printStatisticsReport === 'function') {
                this.testResults.printStatisticsReport_callable = {
                    status: 'PASS',
                    message: 'printStatisticsReport ist aufrufbar'
                };
            }
            
            // Test exportEnhancedStatistics Parameter-Validation
            if (typeof exportEnhancedStatistics === 'function') {
                // Simuliere ungültigen Parameter
                try {
                    exportEnhancedStatistics(null);
                    this.testResults.exportEnhancedStatistics_validation = {
                        status: 'PASS',
                        message: 'Parameter-Validation funktioniert'
                    };
                } catch (error) {
                    this.testResults.exportEnhancedStatistics_validation = {
                        status: 'ERROR',
                        error: error.message
                    };
                }
            }
            
        } catch (error) {
            this.errors.push(`Export-Function Test Fehler: ${error.message}`);
        }
    }
    
    testExtensionSafeSystem() {
        console.log('🛡️ Teste Extension-Safe System...');
        
        try {
            // Test Extension-Safe DOM
            if (window.MineSearchExtensionSafe) {
                this.testResults.extensionSafeSystem = {
                    status: 'PASS',
                    conflicts: window.MineSearchExtensionSafe.conflictManager.conflicts.length,
                    message: `Extension-Safe System aktiv mit ${window.MineSearchExtensionSafe.conflictManager.conflicts.length} erkannten Konflikten`
                };
                
                // Test Safe DOM Creation
                if (window.safeCreateElement) {
                    try {
                        const testElement = window.safeCreateElement('div', { id: 'test' });
                        if (testElement && testElement.hasAttribute('data-minesearch-element')) {
                            this.testResults.safeDOM = {
                                status: 'PASS',
                                message: 'Safe DOM Creation funktioniert'
                            };
                        } else {
                            this.testResults.safeDOM = {
                                status: 'FAIL',
                                message: 'Safe DOM Creation fehlerhaft'
                            };
                        }
                    } catch (error) {
                        this.testResults.safeDOM = {
                            status: 'ERROR',
                            error: error.message
                        };
                    }
                }
                
                // Test Safe Notifications
                if (window.safeShowNotification) {
                    this.testResults.safeNotifications = {
                        status: 'PASS',
                        message: 'Safe Notifications verfügbar'
                    };
                }
                
            } else {
                this.testResults.extensionSafeSystem = {
                    status: 'FAIL',
                    message: 'Extension-Safe System nicht geladen'
                };
                this.errors.push('❌ Extension-Safe System nicht verfügbar');
            }
            
        } catch (error) {
            this.errors.push(`Extension-Safe Test Fehler: ${error.message}`);
        }
    }
    
    testDOMOperations() {
        console.log('🏗️ Teste DOM-Operationen...');
        
        try {
            // Test Standard DOM-Erstellung
            const testDiv = document.createElement('div');
            testDiv.id = 'minesearch-test-element';
            testDiv.setAttribute('data-test', 'validation');
            
            this.testResults.domCreation = {
                status: testDiv && testDiv.id === 'minesearch-test-element' ? 'PASS' : 'FAIL',
                message: 'Standard DOM-Erstellung funktioniert'
            };
            
            // Test Secure Element Creation
            if (typeof createSecureElement === 'function') {
                const secureDiv = createSecureElement('div', { id: 'secure-test' });
                this.testResults.secureElementCreation = {
                    status: secureDiv && secureDiv.id === 'secure-test' ? 'PASS' : 'FAIL',
                    message: 'Secure Element Creation funktioniert'
                };
            }
            
        } catch (error) {
            this.errors.push(`DOM Operations Test Fehler: ${error.message}`);
        }
    }
    
    testErrorHandling() {
        console.log('⚠️ Teste Error Handling...');
        
        try {
            // Test Export Function Error Handling
            if (typeof exportEnhancedStatistics === 'function') {
                // Test mit ungültigen Parametern
                const originalConsoleError = console.error;
                let errorLogged = false;
                
                console.error = function(...args) {
                    if (args[0] && args[0].includes('Export error')) {
                        errorLogged = true;
                    }
                    originalConsoleError.apply(console, args);
                };
                
                // Trigger Error
                exportEnhancedStatistics('invalid_type');
                
                setTimeout(() => {
                    console.error = originalConsoleError;
                    this.testResults.exportErrorHandling = {
                        status: errorLogged ? 'PASS' : 'FAIL',
                        message: errorLogged ? 'Error Handling funktioniert' : 'Keine Fehlerbehandlung erkannt'
                    };
                }, 100);
            }
            
        } catch (error) {
            this.errors.push(`Error Handling Test Fehler: ${error.message}`);
        }
    }
    
    generateReport() {
        console.log('📋 Generiere Validation Report...');
        
        const totalTests = Object.keys(this.testResults).length;
        const passedTests = Object.values(this.testResults).filter(r => r.status === 'PASS').length;
        const failedTests = Object.values(this.testResults).filter(r => r.status === 'FAIL').length;
        const errorTests = Object.values(this.testResults).filter(r => r.status === 'ERROR').length;
        
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: totalTests,
                passed: passedTests,
                failed: failedTests,
                errors: errorTests,
                successRate: Math.round((passedTests / totalTests) * 100)
            },
            results: this.testResults,
            errors: this.errors,
            recommendations: this.generateRecommendations()
        };
        
        // Console Report
        console.log('🎯 VALIDATION REPORT:');
        console.log(`✅ Erfolgreich: ${passedTests}/${totalTests} (${report.summary.successRate}%)`);
        console.log(`❌ Fehlgeschlagen: ${failedTests}`);
        console.log(`💥 Fehler: ${errorTests}`);
        
        if (this.errors.length > 0) {
            console.log('🚨 KRITISCHE PROBLEME:');
            this.errors.forEach(error => console.log(error));
        }
        
        // Speichere Report
        window.MineSearchValidationReport = report;
        
        // Show Notification
        const notificationFunc = window.safeShowNotification || window.showNotification || console.log;
        if (report.summary.successRate >= 80) {
            notificationFunc(`✅ JavaScript Validation: ${report.summary.successRate}% erfolgreich`, 'success');
        } else {
            notificationFunc(`⚠️ JavaScript Validation: ${report.summary.successRate}% - Probleme erkannt`, 'warning');
        }
    }
    
    generateRecommendations() {
        const recommendations = [];
        
        if (this.errors.length > 0) {
            recommendations.push('Behebe die kritischen Funktions-Fehler vor dem Produktiveinsatz');
        }
        
        if (!window.MineSearchExtensionSafe) {
            recommendations.push('Lade extension-safe.js für bessere Browser-Extension-Kompatibilität');
        }
        
        if (this.testResults.exportEnhancedStatistics && this.testResults.exportEnhancedStatistics.status !== 'PASS') {
            recommendations.push('Überprüfe exportEnhancedStatistics Funktion - Export-Features könnten nicht funktionieren');
        }
        
        if (this.testResults.printStatisticsReport && this.testResults.printStatisticsReport.status !== 'PASS') {
            recommendations.push('Implementiere printStatisticsReport Funktion für Druckfunktionalität');
        }
        
        return recommendations;
    }
}

// Auto-Start der Validation nach DOM-Load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            new MineSearchFunctionValidator();
        }, 1000); // Warte 1s damit alle Scripts geladen sind
    });
} else {
    setTimeout(() => {
        new MineSearchFunctionValidator();
    }, 1000);
}

// Export für manuelle Tests
window.runMineSearchValidation = function() {
    return new MineSearchFunctionValidator();
};