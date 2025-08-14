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
    
    // Hole Search-Optionen (mit Null-Checks für fehlende Elements)
    const twoPhaseElement = document.getElementById('two_phase_enabled');
    const smartSearchElement = document.getElementById('smart_search_enabled');  
    const comprehensiveElement = document.getElementById('comprehensive_search_enabled');
    
    const twoPhaseEnabled = twoPhaseElement ? twoPhaseElement.checked : false;
    const smartSearchEnabled = smartSearchElement ? smartSearchElement.checked : false;
    const comprehensiveSearchEnabled = comprehensiveElement ? comprehensiveElement.checked : false;
    
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
            displayResults(data);  // CRITICAL FIX: Pass full data object, not just data.data
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
 * BATCH SEARCH: Startet eine Batch-Suche mit 2-Schritt-Workflow (CSV Upload + Batch Search)
 * ÄNDERUNG 13.08.2025: Implementierung des korrekten Backend-Workflows
 * ÄNDERUNG 14.08.2025: AbortController Support für Abbruch-Funktion
 */

// Global abort controller für Batch Search
let batchSearchAbortController = null;

async function startBatchSearch() {
    const formData = new FormData(document.getElementById('csv-form'));
    
    // Validiere Eingaben
    const csvFile = formData.get('file');
    const selectedModels = Array.from(document.querySelectorAll('input[name="model"]:checked')).map(cb => cb.value);
    
    if (!csvFile || csvFile.size === 0) {
        showNotification('Bitte wählen Sie eine CSV-Datei aus.', 'warning');
        return;
    }
    
    if (selectedModels.length === 0) {
        showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
        return;
    }
    
    // Hole Batch-Search-Optionen (mit Null-Checks für fehlende Elements)
    const batchTwoPhaseElement = document.getElementById('batch_two_phase_enabled');
    const batchSmartSearchElement = document.getElementById('batch_smart_search_enabled');
    const batchComprehensiveElement = document.getElementById('batch_comprehensive_search_enabled');
    
    const twoPhaseEnabled = batchTwoPhaseElement ? batchTwoPhaseElement.checked : false;
    const smartSearchEnabled = batchSmartSearchElement ? batchSmartSearchElement.checked : false;
    const comprehensiveSearchEnabled = batchComprehensiveElement ? batchComprehensiveElement.checked : false;
    
    // NEUE FUNKTION: Batch Count Optionen auslesen
    const batchModeElement = document.querySelector('input[name="batch_mode"]:checked');
    const batchCountElement = document.getElementById('batch-count');
    
    const batchMode = batchModeElement ? batchModeElement.value : 'limited'; // Default: limited
    const batchCount = batchCountElement ? parseInt(batchCountElement.value) : 3; // Default: 3
    
    // Validierung
    if (batchMode === 'limited' && (isNaN(batchCount) || batchCount < 1 || batchCount > 100)) {
        showNotification('Die Anzahl der Minen muss zwischen 1 und 100 liegen.', 'warning');
        return;
    }
    
    console.log(`📊 [BATCH-OPTIONS] Mode: ${batchMode}, Count: ${batchCount}`);
    
    let searchTypeText = "Batch Standard-Suche";
    if (comprehensiveSearchEnabled) {
        searchTypeText = "🚀 Batch Comprehensive Search";
    } else if (smartSearchEnabled) {
        searchTypeText = "🤖 Batch Smart-Search";
    } else if (twoPhaseEnabled) {
        searchTypeText = "🔍 Batch 2-Phasen-Suche";
    }
    
    // Erweitere Search Type Text mit Count-Information
    const countText = batchMode === 'all' ? 'alle Minen' : `erste ${batchCount} Minen`;
    console.log(`📊 [BATCH-SEARCH] Starte ${searchTypeText} mit ${selectedModels.length} Modellen für ${countText}`);
    
    // Erstelle neue AbortController für diese Suche
    batchSearchAbortController = new AbortController();
    const signal = batchSearchAbortController.signal;
    
    const resultsDiv = document.getElementById('batch-results');
    showLoadingMessage(resultsDiv, `CSV wird hochgeladen...`, 
        `CSV-Datei: ${csvFile.name} | Verarbeitung: ${countText} mit ${selectedModels.length} Modellen`, 
        true, true, 'cancelBatchSearch()'  // Show cancel button
    );
    
    try {
        // SCHRITT 1: CSV UPLOAD - Erstelle Session ID
        console.log('📤 [BATCH-STEP-1] Uploading CSV file...');
        
        const uploadFormData = new FormData();
        uploadFormData.append('csv_file', csvFile);
        
        const uploadResponse = await fetch(`${window.API_BASE_URL}/api/upload-csv`, {
            method: 'POST',
            body: uploadFormData,
            signal: signal  // Add abort support
        });
        
        if (!uploadResponse.ok) {
            throw new Error(`CSV Upload fehlgeschlagen: ${uploadResponse.status}`);
        }
        
        // Extract session_id from HTML response (backend sends HTML with hidden session_id field)
        const uploadHtml = await uploadResponse.text();
        console.log(`✅ [BATCH-STEP-1] CSV uploaded successfully, HTML length: ${uploadHtml.length}`);
        
        // Extract session_id from HTML using regex
        const sessionIdMatch = uploadHtml.match(/name="session_id"\s+value="([^"]+)"/);
        if (!sessionIdMatch) {
            throw new Error('Session ID konnte nicht aus Upload-Response extrahiert werden');
        }
        
        const sessionId = sessionIdMatch[1];
        console.log(`🎯 [BATCH-STEP-1] Session ID extracted: ${sessionId}`);
        
        // Update UI for batch search phase
        showLoadingMessage(resultsDiv, `${searchTypeText} läuft...`, 
            `Session: ${sessionId.substring(0, 8)}... | Verarbeitung mit ${selectedModels.length} Modellen`, 
            false, true, 'cancelBatchSearch()' // Don't restart timer, continue from upload phase, show cancel button
        );
        
        // SCHRITT 2: BATCH SEARCH mit Session ID
        console.log('🔍 [BATCH-STEP-2] Starting batch search with session ID...');
        
        const batchFormData = new FormData();
        batchFormData.append('session_id', sessionId);
        batchFormData.append('search_type', comprehensiveSearchEnabled ? 'comprehensive' : 'standard');
        batchFormData.append('search_all', batchMode === 'all' ? 'true' : 'false');
        batchFormData.append('count', batchMode === 'limited' ? batchCount.toString() : '0');
        
        // Add selected models as comma-separated string
        batchFormData.append('selected_models', selectedModels.join(','));
        
        // Add search options
        batchFormData.append('twoPhase', twoPhaseEnabled.toString());
        batchFormData.append('smartSearch', smartSearchEnabled.toString());
        batchFormData.append('comprehensive', comprehensiveSearchEnabled.toString());
        
        const batchResponse = await fetch(`${window.API_BASE_URL}/api/batch-search`, {
            method: 'POST',
            body: batchFormData,
            signal: signal  // Add abort support
        });
        
        if (!batchResponse.ok) {
            const errorText = await batchResponse.text();
            console.error(`❌ [BATCH-STEP-2] Batch search failed: ${batchResponse.status}`, errorText);
            throw new Error(`Batch-Suche fehlgeschlagen (${batchResponse.status}): ${errorText}`);
        }
        
        const batchResultsHtml = await batchResponse.text();
        console.log(`✅ [BATCH-STEP-2] Batch search completed, HTML length: ${batchResultsHtml.length}`);
        
        // Stop timer
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        // Display results using safeSetHTML for proper HTML rendering
        safeSetHTML(resultsDiv, batchResultsHtml);
        showNotification(`✅ ${searchTypeText} erfolgreich abgeschlossen`, 'success');
        
    } catch (error) {
        console.error(`❌ [BATCH-SEARCH] Error:`, error);
        
        // Stop timer
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        // Handle abort vs other errors
        if (error.name === 'AbortError') {
            resultsDiv.innerHTML = createErrorHTML('Batch-Suche abgebrochen', 'Die Suche wurde vom Benutzer abgebrochen.');
            showNotification(`🛑 Batch-Suche wurde abgebrochen`, 'info');
        } else {
            resultsDiv.innerHTML = createErrorHTML('Batch-Suche fehlgeschlagen', error.message);
            showNotification(`❌ Batch-Suche fehlgeschlagen: ${error.message}`, 'error');
        }
    } finally {
        // Clean up abort controller
        batchSearchAbortController = null;
    }
}

/**
 * CANCEL BATCH SEARCH: Bricht die laufende Batch-Suche ab
 */
function cancelBatchSearch() {
    console.log('🛑 [CANCEL-BATCH] Aborting batch search...');
    
    if (batchSearchAbortController) {
        batchSearchAbortController.abort();
        console.log('✅ [CANCEL-BATCH] Batch search aborted successfully');
    } else {
        console.log('⚠️ [CANCEL-BATCH] No active batch search to abort');
    }
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
        
        // PHASE 2: Search Interface Revolution - Intelligente Provider-Kategorisierung
        console.log('🎨 [UI-REVOLUTION] Implementing Smart Model Selection...');
        
        // Smart Provider Categories & Priorities
        const providerCategories = {
            recommended: ['perplexity', 'openrouter', 'abacus'],
            webSearch: ['tavily', 'exa', 'grok'],
            premium: ['openai', 'anthropic', 'gemini'],
            scraping: ['scrapingbee', 'firecrawl', 'brightdata']
        };
        
        // Smart Defaults für beliebte Modelle
        const smartDefaults = [
            'perplexity:sonar-pro',
            'openrouter:deepseek-free', 
            'abacus:deep-agent'
        ];
        
        let modelsHTML = `
            <div class="search-interface-revolution">
                <!-- Quick Start Section -->
                <div class="quick-start-section">
                    <h4 style="color: var(--primary-700); margin-bottom: var(--space-md); display: flex; align-items: center; gap: var(--space-sm);">
                        ⚡ Quick Start
                        <span style="background: var(--success-100); color: var(--success-700); padding: 4px 8px; border-radius: var(--radius-sm); font-size: 0.75rem; font-weight: 600;">Empfohlen</span>
                    </h4>
                    <div class="quick-selection-pills">
                        <button type="button" class="quick-pill recommended" onclick="selectQuickPreset('recommended')" title="Beste Allround-Modelle für Mining-Recherche">
                            🏆 Beste Auswahl (3 Modelle)
                        </button>
                        <button type="button" class="quick-pill web-focus" onclick="selectQuickPreset('webSearch')" title="Modelle mit Web-Zugriff für aktuelle Daten">
                            🌐 Web-Suche (6 Modelle)
                        </button>
                        <button type="button" class="quick-pill premium" onclick="selectQuickPreset('premium')" title="Premium-Modelle für komplexe Analysen">
                            💎 Premium (12 Modelle)
                        </button>
                        <button type="button" class="quick-pill all" onclick="selectQuickPreset('all')" title="Alle verfügbaren Modelle verwenden">
                            🚀 Alle (55 Modelle)
                        </button>
                    </div>
                </div>

                <!-- Advanced Selection (Initially Hidden) -->
                <div class="advanced-selection-section" style="display: none;">
                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: var(--space-md);">
                        <h4 style="color: var(--gray-700); margin: 0;">⚙️ Erweiterte Auswahl</h4>
                        <button type="button" class="hide-advanced-btn" onclick="hideAdvancedSelection()">
                            ⬆️ Verbergen
                        </button>
                    </div>
        `;
        
        // Generate Provider Groups with improved UX
        Object.entries(providerGroups).forEach(([provider, models]) => {
            const providerName = getProviderDisplayName(provider);
            const providerId = provider.replace(/[^a-zA-Z0-9]/g, '_');
            const categoryInfo = getProviderCategory(provider, providerCategories);
            
            modelsHTML += `
                <div class="provider-group ${categoryInfo.class}" data-provider="${provider}">
                    <div class="provider-header" onclick="toggleProviderModels('${provider}')">
                        <input type="checkbox" id="provider_${providerId}" 
                               onchange="toggleProviderCheckbox('${provider}')" 
                               onclick="event.stopPropagation()">
                        <div class="provider-info">
                            <strong>${categoryInfo.icon} ${providerName}</strong>
                            <span class="provider-meta">${models.length} Modelle • ${categoryInfo.description}</span>
                        </div>
                        <span class="provider-toggle">▼</span>
                    </div>
                    <div class="models-list" style="display: none;">
            `;
            
            models.forEach(model => {
                const modelDisplayName = model.id.split(':')[1] || model.id;
                const isDefault = smartDefaults.includes(model.id);
                const modelMeta = getModelMeta(model.info);
                
                modelsHTML += `
                    <label class="model-option ${isDefault ? 'recommended' : ''}">
                        <input type="checkbox" name="model" value="${model.id}" 
                               ${isDefault ? 'checked' : ''}
                               onchange="updateProviderCheckboxState('${provider}')">
                        <div class="model-details">
                            <span class="model-name">${modelDisplayName} ${isDefault ? '⭐' : ''}</span>
                            <span class="model-description">${modelMeta.description}</span>
                            <div class="model-tags">
                                ${modelMeta.tags.map(tag => `<span class="tag ${tag.class}">${tag.text}</span>`).join('')}
                            </div>
                        </div>
                    </label>
                `;
            });
            
            modelsHTML += `
                    </div>
                </div>
            `;
        });
        
        modelsHTML += `
                </div>
                
                <!-- Show Advanced Button -->
                <div class="show-advanced-section">
                    <button type="button" class="show-advanced-btn" onclick="showAdvancedSelection()">
                        ⚙️ Erweiterte Auswahl anzeigen (${Object.values(data.models).length} Modelle)
                    </button>
                </div>
                
                <!-- Selection Summary -->
                <div class="selection-summary">
                    <div class="selected-count">
                        <strong id="selected-models-count">3</strong> Modelle ausgewählt
                    </div>
                    <button type="button" class="clear-selection" onclick="clearAllModels()" style="display: none;">
                        Alle abwählen
                    </button>
                </div>
            </div>
        `;
        
        modelSelection.innerHTML = modelsHTML;
        console.log(`✅ [UI-REVOLUTION] Smart Model Selection with ${Object.keys(providerGroups).length} providers and ${Object.values(data.models).length} models loaded`);
        
        // Initialize UI Revolution features
        initializeQuickPresets(providerGroups, data.models);
        updateSelectionCounter();
        
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

// ============================================
// UI REVOLUTION: SMART MODEL SELECTION
// Phase 2 Implementation
// ============================================

// Helper Functions für Search Interface Revolution
function getProviderDisplayName(provider) {
    const displayNames = {
        'perplexity': 'Perplexity',
        'openrouter': 'OpenRouter', 
        'abacus': 'Abacus AI',
        'tavily': 'Tavily Search',
        'exa': 'Exa Neural',
        'scrapingbee': 'ScrapingBee',
        'firecrawl': 'Firecrawl',
        'brightdata': 'Bright Data',
        'openai': 'OpenAI',
        'anthropic': 'Anthropic',
        'gemini': 'Google Gemini',
        'grok': 'Grok (X.AI)'
    };
    return displayNames[provider] || provider.charAt(0).toUpperCase() + provider.slice(1);
}

function getProviderCategory(provider, categories) {
    if (categories.recommended.includes(provider)) {
        return {
            class: 'recommended-provider',
            icon: '🏆',
            description: 'Empfohlen für Mining-Recherche'
        };
    }
    if (categories.webSearch.includes(provider)) {
        return {
            class: 'web-provider',
            icon: '🌐',
            description: 'Web-Suche mit aktuellen Daten'
        };
    }
    if (categories.premium.includes(provider)) {
        return {
            class: 'premium-provider',
            icon: '💎',
            description: 'Premium-Modelle für komplexe Analysen'
        };
    }
    if (categories.scraping.includes(provider)) {
        return {
            class: 'scraping-provider',
            icon: '🔍',
            description: 'Web-Scraping und Datenextraktion'
        };
    }
    return {
        class: 'standard-provider',
        icon: '🤖',
        description: 'Standard-Modelle'
    };
}

function getModelMeta(modelInfo) {
    const tags = [];
    let description = modelInfo.description || 'KI-Modell für Mining-Analyse';
    
    // Add capability tags
    if (modelInfo.is_free) {
        tags.push({ text: 'Kostenlos', class: 'free' });
    }
    if (modelInfo.supports_web_search) {
        tags.push({ text: 'Web-Suche', class: 'web' });
    }
    if (modelInfo.supports_deep_research) {
        tags.push({ text: 'Deep Research', class: 'research' });
    }
    if (modelInfo.max_tokens >= 10000) {
        tags.push({ text: 'Large Context', class: 'large' });
    }
    
    return { description, tags };
}

// Quick Preset Functions
function selectQuickPreset(presetType) {
    console.log(`🎯 [UI-REVOLUTION] Selecting preset: ${presetType}`);
    
    // Clear all selections first
    clearAllModels();
    
    const providerCategories = {
        recommended: ['perplexity', 'openrouter', 'abacus'],
        webSearch: ['tavily', 'exa', 'grok'],
        premium: ['openai', 'anthropic', 'gemini'],
        scraping: ['scrapingbee', 'firecrawl', 'brightdata']
    };
    
    let modelsToSelect = [];
    
    switch(presetType) {
        case 'recommended':
            modelsToSelect = [
                'perplexity:sonar-pro',
                'openrouter:deepseek-free',
                'abacus:deep-agent'
            ];
            break;
            
        case 'webSearch':
            modelsToSelect = document.querySelectorAll('input[name="model"]');
            modelsToSelect = Array.from(modelsToSelect)
                .filter(input => {
                    const provider = input.value.split(':')[0];
                    return providerCategories.webSearch.includes(provider);
                })
                .map(input => input.value);
            break;
            
        case 'premium':
            modelsToSelect = document.querySelectorAll('input[name="model"]');
            modelsToSelect = Array.from(modelsToSelect)
                .filter(input => {
                    const provider = input.value.split(':')[0];
                    return providerCategories.premium.includes(provider);
                })
                .map(input => input.value);
            break;
            
        case 'all':
            modelsToSelect = Array.from(document.querySelectorAll('input[name="model"]'))
                .map(input => input.value);
            break;
    }
    
    // Select the models
    modelsToSelect.forEach(modelId => {
        const checkbox = document.querySelector(`input[name="model"][value="${modelId}"]`);
        if (checkbox) {
            checkbox.checked = true;
            // Update provider checkbox state
            const provider = modelId.split(':')[0];
            updateProviderCheckboxState(provider);
        }
    });
    
    // Update counter and highlight selected preset
    updateSelectionCounter();
    
    // Highlight selected preset
    document.querySelectorAll('.quick-pill').forEach(pill => {
        pill.classList.remove('active');
    });
    document.querySelector(`.quick-pill.${presetType}`)?.classList.add('active');
    
    console.log(`✅ [UI-REVOLUTION] Selected ${modelsToSelect.length} models for preset: ${presetType}`);
}

function showAdvancedSelection() {
    document.querySelector('.advanced-selection-section').style.display = 'block';
    document.querySelector('.show-advanced-section').style.display = 'none';
    console.log('🔧 [UI-REVOLUTION] Advanced selection shown');
}

function hideAdvancedSelection() {
    document.querySelector('.advanced-selection-section').style.display = 'none';
    document.querySelector('.show-advanced-section').style.display = 'block';
    console.log('🔧 [UI-REVOLUTION] Advanced selection hidden');
}

function clearAllModels() {
    document.querySelectorAll('input[name="model"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    document.querySelectorAll('input[id^="provider_"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    document.querySelectorAll('.quick-pill').forEach(pill => {
        pill.classList.remove('active');
    });
    
    updateSelectionCounter();
    console.log('🧹 [UI-REVOLUTION] All models cleared');
}

function updateSelectionCounter() {
    const selectedCount = document.querySelectorAll('input[name="model"]:checked').length;
    const counterElement = document.getElementById('selected-models-count');
    const clearButton = document.querySelector('.clear-selection');
    
    if (counterElement) {
        counterElement.textContent = selectedCount;
    }
    
    if (clearButton) {
        clearButton.style.display = selectedCount > 0 ? 'block' : 'none';
    }
}

function initializeQuickPresets(providerGroups, models) {
    // Set default preset selection (recommended)
    setTimeout(() => {
        selectQuickPreset('recommended');
    }, 500);
    
    console.log('🎨 [UI-REVOLUTION] Quick presets initialized with smart defaults');
}

// Export search functions to global scope
window.startSingleSearch = startSingleSearch;
window.startBatchSearch = startBatchSearch;
window.cancelBatchSearch = cancelBatchSearch;
window.loadModelsForFilter = loadModelsForFilter;
window.validateSearchForm = validateSearchForm;
window.handleSearchOptionsChange = handleSearchOptionsChange;
window.SearchState = SearchState;

// Export UI Revolution functions
window.selectQuickPreset = selectQuickPreset;
window.showAdvancedSelection = showAdvancedSelection;
window.hideAdvancedSelection = hideAdvancedSelection;
window.clearAllModels = clearAllModels;
window.updateSelectionCounter = updateSelectionCounter;
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