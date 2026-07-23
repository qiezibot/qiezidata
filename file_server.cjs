// 启动一个临时HTTP服务器，提供图片文件
// 然后在豆包页面通过fetch获取图片并上传

const http = require('http');
const fs = require('fs');
const path = require('path');

const FILE_PATH = 'E:\\openclaw压缩包及启动教程\\u-claw\\portable\\data\\.openclaw\\workspace\\source.jpg';
const PORT = 18765;

const server = http.createServer((req, res) => {
  if (req.url === '/image.jpg') {
    const img = fs.readFileSync(FILE_PATH);
    res.writeHead(200, { 
      'Content-Type': 'image/jpeg',
      'Access-Control-Allow-Origin': '*',
      'Content-Length': img.length
    });
    res.end(img);
    console.log('Image served');
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`File server running on http://127.0.0.1:${PORT}/image.jpg`);
  console.log('Press Ctrl+C to stop');
});

// Auto-stop after 30 seconds
setTimeout(() => {
  server.close();
  process.exit(0);
}, 30000);
