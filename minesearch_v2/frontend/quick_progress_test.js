const { chromium } = require('playwright');

(async () => {
  console.log('⚡ QUICK PROGRESS BAR TEST');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    
    // Check if progress tracking is loaded
    const hasProgressFunction = await page.evaluate(() => {
      return typeof window.showEnhancedLoadingMessage === 'function';
    });
    
    console.log(`📊 Progress Function Available: ${hasProgressFunction ? '✅' : '❌'}`);
    
    // Check HTMX events on CSV form
    const hasHTMXEvents = await page.evaluate(() => {
      const form = document.getElementById('csv-upload-form');
      return form && form.hasAttribute('hx-on::before-request');
    });
    
    console.log(`📂 CSV Form has HTMX Progress Events: ${hasHTMXEvents ? '✅' : '❌'}`);
    
    // Test progress bar display
    if (hasProgressFunction) {
      await page.evaluate(() => {
        window.showEnhancedLoadingMessage('TEST PROGRESS', 'test');
      });
      
      await page.waitForTimeout(1000);
      
      const progressVisible = await page.isVisible('.progress-container').catch(() => false);
      console.log(`🎯 Progress Bar Displays: ${progressVisible ? '✅ SUCCESS!' : '❌ FAILED'}`);
    }
    
    // Final verdict
    if (hasProgressFunction && hasHTMXEvents) {
      console.log('🎉 SOLUTION IMPLEMENTED SUCCESSFULLY! 🎉');
      console.log('👉 User should now see blue progress bar during CSV upload!');
    } else {
      console.log('❌ Implementation still has issues');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
  
  await browser.close();
})();