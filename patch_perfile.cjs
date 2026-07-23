const fs = require('fs');
const path = require('path');

const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const openClawDist = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';

function patchFile(filePath) {
  let c = fs.readFileSync(filePath, 'utf8');
  if (!c.includes('openclaw')) return false;
  
  const fileDir = path.dirname(filePath);
  const rel = path.relative(fileDir, openClawDist).replace(/\\/g, '/');
  
  c = c.replace(/from "openclaw\/([^"]+)"/g, (m, subpath) => {
    let fp = subpath;
    if (!fp.endsWith('.js') && !fp.endsWith('.cjs')) fp += '/index.js';
    const final = rel + '/' + fp;
    const resolved = path.resolve(fileDir, final);
    const exists = fs.existsSync(resolved);
    console.log(`  ${path.basename(filePath)}: ${subpath} -> ${final.substring(final.lastIndexOf('openclaw'))} [${exists ? 'OK' : 'MISSING'}]`);
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

console.log('Patching with per-file relative paths...');
patchDir(base);
console.log('\nDone.');
