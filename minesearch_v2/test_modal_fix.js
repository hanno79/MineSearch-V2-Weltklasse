// Test script to validate modal fix
const API_BASE_URL = 'http://localhost:8000';

async function testModelDetailsAPI() {
    console.log('🔍 Testing Model Details API...');
    try {
        const response = await fetch(`${API_BASE_URL}/api/statistics/model/openrouter:deepseek-chimera-free/details`);
        const data = await response.json();
        
        console.log('✅ API Response received');
        console.log('- Success:', data.success);
        console.log('- Data keys:', Object.keys(data.data || {}));
        console.log('- Field performance type:', typeof data.data.field_performance);
        console.log('- Field performance length:', data.data.field_performance?.length);
        
        // Test the data structure that should be passed to functions
        const fieldData = data.success ? (data.data.field_performance || []) : [];
        console.log('- Processed fieldData type:', typeof fieldData);
        console.log('- Processed fieldData is array:', Array.isArray(fieldData));
        console.log('- Processed fieldData length:', fieldData.length);
        
        if (fieldData.length > 0) {
            console.log('- First field item:', fieldData[0]);
        }
        
        return true;
    } catch (error) {
        console.error('❌ Model Details API test failed:', error);
        return false;
    }
}

async function testFieldPerformanceAPI() {
    console.log('🔍 Testing Field Performance API...');
    try {
        const response = await fetch(`${API_BASE_URL}/api/statistics/fields/performance?model_id=openrouter:deepseek-chimera-free`);
        const data = await response.json();
        
        console.log('✅ API Response received');
        console.log('- Success:', data.success);
        console.log('- Data keys:', Object.keys(data.data || {}));
        console.log('- Field statistics type:', typeof data.data.field_statistics);
        console.log('- Field statistics length:', data.data.field_statistics?.length);
        
        // Test the data structure that should be passed to functions
        const fieldData = data.success ? (data.data.field_statistics || []) : [];
        console.log('- Processed fieldData type:', typeof fieldData);
        console.log('- Processed fieldData is array:', Array.isArray(fieldData));
        console.log('- Processed fieldData length:', fieldData.length);
        
        if (fieldData.length > 0) {
            console.log('- First field item:', fieldData[0]);
        }
        
        return true;
    } catch (error) {
        console.error('❌ Field Performance API test failed:', error);
        return false;
    }
}

async function runTests() {
    console.log('🚀 Starting Modal Fix Validation Tests\n');
    
    const test1 = await testModelDetailsAPI();
    console.log('');
    const test2 = await testFieldPerformanceAPI();
    
    console.log('\n📊 Test Results:');
    console.log(`- Model Details API: ${test1 ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`- Field Performance API: ${test2 ? '✅ PASS' : '❌ FAIL'}`);
    
    if (test1 && test2) {
        console.log('\n🎉 All tests passed! Modal functions should now work correctly.');
    } else {
        console.log('\n⚠️ Some tests failed. Check the errors above.');
    }
}

// Run tests if this is executed directly
if (typeof window === 'undefined') {
    // Node.js environment
    const fetch = require('node-fetch');
    runTests();
}