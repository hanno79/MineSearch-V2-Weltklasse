/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Core Utility Functions
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (8961 → 500 Zeilen Regel)
 * Core Utilities: Security, Validation, HTML Generation, Timing
 */

// ============================================
// SECURITY & VALIDATION FUNCTIONS
// ============================================

// SECURITY: Sichere Hilfsfunktion für HTML-Injection
function sanitizeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// SECURITY: Sichere JavaScript-String-Escaping für onclick-Handler
function escapeJavaScriptString(str) {
    if (!str) return '';
    // Escape alle kritischen Zeichen für JavaScript-Strings
    return str
        .replace(/\\/g, '\\\\')    // Backslash zuerst escapen
        .replace(/'/g, "\\'")      // Single quotes escapen
        .replace(/"/g, '\\"')      // Double quotes escapen
        .replace(/\n/g, '\\n')     // Newlines escapen
        .replace(/\r/g, '\\r')     // Carriage returns escapen
        .replace(/\t/g, '\\t')     // Tabs escapen
        .replace(/\f/g, '\\f')     // Form feeds escapen
        .replace(/\v/g, '\\v')     // Vertical tabs escapen
        .replace(/\0/g, '\\0');    // Null bytes escapen
}

// SECURITY: Alternative Lösung - JSON.stringify für sichere String-Übergabe
function safeJSONStringify(str) {
    if (!str) return "''";
    return JSON.stringify(str);
}

// SECURITY: Sichere Funktion für innerHTML-Replacement
function safeSetHTML(element, html) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (!element) return;
    
    // Erstelle ein neues Element
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Entferne alle Script-Tags
    const scripts = tempDiv.querySelectorAll('script');
    scripts.forEach(script => script.remove());
    
    // Setze den gefilterten Inhalt
    element.innerHTML = tempDiv.innerHTML;
}

// ============================================
// FIELD TYPE DETECTION & DATA UTILITIES
// ============================================

// Feldtyp-Erkennung für intelligente Synonym-Deduplizierung
function detectFieldType(fieldName) {
    const typeMapping = {
        'country': 'country',
        'land': 'country', 
        'country_name': 'country',
        'region': 'region',
        'province': 'region',
        'state': 'region',
        'quebec': 'region',
        'status': 'status',
        'mine_status': 'status',
        'operation_status': 'status',
        'mineral': 'mineral',
        'commodity': 'mineral',
        'primary_mineral': 'mineral',
        'primary_commodity': 'mineral'
    };
    
    const fieldLower = fieldName.toLowerCase();
    
    // Exakte Übereinstimmung
    if (typeMapping[fieldLower]) {
        return typeMapping[fieldLower];
    }
    
    // Teilstring-Suche für zusammengesetzte Feldnamen
    for (const [key, type] of Object.entries(typeMapping)) {
        if (fieldLower.includes(key)) {
            return type;
        }
    }
    
    return 'general';
}

// Helper functions for field difficulty analysis
function getFieldDifficulty(successRate) {
    if (successRate >= 80) {
        return { label: "Sehr Einfach", color: "#28a745", description: "Wird fast immer gefunden" };
    } else if (successRate >= 60) {
        return { label: "Einfach", color: "#007bff", description: "Meist erfolgreich gefunden" };
    } else if (successRate >= 40) {
        return { label: "Mittel", color: "#ffc107", description: "Moderate Erfolgsrate" };
    } else if (successRate >= 20) {
        return { label: "Schwer", color: "#fd7e14", description: "Niedrige Erfolgsrate" };
    } else {
        return { label: "Sehr Schwer", color: "#dc3545", description: "Selten erfolgreich" };
    }
}

// ============================================
// TIMING & PERFORMANCE UTILITIES
// ============================================

// LÖSUNG 14.07.2025: Timer für Suchdauer-Anzeige
const searchTimer = {
    startTime: null,
    intervalId: null,
    
    start: function() {
        this.startTime = Date.now();
        this.intervalId = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            
            // Aktualisiere das echte GUI-Timer-Element
            const loadingTimer = document.getElementById('loading-timer');
            if (loadingTimer) {
                loadingTimer.textContent = this.formatTime(elapsed);
            }
            
            // Fallback: Aktualisiere auch .search-timer Elemente falls vorhanden
            const timerElements = document.querySelectorAll('.search-timer');
            timerElements.forEach(el => {
                el.textContent = this.formatTime(elapsed);
            });
        }, 1000);
    },
    
    stop: function() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },
    
    formatTime: function(totalSeconds) {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
};

// Export timer to global scope for other modules
window.searchTimer = searchTimer;

// ============================================
// HTML GENERATION UTILITIES
// ============================================

function createLoadingHTML(title, message = '', showSpinner = true, showTimer = false, showCancelButton = false, cancelFunction = '') {
    const spinnerHTML = showSpinner ? `
        <div style="margin-top: 10px;">
            <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #0ea5e9; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
    ` : '';
    
    // Timer wird über #loading-timer im HTML angezeigt - kein extra Element nötig
    const timerHTML = '';
    
    // Cancel Button nur für Batch-Operationen
    const cancelButtonHTML = showCancelButton && cancelFunction ? `
        <div style="margin-top: 15px;">
            <button onclick="${cancelFunction}" 
                    style="
                        background: #ef4444; 
                        color: white; 
                        border: none; 
                        padding: 8px 16px; 
                        border-radius: 6px; 
                        cursor: pointer; 
                        font-size: 14px;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                    "
                    onmouseover="this.style.background='#dc2626'"
                    onmouseout="this.style.background='#ef4444'">
                🛑 Abbrechen
            </button>
        </div>
    ` : '';
    
    return `
        <div style="padding: 20px; text-align: center; background: #f0f9ff; border-radius: 8px; border: 1px solid #0ea5e9;">
            <h3>${sanitizeHTML(title)}</h3>
            ${message ? `<p>${sanitizeHTML(message)}</p>` : ''}
            ${timerHTML}
            ${spinnerHTML}
            ${cancelButtonHTML}
        </div>
    `;
}

function showLoadingMessage(element, title, message = '', startTimer = false, showCancelButton = false, cancelFunction = '') {
    element.innerHTML = createLoadingHTML(title, message, true, startTimer, showCancelButton, cancelFunction);
    
    if (startTimer) {
        searchTimer.start();
    }
}

function stopSearchTimer() {
    searchTimer.stop();
}

function createErrorHTML(title, message = '') {
    return `
        <div style="padding: 20px; text-align: center; background: #fef2f2; border-radius: 8px; border: 1px solid #f87171;">
            <h3 style="color: #dc2626;">${sanitizeHTML(title)}</h3>
            ${message ? `<p style="color: #dc2626;">${sanitizeHTML(message)}</p>` : ''}
        </div>
    `;
}

// ============================================
// EXPORT & FILE UTILITIES
// ============================================

function exportModelData(modelId) {
    console.log(`📊 Exporting data for model: ${modelId}`);
    showNotification('📊 Model-Daten werden exportiert...', 'info');
    
    // Export als CSV über API
    const exportUrl = `${window.API_BASE_URL}/api/statistics/export/csv?table=models&model_id=${encodeURIComponent(modelId)}&days_back=30`;
    
    // Erstelle unsichtbaren Download-Link
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = `model_${modelId}_statistics.csv`;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('✅ Model-Daten erfolgreich exportiert', 'success');
}

// ============================================
// NOTIFICATION SYSTEM
// ============================================

function showNotification(message, type = 'info') {
    // Simple notification system - kann später erweitert werden
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Optional: Toast notification creation
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 6px;
        z-index: 10000;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 300px;
        word-wrap: break-word;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// ============================================
// BROWSER COMPATIBILITY & FEATURE DETECTION
// ============================================

function checkBrowserSupport() {
    const features = {
        fetch: typeof fetch !== 'undefined',
        promise: typeof Promise !== 'undefined',
        arrow: function() { try { eval('() => {}'); return true; } catch(e) { return false; } }(),
        const: function() { try { eval('const x = 1'); return true; } catch(e) { return false; } }()
    };
    
    const unsupported = Object.entries(features)
        .filter(([key, value]) => !value)
        .map(([key]) => key);
    
    if (unsupported.length > 0) {
        console.warn('Browser compatibility issues detected:', unsupported);
        showNotification(`Browser-Kompatibilitätsprobleme: ${unsupported.join(', ')}`, 'error');
        return false;
    }
    
    return true;
}

// ============================================
// INITIALIZATION
// ============================================

// Browser-Support beim Laden prüfen
document.addEventListener('DOMContentLoaded', function() {
    checkBrowserSupport();
    console.log('🔧 MineSearch Utils initialized');
});

console.log('📚 MineSearch 2.0 - Core Utilities loaded');