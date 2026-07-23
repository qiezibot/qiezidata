import urllib.request, ssl, http.cookiejar

ctx = ssl.create_default_context()
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))

# 1. Login
data = b'username=admin&password=admin123'
req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=data, method='POST',
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
r = opener.open(req, timeout=30)
body = r.read().decode('utf-8')

print(f'Status: {r.status}, len={len(body)}')

# 2. Check login title
idx1 = body.find('<title>')
idx2 = body.find('</title>')
print(f'Title: {body[idx1:idx2+8]}')

# 3. Check for Chinese keywords
for kw in ['茄子', '仪表盘', '文件管理', '用户管理', '上传文件', '退出', '全部文件']:
    print(f'{kw}: {kw in body}')

# 4. Try admin/stats
r2 = opener.open('https://qiezidata-production.up.railway.app/admin/stats', timeout=30)
import json
stats = json.loads(r2.read())
print(f'\nStats: {stats}')
