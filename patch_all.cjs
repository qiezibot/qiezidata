const fs = require('fs');
const path = require('path');
const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const relBase = '../../../app/core/node_modules/openclaw';

function patchDir(dir) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(f => {
    const fp = path.join(dir, f.name);
    if (f.isDirectory()) { patchDir(fp); return; }
    if (!f.name.endsWith('.js')) return;
    let c = fs.readFileSync(fp, 'utf8');
    if (!c.includes('openclaw/')) return;
    c = c.replace(/from "openclaw\//g, `from "${relBase}/`);
    c = c.replace(/from 'openclaw\//g, `from '${relBase}/`);
    c = c.replace(/require\("openclaw\//g, `require("${relBase}/`);
    c = c.replace(/require\('openclaw\//g, `require('${relBase}/`);
    fs.writeFileSync(fp, c);
    const shortPath = fp.substring(fp.indexOf('qqbot') + 6);
    console.log('Patched:', shortPath);
  });
}

patchDir(base);
console.log('All files patched.');
