const { chromium } = require('playwright');

async function checkTabs() {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Check all tab elements
    const allTabs = await page.$$('input[type="radio"][name="tab"]');
    console.log(`Found ${allTabs.length} tab radio buttons:`);
    
    for (let i = 0; i < allTabs.length; i++) {
        const tab = allTabs[i];
        const id = await tab.getAttribute('id');
        const value = await tab.getAttribute('value');
        const visible = await tab.isVisible();
        const enabled = await tab.isEnabled();
        
        console.log(`  Tab ${i+1}: #${id} (value: ${value}) - Visible: ${visible}, Enabled: ${enabled}`);
    }
    
    // Check tab labels
    const tabLabels = await page.$$('label[for*="tab"]');
    console.log(`\nFound ${tabLabels.length} tab labels:`);
    
    for (let i = 0; i < tabLabels.length; i++) {
        const label = tabLabels[i];
        const forAttr = await label.getAttribute('for');
        const text = await label.textContent();
        const visible = await label.isVisible();
        
        console.log(`  Label ${i+1}: for="${forAttr}" - Text: "${text}" - Visible: ${visible}`);
    }
    
    // Try clicking on labels instead
    console.log('\nTrying to click CSV tab label...');
    try {
        const csvLabel = await page.$('label[for="csv-tab"]');
        if (csvLabel) {
            await csvLabel.click();
            console.log('✅ CSV tab label clicked successfully');
            await page.waitForTimeout(2000);
            
            // Check if CSV section is now visible
            const csvSection = await page.$('#csv-upload');
            if (csvSection) {
                const visible = await csvSection.isVisible();
                console.log(`CSV section visible: ${visible}`);
            }
        }
    } catch (error) {
        console.log('❌ Error clicking CSV label:', error.message);
    }
    
    await page.screenshot({ path: 'tab_structure_check.png' });
    await browser.close();
}

checkTabs().catch(console.error);