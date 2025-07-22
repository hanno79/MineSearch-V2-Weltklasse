/*
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Navigation Management für MineSearch v2
*/

class Navigation {
    constructor() {
        this.activeTab = 'single-search';
        this.init();
    }

    init() {
        this.createNavigation();
        this.bindEvents();
        this.showTab(this.activeTab);
    }

    createNavigation() {
        const nav = document.getElementById('main-navigation');
        nav.innerHTML = `
            <div class="tab-navigation">
                <input type="radio" id="tab-single" name="search-tab" value="single-search" checked>
                <label for="tab-single">Einzelsuche</label>
                
                <input type="radio" id="tab-batch" name="search-tab" value="batch-search">
                <label for="tab-batch">Batch-Suche</label>
                
                <input type="radio" id="tab-sources" name="search-tab" value="sources">
                <label for="tab-sources">Quellen-Datenbank</label>
                
                <input type="radio" id="tab-results" name="search-tab" value="results">
                <label for="tab-results">Ergebnis-Datenbank</label>
                
                <input type="radio" id="tab-stats" name="search-tab" value="statistics">
                <label for="tab-stats">Statistiken</label>
            </div>
        `;
    }

    bindEvents() {
        document.querySelectorAll('input[name="search-tab"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.showTab(e.target.value);
                }
            });
        });
    }

    showTab(tabId) {
        this.activeTab = tabId;
        
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Load appropriate content
        this.loadTabContent(tabId);
    }

    loadTabContent(tabId) {
        const mainContent = document.getElementById('main-content');
        
        switch(tabId) {
            case 'single-search':
                this.loadSingleSearchForm(mainContent);
                break;
            case 'batch-search':
                this.loadBatchSearchForm(mainContent);
                break;
            case 'sources':
                this.loadSourcesView(mainContent);
                break;
            case 'results':
                this.loadResultsView(mainContent);
                break;
            case 'statistics':
                this.loadStatisticsView(mainContent);
                break;
        }
    }

    loadSingleSearchForm(container) {
        container.innerHTML = `
            <div class="tab-content active" id="single-search-content">
                <h2>Einzelsuche</h2>
                <form id="single-search-form" class="search-form active">
                    <div class="form-group">
                        <label for="mine-name">Mine Name:</label>
                        <input type="text" id="mine-name" name="mine_name" required 
                               placeholder="z.B. Grasberg, Canadian Malartic, Mount Isa">
                    </div>
                    <div class="form-group">
                        <label for="country">Land (optional):</label>
                        <input type="text" id="country" name="country" 
                               placeholder="z.B. Peru, Canada, Australien">
                    </div>
                    <div class="form-group">
                        <label for="commodity">Rohstoff (optional):</label>
                        <input type="text" id="commodity" name="commodity" 
                               placeholder="z.B. Gold, Kupfer, Eisenerz">
                    </div>
                    <button type="submit" class="unified-search-button">
                        🔍 Suche starten
                    </button>
                </form>
            </div>
        `;
    }

    loadBatchSearchForm(container) {
        container.innerHTML = `
            <div class="tab-content active" id="batch-search-content">
                <h2>Batch-Suche</h2>
                <div class="search-form active">
                    <p>CSV-Upload für mehrere Minen...</p>
                    <!-- Batch search form will be implemented here -->
                </div>
            </div>
        `;
    }

    loadSourcesView(container) {
        container.innerHTML = `
            <div class="tab-content active" id="sources-content">
                <h2>Quellen-Datenbank</h2>
                <div id="sources-statistics"></div>
                <div id="sources-table"></div>
            </div>
        `;
    }

    loadResultsView(container) {
        container.innerHTML = `
            <div class="tab-content active" id="results-content">
                <h2>Ergebnis-Datenbank</h2>
                <div id="results-statistics"></div>
                <div id="results-table"></div>
            </div>
        `;
    }

    loadStatisticsView(container) {
        container.innerHTML = `
            <div class="tab-content active" id="statistics-content">
                <h2>Statistiken</h2>
                <div id="statistics-charts"></div>
            </div>
        `;
    }
}

// Initialize navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.navigation = new Navigation();
});