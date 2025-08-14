/**
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Debug der Card-Routing und Navigation
 */

const { chromium } = require('playwright');

async function debugCardRouting() {
    console.log('🔍 [DEBUG] Analysiere Navigation und Card-Routing...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        console.log('✅ [DEBUG] Page loaded');
        
        // Screenshot der Startseite
        await page.screenshot({ path: 'debug_initial_page.png', fullPage: true });
        
        // Alle Navigation-Links finden
        const navLinks = await page.$$eval('nav a, .nav-link, a[href*="#"]', links => 
            links.map(link => ({
                text: link.textContent?.trim(),
                href: link.href || link.getAttribute('href'),
                className: link.className
            }))
        );
        
        console.log('🧭 [DEBUG] Navigation Links gefunden:');
        navLinks.forEach((link, i) => {
            console.log(`  [${i+1}] "${link.text}" -> ${link.href} (${link.className})`);
        });
        
        // Versuche verschiedene Selektoren für Ergebnisse-Tab
        const possibleSelectors = [
            'a[href="#ergebnisse"]',
            'a[data-tab="consolidated"]',
            'a[data-tab="ergebnisse"]',
            '.nav-link[href="#ergebnisse"]',
            'a:contains("Ergebnisse")',
            'button[data-tab="consolidated"]'
        ];
        
        for (const selector of possibleSelectors) {
            try {
                const element = await page.$(selector);
                if (element) {
                    const text = await element.textContent();
                    console.log(`✅ [DEBUG] Selector "${selector}" gefunden: "${text}"`);
                } else {
                    console.log(`❌ [DEBUG] Selector "${selector}" nicht gefunden`);
                }
            } catch (error) {
                console.log(`❌ [DEBUG] Selector "${selector}" Fehler: ${error.message}`);
            }
        }
        
        // Alle clickable Elemente mit "ergebnis" oder "consolid" im Text
        const resultElements = await page.$$eval('a, button, [data-tab]', elements => 
            elements.filter(el => {
                const text = el.textContent?.toLowerCase() || '';
                const attrs = Array.from(el.attributes).map(attr => attr.value.toLowerCase()).join(' ');
                return text.includes('ergebnis') || text.includes('consolid') || 
                       attrs.includes('ergebnis') || attrs.includes('consolid');
            }).map(el => ({
                tagName: el.tagName,
                text: el.textContent?.trim(),
                id: el.id,
                className: el.className,
                dataTab: el.getAttribute('data-tab'),
                href: el.href || el.getAttribute('href')
            }))
        );
        
        console.log('🎯 [DEBUG] Elemente mit "ergebnis" oder "consolid":');
        resultElements.forEach((el, i) => {
            console.log(`  [${i+1}] ${el.tagName}: "${el.text}" | data-tab: ${el.dataTab} | href: ${el.href}`);
        });
        
        // Prüfe, ob bereits Data-Cards auf der Seite sind
        const existingCards = await page.$$('.mine-data-card');
        console.log(`📊 [DEBUG] Bereits vorhandene Data-Cards: ${existingCards.length}`);
        
        if (existingCards.length > 0) {
            // Extrahiere Titel von vorhandenen Cards
            const cardTitles = [];
            for (let i = 0; i < Math.min(3, existingCards.length); i++) {
                const titleElement = await existingCards[i].$('.card-title');
                if (titleElement) {
                    const title = await titleElement.textContent();
                    cardTitles.push(title);
                }
            }
            console.log('🏷️ [DEBUG] Vorhandene Card-Titel:', cardTitles);
        }
        
        await page.screenshot({ path: 'debug_final_analysis.png', fullPage: true });
        
    } catch (error) {
        console.error('❌ [DEBUG] Error:', error);
    } finally {
        await browser.close();
    }
}

debugCardRouting().catch(console.error);