const fs = require('fs');
const c = fs.readFileSync('E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/src/channel.js', 'utf8');
// Print lines 1-10
c.split('\n').slice(0, 15).forEach((l, i) => console.log((i+1) + ':', l));
