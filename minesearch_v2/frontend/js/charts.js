/*
Author: rahn
Datum: 12.07.2025
Version: 1.0
Beschreibung: Charts Module für MineSearch v2 Frontend (Chart.js Integration)
*/

// Chart.js Integration für MineSearch v2
console.log('Charts Module geladen');

// Chart Utilities und Konfiguration
window.MineSearchCharts = {
    initialized: true,
    version: '1.0',
    
    // Standard Chart.js Konfiguration für MineSearch
    defaultConfig: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: 'MineSearch Statistiken'
            }
        }
    },
    
    // Erstelle Chart für Statistiken
    createChart: function(canvasId, type, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Chart canvas mit ID '${canvasId}' nicht gefunden`);
            return null;
        }
        
        const config = {
            type: type,
            data: data,
            options: { ...this.defaultConfig, ...options }
        };
        
        return new Chart(canvas, config);
    }
};

// TODO: Extrahiere Chart-Funktionalität aus index.html
// Für jetzt: Verwende index.html als Hauptversion