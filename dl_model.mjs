import { writeFile, mkdir } from 'fs/promises';
const url = 'https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip';
const out = 'vosk-model-small-cn-0.22.zip';

console.log('Downloading Vosk model (42MB)...');
const res = await fetch(url);
const chunks = [];
let total = 0;
const reader = res.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  chunks.push(value);
  total += value.length;
  process.stdout.write('\r' + (total/1024/1024).toFixed(1) + 'MB');
}
const buf = Buffer.concat(chunks);
await writeFile(out, buf);
console.log('\nOK: ' + (buf.length/1024/1024).toFixed(1) + 'MB downloaded');
