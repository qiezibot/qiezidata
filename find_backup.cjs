const fs = require('fs');

// I need to rebuild plugin-sdk/index.js from the current dist content
// The plugin-sdk/index.js originally exported these from various modules:
// 1. buildFalImageGenerationProvider - from an ai chunk
// 2. ChannelPlugin - type export
// 3. OpenClawConfig - type export
// etc.

// Since I broke the original, let me just get a fresh copy from npm
const { execSync } = require('child_process');

// Create a temp dir
const tmpDir = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/workspace/tmp_oc';
try { fs.mkdirSync(tmpDir); } catch(e) {}

// We can extract the tarball using node:zlib
const zlib = require('zlib');
const path = require('path');

const tgzPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/workspace/openclaw-2026.5.12.tgz';
const gunzip = zlib.createGunzip();
const fs_read = fs.createReadStream(tgzPath);
const { pipeline } = require('stream');

// We need to parse tar. Let's do it manually.
// Actually, let me just re-pack npm and use a simpler approach

// Delete the corrupted sdk index and reinstall just that module
// OR - even simpler - check if there's a backup in node_modules/.cache
const cacheDir = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/.cache';
function findBackup(dir, depth=0) {
  if (depth > 3) return;
  try {
    fs.readdirSync(dir, {withFileTypes: true}).forEach(f => {
      const fp = path.join(dir, f.name);
      if (f.isDirectory()) { findBackup(fp, depth+1); return; }
      if (f.name.includes('plugin-sdk') || (f.name.endsWith('.js') && f.name.includes('index'))) {
        const c = fs.readFileSync(fp, 'utf8');
        if (c.includes('buildFalImageGenerationProvider') && c.includes('export {')) {
          console.log('FOUND BACKUP at:', fp);
        }
      }
    });
  } catch(e) {}
}
if (fs.existsSync(cacheDir)) findBackup(cacheDir);

// Alternative: check working directory for the tgz
console.log('tgz file exists:', fs.existsSync(tgzPath));

// Let's use python to extract
try {
  const pyOut = execSync('python --version 2>&1', {encoding:'utf8'});
  console.log('Python available:', pyOut.trim());
} catch(e) {
  console.log('Python not available');
}
