/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Search Functions & Logic
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (8498 → 500 Zeilen Regel)
 * Search Functions: Single Search, Batch Search, Model Loading, Form Validation
 */

// ============================================
// SEARCH EXECUTION FUNCTIONS
// ============================================

/**
 * SINGLE SEARCH: Startet eine Einzelsuche mit ausgewählten Modellen
 */
function startSingleSearch() {
    const selectedModels = Array.from(document.querySelectorAll('input[name="model"]:checked')).map(cb => cb.value);
    
    if (selectedModels.length === 0) {
        showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
        return;
    }
    
    // Hole Search-Optionen
    const twoPhaseEnabled = document.getElementById('two_phase_enabled').checked;
    const smartSearchEnabled = document.getElementById('smart_search_enabled').checked;
    const comprehensiveSearchEnabled = document.getElementById('comprehensive_search_enabled').checked;
    
    const formData = new FormData(document.getElementById('single-search-form'));
    
    const requestBody = {
        mine_name: formData.get('mine_name'),
        country: formData.get('country'),
        commodity: formData.get('commodity'),
        model_ids: selectedModels,
        comprehensive_search: comprehensiveSearchEnabled
    };
    
    let searchTypeText = "Standard-Suche";
    if (comprehensiveSearchEnabled) {
        searchTypeText = "🚀 Comprehensive Search";
    } else if (smartSearchEnabled) {
        searchTypeText = "🤖 Smart-Search";
    } else if (twoPhaseEnabled) {
        searchTypeText = "🔍 2-Phasen-Suche";
    }
    
    console.log(`🔍 [SEARCH] Starte ${searchTypeText} mit ${selectedModels.length} Modellen`);
    console.log(`📋 [SEARCH] Request Body:`, requestBody);
    
    const resultsDiv = document.getElementById('results');
    showLoadingMessage(resultsDiv, `${searchTypeText} läuft...`, 
        `Mine: ${requestBody.mine_name || 'Alle'} | Land: ${requestBody.country || 'Alle'} | Rohstoff: ${requestBody.commodity || 'Alle'}`, 
        true
    );
    
    // Timer wird bereits durch showLoadingMessage(startTimer=true) gestartet
    console.log('🕒 [TIMER] Timer should be started by showLoadingMessage');
    
    fetch(`${window.API_BASE_URL}/api/search/multi`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        console.log(`✅ [SEARCH] Response received:`, data);
        
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        if (data.success) {
            displayResults(data.data);
            showNotification(`✅ ${searchTypeText} erfolgreich abgeschlossen`, 'success');
        } else {
            console.error(`❌ [SEARCH] API Error:`, data.error);
            resultsDiv.innerHTML = createErrorHTML('Suche fehlgeschlagen', data.error || 'Unbekannter Fehler');
            showNotification(`❌ Suche fehlgeschlagen: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error(`❌ [SEARCH] Network Error:`, error);
        
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        resultsDiv.innerHTML = createErrorHTML('Verbindungsfehler', 'Bitte überprüfen Sie Ihre Netzwerkverbindung.');
        showNotification(`❌ Verbindungsfehler: ${error.message}`, 'error');
    });
}

/**
 * BATCH SEARCH: Startet eine Batch-Suche mit CSV-Upload
 */
function startBatchSearch() {
    const formData = new FormData(document.getElementById('batch-search-form'));
    
    // Validiere Eingaben
    const csvFile = formData.get('csv_file');
    const selectedModels = Array.from(document.querySelectorAll('input[name="model"]:checked')).map(cb => cb.value);
    
    if (!csvFile || csvFile.size === 0) {
        showNotification('Bitte wählen Sie eine CSV-Datei aus.', 'warning');
        return;
    }
    
    if (selectedModels.length === 0) {
        showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
        return;
    }
    
    // Hole Batch-Search-Optionen
    const twoPhaseEnabled = document.getElementById('batch_two_phase_enabled').checked;
    const smartSearchEnabled = document.getElementById('batch_smart_search_enabled').checked;
    const comprehensiveSearchEnabled = document.getElementById('batch_comprehensive_search_enabled').checked;
    
    // Füge Modelle zur FormData hinzu
    selectedModels.forEach(model => {
        formData.append('selected_models', model);
    });
    
    // Füge Search-Optionen hinzu
    formData.append('twoPhase', twoPhaseEnabled);
    formData.append('smartSearch', smartSearchEnabled);
    formData.append('comprehensive', comprehensiveSearchEnabled);
    
    let searchTypeText = "Batch Standard-Suche";
    if (comprehensiveSearchEnabled) {
        searchTypeText = "🚀 Batch Comprehensive Search";
    } else if (smartSearchEnabled) {
        searchTypeText = "🤖 Batch Smart-Search";
    } else if (twoPhaseEnabled) {
        searchTypeText = "🔍 Batch 2-Phasen-Suche";
    }
    
    console.log(`📊 [BATCH-SEARCH] Starte ${searchTypeText} mit ${selectedModels.length} Modellen`);
    
    const resultsDiv = document.getElementById('results');
    showLoadingMessage(resultsDiv, `${searchTypeText} läuft...`, 
        `CSV-Datei: ${csvFile.name} | Modelle: ${selectedModels.length}`, 
        true
    );
    
    // Timer wird bereits durch showLoadingMessage(startTimer=true) gestartet
    console.log('🕒 [BATCH-TIMER] Timer should be started by showLoadingMessage');
    
    fetch(`${window.API_BASE_URL}/api/batch-search`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(data => {
        console.log(`✅ [BATCH-SEARCH] Response received`);
        
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        resultsDiv.innerHTML = data;
        showNotification(`✅ ${searchTypeText} erfolgreich abgeschlossen`, 'success');
    })
    .catch(error => {
        console.error(`❌ [BATCH-SEARCH] Error:`, error);
        
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        resultsDiv.innerHTML = createErrorHTML('Batch-Suche fehlgeschlagen', error.message);
        showNotification(`❌ Batch-Suche fehlgeschlagen: ${error.message}`, 'error');
    });
}

// ============================================
// MODEL LOADING & SELECTION
// ============================================

/**
 * MODEL LOADING: Lädt verfügbare Modelle für die Auswahl
 */
async function loadModelsForFilter() {
    console.log('🔄 [MODEL-FILTER] Loading models for filter dropdown...');
    
    const modelSelection = document.getElementById('model-selection');
    if (!modelSelection) {
        console.error('❌ [DEBUG] model-selection element NOT FOUND!');
        return;
    }
    
    try {
        console.log(`🌐 [DEBUG] Making API call to: ${window.API_BASE_URL}/api/models`);
        const response = await fetch(`${window.API_BASE_URL}/api/models`);
        console.log(`📡 [DEBUG] API Response status: ${response.status}`);
        
        const data = await response.json();
        console.log(`📊 [DEBUG] API Response data.success: ${data.success}`);
        console.log(`📋 [DEBUG] Available models count: ${data.models ? Object.keys(data.models).length : 0}`);
        
        if (!data.success || !data.models) {
            throw new Error('Keine Modell-Daten verfügbar');
        }
        
        // Gruppiere Modelle nach Provider
        const providerGroups = {};
        Object.entries(data.models).forEach(([modelId, modelInfo]) => {
            const provider = modelId.split(':')[0];
            if (!providerGroups[provider]) {
                providerGroups[provider] = [];
            }
            providerGroups[provider].push({
                id: modelId,
                info: modelInfo
            });
        });
        
        console.log(`🏷️ [DEBUG] Providers found: ${Object.keys(providerGroups).join(', ')}`);
        
        // Generiere HTML für Model Selection
        let modelsHTML = '';
        
        Object.entries(providerGroups).forEach(([provider, models]) => {
            const providerName = provider.charAt(0).toUpperCase() + provider.slice(1);
            const providerId = provider.replace(/[^a-zA-Z0-9]/g, '_');
            
            modelsHTML += `
                <div class="provider-group" data-provider="${provider}">
                    <div style="display: flex; align-items: center; padding: 10px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; margin-bottom: 5px; cursor: pointer;" 
                         onclick="toggleProviderModels('${provider}')">
                        <input type="checkbox" id="provider_${providerId}" 
                               onchange="toggleProviderCheckbox('${provider}')" 
                               onclick="event.stopPropagation()"
                               style="margin-right: 10px;">
                        <strong style="flex: 1;">${providerName}</strong>
                        <span class="provider-toggle" style="font-weight: bold; color: #6c757d;">▼</span>
                    </div>
                    <div class="models-list" style="margin-left: 20px; display: block;">
            `;
            
            models.forEach(model => {
                const modelDisplayName = model.id.split(':')[1] || model.id;
                modelsHTML += `
                    <label style="display: block; padding: 5px; cursor: pointer;">
                        <input type="checkbox" name="model" value="${model.id}" 
                               onchange="updateProviderCheckboxState('${provider}')"
                               style="margin-right: 8px;">
                        ${modelDisplayName}
                    </label>
                `;
            });
            
            modelsHTML += `
                    </div>
                </div>
            `;
        });
        
        modelSelection.innerHTML = modelsHTML;
        console.log(`✅ [MODEL-FILTER] ${Object.keys(providerGroups).length} Provider mit ${Object.values(data.models).length} Modellen geladen`);
        
    } catch (error) {
        console.error('❌ [MODEL-FILTER] Error loading models:', error);
        modelSelection.innerHTML = createErrorHTML(
            'Modelle konnten nicht geladen werden', 
            error.message
        );
    }
}

// ============================================
// FORM VALIDATION & UTILITIES
// ============================================

/**
 * FORM VALIDATION: Validiert Search-Form-Eingaben
 */
function validateSearchForm(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form ${formId} not found`);
        return false;
    }
    
    const formData = new FormData(form);
    const mineName = formData.get('mine_name');
    const country = formData.get('country');
    const commodity = formData.get('commodity');
    
    // Mindestens ein Suchkriterium erforderlich
    if (!mineName && !country && !commodity) {
        showNotification('Bitte geben Sie mindestens ein Suchkriterium ein.', 'warning');
        return false;
    }
    
    // Modell-Auswahl prüfen
    const selectedModels = Array.from(document.querySelectorAll('input[name="model"]:checked'));
    if (selectedModels.length === 0) {
        showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
        return false;
    }
    
    return true;
}

/**
 * SEARCH OPTIONS: Behandelt Such-Optionen-Änderungen
 */
function handleSearchOptionsChange() {
    const twoPhase = document.getElementById('two_phase_enabled');
    const smartSearch = document.getElementById('smart_search_enabled');
    const comprehensive = document.getElementById('comprehensive_search_enabled');
    
    // Mutual exclusivity logic - nur eine Option gleichzeitig
    if (comprehensive && comprehensive.checked) {
        if (twoPhase) twoPhase.checked = false;
        if (smartSearch) smartSearch.checked = false;
    } else if (smartSearch && smartSearch.checked) {
        if (twoPhase) twoPhase.checked = false;
        if (comprehensive) comprehensive.checked = false;
    } else if (twoPhase && twoPhase.checked) {
        if (smartSearch) smartSearch.checked = false;
        if (comprehensive) comprehensive.checked = false;
    }
}

// ============================================
// SEARCH STATE MANAGEMENT
// ============================================

/**
 * SEARCH STATE: Verwaltet den aktuellen Suchzustand
 */
const SearchState = {
    isSearching: false,
    currentSearchId: null,
    currentSearchType: 'single',
    
    startSearch: function(searchId, searchType = 'single') {
        this.isSearching = true;
        this.currentSearchId = searchId;
        this.currentSearchType = searchType;
        
        // UI Updates
        const searchButton = document.querySelector('.search-submit-button');
        const cancelButton = document.querySelector('.cancel-search-button');
        
        if (searchButton) {
            ButtonStateController.setLoading(searchButton, 'Sucht...');
        }
        
        if (cancelButton) {
            cancelButton.style.display = 'inline-block';
        }
    },
    
    endSearch: function() {
        this.isSearching = false;
        this.currentSearchId = null;
        
        // UI Updates
        const searchButton = document.querySelector('.search-submit-button');
        const cancelButton = document.querySelector('.cancel-search-button');
        
        if (searchButton) {
            ButtonStateController.resetState(searchButton);
        }
        
        if (cancelButton) {
            cancelButton.style.display = 'none';
        }
        
        // Stop timer
        if (typeof stopSearchTimer === 'function') {
            stopSearchTimer();
        }
    },
    
    cancelCurrentSearch: function() {
        if (!this.isSearching) return;
        
        console.log(`🛑 [SEARCH] Cancelling ${this.currentSearchType} search`);
        
        // Abort API requests if SearchAPI is available
        if (window.SearchAPI && typeof SearchAPI.abortSearch === 'function') {
            SearchAPI.abortSearch(this.currentSearchId);
        }
        
        this.endSearch();
        
        // Update results display
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.innerHTML = createErrorHTML(
                'Suche abgebrochen', 
                'Die laufende Suche wurde vom Benutzer abgebrochen.'
            );
        }
        
        showNotification('🛑 Suche wurde abgebrochen', 'info');
    }
};

// ============================================
// SEARCH RESULT PROCESSING
// ============================================

/**
 * RESULTS PROCESSING: Verarbeitet und zeigt Suchergebnisse
 */
function processSearchResults(data, searchType = 'single') {
    console.log(`📊 [RESULTS] Processing ${searchType} search results`);
    
    if (!data || !data.results) {
        console.error('❌ [RESULTS] No results data provided');
        return;
    }
    
    const results = Array.isArray(data.results) ? data.results : [data.results];
    
    // Statistiken
    const totalResults = results.length;
    const successfulResults = results.filter(r => r.success).length;
    const uniqueMines = [...new Set(results.map(r => r.mine_name))].filter(Boolean);
    
    console.log(`📈 [RESULTS] Statistics: ${successfulResults}/${totalResults} erfolgreiche Ergebnisse, ${uniqueMines.length} eindeutige Minen`);
    
    // Update search state
    SearchState.endSearch();
    
    return {
        total: totalResults,
        successful: successfulResults,
        mines: uniqueMines,
        results: results
    };
}

// ============================================
// GLOBAL EXPORTS & INITIALIZATION
// ============================================

// Export search functions to global scope
window.startSingleSearch = startSingleSearch;
window.startBatchSearch = startBatchSearch;
window.loadModelsForFilter = loadModelsForFilter;
window.validateSearchForm = validateSearchForm;
window.handleSearchOptionsChange = handleSearchOptionsChange;
window.SearchState = SearchState;
window.processSearchResults = processSearchResults;

// Initialize search options event handlers
document.addEventListener('DOMContentLoaded', function() {
    // Setup search option change handlers
    ['two_phase_enabled', 'smart_search_enabled', 'comprehensive_search_enabled'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', handleSearchOptionsChange);
        }
    });
    
    // Setup batch search option handlers
    ['batch_two_phase_enabled', 'batch_smart_search_enabled', 'batch_comprehensive_search_enabled'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', handleSearchOptionsChange);
        }
    });
});

console.log('🔍 MineSearch 2.0 - Search Functions loaded');