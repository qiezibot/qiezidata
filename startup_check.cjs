/**
 * startup_check.cjs - 启动自检脚本
 * 每次OpenClaw重启后自动检查关键功能是否正常
 * 由 AGENTS.md 中的启动流程自动触发
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const TTS_DIR = 'C:\\temp\\tts';
const PYTHON = findPython();

function findPython() {
  const candidates = [
    'C:\\Program Files\\Python311\\python.exe',
    'C:\\Users\\lfy20\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
    'C:\\Users\\admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
  ];
  for (const p of candidates) {
    try {
      execSync(`"${p}" --version`, { stdio: 'pipe', timeout: 3000 });
      return p;
    } catch(e) {}
  }
  return 'python';
}
const SILK_SCRIPT = path.join(__dirname, 'tts_to_silk.py');

let errors = [];

function log(msg, ok = true) {
  const icon = ok ? '✅' : '❌';
  console.log(`${icon} ${msg}`);
  if (!ok) errors.push(msg);
}

function run(cmd, opts = {}) {
  try {
    return execSync(cmd, { timeout: 30000, stdio: 'pipe', ...opts }).toString().trim();
  } catch (e) {
    return null;
  }
}

console.log('═══════════════════════════════════════');
console.log('🔍 启动自检 - 语音链路');
console.log('═══════════════════════════════════════');

// 1. 检查Python
const pyVer = run(`"${PYTHON}" --version`);
if (pyVer) {
  log(`Python: ${pyVer}`);
} else {
  log('Python 不可用', false);
}

// 2. 检查edge-tts
const edgeOk = run(`"${PYTHON}" -c "import edge_tts; print('OK')"`);
log(`edge-tts: ${edgeOk || '不可用'}`, !!edgeOk);

// 3. 检查pysilk
let silkVer = null;
try {
  silkVer = run(`"${PYTHON}" -c "import pysilk; print('OK')"`);
} catch(e) {}
log(`pysilk: ${silkVer || '不可用'}`, !!silkVer);

// 4. 检查ffmpeg
const FFMPEG = 'C:\\ffmpeg\\ffmpeg-8.1.1-essentials_build\\bin\\ffmpeg.exe';
const ffOk = fs.existsSync(FFMPEG);
log(`ffmpeg: ${FFMPEG}`, ffOk);

// 5. 测试完整语音生成链路
if (edgeOk && silkVer && ffOk) {
  const testText = '测试';
  const testSilk = path.join(TTS_DIR, 'startup_test.silk');
  try {
    const result = run(`"${PYTHON}" "${SILK_SCRIPT}" "${testText}" "${testSilk}"`);
    if (result && result.startsWith('OK:') && fs.existsSync(testSilk)) {
      log(`语音生成链路测试: ${fs.statSync(testSilk).size} bytes`);
      // 清理测试文件
      try { fs.unlinkSync(testSilk); } catch(e) {}
    } else {
      log('语音生成链路测试失败', false);
    }
  } catch (e) {
    log(`语音生成链路测试异常: ${e.message}`, false);
  }
} else {
  log('语音链路组件不全，跳过测试', false);
}

// 6. 清理旧文件
if (fs.existsSync(TTS_DIR)) {
  try {
    const files = fs.readdirSync(TTS_DIR)
      .filter(f => f.startsWith('zz_') && !f.endsWith('.silk'));
    log(`可清理的旧临时文件: ${files.length}个`);
  } catch(e) {}
}

// 7. 清理旧silk文件
const oldSilkFiles = fs.existsSync(TTS_DIR) 
  ? fs.readdirSync(TTS_DIR).filter(f => f.startsWith('zz_') && f.endsWith('.silk'))
  : [];
log(`当前zz_*.silk文件: ${oldSilkFiles.length}个`);

console.log('═══════════════════════════════════════');
console.log(`📋 自检完成 - ${errors.length === 0 ? '全部正常' : errors.length + '个问题'}`);
console.log('═══════════════════════════════════════');

if (errors.length > 0) {
  console.log('\n⚠️  需要关注的问题:');
  errors.forEach(e => console.log(`  - ${e}`));
}

// 返回退出码供调用者判断
process.exit(errors.length > 0 ? 1 : 0);
