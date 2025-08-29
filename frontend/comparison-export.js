/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Export Functions für Interactive Comparison Results
 */

// ============================================
// COMPARISON EXPORT SYSTEM
// ============================================

/**
 * MAIN EXPORT CLASS: Handles all comparison export functionality
 */
class ComparisonExporter {
    constructor() {
        this.exportHistory = [];
        console.log('📤 [EXPORT] ComparisonExporter initialisiert');
    }
    
    /**
     * MAIN EXPORT FUNCTION: Routes to specific export types
     */
    async exportComparison(comparisonId, format) {
        console.log(`📤 [EXPORT] Exporting comparison ${comparisonId} in format: ${format}`);
        
        const comparison = window.comparisonEngine.getComparison(comparisonId);
        if (!comparison) {
            throw new Error(`Comparison ${comparisonId} nicht gefunden`);
        }
        
        let result;
        
        switch (format) {
            case 'consensus':
                result = this.exportConsensusData(comparison);
                break;
            case 'detailed':
                result = this.exportDetailedAnalysis(comparison);
                break;
            case 'json':
                result = this.exportRawJSON(comparison);
                break;
            case 'report':
                result = this.generateReport(comparison);
                break;
            case 'csv':
                result = this.exportCSV(comparison);
                break;
            case 'excel':
                result = this.exportExcel(comparison);
                break;
            default:
                throw new Error(`Export format ${format} nicht unterstützt`);
        }
        
        // Track export
        this.exportHistory.push({
            comparisonId,
            format,
            timestamp: new Date().toISOString(),
            filename: result.filename
        });
        
        // Trigger download
        this.downloadFile(result.content, result.filename, result.mimeType);
        
        console.log(`✅ [EXPORT] Export ${format} erfolgreich: ${result.filename}`);
        return result;
    }
    
    /**
     * CONSENSUS EXPORT: Nur consensus-basierte Daten
     */
    exportConsensusData(comparison) {
        const consensusData = {
            metadata: {
                comparisonId: comparison.id,
                timestamp: comparison.timestamp,
                models: comparison.models,
                consensusScore: comparison.consensus.overallScore,
                exportTime: new Date().toISOString()
            },
            strongConsensus: {},
            weakConsensus: {},
            summary: {
                totalFields: comparison.metadata.totalFields,
                consensusFields: comparison.metadata.consensusFields,
                strongConsensusCount: comparison.consensus.strongConsensus.length,
                weakConsensusCount: comparison.consensus.weakConsensus.length
            }
        };
        
        // Strong consensus fields
        comparison.consensus.strongConsensus.forEach(fieldName => {
            const fieldData = comparison.consensus.fields[fieldName];
            consensusData.strongConsensus[fieldName] = {
                value: fieldData.value,
                agreeingModels: fieldData.models,
                strength: fieldData.strength,
                confidence: fieldData.confidence,
                weight: fieldData.weight
            };
        });
        
        // Weak consensus fields
        comparison.consensus.weakConsensus.forEach(fieldName => {
            const fieldData = comparison.consensus.fields[fieldName];
            consensusData.weakConsensus[fieldName] = {
                value: fieldData.value,
                agreeingModels: fieldData.models,
                strength: fieldData.strength,
                confidence: fieldData.confidence,
                weight: fieldData.weight
            };
        });
        
        const content = JSON.stringify(consensusData, null, 2);
        const filename = `consensus_data_${comparison.id}_${this.getTimestamp()}.json`;
        
        return {
            content,
            filename,
            mimeType: 'application/json'
        };
    }
    
    /**
     * DETAILED ANALYSIS EXPORT: Komplette Analyse mit allen Details
     */
    exportDetailedAnalysis(comparison) {
        const detailedData = {
            metadata: {
                comparisonId: comparison.id,
                timestamp: comparison.timestamp,
                models: comparison.models,
                totalFields: comparison.metadata.totalFields,
                consensusFields: comparison.metadata.consensusFields,
                discrepancyCount: comparison.metadata.discrepancyCount,
                overallQuality: comparison.metadata.overallQuality,
                exportTime: new Date().toISOString()
            },
            consensus: {
                overallScore: comparison.consensus.overallScore,
                strongConsensus: comparison.consensus.strongConsensus,
                weakConsensus: comparison.consensus.weakConsensus,
                noConsensus: comparison.consensus.noConsensus,
                fields: comparison.consensus.fields
            },
            discrepancies: comparison.discrepancies.map(disc => ({
                field: disc.field,
                type: disc.type,
                severity: disc.severity,
                impact: disc.impact,
                weight: disc.weight,
                conflictingValues: disc.values.map(v => ({
                    model: v.model,
                    value: v.value,
                    confidence: v.confidence
                }))
            })),
            modelPerformance: Object.entries(comparison.analysis.modelPerformance).map(([modelId, performance]) => ({
                model: modelId,
                dataCompleteness: performance.dataCompleteness,
                confidence: performance.confidence,
                sourceQuality: performance.sourceQuality,
                responseTime: performance.responseTime,
                overallScore: (performance.dataCompleteness + performance.confidence + performance.sourceQuality) / 3
            })),
            fieldAnalysis: Object.entries(comparison.analysis.fieldAnalysis).map(([fieldName, fieldData]) => ({
                field: fieldName,
                weight: fieldData.weight,
                confidence: fieldData.confidence,
                valueCount: fieldData.values.length,
                hasConsensus: comparison.consensus.fields[fieldName] ? true : false,
                hasDiscrepancy: comparison.discrepancies.some(d => d.field === fieldName),
                values: fieldData.values
            }))
        };
        
        const content = JSON.stringify(detailedData, null, 2);
        const filename = `detailed_analysis_${comparison.id}_${this.getTimestamp()}.json`;
        
        return {
            content,
            filename,
            mimeType: 'application/json'
        };
    }
    
    /**
     * RAW JSON EXPORT: Komplette raw comparison data
     */
    exportRawJSON(comparison) {
        const content = JSON.stringify(comparison, null, 2);
        const filename = `raw_comparison_${comparison.id}_${this.getTimestamp()}.json`;
        
        return {
            content,
            filename,
            mimeType: 'application/json'
        };
    }
    
    /**
     * REPORT GENERATION: Human-readable HTML report
     */
    generateReport(comparison) {
        const reportHTML = `
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Comparison Report - ${comparison.id}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #2563eb; color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .metric-card { background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 8px; padding: 20px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2563eb; }
        .metric-label { color: #64748b; font-weight: 600; margin-top: 8px; }
        .section { margin: 40px 0; }
        .section h2 { border-bottom: 3px solid #2563eb; padding-bottom: 10px; }
        .consensus-item { background: #dcfce7; border-left: 4px solid #16a34a; padding: 15px; margin: 10px 0; }
        .discrepancy-item { background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 10px 0; }
        .model-performance { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .model-card { background: #eff6ff; border: 2px solid #bfdbfe; border-radius: 8px; padding: 20px; }
        .progress-bar { background: #e5e7eb; height: 20px; border-radius: 10px; overflow: hidden; margin: 8px 0; }
        .progress-fill { background: #2563eb; height: 100%; transition: width 0.3s; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #d1d5db; padding: 12px; text-align: left; }
        th { background: #f3f4f6; font-weight: 600; }
        .footer { margin-top: 50px; padding: 20px; background: #f8fafc; border-radius: 8px; text-align: center; color: #64748b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Model Comparison Report</h1>
        <p>Comparison ID: ${comparison.id}</p>
        <p>Generated: ${new Date().toLocaleString()}</p>
    </div>
    
    <div class="summary-grid">
        <div class="metric-card">
            <div class="metric-value">${Math.round(comparison.consensus.overallScore * 100)}%</div>
            <div class="metric-label">Konsens-Score</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${Math.round(comparison.metadata.overallQuality * 100)}%</div>
            <div class="metric-label">Datenqualität</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${comparison.metadata.consensusFields}</div>
            <div class="metric-label">Konsens-Felder</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${comparison.metadata.discrepancyCount}</div>
            <div class="metric-label">Diskrepanzen</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📊 Analysierte Modelle</h2>
        <div class="model-performance">
            ${comparison.models.map(modelId => {
                const performance = comparison.analysis.modelPerformance[modelId];
                const overall = Math.round((performance.dataCompleteness + performance.confidence + performance.sourceQuality) / 3 * 100);
                return `
                    <div class="model-card">
                        <h3>${modelId}</h3>
                        <div>
                            <strong>Overall Score: ${overall}%</strong>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${overall}%"></div>
                            </div>
                        </div>
                        <div>
                            Datenvollständigkeit: ${Math.round(performance.dataCompleteness * 100)}%
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${Math.round(performance.dataCompleteness * 100)}%"></div>
                            </div>
                        </div>
                        <div>
                            Vertrauen: ${Math.round(performance.confidence * 100)}%
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${Math.round(performance.confidence * 100)}%"></div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    </div>
    
    <div class="section">
        <h2>✅ Starker Konsens (${comparison.consensus.strongConsensus.length} fields)</h2>
        ${comparison.consensus.strongConsensus.map(fieldName => {
            const fieldData = comparison.consensus.fields[fieldName];
            return `
                <div class="consensus-item">
                    <strong>${fieldName}:</strong> "${fieldData.value}"<br>
                    <small>Agreeing models: ${fieldData.models.join(', ')} | Strength: ${Math.round(fieldData.strength * 100)}%</small>
                </div>
            `;
        }).join('')}
    </div>
    
    ${comparison.discrepancies.length > 0 ? `
    <div class="section">
        <h2>⚠️ Signifikante Diskrepanzen (${comparison.discrepancies.length})</h2>
        ${comparison.discrepancies.slice(0, 10).map(disc => `
            <div class="discrepancy-item">
                <strong>${disc.field}</strong> (Impact: ${Math.round(disc.impact * 100)})<br>
                ${disc.values.map(v => `${v.model}: "${v.value}"`).join(' | ')}
            </div>
        `).join('')}
    </div>
    ` : ''}
    
    <div class="footer">
        <p>🚀 Generated by MineSearch 2.0 Interactive Comparison Engine</p>
        <p>Report ID: ${comparison.id} | Export Time: ${new Date().toISOString()}</p>
    </div>
</body>
</html>`;
        
        const filename = `comparison_report_${comparison.id}_${this.getTimestamp()}.html`;
        
        return {
            content: reportHTML,
            filename,
            mimeType: 'text/html'
        };
    }
    
    /**
     * CSV EXPORT: Field-by-field comparison in CSV format
     */
    exportCSV(comparison) {
        const csvRows = [];
        
        // Header row
        const headers = ['Field', 'Weight', 'Consensus', ...comparison.models, 'Status'];
        csvRows.push(headers.join(','));
        
        // Field rows
        Object.entries(comparison.analysis.fieldAnalysis).forEach(([fieldName, fieldData]) => {
            const hasConsensus = comparison.consensus.fields[fieldName];
            const hasDiscrepancy = comparison.discrepancies.some(d => d.field === fieldName);
            
            const row = [
                `"${fieldName}"`,
                fieldData.weight.toFixed(2),
                hasConsensus ? `"${hasConsensus.value}"` : '',
            ];
            
            // Add values for each model
            comparison.models.forEach(modelId => {
                const modelValue = fieldData.values.find(v => v.model === modelId);
                row.push(modelValue ? `"${modelValue.value}"` : '');
            });
            
            // Status
            let status = 'No Data';
            if (hasConsensus) status = 'Consensus';
            else if (hasDiscrepancy) status = 'Discrepancy';
            row.push(`"${status}"`);
            
            csvRows.push(row.join(','));
        });
        
        const content = csvRows.join('\n');
        const filename = `comparison_data_${comparison.id}_${this.getTimestamp()}.csv`;
        
        return {
            content,
            filename,
            mimeType: 'text/csv'
        };
    }
    
    /**
     * EXCEL EXPORT: Rich Excel format with multiple sheets
     */
    exportExcel(comparison) {
        // For now, export as enhanced CSV (later can be upgraded to real Excel)
        const worksheets = {
            summary: this.generateSummarySheet(comparison),
            consensus: this.generateConsensusSheet(comparison),
            discrepancies: this.generateDiscrepancySheet(comparison),
            performance: this.generatePerformanceSheet(comparison)
        };
        
        let excelContent = '';
        Object.entries(worksheets).forEach(([sheetName, data]) => {
            excelContent += `=== ${sheetName.toUpperCase()} ===\n`;
            excelContent += data;
            excelContent += '\n\n';
        });
        
        const filename = `comparison_excel_${comparison.id}_${this.getTimestamp()}.txt`;
        
        return {
            content: excelContent,
            filename,
            mimeType: 'text/plain'
        };
    }
    
    /**
     * HELPER METHODS
     */
    generateSummarySheet(comparison) {
        return `Comparison Summary
Comparison ID,${comparison.id}
Timestamp,${comparison.timestamp}
Models,${comparison.models.join('; ')}
Konsens-Score,${Math.round(comparison.consensus.overallScore * 100)}%
Datenqualität,${Math.round(comparison.metadata.overallQuality * 100)}%
Total Fields,${comparison.metadata.totalFields}
Konsens-Felder,${comparison.metadata.consensusFields}
Diskrepanzen,${comparison.metadata.discrepancyCount}`;
    }
    
    generateConsensusSheet(comparison) {
        const rows = ['Field,Value,Models,Strength,Type'];
        
        comparison.consensus.strongConsensus.forEach(fieldName => {
            const fieldData = comparison.consensus.fields[fieldName];
            rows.push(`"${fieldName}","${fieldData.value}","${fieldData.models.join('; ')}",${Math.round(fieldData.strength * 100)}%,Strong`);
        });
        
        comparison.consensus.weakConsensus.forEach(fieldName => {
            const fieldData = comparison.consensus.fields[fieldName];
            rows.push(`"${fieldName}","${fieldData.value}","${fieldData.models.join('; ')}",${Math.round(fieldData.strength * 100)}%,Weak`);
        });
        
        return rows.join('\n');
    }
    
    generateDiscrepancySheet(comparison) {
        const rows = ['Field,Impact,Severity,Type,Values'];
        
        comparison.discrepancies.forEach(disc => {
            const values = disc.values.map(v => `${v.model}="${v.value}"`).join('; ');
            rows.push(`"${disc.field}",${Math.round(disc.impact * 100)},${disc.severity.toFixed(2)},${disc.type},"${values}"`);
        });
        
        return rows.join('\n');
    }
    
    generatePerformanceSheet(comparison) {
        const rows = ['Model,Datenvollständigkeit,Vertrauen,Source Quality,Overall Score'];
        
        Object.entries(comparison.analysis.modelPerformance).forEach(([modelId, performance]) => {
            const overall = Math.round((performance.dataCompleteness + performance.confidence + performance.sourceQuality) / 3 * 100);
            rows.push(`"${modelId}",${Math.round(performance.dataCompleteness * 100)}%,${Math.round(performance.confidence * 100)}%,${Math.round(performance.sourceQuality * 100)}%,${overall}%`);
        });
        
        return rows.join('\n');
    }
    
    /**
     * FILE DOWNLOAD: Triggers browser download
     */
    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Cleanup
        setTimeout(() => URL.revokeObjectURL(url), 100);
    }
    
    /**
     * TIMESTAMP: Generates timestamp for filenames
     */
    getTimestamp() {
        return new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] + '_' + 
               new Date().toTimeString().split(' ')[0].replace(/:/g, '');
    }
    
    /**
     * EXPORT HISTORY: Returns export history
     */
    getExportHistory() {
        return this.exportHistory;
    }
}

// ============================================
// GLOBAL INITIALIZATION
// ============================================

// Create global exporter instance
window.comparisonExporter = new ComparisonExporter();

// Export functions for UI
window.exportComparison = (comparisonId, format) => {
    return window.comparisonExporter.exportComparison(comparisonId, format);
};

window.showAllDiscrepancies = (comparisonId) => {
    console.log(`📋 [DISCREPANCIES] Showing all discrepancies for ${comparisonId}`);
    
    const comparison = window.comparisonEngine.getComparison(comparisonId);
    if (!comparison) {
        alert('Comparison nicht gefunden!');
        return;
    }
    
    // Export detailed discrepancy analysis
    const discrepancyExport = window.comparisonExporter.exportDetailedAnalysis(comparison);
    
    // Show modal with all discrepancies
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background: rgba(0,0,0,0.8); z-index: 10000; 
        display: flex; align-items: center; justify-content: center;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: white; border-radius: 12px; padding: 30px; 
        max-width: 80%; max-height: 80%; overflow-y: auto;
        box-shadow: 0 25px 50px rgba(0,0,0,0.25);
    `;
    
    content.innerHTML = `
        <h2>⚠️ All Discrepancies - ${comparisonId}</h2>
        <p><strong>Total Discrepancies:</strong> ${comparison.discrepancies.length}</p>
        ${comparison.discrepancies.map((disc, idx) => `
            <div style="border: 1px solid #e5e7eb; margin: 10px 0; padding: 15px; border-radius: 8px;">
                <h4>${idx + 1}. ${disc.field}</h4>
                <p><strong>Impact:</strong> ${Math.round(disc.impact * 100)} | <strong>Severity:</strong> ${disc.severity.toFixed(2)}</p>
                <div style="background: #f8fafc; padding: 10px; border-radius: 4px;">
                    ${disc.values.map(v => `<div><strong>${v.model}:</strong> "${v.value}" (${Math.round(v.confidence * 100)}%)</div>`).join('')}
                </div>
            </div>
        `).join('')}
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="this.closest('.modal').remove()" style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                Schließen
            </button>
            <button onclick="window.exportComparison('${comparisonId}', 'detailed')" style="background: #16a34a; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-left: 10px;">
                Details exportieren
            </button>
        </div>
    `;
    
    modal.className = 'modal';
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
};

console.log('📤 [EXPORT] Comparison Export System geladen');