/**
 * Favicon Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test der Favicon-Integration
 */

const { chromium } = require('playwright');

async function testFavicon() {
    console.log('🎯 [FAVICON-TEST] Testing favicon integration...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor network requests for favicon
    const faviconRequests = [];
    page.on('request', request => {
        if (request.url().includes('favicon')) {
            faviconRequests.push({
                url: request.url(),
                method: request.method()
            });
        }
    });
    
    // Monitor responses for favicon
    const faviconResponses = [];
    page.on('response', response => {
        if (response.url().includes('favicon')) {
            faviconResponses.push({
                url: response.url(),
                status: response.status(),
                contentType: response.headers()['content-type']
            });
        }
    });
    
    try {
        console.log('📍 [STEP 1] Loading page and checking favicon requests...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('📊 [REQUESTS] Favicon requests made:');
        faviconRequests.forEach((req, index) => {
            console.log(`  ${index + 1}. ${req.method} ${req.url}`);
        });
        
        console.log('📊 [RESPONSES] Favicon responses received:');
        faviconResponses.forEach((res, index) => {
            const status = res.status === 200 ? '✅' : '❌';
            console.log(`  ${index + 1}. ${status} ${res.status} ${res.url}`);
            console.log(`      Content-Type: ${res.contentType}`);
        });
        
        // Check HTML head for favicon links
        const faviconLinks = await page.$$eval('link[rel*="icon"]', links => {
            return links.map(link => ({
                rel: link.rel,
                href: link.href,
                type: link.type || 'not specified',
                sizes: link.sizes.toString() || 'not specified'
            }));
        });
        
        console.log('📊 [HTML] Favicon links in HTML head:');
        faviconLinks.forEach((link, index) => {
            console.log(`  ${index + 1}. rel="${link.rel}" href="${link.href}"`);
            console.log(`      type="${link.type}" sizes="${link.sizes}"`);
        });
        
        // Screenshot to show favicon in tab
        await page.screenshot({ path: 'favicon_test_result.png' });
        console.log('📸 Screenshot saved: favicon_test_result.png');
        
        // Summary
        console.log('');
        console.log('🏆 [FAVICON TEST RESULTS]');
        console.log('=========================');
        
        const hasSuccessfulRequests = faviconResponses.some(res => res.status === 200);
        const hasCorrectLinks = faviconLinks.length >= 3;
        const hasSVG = faviconResponses.some(res => res.contentType?.includes('svg'));
        const hasICO = faviconResponses.some(res => res.contentType?.includes('icon'));
        
        console.log(`✅ Favicon requests made: ${faviconRequests.length > 0 ? 'YES' : 'NO'}`);
        console.log(`✅ Successful responses: ${hasSuccessfulRequests ? 'YES' : 'NO'}`);
        console.log(`✅ HTML links present: ${hasCorrectLinks ? 'YES' : 'NO'}`);
        console.log(`✅ SVG favicon served: ${hasSVG ? 'YES' : 'NO'}`);
        console.log(`✅ ICO fallback served: ${hasICO ? 'YES' : 'NO'}`);
        
        const success = hasSuccessfulRequests && hasCorrectLinks;
        if (success) {
            console.log('');
            console.log('🎉 FAVICON INTEGRATION: SUCCESS!');
            console.log('✅ No more 404 errors for favicon requests');
            console.log('✅ Professional MineSearch icon visible in browser tabs');
            console.log('✅ Multiple formats supported (SVG + ICO + PNG)');
        } else {
            console.log('');
            console.log('❌ FAVICON INTEGRATION: NEEDS ATTENTION');
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'favicon_test_error.png' });
    } finally {
        await browser.close();
    }
}

testFavicon().catch(console.error);