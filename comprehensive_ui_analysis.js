/**
 * Comprehensive UI/UX Content Analysis
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Vollständige Analyse aller Tabs mit Fokus auf Inhalte und Cross-Tab-Konsistenz
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

class ComprehensiveUIAnalyzer {
    constructor() {
        this.browser = null;
        this.page = null;
        this.analysisResults = {
            ergebnisse: {},
            statistiken: {},
            quellen: {},
            crossValidation: {},
            issues: [],
            screenshots: []
        };
        this.referenceData = {
            mineNames: new Set(),
            modelNames: new Set(),
            sourceNames: new Set(),
            counts: {}
        };
    }

    async initialize() {
        console.log('🚀 [ANALYZER] Initializing Comprehensive UI Analysis...');
        this.browser = await chromium.launch({ 
            headless: false,
            slowMo: 1000 // Langsamer für bessere Beobachtung
        });
        this.page = await this.browser.newPage();
        
        // Console monitoring for errors
        this.page.on('console', msg => {
            if (msg.type() === 'error') {
                this.logIssue('JavaScript Error', msg.text(), 'high');
            }
        });

        await this.page.goto('http://localhost:8000');
        await this.page.waitForLoadState('networkidle');
        await this.page.waitForTimeout(3000);
        console.log('✅ [ANALYZER] Page loaded successfully');
    }

    async takeScreenshot(name, description = '') {
        const filename = `analysis_${name}_${Date.now()}.png`;
        const filepath = path.join(__dirname, filename);
        await this.page.screenshot({ path: filepath, fullPage: true });
        
        this.analysisResults.screenshots.push({
            name,
            filename,
            description,
            timestamp: new Date().toISOString()
        });
        
        console.log(`📷 [SCREENSHOT] ${name}: ${filepath}`);
        return filename;
    }

    logIssue(category, description, severity = 'medium', tab = 'general') {
        const issue = {
            category,
            description,
            severity,
            tab,
            timestamp: new Date().toISOString()
        };
        
        this.analysisResults.issues.push(issue);
        console.log(`⚠️ [${severity.toUpperCase()}] ${category}: ${description}`);
    }

    async analyzeErgebnisseTab() {
        console.log('📋 [PHASE 1] Analyzing Ergebnisse (Consolidated) Tab...');
        
        // Navigate to Consolidated tab
        await this.page.click('a[data-tab="consolidated"]');
        await this.page.waitForTimeout(2000);
        await this.takeScreenshot('ergebnisse_initial', 'Initial view of Ergebnisse tab');

        // Wait for data to load
        console.log('⏳ [PHASE 1] Waiting for consolidated data to load...');
        await this.page.waitForTimeout(5000);

        // Analyze data cards
        await this.analyzeDataCards();
        
        // Test modal dialogs
        await this.testModalDialogs();
        
        // Collect reference data for cross-validation
        await this.collectReferenceData();

        console.log('✅ [PHASE 1] Ergebnisse Tab analysis completed');
    }

    async analyzeDataCards() {
        console.log('🔍 [DATA-CARDS] Analyzing mine data cards...');

        const cards = await this.page.$$('.mine-data-card');
        console.log(`📊 [DATA-CARDS] Found ${cards.length} mine cards`);

        if (cards.length === 0) {
            this.logIssue('No Data Cards', 'No mine data cards found in Ergebnisse tab', 'high', 'ergebnisse');
            return;
        }

        for (let i = 0; i < Math.min(cards.length, 5); i++) { // Analyze first 5 cards
            const card = cards[i];
            await this.analyzeIndividualCard(card, i + 1);
        }

        this.analysisResults.ergebnisse.totalCards = cards.length;
    }

    async analyzeIndividualCard(card, cardNumber) {
        console.log(`🏭 [CARD ${cardNumber}] Analyzing individual card...`);

        try {
            // Extract card data
            const cardData = await card.evaluate(el => {
                const title = el.querySelector('.card-title')?.textContent?.trim();
                const subtitle = el.querySelector('.card-subtitle')?.textContent?.trim();
                const mineType = el.querySelector('.mine-type-badge')?.textContent?.trim();
                
                // Extract all data rows
                const dataRows = Array.from(el.querySelectorAll('.data-row')).map(row => ({
                    label: row.querySelector('.data-label')?.textContent?.trim(),
                    value: row.querySelector('.data-value, .status-indicator')?.textContent?.trim()
                }));
                
                // Extract source badges
                const sourceBadges = Array.from(el.querySelectorAll('.source-badge')).map(badge => 
                    badge.textContent?.trim()
                );
                
                return {
                    title,
                    subtitle,
                    mineType,
                    dataRows,
                    sourceBadges
                };
            });

            console.log(`📊 [CARD ${cardNumber}] Data:`, JSON.stringify(cardData, null, 2));

            // Validation checks
            this.validateCardData(cardData, cardNumber);
            
            // Store reference data
            if (cardData.title) {
                this.referenceData.mineNames.add(cardData.title.replace('🏭 ', ''));
            }
            
            cardData.sourceBadges.forEach(source => {
                if (source) this.referenceData.sourceNames.add(source);
            });

        } catch (error) {
            this.logIssue('Card Analysis Error', `Error analyzing card ${cardNumber}: ${error.message}`, 'medium', 'ergebnisse');
        }
    }

    validateCardData(cardData, cardNumber) {
        // Check for missing essential data
        if (!cardData.title || cardData.title === '🏭 Unbekannte Mine') {
            this.logIssue('Missing Mine Name', `Card ${cardNumber} has missing or default mine name`, 'high', 'ergebnisse');
        }

        if (!cardData.subtitle || cardData.subtitle.includes('Unbekannt')) {
            this.logIssue('Missing Location', `Card ${cardNumber} has missing location information`, 'medium', 'ergebnisse');
        }

        // Check for suspicious data patterns
        cardData.dataRows.forEach(row => {
            if (row.value && (
                row.value.includes('null') || 
                row.value.includes('undefined') || 
                row.value.includes('NaN') ||
                row.value.includes('0000-00-00') ||
                row.value === '0.0' ||
                row.value === 'None'
            )) {
                this.logIssue('Suspicious Data Value', `Card ${cardNumber} - ${row.label}: "${row.value}"`, 'medium', 'ergebnisse');
            }
        });

        // Check for missing source attribution
        if (cardData.sourceBadges.length === 0) {
            this.logIssue('No Source Attribution', `Card ${cardNumber} has no source badges`, 'medium', 'ergebnisse');
        }
    }

    async testModalDialogs() {
        console.log('🔍 [MODALS] Testing modal dialog functionality...');

        const detailsButtons = await this.page.$$('button:has-text("Details anzeigen")');
        
        if (detailsButtons.length === 0) {
            this.logIssue('No Detail Buttons', 'No "Details anzeigen" buttons found', 'high', 'ergebnisse');
            return;
        }

        // Test first details button
        try {
            console.log('🔍 [MODAL] Clicking first details button...');
            await detailsButtons[0].click();
            await this.page.waitForTimeout(2000);

            // Check if modal opened
            const modal = await this.page.$('.modal, [role="dialog"]');
            if (modal) {
                await this.takeScreenshot('modal_details', 'Details modal opened');
                console.log('✅ [MODAL] Details modal opened successfully');

                // Analyze modal content
                await this.analyzeModalContent(modal);

                // Close modal
                const closeButton = await this.page.$('.modal button:has-text("Schließen"), .modal .close, [aria-label="Close"]');
                if (closeButton) {
                    await closeButton.click();
                    await this.page.waitForTimeout(1000);
                }
            } else {
                this.logIssue('Modal Not Opening', 'Details modal did not open when button clicked', 'high', 'ergebnisse');
            }
        } catch (error) {
            this.logIssue('Modal Test Error', `Error testing modal: ${error.message}`, 'medium', 'ergebnisse');
        }
    }

    async analyzeModalContent(modal) {
        const modalData = await modal.evaluate(el => {
            const title = el.querySelector('h1, h2, h3, .modal-title')?.textContent?.trim();
            
            const fields = Array.from(el.querySelectorAll('.field-row, .data-row, tr')).map(row => {
                const label = row.querySelector('.field-label, .data-label, td:first-child')?.textContent?.trim();
                const value = row.querySelector('.field-value, .data-value, td:last-child')?.textContent?.trim();
                return { label, value };
            }).filter(field => field.label && field.value);

            return { title, fields };
        });

        console.log(`📊 [MODAL] Content: ${modalData.fields.length} fields found`);

        // Validate modal content
        if (modalData.fields.length === 0) {
            this.logIssue('Empty Modal', 'Modal contains no field data', 'high', 'ergebnisse');
        }

        // Check for placeholder values
        modalData.fields.forEach(field => {
            if (field.value && (
                field.value.includes('Lorem ipsum') ||
                field.value.includes('Placeholder') ||
                field.value === 'TBD' ||
                field.value === 'TODO'
            )) {
                this.logIssue('Placeholder Content', `Modal field "${field.label}" contains placeholder: "${field.value}"`, 'medium', 'ergebnisse');
            }
        });
    }

    async collectReferenceData() {
        console.log('📊 [REFERENCE] Collecting reference data for cross-validation...');
        
        // Count cards for cross-validation
        const cardCount = await this.page.$$eval('.mine-data-card', cards => cards.length);
        this.referenceData.counts.totalMines = cardCount;
        
        console.log(`📊 [REFERENCE] Collected: ${this.referenceData.mineNames.size} mine names, ${this.referenceData.sourceNames.size} source names`);
    }

    async analyzeStatistikenTab() {
        console.log('📈 [PHASE 2] Analyzing Statistiken Tab...');
        
        await this.page.click('a[data-tab="statistics"]');
        await this.page.waitForTimeout(3000);
        await this.takeScreenshot('statistiken_initial', 'Initial view of Statistiken tab');

        // Wait for statistics to load
        console.log('⏳ [PHASE 2] Waiting for statistics data to load...');
        await this.page.waitForTimeout(5000);

        await this.analyzeModelStatistics();
        await this.validateLogicalDependencies();
        
        console.log('✅ [PHASE 2] Statistiken Tab analysis completed');
    }

    async analyzeModelStatistics() {
        console.log('🔍 [STATISTICS] Analyzing model statistics cards...');

        const statCards = await this.page.$$('.model-card, .statistics-card, .data-card');
        console.log(`📊 [STATISTICS] Found ${statCards.length} statistics cards`);

        if (statCards.length === 0) {
            this.logIssue('No Statistics Cards', 'No statistics cards found', 'high', 'statistiken');
            return;
        }

        // Analyze each statistics card
        for (let i = 0; i < Math.min(statCards.length, 10); i++) {
            await this.analyzeStatisticsCard(statCards[i], i + 1);
        }
    }

    async analyzeStatisticsCard(card, cardNumber) {
        console.log(`🤖 [STAT-CARD ${cardNumber}] Analyzing statistics card...`);

        try {
            const cardData = await card.evaluate(el => {
                const title = el.querySelector('h3, .card-title, .model-name')?.textContent?.trim();
                
                const metrics = Array.from(el.querySelectorAll('.metric, .stat-item, .data-row')).map(metric => {
                    const label = metric.querySelector('.metric-label, .stat-label, .data-label')?.textContent?.trim();
                    const value = metric.querySelector('.metric-value, .stat-value, .data-value')?.textContent?.trim();
                    return { label, value };
                }).filter(m => m.label && m.value);

                return { title, metrics };
            });

            console.log(`📊 [STAT-CARD ${cardNumber}] ${cardData.title}: ${cardData.metrics.length} metrics`);

            // Store model name for cross-validation
            if (cardData.title) {
                this.referenceData.modelNames.add(cardData.title);
            }

            // Validate statistical logic
            this.validateStatisticsLogic(cardData, cardNumber);

        } catch (error) {
            this.logIssue('Statistics Analysis Error', `Error analyzing statistics card ${cardNumber}: ${error.message}`, 'medium', 'statistiken');
        }
    }

    validateStatisticsLogic(cardData, cardNumber) {
        const metrics = {};
        
        // Parse metrics into structured data
        cardData.metrics.forEach(metric => {
            const value = metric.value;
            
            if (metric.label.toLowerCase().includes('suchen') && metric.label.toLowerCase().includes('gesamt')) {
                metrics.totalSearches = this.parseNumericValue(value);
            }
            if (metric.label.toLowerCase().includes('erfolgreich')) {
                metrics.successfulSearches = this.parseNumericValue(value);
            }
            if (metric.label.toLowerCase().includes('erfolgsrate') || metric.label.toLowerCase().includes('success')) {
                metrics.successRate = this.parsePercentageValue(value);
            }
            if (metric.label.toLowerCase().includes('antwortzeit') || metric.label.toLowerCase().includes('response')) {
                metrics.responseTime = this.parseNumericValue(value);
            }
        });

        // Critical logic validations
        
        // Rule 1: Zero searches → everything else must be zero/null
        if (metrics.totalSearches === 0) {
            if (metrics.successfulSearches > 0) {
                this.logIssue('Logic Violation', `Card ${cardNumber}: 0 total searches but ${metrics.successfulSearches} successful`, 'high', 'statistiken');
            }
            if (metrics.successRate > 0) {
                this.logIssue('Logic Violation', `Card ${cardNumber}: 0 total searches but ${metrics.successRate}% success rate`, 'high', 'statistiken');
            }
            if (metrics.responseTime > 0) {
                this.logIssue('Logic Violation', `Card ${cardNumber}: 0 total searches but has response time`, 'high', 'statistiken');
            }
        }

        // Rule 2: Successful searches can't exceed total searches
        if (metrics.successfulSearches > metrics.totalSearches) {
            this.logIssue('Logic Violation', `Card ${cardNumber}: ${metrics.successfulSearches} successful > ${metrics.totalSearches} total searches`, 'high', 'statistiken');
        }

        // Rule 3: Success rate calculation
        if (metrics.totalSearches > 0 && metrics.successfulSearches >= 0 && metrics.successRate >= 0) {
            const calculatedRate = Math.round((metrics.successfulSearches / metrics.totalSearches) * 100);
            if (Math.abs(calculatedRate - metrics.successRate) > 1) { // Allow 1% rounding difference
                this.logIssue('Logic Violation', `Card ${cardNumber}: Success rate should be ${calculatedRate}% but shows ${metrics.successRate}%`, 'medium', 'statistiken');
            }
        }

        // Rule 4: Success rate can't exceed 100%
        if (metrics.successRate > 100) {
            this.logIssue('Logic Violation', `Card ${cardNumber}: Success rate ${metrics.successRate}% > 100%`, 'high', 'statistiken');
        }
    }

    parseNumericValue(value) {
        if (!value) return 0;
        const parsed = parseFloat(value.replace(/[^\d.-]/g, ''));
        return isNaN(parsed) ? 0 : parsed;
    }

    parsePercentageValue(value) {
        if (!value) return 0;
        const parsed = parseFloat(value.replace(/[^\d.-]/g, ''));
        return isNaN(parsed) ? 0 : parsed;
    }

    async validateLogicalDependencies() {
        console.log('🔍 [LOGIC] Validating logical dependencies across statistics...');
        
        // This will be implemented with specific cross-checks
        // between different statistical elements
    }

    async analyzeQuellenTab() {
        console.log('📚 [PHASE 3] Analyzing Quellen Tab...');
        
        await this.page.click('a[data-tab="sources"]');
        await this.page.waitForTimeout(3000);
        await this.takeScreenshot('quellen_initial', 'Initial view of Quellen tab');

        await this.analyzeSourcesList();
        
        console.log('✅ [PHASE 3] Quellen Tab analysis completed');
    }

    async analyzeSourcesList() {
        console.log('🔍 [SOURCES] Analyzing sources list...');

        const sourceItems = await this.page.$$('.source-item, .source-card, tbody tr');
        console.log(`📊 [SOURCES] Found ${sourceItems.length} source entries`);

        this.referenceData.counts.totalSources = sourceItems.length;

        if (sourceItems.length === 0) {
            this.logIssue('No Sources', 'No source items found in Quellen tab', 'high', 'quellen');
        }
    }

    async performCrossValidation() {
        console.log('🔍 [PHASE 4] Performing Cross-Tab Validation...');

        // Validate mine names consistency
        console.log(`📊 [CROSS-VALIDATION] Mine names found: ${this.referenceData.mineNames.size}`);
        console.log(`📊 [CROSS-VALIDATION] Model names found: ${this.referenceData.modelNames.size}`);
        console.log(`📊 [CROSS-VALIDATION] Source names found: ${this.referenceData.sourceNames.size}`);

        // Log reference data for analysis
        console.log('📋 [CROSS-VALIDATION] Mine Names:', Array.from(this.referenceData.mineNames));
        console.log('📋 [CROSS-VALIDATION] Model Names:', Array.from(this.referenceData.modelNames));
        console.log('📋 [CROSS-VALIDATION] Source Names:', Array.from(this.referenceData.sourceNames));
    }

    async generateReport() {
        console.log('📄 [REPORT] Generating comprehensive analysis report...');

        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                totalIssues: this.analysisResults.issues.length,
                highSeverityIssues: this.analysisResults.issues.filter(i => i.severity === 'high').length,
                screenshotsTaken: this.analysisResults.screenshots.length
            },
            referenceData: {
                mineNames: Array.from(this.referenceData.mineNames),
                modelNames: Array.from(this.referenceData.modelNames),
                sourceNames: Array.from(this.referenceData.sourceNames),
                counts: this.referenceData.counts
            },
            detailedResults: this.analysisResults,
            recommendations: this.generateRecommendations()
        };

        // Save detailed JSON report
        const reportPath = path.join(__dirname, `ui_analysis_report_${Date.now()}.json`);
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`📄 [REPORT] Detailed report saved: ${reportPath}`);

        return report;
    }

    generateRecommendations() {
        const recommendations = [];
        
        const highIssues = this.analysisResults.issues.filter(i => i.severity === 'high');
        if (highIssues.length > 0) {
            recommendations.push(`🚨 CRITICAL: ${highIssues.length} high-severity issues need immediate attention`);
        }

        const logicIssues = this.analysisResults.issues.filter(i => i.category.includes('Logic Violation'));
        if (logicIssues.length > 0) {
            recommendations.push(`🔍 LOGIC: ${logicIssues.length} logical inconsistencies detected - review statistical calculations`);
        }

        return recommendations;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
        console.log('🧹 [CLEANUP] Analysis completed and browser closed');
    }
}

// Main execution
async function runComprehensiveAnalysis() {
    const analyzer = new ComprehensiveUIAnalyzer();
    
    try {
        await analyzer.initialize();
        
        // Phase 1: Ergebnisse Tab
        await analyzer.analyzeErgebnisseTab();
        
        // Phase 2: Statistiken Tab
        await analyzer.analyzeStatistikenTab();
        
        // Phase 3: Quellen Tab
        await analyzer.analyzeQuellenTab();
        
        // Phase 4: Cross-validation
        await analyzer.performCrossValidation();
        
        // Generate final report
        const report = await analyzer.generateReport();
        
        console.log('\n🎉 [COMPLETE] Comprehensive UI Analysis finished!');
        console.log(`📊 [SUMMARY] ${report.summary.totalIssues} total issues found (${report.summary.highSeverityIssues} high severity)`);
        console.log(`📷 [SUMMARY] ${report.summary.screenshotsTaken} screenshots taken for documentation`);
        
        return report;
        
    } catch (error) {
        console.error('💥 [ERROR] Analysis failed:', error);
    } finally {
        await analyzer.cleanup();
    }
}

// Run the analysis if called directly
if (require.main === module) {
    runComprehensiveAnalysis().catch(console.error);
}

module.exports = { ComprehensiveUIAnalyzer, runComprehensiveAnalysis };