/*
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Extension-Safe JavaScript Utilities für MineSearch v2
*/

// Extension-Konflikt-Erkennung
class ExtensionConflictManager {
    constructor() {
        this.conflicts = this.detectConflicts();
        this.init();
    }
    
    detectConflicts() {
        const conflicts = [];
        
        try {
            // Erkenne kwift.CHROME.js Extension
            if (window.kwift && window.kwift.CHROME) {
                conflicts.push({
                    name: 'kwift.CHROME.js',
                    type: 'chrome_extension',
                    risk: 'medium',
                    mitigation: 'namespace_isolation'
                });
                console.info('🔧 kwift.CHROME.js Extension erkannt - Kompatibilitäts-Modus aktiviert');
            }
            
            // Erkenne andere häufige Extension-Konflikte
            if (window.chrome && window.chrome.runtime && window.chrome.runtime.onMessage) {
                conflicts.push({
                    name: 'Generic Chrome Extension',
                    type: 'chrome_extension', 
                    risk: 'low',
                    mitigation: 'careful_dom_manipulation'
                });
            }
            
            // Erkenne AdBlocker oder ähnliche DOM-Manipulatoren
            if (document.querySelector('[data-adblock]') || document.querySelector('.adblock')) {
                conflicts.push({
                    name: 'AdBlocker',
                    type: 'dom_manipulator',
                    risk: 'low',
                    mitigation: 'robust_selectors'
                });
            }
            
            // Erkenne Script-Injection-Extensions
            const scriptTags = document.querySelectorAll('script[src*="extension://"]');
            if (scriptTags.length > 0) {
                conflicts.push({
                    name: 'Script Injection Extension',
                    type: 'script_injector',
                    risk: 'medium',
                    mitigation: 'isolated_execution'
                });
            }
            
        } catch (error) {
            console.warn('Extension conflict detection failed:', error);
        }
        
        return conflicts;
    }
    
    init() {
        if (this.conflicts.length > 0) {
            console.log('🛡️ Extension-Konflikte erkannt:', this.conflicts.map(c => c.name).join(', '));
            this.applyMitigations();
        }
    }
    
    applyMitigations() {
        // Namespace-Protection
        if (!window.MineSearchProtected) {
            window.MineSearchProtected = {};
        }
        
        // DOM-Mutation-Observer für Extension-Protection
        if (window.MutationObserver) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && mutation.target.hasAttribute) {
                        const mineSearchElements = mutation.target.querySelectorAll('[data-minesearch-element]');
                        mineSearchElements.forEach(element => {
                            // Schütze MineSearch-Elemente vor Extension-Interferenz
                            element.setAttribute('data-minesearch-protected', 'true');
                        });
                    }
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }
    
    isHighRisk() {
        return this.conflicts.some(c => c.risk === 'high');
    }
    
    isMediumRisk() {
        return this.conflicts.some(c => c.risk === 'medium');
    }
}

// Extension-Safe DOM-Utilities
class SafeDOM {
    constructor(conflictManager) {
        this.conflictManager = conflictManager;
    }
    
    createElement(tagName, attributes = {}, namespace = 'minesearch') {
        try {
            const element = document.createElement(tagName);
            
            // Füge MineSearch-Namespace hinzu
            element.setAttribute('data-minesearch-element', namespace);
            element.setAttribute('data-minesearch-protected', 'true');
            
            // Extension-sichere Attribut-Setzung
            for (const [key, value] of Object.entries(attributes)) {
                if (this.isSafeAttribute(key, value)) {
                    element.setAttribute(key, String(value));
                }
            }
            
            return element;
        } catch (error) {
            console.error('Safe DOM creation failed:', error);
            return document.createElement(tagName);
        }
    }
    
    isSafeAttribute(key, value) {
        // Whitelist-basierte Attribut-Validation
        const safeAttributes = [
            'href', 'download', 'style', 'class', 'id', 
            'title', 'alt', 'src', 'data-*'
        ];
        
        const isSafe = safeAttributes.some(attr => 
            key === attr || (attr.endsWith('*') && key.startsWith(attr.slice(0, -1)))
        );
        
        return isSafe && (typeof value === 'string' || typeof value === 'number');
    }
    
    addEventListener(element, event, handler, options = {}) {
        try {
            // Extension-sicherer Event-Handler-Wrapper
            const safeHandler = (e) => {
                try {
                    // Nur verarbeiten wenn es ein MineSearch-Element ist
                    if (e.target && (
                        e.target.hasAttribute('data-minesearch-element') ||
                        e.target.closest('[data-minesearch-element]')
                    )) {
                        return handler(e);
                    }
                } catch (error) {
                    console.warn('Event handler error:', error);
                }
            };
            
            element.addEventListener(event, safeHandler, options);
            return safeHandler;
        } catch (error) {
            console.error('Safe event listener failed:', error);
            return null;
        }
    }
    
    querySelector(selector, safe = true) {
        try {
            if (safe) {
                // Füge MineSearch-Namespace-Filter hinzu
                const safeSelector = `[data-minesearch-element] ${selector}, ${selector}[data-minesearch-element]`;
                return document.querySelector(safeSelector);
            }
            return document.querySelector(selector);
        } catch (error) {
            console.error('Safe querySelector failed:', error);
            return null;
        }
    }
}

// Extension-Safe Notification System
class SafeNotifications {
    constructor(conflictManager) {
        this.conflictManager = conflictManager;
        this.fallbackContainer = null;
        this.initFallbackContainer();
    }
    
    initFallbackContainer() {
        try {
            this.fallbackContainer = document.createElement('div');
            this.fallbackContainer.id = 'minesearch-fallback-notifications';
            this.fallbackContainer.setAttribute('data-minesearch-element', 'notifications');
            this.fallbackContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            `;
            document.body.appendChild(this.fallbackContainer);
        } catch (error) {
            console.warn('Fallback notification container creation failed:', error);
        }
    }
    
    show(message, type = 'info', duration = 3000) {
        try {
            // Logge Extension-Konflikte
            if (this.conflictManager.conflicts.length > 0) {
                console.log(`[EXTENSION-SAFE] ${message}`);
            }
            
            // Versuche normale showNotification
            if (typeof showNotification === 'function' && !this.conflictManager.isHighRisk()) {
                showNotification(message, type, duration);
                return;
            }
            
            // Fallback: Eigenes Notification-System
            this.showFallbackNotification(message, type, duration);
            
        } catch (error) {
            console.error('Safe notification failed:', error);
            this.showConsoleFallback(message, type);
        }
    }
    
    showFallbackNotification(message, type, duration) {
        if (!this.fallbackContainer) return;
        
        const notification = document.createElement('div');
        notification.setAttribute('data-minesearch-element', 'notification');
        notification.textContent = message;
        
        const colors = {
            success: '#059669',
            error: '#dc2626', 
            warning: '#d97706',
            info: '#2563eb'
        };
        
        notification.style.cssText = `
            background: ${colors[type] || colors.info};
            color: white;
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            pointer-events: auto;
            animation: slideIn 0.3s ease-out;
        `;
        
        this.fallbackContainer.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.3s ease-out';
                setTimeout(() => {
                    if (notification.parentNode) {
                        this.fallbackContainer.removeChild(notification);
                    }
                }, 300);
            }
        }, duration);
    }
    
    showConsoleFallback(message, type) {
        const emoji = {
            success: '✅',
            error: '❌', 
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        console.log(`${emoji[type] || emoji.info} [${type.toUpperCase()}] ${message}`);
        
        if (type === 'error') {
            alert(`Fehler: ${message}`);
        }
    }
}

// Function Validation System
class FunctionValidator {
    constructor() {
        this.validatedFunctions = new Set();
    }
    
    validate(funcName, context = window) {
        try {
            const cacheKey = `${context.constructor.name}.${funcName}`;
            
            if (this.validatedFunctions.has(cacheKey)) {
                return true;
            }
            
            if (typeof context[funcName] === 'function') {
                this.validatedFunctions.add(cacheKey);
                return true;
            }
            
            console.warn(`Funktion ${funcName} ist nicht verfügbar in`, context);
            return false;
        } catch (error) {
            console.error(`Fehler beim Validieren der Funktion ${funcName}:`, error);
            return false;
        }
    }
    
    validateAll(functionNames, context = window) {
        const results = {};
        functionNames.forEach(name => {
            results[name] = this.validate(name, context);
        });
        return results;
    }
    
    createSafeWrapper(funcName, fallback = null, context = window) {
        return (...args) => {
            if (this.validate(funcName, context)) {
                try {
                    return context[funcName](...args);
                } catch (error) {
                    console.error(`Fehler beim Ausführen von ${funcName}:`, error);
                    return fallback ? fallback(...args) : undefined;
                }
            } else {
                console.warn(`Sicherer Wrapper: ${funcName} nicht verfügbar`);
                return fallback ? fallback(...args) : undefined;
            }
        };
    }
}

// Global Extension-Safe System initialisieren
window.MineSearchExtensionSafe = {
    conflictManager: new ExtensionConflictManager(),
    safeDOM: null,
    safeNotifications: null,
    functionValidator: new FunctionValidator(),
    
    init() {
        this.safeDOM = new SafeDOM(this.conflictManager);
        this.safeNotifications = new SafeNotifications(this.conflictManager);
        
        // Globale Shortcuts
        window.safeCreateElement = (tagName, attributes) => this.safeDOM.createElement(tagName, attributes);
        window.safeShowNotification = (message, type, duration) => this.safeNotifications.show(message, type, duration);
        window.validateFunction = (funcName, context) => this.functionValidator.validate(funcName, context);
        
        console.log('🛡️ MineSearch Extension-Safe System aktiviert');
        
        if (this.conflictManager.conflicts.length > 0) {
            console.log('⚠️ Extension-Konflikte:', this.conflictManager.conflicts);
        }
    }
};

// Auto-Init wenn DOM bereit
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.MineSearchExtensionSafe.init();
    });
} else {
    window.MineSearchExtensionSafe.init();
}