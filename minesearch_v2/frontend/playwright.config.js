/**
 * Author: rahn
 * Datum: 27.07.2025
 * Version: 1.0
 * Beschreibung: Playwright Konfiguration für MineSearch Frontend Tests
 */

module.exports = {
    testDir: './',
    timeout: 30 * 1000,
    expect: {
        timeout: 5000
    },
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: 'html',
    use: {
        baseURL: 'http://localhost:3000',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        headless: true, // Für Container-Umgebung
    },

    projects: [
        {
            name: 'chromium',
            use: { 
                ...require('@playwright/test').devices['Desktop Chrome'],
                // Für Container ohne GPU
                launchOptions: {
                    args: [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-first-run',
                        '--no-zygote',
                        '--single-process'
                    ]
                }
            },
        },
    ],

    webServer: [
        {
            command: 'python -m http.server 3000',
            port: 3000,
            reuseExistingServer: !process.env.CI,
        }
    ],
};