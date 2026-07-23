import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
r = requests.get('https://apkpure.net/delta-force-hawk-ops-cn/com.tencent.tmgp.dfm/download', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
html = r.text
# Find download links
matches = re.findall(r'downloadUrl["\']?\s*:\s*["\']([^"\']+)["\']', html)
for m in matches:
    print('downloadUrl:', m[:300])
matches2 = re.findall(r'data-url=["\']([^"\']+)["\']', html)
for m in matches2:
    if 'apk' in m.lower() or 'download' in m.lower():
        print('data-url:', m[:300])
matches3 = re.findall(r'href=["\']([^"\']*download[^"\']*)["\']', html)
for m in matches3:
    print('href:', m[:200])
# Check for the download button
if 'download-btn' in html or 'download-button' in html or 'downloader' in html:
    print('Found download button')
# Look for the XAPK/APK download
matches4 = re.findall(r'https://[^"\']+apkpure[^"\']+download[^"\']+', html)
for m in matches4:
    print('APKPure URL:', m[:300])
