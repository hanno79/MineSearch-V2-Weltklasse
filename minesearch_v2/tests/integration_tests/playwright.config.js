/**
 * Author: rahn
 * Datum: 16.07.2025
 * Version: 1.0
 * Beschreibung: Playwright-Konfiguration für MineSearch v2.1 Investigation Tests
 */

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './',
  fullyParallel: false, // Für Investigation sequenziell ausführen
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 1, // Nur ein Worker für Investigation
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-reports/playwright-results.json' }],
    ['list']
  ],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'echo "Backend should be running on localhost:8000"',
    port: 8000,
    reuseExistingServer: !process.env.CI,
  },
});