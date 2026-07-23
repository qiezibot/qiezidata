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

async function testUser(username, password) {
  const base = 'https://qiezidata-production.up.railway.app';
  const loginData = 'username=' + encodeURIComponent(username) + '&password=' + encodeURIComponent(password);
  
  console.log('=== Login as ' + username + ' (pw: ' + password + ') ===');
  let loginResp = await request('POST', base + '/login', loginData);
  console.log('Status:', loginResp.status, '| Location:', loginResp.headers['location']);
  
  let cookie = loginResp.headers['set-cookie'];
  if (cookie) cookie = cookie.map(c => c.split(';')[0]).join('; ');
  
  if (!cookie) {
    console.log('Login failed - no cookie');
    return { success: false, content: '' };
  }
  
  console.log('Cookie:', cookie.substring(0, 60) + '...');
  console.log('=== Home page ===');
  let homeResp = await request('GET', base + '/', null, null, cookie);
  console.log('Status:', homeResp.status, '| Length:', homeResp.body.length);
  
  return { success: true, content: homeResp.body };
}

async function main() {
  // Step 0: Check debug endpoint
  console.log('=== DEBUG ENDPOINT ===');
  const debugResp = await request('GET', 'https://qiezidata-production.up.railway.app/debug');
  console.log('Debug status:', debugResp.status, '| OK:', debugResp.status === 200);
  
  // Check chengzi password from debug
  console.log('\nDebug body (partial):', debugResp.body.substring(0, 500));
  
  // Test admin first
  let admin = await testUser('admin', 'admin123');
  if (admin.success) {
    let body = admin.content;
    const hasUserMgmt = body.includes('用户管理');
    const hasDashboard = body.includes('仪表盘');
    console.log('\n<<< ADMIN RESULTS >>>');
    console.log('Contains 用户管理:', hasUserMgmt);
    console.log('Contains 仪表盘:', hasDashboard);
    
    // Extract all nav items
    const navLines = body.match(/<div class="nav-item[^>]*>[\s\S]*?<\/div>/g) || [];
    console.log('\nNav items found:');
    navLines.forEach(function(n) {
      var text = n.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
      if (text) console.log('  -', text);
    });
  }
  
  // Try chengzi with different passwords
  console.log('\n========================================');
  console.log('Testing chengzi...');
  var passwords = ['chengzi', 'chengzi123', '123456', 'qiezidata', 'eggplant'];
  
  for (var i = 0; i < passwords.length; i++) {
    var result = await testUser('chengzi', passwords[i]);
    if (result.success && result.content) {
      var body = result.content;
      console.log('\n<<< CHENGZI RESULTS (pw: ' + passwords[i] + ') >>>');
      console.log('Contains 用户管理:', body.includes('用户管理'));
      console.log('Contains 仪表盘:', body.includes('仪表盘'));
      console.log('Contains 文件管理:', body.includes('文件管理'));
      console.log('Contains 文件上传:', body.includes('上传'));
      
      var navLines = body.match(/<div class="nav-item[^>]*>[\s\S]*?<\/div>/g) || [];
      console.log('\nNav items found:');
      navLines.forEach(function(n) {
        var text = n.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
        if (text) console.log('  -', text);
      });
      break;
    }
  }
  
  // Test qiezi
  console.log('\n========================================');
  var qiezi = await testUser('qiezi', 'qiezi123');
  if (qiezi.success && qiezi.content) {
    var body = qiezi.content;
    console.log('\n<<< QIEZI RESULTS >>>');
    console.log('Contains 用户管理:', body.includes('用户管理'));
    console.log('Contains 仪表盘:', body.includes('仪表盘'));
    console.log('Contains 文件管理:', body.includes('文件管理'));
    
    var navLines = body.match(/<div class="nav-item[^>]*>[\s\S]*?<\/div>/g) || [];
    console.log('\nNav items found:');
    navLines.forEach(function(n) {
      var text = n.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
      if (text) console.log('  -', text);
    });
  }
  
  console.log('\n=== TESTS COMPLETE ===');
}

main().catch(console.error);
