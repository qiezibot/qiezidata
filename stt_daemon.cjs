const { spawn } = require('child_process');
const path = require('path');
const readline = require('readline');

const pythonPath = path.join(
  process.env.LOCALAPPDATA || 'C:\\Users\\admin\\AppData\\Local',
  'Programs', 'Python', 'Python311', 'python.exe'
);
const daemonScript = path.join(__dirname, 'stt_daemon.py');

// Start Python daemon process once
const daemon = spawn(pythonPath, [daemonScript], {
  stdio: ['pipe', 'pipe', 'ignore'],
  encoding: 'utf-8',
  windowsHide: true
});

const rl = readline.createInterface({ input: daemon.stdout });
let pendingResolve = null;

rl.on('line', (line) => {
  if (pendingResolve) {
    pendingResolve(line.trim());
    pendingResolve = null;
  }
});

daemon.on('exit', (code) => {
  console.error('STT daemon exited:', code);
  process.exit(1);
});

function stt(audioFile) {
  return new Promise((resolve, reject) => {
    pendingResolve = resolve;
    daemon.stdin.write(audioFile + '\n');
    setTimeout(() => {
      if (pendingResolve) {
        pendingResolve('(timeout)');
        pendingResolve = null;
      }
    }, 15000);
  });
}

// CLI mode: single file
const audioFile = process.argv[2];
if (audioFile) {
  stt(audioFile).then((text) => {
    console.log(text);
    process.exit(0);
  });
}

module.exports = { stt };
