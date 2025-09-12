/**
 * Author: rahn
 * Datum: 11.09.2025
 * Version: 1.0
 * Beschreibung: Vereinfachte Display-Logik für das neue 3-Ebenen-Layout
 * 
 * Ersetzt die komplexe Comparison-Display-Logik durch eine saubere,
 * nutzerfreundliche Anzeige basierend auf SearchResultCard.
 */

// ============================================
// HAUPTFUNKTION: VERGLEICHSERGEBNIS ANZEIGEN
// ============================================

/**
 * ZENTRALE DISPLAY-FUNKTION: Zeigt Multi-Model-Vergleich als kompakte Karte
 */
function displaySearchComparison(comparisonResult, targetElementId = 'results') {
    console.log('🎯 [SIMPLIFIED-DISPLAY] Zeige Vergleichsergebnis:', comparisonResult);
    
    const targetElement = document.getElementById(targetElementId);
    if (!targetElement) {
        console.error('❌ [SIMPLIFIED-DISPLAY] Target-Element nicht gefunden:', targetElementId);
        return;
    }
    
    // Speichere Ergebnis global für Interaktionen
    window.lastComparisonResult = comparisonResult;
    
    // Prüfe ob gültige Vergleichsdaten vorhanden
    if (!comparisonResult || !comparisonResult.consensus) {
        targetElement.innerHTML = generateErrorDisplay('Keine gültigen Vergleichsdaten erhalten');
        return;
    }
    
    // Generiere neue Card-basierte Anzeige
    const cardHTML = generateSearchResultCard(comparisonResult);
    
    // Zeige Results-Container und füge Card hinzu
    targetElement.style.display = 'block';
    targetElement.innerHTML = `
        <div class="search-results-header">
            <h3>🎯 Suchergebnis</h3>
            <div class="results-meta">
                <span class="model-count">${comparisonResult.models?.length || 0} Modelle</span>
                <span class="consensus-count">${comparisonResult.consensus?.strongConsensus?.length || 0} starke Übereinstimmungen</span>
                <span class="timestamp">${new Date().toLocaleString('de-DE')}</span>
            </div>
        </div>
        
        <div class="search-results-content">
            ${cardHTML}
        </div>
        
        <div class="search-results-actions">
            <button class="action-button secondary" onclick="showRawComparisonData()" title="Zeige technische Details">
                🔬 Technische Analyse
            </button>
            <button class="action-button secondary" onclick="exportSearchResult()" title="Ergebnis exportieren">
                📤 Exportieren
            </button>
            <button class="action-button" onclick="startNewSearch()" title="Neue Suche starten">
                🔍 Neue Suche
            </button>
        </div>
    `;
    
    // Scroll zu Ergebnissen
    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    console.log('✅ [SIMPLIFIED-DISPLAY] Ergebnis erfolgreich angezeigt');
}

/**
 * BATCH RESULTS: Zeigt mehrere Suchergebnisse für Batch-Processing
 */
function displayBatchResults(batchResults, targetElementId = 'batch-results') {
    console.log('📊 [SIMPLIFIED-DISPLAY] Zeige Batch-Ergebnisse:', batchResults.length, 'Ergebnisse');
    
    const targetElement = document.getElementById(targetElementId);
    if (!targetElement) {
        console.error('❌ [SIMPLIFIED-DISPLAY] Batch Target-Element nicht gefunden:', targetElementId);
        return;
    }
    
    if (!batchResults || batchResults.length === 0) {
        targetElement.innerHTML = generateErrorDisplay('Keine Batch-Ergebnisse verfügbar');
        return;
    }
    
    // Statistiken berechnen
    const totalResults = batchResults.length;
    const successfulResults = batchResults.filter(r => r.success && r.comparison).length;
    const highQualityResults = batchResults.filter(r => 
        r.success && r.comparison && calculateCardQualityScore(r.comparison) >= 70
    ).length;
    
    // Header generieren
    const headerHTML = `
        <div class="batch-results-header">
            <h3>📊 Batch-Verarbeitung abgeschlossen</h3>
            <div class="batch-stats">
                <div class="stat-item">
                    <span class="stat-number">${totalResults}</span>
                    <span class="stat-label">Gesamt</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${successfulResults}</span>
                    <span class="stat-label">Erfolgreich</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${highQualityResults}</span>
                    <span class="stat-label">Hohe Qualität</span>
                </div>
            </div>
        </div>
    `;
    
    // Generiere Cards für jedes Ergebnis
    const cardsHTML = batchResults
        .filter(result => result.success && result.comparison)
        .map((result, index) => {
            const comparison = result.comparison;
            comparison.mine_name = result.mine_name || `Mine ${index + 1}`;
            return generateSearchResultCard(comparison);
        })
        .join('');
    
    // Kombiniere alles
    targetElement.innerHTML = `
        ${headerHTML}
        
        <div class="batch-results-content">
            ${cardsHTML || '<div class="no-results">Keine erfolgreichen Ergebnisse zum Anzeigen</div>'}
        </div>
        
        <div class="batch-results-actions">
            <button class="action-button secondary" onclick="exportBatchResults()" title="Alle Ergebnisse exportieren">
                📤 Alle exportieren
            </button>
            <button class="action-button secondary" onclick="showBatchStatistics()" title="Detaillierte Statistiken">
                📈 Statistiken
            </button>
            <button class="action-button" onclick="startNewBatch()" title="Neue Batch-Suche">
                📊 Neue Batch-Suche
            </button>
        </div>
    `;
    
    targetElement.style.display = 'block';
    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    console.log('✅ [SIMPLIFIED-DISPLAY] Batch-Ergebnisse erfolgreich angezeigt');
}

// ============================================
// HILFSFUNKTIONEN
// ============================================

/**
 * ERROR DISPLAY: Generiert Fehler-Anzeige
 */
function generateErrorDisplay(errorMessage) {
    return `
        <div class="error-display">
            <div class="error-icon">⚠️</div>
            <div class="error-content">
                <h4>Fehler beim Laden der Ergebnisse</h4>
                <p>${errorMessage}</p>
                <button class="action-button" onclick="location.reload()">
                    🔄 Seite neu laden
                </button>
            </div>
        </div>
    `;
}

// ============================================
// INTEGRATION MIT BESTEHENDEN FUNKTIONEN
// ============================================

/**
 * LEGACY COMPATIBILITY: Ersetzt alte displayComparison Funktion
 */
function displayComparison(comparisonResult, targetElementId) {
    // Leite zu neuer Funktion weiter
    displaySearchComparison(comparisonResult, targetElementId);
}

/**
 * LEGACY COMPATIBILITY: Ersetzt alte displayResults Funktion
 */
function displayResults(results, targetElementId) {
    if (Array.isArray(results)) {
        // Batch-Ergebnisse
        displayBatchResults(results, targetElementId);
    } else {
        // Einzel-Ergebnis
        displaySearchComparison(results, targetElementId);
    }
}

// ============================================
// AKTIONS-HANDLER
// ============================================

/**
 * RAW DATA: Zeigt technische Vergleichsdaten in Modal
 */
function showRawComparisonData() {
    if (!window.lastComparisonResult) {
        showNotification('❌ Keine Vergleichsdaten verfügbar', 'error');
        return;
    }
    
    // Verwende bestehende Modal-Infrastruktur oder erstelle neue
    showTechnicalAnalysisModal(window.lastComparisonResult);
}

/**
 * EXPORT: Exportiert Suchergebnis
 */
function exportSearchResult() {
    if (!window.lastComparisonResult) {
        showNotification('❌ Keine Daten zum Exportieren verfügbar', 'error');
        return;
    }
    
    // Verwende bestehende Export-Funktionen
    if (typeof exportComparison === 'function') {
        exportComparison(window.lastComparisonResult.id, 'consensus');
    } else {
        showNotification('📤 Export-Funktion wird geladen...', 'info');
    }
}

/**
 * NEW SEARCH: Startet neue Suche
 */
function startNewSearch() {
    // Leere Results
    const resultsElement = document.getElementById('results');
    if (resultsElement) {
        resultsElement.innerHTML = '';
        resultsElement.style.display = 'none';
    }
    
    // Fokus auf Suchfeld
    const searchInput = document.getElementById('mine_name');
    if (searchInput) {
        searchInput.focus();
    }
    
    showNotification('🔍 Bereit für neue Suche', 'success');
}

/**
 * BATCH ACTIONS: Batch-spezifische Aktionen
 */
function startNewBatch() {
    // Leere Batch Results
    const batchResultsElement = document.getElementById('batch-results');
    if (batchResultsElement) {
        batchResultsElement.innerHTML = '';
        batchResultsElement.style.display = 'none';
    }
    
    // Fokus auf CSV Upload
    const csvInput = document.getElementById('csv_file');
    if (csvInput) {
        csvInput.focus();
    }
    
    showNotification('📊 Bereit für neue Batch-Suche', 'success');
}

function exportBatchResults() {
    showNotification('📤 Batch-Export wird implementiert...', 'info');
}

function showBatchStatistics() {
    showNotification('📈 Statistik-View wird implementiert...', 'info');
}

// ============================================
// NOTIFICATION SYSTEM FALLBACK
// ============================================

/**
 * NOTIFICATION: Fallback wenn showNotification nicht verfügbar
 */
if (typeof showNotification !== 'function') {
    window.showNotification = function(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // Einfaches Alert als Fallback
        if (type === 'error') {
            alert(message);
        }
    };
}

// Export für Module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        displaySearchComparison,
        displayBatchResults,
        displayComparison,
        displayResults
    };
}

console.log('✅ [SIMPLIFIED-DISPLAY] Modul geladen - Neue Display-Logik aktiv');