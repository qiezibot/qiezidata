const fs = require('fs');
const path = require('path');

const indexPath = path.join('E:', 'openclaw压缩包及启动教程', 'u-claw', 'portable', 'data', '.openclaw', 'extensions', 'qqbot', 'dist', 'index.js');
const relBase = '../../../app/core/node_modules/openclaw';

let content = fs.readFileSync(indexPath, 'utf8');
// Replace bare "openclaw" imports with relative paths
content = content.replace(/from "openclaw\//g, `from "${relBase}/`);
content = content.replace(/from 'openclaw\//g, `from '${relBase}/`);
content = content.replace(/require\("openclaw\//g, `require("${relBase}/`);
content = content.replace(/require\('openclaw\//g, `require('${relBase}/`);

fs.writeFileSync(indexPath, content);
console.log('Patched qqbot index.js successfully');
console.log('New import lines:');
content.split('\n').filter(l => l.includes('openclaw')).forEach(l => console.log('  ' + l.trim()));
