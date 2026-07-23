// tts-edge.cjs - 真实语音生成（edge-tts）
// 用法: node tts-edge.cjs "要说的文字" 输出文件.wav
// 用独立的Python脚本执行edge-tts，避免Node调用Python的阻塞问题

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const text = process.argv[2] || '你好';
const outFile = process.argv[3] || path.join(__dirname, 'voice.wav');
const dir = path.dirname(outFile);

if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}

// 查找Python
function findPython() {
  const candidates = [
    'python', 'python3',
    'C:\\Program Files\\Python311\\python.exe',
    'C:\\Users\\lfy20\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
    'C:\\Users\\admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
  ];
  for (const p of candidates) {
    try {
      execSync(`"${p}" --version`, { stdio: 'pipe', timeout: 3000 });
      return p;
    } catch (e) { /* try next */ }
  }
  return 'python';
}

const python = findPython();

// 使用edge-tts Python lib生成语音
// edge-tts 直接输出WAV（或MP3），需要先安装: pip install edge-tts
const pyScript = `
import asyncio
import edge_tts
import sys

async def main():
    text = sys.argv[1]
    out_file = sys.argv[2]
    communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
    await communicate.save(out_file)
    print(f"OK:{out_file}")

asyncio.run(main())
`;

const tmpScript = path.join(dir, '_tts_gen.py');
fs.writeFileSync(tmpScript, pyScript);

try {
  const result = execSync(
    `"${python}" "${tmpScript}" "${text}" "${outFile}"`,
    { timeout: 15000, stdio: ['pipe', 'pipe', 'pipe'] }
  );
  console.log(result.toString().trim());
  // 清理临时脚本
  try { fs.unlinkSync(tmpScript); } catch(e) {}
} catch (e) {
  console.error(`edge-tts error: ${e.message}`);
  // fallback: 写静音文件让插件不卡
  const sampleRate = 24000;
  const numSamples = Math.floor(sampleRate * 0.5);
  const dataSize = numSamples * 2;
  const buf = Buffer.alloc(44 + dataSize);
  buf.write('RIFF', 0);
  buf.writeUInt32LE(36 + dataSize, 4);
  buf.write('WAVE', 8);
  buf.write('fmt ', 12);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20);
  buf.writeUInt16LE(1, 22);
  buf.writeUInt32LE(sampleRate, 24);
  buf.writeUInt32LE(sampleRate * 2, 28);
  buf.writeUInt16LE(2, 32);
  buf.writeUInt16LE(16, 34);
  buf.write('data', 36);
  buf.writeUInt32LE(dataSize, 40);
  fs.writeFileSync(outFile, buf);
  console.log('FALLBACK:' + outFile);
}
