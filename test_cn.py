import urllib.request, ssl, http.cookiejar, json

ctx = ssl.create_default_context()
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))

# Login first
data = b'username=admin&password=admin123'
req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=data, method='POST',
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
r = opener.open(req, timeout=45)
body = r.read().decode('utf-8')
print(f'Login: status={r.status}, len={len(body)}')

# Check admin page features
features = ['\u4eea\u8868\u76d8', '\u6587\u4ef6\u7ba1\u7406', '\u7528\u6237\u7ba1\u7406', '\u4e91\u6570\u636e',
            '\u9000\u51fa\u767b\u5f55', 'page-clouddata', 'loadCloudData', 'addCloudData', 'delCloudData']
for f in features:
    print(f'  {f}: {f in body}')

# Test clouddata API: add
req2 = urllib.request.Request('https://qiezidata-production.up.railway.app/admin/clouddata/add',
    data=json.dumps({'key':'test_key','value':'hello world'}).encode(),
    headers={'Content-Type':'application/json'}, method='POST')
r2 = opener.open(req2, timeout=45)
print(f'\nCloudData add: status={r2.status}, body={r2.read().decode()}')

# Test clouddata API: list
r3 = opener.open('https://qiezidata-production.up.railway.app/admin/clouddata', timeout=45)
d = json.loads(r3.read())
print(f'CloudData list: status={r3.status}, count={len(d)}, data={d}')

# Test clouddata API: get stats
r4 = opener.open('https://qiezidata-production.up.railway.app/admin/stats', timeout=45)
print(f'Stats: {json.loads(r4.read())}')

print('\nALL OK!')
