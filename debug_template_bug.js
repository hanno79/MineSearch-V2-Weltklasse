/**
 * Debug Template Bug Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test warum cancelButtonHTML nicht im finalen Template landet
 */

const { chromium } = require('playwright');

async function debugTemplateBug() {
    console.log('🔍 [DEBUG] Testing template generation bug...');
    
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
        
        console.log('📍 [STEP 2] Step-by-step template debugging...');
        
        const result = await page.evaluate(() => {
            // Step-by-step debugging the template generation
            
            const title = 'Test Loading Message';
            const message = 'Test Description';
            const showSpinner = true;
            const showTimer = false;
            const showCancelButton = true;
            const cancelFunction = 'cancelSingleSearch()';
            
            console.log('🔧 [TEMPLATE-DEBUG] Starting step-by-step analysis...');
            
            // STEP 1: Generate spinner HTML
            const spinnerHTML = showSpinner ? `
        <div style="margin-top: 10px;">
            <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #0ea5e9; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
    ` : '';
            console.log('🔧 STEP 1 - spinnerHTML length:', spinnerHTML.length);
            
            // STEP 2: Generate timer HTML (should be empty)
            const timerHTML = '';
            console.log('🔧 STEP 2 - timerHTML length:', timerHTML.length);
            
            // STEP 3: Generate cancel button HTML
            const condition = showCancelButton && cancelFunction;
            console.log('🔧 STEP 3 - Cancel button condition:', condition);
            
            const cancelButtonHTML = condition ? `
        <div style="margin-top: 15px;">
            <button onclick="${cancelFunction}" 
                    style="
                        background: #ef4444; 
                        color: white; 
                        border: none; 
                        padding: 8px 16px; 
                        border-radius: 6px; 
                        cursor: pointer; 
                        font-size: 14px;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                    "
                    onmouseover="this.style.background='#dc2626'"
                    onmouseout="this.style.background='#ef4444'">
                🛑 Abbrechen
            </button>
        </div>
    ` : '';
            
            console.log('🔧 STEP 3 - cancelButtonHTML length:', cancelButtonHTML.length);
            console.log('🔧 STEP 3 - cancelButtonHTML includes Abbrechen:', cancelButtonHTML.includes('Abbrechen'));
            
            // STEP 4: Generate full template
            const fullTemplate = `
        <div style="padding: 20px; text-align: center; background: #f0f9ff; border-radius: 8px; border: 1px solid #0ea5e9;">
            <h3>${title}</h3>
            ${message ? `<p>${message}</p>` : ''}
            ${timerHTML}
            ${spinnerHTML}
            ${cancelButtonHTML}
        </div>
    `;
            
            console.log('🔧 STEP 4 - fullTemplate length:', fullTemplate.length);
            console.log('🔧 STEP 4 - fullTemplate includes cancelButtonHTML:', fullTemplate.includes(cancelButtonHTML.trim()));
            console.log('🔧 STEP 4 - fullTemplate includes Abbrechen:', fullTemplate.includes('Abbrechen'));
            
            // STEP 5: Compare with original function
            let originalResult = '';
            try {
                originalResult = createLoadingHTML(title, message, showSpinner, showTimer, showCancelButton, cancelFunction);
                console.log('🔧 STEP 5 - originalResult length:', originalResult.length);
                console.log('🔧 STEP 5 - originalResult includes Abbrechen:', originalResult.includes('Abbrechen'));
            } catch (error) {
                console.error('🔧 STEP 5 - Error calling createLoadingHTML:', error);
            }
            
            return {
                success: true,
                spinnerLength: spinnerHTML.length,
                cancelButtonLength: cancelButtonHTML.length,
                fullTemplateLength: fullTemplate.length,
                originalResultLength: originalResult.length,
                manualHasAbbrechen: fullTemplate.includes('Abbrechen'),
                originalHasAbbrechen: originalResult.includes('Abbrechen'),
                templatesMatch: fullTemplate.trim() === originalResult.trim(),
                cancelButtonHTML: cancelButtonHTML,
                fullTemplate: fullTemplate,
                originalResult: originalResult
            };
        });
        
        console.log('📊 [RESULT]');
        console.log('  Spinner HTML length:', result.spinnerLength);
        console.log('  Cancel button HTML length:', result.cancelButtonLength);
        console.log('  Full template length:', result.fullTemplateLength);
        console.log('  Original result length:', result.originalResultLength);
        console.log('  Manual template has Abbrechen:', result.manualHasAbbrechen);
        console.log('  Original result has Abbrechen:', result.originalHasAbbrechen);
        console.log('  Templates match:', result.templatesMatch);
        
        if (result.cancelButtonHTML) {
            console.log('\n📝 [CANCEL-BUTTON-HTML]:');
            console.log(result.cancelButtonHTML);
        }
        
        if (!result.originalHasAbbrechen && result.manualHasAbbrechen) {
            console.log('\n❌ [BUG CONFIRMED] Manual template works, original function does not!');
            console.log('\n📝 [ORIGINAL-RESULT]:');
            console.log(result.originalResult.substring(0, 600) + '...');
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

debugTemplateBug().catch(console.error);