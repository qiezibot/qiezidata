const fs = require('fs');
const c = fs.readFileSync('E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/plugin-sdk/index.js', 'utf8');
console.log(c.substring(0, 500));
