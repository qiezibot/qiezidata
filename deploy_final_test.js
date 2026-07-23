const https = require('https');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

function request(method, url, body, contentType, cookie) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const headers = { 'Content-Type': contentType || 'application/x-www-form-urlencoded' };
    if (body) headers['Content-Length'] = Buffer.byteLength(body);
    if (cookie) headers['Cookie'] = cookie;
    
    const opts = {
      hostname: u.hostname, path: u.pathname + (u.search || ''), method: method,
      headers: headers, rejectUnauthorized: false
    };
    
    const req = https.request(opts, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function main() {
  // Get admin page
  var loginResp = await request('POST', 'https://qiezidata-production.up.railway.app/login', 'username=admin&password=admin123');
  var cookie = loginResp.headers['set-cookie'];
  if (cookie) cookie = cookie.map(function(c) { return c.split(';')[0]; }).join('; ');
  
  var homeResp = await request('GET', 'https://qiezidata-production.up.railway.app/', null, null, cookie);
  var adminBody = homeResp.body;
  
  console.log('=== ADMIN PAGE ANALYSIS ===');
  console.log('Contains _USER:', adminBody.includes('_USER'));
  
  var idx = adminBody.indexOf('_USER');
  if (idx > -1) {
    console.log('Context around _USER:');
    console.log(adminBody.substring(Math.max(0, idx-200), Math.min(adminBody.length, idx+200)));
  }
  
  var navItems = adminBody.match(/switchPage\('([^']+)'/g);
  if (navItems) {
    console.log('\nAdmin nav items:');
    navItems.forEach(function(n) {
      var page = n.replace("switchPage('", "").replace("'", "");
      console.log('  - ' + page);
    });
  }
  
  // Get chengzi page
  var loginResp2 = await request('POST', 'https://qiezidata-production.up.railway.app/login', 'username=chengzi&password=chengzi123');
  var cookie2 = loginResp2.headers['set-cookie'];
  if (cookie2) cookie2 = cookie2.map(function(c) { return c.split(';')[0]; }).join('; ');
  
  var homeResp2 = await request('GET', 'https://qiezidata-production.up.railway.app/', null, null, cookie2);
  var chengziBody = homeResp2.body;
  
  console.log('\n=== CHENGZI PAGE ANALYSIS ===');
  console.log('Contains _USER:', chengziBody.includes('_USER'));
  
  var idx2 = chengziBody.indexOf('_USER');
  if (idx2 > -1) {
    console.log('Context around _USER:');
    console.log(chengziBody.substring(Math.max(0, idx2-200), Math.min(chengziBody.length, idx2+200)));
  }
  
  var navItems2 = chengziBody.match(/switchPage\('([^']+)'/g);
  if (navItems2) {
    console.log('\nChengzi nav items:');
    navItems2.forEach(function(n) {
      var page = n.replace("switchPage('", "").replace("'", "");
      console.log('  - ' + page);
    });
  }
  
  // Check for Jinja2 template syntax
  var jinja2 = adminBody.match(/\{\{.*?\}\}|\{%.*?%\}/g);
  if (jinja2) {
    console.log('\nJinja2 template tags in admin:');
    jinja2.forEach(function(j) { console.log('  ' + j); });
  }
  
  var jinja2b = chengziBody.match(/\{\{.*?\}\}|\{%.*?%\}/g);
  if (jinja2b) {
    console.log('\nJinja2 template tags in chengzi:');
    jinja2b.forEach(function(j) { console.log('  ' + j); });
  }
  
  // Summary comparison
  console.log('\n========================================');
  console.log('=== FINAL COMPARISON ===');
  console.log('Admin sees 用户管理:', adminBody.includes('用户管理'));
  console.log('Admin sees 仪表盘:', adminBody.includes('仪表盘'));
  console.log('Chengzi sees 用户管理:', chengziBody.includes('用户管理'));
  console.log('Chengzi sees 仪表盘:', chengziBody.includes('仪表盘'));
  console.log('Admin page length:', adminBody.length);
  console.log('Chengzi page length:', chengziBody.length);
  console.log('Pages are identical:', adminBody === chengziBody);
}

main().catch(console.error);
