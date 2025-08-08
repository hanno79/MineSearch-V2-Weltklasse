/**
 * Author: rahn
 * Datum: 04.08.2025
 * Version: 1.0
 * Beschreibung: Enhanced Progress Tracking System für MineSearch v2
 */

class ProgressTrackingSystem {
    constructor() {
        this.activeConnections = new Map();
        this.currentSessionId = null;
        this.baseUrl = window.location.origin;
        this.wsUrl = this.baseUrl.replace('http', 'ws');
    }

    /**
     * Erstelle neue Progress-Session und starte WebSocket-Verbindung
     */
    async createProgressSession(mines, models) {
        try {
            const response = await fetch(`${this.baseUrl}/api/progress/create-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mines: mines,
                    models: models
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.currentSessionId = result.session_id;
                console.log(`Progress session created: ${this.currentSessionId}`);
                return result.session_id;
            } else {
                throw new Error(result.detail || 'Failed to create progress session');
            }
        } catch (error) {
            console.error('Error creating progress session:', error);
            throw error;
        }
    }

    /**
     * Erstelle erweiterte Loading-Komponente mit Progress-Bar
     */
    createEnhancedLoadingHTML(title, message = '', sessionId = null) {
        const progressBarId = `progress-bar-${Date.now()}`;
        const progressTextId = `progress-text-${Date.now()}`;
        const currentOperationId = `current-operation-${Date.now()}`;
        const etaId = `eta-${Date.now()}`;

        return `
            <div class="enhanced-loading-container" style="
                padding: 30px; 
                text-align: center; 
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                border-radius: 12px; 
                border: 2px solid #0ea5e9;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin: 20px 0;
            ">
                <h3 style="color: #0c4a6e; margin-bottom: 15px; font-size: 1.5em;">
                    ${this.sanitizeHTML(title)}
                </h3>
                
                ${message ? `<p style="color: #0369a1; margin-bottom: 20px;">${this.sanitizeHTML(message)}</p>` : ''}
                
                ${sessionId ? `
                    <!-- Progress Bar Container -->
                    <div class="progress-container" style="
                        background: #e2e8f0; 
                        border-radius: 10px; 
                        height: 30px; 
                        margin: 20px 0;
                        position: relative;
                        overflow: hidden;
                        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <div id="${progressBarId}" class="progress-fill" style="
                            height: 100%; 
                            background: linear-gradient(90deg, #0ea5e9, #0284c7);
                            width: 0%; 
                            transition: width 0.5s ease;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-weight: bold;
                            font-size: 14px;
                            border-radius: 8px;
                        ">
                            <span id="${progressTextId}">0%</span>
                        </div>
                    </div>
                    
                    <!-- Progress Information -->
                    <div class="progress-info" style="
                        display: grid; 
                        grid-template-columns: 1fr 1fr; 
                        gap: 15px; 
                        margin-top: 20px;
                        font-size: 14px;
                    ">
                        <div style="
                            background: rgba(255,255,255,0.7); 
                            padding: 10px; 
                            border-radius: 8px;
                            border: 1px solid #cbd5e1;
                        ">
                            <strong style="color: #475569;">Aktuelle Operation:</strong><br>
                            <span id="${currentOperationId}" style="color: #0f172a;">Initialisiere...</span>
                        </div>
                        
                        <div style="
                            background: rgba(255,255,255,0.7); 
                            padding: 10px; 
                            border-radius: 8px;
                            border: 1px solid #cbd5e1;
                        ">
                            <strong style="color: #475569;">Geschätzte Zeit:</strong><br>
                            <span id="${etaId}" style="color: #0f172a;">Berechne...</span>
                        </div>
                    </div>
                ` : ''}
                
                <!-- Loading Spinner -->
                <div class="loading-spinner" style="
                    margin: 20px auto 0; 
                    width: 40px; 
                    height: 40px; 
                    border: 4px solid #cbd5e1; 
                    border-top: 4px solid #0ea5e9; 
                    border-radius: 50%; 
                    animation: spin 1s linear infinite;
                "></div>
                
                ${sessionId ? `
                    <!-- WebSocket Status -->
                    <div class="websocket-status" style="
                        margin-top: 15px; 
                        font-size: 12px; 
                        color: #64748b;
                    ">
                        <span id="ws-status-${sessionId}">🔄 Verbindung wird hergestellt...</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Zeige Enhanced Loading Message mit Progress-Tracking
     */
    showEnhancedLoadingMessage(element, title, message = '', mines = [], models = []) {
        // VALIDATION: Prüfe ob Element und Titel vorhanden sind
        if (!element) {
            console.error('❌ showEnhancedLoadingMessage: Element is null or undefined');
            return;
        }
        
        if (!title || title.trim() === '') {
            console.error('❌ showEnhancedLoadingMessage: Title is empty');
            title = 'Loading...';
        }
        
        console.log(`🚀 showEnhancedLoadingMessage: "${title}" (mines: ${mines.length}, models: ${models.length})`);
        
        // BUGFIX 04.08.2025: Zeige sofort Loading-HTML mit Placeholder
        const tempSessionId = `temp-${Date.now()}`;
        element.innerHTML = this.createEnhancedLoadingHTML(title, message, tempSessionId);
        
        // Erstelle Session wenn Minen und Modelle gegeben sind
        if (mines.length > 0 && models.length > 0) {
            console.log(`🚀 Creating progress session for ${mines.length} mines × ${models.length} models`);
            
            this.createProgressSession(mines, models)
                .then(sessionId => {
                    console.log(`✅ Progress session created: ${sessionId}, updating HTML...`);
                    // Update HTML mit echter Session-ID
                    element.innerHTML = this.createEnhancedLoadingHTML(title, message, sessionId);
                    // Verbinde WebSocket
                    this.connectWebSocket(sessionId, element);
                })
                .catch(error => {
                    console.error('Progress session creation failed, keeping basic progress UI:', error);
                    // Behalte die Progress-UI, aber ohne WebSocket
                    console.log('Keeping progress UI without WebSocket connection');
                });
        } else {
            console.log('No mines/models provided, showing basic enhanced loading with 3-second minimum display');
            // Fallback ohne Progress-Tracking, aber mit Progress-Bar-UI
            element.innerHTML = this.createEnhancedLoadingHTML(title, message, tempSessionId);
            
            // Minimum 3 Sekunden anzeigen, damit User den Progress-Bar sieht
            this.minDisplayTimeout = setTimeout(() => {
                console.log('Minimum display time reached for basic loading');
            }, 3000);
        }
    }

    /**
     * Verbinde WebSocket für Real-time Progress Updates
     */
    connectWebSocket(sessionId, element) {
        if (this.activeConnections.has(sessionId)) {
            console.log(`WebSocket already connected for session: ${sessionId}`);
            return;
        }

        const wsUrl = `${this.wsUrl}/ws/search-progress/${sessionId}`;
        console.log(`Connecting to WebSocket: ${wsUrl}`);

        try {
            const websocket = new WebSocket(wsUrl);
            
            websocket.onopen = (event) => {
                console.log(`WebSocket connected for session: ${sessionId}`);
                this.activeConnections.set(sessionId, websocket);
                this.updateWebSocketStatus(sessionId, '🟢 Verbunden - Live Updates aktiv');
                
                // Sende Ping für initialen Status
                websocket.send(JSON.stringify({ type: 'ping' }));
            };

            websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleProgressUpdate(sessionId, data, element);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            websocket.onclose = (event) => {
                console.log(`WebSocket closed for session: ${sessionId}, code: ${event.code}`);
                this.activeConnections.delete(sessionId);
                this.updateWebSocketStatus(sessionId, '🔴 Verbindung getrennt');
                
                // BUGFIX 04.08.2025: Auto-Reconnect bei unerwarteter Trennung
                if (event.code !== 1000 && event.code !== 1001) {
                    console.log(`Attempting WebSocket reconnect for session: ${sessionId} in 3 seconds...`);
                    setTimeout(() => {
                        if (!this.activeConnections.has(sessionId)) {
                            console.log(`Reconnecting WebSocket for session: ${sessionId}`);
                            this.connectWebSocket(sessionId, element);
                        }
                    }, 3000);
                }
            };

            websocket.onerror = (error) => {
                console.error(`WebSocket error for session: ${sessionId}`, error);
                this.updateWebSocketStatus(sessionId, '⚠️ Verbindungsfehler');
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateWebSocketStatus(sessionId, '❌ Verbindung fehlgeschlagen');
        }
    }

    /**
     * Handle Progress Updates from WebSocket
     */
    handleProgressUpdate(sessionId, data, element) {
        console.log(`Progress update for session ${sessionId}:`, data);

        if (data.type === 'progress_update' && data.data) {
            const progressData = data.data;
            this.updateProgressDisplay(sessionId, progressData);
        } else if (data.type === 'pong' && data.data) {
            const progressData = data.data;
            this.updateProgressDisplay(sessionId, progressData);
        }
    }

    /**
     * Update Progress Display Elements
     */
    updateProgressDisplay(sessionId, progressData) {
        const progressBar = document.querySelector(`[id*="progress-bar"]`);
        const progressText = document.querySelector(`[id*="progress-text"]`);
        const currentOperation = document.querySelector(`[id*="current-operation"]`);
        const eta = document.querySelector(`[id*="eta"]`);

        if (progressBar && progressText) {
            const percentage = progressData.percentage || 0;
            progressBar.style.width = `${percentage}%`;
            progressText.textContent = `${percentage.toFixed(1)}%`;
        }

        if (currentOperation) {
            if (progressData.current_mine && progressData.current_model) {
                currentOperation.textContent = `${progressData.current_mine} mit ${progressData.current_model}`;
            } else {
                currentOperation.textContent = progressData.current_operation || 'Bearbeite...';
            }
        }

        if (eta && progressData.eta_seconds) {
            const etaMinutes = Math.ceil(progressData.eta_seconds / 60);
            eta.textContent = `~${etaMinutes} Min`;
        } else if (eta) {
            eta.textContent = 'Berechne...';
        }

        // Update WebSocket Status
        this.updateWebSocketStatus(sessionId, `🟢 Live - ${progressData.current}/${progressData.total} Operationen`);
    }

    /**
     * Update WebSocket Status Display
     */
    updateWebSocketStatus(sessionId, status) {
        const statusElement = document.getElementById(`ws-status-${sessionId}`);
        if (statusElement) {
            statusElement.textContent = status;
        }
    }

    /**
     * Disconnect WebSocket Connection
     */
    disconnectWebSocket(sessionId) {
        const websocket = this.activeConnections.get(sessionId);
        if (websocket) {
            websocket.close();
            this.activeConnections.delete(sessionId);
            console.log(`WebSocket disconnected for session: ${sessionId}`);
        }
    }

    /**
     * Hide Enhanced Loading Message
     */
    hideEnhancedLoadingMessage(element = null) {
        // Clear minimum display timeout if active
        if (this.minDisplayTimeout) {
            clearTimeout(this.minDisplayTimeout);
            this.minDisplayTimeout = null;
        }
        
        const hideElements = () => {
            if (element) {
                // Entferne Progress-Container aus spezifischem Element
                const progressContainer = element.querySelector('.progress-container');
                if (progressContainer) {
                    progressContainer.remove();
                }
                
                // Entferne Enhanced Loading Container
                const enhancedContainer = element.querySelector('.enhanced-loading-container');
                if (enhancedContainer) {
                    enhancedContainer.remove();
                }
                
                // Reset innerHTML wenn komplett leer
                if (!element.innerHTML.trim()) {
                    element.innerHTML = '';
                }
            } else {
                // Entferne alle Progress-Container im Dokument
                document.querySelectorAll('.progress-container, .enhanced-loading-container').forEach(container => {
                    container.remove();
                });
            }
            
            // Cleanup WebSocket connections
            this.cleanup();
            
            console.log('✅ Enhanced loading message hidden');
        };
        
        // Wenn Minimum-Display aktiv ist, warte bis es abgelaufen ist
        if (this.minDisplayTimeout) {
            console.log('⏱️ Waiting for minimum display time before hiding');
            setTimeout(() => {
                hideElements();
            }, 500); // Zusätzliche 500ms Puffer
        } else {
            hideElements();
        }
    }

    /**
     * Cleanup all WebSocket connections
     */
    cleanup() {
        this.activeConnections.forEach((websocket, sessionId) => {
            websocket.close();
            console.log(`Cleanup: WebSocket closed for session: ${sessionId}`);
        });
        this.activeConnections.clear();
    }

    /**
     * HTML Sanitization Helper
     */
    sanitizeHTML(str) {
        if (typeof str !== 'string') return '';
        return str.replace(/[&<>"']/g, function(match) {
            const escapeMap = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;'
            };
            return escapeMap[match];
        });
    }
}

// Global Progress Tracking Instance
window.progressTracker = new ProgressTrackingSystem();

// Enhanced Loading Functions (backward compatible)
window.showEnhancedLoadingMessage = function(element, title, message = '', mines = [], models = []) {
    if (window.progressTracker) {
        window.progressTracker.showEnhancedLoadingMessage(element, title, message, mines, models);
    } else {
        console.error('Progress tracker not initialized');
        // Fallback to regular loading message
        element.innerHTML = `
            <div class="enhanced-loading">
                <div class="spinner"></div>
                <h3>${title}</h3>
                <p>${message}</p>
            </div>
        `;
    }
};

window.hideEnhancedLoadingMessage = function(element = null) {
    if (window.progressTracker) {
        window.progressTracker.hideEnhancedLoadingMessage(element);
    } else {
        console.error('Progress tracker not initialized');
        // Fallback: Remove common progress elements
        document.querySelectorAll('.progress-container, .enhanced-loading-container, .enhanced-loading').forEach(container => {
            container.remove();
        });
    }
};

// CSS Animation für Spinner
if (!document.getElementById('progress-tracking-styles')) {
    const style = document.createElement('style');
    style.id = 'progress-tracking-styles';
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .enhanced-loading-container {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .progress-fill {
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
    `;
    document.head.appendChild(style);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.progressTracker) {
        window.progressTracker.cleanup();
    }
});

console.log('✅ Progress Tracking System loaded successfully');