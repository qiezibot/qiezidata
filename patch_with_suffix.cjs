const fs = require('fs');
const path = require('path');

// Set the CORRECT path - openclaw/plugin-sdk resolves to openclaw/dist/plugin-sdk/index.js
// We use the full relative path with .js suffix for ESM compliance
const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const rel = '../../../../../app/core/node_modules/openclaw/dist';

function patchFiles(dir) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(f => {
    const fp = path.join(dir, f.name);
    if (f.isDirectory()) { patchFiles(fp); return; }
    if (!f.name.endsWith('.js')) return;
    let c = fs.readFileSync(fp, 'utf8');
    if (!c.includes('openclaw')) return;
    // Replace "openclaw/xxx" with the full relative path + .js
    c = c.replace(/from "openclaw\/([^"]+)"/g, (m, subpath) => {
      // subpath might be "plugin-sdk" -> plugin-sdk/index.js
      let filePath = subpath;
      if (!filePath.endsWith('.js')) filePath += '/index.js';
      const finalPath = rel + '/' + filePath;
      // Verify the file exists
      const resolved = path.resolve(base, finalPath);
      const exists = fs.existsSync(resolved);
      console.log(`  ${subpath} -> ${finalPath.substring(finalPath.lastIndexOf('openclaw'))} [${exists ? 'OK' : 'MISSING'}]`);
      return `from "${finalPath}"`;
    });
    c = c.replace(/require\("openclaw\/([^"]+)"\)/g, (m, subpath) => {
      let filePath = subpath;
      if (!filePath.endsWith('.js')) filePath += '/index.js';
      return `require("${rel}/${filePath}")`;
    });
    fs.writeFileSync(fp, c);
  });
}

console.log('Patching files...');
patchFiles(base);
console.log('\nVerification:');
const content = fs.readFileSync(path.join(base, 'index.js'), 'utf8');
content.split('\n').filter(l => l.includes('openclaw')).forEach(l => console.log(l.trim()));
