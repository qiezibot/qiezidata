const { execSync } = require('child_process');
try {
  const out = execSync('node --input-type=module -e "import m from \'file:///E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/index.js\'; console.log(\'LOADED OK\', Object.keys(m).slice(0,10).join(\', \'))"', {
    timeout: 10000,
    encoding: 'utf8',
    cwd: 'E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist'
  });
  console.log(out);
} catch(e) {
  console.log('Error:', e.message?.substring(0, 500) || e.stdout?.substring(0, 500));
}
