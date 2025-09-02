/**
 * Author: rahn
 * Datum: 11.08.2025
 * Version: 1.0
 * Beschreibung: Progressive Model Selection UX für MineSearch 2.0
 * Verwaltet 55 Modelle mit modernem UX ohne Funktionalitätsverlust
 */

// ÄNDERUNG 11.08.2025: Progressive Model Selection System für weltbestes UI/UX
class ProgressiveModelSelection {
    constructor() {
        // SINGLETON FIX: Prevent multiple instances from overwriting each other
        if (window.progressiveModelSelection && window.progressiveModelSelection.isReady) {
            console.warn('⚠️ [MODEL-UX] SINGLETON: Attempting to create duplicate instance - returning existing');
            return window.progressiveModelSelection;
        }
        
        this.models = [];
        this.selectedModels = new Set();
        this.providers = new Map();
        this.currentProvider = 'all';
        this.isAdvancedMode = false;
        this.isReady = false;
        this._initializing = false;
        
        console.log('🎨 [MODEL-UX] Progressive Model Selection initialized - New Singleton instance');
        
        this.init();
    }
    
    async init() {
        // SINGLETON FIX: Mark as initializing to prevent double initialization
        this._initializing = true;
        
        try {
            await this.loadModels();
            this.setupEventListeners();
            this.renderQuickSelection();
            this.isReady = true;
            this._initializing = false;
            console.log('✅ [MODEL-UX] Progressive Model Selection ready - Singleton instance active');
        } catch (error) {
            this._initializing = false;
            console.error('❌ [MODEL-UX] Initialization failed:', error);
            throw error; // Re-throw to signal failure
        }
    }
    
    async loadModels() {
        try {
            // PROVIDER-STATUS 24.08.2025: Lade verfügbare und nicht verfügbare Modelle mit Grund
            const availableResponse = await fetch(`${window.API_BASE_URL}/api/available-models`);
            
            // Check HTTP status before parsing JSON
            if (!availableResponse.ok) {
                let errorMessage;
                try {
                    // Try to get JSON error details
                    const errorData = await availableResponse.json();
                    errorMessage = errorData.message || errorData.error || `HTTP ${availableResponse.status}`;
                } catch (jsonError) {
                    // Fall back to text if JSON parsing fails
                    try {
                        errorMessage = await availableResponse.text();
                    } catch (textError) {
                        errorMessage = `HTTP ${availableResponse.status} ${availableResponse.statusText}`;
                    }
                }
                throw new Error(`Available models API request failed (${availableResponse.status}): ${errorMessage}`);
            }
            
            const availableData = await availableResponse.json();
            
            if (availableData.success && availableData.data) {
                // Kombiniere verfügbare und nicht verfügbare Modelle
                const availableModels = availableData.data.available_models || {};
                const unavailableModels = availableData.data.unavailable_models || {};
                
                this.models = [
                    // Verfügbare Modelle
                    ...Object.entries(availableModels).map(([model_id, modelData]) => ({
                        model_id: model_id,
                        ...modelData,
                        display_name: modelData.name || model_id,
                        available: true,
                        provider_status: 'healthy'
                    })),
                    // Nicht verfügbare Modelle
                    ...Object.entries(unavailableModels).map(([model_id, modelData]) => ({
                        model_id: model_id,
                        ...modelData,
                        display_name: modelData.name || model_id,
                        available: false,
                        provider_status: modelData.provider_status || 'error',
                        error_reason: modelData.error || 'Provider nicht verfügbar'
                    }))
                ];
                
                this.organizeProviders();
                
                const availableCount = Object.keys(availableModels).length;
                const unavailableCount = Object.keys(unavailableModels).length;
                console.log(`📊 [MODEL-UX] Provider Status geladen: ${availableCount}✅ verfügbar, ${unavailableCount}❌ nicht verfügbar`);
            } else {
                console.log('📊 [MODEL-UX] Fallback zu legacy API...');
                await this.loadLegacyModels();
            }
        } catch (error) {
            console.error('❌ [MODEL-UX] Failed to load available models:', error);
            // FALLBACK: Legacy API
            try {
                await this.loadLegacyModels();
            } catch (legacyError) {
                console.error('❌ [MODEL-UX] Legacy API also failed:', legacyError);
                // Final fallback: extract existing models from DOM
                this.extractExistingModels();
            }
        }
    }

    async loadLegacyModels() {
        try {
            const response = await fetch(`${window.API_BASE_URL}/api/models`);
            
            // Check HTTP status before parsing JSON
            if (!response.ok) {
                let errorMessage;
                try {
                    // Try to get JSON error details
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorData.error || `HTTP ${response.status}`;
                } catch (jsonError) {
                    // Fall back to text if JSON parsing fails
                    try {
                        errorMessage = await response.text();
                    } catch (textError) {
                        errorMessage = `HTTP ${response.status} ${response.statusText}`;
                    }
                }
                throw new Error(`API request failed (${response.status}): ${errorMessage}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.models) {
                // ÄNDERUNG 22.08.2025: Fix für API-Datenformat - Object zu Array konvertieren
                if (Array.isArray(data.models)) {
                    this.models = data.models.map(model => ({
                        ...model,
                        available: true,
                        provider_status: 'unknown'
                    }));
                } else {
                    // Konvertiere Object zu Array mit model_id als Key
                    this.models = Object.entries(data.models).map(([model_id, modelData]) => ({
                        model_id: model_id,
                        ...modelData,
                        display_name: modelData.name || model_id,
                        available: true,
                        provider_status: 'unknown'
                    }));
                }
                this.organizeProviders();
                console.log(`📊 [MODEL-UX] Legacy: Loaded ${this.models.length} models from ${this.providers.size} providers`);
            } else {
                console.log('📊 [MODEL-UX] No models in API response, extracting existing...');
                this.extractExistingModels();
            }
        } catch (error) {
            console.error('❌ [MODEL-UX] Legacy API failed:', error);
            // FALLBACK: Use existing models if API fails
            this.extractExistingModels();
        }
    }
    
    extractExistingModels() {
        const existingCheckboxes = document.querySelectorAll('#model-selection input[type="checkbox"]');
        this.models = Array.from(existingCheckboxes).map(checkbox => {
            const value = checkbox.value;
            const [provider, model] = value.includes(':') ? value.split(':') : ['unknown', value];
            return {
                model_id: value,
                provider_name: provider,
                model_name: model,
                display_name: model
            };
        });
        this.organizeProviders();
        console.log(`📊 [MODEL-UX] Extracted ${this.models.length} existing models`);
    }
    
    organizeProviders() {
        this.providers.clear();
        
        if (!Array.isArray(this.models)) {
            console.error('❌ [MODEL-UX] Models is not an array:', typeof this.models);
            this.models = [];
            return;
        }
        
        console.log(`🏷️ [MODEL-UX] ORGANIZE DEBUG - Processing ${this.models.length} models`);
        
        this.models.forEach((model, index) => {
            // ÄNDERUNG 24.08.2025: Verwende provider_category für UI-Gruppierung statt technischen provider
            const provider = model.provider_category || model.provider || model.provider_name || 'unknown';
            
            // ROBUSTHEIT: Logge fehlende Provider-Informationen
            if (!model.provider_category && !model.provider && !model.provider_name) {
                console.warn(`⚠️ [MODEL-UX] Model ${index} (${model.model_id || 'NO-ID'}) has no provider information`);
            }
            
            if (!this.providers.has(provider)) {
                this.providers.set(provider, []);
                console.log(`🏷️ [MODEL-UX] Created new provider group: ${provider}`);
            }
            this.providers.get(provider).push(model);
        });
        
        console.log('🏷️ [MODEL-UX] Provider organization complete:');
        this.providers.forEach((models, provider) => {
            console.log(`  ${provider}: ${models.length} models`);
        });
    }
    
    setupEventListeners() {
        // Advanced Mode Toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('.advanced-toggle-btn')) {
                console.log('🎛️ [MODEL-UX] Advanced toggle clicked');
                this.toggleAdvancedMode();
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            if (e.target.matches('.smart-selection')) {
                console.log('🎯 [MODEL-UX] Smart selection clicked:', e.target.dataset.selectionType);
                console.log('🎯 [MODEL-UX] Current selected models count before:', this.selectedModels.size);
                this.handleSmartSelection(e.target);
                console.log('🎯 [MODEL-UX] Current selected models count after:', this.selectedModels.size);
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            if (e.target.matches('.provider-selection')) {
                console.log('🏢 [MODEL-UX] Provider selection clicked:', e.target.dataset.provider);
                console.log('🏢 [MODEL-UX] Current selected models count before:', this.selectedModels.size);
                this.handleProviderSelection(e.target);
                console.log('🏢 [MODEL-UX] Current selected models count after:', this.selectedModels.size);
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            if (e.target.matches('.provider-tab')) {
                this.switchProvider(e.target.dataset.provider);
            }
            
            if (e.target.matches('.model-card') || e.target.closest('.model-card')) {
                const card = e.target.matches('.model-card') ? e.target : e.target.closest('.model-card');
                this.toggleModelSelection(card);
            }
            
            if (e.target.matches('.clear-selection-btn')) {
                this.clearAllSelections();
            }
        });
        
        // Model checkbox changes
        document.addEventListener('change', (e) => {
            if (e.target.matches('#model-selection input[type="checkbox"]')) {
                const modelId = e.target.value;
                if (e.target.checked) {
                    this.selectedModels.add(modelId);
                } else {
                    this.selectedModels.delete(modelId);
                }
                this.updateSelectionSummary();
                this.syncWithExistingCheckboxes();
            }
        });
    }
    
    renderQuickSelection() {
        const container = document.getElementById('model-selection');
        if (!container) {
            console.warn('❌ [MODEL-UX] model-selection container not found');
            return;
        }
        
        console.log('🎨 [MODEL-UX] Rendering Progressive Model Selection UI...');
        console.log('🎨 [MODEL-UX] Container current innerHTML length:', container.innerHTML.length);
        
        // Get provider stats
        const providerStats = Array.from(this.providers.entries()).map(([name, models]) => ({
            name,
            count: models.length,
            displayName: this.getProviderDisplayName(name)
        })).sort((a, b) => b.count - a.count);
        
        // Get free models count - KOSTENLOS-FIX 24.08.2025: Multiple detection methods
        const freeModels = this.models.filter(model => 
            model.is_free === true || 
            (model.display_name && model.display_name.toLowerCase().includes('kostenlos')) ||
            (model.name && model.name.toLowerCase().includes('kostenlos')) ||
            (model.model_id && model.model_id.toLowerCase().includes('free'))
        );
        
        // Get top performance models (empirisch basiert auf bekannten starken Modellen)
        const topPerformanceModels = this.getTopPerformanceModels();
        
        const quickSelectionHtml = `
            <div class="model-selection-enhanced">
                <h3 style="margin-bottom: var(--space-lg); color: var(--gray-800); display: flex; align-items: center; gap: var(--space-sm);">
                    🤖 Model Selection
                    <span style="background: var(--primary-100); color: var(--primary-700); padding: 4px 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">
                        ${this.models.filter(m => m.available !== false).length}✅ verfügbar, ${this.models.filter(m => m.available === false).length}❌ nicht verfügbar
                    </span>
                </h3>
                
                <!-- PROVIDER STATUS OVERVIEW 24.08.2025 -->
                ${this.renderProviderStatusOverview()}
                
                <!-- Smart Quick Selection Pills -->
                <div class="quick-model-selection">
                    <!-- Smart Selections -->
                    <div class="quick-model-pill smart-selection" data-selection-type="free" style="background: var(--green-100); color: var(--green-700); border-color: var(--green-300);">
                        💰 Kostenlos
                        <span class="count">${freeModels.length}</span>
                    </div>
                    
                    <div class="quick-model-pill smart-selection" data-selection-type="top3" style="background: var(--gold-100); color: var(--gold-700); border-color: var(--gold-300);">
                        🏆 Top 3 Beste
                        <span class="count">3</span>
                    </div>
                    
                    <div class="quick-model-pill smart-selection" data-selection-type="all" style="background: var(--blue-100); color: var(--blue-700); border-color: var(--blue-300);">
                        🌟 Alle Modelle
                        <span class="count">${this.models.length}</span>
                    </div>
                    
                    <!-- Provider Groups -->
                    ${providerStats.map(provider => `
                        <div class="quick-model-pill provider-selection" data-provider="${provider.name}">
                            ${provider.displayName}
                            <span class="count">${provider.count}</span>
                        </div>
                    `).join('')}
                    
                    <div class="quick-model-pill advanced-toggle-btn" style="background: var(--gray-100); color: var(--gray-700); border-color: var(--gray-300);">
                        ⚙️ Erweitert
                        <span class="count">Einzeln</span>
                    </div>
                </div>
                
                <!-- Advanced Model Browser -->
                <div class="advanced-model-browser">
                    <!-- Provider Tabs -->
                    <div class="provider-tabs">
                        <div class="provider-tab active" data-provider="all">
                            Alle Anbieter
                            <span class="model-count">${this.models.length}</span>
                        </div>
                        ${Array.from(this.providers.entries()).map(([provider, models]) => `
                            <div class="provider-tab" data-provider="${provider}">
                                ${this.getProviderDisplayName(provider)}
                                <span class="model-count">${models.length}</span>
                            </div>
                        `).join('')}
                    </div>
                    
                    <!-- Models Grid -->
                    <div class="models-grid" id="models-grid">
                        ${this.renderModelsGrid('all')}
                    </div>
                </div>
                
                <!-- Selection Summary -->
                <div class="selection-summary">
                    <div class="selected-models-count">
                        <strong data-selection-counter>0</strong> Modelle ausgewählt
                    </div>
                    <button class="clear-selection-btn" style="display: none;">
                        Alle abwählen
                    </button>
                </div>
                
                <!-- REMOVED: Legacy Compatibility Checkboxes - Caused counter inconsistency (name="models" vs name="model") -->
            </div>
        `;
        
        container.innerHTML = quickSelectionHtml;
        console.log('🎨 [MODEL-UX] UI rendered, new innerHTML length:', container.innerHTML.length);
        
        // Verify counter element was created
        const counterElement = document.getElementById('selected-count');
        console.log('🎨 [MODEL-UX] Counter element created:', !!counterElement);
        
        this.updateSelectionSummary();
    }
    
    renderProviderStatusOverview() {
        // PROVIDER STATUS OVERVIEW 24.08.2025: Zeige Provider-Probleme auf einen Blick
        const providerStats = new Map();
        
        this.models.forEach(model => {
            const provider = model.provider || model.model_id?.split(':')[0] || 'unknown';
            if (!providerStats.has(provider)) {
                providerStats.set(provider, { available: 0, unavailable: 0, errors: [] });
            }
            
            const stats = providerStats.get(provider);
            if (model.available === false) {
                stats.unavailable++;
                if (model.error_reason && !stats.errors.includes(model.error_reason)) {
                    stats.errors.push(model.error_reason);
                }
            } else {
                stats.available++;
            }
        });
        
        const problemProviders = Array.from(providerStats.entries())
            .filter(([provider, stats]) => stats.unavailable > 0)
            .sort((a, b) => b[1].unavailable - a[1].unavailable);
        
        if (problemProviders.length === 0) {
            return `
                <div class="provider-status-overview" style="margin-bottom: var(--space-lg);">
                    <div style="background: var(--success-50); color: var(--success-800); padding: var(--space-sm); border-radius: var(--radius-md); font-size: 0.9rem;">
                        ✅ Alle Provider funktionsfähig
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="provider-status-overview" style="margin-bottom: var(--space-lg);">
                <div class="provider-problems" style="background: var(--warning-50); border: 1px solid var(--warning-200); border-radius: var(--radius-md); padding: var(--space-sm);">
                    <div style="color: var(--warning-800); font-weight: 600; margin-bottom: var(--space-xs); font-size: 0.9rem;">
                        ⚠️ Provider mit Problemen:
                    </div>
                    ${problemProviders.map(([provider, stats]) => `
                        <div style="font-size: 0.8rem; color: var(--warning-700); margin-bottom: 2px;">
                            <strong>${this.getProviderDisplayName(provider)}:</strong> 
                            ${stats.unavailable}/${stats.available + stats.unavailable} Modelle nicht verfügbar
                            ${stats.errors.length > 0 ? `(${stats.errors.join(', ')})` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    renderModelsGrid(provider) {
        const modelsToShow = provider === 'all' ? this.models : (this.providers.get(provider) || []);
        
        return modelsToShow.map(model => {
            const isAvailable = model.available !== false;
            const isDisabled = !isAvailable;
            const statusClass = isAvailable ? 'model-available' : 'model-unavailable';
            const statusIcon = isAvailable ? '✅' : '❌';
            const statusText = isAvailable ? '' : `❌ ${model.error_reason || 'Nicht verfügbar'}`;
            
            return `
                <div class="model-card ${statusClass}" data-model-id="${model.model_id || ''}">
                    <input type="checkbox" name="model" value="${model.model_id || ''}" 
                           ${this.selectedModels.has(model.model_id) ? 'checked' : ''} 
                           ${isDisabled ? 'disabled' : ''}>
                    <div class="model-provider">
                        ${statusIcon} ${this.getProviderDisplayName(model.provider_category || model.provider_name || model.provider || model.model_id?.split(':')[0])}
                    </div>
                    <div class="model-name">${model.display_name || model.model_name || model.model_id || 'Unknown Model'}</div>
                    <div class="model-description">
                        ${isAvailable ? this.getModelDescription(model) : `<span class="error-message">${statusText}</span>`}
                    </div>
                    ${!isAvailable ? `<div class="model-status-details">Status: ${model.provider_status}</div>` : ''}
                </div>
            `;
        }).join('');
    }
    
    getProviderDisplayName(provider) {
        // SICHERHEITS-FIX: Verhindere undefined/null provider
        if (!provider || typeof provider !== 'string') {
            console.warn('[MODEL-UX] Invalid provider name:', provider);
            return 'Unknown Provider';
        }
        
        const displayNames = {
            'perplexity': 'Perplexity',
            'openrouter': 'OpenRouter',
            'abacus': 'Abacus AI',
            'tavily': 'Tavily',
            'exa': 'Exa',
            'openai': 'OpenAI',
            'anthropic': 'Anthropic',
            'gemini': 'Google Gemini',
            'grok': 'xAI Grok',
            'scrapingbee': 'ScrapingBee',
            'firecrawl': 'Firecrawl',
            'brightdata': 'BrightData',
        };
        return displayNames[provider] || provider.charAt(0).toUpperCase() + provider.slice(1);
    }
    
    getModelDescription(model) {
        // SICHERHEITS-FIX: Verhindere undefined model properties
        if (!model) {
            console.warn('[MODEL-UX] Invalid model object:', model);
            return 'Unknown Model';
        }
        
        const descriptions = {
            'sonar': 'Echtzeitsuche mit aktuellen Daten',
            'sonar-pro': 'Erweiterte Echtzeitsuche',
            'deepseek': 'Leistungsstarkes Reasoning Model',
            'claude': 'Intelligente Textanalyse',
            'gpt': 'Vielseitiges Sprachmodell',
            'gemini': 'Google\'s multimodales Model'
        };
        
        // Verwende model_name, model_id oder display_name als Fallback
        const modelName = (model.model_name || model.model_id || model.display_name || '').toLowerCase();
        
        for (const [key, description] of Object.entries(descriptions)) {
            if (modelName.includes(key)) {
                return description;
            }
        }
        
        return `${this.getProviderDisplayName(model.provider_name || model.model_id?.split(':')[0])} Model für Mining-Recherche`;
    }
    
    // SCORE-SYSTEM FIX 01.09.2025: Modell-Quality-Scores für echte Top 3 Auswahl
    getModelQualityScores() {
        // Empirische Mining-Research Quality Scores (0-100 Punkte)
        return {
            // Premium AI Models - Höchste Qualität
            'openrouter:claude-3.5-sonnet': 95,
            'openrouter:claude-3-opus': 93, 
            'openrouter:gpt-4o': 92,
            'openrouter:gemini-2.0-flash': 90,
            'openrouter:gpt-4-turbo': 89,
            'openrouter:deepseek-chat': 88,
            
            // Spezialisierte Research Models
            'abacus:deep-agent': 87,
            'tavily:deep-research': 86,
            'tavily:search': 85,
            
            // Gute kostenlose Models
            'openrouter:deepseek-free': 82,
            'openrouter:claude-3.5-haiku': 81,
            'openrouter:gemini-1.5-pro': 80,
            'openrouter:kimi-k2': 78,
            'openrouter:deepseek-reasoner': 77,
            'openrouter:gpt-4o-mini': 76,
            
            // Solid Models
            'openrouter:gemini-1.5-flash': 75,
            'openrouter:deepseek-chimera-free': 73,
            'openrouter:llama-3.3-nemotron-super': 72,
            'openrouter:glm-4.5': 70,
            'openrouter:mistral-small-free': 68,
            'openrouter:grok-2': 67,
            'openrouter:perplexity-sonar-pro': 66,
            'openrouter:perplexity-sonar': 65,
            
            // Specialized Tools
            'exa:neural-search': 75,
            'exa:research-pro': 73, 
            'exa:research': 70,
            'firecrawl:extract': 65,
            'scrapingbee:ai-extract': 60,
            
            // Standard scraping tools
            'firecrawl:scrape': 55,
            'firecrawl:crawl': 53,
            'scrapingbee:js-render': 50,
            'scrapingbee:basic-scrape': 45,
            'brightdata:browser-api': 52,
            'brightdata:web-scraper': 48,
            'brightdata:serp': 46
        };
    }
    
    getTopPerformanceModels() {
        // SCORE-BASIERTE TOP-3 AUSWAHL - FIX 01.09.2025
        console.log(`🏆 [MODEL-UX] Selecting top 3 models by quality score from ${this.models.length} available models`);
        
        const scores = this.getModelQualityScores();
        const availableModels = this.models.filter(model => model.available !== false);
        
        // Sortiere verfügbare Modelle nach Score (höchster zuerst)
        const scoredModels = availableModels
            .map(model => ({
                ...model,
                quality_score: scores[model.model_id] || 0  // Default 0 für unbekannte Modelle
            }))
            .sort((a, b) => b.quality_score - a.quality_score);
            
        console.log(`🏆 [MODEL-UX] Available models with scores:`);
        scoredModels.slice(0, 10).forEach(model => {
            console.log(`  ${model.model_id}: ${model.quality_score} points`);
        });
        
        // Nimm die ersten 3 (höchste Scores)
        const topModels = scoredModels.slice(0, 3);
        
        console.log(`🏆 [MODEL-UX] Top 3 selected:`, topModels.map(m => `${m.model_id} (${m.quality_score}pts)`).join(', '));
        return topModels;
    }
    
    handleSmartSelection(pill) {
        const selectionType = pill.dataset.selectionType;
        const wasSelected = pill.classList.contains('selected');
        
        console.log(`🎯 [MODEL-UX] Handling smart selection: ${selectionType}, wasSelected: ${wasSelected}`);
        
        let modelsToToggle = [];
        
        switch (selectionType) {
            case 'free':
                // KOSTENLOS-FIX 24.08.2025: Erweiterte kostenlos-Erkennung
                modelsToToggle = this.models.filter(model => 
                    (model.is_free === true || 
                     (model.display_name && model.display_name.toLowerCase().includes('kostenlos')) ||
                     (model.name && model.name.toLowerCase().includes('kostenlos')) ||
                     (model.model_id && model.model_id.toLowerCase().includes('free'))) &&
                    model.available !== false
                );
                console.log(`💰 [MODEL-UX] Available free models found: ${modelsToToggle.length}`);
                break;
                
            case 'top3':
                modelsToToggle = this.getTopPerformanceModels().filter(model => model.available !== false);
                console.log(`🏆 [MODEL-UX] Available top 3 models found: ${modelsToToggle.length}`);
                break;
                
            case 'all':
                modelsToToggle = this.models.filter(model => model.available !== false);
                console.log(`🌟 [MODEL-UX] All available models: ${modelsToToggle.length}`);
                break;
                
            default:
                console.warn(`❌ [MODEL-UX] Unknown selection type: ${selectionType}`);
                return;
        }
        
        if (!modelsToToggle || modelsToToggle.length === 0) {
            console.error(`❌ [MODEL-UX] No models found for selection type: ${selectionType}`);
            console.log(`🎯 [MODEL-UX] Available models summary:`);
            console.log(`  Total models: ${this.models.length}`);
            console.log(`  Available models: ${this.models.filter(m => m.available !== false).length}`);
            if (selectionType === 'free') {
                const freeCount = this.models.filter(model => 
                    (model.is_free === true || 
                     (model.display_name && model.display_name.toLowerCase().includes('kostenlos')) ||
                     (model.name && model.name.toLowerCase().includes('kostenlos')) ||
                     (model.model_id && model.model_id.toLowerCase().includes('free'))) &&
                    model.available !== false
                ).length;
                console.log(`  Free models available: ${freeCount}`);
            }
            return;
        }
        
        if (wasSelected) {
            // Deselect all models of this type - ROBUST ID FIX 01.09.2025
            let removedCount = 0;
            modelsToToggle.forEach((model, index) => {
                // ROBUST MODEL-ID DETECTION - Multiple fallbacks
                const modelId = model.model_id || model.id || model.value || model.name;
                
                if (modelId && this.selectedModels.has(modelId)) {
                    this.selectedModels.delete(modelId);
                    removedCount++;
                    console.log(`  ❌ Removed model ${index + 1}: ${modelId}`);
                } else if (modelId) {
                    console.log(`  ⚠️ Model ${index + 1} was not selected: ${modelId}`);
                } else {
                    console.error(`  ❌ Model ${index + 1} has no valid ID for deselection`);
                }
            });
            
            pill.classList.remove('selected');
            console.log(`🔄 [MODEL-UX] Smart deselection completed: ${selectionType} - ${removedCount}/${modelsToToggle.length} models removed`);
            console.log(`🔄 [MODEL-UX] Total selected models now: ${this.selectedModels.size}`);
        } else {
            // Select all models of this type - ROBUST ID FIX 01.09.2025
            let addedCount = 0;
            modelsToToggle.forEach((model, index) => {
                // ROBUST MODEL-ID DETECTION - Multiple fallbacks
                const modelId = model.model_id || model.id || model.value || model.name;
                
                if (modelId) {
                    this.selectedModels.add(modelId);
                    addedCount++;
                    console.log(`  ✅ Added model ${index + 1}: ${modelId}`);
                } else {
                    console.error(`  ❌ Model ${index + 1} has no valid ID:`, {
                        model_id: model.model_id,
                        id: model.id,
                        value: model.value,
                        name: model.name,
                        keys: Object.keys(model)
                    });
                }
            });
            
            // Visual feedback for successful selection
            pill.classList.add('selected');
            setTimeout(() => pill.classList.remove('selected'), 300); // Kurzes visuelles Feedback
            console.log(`✅ [MODEL-UX] Smart selection completed: ${selectionType} - ${addedCount}/${modelsToToggle.length} models added`);
            console.log(`✅ [MODEL-UX] Total selected models now: ${this.selectedModels.size}`);
        }
        
        this.syncWithExistingCheckboxes();
        this.updateSelectionSummary();
        this.updateAdvancedModeVisuals();
    }
    
    handleProviderSelection(pill) {
        const provider = pill.dataset.provider;
        
        console.log(`🏢 [MODEL-UX] PROVIDER SELECTION DEBUG - Handling: ${provider}`);
        console.log(`🏢 [MODEL-UX] Available providers:`, Array.from(this.providers.keys()));
        
        if (!provider) {
            console.error(`❌ [MODEL-UX] No provider found in pill dataset`);
            return;
        }
        
        // ROBUST PROVIDER MATCHING - FIX 01.09.2025
        let providerModels = this.providers.get(provider) || [];
        
        // Falls exakte Übereinstimmung fehlschlägt, versuche case-insensitive match
        if (providerModels.length === 0) {
            console.log(`🏢 [MODEL-UX] Exact match failed, trying case-insensitive...`);
            for (const [key, models] of this.providers.entries()) {
                if (key.toLowerCase() === provider.toLowerCase()) {
                    providerModels = models;
                    console.log(`🏢 [MODEL-UX] Found case-insensitive match: ${key}`);
                    break;
                }
            }
        }
        
        const wasSelected = pill.classList.contains('selected');
        console.log(`🏢 [MODEL-UX] Provider ${provider}: ${providerModels.length} models found, wasSelected: ${wasSelected}`);
        
        if (providerModels.length === 0) {
            console.error(`❌ [MODEL-UX] No models found for provider: ${provider}`);
            console.log(`🏢 [MODEL-UX] Available providers with counts:`);
            this.providers.forEach((models, key) => {
                console.log(`  ${key}: ${models.length} models`);
            });
            return;
        }
        
        if (wasSelected) {
            // Deselect all provider models - FIX 01.09.2025
            console.log(`🏢 [MODEL-UX] Deselecting ${providerModels.length} models for provider ${provider}`);
            providerModels.forEach(model => {
                if (model.model_id) {
                    this.selectedModels.delete(model.model_id);
                    console.log(`  ❌ Removed: ${model.model_id}`);
                }
            });
            pill.classList.remove('selected');
            console.log(`🔄 [MODEL-UX] Provider deselected: ${provider} (${providerModels.length} models removed)`);
        } else {
            // Select all available provider models - ROBUST ID FIX 01.09.2025
            const availableProviderModels = providerModels.filter(model => model.available !== false);
            console.log(`🏢 [MODEL-UX] Selecting ${availableProviderModels.length}/${providerModels.length} available models for provider ${provider}`);
            
            let addedCount = 0;
            availableProviderModels.forEach((model, index) => {
                // ROBUST MODEL-ID DETECTION - Multiple fallbacks
                const modelId = model.model_id || model.id || model.value || model.name;
                
                if (modelId) {
                    this.selectedModels.add(modelId);
                    addedCount++;
                    console.log(`  ✅ Added model ${index + 1}: ${modelId}`);
                } else {
                    console.error(`  ❌ Provider model ${index + 1} has no valid ID:`, {
                        model_id: model.model_id,
                        id: model.id,
                        value: model.value,
                        name: model.name,
                        keys: Object.keys(model)
                    });
                }
            });
            
            pill.classList.add('selected');
            console.log(`✅ [MODEL-UX] Provider selection completed: ${provider} - ${addedCount}/${availableProviderModels.length} models added`);
            console.log(`✅ [MODEL-UX] Total selected models now: ${this.selectedModels.size}`);
        }
        
        this.syncWithExistingCheckboxes();
        this.updateSelectionSummary();
        this.updateAdvancedModeVisuals();
    }
    
    // ENTFERNT: handleQuickSelection - wird durch spezifische handleSmartSelection und handleProviderSelection ersetzt
    
    toggleAdvancedMode() {
        this.isAdvancedMode = !this.isAdvancedMode;
        const advancedBrowser = document.querySelector('.advanced-model-browser');
        const toggleBtn = document.querySelector('.advanced-toggle-btn');
        
        if (this.isAdvancedMode) {
            advancedBrowser.classList.add('show');
            toggleBtn.textContent = '⬆️ Einfach';
            toggleBtn.querySelector('.count').textContent = 'Minimieren';
        } else {
            advancedBrowser.classList.remove('show');
            toggleBtn.innerHTML = '⚙️ Erweitert <span class="count">Alle</span>';
        }
        
        console.log(`🎛️ [MODEL-UX] Advanced mode: ${this.isAdvancedMode ? 'ON' : 'OFF'}`);
    }
    
    switchProvider(provider) {
        this.currentProvider = provider;
        
        // Update tab styling
        document.querySelectorAll('.provider-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.provider === provider);
        });
        
        // Update models grid
        const modelsGrid = document.getElementById('models-grid');
        modelsGrid.innerHTML = this.renderModelsGrid(provider);
        modelsGrid.classList.add('show');
        
        console.log(`📑 [MODEL-UX] Switched to provider: ${provider}`);
    }
    
    toggleModelSelection(card) {
        const modelId = card.dataset.modelId;
        const checkbox = card.querySelector('input[type="checkbox"]');
        
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) {
                this.selectedModels.add(modelId);
                card.classList.add('selected');
            } else {
                this.selectedModels.delete(modelId);
                card.classList.remove('selected');
            }
            
            this.syncWithExistingCheckboxes();
            this.updateSelectionSummary();
        }
    }
    
    clearAllSelections() {
        this.selectedModels.clear();
        
        // Clear visual selections
        document.querySelectorAll('.model-card').forEach(card => {
            card.classList.remove('selected');
            const checkbox = card.querySelector('input[type="checkbox"]');
            if (checkbox) checkbox.checked = false;
        });
        
        document.querySelectorAll('.quick-model-pill').forEach(pill => {
            pill.classList.remove('selected');
        });
        
        this.syncWithExistingCheckboxes();
        this.updateSelectionSummary();
        
        console.log('🧹 [MODEL-UX] All selections cleared');
    }
    
    syncWithExistingCheckboxes() {
        // CONSISTENCY FIX: Sync with main system checkboxes (name="model")  
        const existingCheckboxes = document.querySelectorAll('#model-selection input[type="checkbox"][name="model"]');
        console.log(`🔄 [MODEL-UX] SYNC DEBUG - Found ${existingCheckboxes.length} checkboxes to sync`);
        console.log(`🔄 [MODEL-UX] Selected models count: ${this.selectedModels.size}`);
        console.log(`🔄 [MODEL-UX] Selected models:`, Array.from(this.selectedModels));
        
        if (existingCheckboxes.length === 0) {
            console.warn(`⚠️ [MODEL-UX] No checkboxes found with selector: #model-selection input[type="checkbox"][name="model"]`);
            // Fallback: Try to find any checkboxes
            const allCheckboxes = document.querySelectorAll('#model-selection input[type="checkbox"]');
            console.log(`🔄 [MODEL-UX] Found ${allCheckboxes.length} total checkboxes in model-selection`);
            if (allCheckboxes.length > 0) {
                console.log(`🔄 [MODEL-UX] First checkbox name attribute:`, allCheckboxes[0].name);
            }
        }
        
        let syncCount = 0;
        existingCheckboxes.forEach(checkbox => {
            const wasChecked = checkbox.checked;
            const shouldBeChecked = this.selectedModels.has(checkbox.value);
            checkbox.checked = shouldBeChecked;
            
            if (wasChecked !== shouldBeChecked) {
                console.log(`🔄 [MODEL-UX] Synced ${checkbox.value}: ${wasChecked} → ${shouldBeChecked}`);
                syncCount++;
            }
        });
        
        console.log(`🔄 [MODEL-UX] Sync completed: ${syncCount} checkboxes changed`);
    }
    
    updateSelectionSummary() {
        console.log(`🔢 [MODEL-UX] updateSelectionSummary called, selectedModels.size: ${this.selectedModels.size}`);
        console.log(`🔢 [MODEL-UX] Selected models:`, Array.from(this.selectedModels));
        
        const count = this.selectedModels.size;
        const clearButton = document.querySelector('.clear-selection-btn');
        
        // STATE FIX 01.09.2025: Robuste Counter-Updates
        // Update all counter elements with data-selection-counter attribute
        const counterElements = document.querySelectorAll('[data-selection-counter]');
        console.log(`🔢 [MODEL-UX] Updating ${counterElements.length} counter elements to show: ${count}`);
        
        counterElements.forEach((element, index) => {
            const oldValue = element.textContent;
            element.textContent = count;
            console.log(`  Counter ${index + 1}: ${oldValue} → ${count}`);
        });
        
        // FALLBACK: Also update any other possible counter elements
        const fallbackSelectors = ['#selected-count', '.selected-models-count strong', '.selection-summary strong'];
        fallbackSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (element && element.textContent !== count.toString()) {
                    console.log(`🔢 [MODEL-UX] Fallback update for ${selector}: ${element.textContent} → ${count}`);
                    element.textContent = count;
                }
            });
        });
        
        // Update clear button visibility
        if (clearButton) {
            clearButton.style.display = count > 0 ? 'block' : 'none';
        }
        
        // Update pill states (inline implementation)
        this.updateProviderPillStates();
        
        // Update smart selection pills
        document.querySelectorAll('.smart-selection').forEach(pill => {
            const selectionType = pill.dataset.selectionType;
            let relevantModels = [];
            
            switch (selectionType) {
                case 'free':
                    // KOSTENLOS-FIX 24.08.2025: Erweiterte kostenlos-Erkennung
                    relevantModels = this.models.filter(model => 
                        model.is_free === true || 
                        (model.display_name && model.display_name.toLowerCase().includes('kostenlos')) ||
                        (model.name && model.name.toLowerCase().includes('kostenlos')) ||
                        (model.model_id && model.model_id.toLowerCase().includes('free'))
                    );
                    break;
                case 'top3':
                    relevantModels = this.getTopPerformanceModels();
                    break;
                case 'all':
                    relevantModels = this.models;
                    break;
            }
            
            const selectedFromRelevant = relevantModels.filter(model => 
                this.selectedModels.has(model.model_id)
            ).length;
            
            // SMART-SELECTION FIX 28.08.2025: Button bleibt deselektiert nach Aktion
            // Entferne automatische "selected" Markierung - Button soll nur temporär selected sein während Klick
            // pill.classList.toggle('selected', selectedFromRelevant === relevantModels.length && relevantModels.length > 0);
        });
        
        // Update provider selection pills
        document.querySelectorAll('.provider-selection').forEach(pill => {
            const provider = pill.dataset.provider;
            const providerModels = this.providers.get(provider) || [];
            const selectedFromProvider = providerModels.filter(model => 
                this.selectedModels.has(model.model_id)
            ).length;
            
            pill.classList.toggle('selected', selectedFromProvider === providerModels.length && providerModels.length > 0);
        });
        
        // Update old quick selection pills (legacy support)
        document.querySelectorAll('.quick-model-pill[data-provider]:not(.provider-selection)').forEach(pill => {
            const provider = pill.dataset.provider;
            const providerModels = this.providers.get(provider) || [];
            const selectedFromProvider = providerModels.filter(model => 
                this.selectedModels.has(model.model_id)
            ).length;
            
            pill.classList.toggle('selected', selectedFromProvider === providerModels.length && providerModels.length > 0);
        });
    }
    
    updateProviderPillStates() {
        // Update provider-specific pill states
        document.querySelectorAll('.provider-pill, .quick-model-pill[data-provider]').forEach(pill => {
            const provider = pill.dataset.provider;
            if (provider && this.providers.has(provider)) {
                const providerModels = this.providers.get(provider);
                const selectedFromProvider = providerModels.filter(model => 
                    this.selectedModels.has(model.model_id)
                ).length;
                
                // Update visual state based on selection
                pill.classList.toggle('selected', selectedFromProvider === providerModels.length && providerModels.length > 0);
                pill.classList.toggle('partial', selectedFromProvider > 0 && selectedFromProvider < providerModels.length);
            }
        });
    }
    
    updateAdvancedModeVisuals() {
        // Update model cards in advanced mode
        document.querySelectorAll('.model-card').forEach(card => {
            const modelId = card.dataset.modelId;
            const checkbox = card.querySelector('input[type="checkbox"]');
            
            if (checkbox) {
                checkbox.checked = this.selectedModels.has(modelId);
                card.classList.toggle('selected', this.selectedModels.has(modelId));
            }
        });
    }
    
    getSelectedModels() {
        return Array.from(this.selectedModels);
    }
}

// SINGLETON FIX 01.09.2025: Verhindere mehrfache Initialisierung
// Initialize Progressive Model Selection when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for existing model loading to complete, then initialize
    setTimeout(() => {
        if (!window.progressiveModelSelection) {
            console.log('🎨 [MODEL-UX] Initializing Progressive Model Selection...');
            window.progressiveModelSelection = new ProgressiveModelSelection();
        } else {
            console.log('🎨 [MODEL-UX] Progressive Model Selection already initialized, skipping...');
        }
    }, 500);
});

// SINGLETON FIX: Backup initialization ONLY if primary really failed
window.addEventListener('load', () => {
    setTimeout(() => {
        // CRITICAL FIX: Only initialize if NO instance exists OR it's not ready AND not currently initializing
        if (!window.progressiveModelSelection) {
            console.log('🎨 [MODEL-UX] SINGLETON: No instance found, creating backup instance');
            window.progressiveModelSelection = new ProgressiveModelSelection();
        } else if (!window.progressiveModelSelection.isReady && !window.progressiveModelSelection._initializing) {
            console.warn('⚠️ [MODEL-UX] SINGLETON: Primary instance failed to initialize, recreating');
            // Clear the failed instance
            delete window.progressiveModelSelection;
            window.progressiveModelSelection = new ProgressiveModelSelection();
        } else {
            console.log('✅ [MODEL-UX] SINGLETON: Primary instance is ready, no backup needed');
        }
    }, 2000);
});

console.log('🎨 [MODEL-UX] Progressive Model Selection loaded');