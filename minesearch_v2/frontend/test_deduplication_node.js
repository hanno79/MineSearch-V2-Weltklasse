/*
Author: rahn
Datum: 28.07.2025
Version: 1.0
Beschreibung: Node.js Test für Deduplication Engine
*/

const fs = require('fs');
const path = require('path');

// Read the deduplication engine file
const enginePath = path.join(__dirname, 'js', 'deduplication-engine.js');
let engineCode = fs.readFileSync(enginePath, 'utf8');

// Remove browser-specific code for Node.js testing
engineCode = engineCode.replace(/window\./g, 'global.');
engineCode = engineCode.replace(/document\.addEventListener.*\{[\s\S]*?\}\);/g, '');
engineCode = engineCode.replace(/if \(typeof module.*[\s\S]*?\}/g, '');

// Create mock global objects for Node.js
global.document = {
    addEventListener: () => {},
    readyState: 'complete'
};
global.window = global;

// Execute the engine code
try {
    eval(engineCode);
} catch (error) {
    console.error('Error evaluating engine code:', error.message);
    console.log('Engine code length:', engineCode.length);
    // Let's try a different approach - just test the basic functionality
}

// Test the deduplication engine
console.log('🧪 Testing Deduplication Engine...\n');

const engine = new DeduplicationEngine();

// Test 1: Basic country deduplication
console.log('Test 1: Country Deduplication');
const countryTest = "Canada / Canada / United States / Canada / USA / Kanada";
const countryResult = engine.deduplicateValues(countryTest, 'country');
console.log(`Input:  ${countryTest}`);
console.log(`Output: ${countryResult}`);
console.log(`✅ Expected: Canada and USA consolidated\n`);

// Test 2: Mining status deduplication
console.log('Test 2: Mining Status Deduplication');
const statusTest = "Aktiv / Active / Operating / Geplant / Planned / Aktiv / Betrieb";
const statusResult = engine.deduplicateValues(statusTest, 'status');
console.log(`Input:  ${statusTest}`);
console.log(`Output: ${statusResult}`);
console.log(`✅ Expected: Aktiv and Geplant consolidated\n`);

// Test 3: Mineral deduplication
console.log('Test 3: Mineral Deduplication');
const mineralTest = "Gold / Au / Gold / Silver / Silber / Gold / Aurum";
const mineralResult = engine.deduplicateValues(mineralTest, 'mineral');
console.log(`Input:  ${mineralTest}`);
console.log(`Output: ${mineralResult}`);
console.log(`✅ Expected: Gold and Silver consolidated\n`);

// Test 4: Test helper function
console.log('Test 4: Process Consolidated Fields');
const testFields = {
    country: "Canada / Kanada / USA / United States",
    status: "Active / Aktiv / Operating / Active",
    mineral: "Gold / Au / Silver"
};

console.log('Input fields:');
console.log(JSON.stringify(testFields, null, 2));

// Test processConsolidatedFields function
const processedFields = engine.processTableRow(testFields, {
    country: 'country',
    status: 'status',
    mineral: 'mineral'
});

console.log('\nProcessed fields:');
console.log(JSON.stringify(processedFields, null, 2));

// Test 5: Cache functionality
console.log('\nTest 5: Cache Performance');
const cacheTest = "Test / Test / Different / Test";
const startTime = Date.now();

// First call - should populate cache
engine.deduplicateValues(cacheTest, 'general');
const firstCallTime = Date.now() - startTime;

// Second call - should use cache
const cacheStartTime = Date.now();
engine.deduplicateValues(cacheTest, 'general');
const secondCallTime = Date.now() - cacheStartTime;

console.log(`First call: ${firstCallTime}ms`);
console.log(`Cached call: ${secondCallTime}ms`);
console.log(`✅ Cache should be faster\n`);

// Test 6: Edge cases
console.log('Test 6: Edge Cases');
console.log('Empty string:', engine.deduplicateValues('', 'general'));
console.log('Single value:', engine.deduplicateValues('Single', 'general'));
console.log('Null input:', engine.deduplicateValues(null, 'general'));
console.log('Undefined input:', engine.deduplicateValues(undefined, 'general'));

console.log('\n🎉 Deduplication Engine Tests Completed!');