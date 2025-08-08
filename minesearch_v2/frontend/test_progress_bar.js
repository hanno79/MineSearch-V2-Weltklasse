const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('🔍 Testing Progress Bar Implementation...');
  
  try {
    // Navigiere zur Hauptseite
    await page.goto('http://localhost:8000');
    await page.waitForTimeout(2000);
    
    console.log('✅ Page loaded successfully');
    
    // Prüfe ob progress-tracking.js geladen wurde
    const hasProgressTracker = await page.evaluate(() => {
      return typeof window.showEnhancedLoadingMessage === 'function';
    });
    
    console.log(`📊 Progress Tracker Function Available: ${hasProgressTracker ? '✅' : '❌'}`);
    
    // Prüfe CSV Upload Form
    const csvForm = await page.$('#csv-upload-form');
    if (csvForm) {
      console.log('✅ CSV Upload Form found');
      
      // Prüfe HTMX Events
      const hasHTMXEvents = await page.evaluate(() => {
        const form = document.getElementById('csv-upload-form');
        return form && form.hasAttribute('hx-on::before-request');
      });
      
      console.log(`📋 CSV Form has Progress Events: ${hasHTMXEvents ? '✅' : '❌'}`);
    }
    
    // Simulate CSV Upload (ohne echte Datei)
    console.log('🧪 Testing Progress Bar Visibility...');
    
    await page.evaluate(() => {
      if (typeof window.showEnhancedLoadingMessage === 'function') {
        window.showEnhancedLoadingMessage('Test Progress Bar', 'test');
        console.log('Progress bar should now be visible!');
      }
    });
    
    await page.waitForTimeout(3000);
    
    // Prüfe ob Progress Container sichtbar ist
    const progressVisible = await page.isVisible('.progress-container');
    console.log(`🎯 Progress Bar Visible: ${progressVisible ? '✅ SUCCESS!' : '❌ NOT VISIBLE'}`);
    
    if (progressVisible) {
      console.log('🎉 PROBLEM SOLVED! Progress Bar is now working!');
    } else {
      console.log('❌ Progress Bar still not visible - need further debugging');
    }
    
    // Screenshot für Verification
    await page.screenshot({ path: 'progress_bar_test.png', fullPage: true });
    console.log('📸 Screenshot saved as progress_bar_test.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
  
  await page.waitForTimeout(5000); // Zeit um visuell zu überprüfen
  await browser.close();
})();