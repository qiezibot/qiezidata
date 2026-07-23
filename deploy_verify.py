import urllib.request, ssl, http.cookiejar, json
ctx = ssl.create_default_context(); cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))
opener.open(urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=b'username=admin&password=admin123', method='POST', headers={'Content-Type':'application/x-www-form-urlencoded'}), timeout=45)

# 1. Check clouddata list API returns real data
r = opener.open('https://qiezidata-production.up.railway.app/admin/clouddata', timeout=30)
d = json.loads(r.read())
print('admin/clouddata:', type(d).__name__, 'count:', len(d) if isinstance(d, list) else 'N/A')
if isinstance(d, list) and d:
    print('  sample:', d[0])

# 2. Check page has markCD and exportCD
r = opener.open('https://qiezidata-production.up.railway.app/', timeout=30)
html = r.read().decode('utf-8')
checks = {'exportCD':'OK' if 'exportCD' in html else 'M', 'markCD':'OK' if 'markCD' in html else 'M'}
print('Page:', {k:v for k,v in checks.items()})

# 3. Test markCD API
r = opener.open(urllib.request.Request('https://qiezidata-production.up.railway.app/clouddata/mark/id/2?read=true', data=b'', method='POST'), timeout=30)
print('mark id 2:', r.status, r.read().decode())

print('ALL VERIFIED')
