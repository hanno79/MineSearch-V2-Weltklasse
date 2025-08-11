/**
 * Script to identify and report all duplicate variable declarations
 */

const fs = require('fs');
const path = require('path');

// Read index.html
const indexPath = '/app/frontend/index.html';
const indexContent = fs.readFileSync(indexPath, 'utf8');

// Variables that should be removed from index.html (they exist in separate modules)
const variablesToRemove = [
    'userInactivityTimer',
    'INACTIVITY_TIMEOUT',
    'lastActivityTime',
    'activeDataSource',
    'isRefreshActive'
];

console.log('🔍 Scanning for duplicate variables...');

variablesToRemove.forEach(varName => {
    const regex = new RegExp(`(let|const|var)\\s+${varName}\\s*=`, 'g');
    const matches = indexContent.match(regex);
    if (matches && matches.length > 0) {
        console.log(`❌ Found ${matches.length} declarations of: ${varName}`);
    }
});

// Get lines with variable declarations
const lines = indexContent.split('\n');
const declarationLines = [];

lines.forEach((line, index) => {
    variablesToRemove.forEach(varName => {
        if (line.includes(`let ${varName}`) || line.includes(`const ${varName}`) || line.includes(`var ${varName}`)) {
            declarationLines.push({
                line: index + 1,
                content: line.trim(),
                variable: varName
            });
        }
    });
});

console.log('📋 Variable declarations found in index.html:');
declarationLines.forEach(decl => {
    console.log(`   Line ${decl.line}: ${decl.content}`);
});

console.log('\n✅ Analysis complete. These variables should be removed from index.html as they exist in separate modules.');