/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Chart & Visualization Functions
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (Phase 3 - Final Refactoring)
 * Chart Functions: Chart.js Integration, Statistical Visualizations, Performance Charts
 */

// ============================================
// CHART INSTANCES MANAGEMENT
// ============================================

/**
 * GLOBAL CHART INSTANCES: Verwaltet alle Chart-Instanzen für Cleanup
 */
window.MineSearchChartInstances = {
    successRateChart: null,
    consistencyChart: null,
    responseTimeChart: null,
    performanceRadarChart: null
};

// ============================================
// CHART LIFECYCLE MANAGEMENT
// ============================================

/**
 * DESTROY EXISTING CHARTS: Zerstört bestehende Charts vor Neuerstellung
 */
function destroyExistingCharts() {
    console.log('🔥 [CHARTS] Destroying existing charts to prevent canvas reuse error');
    
    Object.keys(window.MineSearchChartInstances).forEach(chartKey => {
        const chartInstance = window.MineSearchChartInstances[chartKey];
        if (chartInstance && typeof chartInstance.destroy === 'function') {
            console.log(`🔥 [CHARTS] Destroying chart: ${chartKey}`);
            chartInstance.destroy();
            window.MineSearchChartInstances[chartKey] = null;
        }
    });
}

/**
 * VALIDATE CHART.JS: Prüft ob Chart.js verfügbar ist
 */
function validateChartJS() {
    if (typeof Chart === 'undefined') {
        console.error('❌ [CHARTS] Chart.js not loaded - charts cannot be created');
        showNotification('Chart.js konnte nicht geladen werden', 'error');
        return false;
    }
    return true;
}

// ============================================
// MAIN CHART LOADING FUNCTION
// ============================================

/**
 * LOAD STATISTICS CHARTS: Hauptfunktion für Chart-Erstellung
 */
async function loadStatisticsCharts(statisticsData = null) {
    console.log('📊 [CHARTS] Loading statistics charts with real data...');
    
    if (!statisticsData) {
        console.warn('⚠️ [CHARTS] No statistics data provided for charts');
        return;
    }
    
    if (!validateChartJS()) {
        return;
    }
    
    // Cleanup bestehende Charts
    destroyExistingCharts();
    
    try {
        console.log('✅ [CHARTS] Chart.js loaded, creating all 4 charts');
        
        // Erstelle alle Chart-Typen
        await createSuccessRateChart(statisticsData);
        await createConsistencyChart(statisticsData);
        await createResponseTimeChart(statisticsData);
        await createPerformanceRadarChart(statisticsData);
        
        console.log('✅ [CHARTS] All charts created successfully');
        
    } catch (error) {
        console.error('❌ [CHARTS] Error creating charts:', error);
        showNotification('Fehler beim Erstellen der Charts', 'error');
    }
}

// ============================================
// INDIVIDUAL CHART CREATORS
// ============================================

/**
 * SUCCESS RATE CHART: Balkendiagramm für Modell-Erfolgsraten
 */
async function createSuccessRateChart(statisticsData) {
    console.log('📊 [CHARTS] Creating Success Rate Chart');
    
    const successRateCanvas = document.getElementById('successRateChart');
    if (!successRateCanvas) {
        console.warn('⚠️ [CHARTS] successRateChart canvas not found');
        return;
    }
    
    // Chart-Konfiguration
    window.MineSearchChartInstances.successRateChart = new Chart(successRateCanvas, {
        type: 'bar',
        data: {
            labels: statisticsData.map(stat => stat.model_display_name || stat.model_id),
            datasets: [{
                label: 'Erfolgsrate (%)',
                data: statisticsData.map(stat => (stat.success_rate * 100).toFixed(1)),
                backgroundColor: statisticsData.map(stat => 
                    stat.success_rate >= 0.8 ? '#059669' : 
                    stat.success_rate >= 0.6 ? '#d97706' : '#dc2626'
                ),
                borderColor: statisticsData.map(stat => 
                    stat.success_rate >= 0.8 ? '#047857' : 
                    stat.success_rate >= 0.6 ? '#b45309' : '#b91c1c'
                ),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { 
                y: { 
                    beginAtZero: true, 
                    max: 100,
                    title: {
                        display: true,
                        text: 'Erfolgsrate (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Modelle'
                    }
                }
            },
            plugins: { 
                title: { 
                    display: true, 
                    text: 'Modell-Erfolgsraten' 
                },
                legend: {
                    display: false
                }
            }
        }
    });
    
    console.log('✅ [CHARTS] Success Rate Chart created and tracked');
}

/**
 * CONSISTENCY CHART: Doughnut-Chart für Modell-Konsistenz
 */
async function createConsistencyChart(statisticsData) {
    console.log('📊 [CHARTS] Creating Consistency Chart');
    
    const consistencyCanvas = document.getElementById('consistencyChart');
    if (!consistencyCanvas) {
        console.warn('⚠️ [CHARTS] consistencyChart canvas not found');
        return;
    }
    
    // Chart-Konfiguration
    window.MineSearchChartInstances.consistencyChart = new Chart(consistencyCanvas, {
        type: 'doughnut',
        data: {
            labels: statisticsData.map(stat => stat.model_display_name || stat.model_id),
            datasets: [{
                label: 'Konsistenz (%)',
                data: statisticsData.map(stat => (stat.overall_consistency * 100).toFixed(1)),
                backgroundColor: [
                    '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', 
                    '#10b981', '#6366f1', '#f97316', '#ec4899',
                    '#06b6d4', '#84cc16', '#a855f7', '#f43f5e'
                ],
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                title: { 
                    display: true, 
                    text: 'Modell-Konsistenz' 
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
    
    console.log('✅ [CHARTS] Consistency Chart created and tracked');
}

/**
 * RESPONSE TIME CHART: Liniendiagramm für Response-Zeiten
 */
async function createResponseTimeChart(statisticsData) {
    console.log('📊 [CHARTS] Creating Response Time Chart');
    
    const responseTimeCanvas = document.getElementById('responseTimeChart');
    if (!responseTimeCanvas) {
        console.warn('⚠️ [CHARTS] responseTimeChart canvas not found');
        return;
    }
    
    // Chart-Konfiguration
    window.MineSearchChartInstances.responseTimeChart = new Chart(responseTimeCanvas, {
        type: 'line',
        data: {
            labels: statisticsData.map(stat => stat.model_display_name || stat.model_id),
            datasets: [{
                label: 'Response Zeit (ms)',
                data: statisticsData.map(stat => stat.avg_response_time_ms || 0),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { 
                y: { 
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Zeit (ms)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Modelle'
                    }
                }
            },
            plugins: { 
                title: { 
                    display: true, 
                    text: 'Durchschnittliche Response-Zeiten' 
                }
            }
        }
    });
    
    console.log('✅ [CHARTS] Response Time Chart created and tracked');
}

/**
 * PERFORMANCE RADAR CHART: Radar-Chart für Gesamtperformance
 */
async function createPerformanceRadarChart(statisticsData) {
    console.log('📊 [CHARTS] Creating Performance Radar Chart');
    
    const performanceRadarCanvas = document.getElementById('performanceRadarChart');
    if (!performanceRadarCanvas) {
        console.warn('⚠️ [CHARTS] performanceRadarChart canvas not found');
        return;
    }
    
    // Nimm nur die besten 5 Modelle für bessere Lesbarkeit
    const topModels = statisticsData
        .sort((a, b) => (b.success_rate || 0) - (a.success_rate || 0))
        .slice(0, 5);
    
    // Chart-Konfiguration
    window.MineSearchChartInstances.performanceRadarChart = new Chart(performanceRadarCanvas, {
        type: 'radar',
        data: {
            labels: ['Erfolgsrate', 'Konsistenz', 'Gefundene Felder', 'Geschwindigkeit', 'Gesamtperformance'],
            datasets: topModels.map((stat, index) => ({
                label: stat.model_display_name || stat.model_id,
                data: [
                    Math.max(0, Math.min((stat.success_rate || 0) * 100, 100)),
                    Math.max(0, Math.min((stat.overall_consistency || 0) * 100, 100)),
                    Math.max(0, Math.min(stat.avg_fields_found || 0, 19)), // Max 19 Felder
                    Math.max(0, Math.min(100 - Math.max(0, (stat.avg_response_time_ms || 0) / 50), 100)), // Speed max 100
                    Math.max(0, Math.min(((stat.success_rate || 0) + (stat.overall_consistency || 0)) / 2 * 100, 100))
                ],
                backgroundColor: `hsla(${index * 72}, 70%, 50%, 0.2)`,
                borderColor: `hsla(${index * 72}, 70%, 50%, 1)`,
                pointBackgroundColor: `hsla(${index * 72}, 70%, 50%, 1)`,
                pointBorderColor: '#ffffff',
                pointHoverBackgroundColor: '#ffffff',
                pointHoverBorderColor: `hsla(${index * 72}, 70%, 50%, 1)`
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                title: { 
                    display: true, 
                    text: 'Performance-Vergleich (Top 5 Modelle)' 
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
    
    console.log('✅ [CHARTS] Performance Radar Chart created and tracked');
}

// ============================================
// CHART HELPER FUNCTIONS
// ============================================

/**
 * GET CHART COLORS: Generiert Farben basierend auf Performance-Werten
 */
function getChartColors(values, type = 'performance') {
    return values.map(value => {
        switch (type) {
            case 'performance':
                if (value >= 80) return '#059669'; // Grün
                if (value >= 60) return '#d97706'; // Orange
                return '#dc2626'; // Rot
            
            case 'response_time':
                if (value <= 5000) return '#059669'; // Schnell - Grün
                if (value <= 15000) return '#d97706'; // Mittel - Orange
                return '#dc2626'; // Langsam - Rot
            
            default:
                return '#3b82f6'; // Standard Blau
        }
    });
}

/**
 * UPDATE CHART DATA: Aktualisiert Chart-Daten ohne Neuzeichnung
 */
function updateChartData(chartKey, newData) {
    const chartInstance = window.MineSearchChartInstances[chartKey];
    if (!chartInstance) {
        console.warn(`⚠️ [CHARTS] Chart ${chartKey} not found for update`);
        return;
    }
    
    try {
        chartInstance.data = newData;
        chartInstance.update();
        console.log(`✅ [CHARTS] Chart ${chartKey} updated successfully`);
    } catch (error) {
        console.error(`❌ [CHARTS] Error updating chart ${chartKey}:`, error);
    }
}

/**
 * RESIZE ALL CHARTS: Passt alle Charts an neue Container-Größen an
 */
function resizeAllCharts() {
    console.log('📐 [CHARTS] Resizing all charts');
    
    Object.keys(window.MineSearchChartInstances).forEach(chartKey => {
        const chartInstance = window.MineSearchChartInstances[chartKey];
        if (chartInstance && typeof chartInstance.resize === 'function') {
            chartInstance.resize();
        }
    });
}

/**
 * GET CHART STATUS: Gibt Status aller Charts zurück
 */
function getChartsStatus() {
    const status = {};
    
    Object.keys(window.MineSearchChartInstances).forEach(chartKey => {
        const chartInstance = window.MineSearchChartInstances[chartKey];
        status[chartKey] = {
            exists: chartInstance !== null,
            isDestroyed: chartInstance && chartInstance.isDestroyed,
            canvas: document.getElementById(chartKey.replace('Chart', 'Chart'))
        };
    });
    
    return status;
}

// ============================================
// CHART DATA PROCESSING
// ============================================

/**
 * PROCESS STATISTICS FOR CHARTS: Bereitet Statistik-Daten für Charts vor
 */
function processStatisticsForCharts(rawData) {
    if (!rawData || !Array.isArray(rawData)) {
        console.warn('⚠️ [CHARTS] Invalid statistics data provided');
        return [];
    }
    
    return rawData.map(stat => ({
        model_id: stat.model_id || 'Unknown',
        model_display_name: stat.model_display_name || stat.model_id || 'Unknown',
        success_rate: Math.max(0, Math.min(stat.success_rate || 0, 1)),
        overall_consistency: Math.max(0, Math.min(stat.overall_consistency || 0, 1)),
        avg_fields_found: Math.max(0, stat.avg_fields_found || 0),
        avg_response_time_ms: Math.max(0, stat.avg_response_time_ms || 0),
        total_tests: Math.max(0, stat.total_tests || 0)
    }));
}

/**
 * CALCULATE CHART METRICS: Berechnet Metriken für Chart-Anzeige
 */
function calculateChartMetrics(statisticsData) {
    if (!statisticsData || !Array.isArray(statisticsData)) {
        return null;
    }
    
    const metrics = {
        totalModels: statisticsData.length,
        avgSuccessRate: 0,
        avgConsistency: 0,
        avgResponseTime: 0,
        bestModel: null,
        worstModel: null
    };
    
    if (statisticsData.length > 0) {
        metrics.avgSuccessRate = statisticsData.reduce((sum, stat) => sum + (stat.success_rate || 0), 0) / statisticsData.length;
        metrics.avgConsistency = statisticsData.reduce((sum, stat) => sum + (stat.overall_consistency || 0), 0) / statisticsData.length;
        metrics.avgResponseTime = statisticsData.reduce((sum, stat) => sum + (stat.avg_response_time_ms || 0), 0) / statisticsData.length;
        
        // Bestes und schlechtestes Modell
        const sortedByPerformance = [...statisticsData].sort((a, b) => (b.success_rate || 0) - (a.success_rate || 0));
        metrics.bestModel = sortedByPerformance[0];
        metrics.worstModel = sortedByPerformance[sortedByPerformance.length - 1];
    }
    
    return metrics;
}

// ============================================
// WINDOW RESIZE HANDLER
// ============================================

// Auto-resize bei Fenster-Größenänderung
window.addEventListener('resize', debounce(resizeAllCharts, 250));

// Debounce-Helper für Performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export chart functions to global scope
window.loadStatisticsCharts = loadStatisticsCharts;
window.destroyExistingCharts = destroyExistingCharts;
window.createSuccessRateChart = createSuccessRateChart;
window.createConsistencyChart = createConsistencyChart;
window.createResponseTimeChart = createResponseTimeChart;
window.createPerformanceRadarChart = createPerformanceRadarChart;
window.updateChartData = updateChartData;
window.resizeAllCharts = resizeAllCharts;
window.getChartsStatus = getChartsStatus;
window.processStatisticsForCharts = processStatisticsForCharts;
window.calculateChartMetrics = calculateChartMetrics;

console.log('📊 MineSearch 2.0 - Chart Functions loaded');