#!/usr/bin/env node

/**
 * Browser Simulation Test for Models Loading
 * This script simulates a browser environment to test the JavaScript execution
 */

const fs = require('fs');
const path = require('path');

// Simulate basic DOM and fetch API
global.console = {
    log: (...args) => console.log('[BROWSER LOG]', ...args),
    error: (...args) => console.error('[BROWSER ERROR]', ...args),
    warn: (...args) => console.warn('[BROWSER WARN]', ...args)
};

global.document = {
    getElementById: (id) => {
        console.log(`[DOM] getElementById('${id}') called`);
        if (id === 'model-selection') {
            return {
                innerHTML: '',
                style: {}
            };
        }
        return null;
    },
    addEventListener: (event, callback) => {
        console.log(`[DOM] addEventListener('${event}') called`);
        if (event === 'DOMContentLoaded') {
            // Simulate DOM ready after a short delay
            setTimeout(callback, 100);
        }
    }
};

global.fetch = async (url) => {
    console.log(`[FETCH] Making request to: ${url}`);
    
    if (url.includes('/api/models')) {
        // Simulate successful API response
        return {
            status: 200,
            ok: true,
            json: async () => ({
                success: true,
                models: {
                    'perplexity:sonar': {
                        name: 'Test Model 1',
                        description: 'Test Description 1',
                        provider: 'perplexity',
                        is_free: false,
                        timeout: 30
                    },
                    'openrouter:test': {
                        name: 'Test Model 2', 
                        description: 'Test Description 2',
                        provider: 'openrouter',
                        is_free: true,
                        timeout: 60
                    }
                }
            })
        };
    }
    
    throw new Error('Unknown URL');
};

// Simulate window and other globals
global.window = {
    location: { href: 'http://localhost:3000/' }
};

// Load the essential JavaScript code from the HTML file
const indexPath = path.join(__dirname, 'index.html');
const indexContent = fs.readFileSync(indexPath, 'utf8');

// Extract JavaScript code (simplified extraction)
const jsStart = indexContent.indexOf('<script>');
const jsEnd = indexContent.lastIndexOf('</script>');

if (jsStart === -1 || jsEnd === -1) {
    console.error('[TEST] Could not extract JavaScript from HTML');
    process.exit(1);
}

const jsCode = indexContent.substring(jsStart + 8, jsEnd);

// Define constants that should be available
const API_BASE_URL = 'http://localhost:8000';

// Mock required functions that might not be defined in extracted JS
global.showEnhancedLoadingState = (element, message, showProgress) => {
    console.log(`[MOCK] showEnhancedLoadingState called: ${message}`);
    if (element) {
        element.innerHTML = `<div>Loading: ${message}</div>`;
    }
};

global.showGracefulError = (type, message, element, showRetry, callback) => {
    console.error(`[MOCK] showGracefulError: ${type} - ${message}`);
};

global.updateProviderCheckboxState = (provider) => {
    console.log(`[MOCK] updateProviderCheckboxState called for: ${provider}`);
};

console.log('[TEST] Starting browser simulation...');
console.log('[TEST] Simulating JavaScript execution...');

try {
    // Execute the JavaScript code
    eval(`
        const API_BASE_URL = 'http://localhost:8000';
        
        // Extract and execute only the loadAvailableModels function and DOM ready handler
        ${jsCode.match(/async function loadAvailableModels\(\)[\s\S]*?^}/m)?.[0] || ''}
        
        ${jsCode.match(/document\.addEventListener\('DOMContentLoaded'[\s\S]*?}\);/m)?.[0] || ''}
    `);
    
    // Wait for async operations to complete
    setTimeout(() => {
        console.log('[TEST] Test completed');
    }, 2000);
    
} catch (error) {
    console.error('[TEST] Error executing JavaScript:', error);
}