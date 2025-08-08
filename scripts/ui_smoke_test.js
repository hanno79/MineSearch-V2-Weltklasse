// Simple Playwright UI smoke test clicking all tabs
const { chromium } = require('playwright');

(async () => {
  const baseUrl = process.env.UI_BASE_URL || 'http://127.0.0.1:8080/index.html';
  const outDir = process.env.UI_OUT_DIR || '/app/playwright-mcp/screenshots';
  const fs = require('fs');
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  const snap = async (name) => page.screenshot({ path: `${outDir}/${name}.png`, fullPage: true });

  try {
    console.log(`[UI] Navigating to ${baseUrl}`);
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('section.tab-navigation', { timeout: 10000 });
    await snap('01_loaded');

    const clickTab = async (id, formId, name) => {
      await page.click(`label[for="${id}"]`);
      await page.waitForTimeout(200);
      await page.waitForSelector(`#${formId}.active`, { timeout: 5000 });
      console.log(`[UI] Tab visible: ${name}`);
      await snap(`tab_${name}`);
    };

    await clickTab('method_csv', 'csv_form', 'csv');
    await clickTab('method_single', 'single_form', 'single');
    await clickTab('method_sources', 'sources_form', 'sources');
    await clickTab('method_results', 'results_form', 'results');
    await clickTab('method_consolidated', 'consolidated_form', 'consolidated');
    await clickTab('method_statistics', 'statistics_form', 'statistics');

    console.log('[UI] All tabs clicked and validated.');
  } catch (err) {
    console.error('[UI] Smoke test failed:', err);
    await snap('__error');
    process.exitCode = 1;
  } finally {
    await page.close();
    await context.close();
    await browser.close();
  }
})();
