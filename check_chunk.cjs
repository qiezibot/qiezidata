const fs = require('fs');
const c = fs.readFileSync('E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/channel-BZnxNpmP.js', 'utf8');
// Find exports
const exports = c.match(/export\s+\{[\s\S]*?\};/g);
if (exports) exports.forEach(e => console.log(e));
// Also find the specific functions
['applyAccountNameToChannelSection', 'deleteAccountFromConfigSection', 'setAccountEnabledInConfigSection'].forEach(fn => {
  const idx = c.indexOf(fn);
  if (idx >= 0) console.log(fn, 'at', idx, 'context:', c.substring(Math.max(0,idx-20), idx+100));
  else console.log(fn, ': NOT FOUND in chunk');
});
