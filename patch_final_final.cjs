const fs = require('fs');
const path = require('path');

// Post-process: replace "openclaw/plugin-sdk" with correct relative path in all dist js files
const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const target = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/plugin-sdk/index.js';

function patchFile(fp) {
  let c = fs.readFileSync(fp, 'utf8');
  if (!c.includes('openclaw/plugin-sdk')) return false;
  
  const fileDir = path.dirname(fp);
  const rel = path.relative(fileDir, target).replace(/\\/g, '/');
  
  c = c.replace(/from "openclaw\/plugin-sdk"/g, `from "${rel}"`);
  fs.writeFileSync(fp, c);
  console.log(`Patched ${path.relative(base, fp)}: -> ${rel}`);
  return true;
}

function walkDir(dir) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(f => {
    const fp = path.join(dir, f.name);
    if (f.isDirectory()) walkDir(fp);
    else if (f.name.endsWith('.js')) patchFile(fp);
  });
}

walkDir(base);
console.log('Done');
