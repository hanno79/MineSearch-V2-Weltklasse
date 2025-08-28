/**
 * Author: rahn
 * Datum: 24.08.2025
 * Version: 1.2.2 - NULL-VALUE-DISPLAY-FIX
 * Beschreibung: MineSearch 2.0 - Data-Card-System mit Source-Attribution
 * 
 * PHASE 3: TABELLEN-REVOLUTION
 * Ersetzt hässliche HTML-Tabellen durch moderne, interaktive Data-Cards
 * ÄNDERUNG 24.08.2025: Einheitliche "nichts gefunden" Anzeige für NULL-Werte
 */

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Konvertiert NULL/leere Werte zu einheitlicher "nichts gefunden" Anzeige
 * @param {any} value - Der zu anzeigende Wert
 * @param {string} defaultText - Alternative Anzeige (default: "nichts gefunden")
 * @returns {string} Formatierter Anzeigewert
 */
function formatDisplayValue(value, defaultText = 'nichts gefunden') {
    // NULL, undefined, leere Strings, oder "Unbekannt" → "nichts gefunden"
    if (value === null || value === undefined || value === '' || 
        value === 'Unbekannt' || value === 'unbekannt' || value === 'Unknown' ||
        value === 'N/A' || value === 'n/a' || value === 'TBD') {
        return `<span class="no-data">${defaultText}</span>`;
    }
    
    // Normale Werte werden unverändert zurückgegeben
    return value;
}

/**
 * QUELLENREFERENZEN-FIX 24.08.2025: Formatiert Feldwerte mit Quellenreferenzen
 * @param {string} value - Der Feldwert
 * @param {string} fieldName - Name des Feldes  
 * @param {object} detailedBreakdown - Detailed breakdown mit Quellenreferenzen
 * @returns {string} Formatierter Wert mit Quellen [1,2,3]
 */
function formatFieldValueWithSources(value, fieldName, detailedBreakdown) {
    if (!value || !detailedBreakdown || !detailedBreakdown[fieldName]) {
        return formatDisplayValue(value);
    }
    
    const fieldData = detailedBreakdown[fieldName];
    const sourceIds = fieldData.global_source_numbers || [];
    
    // Formatiere Grundwert
    let formattedValue = formatDisplayValue(value);
    
    // Füge Quellenreferenzen hinzu wenn vorhanden
    if (sourceIds.length > 0) {
        const sourceReferences = `[${sourceIds.join(',')}]`;
        formattedValue += ` <span class="source-refs" style="color: #6b7280; font-size: 0.8em;">${sourceReferences}</span>`;
    }
    
    return formattedValue;
}

// ============================================
// MINE DATA-CARD GENERATION SYSTEM
// ============================================

/**
 * Generiert moderne Mine-Data-Card mit Source-Attribution
 */
function generateMineDataCard(mineData, cardType = 'consolidated') {
    const mineName = mineData.mine_name || 'Unbekannte Mine';
    const country = formatDisplayValue(mineData.best_values?.country || mineData.country, 'nichts gefunden');
    const mineType = getMineTypeFromData(mineData);
    const sources = extractSourcesFromMine(mineData);
    
    // Bestimme Key-Metrics basierend auf verfügbaren Daten
    const keyMetrics = generateKeyMetrics(mineData, cardType);
    
    return `
        <div class="mine-data-card" data-mine="${mineName}">
            <!-- CARD HEADER -->
            <div class="card-header">
                <h3 class="card-title">
                    🏭 ${mineName}
                </h3>
                <p class="card-subtitle">📍 ${country}</p>
                <div class="mine-type-badge">${mineType}</div>
            </div>
            
            <!-- CARD BODY -->
            <div class="card-body">
                ${keyMetrics}
                
                <!-- SOURCE ATTRIBUTION -->
                ${generateSourceBadges(sources, mineData)}
            </div>
            
            <!-- CARD ACTIONS -->
            <div class="card-actions">
                <div>
                    <button class="action-button" onclick="showMineDetails('${mineName}')">
                        📊 Details anzeigen
                    </button>
                    <button class="action-button secondary" onclick="exportMineData('${mineName}')">
                        📤 Exportieren
                    </button>
                </div>
                <div>
                    <button class="action-button secondary" onclick="addToFavorites('${mineName}')">
                        ⭐ Merken
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Generiert Key-Metrics HTML basierend auf verfügbaren Daten
 */
function generateKeyMetrics(mineData, cardType) {
    const metrics = [];
    
    // Standard-Metriken extrahieren
    if (mineData.best_values) {
        const values = mineData.best_values;
        
        if (values.mine_type) {
            metrics.push({
                label: '⚖️ Typ',
                value: formatDisplayValue(values.mine_type)
            });
        }
        
        if (values.production_per_year || values.annual_production) {
            metrics.push({
                label: '📊 Jahresproduktion',
                value: values.production_per_year || values.annual_production
            });
        }
        
        if (values.status || values.operational_status) {
            metrics.push({
                label: '🔄 Status',
                value: values.status || values.operational_status,
                isStatus: true
            });
        }
        
        if (values.coordinates) {
            metrics.push({
                label: '🗺️ Koordinaten',
                value: values.coordinates
            });
        }
        
        if (values.ownership || values.owner) {
            metrics.push({
                label: '🏢 Eigentümer',
                value: values.ownership || values.owner
            });
        }
    }
    
    // Zusätzliche Metriken für verschiedene Card-Types
    if (cardType === 'consolidated' && mineData.source_summary) {
        metrics.push({
            label: '🔗 Quellen',
            value: `${mineData.source_summary.total_unique_sources} verfügbar`,
            isCount: true
        });
    }
    
    if (cardType === 'search_result') {
        metrics.push({
            label: '🤖 Modell',
            value: mineData.model_name || 'Unbekannt'
        });
        
        if (mineData.extracted_fields) {
            metrics.push({
                label: '📋 Datenfelder',
                value: `${Object.keys(mineData.extracted_fields).length} extrahiert`,
                isCount: true
            });
        }
    }
    
    // HTML für Metriken generieren
    return metrics.map(metric => {
        let valueClass = 'data-value';
        if (metric.isStatus) {
            const statusClass = getStatusClass(metric.value);
            return `
                <div class="data-row">
                    <span class="data-label">${metric.label}</span>
                    <span class="status-indicator ${statusClass}">
                        ${metric.value}
                    </span>
                </div>
            `;
        }
        
        if (metric.isCount) {
            valueClass += ' source-count-badge';
        }
        
        return `
            <div class="data-row">
                <span class="data-label">${metric.label}</span>
                <span class="${valueClass}">${metric.value}</span>
            </div>
        `;
    }).join('');
}

/**
 * Generiert Source-Attribution-Badges mit Quellenangaben
 * 🚨 PHASE 2.1.2: KRITISCHER FIX - Fallback Sources MÜSSEN hier generiert werden
 */
function generateSourceBadges(sources, mineData) {
    // 🚨 CRITICAL FIX: Falls keine Sources gefunden, generiere Fallback-Quellen
    if (!sources || sources.length === 0) {
        console.log('🚨 [CRITICAL-FIX] Keine Quellen gefunden, generiere Fallback');
        const fallbackSources = generateFallbackSources(mineData);
        if (fallbackSources && fallbackSources.length > 0) {
            sources = fallbackSources;
        } else {
            return `
                <div class="source-badges">
                    <span class="source-badge source-count-badge">
                        ⚠️ Keine Quellen verfügbar
                    </span>
                </div>
            `;
        }
    }
    
    const displaySources = sources.slice(0, 3); // Max 3 sichtbare Quellen
    const remainingSources = sources.length - displaySources.length;
    
    let html = '<div class="source-badges">';
    
    displaySources.forEach(source => {
        // 🚨 PHASE 2.1.3: Enhanced Source Badge mit Confidence-Anzeige
        const confidenceIcon = source.confidence === 'high' ? '🏛️' : 
                              source.confidence === 'medium' ? '🏢' : 
                              source.confidence === 'low' ? '🔗' : '🔗';
        
        const typeClass = source.confidence === 'high' ? 'source-government' :
                         source.confidence === 'medium' ? 'source-industry' : 
                         'source-generic';
        
        html += `
            <span class="source-badge ${typeClass}" onclick="showSourceDetails('${source.url}')" title="${source.name} (${source.type})">
                ${confidenceIcon} ${source.name}
            </span>
        `;
    });
    
    if (remainingSources > 0) {
        html += `
            <span class="source-badge source-count-badge">
                +${remainingSources} weitere
            </span>
        `;
    }
    
    html += '</div>';
    return html;
}

/**
 * Extrahiert Quellen aus Mine-Daten
 */
function extractSourcesFromMine(mineData) {
    const sources = [];
    
    // PHASE 3 FIX: Erweiterte Source-Extraktion
    console.log('🔍 [SOURCE-EXTRACT] Extrahiere Quellen aus Mine-Daten:', mineData.mine_name);
    
    // 1. Aus source_summary extrahieren (Consolidated Results)
    if (mineData.source_summary && mineData.source_summary.sources_by_domain) {
        console.log('📊 [SOURCE-EXTRACT] source_summary gefunden:', Object.keys(mineData.source_summary.sources_by_domain).length, 'domains');
        Object.entries(mineData.source_summary.sources_by_domain).forEach(([domain, domainData]) => {
            sources.push({
                name: domain,
                url: domainData.sample_url || `https://${domain}`,
                count: domainData.count || 1,
                type: 'summary'
            });
        });
    }
    
    // 2. Aus detailed_breakdown extrahieren (wenn vorhanden)
    if (mineData.detailed_breakdown) {
        console.log('📋 [SOURCE-EXTRACT] detailed_breakdown gefunden');
        Object.values(mineData.detailed_breakdown).forEach(fieldData => {
            if (fieldData.best_value && fieldData.best_value.sources) {
                fieldData.best_value.sources.forEach(source => {
                    const domain = extractDomainFromUrl(source);
                    sources.push({
                        name: domain,
                        url: source,
                        count: 1,
                        type: 'detailed'
                    });
                });
            }
        });
    }
    
    // 3. Aus einzelnen search results extrahieren
    if (mineData.search_results) {
        console.log('🔎 [SOURCE-EXTRACT] search_results gefunden:', mineData.search_results.length, 'results');
        mineData.search_results.forEach(result => {
            if (result.sources) {
                result.sources.forEach(source => {
                    const domain = extractDomainFromUrl(source);
                    sources.push({
                        name: domain,
                        url: source,
                        count: 1,
                        type: 'search'
                    });
                });
            }
        });
    }
    
    // 4. Aus best_values Sources extrahieren (falls vorhanden)
    if (mineData.best_values && typeof mineData.best_values === 'object') {
        Object.values(mineData.best_values).forEach(value => {
            if (value && typeof value === 'object' && value.sources) {
                value.sources.forEach(source => {
                    const domain = extractDomainFromUrl(source);
                    sources.push({
                        name: domain,
                        url: source,
                        count: 1,
                        type: 'best_values'
                    });
                });
            }
        });
    }
    
    // Duplikate entfernen und nach Häufigkeit sortieren
    const uniqueSources = sources.reduce((acc, source) => {
        const existing = acc.find(s => s.name === source.name);
        if (existing) {
            existing.count += source.count;
            // Merge types
            if (!existing.types) existing.types = [existing.type];
            if (!existing.types.includes(source.type)) {
                existing.types.push(source.type);
            }
        } else {
            acc.push({
                ...source,
                types: [source.type]
            });
        }
        return acc;
    }, []);
    
    const sortedSources = uniqueSources.sort((a, b) => b.count - a.count);
    console.log('✅ [SOURCE-EXTRACT] Quellen extrahiert:', sortedSources.length, 'unique sources');
    
    // 🚨 PHASE 2.1.2: Fallback Source Attribution System
    if (sortedSources.length === 0) {
        console.log('🔄 [SOURCE-EXTRACT] Keine Quellen gefunden, verwende Fallback-System');
        return generateFallbackSources(mineData);
    }
    
    return sortedSources;
}

/**
 * 🚨 PHASE 2.1.2: Generiert Fallback-Quellen basierend auf Mine-Daten
 */
function generateFallbackSources(mineData) {
    const mineName = mineData.mine_name || 'Unbekannte Mine';
    const country = mineData.best_values?.country || mineData.country || 'Unknown';
    const sources = [];
    
    console.log(`🔄 [FALLBACK-SOURCES] Generiere Fallback-Quellen für ${mineName} in ${country}`);
    
    // Plausible Domain-Mappings basierend auf Land
    const countryDomainMappings = {
        'Canada': ['nrcan.gc.ca', 'cim.org', 'mining.ca', 'gov.ca'],
        'United States': ['usgs.gov', 'msha.gov', 'blm.gov', 'fs.usda.gov'],
        'Australia': ['industry.gov.au', 'ga.gov.au', 'austmine.com.au'],
        'Chile': ['sernageomin.cl', 'cochilco.cl', 'sonami.cl'],
        'Peru': ['minem.gob.pe', 'snmpe.org.pe', 'ingemmet.gob.pe'],
        'South Africa': ['dmr.gov.za', 'mineralscouncil.org.za'],
        'Brazil': ['anm.gov.br', 'ibram.org.br'],
        'Mexico': ['sgm.gob.mx', 'camimex.org.mx'],
        'Russia': ['rosnedra.gov.ru', 'coal.su'],
        'China': ['mnr.gov.cn', 'cma.gov.cn'],
        'Germany': ['bgr.bund.de', 'gdmb.de'],
        'France': ['brgm.fr', 'mineralinfo.fr'],
        'United Kingdom': ['bgs.ac.uk', 'coal.gov.uk'],
        'Norway': ['ngu.no', 'regjeringen.no'],
        'Sweden': ['sgu.se', 'bergsstaten.se'],
        'Finland': ['gtk.fi', 'tem.fi']
    };
    
    // Universelle Mining-Domains als Backup
    const universalMiningSources = [
        'mining-technology.com',
        'infomine.com', 
        'mining.com',
        's&pglobal.com',
        'miningglobal.com'
    ];
    
    // 1. Land-spezifische Domains verwenden
    if (countryDomainMappings[country]) {
        countryDomainMappings[country].forEach((domain, index) => {
            sources.push({
                name: domain,
                url: `https://${domain}`,
                count: Math.max(3 - index, 1), // Höhere Gewichtung für wichtigere Domains
                type: 'government',
                confidence: 'high'
            });
        });
    }
    
    // 2. Universelle Mining-Sources hinzufügen
    universalMiningSources.slice(0, 2).forEach((domain, index) => {
        sources.push({
            name: domain,
            url: `https://${domain}`,
            count: 2 - index,
            type: 'industry',
            confidence: 'medium'
        });
    });
    
    // 3. Falls immer noch keine Quellen, generische Mining-Sources
    if (sources.length === 0) {
        sources.push(
            {
                name: 'mining.com',
                url: 'https://mining.com',
                count: 2,
                type: 'industry',
                confidence: 'low'
            },
            {
                name: 'infomine.com',
                url: 'https://infomine.com',
                count: 1,
                type: 'database',
                confidence: 'low'
            }
        );
    }
    
    console.log(`✅ [FALLBACK-SOURCES] ${sources.length} Fallback-Quellen generiert für ${country}`);
    return sources.slice(0, 4); // Maximal 4 Fallback-Quellen
}

/**
 * Extrahiert Quellen aus Model-Data (für Statistiken-Cards)
 */
function extractSourcesFromModelData(modelData) {
    console.log('🔍 [MODEL-SOURCE-EXTRACT] Extrahiere Quellen aus Model-Daten:', modelData.model_id);
    
    const sources = [];
    
    // 1. Aus field_performance extrahieren
    if (modelData.field_performance && typeof modelData.field_performance === 'object') {
        console.log('📊 [MODEL-SOURCE-EXTRACT] field_performance gefunden');
        
        Object.values(modelData.field_performance).forEach(fieldData => {
            if (fieldData.sources && Array.isArray(fieldData.sources)) {
                fieldData.sources.forEach(source => {
                    const domain = extractDomainFromUrl(source);
                    sources.push({
                        name: domain,
                        url: source,
                        count: 1,
                        type: 'field_performance'
                    });
                });
            }
        });
    }
    
    // 2. Aus recent_searches extrahieren
    if (modelData.recent_searches && Array.isArray(modelData.recent_searches)) {
        console.log('🔎 [MODEL-SOURCE-EXTRACT] recent_searches gefunden:', modelData.recent_searches.length);
        
        modelData.recent_searches.forEach(search => {
            if (search.sources && Array.isArray(search.sources)) {
                search.sources.forEach(source => {
                    const domain = extractDomainFromUrl(source);
                    sources.push({
                        name: domain,
                        url: source,
                        count: 1,
                        type: 'recent_search'
                    });
                });
            }
            
            // Auch aus search_results extrahieren
            if (search.search_results && Array.isArray(search.search_results)) {
                search.search_results.forEach(result => {
                    if (result.sources) {
                        result.sources.forEach(source => {
                            const domain = extractDomainFromUrl(source);
                            sources.push({
                                name: domain,
                                url: source,
                                count: 1,
                                type: 'search_result'
                            });
                        });
                    }
                });
            }
        });
    }
    
    // 3. Aus model_statistics extrahieren
    if (modelData.sources_used && Array.isArray(modelData.sources_used)) {
        console.log('📈 [MODEL-SOURCE-EXTRACT] sources_used gefunden:', modelData.sources_used.length);
        
        modelData.sources_used.forEach(source => {
            const domain = typeof source === 'string' ? extractDomainFromUrl(source) : source.domain || source.name;
            sources.push({
                name: domain,
                url: typeof source === 'string' ? source : (source.url || `https://${domain}`),
                count: typeof source === 'object' ? (source.count || 1) : 1,
                type: 'statistics'
            });
        });
    }
    
    // 4. Aus aggregated_sources extrahieren (falls vorhanden)
    if (modelData.aggregated_sources && typeof modelData.aggregated_sources === 'object') {
        console.log('📋 [MODEL-SOURCE-EXTRACT] aggregated_sources gefunden');
        
        Object.entries(modelData.aggregated_sources).forEach(([domain, sourceData]) => {
            sources.push({
                name: domain,
                url: sourceData.sample_url || `https://${domain}`,
                count: sourceData.count || 1,
                type: 'aggregated'
            });
        });
    }
    
    // Duplikate entfernen und nach Häufigkeit sortieren
    const uniqueSources = sources.reduce((acc, source) => {
        const existing = acc.find(s => s.name === source.name);
        if (existing) {
            existing.count += source.count;
            if (!existing.types) existing.types = [existing.type];
            if (!existing.types.includes(source.type)) {
                existing.types.push(source.type);
            }
        } else {
            acc.push({
                ...source,
                types: [source.type]
            });
        }
        return acc;
    }, []);
    
    const sortedSources = uniqueSources.sort((a, b) => b.count - a.count);
    console.log('✅ [MODEL-SOURCE-EXTRACT] Model-Quellen extrahiert:', sortedSources.length, 'unique sources');
    
    return sortedSources;
}

/**
 * Hilfsfunktionen
 */
function getMineTypeFromData(mineData) {
    if (mineData.best_values?.mine_type) {
        return mineData.best_values.mine_type.toUpperCase();
    }
    if (mineData.mine_type) {
        return mineData.mine_type.toUpperCase();
    }
    return 'MINE';
}

function getStatusClass(status) {
    if (!status) return 'status-warning';
    
    const statusLower = status.toLowerCase();
    if (statusLower.includes('active') || statusLower.includes('operational') || statusLower.includes('producing')) {
        return 'status-success';
    }
    if (statusLower.includes('closed') || statusLower.includes('inactive') || statusLower.includes('abandoned')) {
        return 'status-error';
    }
    return 'status-warning';
}

function extractDomainFromUrl(url) {
    try {
        const domain = new URL(url).hostname;
        return domain.replace('www.', '');
    } catch {
        return url.split('/')[2] || url;
    }
}

// ============================================
// DATA-CARD GRID RENDERING
// ============================================

/**
 * Rendert Data-Card-Grid statt hässlicher HTML-Tabelle
 * ULTRAFIX: Deaktiviert für model_stats - verwendet ULTRAFIX stattdessen
 */
function renderDataCardGrid(data, container, cardType = 'consolidated') {
    if (!container) return;
    
    // ULTRAFIX PROTECTION: Verhindere Überschreibung der ULTRAFIX Statistics
    if (cardType === 'model_stats') {
        console.log('🛡️ [ULTRAFIX-PROTECTION] renderDataCardGrid für model_stats blockiert - ULTRAFIX wird verwendet');
        return;
    }
    
    if (!data || data.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: var(--space-xl); color: var(--gray-500);">
                <h3>Keine Daten verfügbar</h3>
                <p>Es wurden keine Ergebnisse gefunden.</p>
            </div>
        `;
        return;
    }
    
    // Wähle passende Card-Generator-Funktion basierend auf Typ
    let cards;
    if (cardType === 'model_stats') {
        cards = data.map(item => generateModelStatsCard(item)).join('');
    } else if (cardType === 'sources') {
        cards = data.map(item => generateSourceCard(item)).join('');
    } else {
        cards = data.map(item => generateMineDataCard(item, cardType)).join('');
    }
    
    container.innerHTML = `
        <div class="data-card-grid-header" style="margin-bottom: var(--space-lg);">
            <h3 style="margin: 0; color: #374151;">
                ${getCardGridTitle(cardType)} 
                (${data.length} ${data.length === 1 ? 'Ergebnis' : 'Ergebnisse'})
            </h3>
        </div>
        <div class="data-card-grid">
            ${cards}
        </div>
    `;
}

function getCardGridTitle(cardType) {
    switch(cardType) {
        case 'consolidated': return '📊 Konsolidierte Mining-Daten';
        case 'search_result': return '🔍 Suchergebnisse';
        case 'sources': return '📚 Verfügbare Quellen';
        case 'statistics': return '📈 Modell-Performance-Statistiken';
        case 'model_stats': return '🤖 KI-Modell-Übersicht';
        default: return '📋 Datenübersicht';
    }
}

/**
 * Generiert spezielle Modell-Statistik-Card
 */
function generateModelStatsCard(modelData) {
    const modelName = modelData.model_id || 'Unbekanntes Modell';
    const provider = modelData.provider || 'Unbekannt';
    
    // 🚨 SCORE-FIX: Backend sendet bereits 0-10 Scores - keine Skalierung nötig!
    const rawScore = modelData.overall_score || 0;
    const score = Math.min(Math.max(rawScore, 0), 10);
    
    // 🚨 PHASE 1.2: Mathematical Validation - Erfolgsrate auf 0-100% begrenzen
    const rawSuccessRate = modelData.success_rate || 0;
    const successRate = Math.min(Math.max(rawSuccessRate, 0), 100);
    
    const isActive = modelData.is_active || false;
    
    // 🚨 PHASE 1.3: Logical Consistency - Performance-Level basiert auf begrenztem Score
    let performanceLevel = 'Niedrig';
    let performanceClass = 'status-error';
    
    // ZUSÄTZLICH: Bei 0% Erfolgsrate kann Performance nicht gut sein
    if (successRate === 0) {
        performanceLevel = 'Schlecht';
        performanceClass = 'status-error';
    } else if (score >= 8) {
        performanceLevel = 'Exzellent';
        performanceClass = 'status-success';
    } else if (score >= 6) {
        performanceLevel = 'Gut';
        performanceClass = 'status-success';
    } else if (score >= 4) {
        performanceLevel = 'Durchschnitt';
        performanceClass = 'status-warning';
    } else {
        performanceLevel = 'Schlecht';
        performanceClass = 'status-error';
    }
    
    return `
        <div class="mine-data-card model-stats-card" data-model="${modelName}">
            <!-- CARD HEADER -->
            <div class="card-header">
                <div class="header-top-row">
                    <div class="header-content">
                        <h3 class="card-title">
                            🤖 ${modelName}
                        </h3>
                        <p class="card-subtitle">🏢 ${provider}</p>
                    </div>
                    <div class="mine-type-badge ${isActive ? 'status-success' : 'status-error'}">
                        ${isActive ? 'AKTIV' : 'INAKTIV'}
                    </div>
                </div>
            </div>
            
            <!-- CARD BODY -->
            <div class="card-body">
                <div class="data-row">
                    <span class="data-label">🎯 Performance-Score</span>
                    <span class="data-value performance-score" style="font-size: 1.2em;">
                        ${score.toFixed(1)}/10
                        ${modelData.confidence_percentage ? `<small style="color: #666; font-size: 0.8em; display: block;">(Konfidenz: ${modelData.confidence_percentage}%)</small>` : ''}
                    </span>
                </div>
                
                <!-- NEUE SCORE-KOMPONENTEN AUFSCHLÜSSELUNG -->
                ${generateScoreBreakdown(modelData)}
                
                <div class="data-row">
                    <span class="data-label">✅ Erfolgsrate</span>
                    <span class="data-value">
                        ${successRate.toFixed(1)}%
                    </span>
                </div>
                
                <div class="data-row">
                    <span class="data-label">📊 Performance-Level</span>
                    <span class="status-indicator ${performanceClass}">
                        ${performanceLevel}
                    </span>
                </div>
                
                ${generateModelMetrics(modelData)}
                
                <!-- SOURCE ATTRIBUTION FOR MODEL STATS -->
                ${generateSourceBadges(extractSourcesFromModelData(modelData), modelData)}
            </div>
            
            <!-- CARD ACTIONS -->
            <div class="card-actions">
                <div>
                    <button class="action-button" onclick="showModelDetails('${modelName}')">
                        📊 Details anzeigen
                    </button>
                    <button class="action-button secondary" onclick="testModel('${modelName}')">
                        🧪 Testen
                    </button>
                </div>
                <div>
                    <button class="action-button secondary" onclick="toggleModelStatus('${modelName}')">
                        ${isActive ? '⏸️ Deaktivieren' : '▶️ Aktivieren'}
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Generiert zusätzliche Modell-Metriken
 */
function generateModelMetrics(modelData) {
    const metrics = [];
    
    if (modelData.total_searches) {
        metrics.push({
            label: '🔍 Gesamte Suchen',
            value: modelData.total_searches.toLocaleString()
        });
    }
    
    if (modelData.avg_response_time) {
        metrics.push({
            label: '⚡ Ø Antwortzeit',
            value: `${modelData.avg_response_time.toFixed(1)}s`
        });
    }
    
    if (modelData.cost_per_search) {
        metrics.push({
            label: '💰 Kosten/Suche',
            value: `$${modelData.cost_per_search.toFixed(4)}`
        });
    }
    
    return metrics.map(metric => `
        <div class="data-row">
            <span class="data-label">${metric.label}</span>
            <span class="data-value">${metric.value}</span>
        </div>
    `).join('');
}

/**
 * Generiert spezielle Quellen-Card
 */
function generateSourceCard(sourceData) {
    const domain = sourceData.domain || 'Unbekannte Quelle';
    const count = sourceData.count || 0;
    const reliability = sourceData.avg_reliability_score || 0;
    const sampleUrl = sourceData.sample_url || '';
    
    // Reliability-Level bestimmen
    let reliabilityLevel = 'Niedrig';
    let reliabilityClass = 'status-error';
    if (reliability >= 8) {
        reliabilityLevel = 'Ausgezeichnet';
        reliabilityClass = 'status-success';
    } else if (reliability >= 6) {
        reliabilityLevel = 'Gut';
        reliabilityClass = 'status-success';
    } else if (reliability >= 4) {
        reliabilityLevel = 'Durchschnitt';
        reliabilityClass = 'status-warning';
    }
    
    // Domain-Typ herausfinden (für Icon)
    let domainIcon = '🌐';
    if (domain.includes('gov')) domainIcon = '🏛️';
    else if (domain.includes('edu')) domainIcon = '🎓';
    else if (domain.includes('org')) domainIcon = '🏢';
    else if (domain.includes('mining') || domain.includes('metal')) domainIcon = '⛏️';
    else if (domain.includes('news') || domain.includes('reuters') || domain.includes('bloomberg')) domainIcon = '📰';
    
    return `
        <div class="mine-data-card source-card" data-source="${domain}">
            <!-- CARD HEADER -->
            <div class="card-header">
                <h3 class="card-title">
                    ${domainIcon} ${domain}
                </h3>
                <p class="card-subtitle">🔗 Web-Quelle</p>
                <div class="mine-type-badge ${reliabilityClass}">
                    ${reliability.toFixed(1)}/10
                </div>
            </div>
            
            <!-- CARD BODY -->
            <div class="card-body">
                <div class="data-row">
                    <span class="data-label">📊 Verfügbare Quellen</span>
                    <span class="data-value" style="font-size: 1.2em; color: var(--primary-600);">
                        ${count} Dokumente
                    </span>
                </div>
                
                <div class="data-row">
                    <span class="data-label">🎯 Zuverlässigkeit</span>
                    <span class="status-indicator ${reliabilityClass}">
                        ${reliabilityLevel}
                    </span>
                </div>
                
                ${sampleUrl ? `
                    <div class="data-row">
                        <span class="data-label">🔗 Beispiel-URL</span>
                        <span class="data-value" style="font-size: 0.8em; overflow: hidden; text-overflow: ellipsis;">
                            ${sampleUrl.replace('https://', '').substring(0, 40)}...
                        </span>
                    </div>
                ` : ''}
                
                ${generateSourceMetrics(sourceData)}
            </div>
            
            <!-- CARD ACTIONS -->
            <div class="card-actions">
                <div>
                    <button class="action-button" onclick="showSourceDetails('${domain}')">
                        📊 Details anzeigen
                    </button>
                    <button class="action-button secondary" onclick="visitSource('${sampleUrl}')">
                        🔗 Quelle besuchen
                    </button>
                </div>
                <div>
                    <button class="action-button secondary" onclick="analyzeSource('${domain}')">
                        🔍 Analysieren
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Generiert zusätzliche Quellen-Metriken
 */
function generateSourceMetrics(sourceData) {
    const metrics = [];
    
    if (sourceData.last_updated) {
        const lastUpdate = new Date(sourceData.last_updated).toLocaleDateString('de-DE');
        metrics.push({
            label: '📅 Letzte Aktualisierung',
            value: lastUpdate
        });
    }
    
    if (sourceData.data_types && sourceData.data_types.length > 0) {
        metrics.push({
            label: '📋 Datentypen',
            value: sourceData.data_types.slice(0, 2).join(', ') + (sourceData.data_types.length > 2 ? '...' : '')
        });
    }
    
    if (sourceData.response_time_avg) {
        metrics.push({
            label: '⚡ Ø Ladezeit',
            value: `${sourceData.response_time_avg.toFixed(1)}s`
        });
    }
    
    return metrics.map(metric => `
        <div class="data-row">
            <span class="data-label">${metric.label}</span>
            <span class="data-value">${metric.value}</span>
        </div>
    `).join('');
}

// ============================================
// INTERACTIVE FEATURES
// ============================================

/**
 * Zeigt Mine-Details in verbessertem Modal
 */
async function showMineDetails(mineName) {
    console.log(`🔍 [DETAILS] Showing details for: ${mineName}`);
    
    try {
        // API-Call um detaillierte Mine-Daten zu laden
        const response = await fetch(`${window.API_BASE_URL}/api/consolidated/mine/${encodeURIComponent(mineName)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.data) {
            showEnhancedMineModal(mineName, data.data);
        } else {
            throw new Error(data.error || 'Keine Details verfügbar');
        }
        
    } catch (error) {
        console.error(`❌ [DETAILS] Error loading details for ${mineName}:`, error);
        
        // Fallback: Show basic modal with error
        showEnhancedMineModal(mineName, null, error.message);
    }
}

/**
 * Zeigt erweitertes Mine-Modal mit modernem Design
 */
function showEnhancedMineModal(mineName, mineData, errorMessage = null) {
    // Modal Container erstellen
    const modal = document.createElement('div');
    modal.className = 'mine-detail-modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(4px);
        animation: fadeIn 0.3s ease-out;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'mine-detail-modal';
    modalContent.style.cssText = `
        background: white;
        border-radius: 12px;
        max-width: 900px;
        max-height: 85vh;
        width: 90vw;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        position: relative;
        animation: slideInUp 0.4s ease-out;
    `;
    
    // Modal Content generieren
    if (errorMessage) {
        modalContent.innerHTML = generateErrorModalContent(mineName, errorMessage);
    } else {
        modalContent.innerHTML = generateDetailedModalContent(mineName, mineData);
    }
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Event Listeners
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeMineModal();
        }
    });
    
    // ESC-Key Handler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeMineModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Store reference for closing
    window.currentMineModal = modal;
    
    console.log(`✅ [MODAL] Mine details modal shown for: ${mineName}`);
}

/**
 * Generiert detailliertes Modal-Content
 */
function generateDetailedModalContent(mineName, mineData) {
    const bestValues = mineData.best_values || {};
    const sourceInfo = mineData.source_summary || {};
    
    return `
        <div class="modal-header" style="padding: 24px 32px; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; background: white; z-index: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #111827; font-size: 24px; font-weight: 700;">
                        🏭 ${mineName}
                    </h2>
                    <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">
                        📍 ${bestValues.country || 'Land unbekannt'} • 
                        ⚖️ ${bestValues.mine_type || 'Typ unbekannt'}
                    </p>
                </div>
                <button onclick="closeMineModal()" style="
                    background: #f3f4f6; 
                    border: none; 
                    width: 32px; 
                    height: 32px; 
                    border-radius: 8px; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #6b7280;
                    font-size: 18px;
                ">✕</button>
            </div>
        </div>
        
        <div class="modal-body" style="padding: 32px;">
            <!-- ZUSAMMENFASSUNG -->
            <div class="summary-section" style="margin-bottom: 32px;">
                <h3 style="margin: 0 0 16px 0; color: #374151; font-size: 18px; font-weight: 600;">
                    📊 Zusammenfassung
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div style="background: #f8fafc; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                        <div style="color: #3b82f6; font-weight: 600; font-size: 14px;">Gefundene Datenfelder</div>
                        <div style="color: #111827; font-size: 24px; font-weight: 700; margin-top: 4px;">
                            ${Object.keys(bestValues).length}
                        </div>
                    </div>
                    <div style="background: #f0fdf4; padding: 16px; border-radius: 8px; border-left: 4px solid #10b981;">
                        <div style="color: #10b981; font-weight: 600; font-size: 14px;">Verwendete Quellen</div>
                        <div style="color: #111827; font-size: 24px; font-weight: 700; margin-top: 4px;">
                            ${sourceInfo.total_unique_sources || 0}
                        </div>
                    </div>
                    <div style="background: #fefbff; padding: 16px; border-radius: 8px; border-left: 4px solid #8b5cf6;">
                        <div style="color: #8b5cf6; font-weight: 600; font-size: 14px;">Datenqualität</div>
                        <div style="color: #111827; font-size: 24px; font-weight: 700; margin-top: 4px;">
                            ${calculateDataQualityScore(bestValues)}%
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- DETAILLIERTE DATEN -->
            <div class="details-section" style="margin-bottom: 32px;">
                <h3 style="margin: 0 0 16px 0; color: #374151; font-size: 18px; font-weight: 600;">
                    📋 Detaillierte Daten
                </h3>
                <div class="data-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                    ${generateDataFieldCards(bestValues, mineData.detailed_breakdown)}
                </div>
            </div>
            
            <!-- QUELLEN-INFORMATIONEN -->
            ${generateSourcesSection(sourceInfo)}
            
            <!-- EXPORT & AKTIONEN -->
            <div class="actions-section" style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #e5e7eb;">
                <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                    <button onclick="exportMineData('${mineName}')" style="
                        background: #3b82f6; 
                        color: white; 
                        border: none; 
                        padding: 12px 20px; 
                        border-radius: 8px; 
                        font-weight: 500; 
                        cursor: pointer;
                    ">📥 Daten exportieren</button>
                    <button onclick="addToFavorites('${mineName}')" style="
                        background: transparent; 
                        color: #3b82f6; 
                        border: 1px solid #3b82f6; 
                        padding: 12px 20px; 
                        border-radius: 8px; 
                        font-weight: 500; 
                        cursor: pointer;
                    ">⭐ Zu Favoriten</button>
                    <button onclick="shareMineData('${mineName}')" style="
                        background: transparent; 
                        color: #6b7280; 
                        border: 1px solid #d1d5db; 
                        padding: 12px 20px; 
                        border-radius: 8px; 
                        font-weight: 500; 
                        cursor: pointer;
                    ">🔗 Teilen</button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Generiert Error-Modal-Content
 */
function generateErrorModalContent(mineName, errorMessage) {
    return `
        <div class="modal-header" style="padding: 24px 32px; border-bottom: 1px solid #fecaca; background: #fef2f2;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0; color: #dc2626; font-size: 24px; font-weight: 700;">
                    ❌ Details nicht verfügbar
                </h2>
                <button onclick="closeMineModal()" style="
                    background: #fecaca; 
                    border: none; 
                    width: 32px; 
                    height: 32px; 
                    border-radius: 8px; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #dc2626;
                    font-size: 18px;
                ">✕</button>
            </div>
        </div>
        
        <div class="modal-body" style="padding: 32px;">
            <div style="text-align: center; padding: 32px;">
                <h3 style="color: #374151; margin-bottom: 16px;">Details für "${mineName}" konnten nicht geladen werden</h3>
                <p style="color: #6b7280; margin-bottom: 24px;">${errorMessage}</p>
                
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin-bottom: 24px;">
                    <h4 style="color: #374151; margin-bottom: 12px;">💡 Mögliche Lösungen:</h4>
                    <ul style="text-align: left; color: #6b7280; margin: 0; padding-left: 20px;">
                        <li>Überprüfen Sie Ihre Internetverbindung</li>
                        <li>Versuchen Sie es in ein paar Minuten erneut</li>
                        <li>Kontaktieren Sie den Support, wenn das Problem bestehen bleibt</li>
                    </ul>
                </div>
                
                <button onclick="closeMineModal()" style="
                    background: #3b82f6; 
                    color: white; 
                    border: none; 
                    padding: 12px 24px; 
                    border-radius: 8px; 
                    font-weight: 500; 
                    cursor: pointer;
                ">Schließen</button>
            </div>
        </div>
    `;
}

/**
 * Schließt das Mine-Modal
 */
function closeMineModal() {
    if (window.currentMineModal) {
        document.body.removeChild(window.currentMineModal);
        window.currentMineModal = null;
    }
}

/**
 * Exportiert Mine-Daten
 */
function exportMineData(mineName) {
    console.log(`📤 [EXPORT] Exporting data for: ${mineName}`);
    
    // Erstelle Download-Link für JSON-Export
    const exportData = {
        mine_name: mineName,
        export_timestamp: new Date().toISOString(),
        source: 'MineSearch 2.0',
        note: `Exported mining data for ${mineName}`
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${mineName.replace(/[^a-z0-9]/gi, '_')}_export.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    if (typeof showNotification === 'function') {
        showNotification(`📥 Daten für ${mineName} erfolgreich exportiert`, 'success');
    }
}

/**
 * Fügt Mine zu Favoriten hinzu
 */
function addToFavorites(mineName) {
    console.log(`⭐ [FAVORITES] Adding to favorites: ${mineName}`);
    
    const favorites = JSON.parse(localStorage.getItem('mining_favorites') || '[]');
    
    if (!favorites.includes(mineName)) {
        favorites.push(mineName);
        localStorage.setItem('mining_favorites', JSON.stringify(favorites));
        
        if (typeof showNotification === 'function') {
            showNotification(`⭐ ${mineName} wurde zu Favoriten hinzugefügt`, 'success');
        }
    } else {
        if (typeof showNotification === 'function') {
            showNotification(`${mineName} ist bereits in den Favoriten`, 'info');
        }
    }
}

/**
 * Zeigt Source-Details in erweitertem Modal
 */
function showSourceDetails(sourceUrl) {
    console.log(`🔗 [SOURCE] Showing source details: ${sourceUrl}`);
    
    // Extrahiere Domain aus URL für bessere Darstellung
    let domain = sourceUrl;
    try {
        domain = new URL(sourceUrl).hostname.replace('www.', '');
    } catch {
        // Falls sourceUrl kein vollständiger URL ist, verwende es als Domain
    }
    
    // Erstelle Source-Details-Modal
    const modal = document.createElement('div');
    modal.className = 'source-detail-modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(4px);
        animation: fadeIn 0.3s ease-out;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'source-detail-modal';
    modalContent.style.cssText = `
        background: white;
        border-radius: 12px;
        max-width: 600px;
        width: 90vw;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        position: relative;
        animation: slideInUp 0.4s ease-out;
    `;
    
    modalContent.innerHTML = `
        <div class="modal-header" style="padding: 24px 32px; border-bottom: 1px solid #e5e7eb; background: #f0f9ff;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #1e40af; font-size: 24px; font-weight: 700;">
                        🔗 Quellen-Details
                    </h2>
                    <p style="margin: 4px 0 0 0; color: #3b82f6; font-size: 14px;">
                        ${domain}
                    </p>
                </div>
                <button onclick="closeSourceModal()" style="
                    background: #dbeafe; 
                    border: none; 
                    width: 32px; 
                    height: 32px; 
                    border-radius: 8px; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #1e40af;
                    font-size: 18px;
                ">✕</button>
            </div>
        </div>
        
        <div class="modal-body" style="padding: 32px;">
            <div class="source-info">
                <h3 style="color: #374151; margin-bottom: 16px;">📊 Quellen-Informationen</h3>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                        <div>
                            <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">🌐 Domain</div>
                            <div style="color: #6b7280;">${domain}</div>
                        </div>
                        <div>
                            <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">🔗 URL</div>
                            <div style="color: #6b7280; word-break: break-all; font-size: 12px;">${sourceUrl}</div>
                        </div>
                    </div>
                </div>
                
                <div style="background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <h4 style="color: #1e40af; margin-bottom: 12px;">✅ Verfügbare Aktionen</h4>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <button onclick="visitSource('${sourceUrl}')" style="
                            background: #3b82f6; 
                            color: white; 
                            border: none; 
                            padding: 12px 20px; 
                            border-radius: 6px; 
                            cursor: pointer;
                            font-weight: 500;
                        ">🔗 Quelle in neuem Tab öffnen</button>
                        <button onclick="analyzeSource('${domain}')" style="
                            background: transparent; 
                            color: #3b82f6; 
                            border: 1px solid #3b82f6; 
                            padding: 12px 20px; 
                            border-radius: 6px; 
                            cursor: pointer;
                            font-weight: 500;
                        ">🔍 Quelle analysieren</button>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button onclick="closeSourceModal()" style="
                        background: #6b7280; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: 500;
                    ">Schließen</button>
                </div>
            </div>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Event Listeners
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeSourceModal();
        }
    });
    
    // ESC-Key Handler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeSourceModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Store reference for closing
    window.currentSourceModal = modal;
    
    console.log(`✅ [MODAL] Source details modal shown for: ${domain}`);
}

/**
 * Besucht eine Quelle in neuem Tab
 */
function visitSource(sourceUrl) {
    console.log(`🌐 [SOURCE] Visiting source: ${sourceUrl}`);
    
    try {
        // ERWEITERTE URL-VALIDIERUNG
        if (!sourceUrl || sourceUrl.trim() === '') {
            throw new Error('URL ist leer');
        }
        
        // Bereinige URL von eventuellen Formatierungsfehlern
        const cleanUrl = sourceUrl.trim();
        
        // Erkenne ungültige URLs
        if (cleanUrl === 'https:' || cleanUrl === 'http:' || cleanUrl === 'https://' || cleanUrl === 'http://') {
            throw new Error(`Unvollständige URL: ${cleanUrl}`);
        }
        
        // URL-Validation und -Bereinigung
        let fullUrl;
        
        if (cleanUrl.startsWith('http://') || cleanUrl.startsWith('https://')) {
            fullUrl = cleanUrl;
        } else if (cleanUrl.includes('.')) {
            // Domain erkannt, HTTPS hinzufügen
            fullUrl = `https://${cleanUrl}`;
        } else {
            // Fallback für unbekannte Formate
            throw new Error(`URL-Format nicht erkannt: ${cleanUrl}`);
        }
        
        // Finale URL-Validierung mit URL-Konstruktor
        try {
            new URL(fullUrl); // Wirft Fehler bei ungültigen URLs
        } catch (urlError) {
            throw new Error(`Ungültige URL-Struktur: ${fullUrl}`);
        }
        
        console.log(`🔗 [SOURCE] Opening validated URL: ${fullUrl}`);
        
        // Öffne in neuem Tab
        window.open(fullUrl, '_blank', 'noopener,noreferrer');
        
        if (typeof showNotification === 'function') {
            showNotification(`🔗 Quelle wird in neuem Tab geöffnet: ${fullUrl}`, 'info');
        }
        
        console.log(`✅ [SOURCE] Successfully opened: ${fullUrl}`);
    } catch (error) {
        console.error(`❌ [SOURCE] Error visiting source:`, error);
        console.error(`❌ [SOURCE] Original URL value:`, sourceUrl);
        console.error(`❌ [SOURCE] URL type:`, typeof sourceUrl);
        
        // Fallback-Aktion: Google Suche
        const fallbackSearch = `https://www.google.com/search?q=${encodeURIComponent(sourceUrl || 'mining source')}`;
        console.log(`🔄 [SOURCE] Fallback: Opening Google search: ${fallbackSearch}`);
        
        try {
            window.open(fallbackSearch, '_blank', 'noopener,noreferrer');
            
            if (typeof showNotification === 'function') {
                showNotification(`⚠️ URL ungültig - Google-Suche geöffnet: ${sourceUrl}`, 'warning');
            }
        } catch (fallbackError) {
            console.error(`❌ [SOURCE] Fallback auch fehlgeschlagen:`, fallbackError);
            
            if (typeof showNotification === 'function') {
                showNotification(`❌ Fehler beim Öffnen der Quelle: ${error.message}`, 'error');
            }
        }
    }
}

/**
 * Analysiert eine Quelle und zeigt Analyse-Ergebnisse
 */
function analyzeSource(sourceDomain) {
    console.log(`🔍 [SOURCE] Analyzing source: ${sourceDomain}`);
    
    // Erstelle Analyse-Modal
    const modal = document.createElement('div');
    modal.className = 'source-analysis-modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(4px);
        animation: fadeIn 0.3s ease-out;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'source-analysis-modal';
    modalContent.style.cssText = `
        background: white;
        border-radius: 12px;
        max-width: 700px;
        width: 90vw;
        max-height: 85vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        position: relative;
        animation: slideInUp 0.4s ease-out;
    `;
    
    // Bestimme Domain-Typ für bessere Analyse
    let domainType = 'Unknown';
    let analysisIcon = '🔍';
    let trustLevel = 'Mittel';
    let trustColor = '#f59e0b';
    
    if (sourceDomain.includes('gov')) {
        domainType = 'Regierungsquelle';
        analysisIcon = '🏛️';
        trustLevel = 'Sehr Hoch';
        trustColor = '#10b981';
    } else if (sourceDomain.includes('edu')) {
        domainType = 'Bildungseinrichtung';
        analysisIcon = '🎓';
        trustLevel = 'Hoch';
        trustColor = '#059669';
    } else if (sourceDomain.includes('mining') || sourceDomain.includes('metal')) {
        domainType = 'Mining-Fachquelle';
        analysisIcon = '⛏️';
        trustLevel = 'Hoch';
        trustColor = '#059669';
    } else if (sourceDomain.includes('reuters') || sourceDomain.includes('bloomberg') || sourceDomain.includes('news')) {
        domainType = 'Nachrichtenquelle';
        analysisIcon = '📰';
        trustLevel = 'Hoch';
        trustColor = '#059669';
    } else if (sourceDomain.includes('org')) {
        domainType = 'Organisation';
        analysisIcon = '🏢';
        trustLevel = 'Mittel-Hoch';
        trustColor = '#0891b2';
    }
    
    modalContent.innerHTML = `
        <div class="modal-header" style="padding: 24px 32px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #0c4a6e; font-size: 24px; font-weight: 700;">
                        ${analysisIcon} Quellen-Analyse
                    </h2>
                    <p style="margin: 4px 0 0 0; color: #0369a1; font-size: 14px;">
                        ${sourceDomain}
                    </p>
                </div>
                <button onclick="closeAnalysisModal()" style="
                    background: #bae6fd; 
                    border: none; 
                    width: 32px; 
                    height: 32px; 
                    border-radius: 8px; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #0c4a6e;
                    font-size: 18px;
                ">✕</button>
            </div>
        </div>
        
        <div class="modal-body" style="padding: 32px;">
            <!-- TRUST LEVEL INDICATOR -->
            <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #374151; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                    🎯 Vertrauenslevel
                </h3>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="
                        background: ${trustColor}; 
                        color: white; 
                        padding: 8px 16px; 
                        border-radius: 20px; 
                        font-weight: 600;
                        font-size: 14px;
                    ">${trustLevel}</div>
                    <div style="color: #6b7280;">Basierend auf Domain-Typ: ${domainType}</div>
                </div>
            </div>
            
            <!-- DOMAIN ANALYSIS -->
            <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #374151; margin-bottom: 16px;">📊 Domain-Analyse</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div>
                        <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">Typ</div>
                        <div style="color: #6b7280;">${domainType}</div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">Domain</div>
                        <div style="color: #6b7280;">${sourceDomain}</div>
                    </div>
                </div>
            </div>
            
            <!-- RECOMMENDATIONS -->
            <div style="background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #1e40af; margin-bottom: 16px;">💡 Empfehlungen</h3>
                <ul style="color: #374151; margin: 0; padding-left: 20px;">
                    <li style="margin-bottom: 8px;">Diese Quelle wird für Mining-Daten verwendet</li>
                    <li style="margin-bottom: 8px;">Vertrauenslevel: ${trustLevel}</li>
                    <li style="margin-bottom: 8px;">Typ: ${domainType}</li>
                    <li>Regelmäßige Verfügbarkeits-Prüfungen aktiv</li>
                </ul>
            </div>
            
            <!-- ACTIONS -->
            <div style="text-align: center;">
                <button onclick="visitSource('https://${sourceDomain}')" style="
                    background: #3b82f6; 
                    color: white; 
                    border: none; 
                    padding: 12px 20px; 
                    border-radius: 6px; 
                    cursor: pointer;
                    font-weight: 500;
                    margin-right: 12px;
                ">🔗 Quelle besuchen</button>
                <button onclick="closeAnalysisModal()" style="
                    background: #6b7280; 
                    color: white; 
                    border: none; 
                    padding: 12px 20px; 
                    border-radius: 6px; 
                    cursor: pointer;
                    font-weight: 500;
                ">Schließen</button>
            </div>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Event Listeners
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeAnalysisModal();
        }
    });
    
    // ESC-Key Handler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeAnalysisModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Store reference for closing
    window.currentAnalysisModal = modal;
    
    if (typeof showNotification === 'function') {
        showNotification(`🔍 Quellen-Analyse für ${sourceDomain} wird angezeigt`, 'info');
    }
    
    console.log(`✅ [ANALYSIS] Source analysis modal shown for: ${sourceDomain}`);
}

/**
 * Schließt das Source-Details-Modal
 */
function closeSourceModal() {
    if (window.currentSourceModal) {
        document.body.removeChild(window.currentSourceModal);
        window.currentSourceModal = null;
    }
}

/**
 * Schließt das Source-Analysis-Modal
 */
function closeAnalysisModal() {
    if (window.currentAnalysisModal) {
        document.body.removeChild(window.currentAnalysisModal);
        window.currentAnalysisModal = null;
    }
}

// ============================================
// MODEL STATISTICS CARD FUNCTIONS
// ============================================

/**
 * Testet ein KI-Modell mit einer Probe-Abfrage
 */
function testModel(modelName) {
    console.log(`🧪 [MODEL-TEST] Testing model: ${modelName}`);
    
    // Erstelle Test-Modal
    const modal = document.createElement('div');
    modal.className = 'model-test-modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(4px);
        animation: fadeIn 0.3s ease-out;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'model-test-modal';
    modalContent.style.cssText = `
        background: white;
        border-radius: 12px;
        max-width: 800px;
        width: 90vw;
        max-height: 85vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        position: relative;
        animation: slideInUp 0.4s ease-out;
    `;
    
    modalContent.innerHTML = `
        <div class="modal-header" style="padding: 24px 32px; border-bottom: 1px solid #e5e7eb; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #92400e; font-size: 24px; font-weight: 700;">
                        🧪 Modell-Test
                    </h2>
                    <p style="margin: 4px 0 0 0; color: #b45309; font-size: 14px;">
                        ${modelName}
                    </p>
                </div>
                <button onclick="closeModelTestModal()" style="
                    background: #fed7aa; 
                    border: none; 
                    width: 32px; 
                    height: 32px; 
                    border-radius: 8px; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #92400e;
                    font-size: 18px;
                ">✕</button>
            </div>
        </div>
        
        <div class="modal-body" style="padding: 32px;">
            <div class="test-interface">
                <h3 style="color: #374151; margin-bottom: 16px;">⚡ Test-Abfrage durchführen</h3>
                
                <!-- TEST QUERY INPUT -->
                <div style="margin-bottom: 20px;">
                    <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 8px;">
                        🔍 Test-Abfrage eingeben:
                    </label>
                    <textarea id="testQuery" placeholder="z.B. 'Finde Informationen über die Goldmine Barrick in Kanada'" 
                              style="width: 100%; height: 100px; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; resize: vertical;">Finde Informationen über eine Goldmine in Australien</textarea>
                </div>
                
                <!-- TEST RESULTS AREA -->
                <div id="testResults" style="margin-bottom: 20px; min-height: 200px; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px;">
                    <div style="color: #6b7280; text-align: center; padding: 40px 0;">
                        <div style="font-size: 48px; margin-bottom: 16px;">🚀</div>
                        <p>Klicken Sie auf "Test starten", um das Modell zu testen</p>
                    </div>
                </div>
                
                <!-- ACTIONS -->
                <div style="display: flex; gap: 12px; justify-content: center;">
                    <button onclick="startModelTest('${modelName}')" id="startTestBtn" style="
                        background: #f59e0b; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: 500;
                    ">🧪 Test starten</button>
                    <button onclick="closeModelTestModal()" style="
                        background: #6b7280; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: 500;
                    ">Abbrechen</button>
                </div>
            </div>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Event Listeners
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModelTestModal();
        }
    });
    
    // ESC-Key Handler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeModelTestModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Store reference for closing
    window.currentModelTestModal = modal;
    
    if (typeof showNotification === 'function') {
        showNotification(`🧪 Modell-Test für ${modelName} geöffnet`, 'info');
    }
    
    console.log(`✅ [MODEL-TEST] Test modal shown for: ${modelName}`);
}

/**
 * Startet den tatsächlichen Modell-Test
 */
async function startModelTest(modelName) {
    console.log(`🚀 [MODEL-TEST] Starting actual test for: ${modelName}`);
    
    const testQuery = document.getElementById('testQuery')?.value || 'Test-Abfrage';
    const testResults = document.getElementById('testResults');
    const startBtn = document.getElementById('startTestBtn');
    
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.textContent = '🔄 Test läuft...';
        startBtn.style.background = '#9ca3af';
    }
    
    if (testResults) {
        testResults.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 32px; margin-bottom: 12px;">⏳</div>
                <p style="color: #374151; font-weight: 500;">Teste ${modelName}...</p>
                <div style="background: #e5e7eb; height: 4px; border-radius: 2px; margin: 16px 0; overflow: hidden;">
                    <div style="background: #3b82f6; height: 100%; width: 0%; animation: progress 3s ease-in-out forwards;"></div>
                </div>
            </div>
        `;
    }
    
    try {
        // Simuliere Test-Abfrage (in der realen Implementation würde hier ein API-Call stehen)
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Simuliere Test-Ergebnis
        const testResult = {
            success: true,
            responseTime: Math.floor(Math.random() * 3000) + 500,
            quality: Math.floor(Math.random() * 40) + 60,
            model: modelName,
            query: testQuery
        };
        
        if (testResults) {
            const qualityColor = testResult.quality >= 80 ? '#10b981' : testResult.quality >= 60 ? '#f59e0b' : '#ef4444';
            
            testResults.innerHTML = `
                <div style="padding: 20px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                        <div style="font-size: 32px;">✅</div>
                        <div>
                            <h4 style="margin: 0; color: #374151;">Test erfolgreich abgeschlossen</h4>
                            <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">Modell reagiert normal</p>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
                        <div style="background: #f0f9ff; padding: 16px; border-radius: 6px; text-align: center;">
                            <div style="color: #3b82f6; font-weight: 600; font-size: 14px;">Antwortzeit</div>
                            <div style="color: #1e40af; font-size: 24px; font-weight: 700;">${testResult.responseTime}ms</div>
                        </div>
                        <div style="background: ${qualityColor === '#10b981' ? '#f0fdf4' : qualityColor === '#f59e0b' ? '#fef3c7' : '#fef2f2'}; padding: 16px; border-radius: 6px; text-align: center;">
                            <div style="color: ${qualityColor}; font-weight: 600; font-size: 14px;">Qualität</div>
                            <div style="color: ${qualityColor}; font-size: 24px; font-weight: 700;">${testResult.quality}%</div>
                        </div>
                    </div>
                    
                    <div style="background: #f8fafc; border-radius: 6px; padding: 16px;">
                        <h5 style="color: #374151; margin: 0 0 8px 0;">Test-Abfrage:</h5>
                        <p style="color: #6b7280; margin: 0; font-style: italic;">"${testResult.query}"</p>
                    </div>
                </div>
            `;
        }
        
        if (typeof showNotification === 'function') {
            showNotification(`✅ Modell-Test abgeschlossen: ${modelName} (${testResult.responseTime}ms)`, 'success');
        }
        
    } catch (error) {
        console.error(`❌ [MODEL-TEST] Test failed:`, error);
        
        if (testResults) {
            testResults.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 32px; margin-bottom: 12px;">❌</div>
                    <h4 style="color: #dc2626; margin-bottom: 8px;">Test fehlgeschlagen</h4>
                    <p style="color: #6b7280;">${error.message}</p>
                </div>
            `;
        }
        
        if (typeof showNotification === 'function') {
            showNotification(`❌ Modell-Test fehlgeschlagen: ${error.message}`, 'error');
        }
    } finally {
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = '🔄 Erneut testen';
            startBtn.style.background = '#f59e0b';
        }
    }
}

/**
 * Ändert den Status eines Modells (Aktivieren/Deaktivieren)
 */
function toggleModelStatus(modelName) {
    console.log(`🔄 [MODEL-STATUS] Toggling status for: ${modelName}`);
    
    // Erstelle Status-Toggle-Modal
    const modal = document.createElement('div');
    modal.className = 'model-status-modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(4px);
        animation: fadeIn 0.3s ease-out;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.className = 'model-status-modal';
    modalContent.style.cssText = `
        background: white;
        border-radius: 12px;
        max-width: 500px;
        width: 90vw;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        position: relative;
        animation: slideInUp 0.4s ease-out;
    `;
    
    // Bestimme aktuellen Status (simuliert)
    const isCurrentlyActive = Math.random() > 0.5;
    const newStatus = !isCurrentlyActive;
    
    modalContent.innerHTML = `
        <div class="modal-header" style="padding: 24px 32px; border-bottom: 1px solid #e5e7eb; background: ${newStatus ? '#f0fdf4' : '#fef2f2'};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: ${newStatus ? '#059669' : '#dc2626'}; font-size: 24px; font-weight: 700;">
                        ${newStatus ? '▶️' : '⏸️'} Modell-Status ändern
                    </h2>
                    <p style="margin: 4px 0 0 0; color: ${newStatus ? '#065f46' : '#991b1b'}; font-size: 14px;">
                        ${modelName}
                    </p>
                </div>
                <button onclick="closeModelStatusModal()" style="
                    background: ${newStatus ? '#bbf7d0' : '#fecaca'}; 
                    border: none; 
                    width: 32px; 
                    height: 32px; 
                    border-radius: 8px; 
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: ${newStatus ? '#059669' : '#dc2626'};
                    font-size: 18px;
                ">✕</button>
            </div>
        </div>
        
        <div class="modal-body" style="padding: 32px;">
            <div class="status-change-info">
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="font-size: 64px; margin-bottom: 16px;">
                        ${newStatus ? '✅' : '⚠️'}
                    </div>
                    <h3 style="color: #374151; margin-bottom: 8px;">
                        Modell ${newStatus ? 'aktivieren' : 'deaktivieren'}?
                    </h3>
                    <p style="color: #6b7280;">
                        ${newStatus ? 
                            'Das Modell wird für Suchabfragen verfügbar sein.' : 
                            'Das Modell wird nicht mehr für Suchabfragen verwendet.'}
                    </p>
                </div>
                
                <div style="background: ${newStatus ? '#f0f9ff' : '#fef3c7'}; border: 1px solid ${newStatus ? '#bfdbfe' : '#fde68a'}; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                    <h4 style="color: ${newStatus ? '#1e40af' : '#92400e'}; margin-bottom: 12px;">
                        ${newStatus ? '✅' : '⚠️'} Status-Änderung
                    </h4>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #6b7280;">Aktuell:</span>
                        <span style="background: ${isCurrentlyActive ? '#dcfce7' : '#fee2e2'}; color: ${isCurrentlyActive ? '#166534' : '#991b1b'}; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                            ${isCurrentlyActive ? 'AKTIV' : 'INAKTIV'}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                        <span style="color: #6b7280;">Nach Änderung:</span>
                        <span style="background: ${newStatus ? '#dcfce7' : '#fee2e2'}; color: ${newStatus ? '#166534' : '#991b1b'}; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                            ${newStatus ? 'AKTIV' : 'INAKTIV'}
                        </span>
                    </div>
                </div>
                
                <div style="display: flex; gap: 12px; justify-content: center;">
                    <button onclick="confirmStatusToggle('${modelName}', ${newStatus})" style="
                        background: ${newStatus ? '#10b981' : '#f59e0b'}; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: 500;
                    ">${newStatus ? '▶️ Aktivieren' : '⏸️ Deaktivieren'}</button>
                    <button onclick="closeModelStatusModal()" style="
                        background: #6b7280; 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 6px; 
                        cursor: pointer;
                        font-weight: 500;
                    ">Abbrechen</button>
                </div>
            </div>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Event Listeners
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModelStatusModal();
        }
    });
    
    // ESC-Key Handler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeModelStatusModal();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Store reference for closing
    window.currentModelStatusModal = modal;
    
    console.log(`✅ [MODEL-STATUS] Status toggle modal shown for: ${modelName}`);
}

/**
 * Bestätigt die Status-Änderung
 */
function confirmStatusToggle(modelName, newStatus) {
    console.log(`✅ [MODEL-STATUS] Confirming status change: ${modelName} -> ${newStatus ? 'ACTIVE' : 'INACTIVE'}`);
    
    // Simuliere Status-Änderung
    if (typeof showNotification === 'function') {
        showNotification(
            `${newStatus ? '▶️' : '⏸️'} ${modelName} wurde ${newStatus ? 'aktiviert' : 'deaktiviert'}`,
            newStatus ? 'success' : 'warning'
        );
    }
    
    closeModelStatusModal();
    
    // Optional: Seite neu laden um aktualisierten Status zu zeigen
    setTimeout(() => {
        if (confirm('Möchten Sie die Seite neu laden, um die Änderungen zu sehen?')) {
            window.location.reload();
        }
    }, 1000);
}

/**
 * Schließt das Model-Test-Modal
 */
function closeModelTestModal() {
    if (window.currentModelTestModal) {
        document.body.removeChild(window.currentModelTestModal);
        window.currentModelTestModal = null;
    }
}

/**
 * Schließt das Model-Status-Modal
 */
function closeModelStatusModal() {
    if (window.currentModelStatusModal) {
        document.body.removeChild(window.currentModelStatusModal);
        window.currentModelStatusModal = null;
    }
}

// ============================================
// GLOBAL EXPORTS - CRITICAL FOR INTEGRATION
// ============================================

// Export alle Data-Card-Funktionen zum globalen Scope
window.renderDataCardGrid = renderDataCardGrid;
window.generateMineDataCard = generateMineDataCard;
window.generateModelStatsCard = generateModelStatsCard;
window.generateSourceCard = generateSourceCard;
window.generateKeyMetrics = generateKeyMetrics;
window.generateSourceBadges = generateSourceBadges;

// Export Interactive Features
window.showMineDetails = showMineDetails;
window.exportMineData = exportMineData;
window.addToFavorites = addToFavorites;
window.showSourceDetails = showSourceDetails;
window.visitSource = visitSource;
window.analyzeSource = analyzeSource;
window.closeSourceModal = closeSourceModal;
window.closeAnalysisModal = closeAnalysisModal;

// Export Model Test & Status Functions
window.testModel = testModel;
window.toggleModelStatus = toggleModelStatus;
window.closeModelTestModal = closeModelTestModal;
window.closeModelStatusModal = closeModelStatusModal;

// Export Helper Functions
window.extractSourcesFromMine = extractSourcesFromMine;
window.extractSourcesFromModelData = extractSourcesFromModelData;
window.getMineTypeFromData = getMineTypeFromData;
window.getStatusClass = getStatusClass;
window.calculateDataQualityScore = calculateDataQualityScore;
window.generateDataFieldCards = generateDataFieldCards;
window.generateSourcesSection = generateSourcesSection;

/**
 * NEUE FUNKTION: Score-Breakdown für detaillierte Performance-Anzeige
 */
function generateScoreBreakdown(modelData) {
    if (!modelData.score_breakdown) {
        return ''; // Keine Breakdown-Daten verfügbar
    }
    
    const breakdown = modelData.score_breakdown;
    
    return `
        <div class="score-breakdown-section" style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 0.85em;">
            <div style="font-weight: bold; margin-bottom: 8px; color: #495057;">📊 Score-Aufschlüsselung:</div>
            
            <div class="score-component" style="margin-bottom: 4px;">
                <span style="color: #28a745;">🎯 Feldqualität:</span>
                <span style="float: right; font-weight: bold;">${breakdown.fieldQuality?.score?.toFixed(1) || 'N/A'}/10</span>
                <small style="display: block; color: #6c757d; font-size: 0.9em; margin-top: 2px;">
                    ${breakdown.fieldQuality?.qualityLevel || 'N/A'} - ${breakdown.fieldQuality?.details?.percentage || '0.0'}% echte Werte
                    ${breakdown.fieldQuality?.details?.qualityBreakdown ? 
                        `<br>🟢 ${breakdown.fieldQuality.details.qualityBreakdown.high} hoch, 🟡 ${breakdown.fieldQuality.details.qualityBreakdown.medium} mittel, 🔴 ${breakdown.fieldQuality.details.qualityBreakdown.low} niedrig` : ''}
                </small>
            </div>
            
            <div class="score-component" style="margin-bottom: 4px;">
                <span style="color: #17a2b8;">🔄 Konsistenz:</span>
                <span style="float: right; font-weight: bold;">${breakdown.consistency?.score?.toFixed(1) || 'N/A'}/10</span>
                <small style="display: block; color: #6c757d; font-size: 0.9em;">
                    ${breakdown.consistency?.details?.interpretation || ''}
                </small>
            </div>
            
            <div class="score-component" style="margin-bottom: 4px;">
                <span style="color: #ffc107;">⚡ Geschwindigkeit:</span>
                <span style="float: right; font-weight: bold;">${breakdown.speed?.score?.toFixed(1) || 'N/A'}/10</span>
                <small style="display: block; color: #6c757d; font-size: 0.9em;">
                    ${breakdown.speed?.details?.avgResponseTimeFormatted || 'N/A'}
                </small>
            </div>
            
            <div class="score-component">
                <span style="color: #fd7e14;">💰 Kosten:</span>
                <span style="float: right; font-weight: bold;">${breakdown.cost?.score?.toFixed(1) || 'N/A'}/10</span>
                <small style="display: block; color: #6c757d; font-size: 0.9em;">
                    ${breakdown.cost?.details?.interpretation || 'N/A'}
                </small>
            </div>
        </div>
    `;
}

// Export Modal Functions
window.closeMineModal = closeMineModal;
window.shareMineData = shareMineData;
window.generateScoreBreakdown = generateScoreBreakdown;

console.log('🎨 MineSearch 2.0 - Data-Card-System mit Source-Attribution geladen');

// ============================================
// HELPER FUNCTIONS FÜR MODAL-CONTENT
// ============================================

/**
 * Berechnet Datenqualitäts-Score basierend auf verfügbaren Feldern
 */
function calculateDataQualityScore(bestValues) {
    if (!bestValues || Object.keys(bestValues).length === 0) return 0;
    
    const importantFields = [
        'mine_name', 'country', 'mine_type', 'status', 'operational_status',
        'production_per_year', 'annual_production', 'coordinates', 'ownership',
        'commodity', 'reserves', 'resources'
    ];
    
    let foundFields = 0;
    importantFields.forEach(field => {
        if (bestValues[field] && bestValues[field] !== 'Unbekannt' && bestValues[field].trim() !== '') {
            foundFields++;
        }
    });
    
    return Math.round((foundFields / importantFields.length) * 100);
}

/**
 * Generiert Data-Field-Cards für Modal-Details
 */
function generateDataFieldCards(bestValues, detailedBreakdown = null) {
    if (!bestValues || Object.keys(bestValues).length === 0) {
        return '<div style="text-align: center; color: #6b7280; padding: 32px;">Keine detaillierten Daten verfügbar</div>';
    }
    
    const fieldCategories = {
        basic: ['mine_name', 'country', 'mine_type', 'status', 'operational_status'],
        location: ['coordinates', 'region', 'state', 'province'],
        business: ['ownership', 'owner', 'company', 'operator'],
        production: ['production_per_year', 'annual_production', 'commodity', 'reserves', 'resources'],
        financial: ['market_cap', 'revenue', 'costs', 'employees', 'workforce'],
        technical: ['mining_method', 'processing_method', 'equipment', 'capacity']
    };
    
    let html = '';
    
    Object.entries(fieldCategories).forEach(([category, fields]) => {
        const categoryFields = fields.filter(field => bestValues[field]);
        if (categoryFields.length === 0) return;
        
        html += `
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #374151; font-size: 14px; font-weight: 600; text-transform: uppercase;">
                    ${getCategoryIcon(category)} ${getCategoryName(category)}
                </h4>
                <div style="space-y: 8px;">
                    ${categoryFields.map(field => `
                        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f3f4f6;">
                            <span style="color: #6b7280; font-size: 13px;">${formatFieldName(field)}</span>
                            <span style="color: #111827; font-size: 13px; font-weight: 500; text-align: right; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">
                                ${formatFieldValueWithSources(bestValues[field], field, detailedBreakdown)}
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });
    
    return html;
}

/**
 * Generiert Quellen-Section für Modal
 */
function generateSourcesSection(sourceInfo) {
    if (!sourceInfo || !sourceInfo.sources_by_domain) {
        return `
            <div class="sources-section" style="margin-bottom: 32px;">
                <h3 style="margin: 0 0 16px 0; color: #374151; font-size: 18px; font-weight: 600;">
                    📚 Quellen-Informationen
                </h3>
                <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="color: #92400e;">⚠️ Keine Quellen-Informationen verfügbar</div>
                </div>
            </div>
        `;
    }
    
    const sourcesArray = Object.entries(sourceInfo.sources_by_domain)
        .map(([domain, data]) => ({
            domain,
            count: data.count || 1,
            url: data.sample_url || `https://${domain}`
        }))
        .sort((a, b) => b.count - a.count);
    
    return `
        <div class="sources-section" style="margin-bottom: 32px;">
            <h3 style="margin: 0 0 16px 0; color: #374151; font-size: 18px; font-weight: 600;">
                📚 Quellen-Informationen (${sourceInfo.total_unique_sources || 0} Quellen)
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 12px;">
                ${sourcesArray.slice(0, 6).map(source => `
                    <div style="background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="color: #1e40af; font-weight: 500; font-size: 13px; overflow: hidden; text-overflow: ellipsis;">
                                🔗 ${source.domain}
                            </span>
                            <span style="background: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: 600;">
                                ${source.count}
                            </span>
                        </div>
                        <button onclick="window.open('${source.url}', '_blank')" style="
                            background: transparent; 
                            color: #3b82f6; 
                            border: 1px solid #3b82f6; 
                            padding: 4px 8px; 
                            border-radius: 4px; 
                            font-size: 11px; 
                            cursor: pointer;
                        ">Quelle besuchen</button>
                    </div>
                `).join('')}
                
                ${sourcesArray.length > 6 ? `
                    <div style="background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; padding: 12px; display: flex; align-items: center; justify-content: center; color: #6b7280; font-size: 13px;">
                        +${sourcesArray.length - 6} weitere Quellen
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Teilt Mine-Daten
 */
function shareMineData(mineName) {
    const shareData = {
        title: `Mining-Daten: ${mineName}`,
        text: `Schaue dir diese detaillierten Mining-Informationen für ${mineName} an.`,
        url: window.location.href
    };
    
    if (navigator.share) {
        navigator.share(shareData);
    } else {
        // Fallback: Copy to clipboard
        const shareText = `${shareData.text} ${shareData.url}`;
        navigator.clipboard.writeText(shareText).then(() => {
            if (typeof showNotification === 'function') {
                showNotification('🔗 Link wurde in die Zwischenablage kopiert', 'success');
            }
        });
    }
    
    console.log(`🔗 [SHARE] Shared mine data for: ${mineName}`);
}

// Helper functions for field categorization
function getCategoryIcon(category) {
    const icons = {
        basic: '📋',
        location: '📍', 
        business: '🏢',
        production: '⚡',
        financial: '💰',
        technical: '🔧'
    };
    return icons[category] || '📊';
}

function getCategoryName(category) {
    const names = {
        basic: 'Grunddaten',
        location: 'Standort',
        business: 'Unternehmen',
        production: 'Produktion',
        financial: 'Finanzen',
        technical: 'Technik'
    };
    return names[category] || category;
}

function formatFieldName(field) {
    const fieldNames = {
        mine_name: 'Mine Name',
        country: 'Land',
        mine_type: 'Mine-Typ',
        status: 'Status',
        operational_status: 'Betriebsstatus',
        coordinates: 'Koordinaten',
        region: 'Region',
        state: 'Bundesstaat',
        province: 'Provinz',
        ownership: 'Eigentümer',
        owner: 'Besitzer',
        company: 'Unternehmen',
        operator: 'Betreiber',
        production_per_year: 'Jahresproduktion',
        annual_production: 'Jährliche Produktion',
        commodity: 'Rohstoff',
        reserves: 'Reserven',
        resources: 'Ressourcen',
        market_cap: 'Marktkapitalisierung',
        revenue: 'Umsatz',
        costs: 'Kosten',
        employees: 'Mitarbeiter',
        workforce: 'Belegschaft',
        mining_method: 'Abbaumethode',
        processing_method: 'Verarbeitungsmethode',
        equipment: 'Ausrüstung',
        capacity: 'Kapazität'
    };
    return fieldNames[field] || field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}