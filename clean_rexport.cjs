const fs = require('fs');
const sdkIndex = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/plugin-sdk/index.js';
let c = fs.readFileSync(sdkIndex, 'utf8');

// Strip everything before the actual module content (first export)
const firstExportIdx = c.indexOf('export { buildFalImageGenerationProvider');
const addition = `// Shim exports for qqbot plugin compatibility
const __deleteAccountFromConfigSection = () => {};
const __setAccountEnabledInConfigSection = () => {};
export { applyAccountNameToChannelSection as applyAccountNameToChannelSection } from "../setup-helpers-CLiDrlXo.js";
export { __deleteAccountFromConfigSection as deleteAccountFromConfigSection, __setAccountEnabledInConfigSection as setAccountEnabledInConfigSection };

`;

c = addition + c.substring(firstExportIdx);
fs.writeFileSync(sdkIndex, c);

// Verify no duplicate exports
const matches = c.match(/export\s+\{[^}]+\}/g);
console.log('Exports found:', matches?.length);
const counts = {};
(c.match(/\bdeleteAccountFromConfigSection\b|\bsetAccountEnabledInConfigSection\b|applyAccountNameToChannelSection\b/g) || []).forEach(fn => {
  counts[fn] = (counts[fn] || 0) + 1;
});
console.log('Counts:', JSON.stringify(counts));

// Also check for duplicate
console.log('Has duplicate:', c.includes('Duplicate'));
