import urllib.request, json, http.cookiejar

API = 'https://qiezidata-production.up.railway.app'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

req = urllib.request.Request(API+'/login', data=b'username=admin&password=admin123', headers={'Content-Type':'application/x-www-form-urlencoded'})
opener.open(req)

r = opener.open(urllib.request.Request(API+'/'))
html = r.read().decode('utf-8')
print(f'HTML: {len(html)}B')

idx = html.find('Id</th>')
if idx >= 0:
    end = html.find('</tr>', idx)
    print(f'Live: {html[idx:end+5]}')
else:
    print('No Id th')
    for s in ['数据名字', '项目', '<th>I']:
        i = html.find(s)
        if i >= 0:
            print(f'{s}: {html[max(0,i-5):i+25]}')
