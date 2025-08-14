/**
 * Debug Cancel Button Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Direct test der showLoadingMessage Funktion mit Cancel-Button
 */

const { chromium } = require('playwright');

async function debugCancelButton() {
    console.log('🔍 [DEBUG] Testing showLoadingMessage function directly...');
    
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
        
        console.log('📍 [STEP 2] Test showLoadingMessage function directly...');
        
        // Test the function directly in browser console
        const result = await page.evaluate(() => {
            const resultsDiv = document.getElementById('results');
            if (!resultsDiv) {
                return { error: 'Results div not found' };
            }
            
            console.log('Testing showLoadingMessage with cancel button...');
            
            // Test createLoadingHTML directly first
            if (typeof createLoadingHTML === 'function') {
                const htmlWithCancel = createLoadingHTML(
                    'Test Message', 
                    'Test Description', 
                    true, // showSpinner
                    false, // showTimer
                    true, // showCancelButton
                    'cancelSingleSearch()' // cancelFunction
                );
                
                console.log('createLoadingHTML result:', htmlWithCancel);
                
                // Check if cancel button HTML is included
                const hasCancelButton = htmlWithCancel.includes('cancelSingleSearch()');
                const hasAbbruchButton = htmlWithCancel.includes('Abbrechen');
                
                return {
                    success: true,
                    htmlLength: htmlWithCancel.length,
                    hasCancelButton,
                    hasAbbruchButton,
                    htmlPreview: htmlWithCancel.substring(0, 500)
                };
            } else {
                return { error: 'createLoadingHTML function not found' };
            }
        });
        
        console.log('📊 [RESULT]', JSON.stringify(result, null, 2));
        
        if (result.success) {
            console.log('📍 [STEP 3] Apply the HTML to results div...');
            
            await page.evaluate(() => {
                const resultsDiv = document.getElementById('results');
                if (typeof showLoadingMessage === 'function') {
                    showLoadingMessage(
                        resultsDiv,
                        'Test Search läuft...',
                        'Mine: Test Mine | Land: Test Country',
                        true, // startTimer
                        true, // showCancelButton
                        'cancelSingleSearch()' // cancelFunction
                    );
                    console.log('showLoadingMessage called successfully');
                } else {
                    console.error('showLoadingMessage function not found');
                }
            });
            
            await page.waitForTimeout(2000);
            
            // Take screenshot of results
            await page.screenshot({ path: 'debug_cancel_button_test.png', fullPage: true });
            
            // Check if cancel button exists in DOM
            const cancelButtonExists = await page.$('button[onclick="cancelSingleSearch()"]');
            console.log(`📍 [STEP 4] Cancel button exists in DOM: ${cancelButtonExists ? 'YES' : 'NO'}`);
            
            if (cancelButtonExists) {
                const isVisible = await cancelButtonExists.isVisible();
                console.log(`📍 [STEP 4] Cancel button visible: ${isVisible}`);
            }
            
            // Get final HTML content
            const finalHTML = await page.evaluate(() => {
                const resultsDiv = document.getElementById('results');
                return resultsDiv ? resultsDiv.innerHTML : 'Results div not found';
            });
            
            console.log('📍 [STEP 5] Final HTML preview:');
            console.log(finalHTML.substring(0, 300) + '...');
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

debugCancelButton().catch(console.error);