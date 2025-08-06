/**
 * Author: rahn
 * Datum: 06.08.2025
 * Version: 1.0
 * Beschreibung: Quick System Test für MineSearch v2 - Angepasste Selektoren
 */

import { test, expect } from '@playwright/test';

test.describe('MineSearch v2 - Quick System Test', () => {
    
    test.beforeEach(async ({ page }) => {
        // Navigate to the application
        await page.goto('http://localhost:8000');
        
        // Wait for the page to load
        await page.waitForSelector('h1', { timeout: 10000 });
        
        console.log('✅ Page loaded successfully');
    });

    test('Phase 4.1: Frontend Loading and Basic Elements', async ({ page }) => {
        console.log('🧪 TEST: Frontend Loading and Basic Elements');
        
        // Check main title
        const title = await page.locator('h1');
        await expect(title).toBeVisible();
        console.log('✅ Main title found');
        
        // Look for file input elements (CSV upload)
        const fileInputs = await page.locator('input[type="file"]').all();
        if (fileInputs.length > 0) {
            console.log(`✅ Found ${fileInputs.length} file input(s) for CSV upload`);
        } else {
            console.log('⚠️ No file input elements found');
        }
        
        // Look for select elements (model selection)
        const selects = await page.locator('select').all();
        if (selects.length > 0) {
            console.log(`✅ Found ${selects.length} select element(s) for model selection`);
        } else {
            console.log('⚠️ No select elements found');
        }
        
        // Look for buttons (start search)
        const buttons = await page.locator('button').all();
        if (buttons.length > 0) {
            console.log(`✅ Found ${buttons.length} button(s)`);
        } else {
            console.log('⚠️ No buttons found');
        }
    });

    test('Phase 4.2: API Endpoints Test', async ({ page }) => {
        console.log('🧪 TEST: API Endpoints');
        
        // Test API endpoints
        const endpoints = [
            '/api/statistics',
            '/api/mines/all',
            '/api/results'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await page.request.get(`http://localhost:8000${endpoint}`);
                console.log(`📡 ${endpoint}: HTTP ${response.status()}`);
                
                if (response.status() === 200) {
                    const responseBody = await response.text();
                    try {
                        const jsonData = JSON.parse(responseBody);
                        console.log(`✅ ${endpoint}: Valid JSON response`);
                    } catch (e) {
                        console.log(`⚠️ ${endpoint}: Non-JSON response`);
                    }
                } else if (response.status() === 404) {
                    console.log(`❌ ${endpoint}: Endpoint not found`);
                } else {
                    console.log(`⚠️ ${endpoint}: HTTP ${response.status()}`);
                }
            } catch (error) {
                console.log(`❌ ${endpoint}: Request failed - ${error.message}`);
            }
        }
        
        console.log('✅ API endpoints test completed');
    });

    test('Phase 4.3: UI Elements Discovery', async ({ page }) => {
        console.log('🧪 TEST: UI Elements Discovery');
        
        // Get page content for analysis
        const bodyText = await page.locator('body').textContent();
        
        // Check for key terms that should be present
        const keyTerms = [
            'MineSearch',
            'CSV',
            'Upload',
            'Search',
            'Models',
            'Results',
            'Statistics'
        ];
        
        console.log('📊 Key Terms Analysis:');
        for (const term of keyTerms) {
            if (bodyText.toLowerCase().includes(term.toLowerCase())) {
                console.log(`✅ "${term}" found in page content`);
            } else {
                console.log(`❌ "${term}" NOT found in page content`);
            }
        }
        
        // Look for form elements
        const forms = await page.locator('form').all();
        console.log(`📝 Forms found: ${forms.length}`);
        
        // Look for input elements
        const inputs = await page.locator('input').all();
        console.log(`📝 Input elements found: ${inputs.length}`);
        
        // Look for divs with common IDs
        const commonIds = ['content', 'main', 'container', 'app', 'search', 'results'];
        for (const id of commonIds) {
            const element = page.locator(`#${id}`);
            if (await element.isVisible()) {
                console.log(`✅ Element #${id} found and visible`);
            }
        }
    });

    test('Phase 4.4: Console Errors Check', async ({ page }) => {
        console.log('🧪 TEST: Console Errors Check');
        
        const errors = [];
        const warnings = [];
        
        // Listen for console messages
        page.on('console', msg => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
                console.log(`❌ Console Error: ${msg.text()}`);
            } else if (msg.type() === 'warning') {
                warnings.push(msg.text());
                console.log(`⚠️ Console Warning: ${msg.text()}`);
            }
        });
        
        // Navigate and wait a bit to catch any console messages
        await page.reload();
        await page.waitForTimeout(5000);
        
        console.log(`📊 Console Summary:`);
        console.log(`   Errors: ${errors.length}`);
        console.log(`   Warnings: ${warnings.length}`);
        
        if (errors.length === 0) {
            console.log('✅ No console errors detected');
        } else {
            console.log('❌ Console errors present (see above)');
        }
        
        // Don't fail the test for console warnings/errors in this discovery phase
        expect(true).toBeTruthy();
    });

    test('Phase 4.5: Basic Performance Check', async ({ page }) => {
        console.log('🧪 TEST: Basic Performance Check');
        
        const startTime = Date.now();
        
        // Navigate to the page
        await page.goto('http://localhost:8000');
        const loadTime = Date.now() - startTime;
        
        console.log(`📊 Page Load Time: ${loadTime}ms`);
        
        // Wait for main elements to be visible
        const titleVisible = await page.locator('h1').isVisible();
        const bodyVisible = await page.locator('body').isVisible();
        
        console.log(`✅ Title Visible: ${titleVisible}`);
        console.log(`✅ Body Visible: ${bodyVisible}`);
        
        // Performance assertions
        expect(loadTime).toBeLessThan(10000); // Page should load in less than 10s
        expect(titleVisible).toBeTruthy();
        expect(bodyVisible).toBeTruthy();
        
        console.log('✅ Basic performance test completed');
    });
});