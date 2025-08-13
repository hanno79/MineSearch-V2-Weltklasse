/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Advanced Discrepancy Highlighting System für Interactive Comparisons
 */

// ============================================
// DISCREPANCY HIGHLIGHTING SYSTEM
// ============================================

/**
 * MAIN CLASS: Advanced discrepancy visualization and interaction
 */
class DiscrepancyHighlighter {
    constructor() {
        this.activeHighlights = new Map();
        this.highlightStyles = this.initializeHighlightStyles();
        this.interactionHandlers = new Map();
        
        console.log('⚠️ [DISCREPANCY] DiscrepancyHighlighter initialisiert');
    }
    
    /**
     * HIGHLIGHT STYLES: Definiert visuelle Stile für verschiedene Discrepancy-Types
     */
    initializeHighlightStyles() {
        return {
            severity: {
                critical: {
                    background: 'linear-gradient(135deg, #fecaca, #f87171)',
                    border: '3px solid #dc2626',
                    boxShadow: '0 0 20px rgba(220, 38, 38, 0.4)',
                    color: '#991b1b',
                    animation: 'pulse-critical 2s infinite'
                },
                high: {
                    background: 'linear-gradient(135deg, #fed7aa, #fdba74)',
                    border: '2px solid #ea580c',
                    boxShadow: '0 0 15px rgba(234, 88, 12, 0.3)',
                    color: '#9a3412',
                    animation: 'pulse-high 3s infinite'
                },
                medium: {
                    background: 'linear-gradient(135deg, #fef3c7, #fde68a)',
                    border: '2px solid #f59e0b',
                    boxShadow: '0 0 10px rgba(245, 158, 11, 0.2)',
                    color: '#92400e',
                    animation: 'pulse-medium 4s infinite'
                },
                low: {
                    background: 'linear-gradient(135deg, #e0f2fe, #b3e5fc)',
                    border: '1px solid #0284c7',
                    boxShadow: '0 0 5px rgba(2, 132, 199, 0.15)',
                    color: '#075985',
                    animation: 'none'
                }
            },
            type: {
                value_conflict: {
                    borderStyle: 'dashed',
                    pattern: 'repeating-linear-gradient(45deg, transparent, transparent 5px, rgba(220, 38, 38, 0.1) 5px, rgba(220, 38, 38, 0.1) 10px)'
                },
                missing_data: {
                    borderStyle: 'dotted',
                    pattern: 'repeating-linear-gradient(90deg, transparent, transparent 3px, rgba(156, 163, 175, 0.3) 3px, rgba(156, 163, 175, 0.3) 6px)'
                },
                format_mismatch: {
                    borderStyle: 'double',
                    pattern: 'repeating-conic-gradient(from 0deg, transparent 0deg, rgba(234, 88, 12, 0.1) 90deg, transparent 180deg)'
                }
            }
        };
    }
    
    /**
     * MAIN HIGHLIGHT FUNCTION: Highlights discrepancies in comparison view
     */
    highlightDiscrepancies(comparison, containerElement) {
        console.log(`⚠️ [DISCREPANCY] Highlighting ${comparison.discrepancies.length} discrepancies`);
        
        // Clear previous highlights
        this.clearHighlights(containerElement);
        
        // Add CSS animations if not present
        this.injectHighlightCSS();
        
        // Process each discrepancy
        comparison.discrepancies.forEach((discrepancy, index) => {
            this.highlightSingleDiscrepancy(discrepancy, index, containerElement, comparison);
        });
        
        // Add interactive controls
        this.addDiscrepancyControls(containerElement, comparison);
        
        console.log(`✅ [DISCREPANCY] ${comparison.discrepancies.length} discrepancies highlighted`);
    }
    
    /**
     * SINGLE DISCREPANCY: Highlights einzelne Diskrepanz
     */
    highlightSingleDiscrepancy(discrepancy, index, containerElement, comparison) {
        const fieldName = discrepancy.field;
        const severity = this.calculateSeverityClass(discrepancy.severity);
        
        // Find field elements in the comparison view
        const fieldElements = containerElement.querySelectorAll(`[data-field="${fieldName}"], .field-name:contains("${fieldName}")`);
        
        if (fieldElements.length === 0) {
            console.warn(`⚠️ [DISCREPANCY] Field elements not found for: ${fieldName}`);
            return;
        }
        
        fieldElements.forEach(element => {
            this.applyDiscrepancyHighlight(element, discrepancy, severity, index);
        });
        
        // Highlight conflicting values
        this.highlightConflictingValues(discrepancy, containerElement, severity);
    }
    
    /**
     * APPLY HIGHLIGHT: Wendet Highlight-Styles auf Element an
     */
    applyDiscrepancyHighlight(element, discrepancy, severity, index) {
        const highlightId = `discrepancy-${index}`;
        
        // Store original styles
        if (!element.dataset.originalStyles) {
            element.dataset.originalStyles = element.style.cssText;
        }
        
        // Apply highlight styles
        const styles = this.highlightStyles.severity[severity];
        Object.assign(element.style, {
            background: styles.background,
            border: styles.border,
            boxShadow: styles.boxShadow,
            color: styles.color,
            animation: styles.animation,
            position: 'relative',
            zIndex: '10',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
        });
        
        // Add discrepancy indicator
        this.addDiscrepancyIndicator(element, discrepancy, highlightId);
        
        // Add click handler for detailed view
        const clickHandler = () => this.showDiscrepancyDetails(discrepancy, element);
        element.addEventListener('click', clickHandler);
        
        // Store for cleanup
        this.activeHighlights.set(highlightId, {
            element,
            discrepancy,
            clickHandler,
            originalStyles: element.dataset.originalStyles
        });
        
        // Add hover effects
        this.addHoverEffects(element, discrepancy);
    }
    
    /**
     * CONFLICTING VALUES: Highlights conflicting values within field
     */
    highlightConflictingValues(discrepancy, containerElement, severity) {
        discrepancy.values.forEach((valueData, valueIndex) => {
            const modelElements = containerElement.querySelectorAll(`[data-model="${valueData.model}"]`);
            
            modelElements.forEach(modelElement => {
                const valueElement = modelElement.querySelector('.field-value, .value-text');
                if (valueElement && valueElement.textContent.includes(valueData.value)) {
                    
                    // Apply value-specific highlight
                    valueElement.style.cssText += `
                        background: ${this.generateValueConflictGradient(valueIndex, discrepancy.values.length)};
                        border-radius: 4px;
                        padding: 2px 4px;
                        margin: 1px;
                        position: relative;
                        display: inline-block;
                    `;
                    
                    // Add confidence indicator
                    this.addConfidenceIndicator(valueElement, valueData);
                }
            });
        });
    }
    
    /**
     * VALUE CONFLICT GRADIENT: Generiert unique gradients für conflicting values
     */
    generateValueConflictGradient(index, total) {
        const colors = [
            ['#fecaca', '#f87171'], // Red
            ['#fed7aa', '#fdba74'], // Orange  
            ['#fef3c7', '#fde68a'], // Yellow
            ['#dcfce7', '#86efac'], // Green
            ['#dbeafe', '#93c5fd'], // Blue
            ['#e9d5ff', '#c084fc']  // Purple
        ];
        
        const colorPair = colors[index % colors.length];
        return `linear-gradient(135deg, ${colorPair[0]}, ${colorPair[1]})`;
    }
    
    /**
     * DISCREPANCY INDICATOR: Fügt visuellen Indikator hinzu
     */
    addDiscrepancyIndicator(element, discrepancy, highlightId) {
        const indicator = document.createElement('div');
        indicator.className = `discrepancy-indicator ${highlightId}`;
        indicator.innerHTML = `
            <div class="discrepancy-badge" style="
                position: absolute;
                top: -8px;
                right: -8px;
                background: #dc2626;
                color: white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
                z-index: 1000;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                animation: bounce 2s infinite;
            ">⚠</div>
            
            <div class="discrepancy-tooltip" style="
                position: absolute;
                top: -40px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                white-space: nowrap;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.3s;
                z-index: 1001;
            ">
                ${discrepancy.field}: ${discrepancy.values.length} conflicting values
            </div>
        `;
        
        // Make indicator relative to element
        if (element.style.position === '' || element.style.position === 'static') {
            element.style.position = 'relative';
        }
        
        element.appendChild(indicator);
    }
    
    /**
     * CONFIDENCE INDICATOR: Zeigt Confidence-Level für Values
     */
    addConfidenceIndicator(valueElement, valueData) {
        const confidence = Math.round(valueData.confidence * 100);
        const confidenceBar = document.createElement('div');
        confidenceBar.className = 'confidence-indicator';
        confidenceBar.style.cssText = `
            position: absolute;
            bottom: -2px;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(to right, 
                ${confidence < 50 ? '#dc2626' : confidence < 75 ? '#f59e0b' : '#16a34a'} ${confidence}%, 
                #e5e7eb ${confidence}%
            );
            border-radius: 0 0 2px 2px;
        `;
        
        // Add confidence tooltip
        confidenceBar.title = `Confidence: ${confidence}% (${valueData.model})`;
        
        valueElement.style.position = 'relative';
        valueElement.appendChild(confidenceBar);
    }
    
    /**
     * HOVER EFFECTS: Erweiterte Hover-Interaktionen
     */
    addHoverEffects(element, discrepancy) {
        const mouseEnterHandler = (e) => {
            // Show tooltip
            const tooltip = element.querySelector('.discrepancy-tooltip');
            if (tooltip) {
                tooltip.style.opacity = '1';
            }
            
            // Enhance highlight
            element.style.transform = 'scale(1.02)';
            element.style.zIndex = '100';
            
            // Show related conflicts
            this.highlightRelatedConflicts(discrepancy);
        };
        
        const mouseLeaveHandler = (e) => {
            // Hide tooltip
            const tooltip = element.querySelector('.discrepancy-tooltip');
            if (tooltip) {
                tooltip.style.opacity = '0';
            }
            
            // Reset transform
            element.style.transform = 'scale(1)';
            element.style.zIndex = '10';
            
            // Hide related conflicts
            this.hideRelatedConflicts();
        };
        
        element.addEventListener('mouseenter', mouseEnterHandler);
        element.addEventListener('mouseleave', mouseLeaveHandler);
        
        // Store handlers for cleanup
        const highlightId = `discrepancy-hover-${Date.now()}`;
        this.interactionHandlers.set(highlightId, {
            element,
            mouseEnterHandler,
            mouseLeaveHandler
        });
    }
    
    /**
     * RELATED CONFLICTS: Zeigt related conflicts
     */
    highlightRelatedConflicts(discrepancy) {
        // Implementation for showing related conflicts across the comparison
        document.querySelectorAll(`[data-field="${discrepancy.field}"]`).forEach(el => {
            if (!el.classList.contains('discrepancy-highlight')) {
                el.style.outline = '2px dashed rgba(220, 38, 38, 0.5)';
            }
        });
    }
    
    hideRelatedConflicts() {
        document.querySelectorAll('[style*="outline"]').forEach(el => {
            el.style.outline = '';
        });
    }
    
    /**
     * DISCREPANCY DETAILS: Zeigt detaillierte Discrepancy-Informationen
     */
    showDiscrepancyDetails(discrepancy, triggerElement) {
        console.log(`📋 [DISCREPANCY] Showing details for: ${discrepancy.field}`);
        
        const modal = document.createElement('div');
        modal.className = 'discrepancy-detail-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
            animation: slideIn 0.3s ease;
        `;
        
        modalContent.innerHTML = `
            <div style="text-align: center; margin-bottom: 25px;">
                <h2 style="color: #dc2626; margin-bottom: 10px;">⚠️ Discrepancy Analysis</h2>
                <h3 style="color: #374151;">${discrepancy.field}</h3>
            </div>
            
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h4>📊 Impact Analysis</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 15px;">
                    <div style="text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #dc2626;">${Math.round(discrepancy.impact * 100)}</div>
                        <div style="font-size: 12px; color: #6b7280;">Impact Score</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #ea580c;">${discrepancy.severity.toFixed(2)}</div>
                        <div style="font-size: 12px; color: #6b7280;">Severity</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #0891b2;">${discrepancy.values.length}</div>
                        <div style="font-size: 12px; color: #6b7280;">Conflicts</div>
                    </div>
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4>🔍 Conflicting Values</h4>
                ${discrepancy.values.map((value, idx) => `
                    <div style="
                        background: ${this.generateValueConflictGradient(idx, discrepancy.values.length)};
                        border: 1px solid #e5e7eb;
                        border-radius: 8px;
                        padding: 12px;
                        margin: 8px 0;
                    ">
                        <div style="font-weight: bold; margin-bottom: 5px;">${value.model}</div>
                        <div style="font-family: monospace; background: rgba(255,255,255,0.7); padding: 4px 8px; border-radius: 4px; margin: 5px 0;">"${value.value}"</div>
                        <div style="font-size: 12px; color: #6b7280;">
                            Confidence: ${Math.round(value.confidence * 100)}%
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <div style="margin-bottom: 25px;">
                <h4>💡 Resolution Suggestions</h4>
                <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px;">
                    ${this.generateResolutionSuggestions(discrepancy)}
                </div>
            </div>
            
            <div style="text-align: center;">
                <button onclick="this.closest('.discrepancy-detail-modal').remove()" style="
                    background: #2563eb;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    margin-right: 10px;
                ">Close</button>
                <button onclick="window.exportDiscrepancyReport && window.exportDiscrepancyReport('${discrepancy.field}')" style="
                    background: #16a34a;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                ">Export Report</button>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    /**
     * RESOLUTION SUGGESTIONS: Generiert Lösungsvorschläge
     */
    generateResolutionSuggestions(discrepancy) {
        const suggestions = [];
        
        if (discrepancy.values.length === 2) {
            suggestions.push('💬 Consider cross-referencing with additional sources to break the tie');
        }
        
        if (discrepancy.field.includes('Koordinate') || discrepancy.field.includes('coordinate')) {
            suggestions.push('🗺️ Use geographical validation services to verify coordinates');
        }
        
        if (discrepancy.field.includes('kosten') || discrepancy.field.includes('cost')) {
            suggestions.push('💰 Check if values are in different currencies or time periods');
        }
        
        if (discrepancy.field.includes('Jahr') || discrepancy.field.includes('year')) {
            suggestions.push('📅 Verify if dates refer to different milestones (planning vs. actual)');
        }
        
        const highestConfidence = Math.max(...discrepancy.values.map(v => v.confidence));
        const highestConfidenceModel = discrepancy.values.find(v => v.confidence === highestConfidence);
        if (highestConfidenceModel) {
            suggestions.push(`🎯 Consider prioritizing value from ${highestConfidenceModel.model} (highest confidence: ${Math.round(highestConfidence * 100)}%)`);
        }
        
        if (suggestions.length === 0) {
            suggestions.push('🔍 Manual review recommended to resolve this discrepancy');
        }
        
        return suggestions.map(s => `<div style="margin: 5px 0;">${s}</div>`).join('');
    }
    
    /**
     * DISCREPANCY CONTROLS: Fügt interaktive Steuerung hinzu
     */
    addDiscrepancyControls(containerElement, comparison) {
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'discrepancy-controls';
        controlsContainer.style.cssText = `
            position: sticky;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        `;
        
        controlsContainer.innerHTML = `
            <h4 style="margin: 0 0 15px 0; color: #374151;">⚠️ Discrepancy Controls</h4>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <button onclick="window.discrepancyHighlighter.toggleHighlights()" style="
                    background: #6366f1; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
                ">Toggle Highlights</button>
                <button onclick="window.discrepancyHighlighter.showAllDiscrepancies()" style="
                    background: #dc2626; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
                ">Show All Details</button>
                <button onclick="window.discrepancyHighlighter.exportDiscrepancyReport()" style="
                    background: #16a34a; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
                ">Export Report</button>
                <button onclick="window.discrepancyHighlighter.clearHighlights()" style="
                    background: #6b7280; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
                ">Clear Highlights</button>
            </div>
            <div style="margin-top: 15px; font-size: 11px; color: #6b7280;">
                Found: ${comparison.discrepancies.length} discrepancies
            </div>
        `;
        
        containerElement.insertBefore(controlsContainer, containerElement.firstChild);
    }
    
    /**
     * UTILITY METHODS
     */
    calculateSeverityClass(severity) {
        if (severity >= 0.8) return 'critical';
        if (severity >= 0.6) return 'high';
        if (severity >= 0.4) return 'medium';
        return 'low';
    }
    
    injectHighlightCSS() {
        if (document.getElementById('discrepancy-highlight-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'discrepancy-highlight-styles';
        style.textContent = `
            @keyframes pulse-critical {
                0%, 100% { box-shadow: 0 0 20px rgba(220, 38, 38, 0.4); }
                50% { box-shadow: 0 0 30px rgba(220, 38, 38, 0.8); }
            }
            @keyframes pulse-high {
                0%, 100% { box-shadow: 0 0 15px rgba(234, 88, 12, 0.3); }
                50% { box-shadow: 0 0 25px rgba(234, 88, 12, 0.6); }
            }
            @keyframes pulse-medium {
                0%, 100% { box-shadow: 0 0 10px rgba(245, 158, 11, 0.2); }
                50% { box-shadow: 0 0 15px rgba(245, 158, 11, 0.4); }
            }
            @keyframes bounce {
                0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
                40%, 43% { transform: translate3d(0, -6px, 0); }
                70% { transform: translate3d(0, -3px, 0); }
                90% { transform: translate3d(0, -1px, 0); }
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideIn {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    toggleHighlights() {
        const highlights = document.querySelectorAll('.discrepancy-indicator');
        highlights.forEach(highlight => {
            highlight.style.display = highlight.style.display === 'none' ? '' : 'none';
        });
    }
    
    showAllDiscrepancies() {
        // Show master discrepancy overview
        console.log('📋 [DISCREPANCY] Showing all discrepancies overview');
        // Implementation would show comprehensive overview
    }
    
    exportDiscrepancyReport() {
        console.log('📤 [DISCREPANCY] Exporting discrepancy report');
        // Implementation would export detailed discrepancy report
    }
    
    clearHighlights(containerElement = document) {
        console.log('🧹 [DISCREPANCY] Clearing all highlights');
        
        // Restore original styles
        this.activeHighlights.forEach((highlight, id) => {
            if (highlight.element) {
                highlight.element.style.cssText = highlight.originalStyles || '';
                highlight.element.removeEventListener('click', highlight.clickHandler);
            }
        });
        
        // Clear interaction handlers
        this.interactionHandlers.forEach((handler, id) => {
            if (handler.element) {
                handler.element.removeEventListener('mouseenter', handler.mouseEnterHandler);
                handler.element.removeEventListener('mouseleave', handler.mouseLeaveHandler);
            }
        });
        
        // Remove indicators
        containerElement.querySelectorAll('.discrepancy-indicator, .discrepancy-controls').forEach(el => {
            el.remove();
        });
        
        // Clear maps
        this.activeHighlights.clear();
        this.interactionHandlers.clear();
    }
}

// ============================================
// GLOBAL INITIALIZATION
// ============================================

// Create global instance
window.discrepancyHighlighter = new DiscrepancyHighlighter();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DiscrepancyHighlighter;
}

console.log('⚠️ [DISCREPANCY] Advanced Discrepancy Highlighting System geladen');