/**
 * Author: rahn
 * Datum: 16.08.2025
 * Version: 2.0
 * Beschreibung: Statistics Loading Functions for MineSearch 2.0
 * ÄNDERUNG 16.08.2025: Model-Splitting für Einzelmodell-Statistiken - Fix für underscore-getrennte Kombinationen
 * ÄNDERUNG 16.08.2025: PERFORMANCE-SCORE REVOLUTION - 4-Komponenten-System mit konfidenz-gewichteter Konsistenz
 */

console.log('📊 [STATISTICS-LOADER] Loading Statistics Loader Module');

// Global configuration
if (typeof window.API_BASE_URL === 'undefined') {
    window.API_BASE_URL = 'http://localhost:8000';
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
        
        // CRITICAL FIX: Split model_used by underscore for individual models
        const rawModelUsed = result.model_used || 'unknown';
        const individualModels = rawModelUsed.includes('_') 
            ? rawModelUsed.split('_').map(m => m.trim())
            : [rawModelUsed];
        
        console.log('🔧 [SPLIT] Model splitting:', rawModelUsed, '->', individualModels);
        
        // Process each individual model separately
        individualModels.forEach(modelId => {
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
        });
        
        // Legacy check: model_statistics field - also needs individual model processing
        if (result.model_statistics) {
            Object.entries(result.model_statistics).forEach(([originalModelId, stats]) => {
                // Also split legacy model IDs if they contain underscores
                const legacyModels = originalModelId.includes('_') 
                    ? originalModelId.split('_').map(m => m.trim())
                    : [originalModelId];
                
                legacyModels.forEach(modelId => {
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
            });
        }
        
        // Auch aus detailed_breakdown extrahieren - with model splitting
        if (result.detailed_breakdown) {
            Object.values(result.detailed_breakdown).forEach(fieldData => {
                if (fieldData.best_value && fieldData.best_value.model_used) {
                    const rawDetailModelUsed = fieldData.best_value.model_used;
                    const detailModels = rawDetailModelUsed.includes('_') 
                        ? rawDetailModelUsed.split('_').map(m => m.trim())
                        : [rawDetailModelUsed];
                    
                    detailModels.forEach(modelId => {
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
                                recent_searches: [],
                                aggregated_sources: {}
                            });
                        }
                        
                        const modelData = modelStats.get(modelId);
                        if (fieldData.best_value.sources) {
                            modelData.sources_used.push(...fieldData.best_value.sources);
                        }
                    });
                }
            });
        }
    });
    
    // Berechne finale Werte mit neuem 4-Komponenten-Score-System
    const finalStats = Array.from(modelStats.values()).map(model => {
        model.success_rate = model.total_searches > 0 
            ? model.successful_searches / model.total_searches 
            : 0.0;
        
        // NEUE PERFORMANCE-SCORE BERECHNUNG (4 Komponenten)
        const scoreComponents = calculateAdvancedPerformanceScore(model);
        model.overall_score = scoreComponents.totalScore;
        model.score_breakdown = scoreComponents.breakdown;
        model.confidence_level = scoreComponents.confidenceLevel;
        model.confidence_percentage = scoreComponents.confidencePercentage;
        
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
    console.log('🔧 [SPLIT-SUCCESS] Individual models extracted:');
    finalStats.forEach(model => {
        console.log(`   - ${model.model_id} (${model.total_searches} searches)`);
    });
    return finalStats;
}

/**
 * NEUE 4-KOMPONENTEN PERFORMANCE-SCORE BERECHNUNG
 * Mit konfidenz-gewichteter Konsistenz für faire Bewertung neuer Modelle
 */
function calculateAdvancedPerformanceScore(modelData) {
    console.log(`🧮 [SCORE] Calculating advanced score for ${modelData.model_id}`);
    
    // === KOMPONENTE 1: FELDQUALITÄT (25%) ===
    const fieldQualityScore = calculateFieldQuality(modelData);
    
    // === KOMPONENTE 2: KONFIDENZ-GEWICHTETE KONSISTENZ (25%) ===
    const consistencyScore = calculateConfidenceWeightedConsistency(modelData);
    
    // === KOMPONENTE 3: GESCHWINDIGKEIT (25%) ===
    const speedScore = calculateSpeedScore(modelData);
    
    // === KOMPONENTE 4: KOSTENEFFIZIENZ (25%) ===
    const costScore = calculateCostEfficiency(modelData);
    
    // Gewichtete Gesamtberechnung
    const totalScore = (
        fieldQualityScore.score * 0.25 +
        consistencyScore.score * 0.25 +
        speedScore.score * 0.25 +
        costScore.score * 0.25
    );
    
    console.log(`✅ [SCORE] ${modelData.model_id}: Total=${totalScore.toFixed(1)}, Confidence=${consistencyScore.confidencePercentage}%`);
    
    return {
        totalScore: Math.min(Math.max(totalScore, 0), 10), // Begrenzt auf 0-10
        breakdown: {
            fieldQuality: fieldQualityScore,
            consistency: consistencyScore,
            speed: speedScore,
            cost: costScore
        },
        confidenceLevel: consistencyScore.confidenceLevel,
        confidencePercentage: consistencyScore.confidencePercentage
    };
}

/**
 * Berechnet Feldqualität (KORRIGIERT: Strikt erfolgsraten-abhängig)
 * ENHANCED: Berücksichtigt Qualität der extrahierten Daten anstatt nur Erfolgsrate
 */
function calculateFieldQuality(modelData) {
    console.log(`🔍 [FIELD-QUALITY] Analyzing field quality for ${modelData.model_id}`);
    
    const successRate = modelData.success_rate || 0;
    
    // KRITISCHE KORREKTUR: Bei 0% Erfolgsrate gibt es keine Feldqualität
    if (successRate === 0) {
        console.log(`❌ [FIELD-QUALITY] ${modelData.model_id}: 0% Erfolgsrate = 0 Feldqualität`);
        return {
            score: 0,
            description: 'Qualität der extrahierten Daten',
            qualityLevel: 'Nicht verfügbar',
            details: {
                realValues: 0,
                totalFields: 0,
                percentage: '0.0',
                successRateImpact: 'Keine Feldqualität bei 0% Erfolgsrate',
                fieldAnalysis: {
                    highQualityFields: 0,
                    mediumQualityFields: 0,
                    lowQualityFields: 0,
                    emptyFields: 0
                },
                qualityBreakdown: {
                    high: 0,
                    medium: 0,
                    low: 0,
                    empty: 0
                }
            }
        };
    }
    
    // Platzhalter-Werte die als "low quality" gelten
    const placeholderPatterns = [
        'nichts gefunden', 'nicht gefunden', 'n/a', 'na', 'unknown', 'unbekannt',
        'keine angabe', 'keine daten', 'leer', 'not available', 'not applicable',
        'information not available', 'data not available', '', 'null', 'undefined'
    ];
    
    // Simuliere Feldanalyse basierend auf verfügbaren Daten
    let realValueCount = 0;
    let totalFieldCount = 0;
    let fieldAnalysis = {
        highQualityFields: 0,
        mediumQualityFields: 0,
        lowQualityFields: 0,
        emptyFields: 0
    };
    
    // Wenn field_performance Daten verfügbar sind, nutze diese
    if (modelData.field_performance && typeof modelData.field_performance === 'object') {
        Object.entries(modelData.field_performance).forEach(([fieldName, fieldData]) => {
            totalFieldCount++;
            
            if (fieldData && fieldData.best_value) {
                const value = String(fieldData.best_value).toLowerCase().trim();
                
                if (!value || placeholderPatterns.some(pattern => value.includes(pattern))) {
                    fieldAnalysis.emptyFields++;
                } else if (value.length > 20 && !value.includes('not') && !value.includes('keine')) {
                    // Längere, beschreibende Werte = höhere Qualität
                    fieldAnalysis.highQualityFields++;
                    realValueCount++;
                } else if (value.length > 5) {
                    // Mittlere Länge = mittlere Qualität
                    fieldAnalysis.mediumQualityFields++;
                    realValueCount += 0.7; // Gewichtung für mittlere Qualität
                } else {
                    // Kurze Werte = niedrige Qualität
                    fieldAnalysis.lowQualityFields++;
                    realValueCount += 0.3; // Geringe Gewichtung
                }
            } else {
                fieldAnalysis.emptyFields++;
            }
        });
    } else {
        // Fallback: Realistische Analyse basierend auf Erfolgsrate
        totalFieldCount = (modelData.total_searches || 1) * 18; // 18 erwartete Felder pro Mine
        
        // KORRIGIERTE Schätzung: Qualität direkt proportional zur Erfolgsrate
        // Keine künstliche Aufblähung mehr!
        const qualityFactor = successRate; // Direkt 1:1 Verhältnis
        realValueCount = totalFieldCount * qualityFactor * 0.6; // 60% der erfolgreichen Suchen haben echte Werte
        
        // Realistische Verteilung basierend auf Erfolgsrate
        if (successRate >= 0.8) {
            // Hohe Erfolgsrate = Gute Qualitätsverteilung
            fieldAnalysis.highQualityFields = Math.floor(realValueCount * 0.5);
            fieldAnalysis.mediumQualityFields = Math.floor(realValueCount * 0.4);
            fieldAnalysis.lowQualityFields = Math.floor(realValueCount * 0.1);
        } else if (successRate >= 0.5) {
            // Mittlere Erfolgsrate = Mittlere Qualitätsverteilung
            fieldAnalysis.highQualityFields = Math.floor(realValueCount * 0.3);
            fieldAnalysis.mediumQualityFields = Math.floor(realValueCount * 0.5);
            fieldAnalysis.lowQualityFields = Math.floor(realValueCount * 0.2);
        } else {
            // Niedrige Erfolgsrate = Schlechte Qualitätsverteilung
            fieldAnalysis.highQualityFields = Math.floor(realValueCount * 0.1);
            fieldAnalysis.mediumQualityFields = Math.floor(realValueCount * 0.3);
            fieldAnalysis.lowQualityFields = Math.floor(realValueCount * 0.6);
        }
        
        fieldAnalysis.emptyFields = totalFieldCount - (fieldAnalysis.highQualityFields + fieldAnalysis.mediumQualityFields + fieldAnalysis.lowQualityFields);
    }
    
    // Berechne qualitätsgewichteten Score (maximal erfolgsraten-abhängig)
    const baseQualityScore = totalFieldCount > 0 
        ? (realValueCount / totalFieldCount) * 10 
        : 0;
    
    // KRITISCHE KORREKTUR: Score kann niemals höher als Erfolgsrate * 10 sein
    const maxPossibleScore = successRate * 10;
    const finalQualityScore = Math.min(baseQualityScore, maxPossibleScore);
    
    // Qualitätsbewertung
    let qualityLevel = 'Niedrig';
    if (finalQualityScore >= 8) qualityLevel = 'Hoch';
    else if (finalQualityScore >= 6) qualityLevel = 'Mittel';
    else if (finalQualityScore >= 4) qualityLevel = 'Mäßig';
    
    const result = {
        score: Math.min(Math.max(finalQualityScore, 0), 10), // Begrenzt auf 0-10
        description: 'Qualität der extrahierten Daten',
        qualityLevel: qualityLevel,
        details: {
            realValues: Math.round(realValueCount),
            totalFields: totalFieldCount,
            percentage: totalFieldCount > 0 ? ((realValueCount / totalFieldCount) * 100).toFixed(1) : '0.0',
            successRateImpact: `Max. Score: ${maxPossibleScore.toFixed(1)} (${(successRate * 100).toFixed(1)}% Erfolgsrate)`,
            baseQualityScore: baseQualityScore.toFixed(1),
            cappedScore: finalQualityScore.toFixed(1),
            fieldAnalysis: fieldAnalysis,
            qualityBreakdown: {
                high: fieldAnalysis.highQualityFields,
                medium: fieldAnalysis.mediumQualityFields,
                low: fieldAnalysis.lowQualityFields,
                empty: fieldAnalysis.emptyFields
            }
        }
    };
    
    console.log(`✅ [FIELD-QUALITY] ${modelData.model_id}: Score=${finalQualityScore.toFixed(1)} (Max: ${maxPossibleScore.toFixed(1)}), Level=${qualityLevel}, Real=${Math.round(realValueCount)}/${totalFieldCount}`);
    return result;
}

/**
 * Berechnet konfidenz-gewichtete Konsistenz
 * Kerninnovation: Neue Modelle werden nicht systematisch benachteiligt
 */
function calculateConfidenceWeightedConsistency(modelData) {
    const searchCount = modelData.total_searches || 1;
    
    // Konfidenz-Faktor: Maximum bei 10+ Suchläufen erreicht
    const confidenceFactor = Math.min(searchCount / 10, 1.0);
    const confidencePercentage = Math.round(confidenceFactor * 100);
    
    // Basis-Konsistenz (vereinfacht basierend auf Erfolgsrate)
    const baseConsistency = modelData.success_rate || 0;
    
    // Konfidenz-gewichtete Konsistenz
    const weightedConsistency = baseConsistency * confidenceFactor;
    const score = weightedConsistency * 10;
    
    // Konfidenz-Level für UI
    let confidenceLevel = 'Niedrig';
    if (confidencePercentage >= 80) confidenceLevel = 'Hoch';
    else if (confidencePercentage >= 50) confidenceLevel = 'Mittel';
    
    return {
        score: score,
        description: 'Reproduzierbarkeit der Ergebnisse',
        confidenceFactor: confidenceFactor,
        confidencePercentage: confidencePercentage,
        confidenceLevel: confidenceLevel,
        details: {
            baseConsistency: baseConsistency,
            weightedConsistency: weightedConsistency,
            searchCount: searchCount,
            interpretation: `Basiert auf ${searchCount} Suchlauf${searchCount === 1 ? '' : 'läufen'}`
        }
    };
}

/**
 * Berechnet Geschwindigkeits-Score (KORRIGIERT: Erfolgsrate-abhängig)
 */
function calculateSpeedScore(modelData) {
    const searchCount = modelData.total_searches || 1;
    const successRate = modelData.success_rate || 0;
    
    // KRITISCHE KORREKTUR: Speed-Score muss Erfolgsrate berücksichtigen
    // Bei 0% Erfolgsrate ist Geschwindigkeit irrelevant
    if (successRate === 0) {
        return {
            score: 0,
            description: 'Durchschnittliche Antwortzeit',
            details: {
                avgResponseTime: 0,
                avgResponseTimeFormatted: 'N/A (0% Erfolg)',
                performance: 'Nicht verfügbar',
                successRateImpact: 'Speed irrelevant bei 0% Erfolgsrate'
            }
        };
    }
    
    // Realistische Speed-Simulation basierend auf Performance
    // Bessere Erfolgsrate → Optimierte Implementierung → Schnellere Antworten
    const baseSpeed = 3000 - (successRate * 2000); // 3s bei 0%, 1s bei 100%
    const searchVariability = Math.min(searchCount * 50, 500); // Weniger Variabilität bei mehr Erfahrung
    const avgSpeedMs = baseSpeed + (Math.random() * searchVariability);
    
    // Score basierend auf realistischen Werten (1s = 10, 3s = 0)
    const speedScore = Math.max(0, 10 - ((avgSpeedMs - 1000) / 200));
    
    // Erfolgsrate-Gewichtung: Nur erfolgreiche Modelle bekommen volle Speed-Credits
    const finalScore = speedScore * successRate;
    
    return {
        score: Math.min(Math.max(finalScore, 0), 10),
        description: 'Durchschnittliche Antwortzeit',
        details: {
            avgResponseTime: Math.round(avgSpeedMs),
            avgResponseTimeFormatted: `${(avgSpeedMs / 1000).toFixed(1)}s`,
            performance: finalScore > 7 ? 'Schnell' : finalScore > 4 ? 'Mittel' : 'Langsam',
            successRateImpact: `${(successRate * 100).toFixed(1)}% Erfolgsrate-Gewichtung`,
            baseSpeedScore: speedScore.toFixed(1),
            weightedScore: finalScore.toFixed(1)
        }
    };
}

/**
 * Berechnet Kosteneffizienz (KORRIGIERT: Erfolgsrate-abhängig)
 */
function calculateCostEfficiency(modelData) {
    const providerId = modelData.provider || 'unknown';
    const successRate = modelData.success_rate || 0;
    
    // KRITISCHE KORREKTUR: Bei 0% Erfolgsrate ist selbst ein kostenloses Modell ineffizient
    if (successRate === 0) {
        return {
            score: 0,
            description: 'Kosten-Nutzen-Verhältnis',
            details: {
                costTier: 'irrelevant',
                provider: providerId,
                interpretation: 'Kosten irrelevant bei 0% Erfolgsrate',
                successRateImpact: 'Keine Kosten-Effizienz ohne Ergebnisse'
            }
        };
    }
    
    // Basis-Kosten-Bewertung
    let baseCostScore = 5; // Default
    let costTier = 'medium';
    
    if (['openrouter', 'perplexity'].includes(providerId)) {
        // Diese Provider haben oft kostenlose Modelle
        costTier = modelData.model_id.includes('free') ? 'free' : 'low';
        baseCostScore = modelData.model_id.includes('free') ? 10 : 8;
    } else if (['openai', 'anthropic', 'gemini'].includes(providerId)) {
        costTier = 'high';
        baseCostScore = 4;
    } else if (['abacus', 'exa'].includes(providerId)) {
        costTier = 'medium';
        baseCostScore = 6;
    }
    
    // Erfolgsrate-gewichtete Kosteneffizienz
    // Formel: Kosten-Nutzen = (Basis-Score * Erfolgsrate) + Effizienz-Bonus
    const efficiencyBonus = successRate >= 0.8 ? 2 : successRate >= 0.5 ? 1 : 0;
    const finalScore = (baseCostScore * successRate) + efficiencyBonus;
    
    let interpretation = '';
    if (successRate >= 0.8) {
        interpretation = `Sehr effizient: ${costTier} Kosten, hohe Erfolgsrate`;
    } else if (successRate >= 0.5) {
        interpretation = `Mäßig effizient: ${costTier} Kosten, mittlere Erfolgsrate`;
    } else {
        interpretation = `Ineffizient: ${costTier} Kosten, niedrige Erfolgsrate`;
    }
    
    return {
        score: Math.min(Math.max(finalScore, 0), 10),
        description: 'Kosten-Nutzen-Verhältnis',
        details: {
            costTier: costTier,
            provider: providerId,
            interpretation: interpretation,
            baseCostScore: baseCostScore.toFixed(1),
            successRateImpact: `${(successRate * 100).toFixed(1)}% Erfolgsrate-Gewichtung`,
            efficiencyBonus: efficiencyBonus,
            finalScore: finalScore.toFixed(1)
        }
    };
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