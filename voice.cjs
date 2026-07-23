const { spawn } = require('child_process');
const path = require('path');
const readline = require('readline');
const fs = require('fs');

const TTS_DIR = 'C:\\temp\\tts';
if (!fs.existsSync(TTS_DIR)) fs.mkdirSync(TTS_DIR, { recursive: true });

const pythonPath = path.join(
  process.env.LOCALAPPDATA || 'C:\\Users\\admin\\AppData\\Local',
  'Programs', 'Python', 'Python311', 'python.exe'
);
const daemonScript = path.join(__dirname, 'stt_daemon.py');

// ===== STT Daemon =====
let sttProc = null;
let sttResolve = null;
let sttRl = null;

function ensureSttProc() {
  if (sttProc) return;
  
  sttProc = spawn(pythonPath, ['-u', daemonScript], {
    stdio: ['pipe', 'pipe', 'pipe'],
    windowsHide: true,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });

  sttRl = readline.createInterface({ input: sttProc.stdout });

  sttRl.on('line', (line) => {
    if (sttResolve) {
      sttResolve(line.trim());
      sttResolve = null;
    }
  });

  sttProc.on('exit', () => {
    sttProc = null;
    sttRl = null;
    if (sttResolve) {
      sttResolve('(daemon died)');
      sttResolve = null;
    }
  });
}

async function stt(audioFile) {
  return new Promise((resolve) => {
    ensureSttProc();
    sttResolve = resolve;
    sttProc.stdin.write(audioFile + '\n');
    setTimeout(() => {
      if (sttResolve) {
        sttResolve('(timeout)');
        sttResolve = null;
      }
    }, 20000);
  });
}

// ===== TTS =====
async function tts(text) {
  const outFile = path.join(TTS_DIR, `voice_${Date.now()}.mp3`);
  return new Promise((resolve, reject) => {
    const child = spawn(pythonPath, [
      '-m', 'edge_tts',
      '--voice', 'zh-CN-XiaoxiaoNeural',
      '--text', text,
      '--write-media', outFile
    ], { windowsHide: true });
    child.on('close', (code) => {
      if (code === 0) resolve(outFile);
      else reject(new Error(`TTS exit ${code}`));
    });
  });
}

// ===== CLI Mode =====
const args = process.argv.slice(2);
if (args[0] === 'stt' && args[1]) {
  stt(args[1]).then((r) => {
    process.stdout.write(r);
    process.exit(0);
  });
} else if (args[0] === 'tts' && args[1]) {
  tts(args[1]).then((f) => {
    console.log(f);
    process.exit(0);
  });
} else if (args[0] === 'bench') {
  // Benchmark: load daemon, then run 3 STTs
  (async () => {
    const files = [
      'C:\\Users\\admin\\.openclaw\\qqbot\\downloads\\97dde9bffaa50526ee849a01bc8a095a.bin',
      'C:\\Users\\admin\\.openclaw\\qqbot\\downloads\\e1abc301508172868149688728a7efab.bin',
      'C:\\Users\\admin\\.openclaw\\qqbot\\downloads\\0486058ba1a2dfa12e4d1b19450f8fe7.bin'
    ];
    for (const f of files) {
      const start = Date.now();
      const r = await stt(f);
      const ms = Date.now() - start;
      console.log(`${ms}ms -> ${r}`);
    }
    process.exit(0);
  })();
}

module.exports = { stt, tts };
