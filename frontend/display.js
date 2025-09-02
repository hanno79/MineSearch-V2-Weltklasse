/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 2.7 - FIX: Model-ID Normalisierung für robuste Duplikat-Erkennung
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
    console.log(`🔧 [CONSOLIDATED] API_BASE_URL: ${window.API_BASE_URL}`);
    
    const targetElement = document.getElementById('consolidated-table-container');
    if (!targetElement) {
        console.error('❌ [CONSOLIDATED] consolidated-table-container element not found!');
        return;
    }
    
    showEnhancedLoadingState(targetElement, 'Lade konsolidierte Ergebnisse...', true);
    
    try {
        const params = new URLSearchParams({
            sort_by: sortBy,
            order: order,
            exclude_exa: 'true',
            days_back: '30'
        });
        
        const url = `${window.API_BASE_URL}/api/consolidated/results?${params}`;
        console.log(`🌐 [CONSOLIDATED] Fetching from: ${url}`);
        
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        
        console.log(`📡 [CONSOLIDATED] Response status: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ [CONSOLIDATED] Server error: ${errorText}`);
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log(`📊 [CONSOLIDATED] Received data structure:`, {
            success: data.success,
            hasData: !!data.data,
            dataKeys: data.data ? Object.keys(data.data) : [],
            consolidatedResultsCount: data.data?.consolidated_results?.length || 0
        });
        
        if (data.success && data.data && data.data.consolidated_results) {
            displayConsolidatedResults(data.data, sortBy, order);
            
            const totalResults = data.data.consolidated_results.length;
            showNotification(`✅ Konsolidierte Ergebnisse geladen: ${totalResults} Minen`, 'success');
        } else {
            const errorMsg = data.error || data.message || 'Keine konsolidierten Daten verfügbar';
            console.warn(`⚠️ [CONSOLIDATED] No data available: ${errorMsg}`);
            
            targetElement.innerHTML = createErrorHTML(
                'Keine konsolidierten Ergebnisse verfügbar',
                'Es wurden noch keine Suchergebnisse gespeichert. Führen Sie zunächst einige Suchen durch.'
            );
            
            showNotification(`ℹ️ ${errorMsg}`, 'info');
        }
        
    } catch (error) {
        console.error('❌ [CONSOLIDATED] Loading error:', error);
        console.error('❌ [CONSOLIDATED] Error stack:', error.stack);
        
        let errorMessage = error.message;
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage = 'Verbindung zum Server fehlgeschlagen. Überprüfen Sie, ob der Service läuft.';
        }
        
        targetElement.innerHTML = createErrorHTML(
            'Fehler beim Laden der konsolidierten Ergebnisse',
            errorMessage
        );
        
        showNotification(`❌ Konsolidierte Ergebnisse konnten nicht geladen werden: ${errorMessage}`, 'error');
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
            // 🚀 LOGIC-REVOLUTION PHASE 1.2: Model-Splitting vor Display
            const splitData = splitCombinedModels(data.data);
            
            // 🔄 MODEL KONSOLIDIERUNG PHASE 3: Konsolidiere Duplikate zu einer Card pro Modell
            const consolidatedModels = consolidateModels(splitData.models);
            const processedData = {
                ...splitData,
                models: consolidatedModels,
                _consolidation_metadata: {
                    split_count: splitData.models.length,
                    consolidated_count: consolidatedModels.length,
                    duplicates_removed: splitData.models.length - consolidatedModels.length
                }
            };
            
            displayComprehensiveModelStatistics(processedData);
            
            const originalModels = data.data.models ? data.data.models.length : 0;
            const consolidatedCount = processedData._consolidation_metadata.consolidated_count;
            const duplicatesRemoved = processedData._consolidation_metadata.duplicates_removed;
            showNotification(`✅ Modell-Statistiken geladen: ${consolidatedCount} unique Modelle (${duplicatesRemoved} Duplikate konsolidiert)`, 'success');
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
    console.log(`🎨 [TABLE VIEW] NEW TABLE-BASED DISPLAY: ${data.consolidated_results?.length || 0} mines`);
    
    const container = document.getElementById('consolidated-table-container');
    const countElement = document.getElementById('results-count');
    
    if (!container) {
        console.error('[TABLE VIEW] Container not found: consolidated-table-container');
        return;
    }
    
    if (!data.consolidated_results || data.consolidated_results.length === 0) {
        container.innerHTML = createErrorHTML(
            'Keine konsolidierten Ergebnisse verfügbar',
            'Es wurden keine konsolidierten Daten gefunden.'
        );
        if (countElement) countElement.textContent = '0 Minen gefunden';
        return;
    }
    
    // Cache Global Source Index für Quellenreferenzen
    window.globalSourceIndex = data.global_source_index || {};
    window.currentConsolidatedData = data.consolidated_results; // For modal access
    console.log(`[TABLE VIEW] Cached ${Object.keys(window.globalSourceIndex).length} source references`);
    
    // Update results count
    if (countElement) {
        countElement.textContent = `${data.consolidated_results.length} Minen gefunden`;
    }
    
    // Check which view is active
    const activeView = document.querySelector('.toggle-btn.active')?.getAttribute('data-view') || 'table';
    
    if (activeView === 'table') {
        renderConsolidatedTable(data.consolidated_results, sortBy, order);
    } else {
        renderConsolidatedCards(data.consolidated_results, sortBy, order);
    }
    
    console.log(`[TABLE VIEW] Successfully rendered ${data.consolidated_results.length} mines in ${activeView} view`);
}

/**
 * NEUE TABELLEN-RENDERING FUNKTION
 * Zeigt Minen in Tabellenform - CSV Export Vorschau
 */
function renderConsolidatedTable(mines, sortBy, order) {
    const container = document.getElementById('consolidated-table-container');
    
    // Sammle alle verfügbaren Felder aus allen Minen
    const allFields = new Set();
    mines.forEach(mine => {
        if (mine.best_values) {
            Object.keys(mine.best_values).forEach(field => {
                // FELDANZEIGE-FIX 29.08.2025: Nur Meta-Felder und englische Ursprungsfelder filtern
                if (!field.startsWith('_') && // Meta-Felder wie _source_mapping ausschließen
                    !['Mine', 'mine', 'mine_name', 'country', 'province'].includes(field)) {
                    allFields.add(field);
                }
            });
        }
    });
    
    // SPALTENREIHENFOLGE-FIX 29.08.2025: Exakte User-Anforderung
    // Mine, Land, Region sind feste Spalten (werden separat behandelt)
    // Danach: Eigentümer, Betreiber, x-Koordinate, y-Koordinate, Rohstoffe, Minentyp, 
    // Aktivitätsstatus, Produktionsstart, Produktionsende, Fördermenge, Minenfläche, 
    // Restaurationskosten, Kostenjahr, Dokumentenjahr, Quellenangaben
    const fieldOrder = [
        'Eigentümer', 'Betreiber',
        'x-Koordinate', 'y-Koordinate', 
        'Rohstoffe', 'Minentyp', 'Aktivitätsstatus',
        'Produktionsstart', 'Produktionsende', 'Fördermenge/Jahr',
        'Minenfläche in qkm',
        'Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr'
        // Quellenangaben wird separat ans Ende gesetzt
    ];
    
    // Sortiere Felder nach logischer Reihenfolge
    const orderedFields = [];
    
    // Erst bekannte Felder in gewünschter Reihenfolge
    fieldOrder.forEach(orderField => {
        if (allFields.has(orderField)) {
            orderedFields.push(orderField);
            allFields.delete(orderField); // Entferne aus Set für Fallback
        }
    });
    
    // Dann unbekannte Felder alphabetisch (außer Quellenangaben)
    Array.from(allFields)
        .filter(field => field !== 'Quellenangaben')
        .sort()
        .forEach(field => orderedFields.push(field));
    
    // Quellenangaben ans Ende
    if (allFields.has('Quellenangaben')) {
        orderedFields.push('Quellenangaben');
    }
    
    const fieldArray = orderedFields;
    console.log(`[TABLE VIEW] Found ${fieldArray.length} unique fields across all mines (filtered and ordered)`);
    
    // Erstelle Tabellenkopf
    const headerCells = [
        '<th class="mine-name-col">Mine Name</th>',
        '<th class="country-col">Land</th>',
        '<th class="region-col">Region</th>',
        ...fieldArray.map(field => `<th class="field-col" title="${sanitizeHTML(field)}">${truncateFieldName(field)}</th>`),
        '<th class="actions-col">Details</th>'
    ];
    
    // Erstelle Tabellenzeilen
    const tableRows = mines.map(mine => {
        const mineName = sanitizeHTML(mine.mine_name || 'Unbekannt');
        // FELDANZEIGE-FIX 29.08.2025: Nutze konsolidierte deutsche Feldnamen
        const country = sanitizeHTML(mine.best_values?.['Land'] || 'Unbekannt');
        const region = sanitizeHTML(mine.best_values?.['Region'] || 'Unbekannt');
        
        const fieldCells = fieldArray.map(field => {
            const value = mine.best_values?.[field];
            let displayValue;
            
            // EINHEITEN-FIX 29.08.2025: Spezielle Formatierung nach User-Anforderungen
            if (field === 'Restaurationskosten' && value && value !== 'Nichts gefunden' && value !== '-') {
                // Restaurationskosten immer in $
                const numericValue = String(value).replace(/[^\d.,]/g, ''); // Entferne alles außer Zahlen und Komma/Punkt
                displayValue = numericValue ? `$${numericValue}` : sanitizeHTML(String(value).substring(0, 30));
            } else if (field === 'Minenfläche in qkm' && value && value !== 'Nichts gefunden' && value !== '-') {
                // Minenfläche in ha (1 qkm = 100 ha)
                const match = String(value).match(/(\d+(?:\.\d+)?)/);
                if (match) {
                    const qkmValue = parseFloat(match[1]);
                    const haValue = (qkmValue * 100).toFixed(2);
                    displayValue = `${haValue} ha`;
                } else {
                    displayValue = sanitizeHTML(String(value).substring(0, 30));
                }
            } else if ((field === 'x-Koordinate' || field === 'y-Koordinate') && value && value !== 'Nichts gefunden' && value !== '-') {
                // Koordinaten als UTM (falls numerisch)
                const match = String(value).match(/(-?\d+(?:\.\d+)?)/);
                if (match) {
                    displayValue = `${match[1]} UTM`;
                } else {
                    displayValue = sanitizeHTML(String(value).substring(0, 30));
                }
            } else {
                displayValue = value ? sanitizeHTML(String(value).substring(0, 30)) : '-';
            }
            
            const sources = mine.detailed_breakdown?.[field]?.sources || [];
            const sourceText = sources.length > 0 ? `[${sources.slice(0, 2).join(', ')}${sources.length > 2 ? '...' : ''}]` : '';
            
            return `<td class="field-cell" title="${sanitizeHTML(value || '')}">${displayValue} <small class="source-ref">${sourceText}</small></td>`;
        });
        
        return `
            <tr class="mine-row" data-mine="${escapeJavaScriptString(mine.mine_name)}">
                <td class="mine-name-cell"><strong>${mineName}</strong></td>
                <td class="country-cell">${country}</td>
                <td class="region-cell">${region}</td>
                ${fieldCells.join('')}
                <td class="actions-cell">
                    <button class="details-btn" onclick="showMineDetailsModal('${escapeJavaScriptString(mine.mine_name)}')">
                        📊 Details
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Render Tabelle
    container.innerHTML = `
        <div class="table-responsive">
            <table class="consolidated-results-table">
                <thead>
                    <tr>
                        ${headerCells.join('')}
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
        <div class="table-footer">
            <p class="table-info">
                📊 Tabelle zeigt CSV-Export Format | 
                🔍 Klicken Sie auf "Details" für umfassende Statistiken |
                💡 Horizontal scrollen für alle Felder
            </p>
        </div>
    `;
}

/**
 * FALLBACK CARD-RENDERING (Legacy)
 */
function renderConsolidatedCards(mines, sortBy, order) {
    const container = document.getElementById('consolidated-table-container');
    
    // Use existing field-based card generation
    const cards = mines.map(mine => generateFieldBasedCard(mine)).join('');
    
    container.innerHTML = `
        <div class="field-display-container">
            <div class="field-display-header">
                <h3 class="field-display-title">
                    📋 Mine-Ergebnisse als Cards
                    <span class="result-count">(${mines.length} Minen)</span>
                </h3>
            </div>
            <div class="field-display-grid">
                ${cards}
            </div>
        </div>
    `;
}

/**
 * HILFSFUNKTIONEN
 */
function truncateFieldName(fieldName) {
    if (fieldName.length <= 15) return fieldName;
    return fieldName.substring(0, 12) + '...';
}

/**
 * VIEW TOGGLE HANDLER
 */
function switchConsolidatedView(viewType) {
    console.log(`[VIEW TOGGLE] Switching to ${viewType} view`);
    
    // Update toggle buttons
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-view') === viewType) {
            btn.classList.add('active');
        }
    });
    
    // Re-render with current data
    if (window.currentConsolidatedData) {
        if (viewType === 'table') {
            renderConsolidatedTable(window.currentConsolidatedData);
        } else {
            renderConsolidatedCards(window.currentConsolidatedData);
        }
    }
}

/**
 * PHASE 2.1: FIELD-BASED CARD GENERATOR 14.08.2025
 * Generiert Cards mit strukturierten Feldern statt nur Metadaten
 */
function generateFieldBasedCard(mine) {
    if (!mine) return '';
    
    // PHASE 2.1: Extract structured fields (neue API-Struktur)
    const structuredFields = mine.structured_fields || {};
    // FIX: Land-Anzeige Problem - suche country/region sowohl auf Root- als auch Metadata-Ebene
    const metadata = mine.metadata || {
        mine_name: mine.mine_name,
        country: mine.country || mine.metadata?.country,
        region: mine.region || mine.metadata?.region
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
                        📍 ${metadata.country || 'Nichts gefunden'}${metadata.region ? `, ${metadata.region}` : ''}
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
                    <span class="stat">🕒 ${mine.last_updated ? new Date(mine.last_updated).toLocaleDateString('de-DE') : 'Nichts gefunden'}</span>
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
    const value = fieldData.value || 'Nichts gefunden';  // PHASE 14.3: Einheitliche Frontend-Darstellung
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
                    <strong>Land:</strong> ${mineData.country || mineData.metadata?.country || 'Nicht verfügbar'}${mineData.region || mineData.metadata?.region ? `, ${mineData.region || mineData.metadata?.region}` : ''}
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
                        .map(([field, value]) => {
                            // PHASE 16.2: Hole Field-spezifische Source-Informationen
                            const fieldData = mineData.structured_fields ? mineData.structured_fields[field] : null;
                            const sourceCount = fieldData ? (fieldData.source_references?.length || 0) : 0;
                            const confidenceScore = fieldData ? fieldData.confidence_score : null;
                            
                            return `
                        <div class="field-data-card">
                            <div class="field-header">
                                <span class="field-name">${field}</span>
                                <div class="field-source-info">
                                    ${sourceCount > 0 ? `
                                        <span class="source-count-badge" title="${sourceCount} Quellen verwendet">
                                            📊 ${sourceCount} Quellen
                                        </span>
                                    ` : '<span class="source-badge">📊 Konsolidiert</span>'}
                                    ${confidenceScore !== null ? `
                                        <span class="confidence-badge" title="Vertrauens-Score basierend auf Quellenqualität">
                                            🎯 ${confidenceScore}%
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                            <div class="field-value">
                                ${value || '<span class="missing-value">Nicht verfügbar</span>'}
                            </div>
                            ${sourceCount > 0 ? `
                                <div class="field-sources-preview">
                                    <button class="btn-mini" onclick="showFieldSourceDetails('${mineName.replace(/'/g, "\\'")}', '${field.replace(/'/g, "\\'")}')">
                                        📚 Quellen anzeigen
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    `;
                        }).join('')}
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
                        <span style="color: ${statusColor}; font-weight: bold;">${source.status || 'nichts gefunden'}</span>
                    </div>
                </div>
                <div style="color: #6b7280; font-size: 11px;">
                    Typ: ${source.type || 'general'} | Letzte Aktualisierung: ${source.last_updated ? new Date(source.last_updated).toLocaleDateString('de-DE') : 'Nichts gefunden'}
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
// CSV EXPORT FUNCTIONS - PHASE 16.1
// ============================================

/**
 * PHASE 16.1: CSV Export für Consolidated Results
 * Exportiert alle konsolidierten Minen-Daten als CSV-Datei
 */
async function exportConsolidatedCSV() {
    console.log('📊 [CSV-EXPORT] Starting CSV export for consolidated results...');
    
    // Variable außerhalb des try-Blocks deklarieren für finally-Block Zugriff
    let exportBtn = null;
    
    try {
        // Zeige Loading-Status
        exportBtn = document.getElementById('csv-export-btn') || document.querySelector('button[onclick="exportConsolidatedCSV()"]');
        if (exportBtn) {
            exportBtn.textContent = '⏳ Exportiere...';
            exportBtn.disabled = true;
        }
        
        // Hole die aktuellen Filter-Parameter
        const country = document.getElementById('consolidated_country')?.value || '';
        const region = document.getElementById('consolidated_region')?.value || '';
        const daysBack = document.getElementById('consolidated_days')?.value || '30';
        const sortBy = document.getElementById('consolidated_sort')?.value || 'mine_name';
        
        // PHASE 16.3: Verwende dedizierten CSV Export Endpunkt
        const params = new URLSearchParams({
            exclude_exa: 'true',
            days_back: daysBack,
            sort_by: sortBy
        });
        
        if (country) params.append('country', country);
        if (region) params.append('region', region);
        
        // PHASE 16.3 FIX: Korrekte API-Route für CSV Export
        const csvUrl = `${window.API_BASE_URL}/api/consolidated/results/export/csv?${params.toString()}`;
        
        // Trigger download durch temporäres Link-Element
        const downloadLink = document.createElement('a');
        downloadLink.href = csvUrl;
        downloadLink.style.display = 'none';
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        console.log(`✅ [CSV-EXPORT] CSV Export gestartet: ${csvUrl}`);
        showNotification(`✅ CSV Export gestartet - Download beginnt automatisch`, 'success');
        
    } catch (error) {
        console.error('❌ [CSV-EXPORT] Export error:', error);
        showNotification(`❌ CSV Export fehlgeschlagen: ${error.message}`, 'error');
    } finally {
        // Button zurücksetzen
        if (exportBtn) {
            exportBtn.textContent = '📊 CSV Export (| separiert)';
            exportBtn.disabled = false;
        }
    }
}

// PHASE 16.3: CSV-Generierungsfunktionen entfernt - Backend übernimmt CSV-Export vollständig
// CSV Export erfolgt jetzt server-seitig über /api/consolidated/results/export/csv

// ============================================
// FIELD-SPECIFIC SOURCE DETAILS - PHASE 16.2
// ============================================

/**
 * PHASE 16.2: Zeigt detaillierte Quelleninformationen für ein spezifisches Feld
 */
async function showFieldSourceDetails(mineName, fieldName) {
    console.log(`📚 [FIELD-SOURCES] Loading source details for: ${mineName} -> ${fieldName}`);
    
    try {
        // API call to get detailed field sources
        const response = await fetch(`${window.API_BASE_URL}/api/consolidated/mine/${encodeURIComponent(mineName)}?include_sources=true`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.data || !data.data.structured_fields) {
            throw new Error('Keine Feldquellen verfügbar');
        }
        
        const fieldData = data.data.structured_fields[fieldName];
        if (!fieldData) {
            throw new Error(`Feld '${fieldName}' nicht gefunden`);
        }
        
        // Generiere Field-Source-Details HTML
        const sourceDetailsHTML = generateFieldSourceDetailsHTML(mineName, fieldName, fieldData);
        
        // Show modal using existing modal system
        showModal(`📚 Quellen: ${fieldName}`, sourceDetailsHTML, 'medium');
        
    } catch (error) {
        console.error(`❌ [FIELD-SOURCES] Error:`, error);
        showNotification(`❌ Fehler beim Laden der Feldquellen: ${error.message}`, 'error');
    }
}

/**
 * Generiert HTML für Field-spezifische Source-Details
 */
function generateFieldSourceDetailsHTML(mineName, fieldName, fieldData) {
    const value = fieldData.value || 'Nicht verfügbar';
    const confidenceScore = fieldData.confidence_score || 0;
    const sourceReferences = fieldData.source_references || [];
    const globalSourceNumbers = fieldData.global_source_numbers || [];
    
    let sourcesHTML = '';
    
    if (sourceReferences.length === 0) {
        sourcesHTML = '<div class="no-sources">Keine spezifischen Quellen für dieses Feld verfügbar.</div>';
    } else {
        sourcesHTML = sourceReferences.map((sourceUrl, index) => {
            const sourceNumber = globalSourceNumbers[index] || (index + 1);
            const domain = sourceUrl ? new URL(sourceUrl).hostname : 'Unbekannt';
            
            return `
                <div class="field-source-item">
                    <div class="source-header">
                        <span class="source-number">[${sourceNumber}]</span>
                        <span class="source-domain">${domain}</span>
                    </div>
                    <div class="source-url" title="${sourceUrl}">
                        ${sourceUrl.length > 80 ? sourceUrl.substring(0, 77) + '...' : sourceUrl}
                    </div>
                    <div class="source-actions">
                        <button class="btn-small" onclick="openSourceInNewTab('${sourceUrl}')">
                            🔗 Öffnen
                        </button>
                        <button class="btn-small" onclick="copyToClipboard('${sourceUrl}')">
                            📋 Kopieren
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    return `
        <div class="field-source-details">
            <div class="field-summary">
                <h4>📊 Feld-Zusammenfassung</h4>
                <div class="summary-grid">
                    <div class="summary-item">
                        <strong>Mine:</strong> ${mineName}
                    </div>
                    <div class="summary-item">
                        <strong>Feld:</strong> ${fieldName}
                    </div>
                    <div class="summary-item">
                        <strong>Wert:</strong> ${value}
                    </div>
                    <div class="summary-item">
                        <strong>Vertrauen:</strong> ${confidenceScore}%
                    </div>
                    <div class="summary-item">
                        <strong>Quellen:</strong> ${sourceReferences.length}
                    </div>
                </div>
            </div>
            
            <div class="field-sources-list">
                <h4>📚 Quellendetails</h4>
                ${sourcesHTML}
            </div>
            
            <div class="source-legend">
                <p><small>💡 <strong>Tipp:</strong> Klicken Sie auf "🔗 Öffnen" um die Original-Quelle zu besuchen.</small></p>
            </div>
        </div>
    `;
}

/**
 * Öffnet eine Quelle in einem neuen Tab
 */
function openSourceInNewTab(url) {
    if (url && url.startsWith('http')) {
        window.open(url, '_blank', 'noopener,noreferrer');
    } else {
        showNotification('❌ Ungültige URL', 'error');
    }
}

/**
 * Kopiert Text in die Zwischenablage
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('✅ URL kopiert!', 'success');
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showNotification('❌ Kopieren fehlgeschlagen', 'error');
    }
}

// ============================================
// LOGIC-REVOLUTION: MODEL-SPLITTING FUNCTION
// ============================================

/**
 * LOGIC-REVOLUTION PHASE 2.1: Revolutionäre 5-Komponenten Score-Berechnung
 * Neue Gewichtung: Feldqualität 25%, Konsistenz 25%, Geschwindigkeit 25%, Kosten 20%, Durchlauf-Vertrauen 5%
 * STRICT RULE: Score = 0 bei 0% Erfolgsrate für ALLE Komponenten
 */
function calculateRevolutionary5ComponentScore(modelData) {
    console.log(`🚀 [REVOLUTIONARY-SCORE] Calculating 5-component score for ${modelData.model_id}`);
    
    const successRate = modelData.success_rate || 0;
    const searchCount = modelData.total_searches || 1;
    const splitFactor = modelData._split_factor || 1;
    
    // STRICT RULE: Bei 0% Erfolgsrate alle Komponenten = 0
    if (successRate === 0) {
        console.log(`❌ [REVOLUTIONARY-SCORE] ${modelData.model_id}: 0% Erfolgsrate = 0 Gesamtscore`);
        return {
            totalScore: 0,
            breakdown: {
                fieldQuality: { score: 0, description: 'Feldqualität', details: 'Keine bei 0% Erfolgsrate' },
                consistency: { score: 0, description: 'Konsistenz', details: 'Keine bei 0% Erfolgsrate' },
                speed: { score: 0, description: 'Geschwindigkeit', details: 'Irrelevant bei 0% Erfolgsrate' },
                cost: { score: 0, description: 'Kosteneffizienz', details: 'Irrelevant bei 0% Erfolgsrate' },
                trustworthiness: { score: 0, description: 'Durchlauf-Vertrauen', details: 'Keine Vertrauenswürdigkeit bei 0% Erfolgsrate' }
            },
            confidenceLevel: 'Nicht verfügbar',
            confidencePercentage: 0
        };
    }
    
    // === KOMPONENTE 1: FELDQUALITÄT (25%) ===
    const fieldQualityScore = calculateRevolutionaryFieldQuality(modelData);
    
    // === KOMPONENTE 2: KONSISTENZ (25%) ===
    const consistencyScore = calculateRevolutionaryConsistency(modelData);
    
    // === KOMPONENTE 3: GESCHWINDIGKEIT (25%) ===
    const speedScore = calculateRevolutionarySpeed(modelData);
    
    // === KOMPONENTE 4: KOSTENEFFIZIENZ (20%) ===
    const costScore = calculateRevolutionaryCost(modelData);
    
    // === KOMPONENTE 5: DURCHLAUF-VERTRAUEN (5%) ===
    const trustworthinessScore = calculateRevolutionaryTrustworthiness(modelData);
    
    // Gewichtete Gesamtberechnung - NEUE GEWICHTUNG!
    const totalScore = (
        fieldQualityScore.score * 0.25 +
        consistencyScore.score * 0.25 +
        speedScore.score * 0.25 +
        costScore.score * 0.20 +
        trustworthinessScore.score * 0.05
    );
    
    // Konfidenz basierend auf Durchläufen und Split-Faktor
    const confidenceFactor = Math.min(searchCount / 10, 1.0) * (1 / Math.sqrt(splitFactor));
    const confidencePercentage = Math.round(confidenceFactor * 100);
    
    let confidenceLevel = 'Niedrig';
    if (confidencePercentage >= 80) confidenceLevel = 'Hoch';
    else if (confidencePercentage >= 50) confidenceLevel = 'Mittel';
    
    console.log(`✅ [REVOLUTIONARY-SCORE] ${modelData.model_id}: Total=${totalScore.toFixed(1)}/100, Confidence=${confidencePercentage}%`);
    
    return {
        totalScore: Math.min(Math.max(totalScore, 0), 100), // 0-100 Scale
        breakdown: {
            fieldQuality: fieldQualityScore,
            consistency: consistencyScore,
            speed: speedScore,
            cost: costScore,
            trustworthiness: trustworthinessScore
        },
        confidenceLevel: confidenceLevel,
        confidencePercentage: confidencePercentage
    };
}

/**
 * KOMPONENTE 1: Revolutionäre Feldqualität (25%)
 */
function calculateRevolutionaryFieldQuality(modelData) {
    const successRate = modelData.success_rate || 0;
    if (successRate === 0) return { score: 0, description: 'Feldqualität', details: 'Keine bei 0% Erfolgsrate' };
    
    // FINAL OPTIMIZATION: Strenger Threshold - Niedrige Erfolgsrate = niedrige Scores
    if (successRate < 0.3) {
        // Unter 30% = Maximum 40 Punkte (4.0/10 auf Frontend-Scale)
        const baseQuality = successRate * 40; // 0-12 Punkte bei unter 30%
        return {
            score: Math.min(baseQuality, 40),
            description: 'Feldqualität', 
            details: `${(successRate*100).toFixed(1)}% Erfolgsrate (niedrig)`
        };
    }
    
    // Ab 30% normale Berechnung
    const baseQuality = successRate * 80; // 0-80 Punkte basierend auf Erfolgsrate
    const qualityBonus = successRate >= 0.8 ? 20 : successRate >= 0.5 ? 10 : 0; // Bonus für hohe Erfolgsrate
    
    return {
        score: Math.min(baseQuality + qualityBonus, 100),
        description: 'Feldqualität',
        details: `${(successRate*100).toFixed(1)}% Erfolgsrate`
    };
}

/**
 * KOMPONENTE 2: Revolutionäre Konsistenz (25%)
 */
function calculateRevolutionaryConsistency(modelData) {
    const successRate = modelData.success_rate || 0;
    if (successRate === 0) return { score: 0, description: 'Konsistenz', details: 'Keine bei 0% Erfolgsrate' };
    
    const searchCount = modelData.total_searches || 1;
    const splitFactor = modelData._split_factor || 1;
    
    // FINAL OPTIMIZATION: Strenger Threshold auch für Konsistenz
    if (successRate < 0.3) {
        // Unter 30% = Reduzierte Konsistenz-Bewertung
        const baseConsistency = successRate * 30; // 0-9 Punkte bei unter 30%
        const trustBonus = Math.min(searchCount / 20, 0.5) * 10; // Reduzierter Bonus
        return {
            score: Math.min(baseConsistency + trustBonus, 40),
            description: 'Konsistenz',
            details: `${searchCount} Durchläufe, niedrige Rate: ${(successRate*100).toFixed(1)}%`
        };
    }
    
    // Ab 30% normale Berechnung
    const baseConsistency = successRate * 70; // 0-70 Punkte
    const trustBonus = Math.min(searchCount / 10, 1.0) * 20; // 0-20 Bonus für viele Durchläufe
    const splitPenalty = Math.max(0, (splitFactor - 1) * 5); // Penalty für Split-Kombinationen
    
    return {
        score: Math.min(Math.max(baseConsistency + trustBonus - splitPenalty, 0), 100),
        description: 'Konsistenz',
        details: `${searchCount} Durchläufe, Split-Faktor: ${splitFactor}`
    };
}

/**
 * KOMPONENTE 3: Revolutionäre Geschwindigkeit (25%)
 */
function calculateRevolutionarySpeed(modelData) {
    const successRate = modelData.success_rate || 0;
    if (successRate === 0) return { score: 0, description: 'Geschwindigkeit', details: 'Irrelevant bei 0% Erfolgsrate' };
    
    const provider = modelData.provider || 'unknown';
    
    // Provider-basierte Speed-Bewertung (da keine echten Timing-Daten verfügbar)
    let baseSpeed = 50; // Default
    if (['openrouter'].includes(provider)) baseSpeed = 75; // Schnell
    else if (['perplexity'].includes(provider)) baseSpeed = 85; // Sehr schnell
    else if (['abacus', 'exa'].includes(provider)) baseSpeed = 60; // Mittel
    
    // Erfolgsrate-Gewichtung
    const speedScore = baseSpeed * successRate;
    
    return {
        score: Math.min(speedScore, 100),
        description: 'Geschwindigkeit',
        details: `${provider} Provider`
    };
}

/**
 * KOMPONENTE 4: Revolutionäre Kosteneffizienz (20%)
 */
function calculateRevolutionaryCost(modelData) {
    const successRate = modelData.success_rate || 0;
    if (successRate === 0) return { score: 0, description: 'Kosteneffizienz', details: 'Irrelevant bei 0% Erfolgsrate' };
    
    const modelId = modelData.model_id || '';
    const provider = modelData.provider || 'unknown';
    
    // Kosten-Tier basierend auf Model und Provider
    let baseCost = 50; // Default
    if (modelId.includes('free')) baseCost = 95; // Kostenlos = Sehr gut
    else if (['openrouter', 'perplexity'].includes(provider)) baseCost = 80; // Günstig
    else if (['openai', 'anthropic'].includes(provider)) baseCost = 30; // Teuer
    else if (['abacus', 'exa'].includes(provider)) baseCost = 60; // Mittel
    
    // Erfolgsrate-Gewichtung
    const costScore = baseCost * successRate;
    
    return {
        score: Math.min(costScore, 100),
        description: 'Kosteneffizienz',
        details: modelId.includes('free') ? 'Kostenlos' : `${provider} Provider`
    };
}

/**
 * KOMPONENTE 5: Revolutionäres Durchlauf-Vertrauen (5%)
 */
function calculateRevolutionaryTrustworthiness(modelData) {
    const successRate = modelData.success_rate || 0;
    if (successRate === 0) return { score: 0, description: 'Durchlauf-Vertrauen', details: 'Keine Vertrauenswürdigkeit bei 0% Erfolgsrate' };
    
    const searchCount = modelData.total_searches || 1;
    const splitFactor = modelData._split_factor || 1;
    
    // Vertrauen basierend auf Anzahl Durchläufe und Split-Penalty
    const trustBase = Math.min(searchCount / 20, 1.0) * 80; // 0-80 Punkte für Durchläufe
    const successBonus = successRate * 20; // 0-20 Bonus für Erfolgsrate
    const splitPenalty = Math.max(0, (splitFactor - 1) * 10); // Penalty für Kombinationen
    
    return {
        score: Math.min(Math.max(trustBase + successBonus - splitPenalty, 0), 100),
        description: 'Durchlauf-Vertrauen',
        details: `${searchCount} Durchläufe, ${(successRate*100).toFixed(1)}% Erfolg`
    };
}

/**
 * MODEL KONSOLIDIERUNG PHASE 1: Konsolidiert mehrere Vorkommen desselben Modells
 * Löst das Problem: 3x "openrouter:deepseek-free" → 1x konsolidierte Card
 */
function consolidateModels(modelsList) {
    console.log('🔄 [MODEL-CONSOLIDATION] Consolidating duplicate models...');
    
    if (!modelsList || modelsList.length === 0) {
        console.warn('⚠️ [MODEL-CONSOLIDATION] No models to consolidate');
        return [];
    }
    
    // Group models by model_id with ENHANCED normalization
    const modelGroups = {};
    modelsList.forEach((model, index) => {
        // Enhanced normalization for robust duplicate detection
        const rawModelId = model.model_id || `unknown_${index}`;
        
        // ENHANCED NORMALIZATION ALGORITHM:
        // 1. Trim whitespace
        // 2. Convert to lowercase  
        // 3. Remove special characters and normalize separators
        // 4. Handle provider prefix variations
        let normalizedModelId = rawModelId.trim().toLowerCase();
        
        // Normalize common variations
        normalizedModelId = normalizedModelId
            .replace(/[_\-\s]+/g, '-')  // Normalize separators to hyphens
            .replace(/^(openrouter|perplexity|abacus|exa):/, '$1:')  // Ensure consistent provider format
            .replace(/[\(\)\[\]\.]/g, '')  // Remove brackets and dots
            .replace(/[0-9]+(\.[0-9]+)?[kmbt]?$/i, '')  // Remove version numbers at end
            .replace(/(-free|-pro|-beta|-alpha|-v[0-9]+)$/i, '$1')  // Preserve important suffixes
            .replace(/(-llama-3)(\w*)/, '$1')  // Normalize llama-3 variations
            .replace(/(-glm-4)(\w*)/, '$1');  // Normalize glm-4 variations
        
        console.log(`🔍 [NORMALIZATION] "${rawModelId}" → "${normalizedModelId}"`);
        
        // Use normalized model_id as grouping key
        const groupKey = normalizedModelId;
        
        if (!modelGroups[groupKey]) {
            modelGroups[groupKey] = [];
        }
        modelGroups[groupKey].push({
            ...model,
            _normalized_id: normalizedModelId,
            _original_id: rawModelId
        });
    });
    
    console.log(`📊 [MODEL-CONSOLIDATION] Found ${Object.keys(modelGroups).length} unique models from ${modelsList.length} entries`);
    
    // DEBUG: Log all model IDs and their sources
    console.log('🔍 [DEBUG-CONSOLIDATION] All input models:');
    modelsList.forEach((model, i) => {
        console.log(`   ${i+1}: "${model.model_id}" (source: ${model._original_combination || 'individual'})`);
    });
    
    // Consolidate each group
    const consolidatedModels = [];
    
    Object.entries(modelGroups).forEach(([normalizedId, models]) => {
        // Use original model_id from first model for display
        const originalModelId = models[0]._original_id || normalizedId;
        
        if (models.length === 1) {
            // Single model - no consolidation needed
            consolidatedModels.push(models[0]);
            console.log(`✅ [MODEL-CONSOLIDATION] ${originalModelId}: Single entry, no consolidation needed`);
        } else {
            // Multiple models - consolidate them
            console.log(`🔄 [MODEL-CONSOLIDATION] ${originalModelId}: Consolidating ${models.length} entries`);
            
            // PHASE 2: AGGREGATION LOGIC
            let totalSearches = 0;
            let totalSuccessfulSearches = 0;
            let allSources = new Set();
            let firstModel = models[0]; // Use first model as base
            
            models.forEach(model => {
                totalSearches += (model.total_searches || 0);
                totalSuccessfulSearches += (model.successful_searches || 0);
                
                // Collect unique sources
                if (model.sources) {
                    if (Array.isArray(model.sources)) {
                        model.sources.forEach(source => allSources.add(source));
                    } else if (typeof model.sources === 'string') {
                        allSources.add(model.sources);
                    }
                }
            });
            
            // Calculate new success rate
            const newSuccessRate = totalSearches > 0 ? totalSuccessfulSearches / totalSearches : 0;
            
            // Recalculate Revolutionary Score with consolidated data
            const revolutionaryScore = calculateRevolutionary5ComponentScore({
                model_id: originalModelId,
                provider: firstModel.provider || (originalModelId.includes(':') ? originalModelId.split(':')[0] : 'unknown'),
                total_searches: totalSearches,
                successful_searches: totalSuccessfulSearches,
                success_rate: newSuccessRate,
                _split_factor: 1 // Reset split factor for consolidated models
            });
            
            // Create consolidated model
            const consolidatedModel = {
                ...firstModel, // Use first model as base
                model_id: originalModelId,
                total_searches: totalSearches,
                successful_searches: totalSuccessfulSearches,
                success_rate: newSuccessRate,
                success_rate_percent: newSuccessRate * 100,
                // Updated revolutionary scores
                overall_score: revolutionaryScore.totalScore,
                score_breakdown: revolutionaryScore.breakdown,
                confidence_level: revolutionaryScore.confidenceLevel,
                confidence_percentage: revolutionaryScore.confidencePercentage,
                // Consolidation metadata
                sources: Array.from(allSources),
                _consolidated: true,
                _original_entries: models.length,
                _consolidation_source: models.map(m => m._original_combination || 'individual').filter(Boolean)
            };
            
            consolidatedModels.push(consolidatedModel);
            
            console.log(`✅ [MODEL-CONSOLIDATION] ${originalModelId}: ${models.length} entries → 1 consolidated (${totalSearches} searches, ${(newSuccessRate*100).toFixed(1)}% success)`);
        }
    });
    
    console.log(`🎉 [MODEL-CONSOLIDATION] Complete: ${modelsList.length} models → ${consolidatedModels.length} consolidated models`);
    return consolidatedModels;
}

/**
 * LOGIC-REVOLUTION PHASE 1.2: Spaltet kombinierte Model-IDs in Einzelmodelle auf
 * Löst das Problem: "openrouter:deepseek-free_openrouter:mistral-small-free" → Einzelmodelle
 */
function splitCombinedModels(statisticsData) {
    console.log('🔧 [MODEL-SPLITTING] Processing backend model combinations...');
    
    if (!statisticsData || !statisticsData.models) {
        console.warn('⚠️ [MODEL-SPLITTING] No models data to process');
        return statisticsData;
    }
    
    const originalModels = statisticsData.models;
    const splitModels = [];
    let combinationsFound = 0;
    let modelsCreated = 0;
    
    originalModels.forEach((modelData, index) => {
        const originalModelId = modelData.model_id || '';
        
        // Check for underscore combinations
        if (originalModelId.includes('_')) {
            console.log(`🔍 [MODEL-SPLITTING] Found combination: ${originalModelId}`);
            combinationsFound++;
            
            // Split by underscore and create individual models
            const individualModelIds = originalModelId.split('_').map(id => id.trim());
            console.log(`   📝 [MODEL-SPLITTING] Splitting into: ${individualModelIds.join(', ')}`);
            
            individualModelIds.forEach(modelId => {
                if (modelId) { // Skip empty strings
                    // Create individual model data with recalculated scores
                    const adjustedTotalSearches = Math.round((modelData.total_searches || 0) / individualModelIds.length);
                    const adjustedSuccessfulSearches = Math.round((modelData.successful_searches || 0) / individualModelIds.length);
                    const adjustedSuccessRate = adjustedTotalSearches > 0 ? adjustedSuccessfulSearches / adjustedTotalSearches : 0;
                    
                    // 🚀 LOGIC-REVOLUTION PHASE 2.1: 5-Komponenten Score-Berechnung
                    const revolutionaryScore = calculateRevolutionary5ComponentScore({
                        model_id: modelId,
                        provider: modelId.includes(':') ? modelId.split(':')[0] : 'unknown',
                        total_searches: adjustedTotalSearches,
                        successful_searches: adjustedSuccessfulSearches,
                        success_rate: adjustedSuccessRate,
                        _split_factor: individualModelIds.length
                    });
                    
                    const individualModel = {
                        ...modelData, // Copy all original data
                        model_id: modelId,
                        provider: modelId.includes(':') ? modelId.split(':')[0] : 'unknown',
                        total_searches: adjustedTotalSearches,
                        successful_searches: adjustedSuccessfulSearches,
                        success_rate: adjustedSuccessRate,
                        success_rate_percent: adjustedSuccessRate * 100, // For display
                        // 🚀 REVOLUTIONARY SCORE: 5-Komponenten System
                        overall_score: revolutionaryScore.totalScore,
                        score_breakdown: revolutionaryScore.breakdown,
                        confidence_level: revolutionaryScore.confidenceLevel,
                        confidence_percentage: revolutionaryScore.confidencePercentage,
                        _original_combination: originalModelId, // Track original for debugging
                        _split_factor: individualModelIds.length // Track split factor
                    };
                    
                    splitModels.push(individualModel);
                    modelsCreated++;
                }
            });
        } else {
            // 🚀 LOGIC-REVOLUTION PHASE 2.2: Apply revolutionary scoring to ALL models
            const revolutionaryScore = calculateRevolutionary5ComponentScore({
                model_id: modelData.model_id,
                provider: modelData.provider || (modelData.model_id?.includes(':') ? modelData.model_id.split(':')[0] : 'unknown'),
                total_searches: modelData.total_searches || 0,
                successful_searches: modelData.successful_searches || 0,
                success_rate: modelData.success_rate || 0,
                _split_factor: 1
            });
            
            // Keep single models with revolutionary scores
            splitModels.push({
                ...modelData,
                // 🚀 REVOLUTIONARY SCORE: Apply to ALL models
                overall_score: revolutionaryScore.totalScore,
                score_breakdown: revolutionaryScore.breakdown,
                confidence_level: revolutionaryScore.confidenceLevel,
                confidence_percentage: revolutionaryScore.confidencePercentage,
                success_rate_percent: (modelData.success_rate || 0) * 100, // Ensure display format
                _original_combination: 'individual', // Mark as individual model for consolidation tracking
                _split_factor: 1
            });
            modelsCreated++;
        }
    });
    
    console.log(`✅ [MODEL-SPLITTING] Complete: ${combinationsFound} combinations → ${modelsCreated} individual models`);
    console.log(`📊 [MODEL-SPLITTING] Original: ${originalModels.length} models, New: ${splitModels.length} models`);
    
    // Return processed data
    return {
        ...statisticsData,
        models: splitModels,
        _split_metadata: {
            original_count: originalModels.length,
            new_count: splitModels.length,
            combinations_processed: combinationsFound,
            models_created: modelsCreated
        }
    };
}

// ============================================
// MINE DETAIL MODAL FUNCTIONS
// ============================================

/**
 * NEUE MINE DETAILS MODAL: Zeigt umfassende Statistiken für eine Mine
 */
async function showMineDetailsModal(mineName) {
    console.log(`[MINE MODAL] Opening details for: ${mineName}`);
    
    const modal = document.getElementById('mine-detail-modal');
    const title = document.getElementById('mine-modal-title');
    const body = document.getElementById('mine-modal-body');
    
    if (!modal || !title || !body) {
        console.error('[MINE MODAL] Modal elements not found');
        return;
    }
    
    // Update modal title
    title.textContent = `📊 ${mineName} - Detailstatistiken`;
    
    // Show loading state
    body.innerHTML = createLoadingHTML('Lade historische Mine-Daten...', 'Analysiere alle bisherigen Suchen für diese Mine');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    try {
        // Fetch historical statistics from new API
        const response = await fetch(`${window.API_BASE_URL}/api/consolidated/mine/${encodeURIComponent(mineName)}/statistics?days_back=90&exclude_exa=true`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Unbekannter Fehler beim Laden der Mine-Statistiken');
        }
        
        // Render detailed statistics
        renderMineDetailModal(data.data, mineName);
        
    } catch (error) {
        console.error('[MINE MODAL] Error loading statistics:', error);
        body.innerHTML = createErrorHTML(
            'Fehler beim Laden der Mine-Statistiken',
            error.message
        );
    }
}

/**
 * MINE DETAIL MODAL RENDERER
 */
function renderMineDetailModal(stats, mineName) {
    const body = document.getElementById('mine-modal-body');
    
    if (!stats) {
        body.innerHTML = createErrorHTML('Keine Daten verfügbar', 'Für diese Mine wurden keine Statistiken gefunden.');
        return;
    }
    
    const fields = stats.field_statistics || {};
    const models = stats.model_performance || {};
    const quality = stats.quality_metrics || {};
    const timeline = stats.timeline || {};
    
    // Erstelle Field-Statistiken Cards
    const fieldCards = Object.entries(fields).map(([fieldName, fieldData]) => {
        const consistency = fieldData.consistency_rate || 0;
        const consistencyClass = consistency > 80 ? 'high' : consistency > 60 ? 'medium' : 'low';
        
        return `
            <div class="field-stat-card">
                <div class="field-header">
                    <h4>${sanitizeHTML(fieldName)}</h4>
                    <span class="consistency-badge ${consistencyClass}">${consistency}% konsistent</span>
                </div>
                <div class="field-details">
                    <div class="stat-item">
                        <strong>Häufigster Wert:</strong> 
                        <span class="value-highlight">${sanitizeHTML(fieldData.most_common_value || 'Unbekannt')}</span>
                    </div>
                    <div class="stat-item">
                        <strong>Gefunden von:</strong> ${fieldData.models_found_by?.join(', ') || 'Unbekannt'}
                    </div>
                    <div class="stat-item">
                        <strong>Modell-Übereinstimmung:</strong> ${Math.round(fieldData.model_agreement || 0)}%
                    </div>
                    <div class="stat-item">
                        <strong>Erste Entdeckung:</strong> ${fieldData.first_found || 'Unbekannt'}
                    </div>
                    ${fieldData.all_values && fieldData.all_values.length > 1 ? `
                        <details class="value-variants">
                            <summary>Alle gefundenen Werte (${fieldData.unique_values})</summary>
                            <ul>
                                ${fieldData.all_values.slice(0, 5).map(([value, count]) => 
                                    `<li>${sanitizeHTML(value)} <small>(${count}x)</small></li>`
                                ).join('')}
                            </ul>
                        </details>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // Erstelle Modell-Performance Übersicht
    const modelCards = Object.entries(models).map(([modelId, modelData]) => `
        <div class="model-performance-card">
            <h4>${sanitizeHTML(modelId)}</h4>
            <div class="model-stats">
                <div class="model-stat">
                    <span class="stat-label">Suchen:</span>
                    <span class="stat-value">${modelData.searches}</span>
                </div>
                <div class="model-stat">
                    <span class="stat-label">Ø Felder:</span>
                    <span class="stat-value">${modelData.avg_fields_found}</span>
                </div>
                <div class="model-stat">
                    <span class="stat-label">Erfolgsrate:</span>
                    <span class="stat-value">${modelData.success_rate}%</span>
                </div>
                <div class="model-stat">
                    <span class="stat-label">Ø Zeit:</span>
                    <span class="stat-value">${modelData.avg_response_time}s</span>
                </div>
            </div>
        </div>
    `).join('');
    
    body.innerHTML = `
        <div class="mine-detail-content">
            <!-- Qualitäts-Übersicht -->
            <div class="quality-overview">
                <div class="quality-card">
                    <h3>📈 Gesamtqualität</h3>
                    <div class="quality-score ${quality.overall_quality_score > 80 ? 'excellent' : quality.overall_quality_score > 60 ? 'good' : 'poor'}">
                        ${quality.overall_quality_score}%
                    </div>
                    <p class="quality-rating">${quality.consistency_rating} Konsistenz</p>
                </div>
                <div class="timeline-card">
                    <h3>⏱️ Zeitraum</h3>
                    <div class="timeline-info">
                        <div><strong>Erste Suche:</strong> ${timeline.first_search || 'Unbekannt'}</div>
                        <div><strong>Letzte Suche:</strong> ${timeline.last_search || 'Unbekannt'}</div>
                        <div><strong>Suchfrequenz:</strong> ${timeline.search_frequency || 'Unbekannt'}</div>
                        <div><strong>Gesamt Suchen:</strong> ${stats.analysis_period?.total_searches || 0}</div>
                    </div>
                </div>
                <div class="summary-card">
                    <h3>📊 Zusammenfassung</h3>
                    <div class="summary-stats">
                        <div><strong>Analysierte Felder:</strong> ${quality.total_fields_analyzed}</div>
                        <div><strong>Verwendete Modelle:</strong> ${quality.models_used_count}</div>
                        <div><strong>Analysezeit:</strong> ${stats.analysis_period?.days_back} Tage</div>
                    </div>
                </div>
            </div>
            
            <!-- Field-Statistiken -->
            <div class="section-header">
                <h3>🔍 Feld-Analyse (${Object.keys(fields).length} Felder)</h3>
            </div>
            <div class="field-stats-grid">
                ${fieldCards || '<p>Keine Feld-Daten verfügbar</p>'}
            </div>
            
            <!-- Modell-Performance -->
            <div class="section-header">
                <h3>⚡ Modell-Performance (${Object.keys(models).length} Modelle)</h3>
            </div>
            <div class="model-performance-grid">
                ${modelCards || '<p>Keine Modell-Daten verfügbar</p>'}
            </div>
        </div>
    `;
}

/**
 * CLOSE MINE DETAIL MODAL
 */
function closeMineDetailModal() {
    const modal = document.getElementById('mine-detail-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// ============================================
// VIEW TOGGLE EVENT HANDLERS
// ============================================

// Add event listeners for view toggle when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Set up view toggle buttons
    const toggleButtons = document.querySelectorAll('.toggle-btn');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const viewType = this.getAttribute('data-view');
            switchConsolidatedView(viewType);
        });
    });
    
    console.log('🔧 [VIEW TOGGLE] Event handlers set up for consolidated view switching');
});

// ============================================
// DEFINITIVE GLOBAL EXPORTS - NUR HIER!
// ============================================
// Alle wichtigen Tab-Loading-Funktionen exportieren
window.loadSources = loadSources;
window.loadResults = loadResults;
window.loadConsolidatedResults = loadConsolidatedResults;

// CSV Export Function - PHASE 16.1
window.exportConsolidatedCSV = exportConsolidatedCSV;

// PHASE 16.2: Field-specific Source Details Function
window.showFieldSourceDetails = showFieldSourceDetails;

// Display-Funktionen exportieren
window.displayGroupedSources = displayGroupedSources;
window.displayResultsTable = displayResultsTable;
window.displayConsolidatedResults = displayConsolidatedResults;
window.displayComprehensiveModelStatistics = displayComprehensiveModelStatistics;
window.displayBasicModelStatistics = displayBasicModelStatistics;

// NEUE FUNKTIONEN: Tabellen-Ansicht und Mine-Details
window.switchConsolidatedView = switchConsolidatedView;
window.showMineDetailsModal = showMineDetailsModal;
window.closeMineDetailModal = closeMineDetailModal;

// loadModelStatistics ist bereits korrekt in Zeile 264 als window-Funktion definiert

console.log('📊 MineSearch 2.0 - Display Functions loaded');
console.log('✅ [EXPORT] All critical tab-loading functions exported to window scope');