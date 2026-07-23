const fs = require('fs');

// The qqbot plugin imports from "openclaw/plugin-sdk" which doesn't export
// applyAccountNameToChannelSection, deleteAccountFromConfigSection, setAccountEnabledInConfigSection
// These are exported from submodules. We need to change the import source.

const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const openclawDir = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';

// Find which file actually exports these functions
function findExport(fnName) {
  const fs2 = require('fs');
  const dir = openclawDir + '/plugin-sdk';
  const files = fs2.readdirSync(dir).filter(f => f.endsWith('.js'));
  for (const file of files) {
    const c = fs2.readFileSync(dir + '/' + file, 'utf8');
    if (c.includes('export ' + fnName) || c.includes('exports.' + fnName)) {
      return { file, content: c.substring(0, 200) };
    }
  }
  return null;
}

['applyAccountNameToChannelSection', 'deleteAccountFromConfigSection', 'setAccountEnabledInConfigSection'].forEach(fn => {
  const result = findExport(fn);
  console.log(fn + ':', result ? 'found in ' + result.file : 'NOT FOUND');
});

// Check what channel.js currently imports
const channelJs = fs.readFileSync(base + '/src/channel.js', 'utf8');
const importLine = channelJs.match(/import \{[\s\S]*?\} from "[^"]+"/);
if (importLine) {
  console.log('\nCurrent import:', importLine[0].substring(0, 200));
}
