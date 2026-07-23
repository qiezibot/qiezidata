const fs = require('fs');
const https = require('https');

const urls = [
  'https://p3-flow-imagex-sign.byteimg.com/tos-cn-i-a9rns2rl98/rc_gen_image/eb042491e19e4024a89041bb26e816ed.jpeg',
  'https://p3-flow-imagex-sign.byteimg.com/tos-cn-i-a9rns2rl98/rc_gen_image/eb042491e19e4024a89041bb26e816ed.jpeg~tplv-a9rns2rl98-downsize_watermark_1_5_b.png?lk3s=8e244e95&rcl=2026051422192859FE2E1CA6805B253DC7&rrcfp=827586d3&x-expires=2094128383&x-signature=JbfbXMeQdmqZ87eei%2BjsFQNiK7U%3D'
];

function download(url, filename) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      if (res.statusCode !== 200) {
        console.log(`Status ${res.statusCode} for ${filename}`);
        // Handle redirect
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          console.log(`Redirect to ${res.headers.location}`);
          download(res.headers.location, filename).then(resolve).catch(reject);
          return;
        }
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }
      const ws = fs.createWriteStream(filename);
      res.pipe(ws);
      ws.on('finish', () => {
        const size = fs.statSync(filename).size;
        console.log(`Downloaded ${filename}: ${size} bytes`);
        resolve(size);
      });
    }).on('error', reject);
  });
}

async function main() {
  await download(urls[0], 'result_hd.jpg');
  await download(urls[1], 'result_watermark.png');
  console.log('All done');
}

main().catch(console.error);
