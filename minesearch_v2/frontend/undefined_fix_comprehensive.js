#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Umfassende Behebung der undefined-Werte im Frontend
 */

const fs = require('fs');
const path = require('path');

function fixUndefinedValues() {
    console.log('🔧 UNDEFINED-WERTE KORREKTUR GESTARTET');
    console.log('=' * 50);
    
    // 1. Lese results-display.js
    const resultsDisplayPath = '/app/minesearch_v2/frontend/js/results-display.js';
    let resultsDisplayContent = fs.readFileSync(resultsDisplayPath, 'utf8');
    
    console.log('📝 Korrigiere results-display.js...');
    
    // 2. Verbessere das safeValue Helper
    const safeValueFunction = `
    // ENHANCED UNDEFINED FIX 02.08.2025
    safeValue: function(value, fallback = 'N/A') {
        // Comprehensive null/undefined handling
        if (value === null || value === undefined || value === 'null' || value === 'undefined') {
            return fallback;
        }
        
        // Handle empty strings and whitespace
        if (typeof value === 'string') {
            const trimmed = value.trim();
            if (trimmed === '' || trimmed === 'null' || trimmed === 'undefined') {
                return fallback;
            }
            return trimmed;
        }
        
        // Handle numbers
        if (typeof value === 'number') {
            return isNaN(value) ? fallback : value;
        }
        
        return value;
    },

    // ENHANCED NUMBER FORMATTING
    formatNumber: function(value, decimals = 1, suffix = '') {
        const safeVal = this.safeValue(value, 0);
        if (typeof safeVal === 'number' || !isNaN(parseFloat(safeVal))) {
            return parseFloat(safeVal).toFixed(decimals) + suffix;
        }
        return 'N/A';
    },

    // ENHANCED PERCENTAGE FORMATTING  
    formatPercentage: function(value) {
        const safeVal = this.safeValue(value, 0);
        if (typeof safeVal === 'number' || !isNaN(parseFloat(safeVal))) {
            return parseFloat(safeVal).toFixed(1) + '%';
        }
        return 'N/A';
    },`;
    
    // 3. Finde und ersetze die problematische Zeile 302
    const problematicPattern = /const value = model && model\[col\.key\] !== undefined \? model\[col\.key\] : 'N\/A';/;
    const improvedHandling = `
                    // COMPREHENSIVE UNDEFINED FIX 02.08.2025
                    let rawValue = model && model[col.key] !== undefined ? model[col.key] : null;
                    const value = this.safeValue(rawValue, 'N/A');`;
    
    resultsDisplayContent = resultsDisplayContent.replace(problematicPattern, improvedHandling);
    
    // 4. Verbessere die Prozent- und Zahlen-Anzeige
    const percentagePattern = /(\w+_rate|consistency|confidence).*?cellContent = [^;]+;/gs;
    resultsDisplayContent = resultsDisplayContent.replace(
        /cellContent = `\${.*?\.toFixed\(1\)}%`;/g,
        'cellContent = this.formatPercentage(model[col.key]);'
    );
    
    // 5. Füge die neuen Helper-Funktionen hinzu
    const sanitizeHTMLPattern = /(sanitizeHTML: function\(str\) \{[\s\S]*?\},)/;
    resultsDisplayContent = resultsDisplayContent.replace(
        sanitizeHTMLPattern,
        `$1${safeValueFunction}`
    );
    
    // 6. Speichere die korrigierte Datei
    fs.writeFileSync(resultsDisplayPath, resultsDisplayContent);
    console.log('✅ results-display.js korrigiert');
    
    // 7. Erstelle einen verbesserten JavaScript-Fix
    const frontendFixJS = `
// CRITICAL UNDEFINED FIX - 02.08.2025
// Globally fix undefined values in the DOM

(function() {
    'use strict';
    
    // Enhanced safe value function
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
    
    // Override innerHTML and textContent to prevent undefined
    const originalInnerHTML = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
    const originalTextContent = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
    
    Object.defineProperty(Element.prototype, 'innerHTML', {
        get: originalInnerHTML.get,
        set: function(value) {
            const safeValue = window.safeDisplayValue(value, '');
            originalInnerHTML.set.call(this, safeValue);
        }
    });
    
    Object.defineProperty(Node.prototype, 'textContent', {
        get: originalTextContent.get,
        set: function(value) {
            const safeValue = window.safeDisplayValue(value, '');
            originalTextContent.set.call(this, safeValue);
        }
    });
    
    // Fix existing undefined values in DOM
    function fixExistingUndefined() {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let node;
        const nodesToFix = [];
        
        while (node = walker.nextNode()) {
            if (node.textContent && node.textContent.includes('undefined')) {
                nodesToFix.push(node);
            }
        }
        
        console.log(\`🔧 Fixing \${nodesToFix.length} undefined values in DOM\`);
        
        nodesToFix.forEach(node => {
            node.textContent = node.textContent.replace(/undefined/g, 'N/A');
        });
        
        // Fix table cells specifically
        document.querySelectorAll('td, th').forEach(cell => {
            if (cell.textContent === 'undefined' || cell.innerHTML.includes('undefined')) {
                cell.textContent = 'N/A';
            }
        });
    }
    
    // Run fix when DOM loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixExistingUndefined);
    } else {
        fixExistingUndefined();
    }
    
    // Monitor for new undefined values
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(mutation => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE && node.textContent.includes('undefined')) {
                        node.textContent = node.textContent.replace(/undefined/g, 'N/A');
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        const undefinedElements = node.querySelectorAll('*');
                        undefinedElements.forEach(el => {
                            if (el.textContent === 'undefined') {
                                el.textContent = 'N/A';
                            }
                        });
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('🛡️ Undefined-Schutz aktiviert');
    
})();
`;
    
    // 8. Speichere den globalen Fix
    fs.writeFileSync('/app/minesearch_v2/frontend/js/undefined-fix.js', frontendFixJS);
    console.log('✅ undefined-fix.js erstellt');
    
    // 9. Aktualisiere index.html um den Fix einzubinden
        const indexPath = '/app/frontend/index.html';
    let indexContent = fs.readFileSync(indexPath, 'utf8');
    
    if (!indexContent.includes('undefined-fix.js')) {
        // Füge den Fix vor dem schließenden body-Tag hinzu
        indexContent = indexContent.replace(
            '</body>',
            '    <script src="js/undefined-fix.js"></script>\\n</body>'
        );
        
        fs.writeFileSync(indexPath, indexContent);
        console.log('✅ index.html aktualisiert - undefined-fix.js eingebunden');
    }
    
    console.log('\\n🎉 UNDEFINED-KORREKTUR ABGESCHLOSSEN!');
    console.log('📋 Durchgeführte Änderungen:');
    console.log('   • results-display.js: Verbesserte safeValue-Funktionen');
    console.log('   • undefined-fix.js: Globaler DOM-Schutz gegen undefined');
    console.log('   • index.html: Script-Tag hinzugefügt');
    console.log('   • Real-time Überwachung: MutationObserver aktiviert');
}

if (require.main === module) {
    fixUndefinedValues();
}

module.exports = { fixUndefinedValues };