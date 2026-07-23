import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://sj.qq.com/appdetail/com.tencent.tmgp.dfm', headers=headers, timeout=10)
html = r.text
# Find all apk download URLs  
urls = re.findall(r'https?://[^"\\\'<>\s]+\.apk[^"\\\'<>\s]*', html)
print(f'Found {len(urls)} APK URLs:')
for u in urls:
    print(u[:250])

print('\n--- Looking for delta-specific URLs ---')
# Find anything with tmgp.dfm or delta or 三角
for u in urls:
    if 'tmgp.dfm' in u or 'delta' in u.lower():
        print('MATCH:', u[:300])
