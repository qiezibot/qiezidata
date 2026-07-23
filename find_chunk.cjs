const fs = require('fs');
const dir = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';
fs.readdirSync(dir).forEach(f => {
  if (!f.endsWith('.js')) return;
  const c = fs.readFileSync(dir + '/' + f, 'utf8');
  if (c.includes('applyAccountNameToChannelSection')) {
    console.log(f);
  }
});
