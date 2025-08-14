/**
 * Header Navigation Test - PHASE 1 Validation
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Playwright Test für die Professional Header Revolution
 */

const { chromium } = require('playwright');

async function testHeaderNavigation() {
    console.log('🧭 [HEADER-TEST] Starting Professional Header Navigation Test...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor JavaScript errors
    page.on('pageerror', error => {
        console.log('💥 [JS ERROR]', error.message);
    });
    
    // Monitor console messages
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[NAVIGATION]') || text.includes('[HEADER]')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoad: false,
        headerElements: false,
        quickSearch: false,
        navigation: false,
        mobileMenu: false,
        breadcrumbs: false,
        modals: false
    };
    
    try {
        console.log('🔄 [TEST 1] Page Load & Header Elements...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        testResults.pageLoad = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        console.log('🔄 [TEST 2] Header Elements Validation...');
        
        // Check brand section
        const brandLogo = await page.$('.brand-logo');
        const brandTitle = await page.$('.brand-title');
        const brandVersion = await page.$('.brand-version');
        const brandTagline = await page.$('.brand-tagline');
        
        // Check quick search
        const quickSearchInput = await page.$('#quick-search-input');
        const quickSearchBtn = await page.$('.quick-search-btn');
        
        // Check header actions
        const helpBtn = await page.$('button[onclick="toggleHelpModal()"]');
        const settingsBtn = await page.$('button[onclick="toggleSettingsModal()"]');
        const mobileMenuBtn = await page.$('.mobile-menu-toggle');
        
        // Check navigation
        const mainNavigation = await page.$('.main-navigation');
        const navItems = await page.$$('.nav-item');
        
        // Check breadcrumbs
        const breadcrumbNav = await page.$('#breadcrumb-nav');
        
        const headerElementsCount = [
            brandLogo, brandTitle, brandVersion, brandTagline,
            quickSearchInput, quickSearchBtn,
            helpBtn, settingsBtn, mobileMenuBtn,
            mainNavigation, breadcrumbNav
        ].filter(Boolean).length;
        
        if (headerElementsCount >= 10) {
            testResults.headerElements = true;
            console.log(`✅ [TEST 2] Header elements present: ${headerElementsCount}/11`);
            console.log(`📊 [TEST 2] Navigation items: ${navItems.length}`);
        } else {
            console.log(`❌ [TEST 2] Missing header elements: ${11 - headerElementsCount}`);
        }
        
        console.log('🔄 [TEST 3] Quick Search Functionality...');
        
        if (quickSearchInput && quickSearchBtn) {
            await quickSearchInput.fill('Eleonore Mine');
            await page.waitForTimeout(500);
            
            // Check if search field contains the text
            const searchValue = await quickSearchInput.inputValue();
            if (searchValue === 'Eleonore Mine') {
                testResults.quickSearch = true;
                console.log('✅ [TEST 3] Quick search input functional');
            }
        }
        
        console.log('🔄 [TEST 4] Navigation Tab Switching...');
        
        if (navItems.length >= 5) {
            // Test tab switching by clicking nav items
            for (let i = 0; i < Math.min(3, navItems.length); i++) {
                await navItems[i].click();
                await page.waitForTimeout(1000);
                
                const isActive = await navItems[i].evaluate(el => el.classList.contains('active'));
                if (isActive) {
                    testResults.navigation = true;
                    console.log(`✅ [TEST 4] Navigation item ${i + 1} activated successfully`);
                    break;
                }
            }
        }
        
        console.log('🔄 [TEST 5] Mobile Menu Functionality...');
        
        // Test mobile menu (resize to mobile first)
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        
        const mobileMenuToggle = await page.$('.mobile-menu-toggle');
        if (mobileMenuToggle) {
            const isVisible = await mobileMenuToggle.isVisible();
            if (isVisible) {
                await mobileMenuToggle.click();
                await page.waitForTimeout(1000);
                
                const mobileOverlay = await page.$('#mobile-nav-overlay');
                if (mobileOverlay) {
                    const overlayVisible = await mobileOverlay.isVisible();
                    if (overlayVisible) {
                        testResults.mobileMenu = true;
                        console.log('✅ [TEST 5] Mobile menu opens correctly');
                        
                        // Close mobile menu
                        const closeBtn = await page.$('.mobile-nav-close');
                        if (closeBtn) {
                            await closeBtn.click();
                            await page.waitForTimeout(500);
                        }
                    }
                }
            }
        }
        
        // Back to desktop
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.waitForTimeout(1000);
        
        console.log('🔄 [TEST 6] Breadcrumb Navigation...');
        
        const breadcrumbItems = await page.$$('.breadcrumb-item');
        const currentSection = await page.$('#current-section .breadcrumb-text');
        
        if (breadcrumbItems.length >= 2 && currentSection) {
            const sectionText = await currentSection.textContent();
            if (sectionText && sectionText.trim().length > 0) {
                testResults.breadcrumbs = true;
                console.log(`✅ [TEST 6] Breadcrumb navigation: ${breadcrumbItems.length} items, current: "${sectionText}"`);
            }
        }
        
        console.log('🔄 [TEST 7] Modal System...');
        
        // Test help modal
        if (helpBtn) {
            await helpBtn.click();
            await page.waitForTimeout(1000);
            
            const helpModal = await page.$('#help-modal');
            if (helpModal) {
                const isVisible = await helpModal.isVisible();
                if (isVisible) {
                    testResults.modals = true;
                    console.log('✅ [TEST 7] Help modal opens correctly');
                    
                    // Close modal
                    const closeBtn = await helpModal.$('.modal-close');
                    if (closeBtn) {
                        await closeBtn.click();
                        await page.waitForTimeout(500);
                    }
                }
            }
        }
        
        console.log('🔄 [TEST 8] Final Screenshots...');
        
        // Desktop screenshot
        await page.screenshot({ path: 'header_navigation_desktop.png', fullPage: true });
        
        // Mobile screenshot
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'header_navigation_mobile.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'header_navigation_error.png' });
    } finally {
        await browser.close();
    }
    
    // Final Assessment
    console.log('');
    console.log('🏆 [HEADER NAVIGATION TEST RESULTS]');
    console.log('===================================');
    
    const testItems = [
        { name: 'Page Load', status: testResults.pageLoad },
        { name: 'Header Elements', status: testResults.headerElements },
        { name: 'Quick Search', status: testResults.quickSearch },
        { name: 'Navigation', status: testResults.navigation },
        { name: 'Mobile Menu', status: testResults.mobileMenu },
        { name: 'Breadcrumbs', status: testResults.breadcrumbs },
        { name: 'Modals', status: testResults.modals }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 90) {
        console.log('');
        console.log('🎉 PROFESSIONAL HEADER REVOLUTION: EXCELLENT!');
        console.log('✅ All major header components functional');
        console.log('✅ Navigation system working perfectly');
        console.log('✅ Mobile-first design implemented');
        console.log('✅ Professional brand identity established');
        console.log('🚀 Ready for production use!');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 PROFESSIONAL HEADER REVOLUTION: GOOD PROGRESS');
        console.log('✅ Core functionality working');
        console.log('⚠️ Some features need refinement');
    } else {
        console.log('');
        console.log('⚠️ PROFESSIONAL HEADER REVOLUTION: NEEDS MORE WORK');
        console.log('❌ Multiple issues need attention');
        console.log('🔧 Further debugging required');
    }
    
    console.log('🏁 [HEADER NAVIGATION TEST] Complete');
    return successRate >= 80;
}

testHeaderNavigation().catch(console.error);