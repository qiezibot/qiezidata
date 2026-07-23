const fs = require('fs');
const chunk = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/channel-BZnxNpmP.js';
const c = fs.readFileSync(chunk, 'utf8');
// Check if these functions are exported
['applyAccountNameToChannelSection', 'deleteAccountFromConfigSection', 'setAccountEnabledInConfigSection'].forEach(fn => {
  // Look for export { ... fn ... } pattern
  const regex = new RegExp('export\\s+\\{[^}]*' + fn + '[^}]*\\}');
  const m = c.match(regex);
  console.log(fn + ':', m ? 'exported in chunk' : 'not directly exported');
  // Check if function is defined
  const def = c.includes('function ' + fn) || c.includes(', ' + fn + '=') || c.includes(fn + '=');
  console.log('  defined:', def);
});
