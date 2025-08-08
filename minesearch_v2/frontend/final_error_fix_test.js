const { chromium } = require('playwright');

(async () => {
  console.log('🔧 FINAL ERROR FIX VERIFICATION TEST');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  
  try {
    console.log('🌐 Loading http://localhost:8000...');
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    
    // Check if functions exist
    const functionsExist = await page.evaluate(() => {
      return {
        showEnhancedLoadingMessage: typeof window.showEnhancedLoadingMessage === 'function',
        hideEnhancedLoadingMessage: typeof window.hideEnhancedLoadingMessage === 'function',
        progressTracker: !!window.progressTracker
      };
    });
    
    console.log('📊 Function Availability:');
    console.log(`  showEnhancedLoadingMessage: ${functionsExist.showEnhancedLoadingMessage ? '✅' : '❌'}`);
    console.log(`  hideEnhancedLoadingMessage: ${functionsExist.hideEnhancedLoadingMessage ? '✅' : '❌'}`);
    console.log(`  progressTracker: ${functionsExist.progressTracker ? '✅' : '❌'}`);
    
    // Test function calls (without triggering HTMX)
    console.log('🧪 Testing Function Calls...');
    await page.evaluate(() => {
      try {
        // Test with correct parameters
        const testDiv = document.createElement('div');
        testDiv.id = 'test-progress';
        document.body.appendChild(testDiv);
        
        window.showEnhancedLoadingMessage(testDiv, 'Test Title', 'Test Message');
        console.log('✅ showEnhancedLoadingMessage works');
        
        window.hideEnhancedLoadingMessage(testDiv);
        console.log('✅ hideEnhancedLoadingMessage works');
        
        testDiv.remove();
      } catch (error) {
        console.error('❌ Function test failed:', error);
      }
    });
    
    await page.waitForTimeout(2000);
    
    // Check for HTMX form attributes
    const htmxEvents = await page.evaluate(() => {
      const csvForm = document.getElementById('csv-upload-form');
      return {
        csvFormExists: !!csvForm,
        hasBeforeRequest: csvForm && csvForm.hasAttribute('hx-on::before-request'),
        hasAfterRequest: csvForm && csvForm.hasAttribute('hx-on::after-request'),
        beforeRequestValue: csvForm ? csvForm.getAttribute('hx-on::before-request') : null
      };
    });
    
    console.log('📋 HTMX Event Integration:');
    console.log(`  CSV Form exists: ${htmxEvents.csvFormExists ? '✅' : '❌'}`);
    console.log(`  Has before-request: ${htmxEvents.hasBeforeRequest ? '✅' : '❌'}`);
    console.log(`  Has after-request: ${htmxEvents.hasAfterRequest ? '✅' : '❌'}`);
    
    if (htmxEvents.beforeRequestValue) {
      const hasCorrectParams = htmxEvents.beforeRequestValue.includes('document.getElementById');
      console.log(`  Correct Parameters: ${hasCorrectParams ? '✅' : '❌'}`);
    }
    
    // Check for console errors
    console.log(`\\n🔍 Console Errors Found: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      consoleErrors.forEach((error, i) => {
        console.log(`  ${i+1}. ${error}`);
      });
    }
    
    // Final verdict
    const allGood = functionsExist.showEnhancedLoadingMessage && 
                   functionsExist.hideEnhancedLoadingMessage &&
                   htmxEvents.hasBeforeRequest &&
                   htmxEvents.hasAfterRequest &&
                   consoleErrors.length === 0;
    
    console.log(`\\n🎯 FINAL VERDICT: ${allGood ? '🎉 ALL FIXES SUCCESSFUL!' : '❌ Still has issues'}`);
    
    if (allGood) {
      console.log('\\n✅ User should now see:');
      console.log('  - No JavaScript errors in console');
      console.log('  - Blue progress bar during CSV upload');
      console.log('  - Progress bar disappears when done');
      console.log('  - Batch search works after CSV upload');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
  
  await browser.close();
})();