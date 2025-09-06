/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - Search Functions & Logic
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (8498 → 500 Zeilen Regel)
 * Search Functions: Single Search, Batch Search, Model Loading, Form Validation
 */

// ============================================
// SEARCH EXECUTION FUNCTIONS
// ============================================

// Batch-Konstanten
const BATCH_MAX_COUNT = 1000;
const BATCH_WARNING_THRESHOLD = 200;
const BATCH_STRONG_THRESHOLD = 500;
const BATCH_DEFAULT_CHUNK_SIZE = 250;

// UI-Handler für Batch Count Eingabe (global verfügbar)
function handleBatchCountInput() {
    const input = document.getElementById('batch-count');
    const warn = document.getElementById('batch-count-warning');
    if (!input) return;
    let value = parseInt(input.value || '0');
    if (isNaN(value) || value < 1) value = 1;
    if (value > BATCH_MAX_COUNT) {
        value = BATCH_MAX_COUNT;
        if (typeof showNotification === 'function') {
            showNotification(`Maximale Batch-Größe ist ${BATCH_MAX_COUNT}. Wert wurde angepasst.`, 'warning');
        }
    }
    input.value = value;
    if (warn) {
        if (value > BATCH_STRONG_THRESHOLD) {
            warn.style.display = 'block';
            warn.style.color = '#b45309';
            warn.textContent = '⚠️ Sehr große Batches können langsam sein oder Zeitüberschreitungen verursachen. Wir empfehlen Pagination in Teilpaketen.';
        } else if (value > BATCH_WARNING_THRESHOLD) {
            warn.style.display = 'block';
            warn.style.color = '#92400e';
            warn.textContent = 'ℹ️ Große Batches können länger dauern. Erwägen Sie Pagination in Teilpaketen.';
        } else {
            warn.style.display = 'none';
        }
    }
}

// UI-Handler für Batch Options Toggle (Erweiterte Auswahl-Modi)
function toggleBatchOptions() {
    const selectedMode = document.querySelector('input[name="batch_mode"]:checked')?.value;
    
    // Alle Option-Divs verstecken
    const rangeOptions = document.getElementById('range-options');
    const randomOptions = document.getElementById('random-options');
    
    if (rangeOptions) rangeOptions.style.display = 'none';
    if (randomOptions) randomOptions.style.display = 'none';
    
    // Je nach Modus entsprechende Optionen anzeigen
    if (selectedMode === 'range' && rangeOptions) {
        rangeOptions.style.display = 'block';
        updateRangeInfo();
    } else if (selectedMode === 'random' && randomOptions) {
        randomOptions.style.display = 'block';
    }
}

// Range-Info dynamisch aktualisieren
function updateRangeInfo() {
    const startPos = parseInt(document.getElementById('start-position')?.value || '1');
    const count = parseInt(document.getElementById('range-count')?.value || '20');
    const rangeInfo = document.getElementById('range-info');
    
    if (rangeInfo) {
        const endPos = startPos + count - 1;
        rangeInfo.textContent = `Sucht Minen ${startPos}-${endPos} aus der CSV`;
    }
}

// Event Listeners für Range-Inputs
document.addEventListener('DOMContentLoaded', function() {
    const startInput = document.getElementById('start-position');
    const countInput = document.getElementById('range-count');
    
    if (startInput) {
        startInput.addEventListener('input', updateRangeInfo);
    }
    if (countInput) {
        countInput.addEventListener('input', updateRangeInfo);
    }
});

/**
 * SINGLE SEARCH: Startet eine Einzelsuche mit ausgewählten Modellen
 */
function startSingleSearch() {
    // PROGRESSIVE MODEL SELECTION FIX: Verwende neues Model Selection System
    const selectedModels = window.progressiveModelSelection?.getSelectedModels() || 
                           Array.from(document.querySelectorAll('input[name="model"]:checked')).map(cb => cb.value);
    
    if (selectedModels.length === 0) {
        showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
        return;
    }
    
    // Hole Search-Optionen (mit Null-Checks für fehlende Elements)
    const twoPhaseElement = document.getElementById('two_phase_enabled');
    const smartSearchElement = document.getElementById('smart_search_enabled');  
    const comprehensiveElement = document.getElementById('comprehensive_search_enabled');
    
    const twoPhaseEnabled = twoPhaseElement ? twoPhaseElement.checked : false;
    const smartSearchEnabled = smartSearchElement ? smartSearchElement.checked : false;
    const comprehensiveSearchEnabled = comprehensiveElement ? comprehensiveElement.checked : false;
    
    const formData = new FormData(document.getElementById('single-search-form'));
    
    const requestBody = {
        mine_name: formData.get('mine_name'),
        country: formData.get('country'),
        commodity: formData.get('commodity'),
        model_ids: selectedModels,
        comprehensive_search: comprehensiveSearchEnabled
    };
    
    let searchTypeText = "Standard-Suche";
    if (comprehensiveSearchEnabled) {
        searchTypeText = "🚀 Comprehensive Search";
    } else if (smartSearchEnabled) {
        searchTypeText = "🤖 Smart-Search";
    } else if (twoPhaseEnabled) {
        searchTypeText = "🔍 2-Phasen-Suche";
    }
    
    console.log(`🔍 [SEARCH] Starte ${searchTypeText} mit ${selectedModels.length} Modellen`);
    console.log(`📋 [SEARCH] Request Body:`, requestBody);
    
    // Initialize AbortController für Single Search
    singleSearchAbortController = new AbortController();
    
    const resultsDiv = document.getElementById('results');
    showLoadingMessage(resultsDiv, `${searchTypeText} läuft...`, 
        `Mine: ${requestBody.mine_name || 'Alle'} | Land: ${requestBody.country || 'Alle'} | Rohstoff: ${requestBody.commodity || 'Alle'}`, 
        true, true, 'cancelSingleSearch()'  // Show cancel button for Single Search
    );
    
    // Timer wird bereits durch showLoadingMessage(startTimer=true) gestartet
    console.log('🕒 [TIMER] Timer should be started by showLoadingMessage');
    
    fetch(`${window.API_BASE_URL}/api/search/multi`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody),
        signal: singleSearchAbortController.signal  // Add AbortController signal
    })
    .then(response => response.json())
    .then(data => {
        console.log(`✅ [SEARCH] Response received:`, data);
        
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        if (data.success) {
            displayResults(data);  // CRITICAL FIX: Pass full data object, not just data.data
            showNotification(`✅ ${searchTypeText} erfolgreich abgeschlossen`, 'success');
            
            // 🚀 ENHANCED: Smart Auto-Refresh aller Tabs nach erfolgreicher Einzelsuche
            if (typeof window.smartRefreshAfterSearch === 'function') {
                window.smartRefreshAfterSearch('single');
                console.log('📊 [SEARCH-SUCCESS] Scheduled smart tab refresh after successful single search');
            } else if (typeof window.scheduleStatisticsRefresh === 'function') {
                // Fallback: nur Statistics (Legacy)
                window.scheduleStatisticsRefresh(3000);
                console.log('📊 [SEARCH-SUCCESS] Scheduled statistics refresh after successful search (fallback)');
            }
        } else {
            console.error(`❌ [SEARCH] API Error:`, data.error);
            resultsDiv.innerHTML = createErrorHTML('Suche fehlgeschlagen', data.error || 'Unbekannter Fehler');
            showNotification(`❌ Suche fehlgeschlagen: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        // Check if search was aborted by user
        if (error.name === 'AbortError') {
            console.log('🛑 [SEARCH] Single search was aborted by user');
            // Don't show error notification for user-initiated abort
            // UI is already updated by cancelSingleSearch()
            return;
        }
        
        console.error(`❌ [SEARCH] Network Error:`, error);
        
        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
            window.searchTimer.stop();
        }
        
        resultsDiv.innerHTML = createErrorHTML('Verbindungsfehler', 'Bitte überprüfen Sie Ihre Netzwerkverbindung.');
        showNotification(`❌ Verbindungsfehler: ${error.message}`, 'error');
    });
}

/**
 * BATCH SEARCH: Startet eine Batch-Suche mit 2-Schritt-Workflow (CSV Upload + Batch Search)
 * ÄNDERUNG 13.08.2025: Implementierung des korrekten Backend-Workflows
 * ÄNDERUNG 14.08.2025: AbortController Support für Abbruch-Funktion
 */

// Global abort controllers
let batchSearchAbortController = null;
let singleSearchAbortController = null;

async function startBatchSearch() {
    const formData = new FormData(document.getElementById('csv-form'));
    
    // Validiere Eingaben
    const csvFile = formData.get('file');
    // PROGRESSIVE MODEL SELECTION FIX: Verwende neues Model Selection System
    const selectedModels = window.progressiveModelSelection?.getSelectedModels() || 
                           Array.from(document.querySelectorAll('input[name="model"]:checked')).map(cb => cb.value);
    
    if (!csvFile || csvFile.size === 0) {
        showNotification('Bitte wählen Sie eine CSV-Datei aus.', 'warning');
        return;
    }
    
    if (selectedModels.length === 0) {
        showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
        return;
    }
    
    // Hole Batch-Search-Optionen (mit Null-Checks für fehlende Elements)
    const batchTwoPhaseElement = document.getElementById('batch_two_phase_enabled');
    const batchSmartSearchElement = document.getElementById('batch_smart_search_enabled');
    const batchComprehensiveElement = document.getElementById('batch_comprehensive_search_enabled');
    
    const twoPhaseEnabled = batchTwoPhaseElement ? batchTwoPhaseElement.checked : false;
    const smartSearchEnabled = batchSmartSearchElement ? batchSmartSearchElement.checked : false;
    const comprehensiveSearchEnabled = batchComprehensiveElement ? batchComprehensiveElement.checked : false;
    
    // ENHANCED BATCH: Batch Selection Optionen auslesen
    const batchModeElement = document.querySelector('input[name="batch_mode"]:checked');
    const batchCountElement = document.getElementById('batch-count');
    const startPositionElement = document.getElementById('start-position');
    const rangeCountElement = document.getElementById('range-count');
    const randomCountElement = document.getElementById('random-count');
    
    const batchMode = batchModeElement ? batchModeElement.value : 'limited'; // Default: limited
    const batchCount = batchCountElement ? parseInt(batchCountElement.value) : 3; // Default: 3
    const startPosition = startPositionElement ? parseInt(startPositionElement.value) : 1; // Default: 1
    const rangeCount = rangeCountElement ? parseInt(rangeCountElement.value) : 20; // Default: 20
    const randomCount = randomCountElement ? parseInt(randomCountElement.value) : 10; // Default: 10
    
    // Validierung
    if (batchMode === 'limited' && (isNaN(batchCount) || batchCount < 1 || batchCount > BATCH_MAX_COUNT)) {
        showNotification(`Die Anzahl der Minen muss zwischen 1 und ${BATCH_MAX_COUNT} liegen.`, 'warning');
        return;
    }
    
    console.log(`📊 [BATCH-OPTIONS] Mode: ${batchMode}, Count: ${batchCount}`);
    
    let searchTypeText = "Batch Standard-Suche";
    if (comprehensiveSearchEnabled) {
        searchTypeText = "🚀 Batch Comprehensive Search";
    } else if (smartSearchEnabled) {
        searchTypeText = "🤖 Batch Smart-Search";
    } else if (twoPhaseEnabled) {
        searchTypeText = "🔍 Batch 2-Phasen-Suche";
    }
    
    // Erweitere Search Type Text mit Count-Information
    const countText = batchMode === 'all' ? 'alle Minen' : `erste ${batchCount} Minen`;
    console.log(`📊 [BATCH-SEARCH] Starte ${searchTypeText} mit ${selectedModels.length} Modellen für ${countText}`);
    
    // Erstelle neue AbortController für diese Suche
    batchSearchAbortController = new AbortController();
    const signal = batchSearchAbortController.signal;
    
    const resultsDiv = document.getElementById('batch-results');
    
    // PROGRESS-MERGE 29.08.2025: Zeige nur Progress-Container, keine doppelte Anzeige
    showProgressContainer('uploading', 0, 0);
    updateProgressActivity(`CSV wird hochgeladen: ${csvFile.name}`);
    
    try {
        // SCHRITT 1: CSV UPLOAD - Erstelle Session ID
        console.log('📤 [BATCH-STEP-1] Uploading CSV file...');
        
        // DEFENSIVE FIX 04.09.2025: Extra Validierung vor FormData-Erstellung
        if (!csvFile || csvFile.size === 0) {
            throw new Error('CSV-Datei ist ungültig oder leer');
        }
        
        const uploadFormData = new FormData();
        uploadFormData.append('file', csvFile);
        
        // VALIDATION FIX: Überprüfe ob File korrekt angehängt wurde
        if (!uploadFormData.has('file')) {
            throw new Error('Fehler beim Anhängen der CSV-Datei an FormData');
        }
        
        const uploadResponse = await fetch(`${window.API_BASE_URL}/api/upload-csv`, {
            method: 'POST',
            body: uploadFormData,
            signal: signal  // Add abort support
        });
        
        if (!uploadResponse.ok) {
            // DEBUG FIX 04.09.2025: Detaillierte Fehlermeldung bei 422
            const errorText = await uploadResponse.text();
            console.error(`[CSV-UPLOAD-ERROR] Status: ${uploadResponse.status}, Response: ${errorText}`);
            
            if (uploadResponse.status === 422) {
                throw new Error(`CSV Upload Validierung fehlgeschlagen (422): ${errorText}`);
            }
            throw new Error(`CSV Upload fehlgeschlagen: ${uploadResponse.status}`);
        }
        
        // Extract session_id from HTML response (backend sends HTML with hidden session_id field)
        const uploadHtml = await uploadResponse.text();
        console.log(`✅ [BATCH-STEP-1] CSV uploaded successfully, HTML length: ${uploadHtml.length}`);
        
        // Extract session_id from HTML using regex
        const sessionIdMatch = uploadHtml.match(/name="session_id"\s+value="([^"]+)"/);
        if (!sessionIdMatch) {
            throw new Error('Session ID konnte nicht aus Upload-Response extrahiert werden');
        }
        
        const sessionId = sessionIdMatch[1];
        console.log(`🎯 [BATCH-STEP-1] Session ID extracted: ${sessionId}`);
        
        // Extract mine count from HTML response for better user feedback
        const mineCountMatch = uploadHtml.match(/<strong>(\d+) Minen<\/strong> wurden erkannt/);
        const mineCount = mineCountMatch ? parseInt(mineCountMatch[1]) : 'unbekannt';
        console.log(`📊 [BATCH-STEP-1] Mine count extracted: ${mineCount}`);
        
        // Calculate expected results based on batch mode
        let expectedResults = '';
        if (batchMode === 'all') {
            expectedResults = `Verarbeitung aller ${mineCount} Minen`;
        } else {
            expectedResults = `Verarbeitung der ersten ${batchCount} von ${mineCount} Minen`;
        }
        
        // PROGRESS-MERGE 29.08.2025: Wechsel zu Session-basiertem Progress-Container
        const totalOperations = typeof mineCount === 'number' ? mineCount * selectedModels.length : desiredTotal * selectedModels.length;
        
        // PROGRESS FIX: Clear old progress state before starting new session-based tracking
        if (progressUpdateInterval) {
            console.log('📊 [PROGRESS] Clearing old progress interval before starting session-based tracking');
            clearInterval(progressUpdateInterval);
            progressUpdateInterval = null;
        }
        
        showProgressContainer(sessionId, typeof mineCount === 'number' ? mineCount : desiredTotal, selectedModels.length);
        
        // Update Progress mit CSV-Informationen
        updateProgressState('processing_csv', `✅ CSV verarbeitet: ${mineCount} Minen gefunden | ${expectedResults} mit ${selectedModels.length} Modellen`, 10);
        
        // Zeige batch-results für finale Ergebnisse, aber verstecke Loading-Messages
        resultsDiv.innerHTML = '<div id="batch-final-results" style="display: none;"></div>';
        
        // FRONTEND FIX: Populate selected_models hidden field before batch search
        const hiddenModelsField = document.querySelector('input[name="selected_models"]');
        if (hiddenModelsField) {
            hiddenModelsField.value = selectedModels.join(',');
            console.log('✅ [FRONTEND-FIX] selected_models field populated:', selectedModels.join(','));
        } else {
            console.warn('⚠️ [FRONTEND-FIX] selected_models hidden field not found!');
        }
        
        // SCHRITT 2: BATCH SEARCH mit Session ID (Chunking unterstützt)
        console.log('🔍 [BATCH-STEP-2] Starting batch search with session ID...');

        const desiredTotal = (batchMode === 'all')
            ? (typeof mineCount === 'number' ? mineCount : Number(mineCount) || 0)
            : Math.min(batchCount, (typeof mineCount === 'number' ? mineCount : Number(mineCount) || batchCount));

        const chunkSize = Math.min(BATCH_DEFAULT_CHUNK_SIZE, BATCH_MAX_COUNT);
        const needsChunking = desiredTotal > chunkSize || (batchMode === 'all' && mineCount > chunkSize);

        if (needsChunking) {
            console.log(`🧩 [BATCH-CHUNK] Processing in chunks of ${chunkSize}, total desired: ${desiredTotal}`);
            // Initial progress area
            resultsDiv.innerHTML = `
                <div style="padding: 12px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; margin-bottom: 12px;">
                    <strong>Pagination aktiv:</strong> Wir verarbeiten die Anfrage in Teilpaketen.
                    <div id="batch-chunk-progress" style="margin-top: 6px; font-size: 0.9rem; color: #1e40af;">Chunk 0/0</div>
                </div>
                <div id="batch-chunk-results"></div>
            `;
            const progressEl = document.getElementById('batch-chunk-progress');
            const resultsContainerEl = document.getElementById('batch-chunk-results');

            let processed = 0;
            let chunkIndex = 0;
            const totalChunks = Math.ceil(desiredTotal / chunkSize);
            if (progressEl) progressEl.textContent = `Chunk 0/${totalChunks} (0 verarbeitet)`;

            for (let startIndex = 0; startIndex < desiredTotal; startIndex += chunkSize) {
                if (batchSearchAbortController && batchSearchAbortController.signal.aborted) {
                    throw new DOMException('Aborted', 'AbortError');
                }

                const currentCount = Math.min(chunkSize, desiredTotal - startIndex);
                // TRANSPARENCY FIX 30.08.2025: Session und Cache Control Parameter hinzufügen (auch für Chunks)
                const useCacheElement = document.getElementById('use_cache');
                const forceNewSessionElement = document.getElementById('force_new_session');
                
                const useCacheEnabled = useCacheElement ? useCacheElement.checked : false;
                const forceNewSessionEnabled = forceNewSessionElement ? forceNewSessionElement.checked : true;

                const chunkFormData = new FormData();
                chunkFormData.append('session_id', sessionId);
                chunkFormData.append('search_type', comprehensiveSearchEnabled ? 'comprehensive' : 'standard');
                chunkFormData.append('search_all', 'false');
                
                // ENHANCED BATCH: Map frontend modes to backend parameters
                // Map frontend batch_mode to backend selection_mode
                let selectionMode = 'first_n'; // Default fallback
                if (batchMode === 'limited') selectionMode = 'first_n';
                else if (batchMode === 'range') selectionMode = 'range';
                else if (batchMode === 'random') selectionMode = 'random';
                else if (batchMode === 'all') selectionMode = 'all';
                
                chunkFormData.append('selection_mode', selectionMode);
                chunkFormData.append('count', currentCount.toString());
                chunkFormData.append('start_position', startPosition.toString());
                chunkFormData.append('range_count', rangeCount.toString());
                chunkFormData.append('random_count', randomCount.toString());
                chunkFormData.append('start_index', startIndex.toString());
                chunkFormData.append('selected_models', selectedModels.join(','));
                chunkFormData.append('twoPhase', twoPhaseEnabled.toString());
                chunkFormData.append('smartSearch', smartSearchEnabled.toString());
                chunkFormData.append('comprehensive', comprehensiveSearchEnabled.toString());
                // TRANSPARENCY FIX 30.08.2025: Neue Parameter
                chunkFormData.append('use_cache', useCacheEnabled.toString());
                chunkFormData.append('force_new_session', forceNewSessionEnabled.toString());

                const chunkResponse = await fetch(`${window.API_BASE_URL}/api/batch-search`, {
                    method: 'POST',
                    body: chunkFormData,
                    signal: signal
                });
                if (!chunkResponse.ok) {
                    const errorText = await chunkResponse.text();
                    throw new Error(`Batch-Chunk fehlgeschlagen (${chunkResponse.status}): ${errorText}`);
                }
                const chunkHtml = await chunkResponse.text();
                resultsContainerEl.insertAdjacentHTML('beforeend', chunkHtml);
                processed += currentCount;
                chunkIndex += 1;
                if (progressEl) progressEl.textContent = `Chunk ${chunkIndex}/${totalChunks} (${processed} verarbeitet)`;
            }

            if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
                window.searchTimer.stop();
            }
            showNotification(`✅ ${searchTypeText} in ${totalChunks} Teilpaketen abgeschlossen`, 'success');

            if (typeof window.smartRefreshAfterSearch === 'function') {
                window.smartRefreshAfterSearch('batch');
            } else if (typeof window.scheduleAllTabsRefresh === 'function') {
                window.scheduleAllTabsRefresh('batch');
            }
        } else {
            // TRANSPARENCY FIX 30.08.2025: Session und Cache Control Parameter hinzufügen
            const useCacheElement = document.getElementById('use_cache');
            const forceNewSessionElement = document.getElementById('force_new_session');
            
            const useCacheEnabled = useCacheElement ? useCacheElement.checked : false;
            const forceNewSessionEnabled = forceNewSessionElement ? forceNewSessionElement.checked : true;
            
            console.log(`🔍 [BATCH-TRANSPARENCY] use_cache: ${useCacheEnabled}, force_new_session: ${forceNewSessionEnabled}`);
            
            const batchFormData = new FormData();
            batchFormData.append('session_id', sessionId);
            batchFormData.append('search_type', comprehensiveSearchEnabled ? 'comprehensive' : 'standard');
            batchFormData.append('search_all', 'false');
            
            // ENHANCED BATCH: Map frontend modes to backend parameters
            // Map frontend batch_mode to backend selection_mode
            let selectionMode = 'first_n'; // Default fallback
            if (batchMode === 'limited') selectionMode = 'first_n';
            else if (batchMode === 'range') selectionMode = 'range';
            else if (batchMode === 'random') selectionMode = 'random';
            else if (batchMode === 'all') selectionMode = 'all';
            
            batchFormData.append('selection_mode', selectionMode);
            batchFormData.append('count', desiredTotal.toString());
            batchFormData.append('start_position', startPosition.toString());
            batchFormData.append('range_count', rangeCount.toString());
            batchFormData.append('random_count', randomCount.toString());
            batchFormData.append('start_index', '0');
            batchFormData.append('selected_models', selectedModels.join(','));
            batchFormData.append('twoPhase', twoPhaseEnabled.toString());
            batchFormData.append('smartSearch', smartSearchEnabled.toString());
            batchFormData.append('comprehensive', comprehensiveSearchEnabled.toString());
            // TRANSPARENCY FIX 30.08.2025: Neue Parameter
            batchFormData.append('use_cache', useCacheEnabled.toString());
            batchFormData.append('force_new_session', forceNewSessionEnabled.toString());

            const batchResponse = await fetch(`${window.API_BASE_URL}/api/batch-search`, {
                method: 'POST',
                body: batchFormData,
                signal: signal
            });
            if (!batchResponse.ok) {
                const errorText = await batchResponse.text();
                throw new Error(`Batch-Suche fehlgeschlagen (${batchResponse.status}): ${errorText}`);
            }
            const batchResultsHtml = await batchResponse.text();
            if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
                window.searchTimer.stop();
            }
            
            // PROGRESS-MERGE 29.08.2025: Zeige Ergebnisse und verstecke Progress-Container
            updateProgressState('batch_complete', '✅ Batch-Suche erfolgreich abgeschlossen!', 100);
            
            // Warte 2 Sekunden und zeige dann Ergebnisse
            setTimeout(() => {
                hideProgressContainer();
                resultsDiv.style.display = 'block';
                safeSetHTML(resultsDiv, batchResultsHtml);
                showNotification(`✅ ${searchTypeText} erfolgreich abgeschlossen`, 'success');
            }, 2000);
            
            if (typeof window.smartRefreshAfterSearch === 'function') {
                window.smartRefreshAfterSearch('batch');
            } else if (typeof window.scheduleAllTabsRefresh === 'function') {
                window.scheduleAllTabsRefresh('batch');
            }
        }
        
    } catch (error) {
        // Handle abort vs other errors FIRST (consistent with Single Search)
        if (error.name === 'AbortError') {
            console.log('🛑 [BATCH-SEARCH] Batch search was aborted by user');
            
            // Stop timer
            if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
                window.searchTimer.stop();
            }
            
            // UI is already updated by cancelBatchSearch()
            // Don't show notification - already shown by cancelBatchSearch()
            return;
        } else {
            // Only log non-abort errors
            console.error(`❌ [BATCH-SEARCH] Error:`, error);
            
            // PROGRESS-MERGE 29.08.2025: Zeige Fehler im Progress-Container
            updateProgressState('error', `⚠️ Fehler: ${error.message}`, 0);
            
            // Warte 3 Sekunden und verstecke dann Progress-Container
            setTimeout(() => {
                hideProgressContainer();
                resultsDiv.style.display = 'block';
            }, 3000);
            
            // Stop timer
            if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
                window.searchTimer.stop();
            }
            
            resultsDiv.innerHTML = createErrorHTML('Batch-Suche fehlgeschlagen', error.message);
            showNotification(`❌ Batch-Suche fehlgeschlagen: ${error.message}`, 'error');
        }
    } finally {
        // Clean up abort controller
        batchSearchAbortController = null;
    }
}

/**
 * CANCEL BATCH SEARCH: Bricht die laufende Batch-Suche ab
 */
function cancelBatchSearch() {
    console.log('🛑 [CANCEL-BATCH] Aborting batch search...');
    
    // Stop timer (consistent with Single Search)
    if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
        window.searchTimer.stop();
        console.log('⏹️ [CANCEL-BATCH] Timer stopped');
    }
    
    // Abort API request
    if (batchSearchAbortController) {
        batchSearchAbortController.abort();
        console.log('✅ [CANCEL-BATCH] Batch search aborted successfully');
    } else {
        console.log('⚠️ [CANCEL-BATCH] No active batch search to abort');
    }
    
    // Reset UI state (consistent with Single Search)
    const resultsDiv = document.getElementById('results');
    if (resultsDiv) {
        resultsDiv.innerHTML = `
            <div style="padding: 20px; text-align: center; background: #fff3cd; border-radius: 8px; border: 1px solid #ffc107;">
                <h3>🛑 Batch-Suche abgebrochen</h3>
                <p>Die Batch-Suche wurde erfolgreich abgebrochen.</p>
            </div>
        `;
    }
    
    // PROGRESS-FIX 29.08.2025: Progress-Container verstecken
    hideProgressContainer();
    
    // Show notification
    showNotification('🛑 Batch-Suche erfolgreich abgebrochen', 'info');
}

/**
 * CANCEL SINGLE SEARCH: Bricht die laufende Single-Suche ab
 */
function cancelSingleSearch() {
    console.log('🛑 [CANCEL-SINGLE] Aborting single search...');
    
    // Stop timer
    if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
        window.searchTimer.stop();
        console.log('⏹️ [CANCEL-SINGLE] Timer stopped');
    }
    
    // Abort API request
    if (singleSearchAbortController) {
        singleSearchAbortController.abort();
        console.log('✅ [CANCEL-SINGLE] Single search aborted successfully');
    } else {
        console.log('⚠️ [CANCEL-SINGLE] No active single search to abort');
    }
    
    // Reset UI state
    const resultsDiv = document.getElementById('results');
    if (resultsDiv) {
        resultsDiv.innerHTML = `
            <div style="padding: 20px; text-align: center; background: #fff3cd; border-radius: 8px; border: 1px solid #ffc107;">
                <h3>🛑 Suche abgebrochen</h3>
                <p>Die Suche wurde erfolgreich abgebrochen.</p>
            </div>
        `;
    }
    
    // Show notification
    showNotification('🛑 Suche erfolgreich abgebrochen', 'info');
}

// ============================================
// MODEL LOADING & SELECTION
// ============================================

/**
 * MODEL LOADING: Lädt verfügbare Modelle für die Auswahl
 */
async function loadModelsForFilter() {
    console.log('🔄 [MODEL-FILTER] Loading models for filter dropdown...');
    
    const modelSelection = document.getElementById('model-selection');
    if (!modelSelection) {
        console.error('❌ [DEBUG] model-selection element NOT FOUND!');
        return;
    }
    
    try {
        console.log(`🌐 [DEBUG] Making API call to: ${window.API_BASE_URL}/api/models`);
        const response = await fetch(`${window.API_BASE_URL}/api/models`);
        console.log(`📡 [DEBUG] API Response status: ${response.status}`);
        
        const data = await response.json();
        console.log(`📊 [DEBUG] API Response data.success: ${data.success}`);
        console.log(`📋 [DEBUG] Available models count: ${data.models ? Object.keys(data.models).length : 0}`);
        
        if (!data.success || !data.models) {
            throw new Error('Keine Modell-Daten verfügbar');
        }
        
        // Gruppiere Modelle nach Provider
        const providerGroups = {};
        Object.entries(data.models).forEach(([modelId, modelInfo]) => {
            const provider = modelId.split(':')[0];
            if (!providerGroups[provider]) {
                providerGroups[provider] = [];
            }
            providerGroups[provider].push({
                id: modelId,
                info: modelInfo
            });
        });
        
        console.log(`🏷️ [DEBUG] Providers found: ${Object.keys(providerGroups).join(', ')}`);
        
        // PHASE 2: Search Interface Revolution - Intelligente Provider-Kategorisierung
        console.log('🎨 [UI-REVOLUTION] Implementing Smart Model Selection...');
        
        // Smart Provider Categories & Priorities
        const providerCategories = {
            recommended: ['perplexity', 'openrouter', 'abacus'],
            webSearch: ['tavily', 'exa', 'grok'],
            premium: ['openai', 'anthropic', 'gemini'],
            scraping: ['scrapingbee', 'firecrawl', 'brightdata']
        };
        
        // Smart Defaults für beliebte Modelle
        const smartDefaults = [
            'perplexity:sonar-pro',
            'openrouter:deepseek-free', 
            'abacus:deep-agent'
        ];
        
        let modelsHTML = `
            <div class="search-interface-revolution">
                <!-- Quick Start Section -->
                <div class="quick-start-section">
                    <h4 style="color: var(--primary-700); margin-bottom: var(--space-md); display: flex; align-items: center; gap: var(--space-sm);">
                        ⚡ Quick Start
                        <span style="background: var(--success-100); color: var(--success-700); padding: 4px 8px; border-radius: var(--radius-sm); font-size: 0.75rem; font-weight: 600;">Empfohlen</span>
                    </h4>
                    <div class="quick-selection-pills">
                        <button type="button" class="quick-pill recommended" onclick="selectQuickPreset('recommended')" title="Automatisch beste Modelle basierend auf Performance-Statistiken">
                            🏆 Dynamische Beste Auswahl
                        </button>
                        <button type="button" class="quick-pill web-focus" onclick="selectQuickPreset('webSearch')" title="Modelle mit Web-Zugriff für aktuelle Daten">
                            🌐 Web-Suche (6 Modelle)
                        </button>
                        <button type="button" class="quick-pill premium" onclick="selectQuickPreset('premium')" title="Premium-Modelle für komplexe Analysen">
                            💎 Premium (12 Modelle)
                        </button>
                        <button type="button" class="quick-pill all" onclick="selectQuickPreset('all')" title="Alle verfügbaren Modelle verwenden">
                            🚀 Alle (55 Modelle)
                        </button>
                    </div>
                </div>

                <!-- Advanced Selection (Initially Hidden) -->
                <div class="advanced-selection-section" style="display: none;">
                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: var(--space-md);">
                        <h4 style="color: var(--gray-700); margin: 0;">⚙️ Erweiterte Auswahl</h4>
                        <button type="button" class="hide-advanced-btn" onclick="hideAdvancedSelection()">
                            ⬆️ Verbergen
                        </button>
                    </div>
        `;
        
        // Generate Provider Groups with improved UX
        Object.entries(providerGroups).forEach(([provider, models]) => {
            const providerName = getProviderDisplayName(provider);
            const providerId = provider.replace(/[^a-zA-Z0-9]/g, '_');
            const categoryInfo = getProviderCategory(provider, providerCategories);
            
            modelsHTML += `
                <div class="provider-group ${categoryInfo.class}" data-provider="${provider}">
                    <div class="provider-header" onclick="toggleProviderModels('${provider}')">
                        <input type="checkbox" id="provider_${providerId}" 
                               onchange="toggleProviderCheckbox('${provider}')" 
                               onclick="event.stopPropagation()">
                        <div class="provider-info">
                            <strong>${categoryInfo.icon} ${providerName}</strong>
                            <span class="provider-meta">${models.length} Modelle • ${categoryInfo.description}</span>
                        </div>
                        <span class="provider-toggle">▼</span>
                    </div>
                    <div class="models-list" style="display: none;">
            `;
            
            models.forEach(model => {
                const modelDisplayName = model.id.split(':')[1] || model.id;
                const isDefault = smartDefaults.includes(model.id);
                const modelMeta = getModelMeta(model.info);
                
                modelsHTML += `
                    <label class="model-option ${isDefault ? 'recommended' : ''}">
                        <input type="checkbox" name="model" value="${model.id}" 
                               ${isDefault ? 'checked' : ''}
                               onchange="updateProviderCheckboxState('${provider}')">
                        <div class="model-details">
                            <span class="model-name">${modelDisplayName} ${isDefault ? '⭐' : ''}</span>
                            <span class="model-description">${modelMeta.description}</span>
                            <div class="model-tags">
                                ${modelMeta.tags.map(tag => `<span class="tag ${tag.class}">${tag.text}</span>`).join('')}
                            </div>
                        </div>
                    </label>
                `;
            });
            
            modelsHTML += `
                    </div>
                </div>
            `;
        });
        
        modelsHTML += `
                </div>
                
                <!-- Show Advanced Button -->
                <div class="show-advanced-section">
                    <button type="button" class="show-advanced-btn" onclick="showAdvancedSelection()">
                        ⚙️ Erweiterte Auswahl anzeigen (${Object.values(data.models).length} Modelle)
                    </button>
                </div>
                
                <!-- Selection Summary -->
                <div class="selection-summary">
                    <div class="selected-count">
                        <strong data-selection-counter>3</strong> Modelle ausgewählt
                    </div>
                    <button type="button" class="clear-selection" onclick="clearAllModels()" style="display: none;">
                        Alle abwählen
                    </button>
                </div>
            </div>
        `;
        
        modelSelection.innerHTML = modelsHTML;
        console.log(`✅ [UI-REVOLUTION] Smart Model Selection with ${Object.keys(providerGroups).length} providers and ${Object.values(data.models).length} models loaded`);
        
        // Initialize UI Revolution features
        initializeQuickPresets(providerGroups, data.models);
        updateSelectionCounter();
        
    } catch (error) {
        console.error('❌ [MODEL-FILTER] Error loading models:', error);
        modelSelection.innerHTML = createErrorHTML(
            'Modelle konnten nicht geladen werden', 
            error.message
        );
    }
}

// ============================================
// FORM VALIDATION & UTILITIES
// ============================================

/**
 * FORM VALIDATION: Validiert Search-Form-Eingaben
 */
function validateSearchForm(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form ${formId} not found`);
        return false;
    }
    
    const formData = new FormData(form);
    const mineName = formData.get('mine_name');
    const country = formData.get('country');
    const commodity = formData.get('commodity');
    
    // Mindestens ein Suchkriterium erforderlich
    if (!mineName && !country && !commodity) {
        showNotification('Bitte geben Sie mindestens ein Suchkriterium ein.', 'warning');
        return false;
    }
    
    // Modell-Auswahl prüfen
    const selectedModels = Array.from(document.querySelectorAll('input[name="model"]:checked'));
    if (selectedModels.length === 0) {
        showNotification('Bitte wählen Sie mindestens ein Modell aus.', 'warning');
        return false;
    }
    
    return true;
}

/**
 * SEARCH OPTIONS: Behandelt Such-Optionen-Änderungen
 */
function handleSearchOptionsChange() {
    const twoPhase = document.getElementById('two_phase_enabled');
    const smartSearch = document.getElementById('smart_search_enabled');
    const comprehensive = document.getElementById('comprehensive_search_enabled');
    
    // Mutual exclusivity logic - nur eine Option gleichzeitig
    if (comprehensive && comprehensive.checked) {
        if (twoPhase) twoPhase.checked = false;
        if (smartSearch) smartSearch.checked = false;
    } else if (smartSearch && smartSearch.checked) {
        if (twoPhase) twoPhase.checked = false;
        if (comprehensive) comprehensive.checked = false;
    } else if (twoPhase && twoPhase.checked) {
        if (smartSearch) smartSearch.checked = false;
        if (comprehensive) comprehensive.checked = false;
    }
}

// ============================================
// SEARCH STATE MANAGEMENT
// ============================================

/**
 * SEARCH STATE: Verwaltet den aktuellen Suchzustand
 */
const SearchState = {
    isSearching: false,
    currentSearchId: null,
    currentSearchType: 'single',
    
    startSearch: function(searchId, searchType = 'single') {
        this.isSearching = true;
        this.currentSearchId = searchId;
        this.currentSearchType = searchType;
        
        // UI Updates
        const searchButton = document.querySelector('.search-submit-button');
        const cancelButton = document.querySelector('.cancel-search-button');
        
        if (searchButton) {
            ButtonStateController.setLoading(searchButton, 'Sucht...');
        }
        
        if (cancelButton) {
            cancelButton.style.display = 'inline-block';
        }
    },
    
    endSearch: function() {
        this.isSearching = false;
        this.currentSearchId = null;
        
        // UI Updates
        const searchButton = document.querySelector('.search-submit-button');
        const cancelButton = document.querySelector('.cancel-search-button');
        
        if (searchButton) {
            ButtonStateController.resetState(searchButton);
        }
        
        if (cancelButton) {
            cancelButton.style.display = 'none';
        }
        
        // Stop timer
        if (typeof stopSearchTimer === 'function') {
            stopSearchTimer();
        }
    },
    
    cancelCurrentSearch: function() {
        if (!this.isSearching) return;
        
        console.log(`🛑 [SEARCH] Cancelling ${this.currentSearchType} search`);
        
        // Abort API requests if SearchAPI is available
        if (window.SearchAPI && typeof SearchAPI.abortSearch === 'function') {
            SearchAPI.abortSearch(this.currentSearchId);
        }
        
        this.endSearch();
        
        // Update results display
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.innerHTML = createErrorHTML(
                'Suche abgebrochen', 
                'Die laufende Suche wurde vom Benutzer abgebrochen.'
            );
        }
        
        showNotification('🛑 Suche wurde abgebrochen', 'info');
    }
};

// ============================================
// SEARCH RESULT PROCESSING
// ============================================

/**
 * RESULTS PROCESSING: Verarbeitet und zeigt Suchergebnisse
 */
function processSearchResults(data, searchType = 'single') {
    console.log(`📊 [RESULTS] Processing ${searchType} search results`);
    
    if (!data || !data.results) {
        console.error('❌ [RESULTS] No results data provided');
        return;
    }
    
    const results = Array.isArray(data.results) ? data.results : [data.results];
    
    // Statistiken
    const totalResults = results.length;
    const successfulResults = results.filter(r => r.success).length;
    const uniqueMines = [...new Set(results.map(r => r.mine_name))].filter(Boolean);
    
    console.log(`📈 [RESULTS] Statistics: ${successfulResults}/${totalResults} erfolgreiche Ergebnisse, ${uniqueMines.length} eindeutige Minen`);
    
    // Update search state
    SearchState.endSearch();
    
    return {
        total: totalResults,
        successful: successfulResults,
        mines: uniqueMines,
        results: results
    };
}

// ============================================
// GLOBAL EXPORTS & INITIALIZATION
// ============================================

// ============================================
// UI REVOLUTION: SMART MODEL SELECTION
// Phase 2 Implementation
// ============================================

// Helper Functions für Search Interface Revolution
function getProviderDisplayName(provider) {
    const displayNames = {
        'perplexity': 'Perplexity',
        'openrouter': 'OpenRouter', 
        'abacus': 'Abacus AI',
        'tavily': 'Tavily Search',
        'exa': 'Exa Neural',
        'scrapingbee': 'ScrapingBee',
        'firecrawl': 'Firecrawl',
        'brightdata': 'Bright Data',
        'openai': 'OpenAI',
        'anthropic': 'Anthropic',
        'gemini': 'Google Gemini',
        'grok': 'Grok (X.AI)'
    };
    return displayNames[provider] || provider.charAt(0).toUpperCase() + provider.slice(1);
}

function getProviderCategory(provider, categories) {
    if (categories.recommended.includes(provider)) {
        return {
            class: 'recommended-provider',
            icon: '🏆',
            description: 'Empfohlen für Mining-Recherche'
        };
    }
    if (categories.webSearch.includes(provider)) {
        return {
            class: 'web-provider',
            icon: '🌐',
            description: 'Web-Suche mit aktuellen Daten'
        };
    }
    if (categories.premium.includes(provider)) {
        return {
            class: 'premium-provider',
            icon: '💎',
            description: 'Premium-Modelle für komplexe Analysen'
        };
    }
    if (categories.scraping.includes(provider)) {
        return {
            class: 'scraping-provider',
            icon: '🔍',
            description: 'Web-Scraping und Datenextraktion'
        };
    }
    return {
        class: 'standard-provider',
        icon: '🤖',
        description: 'Standard-Modelle'
    };
}

function getModelMeta(modelInfo) {
    const tags = [];
    let description = modelInfo.description || 'KI-Modell für Mining-Analyse';
    
    // Add capability tags
    if (modelInfo.is_free) {
        tags.push({ text: 'Kostenlos', class: 'free' });
    }
    if (modelInfo.supports_web_search) {
        tags.push({ text: 'Web-Suche', class: 'web' });
    }
    if (modelInfo.supports_deep_research) {
        tags.push({ text: 'Deep Research', class: 'research' });
    }
    if (modelInfo.max_tokens >= 10000) {
        tags.push({ text: 'Large Context', class: 'large' });
    }
    
    return { description, tags };
}

/**
 * PHASE 2.1: Dynamic Model Selection based on Performance Statistics
 * Ermittelt die besten Modelle basierend auf aktuellen Performance-Scores
 */
async function getBestPerformingModels() {
    console.log('🏆 [DYNAMIC-SELECTION] Fetching best performing models from statistics...');
    
    try {
        // Hole aktuelle Statistics
        const response = await fetch(`${window.API_BASE_URL || 'http://localhost:8000'}/api/results?exclude_exa=true&days_back=30&sort_by=mine_name`);
        
        if (!response.ok) {
            console.warn('⚠️ [DYNAMIC-SELECTION] Statistics API not available:', response.status);
            return [];
        }
        
        const data = await response.json();
        
        if (!data.success || !data.data?.results) {
            console.warn('⚠️ [DYNAMIC-SELECTION] No statistics data available');
            return [];
        }
        
        // Generiere Model-Stats wie in statistics-loader.js
        const mockModelStats = generateMockModelStatsFromConsolidatedForSelection(data.data.results);
        
        if (mockModelStats.length === 0) {
            console.warn('⚠️ [DYNAMIC-SELECTION] No model statistics generated');
            return [];
        }
        
        // KRITISCHE KORREKTUR: Filter 0% Erfolgsrate-Modelle KOMPLETT aus
        const qualifiedModels = mockModelStats.filter(model => {
            const isQualified = model.success_rate > 0 && model.overall_score > 0;
            if (!isQualified) {
                console.log(`❌ [DYNAMIC-SELECTION] Disqualified: ${model.model_id} (Success: ${(model.success_rate * 100).toFixed(1)}%, Score: ${model.overall_score?.toFixed(1) || 'N/A'})`);
            }
            return isQualified;
        });
        
        if (qualifiedModels.length === 0) {
            console.warn('⚠️ [DYNAMIC-SELECTION] No qualified models found - all have 0% success rate');
            return [];
        }
        
        // Sortiere nach overall_score (absteigend) - nur qualifizierte Modelle
        const sortedModels = qualifiedModels.sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
        
        // Wähle Top 3 Modelle mit verschiedenen Providern für Diversität
        const selectedModels = [];
        const usedProviders = new Set();
        
        for (const model of sortedModels) {
            if (selectedModels.length >= 3) break;
            
            const provider = model.model_id.split(':')[0];
            
            // Priorisiere Diversität: verschiedene Provider bevorzugen
            if (!usedProviders.has(provider) || selectedModels.length < 2) {
                selectedModels.push(model.model_id);
                usedProviders.add(provider);
                console.log(`✅ [DYNAMIC-SELECTION] Selected top performer: ${model.model_id} (Success: ${(model.success_rate * 100).toFixed(1)}%, Score: ${model.overall_score?.toFixed(1) || 'N/A'})`);
            }
        }
        
        // Falls weniger als 3 gefunden, fülle mit den nächstbesten auf
        if (selectedModels.length < 3) {
            for (const model of sortedModels) {
                if (selectedModels.length >= 3) break;
                if (!selectedModels.includes(model.model_id)) {
                    selectedModels.push(model.model_id);
                    console.log(`✅ [DYNAMIC-SELECTION] Added performer: ${model.model_id} (Score: ${model.overall_score?.toFixed(1) || 'N/A'})`);
                }
            }
        }
        
        console.log(`🏆 [DYNAMIC-SELECTION] Selected ${selectedModels.length} best performers:`, selectedModels);
        return selectedModels;
        
    } catch (error) {
        console.error('❌ [DYNAMIC-SELECTION] Error fetching best performing models:', error);
        return [];
    }
}

/**
 * Vereinfachte Version der Model-Stats-Generierung für Selection
 */
function generateMockModelStatsFromConsolidatedForSelection(results) {
    const modelStats = new Map();
    
    results.forEach(result => {
        const rawModelUsed = result.model_used || 'unknown';
        const individualModels = rawModelUsed.includes('_') 
            ? rawModelUsed.split('_').map(m => m.trim())
            : [rawModelUsed];
        
        individualModels.forEach(modelId => {
            if (!modelStats.has(modelId)) {
                modelStats.set(modelId, {
                    model_id: modelId,
                    total_searches: 0,
                    successful_searches: 0,
                    success_rate: 0,
                    overall_score: 0
                });
            }
            
            const modelData = modelStats.get(modelId);
            modelData.total_searches += 1;
            modelData.successful_searches += result.structured_data ? 1 : 0;
        });
    });
    
    // Berechne finale Scores (KORRIGIERT: Erfolgsrate-abhängig)
    return Array.from(modelStats.values()).map(model => {
        model.success_rate = model.total_searches > 0 
            ? model.successful_searches / model.total_searches 
            : 0.0;
        
        // KRITISCHE KORREKTUR: Usage-Bonus nur bei erfolgreichen Modellen
        // Bei 0% Erfolgsrate gibt es KEINEN Bonus, egal wie oft verwendet
        if (model.success_rate === 0) {
            model.overall_score = 0; // Komplett disqualifiziert
            model.disqualification_reason = 'Keine erfolgreichen Suchen';
            return model;
        }
        
        // Erfolgsrate als Hauptfaktor (70% Gewichtung)
        const successComponent = model.success_rate * 7; // Max 7
        
        // Usage-Bonus nur für erfolgreiche Modelle (30% Gewichtung)
        // Aber nur wenn mindestens 20% Erfolgsrate
        const usageBonus = model.success_rate >= 0.2 
            ? Math.min(model.total_searches / 10, 1.0) * 3 // Max 3
            : 0;
        
        model.overall_score = successComponent + usageBonus; // Max 10
        model.score_breakdown = {
            success_component: successComponent.toFixed(1),
            usage_bonus: usageBonus.toFixed(1),
            total: model.overall_score.toFixed(1)
        };
        
        return model;
    });
}

// Wrapper für onclick-Handler
function selectQuickPreset(presetType) {
    selectQuickPresetAsync(presetType).catch(error => {
        console.error('❌ [DYNAMIC-SELECTION] Preset selection failed:', error);
        // Fallback to synchronous selection if async fails
        selectQuickPresetSync(presetType);
    });
}

// Quick Preset Functions (Async Version)
async function selectQuickPresetAsync(presetType) {
    console.log(`🎯 [UI-REVOLUTION] Selecting preset: ${presetType}`);
    
    // Clear all selections first
    clearAllModels();
    
    const providerCategories = {
        recommended: ['perplexity', 'openrouter', 'abacus'],
        webSearch: ['tavily', 'exa', 'grok'],
        premium: ['openai', 'anthropic', 'gemini'],
        scraping: ['scrapingbee', 'firecrawl', 'brightdata']
    };
    
    let modelsToSelect = [];
    
    switch(presetType) {
        case 'recommended':
            // DYNAMIC SELECTION: Get best performing models from statistics
            modelsToSelect = await getBestPerformingModels();
            if (modelsToSelect.length === 0) {
                // Fallback to static selection if no statistics available
                modelsToSelect = [
                    'perplexity:sonar-pro',
                    'openrouter:deepseek-free',
                    'abacus:deep-agent'
                ];
                console.log('⚠️ [DYNAMIC-SELECTION] Using fallback models - no statistics available');
            } else {
                console.log(`✅ [DYNAMIC-SELECTION] Using top ${modelsToSelect.length} performers from statistics`);
            }
            break;
            
        case 'webSearch':
            modelsToSelect = document.querySelectorAll('input[name="model"]');
            modelsToSelect = Array.from(modelsToSelect)
                .filter(input => {
                    const provider = input.value.split(':')[0];
                    return providerCategories.webSearch.includes(provider);
                })
                .map(input => input.value);
            break;
            
        case 'premium':
            modelsToSelect = document.querySelectorAll('input[name="model"]');
            modelsToSelect = Array.from(modelsToSelect)
                .filter(input => {
                    const provider = input.value.split(':')[0];
                    return providerCategories.premium.includes(provider);
                })
                .map(input => input.value);
            break;
            
        case 'all':
            modelsToSelect = Array.from(document.querySelectorAll('input[name="model"]'))
                .map(input => input.value);
            break;
    }
    
    // Select the models
    modelsToSelect.forEach(modelId => {
        const checkbox = document.querySelector(`input[name="model"][value="${modelId}"]`);
        if (checkbox) {
            checkbox.checked = true;
            // Update provider checkbox state
            const provider = modelId.split(':')[0];
            updateProviderCheckboxState(provider);
        }
    });
    
    // Update counter and highlight selected preset
    updateSelectionCounter();
    
    // Highlight selected preset
    document.querySelectorAll('.quick-pill').forEach(pill => {
        pill.classList.remove('active');
    });
    document.querySelector(`.quick-pill.${presetType}`)?.classList.add('active');
    
    console.log(`✅ [UI-REVOLUTION] Selected ${modelsToSelect.length} models for preset: ${presetType}`);
}

// Synchrone Fallback-Version (ohne Dynamic Selection)
function selectQuickPresetSync(presetType) {
    console.log(`🎯 [UI-REVOLUTION] SYNC Selecting preset: ${presetType}`);
    
    // Clear all selections first
    clearAllModels();
    
    const providerCategories = {
        recommended: ['perplexity', 'openrouter', 'abacus'],
        webSearch: ['tavily', 'exa', 'grok'],
        premium: ['openai', 'anthropic', 'gemini'],
        scraping: ['scrapingbee', 'firecrawl', 'brightdata']
    };
    
    let modelsToSelect = [];
    
    switch(presetType) {
        case 'recommended':
            // Static fallback selection
            modelsToSelect = [
                'perplexity:sonar-pro',
                'openrouter:deepseek-free',
                'abacus:deep-agent'
            ];
            console.log('🔄 [SYNC-SELECTION] Using static recommended models');
            break;
            
        case 'webSearch':
            modelsToSelect = document.querySelectorAll('input[name="model"]');
            modelsToSelect = Array.from(modelsToSelect)
                .filter(input => {
                    const provider = input.value.split(':')[0];
                    return providerCategories.webSearch.includes(provider);
                })
                .map(input => input.value);
            break;
            
        case 'premium':
            modelsToSelect = document.querySelectorAll('input[name="model"]');
            modelsToSelect = Array.from(modelsToSelect)
                .filter(input => {
                    const provider = input.value.split(':')[0];
                    return providerCategories.premium.includes(provider);
                })
                .map(input => input.value);
            break;
            
        case 'all':
            modelsToSelect = Array.from(document.querySelectorAll('input[name="model"]'))
                .map(input => input.value);
            break;
    }
    
    // Select the models
    modelsToSelect.forEach(modelId => {
        const checkbox = document.querySelector(`input[name="model"][value="${modelId}"]`);
        if (checkbox) {
            checkbox.checked = true;
            // Update provider checkbox state
            const provider = modelId.split(':')[0];
            updateProviderCheckboxState(provider);
        }
    });
    
    // Update counter and highlight selected preset
    updateSelectionCounter();
    
    // Highlight selected preset
    document.querySelectorAll('.quick-pill').forEach(pill => {
        pill.classList.remove('active');
    });
    document.querySelector(`.quick-pill.${presetType}`)?.classList.add('active');
    
    console.log(`✅ [UI-REVOLUTION] SYNC Selected ${modelsToSelect.length} models for preset: ${presetType}`);
}

function showAdvancedSelection() {
    document.querySelector('.advanced-selection-section').style.display = 'block';
    document.querySelector('.show-advanced-section').style.display = 'none';
    console.log('🔧 [UI-REVOLUTION] Advanced selection shown');
}

function hideAdvancedSelection() {
    document.querySelector('.advanced-selection-section').style.display = 'none';
    document.querySelector('.show-advanced-section').style.display = 'block';
    console.log('🔧 [UI-REVOLUTION] Advanced selection hidden');
}

function clearAllModels() {
    document.querySelectorAll('input[name="model"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    document.querySelectorAll('input[id^="provider_"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    document.querySelectorAll('.quick-pill').forEach(pill => {
        pill.classList.remove('active');
    });
    
    updateSelectionCounter();
    console.log('🧹 [UI-REVOLUTION] All models cleared');
}

function updateSelectionCounter() {
    // ÄNDERUNG 23.08.2025: Integration mit Progressive Model Selection System
    // Prüfe ob Progressive Model Selection aktiv ist
    let selectedCount = 0;
    
    if (window.progressiveModelSelection && window.progressiveModelSelection.selectedModels) {
        // Nutze die moderne selectedModels Set-Struktur
        selectedCount = window.progressiveModelSelection.selectedModels.size;
        console.log(`🔢 [SEARCH-JS] Using Progressive Model Selection count: ${selectedCount}`);
    } else {
        // Fallback für Legacy-Kompatibilität
        selectedCount = document.querySelectorAll('input[name="model"]:checked').length;
        console.log(`🔢 [SEARCH-JS] Using DOM checkbox count: ${selectedCount}`);
    }
    
    const clearButton = document.querySelector('.clear-selection');
    
    // Update all counter elements with data-selection-counter attribute
    document.querySelectorAll('[data-selection-counter]').forEach(element => {
        console.log(`🔢 [SEARCH-JS] Updating counter: ${element.textContent} → ${selectedCount}`);
        element.textContent = selectedCount;
    });
    
    if (clearButton) {
        clearButton.style.display = selectedCount > 0 ? 'block' : 'none';
    }
}

function initializeQuickPresets(providerGroups, models) {
    // Set default preset selection (recommended)
    setTimeout(() => {
        selectQuickPreset('recommended');
    }, 500);
    
    // PHASE 2.2: Start auto-update for preset buttons
    setTimeout(() => {
        startQuickPresetAutoUpdate();
    }, 1000);
    
    console.log('🎨 [UI-REVOLUTION] Quick presets initialized with smart defaults and auto-update');
}

/**
 * PHASE 2.2: Auto-Update Quick-Presets mit Top-Performern
 * Aktualisiert Button-Labels und Tooltips periodisch mit aktuellen Performance-Daten
 */
async function startQuickPresetAutoUpdate() {
    console.log('🔄 [AUTO-UPDATE] Starting quick preset auto-update system...');
    
    // Initial update
    await updateQuickPresetLabels();
    
    // Periodic updates every 5 minutes
    setInterval(async () => {
        try {
            await updateQuickPresetLabels();
        } catch (error) {
            console.warn('⚠️ [AUTO-UPDATE] Periodic update failed:', error);
        }
    }, 5 * 60 * 1000); // 5 minutes
    
    console.log('✅ [AUTO-UPDATE] Quick preset auto-update system started');
}

/**
 * Aktualisiert die Button-Labels mit aktuellen Top-Performer-Informationen
 */
async function updateQuickPresetLabels() {
    console.log('🏆 [AUTO-UPDATE] Updating quick preset labels with current top performers...');
    
    try {
        // Hole aktuelle Top-Performer
        const topPerformers = await getBestPerformingModels();
        
        if (topPerformers.length === 0) {
            console.log('⚠️ [AUTO-UPDATE] No top performers available - keeping static labels');
            return;
        }
        
        // Update "Beste Auswahl" Button
        const recommendedButton = document.querySelector('.quick-pill.recommended');
        if (recommendedButton) {
            // Extrahiere Provider-Namen für bessere Darstellung
            const providerNames = topPerformers.map(model => {
                const provider = model.split(':')[0];
                return provider.charAt(0).toUpperCase() + provider.slice(1);
            }).slice(0, 3); // Maximal 3 Provider zeigen
            
            const newLabel = `🏆 Top Performers (${providerNames.join(', ')})`;
            const newTooltip = `Automatisch beste Modelle: ${topPerformers.join(', ')}`;
            
            recommendedButton.innerHTML = newLabel;
            recommendedButton.setAttribute('title', newTooltip);
            
            console.log(`✅ [AUTO-UPDATE] Updated recommended button: ${newLabel}`);
        }
        
        // Update andere Preset-Buttons mit aktuellen Counts
        await updatePresetCounts();
        
    } catch (error) {
        console.error('❌ [AUTO-UPDATE] Failed to update preset labels:', error);
    }
}

/**
 * Aktualisiert die Model-Counts in anderen Preset-Buttons
 */
async function updatePresetCounts() {
    const providerCategories = {
        webSearch: ['tavily', 'exa', 'grok'],
        premium: ['openai', 'anthropic', 'gemini'],
        all: [] // Wird dynamisch berechnet
    };
    
    // Zähle verfügbare Modelle pro Kategorie
    const allModels = Array.from(document.querySelectorAll('input[name="model"]'));
    
    Object.entries(providerCategories).forEach(([category, providers]) => {
        let count = 0;
        
        if (category === 'all') {
            count = allModels.length;
        } else {
            count = allModels.filter(input => {
                const provider = input.value.split(':')[0];
                return providers.includes(provider);
            }).length;
        }
        
        // Update Button-Label
        const button = document.querySelector(`.quick-pill.${category === 'webSearch' ? 'web-focus' : category}`);
        if (button && count > 0) {
            const currentText = button.innerHTML;
            const updatedText = currentText.replace(/\(\d+\s+Modelle?\)/, `(${count} Modell${count === 1 ? '' : 'e'})`);
            
            if (updatedText !== currentText) {
                button.innerHTML = updatedText;
                console.log(`✅ [AUTO-UPDATE] Updated ${category} count: ${count} models`);
            }
        }
    });
}

/**
 * Manual refresh für Quick-Presets (kann von außen aufgerufen werden)
 */
async function refreshQuickPresets() {
    console.log('🔄 [MANUAL-REFRESH] Manually refreshing quick presets...');
    await updateQuickPresetLabels();
    console.log('✅ [MANUAL-REFRESH] Quick presets refreshed');
}

// Export search functions to global scope
window.startSingleSearch = startSingleSearch;
window.startBatchSearch = startBatchSearch;
window.cancelBatchSearch = cancelBatchSearch;
window.cancelSingleSearch = cancelSingleSearch;
window.loadModelsForFilter = loadModelsForFilter;
window.validateSearchForm = validateSearchForm;
window.handleSearchOptionsChange = handleSearchOptionsChange;
window.handleBatchCountInput = handleBatchCountInput;
window.toggleBatchOptions = toggleBatchOptions;
window.updateRangeInfo = updateRangeInfo;
window.SearchState = SearchState;

// Export UI Revolution functions
window.selectQuickPreset = selectQuickPreset;
window.getBestPerformingModels = getBestPerformingModels;
window.refreshQuickPresets = refreshQuickPresets;
window.updateQuickPresetLabels = updateQuickPresetLabels;
window.showAdvancedSelection = showAdvancedSelection;
window.hideAdvancedSelection = hideAdvancedSelection;
window.clearAllModels = clearAllModels;
window.updateSelectionCounter = updateSelectionCounter;
window.processSearchResults = processSearchResults;

// Initialize search options event handlers
document.addEventListener('DOMContentLoaded', function() {
    // Setup search option change handlers
    ['two_phase_enabled', 'smart_search_enabled', 'comprehensive_search_enabled'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', handleSearchOptionsChange);
        }
    });
    
    // Setup batch search option handlers
    ['batch_two_phase_enabled', 'batch_smart_search_enabled', 'batch_comprehensive_search_enabled'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', handleSearchOptionsChange);
        }
    });
});

// ====================================== 
// PROGRESS-FIX 29.08.2025: Progress Container Functions
// ======================================

let currentProgressSession = null;
let progressUpdateInterval = null;

/**
 * Zeigt den Progress-Container an und startet die Progress-Überwachung
 * PROGRESS-MERGE 29.08.2025: Unterstützt sowohl Session-basierte als auch direkte Updates
 */
function showProgressContainer(sessionIdOrState, totalMines, totalModels) {
    const progressContainer = document.getElementById('batch-progress-container');
    if (!progressContainer) return;
    
    // TIMING-FIX 04.09.2025: Progress-Startzeit tracken
    window.progressStartTime = Date.now();
    
    // Container anzeigen
    progressContainer.style.display = 'block';
    
    // Wenn erster Parameter ein State ist (z.B. 'uploading'), direkter Modus
    if (typeof sessionIdOrState === 'string' && ['uploading', 'processing_csv', 'source_discovery', 'model_execution'].includes(sessionIdOrState)) {
        // Direkter Modus - kein Session-Tracking
        currentProgressSession = {
            sessionId: null,
            totalMines: totalMines || 0,
            totalModels: totalModels || 0,
            startTime: Date.now(),
            directMode: true,
            currentState: sessionIdOrState
        };
        
        // Fortschritt zurücksetzen
        resetProgressDisplay();
        
        // Direktes Status-Update
        updateTextElement('progress-status', getStatusText(sessionIdOrState));
        updateTextElement('current-activity', getActivityForState(sessionIdOrState));
        
        console.log(`📊 [PROGRESS] Progress-Container gestartet im Direct-Modus: ${sessionIdOrState}`);
    } else {
        // Session-basierter Modus
        currentProgressSession = {
            sessionId: sessionIdOrState,
            totalMines,
            totalModels,
            startTime: Date.now(),
            directMode: false
        };
        
        // Fortschritt zurücksetzen
        resetProgressDisplay();
        
        // Progress-Updates starten
        startProgressUpdates();
        
        console.log(`📊 [PROGRESS] Progress-Container gestartet für Session ${sessionIdOrState}`);
    }
}

/**
 * Versteckt den Progress-Container und stoppt Updates
 */
function hideProgressContainer() {
    const progressContainer = document.getElementById('batch-progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
    
    // Updates stoppen
    if (progressUpdateInterval) {
        clearInterval(progressUpdateInterval);
        progressUpdateInterval = null;
    }
    
    currentProgressSession = null;
    console.log('📊 [PROGRESS] Progress-Container versteckt');
}

/**
 * Setzt die Progress-Anzeige zurück
 */
function resetProgressDisplay() {
    // Progress-Bars zurücksetzen
    const overallBar = document.getElementById('overall-progress-bar');
    const mineBar = document.getElementById('mine-progress-bar');
    if (overallBar) overallBar.style.width = '0%';
    if (mineBar) mineBar.style.width = '0%';
    
    // Text-Elemente zurücksetzen
    const elements = {
        'overall-progress-text': '0%',
        'current-mine-text': '-',
        'current-mine-name': 'Vorbereitung...',
        'progress-status': 'Initialisiere...',
        'sources-found': '0',
        'successful-results': '0',
        'failed-results': '0',
        'progress-eta': 'Berechne...',
        'current-activity': 'Batch-Suche wird vorbereitet...'
    };
    
    Object.entries(elements).forEach(([id, text]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = text;
    });
}

/**
 * Startet regelmäßige Progress-Updates
 */
function startProgressUpdates() {
    if (!currentProgressSession) {
        console.warn('📊 [PROGRESS] startProgressUpdates: currentProgressSession ist null');
        return;
    }
    
    console.log(`📊 [PROGRESS] Starte Progress-Updates für Session: ${currentProgressSession.sessionId}`);
    
    // Alle 2 Sekunden Progress abrufen
    progressUpdateInterval = setInterval(async () => {
        if (!currentProgressSession) {
            clearInterval(progressUpdateInterval);
            return;
        }
        
        try {
            await updateProgressDisplay();
        } catch (error) {
            console.error('📊 [PROGRESS] Fehler beim Update:', error);
        }
    }, 2000);
    
    // Erstes Update sofort
    updateProgressDisplay();
}

/**
 * Aktualisiert die Progress-Anzeige
 */
async function updateProgressDisplay() {
    if (!currentProgressSession) {
        console.warn('📊 [PROGRESS] updateProgressDisplay: currentProgressSession ist null');
        return;
    }
    
    console.log(`📊 [PROGRESS] Updating display für Session: ${currentProgressSession.sessionId}`);
    
    try {
        // Progress vom Backend abrufen 
        const response = await fetch(`${window.API_BASE_URL}/api/progress/${currentProgressSession.sessionId}`);
        if (!response.ok) {
            console.warn('📊 [PROGRESS] Kein Progress verfügbar für Session, stoppe Updates');
            // Stoppe Progress-Updates bei anhaltenden 404-Fehlern
            clearInterval(progressUpdateInterval);
            hideProgressContainer();
            return;
        }
        
        const data = await response.json();
        if (!data.success || !data.data) {
            console.warn('📊 [PROGRESS] Invalid progress data received');
            return;
        }
        
        const progress = data.data;
        
        // TIMING-FIX 04.09.2025: Ignoriere 'completed' in den ersten 5 Sekunden
        const timeSinceStart = Date.now() - (window.progressStartTime || 0);
        if ((progress.status === 'completed' || progress.status === 'finished') && timeSinceStart > 5000) {
            console.log('📊 [PROGRESS] Batch completed, stopping updates');
            clearInterval(progressUpdateInterval);
            setTimeout(() => hideProgressContainer(), 2000);
            return;
        } else if (progress.status === 'completed' && timeSinceStart <= 5000) {
            console.log(`📊 [PROGRESS] Ignoring premature 'completed' status (${Math.round(timeSinceStart/1000)}s since start)`);
        }
        
        // Berechne Progress-Prozentsatz für einfache Progress-Daten
        const totalProgress = progress.total ? Math.round((progress.completed / progress.total) * 100) : 0;
        const currentMineProgress = progress.current_mine_progress || totalProgress;
        
        // Progress-Bars aktualisieren (kompatibel mit altem und neuem Format)
        updateProgressBar('overall-progress-bar', progress.overall_progress || totalProgress);
        updateProgressBar('mine-progress-bar', progress.mine_progress || currentMineProgress);
        
        // Text-Elemente aktualisieren (kompatibel mit altem und neuem Format)
        updateTextElement('overall-progress-text', `${progress.overall_progress || totalProgress}%`);
        updateTextElement('current-mine-text', progress.current_mine || `${progress.completed || 0}/${progress.total || 1}`);
        updateTextElement('current-mine-name', progress.current_mine_name || progress.message || 'Verarbeite...');
        updateTextElement('progress-status', getStatusText(progress.state || progress.status));
        updateTextElement('sources-found', progress.sources_found || 0);
        updateTextElement('successful-results', progress.successful_results || progress.completed || 0);
        updateTextElement('failed-results', progress.failed_results || progress.failed || 0);
        updateTextElement('progress-eta', progress.eta || 'Unbekannt');
        
        // Aktivität aktualisieren
        updateCurrentActivity(progress);
        
        // Bei Abschluss: Container nach 3 Sekunden verstecken (unterstütze beide Status-Formate)
        if (progress.state === 'batch_complete' || progress.state === 'error' || 
            progress.status === 'completed' || progress.status === 'error') {
            setTimeout(() => hideProgressContainer(), 3000);
        }
        
    } catch (error) {
        console.error('📊 [PROGRESS] Fehler beim Progress-Abruf:', error);
    }
}

/**
 * Aktualisiert eine Progress-Bar
 */
function updateProgressBar(elementId, percentage) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.width = `${Math.max(0, Math.min(100, percentage))}%`;
    }
}

/**
 * Aktualisiert ein Text-Element
 */
function updateTextElement(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

/**
 * Konvertiert Progress-Status zu benutzerfreundlichem Text
 */
function getStatusText(state) {
    const statusMap = {
        'uploading': 'CSV wird hochgeladen',
        'processing_csv': 'CSV wird verarbeitet',
        // 2-PHASEN WORKFLOW STATES (29.08.2025)
        'collecting_sources': 'Sammle Quellen von allen Modellen',
        'extracting_data': 'Extrahiere Daten mit allen Quellen',
        // Legacy States (für Kompatibilität)
        'source_discovery': 'Quellen werden gesucht',
        'model_execution': 'Modelle werden ausgeführt',
        'saving_results': 'Ergebnisse werden gespeichert',
        'mine_complete': 'Mine abgeschlossen',
        'batch_complete': 'Batch-Suche abgeschlossen',
        'error': 'Fehler aufgetreten',
        // Neue Status-Werte für Fallback-System
        'running': 'Verarbeitung läuft',
        'completed': 'Abgeschlossen',
        'unknown': 'Status unbekannt'
    };
    
    return statusMap[state] || state || 'Unbekannt';
}

/**
 * Aktualisiert die aktuelle Aktivitäts-Anzeige
 */
function updateCurrentActivity(progress) {
    let activity = 'Batch-Suche läuft...';
    
    if (progress.state === 'source_discovery') {
        activity = `Suche Quellen für ${progress.current_mine_name || 'Mine'}...`;
    } else if (progress.state === 'model_execution') {
        activity = `Führe Modell ${progress.current_model || ''} aus...`;
    } else if (progress.state === 'saving_results') {
        activity = `Speichere Ergebnisse für ${progress.current_mine_name || 'Mine'}...`;
    } else if (progress.state === 'mine_complete') {
        activity = `Mine '${progress.current_mine_name || 'Mine'}' abgeschlossen`;
    } else if (progress.state === 'batch_complete') {
        activity = `✅ Batch-Suche erfolgreich abgeschlossen!`;
    } else if (progress.state === 'error') {
        activity = `⚠️ Fehler: ${progress.message || 'Unbekannter Fehler'}`;
    }
    
    updateTextElement('current-activity', activity);
}

/**
 * PROGRESS-MERGE 29.08.2025: Direkte Aktivitäts-Update-Funktion
 */
function updateProgressActivity(message) {
    updateTextElement('current-activity', message);
}

/**
 * PROGRESS-MERGE 29.08.2025: Gibt Aktivität für State zurück
 */
function getActivityForState(state) {
    const activities = {
        'uploading': 'CSV-Datei wird hochgeladen...',
        'processing_csv': 'CSV-Daten werden verarbeitet...',
        // 2-PHASEN WORKFLOW ACTIVITIES (29.08.2025)
        'collecting_sources': '🔍 Sammle Quellen von allen Modellen...',
        'extracting_data': '⚡ Extrahiere Daten mit allen gefundenen Quellen...',
        // Legacy Activities (für Kompatibilität)
        'source_discovery': 'Quellen werden gesucht...',
        'model_execution': 'Modelle werden ausgeführt...',
        'saving_results': 'Ergebnisse werden gespeichert...',
        'batch_complete': '✅ Batch-Suche erfolgreich abgeschlossen!',
        'error': '⚠️ Fehler bei der Verarbeitung'
    };
    
    return activities[state] || 'Batch-Suche läuft...';
}

/**
 * PROGRESS-MERGE 29.08.2025: Direkte Progress-Updates für nicht-Session-basierte Operationen
 */
function updateProgressState(state, message, percentage) {
    if (!currentProgressSession) return;
    
    // PROGRESS FIX: Nicht überschreiben wenn im Session-basierten Modus
    if (!currentProgressSession.directMode) {
        console.log(`📊 [PROGRESS] Ignoring updateProgressState(${state}) because in session-based mode`);
        return;
    }
    
    currentProgressSession.currentState = state;
    
    updateTextElement('progress-status', getStatusText(state));
    updateTextElement('current-activity', message || getActivityForState(state));
    
    if (percentage !== undefined) {
        updateProgressBar('overall-progress-bar', percentage);
        updateTextElement('overall-progress-text', `${percentage}%`);
    }
}

/**
 * Bricht die aktuelle Batch-Suche ab
 */
function cancelCurrentBatch() {
    if (batchSearchAbortController) {
        batchSearchAbortController.abort();
        hideProgressContainer();
        showNotification('Batch-Suche wurde abgebrochen', 'warning');
    }
}

// Export Progress Functions
window.showProgressContainer = showProgressContainer;
window.hideProgressContainer = hideProgressContainer;
window.cancelCurrentBatch = cancelCurrentBatch;

console.log('🔍 MineSearch 2.0 - Search Functions loaded');
console.log('📊 [PROGRESS] Progress Container Functions loaded');