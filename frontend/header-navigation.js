/**
 * Header Navigation System - PHASE 1: PROFESSIONAL HEADER REVOLUTION
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Navigation, Quick Search, Mobile Menu, Breadcrumbs für MineSearch 2.0
 */

// ============================================
// NAVIGATION STATE MANAGEMENT
// ============================================

const NavigationState = {
    currentTab: 'single',
    mobileMenuOpen: false,
    quickSearchActive: false,
    breadcrumbHistory: ['Dashboard', 'Einzelsuche'],
    
    setCurrentTab: function(tabName) {
        this.currentTab = tabName;
        this.updateBreadcrumb(tabName);
        this.updateActiveNavItems(tabName);
    },
    
    updateBreadcrumb: function(tabName) {
        const tabNames = {
            'single': 'Einzelsuche',
            'csv': 'CSV Batch',
            'consolidated': 'Konsolidierte Ergebnisse', 
            'statistics': 'Modell-Statistiken',
            'sources': 'Quellen-Registry'
        };
        
        this.breadcrumbHistory[1] = tabNames[tabName] || tabName;
        this.renderBreadcrumb();
    },
    
    updateActiveNavItems: function(tabName) {
        // Update header navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.tab === tabName) {
                item.classList.add('active');
            }
        });
        
        // Update tab navigation (existing system)
        const tabInput = document.getElementById(`${tabName}-tab`);
        if (tabInput) {
            tabInput.checked = true;
        }
    },
    
    renderBreadcrumb: function() {
        const breadcrumbNav = document.getElementById('breadcrumb-nav');
        if (!breadcrumbNav) return;
        
        const currentSection = document.getElementById('current-section');
        if (currentSection) {
            currentSection.querySelector('.breadcrumb-text').textContent = this.breadcrumbHistory[1];
        }
    }
};

// ============================================
// TAB SWITCHING & NAVIGATION
// ============================================

/**
 * Switch to specified tab (integrates with Tab-Autoloader system)
 */
function switchToTab(tabName) {
    console.log(`🧭 [NAVIGATION] Switching to tab: ${tabName}`);
    
    // Update navigation state
    NavigationState.setCurrentTab(tabName);
    
    // Integrate with TabAutoLoader system instead of old radio buttons
    if (window.TabAutoLoader && typeof TabAutoLoader.handleTabChange === 'function') {
        TabAutoLoader.handleTabChange(`${tabName}-tab`);
        console.log(`🔄 [NAVIGATION] Triggered TabAutoLoader for: ${tabName}`);
    }
    
    // Update URL hash (for back button support)
    history.replaceState(null, null, `#${tabName}`);
}

// ============================================
// QUICK SEARCH FUNCTIONALITY
// ============================================

/**
 * Execute Quick Search from header
 */
async function executeQuickSearch() {
    const quickSearchInput = document.getElementById('quick-search-input');
    const query = quickSearchInput ? quickSearchInput.value.trim() : '';
    
    if (!query) {
        showNotification('Bitte geben Sie einen Suchbegriff ein.', 'warning');
        return;
    }
    
    console.log(`🔍 [QUICK-SEARCH] Executing search for: ${query}`);
    
    // Switch to single search tab
    switchToTab('single');
    
    // Wait for tab to be active
    setTimeout(() => {
        // Fill search form
        const mineNameField = document.querySelector('input[name="mine_name"]');
        if (mineNameField) {
            mineNameField.value = query;
        }
        
        // Auto-select recommended models
        selectQuickPreset('recommended');
        
        // Start search automatically
        setTimeout(() => {
            startSingleSearch();
        }, 500);
        
    }, 300);
    
    // Clear quick search field
    quickSearchInput.value = '';
    hideQuickSearchSuggestions();
}

/**
 * Handle Enter key in quick search
 */
function handleQuickSearchKeydown(event) {
    if (event.key === 'Enter') {
        executeQuickSearch();
    } else if (event.key === 'Escape') {
        hideQuickSearchSuggestions();
    }
}

/**
 * Show quick search suggestions
 */
function showQuickSearchSuggestions(suggestions) {
    const suggestionsDiv = document.getElementById('quick-search-suggestions');
    if (!suggestionsDiv) return;
    
    if (!suggestions || suggestions.length === 0) {
        hideQuickSearchSuggestions();
        return;
    }
    
    let html = '';
    suggestions.forEach(suggestion => {
        html += `
            <div class="quick-search-suggestion" onclick="selectQuickSearchSuggestion('${suggestion.text}')">
                <span class="suggestion-icon">${suggestion.icon || '🔍'}</span>
                <span class="suggestion-text">${suggestion.text}</span>
                <span class="suggestion-type">${suggestion.type || ''}</span>
            </div>
        `;
    });
    
    suggestionsDiv.innerHTML = html;
    suggestionsDiv.style.display = 'block';
}

/**
 * Hide quick search suggestions
 */
function hideQuickSearchSuggestions() {
    const suggestionsDiv = document.getElementById('quick-search-suggestions');
    if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
    }
}

/**
 * Select a quick search suggestion
 */
function selectQuickSearchSuggestion(text) {
    const quickSearchInput = document.getElementById('quick-search-input');
    if (quickSearchInput) {
        quickSearchInput.value = text;
    }
    hideQuickSearchSuggestions();
    executeQuickSearch();
}

// ============================================
// MOBILE MENU FUNCTIONALITY
// ============================================

/**
 * Toggle mobile navigation menu
 */
function toggleMobileMenu() {
    NavigationState.mobileMenuOpen = !NavigationState.mobileMenuOpen;
    
    const mobileOverlay = document.getElementById('mobile-nav-overlay');
    if (!mobileOverlay) return;
    
    if (NavigationState.mobileMenuOpen) {
        mobileOverlay.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        console.log('📱 [MOBILE-MENU] Opened');
    } else {
        mobileOverlay.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
        console.log('📱 [MOBILE-MENU] Closed');
    }
}

// ============================================
// MODAL FUNCTIONS FOR HEADER ACTIONS
// ============================================

/**
 * Toggle Help Modal
 */
function toggleHelpModal() {
    console.log('❓ [HELP] Opening help modal');
    
    // Create help modal if it doesn't exist
    let helpModal = document.getElementById('help-modal');
    if (!helpModal) {
        helpModal = createHelpModal();
        document.body.appendChild(helpModal);
    }
    
    helpModal.style.display = helpModal.style.display === 'block' ? 'none' : 'block';
}

/**
 * Toggle Settings Modal
 */
function toggleSettingsModal() {
    console.log('⚙️ [SETTINGS] Opening settings modal');
    
    // Create settings modal if it doesn't exist
    let settingsModal = document.getElementById('settings-modal');
    if (!settingsModal) {
        settingsModal = createSettingsModal();
        document.body.appendChild(settingsModal);
    }
    
    settingsModal.style.display = settingsModal.style.display === 'block' ? 'none' : 'block';
}

/**
 * Create Help Modal
 */
function createHelpModal() {
    const modal = document.createElement('div');
    modal.id = 'help-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>🔍 MineSearch 2.0 - Hilfe & Dokumentation</h3>
                <button class="modal-close" onclick="toggleHelpModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="help-section">
                    <h4>🚀 Quick Start</h4>
                    <p>Verwenden Sie die <strong>Quick Search</strong> im Header für sofortige Suchen oder navigieren Sie zu den verschiedenen Bereichen:</p>
                    <ul>
                        <li><strong>🔍 Suche:</strong> Einzelne Mine-spezifische Recherche</li>
                        <li><strong>📊 Batch:</strong> Mehrere Minen über CSV-Upload</li>
                        <li><strong>📋 Ergebnisse:</strong> Alle gesammelten Recherche-Daten</li>
                        <li><strong>📈 Statistiken:</strong> Modell-Performance-Übersicht</li>
                        <li><strong>📚 Quellen:</strong> Verfügbare Datenquellen</li>
                    </ul>
                </div>
                
                <div class="help-section">
                    <h4>💡 Tipps</h4>
                    <ul>
                        <li>Nutzen Sie die <strong>Auto-Modell-Auswahl</strong> für beste Ergebnisse</li>
                        <li>Die <strong>2-Phasen-Suche</strong> liefert detailliertere Daten</li>
                        <li><strong>Mobile-Menü</strong> über das ☰ Symbol verfügbar</li>
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'none';
    return modal;
}

/**
 * Create Settings Modal
 */
function createSettingsModal() {
    const modal = document.createElement('div');
    modal.id = 'settings-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 700px;">
            <div class="modal-header">
                <h3>⚙️ MineSearch 2.0 - Einstellungen</h3>
                <button class="modal-close" onclick="toggleSettingsModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="settings-section">
                    <h4>🎨 Darstellung</h4>
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <input type="checkbox" id="dark-mode-toggle"> 
                        <span>Dark Mode aktivieren</span>
                    </label>
                </div>
                
                
                <div class="settings-section">
                    <h4>🤖 Standard-Suchoptionen (KONSOLIDIERT)</h4>
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                        <input type="checkbox" id="auto-2phase" checked> 
                        <span><strong>🔍 2-Phasen-Suche automatisch aktivieren</strong></span>
                    </label>
                    <small style="display: block; margin-left: 28px; margin-bottom: 15px; color: #555;">
                        Führt zusätzliche gezielte Suchen zu den besten gefundenen Quellen durch.<br>
                        <strong>Wird automatisch aktiviert</strong> bei wenigen Daten, fehlenden Restaurationskosten oder wenigen Quellen.
                    </small>
                    
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                        <input type="checkbox" id="auto-model-selection" checked> 
                        <span><strong>🤖 Smart-Search aktivieren</strong></span>
                    </label>
                    <small style="display: block; margin-left: 28px; margin-bottom: 10px; color: #555;">
                        Beginnt mit schneller Suche und wechselt automatisch zu einem besseren Modell,<br>
                        wenn weniger als 40% der Daten gefunden wurden. Transparenter Suchverlauf.
                    </small>
                </div>
                
                <div class="settings-section">
                    <h4>📊 Export-Einstellungen</h4>
                    <label style="display: block; margin-bottom: 10px;">
                        <span style="display: block; margin-bottom: 5px;">Standard Export-Format:</span>
                        <select id="default-export-format" style="width: 100%; padding: 8px;">
                            <option value="csv">CSV Format</option>
                            <option value="json">JSON Format</option>
                            <option value="excel">Excel Format</option>
                        </select>
                    </label>
                </div>
                
                <div class="settings-actions" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                    <button onclick="saveSettings()" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; margin-right: 10px; cursor: pointer;">
                        💾 Einstellungen speichern
                    </button>
                    <button onclick="resetSettings()" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                        🔄 Zurücksetzen
                    </button>
                </div>
                
                <div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 5px; font-size: 14px;">
                    <strong>ℹ️ Hinweis:</strong> Diese Einstellungen werden automatisch auf alle Such-Formulare angewendet. 
                    Doppelte Einstellungen wurden entfernt - das Header-Settings-Modal ist jetzt die einzige Einstellungsquelle.
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'none';
    
    // NOTE: Model selection removed from settings modal as requested
    // Models are now managed only on the main page
    
    return modal;
}

/**
 * Load Models for Settings Modal - DISABLED
 * NOTE: Model selection is now handled only on the main page as requested
 */
function loadModelsForSettingsModal() {
    console.log('ℹ️ [SETTINGS-MODAL] Model loading disabled - models managed on main page only');
    // Function disabled - model selection removed from settings modal
}

/**
 * Synchronize Modal Models with Main Page Models - DISABLED
 * NOTE: No longer needed as model selection removed from settings modal
 */
function syncModalWithMainModels() {
    console.log('ℹ️ [SYNC] Model sync disabled - no models in settings modal');
    // Function disabled - no model synchronization needed
}

/**
 * Save Settings (localStorage) - ERWEITERT für konsolidierte Einstellungen
 */
function saveSettings() {
    console.log('💾 [SETTINGS] Saving consolidated settings...');
    
    // Basic settings
    const settings = {
        darkMode: document.getElementById('dark-mode-toggle')?.checked || false,
        auto2Phase: document.getElementById('auto-2phase')?.checked || true,
        autoModelSelection: document.getElementById('auto-model-selection')?.checked || true,
        defaultExportFormat: document.getElementById('default-export-format')?.value || 'csv'
    };
    
    // NOTE: Model selection now managed only on main page
    // No need to save model selection from modal
    
    // Save to localStorage
    localStorage.setItem('minesearch-settings', JSON.stringify(settings));
    
    // Apply settings to all search forms immediately
    applySettingsToSearchForms(settings);
    
    showNotification('Einstellungen gespeichert und auf alle Such-Formulare angewendet!', 'success');
    toggleSettingsModal();
    
    console.log('✅ [SETTINGS] Settings saved:', settings);
}

/**
 * Apply Settings to Search Forms - KRITISCH für Synchronisation
 */
function applySettingsToSearchForms(settings) {
    console.log('🔄 [SETTINGS-SYNC] Applying settings to search forms...', settings);
    
    // 1. Synchronize 2-Phase Search setting (previously two_phase_enabled)
    if (settings.auto2Phase !== undefined) {
        // Create virtual checkbox for backward compatibility with existing search functions
        let virtualTwoPhase = document.getElementById('virtual-two-phase');
        if (!virtualTwoPhase) {
            virtualTwoPhase = document.createElement('input');
            virtualTwoPhase.type = 'checkbox';
            virtualTwoPhase.id = 'virtual-two-phase';
            virtualTwoPhase.style.display = 'none';
            document.body.appendChild(virtualTwoPhase);
        }
        virtualTwoPhase.checked = settings.auto2Phase;
        
        // Also create the old ID for compatibility
        let oldTwoPhase = document.getElementById('two_phase_enabled');
        if (!oldTwoPhase) {
            oldTwoPhase = document.createElement('input');
            oldTwoPhase.type = 'checkbox';
            oldTwoPhase.id = 'two_phase_enabled';
            oldTwoPhase.style.display = 'none';
            document.body.appendChild(oldTwoPhase);
        }
        oldTwoPhase.checked = settings.auto2Phase;
    }
    
    // 2. Synchronize Smart Search setting (previously smart_search_enabled)
    if (settings.autoModelSelection !== undefined) {
        let virtualSmartSearch = document.getElementById('virtual-smart-search');
        if (!virtualSmartSearch) {
            virtualSmartSearch = document.createElement('input');
            virtualSmartSearch.type = 'checkbox';
            virtualSmartSearch.id = 'virtual-smart-search';
            virtualSmartSearch.style.display = 'none';
            document.body.appendChild(virtualSmartSearch);
        }
        virtualSmartSearch.checked = settings.autoModelSelection;
        
        // Also create the old ID for compatibility
        let oldSmartSearch = document.getElementById('smart_search_enabled');
        if (!oldSmartSearch) {
            oldSmartSearch = document.createElement('input');
            oldSmartSearch.type = 'checkbox';
            oldSmartSearch.id = 'smart_search_enabled';
            oldSmartSearch.style.display = 'none';
            document.body.appendChild(oldSmartSearch);
        }
        oldSmartSearch.checked = settings.autoModelSelection;
    }
    
    // 3. Synchronize Model Selection (was previously in main page model-selection div)
    if (settings.selectedModels && settings.selectedModels.length > 0) {
        // Create virtual model selection container for backward compatibility
        let virtualModelContainer = document.getElementById('virtual-model-selection');
        if (!virtualModelContainer) {
            virtualModelContainer = document.createElement('div');
            virtualModelContainer.id = 'virtual-model-selection';
            virtualModelContainer.style.display = 'none';
            document.body.appendChild(virtualModelContainer);
        }
        
        // Create virtual checkboxes for each selected model
        settings.selectedModels.forEach(modelId => {
            let virtualCheckbox = document.getElementById(`virtual-${modelId}`);
            if (!virtualCheckbox) {
                virtualCheckbox = document.createElement('input');
                virtualCheckbox.type = 'checkbox';
                virtualCheckbox.id = `virtual-${modelId}`;
                virtualCheckbox.value = modelId;
                virtualCheckbox.name = 'models';
                virtualCheckbox.style.display = 'none';
                virtualModelContainer.appendChild(virtualCheckbox);
            }
            virtualCheckbox.checked = true;
        });
        
        // Also recreate the old model-selection container if needed by search functions
        let oldModelContainer = document.getElementById('model-selection');
        if (!oldModelContainer) {
            oldModelContainer = document.createElement('div');
            oldModelContainer.id = 'model-selection';
            oldModelContainer.style.display = 'none';
            document.body.appendChild(oldModelContainer);
        }
        
        // Clone the virtual checkboxes to old container
        oldModelContainer.innerHTML = '';
        settings.selectedModels.forEach(modelId => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `provider_${modelId.replace(':', '_')}`;
            checkbox.name = 'models';
            checkbox.value = modelId;
            checkbox.checked = true;
            checkbox.style.display = 'none';
            oldModelContainer.appendChild(checkbox);
        });
    }
    
    console.log('✅ [SETTINGS-SYNC] Settings applied to search forms successfully');
}

/**
 * Load Settings on Page Init - KRITISCH für Settings-Wiederherstellung
 */
function loadSavedSettings() {
    console.log('🔄 [SETTINGS-LOAD] Loading saved settings...');
    
    const savedSettings = localStorage.getItem('minesearch-settings');
    if (savedSettings) {
        try {
            const settings = JSON.parse(savedSettings);
            console.log('📋 [SETTINGS-LOAD] Found saved settings:', settings);
            
            // Apply settings to search forms
            applySettingsToSearchForms(settings);
            
            // Apply settings to header modal when it exists
            setTimeout(() => {
                const darkModeToggle = document.getElementById('dark-mode-toggle');
                if (darkModeToggle) darkModeToggle.checked = settings.darkMode || false;
                
                const auto2Phase = document.getElementById('auto-2phase');
                if (auto2Phase) auto2Phase.checked = settings.auto2Phase ?? true;
                
                const autoModelSelection = document.getElementById('auto-model-selection');
                if (autoModelSelection) autoModelSelection.checked = settings.autoModelSelection ?? true;
                
                const exportFormat = document.getElementById('default-export-format');
                if (exportFormat) exportFormat.value = settings.defaultExportFormat || 'csv';
                
                console.log('✅ [SETTINGS-LOAD] Settings applied to header modal');
            }, 500);
            
        } catch (error) {
            console.error('❌ [SETTINGS-LOAD] Error parsing saved settings:', error);
        }
    } else {
        console.log('ℹ️ [SETTINGS-LOAD] No saved settings found, using defaults');
        
        // Apply default settings
        const defaultSettings = {
            darkMode: false,
            auto2Phase: true,
            autoModelSelection: true,
            defaultExportFormat: 'csv',
            selectedModels: []
        };
        applySettingsToSearchForms(defaultSettings);
    }
}

/**
 * Reset Settings
 */
function resetSettings() {
    localStorage.removeItem('minesearch-settings');
    showNotification('Einstellungen zurückgesetzt!', 'info');
    toggleSettingsModal();
    
    // Reload settings with defaults
    setTimeout(() => {
        loadSavedSettings();
    }, 100);
}

// ============================================
// INITIALIZATION & EVENT LISTENERS
// ============================================

/**
 * Update Settings Status Display
 */
function updateSettingsStatusDisplay() {
    console.log('📊 [STATUS] Updating settings status display...');
    
    // Get current settings from localStorage or defaults
    const savedSettings = localStorage.getItem('minesearch-settings');
    let settings = {
        auto2Phase: true,
        autoModelSelection: true,
        selectedModels: []
    };
    
    if (savedSettings) {
        try {
            settings = { ...settings, ...JSON.parse(savedSettings) };
        } catch (error) {
            console.warn('⚠️ [STATUS] Error parsing saved settings, using defaults');
        }
    }
    
    // Update 2-Phase Search status
    const status2Phase = document.getElementById('status-2phase');
    if (status2Phase) {
        status2Phase.textContent = settings.auto2Phase ? '✅ EIN' : '❌ AUS';
        status2Phase.className = `setting-value ${settings.auto2Phase ? 'active' : 'inactive'}`;
    }
    
    // Update Smart Search status
    const statusSmart = document.getElementById('status-smart');
    if (statusSmart) {
        statusSmart.textContent = settings.autoModelSelection ? '✅ EIN' : '❌ AUS';
        statusSmart.className = `setting-value ${settings.autoModelSelection ? 'active' : 'inactive'}`;
    }
    
    // Update Models status
    const statusModels = document.getElementById('status-models');
    if (statusModels) {
        // Count selected models from main page (CONSISTENCY FIX: use name="model" selector)
        const selectedModels = document.querySelectorAll('input[name="model"]:checked');
        const modelCount = selectedModels.length;
        
        if (modelCount > 0) {
            statusModels.textContent = `${modelCount} ausgewählt`;
            statusModels.className = 'setting-value models-count';
        } else {
            // Check for quick preset selections
            const quickPresetActive = document.querySelector('.quick-pill.active');
            if (quickPresetActive) {
                const presetText = quickPresetActive.textContent.trim();
                statusModels.textContent = presetText;
                statusModels.className = 'setting-value models-count';
            } else {
                statusModels.textContent = 'Keine ausgewählt';
                statusModels.className = 'setting-value inactive';
            }
        }
    }
    
    console.log('✅ [STATUS] Settings status display updated');
}

/**
 * Synchronize Navigation State between Header and TabAutoLoader
 * FIX: Ensures both systems show the same active tab
 */
function syncNavigationState() {
    console.log('🔄 [SYNC] Synchronizing navigation state...');
    
    // Force both systems to show 'single' as active on page load
    NavigationState.setCurrentTab('single');
    
    // Also update TabAutoLoader if available
    if (window.TabAutoLoader && typeof TabAutoLoader.handleTabChange === 'function') {
        TabAutoLoader.handleTabChange('single-tab');
        console.log('✅ [SYNC] TabAutoLoader synchronized to single');
    }
    
    console.log('✅ [SYNC] Navigation state synchronized - both systems show single tab');
}

/**
 * Initialize Header Navigation System
 */
function initializeHeaderNavigation() {
    console.log('🧭 [NAVIGATION] Initializing professional header system...');
    
    // KRITISCH: Load saved settings on page init
    loadSavedSettings();
    
    // Set up quick search event listeners
    const quickSearchInput = document.getElementById('quick-search-input');
    if (quickSearchInput) {
        quickSearchInput.addEventListener('keydown', handleQuickSearchKeydown);
        quickSearchInput.addEventListener('focus', () => {
            NavigationState.quickSearchActive = true;
        });
        quickSearchInput.addEventListener('blur', () => {
            // Delay hiding suggestions to allow clicks
            setTimeout(() => {
                NavigationState.quickSearchActive = false;
                hideQuickSearchSuggestions();
            }, 200);
        });
    }
    
    // FIX: Explizite Initialisierung auf 'single' als default
    // Initialize from URL hash only if hash exists, otherwise default to 'single'
    const hash = window.location.hash.substring(1);
    if (hash && ['single', 'csv', 'consolidated', 'statistics', 'sources'].includes(hash)) {
        console.log(`🧭 [NAVIGATION] Initializing from URL hash: ${hash}`);
        NavigationState.setCurrentTab(hash);
    } else {
        console.log('🧭 [NAVIGATION] No valid hash - initializing to single tab');
        NavigationState.setCurrentTab('single'); // Explicit default initialization
    }
    
    // Close mobile menu on outside click
    document.addEventListener('click', (event) => {
        const mobileOverlay = document.getElementById('mobile-nav-overlay');
        if (mobileOverlay && mobileOverlay.style.display === 'block') {
            if (event.target === mobileOverlay) {
                toggleMobileMenu();
            }
        }
    });
    
    // Close modals on outside click
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal-overlay')) {
            event.target.style.display = 'none';
        }
    });
    
    // Initialize settings status display after a delay to allow models to load
    setTimeout(() => {
        updateSettingsStatusDisplay();
        
        // Set up periodic updates for model count
        setInterval(updateSettingsStatusDisplay, 5000);
    }, 3000);
    
    console.log('✅ [NAVIGATION] Professional header system initialized');
    console.log('✅ [SETTINGS] Consolidated settings system active - Header Modal is single source of truth');
    
    // FIX: Synchronize navigation state after both systems are loaded
    setTimeout(() => {
        syncNavigationState();
    }, 500); // Small delay to ensure TabAutoLoader is also initialized
}

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export functions to global scope
window.switchToTab = switchToTab;
window.executeQuickSearch = executeQuickSearch;
window.toggleMobileMenu = toggleMobileMenu;
window.toggleHelpModal = toggleHelpModal;
window.toggleSettingsModal = toggleSettingsModal;
window.saveSettings = saveSettings;
window.resetSettings = resetSettings;
window.NavigationState = NavigationState;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeHeaderNavigation);

console.log('🧭 Header Navigation System loaded');