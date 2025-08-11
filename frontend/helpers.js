/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Helper & Utility Functions
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (Phase 3 - Final Refactoring)
 * Helper Functions: Escaping, Sanitization, Loading States, Error Handling, Notifications
 */

// ============================================
// STRING & SECURITY HELPERS
// ============================================

/**
 * JAVASCRIPT STRING ESCAPING: Sicheres Escaping für JavaScript-Strings
 */
function escapeJavaScriptString(str) {
    if (!str) return '';
    // Escape alle kritischen Zeichen für JavaScript-Strings
    return str
        .replace(/\\/g, '\\\\')    // Backslash zuerst escapen
        .replace(/'/g, "\\'")      // Single quotes escapen
        .replace(/"/g, '\\"')      // Double quotes escapen
        .replace(/\n/g, '\\n')     // Newlines escapen
        .replace(/\r/g, '\\r')     // Carriage returns escapen
        .replace(/\t/g, '\\t');    // Tabs escapen
}

/**
 * SAFE JSON STRINGIFY: Sichere JSON-String-Konvertierung
 */
function safeJSONStringify(str) {
    if (!str) return "''";
    return JSON.stringify(str);
}

/**
 * SAFE HTML SETTING: Sichere Funktion für innerHTML-Replacement
 */
function safeSetHTML(element, html) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (!element) return;
    
    // Security: Basis-Sanitization für XSS-Prävention
    if (typeof sanitizeHTML === 'function') {
        html = sanitizeHTML(html);
    }
    
    element.innerHTML = html;
}

// ============================================
// LOADING STATE HELPERS
// ============================================

/**
 * LOADING HTML GENERATOR: Erstellt Loading-HTML mit Spinner und Timer
 */
function createLoadingHTML(title, message = '', showSpinner = true, showTimer = false) {
    const spinnerHTML = showSpinner ? `
        <div style="margin-top: 10px;">
            <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #0ea5e9; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
    ` : '';
    
    // Timer wird durch #loading-timer im HTML angezeigt - kein extra HTML nötig
    const timerHTML = '';
    
    return `
        <div style="text-align: center; padding: 40px;">
            <h3 style="color: #0ea5e9; margin-bottom: 10px;">${sanitizeHTML(title)}</h3>
            ${message ? `<p style="color: #6b7280; margin-bottom: 10px;">${sanitizeHTML(message)}</p>` : ''}
            ${spinnerHTML}
            ${timerHTML}
        </div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes loading-progress {
                0% { width: 0%; }
                50% { width: 75%; }
                100% { width: 100%; }
            }
        </style>
    `;
}

/**
 * SHOW LOADING MESSAGE: Zeigt Loading-Message in Element
 */
function showLoadingMessage(element, title, message = '', startTimer = false) {
    element.innerHTML = createLoadingHTML(title, message, true, startTimer);
    
    if (startTimer) {
        // Verwende das Master-Timer-System aus utils.js
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.start) {
            window.searchTimer.start();
        }
    }
}

/**
 * ENHANCED LOADING STATE: Erweiterte Loading-Anzeige mit Progress-Bar
 */
function showEnhancedLoadingState(targetElement, message = 'Daten werden geladen...', showProgress = false) {
    // Kann erweitert werden um Progress-Bar falls showProgress = true
    const progressHTML = showProgress ? `
        <div style="width: 100%; background: #e9ecef; border-radius: 10px; margin-top: 15px; height: 6px;">
            <div style="width: 0%; height: 100%; background: #4CAF50; border-radius: 10px; animation: loading-progress 2s ease-in-out infinite;"></div>
        </div>
    ` : '';
    
    const loadingHTML = `
        <div style="text-align: center; padding: 30px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
            <div style="display: inline-block; width: 24px; height: 24px; border: 3px solid #e9ecef; border-top: 3px solid #0ea5e9; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 15px;"></div>
            <p style="color: #495057; margin: 0;">${sanitizeHTML(message)}</p>
            ${progressHTML}
        </div>
    `;
    
    if (typeof targetElement === 'string') {
        targetElement = document.getElementById(targetElement);
    }
    
    if (targetElement) {
        targetElement.innerHTML = loadingHTML;
    }
}

// ============================================
// ERROR HANDLING HELPERS
// ============================================

/**
 * ERROR HTML GENERATOR: Erstellt Error-HTML für Display
 */
function createErrorHTML(title, message = '') {
    return `
        <div style="padding: 20px; text-align: center; background: #fef2f2; border-radius: 8px; border: 1px solid #f87171;">
            <h3 style="color: #dc2626;">${sanitizeHTML(title)}</h3>
            ${message ? `<p style="color: #dc2626;">${sanitizeHTML(message)}</p>` : ''}
        </div>
    `;
}

/**
 * SUCCESS HTML GENERATOR: Erstellt Success-HTML für Display
 */
function createSuccessMessage(title, message = '') {
    return `
        <div style="padding: 20px; text-align: center; background: #f0fdf4; border-radius: 8px; border: 1px solid #22c55e;">
            <h3 style="color: #16a34a;">${sanitizeHTML(title)}</h3>
            ${message ? `<p style="color: #16a34a;">${sanitizeHTML(message)}</p>` : ''}
        </div>
    `;
}

/**
 * SHOW ERROR MESSAGE: Zeigt Error-Message in Element
 */
function showErrorMessage(element, title, message = '') {
    element.innerHTML = createErrorHTML(title, message);
}

/**
 * GRACEFUL ERROR HANDLING: Zeigt benutzerfreundliche Fehler mit Retry-Option
 */
function showGracefulError(errorType, message, targetElement = null, showRetry = false, retryCallback = null) {
    // Sammle Error-Details für Debugging (intern)
    const errorDetails = {
        type: errorType,
        message: message,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent
    };
    
    console.error('[GRACEFUL-ERROR]', errorDetails);
    
    // Benutzerfreundliche Error-Message
    let userFriendlyMessage = 'Ein unerwarteter Fehler ist aufgetreten.';
    
    switch (errorType) {
        case 'network':
            userFriendlyMessage = 'Netzwerkfehler. Bitte überprüfen Sie Ihre Internetverbindung.';
            break;
        case 'timeout':
            userFriendlyMessage = 'Die Anfrage hat zu lange gedauert. Bitte versuchen Sie es erneut.';
            break;
        case 'api':
            userFriendlyMessage = 'Serverfehler. Bitte versuchen Sie es später erneut.';
            break;
        case 'validation':
            userFriendlyMessage = 'Eingabefehler. Bitte überprüfen Sie Ihre Eingaben.';
            break;
        case 'permission':
            userFriendlyMessage = 'Zugriff verweigert. Sie haben nicht die erforderlichen Berechtigungen.';
            break;
    }
    
    const retryButton = showRetry && retryCallback ? `
        <button onclick="${retryCallback.name}()" 
                style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px;">
            🔄 Erneut versuchen
        </button>
    ` : '';
    
    const errorHTML = `
        <div style="padding: 20px; text-align: center; background: #fef2f2; border-radius: 8px; border: 1px solid #f87171; margin: 10px 0;">
            <div style="font-size: 48px; margin-bottom: 10px;">⚠️</div>
            <h3 style="color: #dc2626; margin-bottom: 10px;">${sanitizeHTML(userFriendlyMessage)}</h3>
            <p style="color: #7f1d1d; font-size: 14px; margin-bottom: 10px;">${sanitizeHTML(message)}</p>
            ${retryButton}
        </div>
    `;
    
    if (targetElement) {
        if (typeof targetElement === 'string') {
            targetElement = document.getElementById(targetElement);
        }
        if (targetElement) {
            targetElement.innerHTML = errorHTML;
        }
    }
    
    // Optional: Send error to logging service
    // if (window.errorLogger) {
    //     window.errorLogger.log(errorDetails);
    // }
}

/**
 * NO DETAILS AVAILABLE: Zeigt "Keine Details verfügbar" Message
 */
function showNoDetailsAvailable(targetElement, domain = null) {
    const message = domain ? 
        `Keine Details für Domain "${domain}" verfügbar.` : 
        'Keine Details verfügbar.';
    
    const html = `
        <div style="padding: 20px; text-align: center; background: #f9fafb; border-radius: 8px; border: 1px solid #d1d5db;">
            <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
            <h3 style="color: #6b7280; margin-bottom: 10px;">Keine Daten vorhanden</h3>
            <p style="color: #9ca3af;">${sanitizeHTML(message)}</p>
        </div>
    `;
    
    if (typeof targetElement === 'string') {
        targetElement = document.getElementById(targetElement);
    }
    
    if (targetElement) {
        targetElement.innerHTML = html;
    }
}

// ============================================
// NOTIFICATION SYSTEM
// ============================================

/**
 * NOTIFICATION SYSTEM: Zeigt Toast-ähnliche Benachrichtigungen
 */
function showNotification(message, type = 'info', icon = null) {
    // Prüfe ob bereits eine ähnliche Notification existiert
    const existingNotifications = document.querySelectorAll('.notification');
    for (let notification of existingNotifications) {
        if (notification.textContent.includes(message.substring(0, 30))) {
            return; // Verhindere Duplikate
        }
    }
    
    // Auto-Icon-Selection
    if (!icon) {
        switch (type) {
            case 'success': icon = '✅'; break;
            case 'error': icon = '❌'; break;
            case 'warning': icon = '⚠️'; break;
            case 'info': icon = 'ℹ️'; break;
            default: icon = '🔔'; break;
        }
    }
    
    // Color-Scheme basierend auf Type
    const colors = {
        success: { bg: '#f0fdf4', border: '#22c55e', text: '#16a34a' },
        error: { bg: '#fef2f2', border: '#f87171', text: '#dc2626' },
        warning: { bg: '#fffbeb', border: '#fbbf24', text: '#d97706' },
        info: { bg: '#eff6ff', border: '#60a5fa', text: '#2563eb' }
    };
    
    const color = colors[type] || colors.info;
    
    // Erstelle Notification-Element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            background: ${color.bg};
            border: 2px solid ${color.border};
            border-radius: 8px;
            padding: 16px 20px;
            max-width: 400px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideInRight 0.3s ease-out;
        ">
            <span style="font-size: 20px;">${icon}</span>
            <span style="color: ${color.text}; font-weight: 500; flex: 1;">${sanitizeHTML(message)}</span>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="background: none; border: none; color: ${color.text}; font-size: 18px; cursor: pointer; padding: 0; width: 24px; height: 24px;">
                ×
            </button>
        </div>
        <style>
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        </style>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove nach 5 Sekunden
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

// ============================================
// DOM MANIPULATION HELPERS
// ============================================

/**
 * DOCUMENT FRAGMENT CREATION: Performance-optimierte DOM-Manipulation
 */
function createDocumentFragment() {
    return document.createDocumentFragment();
}

/**
 * APPEND TO FRAGMENT: Element zu Fragment hinzufügen
 */
function appendToFragment(fragment, element) {
    if (typeof element === 'string') {
        const div = document.createElement('div');
        div.innerHTML = element;
        while (div.firstChild) {
            fragment.appendChild(div.firstChild);
        }
    } else {
        fragment.appendChild(element);
    }
}

/**
 * REPLACE CONTENT WITH FRAGMENT: Content mit Fragment ersetzen
 */
function replaceContentWithFragment(container, fragment) {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    if (container) {
        container.innerHTML = '';
        container.appendChild(fragment);
    }
}

// ============================================
// SEARCH TIMER HELPER
// ============================================

/**
 * STOP SEARCH TIMER: Stoppt den Such-Timer (vereinfacht - verwendet utils.js Timer)
 * FIX 11.08.2025: Vereinfacht zur Vermeidung von Timer-Konflikten
 */
function stopSearchTimer() {
    // Verwende das Master-Timer-System aus utils.js
    if (window.searchTimer && typeof window.searchTimer.stop === 'function') {
        window.searchTimer.stop();
    }
    
    // Reset des echten GUI-Timer-Elements
    const loadingTimer = document.getElementById('loading-timer');
    if (loadingTimer) {
        loadingTimer.textContent = '00:00';
    }
}

// ============================================
// EVENT COORDINATION HELPERS
// ============================================

/**
 * PREVENT EVENT CONFLICTS: Verhindert Event-Konflikte
 */
function preventEventConflicts(eventType, handler) {
    return function(...args) {
        try {
            const event = args[0];
            if (event && event.preventDefault) {
                event.preventDefault();
            }
            return handler.apply(this, args);
        } catch (error) {
            console.error(`Event handler error (${eventType}):`, error);
            showNotification(`Event-Fehler: ${error.message}`, 'error');
            return false;
        }
    };
}

/**
 * COORDINATE UI EVENT: Koordiniert UI-Events mit Error-Handling
 */
function coordinateUIEvent(eventName, eventHandler) {
    return preventEventConflicts(eventName, async function(...args) {
        try {
            console.log(`🎯 [UI-EVENT] ${eventName} triggered`);
            const result = await eventHandler.apply(this, args);
            console.log(`✅ [UI-EVENT] ${eventName} completed`);
            return result;
        } catch (error) {
            console.error(`❌ [UI-EVENT] ${eventName} failed:`, error);
            showGracefulError('ui', `${eventName} fehlgeschlagen: ${error.message}`);
            return false;
        }
    });
}

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export helper functions to global scope
window.escapeJavaScriptString = escapeJavaScriptString;
window.safeJSONStringify = safeJSONStringify;
window.safeSetHTML = safeSetHTML;
window.createLoadingHTML = createLoadingHTML;
window.showLoadingMessage = showLoadingMessage;
window.showEnhancedLoadingState = showEnhancedLoadingState;
window.createErrorHTML = createErrorHTML;
window.createSuccessMessage = createSuccessMessage;
window.showErrorMessage = showErrorMessage;
window.showGracefulError = showGracefulError;
window.showNoDetailsAvailable = showNoDetailsAvailable;
window.showNotification = showNotification;
window.createDocumentFragment = createDocumentFragment;
window.appendToFragment = appendToFragment;
window.replaceContentWithFragment = replaceContentWithFragment;
window.stopSearchTimer = stopSearchTimer;
window.preventEventConflicts = preventEventConflicts;
window.coordinateUIEvent = coordinateUIEvent;

console.log('🔧 MineSearch 2.0 - Helper Functions loaded');