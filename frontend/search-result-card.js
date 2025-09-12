/**
 * Author: rahn
 * Datum: 11.09.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.1 - Kompakte SearchResult Card Komponente
 * 
 * Ersetzt die überladene Multi-Model-Comparison-Anzeige durch eine
 * saubere, nutzerfreundliche Karten-Ansicht mit 3-Ebenen-Layout.
 */

// ============================================
// SEARCH RESULT CARD GENERATION
// ============================================

/**
 * Hauptfunktion: Generiert kompakte Mine-Karte aus Multi-Model-Vergleich
 */
function generateSearchResultCard(comparisonResult, expandedCards = new Set()) {
    const mineName = comparisonResult.mine_name || 'Unbekannte Mine';
    const isExpanded = expandedCards.has(mineName);
    
    // Extrahiere Tier-1 Daten (wichtigste Informationen)
    const tier1Data = extractTier1Data(comparisonResult);
    
    // Extrahiere Tier-2 Daten (erweiterte Details)
    const tier2Data = extractTier2Data(comparisonResult);
    
    // Berechne Datenqualität
    const qualityScore = calculateCardQualityScore(comparisonResult);
    
    return `
        <div class="search-result-card ${qualityScore >= 70 ? 'high-quality' : qualityScore >= 40 ? 'medium-quality' : 'low-quality'}" 
             data-mine="${mineName}">
            
            <!-- TIER 1: KOMPAKTE ÜBERSICHT -->
            <div class="card-tier-1">
                <div class="mine-header">
                    <h3 class="mine-name">🏭 ${mineName}</h3>
                    <div class="quality-indicator" title="Datenqualität: ${qualityScore}%">
                        ${getQualityBadge(qualityScore)}
                    </div>
                </div>
                
                <div class="key-metrics">
                    ${generateKeyMetrics(tier1Data)}
                </div>
                
                <div class="card-actions">
                    <button class="expand-button" onclick="toggleCardExpansion('${mineName}')" 
                            aria-label="${isExpanded ? 'Weniger Details' : 'Mehr Details'}">
                        ${isExpanded ? '▲ Weniger' : '▼ Mehr Details'}
                    </button>
                    <button class="action-button secondary" onclick="exportMineData('${mineName}')">
                        📤 Export
                    </button>
                </div>
            </div>
            
            <!-- TIER 2: ERWEITERTE DETAILS (kollabierbar) -->
            ${isExpanded ? `
                <div class="card-tier-2">
                    <div class="extended-data">
                        ${generateExtendedData(tier2Data)}
                    </div>
                    
                    <div class="technical-actions">
                        <button class="action-button" onclick="showDetailedAnalysis('${mineName}')">
                            🔬 Technische Analyse
                        </button>
                        <button class="action-button secondary" onclick="showModelComparison('${mineName}')">
                            📊 Modell-Vergleich
                        </button>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * TIER-1 DATA EXTRACTION: Extrahiert wichtigste Informationen
 */
function extractTier1Data(comparisonResult) {
    const consensus = comparisonResult.consensus || {};
    const strongConsensus = consensus.fields || {};
    
    return {
        country: getBestValue(strongConsensus, 'Country') || 'Unbekannt',
        region: getBestValue(strongConsensus, 'Region') || '',
        commodity: getBestValue(strongConsensus, 'Rohstoff') || 'Unbekannt',
        production: getBestProductionValue(comparisonResult) || 'Unbekannt',
        status: getBestValue(strongConsensus, 'Aktivitätsstatus') || 'Unbekannt',
        mineType: getBestValue(strongConsensus, 'Minentyp') || 'Unbekannt'
    };
}

/**
 * TIER-2 DATA EXTRACTION: Extrahiert erweiterte Informationen
 */
function extractTier2Data(comparisonResult) {
    const consensus = comparisonResult.consensus || {};
    const strongConsensus = consensus.fields || {};
    
    return {
        owner: getBestValue(strongConsensus, 'Eigentümer') || 'Unbekannt',
        operator: getBestValue(strongConsensus, 'Betreiber') || 'Unbekannt',
        coordinates: getCoordinatesValue(strongConsensus) || 'Unbekannt',
        productionStart: getBestValue(strongConsensus, 'Produktionsstart') || 'Unbekannt',
        productionEnd: getBestValue(strongConsensus, 'Produktionsende') || '',
        area: getBestValue(strongConsensus, 'Fläche der Mine in qkm') || 'Unbekannt',
        restorationCosts: getBestValue(strongConsensus, 'Restaurationskosten') || 'Unbekannt'
    };
}

/**
 * BEST VALUE EXTRACTION: Holt besten verfügbaren Wert für ein Feld
 */
function getBestValue(consensusFields, fieldName) {
    if (consensusFields[fieldName] && consensusFields[fieldName].value) {
        return consensusFields[fieldName].value;
    }
    return null;
}

/**
 * PRODUCTION VALUE: Spezielle Behandlung für Produktionswerte
 */
function getBestProductionValue(comparisonResult) {
    const consensus = comparisonResult.consensus?.fields || {};
    
    // Priorisiere "Fördermenge/Jahr Rohstoff" für numerische Werte
    const productionRohstoff = getBestValue(consensus, 'Fördermenge/Jahr Rohstoff');
    if (productionRohstoff && /\d/.test(productionRohstoff)) {
        const commodity = getBestValue(consensus, 'Rohstoff') || '';
        return commodity ? `${productionRohstoff} ${commodity}` : productionRohstoff;
    }
    
    // Fallback auf "Fördermenge/Jahr"
    const production = getBestValue(consensus, 'Fördermenge/Jahr');
    if (production && /\d/.test(production)) {
        return production;
    }
    
    return null;
}

/**
 * COORDINATES VALUE: Formatiert Koordinaten
 */
function getCoordinatesValue(consensusFields) {
    const xCoord = getBestValue(consensusFields, 'x-Koordinate');
    const yCoord = getBestValue(consensusFields, 'y-Koordinate');
    
    if (xCoord && yCoord) {
        return `${parseFloat(xCoord).toFixed(2)}, ${parseFloat(yCoord).toFixed(2)}`;
    }
    return null;
}

/**
 * KEY METRICS GENERATION: Generiert Tier-1 Metriken-HTML
 */
function generateKeyMetrics(tier1Data) {
    const location = tier1Data.region ? 
        `${tier1Data.country}, ${tier1Data.region}` : 
        tier1Data.country;
    
    const mineTypeIcon = getMineTypeIcon(tier1Data.mineType);
    const statusIcon = getStatusIcon(tier1Data.status);
    
    return `
        <div class="metric-row location">
            <span class="metric-icon">📍</span>
            <span class="metric-value">${location}</span>
        </div>
        
        <div class="metric-row mine-info">
            <span class="metric-icon">${mineTypeIcon}</span>
            <span class="metric-value">${tier1Data.commodity}-Mine (${tier1Data.mineType})</span>
        </div>
        
        <div class="metric-row production">
            <span class="metric-icon">📊</span>
            <span class="metric-value">${tier1Data.production}</span>
        </div>
        
        <div class="metric-row status">
            <span class="metric-icon">${statusIcon}</span>
            <span class="metric-value status-${tier1Data.status.toLowerCase()}">${tier1Data.status}</span>
        </div>
    `;
}

/**
 * EXTENDED DATA GENERATION: Generiert Tier-2 erweiterte Daten
 */
function generateExtendedData(tier2Data) {
    const rows = [];
    
    if (tier2Data.owner !== 'Unbekannt') {
        rows.push(`
            <div class="extended-row">
                <span class="extended-label">🏢 Eigentümer:</span>
                <span class="extended-value">${tier2Data.owner}</span>
            </div>
        `);
    }
    
    if (tier2Data.operator !== 'Unbekannt' && tier2Data.operator !== tier2Data.owner) {
        rows.push(`
            <div class="extended-row">
                <span class="extended-label">⚙️ Betreiber:</span>
                <span class="extended-value">${tier2Data.operator}</span>
            </div>
        `);
    }
    
    if (tier2Data.coordinates !== 'Unbekannt') {
        rows.push(`
            <div class="extended-row">
                <span class="extended-label">🗺️ Koordinaten:</span>
                <span class="extended-value">${tier2Data.coordinates}</span>
            </div>
        `);
    }
    
    if (tier2Data.productionStart !== 'Unbekannt') {
        const timeline = tier2Data.productionEnd ? 
            `${tier2Data.productionStart} - ${tier2Data.productionEnd}` :
            `seit ${tier2Data.productionStart}`;
        
        rows.push(`
            <div class="extended-row">
                <span class="extended-label">📅 Produktion:</span>
                <span class="extended-value">${timeline}</span>
            </div>
        `);
    }
    
    if (tier2Data.area !== 'Unbekannt') {
        rows.push(`
            <div class="extended-row">
                <span class="extended-label">📏 Fläche:</span>
                <span class="extended-value">${tier2Data.area}</span>
            </div>
        `);
    }
    
    if (tier2Data.restorationCosts !== 'Unbekannt') {
        rows.push(`
            <div class="extended-row">
                <span class="extended-label">💰 Restaurationskosten:</span>
                <span class="extended-value">${tier2Data.restorationCosts}</span>
            </div>
        `);
    }
    
    return rows.join('') || '<div class="no-extended-data">Keine weiteren Details verfügbar</div>';
}

/**
 * QUALITY SCORE: Berechnet Datenqualitäts-Score für die Karte
 */
function calculateCardQualityScore(comparisonResult) {
    if (!comparisonResult || !comparisonResult.consensus) {
        return 0;
    }
    
    const consensus = comparisonResult.consensus;
    const totalFields = Object.keys(consensus.fields || {}).length;
    const strongConsensusCount = (consensus.strongConsensus || []).length;
    
    if (totalFields === 0) return 0;
    
    const consensusRatio = strongConsensusCount / totalFields;
    const overallScore = consensus.overallScore || 0;
    
    return Math.round((consensusRatio * 0.6 + overallScore * 0.4) * 100);
}

/**
 * UTILITY FUNCTIONS: Icons und Badges
 */
function getMineTypeIcon(mineType) {
    const type = (mineType || '').toLowerCase();
    if (type.includes('untertage') || type.includes('underground')) return '⬇️';
    if (type.includes('tagebau') || type.includes('open pit')) return '🏔️';
    return '⚒️';
}

function getStatusIcon(status) {
    const statusLower = (status || '').toLowerCase();
    if (statusLower.includes('aktiv') || statusLower.includes('active')) return '✅';
    if (statusLower.includes('geschlossen') || statusLower.includes('closed')) return '❌';
    if (statusLower.includes('geplant') || statusLower.includes('planned')) return '🚧';
    return '❓';
}

function getQualityBadge(score) {
    if (score >= 80) return `<span class="quality-badge excellent">${score}%</span>`;
    if (score >= 60) return `<span class="quality-badge good">${score}%</span>`;
    if (score >= 40) return `<span class="quality-badge fair">${score}%</span>`;
    return `<span class="quality-badge poor">${score}%</span>`;
}

// ============================================
// CARD INTERACTION HANDLERS
// ============================================

// Globaler State für expandierte Karten
let expandedCards = new Set();

/**
 * CARD EXPANSION: Toggle Karten-Erweiterung
 */
function toggleCardExpansion(mineName) {
    if (expandedCards.has(mineName)) {
        expandedCards.delete(mineName);
    } else {
        expandedCards.add(mineName);
    }
    
    // Re-render der Karte
    const cardElement = document.querySelector(`[data-mine="${mineName}"]`);
    if (cardElement && window.lastComparisonResult) {
        cardElement.outerHTML = generateSearchResultCard(window.lastComparisonResult, expandedCards);
    }
}

/**
 * DETAILED ANALYSIS: Zeigt Tier-3 technische Analyse
 */
function showDetailedAnalysis(mineName) {
    // Zeige detaillierte Multi-Model-Analyse in einem Modal
    if (window.lastComparisonResult) {
        showTechnicalAnalysisModal(window.lastComparisonResult, mineName);
    }
}

/**
 * MODEL COMPARISON: Zeigt Model-zu-Model Vergleich
 */
function showModelComparison(mineName) {
    // Zeige Model-Comparison in einem separaten Tab/Modal
    if (window.lastComparisonResult) {
        showModelComparisonModal(window.lastComparisonResult, mineName);
    }
}

// Export der Hauptfunktionen
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateSearchResultCard,
        toggleCardExpansion,
        showDetailedAnalysis,
        showModelComparison
    };
}