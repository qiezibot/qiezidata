// 启动后修复QQ机器人的依赖链
const fs = require('fs');
const path = require('path');

const qqbotDir = path.join(__dirname, '..', 'extensions', 'qqbot');
const coreNodeModules = path.join(__dirname, '..', '..', '..', 'app', 'core', 'node_modules');
const targetNodeModules = path.join(qqbotDir, 'node_modules');

// 需要复制的依赖
const deps = ['openclaw', 'typescript'];

for (const dep of deps) {
  const src = path.join(coreNodeModules, dep);
  const dst = path.join(targetNodeModules, dep);
  
  if (!fs.existsSync(dst)) {
    console.log(`复制 ${dep}...`);
    copyRecursive(src, dst);
    console.log(`  ✅ ${dep} 已复制`);
  } else {
    console.log(`  ✅ ${dep} 已存在`);
  }
}

function copyRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyRecursive(srcPath, dstPath);
    } else {
      if (!fs.existsSync(dstPath)) {
        fs.copyFileSync(srcPath, dstPath);
      }
    }
  }
}

console.log('\nQQBot 修复完成！');
