/**
 * Real API Integration Test
 * Testet die Frontend-Backend Integration mit echter API
 */

const http = require('http');

// Function to make HTTP requests
function makeRequest(options, postData = null) {
    return new Promise((resolve, reject) => {
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    resolve({
                        statusCode: res.statusCode,
                        data: JSON.parse(data)
                    });
                } catch (e) {
                    resolve({
                        statusCode: res.statusCode,
                        data: data
                    });
                }
            });
        });
        
        req.on('error', reject);
        
        if (postData) {
            req.write(postData);
        }
        req.end();
    });
}

async function testRealAPIIntegration() {
    console.log('🧪 REAL API INTEGRATION TEST');
    console.log('='.repeat(50));
    
    // Step 1: Clear database
    console.log('1️⃣ Clearing sources database...');
    try {
        const { execSync } = require('child_process');
        execSync(`python -c "
from database.manager import DatabaseManager
from database.models import Source
db = DatabaseManager()
with db.get_session() as session:
    count = session.query(Source).count()
    print(f'Sources before clear: {count}')
    session.query(Source).delete()
    session.commit()
    print('Database cleared')
"`, { stdio: 'inherit' });
    } catch (error) {
        console.error('❌ Failed to clear database:', error.message);
        return;
    }
    
    // Step 2: Test seeding with empty database
    console.log('\\n2️⃣ Testing seeding with empty database...');
    try {
        const response = await makeRequest({
            hostname: 'localhost',
            port: 8000,
            path: '/api/sources/seed?force=false',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`   📡 Status: ${response.statusCode}`);
        if (response.data.success) {
            const stats = response.data.data;
            console.log(`   ✅ SUCCESS: ${stats.final_database_count} sources seeded`);
            console.log(`   📊 Added: ${stats.added_count}, Updated: ${stats.updated_count}, Errors: ${stats.error_count}`);
        } else {
            console.log(`   ❌ FAILED: ${response.data.message}`);
        }
    } catch (error) {
        console.error('❌ API request failed:', error.message);
        return;
    }
    
    // Step 3: Test seeding with existing data (should skip)
    console.log('\\n3️⃣ Testing seeding with existing data...');
    try {
        const response = await makeRequest({
            hostname: 'localhost', 
            port: 8000,
            path: '/api/sources/seed?force=false',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`   📡 Status: ${response.statusCode}`);
        if (response.data.success === false && response.data.message.includes('already contains')) {
            console.log(`   ✅ CORRECTLY SKIPPED: ${response.data.message}`);
        } else {
            console.log(`   ⚠️ UNEXPECTED: ${response.data.message}`);
        }
    } catch (error) {
        console.error('❌ API request failed:', error.message);
        return;
    }
    
    // Step 4: Test forced seeding 
    console.log('\\n4️⃣ Testing forced seeding...');
    try {
        const response = await makeRequest({
            hostname: 'localhost',
            port: 8000,
            path: '/api/sources/seed?force=true',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`   📡 Status: ${response.statusCode}`);
        if (response.data.success) {
            const stats = response.data.data;
            console.log(`   ✅ FORCED SUCCESS: ${stats.final_database_count} sources`);
            console.log(`   📊 Processed: ${stats.total_processed}, Added: ${stats.added_count}, Updated: ${stats.updated_count}`);
        } else {
            console.log(`   ❌ FAILED: ${response.data.message}`);
        }
    } catch (error) {
        console.error('❌ API request failed:', error.message);
        return;
    }
    
    // Step 5: Verify sources are available
    console.log('\\n5️⃣ Verifying sources availability...');
    try {
        const response = await makeRequest({
            hostname: 'localhost',
            port: 8000,
            path: '/api/sources/grouped',
            method: 'GET'
        });
        
        console.log(`   📡 Status: ${response.statusCode}`);
        if (response.data.success) {
            const data = response.data.data;
            console.log(`   ✅ VERIFICATION SUCCESS: ${data.total_sources} sources in ${data.total_domains} domains`);
        } else {
            console.log(`   ❌ VERIFICATION FAILED: ${response.data.message}`);
        }
    } catch (error) {
        console.error('❌ API request failed:', error.message);
    }
    
    console.log('\\n🏁 Integration test completed!');
}

// Run the test
testRealAPIIntegration();