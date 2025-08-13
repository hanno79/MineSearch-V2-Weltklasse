const { chromium } = require('playwright');

(async () => {
    console.log('🔍 [DEBUG] Detaillierter Phase 4 Debug-Test...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Network-Events abhören
    page.on('response', (response) => {
        const url = response.url();
        const status = response.status();
        if (url.includes('style.css') || url.includes('.js') || status >= 400) {
            console.log(`📡 [DEBUG] ${status} - ${url}`);
        }
    });
    
    page.on('console', (msg) => {
        console.log(`🖥️ [CONSOLE] ${msg.text()}`);
    });
    
    try {
        console.log('📋 [DEBUG] Lade http://localhost:8000...');
        await page.goto('http://localhost:8000', { 
            waitUntil: 'networkidle', 
            timeout: 15000 
        });
        
        // Warte länger auf Module Loading
        console.log('⏳ [DEBUG] Warte 8 Sekunden auf vollständiges Laden...');
        await page.waitForTimeout(8000);
        
        // Prüfe DOM-Elemente im Detail
        const linkElements = await page.$$eval('link[rel="stylesheet"]', links => 
            links.map(link => ({
                href: link.href,
                loaded: link.sheet !== null
            }))
        );
        console.log('🔗 [DEBUG] CSS Links:', JSON.stringify(linkElements, null, 2));
        
        // Prüfe Script-Tags
        const scriptElements = await page.$$eval('script[src]', scripts => 
            scripts.map(script => ({
                src: script.src,
                loaded: script.readyState || 'unknown'
            }))
        );
        console.log('📜 [DEBUG] Script Tags (erste 3):', JSON.stringify(scriptElements.slice(0, 3), null, 2));
        
        // Teste direkt ob CSS geladen wurde
        const cssLoaded = await page.evaluate(() => {
            const links = document.querySelectorAll('link[rel="stylesheet"]');
            for (let link of links) {
                if (link.href.includes('style.css')) {
                    return {
                        found: true,
                        href: link.href,
                        hasSheet: !!link.sheet,
                        sheetRules: link.sheet ? link.sheet.cssRules.length : 0
                    };
                }
            }
            return { found: false };
        });
        console.log('🎨 [DEBUG] CSS Load Status:', JSON.stringify(cssLoaded, null, 2));
        
        // Teste JavaScript-Module
        const jsModules = await page.evaluate(() => {
            return {
                window: Object.keys(window).filter(key => 
                    ['ComparisonEngine', 'API_BASE_URL', 'performSearch', 'sanitizeHTML'].includes(key)
                ),
                comparisonEngine: typeof window.ComparisonEngine,
                apiBaseUrl: typeof window.API_BASE_URL
            };
        });
        console.log('🔬 [DEBUG] JavaScript-Module:', JSON.stringify(jsModules, null, 2));
        
        // Screenshot
        await page.screenshot({ 
            path: '/app/debug_detailed_test.png', 
            fullPage: true 
        });
        console.log('📸 [DEBUG] Screenshot gespeichert: /app/debug_detailed_test.png');
        
    } catch (error) {
        console.error('❌ [DEBUG] Fehler:', error.message);
        await page.screenshot({ 
            path: '/app/debug_error.png', 
            fullPage: true 
        });
    } finally {
        await browser.close();
    }
})();