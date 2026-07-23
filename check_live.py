import urllib.request, json, http.cookiejar

API = 'https://qiezidata-production.up.railway.app'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(urllib.request.Request(API+'/login', data=b'username=admin&password=admin123', headers={'Content-Type':'application/x-www-form-urlencoded'}))

r = opener.open(urllib.request.Request(API+'/'))
html = r.read().decode('utf-8')
print(f'HTML: {len(html)}B')

idx = html.find('<th>Id</th>')
if idx >= 0:
    end = html.find('</tr>', idx) + 5
    print(f'Live: {html[idx:end]}')
else:
    idx = html.find('数据名字')
    if idx >= 0:
        print(f'数据名字 found: {html[idx-20:idx+30]}')
    idx = html.find('项目')
    if idx >= 0:
        print(f'项目 found: {html[idx-10:idx+20]}')

# Also check all th
for i, line in enumerate(html.split('\n')):
    if '<th>' in line or '数据名字' in line or '项目' in line:
        print(f'Line {i}: {line.strip()[:120]}')
