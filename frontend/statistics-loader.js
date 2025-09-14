/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Statistics Loading Functions for MineSearch 2.0
 */

console.log('📊 [STATISTICS-LOADER] Loading Statistics Loader Module');

// Global configuration
if (typeof window.API_BASE_URL === 'undefined') {
    window.API_BASE_URL = window.location.origin;
}

/**
 * Lädt Statistiken und zeigt sie als Data-Cards an
 */
async function loadStatistics() {
    console.log('📊 [STATISTICS] Loading statistics...');
    
    try {
        // Get filter values
        const modelFilter = document.getElementById('stats_model')?.value || '';
        const daysFilter = document.getElementById('stats_days')?.value || '30';
        const viewFilter = document.getElementById('stats_view')?.value || 'models';
        
        console.log('📊 [STATISTICS] Filters:', { modelFilter, daysFilter, viewFilter });
        
        // Show loading state
        const container = document.getElementById('model-statistics-table-container');
        if (container) {
            container.innerHTML = `
                <div style="padding: 30px; text-align: center; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px;">
                    <h3>📊 Lade Modell-Statistiken...</h3>
                    <p style="color: #6c757d;">Bitte warten Sie einen Moment.</p>
                    <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid #3b82f6; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                </div>
            `;
        }
        
        // Build API URL
        let apiUrl = `${window.API_BASE_URL}/api/statistics/models`;
        const params = new URLSearchParams();
        
        if (daysFilter && daysFilter !== '0') {
            params.append('days_back', daysFilter);
        }
        if (modelFilter) {
            params.append('model_id', modelFilter);
        }
        if (viewFilter !== 'models') {
            params.append('view', viewFilter);
        }
        
        if (params.toString()) {
            apiUrl += `?${params.toString()}`;
        }
        
        console.log('📊 [STATISTICS] API URL:', apiUrl);
        
        // Try primary endpoint first, then fallback immediately
        console.log('📊 [STATISTICS] Trying results endpoint directly...');
        const altResponse = await fetch(`${window.API_BASE_URL}/api/results?exclude_exa=true&days_back=${daysFilter}&sort_by=mine_name`);
        
        if (altResponse.ok) {
            const altData = await altResponse.json();
            console.log('📊 [STATISTICS] Consolidated data received:', altData);
            
            if (altData.success && altData.data?.results) {
                // altData.data.results is the array of results
                const mockModelStats = generateMockModelStatsFromConsolidated(altData.data.results);
                displayModelStatistics(mockModelStats);
                return;
            } else {
                throw new Error('Keine Ergebnisse verfügbar - Structure: ' + JSON.stringify(Object.keys(altData.data || {})));
            }
        }
        
        // Fallback: Try original statistics endpoint
        console.log('⚠️ [STATISTICS] Consolidated failed, trying original endpoint...');
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error(`Beide Endpoints fehlgeschlagen. HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📊 [STATISTICS] API Response:', data);
        
        if (data.success && data.data) {
            displayModelStatistics(data.data);
            
            // Update summary statistics
            updateStatisticsSummary(data.data);
            
        } else {
            throw new Error(data.message || 'Unbekannter Fehler beim Laden der Statistiken');
        }
        
    } catch (error) {
        console.error('❌ [STATISTICS] Error loading statistics:', error);
        
        // Show error state
        const container = document.getElementById('model-statistics-table-container');
        if (container) {
            container.innerHTML = `
                <div style="padding: 30px; text-align: center; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px;">
                    <h3 style="color: #dc2626;">❌ Fehler beim Laden der Statistiken</h3>
                    <p style="color: #7f1d1d; margin-bottom: 20px;">${error.message}</p>
                    <button onclick="loadStatistics()" class="unified-search-button">
                        🔄 Erneut versuchen
                    </button>
                </div>
            `;
        }
    }
}

/**
 * Zeigt Modell-Statistiken als Data-Cards an
 */
function displayModelStatistics(statisticsData) {
    console.log('📊 [DISPLAY] Displaying model statistics:', statisticsData.length, 'models');
    
    const container = document.getElementById('model-statistics-table-container');
    if (!container) {
        console.error('❌ [DISPLAY] Container not found');
        return;
    }
    
    // Render Data-Card-Grid
    if (typeof window.renderDataCardGrid === 'function') {
        console.log('✅ [DISPLAY] Using renderDataCardGrid for model stats');
        window.renderDataCardGrid(statisticsData, container, 'model_stats');
    } else {
        console.error('❌ [DISPLAY] renderDataCardGrid function not available');
        // Fallback zu einfacher Darstellung
        container.innerHTML = `
            <div style="padding: 30px; text-align: center; background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px;">
                <h3>⚠️ Rendering-Fehler</h3>
                <p>Data-Card-System nicht verfügbar. ${statisticsData.length} Modell-Statistiken geladen, aber Anzeige fehlgeschlagen.</p>
            </div>
        `;
    }
}

/**
 * Generiert Mock-Model-Stats aus Ergebnissen
 */
function generateMockModelStatsFromConsolidated(results) {
    console.log('🔄 [MOCK] Generating mock model stats from results:', results.length);
    
    // Sammle alle verwendeten Modelle
    const modelStats = new Map();
    
    results.forEach(result => {
        console.log('🔍 [DEBUG] Processing result:', result.mine_name, 'with model:', result.model_used);
        
        // Direkt aus model_used extrahieren (einfacher Ansatz)
        const modelId = result.model_used || 'unknown';
        if (!modelStats.has(modelId)) {
            modelStats.set(modelId, {
                model_id: modelId,
                provider: modelId.includes(':') ? modelId.split(':')[0] : 'unknown',
                total_searches: 0,
                successful_searches: 0,
                success_rate: 0,
                overall_score: 0,
                is_active: true,
                sources_used: [],
                field_performance: {},
                recent_searches: [],
                aggregated_sources: {}
            });
        }
        
        const modelData = modelStats.get(modelId);
        modelData.total_searches += 1;
        modelData.successful_searches += result.structured_data ? 1 : 0;
        
        // Sammle Quellen aus various places
        if (result.sources) {
            modelData.sources_used.push(...result.sources);
        }
        
        // Legacy check: model_statistics field
        if (result.model_statistics) {
            Object.entries(result.model_statistics).forEach(([modelId, stats]) => {
                if (!modelStats.has(modelId)) {
                    modelStats.set(modelId, {
                        model_id: modelId,
                        provider: modelId.includes(':') ? modelId.split(':')[0] : 'unknown',
                        total_searches: 0,
                        successful_searches: 0,
                        success_rate: 0,
                        overall_score: 0,
                        is_active: true,
                        sources_used: [],
                        field_performance: {},
                        recent_searches: [],
                        aggregated_sources: {}
                    });
                }
                
                const modelData = modelStats.get(modelId);
                modelData.total_searches += stats.search_count || 0;
                modelData.successful_searches += stats.successful_extractions || 0;
                
                // Sammle Quellen
                if (stats.sources_used) {
                    modelData.sources_used.push(...stats.sources_used);
                }
            });
        }
        
        // Auch aus detailed_breakdown extrahieren
        if (result.detailed_breakdown) {
            Object.values(result.detailed_breakdown).forEach(fieldData => {
                if (fieldData.best_value && fieldData.best_value.model_used) {
                    const modelId = fieldData.best_value.model_used;
                    if (!modelStats.has(modelId)) {
                        modelStats.set(modelId, {
                            model_id: modelId,
                            provider: modelId.includes(':') ? modelId.split(':')[0] : 'unknown',
                            total_searches: 1,
                            successful_searches: 1,
                            success_rate: 1.0,
                            overall_score: 8.0,
                            is_active: true,
                            sources_used: [],
                            field_performance: {},
                            recent_searches: []
                        });
                    }
                    
                    const modelData = modelStats.get(modelId);
                    if (fieldData.best_value.sources) {
                        modelData.sources_used.push(...fieldData.best_value.sources);
                    }
                }
            });
        }
    });
    
    // Berechne finale Werte
    const finalStats = Array.from(modelStats.values()).map(model => {
        model.success_rate = model.total_searches > 0 
            ? model.successful_searches / model.total_searches 
            : 1.0;
        model.overall_score = model.success_rate * 10;
        
        // Duplikate aus sources_used entfernen
        model.sources_used = [...new Set(model.sources_used)];
        
        // Füge aggregated_sources hinzu für bessere Kompatibilität
        if (model.sources_used.length > 0) {
            model.aggregated_sources = {};
            model.sources_used.forEach(source => {
                if (typeof source === 'string') {
                    const domain = source.replace(/^https?:\/\//, '').split('/')[0];
                    model.aggregated_sources[domain] = {
                        count: 1,
                        sample_url: source
                    };
                } else {
                    console.warn('🔍 [DEBUG] Non-string source found:', typeof source, source);
                }
            });
        }
        
        return model;
    });
    
    console.log('✅ [MOCK] Generated', finalStats.length, 'mock model stats');
    return finalStats;
}

/**
 * Aktualisiert Statistiken-Zusammenfassung
 */
function updateStatisticsSummary(statisticsData) {
    const summaryContainer = document.getElementById('model-statistics-summary');
    if (!summaryContainer) return;
    
    const totalModels = statisticsData.length;
    const activeModels = statisticsData.filter(m => m.is_active).length;
    const avgSuccessRate = statisticsData.reduce((sum, m) => sum + (m.success_rate || 0), 0) / totalModels;
    
    summaryContainer.innerHTML = `
        <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 15px 0; color: #1e40af;">📈 Statistiken-Übersicht</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <span style="font-weight: bold; color: #374151;">🤖 Gesamt Modelle:</span>
                    <span style="color: #1f2937;">${totalModels}</span>
                </div>
                <div>
                    <span style="font-weight: bold; color: #374151;">✅ Aktive Modelle:</span>
                    <span style="color: #059669;">${activeModels}</span>
                </div>
                <div>
                    <span style="font-weight: bold; color: #374151;">📊 Ø Erfolgsrate:</span>
                    <span style="color: ${avgSuccessRate >= 0.8 ? '#059669' : avgSuccessRate >= 0.6 ? '#d97706' : '#dc2626'}">${(avgSuccessRate * 100).toFixed(1)}%</span>
                </div>
            </div>
        </div>
    `;
}

// Global exports
window.loadStatistics = loadStatistics;
window.displayModelStatistics = displayModelStatistics;
window.updateStatisticsSummary = updateStatisticsSummary;
window.generateMockModelStatsFromConsolidated = generateMockModelStatsFromConsolidated;

console.log('✅ [STATISTICS-LOADER] Statistics Loader Module loaded successfully');