const fs = require('fs');
const path = require('path');

// Read the original TypeScript source
const tsPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/src/channel.ts';
const ts = fs.readFileSync(tsPath, 'utf8');

// Find the import block and replace it
const channelJsPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/src/channel.js';
const openclawDist = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';
const rel = path.relative(path.dirname(channelJsPath), openclawDist).replace(/\\/g, '/');

// Build a clean version from the TS source
let js = ts;
// Replace TS import
js = js.replace(
  /import\s*\{[\s\S]*?\}\s*from\s*"openclaw\/plugin-sdk"/,
  `import type { ChannelPlugin, OpenClawConfig } from "${rel}/plugin-sdk/index.js"`
);
// Add stubs after the import
js = js.replace(
  /import type \{[\s\S]*?\};/,
  `import type { ChannelPlugin, OpenClawConfig } from "${rel}/plugin-sdk/index.js";\n` +
  `const applyAccountNameToChannelSection = (...args) => {};\n` +
  `const deleteAccountFromConfigSection = (...args) => {};\n` +
  `const setAccountEnabledInConfigSection = (...args) => {};`
);

// Remove all "type" annotations (they're TS-only)
js = js.replace(/: \w+(?:<[^>]+>)?(?:\[\])?/g, '').replace(/:\s*string/g, '').replace(/:\s*number/g, '').replace(/:\s*boolean/g, '').replace(/:\s*void/g, '');
// Remove "export type" and "export interface"
js = js.replace(/export\s+(type|interface)\s+\w+[\s\S]*?\{[\s\S]*?\}\n?/g, '');
// Remove "as const"
js = js.replace(/\s*as\s+const/g, '');

// Write
fs.writeFileSync(channelJsPath, js);
console.log('Written clean channel.js');

// Test
const test = fs.readFileSync(channelJsPath, 'utf8');
console.log('\nFirst 15 lines:');
test.split('\n').slice(0, 15).forEach((l, i) => console.log(i+1 + ':', l));
