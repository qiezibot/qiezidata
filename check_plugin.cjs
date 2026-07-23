const fs = require('fs');
const path = require('path');
const pluginPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/index.js';
const content = fs.readFileSync(pluginPath, 'utf8');
const match = content.match(/from "([^"]+)"/);
console.log('First import:', match ? match[1] : 'none');
if (match) {
  const resolved = path.resolve('E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist', match[1]);
  console.log('Resolves to:', resolved);
  console.log('File exists:', fs.existsSync(resolved));
}
// Also check the config file
const cfg = fs.readFileSync('E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/openclaw.json', 'utf8');
console.log('Config has qqbot channels:', cfg.includes('channels') && cfg.includes('qqbot'));
console.log('Config has qqbot plugins.entries:', cfg.includes('plugins') && cfg.includes('qqbot'));
