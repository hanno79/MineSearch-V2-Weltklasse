
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
        
        console.log(`🔧 Fixing ${nodesToFix.length} undefined values in DOM`);
        
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
    
    // BUGFIX 04.08.2025: Add safety check for document.body before observing  
    function startObserver() {
        const targetNode = document.body || document.documentElement;
        if (targetNode && targetNode.nodeType === Node.ELEMENT_NODE) {
            observer.observe(targetNode, {
                childList: true,
                subtree: true
            });
            console.log('🔍 MutationObserver gestartet für:', targetNode.tagName);
        } else {
            console.warn('⚠️ Kein geeigneter Zielknoten für MutationObserver gefunden');
        }
    }
    
    // Start observer when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startObserver);
    } else {
        startObserver();
    }
    
    console.log('🛡️ Undefined-Schutz aktiviert');
    
})();
