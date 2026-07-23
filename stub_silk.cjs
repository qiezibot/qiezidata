const fs = require('fs');
const file = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/src/utils/platform.js';
let c = fs.readFileSync(file, 'utf8');
// Replace the silk-wasm import with a stub function
c = c.replace(
  /export async function checkSilkWasmAvailable[\s\S]*?return _silkWasmAvailable;\n\}/,
  `export async function checkSilkWasmAvailable() {\n  return false;\n}`
);
// Also remove any "silk-wasm" dynamic import
c = c.replace(/const \{ isSilk \} = await import\("silk-wasm"\)[\s\S]*?isSilk\(new Uint8Array\(0\)\);/, '/* silk-wasm stubbed */');
fs.writeFileSync(file, c);
console.log('Platform.js silk-wasm stubbed');
