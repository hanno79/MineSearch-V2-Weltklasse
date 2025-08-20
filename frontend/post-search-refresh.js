/**
 * Author: rahn
 * Datum: 19.08.2025
 * Version: 1.0
 * Beschreibung: Post-Search Auto-Refresh Orchestrator
 * 
 * KRITISCHER FIX: Automatische Tab-Aktualisierung nach Suchen
 * Stellt sicher, dass alle relevanten Tabs nach Suchen automatisch aktualisiert werden
 */

// ============================================
// POST-SEARCH REFRESH ORCHESTRATOR
// ============================================

/**
 * MASTER REFRESH ORCHESTRATOR: Orchestriert alle Tab-Refreshs nach Suchen
 */
function scheduleAllTabsRefresh(searchType = 'single', delayOffset = 0) {
    console.log(`🔄 [POST-SEARCH] Scheduling comprehensive refresh for ${searchType} search...`);
    
    // Timing Strategy: Gestaffelt für optimale Performance
    const baseDelay = 1000 + delayOffset; // Base 1 second + offset
    
    // 1. SOURCES TAB (schnellste Daten)
    scheduleSourcesRefresh(baseDelay);
    
    // 2. RESULTS TAB (benötigt DB-Zeit)  
    scheduleResultsRefresh(baseDelay + 1000);
    
    // 3. STATISTICS TAB (komplexeste Aggregation)
    if (typeof window.scheduleStatisticsRefresh === 'function') {
        window.scheduleStatisticsRefresh(baseDelay + 2000);
    }
    
    console.log(`📅 [POST-SEARCH] Scheduled refreshes: Sources(+${baseDelay}ms), Results(+${baseDelay + 1000}ms), Statistics(+${baseDelay + 2000}ms)`);
}

/**
 * SOURCES REFRESH: Plane Sources Tab Aktualisierung
 */
function scheduleSourcesRefresh(delayMs = 1000) {
    console.log(`⏰ [SOURCES-REFRESH] Scheduling sources refresh in ${delayMs}ms...`);
    
    setTimeout(() => {
        // Prüfe ob Sources Tab aktiv ist
        const sourcesTab = document.querySelector('[data-tab="sources"]');
        const isSourcesTabActive = sourcesTab && sourcesTab.classList.contains('active');
        
        if (isSourcesTabActive) {
            console.log('🔄 [SOURCES-REFRESH] Auto-refreshing sources after search completion...');
            if (typeof loadSources === 'function') {
                loadSources();
            } else {
                console.warn('⚠️ [SOURCES-REFRESH] loadSources function not available');
            }
        } else {
            console.log('💤 [SOURCES-REFRESH] Sources tab not active, skipping auto-refresh');
        }
    }, delayMs);
}

/**
 * RESULTS REFRESH: Plane Results Tab Aktualisierung  
 */
function scheduleResultsRefresh(delayMs = 2000) {
    console.log(`⏰ [RESULTS-REFRESH] Scheduling results refresh in ${delayMs}ms...`);
    
    setTimeout(() => {
        // Prüfe ob Results Tab aktiv ist
        const resultsTab = document.querySelector('[data-tab="results"]');
        const isResultsTabActive = resultsTab && resultsTab.classList.contains('active');
        
        if (isResultsTabActive) {
            console.log('🔄 [RESULTS-REFRESH] Auto-refreshing results after search completion...');
            if (typeof loadResults === 'function') {
                loadResults();
            } else {
                console.warn('⚠️ [RESULTS-REFRESH] loadResults function not available');
            }
        } else {
            console.log('💤 [RESULTS-REFRESH] Results tab not active, skipping auto-refresh');
        }
    }, delayMs);
}

/**
 * CONSOLIDATED REFRESH: Plane Consolidated Results Tab Aktualisierung
 */
function scheduleConsolidatedRefresh(delayMs = 2500) {
    console.log(`⏰ [CONSOLIDATED-REFRESH] Scheduling consolidated refresh in ${delayMs}ms...`);
    
    setTimeout(() => {
        // Prüfe ob Consolidated Tab aktiv ist
        const consolidatedTab = document.querySelector('[data-tab="consolidated"]');
        const isConsolidatedTabActive = consolidatedTab && consolidatedTab.classList.contains('active');
        
        if (isConsolidatedTabActive) {
            console.log('🔄 [CONSOLIDATED-REFRESH] Auto-refreshing consolidated results after search completion...');
            if (typeof loadConsolidatedResults === 'function') {
                loadConsolidatedResults();
            } else {
                console.warn('⚠️ [CONSOLIDATED-REFRESH] loadConsolidatedResults function not available');
            }
        } else {
            console.log('💤 [CONSOLIDATED-REFRESH] Consolidated tab not active, skipping auto-refresh');
        }
    }, delayMs);
}

/**
 * FORCE REFRESH ALL: Sofortiger Refresh aller Tabs (für manuelle Trigger)
 */
function forceRefreshAllTabs() {
    console.log('🚀 [FORCE-REFRESH] Force refreshing all tabs...');
    
    // Sources
    if (typeof loadSources === 'function') {
        loadSources();
    }
    
    // Results  
    if (typeof loadResults === 'function') {
        loadResults();
    }
    
    // Statistics
    if (typeof window.forceStatisticsRefresh === 'function') {
        window.forceStatisticsRefresh();
    }
    
    // Consolidated
    if (typeof loadConsolidatedResults === 'function') {
        loadConsolidatedResults();
    }
    
    console.log('✅ [FORCE-REFRESH] All tabs force refreshed');
}

/**
 * SMART REFRESH: Intelligenter Refresh basierend auf aktivem Tab
 */
function smartRefreshAfterSearch(searchType = 'single') {
    console.log(`🧠 [SMART-REFRESH] Analyzing optimal refresh strategy for ${searchType} search...`);
    
    // Erkenne aktiven Tab
    const activeTab = document.querySelector('[data-tab].active');
    const activeTabType = activeTab ? activeTab.getAttribute('data-tab') : null;
    
    console.log(`🧠 [SMART-REFRESH] Active tab: ${activeTabType || 'none'}`);
    
    // Optimierte Refresh-Strategie
    if (activeTabType === 'sources') {
        // Wenn Sources aktiv: Priorisiere Sources, dann andere
        scheduleSourcesRefresh(500);
        scheduleResultsRefresh(2000);
        if (typeof window.scheduleStatisticsRefresh === 'function') {
            window.scheduleStatisticsRefresh(3000);
        }
    } else if (activeTabType === 'statistics') {
        // Wenn Statistics aktiv: Priorisiere Statistics, dann andere
        if (typeof window.scheduleStatisticsRefresh === 'function') {
            window.scheduleStatisticsRefresh(1000);
        }
        scheduleSourcesRefresh(1500);
        scheduleResultsRefresh(2500);
    } else if (activeTabType === 'results') {
        // Wenn Results aktiv: Priorisiere Results, dann andere
        scheduleResultsRefresh(500);
        scheduleSourcesRefresh(1500);
        if (typeof window.scheduleStatisticsRefresh === 'function') {
            window.scheduleStatisticsRefresh(2500);
        }
    } else {
        // Default: Standard-Timing
        scheduleAllTabsRefresh(searchType);
    }
    
    console.log(`✅ [SMART-REFRESH] Smart refresh strategy applied for active tab: ${activeTabType}`);
}

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export all refresh functions to global scope
window.scheduleAllTabsRefresh = scheduleAllTabsRefresh;
window.scheduleSourcesRefresh = scheduleSourcesRefresh;
window.scheduleResultsRefresh = scheduleResultsRefresh;
window.scheduleConsolidatedRefresh = scheduleConsolidatedRefresh;
window.forceRefreshAllTabs = forceRefreshAllTabs;
window.smartRefreshAfterSearch = smartRefreshAfterSearch;

console.log('🚀 Post-Search Auto-Refresh Orchestrator loaded');