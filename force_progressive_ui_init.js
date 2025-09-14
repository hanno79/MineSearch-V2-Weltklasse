/**
 * FORCE PROGRESSIVE MODEL SELECTION UI INITIALIZATION
 * Debug script to manually trigger Progressive Model Selection UI
 */

console.log('🔧 [FORCE-INIT] Manual Progressive Model Selection initialization...');

// Wait for DOM to be fully loaded
function forceProgressiveModelSelection() {
    console.log('🎯 [FORCE-INIT] Starting forced initialization...');
    
    // Check if Progressive Model Selection class exists
    if (typeof ProgressiveModelSelection !== 'undefined') {
        console.log('✅ [FORCE-INIT] ProgressiveModelSelection class found');
        
        // Create instance manually
        try {
            window.progressiveModelSelection = new ProgressiveModelSelection();
            console.log('✅ [FORCE-INIT] Progressive Model Selection instance created');
        } catch (error) {
            console.error('❌ [FORCE-INIT] Failed to create instance:', error);
        }
    } else {
        console.log('❌ [FORCE-INIT] ProgressiveModelSelection class NOT found');
        console.log('🔍 [FORCE-INIT] Available global objects:', Object.keys(window));
    }
    
    // Check DOM elements
    const modelSelection = document.getElementById('model-selection');
    if (modelSelection) {
        console.log('✅ [FORCE-INIT] Model selection container found');
        console.log('📊 [FORCE-INIT] Container HTML length:', modelSelection.innerHTML.length);
        
        // Check for existing Progressive UI
        const progressiveContainer = modelSelection.querySelector('.model-selection-enhanced');
        if (progressiveContainer) {
            console.log('✅ [FORCE-INIT] Progressive Model Selection container already exists');
        } else {
            console.log('❌ [FORCE-INIT] Progressive Model Selection container missing - UI not initialized');
            
            // Force creation of Progressive UI
            console.log('🔧 [FORCE-INIT] Attempting to force create Progressive UI...');
            
            if (window.progressiveModelSelection && window.progressiveModelSelection.renderQuickSelection) {
                window.progressiveModelSelection.renderQuickSelection();
                console.log('✅ [FORCE-INIT] Progressive UI manually triggered');
            }
        }
    } else {
        console.log('❌ [FORCE-INIT] Model selection container NOT found');
    }
    
    // Test API directly
    console.log('🧪 [FORCE-INIT] Testing API directly...');
    fetch('/api/models')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.models) {
                const modelCount = Object.keys(data.models).length;
                const providers = new Set(Object.keys(data.models).map(id => id.split(':')[0]));
                console.log(`✅ [FORCE-INIT] API works: ${modelCount} models from ${providers.size} providers`);
                console.log(`🏷️ [FORCE-INIT] Providers: ${Array.from(providers).join(', ')}`);
            } else {
                console.log('❌ [FORCE-INIT] API response invalid');
            }
        })
        .catch(error => {
            console.error('❌ [FORCE-INIT] API test failed:', error);
        });
}

// Execute immediately and after DOM load
forceProgressiveModelSelection();

// Also try after a delay
setTimeout(forceProgressiveModelSelection, 2000);
setTimeout(forceProgressiveModelSelection, 5000);

console.log('🔧 [FORCE-INIT] Force initialization script loaded');