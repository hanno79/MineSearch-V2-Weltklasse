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
    
    // Create modal content
    const modalContent = `
        <div class="consolidated-detail-modal">
            <div class="modal-header">
                <h3>🏭 ${mineName} - Konsolidierte Details</h3>
            </div>
            
            <div class="modal-body">
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
                        <div class="fields-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Feld</th>
                                        <th>Wert</th>
                                        <th>Quelle</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Object.entries(mineData.best_values).map(([field, value]) => `
                                        <tr>
                                            <td><strong>${field}</strong></td>
                                            <td>${value || 'Nicht verfügbar'}</td>
                                            <td><small>Konsolidiert</small></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ` : ''}
                
                ${mineData.source_summary ? `
                    <div class="mine-sources">
                        <h4>📚 Quellen-Übersicht</h4>
                        <p><strong>Gesamte Quellen:</strong> ${mineData.source_summary.total_unique_sources}</p>
                    </div>
                ` : ''}
            </div>
            
            <div class="modal-footer">
                <button onclick="closeModal()" class="btn btn-primary">Schließen</button>
            </div>
        </div>
    `;
    
    // Show modal using existing modal system
    if (typeof showDetailModal === 'function') {
        showDetailModal('Konsolidierte Mine-Details', modalContent);
    } else {
        // Fallback: Simple alert if modal system not available
        alert(`Details für ${mineName}:\n\nFelder: ${mineData.best_values ? Object.keys(mineData.best_values).length : 0}\nQuellen: ${mineData.source_summary?.total_unique_sources || 0}`);
    }
}

/**
 * SHOW DETAIL MODAL: Generic modal display function
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
    
    // Create modal container
    const modal = document.createElement('div');
    modal.className = 'detail-modal';
    modal.style.cssText = `
        background: white;
        border-radius: 8px;
        max-width: 800px;
        max-height: 80vh;
        overflow-y: auto;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    `;
    
    modal.innerHTML = content;
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Close modal on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeModal();
        }
    });
    
    // Store reference for closing
    window.currentModal = overlay;
}

/**
 * CLOSE MODAL: Schließt das aktuelle Modal
 */
function closeModal() {
    if (window.currentModal) {
        document.body.removeChild(window.currentModal);
        window.currentModal = null;
    }
}

// Export display functions to global scope
window.loadSources = loadSources;
window.loadResults = loadResults;
window.loadConsolidatedResults = loadConsolidatedResults;
window.displayGroupedSources = displayGroupedSources;
window.displayResultsTable = displayResultsTable;
window.displayConsolidatedResults = displayConsolidatedResults;
window.displayComprehensiveModelStatistics = displayComprehensiveModelStatistics;
window.displayBasicModelStatistics = displayBasicModelStatistics;

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

// Export display functions to global scope
window.loadSources = loadSources;
window.loadResults = loadResults;
window.loadConsolidatedResults = loadConsolidatedResults;
window.displayGroupedSources = displayGroupedSources;
window.displayResultsTable = displayResultsTable;
window.displayConsolidatedResults = displayConsolidatedResults;
window.displayComprehensiveModelStatistics = displayComprehensiveModelStatistics;
window.displayBasicModelStatistics = displayBasicModelStatistics;

// Export detail view functions
window.viewConsolidatedDetail = viewConsolidatedDetail;
window.showDetailModal = showDetailModal;
window.closeModal = closeModal;
window.loadEnhancedSourceDetails = loadEnhancedSourceDetails;

console.log('📊 MineSearch 2.0 - Display Functions loaded');