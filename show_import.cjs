const fs = require('fs');
const c = fs.readFileSync('E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/src/channel.js', 'utf8');
// Find the original import line
const m = c.match(/import\s*\{[\s\S]*?\}\s*from/);
if (m) {
  // Get the full import line
  const start = m.index;
  const end = c.indexOf('"', c.indexOf('from', start) + 5) + 1;
  console.log('ORIGINAL IMPORT BLOCK:');
  console.log(c.substring(start, end));
}
