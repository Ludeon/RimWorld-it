const fs = require('fs');
const path = require('path');

const logsDir = path.join(__dirname, '..', 'reports');

const regex = /^=+ (.+?) \((\d+)\) =+$/gm;

const allFiles = fs.readdirSync(logsDir)
    .filter(file => file.startsWith('report_') && file.endsWith('.txt'));

// Ordina i file per data 'YYYYMMDD'
const files = allFiles.sort((a, b) => {
    const dateA = a.match(/report_(\d{8})\.txt/)[1];
    const dateB = b.match(/report_(\d{8})\.txt/)[1];
    return dateA.localeCompare(dateB);
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




