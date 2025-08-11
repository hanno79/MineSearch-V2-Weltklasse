/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Auto-Refresh & Session Management
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (Phase 3 - Final Refactoring)
 * Auto-Refresh Functions: Timer Management, Inactivity Handling, Session Persistence
 */

// ============================================
// AUTO-REFRESH CONFIGURATION
// ============================================

/**
 * AUTO-REFRESH CONSTANTS
 */
const AUTO_REFRESH_INTERVAL = 30000; // 30 seconds
const INACTIVITY_TIMEOUT = 5 * 60 * 1000; // 5 minutes
const SESSION_RESTORE_TIMEOUT = 30 * 60 * 1000; // 30 minutes

// ============================================
// AUTO-REFRESH STATE MANAGEMENT
// ============================================

/**
 * AUTO-REFRESH STATE VARIABLES
 */
let autoRefreshInterval = null;
let userInactivityTimer = null;
let currentAutoRefreshTab = null;
let autoRefreshEnabled = true;

// ============================================
// CORE AUTO-REFRESH FUNCTIONS
// ============================================

/**
 * START AUTO REFRESH: Startet Auto-Refresh für einen Tab-Typ
 */
function startAutoRefresh(tabType) {
    console.log(`🔄 [AUTO-REFRESH] Starting auto-refresh for ${tabType} tab (every ${AUTO_REFRESH_INTERVAL/1000}s)`);
    
    // Stop existing auto-refresh
    stopAutoRefresh();
    
    // Check if auto-refresh is enabled
    if (!autoRefreshEnabled) {
        console.log('⚠️ [AUTO-REFRESH] Auto-refresh disabled - not starting');
        return;
    }
    
    // Store current tab for resuming after visibility change
    currentAutoRefreshTab = tabType;
    
    // Start new interval
    autoRefreshInterval = setInterval(() => {
        if (!document.hidden && autoRefreshEnabled) {
            console.log(`🔄 [AUTO-REFRESH] Auto-refreshing ${tabType} data...`);
            
            try {
                switch(tabType) {
                    case 'sources':
                        if (typeof loadSources === 'function') {
                            loadSources();
                        }
                        break;
                    case 'statistics':
                        if (typeof loadModelStatistics === 'function') {
                            loadModelStatistics();
                        }
                        break;
                    case 'results':
                        if (typeof loadResults === 'function') {
                            loadResults();
                        }
                        break;
                    case 'consolidated':
                        if (typeof loadConsolidatedResults === 'function') {
                            loadConsolidatedResults();
                        }
                        break;
                    default:
                        console.warn(`⚠️ [AUTO-REFRESH] Unknown tab type: ${tabType}`);
                }
            } catch (error) {
                console.error(`❌ [AUTO-REFRESH] Error auto-refreshing ${tabType}:`, error);
                // Don't stop auto-refresh on error, just log it
            }
        } else {
            console.log(`⏸️ [AUTO-REFRESH] Skipping refresh (hidden: ${document.hidden}, enabled: ${autoRefreshEnabled})`);
        }
    }, AUTO_REFRESH_INTERVAL);
    
    // Reset inactivity timer
    resetInactivityTimer();
    
    console.log(`✅ [AUTO-REFRESH] Auto-refresh started for ${tabType}`);
}

/**
 * STOP AUTO REFRESH: Stoppt Auto-Refresh
 */
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        console.log('🛑 [AUTO-REFRESH] Stopping auto-refresh');
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        currentAutoRefreshTab = null;
    }
}

/**
 * TOGGLE AUTO REFRESH: Schaltet Auto-Refresh an/aus
 */
function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;
    
    console.log(`🔄 [AUTO-REFRESH] Auto-refresh ${autoRefreshEnabled ? 'enabled' : 'disabled'}`);
    
    if (autoRefreshEnabled && currentAutoRefreshTab) {
        startAutoRefresh(currentAutoRefreshTab);
    } else {
        stopAutoRefresh();
    }
    
    // Update UI indicator if exists
    const indicator = document.getElementById('auto-refresh-indicator');
    if (indicator) {
        indicator.textContent = autoRefreshEnabled ? '🔄 Auto' : '⏸️ Pause';
        indicator.style.color = autoRefreshEnabled ? '#4CAF50' : '#F44336';
    }
    
    // Show notification
    showNotification(
        `Auto-Refresh ${autoRefreshEnabled ? 'aktiviert' : 'deaktiviert'}`, 
        autoRefreshEnabled ? 'success' : 'info'
    );
    
    // Store preference
    localStorage.setItem('autoRefreshEnabled', autoRefreshEnabled.toString());
}

// ============================================
// INACTIVITY MANAGEMENT
// ============================================

/**
 * RESET INACTIVITY TIMER: Setzt Inaktivitäts-Timer zurück
 */
function resetInactivityTimer() {
    // Clear existing timer
    if (userInactivityTimer) {
        clearTimeout(userInactivityTimer);
    }
    
    // Set new timer
    userInactivityTimer = setTimeout(() => {
        console.log('😴 [AUTO-REFRESH] User inactive, stopping auto-refresh');
        stopAutoRefresh();
        
        showNotification('Auto-Refresh wegen Inaktivität pausiert', 'info', '😴');
    }, INACTIVITY_TIMEOUT);
}

/**
 * SETUP ACTIVITY LISTENERS: Richtet Activity-Listener ein
 */
function setupActivityListeners() {
    // Activity events that should reset the inactivity timer
    const activityEvents = ['click', 'keypress', 'scroll', 'mousemove', 'touchstart'];
    
    activityEvents.forEach(eventType => {
        document.addEventListener(eventType, resetInactivityTimer, { passive: true });
    });
    
    console.log('👂 [AUTO-REFRESH] Activity listeners set up');
}

// ============================================
// VISIBILITY CHANGE HANDLING
// ============================================

/**
 * SETUP VISIBILITY LISTENER: Richtet Page-Visibility-Listener ein
 */
function setupVisibilityListener() {
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('👁️ [AUTO-REFRESH] Page hidden, pausing auto-refresh');
            // Don't stop completely, just pause
        } else {
            console.log('👁️ [AUTO-REFRESH] Page visible, checking for tab to restart auto-refresh');
            
            // Resume auto-refresh if it was active
            if (autoRefreshEnabled && currentAutoRefreshTab) {
                console.log(`🔄 [AUTO-REFRESH] Resuming auto-refresh for ${currentAutoRefreshTab}`);
                startAutoRefresh(currentAutoRefreshTab);
            } else {
                // Check active tab and start auto-refresh
                const activeTab = document.querySelector('input[name="tab"]:checked');
                if (activeTab && autoRefreshEnabled) {
                    startAutoRefresh(activeTab.value);
                }
            }
        }
    });
    
    console.log('👁️ [AUTO-REFRESH] Visibility change listener set up');
}

// ============================================
// SESSION MANAGEMENT
// ============================================

/**
 * SAVE SEARCH RESULTS: Speichert Suchergebnisse in Session Storage
 */
function saveSearchResults(results, type = 'search') {
    try {
        const timestamp = new Date().toISOString();
        const sessionData = {
            results: results,
            type: type,
            timestamp: timestamp,
            tabActive: document.querySelector('input[name="tab"]:checked')?.value
        };
        
        sessionStorage.setItem('lastSearchResults', JSON.stringify(sessionData));
        sessionStorage.setItem('lastSearchTimestamp', timestamp);
        
        console.log(`💾 [SESSION] Search results saved (${type})`);
    } catch (error) {
        console.error('❌ [SESSION] Error saving search results:', error);
    }
}

/**
 * SAVE BATCH HTML: Speichert Batch-HTML in Session Storage
 */
function saveBatchHTML(html) {
    try {
        sessionStorage.setItem('lastBatchHTML', html);
        sessionStorage.setItem('lastSearchTimestamp', new Date().toISOString());
        console.log('💾 [SESSION] Batch HTML saved');
    } catch (error) {
        console.error('❌ [SESSION] Error saving batch HTML:', error);
    }
}

/**
 * RESTORE RESULTS IF AVAILABLE: Stellt gespeicherte Ergebnisse wieder her
 */
function restoreResultsIfAvailable() {
    console.log('🔄 [SESSION] Checking for saved results to restore...');
    
    try {
        const savedResults = sessionStorage.getItem('lastSearchResults');
        const savedBatchHTML = sessionStorage.getItem('lastBatchHTML');
        const savedTimestamp = sessionStorage.getItem('lastSearchTimestamp');
        
        if (!savedResults && !savedBatchHTML) {
            console.log('ℹ️ [SESSION] No saved results found');
            return;
        }
        
        if (!savedTimestamp) {
            console.log('⚠️ [SESSION] No timestamp found for saved results');
            return;
        }
        
        // Check if results are still fresh (within 30 minutes)
        const timestamp = new Date(savedTimestamp);
        const minutesAgo = Math.floor((new Date() - timestamp) / 1000 / 60);
        
        if (minutesAgo >= 30) {
            console.log(`⏰ [SESSION] Saved results too old (${minutesAgo} minutes), not restoring`);
            return;
        }
        
        const resultsDiv = document.getElementById('results');
        if (!resultsDiv) {
            console.log('⚠️ [SESSION] Results div not found');
            return;
        }
        
        // Only restore if results area is empty or shows "no results"
        const currentContent = resultsDiv.innerHTML.trim();
        if (currentContent && !currentContent.includes('Keine Suchergebnisse')) {
            console.log('ℹ️ [SESSION] Results div already has content, not restoring');
            return;
        }
        
        if (savedBatchHTML) {
            resultsDiv.innerHTML = savedBatchHTML;
            showNotification(`🔄 Batch-Ergebnisse wiederhergestellt (${minutesAgo}min alt)`, 'info');
            console.log(`✅ [SESSION] Batch HTML restored (${minutesAgo} minutes old)`);
        } else if (savedResults) {
            const sessionData = JSON.parse(savedResults);
            if (sessionData.results && typeof displayResults === 'function') {
                displayResults(sessionData.results);
                showNotification(`🔄 Suchergebnisse wiederhergestellt (${minutesAgo}min alt)`, 'info');
                console.log(`✅ [SESSION] Search results restored (${minutesAgo} minutes old)`);
            }
        }
        
    } catch (error) {
        console.error('❌ [SESSION] Error restoring results:', error);
    }
}

/**
 * CLEAR SAVED RESULTS: Löscht gespeicherte Ergebnisse
 */
function clearSavedResults() {
    try {
        sessionStorage.removeItem('lastSearchResults');
        sessionStorage.removeItem('lastBatchHTML');
        sessionStorage.removeItem('lastSearchTimestamp');
        console.log('🗑️ [SESSION] Saved results cleared');
    } catch (error) {
        console.error('❌ [SESSION] Error clearing saved results:', error);
    }
}

/**
 * GET SESSION INFO: Gibt Session-Informationen zurück
 */
function getSessionInfo() {
    try {
        const savedResults = sessionStorage.getItem('lastSearchResults');
        const savedBatchHTML = sessionStorage.getItem('lastBatchHTML');
        const savedTimestamp = sessionStorage.getItem('lastSearchTimestamp');
        
        const info = {
            hasResults: !!savedResults,
            hasBatchHTML: !!savedBatchHTML,
            timestamp: savedTimestamp ? new Date(savedTimestamp) : null,
            minutesAgo: null,
            isValid: false
        };
        
        if (info.timestamp) {
            info.minutesAgo = Math.floor((new Date() - info.timestamp) / 1000 / 60);
            info.isValid = info.minutesAgo < 30;
        }
        
        return info;
    } catch (error) {
        console.error('❌ [SESSION] Error getting session info:', error);
        return { hasResults: false, hasBatchHTML: false, timestamp: null, minutesAgo: null, isValid: false };
    }
}

// ============================================
// AUTO-REFRESH STATUS & CONTROLS
// ============================================

/**
 * GET AUTO REFRESH STATUS: Gibt Auto-Refresh-Status zurück
 */
function getAutoRefreshStatus() {
    return {
        enabled: autoRefreshEnabled,
        active: !!autoRefreshInterval,
        currentTab: currentAutoRefreshTab,
        interval: AUTO_REFRESH_INTERVAL,
        inactivityTimeout: INACTIVITY_TIMEOUT
    };
}

/**
 * CREATE AUTO REFRESH INDICATOR: Erstellt Auto-Refresh-Indikator UI
 */
function createAutoRefreshIndicator() {
    const existingIndicator = document.getElementById('auto-refresh-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const indicator = document.createElement('div');
    indicator.id = 'auto-refresh-indicator';
    indicator.innerHTML = `
        <div style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: ${autoRefreshEnabled ? '#4CAF50' : '#F44336'};
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        " onclick="toggleAutoRefresh()" title="Auto-Refresh umschalten">
            ${autoRefreshEnabled ? '🔄' : '⏸️'} Auto
        </div>
    `;
    
    document.body.appendChild(indicator);
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * INITIALIZE AUTO REFRESH: Initialisiert Auto-Refresh-System
 */
function initializeAutoRefresh() {
    console.log('🚀 [AUTO-REFRESH] Initializing auto-refresh system...');
    
    // Load saved preference
    const savedPref = localStorage.getItem('autoRefreshEnabled');
    if (savedPref !== null) {
        autoRefreshEnabled = savedPref === 'true';
    }
    
    // Setup listeners
    setupActivityListeners();
    setupVisibilityListener();
    
    // Create UI indicator
    createAutoRefreshIndicator();
    
    // Initial inactivity timer
    resetInactivityTimer();
    
    console.log(`✅ [AUTO-REFRESH] Auto-refresh system initialized (enabled: ${autoRefreshEnabled})`);
}

// ============================================
// PAGE LOAD INITIALIZATION
// ============================================

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize auto-refresh system
    initializeAutoRefresh();
    
    // Restore results after a short delay
    setTimeout(() => {
        restoreResultsIfAvailable();
    }, 1000);
});

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export auto-refresh functions to global scope
window.startAutoRefresh = startAutoRefresh;
window.stopAutoRefresh = stopAutoRefresh;
window.toggleAutoRefresh = toggleAutoRefresh;
window.resetInactivityTimer = resetInactivityTimer;
window.restoreResultsIfAvailable = restoreResultsIfAvailable;
window.saveSearchResults = saveSearchResults;
window.saveBatchHTML = saveBatchHTML;
window.clearSavedResults = clearSavedResults;
window.getSessionInfo = getSessionInfo;
window.getAutoRefreshStatus = getAutoRefreshStatus;
window.initializeAutoRefresh = initializeAutoRefresh;

console.log('🔄 MineSearch 2.0 - Auto-Refresh Functions loaded');