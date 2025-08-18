// node analyze_reports.js

const fs = require('fs');
const path = require('path');

const logsDir = path.join(__dirname, '..', 'reports');

const regex = /^=+ (.+?) \((\d+)\) =+$/gm;

const allFiles = fs.readdirSync(logsDir)
    .filter(file => file.startsWith('report_') && file.endsWith('.txt'));

// Ordina i file per data 'YYYYMMDD'
const files = allFiles.sort((a, b) => {
    const dateA = a.match(/(.)*(\d{8})(?:_(\d+))?\.txt/);
    const dateB = b.match(/(.)*(\d{8})(?:_(\d+))?\.txt/);
    // Ordina prima per data, poi per numero intero (se presente)
    const cmp = dateA[1].localeCompare(dateB[1]);
    if (cmp !== 0) return cmp;
    const numA = dateA[2] ? parseInt(dateA[2], 10) : 0;
    const numB = dateB[2] ? parseInt(dateB[2], 10) : 0;
    return numA - numB;
});

for (const file of files) {
    const filePath = path.join(logsDir, file);
    const content = fs.readFileSync(filePath, 'utf8');

    const errorSummary = {};
    let match;

    while ((match = regex.exec(content)) !== null) {
        const errorType = match[1].trim();
        const count = parseInt(match[2], 10);
        errorSummary[errorType] = (errorSummary[errorType] || 0) + count;
    }

    const results = Object.entries(errorSummary).map(([Tipo, Errori]) => ({
        Tipo,
        Errori
    }));

    const totalErrors = results.reduce((sum, row) => sum + row.Errori, 0);

    console.log(`\n📄 ${file} - ${totalErrors}`);
    console.table(results);
}




