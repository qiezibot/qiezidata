const { execSync } = require('child_process');
const script = 'import m from "file:///E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/extensions/qqbot/dist/index.js"; console.log("LOADED", Object.keys(m).slice(0,5).join(", "));';
// Write to temp file to avoid quoting issues
require('fs').writeFileSync('E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/workspace/_test_import.mjs', script);
try {
  const out = execSync('node E:\\openclaw压缩包及启动教程\\u-claw\\portable\\data\\.openclaw\\workspace\\_test_import.mjs', {encoding:'utf8', timeout:10000});
  console.log(out);
} catch(e) {
  console.log('ERR:', (e.stderr||e.message).substring(0,500));
}
