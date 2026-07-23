import urllib.request, ssl, http.cookiejar, json

ctx = ssl.create_default_context()
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))

# Login
data = b'username=admin&password=admin123'
req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=data, method='POST',
    headers={'Content-Type':'application/x-www-form-urlencoded'})
r = opener.open(req, timeout=45)
print("=== Login OK ===\n")

# === Admin Page ===
body = r.read().decode('utf-8')
for f in ['仪表盘','文件管理','用户管理','云数据','退出登录','page-clouddata']:
    print(f'  Admin UI {f}: {f in body}')

print()

# === Script API Tests ===
tests = [
    ("POST /clouddata", urllib.request.Request('https://qiezidata-production.up.railway.app/clouddata',
        data=json.dumps({'key':'api_test','value':'hello from script'}).encode(),
        headers={'Content-Type':'application/json'}, method='POST')),
    ("GET /clouddata?key=api_test", 'https://qiezidata-production.up.railway.app/clouddata?key=api_test'),
    ("GET /clouddata/api_test", 'https://qiezidata-production.up.railway.app/clouddata/api_test'),
    ("GET /clouddata", 'https://qiezidata-production.up.railway.app/clouddata'),
    ("POST mark read", urllib.request.Request('https://qiezidata-production.up.railway.app/clouddata/mark/api_test?read=true',
        data=b'', method='POST')),
    ("POST mark unread", urllib.request.Request('https://qiezidata-production.up.railway.app/clouddata/mark/api_test?read=false',
        data=b'', method='POST')),
    ("POST mark by id", urllib.request.Request('https://qiezidata-production.up.railway.app/clouddata/mark/id/1?read=true',
        data=b'', method='POST')),
    ("GET export/all", 'https://qiezidata-production.up.railway.app/clouddata/export/all'),
    ("GET export/read", 'https://qiezidata-production.up.railway.app/clouddata/export/read'),
    ("GET export/unread", 'https://qiezidata-production.up.railway.app/clouddata/export/unread'),
    ("DELETE /clouddata/api_test", urllib.request.Request('https://qiezidata-production.up.railway.app/clouddata/api_test', method='DELETE')),
    ("Verify deleted", 'https://qiezidata-production.up.railway.app/clouddata?key=api_test'),
]

all_ok = True
for name, url_or_req in tests:
    try:
        if isinstance(url_or_req, str):
            r = opener.open(url_or_req, timeout=30)
        else:
            r = opener.open(url_or_req, timeout=30)
        body = r.read().decode('utf-8')
        print(f'  \u2705 {name}: {r.status} {body[:100]}')
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f'  \u274c {name}: {e.code} {body[:100]}')
        all_ok = False
    except Exception as e:
        print(f'  \u274c {name}: {e}')
        all_ok = False

print(f'\n=== {\u2705 ALL OK' if all_ok else '\u274c SOME FAILED'} ===')
