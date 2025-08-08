/**
 * Frontend Sources Seeding Simulation Test
 * Testet die seedSourcesDatabase() Funktion ohne Browser
 */

// Mock global objects
global.console = console;

// Use built-in fetch (Node 18+) or mock it
if (typeof fetch === 'undefined') {
    global.fetch = async (url, options) => {
        console.log(`🌐 MOCK FETCH: ${options?.method || 'GET'} ${url}`);
        
        // Simulate successful API response
        return {
            ok: true,
            json: async () => ({
                success: true,
                data: {
                    total_processed: 19,
                    added_count: 11,
                    updated_count: 8,
                    error_count: 0,
                    final_database_count: 19
                }
            })
        };
    };
}

// Mock DOM elements
const mockButton = {
    innerHTML: '🌱 Standard-Quellen laden',
    disabled: false
};

// Mock event
global.event = {
    target: mockButton
};

// Mock API_BASE_URL
global.API_BASE_URL = 'http://localhost:8000';

// Mock showGracefulError function
global.showGracefulError = (type, message) => {
    console.log(`📢 ${type}: ${message}`);
};

// Mock loadSources function  
global.loadSources = () => {
    console.log('🔄 loadSources() called - Sources reload triggered');
};

// Copy the actual seedSourcesDatabase function from frontend
global.seedSourcesDatabase = async function() {
    console.log('🌱 Seeding sources database...');
    
    // Show loading state
    const button = global.event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ Laden...';
    button.disabled = true;
    
    try {
        // Call the API endpoint
        const response = await fetch(`${API_BASE_URL}/api/sources/seed?force=true`, {
            method: 'POST',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Sources seeded successfully:', data.data);
            
            // Show success message
            showGracefulError('SUCCESS', `Standard-Quellen erfolgreich geladen! ${data.data.final_database_count} Quellen in der Datenbank.`);
            
            // Reload the sources list
            setTimeout(() => {
                loadSources();
            }, 1500);
            
        } else {
            console.error('❌ Seeding failed:', data.message);
            showGracefulError('SEEDING_ERROR', data.message || 'Fehler beim Laden der Standard-Quellen');
        }
        
    } catch (error) {
        console.error('❌ Network error during seeding:', error);
        showGracefulError('NETWORK_ERROR', `Netzwerkfehler beim Laden der Standard-Quellen: ${error.message}`);
    } finally {
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
        console.log(`🔄 Button restored: "${button.innerHTML}", disabled: ${button.disabled}`);
    }
};

// Run the test
async function runTest() {
    console.log('🧪 FRONTEND SOURCES SEEDING TEST');
    console.log('='.repeat(50));
    
    console.log('📱 Simulating button click...');
    console.log(`🔲 Initial button state: "${mockButton.innerHTML}", disabled: ${mockButton.disabled}`);
    
    try {
        await seedSourcesDatabase();
        console.log('✅ Frontend function executed successfully');
    } catch (error) {
        console.error('❌ Frontend function failed:', error);
    }
    
    console.log('🏁 Test completed');
}

// Execute test
runTest();