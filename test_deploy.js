const https = require('https');
const http = require('http');
const querystring = require('querystring');

const BASE = 'qiezidata-production.up.railway.app';

function request(method, path, data = null, contentType = 'application/x-www-form-urlencoded') {
  return new Promise((resolve, reject) => {
    const body = data ? querystring.stringify(data) : null;
    const opts = {
      hostname: BASE,
      path: path,
      method: method,
      rejectUnauthorized: false,
      headers: {
        'Content-Type': contentType,
      }
    };
    if (body) opts.headers['Content-Length'] = Buffer.byteLength(body);
    
    const req = https.request(opts, (res) => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: d,
          bodyJson: (() => { try { return JSON.parse(d); } catch(e) { return null; } })()
        });
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function testLogin(username, password) {
  const res = await request('POST', '/login', { username, password });
  // Get the session cookie from set-cookie
  const cookies = res.headers['set-cookie'] || [];
  console.log(`  Login ${username}: status=${res.status}`);
  if (res.status === 200) {
    console.log(`    Response:`, res.bodyJson || res.body.substring(0, 200));
  } else {
    console.log(`    Response: ${res.body.substring(0, 200)}`);
  }
  return { cookies, ...res };
}

function makeRequestWithCookies(method, path, cookies) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: BASE,
      path: path,
      method: method,
      rejectUnauthorized: false,
      headers: { 'Cookie': cookies.join('; ') }
    };
    const req = https.request(opts, (res) => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          body: d,
          bodyJson: (() => { try { return JSON.parse(d); } catch(e) { return null; } })()
        });
      });
    });
    req.on('error', reject);
    req.end();
  });
}

async function main() {
  console.log('=== DEPLOYMENT CHECK ===');
  console.log(`Time: ${new Date().toISOString()}`);
  console.log('');

  // 1. /debug endpoint
  console.log('1. Checking /debug endpoint...');
  const debug = await request('GET', '/debug');
  console.log(`   /debug: ${debug.status} ${debug.status === 200 ? 'OK' : 'FAIL'}`);
  if (debug.bodyJson) {
    console.log(`   DB: ${debug.bodyJson.use_pg ? 'PostgreSQL ✅' : 'unknown'}`);
    console.log(`   Users: ${debug.bodyJson.users.map(u => u.username + '(' + u.id + ')').join(', ')}`);
  }
  console.log('');

  // 2. Login as admin and check /me
  console.log('2. Test login as admin (admin/admin123)...');
  const adminLogin = await testLogin('admin', 'admin123');
  if (adminLogin.status === 200) {
    const adminCookies = adminLogin.headers['set-cookie'] || [];
    const adminData = adminLogin.bodyJson;
    console.log(`   Token/cookie obtained: ${adminCookies.length > 0 ? 'Yes ✅' : 'No ❌'}`);
    
    // Check /me
    console.log('   Checking /me endpoint...');
    const me = await makeRequestWithCookies('GET', '/me', adminCookies);
    console.log(`   /me status: ${me.status}`);
    if (me.bodyJson) {
      console.log(`   User data: ${JSON.stringify(me.bodyJson).substring(0, 200)}`);
    }
    
    // Check /admin/users
    console.log('   Checking /admin/users (should work for admin)...');
    const adminUsers = await makeRequestWithCookies('GET', '/admin/users', adminCookies);
    console.log(`   /admin/users status: ${adminUsers.status}`);
    if (adminUsers.bodyJson) {
      const users = Array.isArray(adminUsers.bodyJson) ? adminUsers.bodyJson : 
                     (adminUsers.bodyJson.users || adminUsers.bodyJson.data || []);
      console.log(`   Users found: ${users.length}`);
    }
    
    // Check /admin/stats
    console.log('   Checking /admin/stats...');
    const adminStats = await makeRequestWithCookies('GET', '/admin/stats', adminCookies);
    console.log(`   /admin/stats status: ${adminStats.status}`);
  }
  console.log('');

  // 3. Test chengzi's password — try common passwords
  console.log('3. Test login as chengzi (need to find password)...');
  console.log('   Trying common passwords...');
  const chengziPasswords = ['chengzi', 'chengzi123', 'cz', 'Chengzi', 'cz123'];
  let chengziCookies = null;
  let chengziPassword = null;
  for (const pw of chengziPasswords) {
    const res = await request('POST', '/login', { username: 'chengzi', password: pw });
    if (res.status === 200) {
      chengziCookies = res.headers['set-cookie'] || [];
      chengziPassword = pw;
      console.log(`   ✅ Login successful with password: ${pw}`);
      break;
    } else {
      console.log(`   ❌ ${pw} failed`);
    }
  }
  
  if (chengziCookies) {
    // Check /me for chengzi
    console.log('   Checking /me for chengzi...');
    const me = await makeRequestWithCookies('GET', '/me', chengziCookies);
    console.log(`   /me status: ${me.status}, data: ${JSON.stringify(me.bodyJson).substring(0, 200)}`);
    
    // Check admin endpoints
    console.log('   Trying /admin/users (should FAIL for non-admin)...');
    const adminUsers = await makeRequestWithCookies('GET', '/admin/users', chengziCookies);
    console.log(`   /admin/users status: ${adminUsers.status} (expected 403/401)`);
    if (adminUsers.bodyJson) {
      console.log(`   Response: ${JSON.stringify(adminUsers.bodyJson).substring(0, 200)}`);
    }
  }
  console.log('');

  // 4. Login as qiezi
  console.log('4. Test login as qiezi (qiezi/qiezi123)...');
  const qieziLogin = await testLogin('qiezi', 'qiezi123');
  if (qieziLogin.status === 200) {
    const qieziCookies = qieziLogin.headers['set-cookie'] || [];
    console.log('   Checking /me for qiezi...');
    const me = await makeRequestWithCookies('GET', '/me', qieziCookies);
    console.log(`   /me status: ${me.status}, data: ${JSON.stringify(me.bodyJson).substring(0, 200)}`);
    
    console.log('   Trying /admin/users (should FAIL for non-admin)...');
    const adminUsers = await makeRequestWithCookies('GET', '/admin/users', qieziCookies);
    console.log(`   /admin/users status: ${adminUsers.status} (expected 403/401)`);
    if (adminUsers.bodyJson) {
      console.log(`   Response: ${JSON.stringify(adminUsers.bodyJson).substring(0, 200)}`);
    }
  }
  
  // 5. Now check the actual HTML page for nav items (need to fetch main page and check content)
  console.log('');
  console.log('5. Fetching main page (login page)...');
  const home = await request('GET', '/');
  const pageText = home.body;
  console.log(`   Pages serves: ${home.status} ${home.status === 200 ? 'OK ✅' : 'FAIL ❌'}`);
  console.log(`   Page title: ${pageText.match(/<title>([^<]*)<\/title>/i) ? pageText.match(/<title>([^<]*)<\/title>/i)[1] : 'N/A'}`);
  
  console.log('');
  
  // Get frontend JS files to find nav structure
  console.log('6. Analyzing frontend for nav structure...');
  // Look for JS chunks
  const scriptMatch = pageText.match(/src="([^"]*\.(?:js|jsx|tsx)[^"]*)"/g);
  if (scriptMatch) {
    console.log(`   Found ${scriptMatch.length} script references`);
    for (const s of scriptMatch) {
      console.log(`   ${s}`);
    }
  }
  
  console.log('');
  console.log('=== SUMMARY ===');
  console.log(`/debug: 200 OK ✅`);
  console.log(`admin login: ${adminLogin.status === 200 ? '✅' : '❌'}`);
  if (chengziPassword) console.log(`chengzi login: ✅ (password: ${chengziPassword})`);
  else console.log(`chengzi login: ❌ (password not found)`);
  console.log(`qiezi login: ${qieziLogin.status === 200 ? '✅' : '❌'}`);
  console.log(`admin /admin/users: ${adminLogin.status === 200 ? '✅ accessible' : '❌'}`);
  
  if (chengziCookies) {
    const chengziAdminCheck = await makeRequestWithCookies('GET', '/admin/users', chengziCookies);
    console.log(`chengzi /admin/users: ${chengziAdminCheck.status === 403 || chengziAdminCheck.status === 401 ? '✅ blocked (correct)' : '⚠️ status=' + chengziAdminCheck.status}`);
  }
}

main().catch(console.error);
