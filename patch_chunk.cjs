const fs = require('fs');
const path = require('path');

const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const openclawDist = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';

// Find the correct chunk file that exports these functions
function findChunk() {
  const dir = openclawDist;
  const files = fs.readdirSync(dir).filter(f => f.startsWith('channel-') && f.endsWith('.js') && f.includes('-'));
  for (const f of files) {
    const c = fs.readFileSync(path.join(dir, f), 'utf8');
    if (c.includes('applyAccountNameToChannelSection') && c.includes('function applyAccountName')) {
      return f;
    }
  }
  return null;
}

const chunk = findChunk();
if (!chunk) {
  console.error('Could not find the correct channel chunk');
  process.exit(1);
}
console.log('Found correct chunk:', chunk);

// Now modify channel.js to import from the chunk instead
const channelPath = path.join(base, 'src', 'channel.js');
let c = fs.readFileSync(channelPath, 'utf8');

const fileDir = path.dirname(channelPath);
const rel = path.relative(fileDir, openclawDist).replace(/\\/g, '/');
const chunkRel = rel + '/' + chunk;

c = c.replace(
  /import \{([^}]+)\} from "[^"]+plugin-sdk[^"]*"/,
  (m, imports) => `import {${imports}} from "${chunkRel}"`
);

fs.writeFileSync(channelPath, c);
console.log('Patched channel.js import to:', chunkRel);

// Verify
const v = fs.readFileSync(channelPath, 'utf8');
const im = v.match(/import \{[\s\S]*?\} from "[^"]+"/);
console.log('Result:', im ? im[0] : 'none');

// Also check index.js
const idxPath = path.join(base, 'index.js');
let idx = fs.readFileSync(idxPath, 'utf8');
const idxDir = path.dirname(idxPath);
const idxRel = path.relative(idxDir, openclawDist).replace(/\\/g, '/');
idx = idx.replace(
  /from "[^"]+plugin-sdk[^"]*"/,
  `from "${idxRel}/${chunk}"`
);
fs.writeFileSync(idxPath, idx);
console.log('index.js also patched');
