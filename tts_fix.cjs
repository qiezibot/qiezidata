// tts_fix.cjs - 修复后的 TTS 调用（改用 https 请求）
const https = require('https');
const fs = require('fs');
const path = require('path');

// 直接用 rest 请求微软 TTS API
async function tts(text, outFile) {
    const ssml = `<speak version="1.0" xml:lang="zh-CN">
        <voice name="zh-CN-XiaoxiaoNeural">${text}</voice>
    </speak>`;

    const req = https.request({
        hostname: 'eastus.tts.speech.microsoft.com',
        path: '/cognitiveservices/v1',
        method: 'POST',
        headers: {
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'audio-16khz-32kbitrate-mono-mp3',
            'User-Agent': 'Mozilla/5.0'
        }
    });

    // 如果不需要 API key 的话用 edge-tts 的 endpoint
    // 但 edge-tts 的 endpoint 是 speech.platform.bing.com
    // 那是个 websocket 连接...

    // 改用 edge-tts 的 REST API
    // 实际上 edge-tts 用的是 wss，不方便直接在 Node 里重现
    // 还是走 python 子进程吧

    const { execSync } = require('child_process');
    try {
        execSync(`python -c "import asyncio; import edge_tts; asyncio.run(edge_tts.Communicate('${text.replace(/'/g,"\\'")}', 'zh-CN-XiaoxiaoNeural').save('${outFile.replace(/\\/g,'/')}'))"`, {
            timeout: 20000,
            stdio: 'pipe'
        });
        return true;
    } catch(e) {
        console.error('TTS failed:', e.message);
        return false;
    }
}

// CLI
const text = process.argv[2] || '你好';
const out = process.argv[3] || path.join(__dirname, 'voice.mp3');
tts(text, out).then(ok => {
    if (ok) console.log('OK:' + out + ':' + fs.statSync(out).size);
    else process.exit(1);
});
