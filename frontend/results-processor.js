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
 * DISPLAY RESULTS: Zeigt Suchergebnisse an
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
        if (data.success && data.data) {
            // Success case
            console.log('✅ [RESULTS] Displaying successful results');
            
            // Save results to session for restoration
            if (typeof saveSearchResults === 'function') {
                saveSearchResults(data, 'single');
            }
            
            // Display results
            const resultHTML = `
                <div style="padding: 20px; background: #f0fdf4; border-radius: 8px; border: 1px solid #10b981; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 15px;">
                        <h3 style="margin: 0; color: #059669;">✅ Suchergebnis für: ${sanitizeHTML(data.data.mine_name || 'Unbekannt')}</h3>
                        <button onclick="exportSearchResults('${data.data.mine_name || 'result'}')" 
                                style="background: #059669; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            📥 Exportieren
                        </button>
                    </div>
                    
                    ${generateResultSummary(data.data)}
                    
                    <div class="result-details" style="margin-top: 20px;">
                        <details style="background: #f9f9f9; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0;">
                            <summary style="cursor: pointer; font-weight: bold; color: #374151; margin-bottom: 10px;">
                                📋 Vollständige Daten anzeigen
                            </summary>
                            <pre style="background: #ffffff; padding: 15px; border-radius: 4px; white-space: pre-wrap; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.4; border: 1px solid #d1d5db; margin-top: 10px;">${sanitizeHTML(JSON.stringify(data.data, null, 2))}</pre>
                        </details>
                    </div>
                </div>
            `;
            
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
 * GENERATE BATCH RESULTS TABLE: Erstellt Tabelle für Batch-Ergebnisse
 */
function generateBatchResultsTable(results) {
    if (!results || results.length === 0) {
        return '<p>Keine Ergebnisse verfügbar</p>';
    }
    
    const tableRows = results.map((result, index) => {
        const status = result.success ? 
            '<span style="color: #059669; font-weight: bold;">✅ Erfolg</span>' : 
            '<span style="color: #dc2626; font-weight: bold;">❌ Fehler</span>';
        
        const fieldsFound = result.structured_data ? Object.keys(result.structured_data).length : 0;
        
        return `
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 8px; text-align: center;">${index + 1}</td>
                <td style="padding: 8px; font-weight: 500;">${sanitizeHTML(result.mine_name || 'Unbekannt')}</td>
                <td style="padding: 8px;">${sanitizeHTML(result.country || 'Unbekannt')}</td>
                <td style="padding: 8px;">${sanitizeHTML(result.commodity || 'Unbekannt')}</td>
                <td style="padding: 8px; text-align: center;">${status}</td>
                <td style="padding: 8px; text-align: center;">${fieldsFound}</td>
                <td style="padding: 8px; font-size: 11px;">${sanitizeHTML(result.model_used || 'Unbekannt')}</td>
                <td style="padding: 8px; text-align: center;">
                    <button onclick="viewResultDetail(${index}, ${safeJSONStringify(result)})" 
                            style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px;">
                        Details
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    return `
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #e5e7eb; font-size: 13px;">
            <thead style="background: #f9fafb;">
                <tr>
                    <th style="padding: 12px 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e5e7eb;">#</th>
                    <th style="padding: 12px 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e5e7eb;">Mine</th>
                    <th style="padding: 12px 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e5e7eb;">Land</th>
                    <th style="padding: 12px 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e5e7eb;">Rohstoff</th>
                    <th style="padding: 12px 8px; text-align: center; font-weight: 600; border-bottom: 1px solid #e5e7eb;">Status</th>
                    <th style="padding: 12px 8px; text-align: center; font-weight: 600; border-bottom: 1px solid #e5e7eb;">Felder</th>
                    <th style="padding: 12px 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e5e7eb;">Modell</th>
                    <th style="padding: 12px 8px; text-align: center; font-weight: 600; border-bottom: 1px solid #e5e7eb;">Aktionen</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
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

// Export result processing functions to global scope
window.displayResults = displayResults;
window.generateResultSummary = generateResultSummary;
window.preserveAccordionState = preserveAccordionState;
window.restoreAccordionState = restoreAccordionState;
window.processSearchResults = processSearchResults;
window.displayBatchResults = displayBatchResults;
window.generateBatchResultsTable = generateBatchResultsTable;

console.log('📊 MineSearch 2.0 - Results Processor loaded');