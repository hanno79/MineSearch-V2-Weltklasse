/**
 * Author: rahn
 * Datum: 18.08.2025  
 * Version: 1.0
 * Beschreibung: Browser-Console Test für Counter-Konsistenz
 * 
 * Dieses Script kann direkt in der Browser-Konsole ausgeführt werden
 * um die Model-Counter-Konsistenz zu testen.
 */

console.log('🧪 [COUNTER-TEST] Starting counter consistency test...');

// Function to test counter consistency
function testCounterConsistency() {
    console.log('📊 [COUNTER-TEST] Testing all counter selectors...');
    
    const results = {
        // Main counter selector (search.js) 
        main_model_counter: document.querySelectorAll('input[name="model"]:checked').length,
        
        // Header navigation counter (header-navigation.js - FIXED)
        header_counter: document.querySelectorAll('input[name="model"]:checked').length,
        
        // Progressive selection counter  
        progressive_counter: document.querySelectorAll('#model-selection input[type="checkbox"][name="model"]:checked').length,
        
        // Legacy counter (should be 0 now after cleanup)
        legacy_counter: document.querySelectorAll('input[name="models"]:checked').length,
        
        // All checkbox counter (generic)
        all_checkbox_counter: document.querySelectorAll('#model-selection input[type="checkbox"]:checked').length,
        
        // Total available models
        total_models: document.querySelectorAll('input[name="model"]').length,
        
        // Display counters from UI
        ui_selected_count: document.getElementById('selected-models-count')?.textContent || 'N/A',
        ui_status_models: document.getElementById('status-models')?.textContent || 'N/A'
    };
    
    console.log('📊 [COUNTER-TEST] Counter Results:');
    console.log(`   Main Model Counter: ${results.main_model_counter}`);
    console.log(`   Header Counter: ${results.header_counter}`);
    console.log(`   Progressive Counter: ${results.progressive_counter}`);
    console.log(`   Legacy Counter: ${results.legacy_counter} (should be 0)`);
    console.log(`   All Checkbox Counter: ${results.all_checkbox_counter}`);
    console.log(`   Total Available Models: ${results.total_models}`);
    console.log(`   UI Selected Count: ${results.ui_selected_count}`);
    console.log(`   UI Status Models: ${results.ui_status_models}`);
    
    // Verify consistency
    const main_count = results.main_model_counter;
    const header_count = results.header_counter;
    const progressive_count = results.progressive_counter;
    const all_checkbox_count = results.all_checkbox_counter;
    const legacy_count = results.legacy_counter;
    
    const consistency_check = (
        main_count === header_count &&
        header_count === progressive_count &&
        progressive_count === all_checkbox_count &&
        legacy_count === 0
    );
    
    if (consistency_check) {
        console.log(`✅ [COUNTER-TEST] CONSISTENCY SUCCESS: All counters show ${main_count} models`);
        console.log(`✅ [COUNTER-TEST] Legacy counter properly cleaned up: ${legacy_count} models`);
        
        // Check if we have the expected number of models (around 55)
        if (results.total_models >= 50 && results.total_models <= 60) {
            console.log(`✅ [COUNTER-TEST] Expected model count: ${results.total_models} models`);
        } else {
            console.warn(`⚠️ [COUNTER-TEST] Unexpected total model count: ${results.total_models}`);
        }
        
        return true;
    } else {
        console.error('❌ [COUNTER-TEST] CONSISTENCY FAILURE:');
        console.error(`   Main: ${main_count}, Header: ${header_count}, Progressive: ${progressive_count}`);
        console.error(`   All Checkbox: ${all_checkbox_count}, Legacy: ${legacy_count}`);
        return false;
    }
}

// Function to select all models and test
function selectAllAndTest() {
    console.log('🎯 [COUNTER-TEST] Selecting all models...');
    
    // Click "Alle" preset button
    const allButton = document.querySelector('.quick-pill.all');
    if (allButton) {
        allButton.click();
        console.log('✅ [COUNTER-TEST] "Alle" button clicked');
        
        // Wait a bit for selection to complete, then test
        setTimeout(() => {
            console.log('📊 [COUNTER-TEST] Testing after "Alle" selection...');
            const success = testCounterConsistency();
            
            if (success) {
                console.log('🎉 [COUNTER-TEST] ALL TESTS PASSED!');
            } else {
                console.error('❌ [COUNTER-TEST] TESTS FAILED!');
            }
        }, 2000);
    } else {
        console.error('❌ [COUNTER-TEST] "Alle" button not found');
        console.log('🔍 [COUNTER-TEST] Available quick buttons:');
        document.querySelectorAll('.quick-pill').forEach(btn => {
            console.log(`   - ${btn.textContent.trim()}`);
        });
    }
}

// Function to clear all and test
function clearAllAndTest() {
    console.log('🧹 [COUNTER-TEST] Clearing all selections...');
    
    // Clear all model checkboxes
    document.querySelectorAll('input[name="model"]:checked').forEach(cb => cb.checked = false);
    
    setTimeout(() => {
        console.log('📊 [COUNTER-TEST] Testing after clearing all...');
        const results = testCounterConsistency();
        
        // Check if all counters are 0
        const main_count = document.querySelectorAll('input[name="model"]:checked').length;
        if (main_count === 0) {
            console.log('✅ [COUNTER-TEST] Clear all successful: 0 models selected');
        } else {
            console.error(`❌ [COUNTER-TEST] Clear all failed: ${main_count} models still selected`);
        }
    }, 1000);
}

// Run the test automatically
console.log('🚀 [COUNTER-TEST] Starting automatic test sequence...');

// First test current state
console.log('📊 [COUNTER-TEST] Testing current state...');
testCounterConsistency();

// Then test after selecting all
setTimeout(() => {
    selectAllAndTest();
    
    // Finally test after clearing all
    setTimeout(() => {
        clearAllAndTest();
    }, 5000);
}, 2000);

console.log('ℹ️ [COUNTER-TEST] You can also run these functions manually:');
console.log('   - testCounterConsistency()');
console.log('   - selectAllAndTest()');
console.log('   - clearAllAndTest()');