/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Data-Card-System mit Source-Attribution
 * 
 * PHASE 3: TABELLEN-REVOLUTION
 * Ersetzt hässliche HTML-Tabellen durch moderne, interaktive Data-Cards
 */

// ============================================
// MINE DATA-CARD GENERATION SYSTEM
// ============================================

/**
 * Generiert moderne Mine-Data-Card mit Source-Attribution
 */
function generateMineDataCard(mineData, cardType = 'consolidated') {
    const mineName = mineData.mine_name || 'Unbekannte Mine';
    const country = mineData.best_values?.country || mineData.country || 'Unbekannt';
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
                ${generateSourceBadges(sources)}
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
                value: values.mine_type
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
 */
function generateSourceBadges(sources) {
    if (!sources || sources.length === 0) {
        return `
            <div class="source-badges">
                <span class="source-badge source-count-badge">
                    ⚠️ Keine Quellen verfügbar
                </span>
            </div>
        `;
    }
    
    const displaySources = sources.slice(0, 3); // Max 3 sichtbare Quellen
    const remainingSources = sources.length - displaySources.length;
    
    let html = '<div class="source-badges">';
    
    displaySources.forEach(source => {
        html += `
            <span class="source-badge" onclick="showSourceDetails('${source.url}')" title="${source.name}">
                🔗 ${source.name}
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
    
    // Aus source_summary extrahieren (Consolidated Results)
    if (mineData.source_summary && mineData.source_summary.sources_by_domain) {
        Object.entries(mineData.source_summary.sources_by_domain).forEach(([domain, domainData]) => {
            sources.push({
                name: domain,
                url: domainData.sample_url || `https://${domain}`,
                count: domainData.count || 1
            });
        });
    }
    
    // Aus einzelnen search results extrahieren
    if (mineData.search_results) {
        mineData.search_results.forEach(result => {
            if (result.sources) {
                result.sources.forEach(source => {
                    sources.push({
                        name: extractDomainFromUrl(source),
                        url: source,
                        count: 1
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
        } else {
            acc.push(source);
        }
        return acc;
    }, []);
    
    return uniqueSources.sort((a, b) => b.count - a.count);
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
 */
function renderDataCardGrid(data, container, cardType = 'consolidated') {
    if (!container) return;
    
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
    const score = modelData.overall_score || 0;
    const successRate = modelData.success_rate || 0;
    const isActive = modelData.is_active || false;
    
    // Performance-Level bestimmen
    let performanceLevel = 'Niedrig';
    let performanceClass = 'status-error';
    if (score >= 8) {
        performanceLevel = 'Exzellent';
        performanceClass = 'status-success';
    } else if (score >= 6) {
        performanceLevel = 'Gut';
        performanceClass = 'status-success';
    } else if (score >= 4) {
        performanceLevel = 'Durchschnitt';
        performanceClass = 'status-warning';
    }
    
    return `
        <div class="mine-data-card model-stats-card" data-model="${modelName}">
            <!-- CARD HEADER -->
            <div class="card-header">
                <h3 class="card-title">
                    🤖 ${modelName}
                </h3>
                <p class="card-subtitle">🏢 ${provider}</p>
                <div class="mine-type-badge ${isActive ? 'status-success' : 'status-error'}">
                    ${isActive ? 'AKTIV' : 'INAKTIV'}
                </div>
            </div>
            
            <!-- CARD BODY -->
            <div class="card-body">
                <div class="data-row">
                    <span class="data-label">🎯 Performance-Score</span>
                    <span class="data-value performance-score" style="font-size: 1.2em; color: var(--primary-600);">
                        ${score.toFixed(1)}/10
                    </span>
                </div>
                
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
function showMineDetails(mineName) {
    console.log(`🔍 [DETAILS] Showing details for: ${mineName}`);
    // Implementation wird in nächstem Schritt hinzugefügt
}

/**
 * Exportiert Mine-Daten
 */
function exportMineData(mineName) {
    console.log(`📤 [EXPORT] Exporting data for: ${mineName}`);
    // Implementation wird in nächstem Schritt hinzugefügt
}

/**
 * Fügt Mine zu Favoriten hinzu
 */
function addToFavorites(mineName) {
    console.log(`⭐ [FAVORITES] Adding to favorites: ${mineName}`);
    // Implementation wird in nächstem Schritt hinzugefügt
}

/**
 * Zeigt Source-Details
 */
function showSourceDetails(sourceUrl) {
    console.log(`🔗 [SOURCE] Showing source details: ${sourceUrl}`);
    // Modal mit Source-Informationen öffnen
}