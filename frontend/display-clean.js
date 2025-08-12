/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 2.0
 * Beschreibung: CLEAN VERSION - Nur die 3 revolutionären Display-Funktionen
 * 
 * PHASE 3: TABELLEN-REVOLUTION ABGESCHLOSSEN
 * Alle hässlichen Tabellen durch wunderschöne Data-Cards ersetzt
 */

/**
 * CONSOLIDATED RESULTS DISPLAY: Zeigt konsolidierte Ergebnisse mit modernen Data-Cards
 */
function displayConsolidatedResults(data, sortBy, order) {
    console.log(`🎨 [DISPLAY] Rendering consolidated results with DATA-CARDS (${data.consolidated_results?.length || 0} mines)`);
    
    const container = document.getElementById('consolidated-table-container');
    if (!container) return;
    
    if (!data.consolidated_results || data.consolidated_results.length === 0) {
        container.innerHTML = createErrorHTML(
            'Keine konsolidierten Ergebnisse verfügbar',
            'Es wurden keine konsolidierten Daten gefunden.'
        );
        return;
    }
    
    // 🚀 REVOLUTION: Verwende moderne Data-Cards statt hässlicher Tabelle
    renderDataCardGrid(data.consolidated_results, container, 'consolidated');
}

/**
 * RESULTS TABLE DISPLAY: Zeigt Suchergebnisse mit modernen Data-Cards
 */
function displayResultsTable(results, sortBy, order) {
    console.log(`🎨 [DISPLAY] Rendering results with DATA-CARDS (${results?.length || 0} results)`);
    
    const container = document.getElementById('results-table-container');
    if (!container) return;
    
    if (!results || results.length === 0) {
        container.innerHTML = createErrorHTML(
            'Keine Ergebnisse verfügbar',
            'Es wurden keine Suchergebnisse gefunden.'
        );
        return;
    }
    
    // 🚀 REVOLUTION: Verwende moderne Data-Cards statt hässlicher Tabelle  
    renderDataCardGrid(results, container, 'search_result');
}

/**
 * GROUPED SOURCES DISPLAY: Zeigt gruppierte Quellen-Daten mit modernen Data-Cards
 */
function displayGroupedSources(data, currentSort = 'count', currentOrder = 'desc') {
    console.log(`🎨 [DISPLAY] Rendering grouped sources with DATA-CARDS (${data.grouped_sources?.length || 0} groups)`);
    
    const container = document.getElementById('sources-table-container');
    if (!container) return;
    
    if (!data.grouped_sources || data.grouped_sources.length === 0) {
        container.innerHTML = createErrorHTML(
            'Keine Quellen verfügbar',
            'Es wurden keine Quellen-Daten gefunden.'
        );
        return;
    }
    
    // 🚀 REVOLUTION: Verwende moderne Data-Cards für Quellen-Übersicht
    renderDataCardGrid(data.grouped_sources, container, 'sources');
}

/**
 * MODEL STATISTICS DISPLAY: Zeigt Modell-Statistiken mit modernen Data-Cards
 */
function displayComprehensiveModelStatistics(data) {
    console.log('📊 [STATISTICS] Displaying comprehensive model statistics with DATA-CARDS');
    
    const targetElement = document.getElementById('model-statistics-table-container');
    if (!targetElement) {
        console.error('❌ [STATISTICS] model-statistics-table-container element not found!');
        return;
    }
    
    const models = data.models || [];
    if (models.length === 0) {
        targetElement.innerHTML = '<div class="no-data">Keine Modell-Statistiken verfügbar</div>';
        return;
    }
    
    // 🚀 REVOLUTION: Verwende moderne Data-Cards für Modell-Statistiken
    renderDataCardGrid(models, targetElement, 'model_stats');
}

/**
 * Error-HTML-Generator (Helper-Funktion)
 */
function createErrorHTML(title, message) {
    return `
        <div style="text-align: center; padding: var(--space-xl); color: var(--gray-500);">
            <h3>${title}</h3>
            <p>${message}</p>
        </div>
    `;
}