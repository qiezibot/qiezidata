const https = require('https');
const TOKEN = 'Bot 1904006743.8TpCayOoGiBfAgCkJsS3fIwaFwdL4oZK';

https.get('https://api.sgroup.qq.com/gateway', {
  headers: { Authorization: TOKEN }
}, (res) => {
  let data = '';
  res.on('data', c => data += c);
  res.on('end', () => {
    console.log('Status:', res.statusCode);
    console.log('Body:', data);
  });
}).on('error', (e) => {
  console.log('Error:', e.message);
});
