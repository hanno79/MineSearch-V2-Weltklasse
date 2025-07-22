/**
 * Author: rahn
 * Datum: 16.07.2025
 * Version: 1.0
 * Beschreibung: Backend-Validierung vor Test-Ausführung
 */

const http = require('http');

const BASE_URL = 'http://localhost:8000';

async function checkBackend() {
    console.log('🔍 Validiere Backend-Verfügbarkeit...');
    
    return new Promise((resolve, reject) => {
        const req = http.get(`${BASE_URL}/api/models`, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                if (res.statusCode === 200) {
                    console.log('✅ Backend läuft und ist erreichbar');
                    try {
                        const json = JSON.parse(data);
                        console.log(`📊 ${Object.keys(json).length} Modelle verfügbar`);
                        resolve(true);
                    } catch (e) {
                        console.log('⚠️  Backend erreichbar, aber unerwartete Antwort');
                        resolve(false);
                    }
                } else {
                    console.log(`❌ Backend antwortet mit Status ${res.statusCode}`);
                    resolve(false);
                }
            });
        });
        
        req.on('error', (err) => {
            console.log(`❌ Backend nicht erreichbar: ${err.message}`);
            console.log('');
            console.log('💡 Starte Backend mit:');
            console.log('   cd ../../backend');
            console.log('   python main.py');
            resolve(false);
        });
        
        req.setTimeout(5000, () => {
            console.log('❌ Backend-Timeout nach 5 Sekunden');
            req.destroy();
            resolve(false);
        });
    });
}

if (require.main === module) {
    checkBackend().then((isRunning) => {
        process.exit(isRunning ? 0 : 1);
    });
}

module.exports = { checkBackend };