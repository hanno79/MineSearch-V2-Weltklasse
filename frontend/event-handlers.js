/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Event Handlers & DOM Coordination
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (Phase 3 - Final Refactoring)
 * Event Functions: HTMX Event Handlers, DOM Event Coordination, UI State Management
 */

// ============================================
// UI COORDINATION STATE
// ============================================

/**
 * UI COORDINATION STATE: Verwaltet UI-Zustand für Event-Koordination
 */
window.uiCoordinationState = {
    sortingInProgress: false,
    searchInProgress: false,
    eventQueue: [],
    lastEventTime: 0,
    activeAccordions: new Set(),
    maxEventQueueSize: 50
};

// ============================================
// CORE EVENT COORDINATION
// ============================================

/**
 * COORDINATE UI EVENT: Koordiniert UI-Events mit Error-Handling
 * Diese Funktion ist bereits in helpers.js definiert, wird aber hier referenziert
 */
// coordinateUIEvent wird von helpers.js bereitgestellt

// ============================================
// DOM CONTENT LOADED HANDLERS
// ============================================

/**
 * MAIN DOM CONTENT LOADED HANDLER: Haupt-Initialisierung
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 [EVENT-HANDLERS] MineSearch 2.0 - Event system initializing...');
    
    // Initialize various components
    initializeEventHandlers();
    
    // Setup model selection debugging
    console.log('🔍 [DEBUG] DOM is ready, checking model-selection element...');
    const modelSelection = document.getElementById('model-selection');
    if (modelSelection) {
        console.log('✅ [DEBUG] model-selection element found in DOM');
    } else {
        console.error('❌ [DEBUG] model-selection element NOT FOUND in DOM!');
    }
    
    // Initialize deduplication test if available
    if (typeof window.DeduplicationEngine !== 'undefined') {
        try {
            // Optional: Test basic functionality
            const testResult = window.DeduplicationEngine.deduplicate([
                { mine_name: "Test Mine", country: "Test" },
                { mine_name: "Test Mine", country: "Test" },
                { mine_name: "Other Mine", country: "Test" }
            ]);
            
            if (testResult && testResult.length === 2) {
                console.log('✅ [DEDUPLICATION] Basic functionality test passed.');
            } else {
                console.warn('⚠️ [DEDUPLICATION] Basic functionality test had unexpected result:', testResult);
            }
        } catch (error) {
            console.error('❌ [DEDUPLICATION] Test failed:', error);
        }
    }
    
    // Load model statistics if function is available
    if (typeof loadModelStatistics === 'function') {
        setTimeout(() => {
            console.log('🔄 [INIT] Auto-loading model statistics...');
            loadModelStatistics();
        }, 1000);
    }
});

/**
 * INITIALIZE EVENT HANDLERS: Richtet alle Event-Handler ein
 */
function initializeEventHandlers() {
    console.log('🎯 [EVENT-HANDLERS] Setting up event handlers...');
    
    // Setup HTMX event handlers
    setupHTMXEventHandlers();
    
    // Setup DOM interaction handlers
    setupDOMInteractionHandlers();
    
    // Setup tab navigation handlers
    setupTabNavigationHandlers();
    
    // Setup search method handlers
    setupSearchMethodHandlers();
    
    console.log('✅ [EVENT-HANDLERS] All event handlers initialized');
}

// ============================================
// HTMX EVENT HANDLERS
// ============================================

/**
 * SETUP HTMX EVENT HANDLERS: Richtet HTMX-spezifische Event-Handler ein
 */
function setupHTMXEventHandlers() {
    console.log('📡 [HTMX] Setting up HTMX event handlers...');
    
    // Before Request Handler
    htmx.on('htmx:beforeRequest', function(evt) {
        console.log('🚀 [HTMX] Request starting:', evt.detail.requestConfig.path);
        
        // Start search timer if available  
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.start) {
            window.searchTimer.start();
        }
        
        // Handle batch search requests
        if (evt.detail.requestConfig.path === '/api/batch-search') {
            console.log('🚀 [PARAMETER-COORDINATOR] Starting definitive parameter coordination');
            
            // Get selected models from UI
            const selectedModels = Array.from(document.querySelectorAll('input[name="model"]:checked')).map(cb => cb.value);
            console.log('🚀 [PARAMETER-COORDINATOR] Selected models from UI:', selectedModels);
            
            // Critical validation BEFORE request is sent
            if (selectedModels.length === 0) {
                console.error('❌ [PARAMETER-COORDINATOR] No models selected - aborting request');
                evt.preventDefault();
                showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
                return false;
            }
            
            // Update UI state
            uiCoordinationState.searchInProgress = true;
        }
        
        // Show loading animation
        const loadingIndicator = document.getElementById('loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
            loadingIndicator.style.animation = 'pulse 1.5s ease-in-out infinite';
        }
    });
    
    // Response Error Handler
    htmx.on('htmx:responseError', function(evt) {
        console.error('🚨 [HTMX] Request failed:', evt.detail.requestConfig.path, 'Status:', evt.detail.xhr.status);
        
        if (evt.detail.requestConfig.path === '/api/batch-search') {
            console.error('🚨 [RESPONSE-VALIDATOR] Batch search failed with status:', evt.detail.xhr.status);
            console.error('🚨 [RESPONSE-VALIDATOR] Response text:', evt.detail.xhr.responseText);
            
            // Handle specific 400 errors
            if (evt.detail.xhr.status === 400) {
                try {
                    const errorData = JSON.parse(evt.detail.xhr.responseText);
                    console.error('🚨 [RESPONSE-VALIDATOR] 400 Error Details:', errorData);
                    
                    let errorMessage = 'Batch-Suche fehlgeschlagen';
                    if (errorData.detail && errorData.detail.includes('no models')) {
                        errorMessage = 'Keine Modelle ausgewählt. Bitte wählen Sie mindestens ein Modell aus.';
                    }
                    
                    showNotification(errorMessage, 'error');
                } catch (parseError) {
                    console.error('❌ [RESPONSE-VALIDATOR] Error parsing 400 response:', parseError);
                    showNotification('Batch-Suche fehlgeschlagen: Ungültige Parameter', 'error');
                }
            } else if (evt.detail.xhr.status === 500) {
                showNotification('Serverfehler bei Batch-Suche. Bitte versuchen Sie es erneut.', 'error');
            } else {
                showNotification(`Batch-Suche fehlgeschlagen (${evt.detail.xhr.status})`, 'error');
            }
        }
        
        // Reset search state
        uiCoordinationState.searchInProgress = false;
        
        // Hide loading indicator
        const loadingIndicator = document.getElementById('loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    });
    
    // After Request Handler
    htmx.on('htmx:afterRequest', function(evt) {
        console.log('✅ [HTMX] Request completed:', evt.detail.requestConfig.path);
        
        if (evt.detail.requestConfig.path === '/api/batch-search' && evt.detail.successful) {
            console.log('✅ [RESPONSE-VALIDATOR] Batch search request successful');
            console.log('✅ [RESPONSE-VALIDATOR] Response length:', evt.detail.xhr.responseText.length);
        }
        
        // Stop search timer if available
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        // Reset search state
        uiCoordinationState.searchInProgress = false;
        
        // Hide loading indicator
        const loadingIndicator = document.getElementById('loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
            loadingIndicator.style.animation = '';
        }
    });
    
    console.log('✅ [HTMX] HTMX event handlers set up');
}

// ============================================
// DOM INTERACTION HANDLERS
// ============================================

/**
 * SETUP DOM INTERACTION HANDLERS: Richtet DOM-Interaktions-Handler ein
 */
function setupDOMInteractionHandlers() {
    console.log('🖱️ [DOM] Setting up DOM interaction handlers...');
    
    // Global click handler for batch interactions
    document.addEventListener('click', function(evt) {
        // Detect batch form interactions
        const isSearchAllButton = evt.target.matches('button[name="search_all"]');
        const isBatchFormElement = evt.target.closest('form') && evt.target.closest('form').id === 'batch-form';
        const isBatchFormButton = evt.target.type === 'submit' && evt.target.closest('#batch-form');
        
        if (isSearchAllButton || isBatchFormElement || isBatchFormButton) {
            console.log('🔄 [PROACTIVE-SYNC] Batch interaction detected - triggering proactive sync');
            
            // Immediate synchronization (before HTMX beforeRequest)
            const batchForm = document.getElementById('batch-form');
            if (batchForm && typeof synchronizeBatchParameters === 'function') {
                synchronizeBatchParameters(batchForm);
            }
        }
        
        // Track click in event queue
        uiCoordinationState.eventQueue.push({
            type: 'click',
            target: evt.target.tagName + (evt.target.id ? '#' + evt.target.id : ''),
            timestamp: Date.now()
        });
        
        // Limit event queue size
        if (uiCoordinationState.eventQueue.length > uiCoordinationState.maxEventQueueSize) {
            uiCoordinationState.eventQueue.shift();
        }
    });
    
    // Keyboard interaction handler
    document.addEventListener('keydown', function(evt) {
        // Handle escape key for modals
        if (evt.key === 'Escape') {
            // Close any open modals
            const modals = document.querySelectorAll('[style*="position: fixed"][style*="z-index"]');
            modals.forEach(modal => {
                if (modal.style.zIndex >= 1000) {
                    modal.remove();
                }
            });
        }
        
        // Handle keyboard shortcuts
        if (evt.ctrlKey || evt.metaKey) {
            switch (evt.key) {
                case 'r':
                    // Ctrl+R: Refresh current tab data
                    evt.preventDefault();
                    refreshCurrentTabData();
                    break;
                case 's':
                    // Ctrl+S: Start search (if form is visible)
                    if (document.querySelector('#single-search-form:not([style*="display: none"])')) {
                        evt.preventDefault();
                        if (typeof startSingleSearch === 'function') {
                            startSingleSearch();
                        }
                    }
                    break;
            }
        }
    });
    
    console.log('✅ [DOM] DOM interaction handlers set up');
}

// ============================================
// TAB NAVIGATION HANDLERS
// ============================================

/**
 * SETUP TAB NAVIGATION HANDLERS: Richtet Tab-Navigation-Handler ein
 */
function setupTabNavigationHandlers() {
    console.log('📑 [TABS] Setting up tab navigation handlers...');
    
    // Tab change handler
    const tabRadios = document.querySelectorAll('input[name="tab"]');
    tabRadios.forEach(radio => {
        radio.addEventListener('change', function(evt) {
            if (evt.target.checked) {
                const tabValue = evt.target.value;
                console.log(`📑 [TABS] Tab changed to: ${tabValue}`);
                
                // Handle tab-specific loading
                handleTabChange(tabValue);
                
                // Start auto-refresh for the new tab if enabled
                if (typeof startAutoRefresh === 'function') {
                    startAutoRefresh(tabValue);
                }
            }
        });
    });
    
    // Observer for tab activation (alternative method)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target.classList.contains('active') && target.textContent.includes('Statistiken')) {
                    // Statistics tab was activated - auto-load data
                    setTimeout(() => {
                        if (typeof loadModelStatistics === 'function') {
                            loadModelStatistics();
                        }
                    }, 500);
                }
            }
        });
    });
    
    // Start observing tab elements
    const tabElements = document.querySelectorAll('.tab-label, .tab-button');
    tabElements.forEach(element => {
        observer.observe(element, { attributes: true, attributeFilter: ['class'] });
    });
    
    console.log('✅ [TABS] Tab navigation handlers set up');
}

// ============================================
// SEARCH METHOD HANDLERS
// ============================================

/**
 * SETUP SEARCH METHOD HANDLERS: Richtet Search-Method-Handler ein
 */
function setupSearchMethodHandlers() {
    console.log('🔍 [SEARCH] Setting up search method handlers...');
    
    // Search method change handler
    function handleSearchMethodChange() {
        const activeTab = document.querySelector('input[name="tab"]:checked');
        if (!activeTab) return;
        
        const tabValue = activeTab.value;
        console.log(`🔍 [SEARCH] Search method change detected for tab: ${tabValue}`);
        
        // Load appropriate data based on active tab
        switch (tabValue) {
            case 'sources':
                if (typeof loadSources === 'function') {
                    loadSources();
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
            case 'statistics':
                if (typeof loadModelStatistics === 'function') {
                    loadModelStatistics();
                }
                break;
        }
    }
    
    // DEAKTIVIERT: Alte search_method inputs wurden entfernt - Event-Handler nicht mehr nötig
    // const searchMethodInputs = document.querySelectorAll('input[name="search_method"], select[name="search_method"]');
    // searchMethodInputs.forEach(input => {
    //     input.addEventListener('change', handleSearchMethodChange);
    // });
    
    console.log('✅ [SEARCH] Search method handlers set up');
}

// ============================================
// TAB HANDLING FUNCTIONS
// ============================================

/**
 * HANDLE TAB CHANGE: Behandelt Tab-Wechsel
 */
function handleTabChange(tabValue) {
    console.log(`🔄 [TAB-SWITCH] Switching to tab: ${tabValue}`);
    
    // Show appropriate loading state
    const targetContainerId = getTabContainerId(tabValue);
    if (targetContainerId) {
        const container = document.getElementById(targetContainerId);
        if (container) {
            showEnhancedLoadingState(container, `🔄 [TAB-SWITCH] Loading ${tabValue} data...`, true);
        }
    }
    
    // Load data for the selected tab
    setTimeout(() => {
        switch (tabValue) {
            case 'sources':
                console.log('🔄 [TAB-SWITCH] Loading sources data...');
                if (typeof loadSources === 'function') {
                    loadSources();
                }
                break;
            case 'results':
                console.log('🔄 [TAB-SWITCH] Loading results data...');
                if (typeof loadResults === 'function') {
                    loadResults();
                }
                break;
            case 'consolidated':
                console.log('🔄 [TAB-SWITCH] Loading consolidated results...');
                if (typeof loadConsolidatedResults === 'function') {
                    loadConsolidatedResults();
                }
                break;
            case 'statistics':
                console.log('🔄 [TAB-SWITCH] Loading model statistics...');
                if (typeof loadModelStatistics === 'function') {
                    loadModelStatistics();
                }
                break;
            default:
                console.warn(`⚠️ [TAB-SWITCH] Unknown tab: ${tabValue}`);
        }
    }, 100);
}

/**
 * GET TAB CONTAINER ID: Gibt Container-ID für Tab zurück
 */
function getTabContainerId(tabValue) {
    const containerMap = {
        'sources': 'sources-table-container',
        'results': 'results-table-container', 
        'consolidated': 'consolidated-results-container',
        'statistics': 'model-statistics-container'
    };
    
    return containerMap[tabValue] || null;
}

/**
 * REFRESH CURRENT TAB DATA: Aktualisiert Daten des aktiven Tabs
 */
function refreshCurrentTabData() {
    const activeTab = document.querySelector('input[name="tab"]:checked');
    if (activeTab) {
        console.log(`🔄 [REFRESH] Refreshing current tab: ${activeTab.value}`);
        handleTabChange(activeTab.value);
        showNotification(`${activeTab.value} Daten werden aktualisiert...`, 'info');
    }
}

// ============================================
// COORDINATED UI FUNCTIONS
// ============================================

/**
 * COORDINATED TABLE SORT: Koordinierte Tabellen-Sortierung
 */
window.loadSourcesWithSort = coordinateUIEvent('TableSort', function(sortBy) {
    console.log(`🔄 [SORT] Enhanced sorting toggle for '${sortBy}' - current: ${window.currentSortBy}/${window.currentSortOrder}`);
    
    // Prevent sorting if already in progress
    if (uiCoordinationState.sortingInProgress) {
        console.log('⚠️ [SORT] Sorting already active - aborted');
        return;
    }
    
    uiCoordinationState.sortingInProgress = true;
    
    // Toggle logic: Same field changes direction, new field starts DESC
    if (window.currentSortBy === sortBy) {
        // Same column: Toggle ASC ↔ DESC
        window.currentSortOrder = window.currentSortOrder === 'desc' ? 'asc' : 'desc';
        console.log(`✅ [SORT] Toggle same column: ${sortBy} → ${window.currentSortOrder}`);
    } else {
        // New column: Start with DESC (except for text fields)
        window.currentSortBy = sortBy;
        window.currentSortOrder = (sortBy === 'domain') ? 'asc' : 'desc';
        console.log(`✅ [SORT] New column: ${sortBy} → ${window.currentSortOrder}`);
    }
    
    // Execute sort
    if (typeof loadSources === 'function') {
        loadSources(window.currentSortBy, window.currentSortOrder);
    }
    
    // Reset sorting state after delay
    setTimeout(() => {
        uiCoordinationState.sortingInProgress = false;
    }, 1000);
});

/**
 * COORDINATED DETAILS TOGGLE: Koordiniertes Details-Toggle
 */
window.toggleSourceDetails = coordinateUIEvent('DetailsToggle', async function(event, domain) {
    const detailsRow = document.getElementById(`details-${domain}`);
    const contentDiv = document.getElementById(`content-${domain}`);
    const button = event?.target?.closest('button') || event?.currentTarget;
    
    if (!detailsRow || !contentDiv) {
        console.error(`❌ [DETAILS] Details elements not found for domain: ${domain}`);
        return;
    }
    
    const isCurrentlyOpen = detailsRow.style.display === 'table-row' || detailsRow.classList.contains('expanded');
    
    if (!isCurrentlyOpen) {
        // Open details
        console.log(`📂 [DETAILS] Opening details for: ${domain}`);
        detailsRow.style.display = 'table-row';
        detailsRow.classList.add('expanded');
        
        if (button) {
            button.classList.add('active');
            button.style.background = '#059669';
            button.style.color = 'white';
        }
        
        // Load enhanced source details if function exists
        if (typeof loadEnhancedSourceDetails === 'function') {
            loadEnhancedSourceDetails(domain, contentDiv);
        }
        
        uiCoordinationState.activeAccordions.add(domain);
    } else {
        // Close details
        console.log(`📁 [DETAILS] Closing details for: ${domain}`);
        detailsRow.style.display = 'none';
        detailsRow.classList.remove('expanded');
        
        if (button) {
            button.classList.remove('active');
            button.style.background = '#3b82f6';
            button.style.color = 'white';
        }
        
        uiCoordinationState.activeAccordions.delete(domain);
    }
});

// ============================================
// EVENT QUEUE MANAGEMENT
// ============================================

/**
 * GET EVENT QUEUE STATUS: Gibt Event-Queue-Status zurück
 */
function getEventQueueStatus() {
    return {
        queueLength: uiCoordinationState.eventQueue.length,
        lastEvent: uiCoordinationState.eventQueue[uiCoordinationState.eventQueue.length - 1],
        sortingInProgress: uiCoordinationState.sortingInProgress,
        searchInProgress: uiCoordinationState.searchInProgress,
        activeAccordions: Array.from(uiCoordinationState.activeAccordions)
    };
}

/**
 * CLEAR EVENT QUEUE: Leert Event-Queue
 */
function clearEventQueue() {
    uiCoordinationState.eventQueue = [];
    console.log('🗑️ [EVENT-QUEUE] Event queue cleared');
}

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export event handling functions to global scope
window.initializeEventHandlers = initializeEventHandlers;
window.setupHTMXEventHandlers = setupHTMXEventHandlers;
window.setupDOMInteractionHandlers = setupDOMInteractionHandlers;
window.setupTabNavigationHandlers = setupTabNavigationHandlers;
window.handleTabChange = handleTabChange;
window.refreshCurrentTabData = refreshCurrentTabData;
window.getEventQueueStatus = getEventQueueStatus;
window.clearEventQueue = clearEventQueue;

console.log('🎯 MineSearch 2.0 - Event Handlers loaded');