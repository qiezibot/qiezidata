const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const pythonPath = path.join(
  process.env.LOCALAPPDATA || 'C:\\Users\\admin\\AppData\\Local',
  'Programs', 'Python', 'Python311', 'python.exe'
);
const sttScript = path.join(__dirname, 'stt_file.py');
const audioFile = process.argv[2];
const outFile = path.join(__dirname, '_stt_out.txt');

if (!audioFile) {
  console.log('Usage: node stt.js <audio_file>');
  process.exit(1);
}

try {
  execSync(
    `"${pythonPath}" "${sttScript}" "${audioFile}"`,
    { timeout: 30000, stdio: ['ignore', 'ignore', 'ignore'] }
  );
  const result = fs.readFileSync(outFile, 'utf-8').trim();
  console.log(result);
} catch(e) {
  console.error('STT Error:', e.message);
  process.exit(1);
}
