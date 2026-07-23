const fs = require('fs');
const path = require('path');

const sdkPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/plugin-sdk/index.js';
const distDir = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';

let c = fs.readFileSync(sdkPath, 'utf8');

// Find all import paths from the sdk file
const importMatches = c.matchAll(/from\s+"\.\.\/([^"]+)"/g);
const neededFiles = new Set();
for (const m of importMatches) {
  neededFiles.add(m[1]);
}

// Map the tgz chunk names to local chunk names
// Read all files in dist dir
const localFiles = {};
fs.readdirSync(distDir).forEach(f => {
  if (f.endsWith('.js')) {
    // Strip hash: e.g. "diagnostic-events-BkhOFI0h.js" -> "diagnostic-events"
    const base = f.replace(/-[A-Za-z0-9]+\.js$/, '').replace(/\.js$/, '');
    if (!localFiles[base]) localFiles[base] = [];
    localFiles[base].push(f);
  }
});

// For each import, check if the file exists. If not, find the local version.
for (const imp of neededFiles) {
  const fullPath = path.join(distDir, imp);
  if (!fs.existsSync(fullPath)) {
    // Try to find a match
    const base = imp.replace(/-[A-Za-z0-9]+(?=\.js$)/, '');
    const candidates = fs.readdirSync(distDir).filter(f => f.startsWith(base.replace('.js','')));
    if (candidates.length > 0) {
      console.log(`REMAP: ${imp} -> ${candidates[0]}`);
      c = c.replace(new RegExp(imp.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), candidates[0]);
    } else {
      console.log(`MISSING: ${imp} - no match for base "${base}"`);
    }
  } else {
    console.log(`OK: ${imp}`);
  }
}

fs.writeFileSync(sdkPath, c);
console.log('\nUpdated plugin-sdk/index.js with correct chunk names');

// Verify
const v = fs.readFileSync(sdkPath, 'utf8');
const imports = v.match(/from "\.\.\/[^"]+"/g);
let allOk = true;
imports.forEach(i => {
  const fp = path.join(distDir, i.slice(7, -1));
  if (!fs.existsSync(fp)) {
    console.log(`STILL MISSING: ${i.slice(7, -1)}`);
    allOk = false;
  }
});
if (allOk) console.log('All imports resolved!');
