const fs = require('fs');
// Restore the imports to use the bare 'openclaw/plugin-sdk' format
// which is how the plugin was originally compiled
const base = 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist';
const correctRel = '../../../../../app/core/node_modules/openclaw';
const wrongRel = '../../../../../app/core/node_modules/openclaw/dist';

function restoreImports(dir) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(f => {
    const fp = require('path').join(dir, f.name);
    if (f.isDirectory()) { restoreImports(fp); return; }
    if (!f.name.endsWith('.js')) return;
    let c = fs.readFileSync(fp, 'utf8');
    if (!c.includes('openclaw')) return;
    // Change "../../../../../app/core/node_modules/openclaw/dist/xxx"
    // to "openclaw/xxx" - let Node's module resolution handle it
    c = c.replace(
      /"\.\.\/\.\.\/\.\.\/\.\.\/\.\.\/app\/core\/node_modules\/openclaw\/dist\//g,
      '"openclaw/'
    );
    fs.writeFileSync(fp, c);
  });
}

restoreImports(base);

// Verify
const content = fs.readFileSync(require('path').join(base, 'index.js'), 'utf8');
content.split('\n').filter(l => l.includes('from')).slice(0,5).forEach(l => console.log(l.trim()));

console.log('\nNow test if Node.js can resolve:');
// Create a test script that mimics ESM resolution
const { execSync } = require('child_process');
try {
  execSync('node --input-type=module -e "import x from \'openclaw/plugin-sdk\'; console.log(\'SUCCESS\', Object.keys(x))"', {
    cwd: base,
    encoding: 'utf8',
    timeout: 8000,
    env: { ...process.env, NODE_PATH: '' }
  });
} catch(e) {
  console.log('Test import error:', e.message?.substring(0,200) || e.stdout?.substring(0,300));
}
