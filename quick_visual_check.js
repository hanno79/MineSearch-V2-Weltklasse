/**
 * Quick Visual Check - See what's actually on screen
 */

const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        await page.goto('http://localhost:8000');
        await page.waitForTimeout(5000);
        
        // Take screenshot to see current state
        await page.screenshot({ path: 'current_model_selection_state.png', fullPage: true });
        
        // Check model selection HTML content
        const modelSelectionHTML = await page.innerHTML('#model-selection');
        console.log('Model Selection HTML:');
        console.log(modelSelectionHTML.substring(0, 1000) + '...');
        
        // Check if checkboxes exist and are visible
        const allCheckboxes = await page.$$('input[type="checkbox"]');
        console.log(`\nTotal checkboxes found: ${allCheckboxes.length}`);
        
        for (let i = 0; i < Math.min(5, allCheckboxes.length); i++) {
            const checkbox = allCheckboxes[i];
            const isVisible = await checkbox.isVisible();
            const id = await checkbox.getAttribute('id');
            const value = await checkbox.getAttribute('value');
            console.log(`Checkbox ${i + 1}: id="${id}" value="${value}" visible=${isVisible}`);
        }
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
})();