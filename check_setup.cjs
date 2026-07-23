const fs = require('fs');
const c = fs.readFileSync('E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/setup-helpers-CLiDrlXo.js', 'utf8');
// Find all exports
const x = c.match(/export\s+\{[\s\S]*?\};/g);
if (x) x.forEach(e => console.log(e));
// Find the 3 functions
['applyAccountNameToChannelSection', 'deleteAccountFromConfigSection', 'setAccountEnabledInConfigSection'].forEach(fn => {
  console.log(fn + ':', c.includes(fn));
});
