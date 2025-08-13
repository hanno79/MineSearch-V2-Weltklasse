/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - UI Components & Interaction Handler
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (8961 → 500 Zeilen Regel)
 * UI Components: Modals, Tabs, Tables, Buttons, Provider Toggle, Search Controls
 */

// ============================================
// MODAL SYSTEM
// ============================================

/**
 * MODAL MANAGER: Zentrale Modal-Verwaltung
 */
const ModalManager = {
    activeModals: [],
    
    create: function(config) {
        const modal = document.createElement('div');
        modal.className = config.className || 'modal';
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(0,0,0,0.8); z-index: 10000; display: flex; 
            align-items: center; justify-content: center; padding: 20px;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = config.contentStyle || `
            background: white; border-radius: 12px; width: 90%; max-width: 1200px; 
            max-height: 90%; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        `;
        
        if (config.content) {
            modalContent.innerHTML = config.content;
        }
        
        modal.appendChild(modalContent);
        
        // Close on background click
        modal.onclick = (e) => {
            if (e.target === modal && config.closeOnBackdrop !== false) {
                this.close(modal);
            }
        };
        
        document.body.appendChild(modal);
        this.activeModals.push(modal);
        
        return modal;
    },
    
    close: function(modal) {
        if (modal && modal.parentNode) {
            modal.parentNode.removeChild(modal);
        }
        const index = this.activeModals.indexOf(modal);
        if (index > -1) {
            this.activeModals.splice(index, 1);
        }
    },
    
    closeAll: function() {
        this.activeModals.forEach(modal => this.close(modal));
    }
};

/**
 * SIMPLE MODEL DETAILS MODAL: Zeigt einfache Modell-Details (called by HTML buttons)
 */
function showModelDetails(modelId) {
    console.log(`🎯 [MODAL] Displaying details for ${modelId}`);
    
    if (!modelId) {
        console.error("❌ [MODAL] No modelId provided");
        showNotification('Keine Model-ID gefunden', 'error');
        return;
    }
    
    // Extrahiere Provider aus modelId
    const provider = modelId.includes(':') ? modelId.split(':')[0] : 'Unknown';
    const modelName = modelId.includes(':') ? modelId.split(':')[1] : modelId;
    
    const modal = ModalManager.create({
        className: 'model-details-modal',
        content: `
            <div style="padding: 30px; min-width: 600px;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 2px solid #3b82f6;">
                    <h2 style="margin: 0; color: #1f2937; font-size: 24px;">
                        🤖 ${sanitizeHTML(modelId)}
                    </h2>
                    <button onclick="ModalManager.close(this.closest('.model-details-modal'))" 
                            style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">
                        ✕ Schließen
                    </button>
                </div>
                
                <!-- Content Grid -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 25px;">
                    <!-- Basic Info -->
                    <div style="background: #f8fafc; padding: 20px; border-radius: 8px;">
                        <h3 style="color: #374151; margin-top: 0; margin-bottom: 15px; font-size: 18px;">
                            📋 Grundinformationen
                        </h3>
                        <div style="line-height: 1.6;">
                            <p style="margin: 8px 0;"><strong>Model ID:</strong> <code style="background: #e5e7eb; padding: 2px 6px; border-radius: 4px;">${sanitizeHTML(modelId)}</code></p>
                            <p style="margin: 8px 0;"><strong>Provider:</strong> <span style="color: #3b82f6; font-weight: 600;">${sanitizeHTML(provider)}</span></p>
                            <p style="margin: 8px 0;"><strong>Model Name:</strong> ${sanitizeHTML(modelName)}</p>
                            <p style="margin: 8px 0;"><strong>Status:</strong> <span style="color: #059669; font-weight: 600;">✅ Aktiv</span></p>
                        </div>
                    </div>
                    
                    <!-- Performance Metrics -->
                    <div style="background: #f0f9ff; padding: 20px; border-radius: 8px;">
                        <h3 style="color: #374151; margin-top: 0; margin-bottom: 15px; font-size: 18px;">
                            ⚡ Performance-Metriken
                        </h3>
                        <div style="line-height: 1.6;">
                            <p style="margin: 8px 0;"><strong>Geschwindigkeit:</strong> <span style="color: #059669;">🚀 Schnell</span></p>
                            <p style="margin: 8px 0;"><strong>Qualität:</strong> <span style="color: #3b82f6;">⭐ Hoch</span></p>
                            <p style="margin: 8px 0;"><strong>Verfügbarkeit:</strong> <span style="color: #059669;">🟢 Online</span></p>
                            <p style="margin: 8px 0;"><strong>Kosten:</strong> <span style="color: #d97706;">💰 Variabel</span></p>
                        </div>
                    </div>
                </div>
                
                <!-- Capabilities -->
                <div style="background: #f6f8fa; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                    <h3 style="color: #374151; margin-top: 0; margin-bottom: 15px; font-size: 18px;">
                        💡 Model-Fähigkeiten
                    </h3>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                        <li>🔍 <strong>Text-Analyse & Generierung:</strong> Hochwertige Textverarbeitung</li>
                        <li>🌐 <strong>Web-Recherche:</strong> ${provider === 'perplexity' ? 'Ja (spezialisiert)' : 'Verfügbar je nach Model'}</li>
                        <li>📊 <strong>Mining-Daten-Analyse:</strong> Spezialisiert auf Bergbau-Recherche</li>
                        <li>🔗 <strong>API-Integration:</strong> Vollständig integriert in MineSearch 2.0</li>
                    </ul>
                </div>
                
                <!-- Actions -->
                <div style="text-align: right; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                    <button onclick="ModalManager.close(this.closest('.model-details-modal'))"
                            style="background: #6b7280; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-right: 10px;">
                        Schließen
                    </button>
                    <button onclick="selectModelForSearch('${sanitizeHTML(modelId)}'); ModalManager.close(this.closest('.model-details-modal'));"
                            style="background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: 600;">
                        🎯 Model auswählen
                    </button>
                </div>
            </div>
        `
    });
    
    console.log("✅ [MODAL] Model details modal created successfully");
    return modal;
}

/**
 * SELECT MODEL FOR SEARCH: Wählt Model für Suche aus
 */
function selectModelForSearch(modelId) {
    console.log(`🎯 [MODEL-SELECTION] Selecting model: ${modelId}`);
    
    // Finde Checkbox für dieses Model
    const checkbox = document.querySelector(`input[name="model"][value="${modelId}"]`);
    if (checkbox) {
        checkbox.checked = true;
        console.log(`✅ [MODEL-SELECTION] Model ${modelId} selected`);
        showNotification(`Model ${modelId} ausgewählt`, 'success');
        
        // Scrolle zur Model-Selection
        checkbox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        console.error(`❌ [MODEL-SELECTION] Checkbox for ${modelId} not found`);
        showNotification(`Model ${modelId} nicht gefunden`, 'error');
    }
}

/**
 * COMPREHENSIVE DETAILS MODAL: Zeigt umfassende Modell-Details
 */
function showComprehensiveModelDetails(modelId, modelData) {
    console.log(`🎯 [MODAL] Displaying comprehensive details for ${modelId}`);
    
    const modal = ModalManager.create({
        className: 'comprehensive-details-modal',
        content: `
            <div style="padding: 30px;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #3b82f6;">
                    <h1 style="margin: 0; color: #1f2937; font-size: 28px;">
                        🤖 ${sanitizeHTML(modelId)}
                    </h1>
                    <button onclick="ModalManager.close(this.closest('.comprehensive-details-modal'))" 
                            style="background: #ef4444; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
                        ✕ Schließen
                    </button>
                </div>
                
                <!-- Tabs -->
                <div style="border-bottom: 1px solid #e5e7eb; margin-bottom: 20px;">
                    <div style="display: flex; gap: 5px;">
                        <button onclick="switchComprehensiveTab('overview', arguments[1])" 
                                style="background: white; border: 1px solid #e5e7eb; border-bottom: 3px solid #2563eb; 
                                       padding: 12px 20px; cursor: pointer; font-weight: 600; color: #2563eb;">
                            📊 Überblick
                        </button>
                        <button onclick="switchComprehensiveTab('scores', arguments[1])" 
                                style="background: transparent; border: 1px solid #e5e7eb; border-bottom: 3px solid transparent; 
                                       padding: 12px 20px; cursor: pointer; font-weight: 600; color: #6b7280;">
                            🏆 Scores
                        </button>
                        <button onclick="switchComprehensiveTab('fields', arguments[1])" 
                                style="background: transparent; border: 1px solid #e5e7eb; border-bottom: 3px solid transparent; 
                                       padding: 12px 20px; cursor: pointer; font-weight: 600; color: #6b7280;">
                            📋 Felder
                        </button>
                        <button onclick="switchComprehensiveTab('performance', arguments[1])" 
                                style="background: transparent; border: 1px solid #e5e7eb; border-bottom: 3px solid transparent; 
                                       padding: 12px 20px; cursor: pointer; font-weight: 600; color: #6b7280;">
                            ⚡ Performance
                        </button>
                    </div>
                </div>
                
                <!-- Tab Content -->
                <div id="comprehensive-modal-content">
                    ${generateOverviewTab(modelData)}
                </div>
            </div>
        `
    });
    
    return modal;
}

/**
 * TAB SWITCHING: Wechselt zwischen Tab-Ansichten im comprehensive modal
 */
function switchComprehensiveTab(tabId, modelData) {
    console.log(`🔄 [TAB-SWITCH] Switching to tab: ${tabId}`);
    
    // Update tab buttons
    const modal = document.querySelector('.comprehensive-details-modal');
    if (!modal) return;
    
    const tabButtons = modal.querySelectorAll('button');
    tabButtons.forEach(button => {
        const isActive = button.textContent.toLowerCase().includes(tabId === 'overview' ? 'überblick' : 
                                                                    tabId === 'scores' ? 'scores' :
                                                                    tabId === 'fields' ? 'felder' : 'performance');
        button.style.background = isActive ? 'white' : 'transparent';
        button.style.borderBottomColor = isActive ? '#2563eb' : 'transparent';
        button.style.color = isActive ? '#2563eb' : '#6b7280';
    });
    
    const contentArea = modal.querySelector('#comprehensive-modal-content');
    if (!contentArea) return;
    
    switch (tabId) {
        case 'overview':
            contentArea.innerHTML = generateOverviewTab(modelData);
            break;
        case 'scores':
            contentArea.innerHTML = generateScoresTab(modelData);
            break;
        case 'fields':
            contentArea.innerHTML = generateFieldsTab(modelData);
            break;
        case 'performance':
            contentArea.innerHTML = generatePerformanceTab(modelData);
            break;
        default:
            contentArea.innerHTML = generateOverviewTab(modelData);
    }
}

// ============================================
// TAB CONTENT GENERATORS
// ============================================

/**
 * OVERVIEW TAB: Gesamtüberblick der wichtigsten Metriken
 */
function generateOverviewTab(modelData) {
    const scoreColor = modelData.overall_score >= 85 ? '#059669' : 
                      modelData.overall_score >= 70 ? '#0891b2' : 
                      modelData.overall_score >= 50 ? '#ea580c' : 
                      modelData.overall_score >= 30 ? '#d97706' : '#dc2626';
    
    return `
        <div style="padding: 30px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb;">
                    <h3 style="margin: 0 0 20px 0; color: #374151; display: flex; align-items: center; gap: 10px;">
                        🏆 Gesamtbewertung
                    </h3>
                    <div style="text-align: center;">
                        <div style="font-size: 48px; font-weight: bold; color: ${scoreColor}; margin-bottom: 10px;">
                            ${modelData.overall_score}%
                        </div>
                        <div style="background: ${scoreColor}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; display: inline-block;">
                            ${modelData.score_category}
                        </div>
                    </div>
                </div>
                
                <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb;">
                    <h3 style="margin: 0 0 20px 0; color: #374151; display: flex; align-items: center; gap: 10px;">
                        📊 Kernindikatoren
                    </h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #374151;">${modelData.completeness_score}%</div>
                            <div style="font-size: 12px; color: #6b7280;">Vollständigkeit</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #374151;">${modelData.consistency_score}%</div>
                            <div style="font-size: 12px; color: #6b7280;">Konsistenz</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #374151;">${modelData.source_diversity_score}%</div>
                            <div style="font-size: 12px; color: #6b7280;">Quellen-Vielfalt</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #374151;">${Math.round(modelData.avg_search_duration_ms / 1000)}s</div>
                            <div style="font-size: 12px; color: #6b7280;">Ø Performance</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * SCORES TAB: Detaillierte Score-Aufschlüsselung
 */
function generateScoresTab(modelData) {
    const scoreComponents = [
        { name: 'Vollständigkeit', value: modelData.completeness_score, weight: '40%', color: '#3b82f6' },
        { name: 'Konsistenz', value: modelData.consistency_score, weight: '30%', color: '#7c3aed' },
        { name: 'Quellen-Vielfalt', value: modelData.source_diversity_score, weight: '20%', color: '#059669' },
        { name: 'Performance', value: modelData.performance_score || Math.max(0, 100 - (modelData.avg_search_duration_ms / 1000 * 2)), weight: '10%', color: '#ea580c' }
    ];
    
    return `
        <div style="padding: 30px;">
            <div style="background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px;">
                <h3 style="margin: 0 0 15px 0; font-size: 20px;">🏆 Score-Aufschlüsselung</h3>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div>
                        <div style="font-size: 36px; font-weight: bold;">${modelData.overall_score}%</div>
                        <div style="opacity: 0.9;">Gesamtscore</div>
                    </div>
                    <div style="flex: 1; font-size: 14px; opacity: 0.9;">
                        Gewichteter Durchschnitt aus ${scoreComponents.length} Bewertungsdimensionen
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
                ${scoreComponents.map(component => `
                    <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="margin: 0; color: #374151;">${component.name}</h4>
                            <span style="background: #f3f4f6; color: #6b7280; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                                ${component.weight}
                            </span>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <div style="font-size: 28px; font-weight: bold; color: ${component.color};">${component.value}%</div>
                        </div>
                        <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="width: ${component.value}%; height: 100%; background: ${component.color}; transition: width 0.3s ease;"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * FIELDS TAB: Feld-spezifische Performance
 */
function generateFieldsTab(modelData) {
    const fieldCategories = {
        'Grunddaten': ['Mine Name', 'Land', 'Region', 'Mine Typ'],
        'Koordinaten': ['Latitude', 'Longitude', 'Höhe'],
        'Betriebsdaten': ['Status', 'Betreiber', 'Produktionsjahr'],
        'Produktion': ['Fördermenge', 'Ressourcen', 'Reserven'],
        'Finanziell': ['Investitionskosten', 'Betriebskosten', 'Restaurationskosten']
    };
    
    return `
        <div style="padding: 30px;">
            <div style="background: linear-gradient(135deg, #059669 0%, #0891b2 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px;">
                <h3 style="margin: 0 0 15px 0; font-size: 20px;">📋 Feld-Performance Analyse</h3>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div>
                        <div style="font-size: 36px; font-weight: bold;">${modelData.avg_fields_found || 12}</div>
                        <div style="opacity: 0.9;">Ø gefundene Felder</div>
                    </div>
                    <div>
                        <div style="font-size: 36px; font-weight: bold;">${modelData.total_expected_fields || 20}</div>
                        <div style="opacity: 0.9;">Erwartete Felder</div>
                    </div>
                </div>
            </div>
            
            ${Object.entries(fieldCategories).map(([category, fields]) => `
                <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin: 0 0 20px 0; color: #374151; padding-bottom: 10px; border-bottom: 2px solid #e5e7eb;">
                        ${category}
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                        ${fields.map(field => {
                            const found = Math.random() > 0.3; // DUMMY-WERT: Mock data für Demo - echte Feld-Performance aus API holen
                            const consistency = Math.floor(Math.random() * 40) + 60; // DUMMY-WERT: Mock data für Demo 
                            const consistencyColor = consistency >= 80 ? '#059669' : consistency >= 60 ? '#0891b2' : '#ea580c';
                            
                            return `
                                <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px; background: ${found ? '#f0fdf4' : '#fef2f2'}; border-radius: 6px; border: 1px solid ${found ? '#bbf7d0' : '#fecaca'};">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span style="font-size: 16px;">${found ? '✅' : '❌'}</span>
                                        <span style="font-weight: 500; color: #374151;">${field}</span>
                                    </div>
                                    ${found ? `
                                        <span style="background: ${consistencyColor}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold;">
                                            ${consistency}%
                                        </span>
                                    ` : '<span style="color: #6b7280; font-size: 12px;">Nicht gefunden</span>'}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * PERFORMANCE TAB: Detaillierte Performance-Metriken
 */
function generatePerformanceTab(modelData) {
    const performanceMetrics = [
        { 
            name: 'Durchschnittliche Antwortzeit', 
            value: `${Math.round(modelData.avg_search_duration_ms / 1000)}s`,
            trend: 'stable',
            description: 'Zeit bis zur vollständigen Antwort'
        },
        {
            name: 'Erfolgsrate',
            value: `${modelData.success_rate_percent}%`,
            trend: modelData.success_rate_percent >= 90 ? 'up' : modelData.success_rate_percent >= 70 ? 'stable' : 'down',
            description: 'Anteil erfolgreicher Suchen'
        },
        {
            name: 'Eindeutige Quellen',
            value: `${modelData.unique_sources_total}`,
            trend: 'up',
            description: 'Anzahl verschiedener genutzter Datenquellen'
        }
    ];
    
    return `
        <div style="padding: 30px;">
            <div style="background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px;">
                <h3 style="margin: 0 0 15px 0; font-size: 20px;">⚡ Performance-Analyse</h3>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div>
                        <div style="font-size: 36px; font-weight: bold;">${modelData.performance_category || 'Mittel'}</div>
                        <div style="opacity: 0.9;">Performance-Kategorie</div>
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
                ${performanceMetrics.map(metric => {
                    const trendIcon = metric.trend === 'up' ? '📈' : metric.trend === 'down' ? '📉' : '➡️';
                    const trendColor = metric.trend === 'up' ? '#059669' : metric.trend === 'down' ? '#dc2626' : '#6b7280';
                    
                    return `
                        <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                <h4 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">${metric.name}</h4>
                                <span style="font-size: 16px;" title="Trend">${trendIcon}</span>
                            </div>
                            <div style="font-size: 32px; font-weight: bold; color: ${trendColor}; margin-bottom: 10px;">
                                ${metric.value}
                            </div>
                            <div style="font-size: 12px; color: #6b7280; line-height: 1.4;">
                                ${metric.description}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

// ============================================
// PROVIDER & MODEL SELECTION
// ============================================

/**
 * PROVIDER TOGGLE: Ein-/Ausklappen der Modell-Listen pro Provider (reine Akkordeon-Funktion)
 */
function toggleProviderModels(provider) {
    const providerSection = document.querySelector(`[data-provider="${provider}"]`);
    if (!providerSection) return;
    
    const modelsList = providerSection.querySelector('.models-list');
    const toggleIcon = providerSection.querySelector('.provider-toggle');
    
    if (modelsList && toggleIcon) {
        const isExpanded = modelsList.style.display !== 'none';
        modelsList.style.display = isExpanded ? 'none' : 'block';
        toggleIcon.textContent = isExpanded ? '▶' : '▼';
    }
}

/**
 * PROVIDER CHECKBOX STATE: Aktualisiert Checkbox-Status basierend auf Modell-Auswahl
 */
function updateProviderCheckboxState(provider) {
    const providerSection = document.querySelector(`[data-provider="${provider}"]`);
    if (!providerSection) return;
    
    const providerCheckbox = providerSection.querySelector('input[type="checkbox"]');
    const modelCheckboxes = providerSection.querySelectorAll('.models-list input[type="checkbox"]');
    
    if (providerCheckbox && modelCheckboxes.length > 0) {
        const checkedModels = Array.from(modelCheckboxes).filter(cb => cb.checked);
        
        if (checkedModels.length === 0) {
            providerCheckbox.checked = false;
            providerCheckbox.indeterminate = false;
        } else if (checkedModels.length === modelCheckboxes.length) {
            providerCheckbox.checked = true;
            providerCheckbox.indeterminate = false;
        } else {
            providerCheckbox.checked = false;
            providerCheckbox.indeterminate = true;
        }
    }
}

/**
 * PROVIDER CHECKBOX TOGGLE: Wählt alle Modelle eines Providers an/ab + steuert Akkordeon
 * FIX 11.08.2025: Kombiniert Checkbox-Funktionalität mit Akkordeon-Steuerung
 */
function toggleProviderCheckbox(provider) {
    console.log(`🔄 [CHECKBOX] Toggling provider: ${provider}`);
    
    const providerSection = document.querySelector(`[data-provider="${provider}"]`);
    if (!providerSection) {
        console.warn(`⚠️ [CHECKBOX] Provider section not found: ${provider}`);
        return;
    }
    
    const providerCheckbox = providerSection.querySelector('input[type="checkbox"]');
    const modelCheckboxes = providerSection.querySelectorAll('.models-list input[type="checkbox"]');
    
    // Checkbox-Funktionalität: Alle Modelle an/abwählen
    if (providerCheckbox && modelCheckboxes.length > 0) {
        const isChecked = providerCheckbox.checked;
        console.log(`🔄 [CHECKBOX] Setting all ${modelCheckboxes.length} models to: ${isChecked}`);
        
        modelCheckboxes.forEach(cb => {
            cb.checked = isChecked;
        });
        
        // Update visual state
        updateProviderCheckboxState(provider);
        
        console.log(`✅ [CHECKBOX] Provider ${provider} toggle complete`);
    } else {
        console.warn(`⚠️ [CHECKBOX] Missing elements for provider: ${provider}`);
    }
    
    // Akkordeon-Funktionalität: Liste öffnen/schließen
    const modelsList = providerSection.querySelector('.models-list');
    const toggleIcon = providerSection.querySelector('.provider-toggle');
    
    if (modelsList && toggleIcon) {
        const isExpanded = modelsList.style.display !== 'none';
        modelsList.style.display = isExpanded ? 'none' : 'block';
        toggleIcon.textContent = isExpanded ? '▶' : '▼';
        console.log(`🎯 [ACCORDION] ${provider} accordion ${isExpanded ? 'collapsed' : 'expanded'}`);
    }
}

// ============================================
// TAB MANAGEMENT SYSTEM
// ============================================

/**
 * TAB HANDLER: Behandelt Wechsel zwischen Haupttabs (Suche, Quellen, etc.)
 */
function handleTabChange() {
    const tabs = document.querySelectorAll('.nav-tab');
    const sections = document.querySelectorAll('.tab-content');
    
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and sections
            tabs.forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding section
            tab.classList.add('active');
            if (sections[index]) {
                sections[index].classList.add('active');
            }
            
            // Trigger content loading for specific tabs
            const tabType = tab.getAttribute('data-tab');
            handleTabContentLoading(tabType);
        });
    });
}

/**
 * TAB CONTENT LOADING: Lädt Inhalte beim Tab-Wechsel
 */
function handleTabContentLoading(tabType) {
    switch (tabType) {
        case 'sources':
            if (typeof loadSources === 'function') {
                loadSources();
            }
            break;
        case 'results':
            if (typeof loadConsolidatedResults === 'function') {
                loadConsolidatedResults();
            }
            break;
        case 'statistics':
            if (typeof loadModelStatistics === 'function') {
                loadModelStatistics();
            }
            break;
    }
}

// ============================================
// SEARCH CONTROLS
// ============================================

/**
 * SEARCH CANCEL: Bricht laufende Suche ab
 */
function cancelSearch() {
    console.log('🛑 [SEARCH] Cancelling active search');
    
    // Stop timer
    if (typeof stopSearchTimer === 'function') {
        stopSearchTimer();
    }
    
    // Abort API requests
    if (window.SearchAPI && typeof SearchAPI.abortSearch === 'function') {
        SearchAPI.abortSearch('current_search');
    }
    
    // Reset UI state
    const searchButton = document.querySelector('.search-submit-button');
    const cancelButton = document.querySelector('.cancel-search-button');
    const resultsSection = document.getElementById('results-section');
    
    if (searchButton) {
        searchButton.disabled = false;
        searchButton.style.display = 'block';
    }
    
    if (cancelButton) {
        cancelButton.style.display = 'none';
    }
    
    if (resultsSection) {
        resultsSection.innerHTML = createErrorHTML('Suche abgebrochen', 'Die laufende Suche wurde vom Benutzer abgebrochen.');
    }
    
    showNotification('🛑 Suche wurde abgebrochen', 'info');
}

// ============================================
// BUTTON STATE MANAGEMENT
// ============================================

/**
 * BUTTON STATE CONTROLLER: Verwaltet Button-Zustände während Operationen
 */
const ButtonStateController = {
    setLoading: function(button, loadingText = 'Lädt...') {
        if (!button) return;
        
        button.dataset.originalText = button.textContent;
        button.textContent = loadingText;
        button.disabled = true;
        button.style.opacity = '0.7';
        button.style.cursor = 'not-allowed';
    },
    
    resetState: function(button) {
        if (!button) return;
        
        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
    },
    
    setError: function(button, errorText = 'Fehler') {
        if (!button) return;
        
        button.textContent = errorText;
        button.style.background = '#dc2626';
        button.style.color = 'white';
        
        setTimeout(() => this.resetState(button), 3000);
    }
};

// ============================================
// EXPORT UTILITIES
// ============================================

/**
 * EXPORT CONTROLS: Behandelt verschiedene Export-Operationen
 */
const ExportManager = {
    exportModelData: function(modelId) {
        console.log(`📊 [EXPORT] Exporting data for model: ${modelId}`);
        showNotification('📊 Model-Daten werden exportiert...', 'info');
        
        const exportUrl = `${window.API_BASE_URL}/api/statistics/export/csv?table=models&model_id=${encodeURIComponent(modelId)}&days_back=30`;
        
        const link = document.createElement('a');
        link.href = exportUrl;
        link.download = `model_${modelId}_statistics.csv`;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('✅ Model-Daten erfolgreich exportiert', 'success');
    },
    
    exportFieldData: function(modelId = null) {
        console.log(`📊 [EXPORT] Exporting field performance data`);
        showNotification('📊 Feld-Performance wird exportiert...', 'info');
        
        let exportUrl = `${window.API_BASE_URL}/api/statistics/export/csv?table=field_performance&days_back=30`;
        if (modelId) {
            exportUrl += `&model_id=${encodeURIComponent(modelId)}`;
        }
        
        const link = document.createElement('a');
        link.href = exportUrl;
        link.download = `field_performance_${modelId || 'all'}_${Date.now()}.csv`;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('✅ Feld-Performance erfolgreich exportiert', 'success');
    }
};

// ============================================
// CLOSE HANDLERS
// ============================================

/**
 * CLOSE FUNCTIONS: Schließt verschiedene Modals und Details
 */
function closeModelDetails() {
    const modal = document.querySelector('.model-details-modal');
    if (modal) {
        ModalManager.close(modal);
    }
}

function closeFieldPerformance() {
    const modal = document.querySelector('.field-performance-modal');
    if (modal) {
        ModalManager.close(modal);
    }
}

// ============================================
// GLOBAL EXPORTS
// ============================================

// Export UI components to global scope
window.ModalManager = ModalManager;
window.showModelDetails = showModelDetails;
window.selectModelForSearch = selectModelForSearch;
window.showComprehensiveModelDetails = showComprehensiveModelDetails;
window.switchComprehensiveTab = switchComprehensiveTab;
window.generateOverviewTab = generateOverviewTab;
window.generateScoresTab = generateScoresTab;
window.generateFieldsTab = generateFieldsTab;
window.generatePerformanceTab = generatePerformanceTab;
window.toggleProviderModels = toggleProviderModels;
window.updateProviderCheckboxState = updateProviderCheckboxState;
window.toggleProviderCheckbox = toggleProviderCheckbox;
window.handleTabChange = handleTabChange;
window.cancelSearch = cancelSearch;
window.ButtonStateController = ButtonStateController;
window.ExportManager = ExportManager;
window.closeModelDetails = closeModelDetails;
window.closeFieldPerformance = closeFieldPerformance;

console.log('🎨 MineSearch 2.0 - UI Components loaded');