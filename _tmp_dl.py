import requests, re, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://sj.qq.com/'
}

# Try the official myapp detail API
url = 'https://api.sj.qq.com/myapp/detailjson?apkName=com.tencent.tmgp.dfm'
try:
    r = requests.get(url, headers=headers, timeout=10, verify=False)
    print('API Status:', r.status_code)
    data = r.json()
    obj = data.get('obj', data)
    if isinstance(obj, dict):
        for k in ['apkUrl', 'downloadUrl', 'url', 'apkDownUrl', 'apkMd5', 'versionName', 'versionCode', 'fileSize', 'packageName']:
            if k in obj:
                print(f'{k}: {str(obj[k])[:200]}')
        print('All keys:', list(obj.keys()))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:800])
except Exception as e:
    print(f'API Error: {e}')

# Try myapp download page
print('\n--- Trying detail page ---')
url2 = 'https://sj.qq.com/myapp/detail.htm?apkName=com.tencent.tmgp.dfm'
try:
    r = requests.get(url2, headers=headers, timeout=10, verify=False)
    # Search for apk download URL patterns
    patterns = [
        r'https?://[^"\'<>]+\.apk',
        r'"apkUrl"\s*:\s*"([^"]+)"',
        r'"downloadUrl"\s*:\s*"([^"]+)"',
        r'"downUrl"\s*:\s*"([^"]+)"',
        r'apkDownUrl["\']?\s*[:=]\s*["\']([^"\']+)',
        r'__INITIAL_STATE__\s*=\s*({.*?});',
    ]
    html = r.text
    for pat in patterns:
        matches = re.findall(pat, html)
        for m in matches[:5]:
            print(f'Match ({pat[:20]}...): {str(m)[:200]}')
    print(f'HTML size: {len(html)} bytes')
except Exception as e:
    print(f'Page Error: {e}')
