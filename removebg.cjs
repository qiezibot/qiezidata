/**
 * 一键抠图工具 - Node.js 版
 * 使用方法: node removebg.cjs [图片文件路径]
 * 不带参数则处理 workspace 下所有 jpg/png
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const WORKSPACE = __dirname;
const args = process.argv.slice(2);

// 检查 @imgly/background-removal 是否安装
function checkDeps() {
    try {
        require.resolve('@imgly/background-removal');
        return true;
    } catch {
        return false;
    }
}

// 获取要处理的图片
function getImages() {
    if (args.length > 0) {
        // 命令行指定的文件
        return args.filter(f => /\.(jpg|jpeg|png)$/i.test(f)).map(f => {
            if (path.isAbsolute(f)) return f;
            return path.join(WORKSPACE, f);
        });
    }
    
    // 默认扫描 workspace 下所有图片（排除 .removed 已处理过的）
    const images = [];
    const files = fs.readdirSync(WORKSPACE);
    for (const f of files) {
        if (/\.(jpg|jpeg|png)$/i.test(f)) {
            images.push(path.join(WORKSPACE, f));
        }
    }
    return images;
}

async function main() {
    console.log('══════════════════════════════');
    console.log('  一键抠图工具');
    console.log('══════════════════════════════\n');
    
    // 安装依赖
    if (!checkDeps()) {
        console.log('📦 首次使用，正在安装依赖（约 30 秒）...');
        execSync('npm install @imgly/background-removal', {
            cwd: WORKSPACE,
            stdio: 'inherit'
        });
        console.log('✅ 依赖安装完成\n');
    }
    
    const { removeBackground } = require('@imgly/background-removal');
    
    const images = getImages();
    if (images.length === 0) {
        console.log('❌ 没有找到图片，请把 jpg/png 图片放到 workspace 目录');
        console.log(`   ${WORKSPACE}`);
        process.exit(1);
    }
    
    console.log(`📷 找到 ${images.length} 张图片:\n`);
    images.forEach((img, i) => {
        console.log(`   ${i+1}. ${path.basename(img)} (${(fs.statSync(img).size / 1024).toFixed(0)} KB)`);
    });
    console.log('');
    
    const outputDir = path.join(WORKSPACE, '抠图结果');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
    }
    
    for (let i = 0; i < images.length; i++) {
        const imgPath = images[i];
        const imgName = path.basename(imgPath, path.extname(imgPath));
        const outputPath = path.join(outputDir, `${imgName}_抠图.png`);
        
        console.log(`⏳ [${i+1}/${images.length}] 正在处理: ${path.basename(imgPath)}`);
        
        try {
            const imageBuffer = fs.readFileSync(imgPath);
            const blob = new Blob([imageBuffer]);
            
            const resultBlob = await removeBackground(blob, {
                model: 'small',  // 小模型快一些，也可以换成 'medium'
                output: {
                    format: 'image/png',
                }
            });
            
            const arrayBuffer = await resultBlob.arrayBuffer();
            const buffer = Buffer.from(arrayBuffer);
            fs.writeFileSync(outputPath, buffer);
            
            console.log(`   ✅ 完成 -> 抠图结果/${imgName}_抠图.png`);
        } catch (err) {
            console.log(`   ❌ 失败: ${err.message}`);
        }
        
        console.log('');
    }
    
    console.log('══════════════════════════════');
    console.log('  🎉 全部处理完成！');
    console.log(`  输出目录: ${outputDir}`);
    console.log('══════════════════════════════');
}

main().catch(console.error);
