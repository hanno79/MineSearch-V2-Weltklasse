const { chromium } = require('playwright');

async function directTest() {
    const browser = await chromium.launch({headless: false});
    const page = await browser.newPage();
    
    page.on('console', msg => console.log('🖥️ [PAGE]', msg.text()));
    
    await page.goto('file:///app/direct_displayResults_test.html');
    await page.waitForTimeout(5000);
    
    const content = await page.$eval('#results', el => el.innerHTML);
    console.log('📊 [RESULT]', content.substring(0, 200));
    
    await browser.close();
}

directTest().catch(console.error);