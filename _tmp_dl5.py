import requests, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# Try to get the APKPure download page and extract download URL
url = 'https://apkpure.net/delta-force-hawk-ops-cn/com.tencent.tmgp.dfm/download'
try:
    r = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
    print(f'Status: {r.status_code}, Size: {len(r.text)}')
    # Look for download links
    import re
    # Various patterns for APK download links
    patterns = [
        r'https?://[^"\']+\.apk[^"\']*',
        r'https?://[^"\']+/download/[^"\']+',
        r'"url"\s*:\s*"([^"]+\.apk[^"]*)"',
        r'href="([^"]*apk[^"]*download[^"]*)"',
        r'"([^"]*d[^"]*apkpure[^"]*download[^"]*)"',
    ]
    for pat in patterns:
        matches = re.findall(pat, r.text)
        for m in matches[:5]:
            clean = m.replace('\\/', '/').replace('\\u0026', '&')
            print(f'  Found: {clean[:250]}')
except Exception as e:
    print(f'Error: {e}')
