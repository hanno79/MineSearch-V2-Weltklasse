/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Results Processing & State Management
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (Phase 3 - Final Refactoring)
 * Results Functions: Result Display, Accordion State Management, Search Result Processing
 */

// ============================================
// CORE RESULT DISPLAY FUNCTIONS
// ============================================

/**
 * DISPLAY RESULTS: Zeigt Suchergebnisse an mit Phase 4 Multi-Model Support
 */
function displayResults(data) {
    console.log('📊 [RESULTS] Displaying search results');
    
    const resultsDiv = document.getElementById('results');
    if (!resultsDiv) {
        console.error('❌ [RESULTS] Results div not found');
        return;
    }
    
    if (!data) {
        console.warn('⚠️ [RESULTS] No data provided');
        resultsDiv.innerHTML = createErrorHTML('Keine Daten', 'Keine Suchergebnisse erhalten');
        return;
    }
    
    try {
        // PHASE 4: MULTI-MODEL COMPARISON DETECTION
        if (data.data && data.data.results && Array.isArray(data.data.results)) {
            console.log('🔬 [PHASE 4] Multi-model results detected');
            
            const successfulResults = data.data.results.filter(r => r.success && r.data);
            
            if (successfulResults.length >= 2) {
                console.log(`🔬 [PHASE 4] Interactive comparison for ${successfulResults.length} models`);
                displayMultiModelComparison(successfulResults, data.data);
                return;
            } else if (successfulResults.length === 1) {
                console.log('📊 [PHASE 3] Single successful model from multi-search');
                displaySingleModelFromMulti(successfulResults[0], data.data);
                return;
            } else {
                console.log('❌ [RESULTS] No successful models in multi-search');
                displayMultiModelErrors(data.data.results);
                return;
            }
        }
        
        // PHASE 3: SINGLE MODEL RESULTS
        if (data.success && data.data) {
            console.log('✅ [RESULTS] Displaying single model results');
            
            // Save results to session for restoration
            if (typeof saveSearchResults === 'function') {
                saveSearchResults(data, 'single');
            }
            
            // PHASE 3: Results Presentation Revolution - Card-based Layout
            console.log('🎨 [RESULTS-REVOLUTION] Implementing modern card-based results...');
            
            const resultHTML = generateModernResultCard(data.data);
            
            safeSetHTML(resultsDiv, resultHTML);
            
        } else {
            // Error case
            console.warn('⚠️ [RESULTS] Displaying error results');
            
            const errorHTML = `
                <div style="padding: 20px; background: #fef2f2; border-radius: 8px; border: 1px solid #f87171;">
                    <h3 style="color: #dc2626; margin: 0 0 10px 0;">❌ Suchergebnis fehlgeschlagen</h3>
                    <p style="color: #7f1d1d; margin-bottom: 15px;">${sanitizeHTML(data.error || 'Unbekannter Fehler')}</p>
                    
                    ${data.details ? `
                        <details style="background: #fef2f2; padding: 10px; border-radius: 4px; margin-top: 10px;">
                            <summary style="cursor: pointer; font-weight: bold; color: #dc2626;">
                                🔍 Fehler-Details
                            </summary>
                            <pre style="background: #ffffff; padding: 10px; border-radius: 4px; white-space: pre-wrap; font-size: 11px; color: #7f1d1d; margin-top: 10px;">${sanitizeHTML(JSON.stringify(data.details, null, 2))}</pre>
                        </details>
                    ` : ''}
                    
                    <button onclick="retryLastSearch()" 
                            style="background: #dc2626; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px;">
                        🔄 Erneut versuchen
                    </button>
                </div>
            `;
            
            safeSetHTML(resultsDiv, errorHTML);
        }
        
    } catch (error) {
        console.error('❌ [RESULTS] Error displaying results:', error);
        resultsDiv.innerHTML = createErrorHTML('Anzeigefehler', `Fehler beim Anzeigen der Ergebnisse: ${error.message}`);
    }
}

/**
 * GENERATE RESULT SUMMARY: Erstellt Zusammenfassung der Ergebnisse
 */
function generateResultSummary(data) {
    if (!data) return '';
    
    const summary = {
        mine_name: data.mine_name || 'Unbekannt',
        country: data.country || 'Unbekannt', 
        commodity: data.commodity || 'Unbekannt',
        fieldsFound: data.structured_data ? Object.keys(data.structured_data).length : 0,
        sources: data.sources ? data.sources.length : 0,
        model: data.model_used || 'Unbekannt'
    };
    
    return `
        <div class="result-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0;">
            <div class="summary-card" style="background: #ffffff; padding: 12px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                <div style="font-size: 20px; font-weight: bold; color: #059669;">${summary.fieldsFound}</div>
                <div style="font-size: 12px; color: #666;">Felder gefunden</div>
            </div>
            
            <div class="summary-card" style="background: #ffffff; padding: 12px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                <div style="font-size: 20px; font-weight: bold; color: #0891b2;">${summary.sources}</div>
                <div style="font-size: 12px; color: #666;">Quellen verwendet</div>
            </div>
            
            <div class="summary-card" style="background: #ffffff; padding: 12px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                <div style="font-size: 16px; font-weight: bold; color: #7c3aed;">${summary.country}</div>
                <div style="font-size: 12px; color: #666;">Land</div>
            </div>
            
            <div class="summary-card" style="background: #ffffff; padding: 12px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                <div style="font-size: 16px; font-weight: bold; color: #ea580c;">${summary.commodity}</div>
                <div style="font-size: 12px; color: #666;">Rohstoff</div>
            </div>
        </div>
        
        <div style="margin: 15px 0; padding: 10px; background: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0;">
            <strong>Verwendetes Modell:</strong> ${sanitizeHTML(summary.model)}
        </div>
    `;
}

// ============================================
// ACCORDION STATE MANAGEMENT
// ============================================

/**
 * PRESERVE ACCORDION STATE: Speichert aktuellen Accordion-Zustand
 */
function preserveAccordionState() {
    console.log('💾 [ACCORDION] Preserving accordion state...');
    
    const preservedState = {
        openDetails: [],
        openModels: [],
        scrollPosition: window.scrollY,
        activeTab: document.querySelector('input[name="tab"]:checked')?.value
    };
    
    // Speichere alle geöffneten Source-Details (klassische Accordion)
    document.querySelectorAll('.details-row[style*="display: table-row"], .details-row.expanded').forEach(row => {
        const parentRow = row.previousElementSibling;
        if (parentRow && parentRow.querySelector('[data-domain]')) {
            const domain = parentRow.querySelector('[data-domain]').getAttribute('data-domain');
            if (domain) {
                preservedState.openDetails.push(domain);
                console.log(`💾 [ACCORDION] Saved open source details for: ${domain}`);
            }
        }
    });
    
    // Speichere alle geöffneten Model-Details (Statistics-Accordion)
    document.querySelectorAll('[id^="model-details-"][style*="table-row"]').forEach(row => {
        const modelId = row.id.replace('model-details-', '').replace(/_/g, '-');
        if (modelId) {
            preservedState.openModels.push(modelId);
            console.log(`💾 [ACCORDION] Saved open model details for: ${modelId}`);
        }
    });
    
    // Speichere erweiterte Source-Details-Accordions (Enhanced Style)
    document.querySelectorAll('[id^="content-"][style*="block"]').forEach(content => {
        const domain = content.id.replace('content-', '');
        if (domain && !preservedState.openDetails.includes(domain)) {
            preservedState.openDetails.push(domain);
            console.log(`💾 [ACCORDION] Saved enhanced source details for: ${domain}`);
        }
    });
    
    console.log(`💾 [ACCORDION] Preserved ${preservedState.openDetails.length} source accordion(s) and ${preservedState.openModels.length} model accordion(s)`);
    
    return preservedState;
}

/**
 * RESTORE ACCORDION STATE: Stellt Accordion-Zustand wieder her
 */
function restoreAccordionState(preservedState) {
    if (!preservedState || (!preservedState.openDetails?.length && !preservedState.openModels?.length)) {
        console.log('🔄 [ACCORDION] No accordion state to restore');
        return;
    }
    
    const totalToRestore = (preservedState.openDetails?.length || 0) + (preservedState.openModels?.length || 0);
    console.log(`🔄 [ACCORDION] Attempting to restore ${totalToRestore} accordion(s)`);
    
    // Kleine Verzögerung für DOM-Stabilität
    setTimeout(() => {
        let restoredCount = 0;
        
        // Restauriere Source-Details (klassische Accordion)
        if (preservedState.openDetails?.length) {
            preservedState.openDetails.forEach(domain => {
                console.log(`🔄 [ACCORDION] Restoring source details for: ${domain}`);
                
                try {
                    // Versuche verschiedene Selektoren für unterschiedliche Accordion-Typen
                    let detailsButton = document.querySelector(`[onclick*="toggleSourceDetails"][onclick*="${domain}"]`);
                    
                    if (!detailsButton) {
                        // Alternative: Button mit data-domain
                        detailsButton = document.querySelector(`[data-domain="${domain}"][onclick*="toggleSourceDetails"]`);
                    }
                    
                    if (!detailsButton) {
                        // Alternative: Enhanced Source Details
                        detailsButton = document.querySelector(`[onclick*="toggleEnhancedSourceDetails"][onclick*="${domain}"]`);
                    }
                    
                    if (detailsButton && !detailsButton.classList.contains('active')) {
                        console.log(`🔄 [ACCORDION] Clicking source details button for: ${domain}`);
                        detailsButton.click();
                        restoredCount++;
                    } else if (detailsButton) {
                        console.log(`ℹ️ [ACCORDION] Source details already active for: ${domain}`);
                        restoredCount++;
                    } else {
                        console.warn(`⚠️ [ACCORDION] Source details button not found for: ${domain}`);
                    }
                } catch (error) {
                    console.error(`❌ [ACCORDION] Error restoring source details for ${domain}:`, error);
                }
            });
        }
        
        // Restauriere Model-Details (Statistics-Accordion)
        if (preservedState.openModels?.length) {
            preservedState.openModels.forEach(modelId => {
                console.log(`🔄 [ACCORDION] Restoring model details for: ${modelId}`);
                
                try {
                    const modelButton = document.querySelector(`[onclick*="toggleModelDetails"][onclick*="${modelId}"]`);
                    
                    if (modelButton && !modelButton.classList.contains('active')) {
                        console.log(`🔄 [ACCORDION] Clicking model details button for: ${modelId}`);
                        modelButton.click();
                        restoredCount++;
                    } else if (modelButton) {
                        console.log(`ℹ️ [ACCORDION] Model details already active for: ${modelId}`);
                        restoredCount++;
                    } else {
                        console.warn(`⚠️ [ACCORDION] Model details button not found for: ${modelId}`);
                    }
                } catch (error) {
                    console.error(`❌ [ACCORDION] Error restoring model details for ${modelId}:`, error);
                }
            });
        }
        
        // Restore scroll position
        if (preservedState.scrollPosition && preservedState.scrollPosition > 0) {
            setTimeout(() => {
                window.scrollTo(0, preservedState.scrollPosition);
                console.log(`📜 [ACCORDION] Scroll position restored: ${preservedState.scrollPosition}px`);
            }, 500);
        }
        
        console.log(`✅ [ACCORDION] Restored ${restoredCount}/${totalToRestore} accordion(s)`);
        
    }, 250); // Delay für DOM-Stabilität
}

// ============================================
// SEARCH RESULT PROCESSING
// ============================================

/**
 * PROCESS SEARCH RESULTS: Verarbeitet Suchergebnisse
 */
function processSearchResults(data, searchType = 'single') {
    console.log(`📊 [RESULTS] Processing ${searchType} search results`);
    
    if (!data || !data.results) {
        console.error('❌ [RESULTS] No results data provided');
        return null;
    }
    
    const results = Array.isArray(data.results) ? data.results : [data.results];
    
    // Statistiken
    const totalResults = results.length;
    const successfulResults = results.filter(r => r.success).length;
    const uniqueMines = [...new Set(results.map(r => r.mine_name))].filter(Boolean);
    const uniqueModels = [...new Set(results.map(r => r.model_used))].filter(Boolean);
    
    const processedData = {
        total: totalResults,
        successful: successfulResults,
        failed: totalResults - successfulResults,
        successRate: totalResults > 0 ? Math.round((successfulResults / totalResults) * 100) : 0,
        mines: uniqueMines,
        models: uniqueModels,
        results: results,
        searchType: searchType,
        timestamp: new Date().toISOString()
    };
    
    console.log(`📈 [RESULTS] Processing complete: ${successfulResults}/${totalResults} erfolgreiche Ergebnisse, ${uniqueMines.length} eindeutige Minen, ${uniqueModels.length} Modelle`);
    
    return processedData;
}

/**
 * DISPLAY BATCH RESULTS: Zeigt Batch-Ergebnisse an
 */
function displayBatchResults(results) {
    console.log('📊 [RESULTS] Displaying batch results');
    
    const resultsDiv = document.getElementById('results');
    if (!resultsDiv) {
        console.error('❌ [RESULTS] Results div not found');
        return;
    }
    
    if (!results || !Array.isArray(results)) {
        resultsDiv.innerHTML = createErrorHTML('Batch-Ergebnisse Fehler', 'Keine gültigen Batch-Ergebnisse erhalten');
        return;
    }
    
    const processedData = processSearchResults({ results: results }, 'batch');
    if (!processedData) {
        resultsDiv.innerHTML = createErrorHTML('Verarbeitungsfehler', 'Batch-Ergebnisse konnten nicht verarbeitet werden');
        return;
    }
    
    // Generate batch results HTML
    const batchHTML = `
        <div class="batch-results" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #374151;">📊 Batch-Suchergebnisse</h3>
                <button onclick="exportBatchResults()" 
                        style="background: #059669; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    📥 Alle exportieren
                </button>
            </div>
            
            <div class="batch-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div class="summary-card" style="background: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #059669;">${processedData.successful}</div>
                    <div style="font-size: 12px; color: #666;">Erfolgreich</div>
                </div>
                
                <div class="summary-card" style="background: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #dc2626;">${processedData.failed}</div>
                    <div style="font-size: 12px; color: #666;">Fehlgeschlagen</div>
                </div>
                
                <div class="summary-card" style="background: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #0891b2;">${processedData.successRate}%</div>
                    <div style="font-size: 12px; color: #666;">Erfolgsrate</div>
                </div>
                
                <div class="summary-card" style="background: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #7c3aed;">${processedData.mines.length}</div>
                    <div style="font-size: 12px; color: #666;">Eindeutige Minen</div>
                </div>
            </div>
            
            <div class="batch-details" style="margin-top: 20px;">
                <details style="background: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <summary style="cursor: pointer; font-weight: bold; color: #374151; margin-bottom: 15px;">
                        📋 Detaillierte Ergebnisse anzeigen (${results.length} Ergebnisse)
                    </summary>
                    <div class="results-table" style="overflow-x: auto; margin-top: 15px;">
                        ${generateBatchResultsTable(results)}
                    </div>
                </details>
            </div>
        </div>
    `;
    
    safeSetHTML(resultsDiv, batchHTML);
    
    // Save batch results to session
    if (typeof saveBatchHTML === 'function') {
        saveBatchHTML(batchHTML);
    }
}

/**
 * GENERATE BATCH RESULTS CARDS: Erstellt moderne Data-Cards für Batch-Ergebnisse
 * PHASE 3: TABELLEN-REVOLUTION - Ersetzt hässliche HTML-Tabelle
 */
function generateBatchResultsTable(results) {
    if (!results || results.length === 0) {
        return `
            <div style="text-align: center; padding: var(--space-xl); color: var(--gray-500);">
                <h3>Keine Ergebnisse verfügbar</h3>
                <p>Es wurden keine Batch-Ergebnisse gefunden.</p>
            </div>
        `;
    }
    
    // Use our data-card system for batch results
    const batchCards = results.map((result, index) => {
        // Transform result to match our mine data card format
        const mineData = {
            mine_name: result.mine_name || 'Unbekannte Mine',
            country: result.country || 'Unbekannt',
            commodity: result.commodity || 'Unbekannt',
            model_used: result.model_used || 'Unbekannt',
            success: result.success,
            fields_found: result.structured_data ? Object.keys(result.structured_data).length : 0,
            result_index: index,
            raw_result: result
        };
        
        return generateBatchResultCard(mineData);
    }).join('');
    
    return `
        <div class="batch-results-header" style="margin-bottom: var(--space-lg);">
            <h3 style="margin: 0; color: #374151;">
                📊 Batch-Suchergebnisse 
                (${results.length} ${results.length === 1 ? 'Ergebnis' : 'Ergebnisse'})
            </h3>
        </div>
        <div class="data-card-grid">
            ${batchCards}
        </div>
    `;
}

/**
 * GENERATE BATCH RESULT CARD: Erstellt moderne Batch-Result-Card
 */
function generateBatchResultCard(mineData) {
    const mineName = mineData.mine_name;
    const country = mineData.country;
    const commodity = mineData.commodity;
    const model = mineData.model_used;
    const success = mineData.success;
    const fieldsFound = mineData.fields_found;
    const index = mineData.result_index;
    
    // Status styling
    const statusClass = success ? 'status-success' : 'status-error';
    const statusText = success ? '✅ Erfolg' : '❌ Fehler';
    const statusColor = success ? 'var(--success-600)' : 'var(--error-600)';
    
    // Quality indicator based on fields found
    let qualityLevel = 'Niedrig';
    let qualityClass = 'status-error';
    if (fieldsFound >= 15) {
        qualityLevel = 'Exzellent';
        qualityClass = 'status-success';
    } else if (fieldsFound >= 10) {
        qualityLevel = 'Gut';
        qualityClass = 'status-success';
    } else if (fieldsFound >= 5) {
        qualityLevel = 'Durchschnitt';
        qualityClass = 'status-warning';
    }
    
    return `
        <div class="mine-data-card batch-result-card" data-mine="${mineName}" data-index="${index}">
            <!-- CARD HEADER -->
            <div class="card-header">
                <h3 class="card-title">
                    🏭 ${mineName}
                </h3>
                <p class="card-subtitle">📍 ${country}</p>
                <div class="mine-type-badge ${statusClass}">
                    ${statusText}
                </div>
            </div>
            
            <!-- CARD BODY -->
            <div class="card-body">
                <div class="data-row">
                    <span class="data-label">🌍 Land</span>
                    <span class="data-value">${country}</span>
                </div>
                
                <div class="data-row">
                    <span class="data-label">⚖️ Rohstoff</span>
                    <span class="data-value">${commodity}</span>
                </div>
                
                <div class="data-row">
                    <span class="data-label">📊 Gefundene Felder</span>
                    <span class="data-value" style="font-size: 1.2em; color: var(--primary-600);">
                        ${fieldsFound} Felder
                    </span>
                </div>
                
                <div class="data-row">
                    <span class="data-label">📈 Datenqualität</span>
                    <span class="status-indicator ${qualityClass}">
                        ${qualityLevel}
                    </span>
                </div>
                
                <div class="data-row">
                    <span class="data-label">🤖 Modell</span>
                    <span class="data-value" style="font-size: 0.9em;">
                        ${model}
                    </span>
                </div>
            </div>
            
            <!-- CARD ACTIONS -->
            <div class="card-actions">
                <div>
                    <button class="action-button" onclick="viewResultDetail(${index}, ${safeJSONStringify(mineData.raw_result)})">
                        📊 Details anzeigen
                    </button>
                    <button class="action-button secondary" onclick="exportSearchResults('${mineName}')">
                        📤 Exportieren
                    </button>
                </div>
                <div>
                    <button class="action-button secondary" onclick="saveToFavorites('${mineName}')">
                        ⭐ Merken
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// RESULT INTERACTION FUNCTIONS
// ============================================

/**
 * VIEW RESULT DETAIL: Zeigt Details eines Einzelergebnisses
 */
window.viewResultDetail = function(index, result) {
    if (!result) {
        console.error('❌ [RESULTS] No result data provided for detail view');
        return;
    }
    
    console.log(`🔍 [RESULTS] Showing detail for result ${index}:`, result.mine_name);
    
    // Create modal or detailed view
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background: rgba(0,0,0,0.5); z-index: 10000; 
        display: flex; justify-content: center; align-items: center;
    `;
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 8px; padding: 30px; max-width: 800px; max-height: 80vh; overflow-y: auto; position: relative;">
            <button onclick="this.closest('[style*=\"position: fixed\"]').remove()" 
                    style="position: absolute; top: 10px; right: 15px; background: none; border: none; font-size: 24px; cursor: pointer; color: #666;">
                ×
            </button>
            
            <h3 style="margin: 0 0 20px 0; color: #374151;">🔍 Ergebnis-Details: ${sanitizeHTML(result.mine_name || 'Unbekannt')}</h3>
            
            <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <div><strong>Status:</strong> ${result.success ? '✅ Erfolgreich' : '❌ Fehlgeschlagen'}</div>
                <div><strong>Modell:</strong> ${sanitizeHTML(result.model_used || 'Unbekannt')}</div>
                <div><strong>Felder gefunden:</strong> ${result.structured_data ? Object.keys(result.structured_data).length : 0}</div>
            </div>
            
            <pre style="background: #f1f5f9; padding: 20px; border-radius: 6px; white-space: pre-wrap; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.4; max-height: 400px; overflow-y: auto;">${sanitizeHTML(JSON.stringify(result, null, 2))}</pre>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
};

/**
 * EXPORT SEARCH RESULTS: Exportiert Suchergebnisse
 */
window.exportSearchResults = function(mineName) {
    console.log(`📥 [RESULTS] Exporting search results for: ${mineName}`);
    showNotification('Export-Funktion wird implementiert...', 'info');
};

/**
 * EXPORT BATCH RESULTS: Exportiert alle Batch-Ergebnisse
 */
window.exportBatchResults = function() {
    console.log('📥 [RESULTS] Exporting all batch results');
    showNotification('Batch-Export wird implementiert...', 'info');
};

/**
 * RETRY LAST SEARCH: Wiederholt letzte Suche
 */
window.retryLastSearch = function() {
    console.log('🔄 [RESULTS] Retrying last search');
    showNotification('Wiederholung der letzten Suche...', 'info');
    
    // Trigger last search if available
    if (typeof startSingleSearch === 'function') {
        setTimeout(() => {
            startSingleSearch();
        }, 1000);
    }
};

// ============================================
// GLOBAL EXPORTS
// ============================================

// ============================================
// PHASE 3: RESULTS PRESENTATION REVOLUTION
// Modern Card-based Results Display
// ============================================

/**
 * RESULTS REVOLUTION: Generate Modern Result Card
 */
function generateModernResultCard(data) {
    console.log('🎨 [RESULTS-CARD] Generating modern result card...');
    
    const mineName = data.mine_name || 'Unbekannt';
    const mineLocation = data.location || data.land || 'Unbekannt';
    const mineType = data.mine_type || data.rohstoff || 'Unbekannt';
    
    // Extract key metrics
    const keyMetrics = extractKeyMetrics(data);
    const qualityScore = calculateDataQuality(data);
    
    return `
        <div class="results-revolution-container">
            <div class="result-card modern-card">
                <!-- Card Header -->
                <div class="card-header">
                    <div class="mine-info">
                        <h2 class="mine-title">⛏️ ${sanitizeHTML(mineName)}</h2>
                        <div class="mine-meta">
                            <span class="location-tag">📍 ${sanitizeHTML(mineLocation)}</span>
                            <span class="type-tag">💎 ${sanitizeHTML(mineType)}</span>
                            <div class="quality-score ${getQualityClass(qualityScore)}">
                                <span class="score-label">Datenqualität:</span>
                                <span class="score-value">${qualityScore}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="action-btn primary" onclick="exportSearchResults('${mineName}')">
                            📥 Export
                        </button>
                        <button class="action-btn secondary" onclick="shareResult('${mineName}')">
                            🔗 Teilen
                        </button>
                    </div>
                </div>

                <!-- Key Metrics Grid -->
                <div class="metrics-grid">
                    ${generateMetricsCards(keyMetrics)}
                </div>

                <!-- Interactive Sections -->
                <div class="result-sections">
                    <!-- Quick Summary -->
                    <div class="section-card summary-section">
                        <div class="section-header">
                            <h4>📊 Zusammenfassung</h4>
                            <span class="expand-btn" onclick="toggleSection('summary')">▼</span>
                        </div>
                        <div class="section-content" id="summary-content">
                            ${generateSmartSummary(data)}
                        </div>
                    </div>

                    <!-- Financial Data -->
                    ${generateFinancialSection(data)}

                    <!-- Technical Data -->
                    ${generateTechnicalSection(data)}

                    <!-- Environmental Data -->
                    ${generateEnvironmentalSection(data)}
                </div>

                <!-- Raw Data (Collapsed by default) -->
                <div class="section-card raw-data-section">
                    <div class="section-header" onclick="toggleSection('raw-data')">
                        <h4>🔧 Vollständige Rohdaten</h4>
                        <span class="expand-btn">▼</span>
                    </div>
                    <div class="section-content collapsed" id="raw-data-content">
                        <div class="json-viewer">
                            <pre class="json-data">${sanitizeHTML(JSON.stringify(data, null, 2))}</pre>
                        </div>
                    </div>
                </div>

                <!-- Result Footer -->
                <div class="card-footer">
                    <div class="result-timestamp">
                        ⏰ Erstellt: ${new Date().toLocaleString('de-DE')}
                    </div>
                    <div class="result-actions">
                        <button class="action-link" onclick="retryLastSearch()">
                            🔄 Neu suchen
                        </button>
                        <button class="action-link" onclick="saveToFavorites('${mineName}')">
                            ⭐ Zu Favoriten
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Helper Functions for Results Revolution
function extractKeyMetrics(data) {
    const metrics = [];
    
    if (data.foerdermenge || data.production) {
        metrics.push({ label: 'Förderung', value: data.foerdermenge || data.production, unit: 't/Jahr', icon: '⚡', type: 'production' });
    }
    if (data.revenues || data.umsatz) {
        metrics.push({ label: 'Umsatz', value: data.revenues || data.umsatz, unit: '€', icon: '💰', type: 'financial' });
    }
    if (data.employees || data.mitarbeiter) {
        metrics.push({ label: 'Mitarbeiter', value: data.employees || data.mitarbeiter, unit: 'Personen', icon: '👥', type: 'employment' });
    }
    if (data.area || data.flaeche) {
        metrics.push({ label: 'Fläche', value: data.area || data.flaeche, unit: 'km²', icon: '🗺️', type: 'area' });
    }
    
    return metrics;
}

function calculateDataQuality(data) {
    const importantFields = ['mine_name', 'location', 'mine_type', 'rohstoff', 'foerdermenge', 'production', 'revenues', 'umsatz', 'employees', 'mitarbeiter'];
    let filledFields = 0;
    importantFields.forEach(field => {
        if (data[field] && data[field] !== 'Unbekannt' && data[field] !== '') filledFields++;
    });
    return Math.round((filledFields / importantFields.length) * 100);
}

function getQualityClass(score) {
    if (score >= 80) return 'quality-excellent';
    if (score >= 60) return 'quality-good';
    if (score >= 40) return 'quality-fair';
    return 'quality-poor';
}

function generateMetricsCards(metrics) {
    if (metrics.length === 0) return '<div class="no-metrics">📊 Mining-Kennzahlen werden geladen...</div>';
    
    return metrics.map(metric => `
        <div class="metric-card ${metric.type}">
            <div class="metric-icon">${metric.icon}</div>
            <div class="metric-content">
                <div class="metric-label">${metric.label}</div>
                <div class="metric-value">${metric.value} <span class="metric-unit">${metric.unit}</span></div>
            </div>
        </div>
    `).join('');
}

function generateSmartSummary(data) {
    const mineName = data.mine_name || 'Diese Mine';
    const location = data.location || data.land;
    const type = data.mine_type || data.rohstoff;
    
    let summary = `${mineName}`;
    if (location) summary += ` befindet sich in ${location}`;
    if (type) summary += ` und produziert ${type}`;
    if (data.foerdermenge || data.production) summary += `. Die jährliche Förderung beträgt ${data.foerdermenge || data.production}.`;
    if (data.employees || data.mitarbeiter) summary += ` Das Unternehmen beschäftigt ${data.employees || data.mitarbeiter} Mitarbeiter.`;
    
    return summary || 'Keine detaillierten Informationen verfügbar.';
}

function generateFinancialSection(data) {
    const hasFinancialData = data.revenues || data.umsatz || data.costs || data.kosten || data.profit || data.gewinn;
    if (!hasFinancialData) return '';
    
    return `
        <div class="section-card financial-section">
            <div class="section-header" onclick="toggleSection('financial')">
                <h4>💰 Finanzdaten</h4>
                <span class="expand-btn">▼</span>
            </div>
            <div class="section-content collapsed" id="financial-content">
                <div class="financial-grid">
                    ${data.revenues || data.umsatz ? `<div class="financial-item"><span class="label">Umsatz:</span><span class="value">${data.revenues || data.umsatz}</span></div>` : ''}
                    ${data.costs || data.kosten ? `<div class="financial-item"><span class="label">Kosten:</span><span class="value">${data.costs || data.kosten}</span></div>` : ''}
                    ${data.profit || data.gewinn ? `<div class="financial-item"><span class="label">Gewinn:</span><span class="value">${data.profit || data.gewinn}</span></div>` : ''}
                </div>
            </div>
        </div>
    `;
}

function generateTechnicalSection(data) {
    const hasTechnicalData = data.equipment || data.ausstattung || data.technology || data.technologie;
    if (!hasTechnicalData) return '';
    
    return `
        <div class="section-card technical-section">
            <div class="section-header" onclick="toggleSection('technical')">
                <h4>🔧 Technische Daten</h4>
                <span class="expand-btn">▼</span>
            </div>
            <div class="section-content collapsed" id="technical-content">
                <div class="technical-grid">
                    ${data.equipment || data.ausstattung ? `<div class="technical-item"><span class="label">Ausstattung:</span><span class="value">${data.equipment || data.ausstattung}</span></div>` : ''}
                    ${data.technology || data.technologie ? `<div class="technical-item"><span class="label">Technologie:</span><span class="value">${data.technology || data.technologie}</span></div>` : ''}
                </div>
            </div>
        </div>
    `;
}

function generateEnvironmentalSection(data) {
    const hasEnvironmentalData = data.environmental_impact || data.umwelt || data.sustainability || data.nachhaltigkeit;
    if (!hasEnvironmentalData) return '';
    
    return `
        <div class="section-card environmental-section">
            <div class="section-header" onclick="toggleSection('environmental')">
                <h4>🌱 Umwelt & Nachhaltigkeit</h4>
                <span class="expand-btn">▼</span>
            </div>
            <div class="section-content collapsed" id="environmental-content">
                <div class="environmental-grid">
                    ${data.environmental_impact || data.umwelt ? `<div class="environmental-item"><span class="label">Umweltauswirkung:</span><span class="value">${data.environmental_impact || data.umwelt}</span></div>` : ''}
                    ${data.sustainability || data.nachhaltigkeit ? `<div class="environmental-item"><span class="label">Nachhaltigkeit:</span><span class="value">${data.sustainability || data.nachhaltigkeit}</span></div>` : ''}
                </div>
            </div>
        </div>
    `;
}

function toggleSection(sectionId) {
    const content = document.getElementById(`${sectionId}-content`);
    const expandBtn = content?.parentElement.querySelector('.expand-btn');
    
    if (content && expandBtn) {
        if (content.classList.contains('collapsed')) {
            content.classList.remove('collapsed');
            expandBtn.textContent = '▲';
        } else {
            content.classList.add('collapsed');
            expandBtn.textContent = '▼';
        }
        console.log(`🔄 [RESULTS-CARD] Toggled section: ${sectionId}`);
    }
}

function shareResult(mineName) {
    const url = window.location.href;
    const text = `Schaue dir diese Mining-Daten für ${mineName} an:`;
    
    if (navigator.share) {
        navigator.share({ title: `Mining Daten: ${mineName}`, text, url });
    } else {
        navigator.clipboard.writeText(`${text} ${url}`);
        if (typeof showNotification === 'function') {
            showNotification('Link in Zwischenablage kopiert', 'success');
        }
    }
    console.log(`🔗 [RESULTS-CARD] Shared result for: ${mineName}`);
}

function saveToFavorites(mineName) {
    const favorites = JSON.parse(localStorage.getItem('mining_favorites') || '[]');
    
    if (!favorites.includes(mineName)) {
        favorites.push(mineName);
        localStorage.setItem('mining_favorites', JSON.stringify(favorites));
        if (typeof showNotification === 'function') {
            showNotification(`${mineName} zu Favoriten hinzugefügt`, 'success');
        }
    } else {
        if (typeof showNotification === 'function') {
            showNotification(`${mineName} bereits in Favoriten`, 'info');
        }
    }
    console.log(`⭐ [RESULTS-CARD] Added to favorites: ${mineName}`);
}

// Export result processing functions to global scope
window.displayResults = displayResults;
window.generateResultSummary = generateResultSummary;
window.preserveAccordionState = preserveAccordionState;
window.restoreAccordionState = restoreAccordionState;
window.processSearchResults = processSearchResults;
window.displayBatchResults = displayBatchResults;
window.generateBatchResultsTable = generateBatchResultsTable;

// Export Results Revolution functions
window.generateModernResultCard = generateModernResultCard;
window.toggleSection = toggleSection;
window.shareResult = shareResult;
window.saveToFavorites = saveToFavorites;

// ============================================
// PHASE 4: MULTI-MODEL COMPARISON FUNCTIONS
// ============================================

/**
 * MULTI-MODEL COMPARISON: Zeigt Interactive Comparison für mehrere Modelle
 */
async function displayMultiModelComparison(successfulResults, fullData) {
    console.log(`🔬 [PHASE 4] Displaying interactive comparison for ${successfulResults.length} models`);
    
    const resultsDiv = document.getElementById('results');
    
    try {
        // Generate comparison using Phase 4 engine
        const comparison = await window.generateComparison(successfulResults);
        
        // Generate comparison UI
        const comparisonHTML = window.generateComparisonView(comparison);
        
        // Add meta information about the search
        const searchInfo = fullData.search_query || 'Multi-Model Search';
        const timestamp = new Date().toLocaleString();
        
        const fullHTML = `
            <div class="multi-model-results">
                <div class="search-metadata">
                    <h2>🔬 Multi-Model Analysis Results</h2>
                    <div class="search-info">
                        <span class="search-query">${searchInfo}</span>
                        <span class="search-timestamp">${timestamp}</span>
                    </div>
                </div>
                
                ${comparisonHTML}
                
                <div class="individual-results-toggle">
                    <button onclick="toggleIndividualResults()" class="toggle-btn">
                        📋 Show Individual Model Results
                    </button>
                    <div id="individual-results" style="display: none;">
                        ${generateIndividualModelResults(successfulResults)}
                    </div>
                </div>
            </div>
        `;
        
        safeSetHTML(resultsDiv, fullHTML);
        
        // Save to session storage for restoration
        if (typeof saveSearchResults === 'function') {
            saveSearchResults({
                success: true,
                data: fullData,
                comparison: comparison
            }, 'multi-model');
        }
        
        console.log('✅ [PHASE 4] Multi-model comparison displayed successfully');
        
    } catch (error) {
        console.error('❌ [PHASE 4] Error displaying comparison:', error);
        
        // Fallback to individual results
        displayIndividualResultsFallback(successfulResults);
    }
}

/**
 * SINGLE MODEL FROM MULTI: Zeigt einzelnes erfolgreiches Ergebnis aus Multi-Search
 */
function displaySingleModelFromMulti(result, fullData) {
    console.log('📊 [PHASE 4] Displaying single successful model from multi-search');
    
    const resultsDiv = document.getElementById('results');
    
    const searchInfo = fullData.search_query || 'Multi-Model Search';
    const totalModels = fullData.total_models || 1;
    const successfulModels = fullData.successful_models || 1;
    
    const singleResultHTML = `
        <div class="single-from-multi">
            <div class="search-metadata">
                <h2>📊 Search Results</h2>
                <div class="search-info">
                    <span class="search-query">${searchInfo}</span>
                    <span class="model-info">${successfulModels}/${totalModels} models successful</span>
                </div>
                <div class="search-warning">
                    ⚠️ Only one model returned results. For better insights, try different models or check your search criteria.
                </div>
            </div>
            
            <div class="successful-model">
                <h3>✅ Successful Model: ${result.model_id}</h3>
                ${generateModernResultCard(result.data)}
            </div>
            
            ${fullData.results.length > 1 ? generateFailedModelsInfo(fullData.results.filter(r => !r.success)) : ''}
        </div>
    `;
    
    safeSetHTML(resultsDiv, singleResultHTML);
}

/**
 * MULTI MODEL ERRORS: Zeigt Fehler-Zusammenfassung für Multi-Model-Search
 */
function displayMultiModelErrors(results) {
    console.log('❌ [PHASE 4] Displaying multi-model errors');
    
    const resultsDiv = document.getElementById('results');
    
    const errorSummary = results.map(result => ({
        model: result.model_id,
        error: result.error || 'Unknown error',
        success: result.success
    }));
    
    const errorHTML = errorSummary.map(item => `
        <div class="model-error">
            <div class="model-name">${item.model}</div>
            <div class="error-message">${item.error}</div>
        </div>
    `).join('');
    
    const fullErrorHTML = `
        <div class="multi-model-errors">
            <div class="error-header">
                <h2>❌ Multi-Model Search Failed</h2>
                <p>No models returned successful results. Please check the errors below:</p>
            </div>
            
            <div class="error-list">
                ${errorHTML}
            </div>
            
            <div class="error-suggestions">
                <h3>💡 Suggestions:</h3>
                <ul>
                    <li>Try different models from the Quick Selection</li>
                    <li>Check your API keys in the provider settings</li>
                    <li>Simplify your search criteria</li>
                    <li>Try a single model search first</li>
                </ul>
            </div>
        </div>
    `;
    
    safeSetHTML(resultsDiv, fullErrorHTML);
}

/**
 * INDIVIDUAL MODEL RESULTS: Generiert Einzelergebnisse für Vergleich
 */
function generateIndividualModelResults(results) {
    console.log('📋 [PHASE 4] Generating individual model results');
    
    return results.map((result, index) => `
        <div class="individual-model-result" data-model="${result.model_id}">
            <div class="model-header">
                <h3>${result.model_id}</h3>
                <div class="model-meta">
                    Model ${index + 1} of ${results.length} • 
                    ${result.data.quality_metrics ? Math.round(result.data.quality_metrics.quality_score * 100) + '% quality' : 'N/A'}
                </div>
            </div>
            <div class="model-result-content">
                ${generateModernResultCard(result.data)}
            </div>
        </div>
    `).join('');
}

/**
 * FAILED MODELS INFO: Zeigt Information über fehlgeschlagene Modelle
 */
function generateFailedModelsInfo(failedResults) {
    if (!failedResults || failedResults.length === 0) return '';
    
    const failedHTML = failedResults.map(result => `
        <div class="failed-model">
            <span class="model-name">${result.model_id}</span>
            <span class="error-message">${(result.error || 'Unknown error').substring(0, 100)}...</span>
        </div>
    `).join('');
    
    return `
        <div class="failed-models-section">
            <h4>❌ Failed Models (${failedResults.length})</h4>
            <div class="failed-models-list">
                ${failedHTML}
            </div>
        </div>
    `;
}

/**
 * INDIVIDUAL RESULTS FALLBACK: Fallback für Comparison-Fehler
 */
function displayIndividualResultsFallback(results) {
    console.log('🔄 [PHASE 4] Using fallback: individual results display');
    
    const resultsDiv = document.getElementById('results');
    
    const fallbackHTML = `
        <div class="comparison-fallback">
            <div class="fallback-header">
                <h2>📊 Individual Model Results</h2>
                <p>Comparison analysis temporarily unavailable. Showing individual results:</p>
            </div>
            
            ${generateIndividualModelResults(results)}
        </div>
    `;
    
    safeSetHTML(resultsDiv, fallbackHTML);
}

/**
 * TOGGLE INDIVIDUAL RESULTS: Zeigt/versteckt individuelle Ergebnisse
 */
function toggleIndividualResults() {
    const individualDiv = document.getElementById('individual-results');
    const toggleBtn = document.querySelector('.toggle-btn');
    
    if (individualDiv && toggleBtn) {
        if (individualDiv.style.display === 'none') {
            individualDiv.style.display = 'block';
            toggleBtn.textContent = '📋 Hide Individual Model Results';
        } else {
            individualDiv.style.display = 'none';
            toggleBtn.textContent = '📋 Show Individual Model Results';
        }
    }
}

// Export Phase 4 functions
window.displayMultiModelComparison = displayMultiModelComparison;
window.displaySingleModelFromMulti = displaySingleModelFromMulti;
window.displayMultiModelErrors = displayMultiModelErrors;
window.toggleIndividualResults = toggleIndividualResults;

console.log('📊 MineSearch 2.0 - Results Processor with Revolution loaded');