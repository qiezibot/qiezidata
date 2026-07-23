// 测试QQ API token是否能获取
const appId = '1904006743';
const clientSecret = '9PgxFYrBVqBXtGd1QpFf6XzRuNrMrNtQ';

async function main() {
  // 尝试获取access_token
  const url = `https://api.qq.com/v1/apps/${appId}/token`;
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appId, clientSecret })
    });
    const text = await resp.text();
    console.log('Status:', resp.status);
    console.log('Response:', text.slice(0, 500));
    try {
      const json = JSON.parse(text);
      if (json.access_token) {
        console.log('TOKEN OK! First 20 chars:', json.access_token.slice(0, 20));
      }
    } catch(e) {
      console.log('Not JSON');
    }
  } catch(e) {
    console.log('Fetch error:', e.message);
  }
}

main();
