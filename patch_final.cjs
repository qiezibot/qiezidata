const fs = require('fs');
const path = require('path');
const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
// From dist/index.js we need to go to ../../../../../app/core/node_modules/openclaw/dist
const relToOpenClawDist = '../../../../../app/core/node_modules/openclaw/dist';

function patchDir(dir) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(f => {
    const fp = path.join(dir, f.name);
    if (f.isDirectory()) { patchDir(fp); return; }
    if (!f.name.endsWith('.js')) return;
    let c = fs.readFileSync(fp, 'utf8');
    if (!c.includes('openclaw/')) return;
    // Replace `openclaw/xxx` with `relToOpenClawDist/xxx`
    c = c.replace(/from "\.\.\/\.\.\/\.\.\/\.\.\/\.\.\/([^"]*?openclaw\/dist\/)([^"]+)"/g, (m, p1, p2) => {
      // This catches the previously wrong replacement
      return `from "${relToOpenClawDist}/${p2}"`;
    });
    c = c.replace(/from "([^"]*)openclaw\//g, `from "${relToOpenClawDist}/`);
    c = c.replace(/from '([^']*)openclaw\//g, `from '${relToOpenClawDist}/`);
    fs.writeFileSync(fp, c);
  });
}

patchDir(base);
console.log('Patched all files.');

// Verify
const content = fs.readFileSync(path.join(base, 'index.js'), 'utf8');
const matches = content.match(/from "([^"]+)"/g);
if (matches) {
  matches.forEach(m => {
    const p = m.slice(6, -1);
    const resolved = path.resolve(base, p);
    console.log(p, '->', resolved, 'exists:', fs.existsSync(resolved));
  });
}
