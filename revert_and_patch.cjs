const fs = require('fs');
const path = require('path');

// Read original channel.ts source and recompile manually
const tsPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/src/channel.ts';
const ts = fs.readFileSync(tsPath, 'utf8');

// Extract the import line
const m = ts.match(/import\s*\{[^}]+\}\s*from\s*"openclaw\/plugin-sdk"/);
if (!m) { console.error('Cannot find import line'); process.exit(1); }

console.log('Original TS import:', m[0]);

// We need to replace the import with: keep only types, stub the functions
// The import is multi-line
const fullImport = ts.match(/import\s*\{[\s\S]*?\}\s*from\s*"openclaw\/plugin-sdk"/);
if (!fullImport) { console.error('Cannot find full import'); process.exit(1); }

const importText = fullImport[0];
// Parse the named imports
const namedPart = importText.match(/\{([\s\S]*?)\}/)[1];
const names = namedPart.split(',').map(s => s.trim()).filter(Boolean);

const types = [];
const funcs = [];
names.forEach(n => {
  if (n.startsWith('type ')) {
    types.push(n.replace('type ', '').trim());
  } else {
    funcs.push(n);
  }
});

console.log('Types:', types);
console.log('Functions to stub:', funcs);

// Build the replacement
const openclawDist = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';
const dist = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const fileDir = dist + '/src/channel.js'; // but this path is for resolution calc

// Actually let's just manually rewrite the whole channel.js from scratch
// by compiling the TS import section

const channelJsPath = path.join(dist, 'src', 'channel.js');
let js = fs.readFileSync(channelJsPath, 'utf8');

// Remove the first import block and replace with our patched version
const importRegex = /^import\s*\{[\s\S]*?\}\s*from\s*"[^"]+";?\n*/m;
js = js.replace(importRegex, '');

// Add our imports and stubs at the top
const rel = path.relative(path.dirname(channelJsPath), openclawDist).replace(/\\/g, '/');

let header = '';
if (types.length > 0) {
  header += `import type { ${types.join(', ')} } from "${rel}/plugin-sdk/index.js";\n`;
}
funcs.forEach(fn => {
  header += `const ${fn} = (...args) => { /* stub for ${fn} */ };\n`;
});

js = header + js;

fs.writeFileSync(channelJsPath, js);
console.log('Written channel.js with proper stubs');

// Verify
const verify = fs.readFileSync(channelJsPath, 'utf8');
console.log('\nFirst 10 lines:');
verify.split('\n').slice(0, 10).forEach((l, i) => console.log(i+1 + ':', l));
