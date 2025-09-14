/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: MineSearch 2.0 - API Communication Layer
 * 
 * ÄNDERUNG 10.08.2025: Extrahiert aus index.html (8961 → 500 Zeilen Regel)
 * Zentralisierte API-Kommunikation mit Error Handling und Timeout Management
 */

// ============================================
// API CONFIGURATION
// ============================================

// API Base URL Konstante
const API_BASE_URL = window.location.origin;

// CRITICAL FIX: Make API_BASE_URL globally accessible
window.API_BASE_URL = API_BASE_URL;

// API Request timeout configuration
const API_TIMEOUT = 30000; // 30 seconds
const API_LONG_TIMEOUT = 120000; // 2 minutes for heavy operations

// ============================================
// CORE API REQUEST HANDLER
// ============================================

class ApiClient {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
        this.abortControllers = new Map();
    }
    
    // Erstelle AbortController für Request-Cancellation
    createAbortController(requestId) {
        if (this.abortControllers.has(requestId)) {
            this.abortControllers.get(requestId).abort();
        }
        
        const controller = new AbortController();
        this.abortControllers.set(requestId, controller);
        return controller;
    }
    
    // Cleanup AbortController
    cleanupAbortController(requestId) {
        if (this.abortControllers.has(requestId)) {
            this.abortControllers.delete(requestId);
        }
    }
    
    // Basis HTTP Request mit Error Handling
    async request(endpoint, options = {}) {
        const requestId = options.requestId || `req_${Date.now()}_${Math.random()}`;
        const controller = this.createAbortController(requestId);
        
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            signal: controller.signal,
            timeout: API_TIMEOUT
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        delete finalOptions.requestId;
        delete finalOptions.timeout;
        
        try {
            // Timeout Promise
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Request timeout')), finalOptions.timeout || API_TIMEOUT);
            });
            
            // Fetch Promise
            const fetchPromise = fetch(`${this.baseUrl}${endpoint}`, finalOptions);
            
            // Race zwischen Fetch und Timeout
            const response = await Promise.race([fetchPromise, timeoutPromise]);
            
            // Cleanup
            this.cleanupAbortController(requestId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
            
        } catch (error) {
            this.cleanupAbortController(requestId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request wurde abgebrochen');
            }
            
            console.error(`API Request Error [${endpoint}]:`, error);
            throw error;
        }
    }
    
    // Convenience methods
    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }
    
    async post(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    async postForm(endpoint, formData, options = {}) {
        const headers = { ...options.headers };
        delete headers['Content-Type']; // Let browser set boundary for FormData
        
        return this.request(endpoint, {
            ...options,
            method: 'POST',
            headers,
            body: formData
        });
    }
    
    // Abort specific request
    abortRequest(requestId) {
        if (this.abortControllers.has(requestId)) {
            this.abortControllers.get(requestId).abort();
            this.cleanupAbortController(requestId);
        }
    }
    
    // Abort all pending requests
    abortAllRequests() {
        for (const [requestId, controller] of this.abortControllers) {
            controller.abort();
        }
        this.abortControllers.clear();
    }
}

// Global API client instance
const apiClient = new ApiClient();

// ============================================
// SPECIFIC API ENDPOINTS
// ============================================

// Models API
const ModelsAPI = {
    async getAvailable() {
        return apiClient.get('/api/models/available');
    },
    
    async getInfo() {
        return apiClient.get('/api/models/info');
    }
};

// Search API
const SearchAPI = {
    async searchMines(data, requestId = null) {
        const options = { 
            timeout: API_LONG_TIMEOUT,
            requestId: requestId || `search_${Date.now()}`
        };
        return apiClient.post('/api/search/mines', data, options);
    },
    
    async batchSearch(data, requestId = null) {
        const options = { 
            timeout: API_LONG_TIMEOUT,
            requestId: requestId || `batch_${Date.now()}`
        };
        return apiClient.post('/api/batch/search', data, options);
    },
    
    abortSearch(requestId) {
        apiClient.abortRequest(requestId);
    }
};

// Sources API
const SourcesAPI = {
    async getGrouped(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/sources/grouped${queryString ? `?${queryString}` : ''}`;
        return apiClient.get(endpoint);
    },
    
    async getByDomain(domain) {
        return apiClient.get(`/api/sources/by-domain/${encodeURIComponent(domain)}`);
    },
    
    async getStatistics() {
        return apiClient.get('/api/sources/stats');
    }
};

// Statistics API  
const StatisticsAPI = {
    async getModelStatistics(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/statistics/models${queryString ? `?${queryString}` : ''}`;
        return apiClient.get(endpoint);
    },
    
    async getDetailedStats(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/statistics/detailed${queryString ? `?${queryString}` : ''}`;
        return apiClient.get(endpoint);
    },
    
    async exportCSV(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/statistics/export/csv${queryString ? `?${queryString}` : ''}`;
        
        // For file downloads, use direct link instead of JSON response
        const link = document.createElement('a');
        link.href = `${API_BASE_URL}${endpoint}`;
        link.download = `statistics_export_${Date.now()}.csv`;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        return { success: true, message: 'Download gestartet' };
    }
};

// Results API
const ResultsAPI = {
    async getConsolidated(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/results/consolidated${queryString ? `?${queryString}` : ''}`;
        return apiClient.get(endpoint);
    },
    
    async getBySession(sessionId, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/results/session/${sessionId}${queryString ? `?${queryString}` : ''}`;
        return apiClient.get(endpoint);
    }
};

// Health Check API
const HealthAPI = {
    async check() {
        return apiClient.get('/health');
    },
    
    async detailed() {
        return apiClient.get('/health/detailed');
    }
};

// ============================================
// ERROR HANDLING UTILITIES
// ============================================

function handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    
    let userMessage = 'Ein unbekannter Fehler ist aufgetreten.';
    
    if (error.message.includes('timeout')) {
        userMessage = 'Die Anfrage hat zu lange gedauert. Bitte versuchen Sie es erneut.';
    } else if (error.message.includes('Network')) {
        userMessage = 'Netzwerkfehler. Bitte überprüfen Sie Ihre Internetverbindung.';
    } else if (error.message.includes('HTTP 404')) {
        userMessage = 'Die angeforderte Ressource wurde nicht gefunden.';
    } else if (error.message.includes('HTTP 500')) {
        userMessage = 'Serverfehler. Bitte versuchen Sie es später erneut.';
    } else if (error.message.includes('abgebrochen')) {
        userMessage = 'Die Anfrage wurde abgebrochen.';
    }
    
    if (typeof showNotification === 'function') {
        showNotification(userMessage, 'error');
    }
    
    return userMessage;
}

// ============================================
// CONNECTION STATUS MONITORING
// ============================================

class ConnectionMonitor {
    constructor() {
        this.isOnline = navigator.onLine;
        this.listeners = [];
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.notifyListeners('online');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.notifyListeners('offline');
        });
    }
    
    addListener(callback) {
        this.listeners.push(callback);
    }
    
    removeListener(callback) {
        const index = this.listeners.indexOf(callback);
        if (index > -1) {
            this.listeners.splice(index, 1);
        }
    }
    
    notifyListeners(status) {
        this.listeners.forEach(callback => callback(status, this.isOnline));
    }
    
    async checkApiConnection() {
        try {
            await HealthAPI.check();
            return true;
        } catch (error) {
            return false;
        }
    }
}

// Global connection monitor
const connectionMonitor = new ConnectionMonitor();

// ============================================
// INITIALIZATION
// ============================================

// Setup connection monitoring
connectionMonitor.addListener((status, isOnline) => {
    console.log(`Connection status: ${status} (Online: ${isOnline})`);
    
    if (typeof showNotification === 'function') {
        if (status === 'online') {
            showNotification('✅ Internetverbindung wiederhergestellt', 'success');
        } else {
            showNotification('⚠️ Keine Internetverbindung', 'error');
        }
    }
});

// Export API modules to global scope for backward compatibility
window.ModelsAPI = ModelsAPI;
window.SearchAPI = SearchAPI;
window.SourcesAPI = SourcesAPI;
window.StatisticsAPI = StatisticsAPI;
window.ResultsAPI = ResultsAPI;
window.HealthAPI = HealthAPI;
window.apiClient = apiClient;
window.handleApiError = handleApiError;
window.connectionMonitor = connectionMonitor;

console.log('🔌 MineSearch 2.0 - API Layer loaded');