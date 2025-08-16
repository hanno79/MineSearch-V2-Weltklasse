/**
 * Author: rahn
 * Datum: 12.08.2025  
 * Version: 1.0
 * Beschreibung: TAB-AUTOLOADER System für MineSearch 2.0 Tab-Navigation
 */

/**
 * Auto-Loading System für Tab-Inhalte
 * Lädt automatisch Daten beim ersten Besuch eines Tabs
 */
const TabAutoLoader = {
    loadedTabs: new Set(['single']), // Single-Tab ist default geladen
    
    /**
     * Initialisiert das Auto-Loading-System
     */
    initialize() {
        console.log('🔄 [TAB-AUTOLOADER] Initializing tab auto-loading system...');
        
        // Event Listener für Header Navigation Items (UPDATED für Header Navigation)
        const navItems = document.querySelectorAll('.nav-item');
        console.log(`🎯 [TAB-AUTOLOADER] Found ${navItems.length} header navigation items`);
        
        navItems.forEach(navItem => {
            const tabName = navItem.dataset.tab;
            console.log(`🎯 [TAB-AUTOLOADER] Setting up listener for: ${tabName}`);
            navItem.addEventListener('click', (e) => {
                e.preventDefault();
                console.log(`📡 [TAB-AUTOLOADER] Tab changed to: ${tabName} via header navigation`);
                this.handleTabChange(`${tabName}-tab`); // Convert to old tab format for compatibility
            });
        });
        
        // FIX: Wait for header navigation to initialize first - EXTENDED DELAY
        // Initial load für default tab - delayed to allow header sync
        setTimeout(() => {
            console.log('🔄 [TAB-AUTOLOADER] Delayed initialization - checking current state...');
            
            // KRITISCH: Warte auf NavigationState und gebe Header-Navigation Priorität
            if (window.NavigationState && window.NavigationState.currentTab) {
                const currentTab = window.NavigationState.currentTab;
                console.log(`🎯 [TAB-AUTOLOADER] Header navigation is set to: ${currentTab} - following header lead`);
                
                // Nur UI aktualisieren, KEINE neue handleTabChange() da Header bereits gesetzt hat
                this.updateTabDisplay(currentTab);
                
                // Auto-Load nur wenn Tab noch nicht geladen
                if (!this.loadedTabs.has(currentTab)) {
                    console.log(`📥 [TAB-AUTOLOADER] Auto-loading data for header-selected tab: ${currentTab}`);
                    this.loadTabData(currentTab);
                    this.loadedTabs.add(currentTab);
                }
            } else {
                // Fallback nur wenn Header nicht initialisiert
                console.log('🔄 [TAB-AUTOLOADER] No header state - using single fallback');
                this.handleTabChange('single-tab');
            }
        }, 600); // ERWEITERTE Verzögerung: Header hat 500ms, wir warten 600ms
    },
    
    /**
     * Behandelt Tab-Wechsel und triggert Auto-Loading
     */
    handleTabChange(tabId) {
        const tabName = tabId.replace('-tab', '');
        console.log(`🔄 [TAB-AUTOLOADER] Switching to tab: ${tabName} (from ${tabId})`);
        
        // Update CSS-Klassen für Tab-Anzeige
        this.updateTabDisplay(tabName);
        
        // Prüfe ob Tab bereits geladen wurde
        if (!this.loadedTabs.has(tabName)) {
            console.log(`📥 [TAB-AUTOLOADER] First visit to ${tabName} tab - auto-loading data...`);
            this.loadTabData(tabName);
            this.loadedTabs.add(tabName);
        } else {
            console.log(`✅ [TAB-AUTOLOADER] Tab ${tabName} already loaded`);
        }
    },
    
    /**
     * Aktualisiert CSS-Klassen für Tab-Display
     */
    updateTabDisplay(activeTabName) {
        console.log(`🎨 [TAB-AUTOLOADER] Updating tab display for: ${activeTabName}`);
        
        // 1. Container-Klassen aktualisieren
        const container = document.querySelector('.container');
        if (container) {
            // Entferne alle Tab-Klassen
            const tabClasses = ['tab-single', 'tab-csv', 'tab-sources', 'tab-statistics', 'tab-consolidated'];
            container.classList.remove(...tabClasses);
            
            // Füge aktive Tab-Klasse hinzu
            container.classList.add(`tab-${activeTabName}`);
            console.log(`✅ [TAB-AUTOLOADER] Set container class to: tab-${activeTabName}`);
        }
        
        // 2. Tab-Content-Sections verwalten - KRITISCH für Sichtbarkeit
        const allTabContents = document.querySelectorAll('.tab-content');
        console.log(`🎨 [TAB-AUTOLOADER] Found ${allTabContents.length} tab contents to manage`);
        
        allTabContents.forEach(tabContent => {
            // WICHTIG: Verstecke alle Tabs durch Entfernen der active-Klasse
            tabContent.classList.remove('active');
            console.log(`🔄 [TAB-AUTOLOADER] Deactivated tab: ${tabContent.id}`);
        });
        
        // Aktiviere nur den gewünschten Tab
        const targetTabMap = {
            'single': 'single-search',
            'csv': 'csv-upload', 
            'sources': 'sources',
            'statistics': 'statistics',
            'consolidated': 'consolidated'
        };
        
        const targetTabId = targetTabMap[activeTabName];
        const activeTab = document.getElementById(targetTabId);
        
        if (activeTab) {
            // WICHTIG: Aktiviere nur den gewünschten Tab durch active-Klasse
            activeTab.classList.add('active');
            console.log(`✅ [TAB-AUTOLOADER] Activated tab content: ${targetTabId} with 'active' class`);
        } else {
            console.error(`❌ [TAB-AUTOLOADER] Tab content not found: ${targetTabId}`);
            console.log(`Available tabs:`, Array.from(allTabContents).map(t => t.id));
        }
    },
    
    /**
     * Lädt Daten für einen spezifischen Tab - MIT DELAYED LOADING
     */
    loadTabData(tabName) {
        console.log(`🔄 [TAB-AUTOLOADER] Loading data for tab: ${tabName}`);
        
        // KRITISCH: Warte auf display.js Funktionen mit retry-logic
        this.loadTabDataWithRetry(tabName, 0);
    },
    
    /**
     * Lädt Tab-Daten mit Retry-Logic für display.js Funktionen
     */
    loadTabDataWithRetry(tabName, attempt = 0) {
        const maxAttempts = 10;
        const retryDelay = 300;
        
        switch(tabName) {
            case 'sources':
                console.log('📚 [TAB-AUTOLOADER] Loading sources data...');
                if (typeof loadSources === 'function') {
                    loadSources('count', 'desc');
                    console.log('✅ [TAB-AUTOLOADER] Sources loaded via global function');
                } else if (typeof window.loadSources === 'function') {
                    window.loadSources('count', 'desc');
                    console.log('✅ [TAB-AUTOLOADER] Sources loaded via window.loadSources');
                } else if (attempt < maxAttempts) {
                    console.log(`🔄 [TAB-AUTOLOADER] loadSources not ready, retry ${attempt + 1}/${maxAttempts}...`);
                    setTimeout(() => this.loadTabDataWithRetry(tabName, attempt + 1), retryDelay);
                } else {
                    console.error('❌ [TAB-AUTOLOADER] loadSources function not found after all retries');
                }
                break;
                
            case 'statistics':
                console.log('📊 [TAB-AUTOLOADER] Loading statistics data...');
                if (typeof loadModelStatistics === 'function') {
                    loadModelStatistics();
                    console.log('✅ [TAB-AUTOLOADER] Statistics loaded via global function');
                } else if (typeof window.loadModelStatistics === 'function') {
                    window.loadModelStatistics();
                    console.log('✅ [TAB-AUTOLOADER] Statistics loaded via window.loadModelStatistics');
                } else if (attempt < maxAttempts) {
                    console.log(`🔄 [TAB-AUTOLOADER] loadModelStatistics not ready, retry ${attempt + 1}/${maxAttempts}...`);
                    setTimeout(() => this.loadTabDataWithRetry(tabName, attempt + 1), retryDelay);
                } else {
                    console.error('❌ [TAB-AUTOLOADER] loadModelStatistics function not found after all retries');
                }
                break;
                
            case 'consolidated':
                console.log('📋 [TAB-AUTOLOADER] Loading consolidated results...');
                if (typeof loadConsolidatedResults === 'function') {
                    loadConsolidatedResults('mine_name', 'asc');
                    console.log('✅ [TAB-AUTOLOADER] Consolidated loaded via global function');
                } else if (typeof window.loadConsolidatedResults === 'function') {
                    window.loadConsolidatedResults('mine_name', 'asc');
                    console.log('✅ [TAB-AUTOLOADER] Consolidated loaded via window.loadConsolidatedResults');
                } else if (attempt < maxAttempts) {
                    console.log(`🔄 [TAB-AUTOLOADER] loadConsolidatedResults not ready, retry ${attempt + 1}/${maxAttempts}...`);
                    setTimeout(() => this.loadTabDataWithRetry(tabName, attempt + 1), retryDelay);
                } else {
                    console.error('❌ [TAB-AUTOLOADER] loadConsolidatedResults function not found after all retries');
                }
                break;
                
            case 'csv':
                console.log('📊 [TAB-AUTOLOADER] CSV tab - no auto-loading needed');
                break;
                
            case 'single':
                console.log('🔍 [TAB-AUTOLOADER] Single search tab - no auto-loading needed');
                break;
                
            default:
                console.warn(`⚠️ [TAB-AUTOLOADER] Unknown tab: ${tabName}`);
        }
    }
};

// Auto-Initialize TabAutoLoader when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        TabAutoLoader.initialize();
    });
} else {
    TabAutoLoader.initialize();
}

console.log('🔄 [TAB-AUTOLOADER] Tab Auto-Loading System loaded');

// Export für globale Verfügbarkeit
window.TabAutoLoader = TabAutoLoader;