/*
Author: rahn
Datum: 29.07.2025
Version: 2.0
Beschreibung: Results Display Module für MineSearch v2 Frontend - Vollständige Implementierung
*/

// Results Display Module für MineSearch v2
window.MineSearchResultsDisplay = {
    initialized: true,
    version: '2.0',
    
    // Hauptfunktion für Einzel-Suchergebnisse
    displayResults: function(data) {
        const resultsDiv = document.getElementById('results');
        
        if (data.success && data.data) {
            this.safeSetHTML(resultsDiv, `
                <div style="padding: 20px; background: #f0fdf4; border-radius: 8px; border: 1px solid #10b981;">
                    <h3>✅ Suchergebnis für: ${this.sanitizeHTML(data.data.mine_name)}</h3>
                    <div style="margin-top: 15px;">
                        <pre style="background: #f9f9f9; padding: 10px; border-radius: 4px; white-space: pre-wrap;">${this.sanitizeHTML(JSON.stringify(data.data, null, 2))}</pre>
                    </div>
                </div>
            `);
        } else {
            this.showError(resultsDiv, 'Keine Ergebnisse gefunden', data.message);
        }
    },

    // Konsolidierte Ergebnisse anzeigen
    displayConsolidatedResults: function(results, sortBy, order) {
        const container = document.getElementById('consolidated-table-container');
        if (!container) return;
        
        if (!results || results.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #666;">
                    <h3>🔍 Keine konsolidierten Ergebnisse gefunden</h3>
                    <p>Es sind noch keine Suchergebnisse für die Konsolidierung verfügbar.</p>
                </div>
            `;
            return;
        }

        // Tabelle erstellen
        const tableHTML = this.buildConsolidatedTable(results, sortBy, order);
        container.innerHTML = tableHTML;
        
        // Event-Listener für Sortierung hinzufügen
        this.attachSortingListeners(container);
        
        // Event-Listener für Details-Modals hinzufügen
        this.attachDetailListeners(container);
    },

    // Standard Ergebnistabelle anzeigen
    displayResultsTable: function(results, sortBy, order) {
        const container = document.getElementById('results-table-container');
        if (!container) return;
        
        if (!results || results.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #666;">
                    <p>Keine Ergebnisse gefunden</p>
                    <small>Führe eine Suche aus um Ergebnisse zu sehen</small>
                </div>`;
            return;
        }

        // Standard Tabelle erstellen
        const tableHTML = this.buildResultsTable(results, sortBy, order);
        container.innerHTML = tableHTML;
        
        // Event-Listener hinzufügen
        this.attachSortingListeners(container);
    },

    // Konsolidierte Tabelle erstellen - USER REQUIREMENTS 30.07.2025
    buildConsolidatedTable: function(results, sortBy, order) {
        // KORREKTUR: Verwende exakt die gleiche Reihenfolge wie Backend FIELD_ORDER
        const columnOrder = [
            { key: 'mine_name', label: '🏔️ Mine', sortable: true },
            { key: 'country', label: '🌍 Land', sortable: true },
            { key: 'region', label: '📍 Region', sortable: true },
            { key: 'overall_confidence', label: '🎯 Zuverlässigkeit', sortable: true },
            { key: 'model_count', label: '🤖 Modelle', sortable: true },
            { key: 'last_updated', label: '📅 Letzte Aktualisierung', sortable: true },
            { key: 'Betreiber', label: '🏢 Betreiber', sortable: true },
            { key: 'Eigentümer', label: '👤 Eigentümer', sortable: true },
            { key: 'Rohstoffe', label: '⛏️ Rohstoffe', sortable: true },
            { key: 'Minentyp', label: '🏗️ Minentyp', sortable: true },
            { key: 'Aktivitätsstatus', label: '🔄 Status', sortable: true },
            { key: 'Produktionsstart', label: '📅 Produktionsstart', sortable: true },
            { key: 'Produktionsende', label: '📅 Produktionsende', sortable: true },
            { key: 'Fördermenge/Jahr', label: '📊 Fördermenge/Jahr', sortable: true },
            { key: 'Minenfläche in qkm', label: '📐 Fläche (qkm)', sortable: true },
            { key: 'x-Koordinate', label: '🌐 x-Koordinate', sortable: true },
            { key: 'y-Koordinate', label: '🌐 y-Koordinate', sortable: true },
            { key: 'Restaurationskosten', label: '💰 Restaurationskosten', sortable: true },
            { key: 'Kostenjahr', label: '📅 Kostenjahr', sortable: true },
            { key: 'Dokumentenjahr', label: '📅 Dokumentenjahr', sortable: true },
            { key: 'Quellenangaben', label: '📚 Quellen', sortable: true },
            { key: 'details', label: '📋 Details', sortable: false }
        ];
        
        // Header-Zeile erstellen
        let headerHTML = '<div class="table-header-row">';
        columnOrder.forEach(col => {
            const sortClass = col.sortable ? 'sortable' : '';
            const sortAttr = col.sortable ? `data-sort="${col.key}"` : '';
            const sortIcon = col.sortable ? this.getSortIcon(col.key, sortBy, order) : '';
            headerHTML += `<div class="table-cell ${sortClass}" ${sortAttr}>${col.label} ${sortIcon}</div>`;
        });
        headerHTML += '</div>';

        // Datenzeilen - USER REQUIREMENTS 30.07.2025
        let rowsHTML = '';
        results.forEach((result, index) => {
            const confidenceColor = this.getConfidenceColor(result.overall_confidence);
            const lastUpdated = result.last_updated ? new Date(result.last_updated).toLocaleDateString('de-DE') : 'N/A';
            
            rowsHTML += `<div class="table-row ${index % 2 === 0 ? 'even' : 'odd'}">`;
            
            // Füge alle Spalten entsprechend columnOrder hinzu
            columnOrder.forEach(col => {
                let cellContent = '';
                
                if (col.key === 'mine_name') {
                    cellContent = `<strong>${this.sanitizeHTML(result.mine_name)}</strong>`;
                } else if (col.key === 'country') {
                    cellContent = this.sanitizeHTML(result.country || 'N/A');
                } else if (col.key === 'region') {
                    cellContent = this.sanitizeHTML(result.region || 'N/A');
                } else if (col.key === 'overall_confidence') {
                    cellContent = `<span style="color: ${confidenceColor}; font-weight: bold;">${result.overall_confidence}%</span>`;
                } else if (col.key === 'model_count') {
                    cellContent = result.model_count;
                } else if (col.key === 'last_updated') {
                    cellContent = lastUpdated;
                } else if (col.key === 'details') {
                    cellContent = `<button class="details-btn" data-mine="${this.sanitizeHTML(result.mine_name)}" 
                                    data-country="${this.sanitizeHTML(result.country || '')}">📋 Details</button>`;
                } else {
                    // Alle anderen Felder aus best_values
                    const value = result.best_values?.[col.key] || 'N/A';
                    cellContent = this.sanitizeHTML(value);
                }
                
                rowsHTML += `<div class="table-cell">${cellContent}</div>`;
            });
            
            rowsHTML += '</div>';
        });

        return `
            <div class="consolidated-table">
                <div class="table-container">
                    ${headerHTML}
                    ${rowsHTML}
                </div>
            </div>
        `;
    },

    // Standard Ergebnistabelle erstellen - USER REQUIREMENTS 30.07.2025
    buildResultsTable: function(results, sortBy, order) {
        // Verwende die gleiche Spaltenstruktur wie konsolidierte Tabelle aber mit Rohdaten
        const columnOrder = [
            { key: 'mine_name', label: '🏔️ Mine', sortable: true },
            { key: 'country', label: '🌍 Land', sortable: true },
            { key: 'region', label: '📍 Region', sortable: true },
            { key: 'model_used', label: '🤖 Modell', sortable: true },
            { key: 'success', label: '✅ Erfolg', sortable: true },
            { key: 'fields_found', label: '📊 Felder gefunden', sortable: true },
            { key: 'search_timestamp', label: '📅 Zeitstempel', sortable: true }
        ];
        
        // Header erstellen
        let headerHTML = '<div class="table-header-row">';
        columnOrder.forEach(col => {
            const sortClass = col.sortable ? 'sortable' : '';
            const sortAttr = col.sortable ? `data-sort="${col.key}"` : '';
            const sortIcon = col.sortable ? this.getSortIcon(col.key, sortBy, order) : '';
            headerHTML += `<div class="table-cell ${sortClass}" ${sortAttr}>${col.label} ${sortIcon}</div>`;
        });
        headerHTML += '</div>';
        
        // Datenzeilen erstellen
        let rowsHTML = '';
        results.forEach((result, index) => {
            const successIcon = result.success ? '✅' : '❌';
            const fieldsFound = result.structured_data ? 
                Object.values(result.structured_data).filter(v => v && String(v).trim() && String(v).trim().toUpperCase() !== 'X').length : 0;
            
            rowsHTML += `<div class="table-row ${index % 2 === 0 ? 'even' : 'odd'}">`;
            
            columnOrder.forEach(col => {
                let cellContent = '';
                
                if (col.key === 'mine_name') {
                    cellContent = this.sanitizeHTML(result.mine_name || 'N/A');
                } else if (col.key === 'country') {
                    cellContent = this.sanitizeHTML(result.country || 'N/A');
                } else if (col.key === 'region') {
                    cellContent = this.sanitizeHTML(result.region || 'N/A');
                } else if (col.key === 'model_used') {
                    cellContent = this.sanitizeHTML(result.model_used || 'N/A');
                } else if (col.key === 'success') {
                    cellContent = successIcon;
                } else if (col.key === 'fields_found') {
                    cellContent = fieldsFound;
                } else if (col.key === 'search_timestamp') {
                    cellContent = result.search_timestamp ? new Date(result.search_timestamp).toLocaleString('de-DE') : 'N/A';
                }
                
                rowsHTML += `<div class="table-cell">${cellContent}</div>`;
            });
            
            rowsHTML += '</div>';
        });

        return `
            <div class="results-table">
                <div class="table-container">
                    ${headerHTML}
                    ${rowsHTML}
                </div>
            </div>
        `;
    },

    // Sortier-Icon ermitteln
    getSortIcon: function(column, sortBy, order) {
        if (sortBy === column) {
            return order === 'asc' ? '▲' : '▼';
        }
        return '↕️';
    },

    // Confidence-Farbe ermitteln
    getConfidenceColor: function(confidence) {
        if (confidence >= 70) return '#10b981'; // Grün
        if (confidence >= 50) return '#f59e0b'; // Orange
        return '#ef4444'; // Rot
    },

    // Event-Listener für Sortierung
    attachSortingListeners: function(container) {
        const sortableHeaders = container.querySelectorAll('.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', (e) => {
                const sortBy = e.target.dataset.sort;
                const currentOrder = new URLSearchParams(window.location.search).get('order') || 'asc';
                const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
                
                // Neulade mit neuer Sortierung
                if (typeof loadConsolidatedResults === 'function') {
                    loadConsolidatedResults(sortBy, newOrder);
                } else if (typeof loadResults === 'function') {
                    loadResults(sortBy, newOrder);
                }
            });
        });
    },

    // Event-Listener für Details-Buttons
    attachDetailListeners: function(container) {
        const detailButtons = container.querySelectorAll('.details-btn');
        detailButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const mineName = e.target.dataset.mine;
                const country = e.target.dataset.country;
                this.showMineDetails(mineName, country);
            });
        });
    },

    // Mine-Details Modal anzeigen
    showMineDetails: function(mineName, country) {
        // Modal erstellen oder öffnen
        const modal = document.getElementById('mine-details-modal') || this.createDetailsModal();
        
        // Loading-State
        const modalContent = modal.querySelector('.modal-content');
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Details für: ${this.sanitizeHTML(mineName)}</h3>
                <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.style.display='none'">×</button>
            </div>
            <div class="modal-body">
                <div class="loading-spinner">Lade Details...</div>
            </div>
        `;
        
        modal.style.display = 'block';
        
        // Details von API laden
        this.loadMineDetails(mineName, country, modalContent);
    },

    // Details-Modal erstellen
    createDetailsModal: function() {
        const modal = document.createElement('div');
        modal.id = 'mine-details-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-background">
                <div class="modal-content">
                    <!-- Content wird dynamisch geladen -->
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        return modal;
    },

    // Mine-Details von API laden
    loadMineDetails: async function(mineName, country, modalContent) {
        try {
            const params = new URLSearchParams();
            if (country) params.append('country', country);
            
            const response = await fetch(`/api/results/consolidated/${encodeURIComponent(mineName)}/details?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderMineDetails(data, modalContent);
            } else {
                throw new Error(data.message || 'Fehler beim Laden der Details');
            }
        } catch (error) {
            modalContent.querySelector('.modal-body').innerHTML = `
                <div style="color: #ef4444; text-align: center; padding: 20px;">
                    <p>❌ Fehler beim Laden der Details</p>
                    <small>${this.sanitizeHTML(error.message)}</small>
                </div>
            `;
        }
    },

    // Mine-Details rendern
    renderMineDetails: function(data, modalContent) {
        const modalBody = modalContent.querySelector('.modal-body');
        
        let detailsHTML = `
            <div class="mine-details">
                <div class="details-summary">
                    <h4>📊 Übersicht</h4>
                    <p><strong>Gesamte Suchen:</strong> ${data.data.total_searches}</p>
                    <p><strong>Verschiedene Modelle:</strong> ${data.data.unique_models}</p>
                    <p><strong>Zeitraum:</strong> ${data.data.date_range.earliest} bis ${data.data.date_range.latest}</p>
                </div>
                
                <div class="model-details">
                    <h4>🤖 Modell-spezifische Ergebnisse</h4>
        `;
        
        data.data.model_details.forEach(model => {
            const qualityColor = this.getConfidenceColor(model.data_quality_percentage);
            
            detailsHTML += `
                <div class="model-detail-card">
                    <div class="model-header">
                        <strong>${this.sanitizeHTML(model.model_display_name)}</strong>
                        <span style="color: ${qualityColor};">${model.data_quality_percentage}% Datenqualität</span>
                    </div>
                    <div class="model-stats">
                        <span>✅ ${model.filled_fields} Felder</span>
                        <span>🔗 ${model.sources_count} Quellen</span>
                        <span>⏱️ ${model.search_duration || 'N/A'}s</span>
                    </div>
                </div>
            `;
        });
        
        detailsHTML += `
                </div>
            </div>
        `;
        
        modalBody.innerHTML = detailsHTML;
    },

    // Hilfsfunktion: HTML sanitisieren
    sanitizeHTML: function(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    },

    // Hilfsfunktion: Sicheres HTML setzen
    safeSetHTML: function(element, html) {
        if (element) {
            element.innerHTML = html;
        }
    },

    // Hilfsfunktion: Fehler anzeigen
    showError: function(container, title, message) {
        this.safeSetHTML(container, `
            <div style="padding: 20px; background: #fef2f2; border-radius: 8px; border: 1px solid #ef4444; color: #dc2626;">
                <h3>❌ ${this.sanitizeHTML(title)}</h3>
                ${message ? `<p>${this.sanitizeHTML(message)}</p>` : ''}
            </div>
        `);
    }
};

// Legacy-Funktionen für Kompatibilität
function displayResults(data) {
    return window.MineSearchResultsDisplay.displayResults(data);
}

function displayConsolidatedResults(results, sortBy, order) {
    return window.MineSearchResultsDisplay.displayConsolidatedResults(results, sortBy, order);
}

function displayResultsTable(results, sortBy, order) {
    return window.MineSearchResultsDisplay.displayResultsTable(results, sortBy, order);
}

console.log('✅ MineSearch Results Display Module v2.0 geladen');