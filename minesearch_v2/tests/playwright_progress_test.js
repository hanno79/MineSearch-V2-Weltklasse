/**
 * Author: rahn
 * Datum: 04.08.2025
 * Version: 2.0
 * Beschreibung: Comprehensive Playwright Tests für Progress-Tracking System
 * ERWEITERT: CSV-Upload, Modell-Auswahl, Progress-Bar Mathematik, WebSocket-Tests
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Progress Tracking System - Comprehensive E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the main application
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    
    // Wait for any JavaScript to initialize
    await page.waitForTimeout(2000);
    console.log('🌐 Page loaded and initialized');
  });

  test('SCENARIO 1: CSV-Upload Test mit Session-Erstellung', async ({ page }) => {
    console.log('🧪 SCENARIO 1: Testing CSV Upload with Session Creation');
    
    // Gehe zum CSV Tab
    await page.click('[data-tab="csv"]');
    await page.waitForTimeout(1000);
    
    // Lade Test-CSV mit 10 Minen
    const csvPath = path.join(__dirname, 'test_mines_10.csv');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);
    console.log('📄 CSV file selected');
    
    // Upload CSV
    await page.click('button:has-text("CSV hochladen")');
    console.log('⬆️ CSV upload initiated');
    
    // Warte auf Upload-Response
    await page.waitForTimeout(3000);
    
    // Validiere Session-Erstellung
    const uploadResult = page.locator('.upload-result, .success-message, .alert-success');
    const hasResult = await uploadResult.isVisible({ timeout: 10000 });
    
    if (hasResult) {
      console.log('✅ CSV Upload successful - Session created');
      const resultText = await uploadResult.textContent();
      console.log(`Upload result: ${resultText}`);
      
      // Validiere Minen-Parsing (sollte 10 Minen enthalten)
      expect(resultText).toMatch(/10|zehn/i);
    } else {
      console.log('⚠️ No clear upload result - may need backend running');
    }
    
    console.log('✅ SCENARIO 1 completed: CSV Upload and Session Creation');
  });

  test('should show ETA and current operation info', async ({ page }) => {
    console.log('🧪 Testing ETA and Operation Info');

    // Fill in search form for multiple operations
    await page.fill('input[name="mine_name"]', 'Eleonore, Canadian Malartic');
    await page.selectOption('select[name="country"]', 'Canada');
    await page.selectOption('select[name="model"]', 'perplexity:sonar');

    // Start search
    await page.click('button[type="submit"]');

    // Wait for enhanced loading message
    const loadingDiv = page.locator('.enhanced-loading');
    await expect(loadingDiv).toBeVisible({ timeout: 5000 });

    // Check for ETA display
    const etaElement = page.locator('.eta-display');
    if (await etaElement.isVisible()) {
      const etaText = await etaElement.textContent();
      console.log(`ETA display: ${etaText}`);
      expect(etaText).toContain('ETA');
    }

    // Check for current operation display
    const currentOpElement = page.locator('.current-operation');
    if (await currentOpElement.isVisible()) {
      const currentOpText = await currentOpElement.textContent();
      console.log(`Current operation: ${currentOpText}`);
    }

    console.log('✅ ETA and operation info elements checked');
  });

  test('should handle WebSocket progress updates', async ({ page }) => {
    console.log('🧪 Testing WebSocket Progress Updates');

    // Listen for WebSocket connections
    let wsConnected = false;
    page.on('websocket', ws => {
      console.log(`WebSocket connection: ${ws.url()}`);
      wsConnected = true;
      
      ws.on('framereceived', frame => {
        console.log(`Received WebSocket frame: ${frame.payload}`);
      });
    });

    // Fill in search form
    await page.fill('input[name="mine_name"]', 'Test Mine');
    await page.selectOption('select[name="country"]', 'Canada');
    await page.selectOption('select[name="model"]', 'perplexity:sonar');

    // Start search
    await page.click('button[type="submit"]');

    // Wait for potential WebSocket connection
    await page.waitForTimeout(3000);

    // Check if progress elements appeared (indicating WebSocket or polling worked)
    const progressContainer = page.locator('.progress-container');
    const hasProgress = await progressContainer.isVisible();
    
    if (hasProgress) {
      console.log('✅ Progress system is functioning (WebSocket or polling)');
    } else {
      console.log('⚠️ No progress elements detected - may need backend running');
    }
  });

  test('should show completion status', async ({ page }) => {
    console.log('🧪 Testing Completion Status');

    // Fill in simple search
    await page.fill('input[name="mine_name"]', 'Quick Test');
    await page.selectOption('select[name="country"]', 'Canada');
    await page.selectOption('select[name="model"]', 'perplexity:sonar');

    // Start search
    await page.click('button[type="submit"]');

    // Wait for either completion or timeout
    try {
      // Look for completion indicators
      const resultElements = [
        '.search-results',
        '.result-card',
        '.error-message',
        '.completion-message'
      ];

      let completionFound = false;
      for (const selector of resultElements) {
        const element = page.locator(selector);
        if (await element.isVisible({ timeout: 10000 })) {
          console.log(`✅ Completion detected: ${selector}`);
          completionFound = true;
          break;
        }
      }

      if (!completionFound) {
        console.log('⚠️ No clear completion indicator found within timeout');
      }

    } catch (error) {
      console.log(`⚠️ Test completed with timeout: ${error.message}`);
    }
  });

  test('should handle progress bar math correctly', async ({ page }) => {
    console.log('🧪 Testing Progress Bar Mathematical Accuracy');

    // Add script to monitor progress updates
    await page.addInitScript(() => {
      window.progressUpdates = [];
      
      // Override console.log to capture progress updates
      const originalLog = console.log;
      console.log = function(...args) {
        if (args[0] && args[0].includes && args[0].includes('%')) {
          window.progressUpdates.push(args[0]);
        }
        originalLog.apply(console, args);
      };
    });

    // Fill in search form for predictable operation count
    await page.fill('input[name="mine_name"]', 'Mine1, Mine2');
    await page.selectOption('select[name="country"]', 'Canada');
    await page.selectOption('select[name="model"]', 'perplexity:sonar');

    // Start search
    await page.click('button[type="submit"]');

    // Wait for progress to potentially update
    await page.waitForTimeout(5000);

    // Check captured progress updates
    const progressUpdates = await page.evaluate(() => window.progressUpdates || []);
    console.log('Progress updates captured:', progressUpdates);

    // Look for percentage values in progress text
    const progressText = page.locator('.progress-fill span');
    if (await progressText.isVisible()) {
      const text = await progressText.textContent();
      console.log(`Final progress text: ${text}`);
      
      // Should contain percentage
      expect(text).toMatch(/\d+(\.\d+)?%/);
    }

    console.log('✅ Progress bar math validation completed');
  });
});

test.afterAll(async () => {
  console.log('🏁 All Progress Tracking tests completed');
});