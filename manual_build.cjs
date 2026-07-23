const fs = require('fs');
const path = require('path');

// Manual build: read TS source files, strip types, convert to ESM JS
const srcDir = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/src';
const outDir = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const sdkRel = '../../../../app/core/node_modules/openclaw/dist/plugin-sdk/index.js';

function stripTypes(ts) {
  // Remove type annotations (simplified - won't handle all TS)
  let js = ts;
  // Remove type imports
  js = js.replace(/import type\s*\{[^}]*\}\s*from\s*"[^"]+";?\n?/g, '');
  // Remove standalone type annotations: : TypeName, : TypeName<...>
  js = js.replace(/:\s*\w+(?:<[^>]*>)?(?:\[\])?\s*(?=[,)=;])/g, '');
  // Remove : string | : number | : boolean etc inline
  js = js.replace(/:\s*(string|number|boolean|void|any|never|unknown|undefined|null)\b/g, '');
  // Remove export type and export interface
  js = js.replace(/export\s+(type|interface)\s+\w+[\s\S]*?\{[\s\S]*?\}\n?/g, '');
  // Remove as const
  js = js.replace(/\s*as\s+const\b/g, '');
  // Clean up multiple empty lines
  js = js.replace(/\n{3,}/g, '\n\n');
  return js;
}

// Process each file
function buildFile(relPath) {
  const tsPath = path.join(srcDir, relPath);
  const jsPath = path.join(outDir, relPath.replace(/\.ts$/, '.js'));
  
  if (!fs.existsSync(tsPath)) {
    console.log('Skip (not found):', relPath);
    return;
  }
  
  let content = fs.readFileSync(tsPath, 'utf8');
  
  // Replace import paths
  content = content.replace(/from\s+"openclaw\/plugin-sdk"/g, `from "${sdkRel}"`);
  content = content.replace(/from\s+['"]openclaw\/plugin-sdk['"]/g, `from "${sdkRel}"`);
  
  // Replace relative imports (keep as-is, they point to other src files)
  content = content.replace(/from\s+"\.\/([^"]+)"/g, (m, p) => {
    const resolved = path.resolve(path.dirname(tsPath), p);
    const relFromJs = path.relative(path.dirname(jsPath), resolved).replace(/\\/g, '/');
    return `from "${relFromJs}"`;
  });
  
  // Strip types
  content = stripTypes(content);
  
  // Ensure .js extension on relative imports
  content = content.replace(/from\s+"(\.[^"]+?)(?<!\.js)"/g, '$1.js"');
  
  // Create output dir
  const jsDir = path.dirname(jsPath);
  if (!fs.existsSync(jsDir)) fs.mkdirSync(jsDir, { recursive: true });
  
  fs.writeFileSync(jsPath, content);
  console.log('Built:', relPath);
}

// Build index.ts
buildFile('../index.ts');
// Build all src/*.ts
fs.readdirSync(srcDir).forEach(f => {
  if (f.endsWith('.ts')) buildFile(f);
});

console.log('\nBuild complete');
