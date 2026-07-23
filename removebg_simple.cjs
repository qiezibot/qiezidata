/**
 * 一键抠图 v2 - 纯 Node.js 内置模块，无需额外依赖
 * 使用 remove.bg 公开 API（免费版每月50张）
 * 
 * 用法: node removebg_simple.cjs
 * 
 * 免费 API Key 获取: https://www.remove.bg/ 注册后获取
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const WORKSPACE = __dirname;
const API_KEY = '';  // ← 填入你的 remove.bg API Key，留空则输出指导信息

// 输出目录
const OUTPUT_DIR = path.join(WORKSPACE, '抠图结果');
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR);
}

// 获取要处理的图片
const images = fs.readdirSync(WORKSPACE).filter(f => /\.(jpg|jpeg|png)$/i.test(f));

if (images.length === 0) {
    console.log('❌ workspace 中没有找到 jpg/png 图片');
    process.exit(1);
}

console.log(`📷 找到 ${images.length} 张图片:\n`);
images.forEach((f, i) => {
    const size = (fs.statSync(path.join(WORKSPACE, f)).size / 1024).toFixed(0);
    console.log(`   ${i+1}. ${f} (${size} KB)`);
});
console.log('');

if (!API_KEY) {
    console.log('═══════════════════════════════════════════');
    console.log('  🔑 需要 remove.bg API Key');
    console.log('═══════════════════════════════════════════');
    console.log('');
    console.log('  免费获取方式:');
    console.log('  1. 打开 https://www.remove.bg/');
    console.log('  2. 注册账号');
    console.log('  3. 进入 API 页面获取 Key');
    console.log('  4. 把 Key 填到本脚本的 API_KEY 变量里');
    console.log('');
    console.log('  或者直接用网页版上传抠图:');
    console.log('  https://www.remove.bg/upload');
    console.log('');
    
    // 既然没有 API Key，直接帮用户打开网页版
    console.log('  🌐 帮你打开网页版...');
    require('child_process').exec('start https://www.remove.bg/upload');
    process.exit(0);
}

// 逐个处理
let idx = 0;
function processNext() {
    if (idx >= images.length) {
        console.log('\n🎉 全部处理完成！');
        console.log(`   输出目录: ${OUTPUT_DIR}`);
        return;
    }
    
    const imgFile = images[idx++];
    const imgPath = path.join(WORKSPACE, imgFile);
    const outName = path.basename(imgFile, path.extname(imgFile)) + '_抠图.png';
    const outPath = path.join(OUTPUT_DIR, outName);
    
    console.log(`⏳ [${idx}/${images.length}] 处理: ${imgFile}`);
    
    const imageData = fs.readFileSync(imgPath);
    
    // Boundary 分隔线
    const boundary = '----' + Math.random().toString(36).substr(2);
    
    let body = '';
    body += '--' + boundary + '\r\n';
    body += 'Content-Disposition: form-data; name="image_file"; filename="' + imgFile + '"\r\n';
    body += 'Content-Type: application/octet-stream\r\n\r\n';
    
    const bodyBuffer = Buffer.concat([
        Buffer.from(body, 'utf-8'),
        imageData,
        Buffer.from('\r\n--' + boundary + '--\r\n', 'utf-8')
    ]);
    
    const options = {
        hostname: 'api.remove.bg',
        path: '/v1.0/removebg',
        method: 'POST',
        headers: {
            'X-Api-Key': API_KEY,
            'Content-Type': 'multipart/form-data; boundary=' + boundary,
            'Content-Length': bodyBuffer.length
        }
    };
    
    const req = https.request(options, (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => {
            const buf = Buffer.concat(chunks);
            
            if (res.statusCode === 200) {
                fs.writeFileSync(outPath, buf);
                console.log(`   ✅ 完成 -> 抠图结果/${outName}`);
            } else {
                console.log(`   ❌ 失败 (${res.statusCode}): ${buf.toString()}`);
            }
            
            processNext();
        });
    });
    
    req.on('error', (e) => {
        console.log(`   ❌ 请求失败: ${e.message}`);
        processNext();
    });
    
    req.write(bodyBuffer);
    req.end();
}

processNext();
