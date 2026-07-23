const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const text = process.argv[2] || '你好';
const outFile = process.argv[3] || path.join(__dirname, 'voice.wav');
const absOut = path.resolve(outFile);

const psScript = [
  'Add-Type -AssemblyName System.Speech;',
  '$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;',
  '$speak.SetOutputToWaveFile("' + absOut.replace(/\\/g, '\\\\') + '");',
  '$speak.Speak("' + text.replace(/"/g, '\\"') + '");',
  '$speak.Dispose();',
  'Write-Output "OK"'
].join('\n');

const psFile = path.join(__dirname, '_tts_temp.ps1');
fs.writeFileSync(psFile, psScript, 'utf8');
try {
  const result = execSync(
    `powershell -ExecutionPolicy Bypass -File "${psFile}"`,
    { timeout: 30000, cwd: __dirname }
  );
  console.log('Voice generated: ' + absOut);
} catch(e) {
  console.error('TTS failed:', e.message);
  process.exit(1);
} finally {
  try { fs.unlinkSync(psFile); } catch(e) {}
}
