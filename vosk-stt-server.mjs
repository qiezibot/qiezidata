/**
 * Vosk STT Server — 把离线 Vosk 包装成 OpenAI 兼容的 /v1/audio/transcriptions 接口
 *
 * 启动: node vosk-stt-server.mjs [端口号]
 * 默认端口: 18766
 *
 * 接口: POST /v1/audio/transcriptions
 * 参数 (multipart/form-data):
 *   - file: 音频文件
 *   - model: (可选，忽略)
 * 返回: { text: "..." }
 */

import http from 'node:http';
import { spawn } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { writeFile, unlink, mkdtemp } from 'node:fs/promises';
import { createWriteStream, createReadStream, existsSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = parseInt(process.argv[2] || '18766', 10);

// Python + 脚本路径
const PYTHON = join(
  process.env.LOCALAPPDATA || 'C:\\Users\\admin\\AppData\\Local',
  'Programs', 'Python', 'Python311', 'python.exe'
);
const STT_SCRIPT = join(__dirname, 'stt_file.py');

// 测试 Python 和 Vosk 是否就绪
async function healthCheck() {
  return new Promise((resolve) => {
    const proc = spawn(PYTHON, ['-c', `
import vosk, json, sys
m = vosk.Model(r'C:\\vosk-model-small-cn-0.22')
print("ok:" + m.__class__.__name__)
`, '--cwd', __dirname], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });
    let out = '';
    proc.stdout.on('data', d => out += d.toString());
    proc.on('close', code => {
      if (code === 0 && out.startsWith('ok:')) {
        resolve(true);
      } else {
        console.error('[health] Vosk init failed:', out);
        resolve(false);
      }
    });
    proc.on('error', e => {
      console.error('[health] Spawn error:', e.message);
      resolve(false);
    });
  });
}

// 解析 multipart/form-data（极简版，只取第一个 file 字段）
function parseMultipart(buffer, boundary) {
  const parts = [];
  const delimiter = Buffer.from(`--${boundary}`);
  const endDelimiter = Buffer.from(`--${boundary}--`);
  
  let start = 0;
  while (start < buffer.length) {
    // 找分隔符
    const sepIdx = buffer.indexOf(delimiter, start);
    if (sepIdx === -1) break;
    const partStart = sepIdx + delimiter.length;
    
    // 跳过分隔符后的 \r\n
    let contentStart = partStart;
    if (buffer[contentStart] === 0x0D) contentStart += 2; // \r\n
    
    // 找下一个分隔符或结束符
    let nextSep = buffer.indexOf(delimiter, contentStart);
    if (nextSep === -1) break;
    
    // 检查是否是结束符
    const checkEnd = buffer.slice(nextSep, nextSep + endDelimiter.length);
    if (checkEnd.equals(endDelimiter)) {
      parts.push(buffer.slice(contentStart, nextSep - 2)); // 去掉尾部 \r\n
      break;
    }
    
    parts.push(buffer.slice(contentStart, nextSep - 2));
    start = nextSep;
  }
  
  // 解析每个 part 的 header 和 body
  for (const part of parts) {
    const headerEnd = part.indexOf(Buffer.from('\r\n\r\n'));
    if (headerEnd === -1) continue;
    
    const header = part.slice(0, headerEnd).toString('utf-8');
    const body = part.slice(headerEnd + 4);
    
    // 检查是否是 file 字段
    if (header.includes('name="file"')) {
      return body;
    }
  }
  return null;
}

async function handleTranscribe(req, res) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
    if (chunks.reduce((a, b) => a + b.length, 0) > 50 * 1024 * 1024) {
      res.writeHead(413, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'File too large (max 50MB)' }));
      return;
    }
  }
  
  const body = Buffer.concat(chunks);
  const contentType = req.headers['content-type'] || '';
  const boundaryMatch = contentType.match(/boundary=([^;]+)/);
  
  if (!boundaryMatch) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Expected multipart/form-data' }));
    return;
  }
  
  const fileData = parseMultipart(body, boundaryMatch[1].trim());
  if (!fileData) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'No file field found in upload' }));
    return;
  }
  
  // 写临时文件
  const tmpDir = await mkdtemp(join(tmpdir(), 'vosk-stt-'));
  const tmpFile = join(tmpDir, 'input.wav');
  await writeFile(tmpFile, fileData);
  
  // 调用 Vosk STT
  const outFile = join(__dirname, '_stt_out.txt');
  
  try {
    await new Promise((resolve, reject) => {
      const proc = spawn(PYTHON, [STT_SCRIPT, tmpFile], {
        stdio: ['ignore', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
        timeout: 30000
      });
      let err = '';
      proc.stderr.on('data', d => err += d.toString());
      proc.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Vosk exited with code ${code}: ${err.slice(0, 200)}`));
      });
      proc.on('error', reject);
    });
    
    const { readFileSync } = await import('node:fs');
    let text = readFileSync(outFile, 'utf-8').trim();
    
    // 清理临时文件
    await unlink(tmpFile);
    await unlink(outFile).catch(() => {});
    
    // 如果识别为空，给个有意义的回复
    if (!text || text === '(no speech)') {
      text = '';
    }
    
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(JSON.stringify({ text }));
  } catch (err) {
    // 清理
    await unlink(tmpFile).catch(() => {});
    
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: err.message }));
  }
}

// 启动服务器
const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }
  
  // 路由
  const url = new URL(req.url, `http://${req.headers.host}`);
  const path = url.pathname;
  
  if (req.method === 'POST' && (path === '/v1/audio/transcriptions' || path === '/audio/transcriptions')) {
    handleTranscribe(req, res);
  } else if (path === '/health' || path === '/') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', service: 'vosk-stt-server' }));
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
  }
});

// 先做健康检查再启动
console.log('🔍 Checking Vosk health...');
const healthy = await healthCheck();
if (!healthy) {
  console.error('❌ Vosk model not ready. Make sure C:\\vosk-model-small-cn-0.22 exists.');
  process.exit(1);
}

server.listen(PORT, '127.0.0.1', () => {
  console.log(`✅ Vosk STT Server running on http://127.0.0.1:${PORT}`);
  console.log(`   POST /v1/audio/transcriptions (multipart/form-data, field: file)`);
});
