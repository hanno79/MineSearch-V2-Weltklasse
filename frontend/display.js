/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Display & Data Loading Functions
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (8343 → 500 Zeilen Regel)
 * Display Functions: Data Loading, Table Generation, Result Display, Statistics
 */

// ============================================
// DATA LOADING FUNCTIONS
// ============================================

/**
 * SOURCES LOADING: Lädt und zeigt Quellen-Datenbank
 */
async function loadSources(sortBy = 'count', order = 'desc') {
    console.log(`🔍 [SOURCES] Loading sources with sort: ${sortBy}, order: ${order}`);
    
    if (loadSourcesInProgress) {
        console.log('⚠️ [SOURCES] Load already in progress - skipping');
        return;
    }
    
    loadSourcesInProgress = true;
    
    // Cancel previous request if exists
    if (loadSourcesAbortController) {
        loadSourcesAbortController.abort();
    }
    loadSourcesAbortController = new AbortController();
    
    const params = new URLSearchParams({
        sort_by: sortBy,
        order: order,
        exclude_inactive: 'false'
    });
    
    const targetElement = document.getElementById('sources-table-container');
    showEnhancedLoadingState(targetElement, 'Lade Quellen-Datenbank...', true);
    
    try {
        const response = await fetch(`${window.API_BASE_URL}/api/sources/grouped?${params.toString()}&_cache_bust=${Date.now()}`, {
            signal: loadSourcesAbortController.signal,
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`📊 [SOURCES] Received data:`, data);
        
        if (data.success && data.data) {
            displayGroupedSources(data.data, sortBy, order);
            
            const totalSources = data.data.total_sources || 0;
            const totalDomains = data.data.grouped_sources ? data.data.grouped_sources.length : 0;
            
            showNotification(`✅ Quellen-Datenbank geladen: ${totalSources} Quellen aus ${totalDomains} Domains`, 'success');
        } else {
            throw new Error(data.error || 'Keine Quellen-Daten verfügbar');
        }
        
    } catch (error) {
        console.error('❌ [SOURCES] Loading error:', error);
        
        if (error.name === 'AbortError') {
            console.log('🛑 [SOURCES] Request aborted');
            return;
        }
        
        targetElement.innerHTML = createErrorHTML(
            'Fehler beim Laden der Quellen',
            error.message
        );
        
        showNotification(`❌ Quellen konnten nicht geladen werden: ${error.message}`, 'error');
        
    } finally {
        loadSourcesInProgress = false;
        loadSourcesAbortController = null;
    }
}

// ENTFERNT: Export wird am Ende der Datei gemacht

/**
 * RESULTS LOADING: Lädt und zeigt Suchergebnisse
 */
async function loadResults(sortBy = 'search_timestamp', order = 'desc') {
    console.log(`📊 [RESULTS] Loading results with sort: ${sortBy}, order: ${order}`);
    
    const targetElement = document.getElementById('results-table-container');
    showEnhancedLoadingState(targetElement, 'Lade Suchergebnisse...', true);
    
    try {
        const response = await HealthAPI.check();
        if (!response.success) {
            throw new Error('API nicht verfügbar');
        }
        
        // Load recent search results
        const params = new URLSearchParams({
            sort_by: sortBy,
            order: order,
            limit: '100',
            include_failed: 'true'
        });
        
        const resultsResponse = await fetch(`${window.API_BASE_URL}/api/results?${params}&_cache_bust=${Date.now()}`);
        
        if (!resultsResponse.ok) {
            throw new Error(`HTTP ${resultsResponse.status}: ${resultsResponse.statusText}`);
        }
        
        const data = await resultsResponse.json();
        console.log(`📋 [RESULTS] Received data:`, data);
        
        if (data.success && data.data) {
            displayResultsTable(data.data.results, sortBy, order);
            
            const totalResults = data.data.results ? data.data.results.length : 0;
            const successfulResults = data.data.results ? data.data.results.filter(r => r.success).length : 0;
            
            showNotification(`✅ Suchergebnisse geladen: ${successfulResults}/${totalResults} erfolgreich`, 'success');
        } else {
            throw new Error(data.error || 'Keine Ergebnisse verfügbar');
        }
        
    } catch (error) {
        console.error('❌ [RESULTS] Loading error:', error);
        
        targetElement.innerHTML = createErrorHTML(
            'Fehler beim Laden der Ergebnisse',
            error.message
        );
        
        showNotification(`❌ Ergebnisse konnten nicht geladen werden: ${error.message}`, 'error');
    }
}

/**
 * CONSOLIDATED RESULTS LOADING: Lädt konsolidierte Ergebnisse
 */
async function loadConsolidatedResults(sortBy = 'mine_name', order = 'asc') {
    console.log(`📈 [CONSOLIDATED] Loading consolidated results with sort: ${sortBy}, order: ${order}`);
    
    const targetElement = document.getElementById('consolidated-table-container');
    showEnhancedLoadingState(targetElement, 'Lade konsolidierte Ergebnisse...', true);
    
    try {
        const params = new URLSearchParams({
            sort_by: sortBy,
            order: order,
            exclude_exa: 'true',
            days_back: '30'
        });
        
        const response = await fetch(`${window.API_BASE_URL}/api/consolidated/results?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`📊 [CONSOLIDATED] Received data:`, data);
        
        if (data.success && data.data) {
            displayConsolidatedResults(data.data, sortBy, order);
            
            const totalResults = data.data.consolidated_results ? data.data.consolidated_results.length : 0;
            showNotification(`✅ Konsolidierte Ergebnisse geladen: ${totalResults} Minen`, 'success');
        } else {
            throw new Error(data.error || 'Keine konsolidierten Daten verfügbar');
        }
        
    } catch (error) {
        console.error('❌ [CONSOLIDATED] Loading error:', error);
        
        targetElement.innerHTML = createErrorHTML(
            'Fehler beim Laden der konsolidierten Ergebnisse',
            error.message
        );
        
        showNotification(`❌ Konsolidierte Ergebnisse konnten nicht geladen werden: ${error.message}`, 'error');
    }
}

// ENTFERNT: Export wird am Ende der Datei gemacht

/**
 * DISPLAY COMPREHENSIVE MODEL STATISTICS: Zeigt detaillierte Modell-Statistiken
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
 * DISPLAY BASIC MODEL STATISTICS: Zeigt einfache Modell-Statistiken (Fallback)
 */
function displayBasicModelStatistics(data) {
    console.log('📊 [STATISTICS] Displaying basic model statistics (fallback)');
    
    const targetElement = document.getElementById('model-statistics-table-container');
    if (!targetElement) {
        console.error('❌ [STATISTICS] model-statistics-table-container element not found!');
        return;
    }
    
    const models = data.models || [];
    if (models.length === 0) {
        targetElement.innerHTML = '<div class="no-data">Keine Modell-Daten verfügbar</div>';
        return;
    }
    
    let html = `
        <div class="statistics-header">
            <h3>📊 Basis-Modell-Statistiken (${models.length} Modelle)</h3>
        </div>
        <div class="statistics-grid">
    `;
    
    models.forEach(model => {
        html += `
            <div class="stat-card">
                <h4>${model.name || model.model_id || 'Unbekannt'}</h4>
                <p>Provider: ${model.provider || 'Unbekannt'}</p>
                <p>Status: ${model.is_active ? 'Aktiv' : 'Inaktiv'}</p>
            </div>
        `;
    });
    
    html += '</div>';
    targetElement.innerHTML = html;
}

/**
 * MODEL STATISTICS LOADING: Lädt Modell-Statistiken
 */
window.loadModelStatistics = async function() {
    console.log('📊 [STATISTICS] Loading comprehensive model statistics...');
    
    const targetElement = document.getElementById('model-statistics-table-container');
    showEnhancedLoadingState(targetElement, 'Lade Modell-Statistiken...', true);
    
    try {
        const params = new URLSearchParams({
            sort_by: 'overall_score',
            order: 'desc',
            days_back: '30',
            exclude_failed: 'false',
            include_details: 'true'
        });
        
        const response = await fetch(`${window.API_BASE_URL}/api/statistics/models/comprehensive?${params.toString()}`);
        
        if (!response.ok) {
            // Fallback to basic statistics
            console.warn('📊 [STATISTICS] Comprehensive API failed, trying fallback...');
            const fallbackResponse = await fetch(`${window.API_BASE_URL}/api/statistics/models/overview?_cache_bust=${Date.now()}`);
            
            if (!fallbackResponse.ok) {
                throw new Error(`HTTP ${fallbackResponse.status}: ${fallbackResponse.statusText}`);
            }
            
            const fallbackData = await fallbackResponse.json();
            if (fallbackData.success) {
                displayBasicModelStatistics(fallbackData.data);
                showNotification('📊 Basis-Modell-Statistiken geladen (Fallback)', 'info');
                return;
            }
        }
        
        const data = await response.json();
        console.log('📋 [STATISTICS] Statistics data received:', data);
        
        if (data.success && data.data) {
            displayComprehensiveModelStatistics(data.data);
            
            const totalModels = data.data.models ? data.data.models.length : 0;
            showNotification(`✅ Modell-Statistiken geladen: ${totalModels} Modelle analysiert`, 'success');
        } else {
            throw new Error(data.error || 'Keine Statistik-Daten verfügbar');
        }
        
    } catch (error) {
        console.error('❌ [STATISTICS] Loading error:', error);
        
        targetElement.innerHTML = createErrorHTML(
            'Fehler beim Laden der Modell-Statistiken',
            error.message
        );
        
        showNotification(`❌ Modell-Statistiken konnten nicht geladen werden: ${error.message}`, 'error');
    }
};

// ============================================
// DISPLAY FUNCTIONS
// ============================================

/**
 * GROUPED SOURCES DISPLAY: Zeigt gruppierte Quellen-Daten
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
 * RESULTS TABLE DISPLAY: Zeigt Suchergebnisse mit modernen Data-Cards
 * PHASE 3: TABELLEN-REVOLUTION - Ersetzt hässliche HTML-Tabelle
 */
function displayResultsTable(results, sortBy, order) {
    console.log(`🎨 [DISPLAY] Rendering results with DATA-CARDS (${results?.length || 0} results)`);
    
    const container = document.getElementById('results');
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
 * CONSOLIDATED RESULTS DISPLAY: Zeigt konsolidierte Ergebnisse
 */
/**
 * PHASE 2.1: KOMPLETT NEUE FELDANZEIGE-IMPLEMENTIERUNG 14.08.2025
 * Zeigt strukturierte Felder statt nur Metadaten in Cards
 */
function displayConsolidatedResults(data, sortBy, order) {
    console.log(`🎨 [PHASE 2.1] NEW FIELD-BASED DISPLAY: ${data.consolidated_results?.length || 0} mines with structured fields`);
    
    const container = document.getElementById('consolidated-table-container');
    if (!container) {
        console.error('[PHASE 2.1] Container not found: consolidated-table-container');
        return;
    }
    
    if (!data.consolidated_results || data.consolidated_results.length === 0) {
        container.innerHTML = createErrorHTML(
            'Keine konsolidierten Ergebnisse verfügbar',
            'Es wurden keine konsolidierten Daten gefunden.'
        );
        return;
    }
    
    // PHASE 2.1: Cache Global Source Index für Quellenreferenzen
    window.globalSourceIndex = data.global_source_index || {};
    console.log(`[PHASE 2.1] Cached ${Object.keys(window.globalSourceIndex).length} source references`);
    
    // PHASE 2.1: NEUE FIELD-BASED CARD GENERATION
    const cards = data.consolidated_results.map(mine => generateFieldBasedCard(mine)).join('');
    
    // PHASE 2.1: Enhanced Container mit Field-Grid-System
    container.innerHTML = `
        <div class="field-display-container">
            <div class="field-display-header">
                <h3 class="field-display-title">
                    📊 Mine-Ergebnisse mit strukturierten Feldern
                    <span class="result-count">(${data.consolidated_results.length} Minen)</span>
                </h3>
                <div class="field-display-stats">
                    <div class="stat-item">
                        📈 ${data.total_sources || 0} Quellen gesamt
                    </div>
                    <div class="stat-item">  
                        🎯 Durchschnittlich ${Math.round(data.consolidated_results.reduce((sum, mine) => sum + (mine.overall_confidence || 0), 0) / data.consolidated_results.length)} % Zuverlässigkeit
                    </div>
                </div>
            </div>
            <div class="field-display-grid">
                ${cards}
            </div>
        </div>
    `;
    
    console.log(`[PHASE 2.1] Successfully rendered ${data.consolidated_results.length} field-based cards`);
}

/**
 * PHASE 2.1: FIELD-BASED CARD GENERATOR 14.08.2025
 * Generiert Cards mit strukturierten Feldern statt nur Metadaten
 */
function generateFieldBasedCard(mine) {
    if (!mine) return '';
    
    // PHASE 2.1: Extract structured fields (neue API-Struktur)
    const structuredFields = mine.structured_fields || {};
    const metadata = mine.metadata || {
        mine_name: mine.mine_name,
        country: mine.country,
        region: mine.region
    };
    
    // PHASE 2.1: Field Summary für Card-Header
    const fieldSummary = mine.field_summary || {
        total_fields: Object.keys(structuredFields).length,
        fields_with_high_confidence: 0,
        avg_confidence: mine.overall_confidence || 0
    };
    
    console.log(`[PHASE 2.1] Generating field card for ${metadata.mine_name}: ${fieldSummary.total_fields} fields`);
    
    // PHASE 2.1: Prioritäts-basierte Feldanzeige (wichtigste Felder zuerst)
    const priorityFields = [
        'Betreiber', 'Eigentümer', 'Rohstoffe', 'Minentyp', 'Aktivitätsstatus',
        'Produktionsstart', 'Produktionsende', 'Fördermenge/Jahr', 
        'Minenfläche in qkm', 'x-Koordinate', 'y-Koordinate',
        'Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr'
    ];
    
    // PHASE 2.1: Generiere Feldanzeige
    const fieldHTML = generateFieldDisplayGrid(structuredFields, priorityFields);
    
    return `
        <div class="field-based-card mine-card" data-mine="${metadata.mine_name}">
            <!-- PHASE 2.1: ENHANCED CARD HEADER -->
            <div class="field-card-header">
                <div class="header-main">
                    <h3 class="mine-title">⛏️ ${metadata.mine_name}</h3>
                    <div class="mine-location">
                        📍 ${metadata.country || 'Unbekannt'}${metadata.region ? `, ${metadata.region}` : ''}
                    </div>
                </div>
                <div class="field-summary-badge">
                    <div class="confidence-score ${getConfidenceClass(fieldSummary.avg_confidence)}">
                        ${Math.round(fieldSummary.avg_confidence)}% Zuverlässigkeit
                    </div>
                    <div class="field-count">
                        ${fieldSummary.total_fields} Felder | ${fieldSummary.fields_with_high_confidence} hochwertig
                    </div>
                </div>
            </div>
            
            <!-- PHASE 2.1: STRUCTURED FIELD DISPLAY -->
            <div class="field-display-section">
                ${fieldHTML}
            </div>
            
            <!-- PHASE 2.1: ENHANCED CARD FOOTER -->
            <div class="field-card-footer">
                <div class="card-actions">
                    <button class="btn-details" onclick="viewConsolidatedDetail('${metadata.mine_name}')">
                        🔍 Alle Felder & Details
                    </button>
                    <button class="btn-sources" onclick="showMineSourceReferences('${metadata.mine_name}')">
                        📚 Quellenreferenzen
                    </button>
                </div>
                <div class="card-stats">
                    <span class="stat">📊 ${mine.model_count || 0} AI-Modelle</span>
                    <span class="stat">📈 ${mine.total_sources || 0} Quellen</span>
                    <span class="stat">🕒 ${mine.last_updated ? new Date(mine.last_updated).toLocaleDateString('de-DE') : 'Unbekannt'}</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * PHASE 2.1: FIELD DISPLAY GRID GENERATOR
 * Erstellt das Raster für strukturierte Feldanzeige
 */
function generateFieldDisplayGrid(structuredFields, priorityOrder) {
    if (!structuredFields || Object.keys(structuredFields).length === 0) {
        return `<div class="no-fields-message">Keine strukturierten Felder verfügbar</div>`;
    }
    
    // PHASE 2.1: Sortiere Felder nach Priorität
    const sortedFields = sortFieldsByPriority(structuredFields, priorityOrder);
    
    // PHASE 2.1: Zeige max 8 Felder in der Card (wichtigste zuerst)
    const displayFields = sortedFields.slice(0, 8);
    const hiddenCount = sortedFields.length - 8;
    
    let fieldsHTML = displayFields.map(([fieldName, fieldData]) => 
        generateSingleFieldDisplay(fieldName, fieldData)
    ).join('');
    
    // PHASE 2.1: Zeige versteckte Felder-Indikator
    if (hiddenCount > 0) {
        fieldsHTML += `
            <div class="hidden-fields-indicator">
                <span class="hidden-count">+ ${hiddenCount} weitere Felder</span>
                <small>Klicken Sie auf "Details" für alle Felder</small>
            </div>
        `;
    }
    
    return `<div class="field-grid">${fieldsHTML}</div>`;
}

/**
 * PHASE 2.1: SINGLE FIELD DISPLAY GENERATOR
 * Erstellt Anzeige für ein einzelnes Feld mit Wert, Score und Quellenreferenzen
 */
function generateSingleFieldDisplay(fieldName, fieldData) {
    const value = fieldData.value || 'Unbekannt';
    const confidenceScore = fieldData.confidence_score || 0;
    const sourceNumbers = fieldData.global_source_numbers || [];
    const sourceCount = fieldData.source_count || 0;
    
    // PHASE 2.1: Value Display (verkürzt falls zu lang)
    let displayValue = value;
    if (value.length > 30) {
        displayValue = value.substring(0, 27) + '...';
    }
    
    // PHASE 2.1: Source References String
    let sourceRefsHTML = '';
    if (sourceNumbers && sourceNumbers.length > 0) {
        const refs = sourceNumbers.slice(0, 3).map(num => `[${num}]`).join('');
        sourceRefsHTML = `<span class="source-refs">${refs}</span>`;
    }
    
    return `
        <div class="field-item" title="Vollständiger Wert: ${value}">
            <div class="field-label">${fieldName}</div>
            <div class="field-value-container">
                <div class="field-value">${displayValue}</div>
                ${sourceRefsHTML}
            </div>
            <div class="field-meta">
                <div class="confidence-indicator ${getConfidenceClass(confidenceScore)}">
                    ${Math.round(confidenceScore)}%
                </div>
                ${sourceCount > 1 ? `<span class="multi-source">✓${sourceCount}</span>` : ''}
            </div>
        </div>
    `;
}

/**
 * PHASE 2.1: FIELD PRIORITY SORTER
 * Sortiert Felder nach Prioritätsliste und alphabetisch für den Rest
 */
function sortFieldsByPriority(fields, priorityOrder) {
    const fieldEntries = Object.entries(fields);
    
    return fieldEntries.sort(([nameA], [nameB]) => {
        const priorityA = priorityOrder.indexOf(nameA);
        const priorityB = priorityOrder.indexOf(nameB);
        
        // Beide in Prioritätsliste
        if (priorityA !== -1 && priorityB !== -1) {
            return priorityA - priorityB;
        }
        
        // A in Priorität, B nicht
        if (priorityA !== -1 && priorityB === -1) {
            return -1;
        }
        
        // B in Priorität, A nicht  
        if (priorityA === -1 && priorityB !== -1) {
            return 1;
        }
        
        // Beide nicht in Priorität - alphabetisch sortieren
        return nameA.localeCompare(nameB, 'de');
    });
}

/**
 * PHASE 2.1: CONFIDENCE CLASS HELPER
 * Bestimmt CSS-Klasse basierend auf Zuverlässigkeits-Score
 */
function getConfidenceClass(score) {
    if (score >= 80) return 'confidence-high';
    if (score >= 60) return 'confidence-medium';  
    if (score >= 30) return 'confidence-low';
    return 'confidence-very-low';
}

/**
 * PHASE 2.1: MINE SOURCE REFERENCES DISPLAY
 * Zeigt Quellenreferenzen für eine spezifische Mine
 */
async function showMineSourceReferences(mineName) {
    console.log(`[PHASE 2.1] Showing source references for mine: ${mineName}`);
    
    try {
        // PHASE 2.1: Hole detaillierte Quelleninformationen
        const response = await fetch(`${window.API_BASE_URL}/api/consolidated/mine/${encodeURIComponent(mineName)}?include_sources=true`);
        
        if (!response.ok) {
            throw new Error(`Failed to load source references: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.data) {
            throw new Error('No source reference data available');
        }
        
        // PHASE 2.1: Erstelle Source-Reference-Modal
        const sourceRefsHTML = generateSourceReferencesModal(mineName, data.data, window.globalSourceIndex || {});
        
        // PHASE 2.1: Zeige Modal
        showModal('Quellenreferenzen', sourceRefsHTML, 'large');
        
    } catch (error) {
        console.error(`[PHASE 2.1] Error showing source references:`, error);
        showNotification(`❌ Fehler beim Laden der Quellenreferenzen: ${error.message}`, 'error');
    }
}

/**
 * PHASE 2.1: SOURCE REFERENCES MODAL GENERATOR  
 * Erstellt HTML für Quellenreferenzen-Modal
 */
function generateSourceReferencesModal(mineName, mineData, globalSourceIndex) {
    // PHASE 2.1: Use new structured_fields structure
    const structuredFields = mineData.structured_fields || {};
    
    if (Object.keys(structuredFields).length === 0) {
        return '<div class="no-data">Keine Quellenreferenzen für ' + mineName + ' verfügbar.</div>';
    }
    
    let referencesHTML = '';
    
    // PHASE 2.1: Gruppiere Quellenreferenzen nach Feld
    Object.entries(structuredFields).forEach(function([fieldName, fieldData]) {
        const sources = fieldData.source_references || [];
        const globalNumbers = fieldData.global_source_numbers || [];
        
        if (sources.length > 0) {
            const sourceItems = sources.map(function(sourceUrl, index) {
                // Use global source number if available, otherwise find in index
                let sourceNumber = globalNumbers[index] || '?';
                if (sourceNumber === '?' && globalSourceIndex) {
                    const entry = Object.entries(globalSourceIndex)
                        .find(function([num, data]) { return data.url === sourceUrl; });
                    sourceNumber = entry ? entry[0] : '?';
                }
                
                // Get source metadata from global index
                const sourceData = globalSourceIndex[sourceNumber] || {};
                const reliability = sourceData.reliability_score || 0;
                const successRate = sourceData.success_rate || 0;
                const domain = sourceData.domain || sourceUrl;
                
                return '<div class="source-item" data-source-url="' + sourceUrl + '">' +
                    '<div class="source-header">' +
                        '<span class="source-number">[' + sourceNumber + ']</span>' +
                        '<span class="source-domain">' + domain + '</span>' +
                    '</div>' +
                    '<div class="source-url">' + sourceUrl + '</div>' +
                    '<div class="source-stats">' +
                        '<span class="source-reliability">Zuverlässigkeit: ' + reliability + '%</span>' +
                        '<span class="source-success">Erfolgsrate: ' + successRate + '%</span>' +
                    '</div>' +
                    '<button class="btn-small" onclick="openSourceInNewTab(\'' + sourceUrl + '\')">' +
                        '🔗 Öffnen' +
                    '</button>' +
                '</div>';
            }).join('');
            
            referencesHTML += '<div class="field-source-group">' +
                '<h4 class="field-name">' + fieldName + '</h4>' +
                '<div class="field-value">"' + fieldData.value + '"</div>' +
                '<div class="source-confidence">Vertrauen: ' + fieldData.confidence_score + '% (' + fieldData.source_count + ' Quellen)</div>' +
                '<div class="source-list">' +
                    sourceItems +
                '</div>' +
            '</div>';
        }
    });
    
    if (!referencesHTML) {
        return '<div class="no-data">Keine Quellenreferenzen für ' + mineName + ' verfügbar.</div>';
    }
    
    return '<div class="source-references-container">' +
        '<div class="mine-info">' +
            '<h3>📚 Quellenreferenzen für ' + mineName + '</h3>' +
            '<p>Diese Quellen wurden für die Datenextraktion verwendet:</p>' +
        '</div>' +
        '<div class="source-references-content">' +
            referencesHTML +
        '</div>' +
    '</div>';
}

/**
 * PHASE 2.1: OPEN SOURCE IN NEW TAB
 * Öffnet Quelle in neuem Tab mit Tracking
 */
function openSourceInNewTab(sourceUrl) {
    console.log(`[PHASE 2.1] Opening source: ${sourceUrl}`);
    
    if (!sourceUrl || !sourceUrl.startsWith('http')) {
        showNotification('❌ Ungültige Quellen-URL', 'error');
        return;
    }
    
    // PHASE 2.1: Öffne in neuem Tab
    window.open(sourceUrl, '_blank', 'noopener,noreferrer');
    
    // PHASE 2.1: Track source access (optional)
    // trackSourceAccess(sourceUrl);
}

// ============================================
// GLOBAL STATE & VARIABLES
// ============================================

// Loading state management
let loadSourcesInProgress = false;
let loadSourcesAbortController = null;

// ============================================
// GLOBAL EXPORTS
// ============================================

// ============================================
// DETAIL VIEW FUNCTIONS
// ============================================

/**
 * VIEW CONSOLIDATED DETAIL: Zeigt Details für konsolidierte Mine-Ergebnisse
 */
async function viewConsolidatedDetail(mineName) {
    console.log(`🔍 [CONSOLIDATED-DETAIL] Loading details for mine: ${mineName}`);
    
    try {
        // API call to get detailed consolidated results
        const response = await fetch(`${window.API_BASE_URL}/api/consolidated/mine/${encodeURIComponent(mineName)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.data) {
            showConsolidatedDetailModal(mineName, data.data);
        } else {
            throw new Error(data.error || 'Keine Details verfügbar');
        }
        
    } catch (error) {
        console.error('❌ [CONSOLIDATED-DETAIL] Error:', error);
        showNotification(`❌ Fehler beim Laden der Details für ${mineName}: ${error.message}`, 'error');
    }
}

/**
 * SHOW CONSOLIDATED DETAIL MODAL: Zeigt Modal mit konsolidierten Mine-Details
 */
function showConsolidatedDetailModal(mineName, mineData) {
    console.log(`📋 [MODAL] Displaying consolidated details for: ${mineName}`);
    
    // REINER Content ohne Modal-Wrapper - showDetailModal() kümmert sich um Modal-Struktur
    const modalContent = `
        <div class="mine-summary">
            <h4>📊 Zusammenfassung</h4>
            <div class="summary-grid">
                <div class="summary-item">
                    <strong>Land:</strong> ${mineData.best_values?.country || 'Nicht verfügbar'}
                </div>
                <div class="summary-item">
                    <strong>Gefundene Felder:</strong> ${mineData.best_values ? Object.keys(mineData.best_values).length : 0}
                </div>
                <div class="summary-item">
                    <strong>Quellen:</strong> ${mineData.source_summary?.total_unique_sources || 0}
                </div>
            </div>
        </div>
        
        ${mineData.best_values ? `
            <div class="mine-fields">
                <h4>📋 Beste Werte</h4>
                <div class="fields-data-grid">
                    ${Object.entries(mineData.best_values)
                        .filter(([field, value]) => !field.startsWith('_'))  // Filtere Meta-Felder wie _source_mapping
                        .map(([field, value]) => `
                        <div class="field-data-card">
                            <div class="field-header">
                                <span class="field-name">${field}</span>
                                <span class="source-badge">📊 Konsolidiert</span>
                            </div>
                            <div class="field-value">
                                ${value || '<span class="missing-value">Nicht verfügbar</span>'}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}
        
        ${mineData.source_summary ? `
            <div class="mine-sources">
                <h4>📚 Quellen-Übersicht</h4>
                <p><strong>Gesamte Quellen:</strong> ${mineData.source_summary.total_unique_sources}</p>
            </div>
        ` : ''}
    `;
    
    // Show modal using existing modal system - KONSISTENT mit anderen Tabs
    if (typeof showDetailModal === 'function') {
        showDetailModal(`🏭 ${mineName} - Konsolidierte Details`, modalContent);
    } else {
        // Fallback: Simple alert if modal system not available
        alert(`Details für ${mineName}:\n\nFelder: ${mineData.best_values ? Object.keys(mineData.best_values).length : 0}\nQuellen: ${mineData.source_summary?.total_unique_sources || 0}`);
    }
}

/**
 * SHOW DETAIL MODAL: Generic modal display function - KONSISTENT mit anderen Tabs
 */
function showDetailModal(title, content) {
    console.log(`📋 [MODAL] Showing detail modal: ${title}`);
    
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    // Create modal container mit KONSISTENTEM Layout
    const modal = document.createElement('div');
    modal.className = 'modal-content detail-modal';
    modal.style.cssText = `
        background: white;
        border-radius: 8px;
        max-width: 800px;
        max-height: 80vh;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        position: relative;
    `;
    
    // KONSISTENTE Modal-Struktur wie andere Tabs
    modal.innerHTML = `
        <div class="modal-header">
            <h3>${title}</h3>
            <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div class="modal-body" style="max-height: calc(80vh - 60px); overflow-y: auto; padding: 20px;">
            ${content}
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Close modal on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeModal();
        }
    });
    
    // Close modal on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && window.currentModal) {
            closeModal();
        }
    });
    
    // Store reference for closing
    window.currentModal = overlay;
}

/**
 * GENERIC SHOW MODAL: Universelle Modal-Funktion für alle Tabs - KONSISTENT
 */
function showModal(title, content, size = 'medium') {
    console.log(`📋 [MODAL] Showing modal: ${title} (size: ${size})`);
    
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    // Determine modal width based on size
    const modalWidth = size === 'large' ? '900px' : size === 'small' ? '400px' : '700px';
    
    // Create modal container mit KONSISTENTEM Layout
    const modal = document.createElement('div');
    modal.className = 'modal-content';
    modal.style.cssText = `
        background: white;
        border-radius: 8px;
        max-width: ${modalWidth};
        max-height: 80vh;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        position: relative;
    `;
    
    // KONSISTENTE Modal-Struktur wie andere Tabs
    modal.innerHTML = `
        <div class="modal-header">
            <h3>${title}</h3>
            <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div class="modal-body" style="max-height: calc(80vh - 60px); overflow-y: auto; padding: 20px;">
            ${content}
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Close modal on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeModal();
        }
    });
    
    // Close modal on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && window.currentModal) {
            closeModal();
        }
    });
    
    // Store reference for closing
    window.currentModal = overlay;
}

/**
 * CLOSE MODAL: Schließt das aktuelle Modal - ROBUST mit Fallbacks
 */
function closeModal() {
    console.log('🔴 [MODAL] closeModal() aufgerufen');
    
    // Methode 1: Verwende window.currentModal Reference
    if (window.currentModal) {
        console.log('🔴 [MODAL] Entferne Modal via currentModal Reference');
        try {
            document.body.removeChild(window.currentModal);
            window.currentModal = null;
            console.log('✅ [MODAL] Modal erfolgreich geschlossen via Reference');
            return;
        } catch (error) {
            console.error('❌ [MODAL] Fehler beim Entfernen via Reference:', error);
        }
    }
    
    // Fallback 1: Suche alle Modal-Overlays
    const overlays = document.querySelectorAll('.modal-overlay');
    if (overlays.length > 0) {
        console.log(`🔴 [MODAL] Gefunden ${overlays.length} Modal-Overlays - entferne alle`);
        overlays.forEach((overlay, index) => {
            try {
                document.body.removeChild(overlay);
                console.log(`✅ [MODAL] Overlay ${index + 1} entfernt`);
            } catch (error) {
                console.error(`❌ [MODAL] Fehler beim Entfernen von Overlay ${index + 1}:`, error);
            }
        });
        window.currentModal = null;
        return;
    }
    
    // Fallback 2: Verstecke Modals via CSS
    const hiddenOverlays = document.querySelectorAll('[style*="position: fixed"][style*="z-index"]');
    if (hiddenOverlays.length > 0) {
        console.log(`🔴 [MODAL] Verstecke ${hiddenOverlays.length} potentielle Modals via CSS`);
        hiddenOverlays.forEach((el, index) => {
            el.style.display = 'none';
            console.log(`✅ [MODAL] Element ${index + 1} versteckt`);
        });
        window.currentModal = null;
        return;
    }
    
    console.log('⚠️ [MODAL] Kein Modal zum Schließen gefunden');
}

// BEREINIGTE EXPORTS ENTFERNT - Nur definitive Exports am Ende der Datei

/**
 * LOAD ENHANCED SOURCE DETAILS: Lädt detaillierte Informationen für eine Domain
 */
async function loadEnhancedSourceDetails(domain, contentDiv) {
    console.log(`🔍 [SOURCE-DETAILS] Loading enhanced details for domain: ${domain}`);
    
    try {
        // API-Call für Domain-spezifische Details
        const response = await fetch(`${window.API_BASE_URL}/api/sources/domain/${encodeURIComponent(domain)}`);
        
        let detailsHtml = '';
        
        if (response.ok) {
            const data = await response.json();
            console.log(`📊 [SOURCE-DETAILS] Received data for ${domain}:`, data);
            
            if (data.success && data.sources && data.sources.length > 0) {
                detailsHtml = generateSourceDetailsHTML(domain, data.sources, data.statistics);
            } else {
                detailsHtml = generateFallbackDetailsHTML(domain, 'Keine detaillierten Quellen-Informationen verfügbar.');
            }
        } else {
            console.warn(`⚠️ [SOURCE-DETAILS] API call failed for ${domain}: ${response.status}`);
            // Fallback: Generate basic details from available information
            detailsHtml = generateBasicSourceDetailsHTML(domain);
        }
        
        contentDiv.innerHTML = detailsHtml;
        
    } catch (error) {
        console.error(`❌ [SOURCE-DETAILS] Error loading details for ${domain}:`, error);
        contentDiv.innerHTML = generateFallbackDetailsHTML(domain, `Fehler beim Laden: ${error.message}`);
    }
}

/**
 * GENERATE SOURCE DETAILS HTML: Erstellt HTML für Domain-Details
 */
function generateSourceDetailsHTML(domain, sources, statistics = {}) {
    const totalSources = sources.length;
    const activeSources = sources.filter(s => s.status === 'active').length;
    const avgReliability = statistics.avg_reliability || 0;
    
    let html = `
        <div class="source-details-container">
            <div class="source-summary">
                <h4 style="margin: 0 0 12px 0; color: #374151;">
                    📊 Domain-Analyse: ${sanitizeHTML(domain)}
                </h4>
                <div class="stats-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px;">
                    <div class="stat-item" style="text-align: center; padding: 8px; background: white; border-radius: 4px; border: 1px solid #e5e7eb;">
                        <div style="font-weight: bold; color: #059669; font-size: 18px;">${totalSources}</div>
                        <div style="font-size: 12px; color: #6b7280;">Gesamte Quellen</div>
                    </div>
                    <div class="stat-item" style="text-align: center; padding: 8px; background: white; border-radius: 4px; border: 1px solid #e5e7eb;">
                        <div style="font-weight: bold; color: #0891b2; font-size: 18px;">${activeSources}</div>
                        <div style="font-size: 12px; color: #6b7280;">Aktive Quellen</div>
                    </div>
                    <div class="stat-item" style="text-align: center; padding: 8px; background: white; border-radius: 4px; border: 1px solid #e5e7eb;">
                        <div style="font-weight: bold; color: #ea580c; font-size: 18px;">${avgReliability.toFixed(1)}%</div>
                        <div style="font-size: 12px; color: #6b7280;">Ø Zuverlässigkeit</div>
                    </div>
                </div>
            </div>
            
            <div class="sources-list">
                <h5 style="margin: 0 0 8px 0; color: #374151;">Quellen-Details:</h5>
                <div style="max-height: 300px; overflow-y: auto;">
    `;
    
    sources.slice(0, 10).forEach((source, index) => {
        const reliability = source.reliability_score || 0;
        const reliabilityColor = reliability >= 80 ? '#059669' : reliability >= 60 ? '#0891b2' : reliability >= 40 ? '#ea580c' : '#dc2626';
        const statusColor = source.status === 'active' ? '#059669' : '#6b7280';
        
        html += `
            <div style="padding: 8px; margin-bottom: 6px; background: white; border-radius: 4px; border-left: 3px solid ${reliabilityColor}; font-size: 13px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div style="font-weight: 500; color: #374151;">Quelle ${index + 1}</div>
                    <div style="display: flex; gap: 12px; font-size: 11px;">
                        <span style="color: ${reliabilityColor}; font-weight: bold;">${reliability.toFixed(1)}%</span>
                        <span style="color: ${statusColor}; font-weight: bold;">${source.status || 'unbekannt'}</span>
                    </div>
                </div>
                <div style="color: #6b7280; font-size: 11px;">
                    Typ: ${source.type || 'general'} | Letzte Aktualisierung: ${source.last_updated ? new Date(source.last_updated).toLocaleDateString('de-DE') : 'Unbekannt'}
                </div>
            </div>
        `;
    });
    
    if (sources.length > 10) {
        html += `<div style="text-align: center; padding: 8px; color: #6b7280; font-size: 12px;">... und ${sources.length - 10} weitere Quellen</div>`;
    }
    
    html += `
                </div>
            </div>
        </div>
    `;
    
    return html;
}

/**
 * GENERATE BASIC SOURCE DETAILS HTML: Erstellt einfache Details ohne API-Daten
 */
function generateBasicSourceDetailsHTML(domain) {
    return `
        <div class="source-details-container">
            <div class="source-summary">
                <h4 style="margin: 0 0 12px 0; color: #374151;">
                    📊 Domain-Informationen: ${sanitizeHTML(domain)}
                </h4>
                <div style="padding: 16px; background: white; border-radius: 4px; border: 1px solid #e5e7eb;">
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">
                        Diese Domain ist in der Quellen-Datenbank registriert und wird für Mine-Informationen verwendet.
                    </p>
                    <div style="margin-top: 12px; padding: 12px; background: #f0f9ff; border-radius: 4px; border-left: 4px solid #3b82f6;">
                        <div style="font-weight: 500; color: #1e40af; font-size: 13px; margin-bottom: 4px;">
                            Domain-Analyse
                        </div>
                        <ul style="margin: 0; padding-left: 16px; color: #374151; font-size: 12px;">
                            <li>Domain wird für Suchergebnisse verwendet</li>
                            <li>Teil der vertrauenswürdigen Quellen-Liste</li>
                            <li>Regelmäßige Verfügbarkeits-Prüfung aktiv</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * GENERATE FALLBACK DETAILS HTML: Erstellt Fallback-HTML bei Fehlern
 */
function generateFallbackDetailsHTML(domain, message) {
    return `
        <div class="source-details-container">
            <div class="source-summary">
                <h4 style="margin: 0 0 12px 0; color: #374151;">
                    📊 ${sanitizeHTML(domain)}
                </h4>
                <div style="padding: 16px; background: #fef3c7; border-radius: 4px; border: 1px solid #f59e0b; text-align: center;">
                    <div style="color: #92400e; font-size: 14px;">
                        ⚠️ ${message}
                    </div>
                    <div style="color: #a16207; font-size: 12px; margin-top: 8px;">
                        Die Domain ist verfügbar, aber detaillierte Informationen können momentan nicht geladen werden.
                    </div>
                </div>
            </div>
        </div>
    `;
}

// BEREINIGTE EXPORTS ENTFERNT - Nur definitive Exports am Ende der Datei

// loadModelStatistics ist bereits korrekt in Zeile 264 als window-Funktion definiert

// Export detail view functions
window.viewConsolidatedDetail = viewConsolidatedDetail;
window.showDetailModal = showDetailModal;
window.showModal = showModal;
window.closeModal = closeModal;
window.loadEnhancedSourceDetails = loadEnhancedSourceDetails;

// ============================================
// DEFINITIVE GLOBAL EXPORTS - NUR HIER!
// ============================================
// Alle wichtigen Tab-Loading-Funktionen exportieren
window.loadSources = loadSources;
window.loadResults = loadResults;
window.loadConsolidatedResults = loadConsolidatedResults;

// Display-Funktionen exportieren
window.displayGroupedSources = displayGroupedSources;
window.displayResultsTable = displayResultsTable;
window.displayConsolidatedResults = displayConsolidatedResults;
window.displayComprehensiveModelStatistics = displayComprehensiveModelStatistics;
window.displayBasicModelStatistics = displayBasicModelStatistics;

// loadModelStatistics ist bereits korrekt in Zeile 264 als window-Funktion definiert

console.log('📊 MineSearch 2.0 - Display Functions loaded');
console.log('✅ [EXPORT] All critical tab-loading functions exported to window scope');