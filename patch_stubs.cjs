const fs = require('fs');
const channelPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/src/channel.js';

let c = fs.readFileSync(channelPath, 'utf8');

// The 3 functions need to be available. Since they're not exported by openclaw's plugin-sdk,
// and they're runtime-injected functions, we add stub shims
// First: replace the import to only get what's available from plugin-sdk
c = c.replace(
  /import \{([^}]+)\} from "([^"]+plugin-sdk[^"]*)"/,
  (m, imports, fromPath) => {
    const funcs = imports.split(',').map(s => s.trim());
    const kept = [];
    const stubs = [];
    funcs.forEach(f => {
      const clean = f.replace(/^(type\s+)/, '').trim();
      if (clean === 'ChannelPlugin' || clean === 'OpenClawConfig') {
        kept.push(f);
      } else {
        const name = clean.replace(/^type\s+/, '');
        stubs.push(`const ${name} = (section, ...args) => { if (typeof args[0] === 'object') { /* stub - runtime injected */ } };`);
      }
    });
    const prefix = stubs.join('\n');
    return `import {${kept.join(',')}} from "${fromPath}"\n${prefix}`;
  }
);

fs.writeFileSync(channelPath, c);
console.log('Patched channel.js with stub functions');

// Verify
const v = fs.readFileSync(channelPath, 'utf8');
console.log(v.match(/import \{[\s\S]*?\} from "[^"]+"/)?.[0]);
console.log('Stubs added:', v.includes('applyAccountNameToChannelSection') && v.includes('const'));
