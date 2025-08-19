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
        
        console.log('🎨 [MODEL-UX] Progressive Model Selection initialized');
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadModels();
            this.setupEventListeners();
            this.renderQuickSelection();
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
                this.models = Array.isArray(data.models) ? data.models : [];
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
            const provider = model.provider_name || 'unknown';
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
                this.toggleAdvancedMode();
            }
            
            if (e.target.matches('.quick-model-pill')) {
                this.handleQuickSelection(e.target);
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
        if (!container) return;
        
        // Get provider stats
        const providerStats = Array.from(this.providers.entries()).map(([name, models]) => ({
            name,
            count: models.length,
            displayName: this.getProviderDisplayName(name)
        })).sort((a, b) => b.count - a.count);
        
        const quickSelectionHtml = `
            <div class="model-selection-enhanced">
                <h3 style="margin-bottom: var(--space-lg); color: var(--gray-800); display: flex; align-items: center; gap: var(--space-sm);">
                    🤖 Model Selection
                    <span style="background: var(--primary-100); color: var(--primary-700); padding: 4px 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">
                        ${this.models.length} verfügbar
                    </span>
                </h3>
                
                <!-- Quick Selection Pills -->
                <div class="quick-model-selection">
                    ${providerStats.slice(0, 6).map(provider => `
                        <div class="quick-model-pill" data-provider="${provider.name}">
                            ${provider.displayName}
                            <span class="count">${provider.count}</span>
                        </div>
                    `).join('')}
                    
                    <div class="quick-model-pill advanced-toggle-btn" style="background: var(--gray-100); color: var(--gray-700); border-color: var(--gray-300);">
                        ⚙️ Erweitert
                        <span class="count">Alle</span>
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
        this.updateSelectionSummary();
    }
    
    renderModelsGrid(provider) {
        const modelsToShow = provider === 'all' ? this.models : (this.providers.get(provider) || []);
        
        return modelsToShow.map(model => `
            <div class="model-card" data-model-id="${model.model_id}">
                <input type="checkbox" name="model" value="${model.model_id}" ${this.selectedModels.has(model.model_id) ? 'checked' : ''}>
                <div class="model-provider">${this.getProviderDisplayName(model.provider_name)}</div>
                <div class="model-name">${model.display_name || model.model_name}</div>
                <div class="model-description">
                    ${this.getModelDescription(model)}
                </div>
            </div>
        `).join('');
    }
    
    getProviderDisplayName(provider) {
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
        const descriptions = {
            'sonar': 'Echtzeitsuche mit aktuellen Daten',
            'sonar-pro': 'Erweiterte Echtzeitsuche',
            'deepseek': 'Leistungsstarkes Reasoning Model',
            'claude': 'Intelligente Textanalyse',
            'gpt': 'Vielseitiges Sprachmodell',
            'gemini': 'Google\'s multimodales Model'
        };
        
        const modelName = model.model_name.toLowerCase();
        for (const [key, description] of Object.entries(descriptions)) {
            if (modelName.includes(key)) {
                return description;
            }
        }
        
        return `${this.getProviderDisplayName(model.provider_name)} Model für Mining-Recherche`;
    }
    
    handleQuickSelection(pill) {
        const provider = pill.dataset.provider;
        
        if (provider) {
            // Select all models from this provider
            const providerModels = this.providers.get(provider) || [];
            const wasSelected = pill.classList.contains('selected');
            
            if (wasSelected) {
                // Deselect all provider models
                providerModels.forEach(model => {
                    this.selectedModels.delete(model.model_id);
                });
                pill.classList.remove('selected');
            } else {
                // Select all provider models
                providerModels.forEach(model => {
                    this.selectedModels.add(model.model_id);
                });
                pill.classList.add('selected');
            }
            
            this.syncWithExistingCheckboxes();
            this.updateSelectionSummary();
            
            console.log(`🔄 [MODEL-UX] Quick selection ${wasSelected ? 'deselected' : 'selected'}: ${provider} (${providerModels.length} models)`);
        }
    }
    
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
        existingCheckboxes.forEach(checkbox => {
            checkbox.checked = this.selectedModels.has(checkbox.value);
        });
        
        // REMOVED: Legacy checkboxes sync - no longer needed after cleanup
    }
    
    updateSelectionSummary() {
        const countElement = document.getElementById('selected-count');
        const clearButton = document.querySelector('.clear-selection-btn');
        
        if (countElement) {
            countElement.textContent = this.selectedModels.size;
        }
        
        if (clearButton) {
            clearButton.style.display = this.selectedModels.size > 0 ? 'block' : 'none';
        }
        
        // Update quick selection pills
        document.querySelectorAll('.quick-model-pill[data-provider]').forEach(pill => {
            const provider = pill.dataset.provider;
            const providerModels = this.providers.get(provider) || [];
            const selectedFromProvider = providerModels.filter(model => 
                this.selectedModels.has(model.model_id)
            ).length;
            
            pill.classList.toggle('selected', selectedFromProvider === providerModels.length && providerModels.length > 0);
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
        console.log('🎨 [MODEL-UX] Initializing Progressive Model Selection...');
        window.progressiveModelSelection = new ProgressiveModelSelection();
    }, 3000);
});

// Also try window load event as backup
window.addEventListener('load', () => {
    setTimeout(() => {
        if (!window.progressiveModelSelection) {
            console.log('🎨 [MODEL-UX] Backup initialization...');
            window.progressiveModelSelection = new ProgressiveModelSelection();
        }
    }, 1000);
});

console.log('🎨 [MODEL-UX] Progressive Model Selection loaded');