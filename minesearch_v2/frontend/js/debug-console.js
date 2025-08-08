/*
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Debug-Konsole für undefined-Fix Überwachung
*/

// Debug Console for undefined fix monitoring
window.DebugConsole = {
    enabled: false,
    logHistory: [],
    maxLogEntries: 100,
    
    // Initialize debug console
    init: function() {
        console.log('🐛 Debug Console wird initialisiert...');
        this.createDebugUI();
        this.setupKeyboardShortcuts();
        console.log('✅ Debug Console aktiviert (Strg+Shift+D zum öffnen)');
    },
    
    // Create debug UI overlay
    createDebugUI: function() {
        const debugPanel = document.createElement('div');
        debugPanel.id = 'debug-console';
        debugPanel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 400px;
            height: 300px;
            background: rgba(0, 0, 0, 0.9);
            color: #00ff00;
            font-family: monospace;
            font-size: 12px;
            padding: 10px;
            border-radius: 5px;
            z-index: 10000;
            display: none;
            overflow-y: auto;
            border: 1px solid #333;
        `;
        
        debugPanel.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px;">
                <h3 style="margin: 0; color: #00ff00;">🐛 Undefined Debug Console</h3>
                <button onclick="DebugConsole.close()" style="background: #ff4444; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer;">×</button>
            </div>
            <div style="margin-bottom: 10px;">
                <button onclick="DebugConsole.runUndefinedScan()" style="background: #0066cc; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-right: 5px;">🔍 Scan</button>
                <button onclick="DebugConsole.getStats()" style="background: #006600; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-right: 5px;">📊 Stats</button>
                <button onclick="DebugConsole.clearLog()" style="background: #666; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">🗑️ Clear</button>
            </div>
            <div id="debug-output" style="height: 200px; overflow-y: auto; background: rgba(0, 0, 0, 0.3); padding: 5px; border-radius: 3px;">
                <div style="color: #888;">Debug-Konsole bereit. Verwende die Buttons oben für Tests.</div>
            </div>
        `;
        
        document.body.appendChild(debugPanel);
        this.debugPanel = debugPanel;
    },
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts: function() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+D to toggle debug console
            if (e.ctrlKey && e.shiftKey && e.code === 'KeyD') {
                e.preventDefault();
                this.toggle();
            }
        });
    },
    
    // Toggle debug console visibility
    toggle: function() {
        if (!this.debugPanel) return;
        
        if (this.debugPanel.style.display === 'none') {
            this.open();
        } else {
            this.close();
        }
    },
    
    // Open debug console
    open: function() {
        if (!this.debugPanel) return;
        this.debugPanel.style.display = 'block';
        this.enabled = true;
        this.log('🐛 Debug Console geöffnet');
    },
    
    // Close debug console
    close: function() {
        if (!this.debugPanel) return;
        this.debugPanel.style.display = 'none';
        this.enabled = false;
    },
    
    // Log message to debug console
    log: function(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            message,
            type
        };
        
        this.logHistory.push(logEntry);
        
        // Keep only latest entries
        if (this.logHistory.length > this.maxLogEntries) {
            this.logHistory.shift();
        }
        
        // Update UI if visible
        if (this.enabled && this.debugPanel) {
            this.updateDebugOutput();
        }
    },
    
    // Update debug output display
    updateDebugOutput: function() {
        const output = document.getElementById('debug-output');
        if (!output) return;
        
        let html = '';
        this.logHistory.slice(-20).forEach(entry => { // Show last 20 entries
            const color = {
                'info': '#00ff00',
                'warn': '#ffaa00', 
                'error': '#ff4444',
                'success': '#00ff88'
            }[entry.type] || '#00ff00';
            
            html += `<div style="color: ${color}; margin-bottom: 2px;">
                <span style="color: #888;">[${entry.timestamp}]</span> ${entry.message}
            </div>`;
        });
        
        output.innerHTML = html;
        output.scrollTop = output.scrollHeight;
    },
    
    // Run undefined scan
    runUndefinedScan: function() {
        this.log('🔍 Starte undefined Scan...', 'info');
        
        try {
            let result = { detected: 0, fixed: 0, duration: 0 };
            
            // Try different scan methods
            if (window.UndefinedDetection && typeof window.UndefinedDetection.forceScan === 'function') {
                result = window.UndefinedDetection.forceScan();
                this.log(`✅ UndefinedDetection Scan: ${result.detected} detected, ${result.fixed} fixed (${result.duration}ms)`, 'success');
            } else if (typeof window.checkUndefinedStatus === 'function') {
                const count = window.checkUndefinedStatus();
                this.log(`✅ Global undefined check: ${count} undefined values found`, 'success');
            } else {
                // Manual scan
                const undefinedElements = Array.from(document.querySelectorAll('*')).filter(el => 
                    el.textContent && el.textContent.includes('undefined')
                );
                this.log(`✅ Manual scan: ${undefinedElements.length} elements with 'undefined' found`, 'success');
            }
        } catch (error) {
            this.log(`❌ Scan Error: ${error.message}`, 'error');
        }
    },
    
    // Get statistics
    getStats: function() {
        this.log('📊 Sammle Statistiken...', 'info');
        
        try {
            // Check if global functions are available
            const hasGlobalSafe = typeof window.safeDisplayValue === 'function';
            const hasDetection = typeof window.UndefinedDetection === 'object';
            const hasUndefinedFix = typeof window.checkUndefinedStatus === 'function';
            
            this.log(`🛡️ Global safeDisplayValue: ${hasGlobalSafe ? '✅' : '❌'}`, hasGlobalSafe ? 'success' : 'warn');
            this.log(`🔍 UndefinedDetection: ${hasDetection ? '✅' : '❌'}`, hasDetection ? 'success' : 'warn');
            this.log(`🔧 checkUndefinedStatus: ${hasUndefinedFix ? '✅' : '❌'}`, hasUndefinedFix ? 'success' : 'warn');
            
            // Get detailed stats if available
            if (window.getUndefinedStats && typeof window.getUndefinedStats === 'function') {
                const stats = window.getUndefinedStats();
                this.log(`📈 Detection Stats: ${stats.detectionCount} total detected, ${stats.fixedCount} total fixed`, 'success');
            }
            
            // Count current undefined elements
            const currentUndefined = Array.from(document.querySelectorAll('*')).filter(el => 
                el.textContent && el.textContent.includes('undefined')
            ).length;
            this.log(`📋 Current undefined elements: ${currentUndefined}`, currentUndefined === 0 ? 'success' : 'warn');
            
        } catch (error) {
            this.log(`❌ Stats Error: ${error.message}`, 'error');
        }
    },
    
    // Clear log
    clearLog: function() {
        this.logHistory = [];
        this.updateDebugOutput();
        this.log('🗑️ Log cleared', 'info');
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.DebugConsole.init();
    });
} else {
    window.DebugConsole.init();
}

console.log('✅ Debug Console Module geladen');