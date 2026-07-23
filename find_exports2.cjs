const fs = require('fs');
const openclawDist = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist';
const dir = openclawDist;
fs.readdirSync(dir).forEach(f => {
  if (!f.endsWith('.js')) return;
  const c = fs.readFileSync(dir + '/' + f, 'utf8');
  if (c.includes('export function applyAccount') || c.includes('export function deleteAccount') || c.includes('export function setAccount')) {
    console.log(f + ':');
    ['applyAccountNameToChannelSection', 'deleteAccountFromConfigSection', 'setAccountEnabledInConfigSection'].forEach(fn => {
      if (c.includes('export function ' + fn)) {
        // get the line
        const lines = c.split('\n');
        const lineIdx = lines.findIndex(l => l.includes('export function ' + fn));
        if (lineIdx >= 0) console.log('  ' + fn + ' at line', lineIdx + 1, ':', lines[lineIdx].substring(0, 80));
      }
    });
  }
});
