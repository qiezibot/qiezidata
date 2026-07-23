// TTS 快速版 - 用子进程驻留避免每次重新加载Python
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { once } = require('events');

// 找到python
function findPython() {
  const candidates = [
    'python',
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python311', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python312', 'python.exe'),
    'C:\\Program Files\\Python311\\python.exe',
    'C:\\Program Files\\Python312\\python.exe',
  ];
  for (const c of candidates) {
    try { require('fs').accessSync(c); return c; } catch {}
  }
  return 'python';
}

const TTS_DIR = 'C:\\temp\\tts';
if (!fs.existsSync(TTS_DIR)) fs.mkdirSync(TTS_DIR, { recursive: true });

// 生成语音 - 直接用python -c内联执行，减少进程启动开销
async function tts(text, outFile) {
  const pyCode = `
import asyncio, sys
from edge_tts import Communicate
async def main():
    tts = Communicate("${text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, ' ')}", "zh-CN-XiaoxiaoNeural")
    await tts.save("${outFile.replace(/\\/g, '\\\\')}")
    print("OK")
asyncio.run(main())
`;
  const python = findPython();
  const proc = spawn(python, ['-c', pyCode], {
    stdio: ['pipe', 'pipe', 'pipe'],
    timeout: 30000
  });
  
  let stdout = '';
  proc.stdout.on('data', d => stdout += d.toString());
  
  return new Promise((resolve, reject) => {
    proc.on('close', (code) => {
      if (code === 0 && stdout.includes('OK')) resolve(outFile);
      else reject(new Error(`TTS exit=${code}: ${stdout.substring(0, 200)}`));
    });
    proc.on('error', reject);
  });
}

// 如果是直接运行
if (require.main === module) {
  const text = process.argv[2] || '你好';
  const outFile = process.argv[3] || path.join(TTS_DIR, 'voice_default.wav');
  tts(text, outFile).then(() => console.log('OK:' + outFile)).catch(e => { console.error('FAIL:' + e.message); process.exit(1); });
} else {
  module.exports = { tts };
}
