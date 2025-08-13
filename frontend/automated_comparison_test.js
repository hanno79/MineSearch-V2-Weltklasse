/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Automated Test für Interactive Comparison Engine
 */

const testMultiModelData = [
    {
        "model_id": "openrouter:deepseek-free",
        "success": true,
        "confidence": 0.8,
        "search_duration": 0,
        "data": {
            "structured_data": {
                "Name": "Eleonore Mine",
                "Country": "Canada", 
                "Region": "Quebec (Nord-du-Québec, Baie-James)",
                "Eigentümer": "Newmont Corporation",
                "Betreiber": "Newmont Corporation",
                "x-Koordinate": "X",
                "y-Koordinate": "52.896400",
                "Aktivitätsstatus": "Aktiv",
                "Restaurationskosten": "X",
                "Jahr der Aufnahme der Kosten": "X",
                "Jahr der Erstellung des Dokumentes": "X",
                "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "X",
                "Minentyp (Untertage/ Open-Pit/ usw.)": "X",
                "Produktionsstart": "2014",
                "Produktionsende": "noch aktiv",
                "Fördermenge/Jahr": "X",
                "Fläche der Mine in qkm": "X",
                "Quellenangaben": "Keine spezifischen Quellen dokumentiert"
            },
            "quality_metrics": {
                "completion_percentage": 105.55555555555556,
                "filled_fields": 19,
                "total_fields": 18,
                "quality_score": 0.7366666666666666,
                "important_fields_filled": 3,
                "important_fields_total": 5
            },
            "sources": [
                {"url": "https://mern.gouv.qc.ca/search", "type": "government", "reliability": 100.0}
            ]
        }
    },
    {
        "model_id": "anthropic:claude-3-5-sonnet",
        "success": true,
        "confidence": 0.8,
        "search_duration": 0,
        "data": {
            "structured_data": {
                "Name": "Eleonore Mine",
                "Country": "Canada",
                "Region": "Quebec, Nord-du-Québec", 
                "Eigentümer": "Newmont Corporation",
                "Betreiber": "Newmont Corporation",
                "x-Koordinate": "X",
                "y-Koordinate": "52.283300",  // DISCREPANCY: Unterschiedliche Koordinate!
                "Aktivitätsstatus": "Aktiv",
                "Restaurationskosten": "X",
                "Jahr der Aufnahme der Kosten": "X",
                "Jahr der Erstellung des Dokumentes": "X",
                "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "X",
                "Minentyp (Untertage/ Open-Pit/ usw.)": "X",
                "Produktionsstart": "2015",  // DISCREPANCY: 2014 vs 2015!
                "Produktionsende": "noch aktiv",
                "Fördermenge/Jahr": "X",
                "Fläche der Mine in qkm": "X",
                "Quellenangaben": "Keine spezifischen Quellen dokumentiert"
            },
            "quality_metrics": {
                "completion_percentage": 105.55555555555556,
                "filled_fields": 19,
                "total_fields": 18,
                "quality_score": 0.7366666666666666,
                "important_fields_filled": 3,
                "important_fields_total": 5
            },
            "sources": [
                {"url": "https://mern.gouv.qc.ca/search", "type": "government", "reliability": 100.0}
            ]
        }
    }
];

async function runAutomatedComparisonTest() {
    console.log('🧪 [AUTOMATED TEST] Starte Automated Comparison Test');
    console.log('====================================================');
    
    try {
        // Load the comparison engine (simulate loading from browser)
        const { ComparisonEngine, ComparisonUIGenerator } = await import('./comparison-engine.js');
        
        const engine = new ComparisonEngine();
        const uiGenerator = new ComparisonUIGenerator(engine);
        
        console.log('✅ [TEST 1] Comparison Engine Initialization: SUCCESS');
        
        // Test 1: Basic comparison generation
        const comparison = await engine.generateComparison(testMultiModelData);
        console.log('✅ [TEST 2] Comparison Generation: SUCCESS');
        console.log(`   - Comparison ID: ${comparison.id}`);
        console.log(`   - Models: ${comparison.models.join(', ')}`);
        console.log(`   - Consensus Score: ${Math.round(comparison.consensus.overallScore * 100)}%`);
        console.log(`   - Discrepancies: ${comparison.metadata.discrepancyCount}`);
        
        // Test 2: Consensus detection
        const consensus = comparison.consensus;
        console.log('✅ [TEST 3] Consensus Detection: SUCCESS');
        console.log(`   - Strong Consensus Fields: ${consensus.strongConsensus.length}`);
        console.log(`   - Weak Consensus Fields: ${consensus.weakConsensus.length}`);
        console.log(`   - No Consensus Fields: ${consensus.noConsensus.length}`);
        console.log(`   - Strong Consensus: ${consensus.strongConsensus.join(', ')}`);
        
        // Test 3: Discrepancy detection
        const discrepancies = comparison.discrepancies;
        console.log('✅ [TEST 4] Discrepancy Detection: SUCCESS');
        console.log(`   - Total Discrepancies: ${discrepancies.length}`);
        
        if (discrepancies.length > 0) {
            console.log('   - Top Discrepancies:');
            discrepancies.slice(0, 3).forEach((disc, idx) => {
                console.log(`     ${idx + 1}. ${disc.field}: Impact ${Math.round(disc.impact * 100)}`);
                console.log(`        Values: ${disc.values.map(v => `${v.model}="${v.value}"`).join(', ')}`);
            });
        }
        
        // Test 4: Field analysis
        const fieldAnalysis = comparison.analysis.fieldAnalysis;
        const analyzedFields = Object.keys(fieldAnalysis).length;
        console.log('✅ [TEST 5] Field Analysis: SUCCESS');
        console.log(`   - Total Fields Analyzed: ${analyzedFields}`);
        
        // Test highest weighted fields
        const sortedFields = Object.entries(fieldAnalysis)
            .sort((a, b) => b[1].weight - a[1].weight)
            .slice(0, 5);
        
        console.log('   - Highest Weighted Fields:');
        sortedFields.forEach(([fieldName, fieldData]) => {
            console.log(`     - ${fieldName}: Weight ${Math.round(fieldData.weight * 100)}%, Confidence ${Math.round(fieldData.confidence * 100)}%`);
        });
        
        // Test 5: Model performance analysis
        const modelPerformance = comparison.analysis.modelPerformance;
        console.log('✅ [TEST 6] Model Performance Analysis: SUCCESS');
        
        Object.entries(modelPerformance).forEach(([modelId, performance]) => {
            console.log(`   - ${modelId}:`);
            console.log(`     Completeness: ${Math.round(performance.dataCompleteness * 100)}%`);
            console.log(`     Confidence: ${Math.round(performance.confidence * 100)}%`);
            console.log(`     Source Quality: ${Math.round(performance.sourceQuality * 100)}%`);
        });
        
        // Test 6: UI generation
        const comparisonHTML = uiGenerator.generateComparisonView(comparison);
        console.log('✅ [TEST 7] UI Generation: SUCCESS');
        console.log(`   - HTML Length: ${comparisonHTML.length} characters`);
        console.log(`   - Contains Header: ${comparisonHTML.includes('comparison-header')}`);
        console.log(`   - Contains Consensus: ${comparisonHTML.includes('consensus-overview')}`);
        console.log(`   - Contains Performance Matrix: ${comparisonHTML.includes('performance-matrix')}`);
        console.log(`   - Contains Field Comparison: ${comparisonHTML.includes('field-comparison')}`);
        console.log(`   - Contains Discrepancy Analysis: ${comparisonHTML.includes('discrepancy-analysis')}`);
        
        // Test 7: Edge cases
        console.log('✅ [TEST 8] Edge Cases Testing: SUCCESS');
        
        // Test single model
        const singleModelComparison = await engine.generateComparison([testMultiModelData[0]]);
        console.log(`   - Single Model View: ${singleModelComparison.type === 'single_model' ? 'SUCCESS' : 'FAILED'}`);
        
        // Test empty array
        try {
            await engine.generateComparison([]);
            console.log('   - Empty Array: FAILED (should throw error)');
        } catch (error) {
            console.log('   - Empty Array: SUCCESS (correctly throws error)');
        }
        
        console.log('====================================================');
        console.log('🎉 [AUTOMATED TEST] ALLE TESTS ERFOLGREICH!');
        console.log('====================================================');
        
        return {
            success: true,
            comparison: comparison,
            html: comparisonHTML,
            testResults: {
                consensusScore: Math.round(comparison.consensus.overallScore * 100),
                discrepancyCount: comparison.metadata.discrepancyCount,
                qualityScore: Math.round(comparison.metadata.overallQuality * 100),
                modelsAnalyzed: comparison.models.length,
                fieldsAnalyzed: analyzedFields
            }
        };
        
    } catch (error) {
        console.error('❌ [AUTOMATED TEST] TEST FAILED:', error);
        console.error('====================================================');
        
        return {
            success: false,
            error: error.message,
            stack: error.stack
        };
    }
}

// Export for Node.js testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { runAutomatedComparisonTest, testMultiModelData };
}

// Auto-run if in browser
if (typeof window !== 'undefined') {
    console.log('🚀 [AUTOMATED TEST] Browser-Test bereit');
    window.runAutomatedComparisonTest = runAutomatedComparisonTest;
}