const fs = require('fs');
const b64 = fs.readFileSync('source.jpg').toString('base64');
console.log('B64_LENGTH:', b64.length);
fs.writeFileSync('image_b64.txt', b64);
console.log('Done');
