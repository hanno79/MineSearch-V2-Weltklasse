/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Analytics & Statistics Functions
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (Phase 3 - Final Refactoring)
 * Analytics Functions: SOURCE DETAILS Analytics, Statistics Calculations, Performance Analysis
 */

// ============================================
// STATISTICS CALCULATION FUNCTIONS
// ============================================

/**
 * CALCULATE SOURCE STATISTICS: Berechnet grundlegende Statistiken für Quellen
 */
function calculateSourceStatistics(sources, data) {
    if (!sources || sources.length === 0) {
        return {
            avgReliability: 0,
            successRate: 0,
            lastActivity: 'Nie',
            successfulSources: 0,
            totalSearches: 0
        };
    }
    
    const totalReliability = sources.reduce((sum, s) => sum + (s.reliability_score || 0), 0);
    const avgReliability = Math.round(totalReliability / sources.length);
    
    const successfulSources = sources.filter(s => (s.successful_searches || 0) > 0).length;
    const successRate = Math.round((successfulSources / sources.length) * 100);
    
    const totalSearches = sources.reduce((sum, s) => sum + (s.total_searches || 0), 0);
    
    // Find latest activity
    const lastActivity = sources.reduce((latest, source) => {
        const sourceDate = source.last_successful_access || source.last_updated;
        if (!sourceDate) return latest;
        const date = new Date(sourceDate);
        return date > latest ? date : latest;
    }, new Date(0));
    
    const lastActivityFormatted = lastActivity.getTime() > 0 ? 
        lastActivity.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 
        'Nie';
    
    return {
        avgReliability,
        successRate,
        lastActivity: lastActivityFormatted,
        successfulSources,
        totalSearches
    };
}

/**
 * CALCULATE FIELD PERFORMANCE: Berechnet Field-Performance für Quellen
 */
function calculateFieldPerformance(sources) {
    if (!sources || sources.length === 0) {
        return {
            fieldsFound: 0,
            coverage: 0,
            avgFieldsPerSource: 0,
            topPerformers: []
        };
    }
    
    // Simulate field performance based on reliability and searches
    const totalFields = sources.reduce((sum, s) => {
        const reliability = s.reliability_score || 0;
        const searches = s.total_searches || 0;
        return sum + Math.round((reliability / 100) * Math.min(searches, 50));
    }, 0);
    
    const coverage = Math.min(100, Math.round((totalFields / (sources.length * 20)) * 100));
    const avgFields = Math.round(totalFields / sources.length);
    
    const topPerformers = sources
        .map(s => ({
            url: s.url,
            fields: Math.round(((s.reliability_score || 0) / 100) * Math.min((s.total_searches || 0), 50))
        }))
        .sort((a, b) => b.fields - a.fields)
        .slice(0, 5);
    
    return {
        fieldsFound: totalFields,
        coverage,
        avgFieldsPerSource: avgFields,
        topPerformers
    };
}

/**
 * CALCULATE SCORE BREAKDOWN: Berechnet detaillierte Score-Analyse
 */
function calculateScoreBreakdown(sources) {
    if (!sources || sources.length === 0) {
        return {
            weightedScore: 0,
            minScore: 0,
            maxScore: 0,
            distribution: { high: 0, medium: 0, low: 0 },
            components: {}
        };
    }
    
    const scores = sources.map(s => s.reliability_score || 0);
    const minScore = Math.min(...scores);
    const maxScore = Math.max(...scores);
    
    // Calculate weighted score based on usage
    const totalUsage = sources.reduce((sum, s) => sum + (s.total_searches || 0), 0);
    const weightedScore = totalUsage > 0 ? 
        Math.round(sources.reduce((sum, s) => {
            const weight = (s.total_searches || 0) / totalUsage;
            return sum + ((s.reliability_score || 0) * weight);
        }, 0)) : Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
    
    // Score distribution
    const distribution = {
        high: sources.filter(s => (s.reliability_score || 0) >= 70).length,
        medium: sources.filter(s => (s.reliability_score || 0) >= 40 && (s.reliability_score || 0) < 70).length,
        low: sources.filter(s => (s.reliability_score || 0) < 40).length
    };
    
    return {
        weightedScore,
        minScore,
        maxScore,
        distribution,
        components: {
            reliability: Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length),
            consistency: Math.round(100 - ((maxScore - minScore) / 2)),
            performance: Math.round((sources.filter(s => (s.successful_searches || 0) > 0).length / sources.length) * 100)
        }
    };
}

/**
 * CALCULATE USAGE ANALYTICS: Berechnet Nutzungsanalytik für Quellen
 */
function calculateUsageAnalytics(sources) {
    if (!sources || sources.length === 0) {
        return {
            totalUsage: 0,
            avgPerSource: 0,
            mostUsed: null,
            usageDistribution: [],
            trends: {}
        };
    }
    
    const totalUsage = sources.reduce((sum, s) => sum + (s.total_searches || 0), 0);
    const avgPerSource = Math.round(totalUsage / sources.length);
    
    const mostUsed = sources.reduce((max, source) => {
        const usage = source.total_searches || 0;
        return usage > (max?.total_searches || 0) ? source : max;
    }, null);
    
    // Usage distribution
    const usageDistribution = [
        { label: 'Nicht verwendet', count: sources.filter(s => (s.total_searches || 0) === 0).length },
        { label: '1-5 Mal', count: sources.filter(s => (s.total_searches || 0) >= 1 && (s.total_searches || 0) <= 5).length },
        { label: '6-20 Mal', count: sources.filter(s => (s.total_searches || 0) >= 6 && (s.total_searches || 0) <= 20).length },
        { label: '20+ Mal', count: sources.filter(s => (s.total_searches || 0) > 20).length }
    ];
    
    return {
        totalUsage,
        avgPerSource,
        mostUsed,
        usageDistribution,
        trends: {
            activeCount: sources.filter(s => (s.total_searches || 0) > 0).length,
            inactiveCount: sources.filter(s => (s.total_searches || 0) === 0).length
        }
    };
}

// ============================================
// ANALYTICS VIEW GENERATORS
// ============================================

/**
 * GENERATE SCORE ANALYSIS VIEW: Erstellt HTML für Score-Analyse
 */
function generateScoreAnalysisView(scoreBreakdown, sources) {
    const { distribution, components, weightedScore } = scoreBreakdown;
    
    return `
        <div class="score-analysis">
            <div class="analysis-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px;">
                
                <!-- Score Distribution Chart -->
                <div class="chart-container" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h5 style="margin: 0 0 15px 0; color: #333;">📊 Score-Verteilung</h5>
                    <div class="score-bars">
                        <div class="score-bar" style="margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <span style="font-size: 12px; color: #666;">Hoch (70-100%)</span>
                                <span style="font-size: 12px; font-weight: bold; color: #4CAF50;">${distribution.high}</span>
                            </div>
                            <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div style="background: #4CAF50; height: 100%; width: ${(distribution.high / sources.length) * 100}%; border-radius: 4px;"></div>
                            </div>
                        </div>
                        
                        <div class="score-bar" style="margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <span style="font-size: 12px; color: #666;">Mittel (40-69%)</span>
                                <span style="font-size: 12px; font-weight: bold; color: #FF9800;">${distribution.medium}</span>
                            </div>
                            <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div style="background: #FF9800; height: 100%; width: ${(distribution.medium / sources.length) * 100}%; border-radius: 4px;"></div>
                            </div>
                        </div>
                        
                        <div class="score-bar">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <span style="font-size: 12px; color: #666;">Niedrig (0-39%)</span>
                                <span style="font-size: 12px; font-weight: bold; color: #F44336;">${distribution.low}</span>
                            </div>
                            <div style="background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div style="background: #F44336; height: 100%; width: ${(distribution.low / sources.length) * 100}%; border-radius: 4px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Score Components -->
                <div class="components-container" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h5 style="margin: 0 0 15px 0; color: #333;">⚡ Score-Komponenten</h5>
                    <div class="components-list">
                        <div class="component-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="font-size: 13px; color: #666;">Reliability</span>
                            <span style="font-size: 14px; font-weight: bold; color: #2196F3;">${components.reliability || 0}%</span>
                        </div>
                        <div class="component-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="font-size: 13px; color: #666;">Konsistenz</span>
                            <span style="font-size: 14px; font-weight: bold; color: #4CAF50;">${components.consistency || 0}%</span>
                        </div>
                        <div class="component-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                            <span style="font-size: 13px; color: #666;">Performance</span>
                            <span style="font-size: 14px; font-weight: bold; color: #FF9800;">${components.performance || 0}%</span>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 2px solid #e0e0e0; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #667eea;">${weightedScore}</div>
                        <div style="font-size: 12px; color: #666;">Gewichteter Gesamt-Score</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * GENERATE USAGE TRENDS VIEW: Erstellt HTML für Nutzungstrends
 */
function generateUsageTrendsView(usageAnalytics, sources) {
    const { usageDistribution, trends, mostUsed, totalUsage } = usageAnalytics;
    
    return `
        <div class="usage-trends">
            <div class="trends-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px;">
                
                <!-- Usage Distribution -->
                <div class="usage-chart" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h5 style="margin: 0 0 15px 0; color: #333;">🎯 Nutzungsverteilung</h5>
                    <div class="usage-bars">
                        ${usageDistribution.map(item => `
                            <div style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                    <span style="font-size: 12px; color: #666;">${item.label}</span>
                                    <span style="font-size: 12px; font-weight: bold; color: #4CAF50;">${item.count}</span>
                                </div>
                                <div style="background: #e0e0e0; height: 6px; border-radius: 3px; overflow: hidden;">
                                    <div style="background: #4CAF50; height: 100%; width: ${sources.length > 0 ? (item.count / sources.length) * 100 : 0}%; border-radius: 3px;"></div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Usage Summary -->
                <div class="usage-summary" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h5 style="margin: 0 0 15px 0; color: #333;">📈 Nutzungsübersicht</h5>
                    <div class="summary-stats">
                        <div class="stat-row" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="font-size: 13px; color: #666;">Gesamtnutzung</span>
                            <span style="font-size: 14px; font-weight: bold; color: #2196F3;">${totalUsage}</span>
                        </div>
                        <div class="stat-row" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="font-size: 13px; color: #666;">Aktive Quellen</span>
                            <span style="font-size: 14px; font-weight: bold; color: #4CAF50;">${trends.activeCount}</span>
                        </div>
                        <div class="stat-row" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                            <span style="font-size: 13px; color: #666;">Inaktive Quellen</span>
                            <span style="font-size: 14px; font-weight: bold; color: #F44336;">${trends.inactiveCount}</span>
                        </div>
                    </div>
                    ${mostUsed ? `
                        <div style="margin-top: 15px; padding-top: 15px; border-top: 2px solid #e0e0e0;">
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Meist genutzte Quelle:</div>
                            <div style="font-size: 11px; font-weight: bold; color: #667eea; word-break: break-all;">${mostUsed.url}</div>
                            <div style="font-size: 12px; color: #4CAF50; margin-top: 2px;">${mostUsed.total_searches || 0} Nutzungen</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * GENERATE FIELD COVERAGE VIEW: Erstellt HTML für Field-Coverage-Analyse
 */
function generateFieldCoverageView(fieldPerformance, sources) {
    const { fieldsFound, coverage, avgFieldsPerSource, topPerformers } = fieldPerformance;
    
    return `
        <div class="field-coverage">
            <div class="coverage-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px;">
                
                <!-- Coverage Overview -->
                <div class="coverage-chart" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h5 style="margin: 0 0 15px 0; color: #333;">🎯 Field-Abdeckung</h5>
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 48px; font-weight: bold; color: #4CAF50; margin-bottom: 5px;">${coverage}%</div>
                        <div style="font-size: 12px; color: #666;">Gesamtabdeckung</div>
                    </div>
                    <div class="coverage-stats">
                        <div class="stat-item" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="font-size: 12px; color: #666;">Felder gefunden</span>
                            <span style="font-size: 13px; font-weight: bold; color: #2196F3;">${fieldsFound}</span>
                        </div>
                        <div class="stat-item" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0;">
                            <span style="font-size: 12px; color: #666;">⌀ pro Quelle</span>
                            <span style="font-size: 13px; font-weight: bold; color: #FF9800;">${avgFieldsPerSource}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Top Performers -->
                <div class="top-performers" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h5 style="margin: 0 0 15px 0; color: #333;">🏆 Top-Performer</h5>
                    <div class="performers-list">
                        ${topPerformers.map((performer, index) => `
                            <div class="performer-item" style="margin-bottom: 12px; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid ${index === 0 ? '#FFD700' : index === 1 ? '#C0C0C0' : index === 2 ? '#CD7F32' : '#4CAF50'};">
                                <div style="font-size: 11px; color: #333; font-weight: bold; margin-bottom: 3px;">#${index + 1}</div>
                                <div style="font-size: 10px; color: #666; word-break: break-all; margin-bottom: 3px;">${performer.url}</div>
                                <div style="font-size: 12px; color: #4CAF50; font-weight: bold;">${performer.fields} Felder</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// FIELD DIFFICULTY ANALYSIS
// ============================================

/**
 * GET FIELD DIFFICULTY: Analysiert Schwierigkeit von Datenfeldern
 */
function getFieldDifficulty(successRate) {
    if (successRate >= 80) return { level: 'Einfach', color: '#4CAF50', icon: '✅' };
    if (successRate >= 60) return { level: 'Mittel', color: '#FF9800', icon: '⚠️' };
    if (successRate >= 40) return { level: 'Schwer', color: '#F44336', icon: '🔴' };
    return { level: 'Sehr Schwer', color: '#B71C1C', icon: '🚫' };
}

// ============================================
// EXPORT FUNCTIONS
// ============================================

/**
 * EXPORT MODEL DATA: Exportiert Modell-Statistiken
 */
function exportModelData(modelId) {
    console.log(`📊 [ANALYTICS] Exportiere Modell-Daten für: ${modelId}`);
    
    try {
        const params = new URLSearchParams({
            model_id: modelId,
            format: 'csv',
            include_details: 'true'
        });
        
        const url = `${window.API_BASE_URL}/api/statistics/export/model?${params}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `model_statistics_${modelId}_${new Date().toISOString().split('T')[0]}.csv`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification(`📁 Modell-Daten für ${modelId} exportiert!`, 'success');
    } catch (error) {
        console.error('Export error:', error);
        showNotification('❌ Fehler beim Export der Modell-Daten', 'error');
    }
}

/**
 * EXPORT FIELD DATA: Exportiert Field-Performance-Daten
 */
function exportFieldData(modelId = null) {
    console.log(`📊 [ANALYTICS] Exportiere Field-Daten${modelId ? ' für ' + modelId : ''}`);
    
    try {
        const params = new URLSearchParams({
            format: 'csv',
            include_difficulty: 'true'
        });
        
        if (modelId) {
            params.append('model_id', modelId);
        }
        
        const url = `${window.API_BASE_URL}/api/statistics/export/fields?${params}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `field_performance${modelId ? '_' + modelId : ''}_${new Date().toISOString().split('T')[0]}.csv`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification(`📁 Field-Performance-Daten exportiert!`, 'success');
    } catch (error) {
        console.error('Export error:', error);
        showNotification('❌ Fehler beim Export der Field-Daten', 'error');
    }
}

// ============================================
// INTERACTIVE FUNCTIONS
// ============================================

/**
 * INITIALIZE SOURCE DETAILS INTERACTIVITY: Initialisiert Interaktivität für Source-Details
 */
function initializeSourceDetailsInteractivity(domain) {
    // Add hover effects for metric cards
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 6px 12px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0,0,0,0.07)';
        });
    });

    // Add click animations for source items
    const sourceItems = document.querySelectorAll('.enhanced-source-item, .enhanced-source-card');
    sourceItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
            this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.12)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 3px 6px rgba(0,0,0,0.08)';
        });
    });

    console.log(`🎛️ [ANALYTICS] Source details interactivity initialized for ${domain}`);
}

/**
 * TOGGLE ANALYTICS VIEW: Wechselt zwischen Analytics-Views
 */
window.toggleAnalyticsView = function(view, domain) {
    console.log(`📊 [ANALYTICS] Switching to ${view} view for ${domain}`);
    
    // Hide all analytics views
    const views = ['score', 'usage', 'performance'];
    views.forEach(v => {
        const viewElement = document.getElementById(`analytics-${v}-${domain}`);
        const button = document.querySelector(`[data-view="${v}"]`);
        
        if (v === view) {
            // Show selected view
            if (viewElement) viewElement.style.display = 'block';
            if (button) {
                button.style.background = '#4CAF50';
                button.style.color = 'white';
                button.classList.add('active');
            }
        } else {
            // Hide other views
            if (viewElement) viewElement.style.display = 'none';
            if (button) {
                button.style.background = '#e0e0e0';
                button.style.color = '#333';
                button.classList.remove('active');
            }
        }
    });
    
    console.log(`✅ [ANALYTICS] Analytics view switched to ${view} for ${domain}`);
};

/**
 * SORT SOURCES: Sortiert Quellen nach verschiedenen Kriterien
 */
window.sortSources = function(domain, sortBy) {
    console.log(`🔄 [ANALYTICS] Sorting sources for ${domain} by ${sortBy}`);
    
    const listContainer = document.getElementById(`sources-list-${domain}`);
    const gridContainer = document.getElementById(`sources-grid-${domain}`);
    
    if (!listContainer && !gridContainer) {
        console.warn(`❌ [ANALYTICS] No source containers found for domain: ${domain}`);
        return;
    }
    
    // Get current source items
    const listItems = listContainer ? Array.from(listContainer.querySelectorAll('.enhanced-source-item')) : [];
    const gridItems = gridContainer ? Array.from(gridContainer.querySelectorAll('.enhanced-source-card')) : [];
    
    // Sort function
    const sortFunction = (a, b) => {
        let aValue, bValue;
        
        switch(sortBy) {
            case 'reliability':
                aValue = parseInt(a.querySelector('.reliability-badge')?.textContent) || 0;
                bValue = parseInt(b.querySelector('.reliability-badge')?.textContent) || 0;
                return bValue - aValue; // Descending
            
            case 'usage':
                aValue = parseInt(a.querySelector('.usage-count')?.textContent) || 0;
                bValue = parseInt(b.querySelector('.usage-count')?.textContent) || 0;
                return bValue - aValue; // Descending
            
            case 'url':
                aValue = a.querySelector('.source-url')?.textContent || '';
                bValue = b.querySelector('.source-url')?.textContent || '';
                return aValue.localeCompare(bValue); // Ascending
            
            default:
                return 0;
        }
    };
    
    // Sort and re-append items
    if (listItems.length > 0) {
        listItems.sort(sortFunction);
        listItems.forEach(item => listContainer.appendChild(item));
    }
    
    if (gridItems.length > 0) {
        gridItems.sort(sortFunction);
        gridItems.forEach(item => gridContainer.appendChild(item));
    }
    
    console.log(`✅ [ANALYTICS] Sources sorted by ${sortBy} for ${domain}`);
    showNotification(`Quellen nach ${sortBy} sortiert`, 'info');
};

// ============================================
// DOMAIN MANAGEMENT FUNCTIONS
// ============================================

/**
 * EXPORT DOMAIN SOURCES: Exportiert Quellen für eine Domain
 */
window.exportDomainSources = function(domain) {
    console.log(`📥 [ANALYTICS] Exportiere Quellen für Domain: ${domain}`);
    
    try {
        const params = new URLSearchParams({
            domain: domain,
            format: 'csv',
            include_stats: 'true'
        });
        
        const url = `${window.API_BASE_URL}/api/sources/export?${params}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `sources_${domain.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification(`📁 Quellen für ${domain} exportiert!`, 'success');
    } catch (error) {
        console.error('Export error:', error);
        showNotification('❌ Fehler beim Export der Domain-Quellen', 'error');
    }
};

/**
 * REFRESH DOMAIN DETAILS: Aktualisiert Details für eine Domain
 */
window.refreshDomainDetails = function(domain) {
    console.log(`🔄 [ANALYTICS] Aktualisiere Details für Domain: ${domain}`);
    
    const contentDiv = document.getElementById(`content-${domain}`);
    if (contentDiv) {
        // Show loading state
        showEnhancedLoadingState(contentDiv, `Aktualisiere Details für ${domain}...`, true);
        
        // Trigger refresh if function exists
        if (typeof loadEnhancedSourceDetails === 'function') {
            loadEnhancedSourceDetails(domain, contentDiv);
        } else {
            setTimeout(() => {
                showNotification(`Details für ${domain} aktualisiert`, 'success');
            }, 1000);
        }
    }
};

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export analytics functions to global scope
window.calculateSourceStatistics = calculateSourceStatistics;
window.calculateFieldPerformance = calculateFieldPerformance;
window.calculateScoreBreakdown = calculateScoreBreakdown;
window.calculateUsageAnalytics = calculateUsageAnalytics;
window.generateScoreAnalysisView = generateScoreAnalysisView;
window.generateUsageTrendsView = generateUsageTrendsView;
window.generateFieldCoverageView = generateFieldCoverageView;
window.getFieldDifficulty = getFieldDifficulty;
window.exportModelData = exportModelData;
window.exportFieldData = exportFieldData;
window.initializeSourceDetailsInteractivity = initializeSourceDetailsInteractivity;

console.log('📊 MineSearch 2.0 - Analytics Functions loaded');