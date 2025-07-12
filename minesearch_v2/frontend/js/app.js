/*
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Main Application Logic für MineSearch v2
*/

class MineSearchApp {
    constructor() {
        this.version = '2.0';
        this.init();
    }

    init() {
        console.log(`MineSearch ${this.version} initialized`);
        this.setupErrorHandling();
        this.loadInitialData();
    }

    setupErrorHandling() {
        window.addEventListener('error', (e) => {
            console.error('Application error:', e.error);
            this.showNotification('Ein unerwarteter Fehler ist aufgetreten.', 'error');
        });
    }

    async loadInitialData() {
        try {
            // Load models from backend
            await this.loadModels();
            
            // Load initial statistics or configuration data
            const response = await fetch('/health');
            const health = await response.json();
            
            if (health.status === 'ok') {
                this.showNotification('System bereit', 'success');
            }
        } catch (error) {
            console.warn('Could not load initial data:', error);
        }
    }

    async loadModels() {
        try {
            const response = await fetch('http://localhost:8000/api/models');
            const data = await response.json();
            
            if (data.success && data.models) {
                this.renderModelSelection(data.models);
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            const modelSelection = document.getElementById('model-selection');
            if (modelSelection) {
                modelSelection.innerHTML = '<p style="color: #dc3545;">Fehler beim Laden der Modelle. Backend nicht erreichbar.</p>';
            }
        }
    }

    renderModelSelection(models) {
        const modelSelection = document.getElementById('model-selection');
        if (!modelSelection) return;

        let html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px;">';
        
        Object.entries(models).forEach(([key, model]) => {
            html += `
                <label style="display: flex; align-items: center; gap: 8px; padding: 8px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">
                    <input type="checkbox" name="models" value="${key}" style="width: 16px; height: 16px;">
                    <div>
                        <strong style="color: #333;">${model.name}</strong>
                        <br>
                        <small style="color: #666;">${model.description}</small>
                        <br>
                        <small style="color: #888;">Provider: ${model.provider} | Timeout: ${model.timeout}s</small>
                    </div>
                </label>
            `;
        });
        
        html += '</div>';
        modelSelection.innerHTML = html;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    // Utility method for API calls
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        try {
            const response = await fetch(endpoint, defaultOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MineSearchApp();
});