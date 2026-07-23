const fs = require('fs');
// Update the re-export in plugin-sdk/index.js
const sdkIndex = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/plugin-sdk/index.js';
let c = fs.readFileSync(sdkIndex, 'utf8');
// Remove our previous added re-export
c = c.replace(/^\/\/ Re-export[\s\S]*?\n\nexport \{[\s\S]*?\} from "[^"]+";\n\n/, '');
// Add proper re-exports: only applyAccountNameToChannelSection re-export, other 2 as shims
const addition = `// Shim exports for qqbot plugin compatibility
const deleteAccountFromConfigSection = () => {};
const setAccountEnabledInConfigSection = () => {};
export { applyAccountNameToChannelSection as applyAccountNameToChannelSection } from "../setup-helpers-CLiDrlXo.js";
export { deleteAccountFromConfigSection, setAccountEnabledInConfigSection };

`;
c = addition + c;
fs.writeFileSync(sdkIndex, c);
console.log('Updated plugin-sdk/index.js with proper shims');
