/*
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Erweiterte undefined-Erkennung und -Behebung für MineSearch Frontend
*/

// Advanced undefined detection and correction system
window.UndefinedDetection = {
    initialized: false,
    detectionCount: 0,
    fixedCount: 0,
    
    // Initialize the detection system
    init: function() {
        if (this.initialized) return;
        
        console.log('🔍 Undefined Detection System - DEAKTIVIERT aufgrund kritischer Bugs');
        
        // CRITICAL FIX: System deactivated due to false positives
        // The system was replacing normal text content with "N/A"
        this.initialized = true;
        console.log('⚠️ Undefined Detection System ist deaktiviert - verursachte Frontend-Zerstörung');
        return; // Exit without starting any functionality
        
        /*
        // Original code disabled:
        console.log('🔍 Undefined Detection System wird initialisiert...');
        
        if (!window.safeDisplayValue) {
            console.warn('⚠️ Global safeDisplayValue function not found. Loading fallback...');
            this.loadFallbackSafeFunction();
        }
        
        this.setupPeriodicChecks();
        this.setupEventListeners();
        
        this.initialized = true;
        console.log('✅ Undefined Detection System aktiviert');
        */
    },
    
    // Load fallback safe function if undefined-fix.js failed to load
    loadFallbackSafeFunction: function() {
        window.safeDisplayValue = function(value, fallback = 'N/A') {
            if (value === null || value === undefined || value === 'null' || value === 'undefined') {
                return fallback;
            }
            
            if (typeof value === 'string') {
                const trimmed = value.trim();
                if (trimmed === '' || trimmed === 'null' || trimmed === 'undefined') {
                    return fallback;
                }
                return trimmed;
            }
            
            if (typeof value === 'number') {
                return isNaN(value) ? fallback : value;
            }
            
            return value;
        };
        
        console.log('🔧 Fallback safeDisplayValue function loaded');
    },
    
    // Set up periodic undefined checks
    setupPeriodicChecks: function() {
        // Check every 5 seconds for undefined values
        setInterval(() => {
            this.runDetectionScan();
        }, 5000);
        
        // Initial scan after 1 second
        setTimeout(() => {
            this.runDetectionScan();
        }, 1000);
    },
    
    // Set up event listeners for dynamic content changes
    setupEventListeners: function() {
        // Listen for AJAX completion
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            const response = await originalFetch.apply(this, args);
            
            // Scan for undefined values after fetch
            setTimeout(() => {
                window.UndefinedDetection.runDetectionScan();
            }, 100);
            
            return response;
        };
        
        // Listen for tab changes
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-link')) {
                setTimeout(() => {
                    this.runDetectionScan();
                }, 500);
            }
        });
    },
    
    // Run comprehensive undefined detection scan
    runDetectionScan: function() {
        const startTime = performance.now();
        let detectedCount = 0;
        let fixedCount = 0;
        
        // Scan all text nodes
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let node;
        const problematicNodes = [];
        
        while (node = walker.nextNode()) {
            if (node.textContent) {
                const content = node.textContent;
                if (this.isProblematicValue(content)) {
                    detectedCount++;
                    problematicNodes.push({
                        node: node,
                        originalValue: content,
                        parent: node.parentElement
                    });
                }
            }
        }
        
        // Fix detected problems
        problematicNodes.forEach(item => {
            const cleanValue = this.cleanUndefinedValue(item.originalValue);
            if (cleanValue !== item.originalValue) {
                item.node.textContent = cleanValue;
                fixedCount++;
                
                console.debug(`🔧 Fixed: "${item.originalValue}" → "${cleanValue}" in ${item.parent?.tagName || 'unknown'}`);
            }
        });
        
        // Scan table cells specifically
        document.querySelectorAll('td, th').forEach(cell => {
            const content = cell.textContent?.trim();
            if (this.isProblematicValue(content)) {
                detectedCount++;
                const cleanValue = this.cleanUndefinedValue(content);
                if (cleanValue !== content) {
                    cell.textContent = cleanValue;
                    fixedCount++;
                    console.debug(`🔧 Fixed table cell: "${content}" → "${cleanValue}"`);
                }
            }
        });
        
        // Update statistics
        this.detectionCount += detectedCount;
        this.fixedCount += fixedCount;
        
        const endTime = performance.now();
        const scanDuration = (endTime - startTime).toFixed(2);
        
        if (detectedCount > 0 || fixedCount > 0) {
            console.log(`🔍 Undefined scan complete: ${detectedCount} detected, ${fixedCount} fixed (${scanDuration}ms)`);
        }
        
        return { detected: detectedCount, fixed: fixedCount, duration: scanDuration };
    },
    
    // Check if a value is problematic (undefined, null, etc.)
    isProblematicValue: function(value) {
        if (!value) return false;
        
        const str = String(value).trim().toLowerCase();
        
        // CRITICAL FIX: Don't treat whitespace, normal text, or HTML content as problematic
        if (str === '' || str.length < 3) return false;
        if (/^[a-z0-9\s\-_.,:;!?()]+$/i.test(str)) return false; // Normal text
        if (str.includes('<') || str.includes('>')) return false; // HTML content
        
        const problematicValues = [
            'undefined',
            'null', 
            '[object object]',
            'nan',
            '[object undefined]',
            '[object null]'
        ];
        
        return problematicValues.includes(str);
    },
    
    // Clean undefined values
    cleanUndefinedValue: function(value) {
        if (window.safeDisplayValue) {
            return window.safeDisplayValue(value, 'N/A');
        }
        
        // Fallback cleaning
        if (this.isProblematicValue(value)) {
            return 'N/A';
        }
        
        return value;
    },
    
    // Get detection statistics
    getStats: function() {
        return {
            detectionCount: this.detectionCount,
            fixedCount: this.fixedCount,
            initialized: this.initialized,
            hasGlobalSafeFunction: typeof window.safeDisplayValue === 'function'
        };
    },
    
    // Manual scan trigger
    forceScan: function() {
        console.log('🔍 Manual undefined scan triggered...');
        return this.runDetectionScan();
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.UndefinedDetection.init();
    });
} else {
    window.UndefinedDetection.init();
}

// Export global functions for convenience
window.checkUndefinedValues = () => window.UndefinedDetection.forceScan();
window.getUndefinedStats = () => window.UndefinedDetection.getStats();

console.log('✅ Undefined Detection Module geladen');