// encode_silk.cjs - 用 silk-wasm 编码 silk 语音
// 从 qqbot 插件里找 silk-wasm
const path = require('path');
const fs = require('fs');

// 查找 silk-wasm 位置
function findSilkWasm() {
    const candidates = [
        path.join(__dirname, '..', 'app', 'core', 'node_modules', '@sliverp', 'qqbot', 'node_modules', 'silk-wasm'),
        path.join(__dirname, '..', '..', 'app', 'core', 'node_modules', '@sliverp', 'qqbot', 'node_modules', 'silk-wasm'),
        'C:\\U-Claw\\app\\core\\node_modules\\@sliverp\\qqbot\\node_modules\\silk-wasm',
    ];
    for (const c of candidates) {
        if (fs.existsSync(path.join(c, 'package.json'))) return c;
    }
    return null;
}

const silkPath = findSilkWasm();
if (!silkPath) {
    console.error('ERR: silk-wasm not found');
    process.exit(1);
}

async function main() {
    const wavPath = process.argv[2];
    const outPath = process.argv[3] || wavPath.replace('.wav', '.silk');
    
    // 需要从 silk-wasm 目录 require
    const silkWasm = require(path.join(silkPath));
    const wavBuf = fs.readFileSync(wavPath);
    const silk = await silkWasm.encode(wavBuf, 24000);
    fs.writeFileSync(outPath, Buffer.from(silk.data));
    console.log(`OK:${outPath}:${silk.data.length}:${silk.duration}ms`);
}

main().catch(e => { console.error('ERR:' + e.message); process.exit(1); });
