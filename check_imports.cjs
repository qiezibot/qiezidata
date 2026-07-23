const fs = require('fs');
const path = require('path');
const distDir = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';

const files = ['index.js', 'src/channel.js', 'src/gateway.js', 'src/runtime.js', 'src/outbound.js',
               'src/onboarding.js', 'src/api.js', 'src/config.js', 'src/types.js',
               'src/ref-index-store.js', 'src/proactive.js', 'src/utils/platform.js'];

files.forEach(f => {
  const fp = path.join(distDir, f);
  if (!fs.existsSync(fp)) return;
  let c = fs.readFileSync(fp, 'utf8');
  const matches = c.match(/from "[^"]+"/g);
  if (!matches) return;
  console.log(f + ':');
  matches.forEach(m => console.log('  ' + m));
});
