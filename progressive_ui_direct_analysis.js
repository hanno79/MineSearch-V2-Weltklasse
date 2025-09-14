/**
 * DIRECT UI ANALYSIS - Progressive Model Selection
 * Direkte Browser-Console Tests ohne Playwright
 * Tests Progressive Model Selection UI nach API Response Format Fix
 */

console.log('🧪 [UI-ANALYSIS] Starting direct Progressive Model Selection analysis...');

// Test 1: Check if Progressive Model Selection UI is properly initialized
setTimeout(() => {
    console.log('\\n🎯 [UI-ANALYSIS] TEST 1: Progressive Model Selection Initialization');
    
    const modelSelectionContainer = document.getElementById('model-selection');
    if (modelSelectionContainer) {
        console.log('✅ [UI-ANALYSIS] Model selection container found');
        
        const progressiveContainer = modelSelectionContainer.querySelector('.model-selection-enhanced');
        if (progressiveContainer) {
            console.log('✅ [UI-ANALYSIS] Progressive Model Selection container found');
            
            // Count Quick Selection Pills
            const quickPills = progressiveContainer.querySelectorAll('.quick-model-pill');
            console.log(`📊 [UI-ANALYSIS] Found ${quickPills.length} quick selection pills`);
            
            quickPills.forEach((pill, index) => {
                const pillText = pill.textContent.trim();
                console.log(`🔸 [UI-ANALYSIS] Pill ${index + 1}: "${pillText}"`);
            });
            
        } else {
            console.log('❌ [UI-ANALYSIS] Progressive Model Selection container NOT found!');
        }
    } else {
        console.log('❌ [UI-ANALYSIS] Model selection container NOT found!');
    }
}, 2000);

// Test 2: Check Model Loading Status
setTimeout(() => {
    console.log('\\n🎯 [UI-ANALYSIS] TEST 2: Model Loading Status');
    
    if (window.progressiveModelSelection) {
        const pms = window.progressiveModelSelection;
        console.log(`📊 [UI-ANALYSIS] Models loaded: ${pms.models ? pms.models.length : 'unknown'}`);
        console.log(`📊 [UI-ANALYSIS] Providers: ${pms.providers ? pms.providers.size : 'unknown'}`);
        console.log(`📊 [UI-ANALYSIS] Selected models: ${pms.selectedModels ? pms.selectedModels.size : 'unknown'}`);
    } else {
        console.log('⚠️ [UI-ANALYSIS] Progressive Model Selection instance not found in window object');
    }
}, 3000);

// Test 3: Interactive Tests - Provider Pills
setTimeout(() => {
    console.log('\\n🎯 [UI-ANALYSIS] TEST 3: Testing Quick Selection Pills Interactivity');
    
    const quickPills = document.querySelectorAll('.quick-model-pill');
    if (quickPills.length > 0) {
        // Simulate click on first pill
        const firstPill = quickPills[0];
        console.log(`🔸 [UI-ANALYSIS] Testing pill: "${firstPill.textContent.trim()}"`);
        
        // Add click event listener to monitor
        firstPill.addEventListener('click', () => {
            console.log('🎯 [UI-ANALYSIS] Quick Selection Pill clicked successfully!');
            
            // Check if models were selected
            setTimeout(() => {
                const checkedBoxes = document.querySelectorAll('#model-selection input[type="checkbox"]:checked');
                console.log(`📊 [UI-ANALYSIS] Models selected after pill click: ${checkedBoxes.length}`);
            }, 500);
        });
        
        // Trigger click
        firstPill.click();
        
    } else {
        console.log('❌ [UI-ANALYSIS] No Quick Selection Pills found for interactive testing');
    }
}, 4000);

// Test 4: Advanced Mode Toggle
setTimeout(() => {
    console.log('\\n🎯 [UI-ANALYSIS] TEST 4: Testing Advanced Mode Toggle');
    
    const advancedToggle = document.querySelector('.advanced-toggle-btn');
    if (advancedToggle) {
        console.log('✅ [UI-ANALYSIS] Advanced toggle button found');
        
        // Add click listener
        advancedToggle.addEventListener('click', () => {
            console.log('🎯 [UI-ANALYSIS] Advanced toggle clicked!');
            
            setTimeout(() => {
                const advancedBrowser = document.querySelector('.advanced-model-browser');
                if (advancedBrowser) {
                    const isVisible = advancedBrowser.offsetParent !== null;
                    console.log(`📊 [UI-ANALYSIS] Advanced Model Browser visible: ${isVisible}`);
                    
                    if (isVisible) {
                        const providerTabs = advancedBrowser.querySelectorAll('.provider-tab');
                        console.log(`📊 [UI-ANALYSIS] Provider tabs in advanced mode: ${providerTabs.length}`);
                        
                        const modelCards = advancedBrowser.querySelectorAll('.model-card');
                        console.log(`📊 [UI-ANALYSIS] Model cards in advanced mode: ${modelCards.length}`);
                    }
                }
            }, 500);
        });
        
        // Trigger click
        advancedToggle.click();
        
    } else {
        console.log('❌ [UI-ANALYSIS] Advanced toggle button NOT found');
    }
}, 5000);

// Test 5: Final Status Report
setTimeout(() => {
    console.log('\\n🎯 [UI-ANALYSIS] TEST 5: Final Status Report');
    
    // Count all model checkboxes
    const allCheckboxes = document.querySelectorAll('#model-selection input[type="checkbox"]');
    const checkedCheckboxes = document.querySelectorAll('#model-selection input[type="checkbox"]:checked');
    
    console.log(`📊 [UI-ANALYSIS] Total model checkboxes: ${allCheckboxes.length}`);
    console.log(`📊 [UI-ANALYSIS] Currently selected: ${checkedCheckboxes.length}`);
    
    // Check selection summary
    const selectionSummary = document.querySelector('.selection-summary');
    if (selectionSummary) {
        const summaryText = selectionSummary.textContent.trim();
        console.log(`📊 [UI-ANALYSIS] Selection summary text: "${summaryText}"`);
    }
    
    // Check for UI conflicts
    const legacyCheckboxes = document.querySelector('#legacy-checkboxes');
    if (legacyCheckboxes) {
        const isHidden = legacyCheckboxes.offsetParent === null;
        console.log(`📊 [UI-ANALYSIS] Legacy checkboxes properly hidden: ${isHidden}`);
    }
    
    console.log('\\n🎉 [UI-ANALYSIS] DIRECT UI ANALYSIS COMPLETE');
    console.log('✅ [UI-ANALYSIS] Progressive Model Selection UI fully analyzed');
    
}, 6000);