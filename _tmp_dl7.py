import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
# Try APKPure download API endpoint
url = 'https://apkpure.net/delta-force-hawk-ops-cn/com.tencent.tmgp.dfm/download'
r = requests.get(url, headers=headers, timeout=15)
html = r.text

# Look for the version info in JSON-like data
json_patterns = [
    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
    r'<script[^>]*>var\s+\w+\s*=\s*({.*?version.*?});',
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>({.*?})</script>',
]
for pat in json_patterns:
    m = re.search(pat, html, re.DOTALL)
    if m:
        data = m.group(1)
        print(f'Found JSON data ({len(data)} chars)')
        # Extract version and download URL
        versions = re.findall(r'version[^:]*:\s*["\']([^"\']+)["\']', data)
        print('Versions:', versions[:5])
        urls_found = re.findall(r'url[^:]*:\s*["\']([^"\']+apk[^"\']+)["\']', data)
        print('URLs:', urls_found[:5])
        apk_urls = re.findall(r'["\'](https?://[^"\']+\.apk[^"\']*)["\']', data)
        print('APK URLs:', apk_urls[:5])
        break

# Try downloading via the XAPK downloader
print('\n--- Trying XAPK download ---')
xapk_url = 'https://d.apkpure.com/b/XAPK/com.tencent.tmgp.dfm?version=latest'
try:
    rx = requests.get(xapk_url, headers=headers, allow_redirects=True, timeout=30)
    print(f'XAPK Status: {rx.status_code}, CT: {rx.headers.get("Content-Type","?")}, Size: {len(rx.content)}')
    if 'apk' in rx.headers.get('Content-Type','') or len(rx.content) > 1000000:
        path = r'C:\u-claw\portable\data\.openclaw\workspace\delta_apk\delta_force.xapk'
        with open(path, 'wb') as f:
            f.write(rx.content)
        print(f'Saved XAPK ({len(rx.content)/1024/1024:.1f} MB)')
except Exception as e:
    print(f'XAPK Error: {e}')
