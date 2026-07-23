const fs = require('fs');
const path = require('path');

const indexJs = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/plugin-sdk/index.js';
const channelChunk1 = 'E:/openclaw压缩包及启动教程/u-claw/portable/app/core/node_modules/openclaw/dist/channel-BZnxNpmP.js';
const channelChunk2 = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/src/channel.js';

// Restore channel.js to its compiled version
const tsPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/src/channel.ts';

// We'll use the dist source compiled version - first need ts installed
// Simpler: check if we can use the existing compiled version and just fix the import path
// The original dist file is lost, so let's recompile

// I'll copy the index.ts/channel.ts to a temp dir, fix the import, and run tsc  
const { execSync } = require('child_process');

// First check if tsc is available
try {
  const tsc = execSync('where tsc', { encoding: 'utf8', timeout: 5000, shell: 'cmd' });
  console.log('tsc found:', tsc.trim());
} catch(e) {
  console.log('tsc not available, installing...');
  // Use the bundled node_modules typescript
  const tscPath = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/node_modules/.bin/tsc.cmd';
  if (fs.existsSync(tscPath)) {
    console.log('Found bundled tsc at:', tscPath);
  } else {
    console.log('No tsc found. Need to figure out another way.');
  }
}

// Alternative approach: modify plugin-sdk/index.js to re-export the needed functions
// by finding them in the correct chunk
let indexContent = fs.readFileSync(indexJs, 'utf8');
if (!indexContent.includes('applyAccountNameToChannelSection')) {
  // Add re-exports
  const chunk1Content = fs.readFileSync(channelChunk1, 'utf8');
  // Find the function sources - look for the actual chunk hash in the import
  // The chunk has a unique name
  const chunkName = path.basename(channelChunk1);
  // Add re-exports at the beginning
  const addition = `// Re-export channel helpers (needed by qqbot plugin)
export { applyAccountNameToChannelSection, deleteAccountFromConfigSection, setAccountEnabledInConfigSection } from "../${chunkName}";
`;
  indexContent = addition + indexContent;
  fs.writeFileSync(indexJs, indexContent);
  console.log('Added re-exports to plugin-sdk/index.js');
  
  // Verify
  const verify = fs.readFileSync(indexJs, 'utf8');
  if (verify.includes('applyAccountNameToChannelSection')) {
    console.log('Re-exports added successfully');
  }
}
