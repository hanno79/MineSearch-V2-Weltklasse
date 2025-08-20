/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Interactive Model Comparison Engine
 * 
 * PHASE 4: Interactive Comparison Views Revolution
 * Intelligente Multi-Model-Vergleiche mit Consensus-Detection
 */

// ============================================
// COMPARISON ENGINE CORE
// ============================================

/**
 * HAUPTKLASSE: ComparisonEngine für intelligente Model-Vergleiche
 */
class ComparisonEngine {
    constructor() {
        this.activeComparisons = new Map();
        this.consensusThreshold = 0.7; // 70% Übereinstimmung für Consensus
        this.fieldWeights = this.initializeFieldWeights();
        
        console.log('🔬 [COMPARISON] ComparisonEngine initialisiert');
    }
    
    /**
     * FIELD WEIGHTS: Definiert Wichtigkeit verschiedener Mining-Felder
     */
    initializeFieldWeights() {
        return {
            // Kritische Identifikationsfelder
            'Name': 1.0,
            'Country': 1.0,
            'Region': 0.9,
            
            // Finanzielle Schlüsselfelder  
            'Restaurationskosten': 0.95,
            'Fördermenge/Jahr': 0.9,
            'Produktionsstart': 0.8,
            
            // Technische Daten
            'Minentyp (Untertage/ Open-Pit/ usw.)': 0.85,
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 0.85,
            'Aktivitätsstatus': 0.8,
            
            // Geografische Daten
            'x-Koordinate': 0.7,
            'y-Koordinate': 0.7,
            'Fläche der Mine in qkm': 0.7,
            
            // Eigentümerschaft
            'Eigentümer': 0.75,
            'Betreiber': 0.7,
            
            // Metadaten
            'Jahr der Aufnahme der Kosten': 0.6,
            'Jahr der Erstellung des Dokumentes': 0.6,
            'Quellenangaben': 0.8
        };
    }
    
    /**
     * MAIN COMPARISON: Startet intelligenten Multi-Model-Vergleich
     */
    async generateComparison(multiModelResults, comparisonId = null) {
        console.log(`🔬 [COMPARISON] Starte Vergleich für ${multiModelResults.length} Modelle`);
        
        if (multiModelResults.length < 2) {
            console.warn('⚠️ [COMPARISON] Mindestens 2 Modelle für Vergleich erforderlich');
            return this.generateSingleModelView(multiModelResults[0]);
        }
        
        const compId = comparisonId || `comp_${Date.now()}`;
        
        // Analysiere alle Modell-Ergebnisse
        const analysis = this.analyzeModelResults(multiModelResults);
        
        // Erkenne Consensus und Discrepancies
        const consensus = this.detectConsensus(analysis);
        const discrepancies = this.detectDiscrepancies(analysis);
        
        // Berechne Vertrauenswerte
        const confidence = this.calculateOverallConfidence(analysis, consensus);
        
        // Erstelle Comparison Object
        const comparison = {
            id: compId,
            timestamp: new Date().toISOString(),
            models: multiModelResults.map(r => r.model_id),
            analysis,
            consensus,
            discrepancies,
            confidence,
            metadata: {
                totalFields: Object.keys(this.fieldWeights).length,
                consensusFields: Object.keys(consensus.fields).length,
                discrepancyCount: discrepancies.length,
                overallQuality: this.calculateQualityScore(analysis)
            }
        };
        
        // Speichere Vergleich
        this.activeComparisons.set(compId, comparison);
        
        console.log(`✅ [COMPARISON] Vergleich ${compId} erstellt: ${comparison.metadata.consensusFields}/${comparison.metadata.totalFields} Consensus-Felder`);
        
        return comparison;
    }
    
    /**
     * MODEL ANALYSIS: Analysiert strukturierte Daten aller Modelle
     */
    analyzeModelResults(results) {
        const analysis = {
            fieldAnalysis: {},
            modelPerformance: {},
            dataQuality: {}
        };
        
        // Sammle alle verfügbaren Felder
        const allFields = new Set();
        results.forEach(result => {
            if (result.data && result.data.structured_data) {
                Object.keys(result.data.structured_data).forEach(field => {
                    if (field !== '_source_mapping') {
                        allFields.add(field);
                    }
                });
            }
        });
        
        // Analysiere jedes Feld über alle Modelle
        allFields.forEach(fieldName => {
            analysis.fieldAnalysis[fieldName] = this.analyzeField(fieldName, results);
        });
        
        // Analysiere Performance jedes Modells
        results.forEach(result => {
            analysis.modelPerformance[result.model_id] = this.analyzeModelPerformance(result);
            analysis.dataQuality[result.model_id] = result.data?.quality_metrics || {};
        });
        
        return analysis;
    }
    
    /**
     * FIELD ANALYSIS: Analysiert ein spezifisches Feld über alle Modelle
     */
    analyzeField(fieldName, results) {
        const fieldData = {
            values: [],
            agreements: [],
            discrepancies: [],
            confidence: 0,
            weight: this.fieldWeights[fieldName] || 0.5
        };
        
        results.forEach(result => {
            if (result.data && result.data.structured_data) {
                const value = result.data.structured_data[fieldName];
                // KORREKTUR: Verwende robuste isEmptyValue Funktion statt nur 'X' und 'N/A'
                if (value && !this.isEmptyValue(value)) {
                    fieldData.values.push({
                        model: result.model_id,
                        value: value,
                        confidence: result.confidence || 0.5,
                        source: result.data.sources || []
                    });
                }
            }
        });
        
        // Erkenne Übereinstimmungen und Diskrepanzen
        this.detectFieldAgreements(fieldData);
        
        return fieldData;
    }
    
    /**
     * FIELD AGREEMENTS: Erkennt Übereinstimmungen in Felddaten
     */
    detectFieldAgreements(fieldData) {
        const valueGroups = {};
        
        // Gruppiere ähnliche Werte
        fieldData.values.forEach(entry => {
            const normalizedValue = this.normalizeValue(entry.value);
            
            if (!valueGroups[normalizedValue]) {
                valueGroups[normalizedValue] = [];
            }
            valueGroups[normalizedValue].push(entry);
        });
        
        // Finde Agreements (mehrere Modelle mit gleichem Wert)
        Object.entries(valueGroups).forEach(([normalizedValue, entries]) => {
            if (entries.length >= 2) {
                fieldData.agreements.push({
                    value: normalizedValue,
                    models: entries.map(e => e.model),
                    confidence: entries.reduce((sum, e) => sum + e.confidence, 0) / entries.length,
                    count: entries.length
                });
            } else if (entries.length === 1) {
                fieldData.discrepancies.push({
                    model: entries[0].model,
                    value: entries[0].value,
                    confidence: entries[0].confidence,
                    type: 'unique_value'
                });
            }
        });
        
        // Berechne Feld-Confidence basierend auf Agreements
        // KORREKTUR: Für komplett leere Felder (keine gültigen Werte) = 0% Confidence
        if (fieldData.values.length === 0) {
            fieldData.confidence = 0;
        } else {
            const maxAgreement = Math.max(...fieldData.agreements.map(a => a.count), 0);
            fieldData.confidence = maxAgreement / fieldData.values.length;
        }
    }
    
    /**
     * EMPTY VALUE DETECTION: Prüft ob ein Wert als leer/ungültig gelten soll
     */
    isEmptyValue(value) {
        if (!value) return true;
        
        const normalizedValue = String(value).toLowerCase().trim();
        
        // Liste der als leer geltenden Werte
        // CRITICAL FIX 19.08.2025: "X" ist KEIN leerer Wert - es ist der korrekte "nicht gefunden" Marker
        const emptyValues = [
            '', 'n/a', 'na', 'null', 'undefined', 'none', 'keine', 'keiner', 'kein',
            'unbekannt', 'unknown', 'nicht verfügbar', 'not available', 'no data',
            'keine angabe', 'keine daten', 'nicht vorhanden', 'not found',
            'leer', 'empty', '-', '--', '---', '?', '??', '???',
            'tbd', 'to be determined', 'wird ermittelt', 'in arbeit',
            'nicht angegeben', 'nicht ermittelt', 'k.a.', 'k.a', 'n.a.',
            'fehlt', 'missing', 'no information', 'no info'
        ];
        
        return emptyValues.includes(normalizedValue) || 
               normalizedValue.length === 0 ||
               /^[\s\-\?\.]*$/.test(normalizedValue); // Nur Leerzeichen, Striche, Fragezeichen
    }

    /**
     * VALUE NORMALIZATION: Normalisiert Werte für besseren Vergleich
     */
    normalizeValue(value) {
        if (typeof value !== 'string') return String(value).toLowerCase();
        
        return value
            .toLowerCase()
            .trim()
            .replace(/[^\w\s]/g, '') // Entferne Sonderzeichen
            .replace(/\s+/g, ' '); // Normalisiere Whitespace
    }
    
    /**
     * CONSENSUS DETECTION: Erkennt Consensus über mehrere Modelle
     */
    detectConsensus(analysis) {
        const consensus = {
            fields: {},
            overallScore: 0,
            strongConsensus: [],
            weakConsensus: [],
            noConsensus: []
        };
        
        Object.entries(analysis.fieldAnalysis).forEach(([fieldName, fieldData]) => {
            const bestAgreement = fieldData.agreements
                .sort((a, b) => b.count - a.count)[0];
            
            if (bestAgreement && bestAgreement.count >= 2) {
                const consensusStrength = bestAgreement.count / fieldData.values.length;
                
                consensus.fields[fieldName] = {
                    value: bestAgreement.value,
                    models: bestAgreement.models,
                    strength: consensusStrength,
                    confidence: bestAgreement.confidence,
                    weight: fieldData.weight
                };
                
                if (consensusStrength >= this.consensusThreshold) {
                    consensus.strongConsensus.push(fieldName);
                } else {
                    consensus.weakConsensus.push(fieldName);
                }
            } else {
                consensus.noConsensus.push(fieldName);
            }
        });
        
        // Berechne Overall Consensus Score
        consensus.overallScore = this.calculateConsensusScore(consensus);
        
        return consensus;
    }
    
    /**
     * DISCREPANCY DETECTION: Erkennt bedeutsame Diskrepanzen
     */
    detectDiscrepancies(analysis) {
        const discrepancies = [];
        
        Object.entries(analysis.fieldAnalysis).forEach(([fieldName, fieldData]) => {
            if (fieldData.values.length >= 2) {
                const uniqueValues = [...new Set(fieldData.values.map(v => this.normalizeValue(v.value)))];
                
                if (uniqueValues.length >= 2) {
                    discrepancies.push({
                        field: fieldName,
                        type: 'value_conflict',
                        severity: this.calculateDiscrepancySeverity(fieldData),
                        weight: fieldData.weight,
                        values: fieldData.values.map(v => ({
                            model: v.model,
                            value: v.value,
                            confidence: v.confidence
                        })),
                        impact: fieldData.weight * uniqueValues.length
                    });
                }
            }
        });
        
        // Sortiere nach Impact/Severity
        return discrepancies.sort((a, b) => b.impact - a.impact);
    }
    
    /**
     * DISCREPANCY SEVERITY: Berechnet Schwere von Diskrepanzen
     */
    calculateDiscrepancySeverity(fieldData) {
        const valueCount = [...new Set(fieldData.values.map(v => this.normalizeValue(v.value)))].length;
        const fieldWeight = fieldData.weight;
        const confidenceSpread = Math.max(...fieldData.values.map(v => v.confidence)) - 
                                Math.min(...fieldData.values.map(v => v.confidence));
        
        // Severity: Hoch wenn wichtiges Feld, viele verschiedene Werte, große Confidence-Unterschiede
        return fieldWeight * valueCount * (1 + confidenceSpread);
    }
    
    /**
     * CONFIDENCE CALCULATION: Berechnet Gesamt-Vertrauen
     */
    calculateOverallConfidence(analysis, consensus) {
        let weightedSum = 0;
        let totalWeight = 0;
        
        Object.entries(analysis.fieldAnalysis).forEach(([fieldName, fieldData]) => {
            const weight = fieldData.weight;
            let fieldConfidence = 0;
            
            if (consensus.fields[fieldName]) {
                fieldConfidence = consensus.fields[fieldName].confidence * consensus.fields[fieldName].strength;
            } else {
                fieldConfidence = fieldData.confidence * 0.5; // Penalty für no consensus
            }
            
            weightedSum += fieldConfidence * weight;
            totalWeight += weight;
        });
        
        return totalWeight > 0 ? weightedSum / totalWeight : 0;
    }
    
    /**
     * CONSENSUS SCORE: Berechnet Overall Consensus Score
     */
    calculateConsensusScore(consensus) {
        let weightedScore = 0;
        let totalWeight = 0;
        
        Object.entries(consensus.fields).forEach(([fieldName, consensusData]) => {
            weightedScore += consensusData.strength * consensusData.weight;
            totalWeight += consensusData.weight;
        });
        
        return totalWeight > 0 ? weightedScore / totalWeight : 0;
    }
    
    /**
     * QUALITY SCORE: Berechnet Gesamt-Datenqualität
     */
    calculateQualityScore(analysis) {
        const scores = Object.values(analysis.dataQuality).map(q => q.quality_score || 0);
        return scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 0;
    }
    
    /**
     * MODEL PERFORMANCE: Analysiert Performance einzelner Modelle
     */
    analyzeModelPerformance(result) {
        const performance = {
            dataCompleteness: 0,
            confidence: result.confidence || 0,
            sourceQuality: 0,
            responseTime: result.search_duration || 0
        };
        
        if (result.data && result.data.structured_data) {
            const fields = Object.entries(result.data.structured_data);
            const filledFields = fields.filter(([key, value]) => 
                key !== '_source_mapping' && value && value !== 'X' && value !== 'N/A'
            );
            
            performance.dataCompleteness = filledFields.length / fields.length;
        }
        
        if (result.data && result.data.sources) {
            performance.sourceQuality = result.data.sources.length > 0 ? 0.8 : 0.3;
        }
        
        return performance;
    }
    
    /**
     * SINGLE MODEL VIEW: Fallback für einzelne Modelle
     */
    generateSingleModelView(result) {
        return {
            id: `single_${Date.now()}`,
            type: 'single_model',
            model: result.model_id,
            data: result.data,
            confidence: result.confidence || 0,
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * GET COMPARISON: Ruft gespeicherten Vergleich ab
     */
    getComparison(comparisonId) {
        return this.activeComparisons.get(comparisonId);
    }
    
    /**
     * CLEANUP: Bereinigt alte Vergleiche
     */
    cleanup(maxAge = 3600000) { // 1 Stunde
        const now = Date.now();
        
        this.activeComparisons.forEach((comparison, id) => {
            const age = now - new Date(comparison.timestamp).getTime();
            if (age > maxAge) {
                this.activeComparisons.delete(id);
                console.log(`🧹 [COMPARISON] Vergleich ${id} bereinigt (${Math.round(age/60000)}min alt)`);
            }
        });
    }
}

// ============================================
// COMPARISON UI GENERATOR
// ============================================

/**
 * UI GENERATOR: Erstellt Interactive Comparison Views
 */
class ComparisonUIGenerator {
    constructor(comparisonEngine) {
        this.engine = comparisonEngine;
        this.currentView = null;
        
        console.log('🎨 [COMPARISON-UI] UI Generator initialisiert');
    }
    
    /**
     * GENERATE COMPARISON VIEW: Hauptfunktion für Comparison UI
     */
    generateComparisonView(comparison) {
        console.log(`🎨 [COMPARISON-UI] Generiere View für Vergleich ${comparison.id}`);
        
        if (comparison.type === 'single_model') {
            return this.generateSingleModelView(comparison);
        }
        
        const comparisonHTML = `
            <div class="comparison-revolution-container" data-comparison-id="${comparison.id}">
                ${this.generateComparisonHeader(comparison)}
                ${this.generateConsensusOverview(comparison)}
                <!-- PHASE 2: Model Performance Matrix nach Statistik-Tab verschoben -->
                ${this.generateFieldByFieldComparison(comparison)}
                ${this.generateDiscrepancyAnalysis(comparison)}
                ${this.generateExportControls(comparison)}
            </div>
        `;
        
        // Auto-highlight discrepancies after DOM insertion
        setTimeout(() => {
            const container = document.querySelector(`[data-comparison-id="${comparison.id}"]`);
            if (container && window.discrepancyHighlighter && comparison.discrepancies.length > 0) {
                console.log(`⚠️ [COMPARISON-UI] Auto-highlighting ${comparison.discrepancies.length} discrepancies`);
                window.discrepancyHighlighter.highlightDiscrepancies(comparison, container);
            }
        }, 500);
        
        return comparisonHTML;
    }
    
    /**
     * COMPARISON HEADER: Übersicht und Metriken
     */
    generateComparisonHeader(comparison) {
        const modelCount = comparison.models.length;
        const consensusPercentage = Math.round(comparison.consensus.overallScore * 100);
        const qualityScore = Math.round(comparison.metadata.overallQuality * 100);
        
        return `
            <div class="comparison-header">
                <div class="comparison-title">
                    <h2>🔬 Model Comparison Analysis</h2>
                    <span class="comparison-meta">${modelCount} Modelle • ${new Date(comparison.timestamp).toLocaleTimeString()}</span>
                </div>
                
                <div class="comparison-metrics">
                    <div class="metric-card consensus">
                        <div class="metric-value">${consensusPercentage}%</div>
                        <div class="metric-label">Consensus</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: ${consensusPercentage}%"></div>
                        </div>
                    </div>
                    
                    <div class="metric-card quality">
                        <div class="metric-value">${qualityScore}%</div>
                        <div class="metric-label">Data Quality</div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: ${qualityScore}%"></div>
                        </div>
                    </div>
                    
                    <div class="metric-card fields">
                        <div class="metric-value">${comparison.metadata.consensusFields}</div>
                        <div class="metric-label">Consensus Fields</div>
                        <div class="metric-sub">von ${comparison.metadata.totalFields}</div>
                    </div>
                    
                    <div class="metric-card discrepancies">
                        <div class="metric-value">${comparison.metadata.discrepancyCount}</div>
                        <div class="metric-label">Discrepancies</div>
                        <div class="metric-sub ${comparison.metadata.discrepancyCount > 5 ? 'high' : 'low'}">
                            ${comparison.metadata.discrepancyCount > 5 ? 'High' : 'Low'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * CONSENSUS OVERVIEW: Zeigt starke Übereinstimmungen
     */
    generateConsensusOverview(comparison) {
        const strongConsensus = comparison.consensus.strongConsensus
            .map(fieldName => {
                const consensusData = comparison.consensus.fields[fieldName];
                return `
                    <div class="consensus-field strong">
                        <div class="field-name">${fieldName}</div>
                        <div class="field-value">${consensusData.value}</div>
                        <div class="field-models">${consensusData.models.join(', ')}</div>
                        <div class="field-strength">${Math.round(consensusData.strength * 100)}% Übereinstimmung</div>
                    </div>
                `;
            }).join('');
        
        const weakConsensus = comparison.consensus.weakConsensus.slice(0, 3)
            .map(fieldName => {
                const consensusData = comparison.consensus.fields[fieldName];
                return `
                    <div class="consensus-field weak">
                        <div class="field-name">${fieldName}</div>
                        <div class="field-value">${consensusData.value}</div>
                        <div class="field-models">${consensusData.models.join(', ')}</div>
                        <div class="field-strength">${Math.round(consensusData.strength * 100)}% Übereinstimmung</div>
                    </div>
                `;
            }).join('');
        
        return `
            <div class="consensus-overview">
                <h3>✅ Strong Consensus (${comparison.consensus.strongConsensus.length} fields)</h3>
                <div class="consensus-fields">
                    ${strongConsensus || '<div class="no-consensus">Keine starken Übereinstimmungen gefunden</div>'}
                </div>
                
                ${weakConsensus ? `
                    <h4>⚠️ Weak Consensus (${comparison.consensus.weakConsensus.length} fields)</h4>
                    <div class="consensus-fields weak">
                        ${weakConsensus}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * MODEL PERFORMANCE MATRIX: Zeigt Performance aller Modelle
     */
    generateModelPerformanceMatrix(comparison) {
        const performanceRows = comparison.models.map(modelId => {
            const performance = comparison.analysis.modelPerformance[modelId];
            const quality = comparison.analysis.dataQuality[modelId];
            
            const completeness = Math.round(performance.dataCompleteness * 100);
            const confidence = Math.round(performance.confidence * 100);
            const sourceQuality = Math.round(performance.sourceQuality * 100);
            const overallScore = Math.round((performance.dataCompleteness + performance.confidence + performance.sourceQuality) / 3 * 100);
            
            return `
                <tr class="performance-row" data-model="${modelId}">
                    <td class="model-name">
                        <div class="model-id">${modelId}</div>
                        <div class="provider-tag">${modelId.split(':')[0]}</div>
                    </td>
                    <td class="performance-score ${this.getScoreClass(overallScore)}">
                        ${overallScore}%
                    </td>
                    <td class="completeness">
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${completeness}%"></div>
                            <span class="score-text">${completeness}%</span>
                        </div>
                    </td>
                    <td class="confidence">
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${confidence}%"></div>
                            <span class="score-text">${confidence}%</span>
                        </div>
                    </td>
                    <td class="source-quality">
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${sourceQuality}%"></div>
                            <span class="score-text">${sourceQuality}%</span>
                        </div>
                    </td>
                    <td class="response-time">
                        ${performance.responseTime ? Math.round(performance.responseTime * 1000) + 'ms' : 'N/A'}
                    </td>
                </tr>
            `;
        }).join('');
        
        return `
            <div class="performance-matrix">
                <h3>📊 Model Performance Matrix</h3>
                <table class="performance-table">
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Overall Score</th>
                            <th>Data Completeness</th>
                            <th>Confidence</th>
                            <th>Source Quality</th>
                            <th>Response Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${performanceRows}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    /**
     * FIELD BY FIELD: Detaillierter Feldvergleich
     */
    generateFieldByFieldComparison(comparison) {
        // PHASE 4: Responsives Card-Layout statt schmaler Tabelle
        const fieldCards = Object.entries(comparison.analysis.fieldAnalysis)
            .filter(([fieldName, fieldData]) => fieldData.values.length > 0)
            .sort((a, b) => b[1].weight - a[1].weight) // Sortiere nach Wichtigkeit
            .map(([fieldName, fieldData]) => {
                const hasConsensus = comparison.consensus.fields[fieldName];
                const hasDiscrepancy = comparison.discrepancies.some(d => d.field === fieldName);
                
                // Organisiere Werte nach Provider für bessere Übersicht
                const valuesByProvider = {};
                fieldData.values.forEach(value => {
                    const provider = value.model.split(':')[0];
                    if (!valuesByProvider[provider]) {
                        valuesByProvider[provider] = [];
                    }
                    valuesByProvider[provider].push(value);
                });
                
                // Generiere Provider-Sektionen
                const providerSections = Object.entries(valuesByProvider).map(([provider, values]) => {
                    const providerValues = values.map(value => {
                        const isConsensus = hasConsensus && hasConsensus.models.includes(value.model);
                        const modelShortName = value.model.split(':')[1] || value.model;
                        
                        return `
                            <div class="model-value ${isConsensus ? 'consensus' : ''} ${hasDiscrepancy ? 'discrepancy' : ''}">
                                <div class="model-name">${modelShortName}</div>
                                <div class="model-result">
                                    <span class="value-text">${value.value}</span>
                                    <span class="confidence-badge">${Math.round(value.confidence * 100)}%</span>
                                </div>
                            </div>
                        `;
                    }).join('');
                    
                    return `
                        <div class="provider-section">
                            <div class="provider-header">${provider}</div>
                            <div class="provider-values">
                                ${providerValues}
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Consensus Information
                const consensusInfo = hasConsensus ? `
                    <div class="consensus-info">
                        <span class="consensus-badge">✓ Consensus</span>
                        <span class="consensus-value">${hasConsensus.value}</span>
                        <span class="consensus-strength">${Math.round(hasConsensus.strength * 100)}%</span>
                    </div>
                ` : '';
                
                // Discrepancy Information
                const discrepancyInfo = hasDiscrepancy ? `
                    <div class="discrepancy-info">
                        <span class="discrepancy-badge">⚠ Konflikt</span>
                        <span class="discrepancy-note">Widersprüchliche Werte gefunden</span>
                    </div>
                ` : '';
                
                return `
                    <div class="field-comparison-card" data-field="${fieldName}">
                        <div class="field-card-header">
                            <h4 class="field-title">${fieldName}</h4>
                            <div class="field-meta">
                                <span class="field-weight">Gewichtung: ${Math.round(fieldData.weight * 100)}%</span>
                                <span class="field-values-count">${fieldData.values.length} Werte</span>
                            </div>
                        </div>
                        
                        ${consensusInfo}
                        ${discrepancyInfo}
                        
                        <div class="field-providers">
                            ${providerSections}
                        </div>
                        
                        <div class="field-summary">
                            <div class="summary-stats">
                                <span>📊 ${fieldData.agreements.length} Übereinstimmungen</span>
                                <span>⚠️ ${fieldData.discrepancies.length} Konflikte</span>
                                <span>🎯 ${Math.round(fieldData.confidence * 100)}% Vertrauen</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        
        return `
            <div class="field-comparison-modern">
                <div class="field-comparison-header">
                    <h3>📋 Field-by-Field Analysis</h3>
                    <div class="comparison-controls">
                        <button class="toggle-view-btn" onclick="toggleFieldViewMode()" title="Zwischen Ansichten wechseln">
                            🔄 Kompakt-Ansicht
                        </button>
                        <button class="expand-all-btn" onclick="expandAllFields()" title="Alle Felder erweitern">
                            📖 Alle erweitern
                        </button>
                    </div>
                </div>
                
                <div class="field-cards-container">
                    ${fieldCards}
                </div>
                
                <div class="field-comparison-footer">
                    <div class="legend">
                        <h4>Legende</h4>
                        <div class="legend-items">
                            <span class="legend-item"><span class="consensus-badge">✓</span> Consensus-Wert</span>
                            <span class="legend-item"><span class="discrepancy-badge">⚠</span> Konflikt erkannt</span>
                            <span class="legend-item"><span class="confidence-badge">%</span> Konfidenz-Level</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * DISCREPANCY ANALYSIS: Zeigt wichtige Diskrepanzen
     */
    generateDiscrepancyAnalysis(comparison) {
        if (comparison.discrepancies.length === 0) {
            return `
                <div class="discrepancy-analysis">
                    <h3>✅ No Significant Discrepancies</h3>
                    <p>Alle Modelle zeigen konsistente Ergebnisse.</p>
                </div>
            `;
        }
        
        const topDiscrepancies = comparison.discrepancies.slice(0, 5)
            .map(discrepancy => {
                const severityClass = this.getSeverityClass(discrepancy.severity);
                
                const valuesList = discrepancy.values.map(v => `
                    <div class="discrepancy-value">
                        <span class="value-model">${v.model}:</span>
                        <span class="value-text">${v.value}</span>
                        <span class="value-confidence">(${Math.round(v.confidence * 100)}%)</span>
                    </div>
                `).join('');
                
                return `
                    <div class="discrepancy-item ${severityClass}">
                        <div class="discrepancy-header">
                            <div class="discrepancy-field">${discrepancy.field}</div>
                            <div class="discrepancy-severity">Impact: ${Math.round(discrepancy.impact * 100)}</div>
                        </div>
                        <div class="discrepancy-values">
                            ${valuesList}
                        </div>
                    </div>
                `;
            }).join('');
        
        return `
            <div class="discrepancy-analysis">
                <h3>⚠️ Significant Discrepancies (${comparison.discrepancies.length})</h3>
                <div class="discrepancy-list">
                    ${topDiscrepancies}
                </div>
                ${comparison.discrepancies.length > 5 ? `
                    <div class="show-more-discrepancies">
                        <button onclick="showAllDiscrepancies('${comparison.id}')">
                            Show ${comparison.discrepancies.length - 5} more discrepancies
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * EXPORT CONTROLS: Export-Optionen für Vergleich
     */
    generateExportControls(comparison) {
        return `
            <div class="export-controls">
                <h4>📤 Export Comparison</h4>
                <div class="export-buttons">
                    <button class="export-btn consensus" onclick="exportComparison('${comparison.id}', 'consensus')">
                        📋 Export Consensus Data
                    </button>
                    <button class="export-btn detailed" onclick="exportComparison('${comparison.id}', 'detailed')">
                        📊 Export Detailed Analysis
                    </button>
                    <button class="export-btn json" onclick="exportComparison('${comparison.id}', 'json')">
                        💾 Export Raw JSON
                    </button>
                    <button class="export-btn report" onclick="exportComparison('${comparison.id}', 'report')">
                        📄 Generate Report
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * HELPER METHODS: Utility-Funktionen für UI
     */
    getScoreClass(score) {
        if (score >= 80) return 'excellent';
        if (score >= 60) return 'good';
        if (score >= 40) return 'fair';
        return 'poor';
    }
    
    getSeverityClass(severity) {
        if (severity >= 0.8) return 'critical';
        if (severity >= 0.6) return 'high';
        if (severity >= 0.4) return 'medium';
        return 'low';
    }
    
    generateSingleModelView(comparison) {
        return `
            <div class="single-model-view">
                <h3>📊 Single Model Result: ${comparison.model}</h3>
                <div class="single-model-data">
                    ${JSON.stringify(comparison.data, null, 2)}
                </div>
            </div>
        `;
    }
}

// ============================================
// GLOBAL INITIALIZATION
// ============================================

// Erstelle globale Instanzen
window.comparisonEngine = new ComparisonEngine();
window.comparisonUIGenerator = new ComparisonUIGenerator(window.comparisonEngine);

// Export functions
window.generateComparison = (multiModelResults) => {
    return window.comparisonEngine.generateComparison(multiModelResults);
};

window.generateComparisonView = (comparison) => {
    return window.comparisonUIGenerator.generateComparisonView(comparison);
};

// Cleanup-Timer (alle 30 Minuten)
setInterval(() => {
    window.comparisonEngine.cleanup();
}, 30 * 60 * 1000);

// ============================================
// FIELD-BY-FIELD UI UTILITY FUNCTIONS
// ============================================

/**
 * TOGGLE VIEW MODE: Wechselt zwischen Kompakt- und Ausführlicher Ansicht
 */
function toggleFieldViewMode() {
    const container = document.querySelector('.field-cards-container');
    const toggleBtn = document.querySelector('.toggle-view-btn');
    
    if (!container || !toggleBtn) return;
    
    const isCompact = container.classList.contains('compact-view');
    
    if (isCompact) {
        // Wechsel zu Ausführlicher Ansicht
        container.classList.remove('compact-view');
        toggleBtn.innerHTML = '🔄 Kompakt-Ansicht';
        toggleBtn.title = 'Zur Kompakt-Ansicht wechseln';
        console.log('🎨 [COMPARISON-UI] Wechsel zu Ausführlicher Ansicht');
    } else {
        // Wechsel zu Kompakt-Ansicht
        container.classList.add('compact-view');
        toggleBtn.innerHTML = '🔄 Ausführlich';
        toggleBtn.title = 'Zur Ausführlichen Ansicht wechseln';
        console.log('🎨 [COMPARISON-UI] Wechsel zu Kompakt-Ansicht');
    }
}

/**
 * EXPAND ALL FIELDS: Erweitert/Kollabiert alle Feld-Karten
 */
function expandAllFields() {
    const fieldCards = document.querySelectorAll('.field-comparison-card');
    const expandBtn = document.querySelector('.expand-all-btn');
    
    if (!fieldCards.length || !expandBtn) return;
    
    const isExpanded = expandBtn.textContent.includes('Kollabieren');
    
    fieldCards.forEach(card => {
        if (isExpanded) {
            // Kollabiere alle Karten
            card.classList.add('collapsed');
            const providers = card.querySelector('.field-providers');
            const summary = card.querySelector('.field-summary');
            if (providers) providers.style.display = 'none';
            if (summary) summary.style.display = 'none';
        } else {
            // Erweitere alle Karten
            card.classList.remove('collapsed');
            const providers = card.querySelector('.field-providers');
            const summary = card.querySelector('.field-summary');
            if (providers) providers.style.display = 'block';
            if (summary) summary.style.display = 'block';
        }
    });
    
    // Update Button-Text
    if (isExpanded) {
        expandBtn.innerHTML = '📖 Alle erweitern';
        expandBtn.title = 'Alle Felder erweitern';
        console.log('🎨 [COMPARISON-UI] Alle Felder kollabiert');
    } else {
        expandBtn.innerHTML = '📕 Alle kollabieren';
        expandBtn.title = 'Alle Felder kollabieren';
        console.log('🎨 [COMPARISON-UI] Alle Felder erweitert');
    }
}

/**
 * FIELD CARD CLICK HANDLER: Toggle einzelne Feld-Karten
 */
function toggleSingleField(fieldName) {
    const fieldCard = document.querySelector(`[data-field="${fieldName}"]`);
    if (!fieldCard) return;
    
    const isCollapsed = fieldCard.classList.contains('collapsed');
    const providers = fieldCard.querySelector('.field-providers');
    const summary = fieldCard.querySelector('.field-summary');
    
    if (isCollapsed) {
        // Erweitere diese Karte
        fieldCard.classList.remove('collapsed');
        if (providers) providers.style.display = 'block';
        if (summary) summary.style.display = 'block';
        console.log(`🎨 [COMPARISON-UI] Feld ${fieldName} erweitert`);
    } else {
        // Kollabiere diese Karte
        fieldCard.classList.add('collapsed');
        if (providers) providers.style.display = 'none';
        if (summary) summary.style.display = 'none';
        console.log(`🎨 [COMPARISON-UI] Feld ${fieldName} kollabiert`);
    }
}

// Export utility functions to global scope
window.toggleFieldViewMode = toggleFieldViewMode;
window.expandAllFields = expandAllFields;
window.toggleSingleField = toggleSingleField;

console.log('🚀 [PHASE 4] Interactive Comparison Engine geladen');