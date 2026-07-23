import urllib.request, json, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=b'username=admin&password=admin123', headers={'Content-Type':'application/x-www-form-urlencoded'})
opener.open(req)
r = opener.open(urllib.request.Request('https://qiezidata-production.up.railway.app/'))
html = r.read().decode('utf-8')
print(f'HTML: {len(html)}B')

checks = ['数据名称', '数据名字', '项目名称', 'set_admin', '设为管理员', '已是管理员', 'key标识符', 'Key:']
for s in checks:
    idx = html.find(s)
    print(f'  {s}: {"FOUND ✓" if idx>=0 else "NOT FOUND ✗"} at {idx if idx>=0 else "-"}')
