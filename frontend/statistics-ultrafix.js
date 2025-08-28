/**
 * Author: rahn
 * Datum: 24.08.2025
 * Version: ULTRAFIX
 * Beschreibung: ULTRAFIX VERSION - Komplett neuer Filename für Cache-Umgehung
 */

console.log('🚀 [STATISTICS-ULTRAFIX] ULTRAFIX Statistics Module Loaded - NEW FILENAME!');

// Global configuration
if (typeof window.API_BASE_URL === 'undefined') {
    window.API_BASE_URL = 'http://localhost:8000';
}

/**
 * ULTRAFIX TRANSFORM FUNCTION - Komplett neue Implementierung
 */
function transformModelDataULTRAFIX(modelData) {
    console.log('🔄 [TRANSFORM-ULTRAFIX] ULTRAFIX Transform executing with', modelData.length, 'models');
    
    return modelData.map((model, index) => {
        console.log(`🔧 [TRANSFORM-ULTRAFIX] Processing ${index+1}/${modelData.length}: ${model.model_id}`);
        console.log(`   - Raw Data: searches=${model.total_searches}, completeness=${model.completeness_score}%, consistency=${model.consistency_score}%`);
        
        // Extrahiere Provider
        const provider = model.model_id.includes(':') ? model.model_id.split(':')[0] : 'unknown';
        
        // Berechne is_active
        const isActive = model.total_searches > 0;
        
        // Berechne Konfidenz
        const confidencePercentage = Math.min(model.total_searches * 10, 100);
        
        // ULTRAFIX: Generiere score_breakdown aus ECHTEN Daten
        const fieldQualityScore = Math.round((model.completeness_score / 100) * 10 * 10) / 10; // Round to 1 decimal
        const consistencyScore = Math.round((model.consistency_score / 100) * 10 * 10) / 10;
        const speedScore = Math.round(Math.max(0, 10 - (model.avg_response_time_ms / 10000)) * 10) / 10;
        const costScore = model.model_id.includes('free') ? 10 : 6;
        
        console.log(`   - Calculated Scores: field=${fieldQualityScore}, consistency=${consistencyScore}, speed=${speedScore}, cost=${costScore}`);
        
        const transformedModel = {
            ...model,
            provider: provider,
            is_active: isActive,
            confidence_percentage: confidencePercentage,
            score_breakdown: {
                fieldQuality: {
                    score: fieldQualityScore,
                    qualityLevel: model.completeness_score > 50 ? 'Hoch' : 'Niedrig',
                    details: { 
                        percentage: model.completeness_score.toFixed(1),
                        realValues: Math.round(model.avg_fields_filled || 0)
                    }
                },
                consistency: {
                    score: consistencyScore,
                    level: model.consistency_score > 80 ? 'Excellent' : 'Good',
                    details: { percentage: model.consistency_score.toFixed(1) }
                },
                speed: {
                    score: speedScore,
                    responseTime: model.avg_response_time_ms,
                    level: speedScore > 8 ? 'Fast' : 'Slow'
                },
                cost: {
                    score: costScore,
                    tier: model.model_id.includes('free') ? 'Free' : 'Paid'
                }
            }
        };
        
        console.log(`✅ [TRANSFORM-ULTRAFIX] ${model.model_id} TRANSFORMED SUCCESSFULLY!`);
        return transformedModel;
    });
}

/**
 * ULTRAFIX STATISTICS RENDERER - Direktes HTML ohne Abhängigkeiten
 */
function renderStatisticsULTRAFIX(transformedModels, container) {
    console.log('🎨 [RENDER-ULTRAFIX] Rendering statistics with ULTRAFIX direct HTML');
    
    let html = `
        <div style="margin-bottom: 24px; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; text-align: center;">
            <h2 style="margin: 0 0 8px 0; font-size: 1.5em;">🤖 KI-Modell-Statistiken</h2>
            <p style="margin: 0; opacity: 0.9;">${transformedModels.length} Modelle mit echten Performance-Daten</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 24px; padding: 0;">
    `;
    
    transformedModels.forEach((model, index) => {
        const performance = model.overall_score || 0;
        const fieldScore = model.score_breakdown.fieldQuality.score;
        const consistencyScore = model.score_breakdown.consistency.score;
        const speedScore = model.score_breakdown.speed.score;
        const costScore = model.score_breakdown.cost.score;
        
        console.log(`🎨 [RENDER-ULTRAFIX] Rendering card ${index+1}: ${model.model_id} with scores: field=${fieldScore}, consistency=${consistencyScore}`);
        
        html += `
            <div style="
                border: 2px solid #e2e8f0;
                border-radius: 16px; 
                padding: 20px; 
                background: white; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.07), 0 10px 15px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
                position: relative;
            " 
            onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.1)'" 
            onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.07), 0 10px 15px rgba(0,0,0,0.05)'">
                
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                    <div>
                        <h3 style="margin: 0 0 4px 0; color: #1a202c; font-size: 1.2em; font-weight: 700;">
                            🤖 ${model.model_id}
                        </h3>
                        <p style="margin: 0; color: #718096; font-size: 0.9em;">🏢 ${model.provider}</p>
                    </div>
                    <div style="
                        padding: 6px 12px; 
                        border-radius: 20px; 
                        font-size: 0.75em; 
                        font-weight: 600; 
                        background: ${model.is_active ? 'linear-gradient(135deg, #48bb78, #38a169)' : '#fed7d7'}; 
                        color: ${model.is_active ? 'white' : '#c53030'};
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    ">
                        ${model.is_active ? 'AKTIV' : 'INAKTIV'}
                    </div>
                </div>
                
                <!-- Main Performance Score -->
                <div style="
                    background: linear-gradient(135deg, #4299e1, #3182ce); 
                    color: white; 
                    padding: 16px; 
                    border-radius: 12px; 
                    margin-bottom: 16px; 
                    text-align: center;
                ">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 4px;">🎯 Performance-Score</div>
                    <div style="font-size: 2.2em; font-weight: 700; line-height: 1;">
                        ${performance.toFixed(1)}<span style="font-size: 0.6em; opacity: 0.8;">/10</span>
                    </div>
                    ${model.confidence_percentage ? `<div style="font-size: 0.8em; opacity: 0.8; margin-top: 4px;">Konfidenz: ${model.confidence_percentage}%</div>` : ''}
                </div>
                
                <!-- Score Breakdown -->
                <div style="
                    background: #f7fafc; 
                    padding: 16px; 
                    border-radius: 12px; 
                    margin-bottom: 16px;
                ">
                    <div style="font-weight: 600; margin-bottom: 12px; color: #2d3748; font-size: 0.9em;">📊 Score-Aufschlüsselung:</div>
                    
                    <!-- Feldqualität -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 8px; background: white; border-radius: 8px;">
                        <div>
                            <span style="color: #38a169; font-weight: 600;">🎯 Feldqualität</span>
                            <div style="font-size: 0.8em; color: #718096;">
                                ${model.score_breakdown.fieldQuality.qualityLevel} - ${model.score_breakdown.fieldQuality.details.percentage}% echte Werte
                            </div>
                        </div>
                        <div style="
                            font-weight: 700; 
                            color: #2d3748; 
                            font-size: 1.1em;
                            padding: 4px 8px;
                            background: linear-gradient(135deg, #48bb78, #38a169);
                            color: white;
                            border-radius: 6px;
                        ">
                            ${fieldScore.toFixed(1)}/10
                        </div>
                    </div>
                    
                    <!-- Konsistenz -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 8px; background: white; border-radius: 8px;">
                        <div>
                            <span style="color: #3182ce; font-weight: 600;">🔄 Konsistenz</span>
                            <div style="font-size: 0.8em; color: #718096;">
                                ${model.score_breakdown.consistency.details.percentage}% Übereinstimmung
                            </div>
                        </div>
                        <div style="
                            font-weight: 700; 
                            font-size: 1.1em;
                            padding: 4px 8px;
                            background: linear-gradient(135deg, #4299e1, #3182ce);
                            color: white;
                            border-radius: 6px;
                        ">
                            ${consistencyScore.toFixed(1)}/10
                        </div>
                    </div>
                    
                    <!-- Geschwindigkeit -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 8px; background: white; border-radius: 8px;">
                        <div>
                            <span style="color: #d69e2e; font-weight: 600;">⚡ Geschwindigkeit</span>
                            <div style="font-size: 0.8em; color: #718096;">
                                ${model.avg_response_time_ms.toFixed(0)}ms Antwortzeit
                            </div>
                        </div>
                        <div style="
                            font-weight: 700; 
                            font-size: 1.1em;
                            padding: 4px 8px;
                            background: linear-gradient(135deg, #ed8936, #d69e2e);
                            color: white;
                            border-radius: 6px;
                        ">
                            ${speedScore.toFixed(1)}/10
                        </div>
                    </div>
                    
                    <!-- Kosten -->
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: white; border-radius: 8px;">
                        <div>
                            <span style="color: #e53e3e; font-weight: 600;">💰 Kosten</span>
                            <div style="font-size: 0.8em; color: #718096;">
                                ${model.score_breakdown.cost.tier} Tier
                            </div>
                        </div>
                        <div style="
                            font-weight: 700; 
                            font-size: 1.1em;
                            padding: 4px 8px;
                            background: linear-gradient(135deg, #f56565, #e53e3e);
                            color: white;
                            border-radius: 6px;
                        ">
                            ${costScore.toFixed(1)}/10
                        </div>
                    </div>
                </div>
                
                <!-- Bottom Stats -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.9em;">
                    <div style="text-align: center; padding: 12px; background: #f0fff4; border-radius: 8px; border: 1px solid #9ae6b4;">
                        <div style="font-weight: 600; color: #38a169;">✅ Erfolgsrate</div>
                        <div style="font-size: 1.2em; font-weight: 700; color: #2f855a;">${(model.success_rate || 0).toFixed(1)}%</div>
                    </div>
                    <div style="text-align: center; padding: 12px; background: #eff6ff; border-radius: 8px; border: 1px solid #93c5fd;">
                        <div style="font-weight: 600; color: #3182ce;">🔍 Suchen</div>
                        <div style="font-size: 1.2em; font-weight: 700; color: #2c5282;">${model.total_searches || 0}</div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    container.innerHTML = html;
    console.log('✅ [RENDER-ULTRAFIX] ULTRAFIX statistics rendered successfully!');
}

/**
 * ULTRAFIX LOAD STATISTICS - Komplett neue Implementierung
 */
async function loadStatisticsULTRAFIX() {
    console.log('📊 [STATISTICS-ULTRAFIX] Loading ULTRAFIX statistics...');
    
    try {
        const container = document.getElementById('model-statistics-table-container');
        if (!container) {
            console.error('❌ [STATISTICS-ULTRAFIX] Container not found!');
            return;
        }
        
        // Loading state
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px;">
                <h3 style="margin: 0 0 12px 0;">🚀 ULTRAFIX: Lade Statistiken...</h3>
                <p style="margin: 0; opacity: 0.9;">Neue Cache-freie Version wird geladen</p>
                <div style="margin-top: 16px; display: inline-block; width: 24px; height: 24px; border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            </div>
        `;
        
        // API Call
        console.log('🌐 [STATISTICS-ULTRAFIX] Fetching API data...');
        const response = await fetch(`${window.API_BASE_URL}/api/results/stats?days_back=30&_ultrafix=${Date.now()}`);
        const data = await response.json();
        
        console.log('📊 [STATISTICS-ULTRAFIX] API Response received:', data.success);
        
        if (data.success) {
            const models = data.data?.models || [];
            console.log('📊 [STATISTICS-ULTRAFIX] Processing', models.length, 'models');
            
            if (models.length > 0) {
                const transformedModels = transformModelDataULTRAFIX(models);
                console.log('🔄 [STATISTICS-ULTRAFIX] Transform complete, rendering...');
                
                renderStatisticsULTRAFIX(transformedModels, container);
                console.log('✅ [STATISTICS-ULTRAFIX] ULTRAFIX rendering complete!');
            } else {
                container.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Keine Modelle gefunden</div>';
            }
        } else {
            throw new Error(data.message || 'API Error');
        }
        
    } catch (error) {
        console.error('❌ [STATISTICS-ULTRAFIX] Error:', error);
        const container = document.getElementById('model-statistics-table-container');
        if (container) {
            container.innerHTML = `
                <div style="padding: 20px; background: #fed7d7; border: 1px solid #fc8181; border-radius: 8px;">
                    <h3 style="color: #c53030;">❌ ULTRAFIX ERROR</h3>
                    <p style="color: #742a2a;">${error.message}</p>
                    <button onclick="loadStatisticsULTRAFIX()" style="
                        padding: 8px 16px; 
                        background: #e53e3e; 
                        color: white; 
                        border: none; 
                        border-radius: 6px; 
                        cursor: pointer;
                    ">🔄 ULTRAFIX Retry</button>
                </div>
            `;
        }
    }
}

// Replace loadStatistics AND loadModelStatistics with ULTRAFIX version
window.loadStatistics = loadStatisticsULTRAFIX;
window.loadModelStatistics = loadStatisticsULTRAFIX;  // KRITISCHER FIX: Tab-Autoloader verwendet loadModelStatistics
window.loadStatisticsULTRAFIX = loadStatisticsULTRAFIX;

/**
 * PHASE 2 FIX: Zeigt Model-Performance von Search-Ergebnissen im Statistik-Tab an
 */
function displaySearchModelPerformance(searchResults) {
    console.log('📊 [SEARCH-PERFORMANCE] Displaying search model performance in statistics tab');
    console.log('📊 [SEARCH-PERFORMANCE] Received results:', searchResults);
    
    if (!searchResults || !Array.isArray(searchResults) || searchResults.length === 0) {
        console.warn('⚠️ [SEARCH-PERFORMANCE] No search results to analyze');
        return;
    }
    
    // Container für Search-Performance (zusätzlich zu normalen Statistiken)
    const statsContainer = document.getElementById('statistics-table-container');
    if (!statsContainer) {
        console.error('❌ [SEARCH-PERFORMANCE] Statistics container not found');
        return;
    }
    
    // Erstelle Search-Performance Sektion OBERHALB der normalen Statistiken
    let searchPerformanceHtml = `
        <div id="search-performance-section" style="margin-bottom: 24px; padding: 20px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border-radius: 12px;">
            <h3 style="margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
                <span>🔍</span> Search-Session Performance
                <span style="font-size: 0.8em; opacity: 0.8;">(${searchResults.length} Modell${searchResults.length !== 1 ? 'e' : ''})</span>
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
    `;
    
    searchResults.forEach((result, index) => {
        const modelId = result.model_id || `Modell ${index + 1}`;
        const success = result.success || false;
        const data = result.data || {};
        const error = result.error || '';
        
        // Analysiere Felddaten wenn verfügbar
        let fieldStats = { total: 0, filled: 0, percentage: 0 };
        if (data && typeof data === 'object') {
            const fields = Object.keys(data).filter(key => !['mine_name', 'search_timestamp', 'model_used'].includes(key));
            fieldStats.total = fields.length;
            fieldStats.filled = fields.filter(key => {
                const value = data[key];
                return value && value !== 'Nichts gefunden' && value !== 'X' && value !== '';
            }).length;
            fieldStats.percentage = fieldStats.total > 0 ? Math.round((fieldStats.filled / fieldStats.total) * 100) : 0;
        }
        
        const statusColor = success ? '#10b981' : '#ef4444';
        const statusIcon = success ? '✅' : '❌';
        
        searchPerformanceHtml += `
            <div style="background: rgba(255,255,255,0.15); padding: 16px; border-radius: 8px; backdrop-filter: blur(10px);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <h4 style="margin: 0; font-size: 1em;">${statusIcon} ${modelId}</h4>
                    <span style="padding: 2px 8px; border-radius: 12px; font-size: 0.75em; background: ${statusColor}; color: white;">
                        ${success ? 'ERFOLG' : 'FEHLER'}
                    </span>
                </div>
                
                ${success ? `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.9em;">
                        <div>
                            <strong>📊 Felder gefüllt:</strong><br>
                            ${fieldStats.filled}/${fieldStats.total} (${fieldStats.percentage}%)
                        </div>
                        <div>
                            <strong>🎯 Vollständigkeit:</strong><br>
                            <div style="background: rgba(255,255,255,0.2); border-radius: 4px; height: 8px; margin-top: 4px;">
                                <div style="background: ${fieldStats.percentage > 70 ? '#10b981' : fieldStats.percentage > 40 ? '#f59e0b' : '#ef4444'}; height: 100%; border-radius: 4px; width: ${fieldStats.percentage}%; transition: width 0.3s ease;"></div>
                            </div>
                        </div>
                    </div>
                ` : `
                    <div style="font-size: 0.85em; color: #fecaca;">
                        <strong>❌ Fehler:</strong> ${error || 'Unbekannter Fehler'}
                    </div>
                `}
            </div>
        `;
    });
    
    searchPerformanceHtml += `
            </div>
            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 0.85em; opacity: 0.9;">
                💡 <strong>Tipp:</strong> Diese Daten stammen aus Ihrer letzten Suche und zeigen die Performance der verwendeten Modelle.
            </div>
        </div>
    `;
    
    // Füge Search-Performance am Anfang des Statistics-Containers hinzu
    const existingPerformance = document.getElementById('search-performance-section');
    if (existingPerformance) {
        existingPerformance.outerHTML = searchPerformanceHtml;
    } else {
        statsContainer.insertAdjacentHTML('afterbegin', searchPerformanceHtml);
    }
    
    console.log('✅ [SEARCH-PERFORMANCE] Search model performance displayed successfully');
}

// Export der neuen Funktion
window.displaySearchModelPerformance = displaySearchModelPerformance;

console.log('✅ [STATISTICS-ULTRAFIX] ULTRAFIX module ready - completely new implementation!');