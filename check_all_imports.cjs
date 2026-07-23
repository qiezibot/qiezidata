const fs = require('fs');
['index.js','src/config.js','src/channel.js','src/runtime.js','src/gateway.js','src/outbound.js','src/onboarding.js','src/api.js','src/types.js','src/proactive.js','src/ref-index-store.js','src/session-store.js','src/known-users.js','src/image-server.js'].forEach(f => {
  const p = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/' + f;
  if (!fs.existsSync(p)) return;
  const c = fs.readFileSync(p, 'utf8');
  const ms = c.match(/from "[^"]+"/g);
  if (ms) {
    console.log(f + ':');
    ms.forEach(m => console.log('  ' + m));
  }
});
