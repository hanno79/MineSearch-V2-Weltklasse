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
        this.models = [];
        this.selectedModels = new Set();
        this.providers = new Map();
        this.currentProvider = 'all';
        this.isAdvancedMode = false;
        this.isReady = false;
        
        console.log('🎨 [MODEL-UX] Progressive Model Selection initialized');
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadModels();
            this.setupEventListeners();
            this.renderQuickSelection();
            this.isReady = true;
            console.log('✅ [MODEL-UX] Progressive Model Selection ready');
        } catch (error) {
            console.error('❌ [MODEL-UX] Initialization failed:', error);
        }
    }
    
    async loadModels() {
        try {
            const response = await fetch(`${window.API_BASE_URL}/api/models`);
            const data = await response.json();
            
            if (data.success && data.models) {
                // ÄNDERUNG 22.08.2025: Fix für API-Datenformat - Object zu Array konvertieren
                if (Array.isArray(data.models)) {
                    this.models = data.models;
                } else {
                    // Konvertiere Object zu Array mit model_id als Key
                    this.models = Object.entries(data.models).map(([model_id, modelData]) => ({
                        model_id: model_id,
                        ...modelData,
                        display_name: modelData.name || model_id
                    }));
                }
                this.organizeProviders();
                console.log(`📊 [MODEL-UX] Loaded ${this.models.length} models from ${this.providers.size} providers`);
            } else {
                console.log('📊 [MODEL-UX] No models in API response, extracting existing...');
                this.extractExistingModels();
            }
        } catch (error) {
            console.error('❌ [MODEL-UX] Failed to load models:', error);
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
        
        this.models.forEach(model => {
            // ÄNDERUNG 22.08.2025: Fix für API-Feld-Namen - provider statt provider_name
            const provider = model.provider || model.provider_name || 'unknown';
            if (!this.providers.has(provider)) {
                this.providers.set(provider, []);
            }
            this.providers.get(provider).push(model);
        });
        
        console.log('🏷️ [MODEL-UX] Organized providers:', Array.from(this.providers.keys()));
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
                this.handleSmartSelection(e.target);
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            if (e.target.matches('.provider-selection')) {
                console.log('🏢 [MODEL-UX] Provider selection clicked:', e.target.dataset.provider);
                this.handleProviderSelection(e.target);
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
        
        // Get free models count
        const freeModels = this.models.filter(model => model.is_free === true);
        
        // Get top performance models (empirisch basiert auf bekannten starken Modellen)
        const topPerformanceModels = this.getTopPerformanceModels();
        
        const quickSelectionHtml = `
            <div class="model-selection-enhanced">
                <h3 style="margin-bottom: var(--space-lg); color: var(--gray-800); display: flex; align-items: center; gap: var(--space-sm);">
                    🤖 Model Selection
                    <span style="background: var(--primary-100); color: var(--primary-700); padding: 4px 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">
                        ${this.models.length} verfügbar
                    </span>
                </h3>
                
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
                    ${providerStats.slice(0, 4).map(provider => `
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
                        <strong id="selected-count">0</strong> Modelle ausgewählt
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
    
    renderModelsGrid(provider) {
        const modelsToShow = provider === 'all' ? this.models : (this.providers.get(provider) || []);
        
        return modelsToShow.map(model => `
            <div class="model-card" data-model-id="${model.model_id || ''}">
                <input type="checkbox" name="model" value="${model.model_id || ''}" ${this.selectedModels.has(model.model_id) ? 'checked' : ''}>
                <div class="model-provider">${this.getProviderDisplayName(model.provider_name || model.model_id?.split(':')[0])}</div>
                <div class="model-name">${model.display_name || model.model_name || model.model_id || 'Unknown Model'}</div>
                <div class="model-description">
                    ${this.getModelDescription(model)}
                </div>
            </div>
        `).join('');
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
            'grok': 'Grok (X.AI)',
            'scrapingbee': 'ScrapingBee',
            'firecrawl': 'Firecrawl',
            'brightdata': 'Bright Data'
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
    
    getTopPerformanceModels() {
        // EMPIRISCHE TOP-3 PERFORMANCE MODELLE basierend auf Mining-Recherche Performance
        // Diese Auswahl basiert auf Performance-Tests und Datenqualität für Mining-Daten
        const topModels = [
            'openrouter:deepseek-free',      // Hervorragend bei strukturierten Mining-Daten
            'perplexity:sonar',              // Exzellent bei aktuellen Mining-Informationen  
            'openrouter:kimi-k2'             // Sehr gut bei komplexen Mining-Analysen
        ];
        
        // Filtriere nur existierende Modelle
        return this.models.filter(model => topModels.includes(model.model_id));
    }
    
    handleSmartSelection(pill) {
        const selectionType = pill.dataset.selectionType;
        const wasSelected = pill.classList.contains('selected');
        
        console.log(`🎯 [MODEL-UX] Handling smart selection: ${selectionType}, wasSelected: ${wasSelected}`);
        
        let modelsToToggle = [];
        
        switch (selectionType) {
            case 'free':
                modelsToToggle = this.models.filter(model => model.is_free === true);
                console.log(`💰 [MODEL-UX] Free models found: ${modelsToToggle.length}`);
                break;
                
            case 'top3':
                modelsToToggle = this.getTopPerformanceModels();
                console.log(`🏆 [MODEL-UX] Top 3 models found: ${modelsToToggle.length}`);
                break;
                
            case 'all':
                modelsToToggle = this.models;
                console.log(`🌟 [MODEL-UX] All models: ${modelsToToggle.length}`);
                break;
                
            default:
                console.warn(`❌ [MODEL-UX] Unknown selection type: ${selectionType}`);
                return;
        }
        
        if (!modelsToToggle || modelsToToggle.length === 0) {
            console.warn(`⚠️ [MODEL-UX] No models found for selection type: ${selectionType}`);
            return;
        }
        
        if (wasSelected) {
            // Deselect all models of this type
            modelsToToggle.forEach(model => {
                if (model.model_id) {
                    this.selectedModels.delete(model.model_id);
                }
            });
            pill.classList.remove('selected');
            console.log(`🔄 [MODEL-UX] Smart deselection: ${selectionType} (${modelsToToggle.length} models)`);
        } else {
            // Select all models of this type
            modelsToToggle.forEach(model => {
                if (model.model_id) {
                    this.selectedModels.add(model.model_id);
                }
            });
            pill.classList.add('selected');
            console.log(`✅ [MODEL-UX] Smart selection: ${selectionType} (${modelsToToggle.length} models)`);
        }
        
        this.syncWithExistingCheckboxes();
        this.updateSelectionSummary();
        this.updateAdvancedModeVisuals();
    }
    
    handleProviderSelection(pill) {
        const provider = pill.dataset.provider;
        
        console.log(`🏢 [MODEL-UX] Handling provider selection: ${provider}`);
        
        if (!provider) {
            console.warn(`⚠️ [MODEL-UX] No provider found in dataset`);
            return;
        }
        
        const providerModels = this.providers.get(provider) || [];
        const wasSelected = pill.classList.contains('selected');
        
        console.log(`🏢 [MODEL-UX] Provider ${provider} has ${providerModels.length} models, wasSelected: ${wasSelected}`);
        
        if (providerModels.length === 0) {
            console.warn(`⚠️ [MODEL-UX] No models found for provider: ${provider}`);
            return;
        }
        
        if (wasSelected) {
            // Deselect all provider models
            providerModels.forEach(model => {
                if (model.model_id) {
                    this.selectedModels.delete(model.model_id);
                }
            });
            pill.classList.remove('selected');
            console.log(`🔄 [MODEL-UX] Provider deselected: ${provider} (${providerModels.length} models)`);
        } else {
            // Select all provider models
            providerModels.forEach(model => {
                if (model.model_id) {
                    this.selectedModels.add(model.model_id);
                }
            });
            pill.classList.add('selected');
            console.log(`✅ [MODEL-UX] Provider selected: ${provider} (${providerModels.length} models)`);
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
        console.log(`🔄 [MODEL-UX] Syncing with ${existingCheckboxes.length} existing checkboxes`);
        console.log(`🔄 [MODEL-UX] Selected models count: ${this.selectedModels.size}`);
        console.log(`🔄 [MODEL-UX] Selected models:`, Array.from(this.selectedModels));
        
        existingCheckboxes.forEach(checkbox => {
            const wasChecked = checkbox.checked;
            checkbox.checked = this.selectedModels.has(checkbox.value);
            if (wasChecked !== checkbox.checked) {
                console.log(`🔄 [MODEL-UX] Checkbox ${checkbox.value}: ${wasChecked} → ${checkbox.checked}`);
            }
        });
        
        // REMOVED: Legacy checkboxes sync - no longer needed after cleanup
    }
    
    updateSelectionSummary() {
        console.log(`🔢 [MODEL-UX] updateSelectionSummary called, selectedModels.size: ${this.selectedModels.size}`);
        
        const countElement = document.getElementById('selected-count');
        const countElement2 = document.getElementById('selected-models-count'); // Legacy compatibility
        const clearButton = document.querySelector('.clear-selection-btn');
        
        // ÄNDERUNG 23.08.2025: Erweiterte Zähler-Aktualisierung für alle möglichen Elemente
        
        // Update Haupt-Zähler
        if (countElement) {
            console.log(`🔢 [MODEL-UX] Updating selected-count: ${countElement.textContent} → ${this.selectedModels.size}`);
            countElement.textContent = this.selectedModels.size;
        } else {
            console.log(`❌ [MODEL-UX] selected-count element not found`);
        }
        
        // Update Legacy-Zähler
        if (countElement2) {
            console.log(`🔢 [MODEL-UX] Updating selected-models-count: ${countElement2.textContent} → ${this.selectedModels.size}`);
            countElement2.textContent = this.selectedModels.size;
        } else {
            console.log(`❌ [MODEL-UX] selected-models-count element not found`);
        }
        
        // Update alle Zähler-Elemente die nur eine Zahl enthalten (spezifischer Selector)
        const specificCounters = document.querySelectorAll('.selected-models-count strong, .selection-summary strong');
        specificCounters.forEach((counter, index) => {
            if (counter.textContent.trim().match(/^\d+$/) && counter.parentElement.textContent.includes('Modelle ausgewählt')) {
                counter.textContent = this.selectedModels.size;
            }
        });
        
        // FALLBACK: Direkte Textinhalt-Ersetzung für "X Modelle ausgewählt" Pattern
        const textNodes = document.evaluate("//text()[contains(., 'Modelle ausgewählt') and string-length(.) < 50]", document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);
        for (let i = 0; i < textNodes.snapshotLength; i++) {
            const textNode = textNodes.snapshotItem(i);
            if (textNode && textNode.textContent.match(/^\d+ Modelle ausgewählt$/)) {
                textNode.textContent = `${this.selectedModels.size} Modelle ausgewählt`;
            }
        }
        
        if (clearButton) {
            clearButton.style.display = this.selectedModels.size > 0 ? 'block' : 'none';
        }
        
        // Update smart selection pills
        document.querySelectorAll('.smart-selection').forEach(pill => {
            const selectionType = pill.dataset.selectionType;
            let relevantModels = [];
            
            switch (selectionType) {
                case 'free':
                    relevantModels = this.models.filter(model => model.is_free === true);
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
            
            pill.classList.toggle('selected', selectedFromRelevant === relevantModels.length && relevantModels.length > 0);
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

// Backup initialization only if really needed
window.addEventListener('load', () => {
    setTimeout(() => {
        if (!window.progressiveModelSelection || !window.progressiveModelSelection.isReady) {
            console.log('🎨 [MODEL-UX] Backup initialization - primary failed...');
            window.progressiveModelSelection = new ProgressiveModelSelection();
        }
    }, 2000);
});

console.log('🎨 [MODEL-UX] Progressive Model Selection loaded');