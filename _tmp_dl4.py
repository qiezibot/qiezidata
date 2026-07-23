import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0'}
urls = [
    'https://d.apkpure.com/b/APK/com.tencent.tmgp.dfm?version=latest',
    'https://apkcombo.com/download/redirect/com.tencent.tmgp.dfm',
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        ct = r.headers.get('Content-Type', '?')
        print(f'URL: {url}')
        print(f'Status: {r.status_code}, CT: {ct}, Size: {len(r.content)}')
        print(f'Final URL: {r.url}')
        if 'apk' in ct or r.url.endswith('.apk'):
            print('FOUND APK!')
    except Exception as e:
        print(f'URL: {url} -> Error: {e}')
    print()
