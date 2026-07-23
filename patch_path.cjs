const fs = require('fs');
const path = require('path');
const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const target = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw';
const correct = path.relative(base, target).replace(/\\/g, '/');
console.log('Correct relative path from dist to openclaw:', correct);

function patchDir(dir) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(f => {
    const fp = path.join(dir, f.name);
    if (f.isDirectory()) { patchDir(fp); return; }
    if (!f.name.endsWith('.js')) return;
    let c = fs.readFileSync(fp, 'utf8');
    if (!c.includes('openclaw/')) return;
    c = c.replace(/from "\.\.\/\.\.\/\.\.\/app\/core\/node_modules\/openclaw\//g, `from "${correct}/`);
    fs.writeFileSync(fp, c);
  });
}

patchDir(base);
console.log('Patched all files with correct path:', correct);

// Verify
const content = fs.readFileSync(path.join(base, 'index.js'), 'utf8');
const match = content.match(/from "([^"]+)"/);
if (match) {
  const resolved = path.resolve(base, match[1]);
  console.log('Verification - resolves to:', resolved);
  console.log('Verification - file exists:', fs.existsSync(resolved));
}
