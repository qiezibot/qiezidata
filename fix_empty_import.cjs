const fs = require('fs');
const channelPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/src/channel.js';

let c = fs.readFileSync(channelPath, 'utf8');

// Fix: import should have at least one named export
c = c.replace(
  /import \{\} from "([^"]+)"/,
  'import { emptyPluginConfigSchema } from "$1"'
);

// Also clean up the double semicolon
c = c.replace(/;;/g, ';');

fs.writeFileSync(channelPath, c);
console.log('Fixed channel.js');
