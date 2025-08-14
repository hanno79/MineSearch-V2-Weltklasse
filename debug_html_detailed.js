/**
 * Debug HTML Detailed Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Detaillierte HTML-Analyse des Cancel-Button Problems
 */

const { chromium } = require('playwright');

async function debugHTMLDetailed() {
    console.log('🔍 [DEBUG] Detailed HTML analysis of cancel button...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        console.log('📍 [STEP 1] Load page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('📍 [STEP 2] Generate HTML with detailed debugging...');
        
        const result = await page.evaluate(() => {
            // Test the createLoadingHTML function with detailed logging
            const title = 'Test Loading Message';
            const message = 'Test Description';
            const showSpinner = true;
            const showTimer = false; 
            const showCancelButton = true;
            const cancelFunction = 'cancelSingleSearch()';
            
            console.log('🔧 [DEBUG] Input parameters:');
            console.log('  showCancelButton:', showCancelButton);
            console.log('  cancelFunction:', cancelFunction);
            
            // Manually create the cancelButtonHTML to debug
            const condition = showCancelButton && cancelFunction;
            console.log('  Condition result:', condition, '(type:', typeof condition, ')');
            
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
            
            console.log('🔧 [DEBUG] Cancel button HTML generated:');
            console.log('  Length:', cancelButtonHTML.length);
            console.log('  Content preview:', cancelButtonHTML.substring(0, 100));
            console.log('  Includes "Abbrechen":', cancelButtonHTML.includes('Abbrechen'));
            console.log('  Includes onclick:', cancelButtonHTML.includes('onclick'));
            
            // Now create the full HTML
            const fullHTML = `
        <div style="padding: 20px; text-align: center; background: #f0f9ff; border-radius: 8px; border: 1px solid #0ea5e9;">
            <h3>${title}</h3>
            ${message ? `<p>${message}</p>` : ''}
            ${showSpinner ? `
        <div style="margin-top: 10px;">
            <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #0ea5e9; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
    ` : ''}
            ${cancelButtonHTML}
        </div>
    `;
            
            console.log('🔧 [DEBUG] Full HTML generated:');
            console.log('  Total length:', fullHTML.length);
            console.log('  Includes cancel button HTML:', fullHTML.includes(cancelButtonHTML));
            console.log('  Includes "Abbrechen":', fullHTML.includes('Abbrechen'));
            
            return {
                success: true,
                cancelButtonLength: cancelButtonHTML.length,
                cancelButtonHTML: cancelButtonHTML,
                fullHTMLLength: fullHTML.length,
                fullHTML: fullHTML,
                includesAbbrechen: fullHTML.includes('Abbrechen'),
                includesOnclick: fullHTML.includes('onclick="cancelSingleSearch()"')
            };
        });
        
        console.log('📊 [RESULT] Manual HTML generation test:');
        console.log('  Cancel button HTML length:', result.cancelButtonLength);
        console.log('  Full HTML includes "Abbrechen":', result.includesAbbrechen);
        console.log('  Full HTML includes onclick:', result.includesOnclick);
        
        if (result.cancelButtonHTML) {
            console.log('\n📝 [CANCEL-BUTTON-HTML]:');
            console.log(result.cancelButtonHTML);
        }
        
        console.log('\n📍 [STEP 3] Test original createLoadingHTML function...');
        
        const originalResult = await page.evaluate(() => {
            const html = createLoadingHTML(
                'Test Loading Message',
                'Test Description',
                true, // showSpinner
                false, // showTimer  
                true, // showCancelButton
                'cancelSingleSearch()' // cancelFunction
            );
            
            return {
                html: html,
                length: html.length,
                includesAbbrechen: html.includes('Abbrechen'),
                includesOnclick: html.includes('onclick="cancelSingleSearch()"')
            };
        });
        
        console.log('📊 [ORIGINAL-FUNCTION] Result:');
        console.log('  HTML length:', originalResult.length);
        console.log('  Includes "Abbrechen":', originalResult.includesAbbrechen);
        console.log('  Includes onclick:', originalResult.includesOnclick);
        
        if (!originalResult.includesAbbrechen) {
            console.log('\n❌ [BUG CONFIRMED] Original function does NOT generate cancel button!');
            console.log('📝 [ORIGINAL-HTML]:');
            console.log(originalResult.html.substring(0, 500) + '...');
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

debugHTMLDetailed().catch(console.error);