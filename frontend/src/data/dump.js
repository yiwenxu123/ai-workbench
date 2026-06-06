import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// To execute TS files that export data, we can just use regex to extract the JSON-like structures
// since they don't have complex TS features in the data objects themselves.
// Wait, a simpler way is to just let vite/tsc compile it or use a regex to extract the array/object.

function extractArray(filePath) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const match = content.match(/export const \w+(?:\s*:\s*\w+(?:\[\])?)?\s*=\s*(\[[\s\S]*?\])(?:\n\n|\nexport|;$)/m);
    
    if (match) {
        try {
            const result = parseObjectLiteralArray(match[1]);
            return JSON.stringify(result, null, 2);
        } catch (e) {
            console.error(`Failed to parse ${filePath}:`, e);
            return null;
        }
    }
    return null;
}

function parseObjectLiteralArray(source) {
    const withoutComments = source
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/(^|[^:])\/\/.*$/gm, '$1');
    const jsonLike = withoutComments
        .replace(/`([^`\\]*(?:\\.[^`\\]*)*)`/g, (_, value) => JSON.stringify(value))
        .replace(/'([^'\\]*(?:\\.[^'\\]*)*)'/g, (_, value) => JSON.stringify(value))
        .replace(/([{,]\s*)([A-Za-z_$][\w$]*)\s*:/g, '$1"$2":')
        .replace(/\bundefined\b/g, 'null')
        .replace(/,\s*([}\]])/g, '$1');
    return JSON.parse(jsonLike);
}

const filesToExtract = {
    'promptTemplates.ts': 'templates.json',
    'videoTemplates.ts': 'video_templates.json',
    'terminology.ts': 'knowledge.json',
    'workTemplates.ts': 'work_templates.json',
    'festivalTemplates.ts': 'festival_templates.json'
};

const backendDataDir = path.resolve(__dirname, '../../backend/data');
if (!fs.existsSync(backendDataDir)) {
    fs.mkdirSync(backendDataDir, { recursive: true });
}

for (const [tsFile, jsonFile] of Object.entries(filesToExtract)) {
    const tsPath = path.resolve(__dirname, tsFile);
    if (fs.existsSync(tsPath)) {
        console.log(`Processing ${tsFile}...`);
        const jsonStr = extractArray(tsPath);
        if (jsonStr) {
            fs.writeFileSync(path.resolve(backendDataDir, jsonFile), jsonStr);
            console.log(`Saved ${jsonFile}`);
        } else {
            console.log(`Failed to extract data from ${tsFile}`);
        }
    }
}
