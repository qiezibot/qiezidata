import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://sj.qq.com/appdetail/com.tencent.tmgp.dfm'
}

session = requests.Session()
url = 'http://imtt2.dd.qq.com/sjy.00008/sjy.00001/16891/apk/769CB3E1F8803B7187758450C1BF8863.apk?fsname=com.tencent.tmgp.dfm_2019.apk'
r = session.get(url, headers=headers, allow_redirects=True, timeout=30)
print(f'Final status: {r.status_code}')
print(f'Final URL: {r.url}')
print(f'Content length: {len(r.content)}')
print(f'Content-Type: {r.headers.get("Content-Type", "?")}')
if len(r.content) < 5000:
    print(f'Content preview: {r.content[:500]}')
else:
    # Save it
    import os
    path = r'C:\u-claw\portable\data\.openclaw\workspace\delta_apk\delta_force.apk'
    with open(path, 'wb') as f:
        f.write(r.content)
    size_mb = len(r.content) / 1024 / 1024
    print(f'Saved to {path} ({size_mb:.1f} MB)')
