/**
 * Debug Cancel Parameters Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test der Parameter-Übergabe an createLoadingHTML
 */

const { chromium } = require('playwright');

async function debugCancelParameters() {
    console.log('🔍 [DEBUG] Testing parameter passing to createLoadingHTML...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs
    page.on('console', msg => {
        console.log('🖥️ [PAGE-CONSOLE]', msg.text());
    });
    
    try {
        console.log('📍 [STEP 1] Load page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('📍 [STEP 2] Test parameter values in createLoadingHTML...');
        
        const result = await page.evaluate(() => {
            // Override createLoadingHTML to log parameters
            const originalCreateLoadingHTML = createLoadingHTML;
            
            window.createLoadingHTML = function(title, message = '', showSpinner = true, showTimer = false, showCancelButton = false, cancelFunction = '') {
                console.log('📊 [DEBUG] createLoadingHTML called with:');
                console.log('  title:', title);
                console.log('  message:', message);
                console.log('  showSpinner:', showSpinner, '(type:', typeof showSpinner, ')');
                console.log('  showTimer:', showTimer, '(type:', typeof showTimer, ')');
                console.log('  showCancelButton:', showCancelButton, '(type:', typeof showCancelButton, ')');
                console.log('  cancelFunction:', cancelFunction, '(type:', typeof cancelFunction, ')');
                
                // Test the condition
                const condition = showCancelButton && cancelFunction;
                console.log('  Condition (showCancelButton && cancelFunction):', condition);
                
                if (condition) {
                    console.log('  ✅ Cancel button should be created');
                } else {
                    console.log('  ❌ Cancel button will NOT be created');
                    if (!showCancelButton) {
                        console.log('    Reason: showCancelButton is falsy');
                    }
                    if (!cancelFunction) {
                        console.log('    Reason: cancelFunction is falsy');
                    }
                }
                
                return originalCreateLoadingHTML.call(this, title, message, showSpinner, showTimer, showCancelButton, cancelFunction);
            };
            
            // Now test the function call
            console.log('🧪 [TEST] Calling createLoadingHTML with cancel button...');
            const result = createLoadingHTML(
                'Test Loading Message',
                'Test Description',
                true, // showSpinner
                false, // showTimer  
                true, // showCancelButton
                'cancelSingleSearch()' // cancelFunction
            );
            
            return {
                success: true,
                htmlLength: result.length,
                includesCancel: result.includes('cancelSingleSearch'),
                includesAbbrechen: result.includes('Abbrechen'),
                htmlPreview: result.substring(0, 600)
            };
        });
        
        console.log('📊 [RESULT]', JSON.stringify(result, null, 2));
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

debugCancelParameters().catch(console.error);