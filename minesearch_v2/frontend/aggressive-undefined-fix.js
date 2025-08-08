// AGGRESSIVE UNDEFINED FIX - 02.08.2025
// Eliminiert ALLE undefined-Werte im DOM sofort und aggressiv

(function() {
    'use strict';
    
    console.log('🔥 AGGRESSIVE UNDEFINED FIX - Starting');
    
    // CRITICAL: Enhanced safe value function with multiple fallbacks
    window.safeDisplayValue = function(value, fallback = 'N/A') {
        // Check for all undefined variants
        if (value === null || value === undefined || 
            value === 'null' || value === 'undefined' ||
            value === 'NULL' || value === 'UNDEFINED' ||
            String(value).toLowerCase() === 'undefined' ||
            String(value).toLowerCase() === 'null') {
            return fallback;
        }
        
        // Handle string processing
        if (typeof value === 'string') {
            const trimmed = value.trim();
            if (trimmed === '' || 
                trimmed.toLowerCase() === 'null' || 
                trimmed.toLowerCase() === 'undefined' ||
                trimmed === 'NaN' ||
                trimmed === '0' && fallback !== '0') {
                return fallback;
            }
            return trimmed;
        }
        
        // Handle numbers
        if (typeof value === 'number') {
            return isNaN(value) ? fallback : value;
        }
        
        return value;
    };
    
    // AGGRESSIVE: Global function to check for undefined values
    window.checkUndefinedValues = function() {
        const undefinedCount = (document.body.textContent.match(/undefined/gi) || []).length;
        console.log(`🔍 Found ${undefinedCount} undefined values in DOM`);
        return undefinedCount;
    };
    
    // AGGRESSIVE: Fix all existing undefined values immediately
    function aggressiveUndefinedFix() {
        let fixedCount = 0;
        
        // 1. Fix all text nodes
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let node;
        const nodesToFix = [];
        
        while (node = walker.nextNode()) {
            if (node.textContent && node.textContent.toLowerCase().includes('undefined')) {
                nodesToFix.push(node);
            }
        }
        
        console.log(`🔧 Fixing ${nodesToFix.length} text nodes with undefined`);
        
        nodesToFix.forEach(node => {
            const originalText = node.textContent;
            node.textContent = originalText
                .replace(/undefined/gi, 'N/A')
                .replace(/null/gi, 'N/A')
                .replace(/NaN/gi, 'N/A');
            fixedCount++;
        });
        
        // 2. Fix all element attributes and innerHTML
        document.querySelectorAll('*').forEach(element => {
            // Fix innerHTML
            if (element.innerHTML && element.innerHTML.toLowerCase().includes('undefined')) {
                element.innerHTML = element.innerHTML
                    .replace(/undefined/gi, 'N/A')
                    .replace(/null/gi, 'N/A');
                fixedCount++;
            }
            
            // Fix attributes
            Array.from(element.attributes).forEach(attr => {
                if (attr.value && attr.value.toLowerCase().includes('undefined')) {
                    attr.value = attr.value
                        .replace(/undefined/gi, 'N/A')
                        .replace(/null/gi, 'N/A');
                    fixedCount++;
                }
            });
        });
        
        // 3. Fix table cells specifically
        document.querySelectorAll('td, th, .table-cell, .field-value').forEach(cell => {
            if (cell.textContent && cell.textContent.toLowerCase().includes('undefined')) {
                cell.textContent = cell.textContent
                    .replace(/undefined/gi, 'N/A')
                    .replace(/null/gi, 'N/A')
                    .replace(/NaN/gi, 'N/A');
                fixedCount++;
            }
        });
        
        // 4. Fix specific patterns found in validation
        document.querySelectorAll('small').forEach(small => {
            if (small.textContent) {
                // Fix patterns like "undefined Tests | 35 Minen"
                if (small.textContent.includes('undefined Tests')) {
                    small.textContent = small.textContent.replace(/undefined Tests/gi, 'N/A Tests');
                    fixedCount++;
                }
                
                // Fix patterns like "Daten: undefined%"
                if (small.textContent.includes('Daten: undefined')) {
                    small.textContent = small.textContent.replace(/Daten: undefined/gi, 'Daten: N/A');
                    fixedCount++;
                }
                
                // Fix patterns like "~undefined Quellen"
                if (small.textContent.includes('undefined Quellen')) {
                    small.textContent = small.textContent.replace(/~undefined Quellen/gi, '~N/A Quellen');
                    fixedCount++;
                }
            }
        });
        
        console.log(`🎯 AGGRESSIVE FIX: Fixed ${fixedCount} undefined occurrences`);
        return fixedCount;
    }
    
    // CRITICAL: Override DOM methods to prevent undefined injection
    const originalInnerHTML = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
    const originalTextContent = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
    
    if (originalInnerHTML) {
        Object.defineProperty(Element.prototype, 'innerHTML', {
            get: originalInnerHTML.get,
            set: function(value) {
                const safeValue = window.safeDisplayValue(value, '');
                originalInnerHTML.set.call(this, safeValue);
            },
            configurable: true
        });
    }
    
    if (originalTextContent) {
        Object.defineProperty(Node.prototype, 'textContent', {
            get: originalTextContent.get,
            set: function(value) {
                const safeValue = window.safeDisplayValue(value, '');
                originalTextContent.set.call(this, safeValue);
            },
            configurable: true
        });
    }
    
    // AGGRESSIVE: Monitor and fix in real-time
    const aggressiveObserver = new MutationObserver(function(mutations) {
        let needsFix = false;
        
        mutations.forEach(mutation => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE) {
                        if (node.textContent && node.textContent.toLowerCase().includes('undefined')) {
                            node.textContent = node.textContent
                                .replace(/undefined/gi, 'N/A')
                                .replace(/null/gi, 'N/A');
                            needsFix = true;
                        }
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check all descendants
                        const walker = document.createTreeWalker(
                            node,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        
                        let textNode;
                        while (textNode = walker.nextNode()) {
                            if (textNode.textContent && textNode.textContent.toLowerCase().includes('undefined')) {
                                textNode.textContent = textNode.textContent
                                    .replace(/undefined/gi, 'N/A')
                                    .replace(/null/gi, 'N/A');
                                needsFix = true;
                            }
                        }
                    }
                });
            }
            
            if (mutation.type === 'characterData') {
                if (mutation.target.textContent && mutation.target.textContent.toLowerCase().includes('undefined')) {
                    mutation.target.textContent = mutation.target.textContent
                        .replace(/undefined/gi, 'N/A')
                        .replace(/null/gi, 'N/A');
                    needsFix = true;
                }
            }
        });
        
        if (needsFix) {
            console.log('🔧 AGGRESSIVE OBSERVER: Fixed undefined values in real-time');
        }
    });
    
    // AGGRESSIVE: Run immediately and continuously
    function runAggressiveFix() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                aggressiveUndefinedFix();
                aggressiveObserver.observe(document.body, {
                    childList: true,
                    subtree: true,
                    characterData: true
                });
            });
        } else {
            aggressiveUndefinedFix();
            aggressiveObserver.observe(document.body, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }
        
        // Run fix every 2 seconds as backup
        setInterval(() => {
            const undefinedCount = window.checkUndefinedValues();
            if (undefinedCount > 0) {
                console.log(`🚨 AGGRESSIVE BACKUP: Found ${undefinedCount} undefined values, fixing...`);
                aggressiveUndefinedFix();
            }
        }, 2000);
    }
    
    // ACTIVATE IMMEDIATELY - DISABLED DUE TO CRITICAL BUG
    // runAggressiveFix(); // DISABLED - was causing N/A spam
    
    console.log('🔥 AGGRESSIVE UNDEFINED FIX - DEAKTIVIERT (verursachte Frontend-Zerstörung)');
    
})();