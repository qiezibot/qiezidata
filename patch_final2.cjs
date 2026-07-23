const fs = require('fs');
const path = require('path');

const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const openClawDist = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';

function patchFile(filePath) {
  let c = fs.readFileSync(filePath, 'utf8');
  if (!c.includes('openclaw/')) return false;
  
  const fileDir = path.dirname(filePath);
  const rel = path.relative(fileDir, openClawDist).replace(/\\/g, '/');
  
  c = c.replace(/from "([^"]*openclaw\/[^"]+)"/g, (m, imp) => {
    // The current import has a relative path. We want to replace it with the correct one.
    // We already know the relative path from fileDir to openClawDist, so just build it.
    // But the import might already have been partially patched.
    // Simplest: just prepend the correct prefix for the subpath
    const subPath = imp.includes('openclaw/dist/') ? imp.substring(imp.lastIndexOf('openclaw/dist/') + 14) : 
                   imp.includes('openclaw/') ? imp.substring(imp.lastIndexOf('openclaw/') + 9) : imp;
    const final = rel + '/' + subPath;
    if (!final.endsWith('.js') && !final.endsWith('.cjs')) final = final + '/index.js';
    const resolved = path.resolve(fileDir, final);
    const exists = fs.existsSync(resolved);
    console.log(`  ${path.basename(filePath)}: ${subPath} -> [${exists ? 'OK' : 'MISSING'}]`);
    return `from "${final}"`;
  });
  
  fs.writeFileSync(filePath, c);
  return true;
}

function patchDir(dir) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(f => {
    const fp = path.join(dir, f.name);
    if (f.isDirectory()) { patchDir(fp); return; }
    if (f.name.endsWith('.js')) patchFile(fp);
  });
}

patchDir(base);
console.log('All patched.');
