/*
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Search Form Management für MineSearch v2
*/

class SearchForms {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Single search form submission
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'single-search-form') {
                e.preventDefault();
                this.handleSingleSearch(e.target);
            }
        });
    }

    async handleSingleSearch(form) {
        const formData = new FormData(form);
        const searchData = {
            mine_name: formData.get('mine_name'),
            country: formData.get('country') || null,
            commodity: formData.get('commodity') || null
        };

        // Show loading state
        this.showLoadingState(true);

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.displayResults(result.data);
            } else {
                this.showError(result.error || 'Fehler bei der Suche');
            }
        } catch (error) {
            this.showError('Netzwerkfehler: ' + error.message);
        } finally {
            this.showLoadingState(false);
        }
    }

    showLoadingState(loading) {
        const button = document.querySelector('.unified-search-button');
        if (loading) {
            button.disabled = true;
            button.innerHTML = '🔄 Suche läuft...';
        } else {
            button.disabled = false;
            button.innerHTML = '🔍 Suche starten';
        }
    }

    displayResults(data) {
        const resultsArea = document.getElementById('results-area');
        resultsArea.style.display = 'block';
        resultsArea.innerHTML = `
            <h3>Suchergebnisse für "${data.mine_name}"</h3>
            <div class="results-content">
                ${this.formatResults(data)}
            </div>
        `;
    }

    formatResults(data) {
        // Format search results for display
        if (!data.structured_data || Object.keys(data.structured_data).length === 0) {
            return '<p>Keine strukturierten Daten gefunden.</p>';
        }

        let html = '<div class="structured-data">';
        
        for (const [field, value] of Object.entries(data.structured_data)) {
            if (value && value !== 'N/A') {
                html += `
                    <div class="data-field">
                        <strong>${field}:</strong> ${value}
                    </div>
                `;
            }
        }
        
        html += '</div>';

        // Add sources if available
        if (data.sources && data.sources.length > 0) {
            html += '<h4>Quellen:</h4><ul>';
            data.sources.forEach(source => {
                html += `<li><a href="${source.url}" target="_blank">${source.url}</a></li>`;
            });
            html += '</ul>';
        }

        return html;
    }

    showError(message) {
        const resultsArea = document.getElementById('results-area');
        resultsArea.style.display = 'block';
        resultsArea.innerHTML = `
            <div class="error-message">
                <h3>❌ Fehler</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize search forms when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.searchForms = new SearchForms();
});