const { test, expect } = require('@playwright/test');

test('Tab Navigation Test', async ({ page }) => {
  console.log('🧪 Starting tab navigation test...');
  
  try {
    await page.goto('http://localhost:8000');
    
    // Wait for page load
    await page.waitForTimeout(3000);
    
    console.log('📋 Page loaded, testing tab navigation...');
    
    // Test Statistics Tab
    console.log('📈 Testing Statistics tab...');
    await page.click('#statistics-tab');
    await page.waitForTimeout(1000);
    
    const statsContainer = await page.$('#model-statistics-table-container');
    console.log('Statistics container found:', !!statsContainer);
    
    // Test Sources Tab  
    console.log('📚 Testing Sources tab...');
    await page.click('#sources-tab');
    await page.waitForTimeout(1000);
    
    const sourcesContainer = await page.$('#sources-container');
    console.log('Sources container found:', !!sourcesContainer);
    
    // Test CSV Tab
    console.log('📊 Testing CSV tab...');
    await page.click('#csv-tab');
    await page.waitForTimeout(1000);
    
    const csvForm = await page.$('#csv-form');
    console.log('CSV form found:', !!csvForm);
    
    // Test Consolidated Tab
    console.log('📋 Testing Consolidated tab...');
    await page.click('#consolidated-tab');
    await page.waitForTimeout(1000);
    
    const consolidatedStats = await page.$('#consolidated-stats');
    console.log('Consolidated stats found:', !!consolidatedStats);
    
    // Back to Single tab
    console.log('🔍 Testing Single tab...');
    await page.click('#single-tab');
    await page.waitForTimeout(1000);
    
    const singleForm = await page.$('#search-form');
    console.log('Single search form found:', !!singleForm);
    
    console.log('✅ Tab navigation test completed successfully');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  }
});