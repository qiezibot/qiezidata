const fs = require('fs');
const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
['index.js', 'src/channel.js'].forEach(f => {
  const c = fs.readFileSync(base + '/' + f, 'utf8');
  const m = c.match(/from "([^"]+)"/);
  console.log(f + ':', m ? m[1] : 'no imports');
});
