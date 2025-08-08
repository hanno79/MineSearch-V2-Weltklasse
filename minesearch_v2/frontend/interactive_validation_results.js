/*
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Interactive Validator Agent - Testergebnisse und Koordination
*/

class InteractiveValidatorAgent {
    constructor() {
        this.version = '1.0';
        this.testResults = {
            buttons: {},
            modals: {},
            navigation: {},
            api: {},
            performance: {},
            errors: [],
            timestamp: new Date().toISOString()
        };
        this.init();
    }

    init() {
        console.log('🔧 Interactive Validator Agent v1.0 - Initialisiert');
        this.setupErrorMonitoring();
        this.analyzeInteractiveElements();
    }

    setupErrorMonitoring() {
        window.addEventListener('error', (e) => {
            this.testResults.errors.push({
                message: e.message,
                source: e.filename,
                line: e.lineno,
                column: e.colno,
                timestamp: new Date().toISOString(),
                stack: e.error ? e.error.stack : null
            });
            console.error('🚨 JavaScript Error detected:', e.message);
        });

        window.addEventListener('unhandledrejection', (e) => {
            this.testResults.errors.push({
                type: 'unhandledRejection',
                reason: e.reason,
                timestamp: new Date().toISOString()
            });
            console.error('🚨 Unhandled Promise Rejection:', e.reason);
        });
    }

    analyzeInteractiveElements() {
        console.log('🔍 Analysiere interaktive Elemente...');

        // Analyze button functions
        this.testButtonFunctions();
        
        // Analyze modal functions
        this.testModalFunctions();
        
        // Analyze navigation elements
        this.testNavigationElements();
        
        // Generate comprehensive report
        this.generateValidationReport();
    }

    testButtonFunctions() {
        console.log('🔘 Teste Button-Funktionen...');

        const buttonFunctions = [
            'startSingleSearch',
            'loadSources', 
            'loadResults',
            'loadStatistics',
            'loadConsolidatedResults',
            'exportEnhancedStatistics',
            'exportConsolidatedCSV',
            'printStatisticsReport',
            'cancelSearch',
            'closeBenchmarkModal',
            'seedSourcesDatabase',
            'toggleSourceDetails',
            'showModelDetails',
            'showFieldDetails',
            'closeModelDetails',
            'showFieldPerformance',
            'exportModelData'
        ];

        buttonFunctions.forEach(func => {
            if (typeof window[func] === 'function') {
                this.testResults.buttons[func] = {
                    status: 'FOUND',
                    type: 'function',
                    parameters: this.extractFunctionParameters(window[func])
                };
                console.log(`✅ ${func} - Funktion verfügbar`);
            } else {
                this.testResults.buttons[func] = {
                    status: 'NOT_FOUND',
                    type: 'missing'
                };
                console.warn(`❌ ${func} - Funktion nicht gefunden`);
            }
        });

        // Test onclick handlers in DOM
        this.testOnClickHandlers();
    }

    testOnClickHandlers() {
        console.log('🔗 Teste onClick-Handler im DOM...');

        const elementsWithOnClick = document.querySelectorAll('[onclick]');
        
        this.testResults.buttons.onClickElements = {
            count: elementsWithOnClick.length,
            elements: []
        };

        elementsWithOnClick.forEach((element, index) => {
            const onClickAttr = element.getAttribute('onclick');
            
            this.testResults.buttons.onClickElements.elements.push({
                index: index,
                tagName: element.tagName,
                onclick: onClickAttr,
                text: element.textContent?.trim().substring(0, 50) || '',
                id: element.id || '',
                className: element.className || ''
            });
        });

        console.log(`📊 ${elementsWithOnClick.length} Elemente mit onClick-Handlern gefunden`);
    }

    testModalFunctions() {
        console.log('🪟 Teste Modal-Funktionen...');

        // Check for modal-related elements
        const modalElements = document.querySelectorAll('[id*="modal"], [class*="modal"]');
        
        this.testResults.modals = {
            modalElements: modalElements.length,
            foundModals: []
        };

        modalElements.forEach(modal => {
            this.testResults.modals.foundModals.push({
                id: modal.id,
                className: modal.className,
                display: window.getComputedStyle(modal).display,
                visibility: window.getComputedStyle(modal).visibility
            });
        });

        console.log(`🪟 ${modalElements.length} Modal-Elemente gefunden`);
    }

    testNavigationElements() {
        console.log('🧭 Teste Navigation-Elemente...');

        // Test tab navigation
        const tabInputs = document.querySelectorAll('input[type="radio"][name="tab"]');
        const tabLabels = document.querySelectorAll('.tab-navigation label');

        this.testResults.navigation = {
            tabInputs: tabInputs.length,
            tabLabels: tabLabels.length,
            activeTab: null
        };

        // Check which tab is currently active
        tabInputs.forEach((input, index) => {
            if (input.checked) {
                this.testResults.navigation.activeTab = {
                    index: index,
                    value: input.value,
                    id: input.id
                };
            }
        });

        console.log(`📑 ${tabInputs.length} Tab-Inputs und ${tabLabels.length} Tab-Labels gefunden`);
    }

    extractFunctionParameters(func) {
        try {
            const funcStr = func.toString();
            const paramMatch = funcStr.match(/\(([^)]*)\)/);
            return paramMatch ? paramMatch[1].split(',').map(p => p.trim()).filter(p => p) : [];
        } catch (error) {
            return [];
        }
    }

    async testAPIConnectivity() {
        console.log('🌐 Teste API-Konnektivität...');

        const apiEndpoints = [
            { name: 'health', url: '/health' },
            { name: 'models', url: '/api/models' },
            { name: 'sources', url: '/api/sources' },
            { name: 'results', url: '/api/consolidated_results' },
            { name: 'statistics', url: '/api/statistics' }
        ];

        this.testResults.api = {};

        for (const endpoint of apiEndpoints) {
            try {
                const startTime = performance.now();
                const response = await fetch(endpoint.url);
                const endTime = performance.now();
                
                this.testResults.api[endpoint.name] = {
                    status: response.ok ? 'OK' : 'ERROR',
                    statusCode: response.status,
                    responseTime: endTime - startTime,
                    contentType: response.headers.get('content-type')
                };

                if (response.ok) {
                    console.log(`✅ ${endpoint.name} API - Status: ${response.status}, Time: ${(endTime - startTime).toFixed(2)}ms`);
                } else {
                    console.warn(`⚠️ ${endpoint.name} API - Status: ${response.status}`);
                }
                
            } catch (error) {
                this.testResults.api[endpoint.name] = {
                    status: 'ERROR',
                    error: error.message,
                    responseTime: null
                };
                console.error(`❌ ${endpoint.name} API - Error: ${error.message}`);
            }
        }
    }

    testPerformance() {
        console.log('⚡ Teste Performance...');

        this.testResults.performance = {
            memory: this.getMemoryInfo(),
            timing: this.getPageTiming(),
            resources: this.getResourceTiming()
        };
    }

    getMemoryInfo() {
        if (performance.memory) {
            return {
                usedJSHeapSize: performance.memory.usedJSHeapSize,
                totalJSHeapSize: performance.memory.totalJSHeapSize,
                jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
                usedMB: (performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(2),
                totalMB: (performance.memory.totalJSHeapSize / 1024 / 1024).toFixed(2)
            };
        }
        return { available: false };
    }

    getPageTiming() {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            return {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                totalLoadTime: navigation.loadEventEnd - navigation.navigationStart
            };
        }
        return { available: false };
    }

    getResourceTiming() {
        const resources = performance.getEntriesByType('resource');
        return {
            totalResources: resources.length,
            slowestResource: this.findSlowestResource(resources),
            resourceTypes: this.categorizeResources(resources)
        };
    }

    findSlowestResource(resources) {
        let slowest = null;
        let maxDuration = 0;

        resources.forEach(resource => {
            if (resource.duration > maxDuration) {
                maxDuration = resource.duration;
                slowest = {
                    name: resource.name,
                    duration: resource.duration,
                    size: resource.transferSize || 0
                };
            }
        });

        return slowest;
    }

    categorizeResources(resources) {
        const categories = {};
        
        resources.forEach(resource => {
            const extension = resource.name.split('.').pop().toLowerCase();
            const category = this.getResourceCategory(extension);
            
            if (!categories[category]) {
                categories[category] = 0;
            }
            categories[category]++;
        });

        return categories;
    }

    getResourceCategory(extension) {
        const categories = {
            'js': 'JavaScript',
            'css': 'Stylesheet',
            'png': 'Image',
            'jpg': 'Image',
            'jpeg': 'Image',
            'gif': 'Image',
            'svg': 'Image',
            'woff': 'Font',
            'woff2': 'Font',
            'ttf': 'Font',
            'html': 'Document'
        };
        
        return categories[extension] || 'Other';
    }

    async runComprehensiveValidation() {
        console.log('🚀 Starte umfassende Validierung...');

        // Run all tests
        await this.testAPIConnectivity();
        this.testPerformance();
        
        // Generate final report
        this.generateValidationReport();
        
        // Send results to MCP system
        await this.sendMCPNotification();
    }

    generateValidationReport() {
        const report = {
            summary: {
                timestamp: this.testResults.timestamp,
                version: this.version,
                totalErrors: this.testResults.errors.length,
                buttonTests: Object.keys(this.testResults.buttons).length,
                modalTests: this.testResults.modals ? Object.keys(this.testResults.modals).length : 0,
                apiTests: Object.keys(this.testResults.api).length
            },
            details: this.testResults
        };

        console.log('📊 Validation Report:', report);
        
        // Store in global scope for external access
        window.InteractiveValidationReport = report;
        
        return report;
    }

    async sendMCPNotification() {
        try {
            const message = `Interactive Validator: Tests completed - ${this.testResults.errors.length} errors detected`;
            
            // Try to notify MCP system
            await fetch('/api/mcp-notify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent: 'interactive-validator',
                    message: message,
                    results: this.testResults.summary || {},
                    timestamp: new Date().toISOString()
                })
            });
            
            console.log('📡 MCP Notification sent');
        } catch (error) {
            console.warn('⚠️ MCP Notification failed:', error.message);
        }
    }

    exportReport() {
        const report = this.generateValidationReport();
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `interactive-validation-report-${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('📄 Validation report exported');
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for other scripts to load
    setTimeout(() => {
        window.InteractiveValidator = new InteractiveValidatorAgent();
        
        // Run comprehensive validation after 2 seconds
        setTimeout(() => {
            window.InteractiveValidator.runComprehensiveValidation();
        }, 2000);
        
    }, 1000);
});

// Export for manual testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InteractiveValidatorAgent;
}