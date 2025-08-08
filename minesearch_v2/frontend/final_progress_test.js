const { chromium } = require('playwright');

(async () => {
  console.log('🎯 FINAL PROGRESS BAR TEST');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000  // Slow down for visual verification
  });
  
  const page = await browser.newPage();
  
  try {
    console.log('📂 Navigating to http://localhost:8000...');
    await page.goto('http://localhost:8000');
    await page.waitForTimeout(3000);
    
    // Test 1: Manual Progress Bar Trigger
    console.log('🧪 Test 1: Manual Progress Bar Trigger');
    await page.evaluate(() => {
      if (typeof window.showEnhancedLoadingMessage === 'function') {
        console.log('✅ showEnhancedLoadingMessage function found!');
        window.showEnhancedLoadingMessage('🎉 TEST PROGRESS BAR AKTIV!', 'test');
      } else {
        console.error('❌ showEnhancedLoadingMessage function NOT found!');
      }
    });
    
    await page.waitForTimeout(3000);
    
    // Check if progress bar is visible
    const progressVisible = await page.isVisible('.progress-container').catch(() => false);
    console.log(`🎯 Manual Progress Bar Visible: ${progressVisible ? '✅ YES!' : '❌ NO'}`);
    
    // Test 2: CSV Upload Form Check
    console.log('🧪 Test 2: CSV Upload Form HTMX Events');
    const hasHTMXEvents = await page.evaluate(() => {
      const form = document.getElementById('csv-upload-form');
      return form && form.hasAttribute('hx-on::before-request');
    });
    console.log(`📂 CSV Form has Progress Events: ${hasHTMXEvents ? '✅ YES!' : '❌ NO'}`);
    
    // Screenshot
    await page.screenshot({ 
      path: '/app/minesearch_v2/frontend/FINAL_PROGRESS_TEST.png', 
      fullPage: true 
    });
    console.log('📸 Screenshot saved: FINAL_PROGRESS_TEST.png');
    
    if (progressVisible && hasHTMXEvents) {
      console.log('🎉🎉🎉 SUCCESS! PROGRESS BAR IS WORKING! 🎉🎉🎉');
    } else {
      console.log('❌ Still issues with progress bar implementation');
    }
    
  } catch (error) {
    console.error('❌ Test error:', error);
  }
  
  await page.waitForTimeout(5000);
  await browser.close();
  console.log('✅ Test completed');
})();